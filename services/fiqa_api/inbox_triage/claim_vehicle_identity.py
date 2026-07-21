"""Claim Vehicle Identity V1 — claim-scoped vehicle slot (backend object).

SSOT: docs/product/CLAIM_VEHICLE_IDENTITY_V1.md (D-010)

This is Claim Vehicle workflow storage — not Policy Add Car
(SERVICE_LANE_ADD_CAR) and not intake_entities dual-write.

Authority remains known_facts + fact_records + Slice1 command outcomes/events.
"""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Final
from uuid import uuid4

from services.fiqa_api.inbox_triage.p20_missing_information import (
    FACT_STATUS_CONFIRMED,
    FACT_STATUS_NEEDS_CORRECTION,
    FACT_STATUS_SUPPLIED_UNCONFIRMED,
    apply_fact_status_update,
    merge_fact_records,
)
from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
    normalize_vin_value,
    validate_vin_value,
)

# ---------------------------------------------------------------------------
# Canonical object + fact-key mapping (alias table)
# ---------------------------------------------------------------------------

VEHICLE_ID_PREFIX: Final = "veh:"

SOURCE_CUSTOMER: Final = "customer"
SOURCE_BROKER_REQUEST: Final = "broker_request"
SOURCE_AI_EXTRACT: Final = "ai_extract"
SOURCE_DOCUMENT: Final = "document"

ALLOWED_SOURCES: Final = frozenset(
    {
        SOURCE_CUSTOMER,
        SOURCE_BROKER_REQUEST,
        SOURCE_AI_EXTRACT,
        SOURCE_DOCUMENT,
    }
)

VERIFICATION_SUPPLIED_UNCONFIRMED: Final = FACT_STATUS_SUPPLIED_UNCONFIRMED
VERIFICATION_CONFIRMED: Final = FACT_STATUS_CONFIRMED
VERIFICATION_NEEDS_CORRECTION: Final = FACT_STATUS_NEEDS_CORRECTION

ALLOWED_VERIFICATION_STATUSES: Final = frozenset(
    {
        VERIFICATION_SUPPLIED_UNCONFIRMED,
        VERIFICATION_CONFIRMED,
        VERIFICATION_NEEDS_CORRECTION,
    }
)

# Logical field → canonical known_facts key
FACT_KEY_YEAR: Final = "vehicle_year"
FACT_KEY_MAKE: Final = "vehicle_make"
FACT_KEY_MODEL: Final = "vehicle_model"
FACT_KEY_VIN: Final = "vehicle_vin"
FACT_KEY_VIN_UNAVAILABLE: Final = "vehicle_vin_unavailable"
FACT_KEY_LICENSE_PLATE: Final = "vehicle_license_plate"
FACT_KEY_PLATE_STATE: Final = "vehicle_plate_state"
FACT_KEY_VERIFICATION: Final = "vehicle_verification_status"
FACT_KEY_SUMMARY: Final = "vehicle_information"
FACT_KEY_SOURCE: Final = "vehicle_identity_source"
FACT_KEY_VEHICLE_ID: Final = "claim_vehicle_id"
FACT_KEY_CREATED_AT: Final = "claim_vehicle_created_at"
FACT_KEY_UPDATED_AT: Final = "claim_vehicle_updated_at"

# Backward-compatible aliases (same logical vehicle — not a second car)
VIN_WRITE_ALIASES: Final = ("vin", "own_vehicle_vin")
SUMMARY_WRITE_ALIASES: Final = ("own_vehicle_info", "primary_vehicle_summary")
VIN_READ_ALIASES: Final = ("vehicle_vin", "vin", "own_vehicle_vin")
SUMMARY_READ_ALIASES: Final = (
    "vehicle_information",
    "own_vehicle_info",
    "primary_vehicle_summary",
)

_YEAR_RE = re.compile(r"^(19|20)\d{2}$")
_PLATE_STATE_RE = re.compile(r"^[A-Z]{2}$")

# known_facts provenance sources accepted by case_store.patch_case_known_facts
_PROVENANCE_BY_IDENTITY_SOURCE: Final = {
    SOURCE_CUSTOMER: "customer_task",
    SOURCE_BROKER_REQUEST: "system_default",
    SOURCE_AI_EXTRACT: "ai_suggestion",
    SOURCE_DOCUMENT: "ai_suggestion",
}

