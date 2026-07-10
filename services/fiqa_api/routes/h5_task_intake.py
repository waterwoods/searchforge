"""H5 Claim structured intake API (P19H-3h-1A)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from services.fiqa_api.inbox_triage.h5_task_intake import (
    intake_info_for_token,
    patch_intake_fields,
    submit_intake_form,
)
from services.fiqa_api.inbox_triage.h5_task_token import verify_h5_task_token

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
