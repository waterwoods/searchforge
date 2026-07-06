"""P19D-1 — Strict WeCom upload guardrail tests."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    append_wecom_gcs_attachment_metadata,
    bind_case_channel_identity,
    get_case_by_id,
    save_case,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import (
    SERVICE_LANE_ADD_CAR,
    SERVICE_LANE_CLAIM_LITE,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.media_download import WeComMediaDownloadResult
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message
from services.fiqa_api.wecom.normalize import normalize_media_message
from services.fiqa_api.wecom.reply import build_guardrail_media_reply, build_media_intake_reply
from services.fiqa_api.wecom.upload_guardrail import (
    BULK_WINDOW_SECONDS,
    CLAIM_BATCH_MAX,
    evaluate_upload_guardrail,
    list_recent_wecom_attachments,
    slot_max_for,
)


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


def _setup_json_store() -> Path:
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    return path


def _triage_stub() -> dict:
    return {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": "Broker review.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
    }


def _cfg(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    load_wecom_kf_config.cache_clear()
    return load_wecom_kf_config()


def _image_msg(
    msg_id: str,
    *,
    external_userid: str = "wm_guard_user",
    send_time: int = 1719750000,
) -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": external_userid,
        "origin": 3,
        "msgtype": "image",
        "send_time": send_time,
        "image": {"media_id": f"MEDIA_{msg_id}"},
    }


def _fake_download(_cfg, *, media_id, msgtype="image"):
    return WeComMediaDownloadResult(
        content=b"\xff\xd8\xff fake jpeg",
        content_type="image/jpeg",
        filename=None,
    )


def _fake_upload(**kwargs):
    from services.fiqa_api.wecom.media_storage import (
        build_storage_uri,
        build_wecom_media_object_path,
        wecom_media_gcs_bucket,
    )

    path = build_wecom_media_object_path(
        external_userid=kwargs["external_userid"],
        msg_id=kwargs["msg_id"],
        ext=".jpg",
        received_at=kwargs.get("received_at"),
    )
    return {
        "storage_uri": build_storage_uri(wecom_media_gcs_bucket(), path),
        "bucket": wecom_media_gcs_bucket(),
        "object_path": path,
        "mime_type": kwargs.get("mime_type"),
        "size_bytes": len(kwargs["content"]),
        "extension": ".jpg",
    }


def _seed_wecom_att(
    case_id: str,
    *,
    msg_id: str,
    external_userid: str,
    received_at: datetime,
    intake_status: str = "promoted",
    guardrail_status: str = "accepted",
) -> None:
    append_wecom_gcs_attachment_metadata(
        case_id,
        {
            "attachment_id": f"att_{msg_id}",
            "source": "wecom",
            "external_userid": external_userid,
            "msg_id": msg_id,
            "msgtype": "image",
            "storage_uri": f"gs://caseiq-wecom-media-qa/wecom/{external_userid}/2026/07/{msg_id}.jpg",
            "mime_type": "image/jpeg",
            "size_bytes": 100,
            "received_at": received_at.isoformat(),
            "intake_status": intake_status,
            "guardrail_status": guardrail_status,
            "eligible_for_ocr": intake_status == "promoted",
            "document_type": "unknown_document",
            "binding_confidence": "high",
            "ocr_status": "not_started",
        },
    )


def _ingest(monkeypatch, msg_id: str, *, external_userid: str = "wm_guard_user", send_time: int = 1719750000):
    cfg = _cfg(monkeypatch)
    norm = normalize_media_message(
        _image_msg(msg_id, external_userid=external_userid, send_time=send_time),
    )
    return ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)


# --- Unit: evaluate_upload_guardrail ---


def test_single_image_promotes():
    ts = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    decision = evaluate_upload_guardrail(
        external_userid="wm_u1",
        received_at=ts,
        service_lane=SERVICE_LANE_ADD_CAR,
        case_id="case_1",
    )
    assert decision.action == "promote"
    assert decision.guardrail_status == "accepted"
    assert decision.metadata["eligible_for_ocr"] is True
    assert decision.metadata["intake_status"] == "promoted"


def test_two_images_normal_slot_first_promote_second_quarantine():
    _setup_json_store()
    saved = save_case("add", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    cid = saved["case_id"]
    ext = "wm_two_img"
    ts = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    _seed_wecom_att(cid, msg_id="m1", external_userid=ext, received_at=ts)
    decision = evaluate_upload_guardrail(
        external_userid=ext,
        received_at=ts + timedelta(seconds=5),
        service_lane=SERVICE_LANE_ADD_CAR,
        case_id=cid,
    )
    assert decision.action == "quarantine"
    assert decision.guardrail_status == "bulk_confirm_needed"
    assert decision.metadata["eligible_for_ocr"] is False


def test_three_images_normal_slot_only_first_promoted_in_batch():
    _setup_json_store()
    saved = save_case("add", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    cid = saved["case_id"]
    ext = "wm_three_img"
    ts = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    _seed_wecom_att(cid, msg_id="m1", external_userid=ext, received_at=ts)
    _seed_wecom_att(
        cid,
        msg_id="m2",
        external_userid=ext,
        received_at=ts + timedelta(seconds=3),
        intake_status="quarantined",
        guardrail_status="bulk_confirm_needed",
    )
    decision = evaluate_upload_guardrail(
        external_userid=ext,
        received_at=ts + timedelta(seconds=6),
        service_lane=SERVICE_LANE_ADD_CAR,
        case_id=cid,
    )
    assert decision.action == "quarantine"
    assert decision.metadata["bulk_sequence"] == 3


def test_more_than_three_bulk_pause():
    _setup_json_store()
    saved = save_case("add", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    cid = saved["case_id"]
    ext = "wm_bulk"
    ts = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    for i in range(3):
        _seed_wecom_att(
            cid,
            msg_id=f"b{i}",
            external_userid=ext,
            received_at=ts + timedelta(seconds=i),
            intake_status="promoted" if i == 0 else "quarantined",
            guardrail_status="bulk_confirm_needed" if i else "accepted",
        )
    decision = evaluate_upload_guardrail(
        external_userid=ext,
        received_at=ts + timedelta(seconds=10),
        service_lane=SERVICE_LANE_ADD_CAR,
        case_id=cid,
    )
    assert decision.action == "quarantine"
    assert decision.guardrail_status == "bulk_upload_paused"
    assert decision.reply_kind == "bulk_pause"


def test_claim_lane_allows_up_to_five():
    _setup_json_store()
    saved = save_case("claim", _triage_stub(), service_lane=SERVICE_LANE_CLAIM_LITE)
    cid = saved["case_id"]
    ext = "wm_claim"
    ts = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    for i in range(4):
        _seed_wecom_att(cid, msg_id=f"c{i}", external_userid=ext, received_at=ts + timedelta(seconds=i))
    decision = evaluate_upload_guardrail(
        external_userid=ext,
        received_at=ts + timedelta(seconds=20),
        service_lane=SERVICE_LANE_CLAIM_LITE,
        case_id=cid,
    )
    assert decision.action == "promote"
    assert decision.metadata["bulk_sequence"] == 5


def test_claim_over_five_quarantines():
    _setup_json_store()
    saved = save_case("claim", _triage_stub(), service_lane=SERVICE_LANE_CLAIM_LITE)
    cid = saved["case_id"]
    ext = "wm_claim_over"
    ts = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    for i in range(CLAIM_BATCH_MAX):
        _seed_wecom_att(cid, msg_id=f"o{i}", external_userid=ext, received_at=ts + timedelta(seconds=i))
    decision = evaluate_upload_guardrail(
        external_userid=ext,
        received_at=ts + timedelta(seconds=30),
        service_lane=SERVICE_LANE_CLAIM_LITE,
        case_id=cid,
    )
    assert decision.action == "quarantine"
    assert decision.guardrail_status == "claim_batch_confirm_needed"
    assert decision.metadata["eligible_for_ocr"] is False


def test_quarantined_not_eligible_for_ocr():
    ts = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    _setup_json_store()
    saved = save_case("add", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    _seed_wecom_att(saved["case_id"], msg_id="x1", external_userid="wm_q", received_at=ts)
    decision = evaluate_upload_guardrail(
        external_userid="wm_q",
        received_at=ts + timedelta(seconds=1),
        service_lane=SERVICE_LANE_ADD_CAR,
        case_id=saved["case_id"],
    )
    assert decision.metadata["eligible_for_ocr"] is False


def test_widened_slot_allows_two():
    assert slot_max_for("registration") == 2
    _setup_json_store()
    saved = save_case("add", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    cid = saved["case_id"]
    ext = "wm_reg"
    ts = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    _seed_wecom_att(cid, msg_id="r1", external_userid=ext, received_at=ts)
    decision = evaluate_upload_guardrail(
        external_userid=ext,
        received_at=ts + timedelta(seconds=2),
        service_lane=SERVICE_LANE_ADD_CAR,
        case_id=cid,
        slot_assignment="registration",
    )
    assert decision.action == "promote"


def test_list_recent_wecom_attachments_window():
    _setup_json_store()
    saved = save_case("add", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    ext = "wm_window"
    ts = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    _seed_wecom_att(saved["case_id"], msg_id="w1", external_userid=ext, received_at=ts)
    recent = list_recent_wecom_attachments(ext, received_at=ts + timedelta(seconds=30))
    assert len(recent) == 1
    old = list_recent_wecom_attachments(
        ext,
        received_at=ts + timedelta(seconds=BULK_WINDOW_SECONDS + 60),
    )
    assert len(old) == 0


# --- Reply copy ---


def test_replies_no_ocr_language():
    for kind in ("single_image", "bulk_confirm", "bulk_pause", "claim_batch"):
        text = build_guardrail_media_reply(
            reply_kind=kind,
            bound=True,
            service_lane=SERVICE_LANE_ADD_CAR,
            binding_confidence="high",
        )
        assert "OCR" not in text
        assert "已识别" not in text


def test_bulk_confirm_reply_mentions_confirm():
    text = build_guardrail_media_reply(reply_kind="bulk_confirm", bound=True, service_lane=SERVICE_LANE_ADD_CAR)
    assert "确认" in text
    assert "第一张" in text


def test_bulk_pause_reply_mentions_pause():
    text = build_guardrail_media_reply(reply_kind="bulk_pause", bound=True, service_lane=SERVICE_LANE_ADD_CAR)
    assert "暂停上传" in text


def test_claim_batch_reply():
    text = build_guardrail_media_reply(reply_kind="claim_batch", bound=True, service_lane=SERVICE_LANE_CLAIM_LITE)
    assert "事故" in text
    assert "OCR" not in text


def test_single_image_uses_legacy_ack():
    text = build_guardrail_media_reply(
        reply_kind="single_image",
        bound=True,
        service_lane=SERVICE_LANE_ADD_CAR,
        binding_confidence="high",
    )
    assert text == build_media_intake_reply(
        bound=True,
        service_lane=SERVICE_LANE_ADD_CAR,
        binding_confidence="high",
    )


# --- Integration ingest ---


def test_ingest_single_image_promoted(monkeypatch):
    _setup_json_store()
    saved = save_case("add", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid="wm_guard_user")
    result = _ingest(monkeypatch, "ingest_single")
    case = get_case_by_id(saved["case_id"])
    att = case["case_attachments"][0]
    assert att["intake_status"] == "promoted"
    assert att["guardrail_status"] == "accepted"
    assert att["eligible_for_ocr"] is True
    assert "陈总" in result["reply_text"]
    assert "OCR" not in result["reply_text"]


def test_ingest_three_images_add_car_guardrail(monkeypatch):
    _setup_json_store()
    saved = save_case("add", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid="wm_guard_user")
    base = 1719750000
    for i, mid in enumerate(("img_a", "img_b", "img_c")):
        result = _ingest(monkeypatch, mid, send_time=base + i)
    case = get_case_by_id(saved["case_id"])
    atts = case["case_attachments"]
    assert len(atts) == 3
    promoted = [a for a in atts if a.get("intake_status") == "promoted"]
    quarantined = [a for a in atts if a.get("intake_status") == "quarantined"]
    assert len(promoted) == 1
    assert len(quarantined) == 2
    assert "确认" in result["reply_text"]


def test_ingest_ten_images_bulk_pause(monkeypatch):
    _setup_json_store()
    saved = save_case("add", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid="wm_guard_user")
    base = 1719760000
    for i in range(10):
        result = _ingest(monkeypatch, f"bulk_{i}", send_time=base + i)
    case = get_case_by_id(saved["case_id"])
    promoted = [a for a in case["case_attachments"] if a.get("intake_status") == "promoted"]
    quarantined = [a for a in case["case_attachments"] if a.get("intake_status") == "quarantined"]
    assert len(promoted) == 1
    assert len(quarantined) == 9
    assert "暂停上传" in result["reply_text"]
    assert all(not a.get("eligible_for_ocr") for a in quarantined)


def test_ingest_five_claim_images(monkeypatch):
    _setup_json_store()
    saved = save_case("claim", _triage_stub(), service_lane=SERVICE_LANE_CLAIM_LITE)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid="wm_claim_ingest")
    base = 1719770000
    for i in range(5):
        result = _ingest(
            monkeypatch,
            f"claim_{i}",
            external_userid="wm_claim_ingest",
            send_time=base + i,
        )
    case = get_case_by_id(saved["case_id"])
    promoted = [a for a in case["case_attachments"] if a.get("intake_status") == "promoted"]
    assert len(promoted) == 5
    assert "事故" in result["reply_text"] or "安全" in result["reply_text"]


def test_msg_id_dedup_still_works(monkeypatch):
    _setup_json_store()
    saved = save_case("add", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid="wm_dedup")
    _ingest(monkeypatch, "dup_msg", external_userid="wm_dedup")
    second = _ingest(monkeypatch, "dup_msg", external_userid="wm_dedup")
    assert second["outcome"] == "duplicate_msg"
    case = get_case_by_id(saved["case_id"])
    assert len(case["case_attachments"]) == 1


def test_existing_metadata_fields_preserved(monkeypatch):
    _setup_json_store()
    saved = save_case("add", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid="wm_meta")
    _ingest(monkeypatch, "meta1", external_userid="wm_meta")
    att = get_case_by_id(saved["case_id"])["case_attachments"][0]
    assert att["source"] == "wecom"
    assert att["storage_uri"].startswith("gs://")
    assert att["ocr_status"] == "not_started"
    assert "msg_id" in att
