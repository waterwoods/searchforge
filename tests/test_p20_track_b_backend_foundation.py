"""P20 Track B Phase 1 contract, persistence, and provenance regressions."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.fiqa_api.db.service_record_repository import (
    _build_extra,
    _build_structured_payload,
    _hydrate_extra_pilot_fields,
)
from services.fiqa_api.inbox_triage.case_store import (
    get_case_by_id,
    patch_case_known_facts,
    save_case,
)
from services.fiqa_api.inbox_triage.h5_task_intake import (
    build_customer_task_contract,
    intake_info_for_token,
    patch_intake_fields,
    submit_intake_form,
)
from services.fiqa_api.inbox_triage.h5_task_token import issue_h5_intake_form_token, verify_h5_task_token
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


@pytest.fixture(autouse=True)
def _case_storage(monkeypatch, tmp_path: Path):
    path = tmp_path / "cases.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(path))
    yield


def _claim_case() -> tuple[str, object]:
    case = save_case(
        "我要理赔",
        {
            "issue_category": "claim_intake",
            "urgency": "high",
            "manual_followup_needed": True,
            "broker_next_step": "Collect claim facts.",
            "client_prep": "",
            "client_reply_draft": "",
            "handoff_ready": False,
        },
        service_lane=SERVICE_LANE_CLAIM,
    )
    case_id = str(case["case_id"])
    claims = verify_h5_task_token(issue_h5_intake_form_token(case_id=case_id))
    assert claims is not None
    return case_id, claims


def _complete_required_h5_fields(claims: object) -> None:
    for step, fields in (
        ("injury", {"anyone_injured": "no"}),
        ("time_location", {"accident_datetime": "2026-07-12T10:00:00Z", "accident_location": "Irvine Blvd"}),
        ("story", {"accident_description": "我停在红灯前，后车追尾撞上我的车。"}),
        ("vehicle_other_party", {"own_vehicle_info": "2020 Toyota Camry"}),
    ):
        patch_intake_fields(claims, step=step, fields=fields)  # type: ignore[arg-type]


def test_task_contract_is_customer_safe_and_tracks_existing_gates():
    case_id, claims = _claim_case()
    _complete_required_h5_fields(claims)

    payload = intake_info_for_token(claims)  # type: ignore[arg-type]
    contract = payload["task_contract"]
    serialized = json.dumps(contract, ensure_ascii=False)

    assert contract["contract_version"] == "0"
    assert contract["task_id"] != case_id
    assert contract["task_status"] == "review_ready"
    assert contract["progress"] == {"completed": 5, "total": 5}
    assert contract["review_ready"] is True
    assert contract["submit_ready"] is True
    assert contract["next_action"]["type"] == "submit"
    assert contract["fields"]["accident_location"] == "Irvine Blvd"
    for forbidden in ("case_id", "tenant_id", "claim_phase", "provenance", "confidence"):
        assert forbidden not in serialized

    submitted = submit_intake_form(claims, submit_intent_id="p20-contract-intent-0001")  # type: ignore[arg-type]
    assert submitted["task_contract"]["task_status"] == "submitted"
    assert submitted["task_contract"]["submit_ready"] is False


def test_postgres_extra_allowlist_round_trips_only_approved_task_state():
    case = {
        "h5_intake_state": {
            "last_step": "review",
            "task_revision": 4,
            "field_dedup_keys": ["h5_field:case:story:a"],
            "submit_intent_ids": ["intent-1"],
        },
        "known_fact_provenance": {
            "accident_location": {"source": "customer_task", "status": "customer_confirmed"}
        },
        "known_fact_conflicts": [{"field": "accident_location", "status": "needs_broker_review"}],
        "unapproved_runtime_blob": {"must_not": "persist"},
    }
    extra = _build_extra(case)
    hydrated: dict = {}
    _hydrate_extra_pilot_fields(hydrated, extra)

    assert hydrated["h5_intake_state"]["submit_intent_ids"] == ["intent-1"]
    assert hydrated["known_fact_provenance"]["accident_location"]["source"] == "customer_task"
    assert hydrated["known_fact_conflicts"][0]["field"] == "accident_location"
    assert "unapproved_runtime_blob" not in extra
    assert "unapproved_runtime_blob" not in hydrated


def test_pg_parity_rehydrates_submitted_claim_contract_without_json_read():
    """Synthetic Claim parity: task writes → PG packets → rehydrated task contract."""
    case_id, claims = _claim_case()
    _complete_required_h5_fields(claims)
    submit_intake_form(claims, submit_intent_id="p20-pg-parity-intent-0001")  # type: ignore[arg-type]
    source = get_case_by_id(case_id) or {}
    source["case_attachments"] = [
        {
            "attachment_id": "att_pg_fixture",
            "source": "h5_task",
            "mime_type": "image/jpeg",
            "slot_assignment": "customer_damage_photo",
        }
    ]

    structured = _build_structured_payload(source)
    rehydrated = {
        **structured,
        "case_id": source["case_id"],
        "created_at": source["created_at"],
        "updated_at": source["updated_at"],
        "case_status": source["case_status"],
        "case_messages": source.get("case_messages") or [],
        "case_activity": source.get("case_activity") or [],
        "source_text": source.get("source_text") or "",
    }
    _hydrate_extra_pilot_fields(rehydrated, _build_extra(source))

    contract = build_customer_task_contract(rehydrated, task_id="opaque-pg-task")
    assert rehydrated["h5_intake_state"]["submit_intent_ids"] == ["p20-pg-parity-intent-0001"]
    assert rehydrated["known_fact_provenance"]["accident_location"]["source"] == "customer_task"
    assert rehydrated["case_attachments"][0]["attachment_id"] == "att_pg_fixture"
    assert contract["task_status"] == "submitted"
    assert contract["submit_ready"] is False
    assert contract["fields"]["accident_location"] == "Irvine Blvd"


def test_provenance_guard_preserves_confirmed_fact_and_logs_conflict():
    case_id, claims = _claim_case()
    patch_intake_fields(
        claims,  # type: ignore[arg-type]
        step="time_location",
        fields={"accident_datetime": "2026-07-12T10:00:00Z", "accident_location": "Irvine Blvd"},
    )

    patch_case_known_facts(
        case_id,
        {"accident_location": "微信消息中的另一地点"},
        source="wecom_customer_message",
        status="customer_supplement",
    )
    patch_case_known_facts(
        case_id,
        {"accident_location": "AI 推测地点"},
        source="ai_suggestion",
    )
    guarded = get_case_by_id(case_id) or {}
    assert guarded["known_facts"]["accident_location"] == "Irvine Blvd"
    assert len(guarded["known_fact_conflicts"]) == 2
    assert any(event["event_type"] == "fact_conflict_detected" for event in guarded["claim_timeline"])

    patch_case_known_facts(
        case_id,
        {"accident_location": "Broker confirmed location"},
        source="broker_confirmed",
        status="confirmed",
        explicit_broker_action=True,
    )
    broker_updated = get_case_by_id(case_id) or {}
    assert broker_updated["known_facts"]["accident_location"] == "Broker confirmed location"
    assert any(event["event_type"] == "broker_confirmed_fact_updated" for event in broker_updated["claim_timeline"])


def test_strict_postgres_read_does_not_consult_json_store(monkeypatch):
    from services.fiqa_api.inbox_triage import case_truth_repository as repository

    monkeypatch.setenv("SERVICE_RECORD_DATABASE_URL", "postgresql://invalid")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_READS", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", "1")
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "0")
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_READ_FALLBACK", "0")
    pg_case = {
        "case_id": "case_pg_only",
        "case_status": "new",
        "issue_category": "claim_intake",
        "urgency": "high",
        "broker_next_step": "review",
        "client_prep": "",
        "client_reply_draft": "",
        "manual_followup_needed": True,
        "created_at": "2026-07-12T00:00:00Z",
        "updated_at": "2026-07-12T00:00:00Z",
        "case_messages": [],
        "case_activity": [],
        "source_text": "",
        "h5_intake_state": {"submit_intent_ids": ["intent-pg"]},
        "known_fact_provenance": {"accident_location": {"source": "customer_task"}},
    }
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.load_full_case_from_postgres",
        lambda case_id: pg_case if case_id == "case_pg_only" else None,
    )
    monkeypatch.setattr(repository, "json_get_case_by_id", lambda _case_id: pytest.fail("JSON store consulted"))

    loaded = repository.get_case_for_read("case_pg_only")
    assert loaded is not None
    assert loaded["h5_intake_state"]["submit_intent_ids"] == ["intent-pg"]
    assert loaded["known_fact_provenance"]["accident_location"]["source"] == "customer_task"
