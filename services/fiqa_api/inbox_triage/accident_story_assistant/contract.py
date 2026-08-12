"""Typed contract for bounded accident-story LangGraph assistant (V1).

Persistence and Claim lifecycle stay outside the graph.
Customer confirmation is required before facts become authoritative.
"""

from __future__ import annotations

import re
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
    "accident_datetime": "事故大约发生在几点？",
    "accident_location": "事故发生在哪里？",
    "injury_status": "有没有人受伤？（有 / 没有 / 不确定）",
    "accident_description": "请用一两句话补充事故经过。",
}

# Relative day-only phrases still need a clock/period follow-up for demo clarity.
VAGUE_TIME_ONLY: frozenset[str] = frozenset(
    {"昨天", "今天", "前天", "yesterday", "today"}
)

FIELD_INPUT_KIND: dict[str, str] = {
    "accident_datetime": "text",
    "accident_location": "text",
    "injury_status": "injury",
    "accident_description": "textarea",
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


def time_needs_refinement(time_text: str) -> bool:
    """True when extracted time is absent, a placeholder, or a bare relative day."""
    from services.fiqa_api.inbox_triage.accident_story_assistant.extractors import (
        is_sentinel_text,
    )

    t = str(time_text or "").strip().lower()
    if not t or is_sentinel_text(t):
        return True
    return t in {x.lower() for x in VAGUE_TIME_ONLY}


def extract_accident_type_label(raw_story: str) -> str:
    text = str(raw_story or "")
    mapping = (
        ("追尾", "追尾"),
        ("侧撞", "侧撞"),
        ("剐蹭", "剐蹭"),
        ("撞到", "碰撞"),
        ("rear[- ]?end", "追尾"),
        ("side[- ]?swipe", "剐蹭"),
    )
    for pat, label in mapping:
        if re.search(pat, text, re.I):
            return label
    return ""


def build_guided_customer_view(state: AccidentStoryState) -> dict[str, Any]:
    """Customer-visible guided panel contract (AI draft until confirm)."""
    raw = str(state.get("raw_story") or "")
    time_text = str(state.get("accident_time_text") or "").strip()
    location = str(state.get("accident_location_text") or "").strip()
    injury = str(state.get("injury_status") or "unknown").strip().lower()
    accident_type = extract_accident_type_label(raw) or extract_accident_type_label(
        str(state.get("normalized_story") or "")
    )
    missing = list(state.get("missing_required_facts") or [])
    questions = list(state.get("followup_questions") or [])[:3]
    conflicts = list(state.get("conflicts") or [])

    def _time_display() -> tuple[str, str]:
        from services.fiqa_api.inbox_triage.accident_story_assistant.extractors import (
            is_sentinel_text,
        )

        if not time_text or is_sentinel_text(time_text):
            return "待确认", "pending"
        if time_needs_refinement(time_text) and "accident_datetime" in missing:
            return f"{time_text}，具体时间待确认", "partial"
        return time_text, "known"

    def _injury_display() -> tuple[str, str]:
        if injury == "no":
            return "没有受伤", "known"
        if injury == "yes":
            return "有人受伤", "known"
        return "待确认", "pending"

    time_zh, time_status = _time_display()
    injury_zh, injury_status = _injury_display()
    loc_zh, loc_status = (location, "known") if location else ("待确认", "pending")
    type_zh, type_status = (accident_type, "known") if accident_type else ("待确认", "pending")

    summary = str(state.get("incident_summary") or "").strip()
    if not summary:
        summary = str(state.get("normalized_story") or raw or "").strip()
        if len(summary) > 48:
            summary = summary[:48] + "…"
    what_zh, what_status = (summary, "known") if summary else ("待确认", "pending")

    vehicles = [str(v).strip() for v in list(state.get("involved_vehicles") or []) if str(v).strip()]
    parties = [str(p).strip() for p in list(state.get("involved_parties") or []) if str(p).strip()]
    involved_bits = [*vehicles[:3], *parties[:2]]
    if involved_bits:
        involved_zh, involved_status = ("、".join(involved_bits), "known")
    else:
        involved_zh, involved_status = ("待确认", "pending")

    fact_rows = [
        {"key": "what_happened", "label_zh": "发生了什么", "value_zh": what_zh, "status": what_status},
        {"key": "accident_type", "label_zh": "事故类型", "value_zh": type_zh, "status": type_status},
        {"key": "accident_datetime", "label_zh": "事故时间", "value_zh": time_zh, "status": time_status},
        {"key": "accident_location", "label_zh": "事故地点", "value_zh": loc_zh, "status": loc_status},
        {"key": "involved", "label_zh": "涉及车辆/人员", "value_zh": involved_zh, "status": involved_status},
        {"key": "injury_status", "label_zh": "受伤情况", "value_zh": injury_zh, "status": injury_status},
    ]

    followup_fields: list[dict[str, str]] = []
    for key in missing[:3]:
        q = FOLLOWUP_COPY.get(key)
        if not q:
            continue
        followup_fields.append(
            {
                "field_key": key,
                "question_zh": q,
                "input_kind": FIELD_INPUT_KIND.get(key, "text"),
                "form_key": {
                    "accident_datetime": "accidentDatetime",
                    "accident_location": "accidentLocation",
                    "injury_status": "injuryStatus",
                    "accident_description": "description",
                }.get(key, key),
            }
        )

    missing_count = len(followup_fields)
    if missing_count:
        missing_message = f"还需要确认 {missing_count} 项"
    else:
        missing_message = "信息已齐，请确认"

    return {
        "title_zh": "AI已帮您整理",
        "draft_label_zh": "AI草稿，尚未确认",
        "fact_rows": fact_rows,
        "missing_count": missing_count,
        "missing_message_zh": missing_message,
        "followup_questions": questions[:3],
        "followup_fields": followup_fields,
        "conflicts": conflicts,
        "conflict_message_zh": "以下信息有冲突，请确认" if conflicts else "",
        "show_full_form_option": True,
        "full_form_option_zh": "查看或修改全部信息",
        "confirm_title_zh": "请确认这些事故事实",
        "confirm_actions": {
            "accept_zh": "信息正确，提交",
            "edit_zh": "修改",
            "redescribe_zh": "重新描述",
        },
    }


def public_proposal(state: AccidentStoryState) -> dict[str, Any]:
    """Customer/Broker-safe proposal view (no lifecycle mutation)."""
    guided = build_guided_customer_view(state)
    return {
        "schema_version": int(state.get("schema_version") or SCHEMA_VERSION),
        "proposal_version": 1,
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
        "guided_view": guided,
    }
