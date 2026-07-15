"""P20 Slice 1 command boundary for Broker Request More -> Customer Continue."""

from __future__ import annotations

import logging
import os
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol
from uuid import uuid4

from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_BROKER_DONE,
    CLAIM_PHASE_BROKER_NEEDS_MORE_INFO,
    CLAIM_PHASE_BROKER_REVIEW,
    CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    GUIDED_STATE_BROKER_NEEDS_MORE_INFO,
    GUIDED_STATE_READY_FOR_BROKER_REVIEW,
    SERVICE_LANE_CLAIM,
    derive_claim_phase,
)

logger = logging.getLogger(__name__)

SLICE1_CAPABILITY_VERSION = 1
SLICE1_FLAG_ENV = "P20_SLICE1_REQUEST_MORE"

STATE_BROKER_REVIEWING = "broker_reviewing"
STATE_BROKER_MORE_REQUESTED = "broker_more_requested"
STATE_CUSTOMER_CONTINUING = "customer_continuing"
STATE_BROKER_REVIEW_READY = "broker_review_ready"

ITEM_STATUS_QUEUED = "queued"
ITEM_STATUS_ACTIVE = "active"
ITEM_STATUS_SATISFIED = "satisfied"
ITEM_STATUS_WITHDRAWN = "withdrawn"

GROUP_STATUS_OPEN = "open"
GROUP_STATUS_COMPLETED = "completed"

