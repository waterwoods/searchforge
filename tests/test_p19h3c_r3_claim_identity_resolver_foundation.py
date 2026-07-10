"""P19H-3c-R3 — Claim identity resolver foundation tests."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.fiqa_api.inbox_triage.case_store import (
    bind_case_channel_identity,
    get_case_by_id,
    save_case,
)
from services.fiqa_api.wecom.claim_basics import ingest_claim_basics_message
from services.fiqa_api.wecom.claim_identity import (
    is_open_claim_candidate_for_basics,
    resolve_claim_identity,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_BROKER_DONE,
    SERVICE_LANE_CLAIM,
)
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.intent import classify_wecom_intent
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.routing_observability import (
    ROUTING_DECISION_EVENT,
    routing_decision_from_log_message,
)

_NOW = datetime(2026, 7, 9, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _json_store():
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)
    yield
    os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


def _claim_stub() -> dict:
    return {
        "issue_category": "claim_intake",
        "urgency": "high",
        "manual_followup_needed": True,
        "broker_next_step": "Claim guided workflow — collect accident basics.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "claim_phase": "claim_started",
    }


def _open_claim_case(
    *,
    case_id: str = "case_a",
    ext: str = "wm_identity",
    updated_at: str | None = None,
    broker_done: bool = False,
    closed: bool = False,
) -> dict:
    ts = updated_at or (_NOW - timedelta(hours=2)).isoformat()
    case = {
        "case_id": case_id,
        "wecom_external_userid": ext,
        "service_lane": SERVICE_LANE_CLAIM,
        "case_status": "closed" if closed else "open",
        "created_at": ts,
        "updated_at": ts,
        "known_facts": {},
        "collected_fields": [],
    }
    if broker_done:
        case["claim_phase"] = CLAIM_PHASE_BROKER_DONE
    return case


def _normalized(text: str, *, ext: str = "wm_identity", msg_id: str = "m1") -> dict:
    return normalize_text_message(
        {
            "msgid": msg_id,
            "open_kfid": "wktest001",
            "external_userid": ext,
            "origin": 3,
            "msgtype": "text",
            "text": {"content": text},
        }
    )


def _routing_logs(caplog) -> list[dict]:
    decisions: list[dict] = []
    for record in caplog.records:
        parsed = routing_decision_from_log_message(record.message)
        if parsed:
            decisions.append(parsed)
    return decisions


def test_01_no_open_claim_create_new():
    decision = resolve_claim_identity(
        external_userid="wm_identity",
        incoming_text="我要理赔",
        open_claims=[],
        now=_NOW,
    )
    assert decision.tier == "C"
    assert decision.action == "create_new"
    assert decision.case_id is None
    assert "no_open_claim" in decision.reasons


def test_02_one_recent_open_claim_append():
    case = _open_claim_case(updated_at=(_NOW - timedelta(hours=2)).isoformat())
    decision = resolve_claim_identity(
        external_userid="wm_identity",
        incoming_text="今天上午10点，在 Irvine Blvd 附近",
        open_claims=[case],
        now=_NOW,
    )
    assert decision.tier == "A"
    assert decision.action == "append_existing"
    assert decision.case_id == "case_a"
    assert decision.score >= 90
    assert decision.reasons[0] in (
        "single_recent_open_claim",
        "active_basics_collection_append",
    )


def test_03_explicit_new_accident_with_open_claim_triggers_resolver():
    case = _open_claim_case(updated_at=(_NOW - timedelta(hours=2)).isoformat())
    decision = resolve_claim_identity(
        external_userid="wm_identity",
        incoming_text="这是新的事故，我要理赔",
        open_claims=[case],
        now=_NOW,
    )
    assert decision.tier == "B"
    assert decision.action == "broker_confirm"
    assert decision.case_id == "case_a"
    assert "customer_said_new_accident" in decision.reasons


def test_04_multiple_open_claims_append_newest():
    case_a = _open_claim_case(case_id="case_a", updated_at=(_NOW - timedelta(hours=1)).isoformat())
    case_b = _open_claim_case(case_id="case_b", updated_at=(_NOW - timedelta(hours=3)).isoformat())
    decision = resolve_claim_identity(
        external_userid="wm_identity",
        incoming_text="对方保险是 AAA",
        open_claims=[case_a, case_b],
        now=_NOW,
    )
    assert decision.tier == "A"
    assert decision.action == "append_existing"
    assert decision.case_id == "case_a"
    assert "active_append_newest" in decision.reasons
    assert set(decision.candidate_case_ids) == {"case_a", "case_b"}


def test_05_old_open_claim_append_first():
    """Append-first: stale open Claim still appends; old policy was broker_confirm."""
    case = _open_claim_case(updated_at=(_NOW - timedelta(hours=100)).isoformat())
    decision = resolve_claim_identity(
        external_userid="wm_identity",
        incoming_text="我要理赔",
        open_claims=[case],
        now=_NOW,
    )
    assert decision.tier == "A"
    assert decision.action == "append_existing"
    assert decision.case_id == "case_a"
    assert decision.reasons[0] == "old_open_claim_append_first"


def test_06_closed_or_broker_done_excluded():
    closed = _open_claim_case(closed=True)
    done = _open_claim_case(case_id="case_done", broker_done=True)
    assert is_open_claim_candidate_for_basics(closed, "wm_identity") is False
    assert is_open_claim_candidate_for_basics(done, "wm_identity") is False
    decision = resolve_claim_identity(
        external_userid="wm_identity",
        incoming_text="我要理赔",
        open_claims=[closed, done],
        now=_NOW,
    )
    assert decision.action == "create_new"
    assert "no_open_claim" in decision.reasons


def test_07_claim_basics_path_multi_open_woyao_claim_appends_newest():
    """Append-first: multi-open 我要理赔 appends to newest; old policy was collision resolver."""
    ext = "wm_multi_claim"
    first = save_case("claim one", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    second = save_case("claim two", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    bind_case_channel_identity(first["case_id"], wecom_external_userid=ext)
    bind_case_channel_identity(second["case_id"], wecom_external_userid=ext)

    result = ingest_claim_basics_message(
        _normalized("我要理赔", ext=ext, msg_id="m_multi"),
        classify_wecom_intent("我要理赔"),
    )
    assert result["active_case_outcome"] != "claim_collision_resolver"
    assert result["case_created"] is False
    assert result["case_id"] == second["case_id"]


def test_08_routing_log_includes_identity_fields(caplog):
    caplog.set_level(logging.INFO)
    ext = "wm_route_identity"
    first = save_case("claim one", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    second = save_case("claim two", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    bind_case_channel_identity(first["case_id"], wecom_external_userid=ext)
    bind_case_channel_identity(second["case_id"], wecom_external_userid=ext)

    ingest_claim_basics_message(
        _normalized("新的事故", ext=ext, msg_id="m_route"),
        classify_wecom_intent("新的事故"),
    )

    identity_logs = [
        log
        for log in _routing_logs(caplog)
        if log.get("event") == ROUTING_DECISION_EVENT and log.get("identity_action")
    ]
    assert identity_logs, "expected routing log with identity fields"
    payload = identity_logs[-1]
    assert payload["identity_tier"] == "B"
    assert payload["identity_action"] == "broker_confirm"
    assert "customer_said_new_accident" in payload.get("identity_reasons", [])


def test_09_append_recent_single_open_claim_integration():
    ext = "wm_single_recent"
    saved = save_case("claim one", _claim_stub(), service_lane=SERVICE_LANE_CLAIM)
    bind_case_channel_identity(saved["case_id"], wecom_external_userid=ext)

    result = ingest_claim_basics_message(
        _normalized("今天上午10点", ext=ext, msg_id="m_append"),
        classify_wecom_intent("今天上午10点"),
    )
    assert result["case_created"] is False
    assert result["case_id"] == saved["case_id"]
    stored = get_case_by_id(saved["case_id"])
    assert stored is not None
    assert stored.get("known_facts", {}).get("accident_datetime")
