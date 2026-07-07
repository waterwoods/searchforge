"""P19E-1 — Add Vehicle Phase 2 text field collection loop."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    get_case_by_id,
    save_case,
    _load_case_for_mutation,
    _persist_case_after_update,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.add_vehicle_phase2 import (
    ingest_phase2_text_collection,
    phase2_text_is_complete,
    phase2_text_still_needed,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.identity import (
    extract_delivery_date_from_text,
    extract_phone_from_text,
    extract_zip_from_text,
)
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.reply import (
    build_h5_photo_phase_complete_reply,
    build_phase2_current_step_reply,
    build_phase2_stage_complete_s2_reply,
)
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event


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
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


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


def _case_with_h5_photos(*, insurance_skipped: bool = False) -> dict:
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    mut = _load_case_for_mutation(saved["case_id"])
    assert mut is not None
    atts = [
        {"attachment_id": "a1", "source": "h5_task", "slot_assignment": "vin_photo"},
        {"attachment_id": "a2", "source": "h5_task", "slot_assignment": "registration_photo"},
    ]
    if not insurance_skipped:
        atts.append({"attachment_id": "a3", "source": "h5_task", "slot_assignment": "insurance_card_photo"})
    mut["case_attachments"] = atts
    if insurance_skipped:
        mut["h5_photo_flow_state"] = {"skipped_slots": ["insurance_card_photo"]}
    _persist_case_after_update(saved["case_id"], mut)
    return get_case_by_id(saved["case_id"]) or mut


def _b0_cfg(monkeypatch) -> object:
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    load_wecom_kf_config.cache_clear()
    return load_wecom_kf_config()


# --- Phase copy ---


def test_s1_photo_complete_reply_uses_stage_complete_framing():
    case = _case_with_h5_photos()
    text = build_h5_photo_phase_complete_reply(case)
    assert "第 1 阶段完成" in text
    assert "照片已收到" not in text
    assert "下一步 · 第 2 步" in text
    assert "加车完成" not in text
    assert "全部资料已收齐" not in text


def test_s1_insurance_skipped_copy():
    case = _case_with_h5_photos(insurance_skipped=True)
    text = build_h5_photo_phase_complete_reply(case)
    assert "○ 保险卡 — 可稍后补" in text


# --- Field extraction ---


def test_extract_all_three_from_combined_chinese_message():
    text = "7月10号提车，ZIP 92705，电话 949-123-4567"
    assert extract_delivery_date_from_text(text) == "7月10日"
    assert extract_zip_from_text(text) == "92705"
    assert extract_phone_from_text(text) == "9491234567"


def test_extract_zip_alone():
    assert extract_zip_from_text("ZIP 92705") == "92705"


def test_extract_phone_alone():
    assert extract_phone_from_text("电话是949-555-1212") == "9495551212"


def test_extract_delivery_date_chinese_month_day():
    assert extract_delivery_date_from_text("我7月12日拿车") == "7月12日"


def test_extract_delivery_date_relative_tomorrow():
    assert extract_delivery_date_from_text("提车明天") is not None


def test_extract_delivery_date_next_monday():
    assert extract_delivery_date_from_text("下周一提车") is not None


def test_phone_conservative_when_ambiguous():
    assert extract_phone_from_text("call me later") is None


def test_mixed_chinese_english_formats():
    text = "提车日期是7/10，停在92705，电话9491234567"
    assert extract_delivery_date_from_text(text) == "7/10"
    assert extract_zip_from_text(text) == "92705"
    assert extract_phone_from_text(text) == "9491234567"


# --- Phase 2 behavior ---


def test_partial_phase2_reply_lists_missing_fields():
    case = _case_with_h5_photos()
    bind_case_channel_identity(case["case_id"], wecom_external_userid="wm_p2", wecom_open_kf_id="wk001")
    result = ingest_phase2_text_collection(
        {"msg_id": "m_zip", "text": "ZIP 92705", "external_userid": "wm_p2"},
        case["case_id"],
    )
    assert result["reply_text"] is not None
    assert "第 2 步进行中" in result["reply_text"]
    assert "92705" in result["reply_text"]
    assert "联系电话" in result["reply_text"]
    stored = get_case_by_id(case["case_id"])
    assert stored is not None
    assert "zip" in [f.lower() for f in stored.get("collected_fields") or []]
    assert "phone" in phase2_text_still_needed(stored)


def test_all_three_fields_sends_s2_and_updates_state():
    case = _case_with_h5_photos()
    bind_case_channel_identity(case["case_id"], wecom_external_userid="wm_p2b", wecom_open_kf_id="wk001")
    text = "7月10号提车，ZIP 92705，电话 949-123-4567"
    result = ingest_phase2_text_collection(
        {"msg_id": "m_all", "text": text, "external_userid": "wm_p2b"},
        case["case_id"],
    )
    reply = result["reply_text"] or ""
    assert "第 2 阶段完成" in reply
    assert "第 3 步：陈总人工确认" in reply
    stored = get_case_by_id(case["case_id"])
    assert stored is not None
    assert phase2_text_is_complete(stored)
    assert stored.get("guided_workflow_state") == "ready_for_broker_review"
    assert stored.get("add_vehicle_phase") == "phase_3_broker_review"


def test_s2_dedup_on_repeat_message():
    case = _case_with_h5_photos()
    bind_case_channel_identity(case["case_id"], wecom_external_userid="wm_p2c", wecom_open_kf_id="wk001")
    payload = {"msg_id": "m_all1", "text": "7月10号提车，ZIP 92705，电话 949-123-4567", "external_userid": "wm_p2c"}
    first = ingest_phase2_text_collection(payload, case["case_id"])
    assert first["reply_text"] is not None
    second = ingest_phase2_text_collection(
        {"msg_id": "m_all2", "text": "7月10号提车，ZIP 92705，电话 949-123-4567", "external_userid": "wm_p2c"},
        case["case_id"],
    )
    assert second["active_case_outcome"] == "phase2_complete_s2_deduped"
    assert second["reply_text"] is None


def test_add_car_after_phase1_shows_progress_card_not_new_h5(monkeypatch):
    case = _case_with_h5_photos()
    bind_case_channel_identity(case["case_id"], wecom_external_userid="wm_follow", wecom_open_kf_id="wk001")
    cfg = _b0_cfg(monkeypatch)
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-h5-secret")
    reset_message_processed_memory_for_tests()
    reset_reply_dedup_memory_for_tests()
    captured: dict = {}

    def fake_send_menu_reply(_cfg, *, external_userid, open_kf_id, msgmenu):
        captured["menu"] = msgmenu

    def fake_send_text_reply(_cfg, *, external_userid, open_kf_id, content):
        captured["text"] = content

    with patch("services.fiqa_api.wecom.slice.send_menu_reply", side_effect=fake_send_menu_reply):
        with patch("services.fiqa_api.wecom.slice.send_text_reply", side_effect=fake_send_text_reply):
            outcomes = process_kf_msg_or_event(
                cfg,
                callback_token="tok",
                open_kf_id="wk001",
                pull_messages=lambda *_a, **_k: [
                    {
                        "msgid": "m_add_car_again",
                        "msgtype": "text",
                        "text": {"content": "我要加车"},
                        "external_userid": "wm_follow",
                        "open_kfid": "wk001",
                    }
                ],
            )
    assert outcomes[0]["active_case_outcome"] == "add_vehicle_progress_card"
    reply_blob = captured.get("text") or str(captured.get("menu") or "")
    assert "加车资料进度" in reply_blob
    assert "第 2 步" in reply_blob


def test_restart_still_creates_new_flow(monkeypatch):
    case = _case_with_h5_photos()
    bind_case_channel_identity(case["case_id"], wecom_external_userid="wm_restart", wecom_open_kf_id="wk001")
    cfg = _b0_cfg(monkeypatch)
    monkeypatch.setenv("H5_TASK_FRONTEND_BASE_URL", "https://example.test")
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-h5-secret")
    reset_message_processed_memory_for_tests()
    reset_reply_dedup_memory_for_tests()

    with patch("services.fiqa_api.wecom.slice.send_menu_reply") as mock_menu:
        process_kf_msg_or_event(
            cfg,
            callback_token="tok",
            open_kf_id="wk001",
            pull_messages=lambda *_a, **_k: [
                {
                    "msgid": "m_restart",
                    "msgtype": "text",
                    "text": {"content": "重新加车"},
                    "external_userid": "wm_restart",
                    "open_kfid": "wk001",
                }
            ],
        )
    assert mock_menu.called


def test_premium_lane_not_regressed(monkeypatch):
    cfg = _b0_cfg(monkeypatch)
    reset_message_processed_memory_for_tests()
    reset_reply_dedup_memory_for_tests()
    captured: dict = {}

    def fake_send_text_reply(_cfg, *, external_userid, open_kf_id, content):
        captured["text"] = content

    with patch("services.fiqa_api.wecom.slice.send_text_reply", side_effect=fake_send_text_reply):
        outcomes = process_kf_msg_or_event(
            cfg,
            callback_token="tok",
            open_kf_id="wk001",
            pull_messages=lambda *_a, **_k: [
                {
                    "msgid": "m_premium",
                    "msgtype": "text",
                    "text": {"content": "续保涨价了，保费太贵"},
                    "external_userid": "wm_premium_user",
                    "open_kfid": "wk001",
                }
            ],
        )
    assert outcomes[0].get("service_lane") == "premium_review" or outcomes[0].get("internal_intent") == "policy_review"


def test_phase2_current_step_empty_prompt():
    case = _case_with_h5_photos()
    text = build_phase2_current_step_reply(case)
    assert "第 2 步】" in text
    assert "提车日期" in text


def test_phase2_s2_copy_safe_language():
    case = _case_with_h5_photos()
    case["collected_fields"] = ["delivery_date", "zip", "phone"]
    text = build_phase2_stage_complete_s2_reply(case)
    assert "资料已基本收齐" in text
    assert "全部资料已收齐" not in text
