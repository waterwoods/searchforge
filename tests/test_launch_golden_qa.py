"""P25 — Launch Golden QA: preview prep, clear, concurrent lock, status."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.camry_golden_qa import configure_ephemeral_local
from scripts.golden_qa_preview import (
    clear_devtools_preview_tokens,
    prepare_devtools_preview,
    preview_has_session_token,
)
from scripts.launch_golden_qa import launch_golden_qa, public_status_view, read_launch_status


@pytest.fixture()
def golden_local(monkeypatch, tmp_path):
    configure_ephemeral_local()
    # Point private config + artifact dir into temp
    private = tmp_path / "project.private.config.json"
    private.write_text(
        json.dumps(
            {
                "condition": {
                    "miniprogram": {
                        "list": [
                            {
                                "name": "Start Claim (customer entry)",
                                "pathName": "pages/start-claim/start-claim",
                                "query": "",
                            },
                            {
                                "name": "pages/entry/entry (token via query only)",
                                "pathName": "pages/entry/entry",
                                "query": "",
                            },
                        ]
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("scripts.golden_qa_preview.PRIVATE_CONFIG", private)
    art = tmp_path / "last_reset"
    art.mkdir()
    monkeypatch.setattr("scripts.camry_golden_qa.ARTIFACT_DIR", art)
    yield {"private": private, "art": art}


def test_prepare_and_clear_preview(golden_local):
    token = "h5t1." + ("a" * 40)
    prep = prepare_devtools_preview(token)
    assert prep["ok"] is True
    assert preview_has_session_token() is True
    cfg = json.loads(golden_local["private"].read_text(encoding="utf-8"))
    entry = next(e for e in cfg["condition"]["miniprogram"]["list"] if e["pathName"] == "pages/entry/entry")
    assert entry["query"] == f"token={token}"

    cleared = clear_devtools_preview_tokens()
    assert cleared["ok"] is True
    assert cleared["cleared"] >= 1
    assert preview_has_session_token() is False


def test_launch_local_resets_and_prepares(golden_local, monkeypatch):
    result = launch_golden_qa(target="local", prepare_preview=True)
    assert result["ok"] is True
    assert result["status"] == "ready_to_scan"
    assert result["case_id"]
    assert result["preview_prepared"] is True
    assert preview_has_session_token() is True
    public = public_status_view(target="local")
    assert "devtools_launch_query" not in public
    assert public["case_id"] == result["case_id"]
    assert public["token_masked"]


def test_concurrent_launch_rejected(golden_local, monkeypatch):
    import scripts.launch_golden_qa as mod

    mod._LAUNCH_IN_FLIGHT = True
    try:
        blocked = launch_golden_qa(target="local", prepare_preview=False)
        assert blocked["ok"] is False
        assert "launch_already_in_progress" in str(blocked.get("failure_reason") or "")
    finally:
        mod._LAUNCH_IN_FLIGHT = False


def test_second_launch_fresh_token(golden_local):
    first = launch_golden_qa(target="local", prepare_preview=True)
    second = launch_golden_qa(target="local", prepare_preview=True)
    assert first["ok"] and second["ok"]
    assert first["case_id"] != second["case_id"]
    # Preview query updated to latest token
    cfg = json.loads(golden_local["private"].read_text(encoding="utf-8"))
    entry = next(e for e in cfg["condition"]["miniprogram"]["list"] if e["pathName"] == "pages/entry/entry")
    assert entry["query"].startswith("token=h5t1.")
    assert second["devtools_launch_query"] == entry["query"]


def test_local_status_does_not_replace_qa_status(golden_local):
    qa_status = {
        "status": "ready_to_scan",
        "case_id": "case_qa",
        "target": "qa",
        "token_masked": "qa…token",
    }
    qa_path = golden_local["art"] / "qa" / "launch_status.json"
    qa_path.parent.mkdir()
    qa_path.write_text(json.dumps(qa_status), encoding="utf-8")

    local = launch_golden_qa(target="local", prepare_preview=False)

    assert local["ok"] is True
    assert json.loads(qa_path.read_text(encoding="utf-8")) == qa_status
    local_status = read_launch_status("local")
    assert local_status["target"] == "local"
    assert local_status["case_id"] == local["case_id"]
