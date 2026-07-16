"""P20 Capability 2 — Broker New Case + Missing Information + Request Draft.

Administrative/pre-task capability. Does not create Slice 1 Request More groups
by itself. Capability 3A SendRequest promotes a saved draft into Request More
+ customer access.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol
from uuid import uuid4

from services.fiqa_api.inbox_triage.p20_missing_information import (
    CHECKLIST_FIELDS,
    FACT_STATUS_MISSING,
    apply_fact_status_update,
    derive_missing_information_checklist,
    merge_fact_records,
    seed_fact_records_from_case,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_BROKER_REVIEW,
    GUIDED_STATE_READY_FOR_BROKER_REVIEW,
    SERVICE_LANE_CLAIM,
)

logger = logging.getLogger(__name__)

CAPABILITY_VERSION = 1
FLAG_ENV = "P20_CASE_INTAKE_DRAFT"
ADMIN_LIFECYCLE_DRAFT = "draft"
ADMIN_LIFECYCLE_ACTIVE = "active"

EVENT_CASE_CREATED = "case_created"
EVENT_REQUEST_DRAFT_SAVED = "request_draft_saved"
EVENT_FACT_STATUS_UPDATED = "fact_status_updated"
EVENT_MISSING_INFORMATION_ASSESSED = "missing_information_assessed"

ALLOWED_DRAFT_ITEM_TYPES = frozenset(
    {meta["item_type"] for meta in CHECKLIST_FIELDS} | {"free_text", "vin", "policy_or_insurance_card", "photo_evidence"}
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def case_intake_feature_enabled() -> bool:
    # Default on for capability delivery; can be disabled explicitly.
    raw = (os.getenv(FLAG_ENV) or "1").strip().lower()
    return raw in ("1", "true", "yes", "on")


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


def _stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _semantic_draft_items(items: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Stable semantic payload for draft comparison (ignores draft_item_id churn)."""
    rows: list[dict[str, Any]] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "field_key": item.get("field_key"),
                "item_type": item.get("item_type"),
                "label": item.get("label"),
                "instructions": item.get("instructions"),
                "required": bool(item.get("required", True)),
                "position": int(item.get("position") or 0),
                "request_mode": item.get("request_mode") or "request_missing",
                "selected": bool(item.get("selected", True)),
            }
        )
    rows.sort(key=lambda row: (int(row.get("position") or 0), str(row.get("field_key") or "")))
    for index, row in enumerate(rows, start=1):
        row["position"] = index
    return rows


