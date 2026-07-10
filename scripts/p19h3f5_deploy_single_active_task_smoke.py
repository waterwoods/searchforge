#!/usr/bin/env python3
"""P19H-3f-5 deploy smoke — Single Active Task per Lane (QA Cloud SQL + API)."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

_env = REPO / ".env.cloudrun"
if _env.exists():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

os.environ["ENV"] = "prod"

from scripts.demo_db_resolve import apply_qa_postgres_env  # noqa: E402

apply_qa_postgres_env(for_write=True)

from services.fiqa_api.inbox_triage.case_store import (  # noqa: E402
    bind_case_channel_identity,
    get_case_by_id,
    patch_case_known_facts,
    save_case,
    update_case_workbench_flags,
    update_claim_workflow_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_collision_choice,
    ingest_claim_status_request,
)
from services.fiqa_api.wecom.claim_end_card import try_send_claim_end_card
from services.fiqa_api.wecom.claim_state import CLAIM_PHASE_BROKER_REVIEW, SERVICE_LANE_CLAIM
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message

FRAME = "━━━━━━━━━━━━"
START_TITLE = "【事故记录已开始 ✅】"
STATUS_TITLE = "【当前状态】"
CONFIRM_TITLE = "【请确认】"
END_TITLE = "【陈总已确认 ✅】"


def _suffix() -> str:
    return datetime.now(timezone.utc).strftime("3f5_smoke_%H%M%S")


def _tag(case_id: str) -> None:
    update_case_workbench_flags(case_id, is_test=True)


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
        "broker_next_step": "Collect basics.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "claim_phase": "claim_started",
    }


def _open_claim(ext: str, *, complete: bool = False) -> str:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = str(saved["case_id"])
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    _tag(cid)
    if complete:
        patch_case_known_facts(
            cid,
            {
                "accident_datetime": "7月8日",
                "accident_location": "Santa Ana",
                "accident_description": "追尾",
            },
        )
        update_claim_workflow_state(cid, claim_phase="accident_basics_complete")
    return cid


def _dl(cfg, **kwargs):
    return WeComMediaDownloadResult(content=b"\xff\xd8\xff", content_type="image/jpeg", filename="p.jpg")


def _up(**kwargs):
    return {"storage_uri": "gs://smoke/x.jpg", "mime_type": "image/jpeg", "size_bytes": 3}


def run_smoke() -> dict:
    suffix = _suffix()
    cfg = load_wecom_kf_config()
    checks: dict[str, dict] = {}

    ext1 = f"wm_3f5s1_{suffix}"
    r1 = ingest_claim_basics_message(_text("我要理赔", ext=ext1, msg_id="s1"), classify_wecom_intent("我要理赔"))
    checks["1_start_card_framed"] = {
        "pass": FRAME in str(r1.get("reply_text") or "") and START_TITLE in str(r1.get("reply_text") or ""),
    }

    ext2 = f"wm_3f5s2_{suffix}"
    cid2 = _open_claim(ext2, complete=True)
    r2 = ingest_claim_status_request(_text("进度", ext=ext2, msg_id="s2"), classify_wecom_intent("进度"))
    checks["2_status_card"] = {
        "pass": r2.get("case_id") == cid2 and STATUS_TITLE in str(r2.get("reply_text") or ""),
    }

    ext3 = f"wm_3f5s3_{suffix}"
    _open_claim(ext3, complete=True)
    newest3 = _open_claim(ext3, complete=True)
    r3 = ingest_claim_basics_message(
        _text("对方保险是 AAA", ext=ext3, msg_id="s3"),
        classify_wecom_intent("对方保险是 AAA"),
    )
    checks["3_multi_open_ordinary_append"] = {
        "pass": r3.get("case_id") == newest3 and r3.get("active_case_outcome") != "claim_collision_resolver",
    }

    ext4 = f"wm_3f5s4_{suffix}"
    _open_claim(ext4, complete=True)
    _open_claim(ext4, complete=True)
    r4 = ingest_claim_basics_message(_text("新的事故", ext=ext4, msg_id="s4"), classify_wecom_intent("新的事故"))
    checks["4_multi_open_new_accident_confirm"] = {
        "pass": r4.get("active_case_outcome") == "claim_collision_resolver"
        and CONFIRM_TITLE in str(r4.get("reply_text") or ""),
    }

    ext5 = f"wm_3f5s5_{suffix}"
    _open_claim(ext5, complete=True)
    ingest_claim_basics_message(_text("新的事故", ext=ext5, msg_id="s5a"), classify_wecom_intent("新的事故"))
    before5 = sum(1 for c in list_all_cases_for_read() if c.get("wecom_external_userid") == ext5)
    r5 = ingest_claim_collision_choice(_text("2", ext=ext5, msg_id="s5b"))
    checks["5_confirm_2_new_start"] = {
        "pass": r5.get("active_case_outcome") == "claim_start_card_sent"
        and sum(1 for c in list_all_cases_for_read() if c.get("wecom_external_userid") == ext5) == before5 + 1,
    }

    ext6 = f"wm_3f5s6_{suffix}"
    r6 = ingest_wecom_media_message(
        normalize_media_message(
            {
                "msgid": f"s6_{suffix}",
                "open_kfid": "wktest001",
                "external_userid": ext6,
                "origin": 3,
                "msgtype": "image",
                "image": {"media_id": "mid"},
            }
        ),
        cfg,
        download_fn=_dl,
        upload_fn=_up,
    )
    checks["6_random_photo_hidden"] = {
        "pass": r6.get("active_case_outcome") == "media_unassigned"
        and not any(c.get("service_lane") == SERVICE_LANE_CLAIM for c in list_all_cases_for_read() if c.get("wecom_external_userid") == ext6),
    }

    ext7 = f"wm_3f5s7_{suffix}"
    add_car = save_case(
        "add car",
        {"issue_category": "add_car_quote", "urgency": "medium", "manual_followup_needed": True, "broker_next_step": "x", "client_prep": "", "client_reply_draft": "", "handoff_ready": False},
        service_lane=SERVICE_LANE_ADD_CAR,
    )
    bind_case_channel_identity(str(add_car["case_id"]), wecom_external_userid=ext7)
    r7 = ingest_claim_basics_message(_text("我要理赔", ext=ext7, msg_id="s7"), classify_wecom_intent("我要理赔"))
    checks["7_add_car_lane_switch"] = {"pass": r7.get("active_case_outcome") == "claim_lane_switch_prompt"}

    ext8 = f"wm_3f5s8_{suffix}"
    cid8 = _open_claim(ext8, complete=False)
    update_claim_workflow_state(cid8, claim_phase=CLAIM_PHASE_BROKER_REVIEW)
    from services.fiqa_api.inbox_triage.case_store import mark_claim_broker_done

    mark_claim_broker_done(cid8)
    end8 = try_send_claim_end_card(cid8)
    checks["8_broker_done_end_card"] = {
        "pass": END_TITLE in str(end8.get("end_card_preview") or ""),
    }

    all_pass = all(c.get("pass") for c in checks.values())
    return {
        "sprint": "P19H-3f-5",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": "PASS" if all_pass else "FAIL",
        "checks": checks,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
