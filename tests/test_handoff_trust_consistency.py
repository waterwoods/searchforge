"""Trust fixes: structural handoff vs still_needed; vehicle text vs primary_vehicle_summary; PG posture helper."""

from __future__ import annotations

import pytest

from services.fiqa_api.db import service_record_settings as srs
from services.fiqa_api.inbox_triage.triage_handoff_reply_composer import (
    apply_handoff_trust_fixes_to_result,
    enforce_add_car_handoff_structural_consistency,
)
from services.fiqa_api.inbox_triage.triage import triage_conversation


def test_enforce_handoff_downgrades_when_structural_still_needed() -> None:
    r: dict = {
        "service_type": "add_car",
        "handoff_ready": True,
        "lifecycle_status": "handoff_pending",
        "still_needed_fields": ["zip"],
        "collected_fields": ["vin"],
        "intake_next_best_ask": "请提供邮编。",
        "client_reply_draft": "Your quote details are ready ✅ please wait",
        "triage_mode": "greenfield",
    }
    enforce_add_car_handoff_structural_consistency(r)
    assert r.get("handoff_ready") is False
    assert "ready" not in (r.get("client_reply_draft") or "").lower()
    assert "quote details" not in (r.get("client_reply_draft") or "").lower()


def test_enforce_preserves_handoff_for_contact_only_gap() -> None:
    r: dict = {
        "service_type": "add_car",
        "handoff_ready": True,
        "lifecycle_status": "handoff_pending",
        "still_needed_fields": ["name", "phone"],
        "collected_fields": ["vin", "zip"],
        "intake_next_best_ask": "",
        "client_reply_draft": "Your quote details are ready ✅",
        "triage_mode": "greenfield",
        "conversation_summary": "x",
        "next_best_question": "",
    }
    enforce_add_car_handoff_structural_consistency(r)
    assert r.get("handoff_ready") is True


def test_vehicle_drift_replaced_in_draft() -> None:
    r: dict = {
        "service_type": "add_car",
        "primary_vehicle_summary": "2024 Honda Accord",
        "client_reply_draft": "Noted—we'll proceed with the 2024 Toyota Camry. Send zip.",
    }
    apply_handoff_trust_fixes_to_result(r)
    d = (r.get("client_reply_draft") or "").lower()
    assert "honda" in d and "accord" in d
    assert "toyota" not in d and "camry" not in d


def test_triage_correction_reply_matches_authoritative_vehicle() -> None:
    prior = [{"role": "customer", "text": "add car 2024 Toyota Camry zip 90210"}]
    latest = "not Toyota, it's Honda Accord"
    r = triage_conversation(latest, prior, client_id="chen_kui")
    assert r.get("primary_vehicle_summary") and "Honda" in (r.get("primary_vehicle_summary") or "")
    draft = (r.get("client_reply_draft") or "").lower()
    assert "toyota" not in draft and "camry" not in draft


@pytest.mark.parametrize(
    "env,expect_mode",
    [
        (
            {
                "ENV": "prod",
                "SERVICE_RECORD_DATABASE_URL": "postgresql://x/y",
                "UNIFIED_INTAKE_DB_PRIMARY_WRITES": "1",
            },
            "STRICT_PG_ONLY",
        ),
        (
            {
                "SERVICE_RECORD_DATABASE_URL": "postgresql://x/y",
                "UNIFIED_INTAKE_PG_DUAL_WRITE": "1",
                "UNIFIED_INTAKE_DB_PRIMARY_WRITES": "0",
            },
            "PG_FIRST_BUT_NOT_STRICT",
        ),
    ],
)
def test_unified_intake_persistence_report_modes(
    monkeypatch: pytest.MonkeyPatch, env: dict[str, str], expect_mode: str
) -> None:
    for k in (
        "ENV",
        "SERVICE_RECORD_DATABASE_URL",
        "DATABASE_URL",
        "UNIFIED_INTAKE_DB_PRIMARY_WRITES",
        "UNIFIED_INTAKE_DB_PRIMARY_READS",
        "UNIFIED_INTAKE_JSON_CASE_WRITES",
        "UNIFIED_INTAKE_PG_DUAL_WRITE",
    ):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    rep = srs.unified_intake_case_persistence_report()
    assert rep.get("unified_intake_case_persistence_mode") == expect_mode
