"""P20 Capability 3A — SendRequest (draft → Slice 1 Request More + customer access).

Atomic broker command. Reuses Slice 1 request group / items / events and the
existing H5 intake-form task token for customer launch. Does not implement
customer submission (Capability 3B).
"""

from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol
from uuid import uuid4

from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
    ADMIN_LIFECYCLE_ACTIVE,
    ADMIN_LIFECYCLE_DRAFT,
    IntakeAggregate,
    RequestDraft,
    build_broker_projection,
    case_intake_feature_enabled,
)
from services.fiqa_api.inbox_triage.p20_missing_information import list_unsupported_send_item_labels
from services.fiqa_api.inbox_triage.p20_customer_launch import (
    DEFAULT_ACCESS_TTL_SECONDS,
    CustomerLaunchTarget,
    issue_customer_launch_token,
    rebuild_customer_launch_from_material,
    validate_access_token,
)
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    ALLOWED_ITEM_TYPES,
    GROUP_STATUS_OPEN,
    ITEM_STATUS_ACTIVE,
    ITEM_STATUS_QUEUED,
    SLICE1_CAPABILITY_VERSION,
    STATE_BROKER_MORE_REQUESTED,
    Slice1Aggregate,
    Slice1Group,
    Slice1Item,
    _event,
    _is_terminal_state,
    _legacy_claim_state,
    _legacy_projection_patch,
    _projection,
    _validate_items,
    broker_may_create_request_more,
)
from services.fiqa_api.wecom.claim_state import SERVICE_LANE_CLAIM

logger = logging.getLogger(__name__)

COMMAND_TYPE = "SendRequest"
EVENT_REQUEST_SENT = "broker_request_more_created"  # Slice 1 canonical event
ACCESS_STATUS_READY = "ready"
ACCESS_STATUS_COMPLETED = "completed"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_command_id(value: str, field_name: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field_name}_required")
    return text[:128]


def _validate_expected_version(expected: int | None) -> int:
    if expected is None:
        raise ValueError("expected_case_version_required")
    try:
        return int(expected)
    except (TypeError, ValueError) as exc:
        raise ValueError("expected_case_version_invalid") from exc


@dataclass
class CustomerAccessRecord:
    access_id: str
    case_id: str
    request_group_id: str
    tenant_id: str | None
    office_id: str | None
    token_hash: str
    token_nonce: str
    token_iat: int
    token_exp: int
    status: str
    access_version: int
    created_by: str
    issued_at: str
    expires_at: str
    completed_at: str | None = None


@dataclass
class SendRequestSnapshot:
    case: dict[str, Any]
    intake_aggregate: IntakeAggregate | None
    draft: RequestDraft | None
    slice1_aggregate: Slice1Aggregate | None
    open_group: Slice1Group | None
    open_items: list[Slice1Item] = field(default_factory=list)
    ready_access: CustomerAccessRecord | None = None
    latest_intake_events: list[dict[str, Any]] = field(default_factory=list)
    latest_slice1_events: list[dict[str, Any]] = field(default_factory=list)
    stored_outcome: dict[str, Any] | None = None


class SendRequestTx(Protocol):
    def insert_group(self, group: Slice1Group) -> None: ...
    def insert_items(self, items: list[Slice1Item]) -> None: ...
    def insert_slice1_events(self, events: list[dict[str, Any]]) -> None: ...
    def upsert_slice1_aggregate(self, aggregate: Slice1Aggregate) -> None: ...
    def update_legacy_projection(self, case_id: str, patch: dict[str, Any]) -> None: ...
    def upsert_intake_aggregate(self, aggregate: IntakeAggregate) -> None: ...
    def upsert_draft(self, draft: RequestDraft) -> None: ...
    def insert_intake_events(self, events: list[dict[str, Any]]) -> None: ...
    def insert_customer_access(self, access: CustomerAccessRecord) -> None: ...
    def update_case_extra(self, case_id: str, patch: dict[str, Any]) -> None: ...


class SendRequestStore(Protocol):
    def read_snapshot(self, case_id: str) -> SendRequestSnapshot | None: ...
    def accept(
        self,
        *,
        case_id: str,
        actor_identity: str,
        command_id: str,
        idempotency_key: str,
        command_type: str,
        handler: Callable[[SendRequestTx, SendRequestSnapshot], dict[str, Any]],
    ) -> dict[str, Any]: ...


