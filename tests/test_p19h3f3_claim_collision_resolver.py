"""P19H-3f-3 — Claim Collision Resolver tests."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    append_follow_up_message,
    bind_case_channel_identity,
    get_case_by_id,
    patch_case_known_facts,
    save_case,
    update_claim_workflow_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_collision_choice,
    ingest_claim_lane_switch_choice,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_BROKER_DONE,
    CLAIM_PHASE_BROKER_REVIEW,
    SERVICE_LANE_CLAIM,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

_NOW = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
_START_MARKER = "【事故记录已开始 ✅】"
_RESOLVER_MARKERS = ("未完成的事故记录", "继续上一个事故", "开始新的事故记录")
_ACCIDENT_NARRATIVE = "昨天7月8号，我们在 Santa Ana 红绿灯停下来，后车没停撞了我们。"


@pytest.fixture(autouse=True)
def _json_store():
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    os.environ["WECOM_KF_TOKEN"] = "tok"
    os.environ["WECOM_KF_ENCODING_AES_KEY"] = "a" * 43
    os.environ["WECOM_CORP_ID"] = "wwtest"
    os.environ["WECOM_KF_SECRET"] = "secret"
    os.environ["WECOM_B0_ACTIVE_WORKSPACE"] = "1"
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)
    load_wecom_kf_config.cache_clear()


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


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


def _triage_stub() -> dict:
    return {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": "Review.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
    }


def _open_claim(*, ext: str = "wm_collision", with_prior_story: bool = False) -> dict:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
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
    case = get_case_by_id(cid) or saved
    case["created_at"] = ts
    case["updated_at"] = ts
    return case


def _normalized(text: str, *, ext: str = "wm_collision", msg_id: str = "m1") -> dict:
    return normalize_text_message(
        {
            "msgid": msg_id,
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "text": {"content": text},
        }
    )


def _claim_count(ext: str) -> int:
    return sum(
        1
        for c in list_all_cases_for_read()
        if c.get("wecom_external_userid") == ext and c.get("service_lane") == SERVICE_LANE_CLAIM
    )


def _slice_text(text: str, *, ext: str = "wm_collision", msg_id: str = "m1") -> dict:
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()

    def pull(_cfg, *, token, open_kf_id):
        return [
            {
                "msgid": msg_id,
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "text",
                "text": {"content": text},
            }
        ]

    results = process_kf_msg_or_event(
        cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull
    )
    assert results, f"no slice outcome for {text!r}"
    return results[0]


def test_01_open_claim_plus_accident_narrative_shows_resolver_no_new_claim():
    ext = "wm_col_a"
    _open_claim(ext=ext, with_prior_story=True)
    result = ingest_claim_basics_message(
        _normalized(_ACCIDENT_NARRATIVE, ext=ext),
        classify_wecom_intent(_ACCIDENT_NARRATIVE),
    )
    assert result["active_case_outcome"] == "claim_collision_resolver"
    assert result["case_created"] is False
    assert _claim_count(ext) == 1
    reply = result.get("reply_text") or ""
    assert any(m in reply for m in _RESOLVER_MARKERS)
    assert _START_MARKER not in reply
    case = get_case_by_id(result["case_id"])
    assert case.get("claim_collision_pending", {}).get("state") == "pending_choice"


def test_02_open_claim_plus_woyao_claim_shows_resolver():
    ext = "wm_col_b"
    _open_claim(ext=ext, with_prior_story=True)
    result = ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext),
        classify_wecom_intent("我要理赔"),
    )
    assert result["active_case_outcome"] == "claim_collision_resolver"
    assert result["case_created"] is False
    assert _claim_count(ext) == 1


def test_03_choice_continue_appends_no_new_claim():
    ext = "wm_col_c"
    saved = _open_claim(ext=ext, with_prior_story=True)
    ingest_claim_basics_message(
        _normalized(_ACCIDENT_NARRATIVE, ext=ext, msg_id="m_trig"),
        classify_wecom_intent(_ACCIDENT_NARRATIVE),
    )
    result = ingest_claim_collision_choice(_normalized("1", ext=ext, msg_id="m_choice"))
    assert result["active_case_outcome"] == "claim_collision_continue"
    assert result["case_created"] is False
    assert result["case_id"] == saved["case_id"]
    assert _claim_count(ext) == 1
    assert "继续记到上一份事故记录" in (result.get("reply_text") or "")


def test_04_choice_new_creates_claim_and_start_card():
    ext = "wm_col_d"
    _open_claim(ext=ext, with_prior_story=True)
    ingest_claim_basics_message(
        _normalized(_ACCIDENT_NARRATIVE, ext=ext, msg_id="m_trig"),
        classify_wecom_intent(_ACCIDENT_NARRATIVE),
    )
    result = ingest_claim_collision_choice(_normalized("2", ext=ext, msg_id="m_new"))
    assert result["active_case_outcome"] == "claim_start_card_sent"
    assert result["case_created"] is True
    assert _claim_count(ext) == 2
    assert _START_MARKER in (result.get("reply_text") or "")


def test_05_choice_contact_no_new_claim():
    ext = "wm_col_e"
    saved = _open_claim(ext=ext, with_prior_story=True)
    ingest_claim_basics_message(
        _normalized(_ACCIDENT_NARRATIVE, ext=ext, msg_id="m_trig"),
        classify_wecom_intent(_ACCIDENT_NARRATIVE),
    )
    result = ingest_claim_collision_choice(_normalized("3", ext=ext, msg_id="m_contact"))
    assert result["active_case_outcome"] == "claim_collision_contact"
    assert result["case_created"] is False
    assert _claim_count(ext) == 1
    assert result.get("needs_broker_manual_handle") is True
    assert "陈总人工确认" in (result.get("reply_text") or "")


def test_06_repeated_resolver_prompt_no_duplicate_claim():
    ext = "wm_col_f"
    _open_claim(ext=ext, with_prior_story=True)
    ingest_claim_basics_message(
        _normalized(_ACCIDENT_NARRATIVE, ext=ext, msg_id="m1"),
        classify_wecom_intent(_ACCIDENT_NARRATIVE),
    )
    result = ingest_claim_basics_message(
        _normalized(_ACCIDENT_NARRATIVE, ext=ext, msg_id="m2"),
        classify_wecom_intent(_ACCIDENT_NARRATIVE),
    )
    assert result["active_case_outcome"] == "claim_collision_resolver"
    assert _claim_count(ext) == 1


def test_07_repeated_choice_two_only_one_new_claim():
    ext = "wm_col_g"
    _open_claim(ext=ext, with_prior_story=True)
    ingest_claim_basics_message(
        _normalized(_ACCIDENT_NARRATIVE, ext=ext, msg_id="m_trig"),
        classify_wecom_intent(_ACCIDENT_NARRATIVE),
    )
    ingest_claim_collision_choice(_normalized("2", ext=ext, msg_id="m_new1"))
    ingest_claim_collision_choice(_normalized("2", ext=ext, msg_id="m_new2"))
    assert _claim_count(ext) == 2


def test_08_broker_done_plus_woyao_claim_allows_new_start():
    ext = "wm_col_h"
    saved = save_case("done claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid=ext)
    update_claim_workflow_state(saved["case_id"], claim_phase=CLAIM_PHASE_BROKER_DONE)
    result = ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext),
        classify_wecom_intent("我要理赔"),
    )
    assert result.get("case_created") is True
    assert result["active_case_outcome"] == "claim_start_card_sent"
    assert _START_MARKER in (result.get("reply_text") or "")


def test_09_multiple_open_claims_no_silent_append_or_create():
    ext = "wm_col_i"
    _open_claim(ext=ext, with_prior_story=True)
    _open_claim(ext=ext, with_prior_story=True)
    result = ingest_claim_basics_message(
        _normalized(_ACCIDENT_NARRATIVE, ext=ext),
        classify_wecom_intent(_ACCIDENT_NARRATIVE),
    )
    assert result["active_case_outcome"] == "claim_collision_resolver"
    assert result["case_created"] is False
    assert _claim_count(ext) == 2
    choice = ingest_claim_collision_choice(_normalized("1", ext=ext, msg_id="m_bad"))
    assert choice["active_case_outcome"] == "claim_collision_multiple_open"
    assert _claim_count(ext) == 2


def test_10_random_photo_before_start_still_hidden():
    ext = "wm_col_j"
    result = _slice_text("[image]", ext=ext, msg_id="m_photo")
    assert result.get("case_created") is not True
    assert _START_MARKER not in (result.get("reply_text") or "")


def test_11_add_car_claim_checkpoint_still_works():
    ext = "wm_col_k"
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid=ext)
    result = _slice_text("我要理赔", ext=ext, msg_id="m_claim")
    assert result.get("active_case_outcome") == "claim_lane_switch_prompt"
    assert _START_MARKER not in (result.get("reply_text") or "")


def test_12_broker_done_end_card_still_works():
    from services.fiqa_api.inbox_triage.case_store import mark_claim_broker_done

    ext = "wm_col_l"
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid=ext)
    update_claim_workflow_state(saved["case_id"], claim_phase=CLAIM_PHASE_BROKER_REVIEW)
    done = mark_claim_broker_done(saved["case_id"])
    assert done.get("already_done") is False or done.get("end_card_sent") is not False
    case = get_case_by_id(saved["case_id"])
    assert case.get("claim_phase") == CLAIM_PHASE_BROKER_DONE


def test_13_live_callback_path_process_kf_msg_or_event():
    ext = "wm_col_m"
    _open_claim(ext=ext, with_prior_story=True)
    result = _slice_text(_ACCIDENT_NARRATIVE, ext=ext, msg_id="m_live")
    assert result.get("active_case_outcome") == "claim_collision_resolver"
    assert result.get("case_created") is False
    choice = _slice_text("1", ext=ext, msg_id="m_live_choice")
    assert choice.get("active_case_outcome") == "claim_collision_continue"


def test_14_explicit_continuation_appends_without_resolver():
    ext = "wm_col_n"
    saved = _open_claim(ext=ext, with_prior_story=True)
    result = ingest_claim_basics_message(
        _normalized("还是同一个事故，补充一下对方保险", ext=ext),
        classify_wecom_intent("还是同一个事故，补充一下对方保险"),
    )
    assert result["case_created"] is False
    assert result["case_id"] == saved["case_id"]
    assert result["active_case_outcome"] != "claim_collision_resolver"
