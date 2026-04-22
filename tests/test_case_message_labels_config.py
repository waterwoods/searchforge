"""case source_text [customer]/[system] labels are configurable (triage client plug point)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.fiqa_api.inbox_triage import config_loader as cl


def test_case_message_labels_default_when_no_file(monkeypatch):
    monkeypatch.setattr(cl, "_load_json", lambda _path: None)
    lab = cl.get_case_message_labels()
    assert lab["customer"] == "客户"
    assert lab["system"] == "系统"


def test_build_source_uses_config_message_labels(monkeypatch):
    # case_store binds the import; patch where it is used
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.case_store.get_case_message_labels",
        lambda: {"customer": "CUST", "system": "SYS"},
    )
    from services.fiqa_api.inbox_triage.case_store import _build_source_from_messages as build_src

    msg = [
        {
            "message_id": "m1",
            "role": "customer",
            "text": "hello",
            "created_at": "2026-01-01T00:00:00Z",
            "sequence": 1,
        }
    ]
    assert build_src(msg) == "[CUST] hello"
