"""Persist customer policy-context confirmation (Stage 2 Loop 1).

Does not upload an insurance card. Does not overwrite AMS/CRM policy SoR.
Marks case intake completeness when the customer confirms existing linked data.
"""

from __future__ import annotations

from typing import Any, Mapping

from services.fiqa_api.inbox_triage.policy_context_decision import (
    CHOICE_CHANGED,
    CHOICE_CORRECT,
    CHOICE_UNCERTAIN,
    DECISION_CONFIRM_EXISTING,
    DECISION_FALLBACK,
    DECISION_REQUIRE_UPLOAD,
    EVENT_POLICY_CONTEXT_CHANGE_REPORTED,
    EVENT_POLICY_CONTEXT_CONFIRMED,
    EVENT_POLICY_CONTEXT_UNCERTAIN,
    decide_policy_context,
    normalize_customer_choice,
)

SOURCE_CUSTOMER_CONFIRMED = "customer_policy_context_confirmed"
FACT_VALUE_CONFIRMED = "已有保单资料，客户已确认"
BROKER_LABEL_CONFIRMED = "已有保单资料，客户已确认"
BROKER_LABEL_UPLOADED = "客户上传了保险卡"


def policy_context_status(case: Mapping[str, Any] | None) -> str:
    if not isinstance(case, Mapping):
        return ""
    raw = case.get("policy_context")
    if not isinstance(raw, Mapping):
        return ""
    return str(raw.get("status") or "").strip().lower()


def policy_context_is_customer_confirmed(case: Mapping[str, Any] | None) -> bool:
    if not isinstance(case, Mapping):
        return False
    raw = case.get("policy_context")
    if not isinstance(raw, Mapping):
        return False
    return (
        str(raw.get("status") or "").strip().lower() == "confirmed"
        and str(raw.get("customer_choice") or "").strip().lower() == CHOICE_CORRECT
    )


def insurance_card_uploaded(case: Mapping[str, Any] | None) -> bool:
    """True only when a real insurance-card attachment/slot exists."""
    if not isinstance(case, Mapping):
        return False
    slots = case.get("claim_attachment_slots")
    if isinstance(slots, Mapping):
        row = slots.get("policy_or_insurance_card")
        if isinstance(row, Mapping) and str(row.get("status") or "").strip().lower() == "received":
            return True
    for att in case.get("case_attachments") or []:
        if not isinstance(att, Mapping):
            continue
        keys = (
            str(att.get(k) or "").strip().lower()
            for k in ("slot_assignment", "claim_slot", "evidence_category", "document_type")
        )
        if any(k in {"policy_or_insurance_card", "insurance_card", "insurance_card_photo"} for k in keys):
            return True
    return False


def broker_policy_evidence_label(case: Mapping[str, Any] | None) -> str | None:
    if insurance_card_uploaded(case):
        return BROKER_LABEL_UPLOADED
    if policy_context_is_customer_confirmed(case):
        return BROKER_LABEL_CONFIRMED
    return None


def _event_type_for_choice(choice: str) -> str:
    if choice == CHOICE_CORRECT:
        return EVENT_POLICY_CONTEXT_CONFIRMED
    if choice == CHOICE_CHANGED:
        return EVENT_POLICY_CONTEXT_CHANGE_REPORTED
    return EVENT_POLICY_CONTEXT_UNCERTAIN


def _timeline_text_for_choice(choice: str) -> str:
    if choice == CHOICE_CORRECT:
        return BROKER_LABEL_CONFIRMED
    if choice == CHOICE_CHANGED:
        return "客户反馈保单/车辆信息有变化"
    return "客户对已有保单资料不确定"


