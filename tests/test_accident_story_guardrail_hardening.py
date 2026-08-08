"""Fix 1/2/3 — injury evidence hard rule, server proposal authority, durable idempotency."""

from __future__ import annotations

import pytest

from services.fiqa_api.inbox_triage.accident_story_assistant.events import (
    reset_ai_story_events_for_tests,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.graph import propose_from_story
from services.fiqa_api.inbox_triage.accident_story_assistant.guardrails import (
    INJURY_LLM_UNSUPPORTED,
    enforce_injury_evidence_guardrail,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.persistence import (
    filter_customer_edits,
    load_proposal_record,
    reset_accident_story_ephemeral_for_tests,
    reset_accident_story_persistence_for_tests,
    store_proposal_record,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.service import (
    confirm_accident_story,
    propose_accident_story,
    reset_accident_story_ephemeral_idempotency_for_tests,
    reset_accident_story_idempotency_for_tests,
)


def setup_function() -> None:
    reset_accident_story_idempotency_for_tests()
    reset_ai_story_events_for_tests()


# ---------------------------------------------------------------------------
# Fix 1 — unknown injury after LLM merge
# ---------------------------------------------------------------------------


def test_llm_no_without_evidence_forced_unknown():
    def evil_llm(_text: str) -> dict:
        return {"injury_status": "no", "accident_location_text": "San Jose"}

    proposal = propose_from_story(raw_story="昨天被追尾。", llm_caller=evil_llm)
    assert proposal["injury_status"] == "unknown"
    assert "injury_status" in (proposal.get("missing_required_facts") or [])
    assert INJURY_LLM_UNSUPPORTED in (proposal.get("warnings") or [])
    # Useful non-injury LLM fields still merge.
    assert "San Jose" in str(proposal.get("accident_location_text") or "")


def test_llm_yes_without_evidence_forced_unknown():
    def evil_llm(_text: str) -> dict:
        return {"injury_status": "yes"}

    proposal = propose_from_story(raw_story="昨天开车的时候被追尾。", llm_caller=evil_llm)
    assert proposal["injury_status"] == "unknown"
    assert INJURY_LLM_UNSUPPORTED in (proposal.get("warnings") or [])


def test_explicit_no_with_matching_llm_allowed():
    def llm(_text: str) -> dict:
        return {"injury_status": "no"}

    proposal = propose_from_story(raw_story="昨天追尾，没有受伤。", llm_caller=llm)
    assert proposal["injury_status"] == "no"
    assert "injury_status" not in (proposal.get("missing_required_facts") or [])


def test_explicit_yes_with_matching_llm_allowed():
    def llm(_text: str) -> dict:
        return {"injury_status": "yes"}

    proposal = propose_from_story(raw_story="昨天追尾，有人受伤了。", llm_caller=llm)
    assert proposal["injury_status"] == "yes"


def test_conflict_hedge_stays_unknown_even_if_llm_says_no():
    def llm(_text: str) -> dict:
        return {"injury_status": "no"}

    proposal = propose_from_story(
        raw_story="有人受伤，同时没有受伤。昨天下午在 Oakland。",
        llm_caller=llm,
    )
    assert proposal["injury_status"] == "unknown"
    assert proposal.get("conflicts")


def test_complete_valid_story_regression():
    proposal = propose_from_story(
        raw_story="昨天下午3点在 San Jose 停车场追尾，没有受伤。",
    )
    assert proposal["injury_status"] == "no"
    assert proposal["accident_location_text"]
    assert "injury_status" not in (proposal.get("missing_required_facts") or [])


def test_enforce_injury_evidence_unit():
    status, conflicts, warns = enforce_injury_evidence_guardrail(
        source_text="昨天被追尾。",
        proposed_injury="no",
    )
    assert status == "unknown"
    assert INJURY_LLM_UNSUPPORTED in warns
    assert "injury_model_lacks_source_evidence" in conflicts


# ---------------------------------------------------------------------------
# Fix 2 — server proposal authority
# ---------------------------------------------------------------------------


def _fake_case_persist(monkeypatch: pytest.MonkeyPatch, case_id: str) -> dict:
    bag: dict = {"case_id": case_id, "known_facts": {}, "known_fact_provenance": {}}

    def patch_case_known_facts(cid, facts_patch, source="customer_confirmed", status="customer_confirmed"):
        if cid != case_id:
            return None
        bag["known_facts"].update(facts_patch)
        bag["source"] = source
        bag["status"] = status
        return dict(bag)

    def load(cid):
        return bag if cid == case_id else None

    def persist(cid, case):
        snapshot = dict(case)
        bag.clear()
        bag.update(snapshot)

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.patch_case_known_facts",
        patch_case_known_facts,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store._load_case_for_mutation",
        load,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store._persist_case_after_update",
        persist,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.append_claim_timeline_event",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.build_claim_timeline_event",
        lambda **k: k,
    )
    return bag


def test_confirm_uses_server_proposal_not_client_tamper(monkeypatch: pytest.MonkeyPatch):
    case_id = "case_server_auth_1"
    bag = _fake_case_persist(monkeypatch, case_id)
    proposed = propose_accident_story(
        raw_story="昨天被追尾。",
        command_id="cmd_srv_auth_1xxxxxxx",
        idempotency_key="idem_srv_auth_1xxxxxx",
    )
    pid = proposed["proposal_id"]
    assert proposed["proposal"]["injury_status"] == "unknown"

    # Client tampers: claims injury=no and invents coverage.
    tampered = dict(proposed["proposal"])
    tampered["injury_status"] = "no"
    tampered["coverage_decision"] = "liable"

    result = confirm_accident_story(
        case_id=case_id,
        command_id="cmd_srv_auth_conf_1xxx",
        idempotency_key="idem_srv_auth_conf_1xx",
        raw_story="昨天被追尾。",
        confirm=True,
        proposal_id=pid,
        proposal_version=1,
        proposal=tampered,
        customer_edits={},
    )
    assert result["ok"] is True
    assert result["persisted"] is True
    # AI draft layer came from server (unknown), not client tamper (no).
    assert bag["accident_story_assistant"]["layers"]["ai_draft"]["injury_status"] == "unknown"
    assert bag["known_facts"]["injury_status"] == "unknown"
    assert "coverage_decision" not in bag["known_facts"]


def test_customer_edit_allowlist_applied(monkeypatch: pytest.MonkeyPatch):
    case_id = "case_edit_allow_1"
    bag = _fake_case_persist(monkeypatch, case_id)
    proposed = propose_accident_story(
        raw_story="昨天被追尾。",
        command_id="cmd_edit_allow_1xxxxxx",
        idempotency_key="idem_edit_allow_1xxxxx",
    )
    result = confirm_accident_story(
        case_id=case_id,
        command_id="cmd_edit_allow_confxxxx",
        idempotency_key="idem_edit_allow_confxx",
        raw_story="昨天被追尾。",
        confirm=True,
        proposal_id=proposed["proposal_id"],
        customer_edits={
            "injury_status": "no",
            "accident_location_text": "Oakland",
            "coverage_decision": "liable",  # ignored
            "secret_field": "x",  # ignored
        },
    )
    assert result["ok"] is True
    assert bag["known_facts"]["injury_status"] == "no"
    assert bag["known_facts"]["accident_location"] == "Oakland"
    assert "coverage_decision" not in bag["known_facts"]
    assert "injury_status" in result["edited_field_names"]


def test_filter_customer_edits_drops_unknown_keys():
    cleaned = filter_customer_edits(
        {"injury_status": "YES", "coverage_decision": "liable", "accident_location_text": " SJ "}
    )
    assert cleaned == {"injury_status": "yes", "accident_location_text": "SJ"}


def test_stale_proposal_id_rejected(monkeypatch: pytest.MonkeyPatch):
    _fake_case_persist(monkeypatch, "case_stale_1")
    result = confirm_accident_story(
        case_id="case_stale_1",
        command_id="cmd_stale_1xxxxxxxxx",
        idempotency_key="idem_stale_1xxxxxxxx",
        raw_story="昨天被追尾。",
        confirm=True,
        proposal_id="asp_does_not_exist_zzzz",
        proposal_version=1,
    )
    assert result["ok"] is False
    assert result["error_code"] == "proposal_not_found_or_expired"


def test_proposal_from_other_case_rejected(monkeypatch: pytest.MonkeyPatch):
    _fake_case_persist(monkeypatch, "case_b")
    stored = store_proposal_record(
        proposal={
            "raw_story": "昨天追尾，没有受伤。",
            "injury_status": "no",
            "proposal_version": 1,
            "incident_summary": "x",
            "followup_questions": [],
        },
        case_id="case_a",
    )
    pid = stored["proposal_id"]
    record = load_proposal_record(pid)
    assert record and record["case_id"] == "case_a"

    result = confirm_accident_story(
        case_id="case_b",
        command_id="cmd_case_mismatch_xxxx",
        idempotency_key="idem_case_mismatch_xxx",
        raw_story="昨天追尾，没有受伤。",
        confirm=True,
        proposal_id=pid,
    )
    assert result["ok"] is False
    assert result["error_code"] == "proposal_case_mismatch"


def test_confirm_replay_safe(monkeypatch: pytest.MonkeyPatch):
    case_id = "case_replay_conf_1"
    bag = _fake_case_persist(monkeypatch, case_id)
    proposed = propose_accident_story(
        raw_story="昨天追尾，没有受伤。",
        command_id="cmd_replay_conf_pxxxxxx",
        idempotency_key="idem_replay_conf_pxxxxx",
    )
    kwargs = dict(
        case_id=case_id,
        command_id="cmd_replay_conf_cxxxxxx",
        idempotency_key="idem_replay_conf_cxxxxx",
        raw_story="昨天追尾，没有受伤。",
        confirm=True,
        proposal_id=proposed["proposal_id"],
        customer_edits={"injury_status": "no"},
    )
    r1 = confirm_accident_story(**kwargs)
    r2 = confirm_accident_story(**kwargs)
    assert r1["ok"] and r1["outcome"] == "accepted"
    assert r2["outcome"] == "replayed"
    assert bag["known_facts"]["injury_status"] == "no"


# ---------------------------------------------------------------------------
# Fix 3 — durable idempotency
# ---------------------------------------------------------------------------


def test_propose_same_process_replay():
    r1 = propose_accident_story(
        raw_story="昨天追尾，没有受伤。",
        command_id="cmd_idem_same_1xxxxxx",
        idempotency_key="idem_idem_same_1xxxxx",
    )
    r2 = propose_accident_story(
        raw_story="昨天追尾，没有受伤。",
        command_id="cmd_idem_same_1xxxxxx",
        idempotency_key="idem_idem_same_1xxxxx",
    )
    assert r1["outcome"] == "accepted"
    assert r2["outcome"] == "replayed"
    assert r1["proposal_id"] == r2["proposal_id"]


def test_propose_survives_ephemeral_clear():
    r1 = propose_accident_story(
        raw_story="昨天追尾，没有受伤。",
        command_id="cmd_idem_dur_1xxxxxxx",
        idempotency_key="idem_idem_dur_1xxxxxx",
    )
    reset_accident_story_ephemeral_idempotency_for_tests()
    r2 = propose_accident_story(
        raw_story="昨天追尾，没有受伤。",
        command_id="cmd_idem_dur_1xxxxxxx",
        idempotency_key="idem_idem_dur_1xxxxxx",
    )
    assert r2["outcome"] == "replayed"
    assert r2["proposal_id"] == r1["proposal_id"]


def test_propose_second_instance_simulation():
    """Clear ephemeral cache; durable memory acts as shared store across 'instances'."""
    r1 = propose_accident_story(
        raw_story="昨天追尾，没有受伤，在 Oakland。",
        command_id="cmd_idem_inst_1xxxxxx",
        idempotency_key="idem_idem_inst_1xxxxx",
    )
    reset_accident_story_ephemeral_for_tests()
    r2 = propose_accident_story(
        raw_story="昨天追尾，没有受伤，在 Oakland。",
        command_id="cmd_idem_inst_1xxxxxx",
        idempotency_key="idem_idem_inst_1xxxxx",
    )
    assert r2["outcome"] == "replayed"
    assert r1["proposal"]["injury_status"] == r2["proposal"]["injury_status"]


def test_idempotency_key_payload_mismatch_conflicts():
    propose_accident_story(
        raw_story="昨天追尾，没有受伤。",
        command_id="cmd_idem_conflict_1xxxx",
        idempotency_key="idem_idem_conflict_1xx",
    )
    conflict = propose_accident_story(
        raw_story="完全不同的故事，今天侧撞。",
        command_id="cmd_idem_conflict_1xxxx",
        idempotency_key="idem_idem_conflict_1xx",
    )
    assert conflict["ok"] is False
    assert conflict["error_code"] == "idempotency_key_conflict"


def test_duplicate_confirm_does_not_double_write(monkeypatch: pytest.MonkeyPatch):
    case_id = "case_dup_conf_1"
    writes = {"n": 0}

    def patch_case_known_facts(cid, facts_patch, source="customer_confirmed", status="customer_confirmed"):
        writes["n"] += 1
        return {"case_id": cid, "known_facts": dict(facts_patch)}

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.patch_case_known_facts",
        patch_case_known_facts,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store._load_case_for_mutation",
        lambda cid: {"case_id": cid},
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store._persist_case_after_update",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.append_claim_timeline_event",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.build_claim_timeline_event",
        lambda **k: k,
    )

    proposed = propose_accident_story(
        raw_story="昨天追尾，没有受伤。",
        command_id="cmd_dup_conf_pxxxxxxxx",
        idempotency_key="idem_dup_conf_pxxxxxxx",
    )
    kwargs = dict(
        case_id=case_id,
        command_id="cmd_dup_conf_cxxxxxxxx",
        idempotency_key="idem_dup_conf_cxxxxxxx",
        raw_story="昨天追尾，没有受伤。",
        confirm=True,
        proposal_id=proposed["proposal_id"],
    )
    assert confirm_accident_story(**kwargs)["outcome"] == "accepted"
    assert confirm_accident_story(**kwargs)["outcome"] == "replayed"
    assert writes["n"] == 1
