#!/usr/bin/env python3
"""P20 Founder QA — create a fresh VIN-only MVP case on QA Cloud SQL.

Creates: New Claim → VIN draft → Send Request (progress 0/1, QR ready).
Does not reuse prior experimental cases.

Usage:
  PYTHONPATH=. python3 scripts/p20_founder_qa_vin_mvp_prep.py --qa
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.demo_db_resolve import apply_qa_postgres_env, load_cloudrun_env_skip_db

WORKBENCH_URL = "https://ui-smoky-beta.vercel.app/workbench/document-intake"


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ids(prefix: str) -> tuple[str, str]:
    tail = uuid4().hex[:12]
    return f"{prefix}_{tail}", f"idem_{prefix}_{tail}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa", action="store_true", help="Use QA Cloud SQL SSOT")
    parser.add_argument("--out", default="/tmp/p20_founder_qa_vin_mvp_handoff.json")
    args = parser.parse_args()
    if not args.qa:
        print("Only --qa is supported for Founder QA prep.", file=sys.stderr)
        return 2

    load_cloudrun_env_skip_db()
    os.environ["ENV"] = "prod"
    ident = apply_qa_postgres_env(for_write=True)
    print(f"[INFO] QA Postgres: {ident.masked()}")

    from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
        default_case_intake_service,
    )
    from services.fiqa_api.inbox_triage.p20_send_request_command_service import (
        default_send_request_service,
    )

    intake = default_case_intake_service()
    send = default_send_request_service()
    broker_id = "office:founder_qa"
    office_id = "founder_qa"
    tenant_id = "chen_kui"
    stamp = _stamp()

    cmd_create, idem_create = _ids("cmd_create")
    created = intake.create_claim(
        broker_id=broker_id,
        office_id=office_id,
        tenant_id=tenant_id,
        command_id=cmd_create,
        idempotency_key=idem_create,
        inputs={
            "is_test": True,
            "title": f"P20 Founder QA VIN MVP {stamp}",
            "customer_name": "Founder QA Customer",
            "contact_note": "VIN-only MVP — do not reuse for other flows",
            "known_facts": {
                "accident_description": "QA fixture: minor rear-end at stoplight (not real PII).",
            },
        },
    )
    if str(created.get("outcome") or "") not in {"accepted", "replayed"}:
        print(json.dumps(created, indent=2), file=sys.stderr)
        return 1

    case_id = str(created.get("case_id") or created.get("broker_projection", {}).get("case_id") or "")
    if not case_id:
        print("create_claim missing case_id", file=sys.stderr)
        return 1

    agg_ver = int(created["broker_projection"]["aggregate_version"])
    checklist = created["broker_projection"].get("missing_information_checklist") or []
    vin_row = next((r for r in checklist if r.get("field_key") == "vin"), None)
    if not vin_row or str(vin_row.get("status") or "") != "missing":
        print("Expected VIN to be the only actionable missing field", file=sys.stderr)
        return 1

    cmd_draft, idem_draft = _ids("cmd_draft")
    draft_result = intake.save_request_draft(
        case_id=case_id,
        broker_id=broker_id,
        command_id=cmd_draft,
        idempotency_key=idem_draft,
        expected_case_version=agg_ver,
        items=[
            {
                "field_key": "vin",
                "item_type": "vin",
                "label": "Vehicle VIN",
                "instructions": "Please enter the 17-character VIN from your vehicle registration.",
                "required": True,
                "position": 1,
                "selected": True,
                "request_mode": "request_missing",
            }
        ],
    )
    if str(draft_result.get("outcome") or "") not in {"accepted", "replayed"}:
        print(json.dumps(draft_result, indent=2), file=sys.stderr)
        return 1

    draft_id = str(draft_result["broker_projection"]["request_draft"]["draft_id"])
    agg_ver2 = int(draft_result["broker_projection"]["aggregate_version"])

    cmd_send, idem_send = _ids("cmd_send")
    sent = send.send_request(
        case_id=case_id,
        broker_id=broker_id,
        request_draft_id=draft_id,
        expected_case_version=agg_ver2,
        command_id=cmd_send,
        idempotency_key=idem_send,
        office_id=office_id,
        tenant_id=tenant_id,
    )
    if str(sent.get("outcome") or "") not in {"accepted", "replayed"}:
        print(json.dumps(sent, indent=2), file=sys.stderr)
        return 1

    access = sent.get("customer_access") or {}
    slice1 = sent.get("slice1_projection") or {}
    progress = access.get("progress") or slice1.get("open_request", {}).get("progress") or {}
    next_action = (slice1.get("customer_next_action") or {}) if slice1 else {}
    handoff = {
        "verdict": "READY_FOR_FOUNDER_QA",
        "created_at_utc": stamp,
        "case_id": case_id,
        "draft_id": draft_id,
        "workbench_url": WORKBENCH_URL,
        "title": f"P20 Founder QA VIN MVP {stamp}",
        "broker_expectation": {
            "simple_status": access.get("simple_status"),
            "progress_satisfied": progress.get("satisfied_count", progress.get("satisfied")),
            "progress_total": progress.get("total_count", progress.get("total")),
            "requested_item": "VIN",
            "qr_ready": bool(access.get("qr_payload") or access.get("copy_link")),
        },
        "customer_expectation": {
            "required_input": next_action.get("required_input"),
            "title": next_action.get("title") or "补充车辆 VIN",
            "launch_url_host": (access.get("launch_url") or "").split("/task/")[0],
        },
        "copy_link": access.get("copy_link"),
        "qr_payload": access.get("qr_payload"),
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(handoff, indent=2))
    print(f"[OK] Handoff written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