ALLOWED_ITEM_TYPES = frozenset(
    {
        "vin",
        "policy_or_insurance_card",
        "free_text",
        "photo_evidence",
    }
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _truthy_env(name: str) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def slice1_feature_flag_enabled() -> bool:
    return _truthy_env(SLICE1_FLAG_ENV)


def case_supports_slice1(case: dict[str, Any]) -> bool:
    raw = case.get("slice1_capability_version")
    if raw is None:
        raw = case.get("p20_slice1_capability_version")
    try:
        return int(raw or 0) >= SLICE1_CAPABILITY_VERSION
    except (TypeError, ValueError):
        return False


def slice1_enabled_for_case(case: dict[str, Any]) -> bool:
    return slice1_feature_flag_enabled() or case_supports_slice1(case)


def _legacy_claim_state(case: dict[str, Any]) -> str:
    explicit = str(case.get("claim_phase") or "").strip().lower()
    if explicit == CLAIM_PHASE_BROKER_REVIEW:
        return STATE_BROKER_REVIEWING
    if explicit == CLAIM_PHASE_BROKER_NEEDS_MORE_INFO:
        return STATE_BROKER_MORE_REQUESTED
    if explicit == CLAIM_PHASE_INTAKE_READY_FOR_BROKER:
        return STATE_BROKER_REVIEW_READY
    if explicit == CLAIM_PHASE_BROKER_DONE:
        return "case_complete"
    phase = derive_claim_phase(case)
    if phase == CLAIM_PHASE_BROKER_REVIEW:
        return STATE_BROKER_REVIEWING
    if phase == CLAIM_PHASE_BROKER_NEEDS_MORE_INFO:
        return STATE_BROKER_MORE_REQUESTED
    if phase == CLAIM_PHASE_INTAKE_READY_FOR_BROKER:
        return STATE_BROKER_REVIEW_READY
    if phase == CLAIM_PHASE_BROKER_DONE:
        return "case_complete"
    return phase or ""


def _is_terminal_state(state: str) -> bool:
    return state in {"case_complete", "cancelled", "rejected", "archived"}


@dataclass
class Slice1Item:
    request_item_id: str
    request_id: str
    case_id: str
    item_type: str
    label: str
    instructions: str
    required: bool
    position: int
    status: str
    created_at: str
    satisfied_at: str | None = None
    satisfied_by_event_id: str | None = None

    def as_projection(self) -> dict[str, Any]:
        return {
            "request_item_id": self.request_item_id,
            "request_id": self.request_id,
            "item_type": self.item_type,
            "label": self.label,
            "instructions": self.instructions,
            "required": self.required,
            "position": self.position,
            "status": self.status,
            "actionable": self.status == ITEM_STATUS_ACTIVE,
            "created_at": self.created_at,
            "satisfied_at": self.satisfied_at,
            "satisfied_by_event_id": self.satisfied_by_event_id,
        }


@dataclass
class Slice1Group:
    request_id: str
    case_id: str
    status: str
    reason: str
    created_by: str
    created_at: str
    updated_at: str
    completed_at: str | None = None


@dataclass
class Slice1Aggregate:
    case_id: str
    workflow_state: str
    aggregate_version: int
    active_request_id: str | None = None
    customer_projection: dict[str, Any] = field(default_factory=dict)
    broker_projection: dict[str, Any] = field(default_factory=dict)


@dataclass
class Slice1Snapshot:
    case: dict[str, Any]
    aggregate: Slice1Aggregate | None = None
    group: Slice1Group | None = None
    items: list[Slice1Item] = field(default_factory=list)
    latest_events: list[dict[str, Any]] = field(default_factory=list)


class Slice1Tx(Protocol):
    def insert_group(self, group: Slice1Group) -> None: ...
    def insert_items(self, items: list[Slice1Item]) -> None: ...
    def update_items(self, items: list[Slice1Item]) -> None: ...
    def update_group(self, group: Slice1Group) -> None: ...
    def insert_events(self, events: list[dict[str, Any]]) -> None: ...
    def upsert_aggregate(self, aggregate: Slice1Aggregate) -> None: ...
    def update_legacy_projection(self, case_id: str, patch: dict[str, Any]) -> None: ...


class Slice1Store(Protocol):
    def read_snapshot(self, case_id: str) -> Slice1Snapshot | None: ...
    def accept(
        self,
        *,
        case_id: str,
        actor_identity: str,
        command_id: str,
        idempotency_key: str,
        command_type: str,
        handler: Callable[[Slice1Tx, Slice1Snapshot], dict[str, Any]],
    ) -> dict[str, Any]: ...


def _projection(
    *,
    case_id: str,
    state: str,
    aggregate_version: int,
    group: Slice1Group | None,
    items: list[Slice1Item],
    latest_events: list[dict[str, Any]] | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    now = timestamp or _utc_now_iso()
    ordered = sorted(items, key=lambda item: item.position)
    active = next((item for item in ordered if item.status == ITEM_STATUS_ACTIVE), None)
    queued = [item for item in ordered if item.status == ITEM_STATUS_QUEUED]
    satisfied = [item for item in ordered if item.status == ITEM_STATUS_SATISFIED]
    total = len(ordered)
    progress = {
        "satisfied": len(satisfied),
        "total": total,
        "remaining": len([item for item in ordered if item.status in {ITEM_STATUS_ACTIVE, ITEM_STATUS_QUEUED}]),
    }
    if active:
        evidence_types = {"photo_evidence", "policy_or_insurance_card"}
        customer_action = {
            "action_type": "provide_evidence" if active.item_type in evidence_types else "provide_fact",
            "request_id": active.request_id,
            "request_item_id": active.request_item_id,
            "title": active.label,
            "instructions": active.instructions,
            "required_input": active.item_type,
            "status": active.status,
            "ordering": {"position": active.position, "total": total},
            "allowed_actions": ["submit_request_item", "contact_broker"],
            "version": aggregate_version,
            "last_updated_at": now,
        }
    elif state == STATE_BROKER_REVIEW_READY:
        customer_action = {
            "action_type": "wait_for_broker_review",
            "request_id": group.request_id if group else None,
            "request_item_id": None,
            "title": "资料已提交给陈总审核",
            "instructions": "陈总会查看你补充的资料。",
            "required_input": None,
            "status": "waiting",
            "ordering": {"position": None, "total": total},
            "allowed_actions": ["contact_broker"],
            "version": aggregate_version,
            "last_updated_at": now,
        }
    else:
        customer_action = {
            "action_type": "contact_broker",
            "request_id": group.request_id if group else None,
            "request_item_id": None,
            "title": "请联系陈总办公室",
            "instructions": "",
            "required_input": None,
            "status": "blocked",
            "ordering": {"position": None, "total": total},
            "allowed_actions": ["contact_broker"],
            "version": aggregate_version,
            "last_updated_at": now,
        }
    if state in {STATE_BROKER_MORE_REQUESTED, STATE_CUSTOMER_CONTINUING}:
        broker_action_type = "wait_for_customer_item"
        broker_status = "waiting_for_customer"
    elif state == STATE_BROKER_REVIEW_READY:
        broker_action_type = "review_customer_response"
        broker_status = "review_ready"
    elif state == STATE_BROKER_REVIEWING:
        broker_action_type = "create_request"
        broker_status = "reviewing"
    else:
        broker_action_type = "none"
        broker_status = "none"
    broker_action = {
        "action_type": broker_action_type,
        "status": broker_status,
        "request_id": group.request_id if group else None,
        "version": aggregate_version,
        "last_updated_at": now,
    }
    request_summary = None
    if group:
        request_summary = {
            "request_id": group.request_id,
            "status": group.status,
            "reason": group.reason,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "completed_at": group.completed_at,
            "active_item": active.as_projection() if active else None,
            "queued_items": [item.as_projection() for item in queued],
            "items": [item.as_projection() for item in ordered],
            "progress": progress,
        }
    return {
        "case_id": case_id,
        "workflow_state": state,
        "aggregate_version": aggregate_version,
        "customer_next_action": customer_action,
        "broker_next_action": broker_action,
        "open_request": request_summary,
        "queued_request_items": [item.as_projection() for item in queued],
        "request_progress": progress,
        "latest_events": list(latest_events or [])[-20:],
        "server_timestamp": now,
    }


def _legacy_projection_patch(projection: dict[str, Any]) -> dict[str, Any]:
    state = str(projection.get("workflow_state") or "")
    claim_phase = CLAIM_PHASE_BROKER_NEEDS_MORE_INFO
    guided = GUIDED_STATE_BROKER_NEEDS_MORE_INFO
    if state == STATE_BROKER_REVIEW_READY:
        claim_phase = CLAIM_PHASE_INTAKE_READY_FOR_BROKER
        guided = GUIDED_STATE_READY_FOR_BROKER_REVIEW
    request = projection.get("open_request") if isinstance(projection.get("open_request"), dict) else None
    return {
        "slice1_capability_version": SLICE1_CAPABILITY_VERSION,
        "p20_slice1_projection": projection,
        "claim_phase": claim_phase,
        "guided_workflow_state": guided,
        "broker_next_step": (projection.get("broker_next_action") or {}).get("status") or "",
        "office_broker_next_step": (projection.get("broker_next_action") or {}).get("status") or "",
        "p20_slice1_request_summary": request,
    }


def _event(
    *,
    event_type: str,
    case_id: str,
    command_id: str,
    correlation_id: str,
    sequence_number: int,
    aggregate_version: int,
    expected_state_version: int,
    actor: str,
    actor_identity: str,
    state_before: str,
    state_after: str,
    idempotency_key: str,
    evidence: dict[str, Any],
    event_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    return {
        "event_id": event_id or f"evt_{uuid4().hex[:16]}",
        "case_id": case_id,
        "event_type": event_type,
        "command_id": command_id,
        "correlation_id": correlation_id,
        "sequence_number": sequence_number,
        "aggregate_version": aggregate_version,
        "expected_state_version": expected_state_version,
        "actor": actor,
        "actor_identity": actor_identity,
        "state_before": state_before,
        "state_after": state_after,
        "visibility": "customer_and_broker",
        "evidence": evidence,
        "idempotency_key": idempotency_key,
        "created_at": timestamp or _utc_now_iso(),
    }


def _response(
    *,
    outcome: str,
    command_id: str,
    correlation_id: str,
    idempotency_key: str,
    event_ids: list[str],
    projection: dict[str, Any],
    error_code: str | None = None,
    original_outcome: str | None = None,
) -> dict[str, Any]:
    out = {
        "outcome": outcome,
        "command_id": command_id,
        "correlation_id": correlation_id,
        "idempotency_key": idempotency_key,
        "event_ids": event_ids,
        "aggregate_version": projection.get("aggregate_version"),
        "customer_projection": projection,
        "broker_projection": projection,
        "request_summary": projection.get("open_request"),
        "server_timestamp": projection.get("server_timestamp"),
    }
    if error_code:
        out["error_code"] = error_code
    if original_outcome:
        out["original_outcome"] = original_outcome
    return out


def _log_command_outcome(
    *,
    command_type: str,
    case_id: str,
    result: dict[str, Any],
) -> None:
    """Non-sensitive Slice 1 observability — no tokens, facts, or evidence bytes."""
    projection = result.get("customer_projection") if isinstance(result.get("customer_projection"), dict) else {}
    action = projection.get("customer_next_action") if isinstance(projection.get("customer_next_action"), dict) else {}
    progress = projection.get("request_progress") if isinstance(projection.get("request_progress"), dict) else {}
    logger.info(
        "p20_slice1_command_outcome",
        extra={
            "slice1_command_type": command_type,
            "slice1_case_id": case_id,
            "slice1_outcome": result.get("outcome"),
            "slice1_error_code": result.get("error_code"),
            "slice1_aggregate_version": result.get("aggregate_version"),
            "slice1_event_count": len(result.get("event_ids") or []),
            "slice1_workflow_state": projection.get("workflow_state"),
            "slice1_customer_action_type": action.get("action_type"),
            "slice1_progress_satisfied": progress.get("satisfied"),
            "slice1_progress_total": progress.get("total"),
        },
    )


def _replay_response(stored: dict[str, Any]) -> dict[str, Any]:
    prior = dict(stored)
    prior["original_outcome"] = prior.get("outcome")
    prior["outcome"] = "replayed"
    return prior


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
    except (TypeError, ValueError):
        raise ValueError("expected_case_version_invalid") from None


def _validate_items(raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("requested_items_required")
    out: list[dict[str, Any]] = []
    seen_positions: set[int] = set()
    for idx, raw in enumerate(raw_items, start=1):
        item = raw if isinstance(raw, dict) else {}
        item_type = str(item.get("item_type") or item.get("type") or "").strip().lower()
        if item_type not in ALLOWED_ITEM_TYPES:
            raise ValueError("unsupported_request_item_type")
        label = str(item.get("label") or "").strip()
        if not label:
            raise ValueError("request_item_label_required")
        position = int(item.get("position") or idx)
        if position in seen_positions:
            raise ValueError("duplicate_request_item_position")
        seen_positions.add(position)
        out.append(
            {
                "request_item_id": str(item.get("request_item_id") or f"req_item_{uuid4().hex[:12]}").strip(),
                "item_type": item_type,
                "label": label[:160],
                "instructions": str(item.get("instructions") or "").strip()[:1000],
                "required": bool(item.get("required", True)),
                "position": position,
            }
        )
    out.sort(key=lambda item: item["position"])
    expected = list(range(1, len(out) + 1))
    positions = [int(item["position"]) for item in out]
    if positions != expected:
        raise ValueError("request_item_positions_must_be_contiguous")
    return out


class P20Slice1CommandService:
    def __init__(self, store: Slice1Store | None = None):
        self.store = store or _default_store()

    def fetch_projection(self, case_id: str) -> dict[str, Any] | None:
        snapshot = self.store.read_snapshot(case_id)
        if snapshot is None:
            return None
        if not slice1_enabled_for_case(snapshot.case) and snapshot.aggregate is None:
            return None
        if snapshot.aggregate is None:
            state = _legacy_claim_state(snapshot.case)
            projection = _projection(
                case_id=case_id,
                state=state,
                aggregate_version=0,
                group=None,
                items=[],
                latest_events=[],
                timestamp=str(snapshot.case.get("updated_at") or "") or None,
            )
            return projection
        return _projection(
            case_id=case_id,
            state=snapshot.aggregate.workflow_state,
            aggregate_version=snapshot.aggregate.aggregate_version,
            group=snapshot.group,
            items=snapshot.items,
            latest_events=snapshot.latest_events,
        )

    def accept_request_more(
        self,
        *,
        case_id: str,
        broker_id: str,
        command_id: str,
        idempotency_key: str,
        expected_case_version: int | None,
        requested_items: list[dict[str, Any]],
        reason: str = "",
        request_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        command_id = _normalize_command_id(command_id, "command_id")
        idempotency_key = _normalize_command_id(idempotency_key, "idempotency_key")
        broker_id = _normalize_command_id(broker_id, "broker_id")
        expected = _validate_expected_version(expected_case_version)
        normalized_items = _validate_items(requested_items)
        corr = (correlation_id or command_id).strip()[:128] or command_id

        def _handle(tx: Slice1Tx, snapshot: Slice1Snapshot) -> dict[str, Any]:
            replay = getattr(snapshot, "stored_outcome", None)
            if isinstance(replay, dict):
                return _replay_response(replay)
            case = snapshot.case
            aggregate = snapshot.aggregate
            current_state = aggregate.workflow_state if aggregate else _legacy_claim_state(case)
            current_version = aggregate.aggregate_version if aggregate else 0
            current_projection = _projection(
                case_id=case_id,
                state=current_state,
                aggregate_version=current_version,
                group=snapshot.group,
                items=snapshot.items,
                latest_events=snapshot.latest_events,
            )
            if str(case.get("service_lane") or "").strip().lower() != SERVICE_LANE_CLAIM:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code="lane_mismatch",
                )
            if not slice1_enabled_for_case(case):
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code="slice1_not_enabled",
                )
            if expected != current_version:
                return _response(
                    outcome="conflict",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code="version_conflict",
                )
            if _is_terminal_state(current_state):
                return _response(
                    outcome="conflict",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code="case_not_active",
                )
            if current_state != STATE_BROKER_REVIEWING:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code="illegal_state",
                )
            if snapshot.group and snapshot.group.status == GROUP_STATUS_OPEN:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code="open_request_exists",
                )
            now = _utc_now_iso()
            rid = (request_id or f"req_{uuid4().hex[:12]}").strip()
            group = Slice1Group(
                request_id=rid,
                case_id=case_id,
                status=GROUP_STATUS_OPEN,
                reason=(reason or "").strip()[:1000],
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
            next_version = current_version + 1
            event = _event(
                event_type="broker_request_more_created",
                case_id=case_id,
                command_id=command_id,
                correlation_id=corr,
                sequence_number=next_version,
                aggregate_version=next_version,
                expected_state_version=expected,
                actor="broker",
                actor_identity=broker_id,
                state_before=current_state,
                state_after=STATE_BROKER_MORE_REQUESTED,
                idempotency_key=idempotency_key,
                evidence={
                    "request_id": rid,
                    "requested_item_ids": [item.request_item_id for item in items],
                    "reason": group.reason,
                    "items": [item.as_projection() for item in items],
                },
                timestamp=now,
            )
            projection = _projection(
                case_id=case_id,
                state=STATE_BROKER_MORE_REQUESTED,
                aggregate_version=next_version,
                group=group,
                items=items,
                latest_events=[event],
                timestamp=now,
            )
            aggregate_out = Slice1Aggregate(
                case_id=case_id,
                workflow_state=STATE_BROKER_MORE_REQUESTED,
                aggregate_version=next_version,
                active_request_id=rid,
                customer_projection=projection,
                broker_projection=projection,
            )
            tx.insert_group(group)
            tx.insert_items(items)
            tx.insert_events([event])
            tx.upsert_aggregate(aggregate_out)
            tx.update_legacy_projection(case_id, _legacy_projection_patch(projection))
            return _response(
                outcome="accepted",
                command_id=command_id,
                correlation_id=corr,
                idempotency_key=idempotency_key,
                event_ids=[event["event_id"]],
                projection=projection,
            )

        result = self.store.accept(
            case_id=case_id,
            actor_identity=broker_id,
            command_id=command_id,
            idempotency_key=idempotency_key,
            command_type="broker_request_more_create",
            handler=_handle,
        )
        _log_command_outcome(command_type="broker_request_more_create", case_id=case_id, result=result)
        return result

    def submit_request_item(
        self,
        *,
        case_id: str,
        customer_id: str,
        active_request_item_id: str,
        command_id: str,
        idempotency_key: str,
        expected_case_version: int | None,
        client_draft_id: str | None = None,
        fact: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        command_id = _normalize_command_id(command_id, "command_id")
        idempotency_key = _normalize_command_id(idempotency_key, "idempotency_key")
        customer_id = _normalize_command_id(customer_id, "customer_id")
        item_id = _normalize_command_id(active_request_item_id, "active_request_item_id")
        expected = _validate_expected_version(expected_case_version)
        corr = (correlation_id or command_id).strip()[:128] or command_id
        fact_payload = fact if isinstance(fact, dict) else None
        evidence_payload = evidence if isinstance(evidence, dict) else None
        if bool(fact_payload) == bool(evidence_payload):
            raise ValueError("exactly_one_fact_or_evidence_required")

        def _handle(tx: Slice1Tx, snapshot: Slice1Snapshot) -> dict[str, Any]:
            replay = getattr(snapshot, "stored_outcome", None)
            if isinstance(replay, dict):
                return _replay_response(replay)
            aggregate = snapshot.aggregate
            state = aggregate.workflow_state if aggregate else _legacy_claim_state(snapshot.case)
            current_version = aggregate.aggregate_version if aggregate else 0
            current_projection = _projection(
                case_id=case_id,
                state=state,
                aggregate_version=current_version,
                group=snapshot.group,
                items=snapshot.items,
                latest_events=snapshot.latest_events,
            )
            if expected != current_version:
                return _response(
                    outcome="conflict",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code="version_conflict",
                )
            if state not in {STATE_BROKER_MORE_REQUESTED, STATE_CUSTOMER_CONTINUING}:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code="illegal_state",
                )
            if not snapshot.group or snapshot.group.status != GROUP_STATUS_OPEN:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code="open_request_not_found",
                )
            items = sorted(snapshot.items, key=lambda i: i.position)
            active = next((item for item in items if item.status == ITEM_STATUS_ACTIVE), None)
            if active is None or active.request_item_id != item_id:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code="request_item_not_active",
                )
            receipt_payload: dict[str, Any]
            receipt_type = "field_saved"
            if fact_payload:
                field_name = str(fact_payload.get("field") or fact_payload.get("field_id") or "").strip()
                value = str(fact_payload.get("value") or "").strip()
                if not field_name or not value:
                    return _response(
                        outcome="rejected",
                        command_id=command_id,
                        correlation_id=corr,
                        idempotency_key=idempotency_key,
                        event_ids=[],
                        projection=current_projection,
                        error_code="fact_payload_invalid",
                    )
                receipt_payload = {
                    "request_id": active.request_id,
                    "request_item_id": active.request_item_id,
                    "field_id": field_name,
                    "value": value,
                    "client_draft_id": client_draft_id,
                }
            else:
                attachment_id = str((evidence_payload or {}).get("attachment_id") or "").strip()
                if not attachment_id:
                    return _response(
                        outcome="rejected",
                        command_id=command_id,
                        correlation_id=corr,
                        idempotency_key=idempotency_key,
                        event_ids=[],
                        projection=current_projection,
                        error_code="evidence_payload_invalid",
                    )
                receipt_type = "evidence_received"
                receipt_payload = {
                    "request_id": active.request_id,
                    "request_item_id": active.request_item_id,
                    "attachment_id": attachment_id,
                    "client_draft_id": client_draft_id,
                }
            now = _utc_now_iso()
            events: list[dict[str, Any]] = []
            sequence = current_version
            if state == STATE_BROKER_MORE_REQUESTED:
                sequence += 1
                events.append(
                    _event(
                        event_type="customer_continue_started",
                        case_id=case_id,
                        command_id=command_id,
                        correlation_id=corr,
                        sequence_number=sequence,
                        aggregate_version=sequence,
                        expected_state_version=expected,
                        actor="customer",
                        actor_identity=customer_id,
                        state_before=state,
                        state_after=STATE_CUSTOMER_CONTINUING,
                        idempotency_key=idempotency_key,
                        evidence={
                            "request_id": active.request_id,
                            "request_item_id": active.request_item_id,
                            "client_draft_id": client_draft_id,
                        },
                        timestamp=now,
                    )
                )
            receipt_state_before = STATE_CUSTOMER_CONTINUING if events else state
            sequence += 1
            receipt_event = _event(
                event_type=receipt_type,
                case_id=case_id,
                command_id=command_id,
                correlation_id=corr,
                sequence_number=sequence,
                aggregate_version=sequence,
                expected_state_version=expected,
                actor="customer",
                actor_identity=customer_id,
                state_before=receipt_state_before,
                state_after=STATE_CUSTOMER_CONTINUING,
                idempotency_key=idempotency_key,
                evidence=receipt_payload,
                timestamp=now,
            )
            events.append(receipt_event)
            active.status = ITEM_STATUS_SATISFIED
            active.satisfied_at = now
            sequence += 1
            remaining = [item for item in items if item.status == ITEM_STATUS_QUEUED]
            next_state = STATE_CUSTOMER_CONTINUING if remaining else STATE_BROKER_REVIEW_READY
            satisfaction_event = _event(
                event_type="customer_request_item_satisfied",
                case_id=case_id,
                command_id=command_id,
                correlation_id=corr,
                sequence_number=sequence,
                aggregate_version=sequence,
                expected_state_version=expected,
                actor="system",
                actor_identity="workflow_engine",
                state_before=STATE_CUSTOMER_CONTINUING,
                state_after=next_state,
                idempotency_key=idempotency_key,
                evidence={
                    "request_id": active.request_id,
                    "request_item_id": active.request_item_id,
                    "satisfied_by_event_id": receipt_event["event_id"],
                    "next_ordered_item_id": remaining[0].request_item_id if remaining else None,
                },
                timestamp=now,
            )
            active.satisfied_by_event_id = satisfaction_event["event_id"]
            events.append(satisfaction_event)
            group = snapshot.group
            if remaining:
                remaining[0].status = ITEM_STATUS_ACTIVE
                group.updated_at = now
            else:
                group.status = GROUP_STATUS_COMPLETED
                group.completed_at = now
                group.updated_at = now
                sequence += 1
                events.append(
                    _event(
                        event_type="supplement_submitted",
                        case_id=case_id,
                        command_id=command_id,
                        correlation_id=corr,
                        sequence_number=sequence,
                        aggregate_version=sequence,
                        expected_state_version=expected,
                        actor="customer",
                        actor_identity=customer_id,
                        state_before=STATE_CUSTOMER_CONTINUING,
                        state_after=STATE_BROKER_REVIEW_READY,
                        idempotency_key=idempotency_key,
                        evidence={
                            "request_id": active.request_id,
                            "final_request_item_id": active.request_item_id,
                            "accepted_request_item_ids": [
                                item.request_item_id
                                for item in items
                                if item.status == ITEM_STATUS_SATISFIED
                            ],
                        },
                        timestamp=now,
                    )
                )
            final_version = sequence
            projection = _projection(
                case_id=case_id,
                state=next_state,
                aggregate_version=final_version,
                group=group,
                items=items,
                latest_events=[*snapshot.latest_events, *events],
                timestamp=now,
            )
            aggregate_out = Slice1Aggregate(
                case_id=case_id,
                workflow_state=next_state,
                aggregate_version=final_version,
                active_request_id=group.request_id if group.status == GROUP_STATUS_OPEN else None,
                customer_projection=projection,
                broker_projection=projection,
            )
            tx.update_items(items)
            tx.update_group(group)
            tx.insert_events(events)
            tx.upsert_aggregate(aggregate_out)
            tx.update_legacy_projection(case_id, _legacy_projection_patch(projection))
            return _response(
                outcome="accepted",
                command_id=command_id,
                correlation_id=corr,
                idempotency_key=idempotency_key,
                event_ids=[event["event_id"] for event in events],
                projection=projection,
            )

        result = self.store.accept(
            case_id=case_id,
            actor_identity=customer_id,
            command_id=command_id,
            idempotency_key=idempotency_key,
            command_type="customer_request_item_submit",
            handler=_handle,
        )
        _log_command_outcome(command_type="customer_request_item_submit", case_id=case_id, result=result)
        return result


