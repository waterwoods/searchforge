"""P19H-3h-1A — Claim H5 structured intake form tests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_store import get_case_by_id, save_case
from services.fiqa_api.inbox_triage.h5_task_link import mint_h5_claim_intake_form_link
from services.fiqa_api.inbox_triage.h5_task_token import (
    FLOW_CLAIM_INTAKE_FORM,
    issue_h5_intake_form_token,
    verify_h5_task_token,
)
from services.fiqa_api.routes.h5_task_intake import router as h5_intake_router
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    SERVICE_LANE_CLAIM,
    derive_claim_phase,
)


@pytest.fixture(autouse=True)
def _case_storage(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cases.json"
        path.write_text("[]", encoding="utf-8")
        monkeypatch.setenv("UNIFIED_INTAKE_CASE_STORAGE_PATH", str(path))
        yield


def _app() -> TestClient:
    app = FastAPI()
    app.include_router(h5_intake_router)
    return TestClient(app)


def _triage_stub() -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Collect claim basics via H5.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "claim_phase": "accident_basics_in_progress",
    }


def _save_claim_case(case_id: str = "case_claim_h5_intake") -> str:
    saved = save_case(
        "我要理赔",
        _triage_stub(),
        service_lane=SERVICE_LANE_CLAIM,
    )
    return str(saved.get("case_id") or case_id)


def test_intake_form_token_mint_and_verify():
    token = issue_h5_intake_form_token(case_id="case_tok", lane="claim")
    assert token.startswith("h5t1.")
    claims = verify_h5_task_token(token)
    assert claims is not None
    assert claims.flow == FLOW_CLAIM_INTAKE_FORM
    assert claims.is_intake_form_token
    assert claims.case_id == "case_tok"


def test_mint_link_uses_claim_route(monkeypatch):
    monkeypatch.setenv("H5_TASK_FRONTEND_BASE_URL", "https://example.test")
    url = mint_h5_claim_intake_form_link(case_id="case_link")
    assert url.startswith("https://example.test/task/claim/h5t1.")


def test_h5_intake_happy_path_and_idempotent_submit():
    case_id = _save_claim_case()
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()
    intent = "11111111-2222-4333-8444-555555555555"

    r0 = client.get(f"/api/h5/tasks/{token}/intake")
    assert r0.status_code == 200
    data0 = r0.json()
    assert data0["flow"] == FLOW_CLAIM_INTAKE_FORM
    assert data0["current_step"] == "injury"
    assert data0["submitted"] is False

    steps = [
        ("injury", {"anyone_injured": "no"}),
        ("time_location", {"accident_datetime": "今天上午10点", "accident_location": "Irvine Blvd"}),
        ("story", {"accident_description": "我停在红灯前，后车追尾撞上我的车。"}),
        ("vehicle_other_party", {"own_vehicle_info": "2020 Toyota Camry"}),
    ]
    for step, fields in steps:
        resp = client.patch(f"/api/h5/tasks/{token}/fields", json={"step": step, "fields": fields})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["completed_count"] >= 1

    r_review = client.get(f"/api/h5/tasks/{token}/intake")
    assert r_review.json()["current_step"] == "review"

    r_submit = client.post(
        f"/api/h5/tasks/{token}/submit",
        json={"submit_intent_id": intent},
        headers={"X-Submit-Intent-Id": intent},
    )
    assert r_submit.status_code == 200
    submit_body = r_submit.json()
    assert submit_body["submitted"] is True
    assert submit_body["already_submitted"] is False

    case = get_case_by_id(case_id) or {}
    facts = case.get("known_facts") or {}
    assert facts.get("anyone_injured") == "no"
    assert facts.get("accident_location") == "Irvine Blvd"
    timeline = case.get("claim_timeline") or []
    event_types = [str(e.get("event_type")) for e in timeline]
    assert "h5_step_complete" in event_types
    assert event_types.count("customer_submitted_intake") == 1
    assert derive_claim_phase(case) == CLAIM_PHASE_INTAKE_READY_FOR_BROKER

    r_dup = client.post(
        f"/api/h5/tasks/{token}/submit",
        json={"submit_intent_id": intent},
        headers={"X-Submit-Intent-Id": intent},
    )
    assert r_dup.status_code == 200
    assert r_dup.json()["already_submitted"] is True
    case2 = get_case_by_id(case_id) or {}
    timeline2 = case2.get("claim_timeline") or []
    assert sum(1 for e in timeline2 if e.get("event_type") == "customer_submitted_intake") == 1


def test_patch_after_submit_rejected():
    case_id = _save_claim_case("case_submit_guard")
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()
    intent = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"

    for step, fields in [
        ("injury", {"anyone_injured": "no"}),
        ("time_location", {"accident_datetime": "昨天", "accident_location": "LA downtown"}),
        ("story", {"accident_description": "对方变道刮到我左前门，双方下车交换信息。"}),
        ("vehicle_other_party", {"own_vehicle_info": "Honda Civic"}),
    ]:
        assert client.patch(
            f"/api/h5/tasks/{token}/fields",
            json={"step": step, "fields": fields},
        ).status_code == 200

    assert client.post(
        f"/api/h5/tasks/{token}/submit",
        json={"submit_intent_id": intent},
    ).status_code == 200

    blocked = client.patch(
        f"/api/h5/tasks/{token}/fields",
        json={"step": "story", "fields": {"accident_description": "尝试再次修改经过描述内容。"}},
    )
    assert blocked.status_code == 409
