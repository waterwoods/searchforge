"""H5 guided single-slot upload API (P19D-2)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from services.fiqa_api.inbox_triage.h5_task_token import verify_h5_task_token
from services.fiqa_api.inbox_triage.h5_task_upload import (
    ingest_h5_single_slot_upload,
    task_info_for_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/h5", tags=["h5-task-upload"])


def _verify_or_403(task_token: str):
    claims = verify_h5_task_token(task_token)
    if claims is None:
        raise HTTPException(status_code=403, detail="invalid_or_expired_task_link")
    return claims


@router.get("/tasks/{task_token}")
async def get_h5_task(task_token: str) -> dict[str, Any]:
    """Return current slot task metadata for H5 page (no auth — token is credential)."""
    claims = _verify_or_403(task_token)
    return task_info_for_token(claims)


@router.post("/tasks/{task_token}/upload")
async def upload_h5_task_attachment(
    task_token: str,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """
    Upload exactly one image for the signed H5 task slot.
    Token binds case + slot; no broker login required.
    """
    claims = _verify_or_403(task_token)
    content = await file.read()
    try:
        return ingest_h5_single_slot_upload(
            claims,
            content=content,
            content_type=file.content_type,
            filename=file.filename,
        )
    except ValueError as exc:
        code = str(exc)
        if code in ("case_not_found",):
            raise HTTPException(status_code=404, detail=code) from exc
        if code in ("invalid_or_expired_task_link", "case_mismatch", "lane_mismatch", "user_ref_mismatch"):
            raise HTTPException(status_code=403, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc
