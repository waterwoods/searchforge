"""H5 Claim structured intake API (P19H-3h-1A)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, File, Form, Header, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field, field_validator

from services.fiqa_api.inbox_triage.h5_task_intake import (
    intake_info_for_token,
    patch_intake_fields,
    submit_intake_form,
)
from services.fiqa_api.inbox_triage.h5_task_token import verify_h5_task_token
from services.fiqa_api.inbox_triage.mp_customer_identity import establish_mp_customer_session
from services.fiqa_api.inbox_triage.p0_customer_context import resolve_customer_context
from services.fiqa_api.inbox_triage.p20_customer_start_claim import (
    customer_start_claim_response,
    start_customer_claim,
)
from services.fiqa_api.inbox_triage.p20_slice1_command_service import default_slice1_service
from services.fiqa_api.inbox_triage.voice_story import (
    transcribe_story_audio,
    transcribe_story_audio_bytes,
)
from services.fiqa_api.speech.metrics import emit_voice_metric
from services.fiqa_api.speech.provider import SpeechProviderError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/h5", tags=["h5-task-intake"])


def _verify_or_403(task_token: str):
    claims = verify_h5_task_token(task_token)
    if claims is None:
        raise HTTPException(status_code=403, detail="invalid_or_expired_task_link")
    return claims


class VoiceStoryAuditBody(BaseModel):
    """Optional P28 voice provenance — never written into known_facts directly."""

    raw_transcript: str = Field(default="", max_length=4000)
    confirmed_story: str | None = Field(default=None, max_length=2000)
    speech_provider: str | None = Field(default=None, max_length=64)
    stt_latency_ms: int | None = Field(default=None, ge=0, le=600_000)
    recording_duration_ms: int | None = Field(default=None, ge=0, le=600_000)

    @field_validator("stt_latency_ms", "recording_duration_ms", mode="before")
    @classmethod
    def _coerce_ms_fields(cls, value: Any) -> Any:
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            raise ValueError("invalid_ms")
        if isinstance(value, (int, float)):
            return int(round(float(value)))
        if isinstance(value, str) and value.strip():
            return int(round(float(value.strip())))
        return value


class H5IntakeFieldsBody(BaseModel):
    step: str = Field(..., min_length=1)
    fields: dict[str, str] = Field(default_factory=dict)
    voice_audit: VoiceStoryAuditBody | None = None


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
    """P29B — Mini Program wx.login code → opaque session identity."""

    code: str = Field(..., min_length=1, max_length=256)


class CustomerContextBody(BaseModel):
    """Established Mini Program identity → one server-owned customer context."""

    session_id: str = Field(..., min_length=8, max_length=128)
    launch_token: str | None = Field(default=None, max_length=4096)


@router.post("/customer/session")
async def post_customer_session(body: CustomerSessionBody) -> dict[str, Any]:
    """
    OpenID login flow (technical only).

    Returns opaque session_id only. Customer Context resolves routing next.
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
    }
    return safe


@router.post("/customer/context")
async def post_customer_context(body: CustomerContextBody) -> dict[str, Any]:
    """Resolve Active Case, resume token, and next action after identity."""
    try:
        return resolve_customer_context(
            session_id=body.session_id,
            launch_token=body.launch_token,
        )
    except ValueError as exc:
        code = str(exc)
        status = 404 if code == "case_not_found" else 403 if code == "invalid_or_expired_task_link" else 401
        raise HTTPException(status_code=status, detail=code) from exc


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


@router.post("/customer/start-claim/story/voice-event")
async def post_start_claim_story_voice_event(
    body: dict[str, Any],
) -> dict[str, Any]:
    """P30: same voice_record_start metric hook before a case exists."""
    event = str((body or {}).get("event") or "").strip()
    if event not in ("voice_record_start",):
        raise HTTPException(status_code=400, detail="unsupported_voice_event")
    emit_voice_metric(
        event,
        surface="start_claim",
        session_id=str((body or {}).get("session_id") or "")[:80] or None,
        recording_duration_ms=(body or {}).get("recording_duration_ms"),
    )
    return {"ok": True, "event": event}


