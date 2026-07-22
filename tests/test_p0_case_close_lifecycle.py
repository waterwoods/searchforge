"""P0 — Broker Close → History lifecycle (Commit 2)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_close import (
    ERROR_ALREADY_CLOSED,
    ERROR_CASE_CLOSED_READ_ONLY,
    assert_customer_case_writable,
    case_is_closed_history,
    case_is_customer_writable,
    close_case,
)
from services.fiqa_api.inbox_triage.h5_task_intake import _load_writable_claim_case, patch_intake_fields
from services.fiqa_api.inbox_triage.h5_task_token import (
    issue_h5_intake_form_token,
    verify_h5_task_token,
)
from services.fiqa_api.inbox_triage.h5_task_upload import ingest_h5_slot_upload, mutate_h5_claim_evidence
from services.fiqa_api.inbox_triage.mp_customer_identity import (
    bind_active_case,
    lookup_bound_case_id,
    reset_mp_active_case_index_for_tests,
    resolve_active_case_for_person_link,
)
from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.inbox_triage.p20_customer_start_claim import start_customer_claim
from services.fiqa_api.inbox_triage.wechat_binding import opaque_person_link_key
from services.fiqa_api.routes import h5_task_intake as h5_routes
from services.fiqa_api.routes import inbox_triage as inbox_routes


@pytest.fixture(autouse=True)
def _clean_index():
    reset_mp_active_case_index_for_tests()
    yield
    reset_mp_active_case_index_for_tests()


def _wire_intake(monkeypatch) -> InMemoryIntakeStore:
    store = InMemoryIntakeStore()
    svc = P20CaseIntakeCommandService(store)
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.default_case_intake_service",
        lambda: svc,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_case_intake_command_service.default_case_intake_service",
        lambda: svc,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_server_client_id",
        lambda: "tenant_demo",
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_customer_start_claim_office_id",
        lambda: "office_demo",
    )
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.is_production_deployment",
        lambda: False,
    )

    def get_case(case_id: str):
        return store.cases.get(case_id)

    def persist(case_id: str, case: dict) -> bool:
        store.cases[case_id] = case
        return True

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_truth_repository.get_case_for_read",
        get_case,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_truth_repository.get_case_triage_stub_for_read",
        get_case,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.h5_task_intake.get_case_for_read",
        get_case,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.h5_task_upload.get_case_for_read",
        get_case,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.mp_customer_identity._load_case",
        get_case,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store._persist_case_after_update",
        persist,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store._require_case_storage_path",
        lambda: None,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store._load_case_for_mutation",
        get_case,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.get_case_by_id",
        get_case,
    )
    # case_close imports these by name — patch the bound symbols too.
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_close._persist_case_after_update",
        persist,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_close._require_case_storage_path",
        lambda: None,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_close._load_case_for_mutation",
        get_case,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_close._clear_intake_session_active_pointers",
        lambda _cid: 0,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.update_case_workbench_flags",
        lambda case_id, *, is_test=None, archived=None: _soft_archive(
            store, case_id, is_test=is_test, archived=archived
        ),
    )
    return store


def _soft_archive(store: InMemoryIntakeStore, case_id: str, *, is_test=None, archived=None):
    case = store.cases.get(case_id)
    if case is None:
        return None
    if is_test is not None:
        case["workbench_test"] = bool(is_test)
    if archived is not None:
        case["workbench_archived"] = bool(archived)
    return case


def _create_bound(monkeypatch, *, suffix: str) -> tuple[InMemoryIntakeStore, str, str, str]:
    store = _wire_intake(monkeypatch)
    link = opaque_person_link_key(suffix)
    out = start_customer_claim(
        command_id=f"cmd-{suffix}",
        idempotency_key=f"idem-{suffix}",
        session_id=link,
        accident_description=f"accident {suffix}",
        is_test=True,
    )
    assert out["outcome"] == "accepted"
    case_id = out["case_id"]
    token = str(out.get("resume_token") or "")
    assert lookup_bound_case_id(link) == case_id
    return store, link, case_id, token


def test_broker_closes_active_case_sets_history_and_clears_binding(monkeypatch):
    store, link, case_id, _token = _create_bound(monkeypatch, suffix="close-1")
    result = close_case(case_id, actor="office:office_demo", reason="founder qa")
    assert result["ok"] is True
    assert result["outcome"] == "closed"
    case = store.cases[case_id]
    assert case_is_closed_history(case)
    assert case["case_status"] == "closed"
    assert case["admin_lifecycle"] == "closed"
    assert case["case_history_state"] == "history"
    assert case["closed_at"]
    assert case["closed_by"] == "office:office_demo"
    assert case["close_reason"] == "founder qa"
    assert lookup_bound_case_id(link) is None
    assert resolve_active_case_for_person_link(link) is None


def test_customer_session_no_active_after_close(monkeypatch):
    _store, link, case_id, _token = _create_bound(monkeypatch, suffix="close-session")
    close_case(case_id, actor="broker:qa")
    assert resolve_active_case_for_person_link(link) is None


def test_same_identity_creates_new_active_after_close(monkeypatch):
    store, link, case_a, _token = _create_bound(monkeypatch, suffix="close-new")
    close_case(case_a, actor="broker:qa")
    second = start_customer_claim(
        command_id="cmd-close-new-2",
        idempotency_key="idem-close-new-2",
        session_id=link,
        accident_description="second accident after close",
        is_test=True,
    )
    assert second["outcome"] == "accepted"
    case_b = second["case_id"]
    assert case_b != case_a
    assert case_is_closed_history(store.cases[case_a])
    assert not case_is_closed_history(store.cases[case_b])
    assert lookup_bound_case_id(link) == case_b
    assert len(store.cases) == 2


def test_closed_case_still_exists_and_readable(monkeypatch):
    store, _link, case_id, _token = _create_bound(monkeypatch, suffix="close-read")
    close_case(case_id, actor="broker:qa")
    assert case_id in store.cases
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read

    loaded = get_case_for_read(case_id)
    assert loaded is not None
    assert case_is_closed_history(loaded)


def test_closed_case_patch_fails(monkeypatch):
    store, _link, case_id, _token = _create_bound(monkeypatch, suffix="close-patch")
    close_case(case_id, actor="broker:qa")
    with pytest.raises(ValueError, match=ERROR_CASE_CLOSED_READ_ONLY):
        _load_writable_claim_case(case_id)
    token = issue_h5_intake_form_token(case_id=case_id, lane="claim")
    claims = verify_h5_task_token(token)
    assert claims is not None
    with pytest.raises(ValueError, match=ERROR_CASE_CLOSED_READ_ONLY):
        patch_intake_fields(claims, step="injury", fields={"anyone_injured": "no"})
    assert store.cases[case_id].get("known_facts", {}).get("anyone_injured") != "no"


def test_closed_case_upload_and_submit_fail(monkeypatch):
    store, _link, case_id, _token = _create_bound(monkeypatch, suffix="close-upload")
    # Ensure claim lane for upload eligibility after close stamp.
    store.cases[case_id]["service_lane"] = "claim"
    close_case(case_id, actor="broker:qa")
    from services.fiqa_api.inbox_triage.h5_task_token import issue_h5_flow_token
    from services.fiqa_api.inbox_triage.h5_task_intake import submit_intake_form

    flow_token = issue_h5_flow_token(case_id=case_id, lane="claim", flow="claim_evidence_pack")
    claims = verify_h5_task_token(flow_token)
    assert claims is not None
    with pytest.raises(ValueError, match=ERROR_CASE_CLOSED_READ_ONLY):
        ingest_h5_slot_upload(
            claims,
            slot="vehicle_damage",
            content=b"fake-bytes",
            content_type="image/jpeg",
            filename="x.jpg",
        )
    with pytest.raises(ValueError, match=ERROR_CASE_CLOSED_READ_ONLY):
        mutate_h5_claim_evidence(
            claims,
            attachment_id="att_x",
            action="note",
            note="nope",
        )
    intake_token = issue_h5_intake_form_token(case_id=case_id, lane="claim")
    intake_claims = verify_h5_task_token(intake_token)
    assert intake_claims is not None
    with pytest.raises(ValueError, match=ERROR_CASE_CLOSED_READ_ONLY):
        submit_intake_form(intake_claims, submit_intent_id="intent-closed")
    assert case_is_closed_history(store.cases[case_id])


def test_old_resume_token_cannot_mutate_or_rebind(monkeypatch):
    store, link, case_a, token_a = _create_bound(monkeypatch, suffix="close-token")
    close_case(case_a, actor="broker:qa")
    second = start_customer_claim(
        command_id="cmd-close-token-b",
        idempotency_key="idem-close-token-b",
        session_id=link,
        accident_description="case b",
        is_test=True,
    )
    case_b = second["case_id"]
    # Old opaque resume may still identify Case A for read, but writes must fail.
    claims_a = verify_h5_task_token(token_a)
    if claims_a is not None:
        assert claims_a.case_id == case_a
    with pytest.raises(ValueError, match=ERROR_CASE_CLOSED_READ_ONLY):
        _load_writable_claim_case(case_a)
    assert lookup_bound_case_id(link) == case_b
    assert not case_is_closed_history(store.cases[case_b])


def test_repeat_close_idempotent(monkeypatch):
    _store, _link, case_id, _token = _create_bound(monkeypatch, suffix="close-idem")
    first = close_case(case_id, actor="broker:qa")
    second = close_case(case_id, actor="broker:qa")
    assert first["outcome"] == "closed"
    assert second["ok"] is True
    assert second["outcome"] == ERROR_ALREADY_CLOSED


def test_customer_cannot_close_via_h5(monkeypatch):
    _wire_intake(monkeypatch)
    app = FastAPI()
    app.include_router(h5_routes.router)
    client = TestClient(app)
    # No customer close route under /api/h5
    res = client.post("/api/h5/cases/case_x/close")
    assert res.status_code in (404, 405)


def test_soft_archive_does_not_release_binding(monkeypatch):
    store, link, case_id, _token = _create_bound(monkeypatch, suffix="soft-arch")
    from services.fiqa_api.inbox_triage.case_store import update_case_workbench_flags

    updated = update_case_workbench_flags(case_id, archived=True)
    assert updated is not None
    assert updated.get("workbench_archived") is True
    assert not case_is_closed_history(updated)
    assert lookup_bound_case_id(link) == case_id
    assert resolve_active_case_for_person_link(link) is not None
    assert case_is_customer_writable(store.cases[case_id])


def test_different_customer_unaffected(monkeypatch):
    store, link_a, case_a, _ta = _create_bound(monkeypatch, suffix="cust-a")
    link_b = opaque_person_link_key("cust-b")
    out_b = start_customer_claim(
        command_id="cmd-cust-b",
        idempotency_key="idem-cust-b",
        session_id=link_b,
        accident_description="B",
        is_test=True,
    )
    case_b = out_b["case_id"]
    close_case(case_a, actor="broker:qa")
    assert lookup_bound_case_id(link_a) is None
    assert lookup_bound_case_id(link_b) == case_b
    assert not case_is_closed_history(store.cases[case_b])


def test_http_broker_close_endpoint(monkeypatch):
    store, link, case_id, _token = _create_bound(monkeypatch, suffix="http-close")
    monkeypatch.setattr(
        "services.fiqa_api.routes.inbox_triage.get_case_for_read",
        lambda cid: store.cases.get(cid),
    )
    monkeypatch.setattr(
        "services.fiqa_api.routes.inbox_triage.assert_case_office_access_allowed",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        "services.fiqa_api.routes.inbox_triage._broker_actor_identity",
        lambda _req: "office:office_demo",
    )
    app = FastAPI()
    app.include_router(inbox_routes.router)
    client = TestClient(app)
    res = client.post(f"/api/inbox/cases/{case_id}/close", json={"reason": "pat"})
    assert res.status_code == 200
    body = res.json()
    assert body["outcome"] in ("closed", "already_closed")
    assert case_is_closed_history(store.cases[case_id])
    assert lookup_bound_case_id(link) is None


def test_assert_helpers():
    open_case = {"case_id": "c1", "case_status": "new"}
    closed = {
        "case_id": "c2",
        "case_status": "closed",
        "case_history_state": "history",
        "closed_at": "2026-07-22T00:00:00Z",
    }
    assert case_is_customer_writable(open_case)
    assert not case_is_customer_writable(closed)
    with pytest.raises(ValueError, match=ERROR_CASE_CLOSED_READ_ONLY):
        assert_customer_case_writable(closed)
    # Soft archive alone is writable
    archived = {"case_id": "c3", "case_status": "reviewing", "workbench_archived": True}
    assert case_is_customer_writable(archived)


def test_bind_helper_still_works_for_active(monkeypatch):
    store = _wire_intake(monkeypatch)
    link = opaque_person_link_key("bind-only")
    store.cases["case_bind"] = {"case_id": "case_bind", "case_status": "new", "service_lane": "claim"}
    bind_active_case(link, "case_bind")
    assert lookup_bound_case_id(link) == "case_bind"
