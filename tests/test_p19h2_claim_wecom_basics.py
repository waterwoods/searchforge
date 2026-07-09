"""P19H-2 — Claim WeCom start card + accident basics + C1."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import get_case_by_id
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_question_safe_reply,
    should_route_claim_guided_workflow,
    should_route_claim_question_safe_reply,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_FORBIDDEN_AUTOMATION_CLAIMS,
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS,
    SERVICE_LANE_CLAIM,
    customer_copy_contains_forbidden_phrase,
    is_accident_basics_complete,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.reply import (
    build_claim_question_safe_reply,
    build_claim_stage_complete_c1_reply,
    build_claim_start_card_reply,
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


def _msg(msg_id: str, content: str, *, ext: str = "wm_claim_h2") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": ext,
        "origin": 3,
        "msgtype": "text",
        "text": {"content": content},
    }


def _normalized(text: str, *, ext: str = "wm_claim_h2", msg_id: str = "m1") -> dict:
    return normalize_text_message(_msg(msg_id, text, ext=ext))


def _assert_no_forbidden_copy(text: str) -> None:
    scrubbed = (text or "").replace("不代表 claim 已正式提交", "")
    assert customer_copy_contains_forbidden_phrase(scrubbed) is None
    for phrase in ("已经帮您报案", "理赔已经提交", "是对方责任", "您的保险一定会赔"):
        assert phrase not in scrubbed


def test_claim_start_card_copy_safe():
    reply = build_claim_start_card_reply()
    assert "陈总办公室的值班助手" in reply
    assert "有没有受伤" in reply
    assert "大概什么时候、在哪里" in reply
    assert "这不代表已经向保险公司正式报案" in reply
    _assert_no_forbidden_copy(reply)


def test_woyao_claim_start_creates_guided_case():
    normalized = _normalized("我要理赔", msg_id="m_start")
    intent = classify_wecom_intent("我要理赔")
    assert should_route_claim_guided_workflow(normalized, intent) is True
    result = ingest_claim_basics_message(normalized, intent)
    assert result["case_created"] is True
    assert result["service_lane"] == SERVICE_LANE_CLAIM
    assert result["active_case_outcome"] == "claim_start_card_sent"
    stored = get_case_by_id(result["case_id"])
    assert stored is not None
    assert stored.get("service_lane") == SERVICE_LANE_CLAIM
    assert stored.get("claim_phase") in ("claim_started", CLAIM_PHASE_ACCIDENT_BASICS_IN_PROGRESS)


def test_zhuangche_not_generic_menu(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_crash", "我撞车了", ext="wm_crash_only")]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    assert results[0]["internal_intent"] == "claim_intake"
    assert results[0]["case_created"] is True
    assert results[0]["service_lane"] == SERVICE_LANE_CLAIM
    assert "陈总办公室的值班助手" in (results[0].get("reply_text") or "")


def test_full_basics_message_sends_c1():
    text = "今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门"
    normalized = _normalized(text, msg_id="m_full")
    intent = classify_wecom_intent(text)
    result = ingest_claim_basics_message(normalized, intent)
    assert result["active_case_outcome"] == "claim_c1_sent"
    stored = get_case_by_id(result["case_id"])
    assert stored is not None
    assert is_accident_basics_complete(stored) is True
    assert stored.get("claim_phase") == CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE
    facts = stored.get("known_facts") or {}
    assert facts.get("accident_datetime")
    assert facts.get("accident_location")
    assert facts.get("accident_description")
    reply = result["reply_text"] or ""
    assert "【事故信息已记录 ✅】" in reply
    assert "补充事故资料" in reply
    assert "http" not in reply.lower()
    _assert_no_forbidden_copy(reply)


def test_partial_basics_time_only_no_c1():
    ext = "wm_partial"
    ingest_claim_basics_message(_normalized("我要理赔", ext=ext, msg_id="m_p1"), classify_wecom_intent("我要理赔"))
    second = ingest_claim_basics_message(
        _normalized("今天上午10点", ext=ext, msg_id="m_p2"),
        classify_wecom_intent("今天上午10点"),
    )
    assert second["active_case_outcome"] == "claim_basics_partial"
    stored = get_case_by_id(second["case_id"])
    assert stored is not None
    assert is_accident_basics_complete(stored) is False
    assert "accident_datetime" in [f.lower() for f in stored.get("collected_fields") or []]
    reply = second["reply_text"] or ""
    assert "还需要" in reply
    assert "第 1 步完成" not in reply


def test_two_message_basics_merge_to_c1():
    ext = "wm_merge"
    ingest_claim_basics_message(
        _normalized("今天上午10点", ext=ext, msg_id="m_m1"),
        classify_wecom_intent("今天上午10点"),
    )
    result = ingest_claim_basics_message(
        _normalized("在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门", ext=ext, msg_id="m_m2"),
        classify_wecom_intent("在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门"),
    )
    assert result["active_case_outcome"] == "claim_c1_sent"
    stored = get_case_by_id(result["case_id"])
    assert stored is not None
    assert is_accident_basics_complete(stored) is True


def test_c1_copy_safe():
    case = {
        "known_facts": {
            "accident_datetime": "今天上午10点",
            "accident_location": "Irvine Blvd",
            "accident_description": "对方变道刮蹭",
        },
        "collected_fields": ["accident_datetime", "accident_location", "accident_description"],
    }
    reply = build_claim_stage_complete_c1_reply(case)
    assert "【事故信息已记录 ✅】" in reply
    assert "补充事故资料" in reply or "照片" in reply
    assert "不代表" in reply
    assert "http" not in reply.lower()
    _assert_no_forbidden_copy(reply)


def test_basics_complete_progress_inquiry_no_generic_menu():
    ext = "wm_done"
    text = "今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门"
    ingest_claim_basics_message(_normalized(text, ext=ext, msg_id="m_done1"), classify_wecom_intent(text))
    result = ingest_claim_basics_message(_normalized("进度", ext=ext, msg_id="m_done2"), classify_wecom_intent("进度"))
    reply = result["reply_text"] or ""
    assert "【事故信息已记录 ✅】" in reply or "事故信息已记录" in reply
    assert "照片" in reply
    assert "http" not in reply.lower()
    assert "请选择您要办理的事项" not in reply


def test_injury_phrase_manual_handle_hint():
    normalized = _normalized("我要理赔，有人受伤", msg_id="m_inj")
    intent = classify_wecom_intent("我要理赔，有人受伤")
    result = ingest_claim_basics_message(normalized, intent)
    reply = result["reply_text"] or ""
    assert "受伤" in reply or "紧急" in reply
    stored = get_case_by_id(result["case_id"]) or {}
    assert result.get("needs_broker_manual_handle") or stored.get("manual_handle")
    _assert_no_forbidden_copy(reply)


def test_claim_question_safe_reply_no_liability_promise():
    normalized = _normalized("出事故了怎么办")
    intent = classify_wecom_intent("出事故了怎么办")
    assert should_route_claim_question_safe_reply(normalized, intent) is True
    assert should_route_claim_guided_workflow(normalized, intent) is False
    result = ingest_claim_question_safe_reply(normalized)
    reply = result["reply_text"] or build_claim_question_safe_reply()
    assert "不能判断" in reply or "不能" in reply
    assert result["case_created"] is False
    _assert_no_forbidden_copy(reply)


def test_restart_add_car_not_claim(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-h5-secret")
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_restart", "重新加车", ext="wm_restart_av")]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    assert results[0]["internal_intent"] == "add_car"
    assert results[0].get("service_lane") != SERVICE_LANE_CLAIM


def test_hello_no_active_case_no_forced_claim(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_hi", "你好", ext="wm_hello_claim")]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    assert results[0]["guided_menu_required"] is True
    assert results[0]["case_created"] is False


def test_forbidden_constants_present():
    assert "已经帮您报案" in CLAIM_FORBIDDEN_AUTOMATION_CLAIMS
    assert "理赔已经提交" in CLAIM_FORBIDDEN_AUTOMATION_CLAIMS


def test_minimal_lane_claim_lite_still_routable_for_question_heavy_message():
    text = "我刚刚在 405 附近撞车了，现在怎么办？要不要报保险？"
    normalized = _normalized(text, msg_id="m_lite")
    intent = classify_wecom_intent(text)
    assert should_route_claim_guided_workflow(normalized, intent) is False
    assert should_route_claim_question_safe_reply(normalized, intent) is False
