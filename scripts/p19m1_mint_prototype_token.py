#!/usr/bin/env python3
"""Mint a Claim intake form token for P19M-1 mini program prototype QA.

Usage:
  PYTHONPATH=. python3 scripts/p19m1_mint_prototype_token.py
  PYTHONPATH=. python3 scripts/p19m1_mint_prototype_token.py --api-base http://127.0.0.1:8001

Prints h5t1 token and DevTools launch query. Does not log secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from services.fiqa_api.inbox_triage.case_store import save_case
from services.fiqa_api.inbox_triage.h5_task_link import mint_h5_claim_intake_form_link
from services.fiqa_api.inbox_triage.h5_task_token import issue_h5_intake_form_token
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


def _bootstrap_case_storage() -> None:
    if os.getenv("UNIFIED_INTAKE_CASE_STORAGE_PATH"):
        return
    tmp = tempfile.mkdtemp(prefix="p19m1_mp_")
    path = Path(tmp) / "cases.json"
    path.write_text("[]", encoding="utf-8")
    os.environ["UNIFIED_INTAKE_CASE_STORAGE_PATH"] = str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Mint P19M-1 prototype Claim intake token")
    parser.add_argument("--api-base", default=os.getenv("P19M1_API_BASE", "http://127.0.0.1:8001"))
    parser.add_argument("--frontend-base", default="https://example.test")
    args = parser.parse_args()

    if not os.getenv("H5_TASK_TOKEN_SECRET"):
        os.environ.setdefault("H5_TASK_TOKEN_SECRET", "dev-prototype-secret-change-me")

    _bootstrap_case_storage()

    saved = save_case(
        "我要理赔",
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
    token = issue_h5_intake_form_token(case_id=case_id, lane="claim")
    link = mint_h5_claim_intake_form_link(
        case_id=case_id,
        base_url=args.frontend_base.rstrip("/"),
    )

    out = {
        "case_id": case_id,
        "token_prefix": token[:12] + "…",
        "token": token,
        "h5_link_prefix": link[:48] + "…",
        "devtools_launch_query": f"token={token}",
        "api_intake_url": f"{args.api_base.rstrip('/')}/api/h5/tasks/{token}/intake",
        "miniapp_config_hint": f'devTaskToken: "{token}"',
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
