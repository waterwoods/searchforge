"""P19H-3f-4 — Unified Status Card + text frame style."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    patch_case_known_facts,
    save_case,
    update_claim_workflow_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_status_request,
    is_claim_guided_start_message,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM, customer_copy_contains_forbidden_phrase
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent, is_claim_status_request
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message
from services.fiqa_api.wecom.reply import (
    build_claim_end_card_reply,
    build_claim_identity_broker_confirm_reply,
    build_claim_lane_switch_reply,
    build_claim_start_card_reply,
    build_claim_start_h5_intake_card_payload,
    build_claim_status_card_reply,
    build_claim_wecom_media_reply,
    build_h5_submit_confirmation_reply,
    frame_wecom_card,
)
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

_FORBIDDEN = (
    "已报案",
    "保险公司已收到",
    "一定会赔",
    "对方全责",
    "coverage approved",
    "claim approved",
)


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
    os.environ["WECOM_B0_ACTIVE_WORKSPACE"] = "1"
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)
    load_wecom_kf_config.cache_clear()


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


def _normalized(text: str, *, ext: str = "wm_p19h3f4", msg_id: str = "m1") -> dict:
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
        "broker_next_step": "Collect basics.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "claim_phase": "claim_started",
    }


def _open_claim(*, ext: str = "wm_p19h3f4", injury_no: bool = False) -> dict:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    facts: dict[str, str] = {
        "accident_datetime": "7月8日",
        "accident_location": "Santa Ana 红绿灯",
        "accident_description": "后车追尾",
    }
    if injury_no:
        facts["injury_status"] = "no"
    patch_case_known_facts(cid, facts)
    update_claim_workflow_state(
        cid,
        claim_phase="accident_basics_in_progress",
        guided_workflow_state="collecting_text",
    )
    from services.fiqa_api.inbox_triage.case_store import append_follow_up_message

    append_follow_up_message(
        cid,
        "basics",
        {
            **_claim_stub(),
            "collected_fields": [
                "accident_datetime",
                "accident_location",
                "accident_description",
            ],
        },
    )
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read

    return get_case_for_read(cid) or saved


def test_frame_wecom_card_wraps_title_and_body():
    framed = frame_wecom_card("【测试】", ["第一行", "第二行"], footer_lines=["提醒：", "免责声明"])
    assert framed.startswith("━━━━━━━━━━━━")
    assert framed.endswith("━━━━━━━━━━━━")
    assert "【测试】" in framed
    assert "第一行" in framed
    assert "提醒：" in framed


def test_start_card_has_frame_and_required_phrases():
    """Production Start Card — H5-first copy (P19H-3h card design system)."""
    reply = build_claim_start_card_reply()
    assert "━━━━━━━━━━━━" in reply
    assert "【事故记录已开始 ✅】" in reply
    assert "提交给陈总审核" in reply
    assert "打开资料填写页面" not in reply  # plain-text fallback; H5 button is on msgmenu
    assert reply.count("这只是资料收集，不代表已经正式向保险公司报案。") == 1
    assert "有没有受伤" not in reply


def test_h5_start_card_menu_has_primary_cta_and_single_disclaimer():
    menu = build_claim_start_h5_intake_card_payload(h5_url="https://example.test/task/claim/h5t1.x")
    head = menu["head_content"]
    assert "【事故记录已开始 ✅】" in head
    assert "提交给陈总审核" in head
    assert head.count("这只是资料收集，不代表已经正式向保险公司报案。") == 1
    assert menu["list"][0]["view"]["content"] == "打开资料填写页面"
    assert "这只是资料收集" not in (menu.get("tail_content") or "")


def test_submit_confirmation_distinct_from_broker_done():
    reply = build_h5_submit_confirmation_reply()
    assert "【资料已提交 ✅】" in reply
    assert "陈总已确认" not in reply
    assert reply.count("这只是资料收集，不代表已经正式向保险公司报案。") == 1


def test_end_card_has_frame_and_required_phrases():
    reply = build_claim_end_card_reply()
    assert "━━━━━━━━━━━━" in reply
    assert "【陈总已确认 ✅】" in reply
    assert "收集阶段已结束" in reply


def test_collision_resolver_card_has_frame_and_choices():
    reply = build_claim_identity_broker_confirm_reply(multiple_open=False)
    assert "━━━━━━━━━━━━" in reply
    assert "【请确认】" in reply
    assert "继续当前事故" in reply
    assert "开始新的事故记录" in reply
    assert "联系陈总" in reply


def test_lane_switch_confirm_card_has_frame_and_choices():
    reply = build_claim_lane_switch_reply()
    assert "━━━━━━━━━━━━" in reply
    assert "开始事故记录" in reply
    assert "继续加车" in reply


def test_claim_status_card_sections_and_no_forbidden_language():
    case = _open_claim(injury_no=True)
    case = dict(case)
    case["case_attachments"] = [
        {"mime_type": "image/jpeg", "msgtype": "image", "source": "wecom"},
    ]
    reply = build_claim_status_card_reply(case)
    assert "【当前状态】" in reply
    assert "已收到" in reply
    assert "还缺" in reply
    assert "下一步" in reply
    assert "没有受伤" in reply
    assert "照片：1 张" in reply
    assert not customer_copy_contains_forbidden_phrase(reply)
    for phrase in _FORBIDDEN:
        assert phrase not in reply


def test_status_request_with_active_claim_returns_status_card():
    _open_claim()
    norm = _normalized("进度", msg_id="m_status")
    intent = classify_wecom_intent("进度")
    result = ingest_claim_status_request(norm, intent)
    assert result["active_case_outcome"] == "claim_status_card"
    assert "【当前状态】" in (result.get("reply_text") or "")


def test_status_request_without_active_claim_does_not_create_claim():
    norm = _normalized("进度", ext="wm_no_claim", msg_id="m_no_claim")
    intent = classify_wecom_intent("进度")
    before = len(list_all_cases_for_read())
    result = ingest_claim_status_request(norm, intent)
    after = len(list_all_cases_for_read())
    assert after == before
    assert result["active_case_outcome"] == "claim_status_no_active"
    assert "我要理赔" in (result.get("reply_text") or "")


def test_basics_complete_reply_is_framed_stage_complete():
    norm = _normalized("我要理赔", msg_id="m_start")
    intent = classify_wecom_intent("我要理赔")
    ingest_claim_basics_message(norm, intent)
    norm2 = _normalized(
        "今天上午10点，在 Irvine Blvd 附近，对方变道刮到我左前门。",
        msg_id="m_basics",
    )
    result = ingest_claim_basics_message(norm2, classify_wecom_intent(norm2["text"]))
    reply = result.get("reply_text") or ""
    assert "【事故信息已记录 ✅】" in reply
    assert "━━━━━━━━━━━━" in reply


def test_photo_ack_short_without_full_status_card():
    ack = build_claim_wecom_media_reply(tier="A")
    assert "收到照片" in ack
    assert "【当前状态】" not in ack
    assert "进度" in ack or "链接" in ack


def test_random_text_does_not_create_claim():
    norm = _normalized("看看这个", ext="wm_random", msg_id="m_random")
    intent = classify_wecom_intent("看看这个")
    assert not is_claim_status_request("看看这个")
    before = len(list_all_cases_for_read())
    from services.fiqa_api.wecom.claim_basics import ingest_claim_holding_ack

    ingest_claim_holding_ack(norm)
    assert len(list_all_cases_for_read()) == before


def test_explicit_start_not_status_request():
    assert is_claim_guided_start_message("我要理赔")
    assert not is_claim_status_request("我要理赔")
    assert is_claim_status_request("理赔进度")


def test_slice_status_request_end_to_end():
    _open_claim(ext="wm_slice_status")
    cfg = load_wecom_kf_config()
    results = process_kf_msg_or_event(
        cfg,
        callback_token="t",
        open_kf_id="wktest001",
        pull_messages=lambda *_a, **_k: [
            {
                "msgid": "m_slice_status",
                "open_kfid": "wktest001",
                "external_userid": "wm_slice_status",
                "origin": 3,
                "msgtype": "text",
                "text": {"content": "进度"},
            }
        ],
    )
    assert results
    assert results[0].get("active_case_outcome") == "claim_status_card"
    assert "【当前状态】" in (results[0].get("reply_text") or "")


def test_random_photo_does_not_create_claim():
    cfg = load_wecom_kf_config()
    before = len(list_all_cases_for_read())
    process_kf_msg_or_event(
        cfg,
        callback_token="t",
        open_kf_id="wktest001",
        pull_messages=lambda *_a, **_k: [
            {
                "msgid": "m_photo_rand",
                "open_kfid": "wktest001",
                "external_userid": "wm_photo_rand",
                "origin": 3,
                "msgtype": "image",
                "image": {"media_id": "mid1"},
            }
        ],
    )
    assert len(list_all_cases_for_read()) == before
