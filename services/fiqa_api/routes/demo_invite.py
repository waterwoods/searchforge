"""Chen Demo Invite HTTP surface — QA / non-Production only.

Support routes: issue / revoke / catalog / reset (Broker T3 foundation).
Customer route: redeem (binds temporary overlay; does not rewrite person_link).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from services.fiqa_api.inbox_triage import demo_invite as di
from services.fiqa_api.security.support_export_gate import assert_support_export_authorized

logger = logging.getLogger(__name__)

support_router = APIRouter(
    prefix="/api/inbox/support/demo-invite",
    tags=["demo-invite"],
)
customer_router = APIRouter(prefix="/api/h5/demo-invite", tags=["demo-invite"])


def _gate_support(request: Request) -> None:
    assert_support_export_authorized(request)
    try:
        di.assert_demo_invite_allowed()
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _map_value_error(exc: ValueError) -> HTTPException:
    code = str(exc)
    status = 403 if code in (
        "demo_invite_disabled",
        "demo_invite_disabled_production",
    ) else 400
    return HTTPException(status_code=status, detail=code)


class IssueBody(BaseModel):
    office_id: str = Field(..., min_length=1, max_length=256)
    scenario_id: str = Field(..., min_length=1, max_length=64)
    ttl_seconds: int | None = Field(default=None, ge=60, le=86400)
    max_uses: int | None = Field(default=None, ge=1, le=100)


class TokenBody(BaseModel):
    token: str = Field(..., min_length=8, max_length=256)
    office_id: str | None = Field(default=None, max_length=256)


class RevokeBody(BaseModel):
    token: str | None = Field(default=None, max_length=256)
    invite_id: str | None = Field(default=None, max_length=64)


class RedeemBody(BaseModel):
    token: str = Field(..., min_length=8, max_length=256)
    session_id: str = Field(..., min_length=8, max_length=80)
    office_id: str | None = Field(default=None, max_length=256)


class SessionBody(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=80)


class OfficeBody(BaseModel):
    office_id: str = Field(..., min_length=1, max_length=256)


@support_router.get("/catalog")
async def demo_invite_catalog(request: Request) -> dict[str, Any]:
    _gate_support(request)
    return {
        "ok": True,
        "is_demo": True,
        "demo_name": di.DEMO_NAME,
        "scenarios": di.list_catalog(),
    }


@support_router.post("/issue")
async def demo_invite_issue(body: IssueBody, request: Request) -> dict[str, Any]:
    _gate_support(request)
    try:
        issued = di.issue_demo_invite(
            office_id=body.office_id,
            scenario_id=body.scenario_id,
            ttl_seconds=body.ttl_seconds,
            max_uses=body.max_uses,
        )
    except ValueError as exc:
        raise _map_value_error(exc) from exc
    return {"ok": True, **issued}


@support_router.post("/validate")
async def demo_invite_validate(body: TokenBody, request: Request) -> dict[str, Any]:
    _gate_support(request)
    return di.validate_demo_invite(body.token, office_id=body.office_id)


@support_router.post("/revoke")
async def demo_invite_revoke(body: RevokeBody, request: Request) -> dict[str, Any]:
    _gate_support(request)
    try:
        return di.revoke_demo_invite(token=body.token, invite_id=body.invite_id)
    except ValueError as exc:
        raise _map_value_error(exc) from exc


@support_router.post("/reset-overlay")
async def demo_invite_reset_overlay(body: SessionBody, request: Request) -> dict[str, Any]:
    _gate_support(request)
    try:
        return di.reset_session_overlay(body.session_id)
    except ValueError as exc:
        raise _map_value_error(exc) from exc


@support_router.post("/reset-office")
async def demo_invite_reset_office(body: OfficeBody, request: Request) -> dict[str, Any]:
    _gate_support(request)
    try:
        return di.reset_office_demo_invites(body.office_id)
    except ValueError as exc:
        raise _map_value_error(exc) from exc


@customer_router.post("/redeem")
async def demo_invite_redeem(body: RedeemBody) -> dict[str, Any]:
    """Customer opens Demo Invite — bind temporary overlay to real session."""
    try:
        di.assert_demo_invite_allowed()
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    try:
        result = di.redeem_demo_invite(
            token=body.token,
            session_id=body.session_id,
            office_id=body.office_id,
        )
    except ValueError as exc:
        raise _map_value_error(exc) from exc

    # Never echo person_link / openid.
    safe = dict(result)
    safe.pop("person_link_key", None)
    safe.pop("openid", None)
    if not safe.get("ok"):
        # Soft-fail: 200 with fallback so Mini Program can blank-degrade cleanly.
        return safe
    return safe
