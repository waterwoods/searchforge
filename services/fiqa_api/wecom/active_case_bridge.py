"""WeCom text event → Active Case resolver bridge (Track A readiness)."""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from services.fiqa_api.inbox_triage.active_case_resolver import (
    ResolverOutcome,
    resolve_active_case_for_evidence,
)
from services.fiqa_api.inbox_triage.case_store import (
    append_evidence_event_only,
    append_follow_up_message,
    bind_case_channel_identity,
    save_case,
    update_case_customer,
    update_case_workspace_flags,
    utc_now_iso,
)
from services.fiqa_api.inbox_triage.case_truth_repository import (
    get_case_for_read,
    list_all_cases_for_read,
    list_cases_for_phone_lookup,
)
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.inbox_triage.phone_normalization import normalize_phone_digits
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.identity import (
    extract_delivery_date_from_text,
    extract_phone_from_text,
    extract_primary_driver_from_text,
    extract_vin_from_text,
    extract_zip_from_text,
)
from services.fiqa_api.wecom.intent import IntentResult, canonical_intent
from services.fiqa_api.wecom.reply import DONE_CARD_TEXT
from services.fiqa_api.wecom.reply_outbox import enqueue_wecom_reply, wecom_reply_outbox_enabled
from services.fiqa_api.wecom.send_msg import send_text_reply, wecom_slice_send_enabled

logger = logging.getLogger(__name__)

WeComIngestOutcome = Literal[
    "skipped",
    "duplicate_msg",
    "need_phone",
    "broker_review",
    "created",
    "attached",
    "intent_not_actionable",
]

_ADD_CAR_CANONICAL = frozenset({"add_vehicle", "add_car"})


def _log_event(event: str, payload: dict[str, Any]) -> None:
    logger.info("%s %s", event, json.dumps(payload, ensure_ascii=False))


def _evidence_filename(msg_id: str) -> str:
    mid = (msg_id or "").strip() or "unknown"
    return f"wecom:{mid}"


def find_case_by_wecom_msg_id(msg_id: str) -> str | None:
    """Return case_id if this WeCom msg_id was already ingested.

    Uses the Postgres-aware `list_all_cases_for_read` facade (not the
    JSON-only `case_store.list_all_cases`, which always returns an empty
    list in production — see UNIFIED_INTAKE_DB_PRIMARY_WRITES). Using the
    JSON-only reader here silently disabled this dedup check in production,
    letting the same msg_id be re-ingested (and re-replied to) on every
    callback retry / sync_msg replay.
    """
    mid = (msg_id or "").strip()
    if not mid:
        return None
    marker = _evidence_filename(mid)
    for case in list_all_cases_for_read():
        for ev in case.get("evidence_events") or []:
            if not isinstance(ev, dict):
                continue
            if ev.get("wecom_msg_id") == mid:
                return str(case.get("case_id") or "").strip() or None
            if ev.get("filename") == marker:
                return str(case.get("case_id") or "").strip() or None
    return None


def _build_add_car_triage_stub(
    phone: str,
    *,
    vin: str | None = None,
    merge_review: bool = False,
) -> dict[str, Any]:
    digits = normalize_phone_digits(phone)
    still_needed = ["year", "make_model", "zip", "delivery_date", "primary_driver", "vin"]
    collected: list[str] = []
    if digits:
        collected.append("phone")
    if vin:
        still_needed = [f for f in still_needed if f != "vin"]
        collected.append("vin")
    stub: dict[str, Any] = {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": (
            "WeCom add-vehicle message received; collect vehicle documents and verify identity."
        ),
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": False,
        "lifecycle_status": "collecting",
        "collection_stage": "collecting",
        "collected_fields": collected,
        "still_needed_fields": still_needed,
        "quote_ready_status": "need_more",
        "service_type": "add_car",
        "extracted_contact_phone": digits,
    }
    if vin:
        stub["vehicle_key"] = vin
    if merge_review:
        stub["quote_ready_status"] = "almost_ready"
    return stub


