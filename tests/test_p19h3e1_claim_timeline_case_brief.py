"""P19H-3e-1 — Claim story timeline + Case Brief foundation."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    append_claim_timeline_event,
    bind_case_channel_identity,
    build_claim_timeline_event,
    get_case_by_id,
    save_case,
    update_claim_workflow_state,
)
from services.fiqa_api.inbox_triage.claim_workbench_display import (
    build_claim_case_brief,
    claim_evidence_copy_is_broker_safe,
    enrich_claim_for_workbench,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import (
    ingest_claim_basics_message,
    ingest_claim_injury_quick_reply,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    SERVICE_LANE_CLAIM,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message
from services.fiqa_api.wecom.reply import (
    build_claim_start_card_reply,
    build_claim_wecom_media_reply,
    build_media_intake_reply,
)

_BASICS_TEXT = "今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门"
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
    return load_wecom_kf_config()


def _msg(msg_id: str, content: str, *, ext: str = "wm_p19h3e1") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": ext,
        "origin": 3,
        "msgtype": "text",
        "text": {"content": content},
    }


def _normalized(text: str, *, ext: str = "wm_p19h3e1", msg_id: str = "m1") -> dict:
    return normalize_text_message(_msg(msg_id, text, ext=ext))


def _claim_stub(**known_facts: str) -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Claim guided workflow",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "collected_fields": list(known_facts.keys()),
        "still_needed_fields": [],
        "known_facts": dict(known_facts),
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        "guided_workflow_state": "collecting_text",
    }


def _start_claim(ext: str = "wm_p19h3e1") -> str:
    intent = classify_wecom_intent("我要理赔")
    result = ingest_claim_basics_message(_normalized("我要理赔", ext=ext, msg_id="m_start"), intent)
    return str(result["case_id"])


def test_01_timeline_text_append():
    case_id = _start_claim()
    intent = classify_wecom_intent(_BASICS_TEXT)
    ingest_claim_basics_message(_normalized(_BASICS_TEXT, msg_id="m_text2"), intent)
    case = get_case_by_id(case_id) or {}
    timeline = case.get("claim_timeline") or []
    text_events = [e for e in timeline if e.get("event_type") == "customer_text"]
    assert text_events
    last = text_events[-1]
    assert last.get("message_id") == "m_text2"
    assert _BASICS_TEXT in str(last.get("text") or "")
    assert last.get("actor") == "customer"
    assert last.get("source_channel") == "wecom"


def test_02_timeline_dedup_message_id():
    case_id = _start_claim()
    event = build_claim_timeline_event(
        event_type="customer_text",
        message_id="dup_mid",
        text="hello",
    )
    append_claim_timeline_event(case_id, event)
    append_claim_timeline_event(case_id, event)
    case = get_case_by_id(case_id) or {}
    matches = [
        e for e in (case.get("claim_timeline") or [])
        if e.get("message_id") == "dup_mid"
    ]
    assert len(matches) == 1


def test_03_image_bind_appends_timeline(cfg, monkeypatch):
    case_id = _start_claim()
    bind_case_channel_identity(case_id, wecom_external_userid="wm_p19h3e1")
    update_claim_workflow_state(case_id, claim_phase=CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE)

    def _fake_download(*_a, **_k):
        return WeComMediaDownloadResult(content=b"\xff\xd8\xff", content_type="image/jpeg", filename="a.jpg")

    def _fake_upload(**_k):
        return {"storage_uri": "gs://bucket/x.jpg", "mime_type": "image/jpeg", "size_bytes": 3}

    monkeypatch.setattr(
        "services.fiqa_api.wecom.media_intake.download_wecom_media",
        _fake_download,
    )
    monkeypatch.setattr(
        "services.fiqa_api.wecom.media_intake.upload_wecom_media_to_gcs",
        _fake_upload,
    )

    media_norm = normalize_media_message(
        {
            "msgid": "img_bind_1",
            "open_kfid": "wktest001",
            "external_userid": "wm_p19h3e1",
            "origin": 3,
            "msgtype": "image",
            "image": {"media_id": "MEDIA001"},
        }
    )
    ingest_wecom_media_message(media_norm, cfg)

    case = get_case_by_id(case_id) or {}
    photo_events = [e for e in (case.get("claim_timeline") or []) if e.get("event_type") == "customer_photo"]
    assert len(photo_events) == 1
    assert photo_events[0].get("attachment_id")
    assert photo_events[0].get("metadata", {}).get("slot_assignment") == "unassigned"

    add_car = save_case("[客户] add car", {"issue_category": "add_car", "urgency": "medium", "broker_next_step": "x", "client_prep": "", "client_reply_draft": "", "manual_followup_needed": False}, service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(add_car["case_id"], wecom_external_userid="wm_add_car_only")
    media_norm2 = normalize_media_message(
        {
            "msgid": "img_add_car",
            "open_kfid": "wktest001",
            "external_userid": "wm_add_car_only",
            "origin": 3,
            "msgtype": "image",
            "image": {"media_id": "MEDIA002"},
        }
    )
    ingest_wecom_media_message(media_norm2, cfg)
    add_car_refreshed = get_case_by_id(add_car["case_id"]) or {}
    assert not add_car_refreshed.get("claim_timeline")


def test_04_basics_complete_once():
    case_id = _start_claim()
    intent = classify_wecom_intent(_BASICS_TEXT)
    ingest_claim_basics_message(_normalized(_BASICS_TEXT, msg_id="m_basics"), intent)
    ingest_claim_basics_message(_normalized(_BASICS_TEXT, msg_id="m_basics_dup"), intent)
    case = get_case_by_id(case_id) or {}
    complete_events = [e for e in (case.get("claim_timeline") or []) if e.get("event_type") == "basics_complete"]
    assert len(complete_events) == 1
    snapshot = complete_events[0].get("metadata", {}).get("facts_snapshot") or {}
    assert snapshot.get("accident_location")


def test_05_build_claim_case_brief_shape():
    saved = save_case(
        f"[客户] {_BASICS_TEXT}",
        _claim_stub(
            accident_datetime="今天上午10点",
            accident_location="Irvine Blvd",
            accident_description="对方变道刮到我左前门",
            injury_status="no",
        ),
        service_lane=SERVICE_LANE_CLAIM,
    )
    brief = build_claim_case_brief(saved)
    for key in (
        "summary",
        "key_facts",
        "evidence_received",
        "missing_info",
        "next_best_question",
        "confidence",
        "source_event_ids",
        "brief_version",
    ):
        assert key in brief
    assert brief["brief_version"] == 1


def test_06_missing_info_priority_injury_unknown():
    saved = save_case(
        "[客户] claim",
        _claim_stub(
            accident_datetime="今天上午10点",
            accident_location="Costco",
            accident_description="追尾",
        ),
        service_lane=SERVICE_LANE_CLAIM,
    )
    brief = build_claim_case_brief(saved)
    assert brief["missing_info"][0]["key"] == "injury_status"
    assert brief["missing_info"][0]["severity"] == "critical"
    assert brief["next_best_question"] == "请问有人受伤吗？"


def test_06b_missing_info_location_when_injury_known():
    saved = save_case(
        "[客户] claim",
        _claim_stub(
            accident_datetime="今天上午10点",
            injury_status="no",
        ),
        service_lane=SERVICE_LANE_CLAIM,
    )
    brief = build_claim_case_brief(saved)
    assert brief["next_best_question"] == "请问事故在哪里发生的？"


def test_07_no_forbidden_language():
    saved = save_case(
        f"[客户] {_BASICS_TEXT}",
        _claim_stub(
            accident_datetime="今天上午10点",
            accident_location="Costco",
            accident_description="追尾",
            injury_status="no",
        ),
        service_lane=SERVICE_LANE_CLAIM,
    )
    brief = build_claim_case_brief(saved)
    assert claim_evidence_copy_is_broker_safe(brief["summary"])
    start_copy = build_claim_start_card_reply(injury_mentioned=False)
    photo_ack = build_claim_wecom_media_reply(tier="A")
    for text in (brief["summary"], start_copy, photo_ack):
        for phrase in _FORBIDDEN_SNIPPETS:
            assert phrase not in text


def test_08_workbench_enrichment():
    saved = save_case(
        f"[客户] {_BASICS_TEXT}",
        _claim_stub(
            accident_datetime="今天上午10点",
            accident_location="Costco",
            accident_description="追尾",
        ),
        service_lane=SERVICE_LANE_CLAIM,
    )
    saved["claim_timeline"] = [
        build_claim_timeline_event(event_type="customer_text", text="test", message_id="x1"),
    ]
    enriched = enrich_claim_for_workbench(saved)
    assert enriched.get("claim_timeline")
    assert enriched.get("claim_case_brief")
    assert enriched.get("claim_evidence_summary")


def test_09_add_vehicle_unaffected():
    saved = save_case(
        "[客户] add car",
        {
            "issue_category": "add_car",
            "urgency": "medium",
            "broker_next_step": "quote",
            "client_prep": "",
            "client_reply_draft": "",
            "manual_followup_needed": False,
        },
        service_lane=SERVICE_LANE_ADD_CAR,
    )
    enriched = enrich_claim_for_workbench(saved)
    assert "claim_case_brief" not in enriched or enriched.get("claim_case_brief") is None
    assert not enriched.get("claim_timeline")


def test_10_injury_quick_reply():
    norm_alone = normalize_text_message(
        {
            "msgid": "inj_alone",
            "open_kfid": "wktest001",
            "external_userid": "wm_injury_alone",
            "origin": 3,
            "msgtype": "text",
            "text": {"content": ""},
            "menu_id": "claim_injury_no",
        }
    )
    alone = ingest_claim_injury_quick_reply(norm_alone, injury_value="no")
    assert alone.get("case_created") is False
    assert alone.get("active_case_outcome") == "claim_injury_holding_gate"
    assert "我要理赔" in (alone.get("reply_text") or "")

    ext = "wm_injury_qr"
    ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext, msg_id="m_start"),
        classify_wecom_intent("我要理赔"),
    )
    norm = normalize_text_message(
        {
            "msgid": "inj_no",
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
    timeline = case.get("claim_timeline") or []
    qr = [e for e in timeline if e.get("metadata", {}).get("quick_reply_key") == "injury_status"]
    assert qr

    norm_yes = normalize_text_message(
        {
            "msgid": "inj_yes",
            "open_kfid": "wktest001",
            "external_userid": "wm_injury_yes",
            "origin": 3,
            "msgtype": "text",
            "text": {"content": ""},
            "menu_id": "claim_injury_yes",
        }
    )
    ingest_claim_basics_message(
        _normalized("我要理赔", ext="wm_injury_yes", msg_id="m_start_yes"),
        classify_wecom_intent("我要理赔"),
    )
    result_yes = ingest_claim_injury_quick_reply(norm_yes, injury_value="yes")
    case_yes = get_case_by_id(str(result_yes["case_id"])) or {}
    assert case_yes.get("known_facts", {}).get("injury_status") == "yes"
    assert result_yes.get("needs_broker_manual_handle")
    assert "上传" not in (result_yes.get("reply_text") or "")

    norm_unk = normalize_text_message(
        {
            "msgid": "inj_unk",
            "open_kfid": "wktest001",
            "external_userid": "wm_injury_unk",
            "origin": 3,
            "msgtype": "text",
            "text": {"content": ""},
            "menu_id": "claim_injury_unknown",
        }
    )
    ingest_claim_basics_message(
        _normalized("我要理赔", ext="wm_injury_unk", msg_id="m_start_unk"),
        classify_wecom_intent("我要理赔"),
    )
    result_unk = ingest_claim_injury_quick_reply(norm_unk, injury_value="unknown")
    case_unk = get_case_by_id(str(result_unk["case_id"])) or {}
    assert case_unk.get("known_facts", {}).get("injury_status") == "unknown"
