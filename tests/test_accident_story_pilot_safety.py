"""Pilot safety — failure injection + kill switches + fallback contract."""

from __future__ import annotations

import pytest

from services.fiqa_api.inbox_triage.accident_story_assistant.events import (
    EVENT_DISABLED,
    EVENT_FALLBACK,
    list_ai_story_events_for_tests,
    reset_ai_story_events_for_tests,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.flags import (
    CUSTOMER_MSG_DISABLED_ZH,
    CUSTOMER_MSG_FALLBACK_ZH,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.graph import (
    propose_from_story,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.metrics import (
    summarize_pilot_metrics,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.service import (
    propose_accident_story,
    reset_accident_story_idempotency_for_tests,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.tracing import (
    META_ALLOWLIST,
    build_root_trace_metadata,
)


def setup_function() -> None:
    reset_accident_story_idempotency_for_tests()
    reset_ai_story_events_for_tests()


def test_feature_flag_disabled_falls_back_to_manual_intake(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACCIDENT_STORY_ASSISTANT_ENABLED", "0")
    result = propose_accident_story(
        raw_story="昨天开车的时候被追尾，没有受伤。",
        command_id="cmd_dis_1",
        idempotency_key="idem_dis_1",
    )
    assert result["ok"] is True
    assert result["lifecycle_mutated"] is False
    proposal = result["proposal"]
    assert proposal["used_fallback"] is True
    assert proposal["manual_intake_required"] is True
    assert proposal["raw_story"].startswith("昨天")
    assert proposal["injury_status"] == "unknown"  # do not invent no
    assert proposal["followup_questions"] == []
    assert CUSTOMER_MSG_DISABLED_ZH in proposal["customer_message_zh"]
    types = {e["event_type"] for e in list_ai_story_events_for_tests()}
    assert EVENT_DISABLED in types
    assert EVENT_FALLBACK in types


def test_missing_credentials_llm_falls_back_deterministic(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACCIDENT_STORY_ASSISTANT_ENABLED", "1")
    monkeypatch.setenv("ACCIDENT_STORY_LLM", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ACCIDENT_STORY_LLM_API_KEY", raising=False)
    proposal = propose_from_story(raw_story="昨天在 San Jose 停车场追尾，没有受伤。")
    assert proposal["injury_status"] == "no"
    assert proposal["used_fallback"] is True
    assert "追尾" in proposal["raw_story"] or proposal["raw_story"]


def test_timeout_injection_preserves_story_and_continues():
    def timeout_llm(_text: str) -> dict:
        raise TimeoutError("provider_timeout")

    result = propose_accident_story(
        raw_story="昨天在 San Jose 停车场追尾，没有受伤。",
        command_id="cmd_to_1",
        idempotency_key="idem_to_1",
        llm_caller=timeout_llm,
    )
    proposal = result["proposal"]
    assert proposal["used_fallback"] is True
    assert proposal["raw_story"]
    assert proposal["injury_status"] == "no"
    assert result["lifecycle_mutated"] is False
    assert "customer_message_zh" in proposal


def test_malformed_json_injection():
    def bad(_text: str) -> dict:
        raise ValueError("invalid_model_json")

    proposal = propose_from_story(
        raw_story="昨天在 Oakland 追尾，没有受伤。",
        llm_caller=bad,
    )
    assert proposal["used_fallback"] is True
    assert proposal["injury_status"] == "no"


def test_unexpected_exception_in_propose(monkeypatch: pytest.MonkeyPatch):
    def boom(*_a, **_k):
        raise RuntimeError("unexpected_internal")

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.accident_story_assistant.service.propose_from_story",
        boom,
    )
    result = propose_accident_story(
        raw_story="昨天追尾，没有受伤。",
        command_id="cmd_ex_1",
        idempotency_key="idem_ex_1",
    )
    assert result["ok"] is True
    assert result["proposal"]["used_fallback"] is True
    assert result["proposal"]["raw_story"].startswith("昨天")
    assert result["lifecycle_mutated"] is False


def test_hallucinated_injury_rejected_via_validate():
    from services.fiqa_api.inbox_triage.accident_story_assistant.extractors import (
        validate_model_proposals,
    )

    with pytest.raises(ValueError, match="hallucinated_fields"):
        validate_model_proposals({"coverage_decision": "liable", "injury_status": "no"})


def test_conflicting_injury_stays_unknown():
    proposal = propose_from_story(raw_story="有人受伤，同时没有受伤。昨天下午在 Oakland。")
    assert proposal["injury_status"] == "unknown"
    assert proposal["conflicts"]


def test_tracing_exception_does_not_break_intake(monkeypatch: pytest.MonkeyPatch):
    def bad_process(_inputs):
        raise RuntimeError("trace_boom")

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.accident_story_assistant.graph.process_traced_inputs",
        bad_process,
    )
    # Even if process_inputs raises at wrap time, propose must still work when tracing off.
    monkeypatch.setenv("ACCIDENT_STORY_LANGSMITH_TRACING", "0")
    proposal = propose_from_story(raw_story="昨天在停车场追尾，没有受伤。")
    assert proposal["injury_status"] == "no"
    assert "raw_story" in proposal


def test_duplicate_command_idempotent():
    r1 = propose_accident_story(
        raw_story="昨天追尾，没有受伤，在 San Jose。",
        command_id="cmd_dup_safety",
        idempotency_key="idem_dup_safety",
    )
    r2 = propose_accident_story(
        raw_story="昨天追尾，没有受伤，在 San Jose。",
        command_id="cmd_dup_safety",
        idempotency_key="idem_dup_safety",
    )
    assert r1["outcome"] == "accepted"
    assert r2["outcome"] == "replayed"


def test_office_allowlist_blocks(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ACCIDENT_STORY_ASSISTANT_ENABLED", "1")
    monkeypatch.setenv("ACCIDENT_STORY_OFFICE_ALLOWLIST", "office_alpha")
    result = propose_accident_story(
        raw_story="昨天追尾，没有受伤。",
        command_id="cmd_allow_1",
        idempotency_key="idem_allow_1",
        office_id="chen_kui",
    )
    assert result["proposal"]["used_fallback"] is True
    assert result["proposal"]["failure_category"] == "disabled"


def test_unknown_not_converted_to_no():
    proposal = propose_from_story(raw_story="昨天追尾，不确定有没有受伤。")
    assert proposal["injury_status"] == "unknown"


def test_metrics_exporter_non_sensitive():
    propose_accident_story(
        raw_story="昨天追尾，没有受伤。",
        command_id="cmd_met_1",
        idempotency_key="idem_met_1",
    )
    summary = summarize_pilot_metrics()
    blob = str(summary)
    assert "昨天追尾" not in blob
    assert summary["proposals_created"] >= 1
    assert summary["pii_policy"]


def test_trace_metadata_allowlist_only():
    meta = build_root_trace_metadata(
        state={"raw_story": "秘密内容", "injury_status": "no", "followup_questions": [], "missing_required_facts": []},
        scenario="unit",
        latency_ms=5,
    )
    assert set(meta.keys()) <= META_ALLOWLIST
    assert "秘密" not in str(meta)


def test_process_traced_inputs_strips_raw_story():
    from services.fiqa_api.inbox_triage.accident_story_assistant.tracing import (
        process_traced_inputs,
        process_traced_outputs,
    )

    marker = "LEAK_MARKER_RAW_STORY_TEXT"
    redacted_in = process_traced_inputs(
        {
            "raw_story": marker,
            "normalized_story": marker,
            "incident_summary": marker,
            "injury_status": "no",
            "proposed_facts": [{"key": "accident_description", "value": marker}],
        }
    )
    blob = str(redacted_in)
    assert marker not in blob
    assert redacted_in.get("redacted") is True
    assert redacted_in["state"]["injury_status"] == "no"

    redacted_out = process_traced_outputs(
        {"raw_story": marker, "injury_status": "unknown", "followup_questions": []}
    )
    assert marker not in str(redacted_out)