def _record_wecom_evidence(case_id: str, msg_id: str) -> None:
    append_evidence_event_only(
        case_id,
        channel="wecom_kf",
        filename=_evidence_filename(msg_id),
    )


# ---------------------------------------------------------------------------
# Track B0.2 — Draft Case creation on "Start", bound to external_userid.
#
# Governed by docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md §4.1/§9 and
# P16_CUSTOMER_FIRST_CONSTITUTION.md Rule 7 (one active case) + Rule 8 (one
# flow at a time). No Broker Confirm, no Done Card, no claim flag here — that
# is B0.3/B0.4 scope. This is the "just Draft Case, then reuse the existing
# collected/still_needed/quote_ready pipeline" entry point only.
# ---------------------------------------------------------------------------

# Fields this Draft flow tracks toward "quote_ready" (contract §4.2 extractor
# scope). Deliberately narrower than the six-field Track A stub below — year
# and make_model have no WeCom-local extractor yet, so they are not part of
# this Draft's readiness gate (adding unreachable fields here would make
# quote_ready_status permanently stuck at "need_more").
_DRAFT_TRACKED_FIELDS: tuple[str, ...] = ("vin", "zip", "delivery_date", "primary_driver")


def find_open_draft_case_by_external_userid(external_userid: str) -> str | None:
    """
    Channel-identity binding (contract §4.1): find the open case (Draft OR,
    since B0.3, already-confirmed Active) already bound to this WeCom
    `external_userid`.

    Track B0.3 / contract §item-5 (customer follow-up): once the broker
    confirms, this identity binding must keep routing to the SAME case — no
    new Draft, no new Start Card, no duplicate case (Constitution Rule 7).
    Only `case_status == closed` ends the binding.

    Narrow lookup only — does not touch or replace the phone-based resolver
    contract (`active_case_resolver.py`), which still governs cross-channel
    merge once a phone is known.
    """
    ext = (external_userid or "").strip()
    if not ext:
        return None
    for case in list_all_cases_for_read():
        if case.get("wecom_external_userid") != ext:
            continue
        if case.get("case_status") == "closed":
            continue
        cid = str(case.get("case_id") or "").strip()
        if cid:
            return cid
    return None


def _draft_readiness(
    already_collected: set[str],
    newly_found: dict[str, str | None],
) -> tuple[list[str], list[str], str]:
    """
    Compute this turn's collected/still_needed/quote_ready_status contribution.

    `collected_fields`/`still_needed_fields` persistence itself is an additive
    union handled by the existing `append_follow_up_message` merge (reused,
    not reimplemented) — but `quote_ready_status` is overwritten each turn, so
    it must be computed against the *cumulative* set (prior turns + this one).
    """
    cumulative = set(already_collected)
    for field, value in newly_found.items():
        if value:
            cumulative.add(field)
    this_turn_collected = [f for f in _DRAFT_TRACKED_FIELDS if newly_found.get(f)]
    still_needed = [f for f in _DRAFT_TRACKED_FIELDS if f not in cumulative]
    if not still_needed:
        quote_ready_status = "quote_ready"
    elif len(still_needed) == 1:
        quote_ready_status = "almost_ready"
    else:
        quote_ready_status = "need_more"
    return this_turn_collected, still_needed, quote_ready_status


