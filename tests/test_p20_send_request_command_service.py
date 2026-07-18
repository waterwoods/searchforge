"""P20 Capability 3A — SendRequest command service tests."""

from __future__ import annotations

import pytest

from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    ADMIN_LIFECYCLE_DRAFT,
    IntakeAggregate,
    RequestDraft,
)
from services.fiqa_api.inbox_triage.p20_customer_launch import (
    hash_launch_token,
    rebuild_customer_launch_from_material,
    validate_access_token,
)
from services.fiqa_api.inbox_triage.p20_send_request_command_service import (
    InMemorySendRequestStore,
    P20SendRequestCommandService,
    draft_items_to_slice1_items,
)
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    GROUP_STATUS_OPEN,
    ITEM_STATUS_ACTIVE,
    P20Slice1CommandService,
    InMemorySlice1Store,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM


def _case() -> dict:
    return {
        "case_id": "case_send_3a",
        "service_lane": SERVICE_LANE_CLAIM,
        "claim_phase": "broker_review",
        "updated_at": "2026-07-15T10:00:00Z",
        "client_id": "tenant_demo",
        "asserted_org_id": "office_demo",
    }


def _intake() -> IntakeAggregate:
    return IntakeAggregate(
        case_id="case_send_3a",
        admin_lifecycle=ADMIN_LIFECYCLE_DRAFT,
        aggregate_version=2,
        is_test=True,
        office_id="office_demo",
        tenant_id="tenant_demo",
        fact_records={},
        created_at="2026-07-15T09:00:00Z",
        updated_at="2026-07-15T09:30:00Z",
    )


def _draft(*, items: list[dict] | None = None) -> RequestDraft:
    default_items = [
        {
            "draft_item_id": "di_1",
            "field_key": "vin",
            "item_type": "vin",
            "label": "VIN",
            "instructions": "Please confirm the VIN",
            "required": True,
            "position": 1,
            "selected": True,
        }
    ]
    return RequestDraft(
        draft_id="draft_abc123",
        case_id="case_send_3a",
        draft_version=1,
        items=items if items is not None else default_items,
        content_hash="hash1",
        updated_by="office:demo",
        created_at="2026-07-15T09:30:00Z",
        updated_at="2026-07-15T09:30:00Z",
        status="draft",
    )


def _svc(**kwargs) -> tuple[P20SendRequestCommandService, InMemorySendRequestStore]:
    store = InMemorySendRequestStore(
        cases={"case_send_3a": _case()},
        intake_aggregates={"case_send_3a": _intake()},
        drafts={"case_send_3a": _draft(**kwargs) if "items" in kwargs else _draft()},
    )
    if "items" in kwargs:
        store.drafts["case_send_3a"] = _draft(items=kwargs["items"])
    return P20SendRequestCommandService(store), store


def _send(
    svc: P20SendRequestCommandService,
    *,
    command_id: str = "cmd_send_0001",
    idempotency_key: str = "idem_send_0001",
    expected: int = 2,
    draft_id: str = "draft_abc123",
) -> dict:
    return svc.send_request(
        case_id="case_send_3a",
        broker_id="office:demo",
        request_draft_id=draft_id,
        expected_case_version=expected,
        command_id=command_id,
        idempotency_key=idempotency_key,
        office_id="office_demo",
        tenant_id="tenant_demo",
    )


def test_draft_items_map_exact_order():
    items = draft_items_to_slice1_items(
        [
            {
                "item_type": "vin",
                "label": "VIN",
                "instructions": "a",
                "required": True,
                "position": 1,
            },
            {
                "item_type": "photo_evidence",
                "label": "Photos",
                "instructions": "b",
                "required": True,
                "position": 2,
            },
        ]
    )
    assert [i["item_type"] for i in items] == ["vin", "photo_evidence"]
    assert [i["position"] for i in items] == [1, 2]


