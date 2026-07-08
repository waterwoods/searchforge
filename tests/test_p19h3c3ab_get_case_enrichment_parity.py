"""P19H-3c-3AB — GET single case enrichment parity with list API."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_store import append_h5_gcs_attachment_metadata, save_case
from services.fiqa_api.inbox_triage.h5_task_token import FLOW_CLAIM_EVIDENCE_PACK
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.routes.inbox_triage import router as inbox_router
from services.fiqa_api.wecom.claim_basics import ingest_claim_basics_message
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    SERVICE_LANE_CLAIM,
)
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.normalize import normalize_text_message

_CLAIM_ENRICHMENT_KEYS = (
    "claim_summary",
    "claim_evidence_summary",
    "workflow_phase",
    "display_title",
    "display_status",
    "workbench_visible",
)


@pytest.fixture(autouse=True)
def _json_store():
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


def _api_client() -> TestClient:
    app = FastAPI()
    app.include_router(inbox_router)
    return TestClient(app)


def _triage_stub_add_car() -> dict:
    return {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": False,
        "broker_next_step": "Review add car packet",
        "client_prep": "",
        "client_reply_draft": "",
        "primary_vehicle_summary": "2024 Tesla Model 3",
        "quote_ready_status": "quote_ready",
    }


def _normalized(text: str, *, ext: str = "wm_claim_parity", msg_id: str = "m1") -> dict:
    return normalize_text_message(
        {
            "msgid": msg_id,
            "msgtype": "text",
            "text": {"content": text},
            "external_userid": ext,
        }
    )


def _seed_claim_basics_complete() -> dict:
    text = "今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门"
    result = ingest_claim_basics_message(
        _normalized(text, ext="wm_p19h3c3ab", msg_id="m_claim_parity"),
        classify_wecom_intent(text),
    )
    assert result["active_case_outcome"] == "claim_c1_sent"
    return result


def _h5_claim_attachment(*, slot: str, attachment_id: str = "att_h5_damage") -> dict:
    return {
        "attachment_id": attachment_id,
        "source": "h5_task",
        "flow": FLOW_CLAIM_EVIDENCE_PACK,
        "slot_assignment": slot,
        "filename": "damage.jpg",
        "mime_type": "image/jpeg",
        "received_at": "2026-07-09T18:00:00+00:00",
        "eligible_for_ocr": False,
    }


def _claim_with_h5_damage() -> str:
    seeded = _seed_claim_basics_complete()
    case_id = seeded["case_id"]
    updated = append_h5_gcs_attachment_metadata(case_id, _h5_claim_attachment(slot="customer_damage_photo"))
    assert updated is not None
    return case_id


def _parity_keys(row: dict) -> dict:
    return {k: row.get(k) for k in _CLAIM_ENRICHMENT_KEYS}


def test_01_claim_single_get_includes_evidence_summary():
    case_id = _claim_with_h5_damage()
    client = _api_client()
    resp = client.get(f"/api/inbox/cases/{case_id}")
    assert resp.status_code == 200
    row = resp.json()
    ces = row.get("claim_evidence_summary")
    assert ces is not None
    assert len(ces["slots"]) == 3
    by_key = {s["slot_key"]: s for s in ces["slots"]}
    assert by_key["customer_damage_photo"]["status"] == "received"
    assert (ces.get("broker_next_action") or "").strip()
    assert row.get("claim_summary") is not None


def test_02_list_and_single_endpoint_parity():
    case_id = _claim_with_h5_damage()
    client = _api_client()
    list_row = next(c for c in client.get("/api/inbox/cases", params={"limit": 50}).json()["cases"] if c["case_id"] == case_id)
    single_row = client.get(f"/api/inbox/cases/{case_id}").json()
    assert _parity_keys(list_row) == _parity_keys(single_row)
    assert list_row["workflow_phase"] == single_row["workflow_phase"]
    assert list_row["workflow_phase"] in (
        CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        "photos_in_progress",
    )


def test_03_add_vehicle_single_get_unaffected():
    saved = save_case("add car", _triage_stub_add_car(), service_lane=SERVICE_LANE_ADD_CAR)
    case_id = saved["case_id"]
    client = _api_client()
    resp = client.get(f"/api/inbox/cases/{case_id}")
    assert resp.status_code == 200
    row = resp.json()
    assert row.get("service_lane") == SERVICE_LANE_ADD_CAR
    assert row.get("primary_vehicle_summary") == "2024 Tesla Model 3"
    assert row.get("claim_evidence_summary") is None


def test_04_claim_without_attachments_still_has_evidence_summary():
    seeded = _seed_claim_basics_complete()
    case_id = seeded["case_id"]
    client = _api_client()
    row = client.get(f"/api/inbox/cases/{case_id}").json()
    ces = row.get("claim_evidence_summary")
    assert ces is not None
    assert len(ces["slots"]) == 3
    by_key = {s["slot_key"]: s for s in ces["slots"]}
    assert by_key["customer_damage_photo"]["status"] == "missing"
    assert by_key["other_party_vehicle_photo"]["status"] == "missing"
    assert by_key["scene_photo"]["status"] == "missing"
    assert (ces.get("broker_next_action") or "").strip()
