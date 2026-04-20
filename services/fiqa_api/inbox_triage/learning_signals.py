"""Lightweight learning / feedback memory (PTD §12) — append-only JSONL, no ML."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_PATH = _REPO_ROOT / "data" / "learning_signals" / "signals.jsonl"


def _path() -> Path:
    raw = (os.environ.get("LEARNING_SIGNALS_PATH") or "").strip()
    return Path(raw) if raw else _DEFAULT_PATH


def _append_line(payload: dict[str, Any]) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False, default=str) + "\n"
    p.open("a", encoding="utf-8").write(line)


def record_user_correction_signal(
    *,
    session_id: str | None,
    case_id: str | None,
    field_key: str,
    prior_value: str | None,
    new_value: str | None,
    source: str = "thread",
    metadata: dict[str, Any] | None = None,
) -> None:
    """User corrected an inferred or collected field — future default/inference tuning."""
    _append_line(
        {
            "kind": "user_correction",
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": (session_id or "").strip(),
            "case_id": (case_id or "").strip(),
            "field_key": str(field_key).strip(),
            "prior_value": prior_value,
            "new_value": new_value,
            "source": source,
            "metadata": dict(metadata or {}),
        }
    )


def record_broker_field_edit_signal(
    *,
    case_id: str | None,
    fields_touched: list[str],
    source: str = "workbench",
    metadata: dict[str, Any] | None = None,
) -> None:
    """Broker completed or edited fields post-handoff — ground truth for drift analysis."""
    _append_line(
        {
            "kind": "broker_field_edit",
            "ts": datetime.now(timezone.utc).isoformat(),
            "case_id": (case_id or "").strip(),
            "fields_touched": [str(x) for x in (fields_touched or []) if str(x).strip()],
            "source": source,
            "metadata": dict(metadata or {}),
        }
    )
