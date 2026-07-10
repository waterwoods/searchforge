"""P19H-3i — Regression: Claim start/H5 commands must not hit legacy bilingual fallback."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    get_case_by_id,
    patch_case_known_facts,
    save_case,
    update_claim_workflow_state,
    update_case_h5_intake_state,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_status_request,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    SERVICE_LANE_CLAIM,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

_LEGACY_MARKERS = (
    "Please confirm everyone is safe",
    "请先确认人是否安全",
    "We cannot advise whether to file a claim",
    "不能替您决定是否报保险",
)


@pytest.fixture(autouse=True)
def _json_store(monkeypatch):
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    monkeypatch.setenv("H5_TASK_FRONTEND_BASE_URL", "https://example.test")
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-h5-secret")
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    load_wecom_kf_config.cache_clear()
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)
    load_wecom_kf_config.cache_clear()


def _normalized(text: str, *, ext: str, msg_id: str) -> dict:
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


def _claim_stub() -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Broker review.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": True,
        "claim_phase": CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    }


def _submitted_claim(*, ext: str) -> dict:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    patch_case_known_facts(
        cid,
        {
            "injury_status": "no",
            "accident_datetime": "7月8日",
            "accident_location": "Santa Ana",
            "accident_description": "后车追尾",
            "own_vehicle_info": "Toyota Camry",
        },
    )
    update_claim_workflow_state(
        cid,
        claim_phase=CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
        guided_workflow_state="ready_for_broker_review",
    )
    update_case_h5_intake_state(
        cid,
        {"submitted_at": "2026-07-10T12:00:00+00:00", "submitted": True},
    )
    return get_case_by_id(cid) or saved


def _msg(msg_id: str, content: str, *, ext: str) -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": ext,
        "origin": 3,
        "msgtype": "text",
        "text": {"content": content},
    }


def _assert_no_legacy(reply: str) -> None:
    for marker in _LEGACY_MARKERS:
        assert marker not in reply


def _run_slice(text: str, *, ext: str, msg_id: str, monkeypatch) -> dict:
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "0")
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()

    def pull(_cfg, *, token, open_kf_id):
        return [_msg(msg_id, text, ext=ext)]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    return results[0]


def test_no_active_claim_wo_yao_li_pei_returns_h5_start_card(monkeypatch):
    ext = "wm_3i_legacy_1"
    result = _run_slice("我要理赔", ext=ext, msg_id="m_legacy_1", monkeypatch=monkeypatch)
    reply = result.get("reply_text") or ""
    _assert_no_legacy(reply)
    assert "【事故记录已开始 ✅】" in reply
    assert "提交给陈总审核" in reply
    assert (
        "打开资料填写页面" in reply
        or "请点击下面链接" in reply
        or "/task/claim/h5t1." in reply
        or result.get("menu_payload") is not None
    )


def test_no_active_claim_h5_phrase_returns_h5_start_not_legacy(monkeypatch):
    ext = "wm_3i_legacy_2"
    result = _run_slice("我需要理赔，发给我 H5", ext=ext, msg_id="m_legacy_2", monkeypatch=monkeypatch)
    reply = result.get("reply_text") or ""
    _assert_no_legacy(reply)
    assert "【事故记录已开始 ✅】" in reply or "/task/claim/h5t1." in reply


def test_no_active_claim_accident_link_returns_h5_not_legacy(monkeypatch):
    ext = "wm_3i_legacy_3"
    result = _run_slice("出事故了，给我链接", ext=ext, msg_id="m_legacy_3", monkeypatch=monkeypatch)
    reply = result.get("reply_text") or ""
    _assert_no_legacy(reply)
    assert "【事故记录已开始 ✅】" in reply or "/task/claim/h5t1." in reply


def test_submitted_claim_h5_phrase_returns_status_card(monkeypatch):
    ext = "wm_3i_legacy_4"
    saved = _submitted_claim(ext=ext)
    result = ingest_claim_status_request(
        _normalized("我需要理赔，发给我 H5", ext=ext, msg_id="m_legacy_4"),
        classify_wecom_intent("我需要理赔，发给我 H5"),
    )
    reply = result.get("reply_text") or ""
    _assert_no_legacy(reply)
    assert result["case_id"] == saved["case_id"]
    assert result["case_created"] is False
    assert "继续补充事故资料" in reply or "打开事故资料页面" in reply
    assert "/task/claim/h5t1." in reply


@pytest.mark.parametrize("text", ["进度", "补资料"])
def test_submitted_claim_status_commands_no_legacy(text: str):
    ext = f"wm_3i_legacy_status_{text}"
    _submitted_claim(ext=ext)
    result = ingest_claim_status_request(
        _normalized(text, ext=ext, msg_id=f"m_{text}"),
        classify_wecom_intent(text),
    )
    reply = result.get("reply_text") or ""
    _assert_no_legacy(reply)
    assert "/task/claim/h5t1." in reply


def test_submitted_claim_supplement_plate_no_legacy():
    ext = "wm_3i_legacy_plate"
    saved = _submitted_claim(ext=ext)
    text = "补充一下，对方车牌是 ABC123"
    result = ingest_claim_basics_message(
        _normalized(text, ext=ext, msg_id="m_plate"),
        classify_wecom_intent(text),
    )
    reply = result.get("reply_text") or ""
    _assert_no_legacy(reply)
    assert result["case_id"] == saved["case_id"]
    assert "/task/claim/h5t1." in reply


def test_add_car_preserved(monkeypatch):
    ext = "wm_3i_legacy_add_car"
    result = _run_slice("我要加车", ext=ext, msg_id="m_add_car", monkeypatch=monkeypatch)
    assert result["internal_intent"] == "add_car"
    _assert_no_legacy(result.get("reply_text") or "")


def test_explicit_new_accident_confirm_allowed(monkeypatch):
    ext = "wm_3i_legacy_new_acc"
    _submitted_claim(ext=ext)
    text = "这是另一个事故，不是刚才那个"
    result = ingest_claim_basics_message(
        _normalized(text, ext=ext, msg_id="m_new_acc"),
        classify_wecom_intent(text),
    )
    reply = result.get("reply_text") or ""
    _assert_no_legacy(reply)
    assert result.get("active_case_outcome") in {
        "claim_collision_resolver",
        "claim_status_card",
        "claim_supplement_appended",
        "claim_start_card_sent",
    }


def test_english_claim_start_no_legacy(monkeypatch):
    ext = "wm_3i_legacy_en"
    result = _run_slice("I need to file a claim", ext=ext, msg_id="m_en", monkeypatch=monkeypatch)
    reply = result.get("reply_text") or ""
    _assert_no_legacy(reply)
    assert "【事故记录已开始 ✅】" in reply or "/task/claim/h5t1." in reply


def test_no_b0_claim_start_still_h5_not_legacy(monkeypatch):
    monkeypatch.delenv("WECOM_B0_ACTIVE_WORKSPACE", raising=False)
    load_wecom_kf_config.cache_clear()
    ext = "wm_3i_legacy_nob0"
    result = _run_slice("我要理赔", ext=ext, msg_id="m_nob0", monkeypatch=monkeypatch)
    reply = result.get("reply_text") or ""
    _assert_no_legacy(reply)
    assert "【事故记录已开始 ✅】" in reply or "/task/claim/h5t1." in reply