def _replay_response(stored: dict[str, Any]) -> dict[str, Any]:
    prior = dict(stored)
    prior["original_outcome"] = prior.get("outcome")
    prior["outcome"] = "replayed"
    return prior


def _coerce_draft_item_type_for_send(row: dict[str, Any]) -> str:
    """Normalize draft item_type for send; coerce legacy vehicle_information free_text."""
    item_type = str(row.get("item_type") or "").strip().lower()
    field_key = str(row.get("field_key") or "").strip().lower()
    if field_key == "vehicle_information" and item_type in {"", "free_text"}:
        return "vehicle_information"
    return item_type


def normalize_draft_items_for_send(draft_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return draft rows with sendable item_type coercion applied (copy)."""
    out: list[dict[str, Any]] = []
    for raw in draft_items or []:
        row = dict(raw) if isinstance(raw, dict) else {}
        row["item_type"] = _coerce_draft_item_type_for_send(row)
        out.append(row)
    return out


def draft_items_to_slice1_items(draft_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map Capability 2 draft items → Slice 1 ordered request items (exact order)."""
    raw: list[dict[str, Any]] = []
    for idx, item in enumerate(normalize_draft_items_for_send(draft_items), start=1):
        item_type = str(item.get("item_type") or "").strip().lower()
        if item_type not in ALLOWED_ITEM_TYPES:
            raise ValueError("unsupported_draft_item_type_for_send")
        raw.append(
            {
                "request_item_id": str(item.get("request_item_id") or f"req_item_{uuid4().hex[:12]}"),
                "item_type": item_type,
                "label": str(item.get("label") or "").strip(),
                "instructions": str(item.get("instructions") or "").strip(),
                "required": bool(item.get("required", True)),
                "position": int(item.get("position") or idx),
            }
        )
    return _validate_items(raw)


def _access_public_card(
    *,
    access: CustomerAccessRecord,
    launch: CustomerLaunchTarget,
    request_summary: dict[str, Any] | None,
    workflow_state: str | None = None,
) -> dict[str, Any]:
    progress = None
    satisfied = 0
    total = 0
    if isinstance(request_summary, dict):
        raw_progress = request_summary.get("progress") if isinstance(request_summary.get("progress"), dict) else {}
        satisfied = int(raw_progress.get("satisfied") or 0)
        total = int(raw_progress.get("total") or len(request_summary.get("items") or []))
        progress = {
            "satisfied_count": satisfied,
            "total_count": total,
        }
    state = str(workflow_state or "").strip().lower()
    review_ready = state == "broker_review_ready" or (total > 0 and satisfied >= total)
    card = launch.public_card()
    card.update(
        {
            "access_ready": True,
            "access_status": access.status,
            "expires_at": access.expires_at,
            "progress": progress,
            "simple_status": "Ready for Review" if review_ready else "Waiting for customer",
            "request_sent": True,
        }
    )
    return card


def _response(
    *,
    outcome: str,
    command_id: str,
    correlation_id: str,
    idempotency_key: str,
    event_ids: list[str],
    intake_projection: dict[str, Any],
    slice1_projection: dict[str, Any] | None = None,
    customer_access: dict[str, Any] | None = None,
    error_code: str | None = None,
    original_outcome: str | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "outcome": outcome,
        "command_id": command_id,
        "correlation_id": correlation_id,
        "idempotency_key": idempotency_key,
        "event_ids": list(event_ids),
        "aggregate_version": intake_projection.get("aggregate_version"),
        "case_id": intake_projection.get("case_id"),
        "broker_projection": intake_projection,
        "slice1_projection": slice1_projection,
        "customer_access": customer_access,
        "customer_projection": (slice1_projection or {}).get("customer_next_action")
        and {
            "case_id": (slice1_projection or {}).get("case_id"),
            "customer_next_action": (slice1_projection or {}).get("customer_next_action"),
            "open_request": (slice1_projection or {}).get("open_request"),
        }
        or intake_projection.get("customer_projection"),
        "server_timestamp": intake_projection.get("server_timestamp") or _utc_now_iso(),
    }
    if error_code:
        out["error_code"] = error_code
    if original_outcome:
        out["original_outcome"] = original_outcome
    return out


class P20SendRequestCommandService:
    def __init__(self, store: SendRequestStore | None = None):
        self.store = store or _default_store()

    def fetch_customer_access_card(self, case_id: str) -> dict[str, Any] | None:
        snapshot = self.store.read_snapshot(case_id)
        if snapshot is None or snapshot.ready_access is None:
            return None
        access = snapshot.ready_access
        try:
            launch = rebuild_customer_launch_from_material(
                case_id=case_id,
                token_nonce=access.token_nonce,
                token_iat=access.token_iat,
                token_exp=access.token_exp,
            )
        except Exception:
            logger.warning("customer_access_rebuild_failed case_id=%s", case_id)
            return {
                "access_ready": True,
                "access_status": access.status,
                "simple_status": "Waiting for customer",
                "request_sent": True,
                "qr_preparing": True,
                "message": "Request sent. Code is still preparing.",
                "expires_at": access.expires_at,
                "copy_link": None,
                "launch_url": None,
                "qr_payload": None,
            }
        request_summary = None
        workflow_state = None
        if snapshot.slice1_aggregate and snapshot.open_group:
            workflow_state = snapshot.slice1_aggregate.workflow_state
            proj = _projection(
                case_id=case_id,
                state=snapshot.slice1_aggregate.workflow_state,
                aggregate_version=snapshot.slice1_aggregate.aggregate_version,
                group=snapshot.open_group,
                items=snapshot.open_items,
                latest_events=snapshot.latest_slice1_events,
            )
            request_summary = proj.get("open_request")
        return _access_public_card(
            access=access,
            launch=launch,
            request_summary=request_summary,
            workflow_state=workflow_state,
        )

    def validate_presented_access(self, case_id: str, token: str) -> str | None:
        snapshot = self.store.read_snapshot(case_id)
        if snapshot is None or snapshot.ready_access is None:
            return "access_invalid"
        access = snapshot.ready_access
        return validate_access_token(
            presented_token=token,
            expected_hash=access.token_hash,
            token_exp=access.token_exp,
        )

    def send_request(
        self,
        *,
        case_id: str,
        broker_id: str,
        request_draft_id: str,
        expected_case_version: int | None,
        command_id: str,
        idempotency_key: str,
        correlation_id: str | None = None,
        office_id: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        if not case_intake_feature_enabled():
            raise RuntimeError("p20_case_intake_disabled")
        command_id = _normalize_command_id(command_id, "command_id")
        idempotency_key = _normalize_command_id(idempotency_key, "idempotency_key")
        broker_id = _normalize_command_id(broker_id, "broker_id")
        draft_id = _normalize_command_id(request_draft_id, "request_draft_id")
        expected = _validate_expected_version(expected_case_version)
        corr = (correlation_id or command_id).strip()[:128] or command_id

        def _handle(tx: SendRequestTx, snapshot: SendRequestSnapshot) -> dict[str, Any]:
            from services.fiqa_api.inbox_triage.case_close import (
                ERROR_CASE_CLOSED_READ_ONLY,
                case_is_closed_history,
            )

            if isinstance(getattr(snapshot, "stored_outcome", None), dict):
                return _replay_response(snapshot.stored_outcome)

            case = snapshot.case
            intake = snapshot.intake_aggregate
            draft = snapshot.draft
            if case_is_closed_history(case):
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    intake_projection={
                        "case_id": case_id,
                        "aggregate_version": intake.aggregate_version if intake else 0,
                        "customer_projection": {"customer_next_action": None},
                    },
                    error_code=ERROR_CASE_CLOSED_READ_ONLY,
                )

            # Build a minimal intake projection for conflict/reject paths.
            def _intake_proj(
                aggregate: IntakeAggregate | None,
                draft_row: RequestDraft | None,
                open_group: dict[str, Any] | None = None,
            ) -> dict[str, Any]:
                if aggregate is None:
                    return {
                        "case_id": case_id,
                        "aggregate_version": 0,
                        "customer_projection": {"customer_next_action": None},
                    }
                return build_broker_projection(
                    case=case,
                    aggregate=aggregate,
                    draft=draft_row,
                    latest_events=snapshot.latest_intake_events,
                    open_request_group=open_group,
                )

            if intake is None:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    intake_projection=_intake_proj(None, None),
                    error_code="intake_aggregate_missing",
                )

            open_group_dict = None
            if snapshot.open_group:
                open_group_dict = {
                    "request_id": snapshot.open_group.request_id,
                    "status": snapshot.open_group.status,
                }
            current_intake = _intake_proj(intake, draft, open_group_dict)

            if expected != intake.aggregate_version:
                # Refresh with current access card when present.
                access_card = None
                if snapshot.ready_access is not None:
                    try:
                        launch = rebuild_customer_launch_from_material(
                            case_id=case_id,
                            token_nonce=snapshot.ready_access.token_nonce,
                            token_iat=snapshot.ready_access.token_iat,
                            token_exp=snapshot.ready_access.token_exp,
                        )
                        access_card = _access_public_card(
                            access=snapshot.ready_access,
                            launch=launch,
                            request_summary=None,
                        )
                    except Exception:
                        access_card = None
                slice1_proj = None
                if snapshot.slice1_aggregate is not None:
                    slice1_proj = _projection(
                        case_id=case_id,
                        state=snapshot.slice1_aggregate.workflow_state,
                        aggregate_version=snapshot.slice1_aggregate.aggregate_version,
                        group=snapshot.open_group,
                        items=snapshot.open_items,
                        latest_events=snapshot.latest_slice1_events,
                    )
                return _response(
                    outcome="conflict",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    intake_projection=current_intake,
                    slice1_projection=slice1_proj,
                    customer_access=access_card,
                    error_code="version_conflict",
                )

            if str(case.get("service_lane") or "").strip().lower() != SERVICE_LANE_CLAIM:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    intake_projection=current_intake,
                    error_code="lane_mismatch",
                )

            if draft is None or not draft.items:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    intake_projection=current_intake,
                    error_code="request_draft_empty",
                )

            if draft.draft_id != draft_id:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    intake_projection=current_intake,
                    error_code="request_draft_mismatch",
                )

            if snapshot.open_group and snapshot.open_group.status == GROUP_STATUS_OPEN:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    intake_projection=current_intake,
                    error_code="open_request_exists",
                )

            if snapshot.ready_access is not None:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    intake_projection=current_intake,
                    error_code="customer_access_exists",
                )

            slice1_state = (
                snapshot.slice1_aggregate.workflow_state
                if snapshot.slice1_aggregate
                else _legacy_claim_state(case)
            )
            slice1_version = snapshot.slice1_aggregate.aggregate_version if snapshot.slice1_aggregate else 0
            if _is_terminal_state(slice1_state):
                return _response(
                    outcome="conflict",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    intake_projection=current_intake,
                    error_code="case_not_active",
                )
            if not broker_may_create_request_more(slice1_state):
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    intake_projection=current_intake,
                    error_code="illegal_state",
                )

            sendable_draft_items = normalize_draft_items_for_send(list(draft.items))
            unsupported_labels = list_unsupported_send_item_labels(sendable_draft_items)
            if unsupported_labels:
                rejected = _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    intake_projection=current_intake,
                    error_code="unsupported_draft_item_type_for_send",
                )
                rejected["unsupported_items"] = unsupported_labels
                return rejected

            normalized_items = draft_items_to_slice1_items(sendable_draft_items)
            now = _utc_now_iso()
            rid = f"req_{uuid4().hex[:12]}"
            group = Slice1Group(
                request_id=rid,
                case_id=case_id,
                status=GROUP_STATUS_OPEN,
                reason="Broker Send Request from saved draft",
                created_by=broker_id,
                created_at=now,
                updated_at=now,
            )
            items = [
                Slice1Item(
                    request_item_id=item["request_item_id"],
                    request_id=rid,
                    case_id=case_id,
                    item_type=item["item_type"],
                    label=item["label"],
                    instructions=item["instructions"],
                    required=item["required"],
                    position=item["position"],
                    status=ITEM_STATUS_ACTIVE if index == 0 else ITEM_STATUS_QUEUED,
                    created_at=now,
                )
                for index, item in enumerate(normalized_items)
            ]
            next_slice1_version = slice1_version + 1
            event = _event(
                event_type=EVENT_REQUEST_SENT,
                case_id=case_id,
                command_id=command_id,
                correlation_id=corr,
                sequence_number=next_slice1_version,
                aggregate_version=next_slice1_version,
                expected_state_version=slice1_version,
                actor="broker",
                actor_identity=broker_id,
                state_before=slice1_state,
                state_after=STATE_BROKER_MORE_REQUESTED,
                idempotency_key=idempotency_key,
                evidence={
                    "request_id": rid,
                    "requested_item_ids": [item.request_item_id for item in items],
                    "reason": group.reason,
                    "items": [item.as_projection() for item in items],
                    "source_draft_id": draft.draft_id,
                    "source_draft_version": draft.draft_version,
                },
                timestamp=now,
            )
            slice1_projection = _projection(
                case_id=case_id,
                state=STATE_BROKER_MORE_REQUESTED,
                aggregate_version=next_slice1_version,
                group=group,
                items=items,
                latest_events=[event],
                timestamp=now,
            )
            slice1_agg = Slice1Aggregate(
                case_id=case_id,
                workflow_state=STATE_BROKER_MORE_REQUESTED,
                aggregate_version=next_slice1_version,
                active_request_id=rid,
                customer_projection=slice1_projection,
                broker_projection=slice1_projection,
            )

            # Issue customer access BEFORE committing writes so failure rolls back.
            launch = issue_customer_launch_token(
                case_id=case_id,
                external_userid=str(case.get("wecom_external_userid") or "") or None,
                ttl_seconds=DEFAULT_ACCESS_TTL_SECONDS,
            )
            access = CustomerAccessRecord(
                access_id=f"access_{uuid4().hex[:12]}",
                case_id=case_id,
                request_group_id=rid,
                tenant_id=(tenant_id or intake.tenant_id or str(case.get("client_id") or "") or None),
                office_id=(office_id or intake.office_id or str(case.get("asserted_org_id") or "") or None),
                token_hash=launch.token_hash,
                token_nonce=launch.token_nonce,
                token_iat=launch.token_iat,
                token_exp=launch.token_exp,
                status=ACCESS_STATUS_READY,
                access_version=1,
                created_by=broker_id,
                issued_at=now,
                expires_at=launch.expires_at_iso,
            )
            access_card = _access_public_card(
                access=access,
                launch=launch,
                request_summary=slice1_projection.get("open_request"),
                workflow_state=str(slice1_projection.get("workflow_state") or ""),
            )

            # Persist Slice 1 + access + intake lifecycle in one transaction.
            tx.insert_group(group)
            tx.insert_items(items)
            tx.insert_slice1_events([event])
            tx.upsert_slice1_aggregate(slice1_agg)
            legacy_patch = _legacy_projection_patch(slice1_projection)
            legacy_patch["slice1_capability_version"] = SLICE1_CAPABILITY_VERSION
            legacy_patch["p20_slice1_capability_version"] = SLICE1_CAPABILITY_VERSION
            legacy_patch["admin_lifecycle"] = ADMIN_LIFECYCLE_ACTIVE
            tx.update_legacy_projection(case_id, legacy_patch)
            tx.update_case_extra(
                case_id,
                {
                    "slice1_capability_version": SLICE1_CAPABILITY_VERSION,
                    "p20_slice1_capability_version": SLICE1_CAPABILITY_VERSION,
                    "admin_lifecycle": ADMIN_LIFECYCLE_ACTIVE,
                },
            )
            tx.insert_customer_access(access)

            next_intake_version = intake.aggregate_version + 1
            sent_draft = RequestDraft(
                draft_id=draft.draft_id,
                case_id=draft.case_id,
                draft_version=draft.draft_version,
                items=list(draft.items),
                content_hash=draft.content_hash,
                updated_by=broker_id,
                created_at=draft.created_at,
                updated_at=now,
                status="sent",
            )
            intake.admin_lifecycle = ADMIN_LIFECYCLE_ACTIVE
            intake.aggregate_version = next_intake_version
            intake.updated_at = now
            intake_event = {
                "event_id": f"evt_{uuid4().hex[:16]}",
                "case_id": case_id,
                "event_type": "request_sent",
                "command_id": command_id,
                "correlation_id": corr,
                "sequence_number": next_intake_version,
                "aggregate_version": next_intake_version,
                "expected_state_version": expected,
                "actor": "broker",
                "actor_identity": broker_id,
                "state_before": ADMIN_LIFECYCLE_DRAFT,
                "state_after": ADMIN_LIFECYCLE_ACTIVE,
                "visibility": "broker",
                "evidence": {
                    "draft_id": draft.draft_id,
                    "request_id": rid,
                    "access_id": access.access_id,
                    "item_count": len(items),
                },
                "idempotency_key": idempotency_key,
                "created_at": now,
            }
            open_after = {"request_id": rid, "status": GROUP_STATUS_OPEN}
            intake_projection = build_broker_projection(
                case={**case, **legacy_patch},
                aggregate=intake,
                draft=sent_draft,
                latest_events=list(snapshot.latest_intake_events) + [intake_event],
                open_request_group=open_after,
            )
            # Attach access card on broker projection for Workbench refresh.
            intake_projection["customer_access"] = access_card
            intake_projection["workflow_state"] = STATE_BROKER_MORE_REQUESTED
            intake_projection["simple_status"] = "Waiting for customer"
            intake_projection["allowed_next_commands"] = ["WaitForCustomer"]
            intake.broker_projection = intake_projection
            intake.customer_projection = {
                "case_id": case_id,
                "customer_next_action": slice1_projection.get("customer_next_action"),
                "message": "Customer task ready",
                "invite": {"status": "ready", "expires_at": access.expires_at},
            }
            tx.upsert_draft(sent_draft)
            tx.upsert_intake_aggregate(intake)
            tx.insert_intake_events([intake_event])

            # Never put raw token into durable outcome logs — card has launch_url only.
            return _response(
                outcome="accepted",
                command_id=command_id,
                correlation_id=corr,
                idempotency_key=idempotency_key,
                event_ids=[event["event_id"], intake_event["event_id"]],
                intake_projection=intake_projection,
                slice1_projection=slice1_projection,
                customer_access=access_card,
            )

        result = self.store.accept(
            case_id=case_id,
            actor_identity=broker_id,
            command_id=command_id,
            idempotency_key=idempotency_key,
            command_type=COMMAND_TYPE,
            handler=_handle,
        )
        logger.info(
            "SendRequest outcome=%s case_id=%s aggregate_version=%s",
            result.get("outcome"),
            case_id,
            result.get("aggregate_version"),
        )
        return result


