"""API route contract for AI Request More drafting — read-only, no send."""

from __future__ import annotations

import copy

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.routes import inbox_triage as routes
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

CASE_ID = "case_api_ai_draft"


def _case() -> dict:
    return {
        "case_id": CASE_ID,
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "client_id": "tenant_demo",
        "asserted_org_id": "office_demo",
        "workbench_test": True,
        "known_facts": {"vehicle_make": "Toyota", "vehicle_model": "Camry"},
    }


def _build_client(monkeypatch) -> tuple[TestClient, P20CaseIntakeCommandService, InMemoryIntakeStore]:
    for name in (
        "REQUEST_MORE_ASSISTANT_ENABLED",
        "REQUEST_MORE_ASSISTANT_LLM",
        "REQUEST_MORE_ASSISTANT_OFFICE_ALLOWLIST",
    ):
        monkeypatch.delenv(name, raising=False)
    store = InMemoryIntakeStore(cases={CASE_ID: _case()})
    service = P20CaseIntakeCommandService(store)
    app = FastAPI()
    app.include_router(routes.router)
    monkeypatch.setattr(routes, "default_case_intake_service", lambda: service)
    monkeypatch.setattr(
        routes, "get_case_for_read", lambda case_id: _case() if case_id == CASE_ID else None
    )
    monkeypatch.setattr(routes, "assert_case_office_access_allowed", lambda *_a, **_k: None)
    monkeypatch.setattr(routes, "client_asserted_office_id", lambda _req: "office_demo")
    return TestClient(app), service, store


def test_assist_returns_template_draft_without_touching_the_case(monkeypatch):
    client, service, store = _build_client(monkeypatch)
    created = service.create_claim(
        broker_id="office:demo",
        office_id="office_demo",
        tenant_id="tenant_demo",
        command_id="cmd-create-api-ai",
        idempotency_key="idem-create-api-ai",
        inputs={"is_test": True},
    )
    real_case_id = created["case_id"]
    store.cases[CASE_ID] = store.cases.pop(real_case_id)
    store.cases[CASE_ID]["case_id"] = CASE_ID
    aggregate = store.aggregates.pop(real_case_id)
    aggregate.case_id = CASE_ID
    store.aggregates[CASE_ID] = aggregate
    version_before = service.fetch_projection(CASE_ID)["aggregate_version"]
    cases_before = copy.deepcopy(store.cases)

    response = client.post(f"/api/inbox/cases/{CASE_ID}/request-draft-assist", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["drafting_available"] is True
    assert body["lifecycle_mutated"] is False
    assert [item["field_key"] for item in body["items"]] == [
        "vin",
        "vehicle_information",
        "policy_or_insurance_card",
    ]
    assert "VIN" in body["draft_text"]
    assert service.fetch_projection(CASE_ID)["aggregate_version"] == version_before
    assert store.cases == cases_before
    assert store.drafts == {}


def test_assist_rejects_unknown_case(monkeypatch):
    client, _service, _store = _build_client(monkeypatch)
    response = client.post("/api/inbox/cases/case_missing/request-draft-assist", json={})
    assert response.status_code == 404
