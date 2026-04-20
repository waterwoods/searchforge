"""Funnel counts, conversion rates, and drop-off heuristics."""

from __future__ import annotations

from typing import Any

from services.fiqa_api.analytics.funnel_events import CANONICAL_FUNNEL_EVENTS


def _session_key(ev: dict[str, Any]) -> str:
    sid = str(ev.get("session_id") or "").strip()
    if sid:
        return f"s:{sid}"
    cid = str(ev.get("case_id") or "").strip()
    if cid:
        return f"c:{cid}"
    return "unknown"


def group_events_by_session(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for e in events:
        if not isinstance(e, dict):
            continue
        sk = _session_key(e)
        out.setdefault(sk, []).append(e)
    for sk in out:
        out[sk].sort(key=lambda x: str(x.get("timestamp") or ""))
    return out


def compute_funnel(events: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Session-scoped funnel: each stage count = number of sessions that emitted that milestone.
    """
    by_s = group_events_by_session(events)
    counts_milestone: dict[str, int] = {k: 0 for k in CANONICAL_FUNNEL_EVENTS}

    for _sk, evs in by_s.items():
        types_seen = {str(e.get("event") or "") for e in evs}
        for name in counts_milestone:
            if name in types_seen:
                counts_milestone[name] += 1

    ss = counts_milestone.get("session_started", 0) or 0
    cc = counts_milestone.get("case_created", 0) or 0
    qr = counts_milestone.get("quote_ready_reached", 0) or 0
    hs = counts_milestone.get("handoff_started", 0) or 0
    hc = counts_milestone.get("handoff_confirmed", 0) or 0

    def rate(num: int, den: int) -> float | None:
        if den <= 0:
            return None
        return round(num / den, 4)

    conversion_rates = {
        "session_to_case": rate(cc, ss),
        "case_to_quote_ready": rate(qr, cc),
        "quote_ready_to_handoff": rate(hs, qr),
        "handoff_to_confirmed": rate(hc, hs),
        "conversion_rate_quote_to_handoff": rate(hs, qr),
    }

    return {
        "counts": {
            "session_started": ss,
            "case_created": cc,
            "quote_ready_reached": qr,
            "quote_ready": qr,
            "handoff_started": hs,
            "handoff_confirmed": hc,
            "broker_followup_started": counts_milestone.get("broker_followup_started", 0),
        },
        "conversion_rates": conversion_rates,
    }


def compute_dropoff_points(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ordered list of step transitions with largest session drop first."""
    f = compute_funnel(events)["counts"]
    steps = [
        ("session_started", "case_created", f.get("session_started", 0), f.get("case_created", 0)),
        ("case_created", "quote_ready_reached", f.get("case_created", 0), f.get("quote_ready_reached", 0)),
        ("quote_ready_reached", "handoff_started", f.get("quote_ready_reached", 0), f.get("handoff_started", 0)),
        ("handoff_started", "handoff_confirmed", f.get("handoff_started", 0), f.get("handoff_confirmed", 0)),
    ]
    drops: list[dict[str, Any]] = []
    for a, b, ca, cb in steps:
        if ca is None or cb is None:
            continue
        raw = int(ca) - int(cb)
        rate = (raw / int(ca)) if int(ca) > 0 else 0.0
        drops.append(
            {
                "from_step": a,
                "to_step": b,
                "drop_sessions": max(0, raw),
                "drop_rate": round(rate, 4),
            }
        )
    drops.sort(key=lambda x: x["drop_sessions"], reverse=True)
    return drops


def compute_dropoff_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Largest funnel drop + lightweight suspected reason (heuristic)."""
    pts = compute_dropoff_points(events)
    if not pts or pts[0].get("drop_sessions", 0) <= 0:
        return {
            "biggest_drop": None,
            "suspected_reason": None,
        }
    top = pts[0]
    pair = f"{top['from_step']} → {top['to_step']}"
    reason = "unknown"
    if top["from_step"] == "session_started":
        reason = "early hesitation / unclear entry / empty first messages"
    elif top["from_step"] == "case_created":
        reason = "field collection friction / trust on structured data"
    elif top["from_step"] == "quote_ready_reached":
        reason = "missing contact / hesitation after quote-ready / conversion copy gap"
    elif top["from_step"] == "handoff_started":
        reason = "customer did not confirm handoff / timing or clarity"
    return {"biggest_drop": pair, "suspected_reason": reason}


def top_issues_from_funnel(events: list[dict[str, Any]], limit: int = 5) -> list[str]:
    summary = compute_dropoff_summary(events)
    issues: list[str] = []
    if summary.get("biggest_drop"):
        issues.append(f"Largest drop: {summary['biggest_drop']} — {summary.get('suspected_reason')}")
    # Stuck heuristics: sessions with quote_ready but no handoff_started
    by_s = group_events_by_session(events)
    stuck_pre_qr = 0
    stuck_post_qr = 0
    for _sk, evs in by_s.items():
        types = {str(e.get("event") or "") for e in evs}
        if "session_started" not in types:
            continue
        if "quote_ready_reached" not in types:
            if "case_created" in types or len(types) > 1:
                stuck_pre_qr += 1
        elif "handoff_started" not in types:
            stuck_post_qr += 1
    if stuck_pre_qr:
        issues.append(f"{stuck_pre_qr} sessions active before quote_ready (stuck in collection)")
    if stuck_post_qr:
        issues.append(f"{stuck_post_qr} sessions reached quote_ready without handoff_started")
    return issues[:limit]
