"""Deterministic North Star score (0–10) for Unified Intake / Add-Car sessions."""

from __future__ import annotations

import re
from typing import Any

# Efficiency: customer turns to reach quote_ready (add-car).
_EFF_GOOD_MAX_TURNS = 8
_EFF_OK_MAX_TURNS = 14

# Misleading "complete" cues while fields still missing (ZH + light EN).
_TRUST_COMPLETE_PAT = re.compile(
    r"(齐全|齐备|齐了|都齐|完整|已全部|都好了|已经全部|all\s+set|we\s+have\s+everything|complete\s+for\s+now)",
    re.IGNORECASE,
)


def _last_case_snapshot(session_events: list[dict[str, Any]]) -> dict[str, Any]:
    snap: dict[str, Any] = {}
    for e in session_events:
        meta = e.get("metadata") if isinstance(e.get("metadata"), dict) else {}
        cs = meta.get("case_snapshot")
        if isinstance(cs, dict) and cs:
            snap = cs
    return snap


def _customer_turn_from_events(session_events: list[dict[str, Any]]) -> int | None:
    """Latest known customer turn index from snapshots."""
    best: int | None = None
    for e in session_events:
        meta = e.get("metadata") if isinstance(e.get("metadata"), dict) else {}
        cs = meta.get("case_snapshot") if isinstance(meta.get("case_snapshot"), dict) else {}
        t = cs.get("customer_turn_index")
        if isinstance(t, int) and t >= 1:
            best = t if best is None else max(best, t)
        t2 = meta.get("customer_turn_index")
        if isinstance(t2, int) and t2 >= 1:
            best = t2 if best is None else max(best, t2)
    return best


def _first_meaningful_turn(session_events: list[dict[str, Any]]) -> int | None:
    for e in session_events:
        if e.get("event") != "first_meaningful_input":
            continue
        meta = e.get("metadata") if isinstance(e.get("metadata"), dict) else {}
        t = meta.get("customer_turn_index")
        if isinstance(t, int):
            return t
    return None


def _quote_ready_turn(session_events: list[dict[str, Any]]) -> int | None:
    for e in session_events:
        if e.get("event") != "quote_ready_reached":
            continue
        meta = e.get("metadata") if isinstance(e.get("metadata"), dict) else {}
        t = meta.get("customer_turn_index")
        if isinstance(t, int):
            return t
    return None


def _has_named_event(session_events: list[dict[str, Any]], name: str) -> bool:
    return any(e.get("event") == name for e in session_events)


def _append_blocked_count(session_events: list[dict[str, Any]]) -> int:
    n = 0
    for e in session_events:
        if e.get("event") == "append_blocked":
            n += 1
        meta = e.get("metadata") if isinstance(e.get("metadata"), dict) else {}
        if meta.get("append_blocked") is True:
            n += 1
    return n


def _any_reroute(session_events: list[dict[str, Any]], case_state: dict[str, Any]) -> bool:
    if bool(case_state.get("reroute_occurred")):
        return True
    for e in session_events:
        meta = e.get("metadata") if isinstance(e.get("metadata"), dict) else {}
        cs = meta.get("case_snapshot") if isinstance(meta.get("case_snapshot"), dict) else {}
        if bool(cs.get("reroute_occurred")):
            return True
    return False


def _any_next_best_question(session_events: list[dict[str, Any]], case_state: dict[str, Any]) -> bool:
    if bool((case_state.get("next_best_question") or "").strip()):
        return True
    for e in session_events:
        meta = e.get("metadata") if isinstance(e.get("metadata"), dict) else {}
        if bool((meta.get("next_best_question") or "").strip()):
            return True
        cs = meta.get("case_snapshot") if isinstance(meta.get("case_snapshot"), dict) else {}
        if bool((cs.get("next_best_question") or "").strip()):
            return True
    return False


def _guidance_from_draft_and_need(case_state: dict[str, Any]) -> float:
    still = case_state.get("still_needed_fields")
    if not isinstance(still, list):
        still = []
    draft = str(case_state.get("client_reply_draft") or "")
    if not still:
        return 2.0
    if "?" in draft or "？" in draft:
        return 1.5
    if re.search(r"(还缺|缺少|需要|请提供|please\s+provide|still\s+need)", draft, re.IGNORECASE):
        return 1.0
    return 0.5


