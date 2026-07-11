#!/usr/bin/env python3
"""P19H-3h-1G — Append-first split-later simulated WeCom smoke (QA DB, no real callbacks)."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.demo_db_resolve import load_cloudrun_env_skip_db

load_cloudrun_env_skip_db()


os.environ["ENV"] = "prod"

from scripts.demo_db_resolve import apply_qa_postgres_env  # noqa: E402

apply_qa_postgres_env(for_write=True)

from services.fiqa_api.inbox_triage.case_store import (  # noqa: E402
    append_follow_up_message,
    bind_case_channel_identity,
    get_case_by_id,
    patch_case_known_facts,
    save_case,
    update_case_workbench_flags,
    update_claim_workflow_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.wecom.claim_basics import (  # noqa: E402
    ingest_claim_basics_message,
    ingest_claim_status_request,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.normalize import normalize_text_message

_NOW = datetime.now(timezone.utc)
_RESOLVER_MARKERS = ("【请确认】", "继续当前事故", "开始新的事故记录")
_START_MARKER = "【事故记录已开始 ✅】"
_STATUS_TITLE = "【当前状态】"


def _suffix() -> str:
    return datetime.now(timezone.utc).strftime("3h_af_smoke_%H%M%S")


def _evidence_path(suffix: str) -> Path:
    return REPO / "docs" / "evidence" / f"p19h3h_append_first_wecom_smoke_{suffix}.json"


def _text(content: str, *, ext: str, msg_id: str) -> dict:
    return normalize_text_message(
        {
            "msgid": msg_id,
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "text": {"content": content},
        }
    )


def _claim_stub() -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Claim guided workflow — collect accident basics.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "claim_phase": "claim_started",
    }


def _open_claim(ext: str, *, with_prior_story: bool = False, incomplete: bool = False) -> str:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = str(saved["case_id"])
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    update_case_workbench_flags(cid, is_test=True)
    ts = (_NOW - timedelta(hours=2)).isoformat()
    if with_prior_story:
        patch_case_known_facts(
            cid,
            {
                "accident_datetime": "7月7日上午",
                "accident_location": "Irvine Blvd",
                "accident_description": "被追尾",
            },
        )
        append_follow_up_message(
            cid,
            "7月7日上午在 Irvine Blvd 被追尾",
            {
                **_claim_stub(),
                "collected_fields": [
                    "accident_datetime",
                    "accident_location",
                    "accident_description",
                ],
            },
        )
        update_claim_workflow_state(
            cid,
            claim_phase="accident_basics_complete",
            guided_workflow_state="collecting_text",
        )
    elif incomplete:
        update_claim_workflow_state(
            cid,
            claim_phase="claim_started",
            guided_workflow_state="collecting_text",
        )
    case = get_case_by_id(cid) or saved
    case["created_at"] = ts
    case["updated_at"] = ts
    return cid


def _claim_count(ext: str) -> int:
    return sum(
        1
        for c in list_all_cases_for_read()
        if c.get("wecom_external_userid") == ext and c.get("service_lane") == SERVICE_LANE_CLAIM
    )


def run_smoke() -> dict:
    suffix = _suffix()
    checks: dict[str, dict] = {}

    ext1 = f"wm_afs1_{suffix}"
    cid1 = _open_claim(ext1, with_prior_story=True)
    before1 = _claim_count(ext1)
    r1 = ingest_claim_basics_message(
        _text("昨天在 Santa Ana 红绿灯被追尾，对方是 State Farm", ext=ext1, msg_id="af1"),
        classify_wecom_intent("昨天在 Santa Ana 红绿灯被追尾，对方是 State Farm"),
    )
    checks["1_narrative_append_no_collision"] = {
        "pass": r1.get("case_id") == cid1
        and r1.get("case_created") is False
        and r1.get("active_case_outcome") != "claim_collision_resolver"
        and not any(m in str(r1.get("reply_text") or "") for m in _RESOLVER_MARKERS)
        and _claim_count(ext1) == before1,
    }

    ext2 = f"wm_afs2_{suffix}"
    cid2 = _open_claim(ext2, with_prior_story=True)
    r2 = ingest_claim_basics_message(
        _text("补充一下，对方保险是 State Farm", ext=ext2, msg_id="af2"),
        classify_wecom_intent("补充一下，对方保险是 State Farm"),
    )
    checks["2_supplement_insurance_append"] = {
        "pass": r2.get("case_id") == cid2
        and r2.get("case_created") is False
        and r2.get("active_case_outcome") != "claim_collision_resolver",
    }

    ext3 = f"wm_afs3_{suffix}"
    _open_claim(ext3, with_prior_story=True)
    r3 = ingest_claim_basics_message(
        _text("这是另一个事故", ext=ext3, msg_id="af3"),
        classify_wecom_intent("这是另一个事故"),
    )
    checks["3_explicit_new_accident_confirm"] = {
        "pass": r3.get("active_case_outcome") == "claim_collision_resolver"
        and r3.get("case_created") is False
        and any(m in str(r3.get("reply_text") or "") for m in _RESOLVER_MARKERS),
    }

    ext4 = f"wm_afs4_{suffix}"
    cid4 = _open_claim(ext4, incomplete=True)
    r4 = ingest_claim_basics_message(
        _text("我要理赔", ext=ext4, msg_id="af4"),
        classify_wecom_intent("我要理赔"),
    )
    checks["4_repeat_woyao_claim_continue_not_collision"] = {
        "pass": r4.get("case_id") == cid4
        and r4.get("case_created") is False
        and r4.get("active_case_outcome") != "claim_collision_resolver",
    }

    ext5 = f"wm_afs5_{suffix}"
    cid5 = _open_claim(ext5, incomplete=True)
    r5 = ingest_claim_status_request(_text("进度", ext=ext5, msg_id="af5"), classify_wecom_intent("进度"))
    checks["5_status_card_h5_continue"] = {
        "pass": r5.get("case_id") == cid5
        and r5.get("active_case_outcome") == "claim_status_card"
        and _STATUS_TITLE in str(r5.get("reply_text") or "")
        and (r5.get("h5_task_link_masked") or "/task/claim/" in str(r5.get("reply_text") or "")),
    }

    ext6 = f"wm_afs6_{suffix}"
    r6 = ingest_claim_basics_message(
        _text("我要理赔", ext=ext6, msg_id="af6"),
        classify_wecom_intent("我要理赔"),
    )
    checks["6_fresh_start_h5_card"] = {
        "pass": r6.get("active_case_outcome") == "claim_start_card_sent"
        and _START_MARKER in str(r6.get("reply_text") or ""),
    }

    all_pass = all(c.get("pass") for c in checks.values())
    return {
        "script": "p19h3h_append_first_wecom_smoke.py",
        "sprint": "P19H-3h-1G",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suffix": suffix,
        "verdict": "PASS" if all_pass else "FAIL",
        "checks": checks,
    }


def main() -> int:
    result = run_smoke()
    out_path = _evidence_path(result["suffix"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": result["verdict"] == "PASS", "evidence": str(out_path)}, indent=2))
    if result["verdict"] != "PASS":
        print(json.dumps(result.get("checks"), indent=2, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
