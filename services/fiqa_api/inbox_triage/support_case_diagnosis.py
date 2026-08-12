"""Deterministic stuck-case diagnosis for the support head (Pilot Reliability Fix 3).

Answers one operator question from persisted business state alone:
「这个客户的 Case 卡在哪里？最后成功到哪一步？下一步该做什么？」

Rules of this module:
- Pure and read-only. It receives an already-loaded case dict and never writes,
  never issues tokens, never calls an LLM.
- No raw customer prose, contact details, secrets, or tokens leave this module;
  timeline/command rows are projected onto a bounded key allowlist.
"""

from __future__ import annotations

from typing import Any, Mapping

DIAGNOSIS_CONTRACT_VERSION = "support_stuck_case_diagnosis_v1"

STATUS_CLOSED = "closed_no_action"
STATUS_START_CLAIM_DEGRADED = "start_claim_degraded"
STATUS_BLOCKED_BY_OPEN_REQUEST_MORE = "blocked_by_open_request_more"
STATUS_WAITING_OFFICE = "waiting_office"
STATUS_STORY_CONFIRMATION_INCOMPLETE = "story_confirmation_incomplete"
STATUS_READY_FOR_OFFICE_ACCEPT = "ready_for_office_accept"
STATUS_WAITING_CUSTOMER = "waiting_customer"
STATUS_UNKNOWN = "unknown"

START_CLAIM_SIDE_EFFECT_EVENT = "start_claim_side_effect_failed"
AUTHORITY_CUSTOMER_CONFIRMED = "customer_confirmed"

_MAX_TIMELINE_EVENTS = 5
_MAX_COMMAND_OUTCOMES = 3

# Timeline metadata is operator diagnostics only — never free text the customer typed.
_TIMELINE_METADATA_KEYS = ("source", "command_id", "warnings", "side_effects", "reason")

# Warnings support can re-verify against persisted state; anything else is advisory
# because the case alone cannot prove whether it was repaired.
_WARNING_POLICY_CONTEXT_UNCONFIRMED = "policy_context_not_confirmed"
_WARNING_ACCIDENT_STORY_UNCONFIRMED = "accident_story_not_confirmed"

_WAITING_CUSTOMER_STATUSES = frozenset({"waiting_client", "waiting_customer"})
_WAITING_OFFICE_STATUSES = frozenset({"new", "reviewing", "agent_followup"})