def build_policy_context_record(
    *,
    decision: Mapping[str, Any],
    customer_choice: str,
    command_id: str,
    idempotency_key: str,
    confirmed_at: str,
) -> dict[str, Any]:
    choice = normalize_customer_choice(customer_choice) or CHOICE_UNCERTAIN
    decision_code = str(decision.get("decision") or DECISION_FALLBACK)
    summary = (
        decision.get("customer_safe_summary")
        if isinstance(decision.get("customer_safe_summary"), Mapping)
        else {}
    )
    vehicle = decision.get("vehicle") if isinstance(decision.get("vehicle"), Mapping) else {}
    policy = decision.get("policy") if isinstance(decision.get("policy"), Mapping) else {}

    if choice == CHOICE_CORRECT and decision_code == DECISION_CONFIRM_EXISTING:
        status = "confirmed"
        upload_required = False
        upload_reason = None
    elif choice == CHOICE_CHANGED:
        status = "upload_required"
        upload_required = True
        upload_reason = "客户反馈信息有变化，请上传最新保险卡。"
    elif choice == CHOICE_UNCERTAIN:
        status = "upload_required"
        upload_required = True
        upload_reason = "客户不确定已有资料，请上传保险卡以便核对。"
    else:
        status = "upload_required"
        upload_required = True
        upload_reason = str(decision.get("upload_reason_zh") or "请上传保险卡。")

    return {
        "decision": decision_code,
        "status": status,
        "customer_choice": choice,
        "upload_required": upload_required,
        "upload_reason_zh": upload_reason,
        "policy_ref": str(policy.get("policy_ref") or "").strip() or None,
        "vehicle_ref": str(vehicle.get("vehicle_ref") or "").strip() or None,
        "carrier_display": str(summary.get("carrier_display") or policy.get("carrier_display") or "").strip()
        or None,
        "vehicle_summary": str(summary.get("vehicle_summary") or "").strip() or None,
        "customer_name": str(summary.get("customer_name") or "").strip() or None,
        "source": str(decision.get("lookup_source") or "lookup"),
        "lookup_confidence": str(decision.get("lookup_confidence") or ""),
        "reason_codes": list(decision.get("reason_codes") or []),
        "snapshot": {
            "customer_safe_summary": dict(summary) if summary else {},
            "policy_status": str(policy.get("status") or ""),
            "policy_freshness": str(policy.get("freshness") or ""),
            "effective_end": str(policy.get("effective_end") or ""),
            "plate_masked": str(summary.get("plate_masked") or ""),
        },
        "confirmed_at": confirmed_at,
        "command_id": command_id,
        "idempotency_key": idempotency_key,
        # Explicit: confirmation is not an uploaded card.
        "insurance_card_uploaded": False,
    }


def apply_policy_context_to_case_dict(
    case: dict[str, Any],
    *,
    record: Mapping[str, Any],
    event_type: str,
    event_text: str,
    now_iso: str,
) -> dict[str, Any]:
    """Mutate a case dict in memory (caller persists). Idempotent by idempotency_key."""
    from services.fiqa_api.inbox_triage.case_store import (
        _claim_timeline_from_case,
        _claim_timeline_is_duplicate,
        build_claim_timeline_event,
    )
    from services.fiqa_api.inbox_triage.p20_missing_information import FACT_STATUS_CONFIRMED

    existing = case.get("policy_context") if isinstance(case.get("policy_context"), dict) else None
    idem = str(record.get("idempotency_key") or "").strip()
    if existing and idem and str(existing.get("idempotency_key") or "").strip() == idem:
        return {"outcome": "replayed", "case": case, "event_appended": False}

    # Already confirmed with same choice — treat as idempotent success without second event.
    if (
        existing
        and str(existing.get("status") or "") == "confirmed"
        and str(record.get("status") or "") == "confirmed"
        and str(existing.get("customer_choice") or "") == CHOICE_CORRECT
    ):
        return {"outcome": "already_confirmed", "case": case, "event_appended": False}

    case["policy_context"] = dict(record)

    # Presentation facts for broker — not an attachment.
    facts = case.get("known_facts") if isinstance(case.get("known_facts"), dict) else {}
    facts = dict(facts)
    if record.get("vehicle_summary"):
        facts["primary_vehicle_summary"] = record["vehicle_summary"]
    if record.get("policy_ref"):
        facts["policy_number"] = record["policy_ref"]
    if record.get("carrier_display"):
        facts["insurance_carrier"] = record["carrier_display"]
    case["known_facts"] = facts
    if record.get("policy_ref"):
        case["policy_number"] = record["policy_ref"]

    fact_records = case.get("fact_records") if isinstance(case.get("fact_records"), dict) else {}
    fact_records = dict(fact_records)
    if str(record.get("status") or "") == "confirmed":
        fact_records["policy_or_insurance_card"] = {
            "field_key": "policy_or_insurance_card",
            "status": FACT_STATUS_CONFIRMED,
            "value": FACT_VALUE_CONFIRMED,
            "previous_value": None,
            "reason": "customer_confirmed_existing_policy_context",
            "source": SOURCE_CUSTOMER_CONFIRMED,
        }
    else:
        # Keep missing / require upload — do not invent confirmed.
        current = fact_records.get("policy_or_insurance_card")
        if not isinstance(current, dict) or str(current.get("status") or "") == FACT_STATUS_CONFIRMED:
            fact_records["policy_or_insurance_card"] = {
                "field_key": "policy_or_insurance_card",
                "status": "missing",
                "value": None,
                "previous_value": None,
                "reason": str(record.get("upload_reason_zh") or "upload_required"),
                "source": "customer_policy_context_choice",
            }
    case["fact_records"] = fact_records

    timeline = _claim_timeline_from_case(case)
    event = build_claim_timeline_event(
        event_type=event_type,
        source_channel="mini_program",
        actor="customer",
        text=event_text,
        created_at=now_iso,
        metadata={
            "source": "policy_context_confirm",
            "decision": record.get("decision"),
            "customer_choice": record.get("customer_choice"),
            "policy_ref": record.get("policy_ref"),
            "vehicle_ref": record.get("vehicle_ref"),
            "insurance_card_uploaded": False,
            "command_id": record.get("command_id"),
            "idempotency_key": record.get("idempotency_key"),
        },
    )
    appended = False
    if not _claim_timeline_is_duplicate(timeline, event):
        # Also treat same event_type + idempotency as duplicate.
        for existing_ev in timeline:
            meta = existing_ev.get("metadata") if isinstance(existing_ev.get("metadata"), dict) else {}
            if (
                str(existing_ev.get("event_type") or "") == event_type
                and str(meta.get("idempotency_key") or "") == idem
                and idem
            ):
                break
        else:
            timeline.append(event)
            appended = True
    case["claim_timeline"] = timeline
    case["updated_at"] = now_iso
    return {"outcome": "accepted", "case": case, "event_appended": appended}


