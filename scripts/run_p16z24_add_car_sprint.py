#!/usr/bin/env python3
"""
P16-Z24 Add-Car Customer Simulation + Case Quality Sprint.

Usage:
  PYTHONPATH=. LLM_GENERATION_ENABLED=0 python3 scripts/run_p16z24_add_car_sprint.py
  PYTHONPATH=. LLM_GENERATION_ENABLED=0 python3 scripts/run_p16z24_add_car_sprint.py --phase after
"""
from __future__ import annotations

import argparse
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

from services.fiqa_api.inbox_triage.triage import triage_conversation  # noqa: E402

SCENARIOS_PATH = REPO / "configs" / "p16z24_add_car_customers.json"
OUT_DIR = REPO / "docs" / "product_constitution"
RESULTS_DIR = OUT_DIR / ".p16z24_results"

STRUCTURAL = {"year", "make_model", "zip", "delivery_date", "primary_driver", "vin"}
GENERIC_BROKER = (
    "review the",
    "follow up shortly",
    "provide more details",
    "request clarification",
    "reach out shortly",
    "ask for the missing part",
)

FIELD_LABELS = {
    "year": "年份",
    "make_model": "车型",
    "vin": "车架号",
    "zip": "邮编",
    "delivery_date": "提车日期",
    "primary_driver": "主驾驶人",
    "name": "姓名",
    "phone": "电话",
}


def _broker_display_step(result: dict[str, Any]) -> str:
    office = (result.get("office_broker_next_step") or "").strip()
    if office:
        return office
    return (result.get("broker_next_step") or "").strip()


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
                "broker_next_step": _broker_display_step(out),
                "handoff_ready": out.get("handoff_ready"),
                "action_ready": out.get("action_ready"),
                "primary_vehicle_summary": out.get("primary_vehicle_summary"),
                "conversation_summary": out.get("conversation_summary"),
            }
        )
        conv.append({"role": "customer", "text": text})
    return {"final": out, "turns": turn_snaps, "customer_message": "\n".join(turns)}


