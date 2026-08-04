"""LangSmith PR B — redaction + golden eval harness tests."""

from __future__ import annotations

import json
from pathlib import Path

from services.fiqa_api.inbox_triage.accident_story_assistant.evaluators import (
    run_evaluators,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.graph import (
    propose_from_story,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.tracing import (
    META_ALLOWLIST,
    build_root_trace_metadata,
    process_traced_inputs,
    redact_state_for_trace,
)

FIXTURE_DIR = Path("tests/fixtures/accident_story_langgraph")


def test_golden_fixture_count_at_least_15():
    files = list(FIXTURE_DIR.glob("*.json"))
    assert len(files) >= 15


def test_redaction_strips_raw_story():
    state = {
        "raw_story": "昨天开车的时候被追尾，没有受伤。电话 415-555-1212",
        "normalized_story": "昨天开车的时候被追尾，没有受伤。",
        "injury_status": "no",
        "missing_required_facts": ["accident_datetime"],
        "followup_questions": ["事故大约发生在几点？"],
        "command_id": "cmd_abcdef1234567890",
    }
    red = redact_state_for_trace(state)
    blob = json.dumps(red, ensure_ascii=False)
    assert "追尾" not in blob
    assert "415" not in blob
    assert red["story_char_len"] > 0
    assert red["injury_status"] == "no"
    assert "command_id_prefix" in red
    assert len(red["command_id_prefix"]) <= 12


def test_process_inputs_redacts_state():
    out = process_traced_inputs({"state": {"raw_story": "秘密故事内容不应出现"}})
    assert "秘密" not in json.dumps(out, ensure_ascii=False)


def test_root_metadata_allowlist_only():
    meta = build_root_trace_metadata(
        state={
            "raw_story": "秘密",
            "injury_status": "unknown",
            "missing_required_facts": ["injury_status"],
            "followup_questions": ["q"],
            "used_fallback": False,
            "model_provider": "deterministic",
            "model_name": "rules_v1",
            "command_id": "cmd_x",
        },
        scenario="unit",
        latency_ms=12,
    )
    assert set(meta.keys()) <= META_ALLOWLIST
    assert "秘密" not in json.dumps(meta, ensure_ascii=False)


def test_demo_fixture_evaluators_pass():
    fx = json.loads(
        (FIXTURE_DIR / "missing_time_location_injury_known.json").read_text(encoding="utf-8")
    )
    proposal = propose_from_story(raw_story=fx["raw_story"], scenario=fx["id"])
    results = run_evaluators(proposal, fx["expect"])
    assert all(r["ok"] for r in results), results
