"""
Assist Layer — post-truth, non-mutating suggestions for Unified Intake.

Reads triage/truth output only; never writes structured truth or readiness.
Canonical Add-Car field ids match PILOT_CONTRACT_ADD_CAR_V1 / add_car_stage1_field_contract.json.
"""
from __future__ import annotations

import json
import logging
import os
import re
from copy import deepcopy
from typing import Any

logger = logging.getLogger(__name__)

ASSIST_SYSTEM_PROMPT = """You are the Assist Layer for a production-grade insurance intake system.

Your job is NOT to extract truth.
Your job is NOT to modify stored structured fields.
Your job is NOT to decide final readiness.

Your job is to read the existing triage/truth result and generate safe, helpful, human-like assistance.

You operate AFTER truth extraction.

## CORE CONTRACT

You will receive:
1. latest customer message
2. current structured truth result
3. missing required fields (canonical API field ids only)
4. readiness / handoff signals
5. optional prior case context for the SAME case only

You must NEVER:
- write new truth values
- overwrite existing structured fields
- upgrade guesses into facts
- mark missing fields as complete
- change readiness state
- tell the customer the case is ready for quote or handoff unless quote_ready_status is quote_ready AND handoff_ready is true (and triage_mode is greenfield)

You may ONLY:
- suggest what to clarify next
- rephrase next-step guidance
- propose confirmation wording
- identify ambiguity for human follow-up

## PRIMARY GOAL

Make the system feel helpful and natural WITHOUT contaminating truth.

Think:
- truth stays strict
- assist becomes human
- minimize back-and-forth
- move the case toward submission efficiently

## CRITICAL STRATEGY — MISSING FIELD COVERAGE

If MULTIPLE required fields are missing:

→ You MUST ask for ALL critical missing fields in ONE message.

Do NOT ask only one field if several are still needed.

However:
- keep it natural and conversational
- group related items
- do NOT sound like a checklist robot

## REQUIRED FIELD PRIORITY (ADD-CAR)

Always prioritize these fields when missing (use field keys from missing_required_fields when present; these are canonical ids):

1. vin
2. delivery_date (coverage start / pickup — one slot; use calendar date wording when asking)
3. zip (California garaging ZIP)
4. primary_driver

If more than one of these is missing:
→ include ALL of them in your suggested_question (and align customer_facing_rephrase).

## HARD RULES

- Never output a guessed structured field value as fact
- Never say a case is ready if quote_ready_status is not quote_ready or handoff_ready is false (when triage_mode is greenfield)
- Never infer ZIP/VIN/date/driver identity from vague references
- Never use context from another case

## AMBIGUITY POLICY

If the customer says something vague, relative, or conflicting:

Examples:
- "next Monday"
- "today"
- "same as my other car"
- "my wife drives mostly"
- "I think zip is 91789 or 91790"
- "maybe this VIN"

Then:

- mark clarification_needed = true
- explain briefly why
- ask ONE clear follow-up question that still includes ALL required missing fields when applicable
- optionally provide candidate_interpretation as suggestion only (clearly non-binding)

## RELATIVE DATE POLICY

When customer uses:
- today
- tomorrow
- next Monday

You must:
- NOT convert to a concrete date
- request explicit date (MM/DD/YYYY)

## DRIVER POLICY

If customer gives role-based driver:

Examples:
- me
- my wife
- mostly me
- both of us

Then:
- treat as ambiguous unless already resolved in truth
- ask who should be listed as PRIMARY driver
- if needed, request full legal name

## CONTEXT TRAP POLICY

If customer says:
- "same as my other car"
- "you already have it"

You must:
- NOT assume any prior data
- explicitly request required fields again

You may read same-case context only to improve phrasing. You must NOT silently carry persisted facts into truth or treat context as newly confirmed.

## STYLE

Be:
- concise
- natural
- broker-friendly
- efficient

Avoid:
- robotic checklist tone
- overly long sentences
- repeating the same phrasing

## OUTPUT FORMAT

Return ONLY valid JSON with exactly these keys:

{
  "clarification_needed": true,
  "clarification_reason": "short reason or none",
  "suggested_question": "one natural question covering all key missing info",
  "candidate_interpretation": "short optional suggestion or none",
  "broker_note": "short operational note",
  "customer_facing_rephrase": "one clean natural sentence"
}

## EXAMPLES

Example 1 — context trap, multiple missing:

Input message: "same as my other car"
Missing: vin, zip, primary_driver

Good output shape:
- clarification_needed true; reason references reference to another vehicle without this car's details
- suggested_question asks for this car's VIN, garaging ZIP, and primary driver in one natural sentence
- broker_note: do not auto-fill from another vehicle record

Example 2 — relative date:

Input: "start next Monday"
Missing: delivery_date

Good output:
- ask for exact start date as MM/DD/YYYY; do not write a calendar date in candidate_interpretation as fact

Example 3 — driver ambiguity:

Input: "my wife drives mostly"
Missing: primary_driver

Good output:
- who should be listed as primary driver; full legal name if needed

## FINAL RULE

If there is any tension:
→ prefer completeness of missing fields
→ without breaking truth safety"""

