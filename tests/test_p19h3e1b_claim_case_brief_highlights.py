"""P19H-3e-1b — Claim Case Brief highlights[] (deterministic, no LLM)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import save_case
from services.fiqa_api.inbox_triage.claim_workbench_display import (
    brief_highlights_are_broker_safe,
    build_claim_case_brief,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    SERVICE_LANE_CLAIM,
)

_FORBIDDEN_HIGHLIGHT_PHRASES = (
    "对方全责",
    "一定会赔",
    "已报案",
    "保险公司已收到",
    "coverage approved",
)


@pytest.fixture(autouse=True)
def _json_store(monkeypatch):
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


def _claim_stub(**known_facts: str) -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Claim guided workflow",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "collected_fields": list(known_facts.keys()),
        "still_needed_fields": [],
        "known_facts": dict(known_facts),
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        "guided_workflow_state": "collecting_text",
    }


def test_brief_has_highlights_array():
    saved = save_case(
        "[客户] claim",
        _claim_stub(accident_datetime="今天上午10点", injury_status="no"),
        service_lane=SERVICE_LANE_CLAIM,
    )
    brief = build_claim_case_brief(saved)
    assert "highlights" in brief
    assert isinstance(brief["highlights"], list)


def test_highlights_max_length_five():
    saved = save_case(
        "[客户] claim",
        _claim_stub(),
        service_lane=SERVICE_LANE_CLAIM,
    )
    brief = build_claim_case_brief(saved)
    assert len(brief["highlights"]) <= 5


def test_photo_count_generates_received_highlight():
    saved = save_case(
        "[客户] claim",
        _claim_stub(injury_status="no"),
        service_lane=SERVICE_LANE_CLAIM,
    )
    saved["case_attachments"] = [
        {
            "attachment_id": "a1",
            "mime_type": "image/jpeg",
            "source": "wecom",
            "received_at": "2026-07-09T10:00:00Z",
        }
    ]
    brief = build_claim_case_brief(saved)
    labels = [h["label"] for h in brief["highlights"]]
    assert any("已收到 1 张照片" in label for label in labels)
    photo_hl = next(h for h in brief["highlights"] if h.get("kind") == "evidence")
    assert photo_hl["level"] == "received"


def test_missing_injury_generates_missing_highlight():
    saved = save_case(
        "[客户] claim",
        _claim_stub(
            accident_datetime="今天上午10点",
            accident_location="Costco",
            accident_description="追尾",
        ),
        service_lane=SERVICE_LANE_CLAIM,
    )
    brief = build_claim_case_brief(saved)
    injury_hl = [h for h in brief["highlights"] if h.get("kind") == "injury"]
    assert injury_hl
    assert injury_hl[0]["level"] == "missing"
    assert "还缺受伤情况确认" in injury_hl[0]["label"]


def test_no_injury_generates_confirmed_highlight():
    saved = save_case(
        "[客户] claim",
        _claim_stub(
            accident_datetime="今天上午10点",
            accident_location="Costco",
            accident_description="追尾",
            injury_status="no",
        ),
        service_lane=SERVICE_LANE_CLAIM,
    )
    brief = build_claim_case_brief(saved)
    injury_hl = [h for h in brief["highlights"] if h.get("kind") == "injury"]
    assert injury_hl
    assert injury_hl[0]["level"] == "important"
    assert "没有受伤" in injury_hl[0]["label"]


def test_injury_yes_generates_important_highlight():
    saved = save_case(
        "[客户] claim",
        _claim_stub(
            accident_datetime="今天上午10点",
            accident_location="Costco",
            accident_description="追尾",
            injury_status="yes",
        ),
        service_lane=SERVICE_LANE_CLAIM,
    )
    brief = build_claim_case_brief(saved)
    injury_hl = [h for h in brief["highlights"] if h.get("kind") == "injury"]
    assert injury_hl
    assert injury_hl[0]["level"] == "important"
    assert "陈总需优先人工确认" in injury_hl[0]["label"]


def test_highlights_no_forbidden_decision_words():
    cases = [
        save_case(
            "[客户] claim",
            _claim_stub(
                accident_datetime="今天上午10点",
                accident_location="Costco",
                accident_description="追尾",
                injury_status="yes",
            ),
            service_lane=SERVICE_LANE_CLAIM,
        ),
        save_case("[客户] claim", _claim_stub(), service_lane=SERVICE_LANE_CLAIM),
    ]
    for case in cases:
        brief = build_claim_case_brief(case)
        assert brief_highlights_are_broker_safe(brief["highlights"])
        combined = " ".join(h["label"] for h in brief["highlights"])
        for phrase in _FORBIDDEN_HIGHLIGHT_PHRASES:
            assert phrase not in combined