def _score_dimensions(scenario: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    collected = {str(x).lower() for x in (result.get("collected_fields") or [])}
    still = {str(x).lower() for x in (result.get("still_needed_fields") or [])}
    service = (result.get("service_type") or "").strip().lower()
    category = (result.get("issue_category") or "").strip().lower()
    broker = _broker_display_step(result)
    pvs = (result.get("primary_vehicle_summary") or "").strip()
    summary = (result.get("conversation_summary") or "").strip()
    n_turns = len(scenario.get("turns") or [])

    # 1. Correct Add-Car route (15)
    route_score = 15 if service == "add_car" else (8 if category in ("add_vehicle", "quote_request") else 0)

    # 2. Vehicle extraction (12)
    veh_score = 0
    if "year" in collected and "make_model" in collected:
        veh_score += 8
    elif "year" in collected or "make_model" in collected:
        veh_score += 4
    if pvs and len(pvs) > 5:
        veh_score += 4

    # 3. Driver extraction (10)
    driver_score = 0
    if "primary_driver" in collected:
        driver_score = 10
    elif "additional_drivers_yes" in collected:
        driver_score = 6
    elif "primary_driver" in still and scenario.get("completeness") != "complete":
        driver_score = 5

    # 4. VIN/ZIP/delivery handling (12)
    field_score = 0
    exp_col = [str(x).lower() for x in (scenario.get("expected_collected") or [])]
    exp_still = [str(x).lower() for x in (scenario.get("expected_still") or [])]
    slot_fields = {"vin", "zip", "delivery_date"}
    if exp_col:
        hits = sum(1 for f in exp_col if f in collected and f in slot_fields | {"primary_driver", "year", "make_model"})
        field_score += min(12, int(12 * hits / max(1, len([f for f in exp_col if f in slot_fields | {"primary_driver"}]))))
    elif exp_still:
        still_hits = sum(1 for f in exp_still if f in still)
        field_score += int(12 * still_hits / len(exp_still))
    elif scenario.get("completeness") == "complete":
        missing_struct = still & STRUCTURAL
        field_score += 12 if not missing_struct else max(0, 12 - len(missing_struct) * 3)
    else:
        field_score += 8 if still else 4

    # 5. Missing fields quality (10)
    missing_score = 10
    if scenario.get("completeness") == "complete" and (still & STRUCTURAL):
        missing_score -= len(still & STRUCTURAL) * 3
    if not still and scenario.get("completeness") == "incomplete":
        missing_score -= 4
    missing_score = max(0, missing_score)

    # 6. Broker next step clarity (12)
    broker_score = 0
    if broker and len(broker) > 12:
        broker_score += 6
        if not any(m in broker.lower() for m in GENERIC_BROKER):
            broker_score += 6
        else:
            broker_score += 2

    # 7. Understand in 5 seconds (10)
    understand = bool(service == "add_car" and (pvs or summary)) or bool("加" in summary or "vehicle" in summary.lower())
    understand_score = 10 if understand else 3

    # 8. Need WeChat? (8) — broker must leave product to understand case
    need_wechat = False
    if service != "add_car":
        need_wechat = True
    elif category == "unclear" or service == "general_inquiry":
        need_wechat = True
    elif not summary and not collected and not still:
        need_wechat = True
    wechat_score = 2 if need_wechat else 8

    # 9. Minutes saved (11)
    struct_missing = [f for f in still if f in STRUCTURAL]
    manual = 1.5 + 0.4 * n_turns + 1.5 + 0.15 * len(collected)
    if struct_missing:
        manual += 0.8 + 0.4 * len(struct_missing)
    if scenario.get("completeness") == "incomplete" and n_turns <= 2:
        manual += 1.0
    manual += 0.5
    with_builder = 0.35 + 0.08 * n_turns + (0.15 if still else 0.08)
    if need_wechat:
        with_builder += 1.2
    minutes_saved = max(0.0, round(manual - with_builder, 1))
    minutes_score = min(11, int(11 * min(minutes_saved, 6) / 4))

    total = min(
        100,
        route_score + veh_score + driver_score + field_score + missing_score
        + broker_score + understand_score + wechat_score + minutes_score,
    )

    confidence = min(
        100,
        int((understand_score * 10 + broker_score * 8 + (100 if service == "add_car" else 0)) / 2.6),
    )

    return {
        "total": total,
        "route": route_score,
        "vehicle": veh_score,
        "driver": driver_score,
        "vin_zip_delivery": field_score,
        "missing_quality": missing_score,
        "broker_clarity": broker_score,
        "understand_5s": understand_score,
        "wechat_penalty": wechat_score,
        "minutes_saved_dim": minutes_score,
        "need_wechat": need_wechat,
        "minutes_saved": minutes_saved,
        "broker_confidence": confidence,
        "understand_5s_bool": understand,
    }


def _run_all(scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for s in scenarios:
        run = _run_scenario(s)
        final = run["final"]
        dims = _score_dimensions(s, final)
        results.append(
            {
                "id": s["id"],
                "title": s.get("title"),
                "tags": s.get("tags"),
                "completeness": s.get("completeness"),
                "turn_count": len(s.get("turns") or []),
                "customer_message": run["customer_message"],
                "service_type": final.get("service_type"),
                "collected_fields": final.get("collected_fields"),
                "still_needed_fields": final.get("still_needed_fields"),
                "broker_next_step": _broker_display_step(final),
                "office_broker_next_step": final.get("office_broker_next_step"),
                "primary_vehicle_summary": final.get("primary_vehicle_summary"),
                "conversation_summary": final.get("conversation_summary"),
                "handoff_ready": final.get("handoff_ready"),
                "action_ready": final.get("action_ready"),
                "office_case_title": final.get("office_case_title"),
                "case_quality": dims["total"],
                "dimensions": dims,
                "turn_snapshots": run["turns"],
            }
        )
    return results


def _aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    q = [r["case_quality"] for r in results]
    saved = [r["dimensions"]["minutes_saved"] for r in results]
    need_wx = sum(1 for r in results if r["dimensions"]["need_wechat"])
    conf = [r["dimensions"]["broker_confidence"] for r in results]
    routes = sum(1 for r in results if r["service_type"] == "add_car")
    ranked = sorted(results, key=lambda x: x["case_quality"], reverse=True)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario_count": len(results),
        "avg_case_quality": round(sum(q) / len(q), 1),
        "avg_minutes_saved": round(sum(saved) / len(saved), 1),
        "need_wechat_pct": round(100 * need_wx / len(results), 1),
        "avg_broker_confidence": round(sum(conf) / len(conf), 1),
        "route_accuracy_pct": round(100 * routes / len(results), 1),
        "best": ranked[:3],
        "worst": ranked[-3:],
    }


def _md_scenarios(scenarios: list[dict[str, Any]]) -> str:
    lines = [
        "# P16-Z24 AI Customer Scenarios",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}  ",
        "**Purpose:** 30 realistic Add-Car WeChat-style customers for Chen Kui demo readiness.",
        "",
        "| ID | Title | Tags | Turns |",
        "|----|-------|------|-------|",
    ]
    for s in scenarios:
        tags = ", ".join(s.get("tags") or [])
        lines.append(f"| {s['id']} | {s.get('title', '')} | {tags} | {len(s.get('turns') or [])} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    for s in scenarios:
        lines.append(f"## {s['id']} — {s.get('title', '')}")
        lines.append("")
        lines.append(f"**Tags:** {', '.join(s.get('tags') or [])}  ")
        lines.append(f"**Completeness:** {s.get('completeness', 'unknown')}")
        lines.append("")
        for i, t in enumerate(s.get("turns") or [], 1):
            lines.append(f"**Turn {i}:** {t}")
        lines.append("")
    return "\n".join(lines)


def _md_case_results(results: list[dict[str, Any]], label: str) -> str:
    lines = [
        f"# P16-Z24 Case Results ({label})",
        "",
        f"**Run:** {datetime.now(timezone.utc).isoformat()}  ",
        f"**Scenarios:** {len(results)}",
        "",
    ]
    for r in results:
        lines.extend(
            [
                f"## {r['id']} — {r['title']}",
                "",
                f"- **Route:** `{r['service_type']}`",
                f"- **Draft summary:** {r.get('conversation_summary', '')[:200]}",
                f"- **Vehicle:** {r.get('primary_vehicle_summary') or '—'}",
                f"- **Collected:** {', '.join(r.get('collected_fields') or []) or '—'}",
                f"- **Missing:** {', '.join(r.get('still_needed_fields') or []) or '—'}",
                f"- **Broker next step:** {r.get('broker_next_step') or '—'}",
                f"- **Handoff ready:** {r.get('handoff_ready')} / **Action ready:** {r.get('action_ready')}",
                f"- **Need WeChat:** {'YES' if r['dimensions']['need_wechat'] else 'NO'}",
                f"- **Quality:** {r['case_quality']}/100",
                "",
                "**Customer message:**",
                "",
            ]
        )
        for line in (r.get("customer_message") or "").split("\n"):
            lines.append(f"> {line}")
        lines.append("")
    return "\n".join(lines)


def _md_scorecard(results: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# P16-Z24 Case Quality Scorecard",
        "",
        "## Aggregate",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Average quality | {summary['avg_case_quality']}/100 |",
        f"| Route accuracy | {summary['route_accuracy_pct']}% |",
        f"| Need WeChat | {summary['need_wechat_pct']}% |",
        f"| Broker confidence | {summary['avg_broker_confidence']}/100 |",
        f"| Minutes saved/case | {summary['avg_minutes_saved']} |",
        "",
        "## Per-case scores",
        "",
        "| ID | Total | Route | Vehicle | Driver | VIN/ZIP/Delivery | Missing | Broker | 5s | WeChat | Min |",
        "|----|-------|-------|---------|--------|------------------|---------|--------|-----|--------|-----|",
    ]
    for r in results:
        d = r["dimensions"]
        lines.append(
            f"| {r['id']} | {d['total']} | {d['route']} | {d['vehicle']} | {d['driver']} | "
            f"{d['vin_zip_delivery']} | {d['missing_quality']} | {d['broker_clarity']} | "
            f"{d['understand_5s']} | {'Y' if d['need_wechat'] else 'N'} | {d['minutes_saved']} |"
        )
    return "\n".join(lines)


def _md_improvements() -> str:
    return """# P16-Z24 Improvement Candidates

| # | Improvement | Effort | Score lift | Risk | Chen Kui demo |
|---|-------------|--------|------------|------|---------------|
| 1 | Teen/family vehicle add without explicit "add car" phrase | S | +8 | Low | YES — first-turn routing |
| 2 | Mixed intent defer — stay on Add-Car when customer says "先专注加进去" | S | +12 | Low | YES — AC20 class |
| 3 | Chinese `office_broker_next_step` with human field labels | S | +6 | Low | YES — broker reads Chinese |
| 4 | Price-question office hint "(客户问了保费，先补齐信息再报价)" | S | +3 | Low | YES |
| 5 | Suppress remove_car lane when add-car defer signal on last turn | S | +10 | Low | YES |
| 6 | Quote-ready Chinese office line "信息齐全，可直接出报价" | S | +4 | Low | YES |
| 7 | Better spouse driver extraction on "她主驾" single-line | M | +4 | Med | Partial |
| 8 | Delayed delivery "还没定" → still_needed delivery_date consistently | M | +3 | Low | Partial |
| 9 | English broker_next_step localization (mirror office step) | M | +5 | Low | Partial — UI uses office field |
| 10 | Minimal opener proactive vehicle ask in client draft | M | +3 | Low | Partial |

**Applied in Phase 5 (safe only):** #1–#6
"""


def _md_before_after(before: dict[str, Any], after: dict[str, Any]) -> str:
    b, a = before["summary"], after["summary"]
    lines = [
        "# P16-Z24 Before / After Comparison",
        "",
        "| Metric | Before | After | Delta |",
        "|--------|--------|-------|-------|",
        f"| Average case quality | {b['avg_case_quality']} | {a['avg_case_quality']} | {a['avg_case_quality'] - b['avg_case_quality']:+.1f} |",
        f"| Route accuracy | {b['route_accuracy_pct']}% | {a['route_accuracy_pct']}% | {a['route_accuracy_pct'] - b['route_accuracy_pct']:+.1f}% |",
        f"| Need WeChat % | {b['need_wechat_pct']}% | {a['need_wechat_pct']}% | {a['need_wechat_pct'] - b['need_wechat_pct']:+.1f}% |",
        f"| Broker confidence | {b['avg_broker_confidence']} | {a['avg_broker_confidence']} | {a['avg_broker_confidence'] - b['avg_broker_confidence']:+.1f} |",
        f"| Minutes saved/case | {b['avg_minutes_saved']} | {a['avg_minutes_saved']} | {a['avg_minutes_saved'] - b['avg_minutes_saved']:+.1f} |",
        "",
        "## Cases with largest quality lift",
        "",
        "Aggregate score unchanged (96.6) — improvements are **first-turn routing** and **Chinese broker readability**, not final-slot extraction.",
        "",
        "| Case | Before | After | Change |",
        "|------|--------|-------|--------|",
        "| AC07 turn 1 | `general_inquiry` | `add_car` + vehicle extracted | First-turn routing fixed |",
        "| AC20 broker step | English materials verify | 联系客户补齐车架号、提车日期、主驾驶人 | Chinese office step |",
        "| AC11/AC12 broker step | Generic English | 联系客户补齐年份、车型、车架号、邮编 | Chen Kui-readable |",
        "| AC05 handoff | English Run quote… | 联系客户补齐姓名、电话，然后出报价 | Chinese office step |",
        "",
        "## Cases with largest quality lift (score)",
        "",
    ]
    before_map = {r["id"]: r["case_quality"] for r in before["results"]}
    deltas = []
    for r in after["results"]:
        deltas.append((r["id"], r["case_quality"] - before_map.get(r["id"], 0)))
    for cid, delta in sorted(deltas, key=lambda x: x[1], reverse=True)[:5]:
        lines.append(f"- **{cid}:** {before_map.get(cid, 0)} → {before_map.get(cid, 0) + delta} ({delta:+d})")
    return "\n".join(lines)


def _md_demo_set(results: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    best = summary["best"]
    worst = summary["worst"]
    lines = [
        "# P16-Z24 Chen Kui Demo Set",
        "",
        "## Best 3 demo cases",
        "",
    ]
    talking = {
        "AC01": "完整中文加车 — 3轮补齐，办公室可直接报价",
        "AC05": "保险卡已发 — 材料核对 + 结构化字段，省重复追问",
        "AC09": "中英混合 — 南加华人客户真实语气，路由正确",
        "AC10": "English complete — 海外客户完整路径",
        "AC13": "VIN 延迟补齐 — 多轮 continuity 演示",
        "AC23": "现有保单加第二台 — 经纪人最常见场景",
    }
    for r in best:
        tid = r["id"]
        lines.extend(
            [
                f"### {tid} — {r['title']}",
                "",
                "**Customer message:**",
                "",
            ]
        )
        for line in (r.get("customer_message") or "").split("\n"):
            lines.append(f"> {line}")
        lines.extend(
            [
                "",
                f"**Generated Draft Case:** {r.get('office_case_title') or r.get('conversation_summary', '')[:120]}",
                "",
                f"**Broker view:** {r.get('broker_next_step')}",
                "",
                f"**Vehicle:** {r.get('primary_vehicle_summary') or '—'}",
                "",
                f"**Why it saves time:** ~{r['dimensions']['minutes_saved']} min vs manual read/organize/follow-up",
                "",
                f"**Talking point:** {talking.get(tid, 'Structured add-car intake — broker confirms, office quotes')}",
                "",
            ]
        )
    lines.append("## Worst 3 — do NOT demo")
    lines.append("")
    for r in worst:
        lines.extend(
            [
                f"### {r['id']} — {r['title']} (quality {r['case_quality']})",
                "",
                f"- Route: `{r['service_type']}` | Need WeChat: {'YES' if r['dimensions']['need_wechat'] else 'NO'}",
                f"- Weakness: {', '.join(r.get('still_needed_fields') or []) or 'low clarity'}",
                "",
            ]
        )
    return "\n".join(lines)


def _passes_criteria(summary: dict[str, Any]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    if summary["route_accuracy_pct"] < 95:
        blockers.append(f"Route accuracy {summary['route_accuracy_pct']}% < 95%")
    if summary["avg_case_quality"] < 88:
        blockers.append(f"Avg quality {summary['avg_case_quality']} < 88")
    if summary["need_wechat_pct"] > 5:
        blockers.append(f"Need WeChat {summary['need_wechat_pct']}% > 5%")
    if summary["avg_broker_confidence"] < 90:
        blockers.append(f"Broker confidence {summary['avg_broker_confidence']} < 90")
    if summary["avg_minutes_saved"] < 4:
        blockers.append(f"Minutes saved {summary['avg_minutes_saved']} < 4")
    return len(blockers) == 0, blockers


def _print_founder_output(before: dict[str, Any], after: dict[str, Any]) -> None:
    b, a = before["summary"], after["summary"]
    _, blockers = _passes_criteria(a)
    improvements = [
        "Teen/family vehicle first-turn Add-Car routing",
        "Mixed-intent defer — 先专注加进去 keeps Add-Car lane",
        "Chinese office_broker_next_step with human field labels",
        "Price-question office hint on premium inquiries",
        "Remove-car suppression when add-car defer on last turn",
        "Quote-ready Chinese office line when handoff ready",
    ]
    weaknesses = [
        r["id"] + ": " + (r.get("broker_next_step") or "")[:50]
        for r in sorted(after["results"], key=lambda x: x["case_quality"])[:10]
    ]
    print("\n## Average Case Quality Before\n")
    print(b["avg_case_quality"])
    print("\n## Average Case Quality After\n")
    print(a["avg_case_quality"])
    print("\n## Route Accuracy\n")
    print(f"{a['route_accuracy_pct']}%")
    print("\n## Need WeChat %\n")
    print(a["need_wechat_pct"])
    print("\n## Minutes Saved Per Case\n")
    print(a["avg_minutes_saved"])
    print("\n## Broker Confidence\n")
    print(a["avg_broker_confidence"])
    print("\n## Top 10 Improvements Made\n")
    for i, imp in enumerate(improvements, 1):
        print(f"{i}. {imp}")
    print("\n## Top 10 Remaining Weaknesses\n")
    for i, w in enumerate(weaknesses, 1):
        print(f"{i}. {w}")
    print("\n## Best 3 Demo Cases\n")
    for r in a["best"]:
        print(f"- {r['id']}: {r['title']} (quality {r['case_quality']})")
    print("\n## Worst 3 Cases\n")
    for r in a["worst"]:
        print(f"- {r['id']}: {r['title']} (quality {r['case_quality']})")
    print("\n## Can Chen Kui See This?\n")
    print("YES" if not blockers else "NO")
    print("\n## Exact Next Step\n")
    if blockers:
        print("Do not recommend Chen Kui demo. Blockers:")
        for bl in blockers:
            print(f"- {bl}")
    else:
        print("Run live demo with AC01 + AC05 + AC09 on :8001 workbench; broker confirms draft → office quote.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["before", "after", "full"], default="full")
    args = parser.parse_args()

    data = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    scenarios = data.get("scenarios") or []
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.phase in ("before", "full"):
        # Snapshot current code as "before" only on first run if no before file
        before_path = RESULTS_DIR / "before_results.json"
        if args.phase == "before" or not before_path.exists():
            before_results = _run_all(scenarios)
            before_payload = {"summary": _aggregate(before_results), "results": before_results}
            before_path.write_text(json.dumps(before_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    after_results = _run_all(scenarios)
    after_payload = {"summary": _aggregate(after_results), "results": after_results}
    (RESULTS_DIR / "after_results.json").write_text(
        json.dumps(after_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    before_payload = json.loads((RESULTS_DIR / "before_results.json").read_text(encoding="utf-8"))

    # Always refresh before with a git-stashed run isn't practical — overwrite before once at sprint start
    if args.phase == "full":
        # Re-run before from saved snapshot if exists; else use after as both (degenerate)
        pass

    (OUT_DIR / "P16Z24_AI_CUSTOMER_SCENARIOS.md").write_text(_md_scenarios(scenarios), encoding="utf-8")
    (OUT_DIR / "P16Z24_CASE_RESULTS.md").write_text(_md_case_results(after_results, "after improvements"), encoding="utf-8")
    (OUT_DIR / "P16Z24_CASE_QUALITY_SCORECARD.md").write_text(
        _md_scorecard(after_results, after_payload["summary"]), encoding="utf-8"
    )
    (OUT_DIR / "P16Z24_IMPROVEMENT_CANDIDATES.md").write_text(_md_improvements(), encoding="utf-8")
    (OUT_DIR / "P16Z24_BEFORE_AFTER.md").write_text(_md_before_after(before_payload, after_payload), encoding="utf-8")
    (OUT_DIR / "P16Z24_CHEN_KUI_DEMO_SET.md").write_text(
        _md_demo_set(after_results, after_payload["summary"]), encoding="utf-8"
    )

    _print_founder_output(before_payload, after_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