def test_send_request_success_creates_group_access_and_projections():
    svc, store = _svc()
    result = _send(svc)
    assert result["outcome"] == "accepted"
    assert result["customer_access"]["access_ready"] is True
    assert result["customer_access"]["copy_link"]
    assert result["customer_access"]["qr_payload"] == result["customer_access"]["launch_url"]
    assert result["customer_access"]["simple_status"] == "Waiting for customer"
    assert result["slice1_projection"]["workflow_state"] == "broker_more_requested"
    assert result["slice1_projection"]["open_request"]["progress"]["total"] == 1
    assert result["customer_access"]["progress"]["total_count"] == 1
    assert result["customer_access"]["progress"]["satisfied_count"] == 0
    assert result["slice1_projection"]["customer_next_action"]["required_input"] == "vin"
    assert store.groups
    assert store.access_by_case["case_send_3a"].status == "ready"
    assert store.drafts["case_send_3a"].status == "sent"
    assert store.intake_aggregates["case_send_3a"].admin_lifecycle == "active"
    assert store.cases["case_send_3a"]["slice1_capability_version"] == 1
    # No raw token in outcome beyond launch URL (token is opaque in path).
    assert "token_hash" not in (result.get("customer_access") or {})


def test_ordered_item_mapping_from_multi_item_draft_accepts_mvp_sendable_pair():
    """VIN + insurance card are both MVP sendable — ordered group must accept."""
    svc, store = _svc(
        items=[
            {
                "draft_item_id": "di_1",
                "field_key": "vin",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "vin please",
                "required": True,
                "position": 1,
                "selected": True,
            },
            {
                "draft_item_id": "di_2",
                "field_key": "policy_or_insurance_card",
                "item_type": "policy_or_insurance_card",
                "label": "Insurance card",
                "instructions": "card please",
                "required": True,
                "position": 2,
                "selected": True,
            },
        ]
    )
    result = _send(svc)
    assert result["outcome"] == "accepted"
    assert result["slice1_projection"]["open_request"]["progress"]["total"] == 2
    assert store.groups
    assert store.access_by_case


def test_send_request_rejects_vehicle_information_only_draft():
    svc, store = _svc(
        items=[
            {
                "draft_item_id": "di_1",
                "field_key": "vehicle_information",
                "item_type": "free_text",
                "label": "Vehicle year / make / model",
                "instructions": "year make model",
                "required": True,
                "position": 1,
                "selected": True,
            }
        ]
    )
    result = _send(svc)
    assert result["outcome"] == "rejected"
    assert result["error_code"] == "unsupported_draft_item_type_for_send"
    assert store.groups == {}


def test_send_request_accepts_vin_only_draft():
    svc, _store = _svc(
        items=[
            {
                "draft_item_id": "di_1",
                "field_key": "vin",
                "item_type": "vin",
                "label": "VIN",
                "instructions": "vin please",
                "required": True,
                "position": 1,
                "selected": True,
            }
        ]
    )
    result = _send(svc)
    assert result["outcome"] == "accepted"


def test_duplicate_command_replay_same_access():
    svc, store = _svc()
    first = _send(svc)
    second = _send(svc)
    assert second["outcome"] == "replayed"
    assert second["customer_access"]["launch_url"] == first["customer_access"]["launch_url"]
    assert len(store.groups) == 1
    assert len(store.access_by_case) == 1
    assert len(store.slice1_events["case_send_3a"]) == 1


def test_duplicate_button_new_ids_rejected_when_open_exists():
    svc, _store = _svc()
    first = _send(svc)
    assert first["outcome"] == "accepted"
    next_version = int(first["aggregate_version"])
    second = _send(
        svc,
        command_id="cmd_send_0002",
        idempotency_key="idem_send_0002",
        expected=next_version,
    )
    assert second["outcome"] == "rejected"
    assert second["error_code"] == "open_request_exists"


def test_stale_version_conflict_returns_projection():
    svc, _store = _svc()
    result = _send(svc, expected=1)
    assert result["outcome"] == "conflict"
    assert result["error_code"] == "version_conflict"
    assert result["broker_projection"]["aggregate_version"] == 2


def test_empty_draft_rejection():
    svc, store = _svc()
    store.drafts["case_send_3a"] = _draft(items=[])
    result = _send(svc)
    assert result["outcome"] == "rejected"
    assert result["error_code"] == "request_draft_empty"


def test_missing_draft_rejection():
    svc, store = _svc()
    del store.drafts["case_send_3a"]
    result = _send(svc)
    assert result["outcome"] == "rejected"
    assert result["error_code"] == "request_draft_empty"


def test_active_request_rejection():
    from services.fiqa_api.inbox_triage.p20_slice1_command_service import Slice1Group

    svc, store = _svc()
    store.groups["req_open"] = Slice1Group(
        request_id="req_open",
        case_id="case_send_3a",
        status=GROUP_STATUS_OPEN,
        reason="existing",
        created_by="office:demo",
        created_at="2026-07-15T09:00:00Z",
        updated_at="2026-07-15T09:00:00Z",
    )
    result = _send(svc)
    assert result["outcome"] == "rejected"
    assert result["error_code"] == "open_request_exists"


