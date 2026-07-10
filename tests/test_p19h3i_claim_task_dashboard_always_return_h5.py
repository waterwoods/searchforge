"""P19H-3i — Claim task dashboard + always-return H5 entry from WeCom."""

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
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.claim_workbench_display import enrich_claim_for_workbench
from services.fiqa_api.wecom.claim_basics import ingest_claim_basics_message, ingest_claim_status_request
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    SERVICE_LANE_CLAIM,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent, is_claim_status_request
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event


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


@pytest.mark.parametrize(
    "text",
    ["进度", "补资料", "链接", "事故资料", "继续填写"],
)
def test_submitted_claim_status_commands_return_h5_continue_link(text: str):
    ext = f"wm_3i_status_{text}"
    saved = _submitted_claim(ext=ext)
    result = ingest_claim_status_request(
        _normalized(text, ext=ext, msg_id=f"m_{text}"),
        classify_wecom_intent(text),
    )
    reply = result.get("reply_text") or ""
    assert result["case_created"] is False
    assert result["case_id"] == saved["case_id"]
    assert result["active_case_outcome"] == "claim_status_card"
    assert "已提交给陈总审核" in reply
    assert "继续补充事故资料" in reply
    assert "/task/claim/h5t1." in reply


def test_submitted_claim_supplement_plate_ack_short_no_raw_h5():
    ext = "wm_3i_plate"
    saved = _submitted_claim(ext=ext)
    text = "补充一下，对方车牌是 ABC123"
    result = ingest_claim_basics_message(
        _normalized(text, ext=ext, msg_id="m_plate"),
        classify_wecom_intent(text),
    )
    reply = result.get("reply_text") or ""
    assert result["active_case_outcome"] == "claim_supplement_appended"
    assert result["case_id"] == saved["case_id"]
    assert "已记录到您当前的事故资料里" in reply
    assert "/task/claim/h5t1." not in reply
    assert "进度" in reply or "链接" in reply


def test_submitted_claim_supplement_plate_ack_includes_h5_link():
    """Backward-compat alias — P19H-3j uses short ack without raw URL."""
    test_submitted_claim_supplement_plate_ack_short_no_raw_h5()


def test_submitted_claim_insurance_supplement_ack_short_no_raw_h5():
    ext = "wm_3i_insurance"
    saved = _submitted_claim(ext=ext)
    text = "对方保险是 State Farm"
    result = ingest_claim_basics_message(
        _normalized(text, ext=ext, msg_id="m_ins"),
        classify_wecom_intent(text),
    )
    reply = result.get("reply_text") or ""
    assert result["case_id"] == saved["case_id"]
    assert "已记录" in reply
    assert "/task/claim/h5t1." not in reply


def test_submitted_claim_insurance_supplement_ack_includes_h5_link():
    """Backward-compat alias — P19H-3j uses short ack without raw URL."""
    test_submitted_claim_insurance_supplement_ack_short_no_raw_h5()


def _msg(msg_id: str, content: str, *, ext: str) -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": ext,
        "origin": 3,
        "msgtype": "text",
        "text": {"content": content},
    }


def test_active_claim_add_car_still_routes_add_car(monkeypatch):
    ext = "wm_3i_add_car"
    _submitted_claim(ext=ext)
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "0")
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()
    text = "我要加车"

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_add_car", text, ext=ext)]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    assert results[0]["internal_intent"] == "add_car"
    assert results[0].get("active_case_outcome") != "claim_supplement_appended"


def test_no_active_claim_claim_start_still_works(monkeypatch):
    ext = "wm_3i_new_claim"
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "0")
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()
    text = "我要理赔"

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_new_claim", text, ext=ext)]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    assert results[0]["internal_intent"] == "claim_intake"
    claim_count = sum(
        1
        for c in list_all_cases_for_read()
        if c.get("wecom_external_userid") == ext and c.get("service_lane") == SERVICE_LANE_CLAIM
    )
    assert claim_count == 1


def test_workbench_labels_wecom_supplement_fact():
    ext = "wm_3i_wb"
    saved = _submitted_claim(ext=ext)
    text = "补充一下，对方车牌是 ABC123"
    ingest_claim_basics_message(
        _normalized(text, ext=ext, msg_id="m_wb"),
        classify_wecom_intent(text),
    )
    case = get_case_by_id(saved["case_id"]) or {}
    enriched = enrich_claim_for_workbench(case)
    brief = enriched.get("claim_case_brief") or {}
    key_facts = brief.get("key_facts") or {}
    assert "客户文字补充" in str(key_facts.get("other_party_plate") or "")
    timeline = enriched.get("claim_timeline") or []
    assert any("ABC123" in str(e.get("text") or "") for e in timeline if isinstance(e, dict))


def test_claim_status_request_markers_include_upload_photo():
    assert is_claim_status_request("上传照片")
    assert is_claim_status_request("补资料")
