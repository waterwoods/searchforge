"""P1 Request More audit — Active Case attach, mapping, completion, closed reject.

Simulates No-QR reopen semantics via the same case_id / Slice1 group (resume path).
"""

from __future__ import annotations

from services.fiqa_api.inbox_triage.case_close import ERROR_CASE_CLOSED_READ_ONLY
from services.fiqa_api.inbox_triage.constitution_projection import (
    TASK_ID_INSURANCE,
    TASK_ID_PHOTOS,
    ConstitutionInputs,
    build_constitution_customer_projection,
)
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    GROUP_STATUS_COMPLETED,
    GROUP_STATUS_OPEN,
    ITEM_STATUS_ACTIVE,
    ITEM_STATUS_QUEUED,
    ITEM_STATUS_SATISFIED,
    InMemorySlice1Store,
    P20Slice1CommandService,
    STATE_BROKER_MORE_REQUESTED,
    STATE_BROKER_REVIEW_READY,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

CASE_A = "case_active_a"


def _case(**extra) -> dict:
    row = {
        "case_id": CASE_A,
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "updated_at": "2026-07-22T18:00:00Z",
        "slice1_capability_version": 1,
        "entry_channel": "mini_program",
        "created_by_actor": "customer",
        "identity_binding_state": "linked",
        "person_link_source": "wechat",
        "person_link_key": "plk_active_a",
        "known_facts": {"accident_description": "倒车碰撞"},
    }
    row.update(extra)
    return row


def _svc(case: dict | None = None) -> tuple[P20Slice1CommandService, InMemorySlice1Store]:
    store = InMemorySlice1Store({CASE_A: case or _case()})
    return P20Slice1CommandService(store), store


def _item(
    *,
    item_id: str,
    label: str,
    item_type: str,
    position: int,
) -> dict:
    return {
        "request_item_id": item_id,
        "item_type": item_type,
        "label": label,
        "instructions": f"请补充{label}",
        "required": True,
        "position": position,
    }


def test_request_attaches_to_existing_active_case_no_duplicate_case():
    svc, store = _svc()
    before_ids = set(store.cases.keys())
    result = svc.accept_request_more(
        case_id=CASE_A,
        broker_id="office:audit",
        command_id="cmd-audit-attach",
        idempotency_key="idem-audit-attach",
        expected_case_version=0,
        requested_items=[
            _item(
                item_id="item_insurance",
                label="保险卡",
                item_type="policy_or_insurance_card",
                position=1,
            )
        ],
        reason="Need insurance card",
        request_id="req_audit_1",
    )
    assert result["outcome"] == "accepted"
    assert set(store.cases.keys()) == before_ids == {CASE_A}
    assert store.groups["req_audit_1"].case_id == CASE_A
    assert store.aggregates[CASE_A].workflow_state == STATE_BROKER_MORE_REQUESTED
    assert store.aggregates[CASE_A].active_request_id == "req_audit_1"


def test_requested_item_mapping_exact_no_vin_fallback():
    svc, store = _svc()
    created = svc.accept_request_more(
        case_id=CASE_A,
        broker_id="office:audit",
        command_id="cmd-audit-map",
        idempotency_key="idem-audit-map",
        expected_case_version=0,
        requested_items=[
            _item(
                item_id="item_insurance",
                label="保险卡",
                item_type="policy_or_insurance_card",
                position=1,
            ),
            _item(
                item_id="item_photos",
                label="事故照片",
                item_type="photo_evidence",
                position=2,
            ),
        ],
        reason="Two items",
        request_id="req_audit_map",
    )
    assert created["outcome"] == "accepted"
    projection = created["customer_projection"]
    assert projection["customer_next_action"]["title"] == "保险卡"
    assert projection["customer_next_action"]["required_input"] == "policy_or_insurance_card"
    labels = [i.label for i in sorted(store.items.values(), key=lambda x: x.position)]
    assert labels == ["保险卡", "事故照片"]

    case = dict(store.cases[CASE_A])
    case["p20_slice1_projection"] = projection
    customer_proj = build_constitution_customer_projection(ConstitutionInputs(case=case))
    customer = customer_proj["customer"]
    assert customer["today"] == "保险卡"
    task_ids = {t["task_id"] for t in customer["tasks"]}
    assert TASK_ID_INSURANCE in task_ids
    assert TASK_ID_PHOTOS in task_ids
    assert "vehicle_vin" not in task_ids
    assert customer["today"] != "Vehicle VIN"


