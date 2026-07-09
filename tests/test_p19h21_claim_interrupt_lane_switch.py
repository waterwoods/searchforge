"""P19H-2.1 — Claim interrupt / lane switch during active Add Vehicle."""

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
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_question_safe_reply,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
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


def _assert_no_deferral(reply: str) -> None:
    assert _DEFER_EN not in reply
    assert _DEFER_ZH not in reply


def _assert_no_filed_language(reply: str) -> None:
    assert "已经报案" not in reply
    assert "理赔已经提交" not in reply


# --- A. Active Add Vehicle + Claim start ---


def test_a_active_add_vehicle_woyao_claim_lane_switch():
    _save_active_add_car_case()
    text = "我要理赔"
    result = ingest_claim_basics_message(_normalized(text, msg_id="a1"), classify_wecom_intent(text))
    reply = result["reply_text"] or ""
    assert result["active_case_outcome"] == "claim_lane_switch_prompt"
    assert result["case_created"] is False
    assert "【理赔资料收集】" in reply
    assert "加车资料流程正在进行" in reply
    assert "开始理赔" in reply
    assert "继续加车" in reply
    assert "联系陈总" in reply
    assert "这不代表已经向保险公司正式报案" in reply or "不代表已经正式报案" in reply
    _assert_no_deferral(reply)
    _assert_no_filed_language(reply)


# --- B. Active Add Vehicle + 开始理赔 ---


def test_b_active_add_vehicle_kaishi_claim_starts_not_deferred():
    _save_active_add_car_case()
    text = "开始理赔"
    result = ingest_claim_basics_message(_normalized(text, msg_id="b1"), classify_wecom_intent(text))
    reply = result["reply_text"] or ""
    assert result["case_created"] is True
    assert result.get("service_lane") == SERVICE_LANE_CLAIM or get_case_by_id(result["case_id"]).get(
        "service_lane"
    ) == SERVICE_LANE_CLAIM
    _assert_no_deferral(reply)
    assert "【理赔资料收集】" in reply or "陈总办公室的值班助手" in reply


# --- C. Active Add Vehicle + accident phrase ---


def test_c_active_add_vehicle_accident_phrase_lane_switch():
    _save_active_add_car_case()
    text = "我发生车祸了"
    result = ingest_claim_basics_message(_normalized(text, msg_id="c1"), classify_wecom_intent(text))
    reply = result["reply_text"] or ""
    assert result["active_case_outcome"] == "claim_lane_switch_prompt"
    _assert_no_deferral(reply)
    assert "【理赔资料收集】" in reply


# --- D. Active Add Vehicle + injury ---


def test_d_active_add_vehicle_injury_safety_manual():
    _save_active_add_car_case()
    text = "有人受伤了，我要理赔"
    result = ingest_claim_basics_message(_normalized(text, msg_id="d1"), classify_wecom_intent(text))
    reply = result["reply_text"] or ""
    assert result["active_case_outcome"] == "claim_injury_manual_handle"
    assert "安全" in reply or "紧急" in reply or "受伤" in reply or "陈总" in reply
    _assert_no_deferral(reply)
    assert "第 1 步完成" not in reply
    _assert_no_filed_language(reply)


# --- E. Active Add Vehicle + claim question ---


def test_e_active_add_vehicle_claim_question_safe_reply():
    _save_active_add_car_case()
    text = "出事故了怎么办"
    normalized = _normalized(text, msg_id="e1")
    result = ingest_claim_question_safe_reply(normalized)
    reply = result["reply_text"] or ""
    assert result["case_created"] is False
    assert "责任" in reply or "coverage" in reply
    assert "开始理赔" in reply or "继续加车" in reply
    _assert_no_deferral(reply)


# --- F. Continue Add Vehicle ---


def test_f_continue_add_vehicle_not_claim():
    ext = "wm_av_cont"
    _save_active_add_car_case(ext=ext)
    text = "继续加车"
    from services.fiqa_api.wecom.claim_basics import ingest_claim_lane_switch_choice

    choice = ingest_claim_lane_switch_choice(_normalized(text, ext=ext, msg_id="f1"))
    reply = choice["reply_text"] or ""
    assert "加车" in reply or "进度" in reply
    assert choice["active_case_outcome"] in ("claim_lane_switch_continue", "add_vehicle_progress_card")


# --- G. Add Vehicle regression ---


def test_g_restart_add_car_still_works(monkeypatch):
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
        return [
            {
                "msgid": "m_restart",
                "open_kfid": "wktest001",
                "external_userid": "wm_restart_h21",
                "origin": 3,
                "msgtype": "text",
                "text": {"content": "重新加车"},
            }
        ]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    assert results[0]["internal_intent"] == "add_car"
    assert results[0].get("service_lane") != SERVICE_LANE_CLAIM


# --- H. Generic secondary-topic still works ---


def test_h_generic_secondary_topic_still_defers(monkeypatch):
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

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    reply = results[0].get("reply_text") or ""
    assert _DEFER_EN in reply or _DEFER_ZH in reply


# --- I. No active case + Claim start ---


def test_i_no_active_case_claim_start_still_works():
    text = "我要理赔"
    result = ingest_claim_basics_message(_normalized(text, ext="wm_no_av", msg_id="i1"), classify_wecom_intent(text))
    assert result["case_created"] is True
    stored = get_case_by_id(result["case_id"])
    assert stored.get("service_lane") == SERVICE_LANE_CLAIM
    assert "陈总办公室的值班助手" in (result["reply_text"] or "") or "【理赔资料收集】" in (result["reply_text"] or "")
