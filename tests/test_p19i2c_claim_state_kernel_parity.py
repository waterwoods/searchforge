"""P19I-2c — Claim state kernel parity refactor acceptance tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services.fiqa_api.wecom import claim_state
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    CLAIM_PHASE_SUMMARY_READY,
    SERVICE_LANE_CLAIM,
    _claim_snapshot_from_case_extra,
    are_claim_photos_complete,
    derive_claim_phase,
    get_claim_missing_items,
    is_accident_basics_complete,
    is_claim_summary_ready,
    is_injury_police_complete,
    is_other_party_info_complete,
)
from services.fiqa_api.workflow_definitions import CLAIM_FOUNDATION_DEFINITION
from services.fiqa_api.workflow_kernel import (
    evaluate_required_gate,
    what_is_collected,
    what_is_missing,
)


def _basics_case() -> dict:
    return {
        "service_lane": SERVICE_LANE_CLAIM,
        "known_facts": {
            "accident_datetime": "今天上午约10点",
            "accident_location": "Irvine Blvd & Culver",
            "accident_description": "对方变道刮蹭我左前门",
        },
        "collected_fields": ["accident_datetime", "accident_location", "accident_description"],
    }


def _damage_attachment() -> dict:
    return {
        "attachment_id": "a1",
        "source": "h5_task",
        "slot_assignment": "customer_damage_photo",
    }


def _vehicle_attachment() -> dict:
    return {
        "attachment_id": "a2",
        "source": "h5_task",
        "slot_assignment": "other_party_vehicle_photo",
    }


def _injury_police_no() -> dict:
    return {
        "known_facts": {"anyone_injured": "否", "police_involved": "否"},
        "collected_fields": ["anyone_injured", "police_involved"],
    }


def _merge_case(*parts: dict) -> dict:
    out: dict = {"service_lane": SERVICE_LANE_CLAIM}
    for part in parts:
        out.update({k: v for k, v in part.items() if k not in ("known_facts", "collected_fields", "case_attachments")})
        if "known_facts" in part:
            out.setdefault("known_facts", {}).update(part["known_facts"])
        if "collected_fields" in part:
            out.setdefault("collected_fields", []).extend(part["collected_fields"])
        if "case_attachments" in part:
            out.setdefault("case_attachments", []).extend(part["case_attachments"])
    return out


class TestKernelWiring:
    def test_claim_state_imports_kernel(self):
        source = Path("services/fiqa_api/wecom/claim_state.py").read_text(encoding="utf-8")
        assert "workflow_kernel" in source
        assert "CLAIM_FOUNDATION_DEFINITION" in source

    def test_intake_ready_constant_exists_for_future_migration(self):
        assert CLAIM_PHASE_INTAKE_READY_FOR_BROKER == "intake_ready_for_broker"
        assert CLAIM_PHASE_SUMMARY_READY == "claim_summary_ready"
        assert CLAIM_PHASE_SUMMARY_READY != CLAIM_PHASE_INTAKE_READY_FOR_BROKER

    def test_foundation_definition_matches_p19h1_required_count(self):
        assert len(CLAIM_FOUNDATION_DEFINITION.required_slots) == 8
        assert CLAIM_FOUNDATION_DEFINITION.human_review_phase == "claim_summary_ready"


class TestAdapterSnapshot:
    def test_empty_case_snapshot_has_no_collected(self):
        snapshot = _claim_snapshot_from_case_extra({})
        assert snapshot.lane == SERVICE_LANE_CLAIM
        assert snapshot.workflow_id == CLAIM_FOUNDATION_DEFINITION.workflow_id
        assert what_is_collected(CLAIM_FOUNDATION_DEFINITION, snapshot) == ()

    def test_basics_case_maps_collected_fields(self):
        case = _basics_case()
        snapshot = _claim_snapshot_from_case_extra(case)
        collected = set(what_is_collected(CLAIM_FOUNDATION_DEFINITION, snapshot))
        assert {"accident_datetime", "accident_location", "accident_description"}.issubset(collected)

    def test_injury_yes_sets_safety_flag(self):
        case = _merge_case(
            _basics_case(),
            {"known_facts": {"anyone_injured": "是"}, "collected_fields": ["anyone_injured"]},
        )
        snapshot = _claim_snapshot_from_case_extra(case)
        assert "injury_yes" in snapshot.safety_flags


class TestKernelParityPredicates:
    def test_basics_complete_parity(self):
        case = _basics_case()
        snapshot = _claim_snapshot_from_case_extra(case)
        missing_keys = {item.key for item in what_is_missing(CLAIM_FOUNDATION_DEFINITION, snapshot)}
        assert is_accident_basics_complete(case) is True
        assert not any(f in missing_keys for f in ("accident_datetime", "accident_location", "accident_description"))

    def test_photos_complete_parity(self):
        case = _merge_case(
            _basics_case(),
            {"case_attachments": [_damage_attachment(), _vehicle_attachment()]},
        )
        snapshot = _claim_snapshot_from_case_extra(case)
        collected = set(what_is_collected(CLAIM_FOUNDATION_DEFINITION, snapshot))
        assert are_claim_photos_complete(case) is True
        assert "customer_damage_photo" in collected
        assert "other_party_vehicle_or_plate" in collected

    def test_other_party_info_parity_via_phone(self):
        case = _merge_case(
            _basics_case(),
            {"case_attachments": [_damage_attachment(), _vehicle_attachment()]},
            {"known_facts": {"other_party_phone": "9491234567"}},
        )
        assert is_other_party_info_complete(case) is True

    def test_summary_ready_matches_required_gate(self):
        case = _merge_case(
            _basics_case(),
            {"case_attachments": [_damage_attachment(), _vehicle_attachment()]},
            {"known_facts": {"other_party_phone": "9491234567"}},
            _injury_police_no(),
        )
        snapshot = _claim_snapshot_from_case_extra(case)
        gate_passed = evaluate_required_gate(CLAIM_FOUNDATION_DEFINITION, snapshot).passed
        assert is_claim_summary_ready(case) is True
        assert gate_passed is True
        assert derive_claim_phase(case) == CLAIM_PHASE_SUMMARY_READY

    def test_missing_items_shape_unchanged(self):
        case = {"service_lane": SERVICE_LANE_CLAIM, "claim_phase": "claim_started"}
        missing = get_claim_missing_items(case)
        assert missing
        first = missing[0]
        assert set(first.keys()) == {"field", "label", "kind"}


class TestNoForbiddenImports:
    def test_claim_state_still_no_io(self):
        source = Path("services/fiqa_api/wecom/claim_state.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        for token in ("requests", "httpx", "sqlalchemy", "openai", "anthropic"):
            assert token not in imported

    def test_claim_state_no_orchestration_frameworks(self):
        source = Path("services/fiqa_api/wecom/claim_state.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        forbidden = {"temporal", "camunda", "langgraph", "prefect", "dagster"}
        assert imported.isdisjoint(forbidden)

    def test_adapter_helper_is_internal(self):
        assert hasattr(claim_state, "_claim_snapshot_from_case_extra")
