"""SpeechProvider interface — STT draft only; never case truth."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class SpeechErrorKind(str, Enum):
    RETRYABLE = "retryable"
    FATAL = "fatal"
    UNSUPPORTED_MEDIA = "unsupported_media"
    EMPTY = "empty"


class SpeechProviderError(Exception):
    """Typed STT failure for orchestration (not a case-state failure)."""

    def __init__(self, kind: SpeechErrorKind, message: str, *, detail: str | None = None):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.detail = detail or message

    def as_dict(self) -> dict[str, str]:
        # Include truncated provider detail for Founder/ops diagnosis (no audio/PII).
        out = {
            "error": "stt_failed",
            "error_kind": self.kind.value,
            "message": self.message,
        }
        detail = (self.detail or "").strip()
        if detail and detail != self.message:
            out["detail"] = detail[:240]
        return out


@dataclass(frozen=True)
class TranscribeOptions:
    # Chirp 2 in us-central1 allows one language code (not multi-lang us/global).
    # Simplified Chinese BCP-47 for Chirp is cmn-Hans-CN (zh-CN is rejected).
    language_codes: tuple[str, ...] = ("cmn-Hans-CN",)
    content_type: str | None = None
    filename: str | None = None


@dataclass(frozen=True)
class TranscriptDraft:
    raw_transcript: str
    provider_id: str
    stt_latency_ms: int
    confidence: float | None = None


class SpeechProvider(ABC):
    @abstractmethod
    def provider_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def transcribe(self, audio_bytes: bytes, options: TranscribeOptions | None = None) -> TranscriptDraft:
        raise NotImplementedError

    def health(self) -> dict[str, Any]:
        return {"provider_id": self.provider_id(), "ok": True}
