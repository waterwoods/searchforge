"""P19B — Workbench attachment API tests (sanitize + preview proxy)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_attachment_api import (
    sanitize_attachment_for_api,
    sanitize_case_attachments_for_api,
    sanitize_case_for_workbench_api,
    set_gcs_download_hook_for_tests,
)
from services.fiqa_api.inbox_triage.case_store import (
    add_attachment_to_case,
    append_wecom_gcs_attachment_metadata,
    save_case,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_WECOM_MEDIA_INTAKE
from services.fiqa_api.routes.inbox_triage import router as inbox_router


@pytest.fixture(autouse=True)
def _reset_gcs_hook():
    set_gcs_download_hook_for_tests(None)
    yield
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
        "manual_followup_needed": False,
        "broker_next_step": "Review",
        "client_prep": "",
        "client_reply_draft": "",
    }


def _wecom_att(attachment_id: str = "att_test123") -> dict:
    return {
        "attachment_id": attachment_id,
        "source": "wecom",
        "external_userid": "wm_secret_full_id_should_hide",
        "media_id": "MEDIA_SECRET",
        "msg_id": "msg_abc",
        "msgtype": "image",
        "storage_uri": "gs://caseiq-wecom-media-qa/wecom/user/2026/07/msg_abc.jpg",
        "mime_type": "image/jpeg",
        "size_bytes": 12345,
        "received_at": "2026-07-05T20:50:00+00:00",
        "document_type": "unknown_document",
        "document_type_confidence": "unknown",
        "binding_confidence": "unknown",
        "ocr_status": "not_started",
        "broker_confirmed": False,
        "intake_status": "unassigned",
    }


def test_sanitize_attachment_includes_guardrail_fields():
    att = {
        **_wecom_att(),
        "intake_status": "quarantined",
        "guardrail_status": "bulk_upload_paused",
        "eligible_for_ocr": False,
        "requires_customer_confirm": True,
        "quarantine_reason": "bulk_upload_over_limit",
    }
    safe = sanitize_attachment_for_api("case_abc", att)
    assert safe["intake_status"] == "quarantined"
    assert safe["guardrail_status"] == "bulk_upload_paused"
    assert safe["eligible_for_ocr"] is False
    assert safe["requires_customer_confirm"] is True


def test_sanitize_legacy_attachment_defaults_promoted():
    safe = sanitize_attachment_for_api("case_abc", _wecom_att())
    assert safe["intake_status"] == "unassigned"  # legacy test att has unassigned
    legacy = sanitize_attachment_for_api("case_abc", {**_wecom_att(), "intake_status": None})
    assert legacy["intake_status"] == "promoted"
    assert legacy["guardrail_status"] == "accepted"
    assert legacy["eligible_for_ocr"] is False


def test_sanitize_attachment_strips_secrets():
    safe = sanitize_attachment_for_api("case_abc", _wecom_att())
    assert "external_userid" not in safe
    assert "media_id" not in safe
    assert "storage_uri" not in safe
    assert safe["preview_url"] == "/api/inbox/cases/case_abc/attachments/att_test123/preview"
    assert safe["preview_available"] is True
    assert safe["ocr_status"] == "not_started"
    assert safe["storage_status"] == "stored"


def test_sanitize_empty_attachments_returns_empty_list():
    case = {"case_id": "case_x", "case_attachments": []}
    assert sanitize_case_attachments_for_api("case_x", case) == []


def test_sanitize_case_masks_external_userid():
    case = {
        "case_id": "case_y",
        "wecom_external_userid": "wm_full_secret_id",
        "case_attachments": [_wecom_att()],
    }
    safe = sanitize_case_for_workbench_api(case)
    assert safe["wecom_external_userid"] is None
    assert len(safe["case_attachments"]) == 1
    assert "storage_uri" not in safe["case_attachments"][0]


def test_no_attachments_case_returns_empty_list():
    saved = save_case("no att", _triage_stub())
    safe = sanitize_case_for_workbench_api(saved)
    assert safe.get("case_attachments") == []


def test_wecom_holding_case_serialization():
    saved = save_case(
        "holding",
        {
            **_triage_stub(),
            "issue_category": "wecom_media_intake",
            "broker_next_step": "Classify photo",
        },
        service_lane=SERVICE_LANE_WECOM_MEDIA_INTAKE,
    )
    append_wecom_gcs_attachment_metadata(saved["case_id"], _wecom_att("att_hold1"))
    from services.fiqa_api.inbox_triage.case_store import get_case_by_id

    case = get_case_by_id(saved["case_id"])
    safe = sanitize_case_for_workbench_api(case)
    assert case.get("service_lane") == SERVICE_LANE_WECOM_MEDIA_INTAKE
    assert len(safe["case_attachments"]) == 1
    assert safe["case_attachments"][0]["source"] == "wecom"


def test_preview_endpoint_streams_gcs_mock():
    _setup_json_store()
    saved = save_case("hold", _triage_stub(), service_lane=SERVICE_LANE_WECOM_MEDIA_INTAKE)
    append_wecom_gcs_attachment_metadata(saved["case_id"], _wecom_att("att_prev1"))
    fake_bytes = b"\xff\xd8\xff fake jpeg"

    def _fake_download(_uri: str):
        return fake_bytes, "image/jpeg"

    set_gcs_download_hook_for_tests(_fake_download)

    app = FastAPI()
    app.include_router(inbox_router)
    client = TestClient(app)
    resp = client.get(f"/api/inbox/cases/{saved['case_id']}/attachments/att_prev1/preview")
    assert resp.status_code == 200
    assert resp.content == fake_bytes
    assert "image/jpeg" in resp.headers.get("content-type", "")
    assert "gs://" not in resp.text
    assert "public" not in resp.text.lower()


def test_preview_endpoint_denies_missing_attachment():
    _setup_json_store()
    saved = save_case("empty", _triage_stub())
    app = FastAPI()
    app.include_router(inbox_router)
    client = TestClient(app)
    resp = client.get(f"/api/inbox/cases/{saved['case_id']}/attachments/att_missing/preview")
    assert resp.status_code == 404


def test_preview_local_attachment():
    _setup_json_store()
    saved = save_case("local", _triage_stub())
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    updated = add_attachment_to_case(
        case_id=saved["case_id"],
        filename="mini.png",
        content=png,
        content_type="image/png",
    )
    att_id = updated["case_attachments"][0]["attachment_id"]
    app = FastAPI()
    app.include_router(inbox_router)
    client = TestClient(app)
    resp = client.get(f"/api/inbox/cases/{saved['case_id']}/attachments/{att_id}/preview")
    assert resp.status_code == 200
    assert resp.content == png
