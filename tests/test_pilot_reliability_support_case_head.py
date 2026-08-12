"""Pilot Reliability Fix 3 — stuck-case support head.

One read-only support call must answer: where is this case stuck, what was the
last success, and what should support do next. No LLM, no mutation, no secrets.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from services.fiqa_api.app_main import app
from services.fiqa_api.inbox_triage import case_store as cs
from services.fiqa_api.inbox_triage.case_store import get_case_by_id, save_case
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    SERVICE_LANE_CLAIM,
)

SIDE_EFFECT_EVENT = "start_claim_side_effect_failed"
RAW_STORY = "昨天下午3点在 San Jose 停车场被追尾，没有受伤。"


@pytest.fixture(autouse=True)
def _json_store(monkeypatch):
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(path))
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "1")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP", raising=False)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    yield


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _claim_case(*, asserted_org_id: str | None = None, **patch: Any) -> str:
    stub = {
        "issue_category": "claim_intake",
        "urgency": "medium",
        "broker_next_step": "Claim guided workflow",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "manual_followup_needed": False,
        "collected_fields": [],
        "still_needed_fields": [],
        "known_facts": {},
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        "guided_workflow_state": "collecting_text",
        "entry_channel": "mini_program",
        "created_by_actor": "customer",
    }
    saved = save_case(
        "[客户] fix3 support head",
        stub,
        service_lane=SERVICE_LANE_CLAIM,
        asserted_org_id=asserted_org_id,
    )
    cid = saved["case_id"]
    if patch:
        case = cs._load_case_for_mutation(cid)
        assert case is not None
        case.update(patch)
        assert cs._persist_case_after_update(cid, case)
    return cid


def _confirmed_story(*, used_fallback: bool = False) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "authority": "customer_confirmed",
        "ai_involved": True,
        "proposal_id": "prop_fix3",
        "last_confirmed_command_id": "cmd-fix3-confirm",
        "used_fallback": used_fallback,
        "fallback_reason_category": "llm_unavailable" if used_fallback else "",
        "raw_story": RAW_STORY,
        "incident_summary": "被追尾",
    }


def _open_request_projection() -> dict[str, Any]:
    return {
        "workflow_state": "broker_more_requested",
        "open_request": {
            "request_id": "req_fix3_open",
            "status": "open",
            "progress": {"total": 2, "satisfied": 0},
            "active_item": {
                "request_item_id": "item_1",
                "status": "active",
                "label": "行驶证照片",
            },
            "items": [
                {"request_item_id": "item_1", "status": "active", "label": "行驶证照片"},
                {"request_item_id": "item_2", "status": "queued", "label": "维修估价单"},
            ],
        },
    }


def _reviewed_request_projection() -> dict[str, Any]:
    return {
        "workflow_state": "broker_review_ready",
        "open_request": {
            "request_id": "req_fix3_review",
            "status": "open",
            "progress": {"total": 1, "satisfied": 1},
            "items": [
                {"request_item_id": "item_1", "status": "satisfied", "label": "行驶证照片"}
            ],
        },
        "latest_events": [
            {
                "event_type": "customer_request_item_submitted",
                "command_id": "cmd-fix3-submit",
                "actor": "customer",
                "actor_identity": "customer:mp:anon",
                "created_at": "2026-08-11T10:00:00Z",
                "aggregate_version": 4,
                "state_before": "broker_more_requested",
                "state_after": "broker_review_ready",
                "evidence": {"note": RAW_STORY},
            }
        ],
    }


def _side_effect_event(warnings: list[str]) -> dict[str, Any]:
    return {
        "event_id": "evt_fix3_sig",
        "event_type": SIDE_EFFECT_EVENT,
        "source_channel": "mini_program",
        "created_at": "2026-08-11T09:00:00Z",
        "actor": "system",
        "message_id": "start_claim_side_effect:cmd-fix3",
        "text": "开案已成功保存，部分补充信息未写入，需人工检查",
        "metadata": {
            "source": "customer_start_claim",
            "command_id": "cmd-fix3",
            "warnings": warnings,
            "side_effects": {"policy_context": "failed"},
        },
    }


def _diagnosis(client: TestClient, case_id: str, **kwargs: Any) -> dict[str, Any]:
    r = client.get(f"/api/inbox/support/case-head/{case_id}", **kwargs)
    assert r.status_code == 200, r.text
    return r.json()["support_diagnosis"]


# --- 1. Healthy case ---------------------------------------------------------


def test_healthy_case_has_no_blocker(client: TestClient):
    cid = _claim_case(
        accident_story_assistant=_confirmed_story(),
        policy_context={"status": "confirmed", "customer_choice": "correct"},
    )

    diag = _diagnosis(client, cid)

    assert diag["blocker"] is None
    assert diag["status"] in {"waiting_office", "ready_for_office_accept"}
    assert diag["signals"]["open_request_more"] is False
    assert diag["signals"]["awaiting_supplement_review"] is False
    assert diag["signals"]["accident_story"]["customer_confirmed"] is True
    assert diag["signals"]["start_claim"]["degraded"] is False
    assert diag["next_support_action"]


# --- 2. Open Request More ----------------------------------------------------


def test_open_request_more_is_the_blocker(client: TestClient):
    cid = _claim_case(
        accident_story_assistant=_confirmed_story(),
        p20_slice1_projection=_open_request_projection(),
    )

    diag = _diagnosis(client, cid)

    assert diag["status"] == "blocked_by_open_request_more"
    assert diag["signals"]["open_request_more"] is True
    assert diag["blocker"]["reason"] == "unresolved_request_more"
    assert diag["blocker"]["open_request"]["request_id"] == "req_fix3_open"
    assert "行驶证照片" in diag["blocker"]["open_request"]["unresolved_labels"]


# --- 3. Awaiting supplement review -------------------------------------------


def test_awaiting_supplement_review_points_at_the_broker(client: TestClient):
    cid = _claim_case(
        accident_story_assistant=_confirmed_story(),
        p20_slice1_projection=_reviewed_request_projection(),
    )

    diag = _diagnosis(client, cid)

    assert diag["status"] == "waiting_office"
    assert diag["signals"]["awaiting_supplement_review"] is True
    assert diag["signals"]["open_request_more"] is False
    assert diag["blocker"]["reason"] == "awaiting_supplement_review"
    assert "已核对补充资料" in diag["next_support_action_zh"]


# --- 4. Office materials accepted --------------------------------------------


def test_office_materials_accepted_moves_case_to_office(client: TestClient):
    cid = _claim_case(
        accident_story_assistant=_confirmed_story(),
        office_materials_accepted_at="2026-08-11T11:00:00Z",
    )

    diag = _diagnosis(client, cid)

    assert diag["status"] == "waiting_office"
    assert diag["signals"]["office_materials_accepted_at"] == "2026-08-11T11:00:00Z"
    assert diag["blocker"] is None


# --- 5. Accident Story degraded / incomplete ---------------------------------


def test_accident_story_fallback_is_visible_without_raw_prose(client: TestClient):
    cid = _claim_case(accident_story_assistant=_confirmed_story(used_fallback=True))

    body = client.get(f"/api/inbox/support/case-head/{cid}").json()
    story = body["support_diagnosis"]["signals"]["accident_story"]

    assert story["used_fallback"] is True
    assert story["fallback_reason_category"] == "llm_unavailable"
    assert story["authority"] == "customer_confirmed"
    assert RAW_STORY not in json.dumps(body, ensure_ascii=False)


def test_unconfirmed_accident_story_is_the_blocker(client: TestClient):
    cid = _claim_case(
        accident_story_assistant={
            "authority": "ai_proposed",
            "used_fallback": True,
            "proposal_id": "prop_fix3",
        }
    )

    diag = _diagnosis(client, cid)

    assert diag["status"] == "story_confirmation_incomplete"
    assert diag["signals"]["accident_story"]["customer_confirmed"] is False


# --- 6. Start Claim side-effect degradation ----------------------------------


def test_unresolved_start_claim_side_effect_outranks_workflow_state(client: TestClient):
    cid = _claim_case(
        accident_story_assistant=_confirmed_story(),
        claim_timeline=[_side_effect_event(["policy_context_not_confirmed"])],
    )

    diag = _diagnosis(client, cid)

    assert diag["status"] == "start_claim_degraded"
    sc = diag["signals"]["start_claim"]
    assert sc["degraded"] is True
    assert sc["degraded_signal_seen"] is True
    assert sc["unresolved_warnings"] == ["policy_context_not_confirmed"]
    assert diag["blocker"]["code"] == SIDE_EFFECT_EVENT


def test_repaired_start_claim_side_effect_is_not_reported_as_stuck(client: TestClient):
    cid = _claim_case(
        accident_story_assistant=_confirmed_story(),
        policy_context={"status": "confirmed", "customer_choice": "correct"},
        claim_timeline=[_side_effect_event(["policy_context_not_confirmed"])],
    )

    diag = _diagnosis(client, cid)

    assert diag["status"] != "start_claim_degraded"
    sc = diag["signals"]["start_claim"]
    assert sc["degraded"] is False
    assert sc["degraded_signal_seen"] is True
    assert sc["advisory_warnings"] == ["policy_context_not_confirmed"]


# --- 7. Recent command outcomes + last success -------------------------------


def test_recent_command_outcomes_and_last_success_are_bounded_and_safe(client: TestClient):
    cid = _claim_case(
        accident_story_assistant=_confirmed_story(),
        p20_slice1_projection=_reviewed_request_projection(),
        claim_timeline=[
            {
                "event_id": "evt_a",
                "event_type": "claim_started",
                "created_at": "2026-08-11T08:00:00Z",
                "actor": "customer",
                "source_channel": "mini_program",
                "text": RAW_STORY,
            },
            {
                "event_id": "evt_b",
                "event_type": "customer_accident_story_confirmed",
                "created_at": "2026-08-11T08:30:00Z",
                "actor": "customer",
                "source_channel": "mini_program",
                "text": RAW_STORY,
            },
        ],
    )

    body = client.get(f"/api/inbox/support/case-head/{cid}").json()
    diag = body["support_diagnosis"]

    outcomes = diag["recent_command_outcomes"]
    assert len(outcomes) == 1
    assert outcomes[0]["command_id"] == "cmd-fix3-submit"
    assert outcomes[0]["state_after"] == "broker_review_ready"
    assert "evidence" not in outcomes[0]

    assert diag["last_success"]["event_type"] == "customer_accident_story_confirmed"
    assert len(diag["recent_timeline_events"]) == 2
    assert diag["recent_timeline_events"][0]["event_id"] == "evt_b"
    assert all("text" not in row for row in diag["recent_timeline_events"])
    assert RAW_STORY not in json.dumps(body, ensure_ascii=False)


# --- 8/9. Not found + office scoping -----------------------------------------


def test_missing_case_is_a_safe_not_found(client: TestClient):
    r = client.get("/api/inbox/support/case-head/case_does_not_exist")
    assert r.status_code == 404
    assert r.json()["detail"] == "case not found"


def test_wrong_office_is_blocked_when_enforcement_is_on(client: TestClient, monkeypatch):
    cid = _claim_case(asserted_org_id="office_alpha")
    monkeypatch.setenv("UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP", "1")

    assert (
        client.get(
            f"/api/inbox/support/case-head/{cid}",
            headers={"X-Org-Id": "office_beta"},
        ).status_code
        == 403
    )
    assert client.get(f"/api/inbox/support/case-head/{cid}").status_code == 403
    assert (
        client.get(
            f"/api/inbox/support/case-head/{cid}",
            headers={"X-Org-Id": "office_alpha"},
        ).status_code
        == 200
    )


def test_support_key_is_required_when_configured(client: TestClient, monkeypatch):
    cid = _claim_case()
    monkeypatch.setenv("UNIFIED_INTAKE_SUPPORT_API_KEY", "fix3-support-key-long-enough-v1")

    assert client.get(f"/api/inbox/support/case-head/{cid}").status_code == 401
    ok = client.get(
        f"/api/inbox/support/case-head/{cid}",
        headers={"X-Unified-Intake-Support-Key": "fix3-support-key-long-enough-v1"},
    )
    assert ok.status_code == 200


# --- 10. No secrets / tokens -------------------------------------------------


def test_response_carries_no_secrets_or_contact_pii(client: TestClient, monkeypatch):
    secret = "fix3-support-key-long-enough-v1"
    monkeypatch.setenv("UNIFIED_INTAKE_SUPPORT_API_KEY", secret)
    cid = _claim_case(
        accident_story_assistant=_confirmed_story(),
        customer_name="王小明",
        customer_phone="+16265551234",
        customer_email="wang@example.com",
        policy_context={"status": "confirmed", "customer_choice": "correct"},
    )

    raw = client.get(
        f"/api/inbox/support/case-head/{cid}",
        headers={"X-Unified-Intake-Support-Key": secret},
    ).text

    for leaked in (secret, "王小明", "+16265551234", "wang@example.com", RAW_STORY):
        assert leaked not in raw
    assert "resume_token" not in raw


# --- Read-only proof ---------------------------------------------------------


def test_support_head_is_read_only(client: TestClient):
    cid = _claim_case(
        accident_story_assistant=_confirmed_story(),
        p20_slice1_projection=_open_request_projection(),
        claim_timeline=[_side_effect_event(["policy_context_not_confirmed"])],
    )
    before = get_case_by_id(cid)

    first = client.get(f"/api/inbox/support/case-head/{cid}").json()
    second = client.get(f"/api/inbox/support/case-head/{cid}").json()
    after = get_case_by_id(cid)

    assert before == after
    assert first["support_diagnosis"] == second["support_diagnosis"]
    assert first["case"] == second["case"]
