"""Accident-story propose/confirm service — persistence outside LangGraph."""

from __future__ import annotations

import threading
from typing import Any

from services.fiqa_api.inbox_triage.accident_story_assistant.contract import public_proposal
from services.fiqa_api.inbox_triage.accident_story_assistant.graph import (
    propose_from_story,
    run_accident_story_graph,
)

_lock = threading.RLock()
_idempotency: dict[str, dict[str, Any]] = {}


def reset_accident_story_idempotency_for_tests() -> None:
    with _lock:
        _idempotency.clear()


def propose_accident_story(
    *,
    raw_story: str,
    command_id: str,
    idempotency_key: str,
    case_id: str | None = None,
    session_id: str | None = None,
    llm_caller: Any | None = None,
) -> dict[str, Any]:
    key = f"propose:{(idempotency_key or command_id).strip()}"
    with _lock:
        if key in _idempotency:
            cached = dict(_idempotency[key])
            cached["outcome"] = "replayed"
            return cached

    proposal = propose_from_story(
        raw_story=raw_story,
        command_id=command_id,
        idempotency_key=idempotency_key,
        llm_caller=llm_caller,
    )
    result = {
        "ok": True,
        "outcome": "accepted",
        "proposal": proposal,
        "case_id": str(case_id or "").strip() or None,
        "session_id_present": bool(str(session_id or "").strip()),
        "lifecycle_mutated": False,
    }
    with _lock:
        _idempotency[key] = dict(result)
    return result


def confirm_accident_story(
    *,
    case_id: str,
    command_id: str,
    idempotency_key: str,
    raw_story: str,
    confirm: bool,
    customer_edits: dict[str, Any] | None = None,
    proposal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply customer-confirmed facts to the case. Unconfirmed proposals never write.

    Does not change Claim lifecycle status, submit, or close.
    """
    cid = str(case_id or "").strip()
    if not cid:
        return {"ok": False, "outcome": "rejected", "error_code": "case_id_required"}
    if not confirm:
        return {
            "ok": True,
            "outcome": "accepted",
            "persisted": False,
            "authority": "ai_proposed",
            "note": "unconfirmed_proposal_not_authoritative",
            "lifecycle_mutated": False,
        }

    key = f"confirm:{(idempotency_key or command_id).strip()}:{cid}"
    with _lock:
        if key in _idempotency:
            cached = dict(_idempotency[key])
            cached["outcome"] = "replayed"
            return cached

    edits = customer_edits if isinstance(customer_edits, dict) else {}
    base = proposal if isinstance(proposal, dict) else public_proposal(
        run_accident_story_graph(raw_story=raw_story, command_id=command_id, idempotency_key=idempotency_key)
    )

    # Customer edits override AI proposal.
    summary = str(edits.get("incident_summary") or base.get("incident_summary") or raw_story or "").strip()
    injury = str(edits.get("injury_status") or base.get("injury_status") or "unknown").strip().lower()
    if injury not in ("yes", "no", "unknown"):
        injury = "unknown"
    time_text = str(edits.get("accident_time_text") or base.get("accident_time_text") or "").strip()
    location = str(
        edits.get("accident_location_text") or base.get("accident_location_text") or ""
    ).strip()
    story = str(edits.get("raw_story") or raw_story or base.get("raw_story") or "").strip()

    facts_patch: dict[str, str] = {}
    if story:
        facts_patch["accident_description"] = story[:2000]
    if summary:
        facts_patch["incident_summary"] = summary[:500]
    if time_text:
        facts_patch["accident_datetime"] = time_text[:120]
    if location:
        facts_patch["accident_location"] = location[:500]
    facts_patch["injury_status"] = injury
    facts_patch["anyone_injured"] = injury

    try:
        from services.fiqa_api.inbox_triage.case_store import (
            append_claim_timeline_event,
            build_claim_timeline_event,
            patch_case_known_facts,
        )

        updated = patch_case_known_facts(
            cid,
            facts_patch,
            source="customer_confirmed",
            status="customer_confirmed",
        )
        if updated is None:
            return {"ok": False, "outcome": "rejected", "error_code": "case_not_found"}

        # Provenance bag for Broker distinction.
        try:
            from services.fiqa_api.inbox_triage.case_store import (
                _load_case_for_mutation,
                _persist_case_after_update,
            )

            case = _load_case_for_mutation(cid)
            if isinstance(case, dict):
                provenance = (
                    dict(case.get("known_fact_provenance") or {})
                    if isinstance(case.get("known_fact_provenance"), dict)
                    else {}
                )
                for fk in facts_patch:
                    provenance[fk] = {
                        "authority": "customer_confirmed",
                        "prior_authority": "ai_proposed",
                        "assistant": "accident_story_langgraph_v1",
                        "command_id": command_id,
                    }
                case["known_fact_provenance"] = provenance
                case["accident_story_assistant"] = {
                    "schema_version": 1,
                    "last_confirmed_command_id": command_id,
                    "ai_involved": True,
                    "authority": "customer_confirmed",
                    "raw_story": story[:2000],
                    "incident_summary": summary[:500],
                }
                _persist_case_after_update(cid, case)
        except Exception:
            pass

        append_claim_timeline_event(
            cid,
            build_claim_timeline_event(
                event_type="customer_accident_story_confirmed",
                source_channel="mini_program",
                actor="customer",
                text="客户已确认事故经过结构化摘要",
                metadata={
                    "source": "accident_story_assistant",
                    "authority": "customer_confirmed",
                    "command_id": command_id,
                    "idempotency_key": idempotency_key,
                    "injury_status": injury,
                },
            ),
        )
    except Exception as exc:
        return {
            "ok": False,
            "outcome": "rejected",
            "error_code": "persist_failed",
            "detail": str(exc)[:200],
        }

    result = {
        "ok": True,
        "outcome": "accepted",
        "persisted": True,
        "authority": "customer_confirmed",
        "case_id": cid,
        "confirmed_fields": sorted(facts_patch.keys()),
        "lifecycle_mutated": False,
    }
    with _lock:
        _idempotency[key] = dict(result)
    return result
