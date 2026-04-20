"""POST /api/inbox/triage: optional inline_image_base64 merges OCR into v6_ocr_signals."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.routes.inbox_triage import TriageRequest, triage_inbox


def test_empty_text_without_image_is_400():
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(triage_inbox(TriageRequest(text="")))
    assert excinfo.value.status_code == 400


def test_inline_image_empty_text_runs_triage(monkeypatch):
    def _fake_extract(_b64: str, _ct: str | None):
        return (
            "2020 Toyota Camry zip 92602 VIN 1HGCM82633A004352 delivery next week driver me",
            {"zip": {"value": "92602", "confidence": 0.6, "source": "ocr_regex"}},
            "test_engine",
        )

    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.v6_attachment_sidecar.extract_ocr_from_inline_base64",
        _fake_extract,
    )
    req = TriageRequest(
        text="",
        inline_image_base64="YQ==",
        inline_image_content_type="image/png",
        soft_route="add_car",
        client_id="chen_kui",
    )
    r = asyncio.run(triage_inbox(req))
    assert isinstance(r, dict)
    assert r.get("issue_category") or r.get("service_type") or r.get("client_reply_draft") is not None