class InMemorySendRequestStore:
    """Test store with transactional rollback for Capability 3A."""

    def __init__(
        self,
        *,
        cases: dict[str, dict[str, Any]] | None = None,
        intake_aggregates: dict[str, IntakeAggregate] | None = None,
        drafts: dict[str, RequestDraft] | None = None,
        slice1_aggregates: dict[str, Slice1Aggregate] | None = None,
        groups: dict[str, Slice1Group] | None = None,
        items: dict[str, Slice1Item] | None = None,
    ):
        self.cases = cases if cases is not None else {}
        self.intake_aggregates = intake_aggregates if intake_aggregates is not None else {}
        self.drafts = drafts if drafts is not None else {}
        self.slice1_aggregates = slice1_aggregates if slice1_aggregates is not None else {}
        self.groups = groups if groups is not None else {}
        self.items = items if items is not None else {}
        self.access_by_case: dict[str, CustomerAccessRecord] = {}
        self.intake_events: dict[str, list[dict[str, Any]]] = {}
        self.slice1_events: dict[str, list[dict[str, Any]]] = {}
        self.outcomes: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.command_outcomes: dict[tuple[str, str], dict[str, Any]] = {}
        self.fail_next_write = False

    def read_snapshot(self, case_id: str) -> SendRequestSnapshot | None:
        case = self.cases.get(case_id)
        if case is None:
            return None
        aggregate = self.slice1_aggregates.get(case_id)
        open_group = None
        if aggregate and aggregate.active_request_id:
            open_group = self.groups.get(aggregate.active_request_id)
        if open_group is None:
            open_group = next(
                (g for g in self.groups.values() if g.case_id == case_id and g.status == GROUP_STATUS_OPEN),
                None,
            )
        if open_group is None:
            candidates = [g for g in self.groups.values() if g.case_id == case_id]
            if candidates:
                open_group = sorted(
                    candidates,
                    key=lambda g: (g.updated_at or "", g.created_at or "", g.request_id),
                    reverse=True,
                )[0]
        open_items = (
            sorted(
                [i for i in self.items.values() if i.request_id == open_group.request_id],
                key=lambda x: x.position,
            )
            if open_group
            else []
        )
        return SendRequestSnapshot(
            case=dict(case),
            intake_aggregate=self.intake_aggregates.get(case_id),
            draft=self.drafts.get(case_id),
            slice1_aggregate=aggregate,
            open_group=open_group,
            open_items=open_items,
            ready_access=self.access_by_case.get(case_id),
            latest_intake_events=list(self.intake_events.get(case_id, [])),
            latest_slice1_events=list(self.slice1_events.get(case_id, [])),
        )

    def insert_group(self, group: Slice1Group) -> None:
        if self.fail_next_write:
            self.fail_next_write = False
            raise RuntimeError("forced_write_failure")
        self.groups[group.request_id] = deepcopy(group)

    def insert_items(self, items: list[Slice1Item]) -> None:
        for item in items:
            self.items[item.request_item_id] = deepcopy(item)

    def insert_slice1_events(self, events: list[dict[str, Any]]) -> None:
        for event in events:
            self.slice1_events.setdefault(str(event["case_id"]), []).append(dict(event))

    def upsert_slice1_aggregate(self, aggregate: Slice1Aggregate) -> None:
        self.slice1_aggregates[aggregate.case_id] = deepcopy(aggregate)

    def update_legacy_projection(self, case_id: str, patch: dict[str, Any]) -> None:
        self.cases.setdefault(case_id, {}).update(patch)

    def upsert_intake_aggregate(self, aggregate: IntakeAggregate) -> None:
        self.intake_aggregates[aggregate.case_id] = deepcopy(aggregate)

    def upsert_draft(self, draft: RequestDraft) -> None:
        self.drafts[draft.case_id] = deepcopy(draft)

    def insert_intake_events(self, events: list[dict[str, Any]]) -> None:
        for event in events:
            self.intake_events.setdefault(str(event["case_id"]), []).append(dict(event))

    def insert_customer_access(self, access: CustomerAccessRecord) -> None:
        if access.status == ACCESS_STATUS_READY:
            existing = self.access_by_case.get(access.case_id)
            if existing and existing.status == ACCESS_STATUS_READY and existing.access_id != access.access_id:
                raise RuntimeError("duplicate_ready_access")
        self.access_by_case[access.case_id] = deepcopy(access)

    def update_case_extra(self, case_id: str, patch: dict[str, Any]) -> None:
        self.cases.setdefault(case_id, {}).update(patch)

    def accept(
        self,
        *,
        case_id: str,
        actor_identity: str,
        command_id: str,
        idempotency_key: str,
        command_type: str,
        handler: Callable[["InMemorySendRequestStore", SendRequestSnapshot], dict[str, Any]],
    ) -> dict[str, Any]:
        prior = self.outcomes.get((case_id, actor_identity, idempotency_key)) or self.command_outcomes.get(
            (case_id, command_id)
        )
        snapshot = self.read_snapshot(case_id)
        if snapshot is None:
            raise ValueError("case_not_found")
        if prior:
            setattr(snapshot, "stored_outcome", prior)
            return handler(self, snapshot)
        before = deepcopy(
            (
                self.cases,
                self.intake_aggregates,
                self.drafts,
                self.slice1_aggregates,
                self.groups,
                self.items,
                self.access_by_case,
                self.intake_events,
                self.slice1_events,
                self.outcomes,
                self.command_outcomes,
            )
        )
        try:
            response = handler(self, snapshot)
            # Persist accepted/conflict/rejected outcomes for replay (same as Slice 1).
            self.outcomes[(case_id, actor_identity, idempotency_key)] = dict(response)
            self.command_outcomes[(case_id, command_id)] = dict(response)
            return response
        except Exception:
            (
                self.cases,
                self.intake_aggregates,
                self.drafts,
                self.slice1_aggregates,
                self.groups,
                self.items,
                self.access_by_case,
                self.intake_events,
                self.slice1_events,
                self.outcomes,
                self.command_outcomes,
            ) = before
            raise


_DEFAULT_SVC: P20SendRequestCommandService | None = None


def _default_store() -> SendRequestStore:
    from services.fiqa_api.db.service_record_repository import make_send_request_postgres_store

    return make_send_request_postgres_store()


def default_send_request_service() -> P20SendRequestCommandService:
    global _DEFAULT_SVC
    if _DEFAULT_SVC is None:
        _DEFAULT_SVC = P20SendRequestCommandService()
    return _DEFAULT_SVC