_SOFT_SOURCES: Final = frozenset({SOURCE_AI_EXTRACT, SOURCE_DOCUMENT})

_IDENTITY_SCALAR_FIELDS: Final = (
    "year",
    "make",
    "model",
    "vin",
    "license_plate",
    "plate_state",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def vehicle_id_for_case(case_id: str) -> str:
    cid = str(case_id or "").strip()
    if not cid:
        raise ValueError("case_id_required")
    return f"{VEHICLE_ID_PREFIX}{cid}"


def _trim_or_none(raw: Any) -> str | None:
    text = str(raw or "").strip()
    return text or None


def _normalize_year(raw: Any) -> str | None:
    text = _trim_or_none(raw)
    if not text:
        return None
    if _YEAR_RE.fullmatch(text):
        return text
    digits = re.sub(r"\D", "", text)
    if _YEAR_RE.fullmatch(digits):
        return digits
    return None


def _normalize_make_model(raw: Any) -> str | None:
    return _trim_or_none(raw)


def _normalize_plate(raw: Any) -> str | None:
    text = _trim_or_none(raw)
    if not text:
        return None
    return re.sub(r"\s+", "", text).upper()


def _normalize_plate_state(raw: Any) -> str | None:
    text = _trim_or_none(raw)
    if not text:
        return None
    upper = text.upper()
    if _PLATE_STATE_RE.fullmatch(upper):
        return upper
    return upper[:2] if len(upper) >= 2 and _PLATE_STATE_RE.fullmatch(upper[:2]) else None


def _parse_bool(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    text = str(raw or "").strip().lower()
    return text in {"1", "true", "yes", "on", "y"}


def _serialize_bool(value: bool) -> str:
    return "true" if value else "false"


def _normalize_source(raw: Any, *, default: str = SOURCE_CUSTOMER) -> str:
    text = str(raw or "").strip().lower()
    if text in ALLOWED_SOURCES:
        return text
    return default


def _normalize_verification(raw: Any, *, default: str = VERIFICATION_SUPPLIED_UNCONFIRMED) -> str:
    text = str(raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    if text == "supplied_but_unconfirmed":
        text = VERIFICATION_SUPPLIED_UNCONFIRMED
    if text == "disputed":
        text = VERIFICATION_NEEDS_CORRECTION
    if text in ALLOWED_VERIFICATION_STATUSES:
        return text
    return default


@dataclass
class ClaimVehicleIdentity:
    """Canonical Claim Vehicle Identity V1 object (one slot per claim)."""

    vehicle_id: str
    case_id: str
    year: str | None = None
    make: str | None = None
    model: str | None = None
    vin: str | None = None
    vin_unavailable: bool = False
    license_plate: str | None = None
    plate_state: str | None = None
    source: str = SOURCE_CUSTOMER
    verification_status: str = VERIFICATION_SUPPLIED_UNCONFIRMED
    summary: str | None = None
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ClaimVehicleMergeResult:
    vehicle: ClaimVehicleIdentity
    created: bool
    changed_fields: list[str] = field(default_factory=list)
    conflict_fields: list[str] = field(default_factory=list)
    matched_by: str = "create"


@dataclass
class ClaimVehicleCommandResult:
    outcome: str
    command_id: str
    idempotency_key: str
    correlation_id: str
    event_ids: list[str]
    vehicle: dict[str, Any] | None
    known_facts_patch: dict[str, str]
    fact_records: dict[str, Any]
    events: list[dict[str, Any]]
    complete: bool
    error_code: str | None = None
    original_outcome: str | None = None
    merge: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "command_id": self.command_id,
            "idempotency_key": self.idempotency_key,
            "correlation_id": self.correlation_id,
            "event_ids": list(self.event_ids),
            "vehicle": dict(self.vehicle) if isinstance(self.vehicle, dict) else self.vehicle,
            "known_facts_patch": dict(self.known_facts_patch),
            "fact_records": deepcopy(self.fact_records),
            "events": [dict(e) for e in self.events],
            "complete": self.complete,
            "error_code": self.error_code,
            "original_outcome": self.original_outcome,
            "merge": dict(self.merge) if isinstance(self.merge, dict) else self.merge,
        }


def build_vehicle_summary(vehicle: ClaimVehicleIdentity | dict[str, Any]) -> str | None:
    data = vehicle.as_dict() if isinstance(vehicle, ClaimVehicleIdentity) else dict(vehicle or {})
    year = _trim_or_none(data.get("year"))
    make = _trim_or_none(data.get("make"))
    model = _trim_or_none(data.get("model"))
    parts = [p for p in (year, make, model) if p]
    if parts:
        return " ".join(parts)
    vin = _trim_or_none(data.get("vin"))
    if vin and len(vin) == 17:
        return f"VIN …{vin[-6:]}"
    plate = _trim_or_none(data.get("license_plate"))
    state = _trim_or_none(data.get("plate_state"))
    if plate and state:
        return f"{state} {plate}"
    if plate:
        return plate
    return None


def is_claim_vehicle_complete(vehicle: ClaimVehicleIdentity | dict[str, Any]) -> bool:
    """Completeness A (valid VIN) or B (vin_unavailable + year/make/model)."""
    data = vehicle.as_dict() if isinstance(vehicle, ClaimVehicleIdentity) else dict(vehicle or {})
    vin = validate_vin_value(data.get("vin"))
    if vin:
        return True
    if not _parse_bool(data.get("vin_unavailable")):
        return False
    return bool(
        _trim_or_none(data.get("year"))
        and _trim_or_none(data.get("make"))
        and _trim_or_none(data.get("model"))
    )


def normalize_claim_vehicle_input(
    payload: dict[str, Any] | None,
    *,
    case_id: str,
    source: str = SOURCE_CUSTOMER,
    verification_status: str | None = None,
    now: str | None = None,
) -> ClaimVehicleIdentity:
    """Normalize a partial or complete Claim Vehicle payload (draft-safe).

    Partial VIN is never persisted as canonical ``vin``.
    """
    raw = payload if isinstance(payload, dict) else {}
    cid = str(case_id or "").strip()
    if not cid:
        raise ValueError("case_id_required")

    vin_raw = raw.get("vin")
    if vin_raw is None:
        vin_raw = raw.get("vehicle_vin")
    if vin_raw is None:
        vin_raw = raw.get("own_vehicle_vin")
    # Accept only fully valid VIN; partial → None (never store as canonical).
    vin = validate_vin_value(vin_raw)

    vin_unavailable = _parse_bool(raw.get("vin_unavailable") if "vin_unavailable" in raw else raw.get("vehicle_vin_unavailable"))
    if vin:
        vin_unavailable = False

    year = _normalize_year(raw.get("year") if "year" in raw else raw.get("vehicle_year"))
    make = _normalize_make_model(raw.get("make") if "make" in raw else raw.get("vehicle_make"))
    model = _normalize_make_model(raw.get("model") if "model" in raw else raw.get("vehicle_model"))
    license_plate = _normalize_plate(
        raw.get("license_plate") if "license_plate" in raw else raw.get("vehicle_license_plate")
    )
    plate_state = _normalize_plate_state(
        raw.get("plate_state") if "plate_state" in raw else raw.get("vehicle_plate_state")
    )

    ts = now or _utc_now_iso()
    explicit_vid = _trim_or_none(raw.get("vehicle_id") or raw.get("claim_vehicle_id"))
    vehicle_id = explicit_vid if explicit_vid and explicit_vid.startswith(VEHICLE_ID_PREFIX) else vehicle_id_for_case(cid)

    identity = ClaimVehicleIdentity(
        vehicle_id=vehicle_id,
        case_id=cid,
        year=year,
        make=make,
        model=model,
        vin=vin,
        vin_unavailable=vin_unavailable,
        license_plate=license_plate,
        plate_state=plate_state,
        source=_normalize_source(raw.get("source") or source),
        verification_status=_normalize_verification(
            verification_status if verification_status is not None else raw.get("verification_status") or raw.get("vehicle_verification_status")
        ),
        summary=None,
        created_at=_trim_or_none(raw.get("created_at") or raw.get("claim_vehicle_created_at")) or ts,
        updated_at=ts,
    )
    identity.summary = build_vehicle_summary(identity)
    return identity


def _first_fact(facts: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = _trim_or_none(facts.get(key))
        if value:
            return value
    return None


def read_claim_vehicle_from_facts(
    known_facts: dict[str, Any] | None,
    *,
    case_id: str,
) -> ClaimVehicleIdentity | None:
    """Hydrate the single claim vehicle slot from known_facts (resume / read path)."""
    facts = known_facts if isinstance(known_facts, dict) else {}
    cid = str(case_id or "").strip()
    if not cid:
        raise ValueError("case_id_required")

    has_signal = any(
        _trim_or_none(facts.get(k))
        for k in (
            FACT_KEY_VIN,
            FACT_KEY_YEAR,
            FACT_KEY_MAKE,
            FACT_KEY_MODEL,
            FACT_KEY_LICENSE_PLATE,
            FACT_KEY_VIN_UNAVAILABLE,
            FACT_KEY_SUMMARY,
            FACT_KEY_VEHICLE_ID,
            *VIN_READ_ALIASES,
            *SUMMARY_READ_ALIASES,
        )
    )
    if not has_signal:
        return None

    vin = validate_vin_value(_first_fact(facts, VIN_READ_ALIASES))
    vin_unavailable = _parse_bool(facts.get(FACT_KEY_VIN_UNAVAILABLE))
    if vin:
        vin_unavailable = False

    vehicle = ClaimVehicleIdentity(
        vehicle_id=_trim_or_none(facts.get(FACT_KEY_VEHICLE_ID)) or vehicle_id_for_case(cid),
        case_id=cid,
        year=_normalize_year(facts.get(FACT_KEY_YEAR)),
        make=_normalize_make_model(facts.get(FACT_KEY_MAKE)),
        model=_normalize_make_model(facts.get(FACT_KEY_MODEL)),
        vin=vin,
        vin_unavailable=vin_unavailable,
        license_plate=_normalize_plate(facts.get(FACT_KEY_LICENSE_PLATE)),
        plate_state=_normalize_plate_state(facts.get(FACT_KEY_PLATE_STATE)),
        source=_normalize_source(facts.get(FACT_KEY_SOURCE), default=SOURCE_CUSTOMER),
        verification_status=_normalize_verification(facts.get(FACT_KEY_VERIFICATION)),
        summary=_first_fact(facts, SUMMARY_READ_ALIASES),
        created_at=_trim_or_none(facts.get(FACT_KEY_CREATED_AT)) or "",
        updated_at=_trim_or_none(facts.get(FACT_KEY_UPDATED_AT)) or "",
    )
    if not vehicle.summary:
        vehicle.summary = build_vehicle_summary(vehicle)
    if not vehicle.created_at:
        vehicle.created_at = vehicle.updated_at or _utc_now_iso()
    if not vehicle.updated_at:
        vehicle.updated_at = vehicle.created_at
    return vehicle


def match_claim_vehicle_slot(
    *,
    case_id: str,
    existing: ClaimVehicleIdentity | None,
    incoming: ClaimVehicleIdentity,
) -> str:
    """Return match reason per freeze hierarchy (always one slot per claim)."""
    cid = str(case_id or "").strip()
    if existing is None:
        return "create"
    if existing.case_id != cid or incoming.case_id != cid:
        return "create"
    if existing.vin and incoming.vin and existing.vin == incoming.vin:
        return "normalized_vin"
    if (
        existing.license_plate
        and incoming.license_plate
        and existing.plate_state
        and incoming.plate_state
        and existing.license_plate == incoming.license_plate
        and existing.plate_state == incoming.plate_state
    ):
        return "plate_and_state"
    if existing.vehicle_id == vehicle_id_for_case(cid) or existing.vehicle_id == incoming.vehicle_id:
        return "existing_slot"
    return "existing_slot"


def _field_values_equal(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return _parse_bool(a) == _parse_bool(b)
    left = _trim_or_none(a)
    right = _trim_or_none(b)
    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    return left.casefold() == right.casefold()


def merge_claim_vehicle(
    existing: ClaimVehicleIdentity | None,
    incoming: ClaimVehicleIdentity,
    *,
    now: str | None = None,
) -> ClaimVehicleMergeResult:
    """Merge into the single claim vehicle slot; protect broker-confirmed values."""
    ts = now or _utc_now_iso()
    matched_by = match_claim_vehicle_slot(
        case_id=incoming.case_id,
        existing=existing,
        incoming=incoming,
    )
    if existing is None:
        created = ClaimVehicleIdentity(
            vehicle_id=vehicle_id_for_case(incoming.case_id),
            case_id=incoming.case_id,
            year=incoming.year,
            make=incoming.make,
            model=incoming.model,
            vin=incoming.vin,
            vin_unavailable=bool(incoming.vin_unavailable) and not incoming.vin,
            license_plate=incoming.license_plate,
            plate_state=incoming.plate_state,
            source=incoming.source,
            verification_status=incoming.verification_status
            if incoming.verification_status in ALLOWED_VERIFICATION_STATUSES
            else VERIFICATION_SUPPLIED_UNCONFIRMED,
            summary=None,
            created_at=incoming.created_at or ts,
            updated_at=ts,
        )
        created.summary = build_vehicle_summary(created)
        changed = [f for f in _IDENTITY_SCALAR_FIELDS if getattr(created, f) is not None]
        if created.vin_unavailable:
            changed.append("vin_unavailable")
        return ClaimVehicleMergeResult(
            vehicle=created,
            created=True,
            changed_fields=changed,
            conflict_fields=[],
            matched_by="create",
        )

    out = ClaimVehicleIdentity(**existing.as_dict())
    out.vehicle_id = vehicle_id_for_case(incoming.case_id)
    out.case_id = incoming.case_id
    changed: list[str] = []
    conflicts: list[str] = []
    confirmed = existing.verification_status == VERIFICATION_CONFIRMED
    soft_incoming = incoming.source in _SOFT_SOURCES

    def _apply_scalar(name: str, new_value: Any) -> None:
        nonlocal out
        if new_value is None or (isinstance(new_value, str) and not str(new_value).strip()):
            return
        current = getattr(out, name)
        if _field_values_equal(current, new_value):
            return
        if confirmed and current is not None and not _field_values_equal(current, new_value):
            # Broker-confirmed values must never be silently overwritten.
            conflicts.append(name)
            return
        if soft_incoming and confirmed:
            conflicts.append(name)
            return
        setattr(out, name, new_value)
        changed.append(name)

    _apply_scalar("year", incoming.year)
    _apply_scalar("make", incoming.make)
    _apply_scalar("model", incoming.model)
    _apply_scalar("vin", incoming.vin)
    _apply_scalar("license_plate", incoming.license_plate)
    _apply_scalar("plate_state", incoming.plate_state)

    if incoming.vin:
        if out.vin_unavailable:
            out.vin_unavailable = False
            changed.append("vin_unavailable")
    elif incoming.vin_unavailable and not out.vin:
        if confirmed and not existing.vin_unavailable:
            conflicts.append("vin_unavailable")
        elif not out.vin_unavailable:
            out.vin_unavailable = True
            changed.append("vin_unavailable")

    if conflicts:
        out.verification_status = VERIFICATION_NEEDS_CORRECTION
    elif incoming.verification_status == VERIFICATION_CONFIRMED:
        out.verification_status = VERIFICATION_CONFIRMED
    elif out.verification_status != VERIFICATION_CONFIRMED:
        if incoming.verification_status == VERIFICATION_NEEDS_CORRECTION:
            out.verification_status = VERIFICATION_NEEDS_CORRECTION
        elif changed:
            out.verification_status = VERIFICATION_SUPPLIED_UNCONFIRMED

    if incoming.source in ALLOWED_SOURCES and (changed or existing is None):
        # Keep broker_request if only soft sources follow; customer may refresh source.
        if not (soft_incoming and confirmed):
            out.source = incoming.source

    out.updated_at = ts
    if not out.created_at:
        out.created_at = existing.created_at or ts
    out.summary = build_vehicle_summary(out)
    return ClaimVehicleMergeResult(
        vehicle=out,
        created=False,
        changed_fields=changed,
        conflict_fields=conflicts,
        matched_by=matched_by,
    )


def claim_vehicle_to_known_facts_patch(vehicle: ClaimVehicleIdentity) -> dict[str, str]:
    """Project identity into canonical known_facts keys + backward-compatible aliases."""
    patch: dict[str, str] = {
        FACT_KEY_VEHICLE_ID: vehicle.vehicle_id,
        FACT_KEY_SOURCE: vehicle.source,
        FACT_KEY_VERIFICATION: vehicle.verification_status,
        FACT_KEY_VIN_UNAVAILABLE: _serialize_bool(bool(vehicle.vin_unavailable) and not vehicle.vin),
        FACT_KEY_CREATED_AT: vehicle.created_at or vehicle.updated_at or _utc_now_iso(),
        FACT_KEY_UPDATED_AT: vehicle.updated_at or _utc_now_iso(),
    }
    if vehicle.year:
        patch[FACT_KEY_YEAR] = vehicle.year
    if vehicle.make:
        patch[FACT_KEY_MAKE] = vehicle.make
    if vehicle.model:
        patch[FACT_KEY_MODEL] = vehicle.model
    if vehicle.vin:
        patch[FACT_KEY_VIN] = vehicle.vin
        for alias in VIN_WRITE_ALIASES:
            patch[alias] = vehicle.vin
    if vehicle.license_plate:
        patch[FACT_KEY_LICENSE_PLATE] = vehicle.license_plate
    if vehicle.plate_state:
        patch[FACT_KEY_PLATE_STATE] = vehicle.plate_state
    summary = vehicle.summary or build_vehicle_summary(vehicle)
    if summary:
        patch[FACT_KEY_SUMMARY] = summary
        for alias in SUMMARY_WRITE_ALIASES:
            patch[alias] = summary
    return patch


def apply_claim_vehicle_fact_records(
    fact_records: dict[str, Any] | None,
    vehicle: ClaimVehicleIdentity,
    *,
    case: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update checklist fact_records for vin / vehicle_information (same logical vehicle)."""
    merged = merge_fact_records(fact_records, case=case)
    status = vehicle.verification_status
    if status not in ALLOWED_VERIFICATION_STATUSES:
        status = VERIFICATION_SUPPLIED_UNCONFIRMED

    if vehicle.vin:
        try:
            merged = apply_fact_status_update(
                merged,
                field_key="vin",
                status=status,
                value=vehicle.vin,
                reason="claim_vehicle_identity",
                preserve_previous=True,
            )
        except ValueError:
            # Confirmed demotion guards — leave vin record untouched.
            pass

    summary = vehicle.summary or build_vehicle_summary(vehicle)
    if summary:
        try:
            merged = apply_fact_status_update(
                merged,
                field_key="vehicle_information",
                status=status,
                value=summary,
                reason="claim_vehicle_identity",
                preserve_previous=True,
            )
        except ValueError:
            pass
    # Stamp source for audit without inventing a parallel store.
    for key in ("vin", "vehicle_information"):
        rec = merged.get(key)
        if isinstance(rec, dict) and rec.get("value"):
            rec = dict(rec)
            rec["source"] = f"claim_vehicle:{vehicle.source}"
            merged[key] = rec
    return merged


def _slice1_style_event(
    *,
    event_type: str,
    case_id: str,
    command_id: str,
    correlation_id: str,
    sequence_number: int,
    actor: str,
    actor_identity: str,
    idempotency_key: str,
    evidence: dict[str, Any],
    timestamp: str,
) -> dict[str, Any]:
    """Slice1-shaped event — not a parallel vehicle_events model."""
    return {
        "event_id": f"evt_{uuid4().hex[:16]}",
        "case_id": case_id,
        "event_type": event_type,
        "command_id": command_id,
        "correlation_id": correlation_id,
        "sequence_number": sequence_number,
        "aggregate_version": sequence_number,
        "expected_state_version": max(0, sequence_number - 1),
        "actor": actor,
        "actor_identity": actor_identity,
        "state_before": "claim_vehicle",
        "state_after": "claim_vehicle",
        "visibility": "customer_and_broker",
        "evidence": evidence,
        "idempotency_key": idempotency_key,
        "created_at": timestamp,
    }


def _normalize_command_token(value: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name}_required")
    return text[:128]


def _replay(result: ClaimVehicleCommandResult) -> ClaimVehicleCommandResult:
    prior = result.as_dict()
    return ClaimVehicleCommandResult(
        outcome="replayed",
        command_id=str(prior["command_id"]),
        idempotency_key=str(prior["idempotency_key"]),
        correlation_id=str(prior["correlation_id"]),
        event_ids=list(prior["event_ids"] or []),
        vehicle=prior.get("vehicle"),
        known_facts_patch=dict(prior.get("known_facts_patch") or {}),
        fact_records=deepcopy(prior.get("fact_records") or {}),
        events=[dict(e) for e in (prior.get("events") or [])],
        complete=bool(prior.get("complete")),
        error_code=prior.get("error_code"),
        original_outcome=str(prior.get("outcome") or "accepted"),
        merge=prior.get("merge"),
    )


class ClaimVehicleIdentityService:
    """Idempotent Claim Vehicle Identity apply — Slice1 command-outcome pattern.

    Does not write intake_entities. Does not open SERVICE_LANE_ADD_CAR.
    """

    def __init__(self) -> None:
        # (case_id, actor_identity, idempotency_key) and (case_id, command_id)
        self._outcomes: dict[tuple[str, str, str], ClaimVehicleCommandResult] = {}
        self._command_outcomes: dict[tuple[str, str], ClaimVehicleCommandResult] = {}

    def clear_outcomes(self) -> None:
        self._outcomes.clear()
        self._command_outcomes.clear()

    def upsert(
        self,
        *,
        case_id: str,
        payload: dict[str, Any],
        command_id: str,
        idempotency_key: str,
        actor: str = "customer",
        actor_identity: str = "customer",
        source: str = SOURCE_CUSTOMER,
        mode: str = "draft",
        known_facts: dict[str, Any] | None = None,
        fact_records: dict[str, Any] | None = None,
        case: dict[str, Any] | None = None,
        persist: bool = False,
        correlation_id: str | None = None,
        sequence_base: int = 0,
    ) -> ClaimVehicleCommandResult:
        cid = _normalize_command_token(case_id, "case_id")
        cmd = _normalize_command_token(command_id, "command_id")
        idem = _normalize_command_token(idempotency_key, "idempotency_key")
        actor_id = _normalize_command_token(actor_identity or actor, "actor_identity")
        corr = (correlation_id or cmd).strip()[:128] or cmd
        mode_norm = str(mode or "draft").strip().lower()
        if mode_norm not in {"draft", "submit"}:
            raise ValueError("invalid_mode")

        prior = self._outcomes.get((cid, actor_id, idem)) or self._command_outcomes.get((cid, cmd))
        if prior is not None:
            return _replay(prior)

        case_obj = case if isinstance(case, dict) else {}
        facts = (
            known_facts
            if isinstance(known_facts, dict)
            else (case_obj.get("known_facts") if isinstance(case_obj.get("known_facts"), dict) else {})
        )
        existing = read_claim_vehicle_from_facts(facts, case_id=cid)
        incoming = normalize_claim_vehicle_input(payload, case_id=cid, source=source)
        # Partial VIN must never appear — normalize_claim_vehicle_input already drops it.
        if _trim_or_none(payload.get("vin") or payload.get("vehicle_vin")) and not incoming.vin:
            # Still allow draft of other fields; reject submit that relied on invalid VIN only.
            if mode_norm == "submit" and not (
                incoming.vin_unavailable and incoming.year and incoming.make and incoming.model
            ):
                rejected = ClaimVehicleCommandResult(
                    outcome="rejected",
                    command_id=cmd,
                    idempotency_key=idem,
                    correlation_id=corr,
                    event_ids=[],
                    vehicle=existing.as_dict() if existing else None,
                    known_facts_patch={},
                    fact_records=merge_fact_records(fact_records, case=case_obj or {"known_facts": facts}),
                    events=[],
                    complete=False,
                    error_code="vin_invalid",
                )
                self._store_outcome(cid, actor_id, idem, cmd, rejected)
                return rejected

        merge = merge_claim_vehicle(existing, incoming)
        vehicle = merge.vehicle

        if mode_norm == "submit" and not is_claim_vehicle_complete(vehicle):
            rejected = ClaimVehicleCommandResult(
                outcome="rejected",
                command_id=cmd,
                idempotency_key=idem,
                correlation_id=corr,
                event_ids=[],
                vehicle=vehicle.as_dict(),
                known_facts_patch={},
                fact_records=merge_fact_records(fact_records, case=case_obj or {"known_facts": facts}),
                events=[],
                complete=False,
                error_code="vehicle_incomplete",
                merge={
                    "created": merge.created,
                    "matched_by": merge.matched_by,
                    "changed_fields": list(merge.changed_fields),
                    "conflict_fields": list(merge.conflict_fields),
                },
            )
            self._store_outcome(cid, actor_id, idem, cmd, rejected)
            return rejected

        facts_patch = claim_vehicle_to_known_facts_patch(vehicle)
        updated_records = apply_claim_vehicle_fact_records(
            fact_records if fact_records is not None else case_obj.get("fact_records"),
            vehicle,
            case=case_obj or {"known_facts": {**facts, **facts_patch}},
        )

        events: list[dict[str, Any]] = []
        # Emit at most one field_saved-style event per accepted command (no duplicates on replay).
        if merge.changed_fields or merge.created or merge.conflict_fields:
            seq = int(sequence_base) + 1
            events.append(
                _slice1_style_event(
                    event_type="field_saved",
                    case_id=cid,
                    command_id=cmd,
                    correlation_id=corr,
                    sequence_number=seq,
                    actor=actor,
                    actor_identity=actor_id,
                    idempotency_key=idem,
                    evidence={
                        "field_id": "vehicle_information" if not vehicle.vin else "vin",
                        "claim_vehicle_id": vehicle.vehicle_id,
                        "value": vehicle.summary or vehicle.vin,
                        "complete": is_claim_vehicle_complete(vehicle),
                        "mode": mode_norm,
                        "matched_by": merge.matched_by,
                        "changed_fields": list(merge.changed_fields),
                        "conflict_fields": list(merge.conflict_fields),
                        "verification_status": vehicle.verification_status,
                        "known_facts_keys": sorted(facts_patch.keys()),
                    },
                    timestamp=vehicle.updated_at or _utc_now_iso(),
                )
            )

        if persist:
            self._persist_known_facts(cid, facts_patch, source=incoming.source)

        # In-memory case mutation for resume tests / callers that pass a case dict.
        if case_obj is not None and case is not None:
            current_facts = dict(case_obj.get("known_facts") or {}) if isinstance(case_obj.get("known_facts"), dict) else {}
            current_facts.update(facts_patch)
            case_obj["known_facts"] = current_facts
            case_obj["fact_records"] = updated_records

        result = ClaimVehicleCommandResult(
            outcome="accepted",
            command_id=cmd,
            idempotency_key=idem,
            correlation_id=corr,
            event_ids=[e["event_id"] for e in events],
            vehicle=vehicle.as_dict(),
            known_facts_patch=facts_patch,
            fact_records=updated_records,
            events=events,
            complete=is_claim_vehicle_complete(vehicle),
            merge={
                "created": merge.created,
                "matched_by": merge.matched_by,
                "changed_fields": list(merge.changed_fields),
                "conflict_fields": list(merge.conflict_fields),
            },
        )
        self._store_outcome(cid, actor_id, idem, cmd, result)
        return result

    def _store_outcome(
        self,
        case_id: str,
        actor_identity: str,
        idempotency_key: str,
        command_id: str,
        result: ClaimVehicleCommandResult,
    ) -> None:
        self._outcomes[(case_id, actor_identity, idempotency_key)] = result
        self._command_outcomes[(case_id, command_id)] = result

    def _persist_known_facts(self, case_id: str, facts_patch: dict[str, str], *, source: str) -> None:
        from services.fiqa_api.inbox_triage.case_store import patch_case_known_facts

        provenance = _PROVENANCE_BY_IDENTITY_SOURCE.get(source, "customer_task")
        patch_case_known_facts(
            case_id,
            facts_patch,
            source=provenance,
            status="pending_confirmation",
        )


def upsert_claim_vehicle_identity(**kwargs: Any) -> ClaimVehicleCommandResult:
    """Module-level helper using a process-local default service (tests may pass their own)."""
    service = kwargs.pop("service", None)
    svc = service if isinstance(service, ClaimVehicleIdentityService) else _DEFAULT_SERVICE
    return svc.upsert(**kwargs)


_DEFAULT_SERVICE = ClaimVehicleIdentityService()
