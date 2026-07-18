"""P26G-Q1 — Task routing + fresh-claim state isolation permanent gates.

Route Gate: actionable tasks have a valid destination for task_source.
Zero-Broker Gate: system_default tasks need no Broker request rows.
Case Isolation Gate: completion requires current-case facts/evidence only.
New-vs-Resume Gate: Start New Claim creates a distinct case; resume binds token case.
"""

from __future__ import annotations

from services.fiqa_api.inbox_triage.constitution_projection import (
    TASK_ID_INSURANCE,
    TASK_ID_PHOTOS,
    TASK_ID_STORY,
    TASK_STATE_BLOCKED,
    TASK_STATE_COMPLETED,
    ConstitutionInputs,
    build_constitution_projection,
)
from services.fiqa_api.inbox_triage.default_intake_plan import (
    TASK_SOURCE_BROKER_REQUESTED,
    TASK_SOURCE_SYSTEM_DEFAULT,
)
from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    InMemoryIntakeStore,
    P20CaseIntakeCommandService,
)
from services.fiqa_api.inbox_triage.p20_customer_start_claim import start_customer_claim
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
    SERVICE_LANE_CLAIM,
)


def _by_id(tasks: list[dict]) -> dict[str, dict]:
    return {str(t["task_id"]): t for t in tasks}


def _fresh_case(case_id: str = "case-q1-fresh", **overrides) -> dict:
    case = {
        "case_id": case_id,
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": CLAIM_PHASE_ACCIDENT_BASICS_COMPLETE,
        "known_facts": {
            "accident_description": "倒车刮蹭",
            "accident_datetime": "2026-07-18 10:00",
            "accident_location": "停车场",
            "injury_status": "no",
        },
        "p20_slice1_projection": {
            "case_id": case_id,
            "workflow_state": "intake",
            "customer_next_action": None,
            "broker_next_action": {"action_type": "none", "status": "none"},
            "open_request": None,
        },
        "claim_evidence_summary": {"received_slots": [], "missing_required_slots": []},
        "case_attachments": [],
        "claim_attachment_slots": {},
        "timeline_events": [],
    }
    case.update(overrides)
    return case


# --- Route Gate ---


def test_route_gate_system_default_insurance_uses_insurance_route():
    projection = build_constitution_projection(ConstitutionInputs(case=_fresh_case()))
    insurance = _by_id(projection["customer"]["tasks"])[TASK_ID_INSURANCE]
    assert insurance["task_source"] == TASK_SOURCE_SYSTEM_DEFAULT
    assert insurance["route"] == "insurance"
    assert insurance["action"]["kind"] == "open_route"
    assert insurance["action"]["task_type"] == TASK_ID_INSURANCE
    assert insurance["action"]["task_source"] == TASK_SOURCE_SYSTEM_DEFAULT
    assert "request_item_id" not in insurance["action"]


def test_route_gate_broker_requested_insurance_uses_request_item():
    case = _fresh_case(
        p20_slice1_projection={
            "case_id": "case-q1-fresh",
            "workflow_state": "broker_more_requested",
            "customer_next_action": {
                "action_type": "provide_evidence",
                "title": "上传保险卡",
                "required_input": "policy_or_insurance_card",
                "status": "active",
                "request_item_id": "item_ins_followup",
                "instructions": "请补一张更清晰的保险卡",
            },
            "broker_next_action": {
                "action_type": "wait_for_customer_item",
                "status": "waiting_for_customer",
            },
            "open_request": {
                "status": "open",
                "active_item": {
                    "item_type": "policy_or_insurance_card",
                    "label": "上传保险卡",
                    "status": "active",
                    "request_item_id": "item_ins_followup",
                },
                "queued_items": [],
            },
        }
    )
    insurance = _by_id(
        build_constitution_projection(ConstitutionInputs(case=case))["customer"]["tasks"]
    )[TASK_ID_INSURANCE]
    assert insurance["task_source"] == TASK_SOURCE_BROKER_REQUESTED
    assert insurance["route"] == "request_item"
    assert insurance["reason"]
    assert insurance["action"]["request_item_id"] == "item_ins_followup"


def test_route_gate_photos_and_story_routes_when_actionable():
    # No insurance Today competition: omit insurance focus by completing insurance slot.
    case = _fresh_case(
        known_facts={},  # story pending
        claim_attachment_slots={
            "policy_or_insurance_card": {
                "status": "received",
                "attachment_ids": ["att_ins"],
            }
        },
        case_attachments=[
            {
                "attachment_id": "att_ins",
                "source": "h5_task",
                "msgtype": "image",
                "slot_assignment": "policy_or_insurance_card",
                "evidence_status": "confirmed",
            }
        ],
        claim_evidence_summary={
            "received_slots": ["policy_or_insurance_card"],
            "missing_required_slots": [],
        },
    )
    by_id = _by_id(
        build_constitution_projection(ConstitutionInputs(case=case))["customer"]["tasks"]
    )
    assert by_id[TASK_ID_PHOTOS]["actionable"] is True
    assert by_id[TASK_ID_PHOTOS]["route"] == "photos"
    assert by_id[TASK_ID_STORY]["actionable"] is True
    assert by_id[TASK_ID_STORY]["route"] == "story"


# --- Zero-Broker Gate ---