DEFAULT_ASSIST: dict[str, Any] = {
    "clarification_needed": False,
    "clarification_reason": "none",
    "suggested_question": "none",
    "candidate_interpretation": "none",
    "broker_note": "none",
    "customer_facing_rephrase": "none",
}

_ASSIST_KEYS = (
    "clarification_needed",
    "clarification_reason",
    "suggested_question",
    "candidate_interpretation",
    "broker_note",
    "customer_facing_rephrase",
)

# Canonical Add-Car pilot slots (same ids as collected_fields / still_needed_fields).
_ADD_CAR_CRITICAL_ASSIST_ORDER: tuple[str, ...] = (
    "vin",
    "delivery_date",
    "zip",
    "primary_driver",
)
_ADD_CAR_STRUCTURAL_HINTS: frozenset[str] = frozenset(
    {
        "year",
        "make_model",
        "zip",
        "delivery_date",
        "primary_driver",
        "vin",
        "name",
        "phone",
    }
)


def _canonical_still_needed_id(raw: str) -> str:
    """Map legacy API ids to contract ids (CASE_CONTRACT_V1: make_model, not model)."""
    s = (raw or "").strip()
    if s.lower() == "model":
        return "make_model"
    return s


def _assist_add_car_context(triage_result: dict[str, Any], still_needed: list[str]) -> bool:
    if str(triage_result.get("service_type") or "").strip().lower() == "add_car":
        return True
    return any(str(x).strip().lower() in _ADD_CAR_STRUCTURAL_HINTS for x in still_needed)


def _slot_filled(collected_lower: set[str], field_id: str) -> bool:
    return str(field_id).strip().lower() in collected_lower


def _missing_required_fields_for_assist(triage_result: dict[str, Any]) -> list[str]:
    """Union of triage still_needed_fields and critical Add-Car slots (canonical ids)."""
    still = [str(x).strip() for x in (triage_result.get("still_needed_fields") or []) if str(x).strip()]
    if not _assist_add_car_context(triage_result, still):
        return still

    collected_lower = {str(x).strip().lower() for x in (triage_result.get("collected_fields") or []) if x}
    seen: set[str] = set()
    out: list[str] = []

    for fid in _ADD_CAR_CRITICAL_ASSIST_ORDER:
        seen.add(fid)
        if _slot_filled(collected_lower, fid):
            continue
        out.append(fid)

    for raw in still:
        canon = _canonical_still_needed_id(raw)
        key = canon.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(canon)

    return out


def _assist_layer_enabled() -> bool:
    return os.environ.get("ENABLE_ASSIST_LAYER", "").strip().lower() in ("1", "true", "yes", "on")