def confirm_policy_context_for_case(
    case_id: str,
    *,
    lookup: Mapping[str, Any] | None,
    customer_choice: str,
    command_id: str,
    idempotency_key: str,
    selected_vehicle_ref: str | None = None,
    selected_vehicle_summary: str | None = None,
) -> dict[str, Any]:
    """Load → decide → persist confirmation. Read/write via case_store mutation path."""
    from services.fiqa_api.inbox_triage.case_store import (
        _load_case_for_mutation,
        _persist_case_after_update,
        _require_case_storage_path,
        _utc_now_iso,
    )

    choice = normalize_customer_choice(customer_choice)
    if not choice:
        return {
            "outcome": "rejected",
            "error_code": "invalid_customer_choice",
            "case": None,
        }

    cid = str(case_id or "").strip()
    if not cid:
        return {"outcome": "case_not_found", "case": None, "event_appended": False}

    _require_case_storage_path()
    case = _load_case_for_mutation(cid)
    if case is None:
        return {"outcome": "case_not_found", "case": None, "event_appended": False}

    decision = decide_policy_context(
        lookup,
        selected_vehicle_ref=selected_vehicle_ref,
        selected_vehicle_summary=selected_vehicle_summary,
    )
    # Customer cannot force CONFIRM_EXISTING when decision forbids it.
    if choice == CHOICE_CORRECT and str(decision.get("decision") or "") != DECISION_CONFIRM_EXISTING:
        choice = CHOICE_UNCERTAIN
        decision = {
            **decision,
            "decision": decision.get("decision") or DECISION_REQUIRE_UPLOAD,
            "upload_reason_zh": decision.get("upload_reason_zh")
            or "当前资料不足以跳过保险卡，请上传保险卡。",
        }

    now = _utc_now_iso()
    record = build_policy_context_record(
        decision=decision,
        customer_choice=choice,
        command_id=str(command_id or "").strip(),
        idempotency_key=str(idempotency_key or "").strip(),
        confirmed_at=now,
    )
    applied = apply_policy_context_to_case_dict(
        case,
        record=record,
        event_type=_event_type_for_choice(choice),
        event_text=_timeline_text_for_choice(choice),
        now_iso=now,
    )
    updated = applied["case"]
    if applied["outcome"] in ("accepted",) and updated is not None:
        if not _persist_case_after_update(cid, updated):
            return {"outcome": "persist_failed", "case": None, "event_appended": False}
        try:
            from services.fiqa_api.inbox_triage.case_activity_events import (
                record_customer_first_action,
                safe_record,
            )

            safe_record(
                record_customer_first_action,
                cid,
                source_surface="mini_program",
                meta={"command_type": "policy_context_confirm"},
            )
        except Exception:
            pass
    return {
        "outcome": applied["outcome"],
        "case": updated,
        "event_appended": bool(applied.get("event_appended")),
        "policy_context": updated.get("policy_context") if isinstance(updated, dict) else None,
        "decision": decision.get("decision"),
    }


def lookup_from_session_overlay(session_id: str | None) -> dict[str, Any] | None:
    """Best-effort Cap 01 lookup for demo-invite / mock overlay sessions."""
    try:
        from services.fiqa_api.inbox_triage.customer_lookup.facade import (
            lookup_customer,
            lookup_demo_invite_fixture,
        )
        from services.fiqa_api.inbox_triage.demo_invite import (
            get_approved_scenario,
            peek_session_overlay,
        )

        overlay = peek_session_overlay(session_id)
        if overlay:
            entry = get_approved_scenario(str(overlay.get("scenario_id") or ""))
            if entry:
                return lookup_demo_invite_fixture(entry["mock_person_link_key"])
        return lookup_customer(None)  # flag-gated; typically FALLBACK
    except Exception:
        return None