def _text(value: Any) -> str:
    return str(value or "").strip()


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _slice1_projection(case: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("p20_slice1_projection", "slice1_projection"):
        proj = case.get(key)
        if isinstance(proj, Mapping):
            return dict(proj)
    return {}


def _claim_timeline(case: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = case.get("claim_timeline")
    if not isinstance(raw, list):
        return []
    return [dict(item) for item in raw if isinstance(item, Mapping)]


def _accident_story_view(case: Mapping[str, Any]) -> dict[str, Any]:
    bag = _mapping(case.get("accident_story_assistant"))
    authority = _text(bag.get("authority")) or None
    return {
        "present": bool(bag),
        "authority": authority,
        "customer_confirmed": authority == AUTHORITY_CUSTOMER_CONFIRMED,
        "ai_involved": bool(bag.get("ai_involved")),
        "used_fallback": bool(bag.get("used_fallback")),
        "fallback_reason_category": _text(bag.get("fallback_reason_category")) or None,
        "proposal_id": _text(bag.get("proposal_id")) or None,
        "last_confirmed_command_id": _text(bag.get("last_confirmed_command_id")) or None,
    }


def _start_claim_view(
    timeline: list[dict[str, Any]],
    *,
    policy_context_confirmed: bool,
    story_confirmed: bool,
) -> dict[str, Any]:
    """Degraded only while a recorded side-effect warning is still true today."""

    signals = [
        evt for evt in timeline if _text(evt.get("event_type")) == START_CLAIM_SIDE_EFFECT_EVENT
    ]
    if not signals:
        return {"degraded": False, "degraded_signal_seen": False, "side_effect_warnings": []}

    latest = max(signals, key=lambda evt: _text(evt.get("created_at")))
    metadata = _mapping(latest.get("metadata"))
    warnings = [_text(w) for w in (metadata.get("warnings") or []) if _text(w)]

    unresolved: list[str] = []
    advisory: list[str] = []
    for code in warnings:
        if code == _WARNING_POLICY_CONTEXT_UNCONFIRMED:
            (advisory if policy_context_confirmed else unresolved).append(code)
        elif code == _WARNING_ACCIDENT_STORY_UNCONFIRMED:
            (advisory if story_confirmed else unresolved).append(code)
        else:
            advisory.append(code)

    return {
        "degraded": bool(unresolved),
        "degraded_signal_seen": True,
        "signal_at": _text(latest.get("created_at")) or None,
        "command_id": _text(metadata.get("command_id")) or None,
        "side_effect_warnings": warnings,
        "unresolved_warnings": unresolved,
        "advisory_warnings": advisory,
        "side_effects": _mapping(metadata.get("side_effects")),
    }


def _safe_timeline_row(event: Mapping[str, Any]) -> dict[str, Any]:
    metadata = _mapping(event.get("metadata"))
    row: dict[str, Any] = {
        "event_id": _text(event.get("event_id")) or None,
        "event_type": _text(event.get("event_type")) or None,
        "created_at": _text(event.get("created_at")) or None,
        "actor": _text(event.get("actor")) or None,
        "source_channel": _text(event.get("source_channel")) or None,
    }
    trimmed = {k: metadata[k] for k in _TIMELINE_METADATA_KEYS if k in metadata}
    if trimmed:
        row["metadata"] = trimmed
    return row


def _safe_command_row(event: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "event_type": _text(event.get("event_type")) or None,
        "command_id": _text(event.get("command_id")) or None,
        "actor": _text(event.get("actor")) or None,
        "created_at": _text(event.get("created_at")) or None,
        "aggregate_version": event.get("aggregate_version"),
        "state_before": _text(event.get("state_before")) or None,
        "state_after": _text(event.get("state_after")) or None,
    }


def _recent_command_outcomes(projection: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = projection.get("latest_events")
    if not isinstance(raw, list):
        return []
    rows = [dict(evt) for evt in raw if isinstance(evt, Mapping)]
    rows.sort(key=lambda evt: _text(evt.get("created_at")), reverse=True)
    return [_safe_command_row(evt) for evt in rows[:_MAX_COMMAND_OUTCOMES]]


def _last_success(timeline: list[dict[str, Any]]) -> dict[str, Any] | None:
    successes = [
        evt
        for evt in timeline
        if _text(evt.get("event_type"))
        and _text(evt.get("event_type")) != START_CLAIM_SIDE_EFFECT_EVENT
    ]
    if not successes:
        return None
    return _safe_timeline_row(max(successes, key=lambda evt: _text(evt.get("created_at"))))


def _request_more_block(case: Mapping[str, Any]) -> tuple[str | None, dict[str, Any]]:
    from services.fiqa_api.inbox_triage.p20_missing_information import (
        office_materials_request_more_block,
    )

    try:
        code, detail = office_materials_request_more_block(dict(case))
    except Exception:  # pragma: no cover - support head must never 500 on a signal
        return None, {}
    return code, detail if isinstance(detail, dict) else {}


def _accept_eligible(case: Mapping[str, Any]) -> bool:
    from services.fiqa_api.inbox_triage.p20_missing_information import (
        office_materials_accept_eligible,
    )

    try:
        return bool(office_materials_accept_eligible(dict(case)))
    except Exception:  # pragma: no cover - support head must never 500 on a signal
        return False


def _case_is_closed(case: Mapping[str, Any]) -> bool:
    from services.fiqa_api.inbox_triage.case_close import case_is_closed_history

    try:
        return bool(case_is_closed_history(dict(case)))
    except Exception:  # pragma: no cover - support head must never 500 on a signal
        return False


def _resolve(
    *,
    closed: bool,
    start_claim: Mapping[str, Any],
    request_more_reason: str | None,
    story: Mapping[str, Any],
    is_claim_lane: bool,
    materials_accepted_at: str | None,
    accept_eligible: bool,
    case_status: str,
    waiting_on: str,
) -> tuple[str, str, str]:
    """Return ``(status, next_support_action, next_support_action_zh)``.

    Ordered most-actionable first: a data-integrity break outranks a workflow wait,
    and an explicit blocker outranks a generic queue status.
    """

    if closed:
        return (
            STATUS_CLOSED,
            "Case is closed History. No support action unless the customer wants a new case.",
            "案件已归档关闭。除非客户要开新案件，否则无需处理。",
        )
    if start_claim.get("degraded"):
        codes = ", ".join(start_claim.get("unresolved_warnings") or []) or "unknown"
        return (
            STATUS_START_CLAIM_DEGRADED,
            (
                f"Start Claim saved the case but enrichment did not land ({codes}). "
                "Re-run the missing step with the customer, then re-check this head."
            ),
            f"开案已保存但补充信息未写入（{codes}）。请让客户补做该步骤，然后重新查看本页。",
        )
    if request_more_reason == "unresolved_request_more":
        return (
            STATUS_BLOCKED_BY_OPEN_REQUEST_MORE,
            "An open Request More is waiting on the customer. Chase the listed items.",
            "有未完成的补充资料请求，正在等客户。请催办清单中的项目。",
        )
    if request_more_reason == "awaiting_supplement_review":
        return (
            STATUS_WAITING_OFFICE,
            "Customer supplement is submitted. Broker must click 「已核对补充资料」.",
            "客户已提交补充资料，等待经纪点击「已核对补充资料」。",
        )
    if materials_accepted_at:
        return (
            STATUS_WAITING_OFFICE,
            "Materials were accepted by the office. The case is in broker/office follow-up.",
            "资料已由办公室确认齐全，案件在经纪/办公室跟进阶段。",
        )
    if is_claim_lane and not story.get("customer_confirmed"):
        return (
            STATUS_STORY_CONFIRMATION_INCOMPLETE,
            "Accident story is not customer-confirmed. Ask the customer to confirm the story.",
            "事故经过尚未由客户确认。请让客户完成事故经过确认。",
        )
    if accept_eligible:
        return (
            STATUS_READY_FOR_OFFICE_ACCEPT,
            "Nothing is missing. Broker can click 「确认资料已齐」.",
            "资料已齐，无缺失项。经纪可以点击「确认资料已齐」。",
        )
    if case_status in _WAITING_CUSTOMER_STATUSES or waiting_on == "client":
        return (
            STATUS_WAITING_CUSTOMER,
            "Case is waiting on the customer. Confirm what was last asked of them.",
            "案件正在等客户。请确认最后一次向客户要了什么。",
        )
    if case_status in _WAITING_OFFICE_STATUSES or waiting_on in {
        "broker",
        "carrier",
        "underwriting",
    }:
        return (
            STATUS_WAITING_OFFICE,
            "Case is in the office queue. Check the broker workbench for the next step.",
            "案件在办公室队列中。请到经纪工作台查看下一步。",
        )
    return (
        STATUS_UNKNOWN,
        "No deterministic blocker found. Open the broker workbench, then logs if still unclear.",
        "未发现确定性的阻塞点。请打开经纪工作台；若仍不清楚再看日志。",
    )


def build_support_case_diagnosis(case: Mapping[str, Any] | None) -> dict[str, Any]:
    """Deterministic, read-only support view of where one case is stuck."""

    if not isinstance(case, Mapping):
        return {
            "diagnosis_contract_version": DIAGNOSIS_CONTRACT_VERSION,
            "status": STATUS_UNKNOWN,
            "next_support_action": "Case not readable.",
            "next_support_action_zh": "无法读取案件。",
        }

    projection = _slice1_projection(case)
    timeline = _claim_timeline(case)
    story = _accident_story_view(case)

    policy_context = _mapping(case.get("policy_context"))
    policy_context_status = _text(policy_context.get("status")).lower() or None

    start_claim = _start_claim_view(
        timeline,
        policy_context_confirmed=policy_context_status == "confirmed",
        story_confirmed=bool(story["customer_confirmed"]),
    )

    block_code, block_detail = _request_more_block(case)
    request_more_reason = _text(block_detail.get("reason")) or None
    materials_accepted_at = _text(case.get("office_materials_accepted_at")) or None
    closed = _case_is_closed(case)
    is_claim_lane = _text(case.get("service_lane")).lower() == "claim"

    # Only worth computing when nothing earlier already explains the block.
    accept_eligible = (
        not closed
        and not start_claim.get("degraded")
        and block_code is None
        and not materials_accepted_at
        and (story["customer_confirmed"] or not is_claim_lane)
        and _accept_eligible(case)
    )

    status, action, action_zh = _resolve(
        closed=closed,
        start_claim=start_claim,
        request_more_reason=request_more_reason,
        story=story,
        is_claim_lane=is_claim_lane,
        materials_accepted_at=materials_accepted_at,
        accept_eligible=accept_eligible,
        case_status=_text(case.get("case_status")).lower(),
        waiting_on=_text(case.get("waiting_on")).lower(),
    )

    blocker: dict[str, Any] | None = None
    if block_code:
        blocker = {
            "code": block_code,
            "reason": request_more_reason,
            "workflow_state": block_detail.get("workflow_state"),
            "open_request": block_detail.get("open_request"),
        }
    elif start_claim.get("degraded"):
        blocker = {
            "code": START_CLAIM_SIDE_EFFECT_EVENT,
            "reason": "start_claim_side_effect_unresolved",
            "unresolved_warnings": start_claim.get("unresolved_warnings"),
        }

    recent = sorted(timeline, key=lambda evt: _text(evt.get("created_at")), reverse=True)

    return {
        "diagnosis_contract_version": DIAGNOSIS_CONTRACT_VERSION,
        "diagnosis_source": "deterministic_persisted_business_state_v1",
        "status": status,
        "next_support_action": action,
        "next_support_action_zh": action_zh,
        "blocker": blocker,
        "last_success": _last_success(timeline),
        "signals": {
            "case_closed": closed,
            "service_lane": _text(case.get("service_lane")) or None,
            "slice1_workflow_state": _text(projection.get("workflow_state")) or None,
            "open_request_more": request_more_reason == "unresolved_request_more",
            "awaiting_supplement_review": request_more_reason == "awaiting_supplement_review",
            "office_materials_accepted_at": materials_accepted_at,
            "office_materials_accept_eligible": accept_eligible,
            "policy_context_status": policy_context_status,
            "accident_story": story,
            "start_claim": start_claim,
        },
        "recent_timeline_events": [_safe_timeline_row(e) for e in recent[:_MAX_TIMELINE_EVENTS]],
        "recent_command_outcomes": _recent_command_outcomes(projection),
    }
