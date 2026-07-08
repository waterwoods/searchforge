"""P19H-3d — WeCom Claim image binding MVP + C1 multi-channel copy."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    get_case_by_id,
    save_case,
    update_claim_workflow_state,
)
from services.fiqa_api.inbox_triage.claim_workbench_display import (
    build_claim_evidence_summary,
    enrich_claim_for_workbench,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import ingest_claim_basics_message
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
    build_claim_c1_h5_evidence_card_payload,
    build_claim_stage_complete_c1_reply,
    build_media_intake_reply,
)
from services.fiqa_api.wecom.routing_observability import routing_decision_from_log_message

_NOW = datetime(2026, 7, 9, 12, 0, 0, tzinfo=timezone.utc)
_BASICS_TEXT = "今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门"
_FORBIDDEN_SNIPPETS = (
    "已经报案",
    "理赔已经提交",
    "已联系保险公司",
    "是对方责任",
    "一定会赔",
    "已报案",
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
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    load_wecom_kf_config.cache_clear()
    return load_wecom_kf_config()


def _triage_stub_add_car() -> dict:
    return {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": "Broker review.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
    }


def _claim_stub(**known_facts: str) -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Claim guided workflow.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "known_facts": dict(known_facts),
        "collected_fields": list(known_facts.keys()),
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    }


def _image_msg(msg_id: str, *, external_userid: str = "wm_h3d_claim") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": external_userid,
        "origin": 3,
        "msgtype": "image",
        "send_time": int(_NOW.timestamp()),
        "image": {"media_id": f"MEDIA_{msg_id}"},
    }


def _fake_download(_cfg, *, media_id, msgtype="image"):
    return WeComMediaDownloadResult(
        content=b"\xff\xd8\xff fake jpeg",
        content_type="image/jpeg",
        filename=None,
    )


def _fake_upload(**kwargs):
    return {
        "storage_uri": "gs://caseiq-wecom-media-qa/wecom/test/2026/07/msg.jpg",
        "bucket": "caseiq-wecom-media-qa",
        "object_path": "wecom/test/2026/07/msg.jpg",
        "mime_type": kwargs.get("mime_type"),
        "size_bytes": len(kwargs["content"]),
        "extension": ".jpg",
    }


def _open_recent_claim(*, ext: str = "wm_h3d_claim") -> str:
    saved = save_case(
        "claim basics",
        _claim_stub(
            accident_datetime="今天上午10点",
            accident_location="Irvine Blvd",
            accident_description="对方变道刮蹭",
        ),
        service_lane=SERVICE_LANE_CLAIM,
    )
    cid = str(saved["case_id"])
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    update_claim_workflow_state(cid, claim_phase=CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE)
    return cid


def _routing_logs(caplog) -> list[dict]:
    decisions: list[dict] = []
    for record in caplog.records:
        parsed = routing_decision_from_log_message(record.message)
        if parsed:
            decisions.append(parsed)
    return decisions


def _assert_no_forbidden_copy(text: str) -> None:
    for phrase in _FORBIDDEN_SNIPPETS:
        assert phrase not in (text or "")


def test_01_one_recent_open_claim_binds_image(cfg):
    cid = _open_recent_claim(ext="wm_h3d_a")
    norm = normalize_media_message(_image_msg("img_a1", external_userid="wm_h3d_a"))
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)

    assert result["active_case_outcome"] == "media_attached_to_case"
    assert result["case_id"] == cid
    assert "照片已收到" in (result["reply_text"] or "")

    case = get_case_by_id(cid)
    atts = case.get("case_attachments") or []
    assert len(atts) == 1
    att = atts[0]
    assert att["source"] == "wecom"
    assert att["slot_assignment"] == "unassigned"
    assert att["needs_broker_review"] is True
    assert att["eligible_for_ocr"] is False
    assert att["flow"] == "claim_multichannel_evidence"

    slots = case.get("claim_attachment_slots") or {}
    for slot_key in ("customer_damage_photo", "other_party_vehicle_photo", "scene_photo"):
        slot_state = slots.get(slot_key) or {}
        assert slot_state.get("status") != "received"


def test_02_no_open_claim_image_only_no_claim_created(cfg):
    norm = normalize_media_message(_image_msg("img_c1", external_userid="wm_h3d_none"))
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)

    assert result["active_case_outcome"] == "media_unassigned"
    assert "我要理赔" in (result["reply_text"] or "")

    claim_cases = [c for c in list_all_cases_for_read() if c.get("service_lane") == SERVICE_LANE_CLAIM]
    assert claim_cases == []


def test_03_multiple_open_claims_no_silent_bind(cfg, caplog):
    ext = "wm_h3d_multi"
    _open_recent_claim(ext=ext)
    _open_recent_claim(ext=ext)

    with caplog.at_level(logging.INFO):
        norm = normalize_media_message(_image_msg("img_multi", external_userid=ext))
        result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)

    assert result["active_case_outcome"] == "media_unassigned"
    assert "混在一起" in (result["reply_text"] or "")

    for case in list_all_cases_for_read():
        if case.get("service_lane") == SERVICE_LANE_CLAIM:
            assert not (case.get("case_attachments") or [])

    logs = _routing_logs(caplog)
    assert any(log.get("identity_action") == "broker_confirm" for log in logs)


def test_04_add_vehicle_unaffected(cfg):
    ext = "wm_h3d_addcar"
    saved = save_case("add car", _triage_stub_add_car(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid=ext)

    norm = normalize_media_message(_image_msg("img_addcar", external_userid=ext))
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)

    assert result["case_id"] == saved["case_id"]
    assert result["active_case_outcome"] == "media_attached_to_case"
    case = get_case_by_id(saved["case_id"])
    att = (case.get("case_attachments") or [])[0]
    assert att.get("slot_assignment") != "unassigned"
    assert att.get("flow") != "claim_multichannel_evidence"


def test_05_workbench_pending_classify_display(cfg):
    cid = _open_recent_claim(ext="wm_h3d_wb")
    norm = normalize_media_message(_image_msg("img_wb", external_userid="wm_h3d_wb"))
    ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)

    case = get_case_by_id(cid)
    summary = build_claim_evidence_summary(case)
    assert summary["unassigned_wecom_photos"]["count"] == 1
    assert summary["unassigned_wecom_photos"]["items"][0]["source"] == "wecom"
    assert "待陈总人工归类" in summary["unassigned_wecom_photos"]["broker_next_action"]

    for slot in summary["slots"]:
        assert slot["status"] != "received"

    enriched = enrich_claim_for_workbench(case)
    assert enriched["claim_evidence_summary"]["unassigned_wecom_photos"]["count"] == 1


def test_06_c1_multichannel_copy():
    case = {
        "known_facts": {
            "accident_datetime": "今天上午10点",
            "accident_location": "Irvine Blvd",
            "accident_description": "对方变道刮蹭",
        },
        "collected_fields": ["accident_datetime", "accident_location", "accident_description"],
    }
    reply = build_claim_stage_complete_c1_reply(case)
    assert "推荐点击下面按钮" in reply
    assert "也可以直接把照片发到微信" in reply
    assert "不用重复上传" in reply
    assert "陈总会人工确认" in reply
    _assert_no_forbidden_copy(reply)

    menu = build_claim_c1_h5_evidence_card_payload(
        h5_url="https://example.com/h5/token",
        case=case,
        already_complete=False,
    )
    head = menu["head_content"]
    assert "推荐点击下面按钮" in head
    assert "上传事故照片" in str(menu.get("list") or "")
    _assert_no_forbidden_copy(head)


def test_07_c1_via_ingest_still_has_h5_button(monkeypatch):
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-h5-secret")
    ext = "wm_h3d_c1"
    ingest_claim_basics_message(
        normalize_text_message(
            {
                "msgid": "m_start",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "text",
                "text": {"content": "我要理赔"},
            }
        ),
        classify_wecom_intent("我要理赔"),
    )
    result = ingest_claim_basics_message(
        normalize_text_message(
            {
                "msgid": "m_basics",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "text",
                "text": {"content": _BASICS_TEXT},
            }
        ),
        classify_wecom_intent(_BASICS_TEXT),
    )
    assert result["active_case_outcome"] == "claim_c1_sent"
    menu = result.get("menu_payload")
    assert menu
    assert any(
        item.get("type") == "view"
        and "上传事故照片" in str((item.get("view") or {}).get("content") or "")
        for item in menu.get("list") or []
    )


def test_08_routing_log_emits_identity_for_claim_image(cfg, caplog):
    _open_recent_claim(ext="wm_h3d_log")
    with caplog.at_level(logging.INFO):
        norm = normalize_media_message(_image_msg("img_log", external_userid="wm_h3d_log"))
        ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)

    logs = _routing_logs(caplog)
    assert any(
        log.get("identity_action") == "append_existing" and log.get("identity_tier") == "A"
        for log in logs
    )


def test_09_claim_media_reply_tiers():
    assert "整理到这个理赔记录" in build_media_intake_reply(
        bound=True,
        service_lane=SERVICE_LANE_CLAIM,
        binding_confidence="high",
        claim_media_reply_tier="A",
    )
    assert "混在一起" in build_media_intake_reply(
        bound=False,
        claim_media_reply_tier="B",
    )
    assert "我要理赔" in build_media_intake_reply(
        bound=False,
        claim_media_reply_tier="C",
    )
