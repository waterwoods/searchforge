"""P19I-2b — Thin workflow kernel helpers tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services.fiqa_api.workflow_definitions import (
    ADD_VEHICLE_MINIMAL_DEFINITION,
    CLAIM_SIMPLIFIED_DEFINITION,
)
from services.fiqa_api.workflow_kernel import (
    WorkflowRuntimeSnapshot,
    compute_completion_score,
    evaluate_human_gate,
    evaluate_required_gate,
    evaluate_safety_gate,
    evaluate_workflow_snapshot,
    get_current_step,
    what_does_task_need,
    what_is_collected,
    what_is_missing,
)


def _av_snapshot(**kwargs) -> WorkflowRuntimeSnapshot:
    defaults = {
        "workflow_id": ADD_VEHICLE_MINIMAL_DEFINITION.workflow_id,
        "lane": ADD_VEHICLE_MINIMAL_DEFINITION.lane,
        "collected_fields": {},
        "attachments": {},
    }
    defaults.update(kwargs)
    return WorkflowRuntimeSnapshot(**defaults)


def _claim_snapshot(**kwargs) -> WorkflowRuntimeSnapshot:
    defaults = {
        "workflow_id": CLAIM_SIMPLIFIED_DEFINITION.workflow_id,
        "lane": CLAIM_SIMPLIFIED_DEFINITION.lane,
        "collected_fields": {},
        "attachments": {},
    }
    defaults.update(kwargs)
    return WorkflowRuntimeSnapshot(**defaults)


class TestDefinitionsWhatDoesTaskNeed:
    def test_add_vehicle_required_and_optional_slots(self):
        slots = what_does_task_need(ADD_VEHICLE_MINIMAL_DEFINITION)
        keys = [slot.key for slot in slots]
        assert keys == [
            "vin_photo",
            "registration_photo",
            "delivery_date",
            "parking_zip",
            "contact_phone",
            "insurance_card_photo",
        ]
        assert sum(1 for slot in slots if slot.required) == 5
        assert sum(1 for slot in slots if not slot.required) == 1

    def test_claim_required_and_optional_slots(self):
        slots = what_does_task_need(CLAIM_SIMPLIFIED_DEFINITION)
        keys = [slot.key for slot in slots]
        assert keys[:7] == [
            "accident_datetime",
            "accident_location",
            "accident_description",
            "customer_damage_photo",
            "other_party_vehicle_or_plate",
            "anyone_injured",
            "police_involved",
        ]
        assert "scene_photo" in keys
        assert "existing_claim_number" in keys
        assert sum(1 for slot in slots if slot.required) == 7
        assert sum(1 for slot in slots if not slot.required) == 6


class TestEmptyAddVehicleSnapshot:
    def test_empty_add_vehicle(self):
        snapshot = _av_snapshot()
        missing = what_is_missing(ADD_VEHICLE_MINIMAL_DEFINITION, snapshot)
        assert len(missing) == 5
        assert compute_completion_score(ADD_VEHICLE_MINIMAL_DEFINITION, snapshot) < 100
        assert evaluate_required_gate(ADD_VEHICLE_MINIMAL_DEFINITION, snapshot).passed is False
        handoff = evaluate_human_gate(ADD_VEHICLE_MINIMAL_DEFINITION, snapshot)
        assert handoff.can_hand_off is False
        assert handoff.ready_for_human_review is False
        step = get_current_step(ADD_VEHICLE_MINIMAL_DEFINITION, snapshot)
        assert step.phase == "photos"
        assert step.action == "collect_photos"
        assert step.missing_items
        assert step.missing_items[0].key == "vin_photo"


class TestPartialAddVehicleSnapshot:
    def test_partial_add_vehicle(self):
        snapshot = _av_snapshot(
            attachments={"vin_photo": "received", "registration_photo": "received"},
            collected_fields={"delivery_date": "7月10日"},
        )
        collected = what_is_collected(ADD_VEHICLE_MINIMAL_DEFINITION, snapshot)
        assert "vin_photo" in collected
        assert "registration_photo" in collected
        assert "delivery_date" in collected
        missing = what_is_missing(ADD_VEHICLE_MINIMAL_DEFINITION, snapshot)
        assert {item.key for item in missing} == {"parking_zip", "contact_phone"}
        empty_score = compute_completion_score(ADD_VEHICLE_MINIMAL_DEFINITION, _av_snapshot())
        partial_score = compute_completion_score(ADD_VEHICLE_MINIMAL_DEFINITION, snapshot)
        assert partial_score > empty_score


class TestCompleteAddVehicleRequired:
    def test_complete_required_optional_missing_ok(self):
        snapshot = _av_snapshot(
            attachments={"vin_photo": "received", "registration_photo": "received"},
            collected_fields={
                "delivery_date": "7月10日",
                "parking_zip": "92705",
                "contact_phone": "2031234567",
            },
        )
        assert evaluate_required_gate(ADD_VEHICLE_MINIMAL_DEFINITION, snapshot).passed is True
        handoff = evaluate_human_gate(ADD_VEHICLE_MINIMAL_DEFINITION, snapshot)
        assert handoff.can_hand_off is True
        assert handoff.ready_for_human_review is True
        assert handoff.needs_manual_handle is False
        step = get_current_step(ADD_VEHICLE_MINIMAL_DEFINITION, snapshot)
        assert step.phase == "ready_for_broker_review"
        assert step.action == "ready_for_human_review"


class TestEmptyClaimSnapshot:
    def test_empty_claim_starts_accident_basics(self):
        snapshot = _claim_snapshot()
        step = get_current_step(CLAIM_SIMPLIFIED_DEFINITION, snapshot)
        assert step.phase == "accident_basics"
        assert step.action == "collect_accident_basics"
        missing = what_is_missing(CLAIM_SIMPLIFIED_DEFINITION, snapshot)
        assert missing[0].phase == "accident_basics"


class TestClaimBasicsWithoutEvidence:
    def test_claim_basics_only_moves_to_evidence(self):
        snapshot = _claim_snapshot(
            collected_fields={
                "accident_datetime": "今天上午",
                "accident_location": "Irvine",
                "accident_description": "追尾",
            },
        )
        step = get_current_step(CLAIM_SIMPLIFIED_DEFINITION, snapshot)
        assert step.phase == "evidence_pack"
        assert step.action == "collect_evidence_pack"


class TestClaimEvidenceComposite:
    def test_composite_other_party_satisfied_by_plate_field(self):
        snapshot = _claim_snapshot(
            collected_fields={
                "accident_datetime": "今天上午",
                "accident_location": "Irvine",
                "accident_description": "追尾",
                "other_party_plate": "8ABC123",
            },
            attachments={"customer_damage_photo": "received"},
        )
        collected = what_is_collected(CLAIM_SIMPLIFIED_DEFINITION, snapshot)
        assert "customer_damage_photo" in collected
        assert "other_party_vehicle_or_plate" in collected
        missing = what_is_missing(CLAIM_SIMPLIFIED_DEFINITION, snapshot)
        assert {item.key for item in missing} == {"anyone_injured", "police_involved"}


class TestClaimRiskConfirmationMissing:
    def test_risk_confirmation_current_step(self):
        snapshot = _claim_snapshot(
            collected_fields={
                "accident_datetime": "今天上午",
                "accident_location": "Irvine",
                "accident_description": "追尾",
                "other_party_plate": "8ABC123",
            },
            attachments={"customer_damage_photo": "received"},
        )
        step = get_current_step(CLAIM_SIMPLIFIED_DEFINITION, snapshot)
        assert step.phase == "risk_confirmation"
        assert step.action == "collect_risk_confirmation"


class TestCompleteClaimRequired:
    def test_complete_claim_ready_for_broker(self):
        snapshot = _claim_snapshot(
            collected_fields={
                "accident_datetime": "今天上午",
                "accident_location": "Irvine",
                "accident_description": "追尾",
                "other_party_plate": "8ABC123",
                "anyone_injured": "no",
                "police_involved": "yes",
            },
            attachments={"customer_damage_photo": "received"},
        )
        assert evaluate_required_gate(CLAIM_SIMPLIFIED_DEFINITION, snapshot).passed is True
        handoff = evaluate_human_gate(CLAIM_SIMPLIFIED_DEFINITION, snapshot)
        assert handoff.can_hand_off is True
        assert handoff.ready_for_human_review is True
        step = get_current_step(CLAIM_SIMPLIFIED_DEFINITION, snapshot)
        assert step.phase == "intake_ready_for_broker"
        assert step.action == "ready_for_human_review"


class TestClaimOptionalScore:
    def test_optional_increases_score_without_blocking_handoff(self):
        base = _claim_snapshot(
            collected_fields={
                "accident_datetime": "今天上午",
                "accident_location": "Irvine",
                "accident_description": "追尾",
                "other_party_plate": "8ABC123",
                "anyone_injured": "no",
                "police_involved": "yes",
            },
            attachments={"customer_damage_photo": "received"},
        )
        richer = _claim_snapshot(
            collected_fields={
                **base.collected_fields,
                "existing_claim_number": "CLM-123",
            },
            attachments={
                **base.attachments,
                "scene_photo": "received",
                "other_party_insurance_card": "received",
            },
        )
        base_score = compute_completion_score(CLAIM_SIMPLIFIED_DEFINITION, base)
        rich_score = compute_completion_score(CLAIM_SIMPLIFIED_DEFINITION, richer)
        assert rich_score > base_score
        assert evaluate_required_gate(CLAIM_SIMPLIFIED_DEFINITION, richer).passed is True


class TestSafetyFlagManualHandle:
    def test_injury_routes_to_manual_handle(self):
        snapshot = _claim_snapshot(safety_flags=("injury_yes",))
        safety = evaluate_safety_gate(CLAIM_SIMPLIFIED_DEFINITION, snapshot)
        assert safety.passed is False
        assert safety.blocked_reason == "injury_yes"
        handoff = evaluate_human_gate(CLAIM_SIMPLIFIED_DEFINITION, snapshot)
        assert handoff.can_hand_off is True
        assert handoff.needs_manual_handle is True
        step = get_current_step(CLAIM_SIMPLIFIED_DEFINITION, snapshot)
        assert step.action == "manual_handle"
        assert step.phase == "manual_handle"


class TestRequiredGateVsCompletionScore:
    def test_high_score_still_fails_required_gate(self):
        snapshot = _av_snapshot(
            attachments={
                "vin_photo": "received",
                "registration_photo": "received",
                "insurance_card_photo": "received",
            },
            collected_fields={"delivery_date": "7月10日", "parking_zip": "92705"},
        )
        score = compute_completion_score(ADD_VEHICLE_MINIMAL_DEFINITION, snapshot)
        assert score >= 80
        assert evaluate_required_gate(ADD_VEHICLE_MINIMAL_DEFINITION, snapshot).passed is False


class TestCurrentStepFocused:
    def test_current_step_one_phase_not_full_checklist(self):
        snapshot = _claim_snapshot()
        step = get_current_step(CLAIM_SIMPLIFIED_DEFINITION, snapshot)
        assert len(step.missing_items) == 3
        assert all(item.phase == "accident_basics" for item in step.missing_items)
        assert step.action == "collect_accident_basics"


class TestEvaluateWorkflowSnapshot:
    def test_snapshot_dict_stable_keys(self):
        result = evaluate_workflow_snapshot(CLAIM_SIMPLIFIED_DEFINITION, _claim_snapshot())
        assert set(result.keys()) == {
            "workflow_id",
            "lane",
            "needs",
            "collected",
            "missing",
            "completion_score",
            "safety_gate",
            "required_gate",
            "current_step",
            "human_handoff",
        }
        assert result["workflow_id"] == "claim_intake_v2_simplified"
        assert isinstance(result["safety_gate"], dict)
        assert isinstance(result["current_step"], dict)


class TestNoForbiddenImports:
    def test_workflow_kernel_has_no_forbidden_framework_imports(self):
        source = Path("services/fiqa_api/workflow_kernel.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        forbidden = {"temporal", "camunda", "langgraph", "prefect", "dagster", "boto3"}
        assert imported.isdisjoint(forbidden)

    def test_workflow_kernel_module_has_no_io(self):
        source = Path("services/fiqa_api/workflow_kernel.py").read_text(encoding="utf-8").lower()
        for token in ("requests", "httpx", "sqlalchemy", "openai", "anthropic"):
            assert token not in source
