"""P19J-1c — WeCom workflow scenario simulator tests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.workflow_scenario_simulator import (
    ALL_PREDEFINED_SCENARIOS,
    SCENARIO_ADD_VEHICLE_CLAIM_QUESTION,
    SCENARIO_ADD_VEHICLE_INJURY_OVERRIDE,
    SCENARIO_ADD_VEHICLE_RESTART,
    SCENARIO_ADD_VEHICLE_SECONDARY_TOPIC,
    SCENARIO_ADD_VEHICLE_TO_CLAIM_INTERRUPT,
    SCENARIO_NO_ACTIVE_CLAIM_BASICS,
    ScenarioStep,
    WorkflowScenarioSession,
    run_predefined_scenario,
)


@pytest.fixture(autouse=True)
def _json_store():
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


def _run_named(name: str, steps: list[ScenarioStep], *, seed_add_vehicle: bool) -> None:
    result = run_predefined_scenario(name, steps, seed_add_vehicle=seed_add_vehicle)
    assert result.passed, f"{name} failed:\n{result.summary}"


# --- Scenario 1: Add Vehicle → Claim interrupt happy path ---


def test_scenario_1_add_vehicle_to_claim_interrupt_happy_path():
    name, steps = SCENARIO_ADD_VEHICLE_TO_CLAIM_INTERRUPT
    _run_named(name, list(steps), seed_add_vehicle=True)


# --- Scenario 2: Add Vehicle + injury override ---


def test_scenario_2_add_vehicle_injury_override():
    name, steps = SCENARIO_ADD_VEHICLE_INJURY_OVERRIDE
    _run_named(name, list(steps), seed_add_vehicle=True)


# --- Scenario 3: Add Vehicle + claim question ---


def test_scenario_3_add_vehicle_claim_question():
    name, steps = SCENARIO_ADD_VEHICLE_CLAIM_QUESTION
    _run_named(name, list(steps), seed_add_vehicle=True)


# --- Scenario 4: Add Vehicle + non-claim secondary topic ---


def test_scenario_4_add_vehicle_secondary_topic_deferral():
    name, steps = SCENARIO_ADD_VEHICLE_SECONDARY_TOPIC
    _run_named(name, list(steps), seed_add_vehicle=True)


# --- Scenario 5: No active case + Claim basics happy path ---


def test_scenario_5_no_active_claim_basics_happy_path():
    name, steps = SCENARIO_NO_ACTIVE_CLAIM_BASICS
    _run_named(name, list(steps), seed_add_vehicle=False)


# --- Scenario 6: Add Vehicle restart remains normal ---


def test_scenario_6_add_vehicle_restart_not_claim():
    name, steps = SCENARIO_ADD_VEHICLE_RESTART
    session = WorkflowScenarioSession(external_userid="wm_restart_j1c")
    session.setup_wecom_env()
    turn = session.route_inbound_text(steps[0].inbound_text)

    assert turn.outcome.get("internal_intent") == "add_car"
    assert turn.outcome.get("service_lane") != SERVICE_LANE_CLAIM
    rule = (turn.routing_decision or {}).get("priority_rule") or ""
    assert "claim_interrupt" not in rule


def test_all_predefined_scenarios_pass():
    for name, steps in ALL_PREDEFINED_SCENARIOS:
        if name == "add_vehicle_restart":
            continue  # covered by dedicated test above
        seed = name != "no_active_claim_basics"
        _run_named(name, list(steps), seed_add_vehicle=seed)


def test_scenario_result_includes_routing_decision_each_step():
    name, steps = SCENARIO_ADD_VEHICLE_TO_CLAIM_INTERRUPT
    result = run_predefined_scenario(name, list(steps), seed_add_vehicle=True)
    for step_result in result.steps:
        assert step_result.routing_decision is not None
        assert step_result.routing_decision.get("event") == "wecom_routing_decision_v1"
        assert step_result.routing_decision.get("priority_rule")
        assert step_result.routing_decision.get("decision")
        assert step_result.routing_decision.get("reason")
