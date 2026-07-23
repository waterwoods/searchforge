"""P26H QA fixture runner — security, cleanup scope, and HTTP gates."""

from __future__ import annotations

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage import p26h_qa_fixture_runner as fx
from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.routes import p26h_fixture as fixture_routes


@pytest.fixture
def enable_runner(monkeypatch):
    monkeypatch.setenv("ENABLE_P26H_FIXTURE_RUNNER", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_QA_FIXTURE_SURFACE", "1")
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.is_production_mode",
        lambda: False,
    )


@pytest.fixture
def intake_store(monkeypatch):
    store = InMemoryIntakeStore()
    svc = P20CaseIntakeCommandService(store)
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.default_case_intake_service",
        lambda: svc,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_server_client_id",
        lambda: "tenant_p26h",
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_customer_start_claim_office_id",
        lambda: "office_p26h",
    )
    # Persist/tag path: map get_case_for_read + _persist to in-memory store.
    def get_case(case_id: str):
        return store.cases.get(case_id)

    def persist(case_id: str, case: dict) -> bool:
        store.cases[case_id] = case
        return True

    def delete(case_id: str) -> bool:
        return store.cases.pop(case_id, None) is not None

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_truth_repository.get_case_for_read",
        get_case,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store._persist_case_after_update",
        persist,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.delete_case",
        delete,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.list_all_cases",
        lambda: list(store.cases.values()),
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.get_case_by_id",
        get_case,
    )

    # Evidence helpers mutate via get_case_for_read + persist already patched;
    # patch slot/attachment helpers to update store directly when needed.
    def append_meta(case_id: str, meta: dict):
        case = store.cases.get(case_id)
        if case is None:
            return None
        case.setdefault("case_attachments", []).append(meta)
        return case

    def record_slot(case_id: str, slot: str, attachment_id: str):
        case = store.cases.get(case_id)
        if case is None:
            return None
        case.setdefault("claim_attachment_slots", {})[slot] = {
            "status": "received",
            "attachment_ids": [attachment_id],
        }
        summary = case.setdefault(
            "claim_evidence_summary",
            {"received_slots": [], "missing_required_slots": []},
        )
        received = summary.setdefault("received_slots", [])
        if slot not in received:
            received.append(slot)
        return case

    def append_event(case_id: str, event: dict):
        case = store.cases.get(case_id)
        if case is None:
            return None
        case.setdefault("timeline_events", []).append(event)
        return case

    def patch_facts(case_id: str, facts: dict, source: str = ""):
        case = store.cases.get(case_id)
        if case is None:
            return None
        case.setdefault("known_facts", {}).update(facts)
        return case

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.append_h5_gcs_attachment_metadata",
        append_meta,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.record_claim_evidence_slot_received",
        record_slot,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.append_claim_timeline_event",
        append_event,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.patch_case_known_facts",
        patch_facts,
    )

    def apply_compat(case_id: str, patch: dict):
        case = store.cases.get(case_id)
        if case is None:
            return None
        case.update(patch)
        return case

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.apply_p20_slice1_compat_projection",
        apply_compat,
    )
    return store


def test_fixture_runner_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_P26H_FIXTURE_RUNNER", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_QA_FIXTURE_SURFACE", raising=False)
    assert fx.fixture_runner_enabled() is False
    with pytest.raises(ValueError, match="p26h_fixture_runner_disabled"):
        fx.assert_fixture_runner_allowed()


def test_fixture_runner_requires_both_flags(monkeypatch):
    monkeypatch.setenv("ENABLE_P26H_FIXTURE_RUNNER", "1")
    monkeypatch.delenv("UNIFIED_INTAKE_QA_FIXTURE_SURFACE", raising=False)
    assert fx.fixture_runner_enabled() is False
    with pytest.raises(ValueError, match="p26h_fixture_surface_disabled"):
        fx.assert_fixture_runner_allowed()


def test_production_like_requires_support_key(monkeypatch):
    monkeypatch.setenv("ENABLE_P26H_FIXTURE_RUNNER", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_QA_FIXTURE_SURFACE", "1")
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.is_production_mode",
        lambda: True,
    )
    with pytest.raises(ValueError, match="p26h_fixture_support_key_required"):
        fx.assert_fixture_runner_allowed()


