"""
Unified Intake case store.

Lightweight local JSON persistence for demo-safe case history:
- save triage result
- list recent cases
- update a simple status
- message-level history (case_messages)
- explicit workflow state
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

CASE_STATUS_VALUES = ("new", "reviewing", "waiting_client", "waiting_customer", "agent_followup", "done", "closed")
CASE_WAITING_ON_VALUES = ("none", "client", "broker", "carrier", "underwriting")
MAX_STORED_CASES = 200
MAX_CASE_NOTES = 20
MAX_CASE_ACTIVITY = 40
MAX_NEXT_CONTACT_BY_LENGTH = 80
MAX_CUSTOMER_NAME_LENGTH = 120
MAX_CUSTOMER_PHONE_LENGTH = 40
MAX_CUSTOMER_EMAIL_LENGTH = 120
MAX_POLICY_NUMBER_LENGTH = 60
MAX_CONTACT_NOTE_LENGTH = 200

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STORE_PATH = REPO_ROOT / "data" / "unified_intake_cases.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _store_path() -> Path:
    raw_path = (os.getenv("UNIFIED_INTAKE_CASES_PATH") or "").strip()
    if not raw_path:
        return DEFAULT_STORE_PATH
    path = Path(raw_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def _validate_status(status: str) -> str:
    normalized = (status or "").strip().lower()
    if normalized not in CASE_STATUS_VALUES:
        raise ValueError(f"invalid status '{status}'")
    return normalized


def _validate_waiting_on(waiting_on: str) -> str:
    normalized = (waiting_on or "none").strip().lower() or "none"
    if normalized not in CASE_WAITING_ON_VALUES:
        raise ValueError(f"invalid waiting_on '{waiting_on}'")
    return normalized


def _normalize_next_contact_by(value: Any) -> str:
    text = str(value or "").strip()
    lowered = text.lower()
    for marker in ("undefined", "null"):
        while lowered.startswith(marker):
            text = text[len(marker):].strip(" -:;,")
            lowered = text.lower()
    text = " ".join(text.split())
    if text.lower() in {"undefined", "null"}:
        return ""
    if len(text) > MAX_NEXT_CONTACT_BY_LENGTH:
        raise ValueError(f"next_contact_by must be <= {MAX_NEXT_CONTACT_BY_LENGTH} characters")
    return text


def _preview_text(value: str, max_length: int = 96) -> str:
    text = " ".join((value or "").strip().split())
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 1]}..."


def _humanize_status(status: str) -> str:
    return (status or "new").replace("_", " ")


def _humanize_waiting_on(waiting_on: str) -> str:
    return (waiting_on or "none").replace("_", " ")


def _parse_source_to_messages(source_text: str, base_timestamp: str | None = None) -> list[dict[str, Any]]:
    """
    Parse source_text ([客户]/[系统] format) into case_messages.
    Used for migration and initial save.
    """
    raw = (source_text or "").strip()
    ts = base_timestamp or _utc_now_iso()
    if not raw:
        return []
    if "[客户]" not in raw and "[系统]" not in raw:
        return [
            {
                "message_id": f"msg_{uuid4().hex[:12]}",
                "role": "customer",
                "text": raw,
                "created_at": ts,
                "sequence": 1,
            }
        ]
    messages: list[dict[str, Any]] = []
    pattern = re.compile(r"\[(客户|系统)\]\s*", re.IGNORECASE)
    parts = pattern.split(raw)
    if len(parts) < 2:
        return [
            {
                "message_id": f"msg_{uuid4().hex[:12]}",
                "role": "customer",
                "text": raw,
                "created_at": ts,
                "sequence": 1,
            }
        ]
    seq = 1
    i = 1
    while i < len(parts) - 1:
        role_label = (parts[i] or "").strip()
        content = (parts[i + 1] or "").split("[")[0].strip() if i + 1 < len(parts) else ""
        role = "customer" if role_label == "客户" else "system"
        if content:
            messages.append({
                "message_id": f"msg_{uuid4().hex[:12]}",
                "role": role,
                "text": content,
                "created_at": ts,
                "sequence": seq,
            })
            seq += 1
        i += 2
    if not messages:
        return [
            {
                "message_id": f"msg_{uuid4().hex[:12]}",
                "role": "customer",
                "text": raw,
                "created_at": ts,
                "sequence": 1,
            }
        ]
    return messages


def _build_source_from_messages(messages: list[dict[str, Any]]) -> str:
    """Build source_text from case_messages for triage/display."""
    if not messages:
        return ""
    sorted_msgs = sorted(messages, key=lambda m: (m.get("sequence", 0), m.get("created_at", "")))
    parts: list[str] = []
    for m in sorted_msgs:
        role = (m.get("role") or "customer").strip().lower()
        label = "客户" if role == "customer" else "系统"
        text = (m.get("text") or "").strip()
        if text:
            parts.append(f"[{label}] {text}")
    return "\n\n".join(parts)


def _normalize_message(msg: Any) -> dict[str, Any] | None:
    """Normalize a case message for storage."""
    if not isinstance(msg, dict):
        return None
    role = (str(msg.get("role") or "customer").strip().lower())
    if role not in ("customer", "system"):
        role = "customer"
    text = str(msg.get("text") or "").strip()
    if not text:
        return None
    return {
        "message_id": str(msg.get("message_id") or f"msg_{uuid4().hex[:12]}"),
        "role": role,
        "text": text,
        "created_at": str(msg.get("created_at") or _utc_now_iso()).strip(),
        "sequence": max(1, int(msg.get("sequence") or 1)),
    }


def _build_activity_entry(activity_type: str, message: str) -> dict[str, str]:
    return {
        "activity_id": f"act_{uuid4().hex[:12]}",
        "activity_type": activity_type,
        "message": message.strip(),
        "created_at": _utc_now_iso(),
    }


def _normalize_note(note: Any) -> dict[str, str] | None:
    if not isinstance(note, dict):
        return None
    body = str(note.get("body") or "").strip()
    created_at = str(note.get("created_at") or "").strip()
    if not body or not created_at:
        return None
    note_id = str(note.get("note_id") or f"note_{uuid4().hex[:12]}")
    return {
        "note_id": note_id,
        "body": body,
        "created_at": created_at,
    }


def _normalize_activity(activity: Any) -> dict[str, str] | None:
    if not isinstance(activity, dict):
        return None
    activity_type = str(activity.get("activity_type") or "").strip() or "case_updated"
    message = str(activity.get("message") or "").strip()
    created_at = str(activity.get("created_at") or "").strip()
    if not message or not created_at:
        return None
    activity_id = str(activity.get("activity_id") or f"act_{uuid4().hex[:12]}")
    return {
        "activity_id": activity_id,
        "activity_type": activity_type,
        "message": message,
        "created_at": created_at,
    }


def _normalize_case(case: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(case)
    notes = normalized.get("case_notes")
    activity = normalized.get("case_activity")
    normalized_notes: list[dict[str, str]] = []
    if isinstance(notes, list):
        for note in notes:
            normalized_note = _normalize_note(note)
            if normalized_note is not None:
                normalized_notes.append(normalized_note)
    normalized_activity: list[dict[str, str]] = []
    if isinstance(activity, list):
        for item in activity:
            normalized_item = _normalize_activity(item)
            if normalized_item is not None:
                normalized_activity.append(normalized_item)
    normalized["case_notes"] = normalized_notes[:MAX_CASE_NOTES]
    normalized["case_activity"] = normalized_activity[:MAX_CASE_ACTIVITY]
    normalized["waiting_on"] = _validate_waiting_on(str(normalized.get("waiting_on") or "none"))
    normalized["next_contact_by"] = _normalize_next_contact_by(normalized.get("next_contact_by") or "")

    # Customer linkage (Lightweight Production Case Record)
    for key in ("customer_name", "customer_phone", "customer_email", "policy_number", "contact_note"):
        if key not in normalized or normalized[key] is None:
            normalized[key] = (normalized.get(key) or "").strip() if isinstance(normalized.get(key), str) else ""

    # Message-level history: ensure case_messages exists; lazy migration from source_text
    existing_messages = normalized.get("case_messages")
    if isinstance(existing_messages, list) and existing_messages:
        normalized_messages: list[dict[str, Any]] = []
        for m in existing_messages:
            nm = _normalize_message(m)
            if nm is not None:
                normalized_messages.append(nm)
        # Re-sequence if needed
        def _seq(m):
            return (m.get("sequence") or 0, m.get("created_at") or "")
        for i, m in enumerate(sorted(normalized_messages, key=_seq)):
            m["sequence"] = i + 1
        normalized["case_messages"] = normalized_messages
    else:
        # Lazy migration: parse source_text into case_messages
        source = (normalized.get("source_text") or "").strip()
        if source:
            normalized["case_messages"] = _parse_source_to_messages(source, normalized.get("created_at"))
        else:
            normalized["case_messages"] = []

    # Client Identity Persistence: preserve client_id when present (no migration for legacy)
    if "client_id" in normalized and normalized.get("client_id"):
        normalized["client_id"] = str(normalized["client_id"]).strip()

    # Phase 2: lifecycle_status — preserve stored value; derive only when missing (legacy migration)
    # Minimal Production Backbone: stored value is source of truth; avoid overwriting on every read
    existing_lc = (normalized.get("lifecycle_status") or "").strip()
    if existing_lc in ("collecting", "handoff_pending", "handed_off", "office_followup"):
        normalized["lifecycle_status"] = existing_lc
    else:
        status = (normalized.get("case_status") or "new").strip().lower()
        normalized["lifecycle_status"] = "handed_off" if status == "new" else "office_followup"

    return normalized


def _validate_triage_result(result: dict[str, Any]) -> dict[str, Any]:
    required = (
        "issue_category",
        "urgency",
        "broker_next_step",
        "client_prep",
        "client_reply_draft",
        "manual_followup_needed",
    )
    validated: dict[str, Any] = {}
    for field in required:
        if field not in result:
            raise ValueError(f"missing triage field '{field}'")
        validated[field] = result[field]
    if not isinstance(validated["manual_followup_needed"], bool):
        raise ValueError("manual_followup_needed must be boolean")
    return validated


def _empty_payload() -> dict[str, list[dict[str, Any]]]:
    return {"cases": []}


def _read_payload() -> dict[str, list[dict[str, Any]]]:
    path = _store_path()
    if not path.exists():
        return _empty_payload()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return _empty_payload()
    cases = payload.get("cases")
    if not isinstance(cases, list):
        return _empty_payload()
    return {"cases": [_normalize_case(case) for case in cases if isinstance(case, dict)]}


def _write_payload(payload: dict[str, list[dict[str, Any]]]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def _sort_recent(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(cases, key=lambda case: (case.get("updated_at") or "", case.get("created_at") or ""), reverse=True)


def list_recent_cases(limit: int = 8) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit or 8), 50))
    payload = _read_payload()
    return _sort_recent(payload["cases"])[:safe_limit]


def get_case_by_id(case_id: str) -> dict[str, Any] | None:
    """Return a case by id, or None if not found."""
    payload = _read_payload()
    for case in payload["cases"]:
        if case.get("case_id") == case_id:
            return _normalize_case(case)
    return None


def save_case(
    source_text: str,
    triage_result: dict[str, Any],
    status: str = "new",
    *,
    origin_session_id: str | None = None,
    client_id: str | None = None,
) -> dict[str, Any]:
    normalized_status = _validate_status(status)
    normalized_result = _validate_triage_result(triage_result)
    timestamp = _utc_now_iso()
    source = (source_text or "").strip()
    case_messages = _parse_source_to_messages(source, timestamp)

    case = {
        "case_id": f"case_{uuid4().hex[:12]}",
        "case_status": normalized_status,
        "created_at": timestamp,
        "updated_at": timestamp,
        "source_text": source,
        "case_messages": case_messages,
        "waiting_on": "none",
        "next_contact_by": "",
        "customer_name": "",
        "customer_phone": "",
        "customer_email": "",
        "policy_number": "",
        "contact_note": "",
        "case_notes": [],
        "case_activity": [
            _build_activity_entry(
                "case_created",
                f"Case created with status {_humanize_status(normalized_status)}.",
            )
        ],
        **normalized_result,
    }
    if (summary := (triage_result.get("conversation_summary") or "").strip()):
        case["conversation_summary"] = summary
    if (collected := triage_result.get("collected_fields")) is not None and isinstance(collected, list):
        case["collected_fields"] = [str(x) for x in collected]
    if (still_needed := triage_result.get("still_needed_fields")) is not None and isinstance(still_needed, list):
        case["still_needed_fields"] = [str(x) for x in still_needed]
    # Explicit workflow state (Lightweight Production Case Record)
    case["handoff_ready"] = bool(triage_result.get("handoff_ready", True))
    case["case_creation_suggested"] = bool(triage_result.get("case_creation_suggested", False))
    case["human_confirmation_required"] = bool(triage_result.get("human_confirmation_required", False))
    if (hf := triage_result.get("human_confirmation_fields")) is not None and isinstance(hf, list):
        case["human_confirmation_fields"] = [str(x) for x in hf]
    else:
        case["human_confirmation_fields"] = []
    if (cs := (triage_result.get("collection_stage") or "").strip()):
        case["collection_stage"] = cs
    if (ft := (triage_result.get("follow_up_type") or "").strip()):
        case["follow_up_type"] = ft
    # Phase 2: lifecycle_status for new case
    case["lifecycle_status"] = "handed_off"
    # Minimal Production Backbone: optional traceability from case to pre-handoff session
    if origin_session_id and (sid := str(origin_session_id or "").strip()):
        case["origin_session_id"] = sid
    if (nbq := (triage_result.get("next_best_question") or "").strip()):
        case["next_best_question"] = nbq
    # Client Identity Persistence: store client_id for append/reopen lifecycle
    if client_id and (cid := str(client_id or "").strip()):
        case["client_id"] = cid

    payload = _read_payload()
    cases = [case, *payload["cases"]]
    payload["cases"] = _sort_recent(cases)[:MAX_STORED_CASES]
    _write_payload(payload)
    return case


def update_case_follow_up(case_id: str, waiting_on: str, next_contact_by: str) -> dict[str, Any] | None:
    normalized_waiting_on = _validate_waiting_on(waiting_on)
    normalized_next_contact_by = _normalize_next_contact_by(next_contact_by)
    payload = _read_payload()
    updated_case: dict[str, Any] | None = None
    for index, case in enumerate(payload["cases"]):
        if case.get("case_id") != case_id:
            continue
        normalized_case = _normalize_case(case)
        previous_waiting_on = normalized_case.get("waiting_on") or "none"
        previous_next_contact_by = normalized_case.get("next_contact_by") or ""
        if (
            previous_waiting_on == normalized_waiting_on
            and previous_next_contact_by == normalized_next_contact_by
        ):
            updated_case = normalized_case
            payload["cases"][index] = normalized_case
            break
        normalized_case["waiting_on"] = normalized_waiting_on
        normalized_case["next_contact_by"] = normalized_next_contact_by
        normalized_case["updated_at"] = _utc_now_iso()
        if normalized_waiting_on == "none" and not normalized_next_contact_by:
            message = "Follow-up target cleared."
        else:
            parts: list[str] = []
            if normalized_waiting_on != "none":
                parts.append(f"waiting on {_humanize_waiting_on(normalized_waiting_on)}")
            if normalized_next_contact_by:
                parts.append(f"next contact by {normalized_next_contact_by}")
            message = f"Follow-up updated: {'; '.join(parts)}."
        normalized_case["case_activity"] = [
            _build_activity_entry("follow_up_updated", message),
            *normalized_case.get("case_activity", []),
        ][:MAX_CASE_ACTIVITY]
        payload["cases"][index] = normalized_case
        updated_case = normalized_case
        break
    if updated_case is None:
        return None
    payload["cases"] = _sort_recent(payload["cases"])
    _write_payload(payload)
    return updated_case


def _truncate(value: str, max_len: int) -> str:
    t = (value or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1]


def update_case_customer(
    case_id: str,
    *,
    customer_name: str | None = None,
    customer_phone: str | None = None,
    customer_email: str | None = None,
    policy_number: str | None = None,
    contact_note: str | None = None,
) -> dict[str, Any] | None:
    """
    Update lightweight customer linkage fields on a case.
    Pass only the fields to update; others are left unchanged.
    """
    payload = _read_payload()
    updated_case: dict[str, Any] | None = None
    for index, case in enumerate(payload["cases"]):
        if case.get("case_id") != case_id:
            continue
        normalized_case = _normalize_case(case)
        changed = False
        if customer_name is not None:
            v = _truncate(customer_name, MAX_CUSTOMER_NAME_LENGTH)
            if normalized_case.get("customer_name") != v:
                normalized_case["customer_name"] = v
                changed = True
        if customer_phone is not None:
            v = _truncate(customer_phone, MAX_CUSTOMER_PHONE_LENGTH)
            if normalized_case.get("customer_phone") != v:
                normalized_case["customer_phone"] = v
                changed = True
        if customer_email is not None:
            v = _truncate(customer_email, MAX_CUSTOMER_EMAIL_LENGTH)
            if normalized_case.get("customer_email") != v:
                normalized_case["customer_email"] = v
                changed = True
        if policy_number is not None:
            v = _truncate(policy_number, MAX_POLICY_NUMBER_LENGTH)
            if normalized_case.get("policy_number") != v:
                normalized_case["policy_number"] = v
                changed = True
        if contact_note is not None:
            v = _truncate(contact_note, MAX_CONTACT_NOTE_LENGTH)
            if normalized_case.get("contact_note") != v:
                normalized_case["contact_note"] = v
                changed = True
        if changed:
            normalized_case["updated_at"] = _utc_now_iso()
            normalized_case["case_activity"] = [
                _build_activity_entry("customer_updated", "Customer linkage updated."),
                *normalized_case.get("case_activity", []),
            ][:MAX_CASE_ACTIVITY]
        payload["cases"][index] = normalized_case
        updated_case = normalized_case
        break
    if updated_case is None:
        return None
    payload["cases"] = _sort_recent(payload["cases"])
    _write_payload(payload)
    return updated_case


# Terminal status: no transitions out (STATE_WORKFLOW_BACKBONE_SPRINT)
TERMINAL_STATUS = ("closed",)


def update_case_status(case_id: str, status: str) -> dict[str, Any] | None:
    normalized_status = _validate_status(status)
    payload = _read_payload()
    updated_case: dict[str, Any] | None = None
    for index, case in enumerate(payload["cases"]):
        if case.get("case_id") != case_id:
            continue
        normalized_case = _normalize_case(case)
        previous_status = normalized_case.get("case_status") or "new"
        # Guardrail: closed is terminal; reject transition from closed
        if previous_status in TERMINAL_STATUS and previous_status != normalized_status:
            raise ValueError(f"Cannot change status from '{previous_status}' (terminal)")
        if previous_status == normalized_status:
            updated_case = normalized_case
            payload["cases"][index] = normalized_case
            break
        normalized_case["case_status"] = normalized_status
        normalized_case["updated_at"] = _utc_now_iso()
        normalized_case["case_activity"] = [
            _build_activity_entry(
                "status_changed",
                f"Status changed from {_humanize_status(previous_status)} to {_humanize_status(normalized_status)}.",
            ),
            *normalized_case.get("case_activity", []),
        ][:MAX_CASE_ACTIVITY]
        payload["cases"][index] = normalized_case
        updated_case = normalized_case
        break
    if updated_case is None:
        return None
    payload["cases"] = _sort_recent(payload["cases"])
    _write_payload(payload)
    return updated_case


def add_case_note(case_id: str, note_text: str) -> dict[str, Any] | None:
    body = (note_text or "").strip()
    if not body:
        raise ValueError("note cannot be empty")
    payload = _read_payload()
    updated_case: dict[str, Any] | None = None
    for index, case in enumerate(payload["cases"]):
        if case.get("case_id") != case_id:
            continue
        normalized_case = _normalize_case(case)
        timestamp = _utc_now_iso()
        note = {
            "note_id": f"note_{uuid4().hex[:12]}",
            "body": body,
            "created_at": timestamp,
        }
        normalized_case["case_notes"] = [note, *normalized_case.get("case_notes", [])][:MAX_CASE_NOTES]
        normalized_case["case_activity"] = [
            _build_activity_entry("note_added", f"Broker note added: {_preview_text(body)}"),
            *normalized_case.get("case_activity", []),
        ][:MAX_CASE_ACTIVITY]
        normalized_case["updated_at"] = timestamp
        payload["cases"][index] = normalized_case
        updated_case = normalized_case
        break
    if updated_case is None:
        return None
    payload["cases"] = _sort_recent(payload["cases"])
    _write_payload(payload)
    return updated_case


def append_follow_up_message(
    case_id: str,
    new_message_text: str,
    triage_result: dict[str, Any],
    *,
    client_id: str | None = None,
) -> dict[str, Any] | None:
    """
    Append a new customer follow-up message to an existing case.
    Adds message-level records to case_messages, updates source_text, and persists workflow state.
    Preserves: case_id, case_status, waiting_on, next_contact_by, case_notes.
    """
    new_msg = (new_message_text or "").strip()
    if not new_msg:
        raise ValueError("new_message cannot be empty")

    validated = _validate_triage_result(triage_result)
    system_reply = (triage_result.get("client_reply_draft") or "").strip()
    timestamp = _utc_now_iso()

    payload = _read_payload()
    updated_case: dict[str, Any] | None = None
    for index, case in enumerate(payload["cases"]):
        if case.get("case_id") != case_id:
            continue
        normalized_case = _normalize_case(case)
        messages = list(normalized_case.get("case_messages") or [])
        next_seq = max((m.get("sequence") or 0 for m in messages), default=0) + 1

        # Add customer message
        messages.append({
            "message_id": f"msg_{uuid4().hex[:12]}",
            "role": "customer",
            "text": new_msg,
            "created_at": timestamp,
            "sequence": next_seq,
        })
        next_seq += 1

        # Add system reply when present
        if system_reply:
            messages.append({
                "message_id": f"msg_{uuid4().hex[:12]}",
                "role": "system",
                "text": system_reply,
                "created_at": timestamp,
                "sequence": next_seq,
            })

        normalized_case["case_messages"] = messages
        normalized_case["source_text"] = _build_source_from_messages(messages)
        normalized_case["updated_at"] = timestamp
        normalized_case["issue_category"] = validated["issue_category"]
        normalized_case["urgency"] = validated["urgency"]
        normalized_case["broker_next_step"] = validated["broker_next_step"]
        normalized_case["client_prep"] = validated["client_prep"]
        normalized_case["client_reply_draft"] = validated["client_reply_draft"]
        normalized_case["manual_followup_needed"] = validated["manual_followup_needed"]

        if (summary := (triage_result.get("conversation_summary") or "").strip()):
            normalized_case["conversation_summary"] = summary
        if (collected := triage_result.get("collected_fields")) is not None and isinstance(collected, list):
            normalized_case["collected_fields"] = [str(x) for x in collected]
        if (still_needed := triage_result.get("still_needed_fields")) is not None and isinstance(still_needed, list):
            normalized_case["still_needed_fields"] = [str(x) for x in still_needed]

        # Explicit workflow state
        normalized_case["handoff_ready"] = bool(triage_result.get("handoff_ready", True))
        normalized_case["case_creation_suggested"] = bool(triage_result.get("case_creation_suggested", False))
        normalized_case["human_confirmation_required"] = bool(triage_result.get("human_confirmation_required", False))
        if (hf := triage_result.get("human_confirmation_fields")) is not None and isinstance(hf, list):
            normalized_case["human_confirmation_fields"] = [str(x) for x in hf]
        else:
            normalized_case["human_confirmation_fields"] = normalized_case.get("human_confirmation_fields") or []
        if (cs := (triage_result.get("collection_stage") or "").strip()):
            normalized_case["collection_stage"] = cs
        if (ft := (triage_result.get("follow_up_type") or "").strip()):
            normalized_case["follow_up_type"] = ft
        # Minimal Production Backbone: append = office follow-up flow
        normalized_case["lifecycle_status"] = "office_followup"
        # Client Identity Persistence: backfill client_id for legacy cases when provided
        if not normalized_case.get("client_id") and client_id and (cid := str(client_id or "").strip()):
            normalized_case["client_id"] = cid

        normalized_case["case_activity"] = [
            _build_activity_entry("follow_up_added", f"Customer follow-up added: {_preview_text(new_msg, 64)}"),
            *normalized_case.get("case_activity", []),
        ][:MAX_CASE_ACTIVITY]
        payload["cases"][index] = normalized_case
        updated_case = normalized_case
        break
    if updated_case is None:
        return None
    payload["cases"] = _sort_recent(payload["cases"])
    _write_payload(payload)
    return updated_case
