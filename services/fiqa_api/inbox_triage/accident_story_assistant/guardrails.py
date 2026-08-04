"""Safety guardrails for accident-story proposals (no claim lifecycle writes)."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.accident_story_assistant.contract import (
    FOLLOWUP_COPY,
    MUST_HAVE_KEYS,
    AccidentStoryState,
    ProposedFact,
    time_needs_refinement,
)


def derive_missing_facts(state: AccidentStoryState) -> list[str]:
    missing: list[str] = []
    story = str(state.get("normalized_story") or state.get("raw_story") or "").strip()
    if not story:
        missing.append("accident_description")
    time_text = str(state.get("accident_time_text") or "").strip()
    # Bare "昨天/今天" still needs a more specific clock/period answer.
    if time_needs_refinement(time_text):
        missing.append("accident_datetime")
    if not str(state.get("accident_location_text") or "").strip():
        missing.append("accident_location")
    injury = str(state.get("injury_status") or "unknown")
    # unknown is a genuine gap for Must Have injury; yes/no are answered.
    if injury not in ("yes", "no"):
        missing.append("injury_status")
    # Preserve order of Must Haves.
    order = {k: i for i, k in enumerate(MUST_HAVE_KEYS)}
    return sorted(missing, key=lambda k: order.get(k, 99))


def draft_followup_questions(missing: list[str], *, max_questions: int = 3) -> list[str]:
    questions: list[str] = []
    for key in missing:
        q = FOLLOWUP_COPY.get(key)
        if q and q not in questions:
            questions.append(q)
        if len(questions) >= max_questions:
            break
    return questions[:max_questions]


def apply_safety_guardrails(state: AccidentStoryState) -> AccidentStoryState:
    """Clamp questions, preserve uncertainty, never invent missing facts."""
    out = dict(state)
    injury = str(out.get("injury_status") or "unknown").lower()
    if injury not in ("yes", "no", "unknown"):
        out["injury_status"] = "unknown"
        warns = list(out.get("warnings") or [])
        warns.append("invalid_injury_coerced_to_unknown")
        out["warnings"] = warns
    # Never convert unknown → no.
    if injury == "unknown":
        out["injury_status"] = "unknown"

    missing = derive_missing_facts(out)  # type: ignore[arg-type]
    out["missing_required_facts"] = missing
    out["followup_questions"] = draft_followup_questions(missing, max_questions=3)

    # Strip empty proposed values — do not fabricate.
    facts: list[ProposedFact] = []
    for fact in list(out.get("proposed_facts") or []):
        if not isinstance(fact, dict):
            continue
        val = str(fact.get("value") or "").strip()
        key = str(fact.get("field_key") or "").strip()
        if not key or not val:
            continue
        if key == "injury_status" and val == "unknown" and "injury_status" in missing:
            # Keep unknown visible but mark low confidence.
            fact = {**fact, "confidence": min(float(fact.get("confidence") or 0.3), 0.3)}
        facts.append(fact)  # type: ignore[arg-type]
    out["proposed_facts"] = facts
    out["followup_questions"] = list(out.get("followup_questions") or [])[:3]
    return out  # type: ignore[return-value]


def build_confirmation_proposal(state: AccidentStoryState) -> AccidentStoryState:
    """Final customer-facing proposal package (still ai_proposed authority)."""
    out = apply_safety_guardrails(state)
    if not str(out.get("incident_summary") or "").strip():
        out["incident_summary"] = str(out.get("normalized_story") or out.get("raw_story") or "")[:500]
    return out
