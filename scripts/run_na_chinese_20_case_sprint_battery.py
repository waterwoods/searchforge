#!/usr/bin/env python3
"""
NA-Chinese Add-Car 18-case sprint battery (rule path).

Usage:
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_na_chinese_20_case_sprint_battery.py
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_na_chinese_20_case_sprint_battery.py --persist-pg \\
    --cases-json /tmp/sprint_cases.json

With --persist-pg: set SERVICE_RECORD_DATABASE_URL + UNIFIED_INTAKE_PG_DUAL_WRITE=1 and UNIFIED_INTAKE_CASES_PATH.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

os.environ.setdefault("LLM_GENERATION_ENABLED", "0")

from services.fiqa_api.inbox_triage.case_store import append_follow_up_message, save_case  # noqa: E402
from services.fiqa_api.inbox_triage.triage import triage_conversation, triage_for_append  # noqa: E402

CLIENT = "chen_kui"

# (id, category_label, turns, mode) — turns: list of customer strings; mode "single" | "append_second"
SCENARIOS: list[tuple[str, str, list[str], str]] = [
    ("S01", "direct_happy_path", ["我要加一台2024 Tesla Model 3，95131，明天提车，我自己开"], "single"),
    ("S02", "incomplete_no_zip", ["想加一辆新车quote，2024 Honda Accord，下周提车，我本人开"], "single"),
    ("S03", "wechat_already_sent", ["加2024 Camry，95131，周五提车。VIN我微信发过了，你看下。"], "single"),
    ("S04", "vin_not_ready", ["加车，2025 BMW X5，92705，我开。VIN车行说还要等两天才能给我。"], "single"),
    ("S05", "spouse_second_driver", ["加一台RAV4，92618，主要我开，我老婆有时候也会开，quote怎么报？"], "single"),
    ("S06", "correction_pickup_day", ["加BMW X5，92705，我开。哦不对，不是明天提，是这个周五提车。"], "single"),
    ("S07", "too_expensive_reshop", ["上次报的价太贵了，我想换一家company看看，coverage也想调低一点，zip还是95131。"], "single"),
    ("S08", "what_still_needed_add_car", ["还想加那台Camry的quote，现在还缺什么？"], "single"),
    ("S09", "one_line_minimal", ["想加车"], "single"),
    ("S10", "mixed_zh_en", ["Add new car quote: 2024 Tesla Model Y, zip 95131, pick up this Friday, I drive."], "single"),
    ("S11", "append_same_record", ["2024 Prius，95132，周六提车，我本人开。"], "append_second"),
    ("S12", "material_followup", ["对了，registration照片刚才又发了一次邮箱，你收到了吗？"], "single"),
    ("S13", "borderline_quote_readiness", ["加2020 Corolla，95131，下周提车，VIN还没拿到，可以先报吗？"], "single"),
    ("S14", "multi_turn_clarification", ["我想加车。"], "multi"),
    ("S15", "almost_ready_last_field", ["2024 Lexus RX，94506，周五提车，我本人开，还差phone给你：4085551212"], "single"),
    ("S16", "dealer_finance_lien", ["加2024 F-150，95350，下周提车，dealer finance，我本人开。"], "single"),
    ("S17", "policyholder_spouse_car", ["帮我老婆那台塞纳也报一下价，她在开，zip 91789。"], "single"),
    ("S18", "noise_polite_office_check", ["我明天提Model 3，要不要先发你行驶证？95131，我本人开。"], "single"),
]

MULTI_TURN_BODY: dict[str, list[str]] = {
    "S14": [
        "我想加车。",
        "2024 Mazda CX-5，95123，这周日提车，我一个人开。",
    ],
}


def _run_triage(turns: list[str]) -> dict:
    if len(turns) == 1:
        return triage_conversation(turns[0], [], client_id=CLIENT)
    conv: list[dict[str, str]] = []
    for i, t in enumerate(turns[:-1]):
        conv.append({"role": "customer", "text": t})
    return triage_conversation(turns[-1], conv, client_id=CLIENT)


def _snapshot(r: dict) -> dict:
    return {
        "issue_category": r.get("issue_category"),
        "quote_ready_status": r.get("quote_ready_status"),
        "collected_fields": r.get("collected_fields"),
        "still_needed_fields": r.get("still_needed_fields"),
        "handoff_ready": r.get("handoff_ready"),
        "lifecycle_status": r.get("lifecycle_status"),
        "broker_next_step": (r.get("broker_next_step") or "")[:200],
        "triage_path": r.get("triage_path"),
        "collection_stage": r.get("collection_stage"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--persist-pg", action="store_true", help="save_case / append to JSON + dual-write")
    ap.add_argument("--cases-json", default="", help="UNIFIED_INTAKE_CASES_PATH when persisting")
    args = ap.parse_args()

    if args.persist_pg:
        path = (args.cases_json or "").strip() or str(REPO / "data" / "sprint_na_cases.json")
        os.environ["UNIFIED_INTAKE_CASES_PATH"] = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        if Path(path).exists():
            Path(path).write_text('{"cases": []}\n', encoding="utf-8")

    out: list[dict] = []

    for sid, cat, turns_template, mode in SCENARIOS:
        turns = list(MULTI_TURN_BODY.get(sid, turns_template))
        if mode == "append_second":
            first_r = triage_conversation(turns[0], [], client_id=CLIENT)
            first_text = turns[0].strip()
            second = "补充：VIN是1HGBH41JXMN109186。"
            existing = f"[客户] {first_text}"
            append_r = triage_for_append(existing, second, client_id=CLIENT)
            row = {
                "id": sid,
                "category": cat,
                "mode": mode,
                "first": _snapshot(first_r),
                "append": _snapshot(append_r),
            }
            if args.persist_pg:
                c1 = save_case(first_text, first_r, client_id=CLIENT)
                append_follow_up_message(c1["case_id"], second, append_r, client_id=CLIENT)
                row["case_id"] = c1["case_id"]
            out.append(row)
            continue

        if mode == "multi":
            r = _run_triage(turns)
            row = {"id": sid, "category": cat, "mode": "multi_turn", "turns": len(turns), "result": _snapshot(r)}
            if args.persist_pg:
                merged = "\n\n".join(f"[客户] {t.strip()}" for t in turns)
                c = save_case(merged, r, client_id=CLIENT)
                row["case_id"] = c["case_id"]
            out.append(row)
            continue

        r = triage_conversation(turns[0], [], client_id=CLIENT)
        row = {"id": sid, "category": cat, "mode": "single", "result": _snapshot(r)}
        if args.persist_pg:
            c = save_case(turns[0].strip(), r, client_id=CLIENT)
            row["case_id"] = c["case_id"]
        out.append(row)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
