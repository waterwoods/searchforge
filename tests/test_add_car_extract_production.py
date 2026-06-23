"""Production-safe add-car extract behavior — no silent mock fallback."""

from __future__ import annotations

import pytest

from services.fiqa_api.routes import add_car as route


def test_allow_mock_extraction_false_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "prod")
    assert route._allow_mock_extraction() is False


def test_allow_mock_extraction_true_in_local_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    assert route._allow_mock_extraction() is True


def test_raise_extraction_failed_structured_detail() -> None:
    with pytest.raises(Exception) as exc:
        route._raise_extraction_failed("quota exceeded")
    err = exc.value
    assert getattr(err, "status_code", None) == 422
    detail = getattr(err, "detail", {})
    assert detail.get("extraction_failed") is True
    assert "couldn't read" in str(detail.get("message", "")).lower()
    assert detail.get("message_zh")
    assert detail.get("reason") == "quota exceeded"
