"""P19H-3f-2 — Live WeCom callback path: Add Car → Claim lane switch."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    get_case_by_id,
    save_case,
    update_add_vehicle_workflow_state,
    update_claim_workflow_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import ingest_claim_lane_switch_choice
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_BROKER_REVIEW,
    SERVICE_LANE_CLAIM,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

_DEFER_EN = "Let's finish your current request first"
_DEFER_ZH = "先完成当前请求"
_DEFER_BROKER = "陈总会人工跟进其他事项"
_START_MARKER = "【事故记录已开始 ✅】"
_CONFIRM_CARD_MARKERS = ("您现在是想开始一份新的事故/理赔记录吗", "暂停当前加车资料收集")


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
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


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


def _save_active_add_car_case(*, ext: str = "wm_live_av") -> dict:
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    return get_case_by_id(cid) or saved


def _slice_text(
    text: str,
    *,
    ext: str = "wm_live_av",
    msg_id: str = "m1",
    b0: bool | None = True,
) -> dict:
    if b0 is True:
        os.environ["WECOM_B0_ACTIVE_WORKSPACE"] = "1"
    elif b0 is False:
        os.environ.pop("WECOM_B0_ACTIVE_WORKSPACE", None)
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


def _assert_no_deferral(reply: str) -> None:
    assert _DEFER_EN not in reply
    assert _DEFER_ZH not in reply
    assert _DEFER_BROKER not in reply


def _save_add_car_broker_review(*, ext: str = "wm_prod_shape") -> dict:
    """Match production log shape: add_car in phase_3_broker_review."""
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    update_add_vehicle_workflow_state(
        cid,
        guided_workflow_state="ready_for_broker_review",
        add_vehicle_phase="phase_3_broker_review",
    )
    return get_case_by_id(cid) or saved


def _save_open_claim_broker_review(*, ext: str) -> dict:
    saved = save_case("claim", _triage_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    update_claim_workflow_state(
        cid,
        claim_phase=CLAIM_PHASE_BROKER_REVIEW,
        guided_workflow_state="ready_for_broker_review",
    )
    return get_case_by_id(cid) or saved


def _assert_confirm_card(result: dict) -> str:
    reply = result.get("reply_text") or ""
    assert result.get("active_case_outcome") == "claim_lane_switch_prompt"
    assert result.get("case_created") is False
    assert any(m in reply for m in _CONFIRM_CARD_MARKERS)
    _assert_no_deferral(reply)
    assert _START_MARKER not in reply
    return reply


def test_live_slice_active_add_car_woyao_claim_no_defer_b0_on():
    _save_active_add_car_case()
    result = _slice_text("我要理赔", msg_id="live1", b0=True)
    _assert_confirm_card(result)
    add_car = get_case_by_id(result["case_id"])
    pending = add_car.get("lane_switch_pending") or {}
    assert pending.get("state") == "pending_confirm"
    assert pending.get("trigger_text") == "我要理赔"


def test_live_slice_active_add_car_woyao_jinxing_claim_no_defer_b0_on():
    _save_active_add_car_case(ext="wm_live_jx")
    result = _slice_text("我要进行理赔", ext="wm_live_jx", msg_id="live2", b0=True)
    _assert_confirm_card(result)


def test_live_slice_active_add_car_xianzai_jinxing_claim_b0_on():
    _save_active_add_car_case(ext="wm_live_xz")
    result = _slice_text("我现在要进行理赔", ext="wm_live_xz", msg_id="live3", b0=True)
    _assert_confirm_card(result)


def test_live_slice_active_add_car_woyao_claim_no_defer_b0_off():
    """Production bug path: minimal_lane defer fired when claim routing was b0-gated only."""
    _save_active_add_car_case(ext="wm_live_b0off")
    result = _slice_text("我要理赔", ext="wm_live_b0off", msg_id="live4", b0=False)
    _assert_confirm_card(result)


def test_live_slice_active_add_car_woyao_jinxing_claim_no_defer_b0_off():
    _save_active_add_car_case(ext="wm_live_b0off2")
    result = _slice_text("我要进行理赔", ext="wm_live_b0off2", msg_id="live5", b0=False)
    _assert_confirm_card(result)


def test_live_slice_confirm_start_creates_claim_start_card():
    ext = "wm_live_confirm"
    add_car = _save_active_add_car_case(ext=ext)
    _slice_text("我要理赔", ext=ext, msg_id="live6a", b0=True)
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    choice = ingest_claim_lane_switch_choice(
        {
            "msg_id": "live6b",
            "external_userid": ext,
            "open_kf_id": "wktest001",
            "text": "开始事故记录",
        }
    )
    reply = choice["reply_text"] or ""
    assert choice["case_created"] is True
    assert choice["active_case_outcome"] == "claim_start_card_sent"
    assert _START_MARKER in reply
    assert get_case_by_id(add_car["case_id"]) is not None
    assert get_case_by_id(choice["case_id"]).get("service_lane") == SERVICE_LANE_CLAIM


def test_live_slice_cancel_continue_add_car():
    ext = "wm_live_cancel"
    add_car = _save_active_add_car_case(ext=ext)
    _slice_text("我要理赔", ext=ext, msg_id="live7a", b0=True)
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    choice = ingest_claim_lane_switch_choice(
        {
            "msg_id": "live7b",
            "external_userid": ext,
            "open_kf_id": "wktest001",
            "text": "继续加车",
        }
    )
    reply = choice["reply_text"] or ""
    assert choice["case_created"] is False
    assert "继续完成加车资料" in reply
    assert "已收到的加车资料会保留" in reply
    assert get_case_by_id(add_car["case_id"]) is not None
    claims = [c for c in list_all_cases_for_read() if c.get("service_lane") == SERVICE_LANE_CLAIM]
    assert not claims


def test_live_slice_repeated_woyao_claim_while_pending():
    ext = "wm_live_repeat"
    _save_active_add_car_case(ext=ext)
    first = _slice_text("我要理赔", ext=ext, msg_id="live8a", b0=True)
    _assert_confirm_card(first)
    second = _slice_text("我要理赔", ext=ext, msg_id="live8b", b0=True)
    _assert_confirm_card(second)
    claims = [c for c in list_all_cases_for_read() if c.get("service_lane") == SERVICE_LANE_CLAIM]
    assert not claims


def test_live_slice_ambiguous_narrative_no_confirm():
    _save_active_add_car_case(ext="wm_live_narr")
    result = _slice_text(
        "昨晚 Costco 被追尾了，后保险杠有点坏",
        ext="wm_live_narr",
        msg_id="live9",
        b0=True,
    )
    reply = result.get("reply_text") or ""
    assert result.get("active_case_outcome") != "claim_lane_switch_prompt"
    assert not any(m in reply for m in _CONFIRM_CARD_MARKERS)
    _assert_no_deferral(reply)
    claims = [c for c in list_all_cases_for_read() if c.get("service_lane") == SERVICE_LANE_CLAIM]
    assert not claims


def test_live_slice_insurance_question_no_confirm():
    _save_active_add_car_case(ext="wm_live_q")
    result = _slice_text(
        "这种情况要不要报保险？",
        ext="wm_live_q",
        msg_id="live10",
        b0=True,
    )
    reply = result.get("reply_text") or ""
    assert result.get("active_case_outcome") != "claim_lane_switch_prompt"
    assert "事故/理赔记录" not in reply
    claims = [c for c in list_all_cases_for_read() if c.get("service_lane") == SERVICE_LANE_CLAIM]
    assert not claims


def test_idle_woyao_claim_still_direct_start_b0_on():
    result = _slice_text("我要理赔", ext="wm_idle_claim", msg_id="live11", b0=True)
    reply = result.get("reply_text") or ""
    assert result.get("case_created") is True
    assert _START_MARKER in reply or "陈总办公室" in reply
    _assert_no_deferral(reply)


def test_live_slice_add_car_broker_review_plus_open_claim_woyao_claim():
    """Production shape: add_car broker_review + open Claim must still lane-switch."""
    ext = "wm_prod_repro"
    _save_add_car_broker_review(ext=ext)
    _save_open_claim_broker_review(ext=ext)
    result = _slice_text("我要理赔", ext=ext, msg_id="live12", b0=True)
    _assert_confirm_card(result)


def test_live_slice_add_car_broker_review_woyao_jinxing_claim():
    ext = "wm_prod_repro2"
    _save_add_car_broker_review(ext=ext)
    _save_open_claim_broker_review(ext=ext)
    result = _slice_text("我要进行理赔", ext=ext, msg_id="live13", b0=True)
    _assert_confirm_card(result)


def test_live_slice_true_other_question_still_defers():
    ext = "wm_other_q"
    _save_add_car_broker_review(ext=ext)
    result = _slice_text("我还想问一下续保", ext=ext, msg_id="live14", b0=True)
    reply = result.get("reply_text") or ""
    assert result.get("active_case_outcome") == "secondary_topic_deferred"
    assert _DEFER_EN in reply or _DEFER_ZH in reply
