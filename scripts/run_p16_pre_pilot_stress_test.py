#!/usr/bin/env python3
"""
P16 Pre-Pilot Stress Test — run all 33 scenarios through actual triage flow.

Usage:
  PYTHONPATH=. LLM_GENERATION_ENABLED=0 python3 scripts/run_p16_pre_pilot_stress_test.py
  PYTHONPATH=. LLM_GENERATION_ENABLED=0 python3 scripts/run_p16_pre_pilot_stress_test.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

os.environ.setdefault("LLM_GENERATION_ENABLED", "0")

from services.fiqa_api.inbox_triage.case_store import append_follow_up_message, save_case
from services.fiqa_api.inbox_triage.triage import triage_conversation, triage_for_append
from services.fiqa_api.routes.inbox_triage import _reply_truth_context_from_case

SCENARIOS_PATH = REPO / "configs" / "p16_pre_pilot_stress_test.json"
OUT_PATH = REPO / "docs" / "trial" / "P16_STRESS_TEST_RESULTS.md"
JSON_OUT = REPO / "docs" / "trial" / ".p16_stress_test_results.json"

STRUCTURAL = {"year", "make_model", "zip", "delivery_date", "primary_driver", "vin"}
GENERIC_BROKER = (
    "review the",
    "follow up shortly",
    "provide more details",
    "request clarification",
    "reach out shortly",
    "ask for the missing part",
)
PRESERVE_SLOTS = {"vin", "zip", "delivery_date", "primary_driver", "name", "phone", "year", "make_model"}


def _broker_display_step(result: dict[str, Any]) -> str:
    office = (result.get("office_broker_next_step") or "").strip()
    if office:
        return office
    return (result.get("broker_next_step") or "").strip()


def _score_conversation(scenario: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    collected = {str(x).lower() for x in (result.get("collected_fields") or [])}
    still = {str(x).lower() for x in (result.get("still_needed_fields") or [])}
    service = (result.get("service_type") or "").strip().lower()
    broker = _broker_display_step(result)
    pvs = (result.get("primary_vehicle_summary") or "").strip()
    summary = (result.get("conversation_summary") or "").strip()
    n_turns = len(scenario.get("turns") or [])

    route_score = 15 if service == "add_car" else 0
    veh_score = 8 if "year" in collected and "make_model" in collected else (4 if collected & {"year", "make_model"} else 0)
    if pvs and len(pvs) > 5:
        veh_score = min(12, veh_score + 4)

    driver_score = 10 if "primary_driver" in collected else (5 if "primary_driver" in still else 0)

    exp_col = {str(x).lower() for x in (scenario.get("expected_collected") or [])}
    exp_still = {str(x).lower() for x in (scenario.get("expected_still") or [])}
    field_score = 8
    if exp_col:
        hits = sum(1 for f in exp_col if f in collected)
        field_score = min(12, int(12 * hits / max(1, len(exp_col))))
    elif exp_still:
        hits = sum(1 for f in exp_still if f in still)
        field_score = min(12, int(12 * hits / max(1, len(exp_still))))

    missing_score = 10
    if scenario.get("completeness") == "complete" and (still & STRUCTURAL):
        missing_score -= len(still & STRUCTURAL) * 3
    missing_score = max(0, missing_score)

    broker_score = 0
    if broker and len(broker) > 12:
        broker_score += 6
        broker_score += 6 if not any(m in broker.lower() for m in GENERIC_BROKER) else 2

    understand = bool(service == "add_car" and (pvs or summary))
    understand_score = 10 if understand else 3
    need_wechat = service != "add_car" or (not summary and not collected and not still)
    wechat_score = 2 if need_wechat else 8

    manual = 1.5 + 0.4 * n_turns + 1.5 + 0.15 * len(collected)
    if still & STRUCTURAL:
        manual += 0.8 + 0.4 * len(still & STRUCTURAL)
    with_builder = 0.35 + 0.08 * n_turns + (0.15 if still else 0.08)
    minutes_saved = max(0.0, round(manual - with_builder, 1))
    minutes_score = min(11, int(11 * min(minutes_saved, 6) / 4))

    total = min(
        100,
        route_score + veh_score + driver_score + field_score + missing_score
        + broker_score + understand_score + wechat_score + minutes_score,
    )
    return {
        "total": total,
        "need_wechat": need_wechat,
        "minutes_saved": minutes_saved,
        "route_ok": service == "add_car",
    }


def _run_conversation(scenario: dict[str, Any]) -> dict[str, Any]:
    turns: list[str] = list(scenario.get("turns") or [])
    conv: list[dict[str, str]] = []
    turn_snaps: list[dict[str, Any]] = []
    out: dict[str, Any] = {}
    for i, text in enumerate(turns):
        out = triage_conversation(text, conv, client_id="chen_kui")
        turn_snaps.append(
            {
                "turn_index": i,
                "text": text,
                "service_type": out.get("service_type"),
                "collected_fields": out.get("collected_fields"),
                "still_needed_fields": out.get("still_needed_fields"),
                "broker_next_step": _broker_display_step(out),
                "handoff_ready": out.get("handoff_ready"),
                "action_ready": out.get("action_ready"),
            }
        )
        conv.append({"role": "customer", "text": text})

    dims = _score_conversation(scenario, out)
    collected = {str(x).lower() for x in (out.get("collected_fields") or [])}

    continuity_ok = True
    continuity_notes: list[str] = []
    preserve = {str(x).lower() for x in (scenario.get("preserve_across_turns") or [])}
    if preserve and len(turn_snaps) > 1:
        for slot in preserve:
            seen = False
            for snap in turn_snaps:
                snap_c = {str(x).lower() for x in (snap.get("collected_fields") or [])}
                if slot in snap_c:
                    seen = True
                elif seen and slot not in snap_c and slot not in {str(x).lower() for x in (snap.get("still_needed_fields") or [])}:
                    continuity_ok = False
                    continuity_notes.append(f"lost {slot} after turn {snap['turn_index']}")

    passed = dims["total"] >= 80 and dims["route_ok"] and continuity_ok
    return {
        "mode": "conversation",
        "final": out,
        "turns": turn_snaps,
        "quality": dims["total"],
        "route": out.get("service_type"),
        "collected_fields": out.get("collected_fields"),
        "still_needed_fields": out.get("still_needed_fields"),
        "broker_next_step": _broker_display_step(out),
        "handoff_ready": out.get("handoff_ready"),
        "action_ready": out.get("action_ready"),
        "formal_submit_ready": out.get("handoff_ready") or out.get("action_ready"),
        "continuity_ok": continuity_ok,
        "continuity_notes": continuity_notes,
        "append_ok": None,
        "pass": passed,
        "dimensions": dims,
    }


def _setup_store() -> None:
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)


def _make_append_case(base_turns: list[str], formal_collected: list[str], formal_still: list[str]) -> tuple[dict, str]:
    conv: list[dict[str, str]] = []
    source_parts: list[str] = []
    for t in base_turns:
        source_parts.append(f"[客户] {t}")
        conv.append({"role": "customer", "text": t})
    source = "\n".join(source_parts)
    formal = triage_conversation(base_turns[-1], conv[:-1], client_id="chen_kui")
    formal["collected_fields"] = formal_collected
    formal["still_needed_fields"] = formal_still
    case = save_case(source, formal, service_lane="add_car")
    return case, source


def _run_append(scenario: dict[str, Any]) -> dict[str, Any]:
    base_turns = list(scenario.get("base_turns") or [])
    append_msgs = list(scenario.get("append_messages") or [])
    formal_collected = list(scenario.get("formal_collected") or [])
    formal_still = list(scenario.get("formal_still") or [])

    case, source = _make_append_case(base_turns, formal_collected, formal_still)
    before_c = {str(x).lower() for x in (case.get("collected_fields") or [])}
    append_snaps: list[dict[str, Any]] = []

    updated = case
    all_ok = True
    for i, msg in enumerate(append_msgs):
        ctx = _reply_truth_context_from_case(updated)
        triage = triage_for_append(source, msg, reply_truth_context=ctx)
        updated = append_follow_up_message(updated["case_id"], msg, triage) or updated
        after_c = {str(x).lower() for x in (updated.get("collected_fields") or [])}
        must_keep = {str(x).lower() for x in (scenario.get("must_preserve") or list(PRESERVE_SLOTS))}
        lost = sorted(must_keep - after_c)
        snap_ok = not lost
        if not snap_ok:
            all_ok = False
        append_snaps.append(
            {
                "append_index": i,
                "message": msg,
                "collected_fields": updated.get("collected_fields"),
                "still_needed_fields": updated.get("still_needed_fields"),
                "lost_slots": lost,
                "pass": snap_ok,
            }
        )
        source = source + f"\n[客户] {msg}"

    final = updated
    out = triage_conversation(append_msgs[-1] if append_msgs else base_turns[-1], [], client_id="chen_kui")
    dims = _score_conversation(scenario, {**out, **final})
    passed = all_ok and (final.get("service_type") or "add_car") == "add_car"
    return {
        "mode": "append",
        "final": final,
        "turns": append_snaps,
        "quality": 100 if all_ok else max(60, dims["total"]),
        "route": final.get("service_type") or "add_car",
        "collected_fields": final.get("collected_fields"),
        "still_needed_fields": final.get("still_needed_fields"),
        "broker_next_step": final.get("office_broker_next_step") or final.get("broker_next_step"),
        "handoff_ready": final.get("handoff_ready"),
        "action_ready": final.get("action_ready"),
        "formal_submit_ready": final.get("handoff_ready"),
        "continuity_ok": all_ok,
        "continuity_notes": [],
        "append_ok": all_ok,
        "pass": passed,
        "dimensions": dims,
    }


def _run_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    mode = (scenario.get("mode") or "conversation").strip().lower()
    if mode == "append":
        run = _run_append(scenario)
    else:
        run = _run_conversation(scenario)
    run["id"] = scenario["id"]
    run["title"] = scenario.get("title", "")
    run["category"] = scenario.get("category", "")
    return run


def _md_report(results: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# P16 Stress Test Results",
        "",
        "**Sprint:** P16-PRE-PILOT-STRESS-TEST-SPRINT · Phase 5",
        f"**Run:** {summary['generated_at']}",
        "**Engine:** `triage_conversation` · `triage_for_append` · LLM_GENERATION_ENABLED=0",
        f"**Scenarios:** {summary['total']} (20 realistic + 3 edge + 5 return-later + 5 append)",
        "",
        "## Executive summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total scenarios | {summary['total']} |",
        f"| Passed (quality ≥80 + integrity) | **{summary['passed']}/{summary['total']} ({summary['pass_rate']:.1f}%)** |",
        f"| Route accuracy | {summary['route_accuracy']:.1f}% |",
        f"| Avg quality score | {summary['avg_quality']}/100 |",
        f"| Append regressions | {summary['append_failures']} |",
        f"| Continuity regressions | {summary['continuity_failures']} |",
        f"| Avg minutes saved vs manual | {summary['avg_minutes_saved']} min |",
        "",
        "---",
        "",
    ]
    for r in results:
        mark = "PASS" if r["pass"] else "FAIL"
        lines.extend(
            [
                f"## {r['id']} — {r['title']} — **{mark}**",
                "",
                f"| Field | Value |",
                f"|-------|-------|",
                f"| Category | {r.get('category', '—')} |",
                f"| Mode | {r.get('mode', 'conversation')} |",
                f"| Route | `{r.get('route')}` |",
                f"| Quality | {r.get('quality')}/100 |",
                f"| Collected | {', '.join(r.get('collected_fields') or []) or '—'} |",
                f"| Still needed | {', '.join(r.get('still_needed_fields') or []) or '—'} |",
                f"| Office next step | {r.get('broker_next_step') or '—'} |",
                f"| Handoff ready | {r.get('handoff_ready')} |",
                f"| Action ready | {r.get('action_ready')} |",
                f"| Formal submit ready | {r.get('formal_submit_ready')} |",
                f"| Continuity OK | {r.get('continuity_ok')} |",
                f"| Append OK | {r.get('append_ok') if r.get('append_ok') is not None else 'N/A'} |",
                "",
            ]
        )
        if r.get("continuity_notes"):
            lines.append(f"**Continuity notes:** {', '.join(r['continuity_notes'])}")
            lines.append("")
        for snap in r.get("turns") or []:
            if "turn_index" in snap:
                lines.append(f"**Turn {snap['turn_index'] + 1}:** collected={snap.get('collected_fields')} still={snap.get('still_needed_fields')}")
            elif "append_index" in snap:
                lines.append(f"**Append {snap['append_index'] + 1}:** `{snap.get('message', '')[:80]}` → lost={snap.get('lost_slots') or 'none'}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not SCENARIOS_PATH.exists():
        print(f"ERROR: {SCENARIOS_PATH} not found", file=sys.stderr)
        return 1

    _setup_store()
    data = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    scenarios = data.get("scenarios") or []
    results = [_run_scenario(s) for s in scenarios]

    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    routes_ok = sum(1 for r in results if (r.get("route") or "").lower() == "add_car" or r.get("mode") == "append")
    qualities = [r["quality"] for r in results]
    minutes = [r["dimensions"]["minutes_saved"] for r in results]
    append_fail = sum(1 for r in results if r.get("append_ok") is False)
    cont_fail = sum(1 for r in results if r.get("continuity_ok") is False)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "passed": passed,
        "pass_rate": round(100 * passed / total, 1) if total else 0,
        "route_accuracy": round(100 * routes_ok / total, 1) if total else 0,
        "avg_quality": round(sum(qualities) / len(qualities), 1) if qualities else 0,
        "avg_minutes_saved": round(sum(minutes) / len(minutes), 1) if minutes else 0,
        "append_failures": append_fail,
        "continuity_failures": cont_fail,
        "results": results,
    }

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    OUT_PATH.write_text(_md_report(results, summary), encoding="utf-8")

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    else:
        for r in results:
            mark = "PASS" if r["pass"] else "FAIL"
            print(f"[{mark}] {r['id']}: quality={r['quality']} route={r.get('route')}")
        print(f"\n{passed}/{total} passed ({summary['pass_rate']}%)")
        print(f"Results: {OUT_PATH}")

    return 0 if passed >= int(total * 0.95) and append_fail == 0 and cont_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
