"""Voice-first Guided Intake V1 — reuse Accident Story; no parallel case system."""

from __future__ import annotations

import pytest

from services.fiqa_api.inbox_triage.accident_story_assistant.contract import (
    build_guided_customer_view,
    public_proposal,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.events import (
    reset_ai_story_events_for_tests,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.graph import propose_from_story
from services.fiqa_api.inbox_triage.accident_story_assistant.service import (
    confirm_accident_story,
    propose_accident_story,
    reset_accident_story_idempotency_for_tests,
)


def setup_function() -> None:
    reset_accident_story_idempotency_for_tests()
    reset_ai_story_events_for_tests()


def _fake_case_persist(monkeypatch: pytest.MonkeyPatch, case_id: str) -> dict:
    bag: dict = {"case_id": case_id, "known_facts": {}, "known_fact_provenance": {}}
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store._require_case_storage_path",
        lambda: None,
    )
    monkeypatch.setattr(
        "services.fiqa_api.db.service_record_settings.db_primary_writes_enabled",
        lambda: False,
    )

    def load(cid):
        return bag if cid == case_id else None

    def persist(cid, case):
        if cid != case_id:
            return False
        snapshot = dict(case)
        bag.clear()
        bag.update(snapshot)
        return True

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store._load_case_for_mutation",
        load,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store._persist_case_after_update",
        persist,
    )
    return bag


def test_voice_transcript_proposal_is_ai_proposed_not_authoritative():
    proposal = propose_from_story(
        raw_story="昨天下午在 San Jose 路口被追尾，没有人受伤。",
    )
    assert proposal["authority_note"] == "ai_proposed_until_customer_confirms"
    for fact in proposal.get("proposed_facts") or []:
        assert fact.get("authority") in (None, "ai_proposed", "customer_confirmed")
        if fact.get("authority"):
            assert fact["authority"] != "broker_reviewed"


def test_guided_review_exposes_customer_friendly_categories():
    proposal = propose_from_story(
        raw_story="昨天在路口被白色轿车追尾，没有受伤。",
    )
    rows = {r["key"]: r for r in proposal["guided_view"]["fact_rows"]}
    assert "what_happened" in rows
    assert rows["what_happened"]["label_zh"] == "发生了什么"
    assert "accident_datetime" in rows
    assert "accident_location" in rows
    assert "involved" in rows
    assert rows["involved"]["label_zh"] == "涉及车辆/人员"
    assert "injury_status" in rows
    # Known vs needs confirmation is visible via status.
    assert rows["injury_status"]["status"] in ("known", "pending", "partial")


def test_complete_voice_story_no_unnecessary_questions():
    proposal = propose_from_story(
        raw_story="昨天下午三点在 Mountain View Castro Street 被追尾，没有人受伤。",
    )
    assert len(proposal["followup_questions"]) == 0
    assert proposal["guided_view"]["missing_count"] == 0


def test_incomplete_voice_story_asks_at_most_three():
    proposal = propose_from_story(raw_story="被追尾了。")
    assert len(proposal["followup_questions"]) <= 3
    assert len(proposal["guided_view"]["followup_fields"]) <= 3
    assert len(proposal["guided_view"]["followup_fields"]) >= 1