def _truth_snapshot(triage_result: dict[str, Any]) -> dict[str, Any]:
    """Subset of triage result safe to pass to the assist model (already-public API fields)."""
    keys = (
        "issue_category",
        "urgency",
        "collected_fields",
        "still_needed_fields",
        "handoff_ready",
        "quote_ready_status",
        "lifecycle_status",
        "collection_stage",
        "triage_mode",
        "next_best_question",
        "client_reply_draft",
        "broker_next_step",
        "conversation_summary",
        "manual_followup_needed",
        "human_confirmation_required",
        "human_confirmation_fields",
        "service_type",
        "vehicle_key",
        "primary_vehicle_summary",
        "case_creation_suggested",
    )
    out: dict[str, Any] = {}
    for k in keys:
        if k in triage_result:
            out[k] = triage_result[k]
    return out


def _context_snapshot(reply_truth_context: dict[str, Any] | None) -> dict[str, Any] | None:
    if not reply_truth_context:
        return None
    allow = (
        "formal_submitted_at",
        "lifecycle_status",
        "persisted_collected_fields",
        "still_needed_fields",
        "persisted_quote_ready_status",
        "service_record_continuation",
        "formal_submit_this_turn",
        "service_record_append",
        "record_contact_name",
        "record_contact_phone",
    )
    out = {k: reply_truth_context[k] for k in allow if k in reply_truth_context}
    return out or None


def _normalize_assist_dict(raw: dict[str, Any] | None) -> dict[str, Any]:
    out = deepcopy(DEFAULT_ASSIST)
    if not raw:
        return out
    cn = raw.get("clarification_needed")
    if isinstance(cn, str):
        out["clarification_needed"] = cn.strip().lower() in ("true", "1", "yes")
    else:
        out["clarification_needed"] = bool(cn)
    for k in _ASSIST_KEYS:
        if k == "clarification_needed":
            continue
        v = raw.get(k)
        if v is None:
            continue
        s = str(v).strip()
        out[k] = s if s else "none"
    return out


def _parse_json_object(content: str) -> dict[str, Any] | None:
    if not content:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", content)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            return None
    return None


def build_assist_layer(
    latest_message: str,
    triage_result: dict[str, Any],
    reply_truth_context: dict[str, Any] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Produce assist-only suggestions from the latest message and current triage (truth) result.

    Does not mutate triage_result. Safe default when disabled, no API key, or on failure.
    """
    if not _assist_layer_enabled():
        return deepcopy(DEFAULT_ASSIST)

    try:
        from services.fiqa_api.clients import get_openai_client
    except Exception as e:
        logger.debug("Assist layer: client import failed: %s", e)
        return deepcopy(DEFAULT_ASSIST)

    client = get_openai_client()
    if client is None:
        return deepcopy(DEFAULT_ASSIST)

    resolved_model = (model or "").strip() or os.environ.get("ASSIST_LAYER_MODEL", "").strip()
    if not resolved_model:
        resolved_model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    payload = {
        "latest_customer_message": (latest_message or "").strip()[:4000],
        "structured_truth_result": _truth_snapshot(triage_result),
        "missing_required_fields": _missing_required_fields_for_assist(triage_result),
        "readiness_handoff_signals": {
            "handoff_ready": triage_result.get("handoff_ready"),
            "quote_ready_status": triage_result.get("quote_ready_status"),
            "lifecycle_status": triage_result.get("lifecycle_status"),
            "collection_stage": triage_result.get("collection_stage"),
            "triage_mode": triage_result.get("triage_mode"),
        },
        "same_case_context_only": _context_snapshot(reply_truth_context),
    }
    user_content = json.dumps(payload, ensure_ascii=False, default=str)

    try:
        response = client.chat.completions.create(
            model=resolved_model,
            messages=[
                {"role": "system", "content": ASSIST_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
        text = ""
        if response.choices:
            text = (response.choices[0].message.content or "").strip()
        parsed = _parse_json_object(text)
        normalized = _normalize_assist_dict(parsed if isinstance(parsed, dict) else None)
        return normalized
    except Exception as e:
        logger.warning("Assist layer LLM call failed, using default: %s", e)
        return deepcopy(DEFAULT_ASSIST)
