"""P19D-4A — H5 Add Vehicle continuous photo flow tests."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_attachment_api import sanitize_attachment_for_api
from services.fiqa_api.inbox_triage.case_store import get_case_by_id, save_case
from services.fiqa_api.inbox_triage.h5_task_link import mint_h5_add_vehicle_photo_flow_link
from services.fiqa_api.inbox_triage.h5_task_token import (
    ADD_VEHICLE_PHOTO_FLOW_SLOTS,
    FLOW_ADD_VEHICLE_PHOTO,
    issue_h5_flow_token,
    issue_h5_task_token,
    verify_h5_task_token,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.routes.h5_task_upload import router as h5_router
from services.fiqa_api.wecom.media_storage import set_gcs_upload_hook_for_tests


@pytest.fixture(autouse=True)
def _reset_hooks():
    set_gcs_upload_hook_for_tests(None)
    yield
    set_gcs_upload_hook_for_tests(None)


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
        "broker_next_step": "Review photos.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "extracted_contact_name": "陈女士",
    }


def _save_add_car_case(
    *,
    external_userid: str = "demo_chen_kui_chen_ready",
    open_kf_id: str = "wktest001",
) -> dict:
    saved = save_case(
        "add car h5 flow test",
        _triage_stub(),
        service_lane=SERVICE_LANE_ADD_CAR,
    )
    from services.fiqa_api.inbox_triage.case_store import bind_case_channel_identity

    bind_case_channel_identity(
        saved["case_id"],
        wecom_external_userid=external_userid,
        wecom_open_kf_id=open_kf_id,
    )
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
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xd9"
    )


def _flow_token(case: dict) -> str:
    return issue_h5_flow_token(
        case_id=case["case_id"],
        external_userid=case.get("wecom_external_userid"),
    )


def test_flow_token_generates_three_slots():
    token = issue_h5_flow_token(case_id="case_flow1")
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.is_flow_token
    assert claims.flow == FLOW_ADD_VEHICLE_PHOTO
    assert claims.slots == ADD_VEHICLE_PHOTO_FLOW_SLOTS


def test_get_task_returns_steps_and_current_step():
    _setup_json_store()
    case = _save_add_car_case()
    token = _flow_token(case)
    client = _client()
    resp = client.get(f"/api/h5/tasks/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["flow"] == FLOW_ADD_VEHICLE_PHOTO
    assert data["current_step"] == "vin_photo"
    assert data["step_index"] == 1
    assert data["step_total"] == 3
    assert len(data["steps"]) == 3
    assert data["steps"][0]["slot"] == "vin_photo"
    assert data["steps"][0]["status"] == "pending"


def test_upload_vin_then_registration_then_insurance():
    _setup_json_store()
    _mock_gcs_upload()
    case = _save_add_car_case()
    token = _flow_token(case)
    client = _client()

    r1 = client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "vin_photo"},
        files={"file": ("vin.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert r1.status_code == 200
    assert r1.json()["slot_assignment"] == "vin_photo"
    assert r1.json()["flow_complete"] is False
    assert r1.json()["next_slot"] == "registration_photo"

    info = client.get(f"/api/h5/tasks/{token}").json()
    assert info["current_step"] == "registration_photo"
    assert info["step_index"] == 2

    r2 = client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "registration_photo"},
        files={"file": ("reg.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert r2.status_code == 200
    assert r2.json()["next_slot"] == "insurance_card_photo"

    info2 = client.get(f"/api/h5/tasks/{token}").json()
    assert info2["current_step"] == "insurance_card_photo"

    r3 = client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "insurance_card_photo"},
        files={"file": ("ins.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert r3.status_code == 200
    assert r3.json()["flow_complete"] is True

    final = client.get(f"/api/h5/tasks/{token}").json()
    assert final["flow_complete"] is True
    assert final["current_step"] is None

    updated = get_case_by_id(case["case_id"])
    assert updated is not None
    atts = updated.get("case_attachments") or []
    slots = {a["slot_assignment"] for a in atts}
    assert slots == {"vin_photo", "registration_photo", "insurance_card_photo"}
    for att in atts:
        assert att["source"] == "h5_task"
        assert att["flow"] == FLOW_ADD_VEHICLE_PHOTO
        assert att["eligible_for_ocr"] is True
        assert att["ocr_status"] == "not_started"
        assert att["broker_confirmed"] is False


def test_skip_insurance_card_completes_flow():
    _setup_json_store()
    _mock_gcs_upload()
    case = _save_add_car_case()
    token = _flow_token(case)
    client = _client()

    client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "vin_photo"},
        files={"file": ("vin.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "registration_photo"},
        files={"file": ("reg.jpg", _tiny_jpeg(), "image/jpeg")},
    )

    skip = client.post(
        f"/api/h5/tasks/{token}/skip",
        data={"slot": "insurance_card_photo"},
    )
    assert skip.status_code == 200
    assert skip.json()["flow_complete"] is True
    assert skip.json()["status"] == "skipped"

    updated = get_case_by_id(case["case_id"])
    skipped = (updated.get("h5_photo_flow_state") or {}).get("skipped_slots") or []
    assert "insurance_card_photo" in skipped


def test_wrong_slot_order_rejected():
    _setup_json_store()
    _mock_gcs_upload()
    case = _save_add_car_case()
    token = _flow_token(case)
    client = _client()
    resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "registration_photo"},
        files={"file": ("reg.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "wrong_slot_order"


def test_non_image_rejected():
    _setup_json_store()
    case = _save_add_car_case()
    token = _flow_token(case)
    client = _client()
    resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "vin_photo"},
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400


def test_oversized_image_rejected():
    _setup_json_store()
    case = _save_add_car_case()
    token = _flow_token(case)
    client = _client()
    big = _tiny_jpeg() + (b"x" * (5 * 1024 * 1024 + 1))
    resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "vin_photo"},
        files={"file": ("big.jpg", big, "image/jpeg")},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "file_too_large"


def test_expired_flow_token_rejected():
    _setup_json_store()
    case = _save_add_car_case()
    now = time.time()
    token = issue_h5_flow_token(case_id=case["case_id"], now=now - 200, ttl_seconds=60)
    client = _client()
    assert client.get(f"/api/h5/tasks/{token}").status_code == 403


def test_tampered_flow_token_rejected():
    _setup_json_store()
    case = _save_add_car_case()
    token = _flow_token(case)
    bad = token[:-3] + "zzz"
    client = _client()
    assert client.get(f"/api/h5/tasks/{bad}").status_code == 403


def test_mint_flow_link_no_secrets():
    os.environ["H5_TASK_TOKEN_SECRET"] = "test-h5-secret"
    os.environ["H5_TASK_FRONTEND_BASE_URL"] = "https://example.test"
    url = mint_h5_add_vehicle_photo_flow_link(case_id="case_link", external_userid="wm_secret_user")
    assert "wm_secret" not in url
    token = url.rsplit("/", 1)[-1]
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.is_flow_token


def test_workbench_labels_for_flow_slots():
    for slot, label in (
        ("vin_photo", "vin_photo"),
        ("registration_photo", "registration_photo"),
        ("insurance_card_photo", "insurance_card_photo"),
    ):
        safe = sanitize_attachment_for_api(
            "case1",
            {
                "attachment_id": f"att_{slot}",
                "source": "h5_task",
                "storage_uri": f"gs://b/h5/case1/{slot}/x.jpg",
                "document_type": slot,
                "slot_assignment": slot,
                "intake_status": "promoted",
                "guardrail_status": "accepted",
                "eligible_for_ocr": True,
                "ocr_status": "not_started",
                "broker_confirmed": False,
                "binding_confidence": "high",
                "mime_type": "image/jpeg",
            },
        )
        assert safe["slot_assignment"] == slot
        assert safe["preview_available"] is True
        assert "storage_uri" not in safe


def test_v1_single_slot_still_works():
    _setup_json_store()
    _mock_gcs_upload()
    case = _save_add_car_case()
    token = issue_h5_task_token(case_id=case["case_id"])
    client = _client()
    info = client.get(f"/api/h5/tasks/{token}").json()
    assert info.get("flow") is None
    assert info["slot"] == "vin_photo"
    resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        files={"file": ("vin.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["slot_assignment"] == "vin_photo"


def test_flow_complete_sends_end_card_once(monkeypatch):
    _setup_json_store()
    _mock_gcs_upload()
    case = _save_add_car_case()
    token = _flow_token(case)
    client = _client()
    sent: list[dict] = []

    def fake_send(case_id: str) -> dict:
        sent.append({"case_id": case_id})
        from datetime import datetime, timezone
        from services.fiqa_api.inbox_triage.case_store import record_h5_photo_flow_end_card_status

        record_h5_photo_flow_end_card_status(
            case_id,
            send_status="sent",
            sent_at=datetime.now(timezone.utc).isoformat(),
        )
        return {"sent": True}

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.h5_task_upload.try_send_h5_photo_flow_end_card",
        fake_send,
    )

    for slot, name in (
        ("vin_photo", "vin.jpg"),
        ("registration_photo", "reg.jpg"),
        ("insurance_card_photo", "ins.jpg"),
    ):
        client.post(
            f"/api/h5/tasks/{token}/upload",
            data={"slot": slot},
            files={"file": (name, _tiny_jpeg(), "image/jpeg")},
        )

    assert len(sent) == 1
    assert sent[0]["case_id"] == case["case_id"]

    # Refresh GET must not trigger another send
    client.get(f"/api/h5/tasks/{token}")
    assert len(sent) == 1

    updated = get_case_by_id(case["case_id"])
    state = (updated or {}).get("h5_photo_flow_state") or {}
    assert state.get("end_card_sent_at")
    assert state.get("end_card_send_status") == "sent"


def test_flow_complete_end_card_send_failure_does_not_fail_upload(monkeypatch):
    _setup_json_store()
    _mock_gcs_upload()
    case = _save_add_car_case()
    token = _flow_token(case)
    client = _client()

    def fail_send(_case_id: str) -> dict:
        return {"sent": False, "reason": "send_failed", "error": "RuntimeError"}

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.h5_task_upload.try_send_h5_photo_flow_end_card",
        fail_send,
    )

    client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "vin_photo"},
        files={"file": ("vin.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "registration_photo"},
        files={"file": ("reg.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    r3 = client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "insurance_card_photo"},
        files={"file": ("ins.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert r3.status_code == 200
    body = r3.json()
    assert body["flow_complete"] is True
    assert body.get("end_card_sent") is False
    assert body.get("end_card_send_warning") == "confirmation_message_pending"


def test_skip_insurance_triggers_end_card_with_skipped_checklist(monkeypatch):
    _setup_json_store()
    _mock_gcs_upload()
    case = _save_add_car_case()
    token = _flow_token(case)
    client = _client()
    captured: list[str] = []

    def capture_send(case_id: str) -> dict:
        from services.fiqa_api.wecom.reply import build_h5_photo_phase_complete_reply
        from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
        from datetime import datetime, timezone
        from services.fiqa_api.inbox_triage.case_store import record_h5_photo_flow_end_card_status

        c = get_case_for_read(case_id)
        captured.append(build_h5_photo_phase_complete_reply(c or {}))
        record_h5_photo_flow_end_card_status(
            case_id,
            send_status="sent",
            sent_at=datetime.now(timezone.utc).isoformat(),
        )
        return {"sent": True}

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.h5_task_upload.try_send_h5_photo_flow_end_card",
        capture_send,
    )

    client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "vin_photo"},
        files={"file": ("vin.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "registration_photo"},
        files={"file": ("reg.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    skip = client.post(
        f"/api/h5/tasks/{token}/skip",
        data={"slot": "insurance_card_photo"},
    )
    assert skip.status_code == 200
    assert skip.json()["flow_complete"] is True
    assert len(captured) == 1
    assert "第 1 步完成" in captured[0]
    assert "照片资料已收到" in captured[0]
    assert "提车日期" in captured[0]
