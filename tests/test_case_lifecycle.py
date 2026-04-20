"""Minimal validation for derived case_lifecycle (additive API field)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from services.fiqa_api.inbox_triage.case_lifecycle import _derive_case_lifecycle
from services.fiqa_api.inbox_triage.triage import triage_conversation
from services.fiqa_api.routes.inbox_triage import _attach_case_lifecycle


def test_derive_submitted_first():
    assert (
        _derive_case_lifecycle(
            {
                "formal_submitted_at": "2026-04-01T00:00:00Z",
                "triage_mode": "greenfield",
                "handoff_ready": True,
                "quote_ready_status": "almost_ready",
            }
        )
        == "submitted"
    )


def test_derive_ready_for_handoff_greenfield_only():
    assert (
        _derive_case_lifecycle(
            {
                "triage_mode": "greenfield",
                "handoff_ready": True,
                "quote_ready_status": "quote_ready",
            }
        )
        == "ready_for_handoff"
    )


def test_derive_handoff_requires_identity_true_not_truthy():
    assert (
        _derive_case_lifecycle(
            {
                "triage_mode": "greenfield",
                "handoff_ready": True,
            }
        )
        == "ready_for_handoff"
    )
    assert (
        _derive_case_lifecycle(
            {
                "triage_mode": "greenfield",
                "handoff_ready": 1,
            }
        )
        == "collecting"
    )


def test_derive_append_handoff_does_not_skip_to_ready_for_handoff():
    assert (
        _derive_case_lifecycle(
            {
                "triage_mode": "append",
                "handoff_ready": True,
                "quote_ready_status": "quote_ready",
            }
        )
        == "collecting"
    )


def test_derive_almost_ready():
    assert _derive_case_lifecycle({"triage_mode": "greenfield", "quote_ready_status": "almost_ready"}) == "almost_ready"


def test_derive_default_collecting():
    assert _derive_case_lifecycle({"triage_mode": "greenfield", "quote_ready_status": "need_more"}) == "collecting"


def test_attach_overlays_formal_submitted_from_persisted_case():
    result = {
        "triage_mode": "greenfield",
        "handoff_ready": False,
        "quote_ready_status": "quote_ready",
    }
    persisted = {"formal_submitted_at": "2026-01-02T00:00:00Z"}
    _attach_case_lifecycle(result, persisted_case=persisted)
    assert result["case_lifecycle"] == "submitted"


def test_triage_flow_collecting_matches_route_derivation():
    r = triage_conversation("I want to add a car", [], client_id="chen_kui")
    _attach_case_lifecycle(r)
    assert r.get("case_lifecycle") == "collecting"


def test_triage_flow_almost_ready():
    r = triage_conversation("VIN is 1HGBH41JXMN109186, my zip is 94043", [], client_id="chen_kui")
    _attach_case_lifecycle(r)
    assert r.get("case_lifecycle") == "almost_ready"


def test_triage_flow_ready_for_handoff():
    # Turn 1 is confirm-first for add-car V4/V5; turn 2 may hand off when quote-ready.
    turns = [{"role": "customer", "text": "I want to add a car"}]
    msg = (
        "VIN 1HGBH41JXMN109186 zip 94043 delivery 2026-05-01 primary driver self "
        "2020 Honda Civic name Andy Chen phone 650-555-0100"
    )
    r = triage_conversation(msg, turns, client_id="chen_kui")
    _attach_case_lifecycle(r)
    assert r.get("handoff_ready") is True
    assert r.get("case_lifecycle") == "ready_for_handoff"


def test_short_ack_with_reply_context_has_lifecycle_via_attach_overlay():
    ctx = {
        "formal_submitted_at": "2026-01-01T00:00:00Z",
        "persisted_collected_fields": ["vin", "zip"],
    }
    tr = triage_conversation(
        "ok",
        [{"role": "customer", "text": "VIN 1HGBH41JXMN109186 zip 94043"}],
        client_id="chen_kui",
        reply_truth_context=ctx,
    )
    # Intake engine may attach derived case_lifecycle; route overlay still authoritative with persisted_case.
    fake_case = {"formal_submitted_at": ctx["formal_submitted_at"]}
    _attach_case_lifecycle(tr, persisted_case=fake_case)
    assert tr["case_lifecycle"] == "submitted"


def test_append_semantics_submitted_when_formal_timestamp_present():
    updated = {
        "formal_submitted_at": "2026-03-01T12:00:00Z",
        "triage_mode": "append",
        "handoff_ready": True,
        "quote_ready_status": "quote_ready",
    }
    assert _derive_case_lifecycle(updated) == "submitted"
