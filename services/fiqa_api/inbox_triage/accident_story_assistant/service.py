"""Accident-story propose/confirm service — persistence outside LangGraph."""

from __future__ import annotations

import threading
import time
from typing import Any

from services.fiqa_api.inbox_triage.accident_story_assistant.contract import public_proposal
from services.fiqa_api.inbox_triage.accident_story_assistant.events import (
    EVENT_ACCEPTED,
    EVENT_CREATED,
    EVENT_EDITED,
    EVENT_FALLBACK,
    EVENT_REJECTED,
    emit_ai_story_event,
    fallback_reason_category,
    timed_ms,
)
from services.fiqa_api.inbox_triage.accident_story_assistant.graph import (
    propose_from_story,
    run_accident_story_graph,
)

_lock = threading.RLock()
_idempotency: dict[str, dict[str, Any]] = {}


def reset_accident_story_idempotency_for_tests() -> None:
    with _lock:
        _idempotency.clear()


def _proposal_event_meta(proposal: dict[str, Any], *, latency_ms: int | None = None) -> dict[str, Any]:
    guided = proposal.get("guided_view") if isinstance(proposal.get("guided_view"), dict) else {}
    return {
        "proposal_version": int(proposal.get("proposal_version") or 1),
        "question_count": len(list(proposal.get("followup_questions") or [])[:3]),
        "missing_count": int(guided.get("missing_count") or len(proposal.get("missing_required_facts") or [])),
        "used_fallback": bool(proposal.get("used_fallback")),
        "fallback_reason_category": fallback_reason_category(str(proposal.get("fallback_reason") or "")),
        "latency_ms": latency_ms,
        "model_provider": str(proposal.get("model_provider") or "")[:64],
        "model_name": str(proposal.get("model_name") or "")[:64],
        "command_id_prefix": "story",
    }


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

    started = time.monotonic()
    proposal = propose_from_story(
        raw_story=raw_story,
        command_id=command_id,
        idempotency_key=idempotency_key,
        llm_caller=llm_caller,
    )
    latency = timed_ms(started)
    meta = _proposal_event_meta(proposal, latency_ms=latency)
    emit_ai_story_event(EVENT_CREATED, case_id=case_id, meta=meta)
    if proposal.get("used_fallback"):
        emit_ai_story_event(EVENT_FALLBACK, case_id=case_id, meta=meta)

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


def _edited_field_names(base: dict[str, Any], edits: dict[str, Any]) -> list[str]:
    names: list[str] = []
    mapping = {
        "incident_summary": "incident_summary",
        "injury_status": "injury_status",
        "accident_time_text": "accident_datetime",
        "accident_location_text": "accident_location",
        "raw_story": "accident_description",
    }
    for edit_key, field_name in mapping.items():
        if edit_key not in edits:
            continue
        new_val = str(edits.get(edit_key) or "").strip()
        old_val = str(base.get(edit_key) or "").strip()
        if new_val and new_val != old_val:
            names.append(field_name)
    return names


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
        emit_ai_story_event(
            EVENT_REJECTED,
            case_id=cid,
            meta={"authority": "ai_proposed", "proposal_version": 1},
        )
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
    edited_names = _edited_field_names(base, edits)

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

    questions_asked = list(base.get("followup_questions") or [])[:3]
    customer_answers = {
        "accident_datetime": time_text[:120],
        "accident_location": location[:500],
        "injury_status": injury,
    }

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

        # Provenance bag for Broker distinction — three explicit layers.
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
                    "proposal_version": int(base.get("proposal_version") or 1),
                    "last_confirmed_command_id": command_id,
                    "ai_involved": True,
                    "authority": "customer_confirmed",
                    "layers": {
                        "customer_raw": {
                            "label_zh": "客户原始描述",
                            "text": story[:2000],
                        },
                        "ai_draft": {
                            "label_zh": "AI整理草稿",
                            "incident_summary": str(base.get("incident_summary") or "")[:500],
                            "accident_time_text": str(base.get("accident_time_text") or "")[:120],
                            "accident_location_text": str(base.get("accident_location_text") or "")[:500],
                            "injury_status": str(base.get("injury_status") or "unknown"),
                            "followup_questions": questions_asked,
                            "used_fallback": bool(base.get("used_fallback")),
                            "authority": "ai_proposed",
                        },
                        "customer_confirmed": {
                            "label_zh": "客户已确认事实",
                            "incident_summary": summary[:500],
                            "accident_time_text": time_text[:120],
                            "accident_location_text": location[:500],
                            "injury_status": injury,
                            "edited_field_names": edited_names,
                            "customer_answers": customer_answers,
                            "authority": "customer_confirmed",
                        },
                    },
                    "raw_story": story[:2000],
                    "incident_summary": summary[:500],
                    "questions_asked": questions_asked,
                    "edited_field_names": edited_names,
                    "used_fallback": bool(base.get("used_fallback")),
                    "fallback_reason_category": fallback_reason_category(
                        str(base.get("fallback_reason") or "")
                    ),
                    # Technical detail only — not primary Broker UI.
                    "tech": {
                        "model_provider": str(base.get("model_provider") or ""),
                        "model_name": str(base.get("model_name") or ""),
                    },
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
                    "edited_field_count": len(edited_names),
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

    event_meta = {
        "proposal_version": int(base.get("proposal_version") or 1),
        "question_count": len(questions_asked),
        "edited_field_names": edited_names,
        "authority": "customer_confirmed",
        "used_fallback": bool(base.get("used_fallback")),
        "fallback_reason_category": fallback_reason_category(str(base.get("fallback_reason") or "")),
        "model_provider": str(base.get("model_provider") or "")[:64],
        "model_name": str(base.get("model_name") or "")[:64],
    }
    if edited_names:
        emit_ai_story_event(EVENT_EDITED, case_id=cid, meta=event_meta)
    emit_ai_story_event(EVENT_ACCEPTED, case_id=cid, meta=event_meta)

    result = {
        "ok": True,
        "outcome": "accepted",
        "persisted": True,
        "authority": "customer_confirmed",
        "case_id": cid,
        "confirmed_fields": sorted(facts_patch.keys()),
        "edited_field_names": edited_names,
        "lifecycle_mutated": False,
    }
    with _lock:
        _idempotency[key] = dict(result)
    return result