def test_transaction_rollback_on_write_failure():
    svc, store = _svc()
    store.fail_next_write = True
    with pytest.raises(RuntimeError, match="forced_write_failure"):
        _send(svc)
    assert store.groups == {}
    assert store.access_by_case == {}
    assert store.intake_aggregates["case_send_3a"].admin_lifecycle == ADMIN_LIFECYCLE_DRAFT


def test_no_access_without_request_and_no_request_without_access():
    svc, store = _svc()
    result = _send(svc)
    assert result["outcome"] == "accepted"
    assert len(store.groups) == 1
    assert len(store.access_by_case) == 1
    access = store.access_by_case["case_send_3a"]
    group = next(iter(store.groups.values()))
    assert access.request_group_id == group.request_id


def test_refresh_rebuilds_same_launch_url():
    svc, store = _svc()
    first = _send(svc)
    access = store.access_by_case["case_send_3a"]
    rebuilt = rebuild_customer_launch_from_material(
        case_id="case_send_3a",
        token_nonce=access.token_nonce,
        token_iat=access.token_iat,
        token_exp=access.token_exp,
    )
    assert rebuilt.launch_url == first["customer_access"]["launch_url"]
    card = svc.fetch_customer_access_card("case_send_3a")
    assert card is not None
    assert card["launch_url"] == first["customer_access"]["launch_url"]


def test_invalid_and_expired_access():
    svc, store = _svc()
    result = _send(svc)
    access = store.access_by_case["case_send_3a"]
    token = result["customer_access"]["launch_url"].rsplit("/", 1)[-1]
    assert validate_access_token(
        presented_token=token,
        expected_hash=access.token_hash,
        token_exp=access.token_exp,
    ) is None
    assert validate_access_token(
        presented_token="h5t1.invalid.tokenvalue00000000000000",
        expected_hash=access.token_hash,
        token_exp=access.token_exp,
    ) == "access_invalid"
    assert validate_access_token(
        presented_token=token,
        expected_hash=access.token_hash,
        token_exp=access.token_exp,
        now=float(access.token_exp + 10),
    ) == "access_expired"
    assert hash_launch_token(token) == access.token_hash


def test_slice1_customer_flow_still_works_after_send():
    """SendRequest must leave a Slice 1-compatible open request for customer submit."""
    send_svc, send_store = _svc()
    sent = _send(send_svc)
    assert sent["outcome"] == "accepted"
    # Mirror into Slice 1 in-memory service for customer submit regression.
    slice_store = InMemorySlice1Store({"case_send_3a": dict(send_store.cases["case_send_3a"])})
    slice_store.aggregates = dict(send_store.slice1_aggregates)
    slice_store.groups = dict(send_store.groups)
    slice_store.items = dict(send_store.items)
    slice_store.events = dict(send_store.slice1_events)
    slice_svc = P20Slice1CommandService(slice_store)
    active_id = sent["slice1_projection"]["customer_next_action"]["request_item_id"]
    submit = slice_svc.submit_request_item(
        case_id="case_send_3a",
        customer_id="h5:demo",
        active_request_item_id=active_id,
        command_id="cmd_submit_vin",
        idempotency_key="idem_submit_vin",
        expected_case_version=sent["slice1_projection"]["aggregate_version"],
        fact={"field": "vin", "value": "1HGCM82633A004352"},
    )
    assert submit["outcome"] == "accepted"
    assert submit["broker_projection"]["workflow_state"] == "broker_review_ready"
    assert (
        submit["broker_projection"]["open_request"]["items"][0]["customer_response"][
            "submitted_value"
        ]
        == "1HGCM82633A004352"
    )

    # Access card readback after customer submit must surface Ready for Review + progress 1/1.
    send_store.slice1_aggregates = dict(slice_store.aggregates)
    send_store.groups = dict(slice_store.groups)
    send_store.items = dict(slice_store.items)
    send_store.slice1_events = dict(slice_store.events)
    card = send_svc.fetch_customer_access_card("case_send_3a")
    assert card is not None
    assert card["simple_status"] == "Ready for Review"
    assert card["progress"]["satisfied_count"] == 1
    assert card["progress"]["total_count"] == 1
