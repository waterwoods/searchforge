"""Google Speech-to-Text Chirp adapter — only module that may import Google STT SDK."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from services.fiqa_api.speech.provider import (
    SpeechErrorKind,
    SpeechProvider,
    SpeechProviderError,
    TranscriptDraft,
    TranscribeOptions,
)

logger = logging.getLogger(__name__)

PROVIDER_ID = "google_chirp"

# WeChat recorder Happy Path uses mp3; Chirp auto-decode also accepts aac/wav/flac.
_SUPPORTED_HINTS = (
    "audio/mpeg",
    "audio/mp3",
    "audio/mpeg3",
    "audio/x-mpeg-3",
    "audio/mp4",
    "audio/aac",
    "audio/x-aac",
    "audio/wav",
    "audio/x-wav",
    "audio/flac",
    "application/octet-stream",
)


def _project_id() -> str:
    explicit = (
        os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT")
        or os.getenv("GCLOUD_PROJECT")
        or ""
    ).strip()
    if explicit:
        return explicit
    # Cloud Run often omits GOOGLE_CLOUD_PROJECT in --set-env-vars; ADC still knows the project.
    try:
        import google.auth

        _, project = google.auth.default()
        return str(project or "").strip()
    except Exception:  # noqa: BLE001 — config probe only
        return ""


def _location() -> str:
    # Chirp 2 is regional (us-central1 / europe-west4 / asia-southeast1), not multi-region "us".
    return (
        os.getenv("SPEECH_LOCATION") or os.getenv("GOOGLE_SPEECH_LOCATION") or "us-central1"
    ).strip()


def _model() -> str:
    return (os.getenv("SPEECH_CHIRP_MODEL") or "chirp_2").strip() or "chirp_2"


class GoogleChirpSpeechProvider(SpeechProvider):
    """First (and only P28) concrete SpeechProvider."""

    def provider_id(self) -> str:
        return PROVIDER_ID

    def health(self) -> dict[str, Any]:
        project = _project_id()
        ok = bool(project)
        return {
            "provider_id": self.provider_id(),
            "ok": ok,
            "project_configured": ok,
            "location": _location(),
            "model": _model(),
        }

    def transcribe(self, audio_bytes: bytes, options: TranscribeOptions | None = None) -> TranscriptDraft:
        opts = options or TranscribeOptions()
        if not audio_bytes:
            raise SpeechProviderError(SpeechErrorKind.UNSUPPORTED_MEDIA, "empty_audio")

        content_type = (opts.content_type or "").strip().lower()
        if content_type and content_type not in _SUPPORTED_HINTS and not content_type.startswith("audio/"):
            raise SpeechProviderError(
                SpeechErrorKind.UNSUPPORTED_MEDIA,
                "unsupported_media",
                detail=content_type,
            )

        project = _project_id()
        if not project:
            raise SpeechProviderError(
                SpeechErrorKind.FATAL,
                "speech_not_configured",
                detail="GOOGLE_CLOUD_PROJECT missing",
            )

        location = _location()
        model = _model()
        started = time.perf_counter()
        try:
            transcript = self._recognize(audio_bytes, project, location, model, opts.language_codes)
        except SpeechProviderError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK errors to taxonomy
            mapped = _map_sdk_error(exc)
            logger.warning(
                "google_chirp_transcribe_failed kind=%s detail=%s",
                mapped.kind.value,
                mapped.detail,
            )
            raise mapped from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        text = (transcript or "").strip()
        if not text:
            raise SpeechProviderError(SpeechErrorKind.EMPTY, "empty_transcript")

        return TranscriptDraft(
            raw_transcript=text,
            provider_id=self.provider_id(),
            stt_latency_ms=latency_ms,
        )

    def _recognize(
        self,
        audio_bytes: bytes,
        project: str,
        location: str,
        model: str,
        language_codes: tuple[str, ...],
    ) -> str:
        from google.api_core.client_options import ClientOptions
        from google.cloud.speech_v2 import SpeechClient
        from google.cloud.speech_v2.types import cloud_speech

        api_endpoint = f"{location}-speech.googleapis.com"
        client = SpeechClient(client_options=ClientOptions(api_endpoint=api_endpoint))
        recognizer = f"projects/{project}/locations/{location}/recognizers/_"
        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=list(language_codes) or ["cmn-Hans-CN"],
            model=model,
            features=cloud_speech.RecognitionFeatures(
                enable_automatic_punctuation=True,
            ),
        )
        request = cloud_speech.RecognizeRequest(
            recognizer=recognizer,
            config=config,
            content=audio_bytes,
        )
        response = client.recognize(request=request)
        parts: list[str] = []
        for result in response.results or []:
            alts = list(result.alternatives or [])
            if not alts:
                continue
            parts.append(str(alts[0].transcript or "").strip())
        return " ".join(p for p in parts if p).strip()


def _map_sdk_error(exc: Exception) -> SpeechProviderError:
    name = type(exc).__name__
    msg = str(exc) or name
    detail = f"{name}: {msg}"[:400]
    lower = f"{name} {msg}".lower()
    if (
        "does not exist in the location" in lower
        or "is not supported by the model" in lower
        or "unsupported" in lower
        or "invalid_argument" in lower
        or "invalid argument" in lower
        or "bad request" in lower
        or "field_violations" in lower
    ):
        # Config/compat errors should surface as unsupported_media (422), not opaque 503.
        return SpeechProviderError(SpeechErrorKind.UNSUPPORTED_MEDIA, "unsupported_media", detail=detail)
    if any(
        token in lower
        for token in (
            "deadline",
            "timeout",
            "unavailable",
            "temporarily",
            "resource exhausted",
            "429",
            "503",
            "500",
        )
    ):
        return SpeechProviderError(SpeechErrorKind.RETRYABLE, "stt_retryable", detail=detail)
    if "permission" in lower or "unauthenticated" in lower or "401" in lower or "403" in lower:
        return SpeechProviderError(SpeechErrorKind.FATAL, "stt_auth_failed", detail=detail)
    return SpeechProviderError(SpeechErrorKind.RETRYABLE, "stt_failed", detail=detail)
