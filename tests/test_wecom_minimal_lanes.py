"""Loop 2 — Premium Review / Claim Lite minimal WeCom lane tests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import count_stored_cases, get_case_by_id
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.minimal_lanes import ingest_wecom_text_to_minimal_lane
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.reply import build_slice_reply
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event
from services.fiqa_api.wecom.sync_cursor import reset_sync_cursor_memory_for_tests


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("WECOM_SLICE_SEND_REPLY", raising=False)
    monkeypatch.delenv("WECOM_B0_ACTIVE_WORKSPACE", raising=False)
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    reset_sync_cursor_memory_for_tests()
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


def _setup_json_store() -> None:
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    os.environ.pop("DATABASE_URL", None)


def _msg(msg_id: str, content: str, *, external_userid: str = "wm_loop2_premium") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": external_userid,
        "origin": 3,
        "msgtype": "text",
        "text": {"content": content},
    }


def test_premium_intent_high_confidence():
    r = classify_wecom_intent("陈总，我 Uber Black 保险又涨了，现在一年 15500，有没有便宜一点？")
    assert r.intent == "policy_review"
    assert r.confidence == "high"


def test_claim_intent_405_accident():
    r = classify_wecom_intent("我刚刚在 405 附近撞车了，现在怎么办？要不要报保险？")
    assert r.intent == "claim_intake"
    assert r.confidence == "high"


def test_mixed_premium_and_claim_is_unclear():
    r = classify_wecom_intent("我保险太贵了，顺便昨天撞车了")
    assert r.intent == "unclear"
    assert r.confidence == "low"


def test_generic_nihao_low_confidence():
    r = classify_wecom_intent("你好")
    assert r.intent == "unclear"
    assert r.confidence == "low"


def test_premium_message_creates_minimal_case():
    _setup_json_store()
    normalized = normalize_text_message(
        _msg("m_prem_1", "陈总，我 Uber Black 保险又涨了，现在一年 15500，有没有便宜一点？")
    )
    intent = classify_wecom_intent(normalized["text"])
    result = ingest_wecom_text_to_minimal_lane(normalized, intent)

    assert result["outcome"] == "created"
    assert result["case_created"] is True
    assert result["service_lane"] == "policy_review"
    assert count_stored_cases() == 1

    stored = get_case_by_id(result["case_id"])
    assert stored is not None
    assert stored.get("service_lane") == "policy_review"
    assert stored.get("issue_category") == "premium_review"
    assert "Price Sensitive" in (stored.get("workbench_tags") or [])
    assert stored.get("p16_broker_packet")
    assert stored.get("known_facts")


def test_claim_message_creates_minimal_case():
    _setup_json_store()
    normalized = normalize_text_message(
        _msg("m_claim_1", "我刚刚在 405 附近撞车了，现在怎么办？要不要报保险？", external_userid="wm_loop2_claim")
    )
    intent = classify_wecom_intent(normalized["text"])
    result = ingest_wecom_text_to_minimal_lane(normalized, intent)

    assert result["outcome"] == "created"
    assert result["service_lane"] == "claim_lite"
    stored = get_case_by_id(result["case_id"])
    assert "Urgent" in (stored.get("workbench_tags") or [])
    assert "Manual Handle" in (stored.get("workbench_tags") or [])


def test_premium_followup_attaches_same_case():
    _setup_json_store()
    ext = "wm_loop2_premium_dup"
    first = normalize_text_message(_msg("m_prem_a", "续保涨价了，保费太贵", external_userid=ext))
    intent1 = classify_wecom_intent(first["text"])
    created = ingest_wecom_text_to_minimal_lane(first, intent1)
    case_id = created["case_id"]

    second = normalize_text_message(_msg("m_prem_b", "续保又涨价了，现在15500", external_userid=ext))
    intent2 = classify_wecom_intent(second["text"])
    attached = ingest_wecom_text_to_minimal_lane(second, intent2)

    assert attached["outcome"] == "attached"
    assert attached["case_id"] == case_id
    assert count_stored_cases() == 1


def test_safe_premium_reply_no_quote_promise():
    text = build_slice_reply("policy_review", guided_menu=False)
    assert "报价" in text or "quote" in text.lower()
    assert "不会" in text or "not" in text.lower()


def test_safe_claim_reply_no_claim_advice():
    text = build_slice_reply("claim_intake", guided_menu=False)
    assert "报保险" in text or "claim" in text.lower()
    assert "不能" in text or "cannot" in text.lower()


def test_slice_b0_premium_creates_case(monkeypatch):
    _setup_json_store()
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_slice_prem", "陈总，我 Uber Black 保险又涨了，现在一年 15500，有没有便宜一点？")]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)

    assert len(results) == 1
    assert results[0]["internal_intent"] == "policy_review"
    assert results[0]["case_created"] is True
    assert results[0]["active_case_outcome"] == "created"
    assert count_stored_cases() == 1


def test_slice_b0_add_car_still_start_card(monkeypatch):
    _setup_json_store()
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    monkeypatch.setenv("H5_TASK_FRONTEND_BASE_URL", "https://example.test")
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-h5-secret")
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_add_car", "明天提新车，帮我加到保险", external_userid="wm_loop2_addcar")]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)

    assert results[0]["active_case_outcome"] == "start_card_sent"
    assert results[0]["case_created"] is True
    assert results[0]["case_id"]
    assert results[0].get("h5_task_link_masked")
    assert count_stored_cases() == 1


def test_slice_b0_hello_no_case(monkeypatch):
    _setup_json_store()
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_hello", "你好", external_userid="wm_loop2_hello")]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)

    assert results[0]["guided_menu_required"] is True
    assert results[0]["case_created"] is False
    assert count_stored_cases() == 0


def test_coverage_intent_high_confidence():
    r = classify_wecom_intent("我保险停了还能开吗？DMV 说我没保险。")
    assert r.intent == "coverage_risk_intake"
    assert r.confidence == "high"


def test_coverage_message_creates_minimal_case():
    _setup_json_store()
    normalized = normalize_text_message(
        _msg("m_cov_1", "我保险停了还能开吗？DMV 说我没保险。", external_userid="wm_loop3_cov")
    )
    intent = classify_wecom_intent(normalized["text"])
    result = ingest_wecom_text_to_minimal_lane(normalized, intent)

    assert result["outcome"] == "created"
    assert result["case_created"] is True
    assert result["service_lane"] == "coverage_risk"
    assert count_stored_cases() == 1

    stored = get_case_by_id(result["case_id"])
    assert stored is not None
    assert stored.get("service_lane") == "coverage_risk"
    assert stored.get("issue_category") == "coverage_status_risk"
    assert stored.get("urgency") == "critical"
    assert "Coverage Risk" in (stored.get("workbench_tags") or [])
    assert "Manual Handle" in (stored.get("workbench_tags") or [])
    assert stored.get("customer_name")
    assert stored.get("p16_broker_packet")
    assert (stored.get("quote_ready_status") or "") != "quote_ready"


def test_coverage_followup_attaches_same_case():
    _setup_json_store()
    ext = "wm_loop3_cov_dup"
    first = normalize_text_message(_msg("m_cov_a", "保单被取消了", external_userid=ext))
    intent1 = classify_wecom_intent(first["text"])
    created = ingest_wecom_text_to_minimal_lane(first, intent1)
    case_id = created["case_id"]

    second = normalize_text_message(_msg("m_cov_b", "DMV 说我没保险", external_userid=ext))
    intent2 = classify_wecom_intent(second["text"])
    attached = ingest_wecom_text_to_minimal_lane(second, intent2)

    assert attached["outcome"] == "attached"
    assert attached["case_id"] == case_id
    assert count_stored_cases() == 1


def test_safe_coverage_reply_no_driving_advice():
    text = build_slice_reply("coverage_risk_intake", guided_menu=False)
    lower = text.lower()
    assert "你现在可以开" not in text
    assert "可以先开" not in text
    assert "you can drive now" not in lower
    assert "you are covered" not in lower
    assert "should be covered" not in lower
    assert "还有保险" not in text
    assert "已恢复" not in text
    assert "不用担心" not in text
    assert "人工" in text or "broker" in lower
    assert "不能" in text or "can't" in lower or "can not" in lower


def test_slice_b0_coverage_creates_case(monkeypatch):
    _setup_json_store()
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_slice_cov", "我保险停了还能开吗？DMV 说我没保险。", external_userid="wm_loop3_slice_cov")]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)

    assert len(results) == 1
    assert results[0]["internal_intent"] == "coverage_risk_intake"
    assert results[0]["case_created"] is True
    assert results[0]["active_case_outcome"] == "created"
    assert results[0]["service_lane"] == "coverage_risk"
    assert count_stored_cases() == 1


def test_slice_b0_claim_still_works(monkeypatch):
    _setup_json_store()
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_slice_claim", "我刚刚在 405 附近撞车了，现在怎么办？要不要报保险？", external_userid="wm_loop3_claim")]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)

    assert results[0]["internal_intent"] == "claim_intake"
    assert results[0]["case_created"] is True
    assert results[0]["service_lane"] == "claim_lite"


def test_mixed_premium_coverage_slice_no_duplicate_explosion(monkeypatch):
    _setup_json_store()
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    load_wecom_kf_config.cache_clear()
    cfg = load_wecom_kf_config()

    def pull(_cfg, *, token, open_kf_id):
        return [
            _msg(
                "m_mixed_cov",
                "我保险太贵了，而且好像停保了，现在还能开车吗？",
                external_userid="wm_loop3_mixed",
            )
        ]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)

    assert results[0]["internal_intent"] == "coverage_risk_intake"
    assert results[0]["case_created"] is True
    assert count_stored_cases() == 1
    reply = results[0].get("reply_text") or ""
    assert "你现在可以开" not in reply
    assert "可以先开" not in reply
