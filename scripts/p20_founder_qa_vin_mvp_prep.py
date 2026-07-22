#!/usr/bin/env python3
"""P20 Founder QA — create a fresh VIN Request More case on QA Cloud SQL.

Business Contract: Start Claim seeds accident Must Have facts first.
Then broker uses Request More for VIN (not VIN-first intake).

Creates: New Claim (accident facts) → VIN draft → Send Request (progress 0/1, QR ready).
Does not reuse prior experimental cases.

Usage:
  PYTHONPATH=. python3 scripts/p20_founder_qa_vin_mvp_prep.py --qa --via-api
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

# Cloud QA document-intake (same host as Golden WORKBENCH_QA_URL). Not Production smoky-beta.
WORKBENCH_URL = (
    "https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/document-intake"
)
API_BASE = os.environ.get("CHEN_KUI_CLOUD_API_URL", "https://fiqa-api-g7zatxrycq-uw.a.run.app")


def _prep_via_live_api(out_path: str) -> int:
    import urllib.request

    api_key = (os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY") or "").strip()
    if not api_key:
        print("UNIFIED_INTAKE_INTAKE_API_KEY required for --via-api", file=sys.stderr)
        return 2

    headers = {"Content-Type": "application/json", "X-Unified-Intake-Api-Key": api_key}
    stamp = _stamp()
    tail = uuid4().hex[:12]

    def post(path: str, body: dict) -> dict:
        req = urllib.request.Request(
            f"{API_BASE.rstrip('/')}{path}",
            data=json.dumps(body).encode(),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode())

    def get(path: str) -> dict:
        req = urllib.request.Request(
            f"{API_BASE.rstrip('/')}{path}",
            headers={"X-Unified-Intake-Api-Key": api_key},
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode())

    created = post(
        "/api/inbox/claims",
        {
            "command_id": f"cmd_api_create_{tail}",
            "idempotency_key": f"idem_api_create_{tail}",
            "is_test": True,
            "title": f"P20 Founder QA VIN Request More {stamp}",
            "customer_name": "Founder QA Customer",
            "contact_note": "Accident Must Have seeded; VIN via Request More",
            "known_facts": {
                "accident_description": "QA fixture rear-end at stoplight.",
                "accident_datetime": "2026-07-15 morning",
                "accident_location": "Irvine Blvd test intersection",
                "injury_status": "no",
                "anyone_injured": "no",
            },
        },
    )
    case_id = str(created.get("case_id") or "")
    agg = int(created["broker_projection"]["aggregate_version"])
    draft = post(
        f"/api/inbox/cases/{case_id}/request-draft",
        {
            "command_id": f"cmd_api_draft_{tail}",
            "idempotency_key": f"idem_api_draft_{tail}",
            "expected_case_version": agg,
            "items": [
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
        },
    )
    draft_id = str(draft["broker_projection"]["request_draft"]["draft_id"])
    agg2 = int(draft["broker_projection"]["aggregate_version"])
    sent = post(
        f"/api/inbox/cases/{case_id}/send-request",
        {
            "command_id": f"cmd_api_send_{tail}",
            "idempotency_key": f"idem_api_send_{tail}",
            "expected_case_version": agg2,
            "request_draft_id": draft_id,
        },
    )
    access = sent.get("customer_access") or {}
    token = str(access.get("copy_link") or "").rsplit("/", 1)[-1]
    h5 = get(f"/api/h5/tasks/{token}/intake") if token else {}
    na = (h5.get("slice1_projection") or {}).get("customer_next_action") or {}
    handoff = {
        "verdict": "READY_FOR_FOUNDER_QA",
        "created_at_utc": stamp,
        "case_id": case_id,
        "draft_id": draft_id,
        "workbench_url": WORKBENCH_URL,
        "title": f"P20 Founder QA VIN MVP {stamp}",
        "broker_expectation": {
            "simple_status": access.get("simple_status"),
            "progress_satisfied": (access.get("progress") or {}).get("satisfied_count"),
            "progress_total": (access.get("progress") or {}).get("total_count"),
            "requested_item": "VIN",
            "qr_ready": bool(access.get("qr_payload") or access.get("copy_link")),
        },
        "customer_expectation": {
            "required_input": na.get("required_input"),
            "title": na.get("title") or "补充车辆 VIN",
            "h5_intake_ok": na.get("required_input") == "vin",
        },
        "copy_link": access.get("copy_link"),
        "qr_payload": access.get("qr_payload"),
    }
    Path(out_path).write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(handoff, indent=2))
    print(f"[OK] Handoff written: {out_path}")
    return 0 if handoff["customer_expectation"]["h5_intake_ok"] else 1


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ids(prefix: str) -> tuple[str, str]:
    tail = uuid4().hex[:12]
    return f"{prefix}_{tail}", f"idem_{prefix}_{tail}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa", action="store_true", help="Use QA Cloud SQL SSOT")
    parser.add_argument(
        "--via-api",
        action="store_true",
        help="Issue customer access via live Cloud Run (required for valid H5 tokens)",
    )
    parser.add_argument("--out", default="/tmp/p20_founder_qa_vin_mvp_handoff.json")
    args = parser.parse_args()
    if not args.qa:
        print("Only --qa is supported for Founder QA prep.", file=sys.stderr)
        return 2

    load_cloudrun_env_skip_db()
    os.environ["ENV"] = "prod"

    if args.via_api:
        return _prep_via_live_api(args.out)

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
            "title": f"P20 Founder QA VIN Request More {stamp}",
            "customer_name": "Founder QA Customer",
            "contact_note": "Accident Must Have seeded; VIN via Request More",
            "known_facts": {
                "accident_description": "QA fixture: minor rear-end at stoplight (not real PII).",
                "accident_datetime": "2026-07-15 morning",
                "accident_location": "Irvine Blvd test intersection",
                "injury_status": "no",
                "anyone_injured": "no",
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
        print("Expected VIN as Request More candidate (missing)", file=sys.stderr)
        return 1
    if str(vin_row.get("business_class") or "") != "request_more":
        print("Expected VIN business_class=request_more", file=sys.stderr)
        return 1
    must_have_ok = all(
        next((r for r in checklist if r.get("field_key") == key), {}).get("status")
        != "missing"
        for key in ("accident_description", "accident_datetime", "accident_location", "injury_status")
    )
    if not must_have_ok:
        print("Expected accident Must Have facts to be seeded", file=sys.stderr)
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
