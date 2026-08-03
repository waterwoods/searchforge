"""Focused tests for Stage 2 case activity timing instrumentation."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.case_activity_events import (
    EVENT_BROKER_FIRST_OPENED,
    EVENT_CUSTOMER_FIRST_ACTION,
    EVENT_CUSTOMER_INTAKE_OPENED,
    SCHEMA_VERSION,
    attach_case_activity_timing,
    get_case_activity_timing,
    hash_session_id,
    record_broker_first_opened,
    record_case_activity_event,
    record_customer_first_action,
    record_customer_intake_opened,
    reset_case_activity_events_for_tests,
)


def setup_function() -> None:
    reset_case_activity_events_for_tests()


def test_customer_intake_opened_first_wins():
    r1 = record_customer_intake_opened("case_t1", source_surface="mini_program", session_id="sess_abc")
    assert r1["ok"] is True
    assert r1["recorded"] is True
    assert r1["event_type"] == EVENT_CUSTOMER_INTAKE_OPENED
    assert r1["actor_role"] == "customer"
    assert r1["schema_version"] == SCHEMA_VERSION
    assert r1["session_id_hash"] == hash_session_id("sess_abc")
    first_ts = r1["created_at"]

    r2 = record_customer_intake_opened("case_t1", source_surface="h5_intake", session_id="sess_other")
    assert r2["recorded"] is False
    assert r2["duplicate"] is True
    assert r2["created_at"] == first_ts

    timing = get_case_activity_timing("case_t1")
    assert timing["customer_intake_opened_at"] == first_ts


def test_customer_first_action_idempotent_and_implies_open():
    r = record_customer_first_action(
        "case_t2",
        source_surface="mini_program",
        meta={"command_type": "policy_context_confirm"},
    )
    assert r["recorded"] is True
    assert r["event_type"] == EVENT_CUSTOMER_FIRST_ACTION
    timing = get_case_activity_timing("case_t2")
    assert timing["customer_intake_opened_at"]
    assert timing["customer_first_action_at"]

    r2 = record_customer_first_action("case_t2", source_surface="h5_intake")
    assert r2["duplicate"] is True
    assert r2["created_at"] == timing["customer_first_action_at"]


def test_broker_first_opened_refresh_does_not_reset():
    r1 = record_broker_first_opened("case_t3", source_surface="broker_workbench")
    assert r1["recorded"] is True
    assert r1["event_type"] == EVENT_BROKER_FIRST_OPENED
    assert r1["actor_role"] == "broker"
    ts = r1["created_at"]

    r2 = record_broker_first_opened("case_t3")
    assert r2["duplicate"] is True
    assert r2["created_at"] == ts


def test_actor_separation_and_no_pii_payload():
    r = record_case_activity_event(
        case_id="case_t4",
        event_type=EVENT_CUSTOMER_FIRST_ACTION,
        actor_role="customer",
        source_surface="mini_program",
        session_id="raw-session-token-should-hash",
        meta={
            "command_type": "story_save",
            "accident_text": "SHOULD_NOT_STORE",
            "customer_message": "SHOULD_NOT_STORE",
            "raw_token": "dit_secret",
            "surface_detail": "start_claim",
        },
    )
    assert r["ok"] is True
    assert r["actor_role"] == "customer"
    assert "raw-session-token" not in str(r.get("session_id_hash") or "")
    assert r["session_id_hash"] == hash_session_id("raw-session-token-should-hash")
    meta = r.get("meta") or {}
    assert "accident_text" not in meta
    assert "customer_message" not in meta
    assert "raw_token" not in meta
    assert meta.get("command_type") == "story_save"
    assert meta.get("surface_detail") == "start_claim"


def test_server_timestamps_are_iso_z():
    r = record_customer_intake_opened("case_t5", source_surface="h5_intake")
    assert r["created_at"].endswith("Z")
    assert "T" in r["created_at"]


def test_attach_case_activity_timing_additive():
    record_broker_first_opened("case_t6")
    case = {"case_id": "case_t6", "formal_submitted_at": "2026-08-03T12:00:00Z"}
    attach_case_activity_timing(case)
    assert case["broker_first_opened_at"]
    assert case["formal_submitted_at"] == "2026-08-03T12:00:00Z"
    assert isinstance(case.get("case_activity_timing"), dict)


def test_export_fetch_header_contract_documented():
    """Exporter must send X-Case-Activity-Record: 0 (see tools/export_case_value_metrics)."""
    from pathlib import Path

    src = Path("tools/export_case_value_metrics.py").read_text(encoding="utf-8")
    assert 'X-Case-Activity-Record": "0"' in src or "X-Case-Activity-Record': '0'" in src
