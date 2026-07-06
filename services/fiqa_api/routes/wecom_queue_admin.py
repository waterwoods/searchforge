"""
WeCom queue admin — protected Cloud Run manual drain/status (Q0.8.1).

GET  /api/admin/wecom/queues/status  — queue counts only (no payload bodies)
POST /api/admin/wecom/queues/drain   — drain one batch inside Cloud Run process

Requires WECOM_QUEUE_ADMIN_TOKEN (fail closed when unset).
Reuses Q0.5 queue_admin helpers; does not toggle WECOM_INBOX_QUEUE / WECOM_REPLY_OUTBOX.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from services.fiqa_api.security.wecom_queue_admin_gate import assert_wecom_queue_admin_authorized
from services.fiqa_api.wecom.queue_admin import (
    drain_wecom_queues,
    fetch_wecom_queue_status,
    repair_stale_wecom_queue_rows,
)

router = APIRouter(prefix="/api/admin/wecom/queues", tags=["WeCom Queue Admin"])

_DEFAULT_DRAIN_LIMIT = 1
_MAX_DRAIN_LIMIT = 25


def _clamp_drain_limit(limit: int | None) -> int:
    if limit is None:
        return _DEFAULT_DRAIN_LIMIT
    return max(1, min(int(limit), _MAX_DRAIN_LIMIT))


def _status_response(status: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, **status}


def _drain_ok(drain_result: dict[str, Any]) -> bool:
    inbox = drain_result.get("inbox") or {}
    outbox = drain_result.get("outbox") or {}
    return (inbox.get("failed") or 0) == 0 and (outbox.get("failed") or 0) == 0


@router.get("/status")
def wecom_queue_status(request: Request) -> dict[str, Any]:
    """Return inbox/outbox counts by status — no payload bodies."""
    assert_wecom_queue_admin_authorized(request)
    try:
        status = fetch_wecom_queue_status()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _status_response(status)


@router.post("/drain")
def wecom_queue_drain(
    request: Request,
    limit: int | None = Query(
        default=None,
        ge=1,
        description=f"Max rows per queue per run (default {_DEFAULT_DRAIN_LIMIT}, capped at {_MAX_DRAIN_LIMIT})",
    ),
    include_status_snapshot: bool = Query(
        default=True,
        description="Include status_before and status_after snapshots in response",
    ),
) -> dict[str, Any]:
    """Drain pending inbox then outbox rows using current Cloud Run environment."""
    assert_wecom_queue_admin_authorized(request)
    effective_limit = _clamp_drain_limit(limit)

    status_before: dict[str, Any] | None = None
    if include_status_snapshot:
        try:
            status_before = fetch_wecom_queue_status()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        drain_result = drain_wecom_queues(limit=effective_limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    response: dict[str, Any] = {
        "ok": _drain_ok(drain_result),
        "limit": effective_limit,
        "inbox": drain_result.get("inbox") or {},
        "outbox": drain_result.get("outbox") or {},
        "max_attempts": drain_result.get("max_attempts"),
        "stale_timeout_seconds": drain_result.get("stale_timeout_seconds"),
    }

    if include_status_snapshot:
        try:
            status_after = fetch_wecom_queue_status()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        response["status_before"] = status_before
        response["status_after"] = status_after

    return response


@router.post("/repair-stale")
def wecom_queue_repair_stale(
    request: Request,
    stale_timeout_seconds: int | None = Query(
        default=None,
        ge=60,
        description="Only reset rows locked longer than this (default 600)",
    ),
    dry_run: bool = Query(
        default=False,
        description="Count stale rows without resetting them",
    ),
) -> dict[str, Any]:
    """Reset stale processing/sending rows to pending — safe operator repair."""
    assert_wecom_queue_admin_authorized(request)
    effective_timeout = stale_timeout_seconds if stale_timeout_seconds is not None else 600
    try:
        result = repair_stale_wecom_queue_rows(
            stale_timeout_seconds=effective_timeout,
            dry_run=dry_run,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"ok": True, **result}
