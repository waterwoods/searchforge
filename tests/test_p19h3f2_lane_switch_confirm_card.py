"""P19H-3f-2 — Add Car → Claim lane switch confirm card."""

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
    ingest_claim_holding_ack,
    ingest_claim_lane_switch_choice,
    ingest_claim_lane_switch_confirm,
    ingest_claim_question_safe_reply,
    should_route_claim_holding_ack,
)
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.reply import build_claim_start_card_reply

_DEFER_EN = "Let's finish your current request first"
_DEFER_ZH = "先完成当前请求"
_START_MARKER = "【事故记录已开始 ✅】"


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


def _assert_no_start_card(reply: str | None, menu_payload: dict | None) -> None:
    combined = (reply or "") + str(menu_payload or "")
    assert _START_MARKER not in combined


def _lane_switch_prompt(text: str, *, ext: str = "wm_av_active", msg_id: str = "m1") -> dict:
    return ingest_claim_basics_message(
        _normalized(text, ext=ext, msg_id=msg_id),
        classify_wecom_intent(text),
    )


def test_active_add_car_xianzai_jinxing_claim_confirm_card():
    _save_active_add_car_case()
    result = _lane_switch_prompt("我现在要进行理赔", msg_id="t1")
    reply = result["reply_text"] or ""
    assert result["active_case_outcome"] == "claim_lane_switch_prompt"
    assert result["case_created"] is False
    assert result.get("menu_payload") is not None
    assert "事故/理赔记录" in reply
    assert "暂停当前加车资料收集" in reply
    assert "开始事故记录" in reply
    assert "继续加车" in reply
    assert "这只是资料收集，不代表已经正式向保险公司报案。" in reply
    _assert_no_deferral(reply)
    _assert_no_start_card(reply, result.get("menu_payload"))


def test_active_add_car_woyao_claim_confirm_card():
    _save_active_add_car_case(ext="wm_woyao")
    result = _lane_switch_prompt("我要理赔", ext="wm_woyao", msg_id="t2")
    reply = result["reply_text"] or ""
    assert result["active_case_outcome"] == "claim_lane_switch_prompt"
    assert result["case_created"] is False
    _assert_no_start_card(reply, result.get("menu_payload"))


def test_confirm_start_accident_record_creates_claim_start_card():
    ext = "wm_confirm"
    add_car = _save_active_add_car_case(ext=ext)
    _lane_switch_prompt("我要理赔", ext=ext, msg_id="t3a")
    result = ingest_claim_lane_switch_choice(_normalized("开始事故记录", ext=ext, msg_id="t3b"))
    reply = result["reply_text"] or ""
    assert result["case_created"] is True
    assert result["active_case_outcome"] == "claim_start_card_sent"
    assert _START_MARKER in reply
    assert "提交给陈总审核" in reply
    assert result.get("menu_payload") is not None
    assert get_case_by_id(add_car["case_id"]) is not None
    claim = get_case_by_id(result["case_id"])
    assert claim.get("service_lane") == SERVICE_LANE_CLAIM


def test_cancel_continue_add_car_no_claim():
    ext = "wm_cancel"
    add_car = _save_active_add_car_case(ext=ext)
    _lane_switch_prompt("我要理赔", ext=ext, msg_id="t4a")
    result = ingest_claim_lane_switch_choice(_normalized("继续加车", ext=ext, msg_id="t4b"))
    reply = result["reply_text"] or ""
    assert result["case_created"] is False
    assert "继续完成加车资料" in reply
    assert get_case_by_id(add_car["case_id"]) is not None
    _assert_no_start_card(reply, None)


def test_active_add_car_random_accident_narrative_no_confirm():
    _save_active_add_car_case(ext="wm_narr")
    text = "昨晚 Costco 被追尾了，后保险杠有点坏"
    intent = classify_wecom_intent(text)
    norm = _normalized(text, ext="wm_narr", msg_id="t5")
    assert should_route_claim_holding_ack(norm, intent) is True
    result = ingest_claim_holding_ack(norm)
    assert result["case_created"] is False
    assert result["active_case_outcome"] == "claim_holding_ack"
    _assert_no_start_card(result.get("reply_text"), None)


def test_active_add_car_insurance_question_no_claim():
    _save_active_add_car_case(ext="wm_q")
    text = "这种情况要不要报保险？"
    result = ingest_claim_question_safe_reply(_normalized(text, ext="wm_q", msg_id="t6"))
    assert result["case_created"] is False
    _assert_no_start_card(result.get("reply_text"), None)


def test_repeated_confirm_does_not_duplicate_claim():
    ext = "wm_idem"
    _save_active_add_car_case(ext=ext)
    _lane_switch_prompt("我要理赔", ext=ext, msg_id="t7a")
    first = ingest_claim_lane_switch_choice(_normalized("开始事故记录", ext=ext, msg_id="t7b"))
    second = ingest_claim_lane_switch_choice(_normalized("开始事故记录", ext=ext, msg_id="t7c"))
    assert first["case_created"] is True
    assert second["case_created"] is False
    assert first["case_id"] == second["case_id"]


def test_no_active_add_car_explicit_claim_still_direct_start():
    text = "我要理赔"
    result = ingest_claim_basics_message(
        _normalized(text, ext="wm_no_av", msg_id="t8"),
        classify_wecom_intent(text),
    )
    assert result["case_created"] is True
    assert _START_MARKER in (result["reply_text"] or "") or _START_MARKER in str(
        result.get("menu_payload") or ""
    )


def test_kaishi_claim_during_add_car_shows_confirm_not_start():
    _save_active_add_car_case(ext="wm_kaishi")
    result = _lane_switch_prompt("开始理赔", ext="wm_kaishi", msg_id="t9")
    assert result["active_case_outcome"] == "claim_lane_switch_prompt"
    assert result["case_created"] is False
    _assert_no_start_card(result.get("reply_text"), result.get("menu_payload"))


def test_lane_switch_confirm_click_creates_claim():
    ext = "wm_click"
    _save_active_add_car_case(ext=ext)
    _lane_switch_prompt("我要理赔", ext=ext, msg_id="t10a")
    result = ingest_claim_lane_switch_confirm(
        {
            **_normalized("", ext=ext, msg_id="t10b"),
            "menu_id": "lane_switch_start_claim",
        }
    )
    assert result["case_created"] is True
    assert _START_MARKER in (result["reply_text"] or "")