def test_create_cleanup_scoped_to_run(enable_runner, intake_store, monkeypatch):
    run = fx.create_run()
    run_id = run["harness_run_id"]
    other = fx.create_run()["harness_run_id"]

    a = fx.create_fresh_claim(harness_run_id=run_id, suffix="a")
    b = fx.create_fresh_claim(harness_run_id=other, suffix="b")
    assert a["case_id"] != b["case_id"]
    assert a["case_id"] in fx.list_run_case_ids(run_id)
    assert b["case_id"] not in fx.list_run_case_ids(run_id)

    # Cross-run inspect refused
    with pytest.raises(ValueError, match="fixture_case_not_in_run"):
        fx.inspect_case(harness_run_id=run_id, case_id=b["case_id"])

    cleaned = fx.cleanup_run(run_id)
    assert cleaned["cleanup"] == "PASS"
    assert a["case_id"] in cleaned["deleted_case_ids"]
    assert a["case_id"] not in intake_store.cases
    assert b["case_id"] in intake_store.cases  # other run untouched

    fx.cleanup_run(other)


def test_cleanup_refuses_camry_and_untagged(enable_runner, intake_store, monkeypatch):
    run_id = fx.create_run()["harness_run_id"]
    # Plant a Camry-looking case with forged harness_run_id — still refuse by demo_name.
    intake_store.cases["case_camry_forge"] = {
        "case_id": "case_camry_forge",
        "workbench_test": True,
        "demo_name": "camry_golden_qa",
        "harness_run_id": run_id,
        "harness_cleanup_eligible": True,
    }
    # Untagged production-like case must not appear in list_run_case_ids
    intake_store.cases["case_real"] = {
        "case_id": "case_real",
        "workbench_test": False,
        "demo_name": "",
        "harness_run_id": run_id,
    }
    assert "case_real" not in fx.list_run_case_ids(run_id)
    # Camry matches SQL/list filters if tagged same run — cleanup must refuse
    monkeypatch.setattr(fx, "list_run_case_ids", lambda _rid: ["case_camry_forge"])
    cleaned = fx.cleanup_run(run_id)
    assert "case_camry_forge" in cleaned["refused_case_ids"]
    assert "case_camry_forge" in intake_store.cases


def test_tokens_masked_in_create_response(enable_runner, intake_store):
    run_id = fx.create_run()["harness_run_id"]
    created = fx.create_fresh_claim(harness_run_id=run_id, suffix="mask")
    assert created.get("resume_token")
    assert "…" in created.get("resume_token_masked", "")
    expired = fx.issue_expired_token(harness_run_id=run_id, case_id=created["case_id"])
    assert "expired_token_masked" in expired
    assert "resume_token" not in expired
    assert expired["rejected_as_expected"] is True
    fx.cleanup_run(run_id)


def test_create_accepts_resumed_same_identity(enable_runner, intake_store, monkeypatch):
    """One Active Case: fixture create must treat outcome=resumed as success."""
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.service_record_database_url",
        lambda: "postgresql://fixture-test",
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.start_customer_claim",
        lambda **_kwargs: {
            "outcome": "resumed",
            "case_id": "case_fx_resumed",
            "resume_token": "h5t1.resumed-token",
        },
    )
    intake_store.cases["case_fx_resumed"] = {
        "case_id": "case_fx_resumed",
        "service_lane": "claim",
        "case_status": "new",
        "known_facts": {"accident_description": "已有案件"},
        "claim_evidence_summary": {
            "received_slots": ["scene_photo"],
            "missing_required_slots": [],
        },
        "case_attachments": [{"attachment_id": "att_keep"}],
    }
    run_id = fx.create_run()["harness_run_id"]
    created = fx.create_fresh_claim(harness_run_id=run_id, suffix="resumed")
    assert created["case_id"] == "case_fx_resumed"
    assert created["outcome"] == "resumed"
    assert created["resume_token"]
    # Resume must not wipe prior evidence.
    kept = intake_store.cases["case_fx_resumed"]
    assert kept["claim_evidence_summary"]["received_slots"] == ["scene_photo"]
    assert kept["case_attachments"]
    fx.cleanup_run(run_id)