def _build_draft_case_stub(
    *,
    already_collected: set[str] | None = None,
    phone: str | None = None,
    vin: str | None = None,
    zip_code: str | None = None,
    delivery_date: str | None = None,
    primary_driver: str | None = None,
    existing_vehicle_key: str | None = None,
) -> dict[str, Any]:
    """Draft Case triage stub — same contract shape as `_build_add_car_triage_stub`,
    reused verbatim (issue_category/collected_fields/still_needed_fields/
    quote_ready_status); only the tracked field set differs (see above)."""
    digits = normalize_phone_digits(phone or "")
    newly_found = {
        "vin": vin,
        "zip": zip_code,
        "delivery_date": delivery_date,
        "primary_driver": primary_driver,
    }
    collected, still_needed, quote_ready_status = _draft_readiness(
        already_collected or set(), newly_found
    )
    if digits:
        collected = ["phone", *collected]
    stub: dict[str, Any] = {
        "issue_category": "add_car_quote",
        "urgency": "medium",
        "manual_followup_needed": True,
        "broker_next_step": "WeCom Draft Case — collect remaining fields; broker confirms before anything changes.",
        "client_prep": "",
        "client_reply_draft": "",
        "handoff_ready": not still_needed,
        "lifecycle_status": "collecting",
        "collection_stage": "collecting",
        "collected_fields": collected,
        "still_needed_fields": still_needed,
        "quote_ready_status": quote_ready_status,
        "service_type": "add_car",
        "extracted_contact_phone": digits,
    }
    if vin:
        stub["vehicle_key"] = vin
    elif existing_vehicle_key:
        # append_follow_up_message overwrites vehicle_key from this turn's stub
        # every time; carry the prior value forward so a VIN captured earlier
        # is not wiped out by a later turn that doesn't repeat it.
        stub["vehicle_key"] = existing_vehicle_key
    return stub


def find_open_add_car_case_by_external_userid(external_userid: str) -> str | None:
    """Channel binding scoped to open add_car cases only (H5 token / Start Card)."""
    ext = (external_userid or "").strip()
    if not ext:
        return None
    for case in list_all_cases_for_read():
        if case.get("wecom_external_userid") != ext:
            continue
        if case.get("case_status") == "closed":
            continue
        if str(case.get("service_lane") or "").strip().lower() not in ("add_car", SERVICE_LANE_ADD_CAR):
            continue
        cid = str(case.get("case_id") or "").strip()
        if cid:
            return cid
    return None


def create_or_attach_draft_case_for_start_click(normalized: dict[str, Any]) -> dict[str, Any]:
    """
    Track B0.2 — customer presses "Start": create ONE Draft Case, bound to
    `external_userid`. Idempotent: a duplicate/double click attaches to the
    already-open Draft instead of creating a second one (Rule 7).
    """
    from services.fiqa_api.inbox_triage.h5_task_upload import is_explicit_add_car_restart

    msg_id = str(normalized.get("msg_id") or "").strip()
    external_userid = str(normalized.get("external_userid") or "").strip()
    text = str(normalized.get("text") or "").strip()
    open_kf_id = str(normalized.get("open_kf_id") or "").strip() or None

    existing = find_open_add_car_case_by_external_userid(external_userid)
    if existing:
        if is_explicit_add_car_restart(text):
            existing = None
        else:
            bind_case_channel_identity(
                existing,
                wecom_external_userid=external_userid,
                wecom_open_kf_id=open_kf_id,
            )
            _record_wecom_evidence(existing, msg_id)
            _log_event(
                "wecom_draft_case_start_click_v1",
                {"msg_id": msg_id, "action": "attached_existing", "case_id": existing},
            )
            return {"outcome": "attached", "case_id": existing, "case_created": False}

    triage_stub = _build_draft_case_stub()
    saved = save_case(
        "[客户] WeCom: Start / 开始",
        triage_stub,
        status="new",
        service_lane=SERVICE_LANE_ADD_CAR,
    )
    case_id = str(saved.get("case_id") or "").strip()
    if case_id and external_userid:
        bind_case_channel_identity(
            case_id,
            wecom_external_userid=external_userid,
            wecom_open_kf_id=str(normalized.get("open_kf_id") or "").strip() or None,
        )
    if case_id:
        _record_wecom_evidence(case_id, msg_id)
    _log_event(
        "wecom_draft_case_start_click_v1",
        {
            "msg_id": msg_id,
            "action": "created",
            "case_id": case_id,
            "external_userid": external_userid,
        },
    )
    return {"outcome": "created", "case_id": case_id or None, "case_created": True}


