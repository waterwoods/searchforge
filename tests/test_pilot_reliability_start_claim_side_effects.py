"""Pilot Reliability Fix 2 — Start Claim side-effect visibility + atomic story confirm.

Start Claim: CreateClaim stays durable and idempotent while a failed post-create
enrichment is reported instead of swallowed.
Accident Story confirm: confirmed facts and their provenance / layer metadata are
written as one case update, so no crash can leave half-confirmed truth.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from services.fiqa_api.inbox_triage import case_store as cs
from services.fiqa_api.inbox_triage.accident_story_assistant.service import (
    confirm_accident_story,
    propose_accident_story,
    reset_accident_story_idempotency_for_tests,
)
from services.fiqa_api.inbox_triage.case_store import get_case_by_id, save_case
from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.inbox_triage.p20_customer_start_claim import (
    SIDE_EFFECT_STATUS_CONFIRMED,
    SIDE_EFFECT_STATUS_FAILED,
    WARNING_ACCIDENT_STORY_UNCONFIRMED,
    WARNING_POLICY_CONTEXT_UNCONFIRMED,
    customer_start_claim_response,
    start_customer_claim,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    SERVICE_LANE_CLAIM,
)

STORY_CONFIRMED_EVENT = "customer_accident_story_confirmed"
SIDE_EFFECT_EVENT = "start_claim_side_effect_failed"


@pytest.fixture(autouse=True)
def _json_store(monkeypatch):
    """Local JSON case store, isolated from ambient persistence env."""
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(path))
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "1")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_accident_story_idempotency_for_tests()
    yield


# --- Problem A: Start Claim side-effect visibility ---------------------------


@pytest.fixture()
def intake_store(monkeypatch) -> InMemoryIntakeStore:
    store = InMemoryIntakeStore()
    svc = P20CaseIntakeCommandService(store)
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.default_case_intake_service",
        lambda: svc,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_server_client_id",
        lambda: "tenant_fix2",
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_customer_start_claim_office_id",
        lambda: "office_fix2",
    )
    return store


def _start(session_id: str, suffix: str, **kwargs: Any) -> dict[str, Any]:
    return start_customer_claim(
        command_id=f"cmd-fix2-{suffix}",
        idempotency_key=f"idem-fix2-{suffix}",
        session_id=session_id,
        accident_description="等红灯被追尾，右后保险杠受损",
        accident_datetime="2026-08-09 10:00",
        accident_location="Irvine Blvd",
        injury_status="no",
        is_test=True,
        **kwargs,
    )


def test_start_claim_durable_when_policy_context_side_effect_raises(
    intake_store: InMemoryIntakeStore, caplog
):
    def _boom(*_a: Any, **_k: Any) -> dict[str, Any]:
        raise RuntimeError("policy_context_store_down")

    from services.fiqa_api.inbox_triage import policy_context_confirm

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(policy_context_confirm, "confirm_policy_context_for_case", _boom)
        with caplog.at_level("WARNING"):
            result = _start("anon-fix2-policy", "policy-1", policy_context_choice="correct")

    # Authoritative claim survived the enrichment failure.
    assert result["outcome"] == "accepted"
    case_id = result["case_id"]
    assert case_id in intake_store.cases
    assert len(intake_store.cases) == 1

    # Failure is neither silent nor mislabelled as confirmed.
    assert result["side_effects"]["policy_context"] == SIDE_EFFECT_STATUS_FAILED
    assert WARNING_POLICY_CONTEXT_UNCONFIRMED in result["side_effect_warnings"]
    assert (result.get("case", {}) or {}).get("policy_context") is None
    assert "policy_context side effect failed" in caplog.text

    # Customer keeps a usable continuation path (resume token + honest warning).
    body = customer_start_claim_response(result)
    assert body["ok"] is True
    assert body["resume_token"]
    assert body["degraded"] is True
    assert WARNING_POLICY_CONTEXT_UNCONFIRMED in body["warnings"]


def test_start_claim_reports_policy_context_rejected_outcome_without_exception(
    intake_store: InMemoryIntakeStore,
):
    """OLD behavior: a rejected confirm returned a dict and was dropped entirely."""
    from services.fiqa_api.inbox_triage import policy_context_confirm

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            policy_context_confirm,
            "confirm_policy_context_for_case",
            lambda *_a, **_k: {"outcome": "persist_failed", "case": None},
        )
        result = _start("anon-fix2-policy-rej", "policy-2", policy_context_choice="correct")

    assert result["outcome"] == "accepted"
    assert result["side_effects"]["policy_context"] == SIDE_EFFECT_STATUS_FAILED
    assert WARNING_POLICY_CONTEXT_UNCONFIRMED in result["side_effect_warnings"]


def test_start_claim_no_duplicate_claim_on_retry_after_side_effect_failure(
    intake_store: InMemoryIntakeStore,
):
    from services.fiqa_api.inbox_triage import policy_context_confirm

    def _boom(*_a: Any, **_k: Any) -> dict[str, Any]:
        raise RuntimeError("policy_context_store_down")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(policy_context_confirm, "confirm_policy_context_for_case", _boom)
        first = _start("anon-fix2-retry", "retry-1", policy_context_choice="correct")
        second = _start("anon-fix2-retry", "retry-1", policy_context_choice="correct")

    assert first["outcome"] == "accepted"
    assert second["outcome"] in ("replayed", "resumed")
    assert len(intake_store.cases) == 1
    if second.get("case_id"):
        assert second["case_id"] == first["case_id"]


def test_start_claim_durable_when_accident_story_confirm_raises(
    intake_store: InMemoryIntakeStore, caplog
):
    from services.fiqa_api.inbox_triage import accident_story_assistant

    def _boom(**_k: Any) -> dict[str, Any]:
        raise RuntimeError("story_persist_down")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(accident_story_assistant, "confirm_accident_story", _boom)
        with caplog.at_level("WARNING"):
            result = _start("anon-fix2-story", "story-1", ai_story_confirmed=True)

    assert result["outcome"] == "accepted"
    case_id = result["case_id"]
    assert case_id in intake_store.cases
    assert len(intake_store.cases) == 1

    assert result["side_effects"]["accident_story"] == SIDE_EFFECT_STATUS_FAILED
    assert WARNING_ACCIDENT_STORY_UNCONFIRMED in result["side_effect_warnings"]
    assert "accident_story side effect failed" in caplog.text

    # No false authoritative story state anywhere.
    persisted = get_case_by_id(case_id)
    assert (persisted or {}).get("accident_story_assistant") in (None, {})

    body = customer_start_claim_response(result)
    assert body["ok"] is True
    assert body["degraded"] is True
    assert WARNING_ACCIDENT_STORY_UNCONFIRMED in body["warnings"]


def test_start_claim_reports_story_confirm_rejection_without_exception(
    intake_store: InMemoryIntakeStore,
):
    """A rejected confirm must never read as customer_confirmed truth."""
    from services.fiqa_api.inbox_triage import accident_story_assistant

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            accident_story_assistant,
            "confirm_accident_story",
            lambda **_k: {
                "ok": False,
                "outcome": "rejected",
                "error_code": "persist_failed",
            },
        )
        result = _start("anon-fix2-story-rej", "story-2", ai_story_confirmed=True)

    assert result["outcome"] == "accepted"
    assert result["side_effects"]["accident_story"] == SIDE_EFFECT_STATUS_FAILED
    assert WARNING_ACCIDENT_STORY_UNCONFIRMED in result["side_effect_warnings"]


def test_start_claim_clean_run_has_no_warnings(intake_store: InMemoryIntakeStore):
    from services.fiqa_api.inbox_triage import accident_story_assistant

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            accident_story_assistant,
            "confirm_accident_story",
            lambda **_k: {
                "ok": True,
                "outcome": "accepted",
                "persisted": True,
                "authority": "customer_confirmed",
            },
        )
        result = _start("anon-fix2-clean", "clean-1", ai_story_confirmed=True)

    assert result["outcome"] == "accepted"
    assert result["side_effects"]["accident_story"] == SIDE_EFFECT_STATUS_CONFIRMED
    assert not result.get("side_effect_warnings")
    body = customer_start_claim_response(result)
    assert "warnings" not in body
    assert "degraded" not in body


def test_start_claim_side_effect_failure_leaves_support_signal_on_case(
    intake_store: InMemoryIntakeStore,
):
    """Durable, idempotent support signal on a case the office can actually see."""
    from services.fiqa_api.inbox_triage import policy_context_confirm

    case = _claim_case()
    cid = case["case_id"]

    def _boom(*_a: Any, **_k: Any) -> dict[str, Any]:
        raise RuntimeError("policy_context_store_down")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(policy_context_confirm, "confirm_policy_context_for_case", _boom)
        # Case already exists in the case store: Cap2 replays onto the same id.
        mp.setattr(
            "services.fiqa_api.inbox_triage.p20_customer_start_claim.default_case_intake_service",
            lambda: _FixedCaseIntakeService(cid),
        )
        first = _start("anon-fix2-signal", "signal-1", policy_context_choice="correct")
        second = _start("anon-fix2-signal", "signal-1", policy_context_choice="correct")

    assert first["side_effects"]["policy_context"] == SIDE_EFFECT_STATUS_FAILED
    assert second["outcome"] in ("accepted", "replayed", "resumed")
    persisted = get_case_by_id(cid)
    signals = [
        e
        for e in (persisted or {}).get("claim_timeline") or []
        if e.get("event_type") == SIDE_EFFECT_EVENT
    ]
    assert len(signals) == 1
    assert signals[0]["actor"] == "system"
    assert WARNING_POLICY_CONTEXT_UNCONFIRMED in signals[0]["metadata"]["warnings"]


class _FixedCaseIntakeService:
    """Cap2 stub that returns one existing case_id (create is not under test here)."""

    def __init__(self, case_id: str) -> None:
        self.case_id = case_id
        self.calls = 0

    def create_claim(self, **_kwargs: Any) -> dict[str, Any]:
        self.calls += 1
        return {
            "outcome": "accepted" if self.calls == 1 else "replayed",
            "case_id": self.case_id,
            "error_code": None,
        }


# --- Problem B: Accident Story confirm atomicity ----------------------------


def _claim_case(**extra: Any) -> dict[str, Any]:
    stub = {
        "issue_category": "claim_intake",
        "urgency": "medium",
        "broker_next_step": "Claim guided workflow",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "manual_followup_needed": False,
        "collected_fields": [],
        "still_needed_fields": [],
        "known_facts": {},
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        "guided_workflow_state": "collecting_text",
        "entry_channel": "mini_program",
        "created_by_actor": "customer",
        "person_link_key": "plk_fix2_qa",
    }
    stub.update(extra)
    return save_case("[客户] fix2 accident story", stub, service_lane=SERVICE_LANE_CLAIM)


def _confirm(case_id: str, suffix: str, **kwargs: Any) -> dict[str, Any]:
    proposed = propose_accident_story(
        raw_story="昨天下午3点在 San Jose 停车场被追尾，没有受伤。",
        command_id=f"cmd-fix2-propose-{suffix}",
        idempotency_key=f"idem-fix2-propose-{suffix}",
        case_id=case_id,
    )
    payload = dict(
        case_id=case_id,
        command_id=f"cmd-fix2-confirm-{suffix}",
        idempotency_key=f"idem-fix2-confirm-{suffix}",
        raw_story="昨天下午3点在 San Jose 停车场被追尾，没有受伤。",
        confirm=True,
        proposal_id=proposed["proposal_id"],
        customer_edits={"accident_location_text": "San Jose 停车场", "injury_status": "no"},
    )
    payload.update(kwargs)
    return confirm_accident_story(**payload)


def _story_events(case: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [
        e
        for e in (case or {}).get("claim_timeline") or []
        if e.get("event_type") == STORY_CONFIRMED_EVENT
    ]


def test_confirm_persists_facts_provenance_and_layers_together():
    case = _claim_case()
    cid = case["case_id"]

    result = _confirm(cid, "together")

    assert result["ok"] is True
    assert result["persisted"] is True
    assert result["authority"] == "customer_confirmed"

    persisted = get_case_by_id(cid)
    assert persisted is not None
    facts = persisted.get("known_facts") or {}
    assert facts["accident_location"] == "San Jose 停车场"
    assert facts["injury_status"] == "no"

    provenance = persisted.get("known_fact_provenance") or {}
    for field in result["confirmed_fields"]:
        assert provenance[field]["authority"] == "customer_confirmed"
        # Provenance not weakened: the fact source survives alongside authority.
        assert provenance[field]["source"] == "customer_confirmed"

    assistant = persisted.get("accident_story_assistant") or {}
    assert assistant["authority"] == "customer_confirmed"
    assert assistant["layers"]["ai_draft"]["authority"] == "ai_proposed"
    assert assistant["layers"]["customer_confirmed"]["authority"] == "customer_confirmed"
    assert len(_story_events(persisted)) == 1


def test_confirm_persist_failure_leaves_no_half_confirmed_state():
    case = _claim_case(known_facts={"accident_description": "原始描述"})
    cid = case["case_id"]

    def _boom(_case_id: str, _case: dict[str, Any]) -> bool:
        raise RuntimeError("case_store_write_down")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(cs, "_persist_case_after_update", _boom)
        result = _confirm(cid, "persist-crash")

    assert result["ok"] is False
    assert result["error_code"] == "persist_failed"

    persisted = get_case_by_id(cid)
    assert persisted is not None
    # Neither side of the old split write landed.
    assert (persisted.get("known_facts") or {}).get("accident_description") == "原始描述"
    assert (persisted.get("known_facts") or {}).get("accident_location") is None
    assert persisted.get("accident_story_assistant") in (None, {})
    assert (persisted.get("known_fact_provenance") or {}) == {}
    assert _story_events(persisted) == []


def test_confirm_provenance_failure_cannot_orphan_confirmed_facts():
    """The old code stamped facts first, then provenance under `except: pass`."""
    case = _claim_case()
    cid = case["case_id"]
    real_apply = cs._apply_claim_timeline_event_to_case

    def _boom(case_dict: dict[str, Any], event: dict[str, Any]) -> bool:
        if str(event.get("event_type") or "") == STORY_CONFIRMED_EVENT:
            raise RuntimeError("provenance_stage_down")
        return real_apply(case_dict, event)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(cs, "_apply_claim_timeline_event_to_case", _boom)
        result = _confirm(cid, "prov-crash")

    assert result["ok"] is False
    assert result["error_code"] == "persist_failed"

    persisted = get_case_by_id(cid)
    assert ((persisted or {}).get("known_facts") or {}) == {}
    assert (persisted or {}).get("accident_story_assistant") in (None, {})


def test_confirm_missing_case_is_rejected_not_silently_dropped():
    result = _confirm("case_does_not_exist_fix2", "missing")
    assert result["ok"] is False
    assert result["error_code"] == "case_not_found"


def test_confirm_retry_same_idempotency_key_is_exactly_once():
    case = _claim_case()
    cid = case["case_id"]
    writes = {"n": 0}
    real_persist = cs._persist_case_after_update

    def _counting(case_id: str, updated: dict[str, Any]) -> bool:
        writes["n"] += 1
        return real_persist(case_id, updated)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(cs, "_persist_case_after_update", _counting)
        first = _confirm(cid, "replay")
        second = _confirm(cid, "replay")

    assert first["outcome"] == "accepted"
    assert second["outcome"] == "replayed"
    assert second["authority"] == "customer_confirmed"
    # One business effect: one persist, one timeline event.
    assert writes["n"] == 1
    persisted = get_case_by_id(cid)
    assert len(_story_events(persisted)) == 1


def test_confirm_rejected_proposal_never_writes_authoritative_story():
    case = _claim_case()
    cid = case["case_id"]

    result = confirm_accident_story(
        case_id=cid,
        command_id="cmd-fix2-unconfirmed-1",
        idempotency_key="idem-fix2-unconfirmed-1",
        raw_story="昨天被追尾。",
        confirm=False,
    )
    assert result["ok"] is True
    assert result["persisted"] is False
    assert result["authority"] == "ai_proposed"

    persisted = get_case_by_id(cid)
    assert (persisted or {}).get("accident_story_assistant") in (None, {})
    assert ((persisted or {}).get("known_facts") or {}) == {}


def test_confirm_db_primary_path_mutates_case_under_lock(monkeypatch):
    """PG-primary pilot path: one locked read → one mutation → one commit."""
    order: list[str] = []
    locked_case = {
        "case_id": "case_fix2_pg",
        "service_lane": SERVICE_LANE_CLAIM,
        "known_facts": {"contact_note": "keep"},
        "known_fact_provenance": {},
        "claim_timeline": [],
        "customer_name": "FromLockedRead",
    }

    def _fake_mutate(case_id: str, mutator):
        order.append("lock_and_load")
        assert case_id == "case_fix2_pg"
        result, should_persist = mutator(locked_case)
        assert should_persist is True
        # Facts, provenance, layers, and timeline are all present before commit.
        assert locked_case["known_facts"]["accident_location"] == "San Jose 停车场"
        assert (
            locked_case["known_fact_provenance"]["accident_location"]["authority"]
            == "customer_confirmed"
        )
        assert locked_case["accident_story_assistant"]["authority"] == "customer_confirmed"
        assert len(_story_events(locked_case)) == 1
        assert locked_case["customer_name"] == "FromLockedRead"
        order.append("persist_under_same_txn")
        return result

    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.db_primary_writes_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.json_case_writes_enabled",
        lambda: False,
    )
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.mutate_full_case_under_lock",
        _fake_mutate,
    )

    result = _confirm("case_fix2_pg", "pg-path")

    assert order == ["lock_and_load", "persist_under_same_txn"]
    assert result["ok"] is True
    assert result["authority"] == "customer_confirmed"