def compute_north_star_score(
    session_events: list[dict[str, Any]],
    case_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Five dimensions × 0–2 → total 0–10. Deterministic, explainable, no LLM.

    session_events: chronological dicts (funnel + optional append_blocked entries).
    case_state: final triage-shaped snapshot; if omitted, derived from last embedded case_snapshot.
    """
    cs = dict(case_state) if isinstance(case_state, dict) else _last_case_snapshot(session_events)

    explain: dict[str, Any] = {}

    # 1) START_EASE
    fm = _first_meaningful_turn(session_events)
    if fm is None:
        start = 0.0
        explain["start_ease"] = "no first_meaningful_input event"
    elif fm <= 1:
        start = 2.0
        explain["start_ease"] = "meaningful input on first customer turn"
    elif fm <= 2:
        start = 1.0
        explain["start_ease"] = "meaningful input by turn 2"
    else:
        start = 0.0
        explain["start_ease"] = "late first meaningful input"

    # 2) CONTINUITY
    blocked = _append_blocked_count(session_events)
    reroute = _any_reroute(session_events, cs)
    if blocked >= 2:
        cont = 0.0
        explain["continuity"] = "multiple append / boundary blocks"
    elif blocked == 1:
        cont = 1.0
        explain["continuity"] = "one continuity break"
    elif reroute:
        cont = 1.0
        explain["continuity"] = "intent reroute mid-session"
    else:
        cont = 2.0
        explain["continuity"] = "no blocked append / reroute"

    # 3) GUIDANCE
    qrs = str(cs.get("quote_ready_status") or "").strip()
    if qrs == "quote_ready":
        guide = 2.0
        explain["guidance"] = "reached quote_ready (clear progression)"
    elif _any_next_best_question(session_events, cs):
        guide = 2.0
        explain["guidance"] = "next_best_question used while collecting"
    else:
        guide = min(2.0, float(_guidance_from_draft_and_need(cs)))
        explain["guidance"] = "inferred from draft vs missing fields"

    # 4) EFFICIENCY
    qr_turn = _quote_ready_turn(session_events)
    if qr_turn is not None:
        if qr_turn <= _EFF_GOOD_MAX_TURNS:
            eff = 2.0
            explain["efficiency"] = f"quote_ready by turn {qr_turn} (≤{_EFF_GOOD_MAX_TURNS})"
        elif qr_turn <= _EFF_OK_MAX_TURNS:
            eff = 1.0
            explain["efficiency"] = f"quote_ready by turn {qr_turn} (ok band)"
        else:
            eff = 0.0
            explain["efficiency"] = "quote_ready took many turns"
    else:
        ic = str(cs.get("issue_category") or "").strip()
        if ic == "customer_requested_human" and cs.get("handoff_ready"):
            eff = 2.0
            explain["efficiency"] = "direct human handoff path (non-quote)"
        else:
            last_turn = _customer_turn_from_events(session_events) or 0
            if last_turn >= _EFF_OK_MAX_TURNS:
                eff = 0.0
                explain["efficiency"] = "no quote_ready; many turns"
            elif last_turn >= _EFF_GOOD_MAX_TURNS:
                eff = 0.5
                explain["efficiency"] = "no quote_ready; moderate length"
            else:
                eff = 1.0
                explain["efficiency"] = "no quote_ready yet; still early"

    if _has_named_event(session_events, "quote_ready_reached") and not _has_named_event(
        session_events,
        "handoff_started",
    ):
        eff = min(float(eff), 1.0)
        explain["efficiency"] = "quote_ready reached but no handoff_started (conversion stall)"

    # 5) TRUST
    still = cs.get("still_needed_fields")
    if not isinstance(still, list):
        still = []
    draft = str(cs.get("client_reply_draft") or "")
    misleading = bool(still) and bool(_TRUST_COMPLETE_PAT.search(draft))
    if misleading:
        trust = 0.0
        explain["trust"] = "complete-like phrasing while fields still missing"
    elif bool(still) and qrs == "quote_ready":
        trust = 0.0
        explain["trust"] = "quote_ready with inconsistent still_needed"
    else:
        trust = 2.0
        explain["trust"] = "no obvious complete/still_needed clash"

    dims = {
        "start_ease": round(start, 2),
        "continuity": round(cont, 2),
        "guidance": round(min(2.0, guide), 2),
        "efficiency": round(min(2.0, eff), 2),
        "trust": round(trust, 2),
    }
    total = round(sum(dims.values()), 2)
    return {
        "total_score": total,
        "dimensions": dims,
        "explain": explain,
    }
