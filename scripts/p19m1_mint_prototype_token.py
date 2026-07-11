#!/usr/bin/env python3
"""Mint a Claim intake form token for P19M-1 mini program prototype QA."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    patch_case_known_facts,
    save_case,
    update_case_workbench_flags,
)
from services.fiqa_api.inbox_triage.h5_task_link import mint_h5_claim_intake_form_link
from services.fiqa_api.inbox_triage.h5_task_token import issue_h5_intake_form_token
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

QA_LABEL_PREFIX = "P19M1A-DEVTOOLS-E2E"


def _utc_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")


def _bootstrap_json_local() -> None:
    if os.getenv("UNIFIED_INTAKE_CASES_PATH"):
        return
    tmp = tempfile.mkdtemp(prefix="p19m1_mp_")
    path = Path(tmp) / "cases.json"
    path.write_text("[]", encoding="utf-8")
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_READS", None)
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.setdefault("UNIFIED_INTAKE_JSON_CASE_WRITES", "1")


def _mask_token(token: str) -> str:
    t = (token or "").strip()
    if len(t) <= 16:
        return "h5t1_…"
    return f"{t[:8]}…{t[-6:]}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Mint P19M-1 prototype Claim intake token")
    parser.add_argument("--api-base", default=os.getenv("P19M1_API_BASE", "http://127.0.0.1:8001"))
    parser.add_argument("--frontend-base", default="https://example.test")
    parser.add_argument("--label", default="", help="Optional QA label suffix")
    parser.add_argument(
        "--cloud-sql",
        action="store_true",
        help="Seed/read QA GCP Cloud SQL (same DB as Cloud Run and run_demo_local.sh)",
    )
    parser.add_argument(
        "--json-local",
        action="store_true",
        help="Isolated temp JSON store (dev only — NOT prototype QA parity)",
    )
    parser.add_argument(
        "--qa-db",
        action="store_true",
        help="Deprecated alias for --cloud-sql",
    )
    args = parser.parse_args()
    if args.qa_db:
        args.cloud_sql = True
    if not args.cloud_sql and not args.json_local:
        parser.error("Specify --cloud-sql (QA SSOT) or --json-local (isolated dev only)")
    if args.cloud_sql and args.json_local:
        parser.error("Cannot combine --cloud-sql and --json-local")
    use_cloud_sql = args.cloud_sql

    if use_cloud_sql:
        from scripts.demo_db_resolve import bootstrap_prototype_cloud_sql_env

        ident = bootstrap_prototype_cloud_sql_env()
        storage_mode = f"cloud_sql ({ident.masked()})"
    else:
        _bootstrap_json_local()
        storage_mode = os.getenv("UNIFIED_INTAKE_CASES_PATH", "json-local")

    tag = (args.label or _utc_tag()).strip()
    qa_label = f"{QA_LABEL_PREFIX}-{tag}"
    ext = f"wm_p19m1a_{tag.replace('-', '_')}"

    saved = save_case(
        f"我要理赔 {qa_label}",
        {
            "issue_category": "claim_intake",
            "urgency": "high",
            "manual_followup_needed": True,
            "broker_next_step": "Collect claim basics via mini program prototype.",
            "client_prep": "",
            "client_reply_draft": "",
            "handoff_ready": False,
            "claim_phase": "accident_basics_in_progress",
        },
        service_lane=SERVICE_LANE_CLAIM,
    )
    case_id = str(saved.get("case_id") or "")
    bind_case_channel_identity(case_id, wecom_external_userid=ext)
    update_case_workbench_flags(case_id, is_test=True)
    patch_case_known_facts(case_id, {"qa_label": qa_label})

    token = issue_h5_intake_form_token(case_id=case_id, lane="claim", external_userid=ext)
    link = mint_h5_claim_intake_form_link(
        case_id=case_id,
        base_url=args.frontend_base.rstrip("/"),
        external_userid=ext,
    )

    out = {
        "qa_label": qa_label,
        "case_id": case_id,
        "masked_token": _mask_token(token),
        "token": token,
        "h5_link_prefix": link[:48] + "…",
        "devtools_launch_query": f"token={token}",
        "api_intake_url": f"{args.api_base.rstrip('/')}/api/h5/tasks/{token}/intake",
        "config_local_hint": f'devTaskToken: "{token}" in miniapp/config.local.ts',
        "storage": storage_mode,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
