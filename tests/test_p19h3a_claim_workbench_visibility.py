"""P19H-3a — Claim case visibility in Workbench document intake API."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_store import save_case
from services.fiqa_api.inbox_triage.claim_workbench_display import (
    build_claim_display_status,
    display_status_is_broker_safe,
    enrich_claim_for_workbench,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.inbox_triage.workbench_enrichment import enrich_cases_for_workbench
from services.fiqa_api.routes.inbox_triage import router as inbox_router
from services.fiqa_api.wecom.claim_basics import ingest_claim_basics_message
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    SERVICE_LANE_CLAIM,
)
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.normalize import normalize_text_message


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


def _normalized(text: str, *, ext: str = "wm_claim_wb", msg_id: str = "m1") -> dict:
    return normalize_text_message(
        {
            "msgid": msg_id,
            "msgtype": "text",
            "text": {"content": text},
            "external_userid": ext,
        }
    )


def _api_client() -> TestClient:
    app = FastAPI()
    app.include_router(inbox_router)
    return TestClient(app)


def _seed_claim_basics_complete() -> dict:
    text = "今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门"
    result = ingest_claim_basics_message(
        _normalized(text, ext="wm_p19h3a", msg_id="m_claim_full"),
        classify_wecom_intent(text),
    )
    assert result["active_case_outcome"] == "claim_c1_sent"
    return result


def test_01_claim_accident_basics_complete_appears_in_workbench_api():
    seeded = _seed_claim_basics_complete()
    case_id = seeded["case_id"]
    resp = _api_client().get("/api/inbox/cases", params={"limit": 50})
    assert resp.status_code == 200
    cases = resp.json().get("cases") or []
    ids = [c.get("case_id") for c in cases]
    assert case_id in ids


def test_02_claim_item_includes_service_lane_claim():
    seeded = _seed_claim_basics_complete()
    case_id = seeded["case_id"]
    resp = _api_client().get("/api/inbox/cases", params={"limit": 50})
    row = next(c for c in resp.json()["cases"] if c["case_id"] == case_id)
    assert row.get("service_lane") == SERVICE_LANE_CLAIM


def test_03_claim_item_includes_accident_basics_fields():
    seeded = _seed_claim_basics_complete()
    case_id = seeded["case_id"]
    resp = _api_client().get("/api/inbox/cases", params={"limit": 50})
    row = next(c for c in resp.json()["cases"] if c["case_id"] == case_id)
    summary = row.get("claim_summary") or {}
    assert summary.get("accident_datetime")
    assert summary.get("accident_location")
    assert summary.get("accident_description")
    facts = row.get("known_facts") or {}
    assert facts.get("accident_datetime")
    assert facts.get("accident_location")
    assert facts.get("accident_description")


def test_04_claim_display_status_does_not_imply_claim_filed():
    seeded = _seed_claim_basics_complete()
    case_id = seeded["case_id"]
    resp = _api_client().get("/api/inbox/cases", params={"limit": 50})
    row = next(c for c in resp.json()["cases"] if c["case_id"] == case_id)
    status = str(row.get("display_status") or "")
    assert display_status_is_broker_safe(status)
    assert "filed" not in status.lower()
    assert row.get("workflow_phase") == CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE


def test_05_add_vehicle_cases_still_appear_unchanged():
    saved = save_case("add car", _triage_stub_add_car(), service_lane=SERVICE_LANE_ADD_CAR)
    _seed_claim_basics_complete()
    resp = _api_client().get("/api/inbox/cases", params={"limit": 50})
    row = next(c for c in resp.json()["cases"] if c["case_id"] == saved["case_id"])
    assert row.get("service_lane") == SERVICE_LANE_ADD_CAR
    assert row.get("primary_vehicle_summary") == "2024 Tesla Model 3"
    assert "claim_summary" not in row or row.get("claim_summary") is None


def test_06_partial_claim_case_does_not_break_api():
    partial = save_case(
        "claim partial",
        {
            "issue_category": "claim_intake",
            "urgency": "high",
            "manual_followup_needed": True,
            "broker_next_step": "Collect basics",
            "client_prep": "",
            "client_reply_draft": "",
            "known_facts": {"accident_datetime": "今天上午10点"},
            "collected_fields": ["accident_datetime"],
        },
        service_lane=SERVICE_LANE_CLAIM,
    )
    resp = _api_client().get("/api/inbox/cases", params={"limit": 50})
    assert resp.status_code == 200
    row = next(c for c in resp.json()["cases"] if c["case_id"] == partial["case_id"])
    assert row.get("service_lane") == SERVICE_LANE_CLAIM
    summary = row.get("claim_summary") or {}
    assert summary.get("accident_datetime") == "今天上午10点"
    assert summary.get("accident_location") is None
    assert display_status_is_broker_safe(str(row.get("display_status") or ""))


def test_enrich_claim_for_workbench_sets_display_title():
    case = enrich_claim_for_workbench(
        {
            "service_lane": SERVICE_LANE_CLAIM,
            "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
            "known_facts": {
                "accident_datetime": "今天上午10点",
                "accident_location": "Irvine Blvd",
                "accident_description": "刮蹭",
            },
            "collected_fields": [
                "accident_datetime",
                "accident_location",
                "accident_description",
            ],
        }
    )
    assert case["display_title"] == "Claim · 理赔资料"
    assert case["workbench_visible"] is True
    assert build_claim_display_status(case) == (
        "Claim Step 1 complete · Accident basics received"
    )


def test_enrich_cases_for_workbench_marks_claim_lane_explicit():
    cases = enrich_cases_for_workbench(
        [{"case_id": "c1", "service_lane": SERVICE_LANE_CLAIM, "known_facts": {}}]
    )
    assert cases[0]["workbench_lane_kind"] == "explicit"
