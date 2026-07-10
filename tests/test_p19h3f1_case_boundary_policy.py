"""P19H-3f-1 — Case boundary policy + smooth new customer claim flow."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import get_case_by_id, save_case
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.claim_workbench_display import (
    build_claim_case_brief,
    build_claim_display_status,
    build_wecom_media_intake_display_status,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_WECOM_MEDIA_INTAKE
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_holding_ack,
    ingest_claim_injury_quick_reply,
    ingest_claim_question_safe_reply,
    should_route_claim_guided_workflow,
    should_route_claim_holding_ack,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_FORBIDDEN_AUTOMATION_CLAIMS,
    SERVICE_LANE_CLAIM,
    customer_copy_contains_forbidden_phrase,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message
from services.fiqa_api.wecom.reply import (
    build_claim_holding_ack_reply,
    build_claim_start_card_reply,
    build_claim_wecom_media_reply,
)
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event
from services.fiqa_api.wecom.workflow_scenario_simulator import (
    SCENARIO_NC2_RANDOM_NARRATIVE,
    SCENARIO_NC3_EXPLICIT_START,
    SCENARIO_NC4_FULL_FLOW,
    SCENARIO_NC5_INJURY_ALONE,
    SCENARIO_NC6_INSURANCE_QUESTION,
    run_predefined_scenario,
)

_BASICS_TEXT = "今天下午三点，在 Costco 停车场出口被后车追尾，后保险杠被撞了。"
_FORBIDDEN_SNIPPETS = (
    "已经报案",
    "理赔已经提交",
    "已联系保险公司",
    "是对方责任",
    "一定会赔",
    "已报案",
    "对方全责",
    "已受理",
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
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


@pytest.fixture
def cfg(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "sec")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    return load_wecom_kf_config()


def _msg(msg_id: str, content: str, *, ext: str = "wm_p19h3f1") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": ext,
        "origin": 3,
        "msgtype": "text",
        "text": {"content": content},
    }


def _normalized(text: str, *, ext: str = "wm_p19h3f1", msg_id: str = "m1") -> dict:
    return normalize_text_message(_msg(msg_id, text, ext=ext))


def _image_msg(msg_id: str, *, ext: str = "wm_p19h3f1_photo") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": ext,
        "origin": 3,
        "msgtype": "image",
        "image": {"media_id": f"media_{msg_id}"},
    }


def _fake_download(_cfg, *, media_id: str, msgtype: str) -> WeComMediaDownloadResult:
    return WeComMediaDownloadResult(
        content=b"\xff\xd8\xff",
        content_type="image/jpeg",
        filename="photo.jpg",
    )


def _fake_upload(**_kwargs) -> dict:
    return {
        "storage_uri": "gs://test-bucket/wecom/photo.jpg",
        "mime_type": "image/jpeg",
        "size_bytes": 3,
    }


def _claim_cases() -> list[dict]:
    return [c for c in list_all_cases_for_read() if c.get("service_lane") == SERVICE_LANE_CLAIM]


def _assert_no_forbidden_copy(text: str) -> None:
    scrubbed = (text or "").replace("不代表 claim 已正式提交", "")
    assert customer_copy_contains_forbidden_phrase(scrubbed) is None
    for phrase in _FORBIDDEN_SNIPPETS:
        assert phrase not in scrubbed


def test_01_random_photo_no_claim(cfg):
    norm = normalize_media_message(_image_msg("img_rand", ext="wm_nc1"))
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    assert result["active_case_outcome"] == "media_unassigned"
    assert _claim_cases() == []
    reply = result["reply_text"] or ""
    assert "我要理赔" in reply
    assert "没有开始事故记录前" in reply
    assert "事故记录已开始" not in reply
    case = get_case_by_id(result["case_id"]) or {}
    assert case.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE
    _assert_no_forbidden_copy(reply)


def test_02_random_narrative_no_formal_claim():
    text = "昨晚 Costco 被追尾了，后保险杠有点坏。"
    normalized = _normalized(text, msg_id="m_narr")
    intent = classify_wecom_intent(text)
    assert should_route_claim_holding_ack(normalized, intent) is True
    assert should_route_claim_guided_workflow(normalized, intent) is False
    result = ingest_claim_holding_ack(normalized)
    assert result["case_created"] is False
    assert _claim_cases() == []
    reply = result["reply_text"] or ""
    assert "我要理赔" in reply
    assert "没有开始事故记录前" in reply
    assert "事故记录已开始" not in reply
    _assert_no_forbidden_copy(reply)


def test_03_explicit_woyao_claim_creates_case():
    normalized = _normalized("我要理赔", msg_id="m_start")
    intent = classify_wecom_intent("我要理赔")
    assert should_route_claim_guided_workflow(normalized, intent) is True
    result = ingest_claim_basics_message(normalized, intent)
    assert result["case_created"] is True
    assert result["service_lane"] == SERVICE_LANE_CLAIM
    stored = get_case_by_id(result["case_id"]) or {}
    assert stored.get("service_lane") == SERVICE_LANE_CLAIM
    reply = result.get("reply_text") or ""
    assert "【事故记录已开始 ✅】" in reply
    assert "提交给陈总审核" in reply
    assert "这只是资料收集，不代表已经正式向保险公司报案。" in reply


def test_04_start_card_only_after_explicit_start():
    holding = build_claim_holding_ack_reply()
    assert "事故记录已开始" not in holding
    start = build_claim_start_card_reply()
    assert "事故记录已开始" in start
    assert "提交给陈总审核" in start
    assert "这只是资料收集，不代表已经正式向保险公司报案。" in start
    result = ingest_claim_basics_message(
        _normalized("我要理赔", msg_id="m_sc"),
        classify_wecom_intent("我要理赔"),
    )
    reply = result.get("reply_text") or ""
    assert "事故记录已开始" in reply
    assert "提交给陈总审核" in reply
    assert "这只是资料收集，不代表已经正式向保险公司报案。" in reply


def test_13_formal_claim_paths_emit_start_card():
    """P19H-3f-1b — any WeCom explicit-start path must emit Start Card."""
    for text in ("我要理赔", "开始理赔", "新事故"):
        ext = f"wm_ceremony_{text}"
        result = ingest_claim_basics_message(
            _normalized(text, ext=ext, msg_id=f"m_{text}"),
            classify_wecom_intent(text),
        )
        assert result.get("case_created") is True, text
        reply = result.get("reply_text") or ""
        assert "【事故记录已开始 ✅】" in reply, text
        assert "这只是资料收集，不代表已经正式向保险公司报案。" in reply, text


def test_05_injury_quick_reply_alone_no_case():
    norm = normalize_text_message(
        {
            "msgid": "inj_alone",
            "open_kfid": "wktest001",
            "external_userid": "wm_inj_alone",
            "origin": 3,
            "msgtype": "text",
            "text": {"content": ""},
            "menu_id": "claim_injury_no",
        }
    )
    result = ingest_claim_injury_quick_reply(norm, injury_value="no")
    assert result["case_created"] is False
    assert result["active_case_outcome"] == "claim_injury_holding_gate"
    assert _claim_cases() == []
    assert "事故记录已开始" not in (result.get("reply_text") or "")


def test_06_injury_inside_active_claim_updates_status():
    ext = "wm_inj_active"
    ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext, msg_id="m_s"),
        classify_wecom_intent("我要理赔"),
    )
    norm = normalize_text_message(
        {
            "msgid": "inj_in",
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "text": {"content": ""},
            "menu_id": "claim_injury_no",
        }
    )
    result = ingest_claim_injury_quick_reply(norm, injury_value="no")
    case = get_case_by_id(str(result["case_id"])) or {}
    assert case.get("known_facts", {}).get("injury_status") == "no"
    assert "大概什么时候" in (result.get("reply_text") or "")


def test_07_no_injury_then_story_timeline_and_brief():
    ext = "wm_nc4_flow"
    ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext, msg_id="m1"),
        classify_wecom_intent("我要理赔"),
    )
    ingest_claim_injury_quick_reply(
        normalize_text_message(
            {
                "msgid": "m2",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "text",
                "text": {"content": ""},
                "menu_id": "claim_injury_no",
            }
        ),
        injury_value="no",
    )
    result = ingest_claim_basics_message(
        _normalized(_BASICS_TEXT, ext=ext, msg_id="m3"),
        classify_wecom_intent(_BASICS_TEXT),
    )
    case = get_case_by_id(str(result["case_id"])) or {}
    timeline = case.get("claim_timeline") or []
    types = {e.get("event_type") for e in timeline}
    assert "claim_started" in types
    assert "customer_text" in types
    assert "basics_complete" in types
    brief = build_claim_case_brief(case)
    assert (brief.get("summary") or "").strip()
    assert (brief.get("next_best_question") or "").strip()
    _assert_no_forbidden_copy(brief.get("summary") or "")


def test_08_active_claim_photo_attaches(cfg):
    ext = "wm_photo_bind"
    ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext, msg_id="m_s"),
        classify_wecom_intent("我要理赔"),
    )
    norm = normalize_media_message(_image_msg("img_bind", ext=ext))
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    assert result["service_lane"] == SERVICE_LANE_CLAIM
    case = get_case_by_id(str(result["case_id"])) or {}
    timeline = case.get("claim_timeline") or []
    assert any(e.get("event_type") == "customer_photo" for e in timeline)
    reply = result["reply_text"] or ""
    assert "已记到这份事故记录里" in reply
    assert "状态" in reply


def test_09_insurance_question_no_claim():
    text = "这种情况要不要报保险？"
    normalized = _normalized(text, msg_id="m_q")
    intent = classify_wecom_intent(text)
    result = ingest_claim_question_safe_reply(normalized)
    assert result["case_created"] is False
    assert _claim_cases() == []
    _assert_no_forbidden_copy(result.get("reply_text") or "")


def test_10_forbidden_language_absent():
    samples = [
        build_claim_start_card_reply(),
        build_claim_holding_ack_reply(),
        build_claim_wecom_media_reply(tier="C"),
    ]
    for sample in samples:
        _assert_no_forbidden_copy(sample)
    for phrase in CLAIM_FORBIDDEN_AUTOMATION_CLAIMS:
        assert phrase not in " ".join(samples)


def test_11_add_vehicle_unaffected(cfg, monkeypatch):
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-h5-secret")
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    saved = save_case(
        "add car",
        {
            "issue_category": "add_car_quote",
            "urgency": "medium",
            "manual_followup_needed": True,
            "broker_next_step": "Review",
            "client_prep": "",
            "client_reply_draft": "",
        },
        service_lane=SERVICE_LANE_ADD_CAR,
    )
    ext = "wm_addcar_ok"

    def pull(_cfg, *, token, open_kf_id):
        return [_msg("m_add", "重新加车", ext=ext)]

    results = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    assert results[0]["internal_intent"] == "add_car"
    assert results[0].get("service_lane") != SERVICE_LANE_CLAIM
    assert saved["case_id"]


def test_12_workbench_labels():
    claim_case = {
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "accident_basics_in_progress",
        "guided_workflow_state": "collecting_text",
        "known_facts": {},
        "collected_fields": [],
    }
    assert "记录中" in build_claim_display_status(claim_case)
    media_case = {"service_lane": SERVICE_LANE_WECOM_MEDIA_INTAKE}
    media_status = build_wecom_media_intake_display_status(media_case)
    assert "技术收件记录" in media_status
    assert "不是正式 case" in media_status


def test_nc2_scenario_passes():
    name, steps = SCENARIO_NC2_RANDOM_NARRATIVE
    result = run_predefined_scenario(name, list(steps), external_userid="wm_nc2")
    assert result.passed, result.summary


def test_nc3_scenario_passes():
    name, steps = SCENARIO_NC3_EXPLICIT_START
    result = run_predefined_scenario(name, list(steps), external_userid="wm_nc3")
    assert result.passed, result.summary


def test_nc4_scenario_passes():
    name, steps = SCENARIO_NC4_FULL_FLOW
    result = run_predefined_scenario(name, list(steps), external_userid="wm_nc4")
    assert result.passed, result.summary


def test_nc5_scenario_passes():
    name, steps = SCENARIO_NC5_INJURY_ALONE
    result = run_predefined_scenario(name, list(steps), external_userid="wm_nc5")
    assert result.passed, result.summary


def test_nc6_scenario_passes():
    name, steps = SCENARIO_NC6_INSURANCE_QUESTION
    result = run_predefined_scenario(name, list(steps), external_userid="wm_nc6")
    assert result.passed, result.summary