@router.post("/customer/start-claim/story/transcribe")
async def post_start_claim_story_transcribe(
    file: UploadFile = File(...),
    recording_duration_ms: int | None = Form(default=None),
    session_id: str | None = Form(default=None),
) -> dict[str, Any]:
    """
    P30 consistency: Start Claim Voice Story draft STT (pre-case).

    Same SpeechProvider as token Story path. Does not create a case or write facts.
    """
    content = await file.read()
    filename = str(file.filename or "")
    content_type = str(file.content_type or "")
    session_key = str(session_id or "").strip()[:80]
    logger.info(
        "p28_voice_transcribe_request %s",
        {
            "surface": "start_claim",
            "has_session": bool(session_key),
            "content_type": content_type,
            "filename_ext": filename.rsplit(".", 1)[-1].lower() if "." in filename else "",
            "byte_length": len(content or b""),
            "recording_duration_ms": recording_duration_ms,
            "multipart_field": "file",
        },
    )
    try:
        result = transcribe_story_audio_bytes(
            audio_bytes=content,
            content_type=content_type,
            filename=filename,
            recording_duration_ms=recording_duration_ms,
            metric_case_id=None,
            metric_surface="start_claim",
        )
        logger.info(
            "p28_voice_transcribe_ok %s",
            {
                "surface": "start_claim",
                "speech_provider": result.get("speech_provider"),
                "stt_latency_ms": result.get("stt_latency_ms"),
                "transcript_chars": len(str(result.get("raw_transcript") or "")),
            },
        )
        return result
    except SpeechProviderError as exc:
        status = 422 if exc.kind.value in ("unsupported_media", "empty") else 503
        if exc.kind.value == "fatal":
            status = 503
        logger.warning(
            "p28_voice_transcribe_fail %s",
            {
                "surface": "start_claim",
                "http_status": status,
                "error_kind": exc.kind.value,
                "message": exc.message,
                "detail": (exc.detail or "")[:240],
                "content_type": content_type,
                "byte_length": len(content or b""),
            },
        )
        raise HTTPException(status_code=status, detail=exc.as_dict()) from exc


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
    voice_audit = body.voice_audit.model_dump() if body.voice_audit else None
    try:
        return patch_intake_fields(
            claims,
            step=body.step,
            fields=body.fields,
            voice_audit=voice_audit,
        )
    except ValueError as exc:
        code = str(exc)
        if code == "case_not_found":
            raise HTTPException(status_code=404, detail=code) from exc
        if code in ("lane_mismatch", "unsupported_flow"):
            raise HTTPException(status_code=403, detail=code) from exc
        if code == "already_submitted":
            raise HTTPException(status_code=409, detail=code) from exc
        if code == "case_closed_read_only":
            raise HTTPException(status_code=409, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc


@router.post("/tasks/{task_token}/story/voice-event")
async def post_story_voice_event(
    task_token: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    """Lightweight metrics hook (e.g. voice_record_start). No case fact writes."""
    claims = _verify_or_403(task_token)
    event = str((body or {}).get("event") or "").strip()
    if event not in ("voice_record_start",):
        raise HTTPException(status_code=400, detail="unsupported_voice_event")
    emit_voice_metric(
        event,
        case_id=claims.case_id,
        recording_duration_ms=(body or {}).get("recording_duration_ms"),
    )
    return {"ok": True, "event": event}


@router.post("/tasks/{task_token}/story/transcribe")
async def post_story_transcribe(
    task_token: str,
    file: UploadFile = File(...),
    recording_duration_ms: int | None = Form(default=None),
) -> dict[str, Any]:
    """
    P28 Happy Path: upload audio → SpeechProvider (Chirp) → editable transcript draft.

    Does not write accident_description. STT failure is recoverable (type manually).
    """
    claims = _verify_or_403(task_token)
    content = await file.read()
    filename = str(file.filename or "")
    content_type = str(file.content_type or "")
    logger.info(
        "p28_voice_transcribe_request %s",
        {
            "case_id": claims.case_id,
            "content_type": content_type,
            "filename_ext": filename.rsplit(".", 1)[-1].lower() if "." in filename else "",
            "byte_length": len(content or b""),
            "recording_duration_ms": recording_duration_ms,
            "multipart_field": "file",
        },
    )
    try:
        result = transcribe_story_audio(
            claims,
            audio_bytes=content,
            content_type=content_type,
            filename=filename,
            recording_duration_ms=recording_duration_ms,
        )
        logger.info(
            "p28_voice_transcribe_ok %s",
            {
                "case_id": claims.case_id,
                "speech_provider": result.get("speech_provider"),
                "stt_latency_ms": result.get("stt_latency_ms"),
                "transcript_chars": len(str(result.get("raw_transcript") or "")),
            },
        )
        return result
    except SpeechProviderError as exc:
        status = 422 if exc.kind.value in ("unsupported_media", "empty") else 503
        if exc.kind.value == "fatal":
            status = 503
        logger.warning(
            "p28_voice_transcribe_fail %s",
            {
                "case_id": claims.case_id,
                "http_status": status,
                "error_kind": exc.kind.value,
                "message": exc.message,
                "detail": (exc.detail or "")[:240],
                "content_type": content_type,
                "byte_length": len(content or b""),
            },
        )
        raise HTTPException(status_code=status, detail=exc.as_dict()) from exc
    except ValueError as exc:
        code = str(exc)
        if code == "case_not_found":
            raise HTTPException(status_code=404, detail=code) from exc
        if code in ("lane_mismatch", "unsupported_flow"):
            raise HTTPException(status_code=403, detail=code) from exc
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
        if code == "case_closed_read_only":
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
        if code == "case_closed_read_only":
            raise HTTPException(status_code=409, detail=code) from exc
        raise HTTPException(status_code=422, detail={"error": code}) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    outcome = str(result.get("outcome") or "")
    if outcome == "conflict":
        raise HTTPException(status_code=409, detail=result)
    if outcome == "rejected":
        err = str(result.get("error_code") or "")
        if err == "case_closed_read_only":
            raise HTTPException(status_code=409, detail=err)
        raise HTTPException(status_code=422, detail=result)
    return result
