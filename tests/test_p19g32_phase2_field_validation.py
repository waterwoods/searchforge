"""P19G-3.2 — Phase 2 phone/date validation guardrail."""

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
    _load_case_for_mutation,
    _persist_case_after_update,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.add_vehicle_phase2 import (
    ingest_phase2_text_collection,
    parse_phase2_text_fields,
    phase2_text_is_complete,
    phase2_text_still_needed,
)
from services.fiqa_api.wecom.identity import (
    extract_delivery_date_from_text,
    extract_delivery_date_with_validation,
    extract_phone_from_text,
    extract_phone_with_validation,
)
from services.fiqa_api.wecom.reply import build_phase2_validation_reply
from services.fiqa_api.inbox_triage.phone_normalization import normalize_us_phone_10_digits


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


def _case_with_h5_photos() -> dict:
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    mut = _load_case_for_mutation(saved["case_id"])
    assert mut is not None
    mut["case_attachments"] = [
        {"attachment_id": "a1", "source": "h5_task", "slot_assignment": "vin_photo"},
        {"attachment_id": "a2", "source": "h5_task", "slot_assignment": "registration_photo"},
        {"attachment_id": "a3", "source": "h5_task", "slot_assignment": "insurance_card_photo"},
    ]
    _persist_case_after_update(saved["case_id"], mut)
    return get_case_by_id(saved["case_id"]) or mut


# --- Phone validation ---


def test_normalize_us_phone_accepts_10_digit():
    assert normalize_us_phone_10_digits("203-123-4567") == "2031234567"


def test_normalize_us_phone_strips_leading_1():
    assert normalize_us_phone_10_digits("12031234567") == "2031234567"


def test_normalize_us_phone_rejects_11_digit_not_starting_with_1():
    assert normalize_us_phone_10_digits("20311155573") is None


def test_extract_phone_does_not_slice_inside_11_digit_run():
    assert extract_phone_from_text("电话是20311155573") is None
    valid, invalid = extract_phone_with_validation("电话是20311155573")
    assert valid is None
    assert invalid == "20311155573"


def test_extract_phone_accepts_formatted_10_digit():
    assert extract_phone_from_text("电话 203-123-4567") == "2031234567"


def test_extract_phone_not_confused_by_zip_and_long_phone():
    text = "Zip code 92705，电话是20311155573"
    assert extract_phone_from_text(text) is None
    _, invalid = extract_phone_with_validation(text)
    assert invalid == "20311155573"


# --- Date validation ---


def test_extract_date_rejects_invalid_month():
    assert extract_delivery_date_from_text("17月12号提车") is None
    valid, invalid = extract_delivery_date_with_validation("17月12号提车")
    assert valid is None
    assert invalid == "17月12号"


def test_extract_date_accepts_valid_chinese_month_day():
    assert extract_delivery_date_from_text("7月10号提车") == "7月10日"


def test_extract_date_rejects_invalid_day():
    valid, invalid = extract_delivery_date_with_validation("7月32号提车")
    assert valid is None
    assert invalid == "7月32号"


def test_extract_date_accepts_slash_format():
    assert extract_delivery_date_from_text("提车日期是7/10") == "7/10"


# --- Andy voice input regression ---


VOICE_INPUT = "我是要是17月12号提车，Zip code 92705，电话是20311155573"


def test_voice_input_parse_flags_invalid_phone_and_date():
    parsed = parse_phase2_text_fields(VOICE_INPUT, {})
    assert parsed["zip"] == "92705"
    assert parsed["phone"] is None
    assert parsed["delivery_date"] is None
    assert parsed["invalid_phone"] == "20311155573"
    assert parsed["invalid_date"] == "17月12号"


def test_voice_input_ingest_saves_zip_only_and_validation_reply():
    case = _case_with_h5_photos()
    bind_case_channel_identity(case["case_id"], wecom_external_userid="wm_voice", wecom_open_kf_id="wk001")
    result = ingest_phase2_text_collection(
        {"msg_id": "m_voice", "text": VOICE_INPUT, "external_userid": "wm_voice"},
        case["case_id"],
    )
    assert result["active_case_outcome"] == "phase2_validation_retry"
    reply = result["reply_text"] or ""
    assert "92705" in reply
    assert "20311155573" in reply
    assert "17月12号" in reply
    assert "10 位电话号码" in reply
    assert "提车日期好像不对" in reply
    assert "第 2 步完成" not in reply

    stored = get_case_by_id(case["case_id"])
    assert stored is not None
    assert "zip" in [f.lower() for f in stored.get("collected_fields") or []]
    assert stored.get("known_facts", {}).get("zip") == "92705"
    assert "phone" not in [f.lower() for f in stored.get("collected_fields") or []]
    assert "delivery_date" not in [f.lower() for f in stored.get("collected_fields") or []]
    assert phase2_text_is_complete(stored) is False
    assert "phone" in phase2_text_still_needed(stored)
    assert "delivery_date" in phase2_text_still_needed(stored)


def test_invalid_phone_only_reply_copy():
    reply = build_phase2_validation_reply({}, invalid_phone="20311155573")
    assert "联系电话位数好像不对" in reply
    assert "20311155573" in reply
    assert "2031234567" in reply


def test_invalid_date_only_reply_copy():
    reply = build_phase2_validation_reply({}, invalid_date="17月12号")
    assert "提车日期好像不对" in reply
    assert "17月12号" in reply
    assert "7月12号" in reply


def test_valid_fields_still_complete_to_s2():
    case = _case_with_h5_photos()
    bind_case_channel_identity(case["case_id"], wecom_external_userid="wm_ok", wecom_open_kf_id="wk001")
    result = ingest_phase2_text_collection(
        {
            "msg_id": "m_ok",
            "text": "7月10号提车，ZIP 92705，电话 203-123-4567",
            "external_userid": "wm_ok",
        },
        case["case_id"],
    )
    assert result["active_case_outcome"] == "phase2_complete_s2_sent"
    stored = get_case_by_id(case["case_id"])
    assert stored is not None
    assert phase2_text_is_complete(stored)
