"""P28 Voice Story orchestration — draft STT + confirm audit on existing story path."""

from __future__ import annotations

import logging
from typing import Any

from services.fiqa_api.inbox_triage.h5_task_token import VerifiedH5TaskToken
from services.fiqa_api.speech.factory import get_speech_provider
from services.fiqa_api.speech.metrics import emit_voice_metric, normalized_levenshtein
from services.fiqa_api.speech.provider import (
    SpeechErrorKind,
    SpeechProviderError,
    TranscribeOptions,
)

logger = logging.getLogger(__name__)

# Happy Path defaults (ADR remaining risk #2).
MAX_AUDIO_BYTES = 5 * 1024 * 1024
MAX_RECORDING_DURATION_MS = 60_000


def transcribe_story_audio_bytes(
    *,
    audio_bytes: bytes,
    content_type: str | None = None,
    filename: str | None = None,
    recording_duration_ms: int | None = None,
    metric_case_id: str | None = None,
    metric_surface: str = "story_task",
) -> dict[str, Any]:
    """
    Upload → SpeechProvider → transcript draft.

    Does NOT write known_facts or mark any task complete.
    Shared by Story task token path and Start Claim (pre-case) path.
    """
    size = len(audio_bytes or b"")
    if size <= 0:
        raise SpeechProviderError(SpeechErrorKind.UNSUPPORTED_MEDIA, "empty_audio")
    if size > MAX_AUDIO_BYTES:
        raise SpeechProviderError(
            SpeechErrorKind.UNSUPPORTED_MEDIA,
            "audio_too_large",
            detail=f"max_bytes={MAX_AUDIO_BYTES}",
        )

    duration = _clamp_duration(recording_duration_ms)
    metric_id = (metric_case_id or "").strip() or None
    emit_voice_metric(
        "stt_attempt",
        case_id=metric_id,
        surface=metric_surface,
        audio_bytes=size,
        recording_duration_ms=duration,
        content_type=content_type or "",
    )
    if duration is not None:
        emit_voice_metric(
            "recording_duration_ms",
            case_id=metric_id,
            surface=metric_surface,
            recording_duration_ms=duration,
        )

    provider = get_speech_provider()
    try:
        draft = provider.transcribe(
            audio_bytes,
            TranscribeOptions(
                content_type=content_type,
                filename=filename,
            ),
        )
    except SpeechProviderError as exc:
        emit_voice_metric(
            "stt_failure",
            case_id=metric_id,
            surface=metric_surface,
            error_kind=exc.kind.value,
            message=exc.message,
            recording_duration_ms=duration,
        )
        raise

    emit_voice_metric(
        "stt_success",
        case_id=metric_id,
        surface=metric_surface,
        provider_id=draft.provider_id,
        stt_latency_ms=draft.stt_latency_ms,
        transcript_chars=len(draft.raw_transcript),
        recording_duration_ms=duration,
    )
    # Audio retention default: discard-after-transcribe (P8). No blob store here.
    return {
        "raw_transcript": draft.raw_transcript,
        "speech_provider": draft.provider_id,
        "stt_latency_ms": draft.stt_latency_ms,
        "recording_duration_ms": duration,
        "audio_retained": False,
    }


def transcribe_story_audio(
    claims: VerifiedH5TaskToken,
    *,
    audio_bytes: bytes,
    content_type: str | None = None,
    filename: str | None = None,
    recording_duration_ms: int | None = None,
) -> dict[str, Any]:
    """
    Token-bound Story task path → same draft STT as Start Claim.

    Does NOT write known_facts or mark the story task complete.
    """
    if not claims.is_intake_form_token:
        raise ValueError("unsupported_flow")
    return transcribe_story_audio_bytes(
        audio_bytes=audio_bytes,
        content_type=content_type,
        filename=filename,
        recording_duration_ms=recording_duration_ms,
        metric_case_id=claims.case_id,
        metric_surface="story_task",
    )


def build_voice_audit_metadata(
    *,
    raw_transcript: str,
    confirmed_story: str,
    speech_provider: str | None = None,
    stt_latency_ms: int | None = None,
    recording_duration_ms: int | None = None,
) -> dict[str, Any]:
    """Audit extras for the existing story confirm timeline event."""
    raw = (raw_transcript or "").strip()
    confirmed = (confirmed_story or "").strip()
    dist, norm = normalized_levenshtein(raw, confirmed)
    meta: dict[str, Any] = {
        "source": "voice",
        "raw_transcript": raw,
        "confirmed_story": confirmed,
        "speech_provider": (speech_provider or "").strip() or "google_chirp",
        "edit_distance": dist,
        "edit_distance_normalized": norm,
        "audio_retained": False,
    }
    if stt_latency_ms is not None:
        meta["stt_latency_ms"] = int(stt_latency_ms)
    if recording_duration_ms is not None:
        meta["recording_duration_ms"] = int(recording_duration_ms)
    return meta


def emit_voice_confirm_metrics(case_id: str, voice_meta: dict[str, Any]) -> None:
    emit_voice_metric(
        "voice_confirm",
        case_id=case_id,
        speech_provider=voice_meta.get("speech_provider"),
        edit_distance=voice_meta.get("edit_distance"),
        edit_distance_normalized=voice_meta.get("edit_distance_normalized"),
        recording_duration_ms=voice_meta.get("recording_duration_ms"),
        stt_latency_ms=voice_meta.get("stt_latency_ms"),
        raw_chars=len(str(voice_meta.get("raw_transcript") or "")),
        confirmed_chars=len(str(voice_meta.get("confirmed_story") or "")),
    )


def _clamp_duration(value: int | None) -> int | None:
    if value is None:
        return None
    try:
        ms = int(value)
    except (TypeError, ValueError):
        return None
    if ms < 0:
        return None
    return min(ms, MAX_RECORDING_DURATION_MS)
