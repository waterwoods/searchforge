"""P19A — WeCom media intake foundation tests (mocked download/GCS)."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
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
    SERVICE_LANE_POLICY_REVIEW,
    SERVICE_LANE_WECOM_MEDIA_INTAKE,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.media_download import (
    WeComMediaDownloadError,
    WeComMediaDownloadResult,
    download_wecom_media,
)
from services.fiqa_api.wecom.media_intake import (
    ingest_wecom_media_message,
    is_supported_media_msgtype,
    resolve_media_case_binding,
)
from services.fiqa_api.wecom.media_storage import (
    build_storage_uri,
    build_wecom_media_object_path,
    infer_extension,
    set_gcs_upload_hook_for_tests,
    upload_wecom_media_to_gcs,
    wecom_media_gcs_bucket,
)
from services.fiqa_api.wecom.message_processed import reset_message_processed_memory_for_tests
from services.fiqa_api.wecom.normalize import normalize_media_message
from services.fiqa_api.wecom.reply import build_media_intake_reply
from services.fiqa_api.wecom.reply_dedup import reset_reply_dedup_memory_for_tests
from services.fiqa_api.wecom.slice import process_kf_msg_or_event
from services.fiqa_api.wecom.sync_cursor import reset_sync_cursor_memory_for_tests
from services.fiqa_api.wecom.sync_msg import pull_customer_messages


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch):
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("WECOM_SLICE_SEND_REPLY", raising=False)
    monkeypatch.delenv("WECOM_B0_ACTIVE_WORKSPACE", raising=False)
    reset_reply_dedup_memory_for_tests()
    reset_message_processed_memory_for_tests()
    reset_sync_cursor_memory_for_tests()
    set_gcs_upload_hook_for_tests(None)
    load_wecom_kf_config.cache_clear()
    yield
    set_gcs_upload_hook_for_tests(None)
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


def _triage_stub(*, issue_category: str = "add_car_quote") -> dict:
    return {
        "issue_category": issue_category,
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": "Broker review.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
    }


def _image_msg(msg_id: str, *, external_userid: str = "wm_media_user_001", media_id: str = "MEDIA001") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": external_userid,
        "origin": 3,
        "msgtype": "image",
        "send_time": 1719750000,
        "image": {"media_id": media_id},
    }


def _file_msg(msg_id: str, *, media_id: str = "FILEMEDIA01") -> dict:
    return {
        "msgid": msg_id,
        "open_kfid": "wktest001",
        "external_userid": "wm_media_user_001",
        "origin": 3,
        "msgtype": "file",
        "send_time": 1719750000,
        "file": {"media_id": media_id, "filename": "policy.pdf"},
    }


def _fake_download(_cfg, *, media_id, msgtype="image"):
    return WeComMediaDownloadResult(
        content=b"\xff\xd8\xff fake jpeg",
        content_type="image/jpeg",
        filename=None,
    )


def _fake_upload(**kwargs):
    ext = ".jpg"
    path = build_wecom_media_object_path(
        external_userid=kwargs["external_userid"],
        msg_id=kwargs["msg_id"],
        ext=ext,
        received_at=kwargs.get("received_at"),
    )
    return {
        "storage_uri": build_storage_uri(wecom_media_gcs_bucket(), path),
        "bucket": wecom_media_gcs_bucket(),
        "object_path": path,
        "mime_type": kwargs.get("mime_type"),
        "size_bytes": len(kwargs["content"]),
        "extension": ext,
    }


def _cfg(monkeypatch):
    monkeypatch.setenv("WECOM_KF_TOKEN", "tok")
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", "a" * 43)
    monkeypatch.setenv("WECOM_CORP_ID", "wwtest")
    monkeypatch.setenv("WECOM_KF_SECRET", "secret")
    load_wecom_kf_config.cache_clear()
    return load_wecom_kf_config()


# --- Media detection ---


def test_supported_media_msgtypes():
    assert is_supported_media_msgtype("image")
    assert is_supported_media_msgtype("file")
    assert not is_supported_media_msgtype("text")
    assert not is_supported_media_msgtype("video")


def test_normalize_image_message_extracts_media_id():
    norm = normalize_media_message(_image_msg("img001"))
    assert norm["msgtype"] == "image"
    assert norm["media_id"] == "MEDIA001"
    assert norm["msg_id"] == "img001"
    assert norm["external_userid"] == "wm_media_user_001"


def test_normalize_file_message_extracts_media_id():
    norm = normalize_media_message(_file_msg("file001"))
    assert norm["msgtype"] == "file"
    assert norm["media_id"] == "FILEMEDIA01"
    assert norm["filename"] == "policy.pdf"


def test_pull_customer_messages_includes_image(monkeypatch):
    monkeypatch.setattr(
        "services.fiqa_api.wecom.sync_msg.sync_kf_messages",
        lambda *a, **k: {
            "errcode": 0,
            "msg_list": [
                _image_msg("m1"),
                {
                    "msgid": "m2",
                    "open_kfid": "wktest001",
                    "external_userid": "wm_media_user_001",
                    "origin": 3,
                    "msgtype": "text",
                    "text": {"content": "hello"},
                },
            ],
            "has_more": 0,
            "next_cursor": "cur1",
        },
    )
    cfg = _cfg(monkeypatch)
    result = pull_customer_messages(cfg, token="t", open_kf_id="wktest001")
    assert len(result.messages) == 2
    types = {(m.get("msgtype") or "").lower() for m in result.messages}
    assert types == {"image", "text"}


# --- Download ---


def test_download_success_binary(monkeypatch):
    class FakeResp:
        headers = {"content-type": "image/jpeg"}
        content = b"jpegbytes"

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        "services.fiqa_api.wecom.media_download.get_access_token",
        lambda cfg: "tok",
    )
    monkeypatch.setattr(
        "services.fiqa_api.wecom.media_download.httpx.get",
        lambda *a, **k: FakeResp(),
    )
    cfg = _cfg(monkeypatch)
    result = download_wecom_media(cfg, media_id="MID123", msgtype="image")
    assert result.content == b"jpegbytes"
    assert result.content_type == "image/jpeg"


def test_download_wecom_json_error(monkeypatch):
    class FakeResp:
        headers = {"content-type": "application/json"}
        content = b'{"errcode":40007,"errmsg":"invalid media_id"}'

        def raise_for_status(self):
            return None

        def json(self):
            return {"errcode": 40007, "errmsg": "invalid media_id"}

    monkeypatch.setattr(
        "services.fiqa_api.wecom.media_download.get_access_token",
        lambda cfg: "tok",
    )
    monkeypatch.setattr(
        "services.fiqa_api.wecom.media_download.httpx.get",
        lambda *a, **k: FakeResp(),
    )
    cfg = _cfg(monkeypatch)
    with pytest.raises(WeComMediaDownloadError, match="wecom_api_error"):
        download_wecom_media(cfg, media_id="BAD", msgtype="image")


def test_download_missing_media_id(monkeypatch):
    cfg = _cfg(monkeypatch)
    with pytest.raises(WeComMediaDownloadError, match="missing_media_id"):
        download_wecom_media(cfg, media_id="", msgtype="image")


def test_download_oversized_image(monkeypatch):
    class FakeResp:
        headers = {"content-type": "image/jpeg"}
        content = b"x" * (6 * 1024 * 1024)

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        "services.fiqa_api.wecom.media_download.get_access_token",
        lambda cfg: "tok",
    )
    monkeypatch.setattr(
        "services.fiqa_api.wecom.media_download.httpx.get",
        lambda *a, **k: FakeResp(),
    )
    cfg = _cfg(monkeypatch)
    with pytest.raises(WeComMediaDownloadError, match="oversize"):
        download_wecom_media(cfg, media_id="BIG", msgtype="image")


def test_unsupported_mime_rejected():
    with pytest.raises(ValueError, match="unsupported_mime"):
        infer_extension(mime_type="application/zip", msgtype="file")


# --- Storage ---


def test_object_path_pattern():
    ts = datetime(2026, 7, 5, 12, 0, tzinfo=timezone.utc)
    path = build_wecom_media_object_path(
        external_userid="wmext001",
        msg_id="msg123",
        ext=".jpg",
        received_at=ts,
    )
    assert path == "wecom/wmext001/2026/07/msg123.jpg"


def test_upload_mock_hook_saves_storage_uri():
    uploaded: list[dict] = []

    def hook(**kwargs):
        uploaded.append(kwargs)
        return build_storage_uri("caseiq-wecom-media-qa", "wecom/test/2026/07/msg.jpg")

    set_gcs_upload_hook_for_tests(hook)
    result = upload_wecom_media_to_gcs(
        external_userid="wmext001",
        msg_id="msg123",
        content=b"data",
        mime_type="image/jpeg",
        received_at=datetime(2026, 7, 5, tzinfo=timezone.utc),
    )
    assert result["storage_uri"].startswith("gs://caseiq-wecom-media-qa/")
    assert uploaded[0]["bucket"] == "caseiq-wecom-media-qa"
    assert "public" not in result["storage_uri"]


# --- Binding ---


def test_binding_active_add_car_high_confidence():
    _setup_json_store()
    saved = save_case("add car", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid="wm_bind_add_car")
    decision = resolve_media_case_binding("wm_bind_add_car")
    assert decision.case_id == cid
    assert decision.binding_confidence == "high"


def test_binding_one_open_policy_review_medium():
    _setup_json_store()
    saved = save_case("premium", _triage_stub(issue_category="policy_review"), service_lane=SERVICE_LANE_POLICY_REVIEW)
    cid = saved["case_id"]
    bind_case_channel_identity(cid, wecom_external_userid="wm_bind_premium")
    decision = resolve_media_case_binding("wm_bind_premium")
    assert decision.case_id == cid
    assert decision.binding_confidence in ("medium", "high")


def test_binding_no_case_unassigned():
    _setup_json_store()
    decision = resolve_media_case_binding("wm_no_case")
    assert decision.case_id is None
    assert decision.intake_status == "unassigned"


def test_binding_multiple_cases_unassigned():
    _setup_json_store()
    for i in range(2):
        saved = save_case(f"case {i}", _triage_stub(issue_category="policy_review"), service_lane=SERVICE_LANE_POLICY_REVIEW)
        bind_case_channel_identity(saved["case_id"], wecom_external_userid="wm_multi")
    decision = resolve_media_case_binding("wm_multi")
    assert decision.case_id is None


# --- Reply copy ---


def test_reply_bound_no_ocr_language():
    text = build_media_intake_reply(bound=True, service_lane=SERVICE_LANE_ADD_CAR, binding_confidence="high")
    assert "OCR" not in text
    assert "陈总" in text


def test_reply_unassigned_disambiguation():
    text = build_media_intake_reply(bound=False, service_lane=None)
    assert "加车" in text
    assert "理赔" in text


def test_reply_coverage_safe_copy():
    text = build_media_intake_reply(bound=True, service_lane="coverage_risk", binding_confidence="high")
    assert "保障" in text
    assert "开车" in text
    assert "OCR" not in text


def test_reply_claim_safe_copy():
    text = build_media_intake_reply(bound=True, service_lane="claim_lite", binding_confidence="medium")
    assert "安全" in text
    assert "OCR" not in text


# --- Intake scenarios A–D ---


def test_scenario_a_active_add_car_attaches(monkeypatch):
    _setup_json_store()
    cfg = _cfg(monkeypatch)
    saved = save_case("draft", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid="wm_scenario_a")
    norm = normalize_media_message(_image_msg("sc_a_1", external_userid="wm_scenario_a"))
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    assert result["active_case_outcome"] == "media_attached_to_case"
    assert result["case_id"] == saved["case_id"]
    case = get_case_by_id(saved["case_id"])
    atts = case.get("case_attachments") or []
    assert len(atts) == 1
    assert atts[0]["source"] == "wecom"
    assert atts[0]["storage_uri"].startswith("gs://")
    assert atts[0]["ocr_status"] == "not_started"
    assert "陈总" in result["reply_text"]


def test_scenario_b_premium_case_attaches(monkeypatch):
    _setup_json_store()
    cfg = _cfg(monkeypatch)
    saved = save_case("premium", _triage_stub(issue_category="policy_review"), service_lane=SERVICE_LANE_POLICY_REVIEW)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid="wm_scenario_b")
    norm = normalize_media_message(_image_msg("sc_b_1", external_userid="wm_scenario_b"))
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    assert result["case_id"] == saved["case_id"]
    assert result["service_lane"] == SERVICE_LANE_POLICY_REVIEW


def test_scenario_c_no_case_unassigned(monkeypatch):
    _setup_json_store()
    cfg = _cfg(monkeypatch)
    norm = normalize_media_message(_image_msg("sc_c_1", external_userid="wm_scenario_c"))
    result = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    assert result["active_case_outcome"] == "media_unassigned"
    assert result["case_created"] is True
    case = get_case_by_id(result["case_id"])
    assert case.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE
    assert "我要理赔" in result["reply_text"]


def test_scenario_d_duplicate_msg_id_no_duplicate_attachment(monkeypatch):
    _setup_json_store()
    cfg = _cfg(monkeypatch)
    saved = save_case("draft", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid="wm_scenario_d")
    norm = normalize_media_message(_image_msg("sc_d_dup", external_userid="wm_scenario_d"))
    first = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    second = ingest_wecom_media_message(norm, cfg, download_fn=_fake_download, upload_fn=_fake_upload)
    assert first["attachment_id"] == second["attachment_id"]
    case = get_case_by_id(saved["case_id"])
    assert len(case.get("case_attachments") or []) == 1


# --- Slice integration + regression E ---


def test_slice_image_message_through_pipeline(monkeypatch):
    _setup_json_store()
    cfg = _cfg(monkeypatch)
    saved = save_case("draft", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid="wm_slice_img")

    def pull(_cfg, *, token, open_kf_id):
        return [_image_msg("slice_img_1", external_userid="wm_slice_img")]

    monkeypatch.setattr(
        "services.fiqa_api.wecom.media_intake.download_wecom_media",
        lambda *a, **k: _fake_download(*a, **k),
    )
    monkeypatch.setattr(
        "services.fiqa_api.wecom.media_intake.upload_wecom_media_to_gcs",
        _fake_upload,
    )

    results = process_kf_msg_or_event(
        cfg,
        callback_token="tok",
        open_kf_id="wktest001",
        pull_messages=pull,
    )
    assert len(results) == 1
    assert results[0]["active_case_outcome"] == "media_attached_to_case"
    assert results[0]["case_id"] == saved["case_id"]


def test_slice_duplicate_image_no_second_reply(monkeypatch):
    _setup_json_store()
    cfg = _cfg(monkeypatch)
    monkeypatch.setenv("WECOM_SLICE_SEND_REPLY", "1")
    saved = save_case("draft", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid="wm_dup_img")
    text_calls: list[dict] = []
    monkeypatch.setattr(
        "services.fiqa_api.wecom.slice.send_text_reply",
        lambda cfg, *, external_userid, open_kf_id, content: text_calls.append({"content": content}),
    )
    monkeypatch.setattr(
        "services.fiqa_api.wecom.media_intake.download_wecom_media",
        lambda *a, **k: _fake_download(*a, **k),
    )
    monkeypatch.setattr(
        "services.fiqa_api.wecom.media_intake.upload_wecom_media_to_gcs",
        _fake_upload,
    )

    def pull(_cfg, *, token, open_kf_id):
        return [_image_msg("dup_img_1", external_userid="wm_dup_img")]

    process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    second = process_kf_msg_or_event(cfg, callback_token="t", open_kf_id="wktest001", pull_messages=pull)
    assert len(text_calls) == 1
    assert second[0].get("processing_skipped") is True


def test_metadata_append_idempotent_by_msg_id():
    _setup_json_store()
    saved = save_case("x", _triage_stub(), service_lane=SERVICE_LANE_ADD_CAR)
    cid = saved["case_id"]
    meta = {
        "attachment_id": "att_test1",
        "source": "wecom",
        "msg_id": "same_msg",
        "storage_uri": "gs://caseiq-wecom-media-qa/wecom/u/2026/07/same_msg.jpg",
        "ocr_status": "not_started",
    }
    append_wecom_gcs_attachment_metadata(cid, meta)
    append_wecom_gcs_attachment_metadata(cid, {**meta, "attachment_id": "att_test2"})
    case = get_case_by_id(cid)
    assert len(case.get("case_attachments") or []) == 1
