#!/usr/bin/env python3
"""
ADD-CAR high-risk language + Postgres + Stage-2 signal sprint battery (rule path).

Usage:
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_high_risk_add_car_pg_stage2_sprint_battery.py
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_high_risk_add_car_pg_stage2_sprint_battery.py --persist-pg \\
    --cases-json /tmp/hr_sprint_cases.json

Env for --persist-pg: SERVICE_RECORD_DATABASE_URL, UNIFIED_INTAKE_PG_DUAL_WRITE=1, UNIFIED_INTAKE_CASES_PATH via --cases-json.
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

# 16 scenarios: (id, family_label, turns, mode)
SCENARIOS: list[tuple[str, str, list[str], str]] = [
    ("H01", "direct_strong", ["我要加一台2024 Tesla Model 3，95131，明天提车，我自己开"], "single"),
    ("H02", "direct_strong", ["加2024 Camry，95131，周五提车。VIN我微信发过了，你看下。"], "single"),
    ("H03", "direct_strong", ["加车，2025 BMW X5，92705，我开。VIN车行说还要等两天才能给我。"], "single"),
    ("H04", "weak_followup", ["还想加那台Camry的quote，现在还缺什么？"], "single"),
    ("H05", "weak_followup", ["材料我微信发过了，还缺什么？"], "single"),
    ("H06", "weak_followup", ["对了，registration照片刚才又发了一次邮箱，你收到了吗？"], "single"),
    ("H07", "weak_followup", ["VIN我发你微信了，还要补什么吗？"], "single"),
    ("H08", "spouse_household", ["加一台RAV4，92618，主要我开，我老婆有时候也会开，quote怎么报？"], "single"),
    ("H09", "spouse_household", ["帮我老婆那台塞纳也报一下价，她在开，zip 91789。"], "single"),
    ("H10", "spouse_household", ["家里还有一台CR-V也要一起报，95120，我跟我老婆都会开。"], "single"),
    ("H11", "reshop_coverage", ["上次报的价太贵了，我想换一家company看看，coverage也想调低一点，zip还是95131。"], "single"),
    ("H12", "reshop_coverage", ["保费太高想换公司，zip 94506，还是那台2023 Accord。"], "single"),
    ("H13", "multi_turn", ["我想加车。", "2024 Mazda CX-5，95123，这周日提车，我一个人开。"], "multi"),
    ("H14", "append_vin", ["2024 Prius，95132，周六提车，我本人开。"], "append_second"),
    ("H15", "almost_quote_prep", ["2024 Lexus RX，94506，周五提车，我本人开，还差phone给你：4085551212"], "single"),
    ("H16", "minimal_opener", ["想加车"], "single"),
]

def _run_triage(turns: list[str]) -> dict:
    if len(turns) == 1:
        return triage_conversation(turns[0], [], client_id=CLIENT)
    conv: list[dict[str, str]] = []
    for t in turns[:-1]:
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
        "broker_next_step": (r.get("broker_next_step") or "")[:220],
        "collection_stage": r.get("collection_stage"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--persist-pg", action="store_true")
    ap.add_argument("--cases-json", default="", help="path for UNIFIED_INTAKE_CASES_PATH")
    args = ap.parse_args()

    if args.persist_pg:
        path = (args.cases_json or "").strip() or str(REPO / "data" / "hr_sprint_cases.json")
        os.environ["UNIFIED_INTAKE_CASES_PATH"] = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text('{"cases": []}\n', encoding="utf-8")

    os.environ.setdefault("UNIFIED_INTAKE_PG_DUAL_WRITE", "1" if args.persist_pg else "0")

    out: list[dict] = []

    for sid, fam, turns_template, mode in SCENARIOS:
        turns = list(turns_template)
        if mode == "append_second":
            first_r = triage_conversation(turns[0], [], client_id=CLIENT)
            first_text = turns[0].strip()
            second = "补充：VIN是1HGBH41JXMN109186。"
            existing = f"[客户] {first_text}"
            append_r = triage_for_append(existing, second, client_id=CLIENT)
            row: dict = {
                "id": sid,
                "family": fam,
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
            row = {"id": sid, "family": fam, "mode": "multi_turn", "turns": len(turns), "result": _snapshot(r)}
            if args.persist_pg:
                merged = "\n\n".join(f"[客户] {t.strip()}" for t in turns)
                c = save_case(merged, r, client_id=CLIENT)
                row["case_id"] = c["case_id"]
            out.append(row)
            continue

        r = triage_conversation(turns[0], [], client_id=CLIENT)
        row = {"id": sid, "family": fam, "mode": "single", "result": _snapshot(r)}
        if args.persist_pg:
            c = save_case(turns[0].strip(), r, client_id=CLIENT)
            row["case_id"] = c["case_id"]
        out.append(row)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
