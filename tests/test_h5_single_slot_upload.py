"""P19D-2 — H5 single-slot VIN upload tests."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_attachment_api import (
    sanitize_attachment_for_api,
    set_gcs_download_hook_for_tests,
)
from services.fiqa_api.inbox_triage.case_store import get_case_by_id, save_case
from services.fiqa_api.inbox_triage.h5_task_token import issue_h5_task_token
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.routes.h5_task_upload import router as h5_router
from services.fiqa_api.wecom.media_storage import set_gcs_upload_hook_for_tests


@pytest.fixture(autouse=True)
def _reset_hooks():
    set_gcs_upload_hook_for_tests(None)
    set_gcs_download_hook_for_tests(None)
    yield
    set_gcs_upload_hook_for_tests(None)
    set_gcs_download_hook_for_tests(None)


def _setup_json_store() -> Path:
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    return path


def _triage_stub() -> dict:
    return {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": "Review VIN photo.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "extracted_contact_name": "陈女士",
    }


def _save_add_car_case(*, external_userid: str = "demo_chen_kui_chen_ready") -> dict:
    saved = save_case(
        "add car h5 test",
        _triage_stub(),
        service_lane=SERVICE_LANE_ADD_CAR,
    )
    from services.fiqa_api.inbox_triage.case_store import bind_case_channel_identity

    bind_case_channel_identity(saved["case_id"], wecom_external_userid=external_userid)
    return get_case_by_id(saved["case_id"]) or saved


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(h5_router)
    return TestClient(app)


def _mock_gcs_upload():
    def _upload(*, bucket: str, object_path: str, content: bytes, content_type: str | None) -> str:
        return f"gs://{bucket}/{object_path}"

    set_gcs_upload_hook_for_tests(_upload)


def _tiny_jpeg() -> bytes:
    # Minimal valid JPEG header bytes for tests
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xd9"
    )


def test_get_task_info_for_valid_token():
    _setup_json_store()
    case = _save_add_car_case()
    token = issue_h5_task_token(case_id=case["case_id"], external_userid=case.get("wecom_external_userid"))
    client = _client()
    resp = client.get(f"/api/h5/tasks/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["slot"] == "vin_photo"
    assert data["lane"] == "add_car"
    assert data["max_images"] == 1
    assert "VIN" in data["task_label"]


def test_expired_token_returns_403():
    _setup_json_store()
    case = _save_add_car_case()
    now = time.time()
    token = issue_h5_task_token(case_id=case["case_id"], now=now - 200, ttl_seconds=60)
    client = _client()
    resp = client.get(f"/api/h5/tasks/{token}")
    assert resp.status_code == 403


def test_upload_one_image_succeeds():
    _setup_json_store()
    _mock_gcs_upload()
    case = _save_add_car_case()
    token = issue_h5_task_token(case_id=case["case_id"], external_userid=case.get("wecom_external_userid"))
    client = _client()
    resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        files={"file": ("vin.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "uploaded"
    assert body["slot_assignment"] == "vin_photo"
    assert body["next_step"] == "registration_deferred"
    assert "storage_uri" not in body
    assert "external_userid" not in body
    assert "http" not in json.dumps(body).lower()
    assert body["upload_measurement"]["request_id"] == "unknown"
    assert isinstance(body["upload_measurement"]["server_duration_ms"], int)
    assert body["upload_measurement"]["server_duration_ms"] >= 0
    assert "token" not in json.dumps(body["upload_measurement"]).lower()

    updated = get_case_by_id(case["case_id"])
    assert updated is not None
    atts = updated.get("case_attachments") or []
    assert len(atts) == 1
    att = atts[0]
    assert att["source"] == "h5_task"
    assert att["slot_assignment"] == "vin_photo"
    assert att["document_type"] == "vin_photo"
    assert att["intake_status"] == "promoted"
    assert att["guardrail_status"] == "accepted"
    assert att["eligible_for_ocr"] is True
    assert att["ocr_status"] == "not_started"
    assert att["broker_confirmed"] is False
    assert att["binding_confidence"] == "high"
    assert att["bound_case_id"] == case["case_id"]


def test_non_image_rejected():
    _setup_json_store()
    case = _save_add_car_case()
    token = issue_h5_task_token(case_id=case["case_id"])
    client = _client()
    resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400


def test_lane_mismatch_returns_403(monkeypatch):
    _setup_json_store()
    case = _save_add_car_case()
    token = issue_h5_task_token(case_id=case["case_id"], lane="add_car", slot="vin_photo")

    def fake_read(case_id: str):
        row = get_case_by_id(case_id)
        if row is None:
            return None
        patched = dict(row)
        patched["service_lane"] = "policy_review"
        return patched

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.h5_task_upload.get_case_for_read",
        fake_read,
    )
    _mock_gcs_upload()
    client = _client()
    resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        files={"file": ("vin.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "lane_mismatch"


def test_octet_stream_wechat_upload_accepted():
    _setup_json_store()
    _mock_gcs_upload()
    case = _save_add_car_case()
    token = issue_h5_task_token(case_id=case["case_id"])
    client = _client()
    resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        files={"file": ("photo", _tiny_jpeg(), "application/octet-stream")},
    )
    assert resp.status_code == 200


def test_oversized_image_rejected():
    _setup_json_store()
    case = _save_add_car_case()
    token = issue_h5_task_token(case_id=case["case_id"])
    client = _client()
    big = _tiny_jpeg() + (b"x" * (5 * 1024 * 1024 + 1))
    resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        files={"file": ("big.jpg", big, "image/jpeg")},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "file_too_large"


def test_sanitize_h5_attachment_for_workbench():
    att = {
        "attachment_id": "att_h5_1",
        "source": "h5_task",
        "storage_uri": "gs://caseiq-wecom-media-qa/h5/case1/vin_photo/2026/07/h5_abc.jpg",
        "document_type": "vin_photo",
        "slot_assignment": "vin_photo",
        "intake_status": "promoted",
        "guardrail_status": "accepted",
        "eligible_for_ocr": True,
        "ocr_status": "not_started",
        "broker_confirmed": False,
        "binding_confidence": "high",
        "mime_type": "image/jpeg",
    }
    safe = sanitize_attachment_for_api("case1", att)
    assert safe["document_type"] == "vin_photo"
    assert safe["slot_assignment"] == "vin_photo"
    assert safe["source"] == "h5_task"
    assert safe["preview_available"] is True
    assert "storage_uri" not in safe


def test_tampered_token_upload_rejected():
    _setup_json_store()
    case = _save_add_car_case()
    token = issue_h5_task_token(case_id=case["case_id"])
    bad = token[:-3] + "zzz"
    client = _client()
    resp = client.post(
        f"/api/h5/tasks/{bad}/upload",
        files={"file": ("vin.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert resp.status_code == 403
