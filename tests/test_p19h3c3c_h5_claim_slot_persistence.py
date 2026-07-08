"""P19H-3c-3C — H5 Claim evidence slot persistence / skip reason tests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_store import bind_case_channel_identity, get_case_by_id, save_case
from services.fiqa_api.inbox_triage.claim_workbench_display import build_claim_evidence_summary
from services.fiqa_api.inbox_triage.h5_task_token import FLOW_CLAIM_EVIDENCE_PACK, issue_h5_flow_token
from services.fiqa_api.routes.h5_task_upload import router as h5_router
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM
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
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Review claim evidence.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
    }


def _save_claim_case() -> dict:
    saved = save_case(
        "claim h5 slot persistence test",
        _triage_stub(),
        service_lane=SERVICE_LANE_CLAIM,
    )
    bind_case_channel_identity(
        saved["case_id"],
        wecom_external_userid="wm_claim_slot_persist",
        wecom_open_kf_id="wktest001",
    )
    return get_case_by_id(saved["case_id"]) or saved


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(h5_router)
    return TestClient(app)


def _claim_flow_token(case: dict) -> str:
    return issue_h5_flow_token(
        case_id=case["case_id"],
        lane="claim",
        flow=FLOW_CLAIM_EVIDENCE_PACK,
        external_userid=case.get("wecom_external_userid"),
    )


def _tiny_jpeg() -> bytes:
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xd9"
    )


def _upload_damage(client: TestClient, token: str) -> None:
    resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "customer_damage_photo"},
        files={"file": ("damage.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert resp.status_code == 200


def test_01_h5_upload_marks_slot_received():
    _setup_json_store()
    set_gcs_upload_hook_for_tests(
        lambda *, bucket, object_path, content, content_type: f"gs://{bucket}/{object_path}"
    )
    case = _save_claim_case()
    token = _claim_flow_token(case)
    client = _client()
    _upload_damage(client, token)

    updated = get_case_by_id(case["case_id"])
    assert updated is not None
    atts = updated.get("case_attachments") or []
    assert len(atts) == 1
    att_id = atts[0]["attachment_id"]

    slots = updated.get("claim_attachment_slots") or {}
    damage = slots["customer_damage_photo"]
    assert damage["status"] == "received"
    assert damage["source_channel"] == "h5_task"
    assert damage["latest_attachment_id"] == att_id
    assert att_id in damage["attachment_ids"]
    assert damage.get("updated_at")

    summary = build_claim_evidence_summary(updated)
    by_key = {s["slot_key"]: s for s in summary["slots"]}
    assert by_key["customer_damage_photo"]["status"] == "received"


def test_02_upload_clears_previous_skipped_status():
    _setup_json_store()
    set_gcs_upload_hook_for_tests(
        lambda *, bucket, object_path, content, content_type: f"gs://{bucket}/{object_path}"
    )
    case = _save_claim_case()
    client = _client()
    token = _claim_flow_token(case)
    _upload_damage(client, token)

    from services.fiqa_api.inbox_triage.case_store import (
        record_claim_evidence_slot_received,
        record_claim_evidence_slot_skip,
    )

    record_claim_evidence_slot_skip(
        case["case_id"],
        slot="other_party_vehicle_photo",
        skip_reason="not_available",
    )
    updated = get_case_by_id(case["case_id"])
    assert updated is not None
    assert updated["claim_attachment_slots"]["other_party_vehicle_photo"]["status"] == "skipped"

    record_claim_evidence_slot_received(
        case["case_id"],
        slot="other_party_vehicle_photo",
        attachment_id="att_other_cleared",
    )
    final = get_case_by_id(case["case_id"])
    assert final is not None
    other = final["claim_attachment_slots"]["other_party_vehicle_photo"]
    assert other["status"] == "received"
    assert other.get("skip_reason") is None
    assert other["latest_attachment_id"] == "att_other_cleared"


def test_03_skip_soft_required_other_party_slot():
    _setup_json_store()
    set_gcs_upload_hook_for_tests(
        lambda *, bucket, object_path, content, content_type: f"gs://{bucket}/{object_path}"
    )
    case = _save_claim_case()
    token = _claim_flow_token(case)
    client = _client()
    _upload_damage(client, token)

    token = _claim_flow_token(get_case_by_id(case["case_id"]) or case)
    before_count = len((get_case_by_id(case["case_id"]) or {}).get("case_attachments") or [])

    skip_resp = client.post(
        f"/api/h5/tasks/{token}/skip",
        data={"slot": "other_party_vehicle_photo", "skip_reason": "not_available"},
    )
    assert skip_resp.status_code == 200

    updated = get_case_by_id(case["case_id"])
    assert updated is not None
    assert len(updated.get("case_attachments") or []) == before_count

    other = updated["claim_attachment_slots"]["other_party_vehicle_photo"]
    assert other["status"] == "skipped"
    assert other["skip_reason"] == "not_available"
    assert other["source_channel"] == "h5_task"

    summary = build_claim_evidence_summary(updated)
    by_key = {s["slot_key"]: s for s in summary["slots"]}
    assert by_key["other_party_vehicle_photo"]["status"] == "skipped"
    assert summary["missing_soft_required_slots"] == []


def test_04_required_customer_damage_cannot_be_skipped():
    _setup_json_store()
    case = _save_claim_case()
    token = _claim_flow_token(case)
    client = _client()

    resp = client.post(
        f"/api/h5/tasks/{token}/skip",
        data={"slot": "customer_damage_photo", "skip_reason": "not_available"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "slot_not_skippable"

    updated = get_case_by_id(case["case_id"])
    assert updated is not None
    slots = updated.get("claim_attachment_slots") or {}
    assert "customer_damage_photo" not in slots or slots.get("customer_damage_photo", {}).get("status") != "skipped"


def test_05_scene_optional_skip():
    _setup_json_store()
    set_gcs_upload_hook_for_tests(
        lambda *, bucket, object_path, content, content_type: f"gs://{bucket}/{object_path}"
    )
    case = _save_claim_case()
    token = _claim_flow_token(case)
    client = _client()
    _upload_damage(client, token)

    token = _claim_flow_token(get_case_by_id(case["case_id"]) or case)
    client.post(
        f"/api/h5/tasks/{token}/skip",
        data={"slot": "other_party_vehicle_photo", "skip_reason": "no_other_party"},
    )

    token = _claim_flow_token(get_case_by_id(case["case_id"]) or case)
    skip_resp = client.post(
        f"/api/h5/tasks/{token}/skip",
        data={"slot": "scene_photo", "skip_reason": "not_needed"},
    )
    assert skip_resp.status_code == 200

    updated = get_case_by_id(case["case_id"])
    assert updated is not None
    scene = updated["claim_attachment_slots"]["scene_photo"]
    assert scene["status"] == "skipped"
    assert scene["skip_reason"] == "not_needed"

    summary = build_claim_evidence_summary(updated)
    assert summary["completion_level"] == "complete"


def test_06_invalid_skip_reason_rejected():
    _setup_json_store()
    set_gcs_upload_hook_for_tests(
        lambda *, bucket, object_path, content, content_type: f"gs://{bucket}/{object_path}"
    )
    case = _save_claim_case()
    token = _claim_flow_token(case)
    client = _client()
    _upload_damage(client, token)

    token = _claim_flow_token(get_case_by_id(case["case_id"]) or case)
    resp = client.post(
        f"/api/h5/tasks/{token}/skip",
        data={"slot": "other_party_vehicle_photo", "skip_reason": "made_up_reason"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "invalid_skip_reason"

    updated = get_case_by_id(case["case_id"])
    assert updated is not None
    slots = updated.get("claim_attachment_slots") or {}
    assert slots.get("other_party_vehicle_photo", {}).get("status") != "skipped"


def test_07_add_vehicle_h5_unaffected():
    _setup_json_store()
    set_gcs_upload_hook_for_tests(
        lambda *, bucket, object_path, content, content_type: f"gs://{bucket}/{object_path}"
    )
    saved = save_case("add car slot persist regression", _triage_stub(), service_lane="add_car")
    case = get_case_by_id(saved["case_id"]) or saved
    token = issue_h5_flow_token(case_id=case["case_id"], lane="add_car")
    client = _client()

    upload_resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "vin_photo"},
        files={"file": ("vin.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert upload_resp.status_code == 200

    updated = get_case_by_id(case["case_id"])
    assert updated is not None
    assert not updated.get("claim_attachment_slots")

    token = issue_h5_flow_token(case_id=case["case_id"], lane="add_car")
    reg_resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "registration_photo"},
        files={"file": ("reg.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert reg_resp.status_code == 200

    token = issue_h5_flow_token(case_id=case["case_id"], lane="add_car")
    skip_resp = client.post(
        f"/api/h5/tasks/{token}/skip",
        data={"slot": "insurance_card_photo"},
    )
    assert skip_resp.status_code == 200
    final = get_case_by_id(case["case_id"])
    assert final is not None
    assert not final.get("claim_attachment_slots")


def test_08_workbench_summary_after_upload_skip():
    _setup_json_store()
    set_gcs_upload_hook_for_tests(
        lambda *, bucket, object_path, content, content_type: f"gs://{bucket}/{object_path}"
    )
    case = _save_claim_case()
    token = _claim_flow_token(case)
    client = _client()
    _upload_damage(client, token)

    token = _claim_flow_token(get_case_by_id(case["case_id"]) or case)
    client.post(
        f"/api/h5/tasks/{token}/skip",
        data={"slot": "other_party_vehicle_photo", "skip_reason": "not_available"},
    )

    updated = get_case_by_id(case["case_id"])
    assert updated is not None
    summary = build_claim_evidence_summary(updated)

    assert summary["completion_level"] == "review_ready"
    assert summary["missing_required_slots"] == []
    assert summary["missing_soft_required_slots"] == []
    assert "陈总" in summary["broker_next_action"] or "资料基本够" in summary["broker_next_action"]

    by_key = {s["slot_key"]: s for s in summary["slots"]}
    assert by_key["customer_damage_photo"]["status"] == "received"
    assert by_key["other_party_vehicle_photo"]["status"] == "skipped"
    assert by_key["scene_photo"]["status"] == "missing"