def ingest_wecom_text_to_draft_case(
    normalized: dict[str, Any],
    case_id: str,
) -> dict[str, Any]:
    """
    Track B0.2 — merge one customer text turn into an already-open Draft Case.

    Reuses the existing `append_follow_up_message` collected/still_needed
    merge (no new extraction/merge engine). Extraction stays adapter-local
    (`wecom/identity.py`), same pattern as phone/VIN in the Track A path.
    """
    msg_id = str(normalized.get("msg_id") or "").strip()
    text = str(normalized.get("text") or "").strip()

    existing_by_msg = find_case_by_wecom_msg_id(msg_id)
    if existing_by_msg:
        _log_event(
            "wecom_draft_case_ingest_v1",
            {"msg_id": msg_id, "outcome": "duplicate_msg", "case_id": existing_by_msg},
        )
        return {"outcome": "duplicate_msg", "case_id": existing_by_msg, "case_created": False}

    case = get_case_for_read(case_id)
    if case is None:
        _log_event(
            "wecom_draft_case_ingest_v1",
            {"msg_id": msg_id, "outcome": "case_not_found", "case_id": case_id},
        )
        return {"outcome": "case_not_found", "case_id": None, "case_created": False}

    already_collected = {str(x).lower() for x in (case.get("collected_fields") or [])}

    phone = normalized.get("phone") or extract_phone_from_text(text)
    vin = extract_vin_from_text(text)
    zip_code = extract_zip_from_text(text)
    delivery_date = extract_delivery_date_from_text(text)
    primary_driver = extract_primary_driver_from_text(text)

    triage_stub = _build_draft_case_stub(
        already_collected=already_collected,
        phone=phone,
        vin=vin,
        zip_code=zip_code,
        delivery_date=delivery_date,
        primary_driver=primary_driver,
        existing_vehicle_key=case.get("vehicle_key"),
    )

    if not text:
        text = "(no text)"
    updated = append_follow_up_message(case_id, text, triage_stub)
    if updated is None:
        _log_event(
            "wecom_draft_case_ingest_v1",
            {"msg_id": msg_id, "outcome": "case_not_found", "case_id": case_id},
        )
        return {"outcome": "case_not_found", "case_id": None, "case_created": False}

    phone_digits = normalize_phone_digits(phone or "")
    if phone_digits:
        update_case_customer(case_id, customer_phone=phone_digits)
    _record_wecom_evidence(case_id, msg_id)

    _log_event(
        "wecom_draft_case_ingest_v1",
        {
            "msg_id": msg_id,
            "outcome": "attached",
            "case_id": case_id,
            "vin_present": bool(vin),
            "zip_present": bool(zip_code),
            "delivery_date_present": bool(delivery_date),
            "primary_driver_present": bool(primary_driver),
            "quote_ready_status": updated.get("quote_ready_status"),
        },
    )
    return {
        "outcome": "attached",
        "case_id": case_id,
        "case_created": False,
        "readiness_gate": "NEED_INFO",
        "quote_ready_status": updated.get("quote_ready_status"),
        "still_needed_fields": updated.get("still_needed_fields"),
    }