class InMemorySlice1Store:
    """Test-only store with the same command-outcome semantics as the PG adapter."""

    def __init__(self, cases: dict[str, dict[str, Any]] | None = None):
        self.cases = cases if cases is not None else {}
        self.aggregates: dict[str, Slice1Aggregate] = {}
        self.groups: dict[str, Slice1Group] = {}
        self.items: dict[str, Slice1Item] = {}
        self.events: dict[str, list[dict[str, Any]]] = {}
        self.outcomes: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.command_outcomes: dict[tuple[str, str], dict[str, Any]] = {}

    def read_snapshot(self, case_id: str) -> Slice1Snapshot | None:
        case = self.cases.get(case_id)
        if case is None:
            return None
        aggregate = self.aggregates.get(case_id)
        group = None
        if aggregate and aggregate.active_request_id:
            group = self.groups.get(aggregate.active_request_id)
        if group is None:
            group = next(
                (g for g in self.groups.values() if g.case_id == case_id and g.status == GROUP_STATUS_OPEN),
                None,
            )
        items = [item for item in self.items.values() if item.case_id == case_id]
        return Slice1Snapshot(
            case=dict(case),
            aggregate=aggregate,
            group=group,
            items=sorted(items, key=lambda item: item.position),
            latest_events=list(self.events.get(case_id, [])),
        )

    def accept(
        self,
        *,
        case_id: str,
        actor_identity: str,
        command_id: str,
        idempotency_key: str,
        command_type: str,
        handler: Callable[[Slice1Tx, Slice1Snapshot], dict[str, Any]],
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
                self.aggregates,
                self.groups,
                self.items,
                self.events,
                self.outcomes,
                self.command_outcomes,
                self.cases,
            )
        )
        try:
            response = handler(self, snapshot)
            self.outcomes[(case_id, actor_identity, idempotency_key)] = dict(response)
            self.command_outcomes[(case_id, command_id)] = dict(response)
            return response
        except Exception:
            (
                self.aggregates,
                self.groups,
                self.items,
                self.events,
                self.outcomes,
                self.command_outcomes,
                self.cases,
            ) = before
            raise

    def insert_group(self, group: Slice1Group) -> None:
        self.groups[group.request_id] = group

    def insert_items(self, items: list[Slice1Item]) -> None:
        for item in items:
            self.items[item.request_item_id] = item

    def update_items(self, items: list[Slice1Item]) -> None:
        self.insert_items(items)

    def update_group(self, group: Slice1Group) -> None:
        self.groups[group.request_id] = group

    def insert_events(self, events: list[dict[str, Any]]) -> None:
        for event in events:
            self.events.setdefault(str(event["case_id"]), []).append(dict(event))

    def upsert_aggregate(self, aggregate: Slice1Aggregate) -> None:
        self.aggregates[aggregate.case_id] = aggregate

    def update_legacy_projection(self, case_id: str, patch: dict[str, Any]) -> None:
        self.cases.setdefault(case_id, {}).update(patch)
        self.cases[case_id]["updated_at"] = patch.get("server_timestamp") or _utc_now_iso()


def _default_store() -> Slice1Store:
    from services.fiqa_api.db.service_record_repository import make_slice1_postgres_store

    return make_slice1_postgres_store()


def default_slice1_service() -> P20Slice1CommandService:
    return P20Slice1CommandService()
