"""H5 Claim structured intake API (P19H-3h-1A)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel, Field

from services.fiqa_api.inbox_triage.h5_task_intake import (
    intake_info_for_token,
    patch_intake_fields,
    submit_intake_form,
)
from services.fiqa_api.inbox_triage.h5_task_token import verify_h5_task_token
from services.fiqa_api.inbox_triage.mp_customer_identity import establish_mp_customer_session
from services.fiqa_api.inbox_triage.p20_customer_start_claim import (
    customer_start_claim_response,
    start_customer_claim,
)
from services.fiqa_api.inbox_triage.p20_slice1_command_service import default_slice1_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/h5", tags=["h5-task-intake"])


def _verify_or_403(task_token: str):
    claims = verify_h5_task_token(task_token)
    if claims is None:
        raise HTTPException(status_code=403, detail="invalid_or_expired_task_link")
    return claims


class H5IntakeFieldsBody(BaseModel):
    step: str = Field(..., min_length=1)
    fields: dict[str, str] = Field(default_factory=dict)


class H5IntakeSubmitBody(BaseModel):
    submit_intent_id: str = Field(..., min_length=8)


class H5RequestItemSubmitBody(BaseModel):
    command_id: str = Field(..., min_length=8)
    idempotency_key: str = Field(..., min_length=8)
    expected_case_version: int = Field(..., ge=0)
    client_draft_id: str | None = Field(default=None)
    fact: dict[str, Any] | None = Field(default=None)
    evidence: dict[str, Any] | None = Field(default=None)


class CustomerStartClaimBody(BaseModel):
    """Mini Program cold-start Claim — thin facade over Cap2 CreateClaim."""

    command_id: str = Field(..., min_length=8, max_length=128)
    idempotency_key: str = Field(..., min_length=8, max_length=128)
    correlation_id: str | None = Field(default=None, max_length=128)
    session_id: str | None = Field(default=None, max_length=128)
    accident_description: str | None = Field(default=None, max_length=2000)
    accident_datetime: str | None = Field(default=None, max_length=120)
    accident_location: str | None = Field(default=None, max_length=500)
    injury_status: str | None = Field(default=None, max_length=32)
    is_test: bool = Field(default=False)


class CustomerSessionBody(BaseModel):
    """P29B — Mini Program wx.login code → opaque session + optional resume."""

    code: str = Field(..., min_length=1, max_length=256)


@router.post("/customer/session")
async def post_customer_session(body: CustomerSessionBody) -> dict[str, Any]:
    """
    OpenID login flow (technical only).

    Returns opaque session_id + optional resume_token when an Active Case exists.
    Never returns OpenID.
    """
    result = await establish_mp_customer_session(body.code)
    if not result.get("ok"):
        code = str(result.get("error_code") or "login_failed")
        status = 503 if code in ("wechat_mp_not_configured", "token_http_error") else 401
        raise HTTPException(status_code=status, detail=code)
    # Strip any accidental identity leakage keys.
    safe = {
        "ok": True,
        "session_id": result.get("session_id"),
        "has_active_case": bool(result.get("has_active_case")),
    }
    if result.get("resume_token"):
        safe["resume_token"] = result.get("resume_token")
    if result.get("resume_expires_at"):
        safe["resume_expires_at"] = result.get("resume_expires_at")
    return safe


@router.post("/customer/start-claim")
async def post_customer_start_claim(
    body: CustomerStartClaimBody,
    http_response: Response,
) -> dict[str, Any]:
    """Customer Start Claim → existing Cap2 CreateClaim (no second command)."""
    try:
        result = start_customer_claim(
            command_id=body.command_id,
            idempotency_key=body.idempotency_key,
            correlation_id=body.correlation_id,
            session_id=body.session_id,
            accident_description=body.accident_description,
            accident_datetime=body.accident_datetime,
            accident_location=body.accident_location,
            injury_status=body.injury_status,
            is_test=body.is_test,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": str(exc)}) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    outcome = str(result.get("outcome") or "")
    if outcome == "accepted":
        http_response.status_code = 201
        return customer_start_claim_response(result)
    if outcome in ("replayed", "resumed"):
        # Idempotent Cap2 replay or One Active Case resume — both are success.
        http_response.status_code = 200
        return customer_start_claim_response(result)
    raise HTTPException(status_code=422, detail=customer_start_claim_response(result))


@router.get("/tasks/{task_token}/intake")
async def get_h5_intake(task_token: str) -> dict[str, Any]:
    """Return Claim intake wizard state for H5 task page."""
    claims = _verify_or_403(task_token)
    try:
        return intake_info_for_token(claims)
    except ValueError as exc:
        code = str(exc)
        if code == "case_not_found":
            raise HTTPException(status_code=404, detail=code) from exc
        if code in ("lane_mismatch", "unsupported_flow"):
            raise HTTPException(status_code=403, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc


@router.patch("/tasks/{task_token}/fields")
async def patch_h5_intake_fields(
    task_token: str,
    body: H5IntakeFieldsBody,
) -> dict[str, Any]:
    """Persist one wizard step's fields to known_facts + claim_timeline."""
    claims = _verify_or_403(task_token)
    try:
        return patch_intake_fields(claims, step=body.step, fields=body.fields)
    except ValueError as exc:
        code = str(exc)
        if code == "case_not_found":
            raise HTTPException(status_code=404, detail=code) from exc
        if code in ("lane_mismatch", "unsupported_flow"):
            raise HTTPException(status_code=403, detail=code) from exc
        if code == "already_submitted":
            raise HTTPException(status_code=409, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc


@router.post("/tasks/{task_token}/submit")
async def submit_h5_intake(
    task_token: str,
    body: H5IntakeSubmitBody,
    x_submit_intent_id: str | None = Header(default=None, alias="X-Submit-Intent-Id"),
) -> dict[str, Any]:
    """Final customer handoff — idempotent via submit_intent_id."""
    claims = _verify_or_403(task_token)
    intent = (x_submit_intent_id or body.submit_intent_id or "").strip()
    try:
        return submit_intake_form(claims, submit_intent_id=intent)
    except ValueError as exc:
        code = str(exc)
        if code == "case_not_found":
            raise HTTPException(status_code=404, detail=code) from exc
        if code in ("lane_mismatch", "unsupported_flow"):
            raise HTTPException(status_code=403, detail=code) from exc
        if code in ("already_submitted",):
            raise HTTPException(status_code=409, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc


@router.post("/tasks/{task_token}/request-items/{item_id}/submit")
async def submit_h5_request_item(
    task_token: str,
    item_id: str,
    body: H5RequestItemSubmitBody,
) -> dict[str, Any]:
    """Slice 1 customer command: satisfy the active broker-requested item."""
    claims = _verify_or_403(task_token)
    customer_identity = f"h5:{claims.user_ref or claims.nonce}"
    try:
        result = default_slice1_service().submit_request_item(
            case_id=claims.case_id,
            customer_id=customer_identity,
            active_request_item_id=item_id,
            command_id=body.command_id,
            idempotency_key=body.idempotency_key,
            expected_case_version=body.expected_case_version,
            client_draft_id=body.client_draft_id,
            fact=body.fact,
            evidence=body.evidence,
        )
    except ValueError as exc:
        code = str(exc)
        if code == "case_not_found":
            raise HTTPException(status_code=404, detail=code) from exc
        raise HTTPException(status_code=422, detail={"error": code}) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    outcome = str(result.get("outcome") or "")
    if outcome == "conflict":
        raise HTTPException(status_code=409, detail=result)
    if outcome == "rejected":
        raise HTTPException(status_code=422, detail=result)
    return result
