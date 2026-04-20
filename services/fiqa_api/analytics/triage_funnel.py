"""Funnel emission helpers for inbox triage (keeps routes thin)."""

from __future__ import annotations

import re
from typing import Any, Protocol

from services.fiqa_api.analytics.funnel_events import emit_funnel_event


class _TurnLike(Protocol):
    role: str
    text: str


def normalize_input(text: str) -> str:
    if not text:
        return ""
    t = str(text).strip()
    t = re.sub(r"\s+", " ", t)
    return t


def customer_turn_index(turns: list[_TurnLike]) -> int:
    n = sum(1 for t in turns if (t.role or "").strip().lower() == "customer")
    return n + 1


# Short replies that should still count toward first_meaningful_input (funnel / messy-user realism).
_SHORT_ACK_MEANINGFUL: frozenset[str] = frozenset(
    {
        "ok",
        "okay",
        "yes",
        "no",
        "hi",
        "hey",
        "yep",
        "sure",
        "pls",
        "please",
    }
)


def is_meaningful_customer_text(text: str) -> bool:
    t = normalize_input(text)
    if len(t) >= 4:
        return True
    if any("\u4e00" <= c <= "\u9fff" for c in t):
        return True
    if t.lower() in _SHORT_ACK_MEANINGFUL:
        return True
    return False


def case_snapshot_for_analytics(
    result: dict[str, Any],
    *,
    customer_turn_index: int,
    text: str,
) -> dict[str, Any]:
    miss = result.get("still_needed_fields")
    coll = result.get("collected_fields")
    suf = result.get("still_needed_user_flow")
    defb = result.get("deferred_to_broker_fields")
    bc = result.get("broker_completion")
    return {
        "quote_ready_status": result.get("quote_ready_status"),
        "still_needed_fields": list(miss) if isinstance(miss, list) else [],
        "still_needed_user_flow": list(suf) if isinstance(suf, list) else [],
        "deferred_to_broker_fields": list(defb) if isinstance(defb, list) else [],
        "broker_usable_case": (bc or {}).get("broker_usable_case") if isinstance(bc, dict) else None,
        "collected_fields": list(coll) if isinstance(coll, list) else [],
        "next_best_question": (str(result.get("next_best_question") or ""))[:400],
        "client_reply_draft": (str(result.get("client_reply_draft") or ""))[:800],
        "handoff_ready": bool(result.get("handoff_ready")),
        "triage_mode": result.get("triage_mode"),
        "append_allowed": result.get("append_allowed"),
        "conversion_stage": result.get("conversion_stage"),
        "issue_category": result.get("issue_category"),
        "reroute_occurred": bool(result.get("reroute_occurred")),
        "customer_turn_index": customer_turn_index,
        "customer_text_len": len(normalize_input(text)),
    }


def emit_session_milestones(
    *,
    session_id: str | None,
    text: str,
    turns: list[_TurnLike],
) -> None:
    sid = (session_id or "").strip() or None
    if not sid:
        return

    emit_funnel_event("session_started", session_id=sid, case_id=None, metadata={})
    ct = customer_turn_index(turns)
    if is_meaningful_customer_text(text):
        emit_funnel_event(
            "first_meaningful_input",
            session_id=sid,
            case_id=None,
            metadata={"customer_turn_index": ct},
        )


def emit_case_created_milestone(
    result: dict[str, Any],
    *,
    turns: list[_TurnLike],
    text: str,
    session_id: str | None,
    case_id: str,
) -> None:
    """Call only when a case row is newly persisted this request."""
    sid = (session_id or "").strip() or None
    cid = (case_id or "").strip()
    if not cid:
        return
    ct = customer_turn_index(turns)
    snap = case_snapshot_for_analytics(result, customer_turn_index=ct, text=text)
    emit_funnel_event(
        "case_created",
        session_id=sid,
        case_id=cid,
        metadata={"case_snapshot": snap, "customer_turn_index": ct},
    )


def emit_funnel_from_triage_result(
    result: dict[str, Any],
    *,
    turns: list[_TurnLike],
    text: str,
    session_id: str | None,
    case_id: str | None = None,
) -> None:
    """Emit quote_ready / handoff funnel milestones (deduped; append-safe)."""
    sid = (session_id or "").strip() or None
    cid = (case_id or str(result.get("case_id") or "").strip() or "").strip() or None
    cid = cid or None
    ct = customer_turn_index(turns)
    snap = case_snapshot_for_analytics(result, customer_turn_index=ct, text=text)
    base_meta: dict[str, Any] = {"case_snapshot": snap, "customer_turn_index": ct}

    if str(result.get("quote_ready_status") or "").strip() == "quote_ready":
        emit_funnel_event(
            "quote_ready_reached",
            session_id=sid,
            case_id=cid,
            metadata=dict(base_meta),
        )

    hr = bool(result.get("handoff_ready"))
    cu = bool(result.get("case_usable"))
    qrs = str(result.get("quote_ready_status") or "").strip()
    ic = str(result.get("issue_category") or "").strip()
    # Align funnel with routing: explicit handoff_ready, or structural quote_ready + case_usable
    # (handoff_ready may stay false until post-confirm even when quote_ready_reached already fired).
    handoff_milestone = hr or (cu and qrs == "quote_ready")
    if handoff_milestone:
        handoff_meta: dict[str, Any] = dict(base_meta)
        handoff_meta["case_usable"] = cu
        handoff_meta["handoff_ready"] = hr
        handoff_meta["quote_ready_status"] = qrs
        handoff_meta["issue_category"] = ic
        handoff_meta["lifecycle_status"] = result.get("lifecycle_status")
        emit_funnel_event("handoff_started", session_id=sid, case_id=cid, metadata=handoff_meta)

    if str(result.get("conversion_stage") or "").strip() == "handoff_confirmed":
        emit_funnel_event("handoff_confirmed", session_id=sid, case_id=cid, metadata=dict(base_meta))