def _preserve_draft_item_ids(
    normalized_items: list[dict[str, Any]],
    prior_items: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Reuse prior draft_item_id when field_key matches to avoid identity churn."""
    prior_ids = {
        str(item.get("field_key") or ""): str(item.get("draft_item_id") or "")
        for item in (prior_items or [])
        if isinstance(item, dict) and item.get("field_key") and item.get("draft_item_id")
    }
    out: list[dict[str, Any]] = []
    for item in normalized_items:
        row = dict(item)
        field_key = str(row.get("field_key") or "")
        if field_key and prior_ids.get(field_key):
            row["draft_item_id"] = prior_ids[field_key]
        out.append(row)
    return out


@dataclass
class IntakeAggregate:
    case_id: str
    admin_lifecycle: str
    aggregate_version: int
    is_test: bool
    office_id: str | None
    tenant_id: str | None
    fact_records: dict[str, Any] = field(default_factory=dict)
    broker_projection: dict[str, Any] = field(default_factory=dict)
    customer_projection: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class RequestDraft:
    draft_id: str
    case_id: str
    draft_version: int
    items: list[dict[str, Any]]
    content_hash: str
    updated_by: str
    created_at: str
    updated_at: str
    status: str = "draft"


@dataclass
class IntakeSnapshot:
    case: dict[str, Any]
    aggregate: IntakeAggregate | None
    draft: RequestDraft | None
    latest_events: list[dict[str, Any]] = field(default_factory=list)
    stored_outcome: dict[str, Any] | None = None
    open_request_group: dict[str, Any] | None = None


class IntakeTx(Protocol):
    def insert_case(self, case: dict[str, Any]) -> None: ...
    def upsert_aggregate(self, aggregate: IntakeAggregate) -> None: ...
    def upsert_draft(self, draft: RequestDraft) -> None: ...
    def insert_events(self, events: list[dict[str, Any]]) -> None: ...
    def update_case_extra(self, case_id: str, patch: dict[str, Any]) -> None: ...


class IntakeStore(Protocol):
    def read_snapshot(self, case_id: str) -> IntakeSnapshot | None: ...
    def find_create_outcome(
        self, *, actor_identity: str, idempotency_key: str, command_id: str
    ) -> dict[str, Any] | None: ...
    def accept_create(
        self,
        *,
        actor_identity: str,
        command_id: str,
        idempotency_key: str,
        command_type: str,
        handler: Callable[["IntakeStore", None], dict[str, Any]],
    ) -> dict[str, Any]: ...
    def accept(
        self,
        *,
        case_id: str,
        actor_identity: str,
        command_id: str,
        idempotency_key: str,
        command_type: str,
        handler: Callable[[IntakeTx, IntakeSnapshot], dict[str, Any]],
    ) -> dict[str, Any]: ...


def _replay_response(stored: dict[str, Any]) -> dict[str, Any]:
    prior = dict(stored)
    prior["original_outcome"] = prior.get("outcome")
    prior["outcome"] = "replayed"
    return prior


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
    out: dict[str, Any] = {
        "outcome": outcome,
        "command_id": command_id,
        "correlation_id": correlation_id,
        "idempotency_key": idempotency_key,
        "event_ids": list(event_ids),
        "aggregate_version": projection.get("aggregate_version"),
        "case_id": projection.get("case_id"),
        "broker_projection": projection,
        "customer_projection": projection.get("customer_projection")
        or {
            "case_id": projection.get("case_id"),
            "customer_next_action": None,
            "message": "No customer task yet.",
        },
        "server_timestamp": projection.get("server_timestamp") or _utc_now_iso(),
    }
    if error_code:
        out["error_code"] = error_code
    if original_outcome:
        out["original_outcome"] = original_outcome
    return out


def _allowed_next_commands(
    *,
    admin_lifecycle: str,
    has_draft: bool,
    open_request: bool,
) -> list[str]:
    commands = ["SaveRequestDraft", "UpdateFactStatus"]
    if admin_lifecycle == ADMIN_LIFECYCLE_DRAFT and not open_request and has_draft:
        commands.append("SendRequest")
    if has_draft and not open_request:
        commands.append("EditRequestDraft")
    if open_request:
        commands.append("WaitForCustomer")
    return commands


def build_broker_projection(
    *,
    case: dict[str, Any],
    aggregate: IntakeAggregate,
    draft: RequestDraft | None,
    latest_events: list[dict[str, Any]] | None = None,
    open_request_group: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fact_records = merge_fact_records(aggregate.fact_records, case=case)
    checklist = derive_missing_information_checklist(fact_records, case=case)
    customer_projection = {
        "case_id": aggregate.case_id,
        "customer_next_action": None,
        "message": "No customer task yet.",
        "invite": None,
    }
    draft_proj = None
    if draft is not None:
        draft_proj = {
            "draft_id": draft.draft_id,
            "draft_version": draft.draft_version,
            "status": draft.status,
            "items": list(draft.items),
            "updated_at": draft.updated_at,
            "updated_by": draft.updated_by,
            "content_hash": draft.content_hash,
        }
    open_request = bool(open_request_group)
    return {
        "case_id": aggregate.case_id,
        "capability": "p20_case_intake",
        "capability_version": CAPABILITY_VERSION,
        "is_test": bool(aggregate.is_test or case.get("workbench_test")),
        "admin_lifecycle": aggregate.admin_lifecycle,
        "workflow_state": None,  # pre-task; canonical workflow not started
        "aggregate_version": aggregate.aggregate_version,
        "office_id": aggregate.office_id,
        "tenant_id": aggregate.tenant_id,
        "known_facts": {
            key: {
                "status": rec.get("status"),
                "value": rec.get("value"),
                "previous_value": rec.get("previous_value"),
                "reason": rec.get("reason"),
            }
            for key, rec in fact_records.items()
        },
        "missing_information_checklist": checklist,
        "request_draft": draft_proj,
        "open_request_more": open_request_group,
        "customer_next_action": None,
        "allowed_next_commands": _allowed_next_commands(
            admin_lifecycle=aggregate.admin_lifecycle,
            has_draft=draft is not None,
            open_request=open_request,
        ),
        "customer_projection": customer_projection,
        "timeline_summary": [
            {
                "event_type": str(e.get("event_type") or ""),
                "created_at": str(e.get("created_at") or ""),
                "actor": str(e.get("actor") or ""),
            }
            for e in (latest_events or [])[-10:]
        ],
        "server_timestamp": _utc_now_iso(),
        "auth_posture": "pilot_office_assertion",
    }


def _validate_draft_items(raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        raise ValueError("draft_items_required")
    out: list[dict[str, Any]] = []
    seen_fields: set[str] = set()
    seen_positions: set[int] = set()
    for idx, raw in enumerate(raw_items, start=1):
        item = raw if isinstance(raw, dict) else {}
        field_key = str(item.get("field_key") or "").strip()
        item_type = str(item.get("item_type") or "").strip().lower()
        if field_key:
            meta = next((m for m in CHECKLIST_FIELDS if m["field_key"] == field_key), None)
            if meta and not item_type:
                item_type = meta["item_type"]
        if item_type not in ALLOWED_DRAFT_ITEM_TYPES:
            raise ValueError("unsupported_draft_item_type")
        label = str(item.get("label") or item.get("customer_label") or "").strip()
        if not label:
            raise ValueError("draft_item_label_required")
        position = int(item.get("position") or idx)
        if position in seen_positions:
            raise ValueError("duplicate_draft_item_position")
        seen_positions.add(position)
        if field_key:
            if field_key in seen_fields:
                raise ValueError("duplicate_draft_field_key")
            seen_fields.add(field_key)
        mode = str(item.get("request_mode") or "request_missing").strip()
        out.append(
            {
                "draft_item_id": str(item.get("draft_item_id") or f"draft_item_{uuid4().hex[:12]}").strip(),
                "field_key": field_key or None,
                "item_type": item_type,
                "label": label[:160],
                "instructions": str(item.get("instructions") or "").strip()[:1000],
                "required": bool(item.get("required", True)),
                "position": position,
                "request_mode": mode[:64],
                "selected": bool(item.get("selected", True)),
            }
        )
    out.sort(key=lambda row: row["position"])
    expected = list(range(1, len(out) + 1))
    if [int(row["position"]) for row in out] != expected:
        raise ValueError("draft_item_positions_must_be_contiguous")
    # Persist only selected items in authoritative draft order.
    selected = [row for row in out if row.get("selected", True)]
    for i, row in enumerate(selected, start=1):
        row["position"] = i
    return selected


def _minimum_create_inputs(body: dict[str, Any]) -> dict[str, Any]:
    """Normalize optional broker-supplied seed fields. Case may be incomplete."""
    customer_name = str(body.get("customer_name") or "").strip()[:120]
    customer_phone = str(body.get("customer_phone") or "").strip()[:40]
    note = str(body.get("note") or body.get("contact_note") or "").strip()[:200]
    known_facts_in = body.get("known_facts") if isinstance(body.get("known_facts"), dict) else {}
    known_facts: dict[str, Any] = {}
    for key in (
        "vin",
        "vehicle_vin",
        "vehicle_year",
        "vehicle_make",
        "vehicle_model",
        "vehicle_information",
        "primary_vehicle_summary",
        "own_vehicle_info",
        "policy_number",
        "accident_description",
        "accident_datetime",
        "accident_date",
        "accident_location",
        "injury_status",
        "anyone_injured",
        "police_involved",
        "other_party_info",
        "other_party_plate",
    ):
        val = str(known_facts_in.get(key) or body.get(key) or "").strip()
        if val:
            known_facts[key] = val
    # Normalize injury alias for checklist seeding.
    if known_facts.get("anyone_injured") and not known_facts.get("injury_status"):
        known_facts["injury_status"] = known_facts["anyone_injured"]
    if known_facts.get("accident_date") and not known_facts.get("accident_datetime"):
        known_facts["accident_datetime"] = known_facts["accident_date"]
    return {
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "contact_note": note,
        "known_facts": known_facts,
        "is_test": bool(body.get("is_test") or body.get("workbench_test")),
        "title": str(body.get("title") or "").strip()[:160],
    }


_ALLOWED_CREATE_ACTORS = frozenset({"broker", "customer"})


def _normalize_create_actor(actor: str | None) -> str:
    value = str(actor or "broker").strip().lower() or "broker"
    if value not in _ALLOWED_CREATE_ACTORS:
        raise ValueError("create_actor_invalid")
    return value


def _build_new_case_record(
    *,
    case_id: str,
    broker_id: str,
    office_id: str | None,
    tenant_id: str | None,
    inputs: dict[str, Any],
    timestamp: str,
    actor: str = "broker",
) -> dict[str, Any]:
    is_test = bool(inputs.get("is_test"))
    title = inputs.get("title") or ("QA Claim intake" if is_test else "Claim intake")
    known_facts = dict(inputs.get("known_facts") or {})
    # Keep still_needed deterministic from seed gaps for legacy display only.
    checklist = derive_missing_information_checklist(seed_fact_records_from_case({"known_facts": known_facts}))
    still_needed = [i["field_key"] for i in checklist if i["status"] == FACT_STATUS_MISSING]
    tags = ["Claim"]
    if is_test:
        tags = ["TEST", "QA", "Claim"]
    if actor == "customer":
        source_text = f"[Customer] Mini Program Start Claim by {broker_id}"
        activity_message = "Customer started Claim case (Capability 2)."
    else:
        source_text = f"[Broker] New Claim created by {broker_id}"
        activity_message = "Broker created Claim case (Capability 2)."
    return {
        "case_id": case_id,
        "case_status": "new",
        "created_at": timestamp,
        "updated_at": timestamp,
        "formal_submitted_at": "",
        "source_text": source_text,
        "case_messages": [],
        "waiting_on": "none",
        "next_contact_by": "",
        "customer_name": inputs.get("customer_name") or ("QA Customer" if is_test else ""),
        "customer_phone": inputs.get("customer_phone") or "",
        "customer_email": "",
        "policy_number": str(known_facts.get("policy_number") or ""),
        "contact_note": inputs.get("contact_note") or "",
        "case_notes": [],
        "case_activity": [
            {
                "activity_id": f"act_{uuid4().hex[:10]}",
                "activity_type": "case_created",
                "message": activity_message,
                "created_at": timestamp,
            }
        ],
        "case_attachments": [],
        "issue_category": "claim_intake",
        "urgency": "normal",
        "manual_followup_needed": True,
        "broker_next_step": "Review the accident first, then Request More only if needed.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "collected_fields": [],
        "still_needed_fields": still_needed,
        "known_facts": known_facts,
        "claim_phase": CLAIM_PHASE_BROKER_REVIEW,
        "guided_workflow_state": GUIDED_STATE_READY_FOR_BROKER_REVIEW,
        "workbench_tags": tags,
        "workbench_test": is_test,
        "lifecycle_status": "collecting",
        "service_lane": SERVICE_LANE_CLAIM,
        "triage_mode": "greenfield",
        "office_case_title": title,
        "office_broker_next_step": "Review accident facts, then decide Request More",
        "p20_case_intake_capability_version": CAPABILITY_VERSION,
        "case_intake_capability_version": CAPABILITY_VERSION,
        "admin_lifecycle": ADMIN_LIFECYCLE_DRAFT,
        "asserted_org_id": office_id or "",
        "client_id": tenant_id or "",
        "created_by_broker": broker_id,
        "created_by_actor": actor,
        "exclude_from_production_metrics": is_test,
    }


class P20CaseIntakeCommandService:
    def __init__(self, store: IntakeStore | None = None):
        self.store = store or _default_store()

    def fetch_projection(self, case_id: str) -> dict[str, Any] | None:
        snapshot = self.store.read_snapshot(case_id)
        if snapshot is None or snapshot.aggregate is None:
            return None
        return build_broker_projection(
            case=snapshot.case,
            aggregate=snapshot.aggregate,
            draft=snapshot.draft,
            latest_events=snapshot.latest_events,
            open_request_group=snapshot.open_request_group,
        )

    def create_claim(
        self,
        *,
        broker_id: str,
        office_id: str | None,
        tenant_id: str | None,
        command_id: str,
        idempotency_key: str,
        correlation_id: str | None = None,
        inputs: dict[str, Any] | None = None,
        actor: str = "broker",
    ) -> dict[str, Any]:
        if not case_intake_feature_enabled():
            raise RuntimeError("p20_case_intake_disabled")
        command_id = _normalize_command_id(command_id, "command_id")
        idempotency_key = _normalize_command_id(idempotency_key, "idempotency_key")
        broker_id = _normalize_command_id(broker_id, "broker_id")
        create_actor = _normalize_create_actor(actor)
        corr = (correlation_id or command_id).strip()[:128] or command_id
        normalized = _minimum_create_inputs(inputs or {})
        office = (office_id or "").strip()[:256] or None
        tenant = (tenant_id or "").strip()[:256] or None

        prior = self.store.find_create_outcome(
            actor_identity=broker_id,
            idempotency_key=idempotency_key,
            command_id=command_id,
        )
        if prior:
            return _replay_response(prior)

        def _handle(tx: IntakeStore, _unused: None) -> dict[str, Any]:
            # Re-check inside transaction/store accept_create.
            existing = tx.find_create_outcome(
                actor_identity=broker_id,
                idempotency_key=idempotency_key,
                command_id=command_id,
            )
            if existing:
                return _replay_response(existing)

            timestamp = _utc_now_iso()
            case_id = f"case_{uuid4().hex[:12]}"
            case = _build_new_case_record(
                case_id=case_id,
                broker_id=broker_id,
                office_id=office,
                tenant_id=tenant,
                inputs=normalized,
                timestamp=timestamp,
                actor=create_actor,
            )
            fact_records = seed_fact_records_from_case(case)
            aggregate = IntakeAggregate(
                case_id=case_id,
                admin_lifecycle=ADMIN_LIFECYCLE_DRAFT,
                aggregate_version=2,
                is_test=bool(normalized.get("is_test")),
                office_id=office,
                tenant_id=tenant,
                fact_records=fact_records,
                created_at=timestamp,
                updated_at=timestamp,
            )
            projection = build_broker_projection(
                case=case,
                aggregate=aggregate,
                draft=None,
                latest_events=[],
                open_request_group=None,
            )
            event = {
                "event_id": f"evt_{uuid4().hex[:16]}",
                "case_id": case_id,
                "event_type": EVENT_CASE_CREATED,
                "command_id": command_id,
                "correlation_id": corr,
                "sequence_number": 1,
                "aggregate_version": 1,
                "expected_state_version": 0,
                "actor": create_actor,
                "actor_identity": broker_id,
                "state_before": "",
                "state_after": ADMIN_LIFECYCLE_DRAFT,
                "visibility": "broker",
                "evidence": {
                    "is_test": bool(normalized.get("is_test")),
                    "office_id": office,
                    "tenant_id": tenant,
                    "seed_fields": sorted(list((normalized.get("known_facts") or {}).keys())),
                    "channel": "mini_program" if create_actor == "customer" else "workbench",
                },
                "idempotency_key": idempotency_key,
                "created_at": timestamp,
            }
            assessed = {
                **event,
                "event_id": f"evt_{uuid4().hex[:16]}",
                "event_type": EVENT_MISSING_INFORMATION_ASSESSED,
                "sequence_number": 2,
                "aggregate_version": 2,
                "evidence": {
                    "checklist_count": len(projection["missing_information_checklist"]),
                    "missing_count": sum(
                        1
                        for row in projection["missing_information_checklist"]
                        if row["status"] == FACT_STATUS_MISSING
                    ),
                },
            }
            aggregate.broker_projection = projection
            aggregate.customer_projection = projection["customer_projection"]
            tx.insert_case(case)
            tx.upsert_aggregate(aggregate)
            tx.insert_events([event, assessed])
            return _response(
                outcome="accepted",
                command_id=command_id,
                correlation_id=corr,
                idempotency_key=idempotency_key,
                event_ids=[event["event_id"], assessed["event_id"]],
                projection=projection,
            )

        result = self.store.accept_create(
            actor_identity=broker_id,
            command_id=command_id,
            idempotency_key=idempotency_key,
            command_type="CreateClaim",
            handler=_handle,
        )
        logger.info(
            "p20_case_intake_create_claim",
            extra={
                "outcome": result.get("outcome"),
                "case_id": result.get("case_id"),
                "aggregate_version": result.get("aggregate_version"),
            },
        )
        return result

    def save_request_draft(
        self,
        *,
        case_id: str,
        broker_id: str,
        command_id: str,
        idempotency_key: str,
        expected_case_version: int | None,
        items: list[dict[str, Any]],
        correlation_id: str | None = None,
        draft_id: str | None = None,
    ) -> dict[str, Any]:
        command_id = _normalize_command_id(command_id, "command_id")
        idempotency_key = _normalize_command_id(idempotency_key, "idempotency_key")
        broker_id = _normalize_command_id(broker_id, "broker_id")
        expected = _validate_expected_version(expected_case_version)
        normalized_items = _validate_draft_items(items)
        corr = (correlation_id or command_id).strip()[:128] or command_id

        def _handle(tx: IntakeTx, snapshot: IntakeSnapshot) -> dict[str, Any]:
            if isinstance(getattr(snapshot, "stored_outcome", None), dict):
                return _replay_response(snapshot.stored_outcome)
            if snapshot.aggregate is None:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection={
                        "case_id": case_id,
                        "aggregate_version": 0,
                        "customer_projection": {"customer_next_action": None},
                    },
                    error_code="intake_aggregate_missing",
                )
            aggregate = snapshot.aggregate
            current_projection = build_broker_projection(
                case=snapshot.case,
                aggregate=aggregate,
                draft=snapshot.draft,
                latest_events=snapshot.latest_events,
                open_request_group=snapshot.open_request_group,
            )
            if expected != aggregate.aggregate_version:
                return _response(
                    outcome="conflict",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code="version_conflict",
                )
            if snapshot.open_request_group:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code="active_request_more_exists",
                )

            timestamp = _utc_now_iso()
            prior = snapshot.draft
            stable_items = _preserve_draft_item_ids(
                normalized_items,
                prior.items if prior is not None else None,
            )
            content_hash = _stable_hash(_semantic_draft_items(stable_items))
            unchanged = prior is not None and (
                prior.content_hash == content_hash
                or _semantic_draft_items(prior.items) == _semantic_draft_items(stable_items)
            )
            next_version = aggregate.aggregate_version
            event_ids: list[str] = []
            if unchanged and prior is not None:
                draft = prior
            else:
                next_version = aggregate.aggregate_version + 1
                draft = RequestDraft(
                    draft_id=(draft_id or (prior.draft_id if prior else None) or f"draft_{uuid4().hex[:12]}"),
                    case_id=case_id,
                    draft_version=(prior.draft_version + 1) if prior else 1,
                    items=stable_items,
                    content_hash=content_hash,
                    updated_by=broker_id,
                    created_at=(prior.created_at if prior else timestamp),
                    updated_at=timestamp,
                    status="draft",
                )
                event = {
                    "event_id": f"evt_{uuid4().hex[:16]}",
                    "case_id": case_id,
                    "event_type": EVENT_REQUEST_DRAFT_SAVED,
                    "command_id": command_id,
                    "correlation_id": corr,
                    "sequence_number": next_version,
                    "aggregate_version": next_version,
                    "expected_state_version": expected,
                    "actor": "broker",
                    "actor_identity": broker_id,
                    "state_before": aggregate.admin_lifecycle,
                    "state_after": aggregate.admin_lifecycle,
                    "visibility": "broker",
                    "evidence": {
                        "draft_id": draft.draft_id,
                        "draft_version": draft.draft_version,
                        "item_count": len(draft.items),
                        "content_hash": content_hash,
                        "field_keys": [i.get("field_key") for i in draft.items],
                    },
                    "idempotency_key": idempotency_key,
                    "created_at": timestamp,
                }
                tx.upsert_draft(draft)
                tx.insert_events([event])
                event_ids = [event["event_id"]]
                aggregate.aggregate_version = next_version
                aggregate.updated_at = timestamp

            projection = build_broker_projection(
                case=snapshot.case,
                aggregate=aggregate,
                draft=draft,
                latest_events=(snapshot.latest_events or [])
                + (
                    [
                        {
                            "event_type": EVENT_REQUEST_DRAFT_SAVED,
                            "created_at": timestamp,
                            "actor": "broker",
                        }
                    ]
                    if event_ids
                    else []
                ),
                open_request_group=None,
            )
            aggregate.broker_projection = projection
            aggregate.customer_projection = projection["customer_projection"]
            tx.upsert_aggregate(aggregate)
            tx.update_case_extra(
                case_id,
                {
                    "p20_case_intake_capability_version": CAPABILITY_VERSION,
                    "admin_lifecycle": aggregate.admin_lifecycle,
                    "updated_at": timestamp,
                },
            )
            return _response(
                outcome="accepted",
                command_id=command_id,
                correlation_id=corr,
                idempotency_key=idempotency_key,
                event_ids=event_ids,
                projection=projection,
            )

        return self.store.accept(
            case_id=case_id,
            actor_identity=broker_id,
            command_id=command_id,
            idempotency_key=idempotency_key,
            command_type="SaveRequestDraft",
            handler=_handle,
        )

    def update_fact_status(
        self,
        *,
        case_id: str,
        broker_id: str,
        command_id: str,
        idempotency_key: str,
        expected_case_version: int | None,
        field_key: str,
        status: str,
        reason: str = "",
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        command_id = _normalize_command_id(command_id, "command_id")
        idempotency_key = _normalize_command_id(idempotency_key, "idempotency_key")
        broker_id = _normalize_command_id(broker_id, "broker_id")
        expected = _validate_expected_version(expected_case_version)
        corr = (correlation_id or command_id).strip()[:128] or command_id

        def _handle(tx: IntakeTx, snapshot: IntakeSnapshot) -> dict[str, Any]:
            if isinstance(getattr(snapshot, "stored_outcome", None), dict):
                return _replay_response(snapshot.stored_outcome)
            if snapshot.aggregate is None:
                raise ValueError("intake_aggregate_missing")
            aggregate = snapshot.aggregate
            current_projection = build_broker_projection(
                case=snapshot.case,
                aggregate=aggregate,
                draft=snapshot.draft,
                latest_events=snapshot.latest_events,
                open_request_group=snapshot.open_request_group,
            )
            if expected != aggregate.aggregate_version:
                return _response(
                    outcome="conflict",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code="version_conflict",
                )
            try:
                updated_facts = apply_fact_status_update(
                    aggregate.fact_records,
                    field_key=field_key,
                    status=status,
                    reason=reason,
                    preserve_previous=True,
                )
            except ValueError as exc:
                return _response(
                    outcome="rejected",
                    command_id=command_id,
                    correlation_id=corr,
                    idempotency_key=idempotency_key,
                    event_ids=[],
                    projection=current_projection,
                    error_code=str(exc),
                )
            timestamp = _utc_now_iso()
            next_version = aggregate.aggregate_version + 1
            previous = (aggregate.fact_records or {}).get(field_key) if isinstance(aggregate.fact_records, dict) else {}
            event = {
                "event_id": f"evt_{uuid4().hex[:16]}",
                "case_id": case_id,
                "event_type": EVENT_FACT_STATUS_UPDATED,
                "command_id": command_id,
                "correlation_id": corr,
                "sequence_number": next_version,
                "aggregate_version": next_version,
                "expected_state_version": expected,
                "actor": "broker",
                "actor_identity": broker_id,
                "state_before": aggregate.admin_lifecycle,
                "state_after": aggregate.admin_lifecycle,
                "visibility": "broker",
                "evidence": {
                    "field_key": field_key,
                    "status_before": (previous or {}).get("status"),
                    "status_after": status,
                    "previous_value": (previous or {}).get("value"),
                    "reason": reason,
                },
                "idempotency_key": idempotency_key,
                "created_at": timestamp,
            }
            aggregate.fact_records = updated_facts
            aggregate.aggregate_version = next_version
            aggregate.updated_at = timestamp
            projection = build_broker_projection(
                case=snapshot.case,
                aggregate=aggregate,
                draft=snapshot.draft,
                latest_events=(snapshot.latest_events or [])
                + [{"event_type": EVENT_FACT_STATUS_UPDATED, "created_at": timestamp, "actor": "broker"}],
                open_request_group=snapshot.open_request_group,
            )
            aggregate.broker_projection = projection
            aggregate.customer_projection = projection["customer_projection"]
            tx.upsert_aggregate(aggregate)
            tx.insert_events([event])
            return _response(
                outcome="accepted",
                command_id=command_id,
                correlation_id=corr,
                idempotency_key=idempotency_key,
                event_ids=[event["event_id"]],
                projection=projection,
            )

        return self.store.accept(
            case_id=case_id,
            actor_identity=broker_id,
            command_id=command_id,
            idempotency_key=idempotency_key,
            command_type="UpdateFactStatus",
            handler=_handle,
        )


class InMemoryIntakeStore:
    """Test store with transactional rollback semantics for Capability 2."""

    def __init__(self, cases: dict[str, dict[str, Any]] | None = None):
        self.cases: dict[str, dict[str, Any]] = cases if cases is not None else {}
        self.aggregates: dict[str, IntakeAggregate] = {}
        self.drafts: dict[str, RequestDraft] = {}
        self.events: dict[str, list[dict[str, Any]]] = {}
        self.outcomes: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.command_outcomes: dict[tuple[str, str], dict[str, Any]] = {}
        self.create_outcomes: dict[tuple[str, str], dict[str, Any]] = {}
        self.create_by_command: dict[str, dict[str, Any]] = {}
        self.open_requests: dict[str, dict[str, Any]] = {}
        self.fail_next_write = False

    def read_snapshot(self, case_id: str) -> IntakeSnapshot | None:
        case = self.cases.get(case_id)
        if case is None:
            return None
        return IntakeSnapshot(
            case=dict(case),
            aggregate=self.aggregates.get(case_id),
            draft=self.drafts.get(case_id),
            latest_events=list(self.events.get(case_id, [])),
            open_request_group=self.open_requests.get(case_id),
        )

    def find_create_outcome(
        self, *, actor_identity: str, idempotency_key: str, command_id: str
    ) -> dict[str, Any] | None:
        return self.create_outcomes.get((actor_identity, idempotency_key)) or self.create_by_command.get(command_id)

    def insert_case(self, case: dict[str, Any]) -> None:
        if self.fail_next_write:
            self.fail_next_write = False
            raise RuntimeError("forced_write_failure")
        self.cases[str(case["case_id"])] = dict(case)

    def upsert_aggregate(self, aggregate: IntakeAggregate) -> None:
        self.aggregates[aggregate.case_id] = deepcopy(aggregate)

    def upsert_draft(self, draft: RequestDraft) -> None:
        self.drafts[draft.case_id] = deepcopy(draft)

    def insert_events(self, events: list[dict[str, Any]]) -> None:
        for event in events:
            self.events.setdefault(str(event["case_id"]), []).append(dict(event))

    def update_case_extra(self, case_id: str, patch: dict[str, Any]) -> None:
        self.cases.setdefault(case_id, {}).update(patch)

    def accept_create(
        self,
        *,
        actor_identity: str,
        command_id: str,
        idempotency_key: str,
        command_type: str,
        handler: Callable[["InMemoryIntakeStore", None], dict[str, Any]],
    ) -> dict[str, Any]:
        prior = self.find_create_outcome(
            actor_identity=actor_identity,
            idempotency_key=idempotency_key,
            command_id=command_id,
        )
        if prior:
            return _replay_response(prior)
        before = deepcopy(
            (
                self.cases,
                self.aggregates,
                self.drafts,
                self.events,
                self.outcomes,
                self.command_outcomes,
                self.create_outcomes,
                self.create_by_command,
            )
        )
        try:
            response = handler(self, None)
            self.create_outcomes[(actor_identity, idempotency_key)] = dict(response)
            self.create_by_command[command_id] = dict(response)
            case_id = str(response.get("case_id") or "")
            if case_id:
                self.outcomes[(case_id, actor_identity, idempotency_key)] = dict(response)
                self.command_outcomes[(case_id, command_id)] = dict(response)
            return response
        except Exception:
            (
                self.cases,
                self.aggregates,
                self.drafts,
                self.events,
                self.outcomes,
                self.command_outcomes,
                self.create_outcomes,
                self.create_by_command,
            ) = before
            raise

    def accept(
        self,
        *,
        case_id: str,
        actor_identity: str,
        command_id: str,
        idempotency_key: str,
        command_type: str,
        handler: Callable[[IntakeTx, IntakeSnapshot], dict[str, Any]],
    ) -> dict[str, Any]:
        prior = self.outcomes.get((case_id, actor_identity, idempotency_key)) or self.command_outcomes.get(
            (case_id, command_id)
        )
        snapshot = self.read_snapshot(case_id)
        if snapshot is None:
            raise ValueError("case_not_found")
        if prior:
            snapshot.stored_outcome = prior
            return handler(self, snapshot)
        before = deepcopy(
            (
                self.cases,
                self.aggregates,
                self.drafts,
                self.events,
                self.outcomes,
                self.command_outcomes,
            )
        )
        try:
            response = handler(self, snapshot)
            self.outcomes[(case_id, actor_identity, idempotency_key)] = dict(response)
            self.command_outcomes[(case_id, command_id)] = dict(response)
            return response
        except Exception:
            (
                self.cases,
                self.aggregates,
                self.drafts,
                self.events,
                self.outcomes,
                self.command_outcomes,
            ) = before
            raise


def _default_store() -> IntakeStore:
    from services.fiqa_api.db.service_record_repository import make_case_intake_postgres_store

    return make_case_intake_postgres_store()


def default_case_intake_service() -> P20CaseIntakeCommandService:
    return P20CaseIntakeCommandService()
