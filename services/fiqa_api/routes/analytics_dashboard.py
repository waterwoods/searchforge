"""Product analytics dashboard (in-memory funnel + deterministic North Star)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from services.fiqa_api.analytics.funnel_events import CANONICAL_FUNNEL_EVENTS, iter_funnel_events
from services.fiqa_api.analytics.funnel_metrics import (
    compute_dropoff_points,
    compute_dropoff_summary,
    compute_funnel,
    group_events_by_session,
    top_issues_from_funnel,
)
from services.fiqa_api.analytics.north_star_score import compute_north_star_score

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _session_has_canonical(evs: list[dict[str, Any]]) -> bool:
    types = {str(e.get("event") or "") for e in evs}
    return bool(types & set(CANONICAL_FUNNEL_EVENTS))


def _aggregate_north_star(events: list[dict[str, Any]]) -> tuple[float | None, dict[str, float | None]]:
    by_s = group_events_by_session(events)
    totals: list[float] = []
    dim_sums: dict[str, float] = {k: 0.0 for k in ("start_ease", "continuity", "guidance", "efficiency", "trust")}
    n_dim = 0
    for _sk, evs in by_s.items():
        if not _session_has_canonical(evs):
            continue
        score = compute_north_star_score(evs, None)
        totals.append(float(score["total_score"]))
        n_dim += 1
        for k, v in score["dimensions"].items():
            dim_sums[k] += float(v)
    if not totals:
        return None, {k: None for k in dim_sums}
    avg = round(sum(totals) / len(totals), 2)
    breakdown = {k: round(dim_sums[k] / n_dim, 2) for k in dim_sums}
    return avg, breakdown


@router.get("/dashboard")
async def analytics_dashboard() -> dict[str, Any]:
    events = iter_funnel_events()
    funnel = compute_funnel(events)
    dropoff_points = compute_dropoff_points(events)
    dropoff_summary = compute_dropoff_summary(events)
    issues = top_issues_from_funnel(events)
    north_star_avg, dimension_breakdown = _aggregate_north_star(events)

    return {
        "north_star_avg": north_star_avg,
        "dimension_breakdown": dimension_breakdown,
        "funnel": funnel,
        "dropoff_points": dropoff_points,
        "dropoff_summary": dropoff_summary,
        "top_issues": issues,
        "sessions_in_buffer": len(group_events_by_session(events)),
    }
