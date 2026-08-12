"""Pilot Reliability Fix 3 completion — identifier → case lookup for the support head.

Support knows a phone, a CLM-#### reference, or a WeChat person link. One read-only
call must turn that into the case_id the stuck-case diagnosis already understands,
without guessing between customers and without leaking contact details.
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
from services.fiqa_api.inbox_triage.mp_customer_identity import (
    bind_active_case,
    reset_mp_active_case_index_for_tests,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    SERVICE_LANE_CLAIM,
)

LOOKUP_URL = "/api/inbox/support/case-lookup"
PHONE = "+1 (626) 555-1234"
PHONE_DIGITS = "6265551234"
OTHER_PHONE = "6265559999"
RAW_STORY = "昨天下午3点在 San Jose 停车场被追尾，没有受伤。"


@pytest.fixture(autouse=True)
def _json_store(monkeypatch):
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("UNIFIED_INTAKE_CASES_PATH", str(path))
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_CASE_WRITES", "1")
    # Phone lookup reads the JSON store through the shared fallback gate.
    monkeypatch.setenv("UNIFIED_INTAKE_JSON_READ_FALLBACK", "1")
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_WRITES", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_DB_PRIMARY_READS", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_SUPPORT_API_KEY", raising=False)
    monkeypatch.delenv("UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP", raising=False)
    monkeypatch.delenv("SERVICE_RECORD_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_mp_active_case_index_for_tests()
    yield
    reset_mp_active_case_index_for_tests()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _confirmed_story() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "authority": "customer_confirmed",
        "ai_involved": True,
        "proposal_id": "prop_lookup",
        "raw_story": RAW_STORY,
        "incident_summary": "被追尾",
    }


def _claim_case(*, asserted_org_id: str | None = None, **patch: Any) -> dict[str, Any]:
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
        "[客户] fix3 support lookup",
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
    stored = get_case_by_id(cid)
    assert stored is not None
    return stored


def _lookup(client: TestClient, **params: Any) -> dict[str, Any]:
    r = client.get(LOOKUP_URL, params=params)
    assert r.status_code == 200, r.text
    return r.json()


# --- 1. Phone → active case --------------------------------------------------


def test_phone_resolves_to_the_active_case(client: TestClient):
    case = _claim_case(customer_phone=PHONE_DIGITS, accident_story_assistant=_confirmed_story())

    body = _lookup(client, phone=PHONE)

    assert body["identifier_kind"] == "phone"
    assert body["found"] is True
    assert body["match_count"] == 1
    assert body["ambiguous"] is False
    assert body["resolved_case_id"] == case["case_id"]
    match = body["matches"][0]
    assert match["case_ref"] == case["case_ref"]
    assert match["active"] is True
    assert match["status"]
    assert match["next_support_action_zh"]
    assert body["next_call"] == f"GET /api/inbox/support/case-head/{case['case_id']}"


# --- 2. support_ref / case_ref → exact case ----------------------------------


def test_support_ref_resolves_exactly_one_case(client: TestClient):
    case = _claim_case(customer_phone=PHONE_DIGITS)
    _claim_case(customer_phone=OTHER_PHONE)
    ref = case["case_ref"]
    assert ref.startswith("CLM-")

    by_case_ref = _lookup(client, case_ref=ref)
    by_support_ref = _lookup(client, support_ref=ref.lower())

    assert by_case_ref["resolved_case_id"] == case["case_id"]
    assert by_case_ref["identifier_kind"] == "case_ref"
    assert by_support_ref["resolved_case_id"] == case["case_id"]
    assert by_support_ref["match_count"] == 1


# --- 3. WeChat person binding → active case ----------------------------------


def test_person_link_resolves_the_bound_active_case(client: TestClient):
    case = _claim_case(customer_phone=PHONE_DIGITS)
    person_link = "wx_" + "a1b2c3d4" * 5
    bind_active_case(person_link, case["case_id"])

    body = _lookup(client, person_link=person_link)

    assert body["identifier_kind"] == "person_link"
    assert body["resolved_case_id"] == case["case_id"]
    assert person_link not in json.dumps(body, ensure_ascii=False)


def test_raw_openid_is_rejected_rather_than_hashed(client: TestClient):
    r = client.get(LOOKUP_URL, params={"person_link": "oX7bC1234567890abcdefg"})

    assert r.status_code == 400
    assert r.json()["detail"] == "support_lookup_invalid_person_link"


# --- 4. Ordering across several cases for one customer -----------------------


def test_multiple_matches_rank_active_and_recent_first(client: TestClient):
    _claim_case(
        customer_phone=PHONE_DIGITS,
        case_status="closed",
        closed_at="2026-08-11T12:00:00Z",
        updated_at="2026-08-11T12:00:00Z",
    )
    stale_active = _claim_case(
        customer_phone=PHONE_DIGITS,
        updated_at="2026-08-09T09:00:00Z",
    )
    fresh_active = _claim_case(
        customer_phone=PHONE_DIGITS,
        updated_at="2026-08-11T09:00:00Z",
    )

    body = _lookup(client, phone=PHONE_DIGITS)

    assert body["match_count"] == 3
    order = [m["case_id"] for m in body["matches"]]
    assert order[0] == fresh_active["case_id"]
    assert order[1] == stale_active["case_id"]
    assert body["matches"][2]["active"] is False


# --- 5. No match -------------------------------------------------------------


def test_no_match_is_a_safe_empty_result(client: TestClient):
    _claim_case(customer_phone=OTHER_PHONE)

    body = _lookup(client, phone=PHONE)

    assert body["found"] is False
    assert body["match_count"] == 0
    assert body["matches"] == []
    assert body["resolved_case_id"] is None
    assert body["next_call"] is None


def test_unknown_case_ref_is_not_a_guess(client: TestClient):
    _claim_case(customer_phone=PHONE_DIGITS)

    body = _lookup(client, support_ref="CLM-9999")

    assert body["found"] is False
    assert body["resolved_case_id"] is None


# --- 6. Ambiguity — never silently choose ------------------------------------


def test_ambiguous_phone_returns_a_bounded_list_without_resolving(client: TestClient):
    for _ in range(7):
        _claim_case(customer_phone=PHONE_DIGITS)

    body = _lookup(client, phone=PHONE_DIGITS)

    assert body["ambiguous"] is True
    assert body["resolved_case_id"] is None
    assert body["next_call"] is None
    assert body["match_count"] == 7
    assert len(body["matches"]) == 5
    assert body["truncated"] is True


def test_two_identifiers_at_once_are_rejected(client: TestClient):
    case = _claim_case(customer_phone=PHONE_DIGITS)

    r = client.get(LOOKUP_URL, params={"phone": PHONE, "case_ref": case["case_ref"]})

    assert r.status_code == 400
    assert r.json()["detail"] == "support_lookup_one_identifier_at_a_time"


def test_missing_and_malformed_identifiers_are_rejected(client: TestClient):
    assert client.get(LOOKUP_URL).json()["detail"] == "support_lookup_identifier_required"
    assert client.get(LOOKUP_URL, params={"phone": "123"}).json()["detail"] == (
        "support_lookup_invalid_phone"
    )
    assert client.get(LOOKUP_URL, params={"case_ref": "not-a-ref"}).json()["detail"] == (
        "support_lookup_invalid_case_ref"
    )


def test_ambiguous_diagnosis_is_not_returned_for_the_wrong_customer(client: TestClient):
    _claim_case(customer_phone=PHONE_DIGITS)
    _claim_case(customer_phone=PHONE_DIGITS)

    body = _lookup(client, phone=PHONE_DIGITS, include_diagnosis=True)

    assert body["ambiguous"] is True
    assert "support_diagnosis" not in body


# --- 7. Office boundary ------------------------------------------------------


def test_other_office_cannot_find_a_case_by_phone(client: TestClient, monkeypatch):
    case = _claim_case(asserted_org_id="office_alpha", customer_phone=PHONE_DIGITS)
    monkeypatch.setenv("UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP", "1")

    beta = client.get(LOOKUP_URL, params={"phone": PHONE}, headers={"X-Org-Id": "office_beta"})
    alpha = client.get(LOOKUP_URL, params={"phone": PHONE}, headers={"X-Org-Id": "office_alpha"})

    assert beta.status_code == 200
    assert beta.json()["match_count"] == 0
    assert beta.json()["resolved_case_id"] is None
    assert alpha.json()["resolved_case_id"] == case["case_id"]


def test_office_assertion_is_required_when_enforcement_is_on(client: TestClient, monkeypatch):
    _claim_case(asserted_org_id="office_alpha", customer_phone=PHONE_DIGITS)
    monkeypatch.setenv("UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP", "1")

    r = client.get(LOOKUP_URL, params={"phone": PHONE})

    assert r.status_code == 403
    assert r.json()["detail"] == "case_office_assertion_required_v1"


def test_support_key_is_required_when_configured(client: TestClient, monkeypatch):
    _claim_case(customer_phone=PHONE_DIGITS)
    monkeypatch.setenv("UNIFIED_INTAKE_SUPPORT_API_KEY", "fix3-lookup-key-long-enough-v1")

    assert client.get(LOOKUP_URL, params={"phone": PHONE}).status_code == 401
    ok = client.get(
        LOOKUP_URL,
        params={"phone": PHONE},
        headers={"X-Unified-Intake-Support-Key": "fix3-lookup-key-long-enough-v1"},
    )
    assert ok.status_code == 200


# --- 8. Privacy --------------------------------------------------------------


def test_lookup_carries_no_contact_pii_secrets_or_story_text(client: TestClient, monkeypatch):
    secret = "fix3-lookup-key-long-enough-v1"
    monkeypatch.setenv("UNIFIED_INTAKE_SUPPORT_API_KEY", secret)
    person_link = "wx_" + "f00dcafe" * 5
    case = _claim_case(
        customer_phone=PHONE_DIGITS,
        customer_name="王小明",
        customer_email="wang@example.com",
        accident_story_assistant=_confirmed_story(),
    )
    bind_active_case(person_link, case["case_id"])

    raw = client.get(
        LOOKUP_URL,
        params={"phone": PHONE, "include_diagnosis": True},
        headers={"X-Unified-Intake-Support-Key": secret},
    ).text

    for leaked in (secret, "王小明", "wang@example.com", PHONE_DIGITS, RAW_STORY, person_link):
        assert leaked not in raw
    assert "resume_token" not in raw


# --- 9. Read-only ------------------------------------------------------------


def test_lookup_is_read_only(client: TestClient):
    case = _claim_case(customer_phone=PHONE_DIGITS, accident_story_assistant=_confirmed_story())
    before = get_case_by_id(case["case_id"])

    first = _lookup(client, phone=PHONE, include_diagnosis=True)
    second = _lookup(client, phone=PHONE, include_diagnosis=True)
    after = get_case_by_id(case["case_id"])

    assert before == after
    assert first["matches"] == second["matches"]
    assert first["support_diagnosis"] == second["support_diagnosis"]


# --- 10. Composition with the existing Fix 3 head ----------------------------


def test_resolved_case_id_feeds_the_existing_support_head(client: TestClient):
    case = _claim_case(customer_phone=PHONE_DIGITS, accident_story_assistant=_confirmed_story())

    body = _lookup(client, phone=PHONE, include_diagnosis=True)
    resolved = body["resolved_case_id"]
    head = client.get(f"/api/inbox/support/case-head/{resolved}")

    assert head.status_code == 200
    head_diagnosis = head.json()["support_diagnosis"]
    assert body["support_diagnosis"] == head_diagnosis
    assert body["matches"][0]["status"] == head_diagnosis["status"]
    assert head.json()["case"]["case_id"] == case["case_id"]
