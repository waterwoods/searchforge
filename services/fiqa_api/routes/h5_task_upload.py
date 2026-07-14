"""H5 guided upload API (P19D-2 single-slot / P19D-4A photo flow)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from services.fiqa_api.inbox_triage.h5_task_token import verify_h5_task_token
from services.fiqa_api.inbox_triage.h5_task_upload import (
    ingest_h5_slot_upload,
    skip_h5_flow_slot,
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
    """Return current slot/flow task metadata for H5 page (no auth — token is credential)."""
    claims = _verify_or_403(task_token)
    try:
        return task_info_for_token(claims)
    except ValueError as exc:
        code = str(exc)
        if code == "case_not_found":
            raise HTTPException(status_code=404, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc


@router.post("/tasks/{task_token}/upload")
async def upload_h5_task_attachment(
    task_token: str,
    request: Request,
    file: UploadFile = File(...),
    slot: str | None = Form(None),
) -> dict[str, Any]:
    """
    Upload exactly one image for the signed H5 task slot.
    Flow tokens require slot form field matching current step.
    """
    request_received_at = datetime.now(timezone.utc).isoformat()
    request_started_at = perf_counter()
    request_id = str(getattr(request.state, "request_id", "unknown"))
    claims = _verify_or_403(task_token)
    content = await file.read()
    timing: dict[str, int] = {
        "file_read_duration_ms": round((perf_counter() - request_started_at) * 1000),
    }
    try:
        response = ingest_h5_slot_upload(
            claims,
            slot=slot,
            content=content,
            content_type=file.content_type,
            filename=file.filename,
            timing=timing,
        )
        total_duration_ms = round((perf_counter() - request_started_at) * 1000)
        response["upload_measurement"] = {
            "request_id": request_id,
            "server_duration_ms": total_duration_ms,
        }
        logger.info(
            "h5_task_upload_timing %s",
            {
                "event": "upload_complete",
                "request_id": request_id,
                "request_received_at": request_received_at,
                "received_file_bytes": len(content),
                **timing,
                "total_server_duration_ms": total_duration_ms,
            },
        )
        return response
    except ValueError as exc:
        code = str(exc)
        if code in ("case_not_found",):
            raise HTTPException(status_code=404, detail=code) from exc
        if code in (
            "invalid_or_expired_task_link",
            "case_mismatch",
            "lane_mismatch",
            "user_ref_mismatch",
        ):
            raise HTTPException(status_code=403, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc


@router.post("/tasks/{task_token}/skip")
async def skip_h5_task_slot(
    task_token: str,
    slot: str = Form(...),
    skip_reason: str | None = Form(None),
) -> dict[str, Any]:
    """Skip optional flow step (insurance_card_photo or Claim evidence slots)."""
    claims = _verify_or_403(task_token)
    try:
        return skip_h5_flow_slot(claims, slot=slot, skip_reason=skip_reason)
    except ValueError as exc:
        code = str(exc)
        if code in ("case_not_found",):
            raise HTTPException(status_code=404, detail=code) from exc
        if code in (
            "invalid_or_expired_task_link",
            "case_mismatch",
            "lane_mismatch",
            "user_ref_mismatch",
        ):
            raise HTTPException(status_code=403, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc
