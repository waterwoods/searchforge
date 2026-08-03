"""Typed contract for bounded accident-story LangGraph assistant (V1).

Persistence and Claim lifecycle stay outside the graph.
Customer confirmation is required before facts become authoritative.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

try:
    from typing import NotRequired  # py311+
except ImportError:  # pragma: no cover
    from typing_extensions import NotRequired  # type: ignore

SCHEMA_VERSION = 1

InjuryStatus = Literal["yes", "no", "unknown"]
FactAuthority = Literal["ai_proposed", "customer_confirmed", "broker_reviewed"]

MUST_HAVE_KEYS: tuple[str, ...] = (
    "accident_description",
    "accident_datetime",
    "accident_location",
    "injury_status",
)

ALLOWED_PROPOSAL_FIELDS: frozenset[str] = frozenset(
    {
        "incident_summary",
        "injury_status",
        "accident_time_text",
        "accident_location_text",
        "involved_parties",
        "involved_vehicles",
    }
)

FOLLOWUP_COPY: dict[str, str] = {
    "accident_datetime": "事故大概是什么时候发生的？",
    "accident_location": "事故发生在什么地点？",
    "injury_status": "有没有人受伤？（有 / 没有 / 不确定）",
    "accident_description": "请用一两句话补充事故经过。",
}


class ProposedFact(TypedDict, total=False):
    field_key: str
    value: str
    authority: FactAuthority
    confidence: float
    source: str


class AccidentStoryState(TypedDict, total=False):
    """LangGraph state — versioned, no PII beyond the story text the customer typed."""

    schema_version: int
    raw_story: str
    normalized_story: str
    incident_summary: str
    injury_status: InjuryStatus
    accident_time_text: str
    accident_location_text: str
    involved_parties: list[str]
    involved_vehicles: list[str]
    proposed_facts: list[ProposedFact]
    missing_required_facts: list[str]
    followup_questions: list[str]
    confidence_by_field: dict[str, float]
    warnings: list[str]
    model_provider: str
    model_name: str
    used_fallback: bool
    fallback_reason: str
    conflicts: list[str]
    command_id: str
    idempotency_key: str
    case_id: NotRequired[str]


class ConfirmationPayload(TypedDict, total=False):
    command_id: str
    idempotency_key: str
    case_id: str
    session_id: str
    raw_story: str
    incident_summary: str
    injury_status: InjuryStatus
    accident_time_text: str
    accident_location_text: str
    customer_edits: dict[str, Any]
    confirm: bool


def empty_state(*, raw_story: str = "", command_id: str = "", idempotency_key: str = "") -> AccidentStoryState:
    return {
        "schema_version": SCHEMA_VERSION,
        "raw_story": str(raw_story or ""),
        "normalized_story": "",
        "incident_summary": "",
        "injury_status": "unknown",
        "accident_time_text": "",
        "accident_location_text": "",
        "involved_parties": [],
        "involved_vehicles": [],
        "proposed_facts": [],
        "missing_required_facts": [],
        "followup_questions": [],
        "confidence_by_field": {},
        "warnings": [],
        "model_provider": "deterministic",
        "model_name": "rules_v1",
        "used_fallback": False,
        "fallback_reason": "",
        "conflicts": [],
        "command_id": command_id,
        "idempotency_key": idempotency_key,
    }


def public_proposal(state: AccidentStoryState) -> dict[str, Any]:
    """Customer/Broker-safe proposal view (no lifecycle mutation)."""
    return {
        "schema_version": int(state.get("schema_version") or SCHEMA_VERSION),
        "raw_story": str(state.get("raw_story") or ""),
        "incident_summary": str(state.get("incident_summary") or ""),
        "injury_status": str(state.get("injury_status") or "unknown"),
        "accident_time_text": str(state.get("accident_time_text") or ""),
        "accident_location_text": str(state.get("accident_location_text") or ""),
        "involved_parties": list(state.get("involved_parties") or []),
        "involved_vehicles": list(state.get("involved_vehicles") or []),
        "proposed_facts": list(state.get("proposed_facts") or []),
        "missing_required_facts": list(state.get("missing_required_facts") or []),
        "followup_questions": list(state.get("followup_questions") or [])[:3],
        "confidence_by_field": dict(state.get("confidence_by_field") or {}),
        "warnings": list(state.get("warnings") or []),
        "conflicts": list(state.get("conflicts") or []),
        "used_fallback": bool(state.get("used_fallback")),
        "fallback_reason": str(state.get("fallback_reason") or ""),
        "model_provider": str(state.get("model_provider") or ""),
        "model_name": str(state.get("model_name") or ""),
        "authority_note": "ai_proposed_until_customer_confirms",
    }