def test_broker_followup_rejects_closed_history(enable_runner, intake_store):
    from services.fiqa_api.inbox_triage.case_close import ERROR_CASE_CLOSED_READ_ONLY

    run_id = fx.create_run()["harness_run_id"]
    created = fx.create_fresh_claim(harness_run_id=run_id, suffix="closed-fu")
    cid = created["case_id"]
    case = intake_store.cases[cid]
    case["case_status"] = "closed"
    case["admin_lifecycle"] = "closed"
    case["case_history_state"] = "history"
    case["closed_at"] = "2026-07-22T00:00:00Z"
    result = fx.create_broker_followup(harness_run_id=run_id, case_id=cid)
    assert result["ok"] is False
    assert result["outcome"] == "rejected"
    assert result["error_code"] == ERROR_CASE_CLOSED_READ_ONLY
    fx.cleanup_run(run_id)


def test_http_refuses_when_disabled(monkeypatch):
    monkeypatch.delenv("ENABLE_P26H_FIXTURE_RUNNER", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_QA_FIXTURE_SURFACE", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    app = FastAPI()
    app.include_router(fixture_routes.router)
    client = TestClient(app)
    status = client.get("/api/inbox/support/p26h-fixture/status")
    assert status.status_code == 200
    assert status.json()["enabled"] is False
    denied = client.post("/api/inbox/support/p26h-fixture/runs")
    assert denied.status_code == 403


def test_http_refuses_invalid_support_key(monkeypatch, enable_runner):
    monkeypatch.setenv("UNIFIED_INTAKE_SUPPORT_API_KEY", "correct-key-value-32chars-min!!")
    app = FastAPI()
    app.include_router(fixture_routes.router)
    client = TestClient(app)
    bad = client.post(
        "/api/inbox/support/p26h-fixture/runs",
        headers={"X-Unified-Intake-Support-Key": "wrong"},
    )
    assert bad.status_code == 401
    good = client.post(
        "/api/inbox/support/p26h-fixture/runs",
        headers={"X-Unified-Intake-Support-Key": "correct-key-value-32chars-min!!"},
    )
    assert good.status_code == 200
    assert good.json()["harness_run_id"].startswith("p26h_")


def test_qa_harness_fail_closed_without_transport(monkeypatch):
    monkeypatch.delenv("P26H_QA_BASE_URL", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_QA_BASE_URL", raising=False)
    monkeypatch.delenv("P26H_QA_TRANSPORT", raising=False)
    from scripts.golden_customer_flow import run_qa

    report = run_qa()
    assert not report.ok
    assert report.failures[0].layer == "Fixture Runner"
    assert report.cleanup_result == "SKIPPED"


def test_harness_tags_survive_postgres_extra_bag():
    """Permanent regression: harness_run_id must round-trip through PG extra."""
    from services.fiqa_api.db.service_record_repository import (
        _build_extra,
        _hydrate_extra_pilot_fields,
    )

    case = {
        "case_id": "case_p26h_tag",
        "workbench_test": True,
        "demo_name": "p26h_ephemeral",
        "harness_run_id": "p26h_20260718220000_deadbeef01",
        "harness_created_at": "2026-07-18T22:00:00Z",
        "harness_environment": "qa",
        "harness_cleanup_eligible": True,
        "exclude_from_production_metrics": True,
    }
    extra = _build_extra(case)
    assert extra["harness_run_id"] == "p26h_20260718220000_deadbeef01"
    assert extra["demo_name"] == "p26h_ephemeral"
    assert extra["workbench_test"] is True

    hydrated: dict = {"case_id": "case_p26h_tag"}
    _hydrate_extra_pilot_fields(hydrated, extra)
    assert hydrated["harness_run_id"] == "p26h_20260718220000_deadbeef01"
    assert hydrated["harness_cleanup_eligible"] is True
    assert fx._is_run_case(hydrated, "p26h_20260718220000_deadbeef01")
