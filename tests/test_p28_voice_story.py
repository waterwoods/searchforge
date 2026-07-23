"""P28 Voice Story Happy Path — SpeechProvider boundary + confirm write path."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.fiqa_api.inbox_triage.case_store import get_case_by_id, save_case
from services.fiqa_api.inbox_triage.h5_task_token import issue_h5_intake_form_token
from services.fiqa_api.routes.h5_task_intake import router as h5_intake_router
from services.fiqa_api.speech.factory import set_speech_provider_for_tests
from services.fiqa_api.speech.metrics import normalized_levenshtein
from services.fiqa_api.speech.provider import (
    SpeechErrorKind,
    SpeechProvider,
    SpeechProviderError,
    TranscriptDraft,
    TranscribeOptions,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


@pytest.fixture(autouse=True)
def _case_storage(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cases.json"
        path.write_text("[]", encoding="utf-8")
        monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(path))
        set_speech_provider_for_tests(None)
        yield
        set_speech_provider_for_tests(None)


class _FakeSpeechProvider(SpeechProvider):
    def __init__(self, draft: str = "我在红灯前被后车追尾了。", error: SpeechProviderError | None = None):
        self._draft = draft
        self._error = error
        self.calls = 0

    def provider_id(self) -> str:
        return "google_chirp"

    def transcribe(self, audio_bytes: bytes, options: TranscribeOptions | None = None) -> TranscriptDraft:
        self.calls += 1
        if self._error:
            raise self._error
        return TranscriptDraft(
            raw_transcript=self._draft,
            provider_id=self.provider_id(),
            stt_latency_ms=12,
        )


def _app() -> TestClient:
    app = FastAPI()
    app.include_router(h5_intake_router)
    return TestClient(app)


def _triage_stub() -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Collect claim basics via H5.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "claim_phase": "accident_basics_in_progress",
    }


def _save_claim_case() -> str:
    saved = save_case(
        "我要理赔",
        _triage_stub(),
        service_lane=SERVICE_LANE_CLAIM,
    )
    return str(saved.get("case_id") or "")


def test_normalized_levenshtein():
    dist, norm = normalized_levenshtein("abc", "abc")
    assert dist == 0 and norm == 0.0
    dist, norm = normalized_levenshtein("abc", "axc")
    assert dist == 1
    assert 0 < norm <= 1


def test_transcribe_returns_draft_without_writing_facts():
    case_id = _save_claim_case()
    token = issue_h5_intake_form_token(case_id=case_id)
    provider = _FakeSpeechProvider("对方变道刮到我左前门。")
    set_speech_provider_for_tests(provider)
    client = _app()

    resp = client.post(
        f"/api/h5/tasks/{token}/story/transcribe",
        files={"file": ("story.mp3", io.BytesIO(b"fake-mp3-bytes"), "audio/mpeg")},
        data={"recording_duration_ms": "3200"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["raw_transcript"] == "对方变道刮到我左前门。"
    assert body["speech_provider"] == "google_chirp"
    assert body["audio_retained"] is False
    assert provider.calls == 1

    case = get_case_by_id(case_id) or {}
    facts = case.get("known_facts") or {}
    assert not facts.get("accident_description")


def test_start_claim_transcribe_returns_same_draft_without_creating_case():
    """P30: Start Claim Voice Story uses the same SpeechProvider draft path."""
    from services.fiqa_api.inbox_triage.case_store import count_stored_cases

    before = count_stored_cases()
    provider = _FakeSpeechProvider("等红灯时被后车追尾了。")
    set_speech_provider_for_tests(provider)
    client = _app()

    resp = client.post(
        "/api/h5/customer/start-claim/story/transcribe",
        files={"file": ("story.mp3", io.BytesIO(b"fake-mp3-bytes"), "audio/mpeg")},
        data={"recording_duration_ms": "2800", "session_id": "wx_test_session"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["raw_transcript"] == "等红灯时被后车追尾了。"
    assert body["speech_provider"] == "google_chirp"
    assert body["audio_retained"] is False
    assert provider.calls == 1
    assert count_stored_cases() == before


def test_transcribe_failure_does_not_block_typed_confirm():
    case_id = _save_claim_case()
    token = issue_h5_intake_form_token(case_id=case_id)
    set_speech_provider_for_tests(
        _FakeSpeechProvider(error=SpeechProviderError(SpeechErrorKind.RETRYABLE, "stt_retryable"))
    )
    client = _app()

    fail = client.post(
        f"/api/h5/tasks/{token}/story/transcribe",
        files={"file": ("story.mp3", io.BytesIO(b"x"), "audio/mpeg")},
    )
    assert fail.status_code == 503
    detail = fail.json()["detail"]
    assert detail["error"] == "stt_failed"
    assert detail["error_kind"] == "retryable"

    ok = client.patch(
        f"/api/h5/tasks/{token}/fields",
        json={
            "step": "story",
            "fields": {"accident_description": "我打字描述事故经过，足够十个字以上。"},
        },
    )
    assert ok.status_code == 200, ok.text
    case = get_case_by_id(case_id) or {}
    assert "打字描述" in str((case.get("known_facts") or {}).get("accident_description") or "")


def test_voice_confirm_persists_raw_and_confirmed_updates_accident_description():
    case_id = _save_claim_case()
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()

    raw = "我在红灯前被后车追尾了。"
    confirmed = "我在红灯前被后车追尾，前保险杠受损。"
    resp = client.patch(
        f"/api/h5/tasks/{token}/fields",
        json={
            "step": "story",
            "fields": {"accident_description": confirmed},
            "voice_audit": {
                "raw_transcript": raw,
                "confirmed_story": confirmed,
                "speech_provider": "google_chirp",
                "stt_latency_ms": 40,
                "recording_duration_ms": 5000,
            },
        },
    )
    assert resp.status_code == 200, resp.text

    case = get_case_by_id(case_id) or {}
    facts = case.get("known_facts") or {}
    assert facts.get("accident_description") == confirmed
    assert facts.get("raw_transcript") in (None, "")

    state = case.get("h5_intake_state") or {}
    last_voice = state.get("last_voice_story") or {}
    assert last_voice.get("raw_transcript") == raw
    assert last_voice.get("confirmed_story") == confirmed

    timeline = case.get("claim_timeline") or []
    voice_events = [
        e
        for e in timeline
        if e.get("event_type") == "h5_step_complete"
        and (e.get("metadata") or {}).get("source") == "voice"
    ]
    assert len(voice_events) == 1
    voice_meta = (voice_events[0].get("metadata") or {}).get("voice") or {}
    assert voice_meta.get("raw_transcript") == raw
    assert voice_meta.get("confirmed_story") == confirmed
    assert voice_meta.get("speech_provider") == "google_chirp"
    assert isinstance(voice_meta.get("edit_distance"), int)


def test_business_layer_has_no_google_speech_import():
    """I-08: orchestration must not import Google STT SDK."""
    import services.fiqa_api.inbox_triage.h5_task_intake as intake_mod
    import services.fiqa_api.inbox_triage.voice_story as voice_mod

    for mod in (voice_mod, intake_mod):
        text = Path(mod.__file__ or "").read_text(encoding="utf-8")
        assert "google.cloud.speech" not in text
        assert "speech_v2" not in text


def test_voice_audit_accepts_float_timing_fields():
    """WeChat/JS Number may send fractional ms — must not 422 int_from_float."""
    case_id = _save_claim_case()
    token = issue_h5_intake_form_token(case_id=case_id)
    client = _app()
    confirmed = "我在红灯前被后车追尾，前保险杠受损。"
    resp = client.patch(
        f"/api/h5/tasks/{token}/fields",
        json={
            "step": "story",
            "fields": {"accident_description": confirmed},
            "voice_audit": {
                "raw_transcript": confirmed,
                "confirmed_story": confirmed,
                "speech_provider": "google_chirp",
                "stt_latency_ms": 1536.7,
                "recording_duration_ms": 4000.2,
            },
        },
    )
    assert resp.status_code == 200, resp.text
    case = get_case_by_id(case_id) or {}
    assert (case.get("known_facts") or {}).get("accident_description") == confirmed
