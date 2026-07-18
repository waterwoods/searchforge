"""P24A Commit 1 — Constitution Projection skeleton contract (kept green under P24B)."""

from __future__ import annotations

import copy

from services.fiqa_api.inbox_triage.constitution_projection import (
    BAND_CUSTOMER_MISSING,
    PROJECTION_VERSION,
    STAGE_CUSTOMER_ACTION_NEEDED,
    ConstitutionInputs,
    attach_constitution_projection,
    build_constitution_projection,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


def _sample_case() -> dict:
    return {
        "case_id": "case_p24a_skeleton_001",
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "accident_basics_complete",
        "customer_name": "Camry Driver",
        "known_facts": {
            "own_vehicle_info": "2020 Toyota Camry",
            "accident_location": "Irvine",
        },
        "p20_slice1_projection": {
            "case_id": "case_p24a_skeleton_001",
            "workflow_state": "broker_more_requested",
            "customer_next_action": {
                "action_type": "provide_evidence",
                "title": "上传保险卡",
                "required_input": "policy_or_insurance_card",
            },
            "broker_next_action": {
                "action_type": "wait_for_customer_item",
                "status": "waiting_for_customer",
            },
        },
        "claim_case_brief": {
            "summary": "placeholder brief",
            "brief_version": 1,
        },
        "claim_evidence_summary": {
            "received_slots": ["scene_photo"],
            "missing_required_slots": ["customer_damage_photo"],
        },
    }


def _assert_stable_schema(projection: dict) -> None:
    assert set(projection.keys()) == {
        "projection_version",
        "case_id",
        "current_stage",
        "customer",
        "broker",
    }
    assert projection["projection_version"] == PROJECTION_VERSION
    assert projection["case_id"] == "case_p24a_skeleton_001"
    assert isinstance(projection["current_stage"], str)
    assert projection["current_stage"]

    customer = projection["customer"]
    assert set(customer.keys()) == {"today", "why", "after", "trust", "current_stage", "tasks"}
    assert isinstance(customer["today"], str)
    assert isinstance(customer["why"], str)
    assert isinstance(customer["after"], str)
    assert set(customer["trust"].keys()) == {"care_line", "care_note"}
    assert isinstance(customer["trust"]["care_line"], str)
    assert isinstance(customer["trust"]["care_note"], str)
    assert isinstance(customer["current_stage"], str)
    assert isinstance(customer["tasks"], list)
    for task in customer["tasks"]:
        assert set(task.keys()) >= {
            "task_id",
            "title",
            "state",
            "progress",
            "is_today",
            "route",
            "actionable",
            "primary_action",
        }
        assert set(task["progress"].keys()) == {"completed", "total"}

    broker = projection["broker"]
    assert set(broker.keys()) == {
        "queue_summary",
        "case_conclusion",
        "next_action",
        "priority",
        "current_stage",
    }
    assert set(broker["queue_summary"].keys()) == {"band", "label", "why_attention"}
    assert set(broker["case_conclusion"].keys()) == {
        "what_happened",
        "known",
        "uncertain",
        "evidence",
        "customer_focus",
        "customer_why",
        "customer_after",
        "customer_trust",
    }
    assert isinstance(broker["queue_summary"]["band"], str)
    assert isinstance(broker["case_conclusion"]["known"], list)
    assert isinstance(broker["case_conclusion"]["uncertain"], list)
    assert isinstance(broker["case_conclusion"]["evidence"], list)
    assert set(broker["next_action"].keys()) == {
        "label",
        "action_type",
        "enabled",
        "note",
    }
    assert isinstance(broker["next_action"]["label"], str)
    assert isinstance(broker["next_action"]["enabled"], bool)
    assert set(broker["priority"].keys()) == {"band", "rank"}
    assert isinstance(broker["priority"]["band"], str)
    assert isinstance(broker["priority"]["rank"], int)
    assert isinstance(broker["current_stage"], str)
    assert broker["current_stage"] == projection["customer"]["current_stage"]


def test_module_loads_and_builds_projection():
    case = _sample_case()
    projection = build_constitution_projection(ConstitutionInputs(case=case))
    _assert_stable_schema(projection)
    # Shared stage follows customer Constitution vocabulary (P24B/P24C).
    assert projection["current_stage"] == STAGE_CUSTOMER_ACTION_NEEDED
    assert projection["customer"]["current_stage"] == STAGE_CUSTOMER_ACTION_NEEDED
    assert projection["broker"]["current_stage"] == STAGE_CUSTOMER_ACTION_NEEDED
    assert projection["broker"]["priority"]["band"] == BAND_CUSTOMER_MISSING
    assert projection["broker"]["next_action"]["label"] == "暂无动作"
    assert projection["broker"]["next_action"]["enabled"] is False


def test_build_does_not_mutate_input_case():
    case = _sample_case()
    before = copy.deepcopy(case)
    _ = build_constitution_projection(
        {
            "case": case,
            "slice1": case["p20_slice1_projection"],
            "brief": case["claim_case_brief"],
            "evidence": case["claim_evidence_summary"],
            "claim_phase": case["claim_phase"],
        }
    )
    assert case == before


def test_attach_is_additive_only():
    case = _sample_case()
    before_keys = set(case.keys())
    before = copy.deepcopy(case)

    out = attach_constitution_projection(case)
    assert out is case
    assert "constitution_projection" in case
    _assert_stable_schema(case["constitution_projection"])

    for key in before_keys:
        assert case[key] == before[key]
    assert set(case.keys()) == before_keys | {"constitution_projection"}


def test_build_is_pure_no_persistence_helpers_invoked(monkeypatch):
    """Skeleton must stay pure: no case_store / Slice1 service / DB calls."""

    def _boom(*_args, **_kwargs):
        raise AssertionError("constitution projection must not touch persistence or network")

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.save_case",
        _boom,
        raising=False,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.get_case_by_id",
        _boom,
        raising=False,
    )
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_repository.fetch_service_records",
        _boom,
        raising=False,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_slice1_command_service.default_slice1_service",
        _boom,
        raising=False,
    )

    projection = build_constitution_projection(ConstitutionInputs(case=_sample_case()))
    _assert_stable_schema(projection)
    attached = attach_constitution_projection(_sample_case())
    _assert_stable_schema(attached["constitution_projection"])
