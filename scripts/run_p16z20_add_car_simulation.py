#!/usr/bin/env python3
"""
P16-Z20 Add-Car Commercial Simulation — runs 20 scenarios through triage_conversation.

Usage:
  PYTHONPATH=. LLM_GENERATION_ENABLED=0 python3 scripts/run_p16z20_add_car_simulation.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

os.environ.setdefault("LLM_GENERATION_ENABLED", "0")

from services.fiqa_api.inbox_triage.triage import triage_conversation  # noqa: E402

SCENARIOS_PATH = REPO / "configs" / "p16z20_add_car_customers.json"
OUT_PATH = REPO / "docs" / "product_constitution" / ".p16z20_results" / "simulation_results.json"

STRUCTURAL = {"year", "make_model", "zip", "delivery_date", "primary_driver", "vin"}
CONTACT = {"name", "phone"}

GENERIC_BROKER = (
    "review the",
    "follow up shortly",
    "provide more details",
    "request clarification",
    "reach out shortly",
)


def _run_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    turns: list[str] = list(scenario.get("turns") or [])
    conv: list[dict[str, str]] = []
    turn_snaps: list[dict[str, Any]] = []
    for i, text in enumerate(turns):
        out = triage_conversation(text, conv, client_id="chen_kui")
        turn_snaps.append(
            {
                "turn_index": i,
                "text": text,
                "service_type": out.get("service_type"),
                "collected_fields": out.get("collected_fields"),
                "still_needed_fields": out.get("still_needed_fields"),
                "broker_next_step": out.get("broker_next_step"),
                "handoff_ready": out.get("handoff_ready"),
                "action_ready": out.get("action_ready"),
                "issue_category": out.get("issue_category"),
                "primary_vehicle_summary": out.get("primary_vehicle_summary"),
                "conversation_summary": out.get("conversation_summary"),
                "client_reply_draft": (out.get("client_reply_draft") or "")[:200],
            }
        )
        conv.append({"role": "customer", "text": text})
    return {"final": out, "turns": turn_snaps}


def _score_case_quality(scenario: dict[str, Any], result: dict[str, Any]) -> tuple[int, list[str]]:
    notes: list[str] = []
    score = 0
    collected = {str(x).lower() for x in (result.get("collected_fields") or [])}
    still = {str(x).lower() for x in (result.get("still_needed_fields") or [])}
    service = (result.get("service_type") or "").strip().lower()
    category = (result.get("issue_category") or "").strip().lower()

    # Route correctness (20)
    if service == "add_car":
        score += 20
    elif category in ("add_vehicle", "add_car", "quote_request"):
        score += 12
        notes.append(f"service_type={service!r}, category={category}")
    else:
        notes.append(f"wrong route: service_type={service!r}, category={category}")

    # Collected coverage (30)
    exp_col = [str(x).lower() for x in (scenario.get("expected_collected") or [])]
    if exp_col:
        hits = sum(1 for f in exp_col if f in collected)
        slot_score = int(30 * hits / len(exp_col))
        score += slot_score
        if hits < len(exp_col):
            missed = [f for f in exp_col if f not in collected]
            notes.append(f"expected collected miss: {missed}")
    else:
        n_turns = len(scenario.get("turns") or [])
        if n_turns <= 1:
            score += 10
        else:
            score += 15

    # Still-needed accuracy (20)
    exp_still = [str(x).lower() for x in (scenario.get("expected_still") or [])]
    if exp_still:
        still_hits = sum(1 for f in exp_still if f in still)
        score += int(20 * still_hits / len(exp_still))
        if still_hits < len(exp_still):
            notes.append(f"still_needed miss: expected {exp_still}, got {sorted(still)}")
    elif scenario.get("completeness") == "complete":
        struct_still = still & STRUCTURAL
        if not struct_still:
            score += 18
        else:
            score += max(0, 18 - len(struct_still) * 4)
            notes.append(f"complete scenario still missing structural: {sorted(struct_still)}")
    else:
        if still:
            score += 12
        else:
            notes.append("incomplete scenario but still_needed empty")
            score += 4

    # Broker next step (15)
    broker = (result.get("broker_next_step") or "").strip()
    if broker and len(broker) > 20:
        score += 8
        if not any(m in broker.lower() for m in GENERIC_BROKER):
            score += 7
        else:
            score += 3
            notes.append("generic broker_next_step")
    else:
        notes.append("broker_next_step weak")

    # Summary / vehicle line (15)
    pvs = (result.get("primary_vehicle_summary") or "").strip()
    summary = (result.get("conversation_summary") or "").strip()
    if pvs and len(pvs) > 8:
        score += 8
    elif summary and len(summary) > 25:
        score += 5
    else:
        notes.append("weak vehicle/summary line")
    if result.get("handoff_ready") or result.get("action_ready"):
        score += 7
    elif service == "add_car":
        score += 3

    return min(score, 100), notes


def _broker_simulation(scenario: dict[str, Any], result: dict[str, Any], quality: int) -> dict[str, Any]:
    collected = {str(x).lower() for x in (result.get("collected_fields") or [])}
    still = list(result.get("still_needed_fields") or [])
    struct_missing = [f for f in still if str(f).lower() in STRUCTURAL]
    pvs = (result.get("primary_vehicle_summary") or "").strip()
    summary = (result.get("conversation_summary") or "").strip()
    service = (result.get("service_type") or "").strip().lower()
    n_turns = len(scenario.get("turns") or [])

    understand_5s = bool(
        service == "add_car" or "add" in summary.lower() or "vehicle" in summary.lower() or "加" in summary
    ) and bool(pvs or summary)

    need_wechat = False
    if service != "add_car":
        need_wechat = True
    elif not pvs and quality < 60:
        need_wechat = True
    elif struct_missing and len(struct_missing) >= 3 and n_turns <= 2:
        need_wechat = True
    elif quality < 50:
        need_wechat = True

    quote_now = service == "add_car" and len(struct_missing) <= 1 and "vin" not in [s.lower() for s in still]

    # Time model (minutes) — aligned with P16-Z19
    manual_read = 1.5 + 0.4 * n_turns
    manual_organize = 1.5 + 0.15 * len(collected)
    manual_followup = 0.0
    if struct_missing:
        manual_followup = 0.8 + 0.4 * len(struct_missing)
    if scenario.get("completeness") == "incomplete" and n_turns <= 2:
        manual_followup += 1.0
    manual_total = manual_read + manual_organize + manual_followup + 0.5

    with_builder = 0.35 + 0.08 * n_turns + (0.15 if still else 0.08)
    if need_wechat:
        with_builder += 1.2
    minutes_saved = max(0.0, round(manual_total - with_builder, 1))

    clarity = min(100, quality + (10 if pvs else -5) + (5 if not need_wechat else -15))
    completeness = min(
        100,
        int(100 * len(collected & STRUCTURAL) / 6) + (10 if not struct_missing else 0),
    )
    confidence = min(100, int((clarity + completeness) / 2) + (10 if quote_now else -10))

    return {
        "understand_5s": understand_5s,
        "need_wechat": need_wechat,
        "quote_immediately": quote_now,
        "still_missing": still,
        "minutes_saved": minutes_saved,
        "manual_minutes": round(manual_total, 1),
        "with_builder_minutes": round(with_builder, 1),
        "case_clarity": max(0, clarity),
        "case_completeness": max(0, completeness),
        "broker_confidence": max(0, confidence),
    }


def main() -> int:
    data = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    scenarios = data.get("scenarios") or []
    results: list[dict[str, Any]] = []

    for s in scenarios:
        run = _run_scenario(s)
        final = run["final"]
        quality, q_notes = _score_case_quality(s, final)
        broker = _broker_simulation(s, final, quality)
        results.append(
            {
                "id": s["id"],
                "title": s.get("title"),
                "tags": s.get("tags"),
                "completeness": s.get("completeness"),
                "turn_count": len(s.get("turns") or []),
                "service_type": final.get("service_type"),
                "collected_fields": final.get("collected_fields"),
                "still_needed_fields": final.get("still_needed_fields"),
                "broker_next_step": final.get("broker_next_step"),
                "primary_vehicle_summary": final.get("primary_vehicle_summary"),
                "conversation_summary": final.get("conversation_summary"),
                "handoff_ready": final.get("handoff_ready"),
                "action_ready": final.get("action_ready"),
                "case_quality": quality,
                "quality_notes": q_notes,
                "broker": broker,
                "turn_snapshots": run["turns"],
            }
        )

    qualities = [r["case_quality"] for r in results]
    saved = [r["broker"]["minutes_saved"] for r in results]
    need_wx = sum(1 for r in results if r["broker"]["need_wechat"])
    confidences = [r["broker"]["broker_confidence"] for r in results]

    ranked = sorted(results, key=lambda x: x["case_quality"], reverse=True)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario_count": len(results),
        "avg_case_quality": round(sum(qualities) / len(qualities), 1),
        "avg_minutes_saved": round(sum(saved) / len(saved), 1),
        "need_wechat_pct": round(100 * need_wx / len(results), 1),
        "avg_broker_confidence": round(sum(confidences) / len(confidences), 1),
        "best": ranked[:3],
        "worst": ranked[-3:],
    }

    payload = {"summary": summary, "results": results}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote {OUT_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
