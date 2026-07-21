"""P35.1 Founder QA harness HTTP surface (support-gated, QA-only)."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from services.fiqa_api.inbox_triage import p35_mp_qa_harness as hx
from services.fiqa_api.security.support_export_gate import assert_support_export_authorized

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inbox/support/p35-mp-qa", tags=["p35-mp-qa"])

_RATE_LOCK = threading.Lock()
_RATE_WINDOW_START = 0.0
_RATE_COUNT = 0
_RATE_LIMIT = 30
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
            raise HTTPException(status_code=429, detail="p35_mp_qa_rate_limited")


def _gate(request: Request, *, mutating: bool = True) -> None:
    assert_support_export_authorized(request)
    try:
        hx.assert_harness_allowed()
    except ValueError as exc:
        code = str(exc)
        if code in (
            "p35_mp_qa_harness_disabled",
            "p35_mp_qa_surface_disabled",
            "p35_mp_qa_support_key_required",
        ):
            raise HTTPException(status_code=403, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc
    if mutating:
        _rate_limit_mutating()


class IdentityBody(BaseModel):
    session_id: str = Field(..., min_length=12, max_length=80)


class PresetBody(BaseModel):
    session_id: str = Field(..., min_length=12, max_length=80)
    confirm: str = Field(..., min_length=3, max_length=32)
    actor: str = Field(default="founder", max_length=64)


@router.get("/status")
async def p35_mp_qa_status(request: Request) -> dict[str, Any]:
    assert_support_export_authorized(request)
    return hx.harness_status()


@router.get("/audit")
async def p35_mp_qa_audit(request: Request, limit: int = 20) -> dict[str, Any]:
    _gate(request, mutating=False)
    return {"ok": True, "events": hx.list_audit_events(limit=limit)}


@router.post("/inspect")
async def p35_mp_qa_inspect(body: IdentityBody, request: Request) -> dict[str, Any]:
    _gate(request, mutating=False)
    try:
        return hx.inspect_identity(body.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/presets/fresh")
async def p35_mp_qa_fresh(body: PresetBody, request: Request) -> dict[str, Any]:
    _gate(request, mutating=True)
    try:
        return hx.preset_fresh_customer(
            session_id=body.session_id,
            confirm=body.confirm,
            actor=body.actor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.warning("p35_mp_qa_fresh_failed %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/presets/active")
async def p35_mp_qa_active(body: PresetBody, request: Request) -> dict[str, Any]:
    _gate(request, mutating=True)
    try:
        return hx.preset_active_claim(
            session_id=body.session_id,
            confirm=body.confirm,
            actor=body.actor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.warning("p35_mp_qa_active_failed %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/presets/request-more")
async def p35_mp_qa_request_more(body: PresetBody, request: Request) -> dict[str, Any]:
    _gate(request, mutating=True)
    try:
        return hx.preset_request_more(
            session_id=body.session_id,
            confirm=body.confirm,
            actor=body.actor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.warning("p35_mp_qa_request_more_failed %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