def ingest_wecom_text_to_active_case(
    normalized: dict[str, Any],
    intent_result: IntentResult,
) -> dict[str, Any]:
    """
    Minimal WeCom → Active Case bridge.

    Only high-confidence add_vehicle with valid phone creates or attaches a case.
    No Trusted Packet from text-only evidence.
    """
    msg_id = str(normalized.get("msg_id") or "").strip()
    text = str(normalized.get("text") or "").strip()
    phone = normalized.get("phone") or extract_phone_from_text(text)
    vin = extract_vin_from_text(text)
    detected = canonical_intent(intent_result.intent)

    _log_event(
        "wecom_intent_detected_v1",
        {
            "msg_id": msg_id,
            "intent": detected,
            "internal_intent": intent_result.intent,
            "confidence": intent_result.confidence,
            "matched_by": intent_result.matched_by,
        },
    )

    existing_case = find_case_by_wecom_msg_id(msg_id)
    if existing_case:
        _log_event(
            "wecom_active_case_resolution_v1",
            {"msg_id": msg_id, "outcome": "duplicate_msg", "case_id": existing_case},
        )
        return {
            "outcome": "duplicate_msg",
            "case_id": existing_case,
            "case_created": False,
            "readiness_gate": None,
        }

    if detected not in _ADD_CAR_CANONICAL or intent_result.confidence != "high":
        if phone and vin and normalize_phone_digits(phone):
            detected = "add_vehicle"
        else:
            return {
                "outcome": "intent_not_actionable",
                "case_id": None,
                "case_created": False,
                "readiness_gate": None,
            }

    if not phone or not normalize_phone_digits(phone) or len(normalize_phone_digits(phone)) != 10:
        _log_event(
            "wecom_identity_missing_v1",
            {
                "msg_id": msg_id,
                "external_userid": normalized.get("external_userid"),
                "intent": detected,
                "gate": "NEED_PHONE",
            },
        )
        return {
            "outcome": "need_phone",
            "case_id": None,
            "case_created": False,
            "readiness_gate": "NEED_INFO",
        }

    phone_digits = normalize_phone_digits(phone)
    decision = resolve_active_case_for_evidence(
        phone=phone_digits,
        intent="add_vehicle",
        new_vin=vin,
        cases=list_cases_for_phone_lookup(phone_digits),
    )

    _log_event(
        "wecom_active_case_resolution_v1",
        {
            "msg_id": msg_id,
            "phone_tail": phone_digits[-4:],
            "resolver_outcome": decision.outcome.value,
            "case_id": decision.case_id,
            "conflict_reason": decision.conflict_reason,
            "candidate_count": decision.candidate_count,
            "vin_present": bool(vin),
        },
    )

    source_text = f"[客户] WeCom: {text}"
    merge_review = decision.outcome == ResolverOutcome.BROKER_REVIEW
    triage_stub = _build_add_car_triage_stub(phone_digits, vin=vin, merge_review=merge_review)

    if decision.outcome == ResolverOutcome.CREATE:
        saved = save_case(
            source_text,
            triage_stub,
            status="new",
            service_lane=SERVICE_LANE_ADD_CAR,
        )
        case_id = str(saved.get("case_id") or "").strip()
        if case_id:
            update_case_customer(case_id, customer_phone=phone_digits)
            _record_wecom_evidence(case_id, msg_id)
        _log_event(
            "wecom_active_case_created_or_attached_v1",
            {"msg_id": msg_id, "action": "created", "case_id": case_id},
        )
        return {
            "outcome": "created",
            "case_id": case_id or None,
            "case_created": True,
            "readiness_gate": "NEED_INFO",
        }

    if decision.outcome == ResolverOutcome.BROKER_REVIEW:
        case_id = str(decision.case_id or "").strip()
        if case_id:
            append_follow_up_message(case_id, text, triage_stub)
            _record_wecom_evidence(case_id, msg_id)
        _log_event(
            "wecom_active_case_created_or_attached_v1",
            {
                "msg_id": msg_id,
                "action": "broker_review",
                "case_id": case_id or None,
                "conflict_reason": decision.conflict_reason,
            },
        )
        return {
            "outcome": "broker_review",
            "case_id": case_id or None,
            "case_created": False,
            "readiness_gate": "BROKER_REVIEW",
            "conflict_reason": decision.conflict_reason,
        }

    case_id = str(decision.case_id or "").strip()
    if case_id:
        append_follow_up_message(case_id, text, triage_stub)
        _record_wecom_evidence(case_id, msg_id)
    _log_event(
        "wecom_active_case_created_or_attached_v1",
        {"msg_id": msg_id, "action": "attached", "case_id": case_id},
    )
    return {
        "outcome": "attached",
        "case_id": case_id or None,
        "case_created": False,
        "readiness_gate": "NEED_INFO",
    }


# ---------------------------------------------------------------------------
# Track B0.3 — Broker Confirm + Done Card.
#
# Governed by docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md §7/§9 and
# P16_CUSTOMER_FIRST_CONSTITUTION.md Rule 6 (Broker Confirms Identity). No
# resolver changes — `active_case_resolver.py` is untouched; this only sets
# the additive `broker_confirmed_at` flag (case_store) and, on the *first*
# successful confirm only, sends exactly ONE Done Card via the existing
# WeCom send APIs (`wecom/send_msg.py`). Never sent again on a repeat call
# and never sent automatically — only from this explicit broker action.
# ---------------------------------------------------------------------------