def test_zero_broker_gate_system_default_executable_without_slice1_rows():
    case = _fresh_case()
    assert case["p20_slice1_projection"]["open_request"] is None
    assert case["p20_slice1_projection"]["customer_next_action"] is None
    by_id = _by_id(
        build_constitution_projection(ConstitutionInputs(case=case))["customer"]["tasks"]
    )
    for task_id in (TASK_ID_INSURANCE, TASK_ID_PHOTOS, TASK_ID_STORY):
        card = by_id[task_id]
        assert card["task_source"] == TASK_SOURCE_SYSTEM_DEFAULT
    assert by_id[TASK_ID_INSURANCE]["actionable"] is True
    assert by_id[TASK_ID_INSURANCE]["route"] == "insurance"


# --- Case Isolation Gate ---


def test_case_isolation_gate_no_fake_photo_completion_without_evidence():
    by_id = _by_id(
        build_constitution_projection(ConstitutionInputs(case=_fresh_case()))["customer"]["tasks"]
    )
    photos = by_id[TASK_ID_PHOTOS]
    assert photos["state"] != TASK_STATE_COMPLETED
    assert photos["progress"]["completed"] == 0
    assert photos["state"] == TASK_STATE_BLOCKED


def test_case_isolation_gate_case_b_does_not_inherit_case_a_completion():
    # Case A: seeded photo summary (no live attachments) + story facts.
    case_a = _fresh_case(
        case_id="case-a",
        known_facts={"accident_description": "Case A story"},
        claim_evidence_summary={"received_slots": ["scene_photo"], "missing_required_slots": []},
        case_attachments=[],
        claim_attachment_slots={},
    )
    proj_a = build_constitution_projection(ConstitutionInputs(case=case_a))
    by_a = _by_id(proj_a["customer"]["tasks"])
    assert by_a[TASK_ID_STORY]["state"] == TASK_STATE_COMPLETED
    assert by_a[TASK_ID_PHOTOS]["state"] == TASK_STATE_COMPLETED

    # Case B: same shape, empty facts/evidence — must not inherit Case A completion.
    case_b = _fresh_case(
        case_id="case-b",
        known_facts={},
        claim_evidence_summary={"received_slots": [], "missing_required_slots": []},
        case_attachments=[],
        claim_attachment_slots={},
        timeline_events=[],
    )
    by_b = _by_id(
        build_constitution_projection(ConstitutionInputs(case=case_b))["customer"]["tasks"]
    )
    assert by_b[TASK_ID_STORY]["state"] != TASK_STATE_COMPLETED
    assert by_b[TASK_ID_STORY]["progress"]["completed"] == 0
    assert by_b[TASK_ID_PHOTOS]["state"] != TASK_STATE_COMPLETED
    assert by_b[TASK_ID_PHOTOS]["progress"]["completed"] == 0
    assert by_b[TASK_ID_INSURANCE]["state"] != TASK_STATE_COMPLETED


def test_case_isolation_gate_why_does_not_claim_photos_without_evidence():
    customer = build_constitution_projection(ConstitutionInputs(case=_fresh_case()))["customer"]
    why = str(customer.get("why") or "")
    assert "现场照片已经完成" not in why


# --- New-vs-Resume Gate ---


def test_new_vs_resume_gate_start_new_creates_distinct_cases(monkeypatch):
    store = InMemoryIntakeStore()
    svc = P20CaseIntakeCommandService(store)
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.default_case_intake_service",
        lambda: svc,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_server_client_id",
        lambda: "tenant_demo",
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_customer_start_claim_office_id",
        lambda: "office_demo",
    )

    first = start_customer_claim(
        command_id="cmd_q1_a",
        idempotency_key="idem_q1_a",
        session_id="sess_same",
        accident_description="Case A story only",
    )
    second = start_customer_claim(
        command_id="cmd_q1_b",
        idempotency_key="idem_q1_b",
        session_id="sess_same",
        accident_description="Case B story only",
    )
    assert first["outcome"] == "accepted"
    assert second["outcome"] == "accepted"
    assert first["case_id"] != second["case_id"]
    assert first.get("resume_token")
    assert second.get("resume_token")
    assert first["resume_token"] != second["resume_token"]

    case_a = store.cases[first["case_id"]]
    case_b = store.cases[second["case_id"]]
    facts_a = (case_a.get("known_facts") or {})
    facts_b = (case_b.get("known_facts") or {})
    assert "Case A" in str(facts_a.get("accident_description") or "")
    assert "Case B" in str(facts_b.get("accident_description") or "")
    assert not (case_b.get("case_attachments") or [])

    by_b = _by_id(
        build_constitution_projection(ConstitutionInputs(case=case_b))["customer"]["tasks"]
    )
    # Case B story completed from its own Start Claim facts only.
    assert by_b[TASK_ID_STORY]["state"] == TASK_STATE_COMPLETED
    assert by_b[TASK_ID_PHOTOS]["state"] != TASK_STATE_COMPLETED


def test_new_vs_resume_gate_idempotent_replay_returns_same_case(monkeypatch):
    store = InMemoryIntakeStore()
    svc = P20CaseIntakeCommandService(store)
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.default_case_intake_service",
        lambda: svc,
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_server_client_id",
        lambda: "tenant_demo",
    )
    monkeypatch.setattr(
        "services.fiqa_api.inbox_triage.p20_customer_start_claim.resolve_customer_start_claim_office_id",
        lambda: "office_demo",
    )
    first = start_customer_claim(
        command_id="cmd_q1_replay",
        idempotency_key="idem_q1_replay",
        session_id="sess_replay",
        accident_description="replay story",
    )
    replay = start_customer_claim(
        command_id="cmd_q1_replay",
        idempotency_key="idem_q1_replay",
        session_id="sess_replay",
        accident_description="replay story",
    )
    assert first["case_id"] == replay["case_id"]
    assert replay["outcome"] in ("accepted", "replayed")
