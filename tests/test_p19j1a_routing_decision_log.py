"""P19J-1a — Structured WeCom routing decision logs."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    get_case_by_id,
    save_case,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_question_safe_reply,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.routing_observability import (
    ROUTING_DECISION_EVENT,
    hash_external_user_id,
    hash_text,
    redact_text_preview,
    routing_decision_from_log_message,
)
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

_DEFER_EN = "Let's finish your current request first"
_DEFER_ZH = "先完成当前请求"


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


def _save_active_add_car_case(*, ext: str = "wm_av_active") -> dict:
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    return get_case_by_id(cid) or saved


def _normalized(text: str, *, ext: str = "wm_av_active", msg_id: str = "m1") -> dict:
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


def _routing_logs(caplog) -> list[dict]:
    decisions: list[dict] = []
    for record in caplog.records:
        parsed = routing_decision_from_log_message(record.message)
        if parsed:
            decisions.append(parsed)
    return decisions


def _last_routing_log(caplog) -> dict:
    logs = _routing_logs(caplog)
    assert logs, "expected at least one routing decision log"
    return logs[-1]


# --- 1. Redaction / hashing ---


def test_redact_phone_in_preview():
    preview = redact_text_preview("电话是2031115557")
    assert preview is not None
    assert "2031115557" not in preview
    assert "[PHONE]" in preview


def test_redact_email_in_preview():
    preview = redact_text_preview("email is test@example.com")
    assert preview is not None
    assert "test@example.com" not in preview
    assert "[EMAIL]" in preview


def test_hash_text_and_length_metadata():
    text = "电话是2031115557"
    assert hash_text(text)
    assert len(hash_text(text) or "") == 64


def test_external_user_id_hashed_not_raw(caplog):
    ext = "wm_secret_user_12345"
    with caplog.at_level(logging.INFO, logger="services.fiqa_api.wecom.routing_observability"):
        ingest_claim_basics_message(
            _normalized("我要理赔", ext=ext, msg_id="hash1"),
            classify_wecom_intent("我要理赔"),
        )
    log = _last_routing_log(caplog)
    assert ext not in json.dumps(log)
    assert log.get("external_user_hash") == hash_external_user_id(ext)


# --- 2. Active Add Vehicle + Claim interrupt ---


def test_active_add_vehicle_woyao_claim_logs_lane_switch(caplog):
    _save_active_add_car_case()
    text = "我要理赔"
    with caplog.at_level(logging.INFO, logger="services.fiqa_api.wecom.routing_observability"):
        result = ingest_claim_basics_message(_normalized(text, msg_id="a1"), classify_wecom_intent(text))
    assert result["active_case_outcome"] == "claim_lane_switch_prompt"
    log = _last_routing_log(caplog)
    assert log["event"] == ROUTING_DECISION_EVENT
    assert log["priority_rule"] == "claim_interrupt_during_active_add_vehicle"
    assert log["decision"] == "lane_switch_prompt"
    assert log["response_type"] == "claim_lane_switch"
    assert "claim_start_intent" in log["reason"]


# --- 3. Active Add Vehicle + Start Claim intent → confirm card first ---


def test_active_add_vehicle_kaishi_claim_logs_lane_switch_prompt(caplog):
    _save_active_add_car_case()
    text = "开始理赔"
    with caplog.at_level(logging.INFO, logger="services.fiqa_api.wecom.routing_observability"):
        result = ingest_claim_basics_message(_normalized(text, msg_id="b1"), classify_wecom_intent(text))
    assert result["case_created"] is False
    assert result["active_case_outcome"] == "claim_lane_switch_prompt"
    log = _last_routing_log(caplog)
    assert log["priority_rule"] == "claim_interrupt_during_active_add_vehicle"
    assert log["decision"] == "lane_switch_prompt"
    assert log["response_type"] == "claim_lane_switch"


def test_active_add_vehicle_confirm_start_logs_start(caplog):
    from services.fiqa_api.wecom.claim_basics import ingest_claim_lane_switch_choice

    _save_active_add_car_case()
    ingest_claim_basics_message(_normalized("我要理赔", msg_id="b0"), classify_wecom_intent("我要理赔"))
    with caplog.at_level(logging.INFO, logger="services.fiqa_api.wecom.routing_observability"):
        result = ingest_claim_lane_switch_choice(_normalized("开始事故记录", msg_id="b1"))
    assert result["case_created"] is True
    log = _last_routing_log(caplog)
    assert log["priority_rule"] == "claim_confirmed_start"
    assert log["decision"] == "start_claim_flow"
    assert log["response_type"] == "claim_start"


# --- 4. Active Add Vehicle + Injury ---


def test_active_add_vehicle_injury_logs_safety_override(caplog):
    _save_active_add_car_case()
    text = "有人受伤了，我要理赔"
    with caplog.at_level(logging.INFO, logger="services.fiqa_api.wecom.routing_observability"):
        result = ingest_claim_basics_message(_normalized(text, msg_id="d1"), classify_wecom_intent(text))
    assert result["active_case_outcome"] == "claim_injury_manual_handle"
    log = _last_routing_log(caplog)
    assert log["priority_rule"] == "injury_safety_override"
    assert log["decision"] == "safety_manual_reply"
    assert log["response_type"] == "claim_safety_manual"


# --- 5. Active Add Vehicle + Claim question ---


def test_active_add_vehicle_claim_question_logs_safe_reply(caplog):
    _save_active_add_car_case()
    text = "出事故了怎么办"
    with caplog.at_level(logging.INFO, logger="services.fiqa_api.wecom.routing_observability"):
        ingest_claim_question_safe_reply(_normalized(text, msg_id="e1"))
    log = _last_routing_log(caplog)
    assert log["priority_rule"] == "claim_question_during_active_add_vehicle"
    assert log["decision"] == "claim_question_safe_reply"


# --- 6. Generic secondary-topic deferral ---


def test_generic_secondary_topic_logs_deferral(monkeypatch, caplog):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()
    ext = "wm_renew_def"
    _save_active_add_car_case(ext=ext)

    def pull(_cfg, *, token, open_kf_id):
        return [
            {
                "msgid": "m_renew",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "text",
                "text": {"content": "我还想问一下续保"},
            }
        ]

    with caplog.at_level(logging.INFO):
        results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    reply = results[0].get("reply_text") or ""
    assert _DEFER_EN in reply or _DEFER_ZH in reply
    log = _last_routing_log(caplog)
    assert log["priority_rule"] == "generic_secondary_topic_deferral"
    assert log["decision"] == "defer_secondary_topic"


# --- 7. No active case + Claim start ---


def test_no_active_case_claim_start_logs(caplog):
    text = "我要理赔"
    with caplog.at_level(logging.INFO, logger="services.fiqa_api.wecom.routing_observability"):
        result = ingest_claim_basics_message(_normalized(text, ext="wm_no_av", msg_id="i1"), classify_wecom_intent(text))
    assert result["case_created"] is True
    log = _last_routing_log(caplog)
    assert log["priority_rule"] == "claim_start_no_active_case"
    assert log["decision"] == "start_claim_flow"


# --- 8. Claim basics C1 log ---


def test_claim_basics_c1_logs_send_claim_c1(caplog):
    text = "今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门"
    with caplog.at_level(logging.INFO, logger="services.fiqa_api.wecom.routing_observability"):
        result = ingest_claim_basics_message(
            _normalized(text, ext="wm_c1", msg_id="c1_full"),
            classify_wecom_intent(text),
        )
    assert result["active_case_outcome"] == "claim_c1_sent"
    log = _last_routing_log(caplog)
    assert log["priority_rule"] == "active_claim_basics_collection"
    assert log["decision"] == "send_claim_c1"
    assert log["response_type"] == "claim_c1"


# --- 9. Add Vehicle route log ---


def test_add_vehicle_progress_route_logs(monkeypatch, caplog):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()
    ext = "wm_av_prog"
    _save_active_add_car_case(ext=ext)

    def pull(_cfg, *, token, open_kf_id):
        return [
            {
                "msgid": "m_prog",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "text",
                "text": {"content": "加车进度"},
            }
        ]

    with caplog.at_level(logging.INFO):
        process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    log = _last_routing_log(caplog)
    assert log["priority_rule"].startswith("add_vehicle_")
    assert log["decision"]
    assert log["reason"]
