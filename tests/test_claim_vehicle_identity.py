"""Claim Vehicle Identity V1 (T2) — backend object, merge, idempotency, facts."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import get_case_by_id, save_case
from services.fiqa_api.inbox_triage.claim_vehicle_identity import (
    FACT_KEY_LICENSE_PLATE,
    FACT_KEY_MAKE,
    FACT_KEY_MODEL,
    FACT_KEY_PLATE_STATE,
    FACT_KEY_SUMMARY,
    FACT_KEY_VEHICLE_ID,
    FACT_KEY_VERIFICATION,
    FACT_KEY_VIN,
    FACT_KEY_VIN_UNAVAILABLE,
    FACT_KEY_YEAR,
    SOURCE_AI_EXTRACT,
    SOURCE_CUSTOMER,
    VERIFICATION_CONFIRMED,
    VERIFICATION_NEEDS_CORRECTION,
    VERIFICATION_SUPPLIED_UNCONFIRMED,
    ClaimVehicleIdentityService,
    build_vehicle_summary,
    claim_vehicle_to_known_facts_patch,
    is_claim_vehicle_complete,
    merge_claim_vehicle,
    normalize_claim_vehicle_input,
    read_claim_vehicle_from_facts,
    vehicle_id_for_case,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

VALID_VIN = "1HGCM82633A004352"


@pytest.fixture
def svc() -> ClaimVehicleIdentityService:
    return ClaimVehicleIdentityService()


@pytest.fixture
def case_storage(monkeypatch, tmp_path: Path):
    path = tmp_path / "cases.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(path))
    yield path


def _claim_case() -> str:
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
    return str(case["case_id"])


# ---------------------------------------------------------------------------
# Normalization / completeness
# ---------------------------------------------------------------------------


def test_valid_vin_normalizes_and_is_complete():
    vehicle = normalize_claim_vehicle_input(
        {"vin": " 1hgcm82633a004352 "},
        case_id="case_a",
    )
    assert vehicle.vin == VALID_VIN
    assert vehicle.vin_unavailable is False
    assert vehicle.vehicle_id == "veh:case_a"
    assert is_claim_vehicle_complete(vehicle) is True


def test_partial_vin_never_persisted_as_canonical():
    vehicle = normalize_claim_vehicle_input({"vin": "1HGCM82633A00435"}, case_id="case_a")
    assert vehicle.vin is None
    patch = claim_vehicle_to_known_facts_patch(vehicle)
    assert FACT_KEY_VIN not in patch
    assert "vin" not in patch


def test_vin_unavailable_path_b_complete():
    vehicle = normalize_claim_vehicle_input(
        {
            "vin_unavailable": True,
            "year": "2020",
            "make": "Toyota",
            "model": "Camry",
        },
        case_id="case_b",
    )
    assert vehicle.vin is None
    assert vehicle.vin_unavailable is True
    assert is_claim_vehicle_complete(vehicle) is True
    assert build_vehicle_summary(vehicle) == "2020 Toyota Camry"


def test_partial_save_incomplete_until_path_a_or_b():
    vehicle = normalize_claim_vehicle_input(
        {"year": "2020", "make": "Toyota"},
        case_id="case_p",
    )
    assert is_claim_vehicle_complete(vehicle) is False
    patch = claim_vehicle_to_known_facts_patch(vehicle)
    assert patch[FACT_KEY_YEAR] == "2020"
    assert patch[FACT_KEY_MAKE] == "Toyota"
    assert FACT_KEY_MODEL not in patch


# ---------------------------------------------------------------------------
# Resume / fact mapping / backward compatibility
# ---------------------------------------------------------------------------


def test_resume_from_known_facts_aliases():
    facts = {
        "own_vehicle_info": "2019 Honda Civic",
        "vin": VALID_VIN,
        "vehicle_year": "2019",
        "vehicle_make": "Honda",
        "vehicle_model": "Civic",
    }
    vehicle = read_claim_vehicle_from_facts(facts, case_id="case_r")
    assert vehicle is not None
    assert vehicle.vin == VALID_VIN
    assert vehicle.year == "2019"
    assert vehicle.make == "Honda"
    assert vehicle.model == "Civic"
    # Legacy summary alias still readable; structured fields win for summary rebuild.
    assert "Honda" in (vehicle.summary or "")


def test_known_facts_patch_writes_canonical_and_aliases():
    vehicle = normalize_claim_vehicle_input(
        {
            "vin": VALID_VIN,
            "year": "2020",
            "make": "Toyota",
            "model": "Camry",
            "license_plate": "8abc123",
            "plate_state": "ca",
        },
        case_id="case_m",
    )
    patch = claim_vehicle_to_known_facts_patch(vehicle)
    assert patch[FACT_KEY_VIN] == VALID_VIN
    assert patch["vin"] == VALID_VIN
    assert patch["own_vehicle_vin"] == VALID_VIN
    assert patch[FACT_KEY_SUMMARY] == "2020 Toyota Camry"
    assert patch["own_vehicle_info"] == "2020 Toyota Camry"
    assert patch["primary_vehicle_summary"] == "2020 Toyota Camry"
    assert patch[FACT_KEY_LICENSE_PLATE] == "8ABC123"
    assert patch[FACT_KEY_PLATE_STATE] == "CA"
    assert patch[FACT_KEY_VEHICLE_ID] == "veh:case_m"
    assert patch[FACT_KEY_VIN_UNAVAILABLE] == "false"


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------


def test_merge_prefers_single_slot_and_vin_match(svc: ClaimVehicleIdentityService):
    case: dict = {"case_id": "case_merge", "known_facts": {}}
    first = svc.upsert(
        case_id="case_merge",
        payload={"year": "2020", "make": "Toyota", "model": "Camry", "vin_unavailable": True},
        command_id="cmd-1",
        idempotency_key="idem-1",
        mode="submit",
        case=case,
    )
    assert first.outcome == "accepted"
    assert first.merge and first.merge["created"] is True
    assert first.vehicle and first.vehicle["vehicle_id"] == "veh:case_merge"

    second = svc.upsert(
        case_id="case_merge",
        payload={"vin": VALID_VIN},
        command_id="cmd-2",
        idempotency_key="idem-2",
        mode="submit",
        case=case,
        known_facts=case["known_facts"],
    )
    assert second.outcome == "accepted"
    assert second.merge and second.merge["created"] is False
    assert second.vehicle and second.vehicle["vehicle_id"] == "veh:case_merge"
    assert second.vehicle["vin"] == VALID_VIN
    # Still exactly one slot id in facts.
    assert case["known_facts"][FACT_KEY_VEHICLE_ID] == "veh:case_merge"


def test_merge_by_plate_and_state(svc: ClaimVehicleIdentityService):
    case: dict = {"case_id": "case_plate", "known_facts": {}}
    svc.upsert(
        case_id="case_plate",
        payload={
            "vin_unavailable": True,
            "year": "2018",
            "make": "Honda",
            "model": "Accord",
            "license_plate": "7xyz999",
            "plate_state": "CA",
        },
        command_id="cmd-p1",
        idempotency_key="idem-p1",
        mode="submit",
        case=case,
    )
    result = svc.upsert(
        case_id="case_plate",
        payload={"license_plate": "7XYZ999", "plate_state": "ca", "year": "2019"},
        command_id="cmd-p2",
        idempotency_key="idem-p2",
        mode="draft",
        case=case,
        known_facts=case["known_facts"],
    )
    assert result.merge and result.merge["matched_by"] in {"plate_and_state", "existing_slot"}
    assert result.vehicle and result.vehicle["year"] == "2019"
    assert result.vehicle["vehicle_id"] == "veh:case_plate"


def test_correction_updates_unconfirmed_same_slot(svc: ClaimVehicleIdentityService):
    case: dict = {"case_id": "case_corr", "known_facts": {}}
    svc.upsert(
        case_id="case_corr",
        payload={"vin_unavailable": True, "year": "2020", "make": "Toyota", "model": "Camry"},
        command_id="cmd-c1",
        idempotency_key="idem-c1",
        mode="submit",
        case=case,
    )
    corrected = svc.upsert(
        case_id="case_corr",
        payload={"vin_unavailable": True, "year": "2021", "make": "Toyota", "model": "Camry"},
        command_id="cmd-c2",
        idempotency_key="idem-c2",
        mode="submit",
        case=case,
        known_facts=case["known_facts"],
    )
    assert corrected.outcome == "accepted"
    assert corrected.vehicle and corrected.vehicle["year"] == "2021"
    assert corrected.vehicle["verification_status"] == VERIFICATION_SUPPLIED_UNCONFIRMED
    assert case["known_facts"][FACT_KEY_YEAR] == "2021"
    assert case["known_facts"]["own_vehicle_info"] == "2021 Toyota Camry"


def test_broker_confirmed_not_silently_overwritten():
    existing = normalize_claim_vehicle_input(
        {"vin": VALID_VIN, "year": "2020", "make": "Toyota", "model": "Camry"},
        case_id="case_conf",
        verification_status=VERIFICATION_CONFIRMED,
    )
    incoming = normalize_claim_vehicle_input(
        {"vin": "2HGES16575H580032", "year": "2019", "make": "Honda", "model": "Civic"},
        case_id="case_conf",
        source=SOURCE_CUSTOMER,
    )
    merged = merge_claim_vehicle(existing, incoming)
    assert merged.vehicle.vin == VALID_VIN
    assert merged.vehicle.year == "2020"
    assert merged.vehicle.make == "Toyota"
    assert "vin" in merged.conflict_fields
    assert merged.vehicle.verification_status == VERIFICATION_NEEDS_CORRECTION


def test_ai_extract_never_overrides_confirmed():
    existing = normalize_claim_vehicle_input(
        {"vin_unavailable": True, "year": "2020", "make": "Toyota", "model": "Camry"},
        case_id="case_ai",
        verification_status=VERIFICATION_CONFIRMED,
    )
    incoming = normalize_claim_vehicle_input(
        {"year": "2018", "make": "Ford", "model": "Focus"},
        case_id="case_ai",
        source=SOURCE_AI_EXTRACT,
    )
    merged = merge_claim_vehicle(existing, incoming)
    assert merged.vehicle.year == "2020"
    assert merged.vehicle.make == "Toyota"
    assert merged.conflict_fields
    assert merged.vehicle.verification_status == VERIFICATION_NEEDS_CORRECTION


# ---------------------------------------------------------------------------
# Idempotency / duplicate submit
# ---------------------------------------------------------------------------


def test_duplicate_submit_replays_without_second_vehicle_or_events(svc: ClaimVehicleIdentityService):
    case: dict = {"case_id": "case_idem", "known_facts": {}}
    first = svc.upsert(
        case_id="case_idem",
        payload={"vin": VALID_VIN},
        command_id="cmd-idem",
        idempotency_key="idem-idem",
        mode="submit",
        case=case,
    )
    assert first.outcome == "accepted"
    assert len(first.events) == 1
    event_ids = list(first.event_ids)

    second = svc.upsert(
        case_id="case_idem",
        payload={"vin": VALID_VIN},
        command_id="cmd-idem",
        idempotency_key="idem-idem",
        mode="submit",
        case=case,
        known_facts=case["known_facts"],
    )
    assert second.outcome == "replayed"
    assert second.original_outcome == "accepted"
    assert second.event_ids == event_ids
    assert second.vehicle and second.vehicle["vehicle_id"] == "veh:case_idem"
    # Facts still single-slot; no second vehicle id invented.
    assert case["known_facts"][FACT_KEY_VEHICLE_ID] == "veh:case_idem"


def test_partial_save_then_resume_then_complete(svc: ClaimVehicleIdentityService):
    case: dict = {"case_id": "case_resume", "known_facts": {}}
    draft = svc.upsert(
        case_id="case_resume",
        payload={"year": "2020", "make": "Toyota"},
        command_id="cmd-d1",
        idempotency_key="idem-d1",
        mode="draft",
        case=case,
    )
    assert draft.outcome == "accepted"
    assert draft.complete is False

    resumed = read_claim_vehicle_from_facts(case["known_facts"], case_id="case_resume")
    assert resumed is not None
    assert resumed.year == "2020"
    assert resumed.make == "Toyota"

    final = svc.upsert(
        case_id="case_resume",
        payload={"vin_unavailable": True, "year": "2020", "make": "Toyota", "model": "Camry"},
        command_id="cmd-d2",
        idempotency_key="idem-d2",
        mode="submit",
        case=case,
        known_facts=case["known_facts"],
    )
    assert final.outcome == "accepted"
    assert final.complete is True
    assert final.vehicle and final.vehicle["vehicle_id"] == vehicle_id_for_case("case_resume")
    assert case["known_facts"][FACT_KEY_MODEL] == "Camry"
    assert case["known_facts"][FACT_KEY_VIN_UNAVAILABLE] == "true"


def test_submit_rejects_incomplete(svc: ClaimVehicleIdentityService):
    result = svc.upsert(
        case_id="case_rej",
        payload={"year": "2020", "make": "Toyota"},
        command_id="cmd-rej",
        idempotency_key="idem-rej",
        mode="submit",
    )
    assert result.outcome == "rejected"
    assert result.error_code == "vehicle_incomplete"


def test_submit_rejects_invalid_vin_without_path_b(svc: ClaimVehicleIdentityService):
    result = svc.upsert(
        case_id="case_badvin",
        payload={"vin": "SHORTVIN"},
        command_id="cmd-badvin",
        idempotency_key="idem-badvin",
        mode="submit",
    )
    assert result.outcome == "rejected"
    assert result.error_code == "vin_invalid"


# ---------------------------------------------------------------------------
# Persistence + no intake_entities dual-write
# ---------------------------------------------------------------------------


def test_persist_known_facts_single_slot(case_storage, svc: ClaimVehicleIdentityService):
    case_id = _claim_case()
    result = svc.upsert(
        case_id=case_id,
        payload={"vin": VALID_VIN, "year": "2020", "make": "Toyota", "model": "Camry"},
        command_id="cmd-persist",
        idempotency_key="idem-persist",
        mode="submit",
        persist=True,
    )
    assert result.outcome == "accepted"
    stored = get_case_by_id(case_id)
    assert stored is not None
    facts = stored.get("known_facts") or {}
    assert facts[FACT_KEY_VIN] == VALID_VIN
    assert facts["vin"] == VALID_VIN
    assert facts["own_vehicle_vin"] == VALID_VIN
    assert facts[FACT_KEY_SUMMARY] == "2020 Toyota Camry"
    assert facts["own_vehicle_info"] == "2020 Toyota Camry"
    assert facts[FACT_KEY_VEHICLE_ID] == f"veh:{case_id}"
    assert facts[FACT_KEY_VERIFICATION] == VERIFICATION_SUPPLIED_UNCONFIRMED


def test_module_does_not_import_intake_entities_writers():
    import ast

    import services.fiqa_api.inbox_triage.claim_vehicle_identity as mod
    import services.fiqa_api.inbox_triage.intake_service_lanes as lanes

    source = Path(mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod_name = node.module or ""
            imported.add(mod_name)
            for alias in node.names:
                imported.add(f"{mod_name}.{alias.name}")
    assert not any("entity_repository" in name for name in imported)
    assert not any("intake_service_lanes" in name for name in imported)
    assert not hasattr(mod, "upsert_active_vehicle")
    assert not hasattr(mod, lanes.SERVICE_LANE_ADD_CAR)
    assert "def vehicle_events" not in source
    assert "class VehicleTimeline" not in source
    assert "vehicle_history" not in source


def test_fact_records_updated_for_vin_and_vehicle_information(svc: ClaimVehicleIdentityService):
    result = svc.upsert(
        case_id="case_fr",
        payload={"vin": VALID_VIN, "year": "2020", "make": "Toyota", "model": "Camry"},
        command_id="cmd-fr",
        idempotency_key="idem-fr",
        mode="submit",
        fact_records={},
    )
    assert result.outcome == "accepted"
    vin_rec = result.fact_records["vin"]
    info_rec = result.fact_records["vehicle_information"]
    assert vin_rec["value"] == VALID_VIN
    assert vin_rec["status"] == VERIFICATION_SUPPLIED_UNCONFIRMED
    assert info_rec["value"] == "2020 Toyota Camry"
    assert info_rec["status"] == VERIFICATION_SUPPLIED_UNCONFIRMED


def test_events_are_slice1_field_saved_not_parallel_model(svc: ClaimVehicleIdentityService):
    result = svc.upsert(
        case_id="case_evt",
        payload={"vin": VALID_VIN},
        command_id="cmd-evt",
        idempotency_key="idem-evt",
        mode="submit",
    )
    assert len(result.events) == 1
    event = result.events[0]
    assert event["event_type"] == "field_saved"
    assert event["command_id"] == "cmd-evt"
    assert event["idempotency_key"] == "idem-evt"
    assert event["evidence"]["claim_vehicle_id"] == "veh:case_evt"
    assert "vehicle_event" not in event["event_type"]


def test_backward_compat_existing_own_vehicle_info_only():
    """Legacy free-text vehicle summary still hydrates the single slot."""
    vehicle = read_claim_vehicle_from_facts(
        {"own_vehicle_info": "2020 Toyota Camry"},
        case_id="case_legacy",
    )
    assert vehicle is not None
    assert vehicle.summary == "2020 Toyota Camry"
    assert vehicle.vehicle_id == "veh:case_legacy"
    # Not complete without VIN or structured path B flags.
    assert is_claim_vehicle_complete(vehicle) is False
