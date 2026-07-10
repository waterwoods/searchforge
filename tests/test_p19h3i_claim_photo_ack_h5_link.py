"""P19H-3i — Claim photo ack includes direct H5 task link."""

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
    update_claim_workflow_state,
    update_case_h5_intake_state,
)
from services.fiqa_api.inbox_triage.case_truth_repository import list_all_cases_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.claim_basics import ingest_claim_basics_message
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    SERVICE_LANE_CLAIM,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message
from services.fiqa_api.wecom.reply import build_claim_wecom_media_reply
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

_LEGACY_FALLBACK_MARKERS = (
    "Chen Kui's team has received your request",
    "陈奎团队已收到您的请求",
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
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    monkeypatch.setenv("H5_TASK_FRONTEND_BASE_URL", "https://example.test")
    monkeypatch.setenv("H5_TASK_TOKEN_SECRET", "test-h5-secret")
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    monkeypatch.setenv("WECOM_B0_ACTIVE_WORKSPACE", "1")
    load_wecom_kf_config.cache_clear()
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)
    load_wecom_kf_config.cache_clear()


def _claim_stub() -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Broker review.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": True,
        "claim_phase": CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    }


def _open_claim(*, ext: str, with_story: bool = False) -> dict:
    saved = save_case("claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    if with_story:
        update_claim_workflow_state(
            cid,
            claim_phase="accident_basics_complete",
            guided_workflow_state="collecting_text",
        )
    else:
        update_claim_workflow_state(
            cid,
            claim_phase="claim_started",
            guided_workflow_state="collecting_text",
        )
    return get_case_by_id(cid) or saved


def _submitted_claim(*, ext: str) -> dict:
    saved = _open_claim(ext=ext, with_story=True)
    cid = saved["case_id"]
    update_claim_workflow_state(
        cid,
        claim_phase=CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
        guided_workflow_state="ready_for_broker_review",
    )
    update_case_h5_intake_state(
        cid,
        {"submitted_at": "2026-07-10T12:00:00+00:00", "submitted": True},
    )
    return get_case_by_id(cid) or saved


def _photo_complete_add_car(*, ext: str) -> dict:
    from services.fiqa_api.inbox_triage.case_store import append_h5_gcs_attachment_metadata

    saved = save_case(
        "add car",
        {
            "issue_category": "add_car_quote",
            "urgency": "medium",
            "manual_followup_needed": True,
            "broker_next_step": "Review.",
            "client_prep": "",
            "client_reply_draft": "",
            "still_needed_fields": ["delivery_date", "zip", "phone"],
            "collected_fields": [],
        },
        service_lane=SERVICE_LANE_ADD_CAR,
    )
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid=ext)
    for idx, slot in enumerate(("vin_photo", "registration_photo", "insurance_card_photo")):
        append_h5_gcs_attachment_metadata(
            cid,
            {
                "source": "h5_task",
                "slot_assignment": slot,
                "h5_upload_id": f"upload_{idx}",
                "mime_type": "image/jpeg",
            },
        )
    case = get_case_by_id(cid) or saved
    case["h5_photo_flow_state"] = {"end_card_sent_at": "2026-07-10T12:00:00+00:00"}
    return case


def _fake_download(_cfg, **kwargs):
    return WeComMediaDownloadResult(
        content=b"fake-image-bytes",
        content_type="image/jpeg",
        filename="photo.jpg",
    )


def _fake_upload(**kwargs):
    return {
        "storage_uri": "gs://test-bucket/wecom/photo.jpg",
        "mime_type": "image/jpeg",
        "filename": "photo.jpg",
    }


def _ingest_photo(*, ext: str, msg_id: str = "img_photo") -> dict:
    cfg = load_wecom_kf_config()
    norm = normalize_media_message(
        {
            "msgid": msg_id,
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "image",
            "image": {"media_id": f"mid_{msg_id}"},
        }
    )
    return ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)


def _assert_no_legacy_fallback(reply: str) -> None:
    for marker in _LEGACY_FALLBACK_MARKERS:
        assert marker not in reply


def test_submitted_claim_photo_ack_includes_h5_link():
    ext = "wm_3i_photo_submitted"
    saved = _submitted_claim(ext=ext)
    result = _ingest_photo(ext=ext, msg_id="img_submitted")
    reply = result.get("reply_text") or ""
    assert result["case_id"] == saved["case_id"]
    assert result["active_case_outcome"] == "media_attached_to_case"
    assert "照片已收到" in reply
    assert "继续补充事故资料" in reply
    assert "/task/claim/h5t1." in reply
    assert "请回复「进度」" not in reply
    assert "broker_done" not in reply.lower()
    _assert_no_legacy_fallback(reply)
    timeline = (get_case_by_id(saved["case_id"]) or {}).get("claim_timeline") or []
    assert any(e.get("event_type") == "customer_photo" for e in timeline)


def test_unsubmitted_claim_photo_ack_includes_h5_link():
    ext = "wm_3i_photo_open"
    saved = _open_claim(ext=ext, with_story=True)
    result = _ingest_photo(ext=ext, msg_id="img_open")
    reply = result.get("reply_text") or ""
    assert result["case_id"] == saved["case_id"]
    assert "/task/claim/h5t1." in reply
    assert "继续补充事故资料" in reply
    assert "照片已收到" in reply


def test_submitted_claim_photo_beats_add_car_phase2():
    ext = "wm_3i_photo_add_car"
    saved = _submitted_claim(ext=ext)
    _photo_complete_add_car(ext=ext)
    result = _ingest_photo(ext=ext, msg_id="img_add_car")
    reply = result.get("reply_text") or ""
    assert result["case_id"] == saved["case_id"]
    assert result["service_lane"] == SERVICE_LANE_CLAIM
    assert "提车日期" not in reply
    assert "/task/claim/h5t1." in reply


def test_no_active_claim_photo_preserves_safe_behavior():
    ext = "wm_3i_photo_none"
    before = len(list_all_cases_for_read())
    result = _ingest_photo(ext=ext, msg_id="img_none")
    reply = result.get("reply_text") or ""
    assert result["active_case_outcome"] == "media_unassigned"
    assert "我要理赔" in reply
    assert "/task/claim/" not in reply
    assert len(list_all_cases_for_read()) >= before


def test_photo_ack_fallback_without_h5_url():
    ack = build_claim_wecom_media_reply(tier="A", h5_intake_url=None)
    assert "照片已收到" in ack
    assert "进度" in ack or "链接" in ack
    assert "/task/claim/" not in ack


def test_legacy_fallback_regression_still_clean(monkeypatch):
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "0")
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    cfg = load_wecom_kf_config()

    def _pull(text: str, ext: str):
        return lambda *_a, **_k: [
            {
                "msgid": f"m_legacy_{ext}",
                "open_kfid": "wktest001",
                "external_userid": ext,
                "origin": 3,
                "msgtype": "text",
                "text": {"content": text},
            }
        ]

    for text, ext_suffix in (
        ("我要理赔", "start"),
        ("我需要理赔，发给我 H5", "h5"),
    ):
        ext = f"wm_3i_photo_legacy_{ext_suffix}"
        results = process_kf_msg_or_event(
            cfg,
            callback_token="t",
            open_kf_id="wktest001",
            pull_messages=_pull(text, ext),
        )
        assert results
        reply = results[0].get("reply_text") or ""
        _assert_no_legacy_fallback(reply)
        assert results[0].get("active_case_outcome") != "legacy_fallback"
