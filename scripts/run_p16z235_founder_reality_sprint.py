#!/usr/bin/env python3
"""P16-Z23.5 Founder Reality Sprint — commercial simulation on fresh 20-case battery."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

os.environ.setdefault("LLM_GENERATION_ENABLED", "0")

from scripts.run_p16z20_add_car_simulation import (  # noqa: E402
    _broker_simulation,
    _run_scenario,
    _score_case_quality,
)

SCENARIOS_PATH = REPO / "configs" / "p16z235_add_car_customers.json"
OUT_PATH = REPO / "docs" / "product_constitution" / ".p16z235_results" / "simulation_results.json"


def _founder_demo_pride(scenario: dict[str, Any], result: dict[str, Any], quality: int, broker: dict[str, Any]) -> dict[str, Any]:
    service = (result.get("service_type") or "").strip().lower()
    draft = (result.get("client_reply_draft") or "").strip()
    pvs = (result.get("primary_vehicle_summary") or "").strip()
    tags = scenario.get("tags") or []

    proud = True
    reasons: list[str] = []

    if service != "add_car" and "high_risk" not in tags and "mixed_intent" not in tags:
        proud = False
        reasons.append(f"wrong lane: {service}")
    if quality < 70:
        proud = False
        reasons.append(f"quality {quality}")
    if broker.get("need_wechat"):
        proud = False
        reasons.append("broker must reopen WeChat")
    if not pvs and "minimal" not in tags:
        proud = False
        reasons.append("no vehicle line")
    if "minimal" in tags and quality >= 73:
        proud = True
        reasons = ["shows checklist gap capture — acceptable demo of incomplete intake"]

    if proud and not reasons:
        if quality >= 88:
            reasons.append("complete structured case + actionable broker step")
        elif result.get("handoff_ready"):
            reasons.append("handoff-ready with clear still_needed")
        else:
            reasons.append("correct incomplete checklist — office knows what to ask")

    return {"proud_demo": proud, "why": "; ".join(reasons) or "meets demo bar"}


def main() -> int:
    data = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    scenarios = data.get("scenarios") or []
    results: list[dict[str, Any]] = []

    for s in scenarios:
        run = _run_scenario(s)
        final = run["final"]
        quality, q_notes = _score_case_quality(s, final)
        broker = _broker_simulation(s, final, quality)
        founder = _founder_demo_pride(s, final, quality, broker)
        service = (final.get("service_type") or "").strip().lower()
        route_ok = service == "add_car"
        results.append(
            {
                "id": s["id"],
                "title": s.get("title"),
                "tags": s.get("tags"),
                "completeness": s.get("completeness"),
                "turn_count": len(s.get("turns") or []),
                "service_type": final.get("service_type"),
                "route_ok": route_ok,
                "collected_fields": final.get("collected_fields"),
                "still_needed_fields": final.get("still_needed_fields"),
                "broker_next_step": final.get("broker_next_step"),
                "handoff_ready": final.get("handoff_ready"),
                "action_ready": final.get("action_ready"),
                "case_quality": quality,
                "quality_notes": q_notes,
                "broker": broker,
                "founder": founder,
            }
        )

    qualities = [r["case_quality"] for r in results]
    saved = [r["broker"]["minutes_saved"] for r in results]
    need_wx = sum(1 for r in results if r["broker"]["need_wechat"])
    confidences = [r["broker"]["broker_confidence"] for r in results]
    route_acc = sum(1 for r in results if r["route_ok"]) / len(results) * 100
    proceed = sum(1 for r in results if r["broker"]["broker_confidence"] >= 70 and not r["broker"]["need_wechat"])
    proud = sum(1 for r in results if r["founder"]["proud_demo"])

    ranked = sorted(results, key=lambda x: x["case_quality"], reverse=True)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario_count": len(results),
        "route_accuracy_pct": round(route_acc, 1),
        "avg_case_quality": round(sum(qualities) / len(qualities), 1),
        "avg_minutes_saved": round(sum(saved) / len(saved), 1),
        "need_wechat_pct": round(100 * need_wx / len(results), 1),
        "avg_broker_confidence": round(sum(confidences) / len(confidences), 1),
        "broker_proceed_immediately_pct": round(100 * proceed / len(results), 1),
        "founder_proud_demo_pct": round(100 * proud / len(results), 1),
        "strongest_5": [{"id": r["id"], "title": r["title"], "quality": r["case_quality"]} for r in ranked[:5]],
        "weakest_5": [{"id": r["id"], "title": r["title"], "quality": r["case_quality"]} for r in ranked[-5:]],
    }

    payload = {"summary": summary, "results": results}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote {OUT_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