class BrokerConfirmError(ValueError):
    """Raised when Broker Confirm cannot proceed (contract §4.1 phone guardrail)."""


def _send_done_card_once(case: dict[str, Any]) -> bool:
    """
    Best-effort Done Card send. Never raises — Broker Confirm (the durable,
    important side effect: `broker_confirmed_at`) must still succeed even if
    the customer channel is unreachable or unconfigured.
    """
    external_userid = str(case.get("wecom_external_userid") or "").strip()
    open_kf_id = str(case.get("wecom_open_kf_id") or "").strip()
    case_id = str(case.get("case_id") or "").strip()
    if not external_userid or not open_kf_id:
        _log_event(
            "wecom_done_card_skipped_v1",
            {"case_id": case_id, "reason": "no_wecom_channel_binding"},
        )
        return False
    if not wecom_slice_send_enabled():
        _log_event(
            "wecom_done_card_skipped_v1",
            {"case_id": case_id, "reason": "WECOM_SLICE_SEND_REPLY not set"},
        )
        return False
    cfg = load_wecom_kf_config()
    if cfg is None:
        _log_event(
            "wecom_done_card_skipped_v1",
            {"case_id": case_id, "reason": "wecom_kf_not_configured"},
        )
        return False
    try:
        reply_payload = {"msgtype": "text", "text": {"content": DONE_CARD_TEXT}}
        if wecom_reply_outbox_enabled():
            created = enqueue_wecom_reply(
                msg_id=None,
                external_userid=external_userid,
                open_kf_id=open_kf_id,
                case_id=case_id,
                reply_type="done_card",
                reply_payload=reply_payload,
            )
            if not created:
                _log_event(
                    "wecom_done_card_skipped_v1",
                    {"case_id": case_id, "reason": "outbox_dedup_key_exists"},
                )
                return False
            _log_event("wecom_done_card_enqueued_v1", {"case_id": case_id})
            return True
        send_text_reply(
            cfg,
            external_userid=external_userid,
            open_kf_id=open_kf_id,
            content=DONE_CARD_TEXT,
        )
        _log_event("wecom_done_card_sent_v1", {"case_id": case_id})
        return True
    except Exception as exc:
        _log_event(
            "wecom_done_card_send_failed_v1",
            {"case_id": case_id, "error": str(exc)},
        )
        return False


def confirm_case_by_broker(case_id: str) -> dict[str, Any]:
    """
    Track B0.3 — broker clicks "Confirm" (or "Manual Promote"): set
    `broker_confirmed_at` and send exactly ONE Done Card. Idempotent — safe
    to call twice; the second call is a no-op that does not resend the card.

    Guardrail (contract §4.1/§9): blocked with `BrokerConfirmError` when the
    case has no phone on file yet (cannot confirm an unidentifiable case).
    """
    case = get_case_for_read(case_id)
    if case is None:
        return {
            "outcome": "case_not_found",
            "case": None,
            "already_confirmed": False,
            "done_card_sent": False,
        }

    phone_digits = normalize_phone_digits(case.get("customer_phone") or "")
    already_confirmed = bool(case.get("broker_confirmed_at"))
    if not phone_digits and not already_confirmed:
        raise BrokerConfirmError(
            "broker_confirm_blocked_no_phone_v1: case has no phone on file yet"
        )

    updated = update_case_workspace_flags(case_id, broker_confirmed_at=utc_now_iso())
    if updated is None:
        return {
            "outcome": "case_not_found",
            "case": None,
            "already_confirmed": already_confirmed,
            "done_card_sent": False,
        }

    done_card_sent = False
    if not already_confirmed:
        done_card_sent = _send_done_card_once(updated)

    _log_event(
        "wecom_broker_confirm_v1",
        {
            "case_id": case_id,
            "already_confirmed": already_confirmed,
            "done_card_sent": done_card_sent,
        },
    )
    return {
        "outcome": "confirmed",
        "case": updated,
        "already_confirmed": already_confirmed,
        "done_card_sent": done_card_sent,
    }
