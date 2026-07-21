"""P35.2 — Founder QA Console BFF (internal Workbench proxy).

Browser calls these routes with the intake API perimeter (when configured).
Support API key is never accepted from or returned to the browser.
Domain mutations reuse p35_mp_qa_harness directly.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from services.fiqa_api.inbox_triage import p35_mp_qa_harness as hx
from services.fiqa_api.security.intake_api_gate import (
    assert_intake_api_authorized,
    intake_api_secret_configured,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/internal/founder-qa", tags=["founder-qa-console"])

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
            raise HTTPException(status_code=429, detail="founder_qa_rate_limited")


def _actor_from_request(request: Request) -> str:
    raw = (request.headers.get("X-Founder-Qa-Actor") or "").strip()
    return (raw or "founder")[:64]


def _authorize_console(request: Request, *, mutating: bool) -> str:
    """Gate console access. Support key must never come from the browser."""
    # Reject accidental support-key passthrough from browser clients.
    if (request.headers.get("X-Unified-Intake-Support-Key") or "").strip():
        raise HTTPException(status_code=400, detail="support_key_not_accepted_on_console")

    try:
        assert_intake_api_authorized(request)
    except HTTPException:
        raise

    from services.fiqa_api.db.service_record_settings import is_production_mode

    # Local/demo without intake key: refuse production; allow status/identity reads so the
    # console can show a disabled banner. Mutations still require harness flags.
    if not intake_api_secret_configured() and is_production_mode():
        raise HTTPException(status_code=403, detail="founder_qa_production_requires_intake_key")

    if mutating:
        if not intake_api_secret_configured() and not hx.harness_enabled():
            raise HTTPException(status_code=403, detail="founder_qa_harness_disabled")
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
        _rate_limit_mutating()

    return _actor_from_request(request)


class IdentitySelectBody(BaseModel):
    session_id: str = Field(..., min_length=12, max_length=80)
    label: str | None = Field(default=None, max_length=64)


class PresetBody(BaseModel):
    confirm: str = Field(..., min_length=3, max_length=32)
    session_id: str | None = Field(default=None, min_length=12, max_length=80)


def _resolve_session_id(body_session: str | None, actor: str) -> str:
    if body_session and body_session.strip():
        return hx.normalize_exact_person_link(body_session)
    pref = hx.get_selected_identity(actor=actor)
    if not pref or not pref.get("session_id"):
        raise HTTPException(status_code=400, detail="selected_identity_required")
    return hx.normalize_exact_person_link(str(pref["session_id"]))


@router.get("/status")
async def founder_qa_status(request: Request) -> dict[str, Any]:
    actor = _authorize_console(request, mutating=False)
    authorized = True
    try:
        # Status remains readable when harness is disabled (shows safety banner).
        return hx.console_status(actor=actor, authorized=authorized)
    except Exception as exc:
        logger.warning("founder_qa_status_failed %s", exc)
        raise HTTPException(status_code=503, detail="status_unavailable") from exc


@router.post("/identity")
async def founder_qa_select_identity(body: IdentitySelectBody, request: Request) -> dict[str, Any]:
    actor = _authorize_console(request, mutating=False)
    try:
        hx.assert_harness_allowed()
    except ValueError as exc:
        # Allow selecting identity even when mutations are disabled, so Founder can prepare.
        if str(exc) not in (
            "p35_mp_qa_harness_disabled",
            "p35_mp_qa_surface_disabled",
            "p35_mp_qa_support_key_required",
        ):
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        row = hx.set_selected_identity(session_id=body.session_id, actor=actor, label=body.label)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    status = hx.console_status(actor=actor, authorized=True)
    return {"ok": True, "selected_identity": row, "status": status}


@router.delete("/identity")
async def founder_qa_forget_identity(request: Request) -> dict[str, Any]:
    actor = _authorize_console(request, mutating=False)
    forgotten = hx.forget_selected_identity(actor=actor)
    status = hx.console_status(actor=actor, authorized=True)
    return {"ok": True, **forgotten, "status": status}


@router.get("/audit")
async def founder_qa_audit(request: Request, limit: int = 20) -> dict[str, Any]:
    _authorize_console(request, mutating=False)
    try:
        hx.assert_harness_allowed()
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"ok": True, "events": hx.list_audit_events(limit=limit)}


def _run_preset(
    *,
    request: Request,
    body: PresetBody,
    preset: str,
) -> dict[str, Any]:
    actor = _authorize_console(request, mutating=True)
    try:
        session_id = _resolve_session_id(body.session_id, actor)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        if preset == "fresh":
            result = hx.preset_fresh_customer(session_id=session_id, confirm=body.confirm, actor=actor)
        elif preset == "active":
            result = hx.preset_active_claim(session_id=session_id, confirm=body.confirm, actor=actor)
        elif preset == "request_more":
            result = hx.preset_request_more(session_id=session_id, confirm=body.confirm, actor=actor)
        else:
            raise HTTPException(status_code=400, detail="unknown_preset")
    except ValueError as exc:
        code = str(exc)
        hx.record_audit_event(
            {
                "preset": preset,
                "ok": False,
                "actor": actor,
                "identity_masked": hx.mask_identity(session_id),
                "error": code,
                "source": "founder_qa_console",
            }
        )
        raise HTTPException(status_code=400, detail=code) from exc
    except RuntimeError as exc:
        logger.warning("founder_qa_preset_failed preset=%s err=%s", preset, exc)
        hx.record_audit_event(
            {
                "preset": preset,
                "ok": False,
                "actor": actor,
                "identity_masked": hx.mask_identity(session_id),
                "error": str(exc),
                "partial": True,
                "source": "founder_qa_console",
            }
        )
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    safe = hx.sanitize_preset_result_for_console(result)
    status = hx.console_status(actor=actor, authorized=True)
    return {
        "ok": bool(safe.get("ok")),
        "preset": safe.get("preset") or preset,
        "result": safe,
        "status": status,
    }


@router.post("/presets/fresh")
async def founder_qa_fresh(body: PresetBody, request: Request) -> dict[str, Any]:
    return _run_preset(request=request, body=body, preset="fresh")


@router.post("/presets/active")
async def founder_qa_active(body: PresetBody, request: Request) -> dict[str, Any]:
    return _run_preset(request=request, body=body, preset="active")


@router.post("/presets/request-more")
async def founder_qa_request_more(body: PresetBody, request: Request) -> dict[str, Any]:
    return _run_preset(request=request, body=body, preset="request_more")
