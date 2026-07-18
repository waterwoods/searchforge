"""P26H QA ephemeral fixture HTTP surface (support-gated, QA-only)."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from services.fiqa_api.inbox_triage import p26h_qa_fixture_runner as fx
from services.fiqa_api.security.support_export_gate import assert_support_export_authorized

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inbox/support/p26h-fixture", tags=["p26h-fixture"])

# Bounded usage: max mutating calls per process window (status is exempt).
_RATE_LOCK = threading.Lock()
_RATE_WINDOW_START = 0.0
_RATE_COUNT = 0
_RATE_LIMIT = 60
_RATE_WINDOW_SEC = 60.0


def _rate_limit_mutating() -> None:
    global _RATE_WINDOW_START, _RATE_COUNT
    now = time.monotonic()
    with _RATE_LOCK:
        if now - _RATE_WINDOW_START > _RATE_WINDOW_SEC:
            _RATE_WINDOW_START = now
            _RATE_COUNT = 0
        _RATE_COUNT += 1
        if _RATE_COUNT > _RATE_LIMIT:
            raise HTTPException(status_code=429, detail="p26h_fixture_rate_limited")


def _gate(request: Request, *, mutating: bool = True) -> None:
    assert_support_export_authorized(request)
    try:
        fx.assert_fixture_runner_allowed()
    except ValueError as exc:
        code = str(exc)
        if code in (
            "p26h_fixture_runner_disabled",
            "p26h_fixture_surface_disabled",
            "p26h_fixture_support_key_required",
        ):
            raise HTTPException(status_code=403, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc
    if mutating:
        _rate_limit_mutating()

class CreateCaseBody(BaseModel):
    suffix: str = Field(default="fresh", max_length=32)
    session_id: str | None = Field(default=None, max_length=128)
    idempotency_key: str | None = Field(default=None, max_length=128)
    accident_description: str = Field(
        default="停车场倒车碰撞，前保险杠受损",
        max_length=2000,
    )


class EvidenceBody(BaseModel):
    slot: str = Field(..., min_length=3, max_length=64)


class StaleCleanupBody(BaseModel):
    max_age_hours: int = Field(default=24, ge=1, le=168)


@router.get("/status")
async def p26h_fixture_status(request: Request) -> dict[str, Any]:
    assert_support_export_authorized(request)
    return fx.fixture_runner_status()


@router.post("/runs")
async def p26h_fixture_create_run(request: Request) -> dict[str, Any]:
    _gate(request, mutating=True)
    return fx.create_run()


@router.post("/runs/{harness_run_id}/cases")
async def p26h_fixture_create_case(
    harness_run_id: str,
    body: CreateCaseBody,
    request: Request,
) -> dict[str, Any]:
    _gate(request, mutating=True)
    try:
        return fx.create_fresh_claim(
            harness_run_id=harness_run_id,
            suffix=body.suffix,
            session_id=body.session_id,
            idempotency_key=body.idempotency_key,
            accident_description=body.accident_description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.warning("p26h_fixture_create_case_failed %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/runs/{harness_run_id}/cases/{case_id}/evidence")
async def p26h_fixture_register_evidence(
    harness_run_id: str,
    case_id: str,
    body: EvidenceBody,
    request: Request,
) -> dict[str, Any]:
    _gate(request, mutating=True)
    try:
        return fx.register_test_evidence(
            harness_run_id=harness_run_id,
            case_id=case_id,
            slot=body.slot,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/runs/{harness_run_id}/cases/{case_id}/vehicle")
async def p26h_fixture_vehicle(
    harness_run_id: str,
    case_id: str,
    request: Request,
) -> dict[str, Any]:
    _gate(request, mutating=True)
    try:
        return fx.patch_vehicle_facts(harness_run_id=harness_run_id, case_id=case_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runs/{harness_run_id}/cases/{case_id}/broker-followup")
async def p26h_fixture_broker_followup(
    harness_run_id: str,
    case_id: str,
    request: Request,
) -> dict[str, Any]:
    _gate(request, mutating=True)
    try:
        return fx.create_broker_followup(harness_run_id=harness_run_id, case_id=case_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/runs/{harness_run_id}/cases/{case_id}/inspect")
async def p26h_fixture_inspect(
    harness_run_id: str,
    case_id: str,
    request: Request,
) -> dict[str, Any]:
    _gate(request, mutating=False)
    try:
        return fx.inspect_case(harness_run_id=harness_run_id, case_id=case_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runs/{harness_run_id}/cases/{case_id}/expired-token")
async def p26h_fixture_expired_token(
    harness_run_id: str,
    case_id: str,
    request: Request,
) -> dict[str, Any]:
    _gate(request, mutating=True)
    try:
        return fx.issue_expired_token(harness_run_id=harness_run_id, case_id=case_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/runs/{harness_run_id}")
async def p26h_fixture_cleanup_run(harness_run_id: str, request: Request) -> dict[str, Any]:
    _gate(request, mutating=True)
    try:
        return fx.cleanup_run(harness_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/cleanup-stale")
async def p26h_fixture_cleanup_stale(body: StaleCleanupBody, request: Request) -> dict[str, Any]:
    _gate(request, mutating=True)
    return fx.cleanup_stale(max_age_hours=body.max_age_hours)
