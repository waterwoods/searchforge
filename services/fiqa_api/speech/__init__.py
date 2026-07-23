"""P28 Voice Story — SpeechProvider boundary (business never imports Google SDK)."""

from services.fiqa_api.speech.factory import get_speech_provider
from services.fiqa_api.speech.provider import (
    SpeechErrorKind,
    SpeechProvider,
    SpeechProviderError,
    TranscriptDraft,
    TranscribeOptions,
)

__all__ = [
    "SpeechErrorKind",
    "SpeechProvider",
    "SpeechProviderError",
    "TranscriptDraft",
    "TranscribeOptions",
    "get_speech_provider",
]
