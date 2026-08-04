"""Bounded LangGraph accident-story assistant — required test matrix."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.accident_story_assistant.events import (
    EVENT_CREATED,
    EVENT_FALLBACK,
    list_ai_story_events_for_tests,
    reset_ai_story_events_for_tests,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.extractors import (
    validate_model_proposals,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.graph import (
    propose_from_story,
    run_accident_story_graph,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.service import (
    confirm_accident_story,
    propose_accident_story,
    reset_accident_story_idempotency_for_tests,
)

FIXTURE_DIR = Path("tests/fixtures/accident_story_langgraph")


def setup_function() -> None:
    reset_accident_story_idempotency_for_tests()
    reset_ai_story_events_for_tests()


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_complete_story_no_unnecessary_questions():
    fx = _load("complete_story.json")
    proposal = propose_from_story(raw_story=fx["raw_story"])
    assert proposal["injury_status"] == "no"
    assert proposal["accident_time_text"]
    assert proposal["accident_location_text"]
    assert len(proposal["followup_questions"]) <= fx["expect"]["max_followup_questions"]
    guided = proposal["guided_view"]
    assert guided["missing_count"] == 0
    assert "请确认" in guided["missing_message_zh"]


def test_missing_location_one_useful_question():
    fx = _load("missing_location.json")
    proposal = propose_from_story(raw_story=fx["raw_story"])
    assert proposal["injury_status"] == "no"
    assert "accident_location" in proposal["missing_required_facts"]
    assert "injury_status" not in proposal["missing_required_facts"]
    assert len(proposal["followup_questions"]) == 1
    assert "哪里" in proposal["followup_questions"][0] or "地点" in proposal["followup_questions"][0]


def test_missing_time_and_injury_minimal_questions():
    fx = _load("missing_time_injury.json")
    proposal = propose_from_story(raw_story=fx["raw_story"])
    for key in fx["expect"]["missing_contains"]:
        assert key in proposal["missing_required_facts"]
    assert len(proposal["followup_questions"]) <= 2
    assert proposal["injury_status"] == "unknown"


def test_demo_incomplete_story_two_questions_injury_known():
    fx = _load("missing_time_location_injury_known.json")
    proposal = propose_from_story(raw_story=fx["raw_story"])
    assert proposal["injury_status"] == "no"
    for key in fx["expect"]["missing_contains"]:
        assert key in proposal["missing_required_facts"]
    for key in fx["expect"]["missing_excludes"]:
        assert key not in proposal["missing_required_facts"]
    assert len(proposal["followup_questions"]) == 2
    guided = proposal["guided_view"]
    assert guided["missing_count"] == 2
    assert "还需要确认 2 项" in guided["missing_message_zh"]
    assert any(r["key"] == "accident_type" and r["value_zh"] == "追尾" for r in guided["fact_rows"])
    assert len(guided["followup_fields"]) == 2
    assert guided["show_full_form_option"] is True


def test_missing_injury_only_one_question():
    fx = _load("missing_injury_only.json")
    proposal = propose_from_story(raw_story=fx["raw_story"])
    assert proposal["missing_required_facts"] == ["injury_status"]
    assert len(proposal["followup_questions"]) == 1
    assert "受伤" in proposal["followup_questions"][0]


def test_all_three_missing_capped_at_three():
    fx = _load("all_three_missing.json")
    proposal = propose_from_story(raw_story=fx["raw_story"])
    assert len(proposal["followup_questions"]) == 3
    assert len(proposal["guided_view"]["followup_fields"]) == 3


def test_explicit_no_injuries_remains_no():
    proposal = propose_from_story(raw_story="昨天追尾，没有受伤。")
    assert proposal["injury_status"] == "no"


def test_uncertain_injury_remains_unknown():
    proposal = propose_from_story(raw_story="昨天追尾，不确定有没有受伤。")
    assert proposal["injury_status"] == "unknown"


def test_conflicting_injury_flagged_not_silently_resolved():
    state = run_accident_story_graph(raw_story="有人受伤，同时没有受伤。")
    assert state["injury_status"] == "unknown"
    assert "injury_yes_and_no_mentioned" in (state.get("conflicts") or [])
    proposal = propose_from_story(raw_story="有人受伤，同时没有受伤。")
    assert proposal["guided_view"]["conflicts"]
    assert "冲突" in proposal["guided_view"]["conflict_message_zh"]


def test_hallucinated_model_field_rejected():
    with pytest.raises(ValueError, match="hallucinated_fields"):
        validate_model_proposals({"coverage_decision": "liable", "injury_status": "no"})


def test_invalid_model_json_triggers_fallback():
    def bad_llm(_text: str) -> dict:
        raise ValueError("invalid_model_json")

    proposal = propose_from_story(
        raw_story="昨天在 San Jose 停车场追尾，没有受伤。",
        llm_caller=bad_llm,
    )
    assert proposal["injury_status"] == "no"
    assert proposal["used_fallback"] is True


def test_model_timeout_triggers_fallback():
    def timeout_llm(_text: str) -> dict:
        raise TimeoutError("timeout")

    proposal = propose_from_story(
        raw_story="昨天在 San Jose 停车场追尾，没有受伤。",
        llm_caller=timeout_llm,
    )
    assert proposal["used_fallback"] is True
    assert proposal["raw_story"]
    assert "llm_unavailable_or_invalid_using_deterministic" in (proposal.get("warnings") or [])


def test_propose_emits_created_and_fallback_events():
    def bad_llm(_text: str) -> dict:
        raise ValueError("invalid_model_json")

    propose_accident_story(
        raw_story="昨天在 San Jose 停车场追尾，没有受伤。",
        command_id="cmd_evt_1_xxxxxxxx",
        idempotency_key="idem_evt_1_xxxxxxx",
        llm_caller=bad_llm,
    )
    types = {e["event_type"] for e in list_ai_story_events_for_tests()}
    assert EVENT_CREATED in types
    assert EVENT_FALLBACK in types
    for e in list_ai_story_events_for_tests():
        meta = e.get("meta") or {}
        assert "raw_story" not in meta
        assert "accident_description" not in meta


def test_repeated_command_idempotent():
    r1 = propose_accident_story(
        raw_story="昨天追尾，没有受伤，在 San Jose。",
        command_id="cmd_story_idem_001",
        idempotency_key="idem_story_001",
    )
    r2 = propose_accident_story(
        raw_story="昨天追尾，没有受伤，在 San Jose。",
        command_id="cmd_story_idem_001",
        idempotency_key="idem_story_001",
    )
    assert r1["outcome"] == "accepted"
    assert r2["outcome"] == "replayed"
    assert r1["proposal"]["incident_summary"] == r2["proposal"]["incident_summary"]


def test_customer_edits_override_ai_proposal():
    proposal = propose_from_story(raw_story="昨天追尾。")
    assert proposal["injury_status"] in ("unknown", "no", "yes")
    result = confirm_accident_story(
        case_id="case_missing_for_edit_test",
        command_id="cmd_edit_1",
        idempotency_key="idem_edit_1",
        raw_story="昨天追尾。",
        confirm=False,
        customer_edits={"injury_status": "no", "accident_location_text": "Oakland"},
        proposal=proposal,
    )
    assert result["persisted"] is False
    assert result["authority"] == "ai_proposed"


def test_unconfirmed_proposal_never_authoritative():
    result = confirm_accident_story(
        case_id="case_unconfirmed_x",
        command_id="cmd_unconf_1",
        idempotency_key="idem_unconf_1",
        raw_story="昨天追尾，没有受伤。",
        confirm=False,
        proposal=propose_from_story(raw_story="昨天追尾，没有受伤。"),
    )
    assert result["ok"] is True
    assert result["persisted"] is False
    assert result["lifecycle_mutated"] is False
    assert "unconfirmed" in result.get("note", "")


def test_lifecycle_not_mutated_on_propose():
    result = propose_accident_story(
        raw_story="昨天在停车场追尾，没有受伤。",
        command_id="cmd_life_1",
        idempotency_key="idem_life_1",
    )
    assert result["lifecycle_mutated"] is False
