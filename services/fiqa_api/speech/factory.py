"""Resolve the active SpeechProvider (Google Chirp only in P28)."""

from __future__ import annotations

from services.fiqa_api.speech.google_chirp import GoogleChirpSpeechProvider
from services.fiqa_api.speech.provider import SpeechProvider

_provider: SpeechProvider | None = None


def get_speech_provider() -> SpeechProvider:
    global _provider
    if _provider is None:
        _provider = GoogleChirpSpeechProvider()
    return _provider


def set_speech_provider_for_tests(provider: SpeechProvider | None) -> None:
    """Test seam only — not a second production provider."""
    global _provider
    _provider = provider