def test_llm_off_deterministic_path_still_works(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACCIDENT_STORY_LLM", "0")
    monkeypatch.setenv("ACCIDENT_STORY_ASSISTANT_ENABLED", "1")
    proposal = propose_from_story(
        raw_story="昨天在家附近追尾，没有受伤。",
    )
    assert proposal["model_provider"] in ("deterministic", "none")
    assert proposal["raw_story"]
    assert "guided_view" in proposal


def test_assistant_disabled_manual_fallback_preserves_story(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACCIDENT_STORY_ASSISTANT_ENABLED", "0")
    out = propose_accident_story(
        raw_story="语音转写：昨天追尾",
        command_id="vf_cmd_1",
        idempotency_key="vf_idem_1",
    )
    assert out.get("ok") is True
    proposal = out["proposal"]
    assert proposal.get("used_fallback") is True
    assert proposal.get("manual_intake_required") is True
    assert "追尾" in proposal.get("raw_story", "")
    assert proposal.get("authority_note") == "ai_proposed_until_customer_confirms"


def test_ai_cannot_become_authoritative_without_confirmation():
    proposal = propose_from_story(raw_story="昨天追尾，没有受伤。")
    result = confirm_accident_story(
        case_id="case_vf_unconfirmed",
        command_id="vf_cmd_unconf",
        idempotency_key="vf_idem_unconf",
        raw_story="昨天追尾，没有受伤。",
        confirm=False,
        proposal=proposal,
    )
    assert result["ok"] is True
    assert result["persisted"] is False
    assert result["lifecycle_mutated"] is False
    assert result["authority"] == "ai_proposed"
    assert "unconfirmed" in result.get("note", "")


def test_customer_confirm_sets_customer_confirmed_provenance(monkeypatch: pytest.MonkeyPatch):
    case_id = "case_vf_confirmed_auth"
    bag = _fake_case_persist(monkeypatch, case_id)
    proposed = propose_accident_story(
        raw_story="昨天上午在路口被追尾，没有人受伤。",
        command_id="vf_cmd_conf_a",
        idempotency_key="vf_idem_conf_a",
    )
    assert proposed.get("ok") is True
    result = confirm_accident_story(
        case_id=case_id,
        command_id="vf_cmd_conf_b",
        idempotency_key="vf_idem_conf_b",
        raw_story="昨天上午在路口被追尾，没有人受伤。",
        confirm=True,
        proposal_id=proposed["proposal_id"],
        customer_edits={
            "injury_status": "no",
            "accident_time_text": "昨天上午",
            "accident_location_text": "路口",
        },
    )
    assert result["ok"] is True
    assert result["persisted"] is True
    assistant = bag.get("accident_story_assistant") or {}
    assert assistant.get("authority") == "customer_confirmed"
    layers = assistant.get("layers") or {}
    assert (layers.get("customer_confirmed") or {}).get("injury_status") == "no"
    assert (layers.get("ai_draft") or {}).get("authority") == "ai_proposed"


def test_duplicate_propose_idempotent():
    first = propose_accident_story(
        raw_story="昨天追尾，没有受伤，在超市门口。",
        command_id="vf_dup_1",
        idempotency_key="vf_dup_idem",
    )
    second = propose_accident_story(
        raw_story="昨天追尾，没有受伤，在超市门口。",
        command_id="vf_dup_1",
        idempotency_key="vf_dup_idem",
    )
    assert first.get("ok") is True
    assert first.get("outcome") == "accepted"
    assert second.get("outcome") == "replayed"
    assert first.get("proposal", {}).get("incident_summary") == second.get("proposal", {}).get(
        "incident_summary"
    )


def test_public_proposal_never_claims_case_authority_without_confirm():
    state_view = public_proposal(
        {
            "schema_version": 1,
            "raw_story": "测试",
            "incident_summary": "测试摘要",
            "injury_status": "unknown",
            "accident_time_text": "",
            "accident_location_text": "",
            "involved_parties": [],
            "involved_vehicles": [],
            "proposed_facts": [
                {
                    "field_key": "injury_status",
                    "value": "unknown",
                    "authority": "ai_proposed",
                    "confidence": 0.2,
                    "source": "deterministic",
                }
            ],
            "missing_required_facts": ["accident_datetime", "accident_location", "injury_status"],
            "followup_questions": ["事故大约发生在几点？"],
            "confidence_by_field": {},
            "warnings": [],
            "conflicts": [],
            "used_fallback": False,
            "fallback_reason": "",
            "model_provider": "deterministic",
            "model_name": "rules_v1",
        }
    )
    assert state_view["authority_note"] == "ai_proposed_until_customer_confirms"
    guided = build_guided_customer_view(
        {
            "raw_story": "测试追尾",
            "incident_summary": "追尾",
            "injury_status": "unknown",
            "accident_time_text": "",
            "accident_location_text": "",
            "involved_vehicles": ["白色轿车"],
            "involved_parties": [],
            "missing_required_facts": ["accident_datetime", "accident_location", "injury_status"],
            "followup_questions": [],
            "conflicts": [],
        }
    )
    assert any(r["key"] == "involved" and "白色" in r["value_zh"] for r in guided["fact_rows"])
