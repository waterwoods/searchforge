"""P19H-3c-1 — Claim H5 evidence pack foundation tests."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_store import bind_case_channel_identity, get_case_by_id, save_case
from services.fiqa_api.inbox_triage.h5_task_link import mint_h5_claim_evidence_pack_link
from services.fiqa_api.inbox_triage.h5_task_token import (
    CLAIM_EVIDENCE_PACK_FLOW_SLOTS,
    FLOW_CLAIM_EVIDENCE_PACK,
    issue_h5_flow_token,
    issue_h5_task_token,
    verify_h5_task_token,
)
from services.fiqa_api.inbox_triage.h5_task_upload import (
    CLAIM_EVIDENCE_SAFETY_COPY,
    OTHER_PARTY_SKIP_REASONS,
    get_claim_evidence_slot_metadata,
)
from services.fiqa_api.routes.h5_task_upload import router as h5_router
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHOTO_FLOW_SLOTS,
    SERVICE_LANE_CLAIM,
    get_claim_attachment_slot_status,
)
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


def _save_claim_case(
    *,
    external_userid: str = "wm_claim_h5_foundation",
    open_kf_id: str = "wktest001",
) -> dict:
    saved = save_case(
        "claim h5 evidence foundation test",
        _triage_stub(),
        service_lane=SERVICE_LANE_CLAIM,
    )
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


def test_01_claim_h5_token_minted_and_validated():
    token = issue_h5_flow_token(
        case_id="case_claim_h5_01",
        lane="claim",
        flow=FLOW_CLAIM_EVIDENCE_PACK,
    )
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.case_id == "case_claim_h5_01"
    assert claims.lane == "claim"
    assert claims.flow == FLOW_CLAIM_EVIDENCE_PACK
    assert claims.slots == CLAIM_EVIDENCE_PACK_FLOW_SLOTS
    assert claims.slots[0] == "customer_damage_photo"


def test_02_add_vehicle_h5_token_still_validates():
    token = issue_h5_task_token(case_id="case_add_car_regression", lane="add_car", slot="vin_photo")
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.lane == "add_car"
    assert claims.slot == "vin_photo"

    flow_token = issue_h5_flow_token(case_id="case_add_car_flow")
    flow_claims = verify_h5_task_token(flow_token)
    assert flow_claims is not None
    assert flow_claims.lane == "add_car"
    assert flow_claims.flow == "add_vehicle_photo_flow"


def test_03_claim_first_slot_task_metadata():
    _setup_json_store()
    case = _save_claim_case()
    token = _claim_flow_token(case)
    resp = _client().get(f"/api/h5/tasks/{token}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["lane"] == "claim"
    assert data["flow"] == FLOW_CLAIM_EVIDENCE_PACK
    assert data["slot_key"] == "customer_damage_photo"
    assert "自己车损照片" in data["slot_label"]
    assert data["required_level"] == "required"
    assert data["eligible_for_ocr"] is False
    assert "不代表 claim 已正式提交" in data["safety_copy"]
    assert data["current_step"] == "customer_damage_photo"
    assert data["title"] == "理赔资料 · 车损照片"
    assert "损伤部位" in data["instruction"]


def test_04_other_party_slot_metadata():
    meta = get_claim_evidence_slot_metadata("other_party_vehicle_photo")
    assert meta["slot_key"] == "other_party_vehicle_photo"
    assert meta["skippable"] is True
    keys = {r["key"] for r in meta["skip_reasons"]}
    assert keys == {
        "no_other_party",
        "not_available",
        "hit_and_run",
        "customer_not_safe_to_collect",
    }


def test_05_scene_slot_metadata():
    meta = get_claim_evidence_slot_metadata("scene_photo")
    assert meta["slot_key"] == "scene_photo"
    assert meta["required_level"] == "optional"
    assert meta["skippable"] is True


def test_06_invalid_lane_rejected():
    with pytest.raises(ValueError, match="unsupported_lane"):
        issue_h5_task_token(case_id="case_bad", lane="random", slot="vin_photo")

    with pytest.raises(ValueError, match="unsupported_lane"):
        issue_h5_flow_token(case_id="case_bad", lane="random", flow=FLOW_CLAIM_EVIDENCE_PACK)


def test_07_claim_slot_names_are_canonical():
    assert CLAIM_PHOTO_FLOW_SLOTS == CLAIM_EVIDENCE_PACK_FLOW_SLOTS
    assert "other_party_vehicle_photo" in CLAIM_PHOTO_FLOW_SLOTS
    assert "other_vehicle_or_plate_photo" not in CLAIM_PHOTO_FLOW_SLOTS
    for slot in CLAIM_EVIDENCE_PACK_FLOW_SLOTS:
        meta = get_claim_evidence_slot_metadata(slot)
        assert meta["slot_key"] == slot


def test_08_claim_slot_upload_creates_attachment_metadata():
    _setup_json_store()
    set_gcs_upload_hook_for_tests(
        lambda *, bucket, object_path, content, content_type: f"gs://{bucket}/{object_path}"
    )
    case = _save_claim_case()
    token = _claim_flow_token(case)
    client = _client()
    resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "customer_damage_photo"},
        files={"file": ("damage.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["slot_assignment"] == "customer_damage_photo"
    assert body["flow_complete"] is False
    assert body["next_slot"] == "other_party_vehicle_photo"

    updated = get_case_by_id(case["case_id"])
    assert updated is not None
    atts = updated.get("case_attachments") or []
    assert len(atts) == 1
    att = atts[0]
    assert att["source"] == "h5_task"
    assert att["slot_assignment"] == "customer_damage_photo"
    assert att["flow"] == FLOW_CLAIM_EVIDENCE_PACK
    assert att["eligible_for_ocr"] is False


def test_09_claim_slot_status_inferred_received():
    _setup_json_store()
    set_gcs_upload_hook_for_tests(
        lambda *, bucket, object_path, content, content_type: f"gs://{bucket}/{object_path}"
    )
    case = _save_claim_case()
    token = _claim_flow_token(case)
    client = _client()
    resp = client.post(
        f"/api/h5/tasks/{token}/upload",
        data={"slot": "customer_damage_photo"},
        files={"file": ("damage.jpg", _tiny_jpeg(), "image/jpeg")},
    )
    assert resp.status_code == 200

    updated = get_case_by_id(case["case_id"])
    assert updated is not None
    status = get_claim_attachment_slot_status(updated, "customer_damage_photo")
    assert status == "received"


def test_10_mint_claim_evidence_pack_link():
    url = mint_h5_claim_evidence_pack_link(
        case_id="case_link_claim",
        external_userid="wm_secret_claim",
        base_url="https://example.test",
    )
    assert url.startswith("https://example.test/task/upload/h5t1.")
    token = url.rsplit("/", 1)[-1]
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.lane == "claim"
    assert claims.flow == FLOW_CLAIM_EVIDENCE_PACK
    assert claims.slots[0] == "customer_damage_photo"
    assert "wm_secret" not in url


def test_11_safety_copy_constant():
    assert "不代表 claim 已正式提交" in CLAIM_EVIDENCE_SAFETY_COPY
    assert len(OTHER_PARTY_SKIP_REASONS) == 4


def test_12_expired_claim_token_rejected():
    now = time.time()
    token = issue_h5_flow_token(
        case_id="case_exp_claim",
        lane="claim",
        flow=FLOW_CLAIM_EVIDENCE_PACK,
        ttl_seconds=60,
        now=now - 120,
    )
    assert verify_h5_task_token(token, now=now) is None