def test_duplicate_send_rejected_idempotent_replay_safe():
    svc, store = _svc()
    first = svc.accept_request_more(
        case_id=CASE_A,
        broker_id="office:audit",
        command_id="cmd-audit-dup",
        idempotency_key="idem-audit-dup",
        expected_case_version=0,
        requested_items=[
            _item(
                item_id="item_insurance",
                label="保险卡",
                item_type="policy_or_insurance_card",
                position=1,
            )
        ],
        request_id="req_audit_dup",
    )
    assert first["outcome"] == "accepted"

    # Same command identity → replay, no second group.
    replay = svc.accept_request_more(
        case_id=CASE_A,
        broker_id="office:audit",
        command_id="cmd-audit-dup",
        idempotency_key="idem-audit-dup",
        expected_case_version=0,
        requested_items=[
            _item(
                item_id="item_insurance",
                label="保险卡",
                item_type="policy_or_insurance_card",
                position=1,
            )
        ],
        request_id="req_audit_dup",
    )
    assert replay["outcome"] == "replayed"

    # Different command while Waiting Customer → rejected; no duplicate group.
    second = svc.accept_request_more(
        case_id=CASE_A,
        broker_id="office:audit",
        command_id="cmd-audit-dup-2",
        idempotency_key="idem-audit-dup-2",
        expected_case_version=first["aggregate_version"],
        requested_items=[
            _item(
                item_id="item_insurance_2",
                label="保险卡",
                item_type="policy_or_insurance_card",
                position=1,
            )
        ],
        request_id="req_audit_dup_2",
    )
    assert second["outcome"] == "rejected"
    assert second["error_code"] in {"illegal_state", "open_request_exists"}
    assert list(store.groups.keys()) == ["req_audit_dup"]
    assert "item_insurance_2" not in store.items


def test_partial_then_all_complete_clears_waiting_customer():
    svc, store = _svc()
    created = svc.accept_request_more(
        case_id=CASE_A,
        broker_id="office:audit",
        command_id="cmd-audit-complete",
        idempotency_key="idem-audit-complete",
        expected_case_version=0,
        requested_items=[
            _item(
                item_id="item_insurance",
                label="保险卡",
                item_type="policy_or_insurance_card",
                position=1,
            ),
            _item(
                item_id="item_vin",
                label="车辆 VIN",
                item_type="vin",
                position=2,
            ),
        ],
        request_id="req_audit_complete",
    )
    assert created["outcome"] == "accepted"
    assert store.items["item_insurance"].status == ITEM_STATUS_ACTIVE
    assert store.items["item_vin"].status == ITEM_STATUS_QUEUED

    partial = svc.submit_request_item(
        case_id=CASE_A,
        customer_id="h5:bound",
        active_request_item_id="item_insurance",
        command_id="cmd-audit-submit-card",
        idempotency_key="idem-audit-submit-card",
        expected_case_version=created["aggregate_version"],
        evidence={"attachment_id": "att_card_1"},
    )
    assert partial["outcome"] == "accepted"
    assert store.items["item_insurance"].status == ITEM_STATUS_SATISFIED
    assert store.items["item_vin"].status == ITEM_STATUS_ACTIVE
    assert store.groups["req_audit_complete"].status == GROUP_STATUS_OPEN
    assert store.aggregates[CASE_A].workflow_state == "customer_continuing"
    broker = partial["broker_projection"]["broker_next_action"]
    assert broker["status"] == "waiting_for_customer"

    done = svc.submit_request_item(
        case_id=CASE_A,
        customer_id="h5:bound",
        active_request_item_id="item_vin",
        command_id="cmd-audit-submit-vin",
        idempotency_key="idem-audit-submit-vin",
        expected_case_version=partial["aggregate_version"],
        fact={"field": "vin", "value": "1HGCM82633A004352"},
    )
    assert done["outcome"] == "accepted"
    assert store.groups["req_audit_complete"].status == GROUP_STATUS_COMPLETED
    assert store.aggregates[CASE_A].workflow_state == STATE_BROKER_REVIEW_READY
    assert done["broker_projection"]["broker_next_action"]["status"] == "review_ready"
    assert done["customer_projection"]["customer_next_action"]["action_type"] == "wait_for_broker_review"


def test_closed_case_rejects_request_more():
    svc, _store = _svc(
        _case(
            case_history_state="history",
            closed_at="2026-07-22T12:00:00Z",
            case_status="closed",
        )
    )
    result = svc.accept_request_more(
        case_id=CASE_A,
        broker_id="office:audit",
        command_id="cmd-audit-closed",
        idempotency_key="idem-audit-closed",
        expected_case_version=0,
        requested_items=[
            _item(
                item_id="item_insurance",
                label="保险卡",
                item_type="policy_or_insurance_card",
                position=1,
            )
        ],
        request_id="req_audit_closed",
    )
    assert result["outcome"] == "rejected"
    assert result["error_code"] == ERROR_CASE_CLOSED_READ_ONLY


def test_no_qr_reopen_same_active_case_projection():
    """Customer ignores QR and reopens via same Active Case — same request object."""
    svc, store = _svc()
    created = svc.accept_request_more(
        case_id=CASE_A,
        broker_id="office:audit",
        command_id="cmd-audit-noqr",
        idempotency_key="idem-audit-noqr",
        expected_case_version=0,
        requested_items=[
            _item(
                item_id="item_insurance",
                label="保险卡",
                item_type="policy_or_insurance_card",
                position=1,
            )
        ],
        request_id="req_audit_noqr",
    )
    assert created["outcome"] == "accepted"
    # Reopen = read projection for same case (session resume issues a token for CASE_A).
    again = svc.fetch_projection(CASE_A)
    assert again is not None
    assert again["case_id"] == CASE_A
    assert again["open_request"]["request_id"] == "req_audit_noqr"
    assert again["customer_next_action"]["title"] == "保险卡"
    assert len(again["open_request"]["items"]) == 1
    assert store.groups["req_audit_noqr"].status == GROUP_STATUS_OPEN
