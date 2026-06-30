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
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

from services.fiqa_api.inbox_triage.config_loader import get_case_message_labels
from services.fiqa_api.db.service_record_settings import is_production_mode

CASE_STATUS_VALUES = ("new", "reviewing", "waiting_client", "waiting_customer", "agent_followup", "done", "closed")
CASE_WAITING_ON_VALUES = ("none", "client", "broker", "carrier", "underwriting")
MAX_STORED_CASES = 200
MAX_CASE_NOTES = 20
MAX_CASE_ACTIVITY = 40
MAX_EVIDENCE_EVENTS = 50
MAX_NEXT_CONTACT_BY_LENGTH = 80
MAX_CUSTOMER_NAME_LENGTH = 120
MAX_CUSTOMER_PHONE_LENGTH = 40
MAX_CUSTOMER_EMAIL_LENGTH = 120
MAX_POLICY_NUMBER_LENGTH = 60
MAX_CONTACT_NOTE_LENGTH = 200
MAX_ATTACHMENTS_PER_CASE = 10
MAX_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_ATTACHMENT_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf")

logger = logging.getLogger(__name__)

# Stage-1 optional light identity (nullable; not auth) — LIGHT_IDENTITY_ENTRY_STUB
_IDENTITY_BINDING_STATES = frozenset({"unbound", "prompted", "deferred", "linked"})
_PERSON_LINK_SOURCES = frozenset({"wechat", "phone", "email"})
_MAX_PERSON_LINK_KEY_LEN = 256

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STORE_PATH = REPO_ROOT / "data" / "unified_intake_cases.json"
DEFAULT_ATTACHMENTS_DIR = REPO_ROOT / "data" / "unified_intake_attachments"


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
    Used for migration and initial save. Bracket labels come from
    :func:`get_case_message_labels` (optional configs/common/case_message_labels.json).
    """
    labels = get_case_message_labels()
    cust = labels.get("customer") or "客户"
    sys_l = labels.get("system") or "系统"
    raw = (source_text or "").strip()
    ts = base_timestamp or _utc_now_iso()
    if not raw:
        return []
    if f"[{cust}]" not in raw and f"[{sys_l}]" not in raw:
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
    pattern = re.compile(
        rf"\[({re.escape(cust)}|{re.escape(sys_l)})\]\s*",
        re.IGNORECASE,
    )
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
        role = "customer" if role_label == cust else "system"
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
    """Build source_text from case_messages for triage/display (labels from config)."""
    if not messages:
        return ""
    labels = get_case_message_labels()
    cust_l = labels.get("customer") or "客户"
    sys_l = labels.get("system") or "系统"
    sorted_msgs = sorted(messages, key=lambda m: (m.get("sequence", 0), m.get("created_at", "")))
    parts: list[str] = []
    for m in sorted_msgs:
        role = (m.get("role") or "customer").strip().lower()
        label = cust_l if role == "customer" else sys_l
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

    # Org hint persistence: X-Org-Id client assertion at case creation (not tenant authority)
    if "asserted_org_id" in normalized and normalized.get("asserted_org_id"):
        normalized["asserted_org_id"] = str(normalized["asserted_org_id"]).strip()[:256]
    elif "asserted_org_id" in normalized:
        normalized.pop("asserted_org_id", None)

    # Phase 2: lifecycle_status — preserve stored value; derive only when missing (legacy migration)
    # Minimal Production Backbone: stored value is source of truth; avoid overwriting on every read
    existing_lc = (normalized.get("lifecycle_status") or "").strip()
    if existing_lc in ("collecting", "handoff_pending", "handed_off", "office_followup"):
        normalized["lifecycle_status"] = existing_lc
    else:
        status = (normalized.get("case_status") or "new").strip().lower()
        normalized["lifecycle_status"] = "handed_off" if status == "new" else "office_followup"

    # ADD_CAR_ATTACHMENT_READY_LITE: preserve case_attachments
    if "case_attachments" not in normalized or not isinstance(normalized.get("case_attachments"), list):
        normalized["case_attachments"] = []
    # V6 OCR signals (optional dict from attachment pipeline)
    if "v6_ocr_signals" in normalized and not isinstance(normalized.get("v6_ocr_signals"), dict):
        normalized["v6_ocr_signals"] = {}

    # Formal submit observability: backfill for legacy JSON before formal_submitted_at existed.
    # Never backfill collecting/handoff_pending drafts — would falsely mark Saved as Submitted.
    fsa = str(normalized.get("formal_submitted_at") or "").strip()
    lc_for_backfill = str(normalized.get("lifecycle_status") or "").strip()
    if not fsa and lc_for_backfill not in ("collecting", "handoff_pending"):
        ca = str(normalized.get("created_at") or "").strip()
        if ca:
            normalized["formal_submitted_at"] = ca

    # Office workbench: lightweight test/archive flags (JSON-first; soft-hide only by default)
    normalized["workbench_test"] = bool(normalized.get("workbench_test"))
    normalized["workbench_archived"] = bool(normalized.get("workbench_archived"))
    # Stage-1 boundary + lane detail (nullable vehicle_key for Add-Car).
    if "service_type" not in normalized:
        normalized["service_type"] = ""
    if "vehicle_key" not in normalized:
        normalized["vehicle_key"] = None
    if "additional_vehicle_mentioned" not in normalized:
        normalized["additional_vehicle_mentioned"] = None
    if "primary_vehicle_summary" not in normalized:
        normalized["primary_vehicle_summary"] = None
    if "additional_vehicle_count_hint" not in normalized:
        normalized["additional_vehicle_count_hint"] = None

    # Optional light identity (nullable; additive JSON fields)
    for ik in ("identity_binding_state", "person_link_key", "person_link_source", "person_link_confidence"):
        if ik not in normalized:
            normalized[ik] = None

    # P17 Phase 1 — lightweight evidence log (ADR-005; no Submission table)
    if "evidence_events" not in normalized or not isinstance(normalized.get("evidence_events"), list):
        normalized["evidence_events"] = []
    if "merge_review_required" not in normalized:
        normalized["merge_review_required"] = bool(normalized.get("merge_review_required"))
    if "conflict_state" not in normalized:
        normalized["conflict_state"] = str(normalized.get("conflict_state") or "none").strip() or "none"

    return normalized


def _normalize_add_car_turn_intent_payload(raw: Any) -> dict[str, Any] | None:
    """Bounded API/case copy of Add-Car intent (Truth→Intent observability)."""
    if not isinstance(raw, dict):
        return None
    fam = str(raw.get("intent_family") or "").strip()
    hbk = str(raw.get("handoff_base_key") or "").strip()
    if not fam or not hbk:
        return None
    notes = raw.get("truth_notes")
    out_notes: list[str] = []
    if isinstance(notes, list):
        out_notes = [str(x) for x in notes if str(x).strip()]
    out: dict[str, Any] = {
        "intent_family": fam,
        "handoff_base_key": hbk,
        "truth_notes": out_notes,
    }
    psk = str(raw.get("phrase_storage_key") or "").strip()
    if psk:
        out["phrase_storage_key"] = psk
    return out


def merge_light_identity_from_client_payload(
    *,
    identity_binding_state: str | None,
    person_link_key: str | None,
    person_link_source: str | None,
    person_link_confidence: float | None,
) -> dict[str, Any]:
    """
    Validate optional identity fields from API request. Returns only keys to merge into triage result.
    All values remain optional; invalid inputs are dropped (no exception).
    """
    out: dict[str, Any] = {}
    if identity_binding_state is not None:
        s = str(identity_binding_state).strip().lower()
        if s in _IDENTITY_BINDING_STATES:
            out["identity_binding_state"] = s
    if person_link_key is not None:
        pk = str(person_link_key).strip()
        if len(pk) > _MAX_PERSON_LINK_KEY_LEN:
            pk = pk[: _MAX_PERSON_LINK_KEY_LEN - 1]
        out["person_link_key"] = pk if pk else None
    if person_link_source is not None:
        src = str(person_link_source).strip().lower()
        if src in _PERSON_LINK_SOURCES:
            out["person_link_source"] = src
        elif src == "":
            out["person_link_source"] = None
    if person_link_confidence is not None:
        try:
            c = float(person_link_confidence)
            if 0.0 <= c <= 1.0:
                out["person_link_confidence"] = c
        except (TypeError, ValueError):
            pass
    return out


def _apply_identity_fields_from_triage_result(case: dict[str, Any], triage_result: dict[str, Any]) -> None:
    """Copy optional identity keys from triage result onto persisted case (additive, nullable)."""
    if "identity_binding_state" in triage_result:
        raw = triage_result.get("identity_binding_state")
        if raw is None:
            case["identity_binding_state"] = None
        else:
            s = str(raw).strip().lower()
            case["identity_binding_state"] = s if s in _IDENTITY_BINDING_STATES else None
    if "person_link_key" in triage_result:
        raw = triage_result.get("person_link_key")
        if raw is None:
            case["person_link_key"] = None
        else:
            pk = str(raw).strip()
            if len(pk) > _MAX_PERSON_LINK_KEY_LEN:
                pk = pk[: _MAX_PERSON_LINK_KEY_LEN - 1]
            case["person_link_key"] = pk if pk else None
    if "person_link_source" in triage_result:
        raw = triage_result.get("person_link_source")
        if raw is None:
            case["person_link_source"] = None
        else:
            src = str(raw).strip().lower()
            case["person_link_source"] = src if src in _PERSON_LINK_SOURCES else None
    if "person_link_confidence" in triage_result:
        raw = triage_result.get("person_link_confidence")
        if raw is None:
            case["person_link_confidence"] = None
        else:
            try:
                c = float(raw)
                case["person_link_confidence"] = c if 0.0 <= c <= 1.0 else None
            except (TypeError, ValueError):
                case["person_link_confidence"] = None


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
    if ac := _normalize_add_car_turn_intent_payload(result.get("add_car_turn_intent")):
        validated["add_car_turn_intent"] = ac
    return validated


def _empty_payload() -> dict[str, list[dict[str, Any]]]:
    return {"cases": []}


def _read_payload() -> dict[str, list[dict[str, Any]]]:
    if is_production_mode():
        logger.warning("JSON path should not be used in production")
        return _empty_payload()
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
    if is_production_mode():
        logger.warning("JSON path should not be used in production")
        return
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def _load_case_for_mutation(case_id: str) -> dict[str, Any] | None:
    """
    Load a case dict for in-place mutation (append, customer update, etc.).

    Uses the same read facade as HTTP/triage (`case_truth_repository.get_case_for_read`)
    so Postgres-primary / dual-write / JSON fallback rules cannot diverge from list/get/append.
    """
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read

    cid = (case_id or "").strip()
    if not cid:
        return None
    return get_case_for_read(cid)


def _replace_case_in_json_store(case_id: str, updated_case: dict[str, Any]) -> bool:
    """Replace one case in the JSON file. Returns False if case_id is missing."""
    payload = _read_payload()
    replaced = False
    for index, case in enumerate(payload["cases"]):
        if case.get("case_id") == case_id:
            payload["cases"][index] = updated_case
            replaced = True
            break
    if not replaced:
        return False
    payload["cases"] = _sort_recent(payload["cases"])
    _write_payload(payload)
    return True


def _require_case_storage_path() -> None:
    """Pilot must not disable both JSON and DB primary writes."""
    from services.fiqa_api.db.service_record_settings import (
        db_primary_writes_enabled,
        json_case_writes_enabled,
    )

    if not json_case_writes_enabled() and not db_primary_writes_enabled():
        raise RuntimeError(
            "Case persistence misconfigured: JSON case writes are off but "
            "UNIFIED_INTAKE_DB_PRIMARY_WRITES is not enabled. Set DATABASE_URL / "
            "SERVICE_RECORD_DATABASE_URL and UNIFIED_INTAKE_DB_PRIMARY_WRITES=1, "
            "or re-enable JSON (unset UNIFIED_INTAKE_JSON_CASE_WRITES)."
        )


def _persist_case_after_update(case_id: str, updated_case: dict[str, Any]) -> bool:
    """
    Write updated case to Postgres (when DB-primary writes) and/or JSON file.
    Returns False if JSON was expected but the case_id was not found in the JSON store.
    """
    from services.fiqa_api.db.service_record_settings import (
        db_primary_writes_enabled,
        json_case_writes_enabled,
    )

    _require_case_storage_path()
    if db_primary_writes_enabled():
        from services.fiqa_api.db.service_record_repository import persist_case_append

        persist_case_append(updated_case)
    if json_case_writes_enabled():
        if not _replace_case_in_json_store(case_id, updated_case):
            return False
    try:
        from services.fiqa_api.db.dual_write import maybe_dual_write_case_append

        maybe_dual_write_case_append(updated_case)
    except Exception:
        pass
    return True


def _sort_recent(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(cases, key=lambda case: (case.get("updated_at") or "", case.get("created_at") or ""), reverse=True)


def count_stored_cases() -> int:
    """Number of cases in the JSON store (bounded by MAX_STORED_CASES on save)."""
    payload = _read_payload()
    return len(payload.get("cases") or [])


def list_recent_cases(limit: int = 8, offset: int = 0) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit or 8), 50))
    safe_offset = max(0, int(offset or 0))
    payload = _read_payload()
    sorted_cases = _sort_recent(payload["cases"])
    return sorted_cases[safe_offset : safe_offset + safe_limit]


def delete_case(case_id: str) -> bool:
    """
    Remove a case from JSON and/or Postgres according to persistence flags.
    Returns True if at least one backing store removed the row.
    """
    from services.fiqa_api.db.service_record_settings import (
        db_primary_writes_enabled,
        json_case_writes_enabled,
    )

    cid = (case_id or "").strip()
    if not cid:
        return False
    removed = False
    if json_case_writes_enabled():
        payload = _read_payload()
        cases = payload.get("cases") or []
        before = len(cases)
        payload["cases"] = [c for c in cases if c.get("case_id") != cid]
        if len(payload["cases"]) < before:
            _write_payload(payload)
            removed = True
    if db_primary_writes_enabled():
        from services.fiqa_api.db.service_record_repository import delete_service_record

        if delete_service_record(cid):
            removed = True
    return removed


def list_all_cases() -> list[dict[str, Any]]:
    """Return all persisted cases sorted newest-first."""
    payload = _read_payload()
    return _sort_recent(payload["cases"])


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
    asserted_org_id: str | None = None,
    service_lane: str | None = None,
) -> dict[str, Any]:
    normalized_status = _validate_status(status)
    normalized_result = _validate_triage_result(triage_result)
    timestamp = _utc_now_iso()
    source = (source_text or "").strip()
    case_messages = _parse_source_to_messages(source, timestamp)

    # ADD_CAR_IDENTITY_CONTACT_LITE: populate contact from triage extraction
    cust_name = (triage_result.get("extracted_contact_name") or "").strip()
    cust_phone = (triage_result.get("extracted_contact_phone") or "").strip()
    if cust_name and len(cust_name) > MAX_CUSTOMER_NAME_LENGTH:
        cust_name = cust_name[: MAX_CUSTOMER_NAME_LENGTH - 1]
    if cust_phone and len(cust_phone) > MAX_CUSTOMER_PHONE_LENGTH:
        cust_phone = cust_phone[: MAX_CUSTOMER_PHONE_LENGTH - 1]

    case = {
        "case_id": f"case_{uuid4().hex[:12]}",
        "case_status": normalized_status,
        "created_at": timestamp,
        "updated_at": timestamp,
        # First moment this record became office-visible (formal persist). Never moved on append/updates.
        "formal_submitted_at": timestamp,
        "source_text": source,
        "case_messages": case_messages,
        "waiting_on": "none",
        "next_contact_by": "",
        "customer_name": cust_name,
        "customer_phone": cust_phone,
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
        "case_attachments": [],
        **normalized_result,
    }
    if (summary := (triage_result.get("conversation_summary") or "").strip()):
        case["conversation_summary"] = summary
    if (sec := (triage_result.get("secondary_issue_note") or "").strip()):
        case["secondary_issue_note"] = sec
    if (collected := triage_result.get("collected_fields")) is not None and isinstance(collected, list):
        case["collected_fields"] = [str(x) for x in collected]
    if (still_needed := triage_result.get("still_needed_fields")) is not None and isinstance(still_needed, list):
        case["still_needed_fields"] = [str(x) for x in still_needed]
    if (qrs := (triage_result.get("quote_ready_status") or "").strip()) in ("quote_ready", "almost_ready", "need_more"):
        case["quote_ready_status"] = qrs
    if (svc := str(triage_result.get("service_type") or "").strip()):
        case["service_type"] = svc
    case["vehicle_key"] = triage_result.get("vehicle_key")
    case["additional_vehicle_mentioned"] = triage_result.get("additional_vehicle_mentioned")
    _pvs = triage_result.get("primary_vehicle_summary")
    case["primary_vehicle_summary"] = None if _pvs is None else (str(_pvs).strip() or None)
    case["additional_vehicle_count_hint"] = triage_result.get("additional_vehicle_count_hint")
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
    # Phase 2: lifecycle_status for new case (respect collecting drafts from Customer First entry)
    ls_in = str(triage_result.get("lifecycle_status") or "").strip()
    if ls_in in ("collecting", "handoff_pending", "handed_off", "office_followup"):
        case["lifecycle_status"] = ls_in
    else:
        case["lifecycle_status"] = "handed_off"
    if case["lifecycle_status"] == "collecting":
        case["formal_submitted_at"] = ""
    # Minimal Production Backbone: optional traceability from case to pre-handoff session
    if origin_session_id and (sid := str(origin_session_id or "").strip()):
        case["origin_session_id"] = sid
    if (nbq := (triage_result.get("next_best_question") or "").strip()):
        case["next_best_question"] = nbq
    if (oct := (triage_result.get("office_case_title") or "").strip()):
        case["office_case_title"] = oct
    if (obs := (triage_result.get("office_broker_next_step") or "").strip()):
        case["office_broker_next_step"] = obs
    tm_save = str(triage_result.get("triage_mode") or "").strip().lower()
    case["triage_mode"] = tm_save if tm_save in ("greenfield", "append") else "greenfield"
    # Client Identity Persistence: store client_id for append/reopen lifecycle
    if client_id and (cid := str(client_id or "").strip()):
        case["client_id"] = cid
    if asserted_org_id and (oid := str(asserted_org_id).strip()[:256]):
        case["asserted_org_id"] = oid
    # Explicit Stage-1 lane (Add-Car-first); set only when caller supplies (e.g. formal Add-Car persist path)
    if service_lane and (sl := str(service_lane).strip()):
        case["service_lane"] = sl
    p16_blob = triage_result.get("p16_broker_packet")
    if isinstance(p16_blob, dict) and p16_blob:
        case["p16_broker_packet"] = p16_blob

    _apply_identity_fields_from_triage_result(case, triage_result)

    from services.fiqa_api.db.service_record_settings import (
        db_primary_writes_enabled,
        json_case_writes_enabled,
    )

    _require_case_storage_path()
    if db_primary_writes_enabled():
        from services.fiqa_api.db.service_record_repository import persist_new_case

        persist_new_case(case)
    if json_case_writes_enabled():
        payload = _read_payload()
        cases = [case, *payload["cases"]]
        payload["cases"] = _sort_recent(cases)[:MAX_STORED_CASES]
        _write_payload(payload)
    try:
        from services.fiqa_api.db.dual_write import maybe_dual_write_new_case

        maybe_dual_write_new_case(case)
    except Exception:
        pass
    return case


def update_case_follow_up(case_id: str, waiting_on: str, next_contact_by: str) -> dict[str, Any] | None:
    normalized_waiting_on = _validate_waiting_on(waiting_on)
    normalized_next_contact_by = _normalize_next_contact_by(next_contact_by)
    _require_case_storage_path()
    normalized_case = _load_case_for_mutation(case_id)
    if normalized_case is None:
        return None
    previous_waiting_on = normalized_case.get("waiting_on") or "none"
    previous_next_contact_by = normalized_case.get("next_contact_by") or ""
    if (
        previous_waiting_on == normalized_waiting_on
        and previous_next_contact_by == normalized_next_contact_by
    ):
        return normalized_case
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
    updated_case = normalized_case
    if not _persist_case_after_update(case_id, updated_case):
        return None
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
    _require_case_storage_path()
    normalized_case = _load_case_for_mutation(case_id)
    if normalized_case is None:
        return None
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
    updated_case = normalized_case
    if not _persist_case_after_update(case_id, updated_case):
        return None
    return updated_case


# Terminal status: no transitions out (STATE_WORKFLOW_BACKBONE_SPRINT)
TERMINAL_STATUS = ("closed",)


def update_case_status(case_id: str, status: str) -> dict[str, Any] | None:
    normalized_status = _validate_status(status)
    _require_case_storage_path()
    normalized_case = _load_case_for_mutation(case_id)
    if normalized_case is None:
        return None
    previous_status = normalized_case.get("case_status") or "new"
    # Guardrail: closed is terminal; reject transition from closed
    if previous_status in TERMINAL_STATUS and previous_status != normalized_status:
        raise ValueError(f"Cannot change status from '{previous_status}' (terminal)")
    if previous_status == normalized_status:
        return normalized_case
    normalized_case["case_status"] = normalized_status
    normalized_case["updated_at"] = _utc_now_iso()
    normalized_case["case_activity"] = [
        _build_activity_entry(
            "status_changed",
            f"Status changed from {_humanize_status(previous_status)} to {_humanize_status(normalized_status)}.",
        ),
        *normalized_case.get("case_activity", []),
    ][:MAX_CASE_ACTIVITY]
    updated_case = normalized_case
    if not _persist_case_after_update(case_id, updated_case):
        return None
    return updated_case


def update_case_workbench_flags(
    case_id: str,
    *,
    is_test: bool | None = None,
    archived: bool | None = None,
) -> dict[str, Any] | None:
    """
    Lightweight workbench labels: mark test data, soft-archive (hide from default views).
    With DB-primary writes, flags are mirrored in Postgres `extra` JSONB; JSON file may be off.
    """
    if is_test is None and archived is None:
        from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read

        return get_case_for_read(case_id)
    _require_case_storage_path()
    normalized_case = _load_case_for_mutation(case_id)
    if normalized_case is None:
        return None
    changed = False
    if is_test is not None and bool(normalized_case.get("workbench_test")) != bool(is_test):
        normalized_case["workbench_test"] = bool(is_test)
        changed = True
    if archived is not None and bool(normalized_case.get("workbench_archived")) != bool(archived):
        normalized_case["workbench_archived"] = bool(archived)
        changed = True
    if not changed:
        return normalized_case
    normalized_case["updated_at"] = _utc_now_iso()
    from services.fiqa_api.inbox_triage.config_loader import get_workbench_activity_copy

    wb = get_workbench_activity_copy()
    prefix = wb.get("prefix") or "工作台："
    parts: list[str] = []
    if is_test is not None:
        parts.append(wb["mark_test_on"] if is_test else wb["mark_test_off"])
    if archived is not None:
        parts.append(wb["archive_on"] if archived else wb["archive_off"])
    joiner = "；"
    msg = prefix + (joiner.join(parts) if parts else wb.get("generic_update") or "更新")
    normalized_case["case_activity"] = [
        _build_activity_entry("workbench_flags", msg),
        *normalized_case.get("case_activity", []),
    ][:MAX_CASE_ACTIVITY]
    updated_case = normalized_case
    if not _persist_case_after_update(case_id, updated_case):
        return None
    return updated_case


def _attachments_dir() -> Path:
    raw = (os.getenv("UNIFIED_INTAKE_ATTACHMENTS_DIR") or "").strip()
    if raw:
        return Path(raw) if Path(raw).is_absolute() else REPO_ROOT / raw
    return DEFAULT_ATTACHMENTS_DIR


def _infer_attachment_type(filename: str) -> str:
    """Infer attachment type from filename for add-car (registration, vin_photo, dec_page, screenshot)."""
    lower = (filename or "").lower()
    if "reg" in lower or "registration" in lower or "dmv" in lower:
        return "registration"
    if "vin" in lower or "车架" in lower:
        return "vin_photo"
    if "dec" in lower or "decl" in lower or "policy" in lower or "保单" in lower:
        return "dec_page"
    return "screenshot"


def add_attachment_to_case(
    case_id: str,
    *,
    filename: str,
    content: bytes,
    content_type: str | None = None,
) -> dict[str, Any] | None:
    """
    Add an attachment to a case. Stores file on disk and metadata in case.
    ADD_CAR_ATTACHMENT_READY_LITE: lightweight attachment support.
    """
    if len(content) > MAX_ATTACHMENT_SIZE_BYTES:
        raise ValueError(f"Attachment exceeds {MAX_ATTACHMENT_SIZE_BYTES // (1024 * 1024)} MB limit")
    base = (filename or "attachment").strip() or "attachment"
    # Sanitize: keep extension, safe basename; validate allowed types
    ext = ""
    for e in ALLOWED_ATTACHMENT_EXTENSIONS:
        if base.lower().endswith(e):
            ext = e
            base = base[: -len(e)].strip()
            break
    if not ext:
        if "pdf" in (content_type or "").lower():
            ext = ".pdf"
        elif (content_type or "").startswith("image/"):
            ext = ".jpg"
        else:
            raise ValueError("Attachment must be image (jpg, png, gif, webp) or PDF")
    if ext.lower() not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise ValueError(f"Attachment type not allowed. Use: {', '.join(ALLOWED_ATTACHMENT_EXTENSIONS)}")
    safe_base = re.sub(r"[^\w\-_.]", "_", base)[:80] or "file"
    safe_filename = f"{safe_base}{ext}"

    _require_case_storage_path()
    normalized_case = _load_case_for_mutation(case_id)
    if normalized_case is None:
        return None
    attachments = list(normalized_case.get("case_attachments") or [])
    if len(attachments) >= MAX_ATTACHMENTS_PER_CASE:
        raise ValueError(f"Case already has maximum {MAX_ATTACHMENTS_PER_CASE} attachments")
    attachment_id = f"att_{uuid4().hex[:12]}"
    att_type = _infer_attachment_type(safe_filename)
    timestamp = _utc_now_iso()
    att_meta = {
        "attachment_id": attachment_id,
        "filename": safe_filename,
        "type": att_type,
        "size_bytes": len(content),
        "created_at": timestamp,
    }
    # Store file
    case_dir = _attachments_dir() / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    file_path = case_dir / f"{attachment_id}_{safe_filename}"
    file_path.write_bytes(content)
    attachments.append(att_meta)
    normalized_case["case_attachments"] = attachments[:MAX_ATTACHMENTS_PER_CASE]
    # V6: OCR sidecar (never blocks save)
    try:
        from services.fiqa_api.inbox_triage.v6_attachment_sidecar import run_v6_ocr_for_saved_attachment

        _prior = normalized_case.get("v6_ocr_signals")
        _prior_d = _prior if isinstance(_prior, dict) else None
        _v6 = run_v6_ocr_for_saved_attachment(
            prior_signals=_prior_d,
            attachment_id=attachment_id,
            file_path=file_path,
            content_type=content_type,
        )
        if _v6:
            normalized_case["v6_ocr_signals"] = _v6
    except Exception:
        pass
    normalized_case["updated_at"] = timestamp
    normalized_case["case_activity"] = [
        _build_activity_entry("attachment_added", f"Attachment added: {safe_filename}"),
        *normalized_case.get("case_activity", []),
    ][:MAX_CASE_ACTIVITY]
    updated_case = normalized_case
    if not _persist_case_after_update(case_id, updated_case):
        return None
    return updated_case


def get_attachment_file_path(case_id: str, attachment_id: str) -> Path | None:
    """Return filesystem path for an attachment, or None if not found."""
    from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read

    case = get_case_for_read(case_id)
    if not case:
        return None
    attachments = case.get("case_attachments") or []
    for att in attachments:
        if att.get("attachment_id") == attachment_id:
            filename = att.get("filename") or "file"
            file_path = _attachments_dir() / case_id / f"{attachment_id}_{filename}"
            if file_path.exists():
                return file_path
            return None
    return None


def add_case_note(case_id: str, note_text: str) -> dict[str, Any] | None:
    body = (note_text or "").strip()
    if not body:
        raise ValueError("note cannot be empty")
    _require_case_storage_path()
    normalized_case = _load_case_for_mutation(case_id)
    if normalized_case is None:
        return None
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
    updated_case = normalized_case
    if not _persist_case_after_update(case_id, updated_case):
        return None
    return updated_case


def _merge_append_field_lists(
    existing_case: dict[str, Any],
    triage_result: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """
    Append is additive memory: union prior collected_fields with fresh triage extraction.
    Never drop a previously captured slot unless triage marks an explicit correction invalidation.
    """
    from services.fiqa_api.inbox_triage.add_car_field_contract import dedupe_preserve_order

    prev_collected = [str(x) for x in (existing_case.get("collected_fields") or []) if str(x).strip()]
    prev_still = [str(x) for x in (existing_case.get("still_needed_fields") or []) if str(x).strip()]
    new_collected = [str(x) for x in (triage_result.get("collected_fields") or []) if str(x).strip()]
    new_still = [str(x) for x in (triage_result.get("still_needed_fields") or []) if str(x).strip()]

    invalidated: set[str] = set()
    merge_meta = triage_result.get("add_car_merge")
    if isinstance(merge_meta, dict) and merge_meta.get("correction_turn"):
        invalidated = {str(x).lower() for x in (merge_meta.get("invalidated_slots") or []) if str(x).strip()}

    preserved = [x for x in prev_collected if x.lower() not in invalidated]
    coll_seen = {x.lower() for x in preserved}
    merged_collected = list(preserved)
    for field in new_collected:
        fl = field.lower()
        if fl and fl not in coll_seen:
            merged_collected.append(field)
            coll_seen.add(fl)

    merged_still = [x for x in new_still if x.lower() not in coll_seen]
    prev_collected_l = {x.lower() for x in prev_collected if x.lower() not in invalidated}
    merged_still = [x for x in merged_still if x.lower() not in prev_collected_l]

    return dedupe_preserve_order(merged_collected), dedupe_preserve_order(merged_still)


_ADD_CAR_OFFICE_STILL_ZH: dict[str, str] = {
    "year": "年份",
    "make_model": "车型",
    "vin": "车架号",
    "zip": "邮编",
    "delivery_date": "提车日期",
    "primary_driver": "主驾驶人",
    "name": "姓名",
    "phone": "电话",
    "notice_image": "notice_image",
}


def _office_broker_next_step_from_still(
    still_needed: list[str],
    *,
    primary_vehicle_summary: str | None = None,
    handoff_ready: bool = False,
) -> str:
    still = [str(x) for x in still_needed if str(x).strip()]
    if still:
        labels = "、".join(_ADD_CAR_OFFICE_STILL_ZH.get(s, s) for s in still[:4])
        return f"联系客户补齐{labels}，然后出报价"
    vehicle = (primary_vehicle_summary or "").strip()
    if handoff_ready and vehicle:
        return f"信息齐全，可直接为{vehicle}出报价"
    if handoff_ready:
        return "信息齐全，可直接出报价"
    return f"核实{vehicle}信息并出报价" if vehicle else "核实车辆信息并出报价"


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

    _require_case_storage_path()
    normalized_case = _load_case_for_mutation(case_id)
    if normalized_case is None:
        return None

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
    if (sec := (triage_result.get("secondary_issue_note") or "").strip()):
        normalized_case["secondary_issue_note"] = sec
    merged_collected, merged_still = _merge_append_field_lists(normalized_case, triage_result)
    normalized_case["collected_fields"] = merged_collected
    normalized_case["still_needed_fields"] = merged_still
    if (qrs := (triage_result.get("quote_ready_status") or "").strip()) in ("quote_ready", "almost_ready", "need_more"):
        normalized_case["quote_ready_status"] = qrs

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
    tm_ap = str(triage_result.get("triage_mode") or "").strip().lower()
    if tm_ap in ("greenfield", "append"):
        normalized_case["triage_mode"] = tm_ap
    if (ac := _normalize_add_car_turn_intent_payload(triage_result.get("add_car_turn_intent"))):
        normalized_case["add_car_turn_intent"] = ac
    elif "add_car_turn_intent" in normalized_case:
        normalized_case.pop("add_car_turn_intent", None)
    if (cb := (triage_result.get("case_boundary") or "").strip()) in (
        "new_issue",
        "borderline",
        "same_case",
    ):
        normalized_case["case_boundary"] = cb
    if (cba := str(triage_result.get("case_boundary_action") or "").strip()) in (
        "append_allowed",
        "requires_confirmation",
        "requires_new_case",
    ):
        normalized_case["case_boundary_action"] = cba
    if (br := str(triage_result.get("boundary_reason") or "").strip()):
        normalized_case["boundary_reason"] = br
    if (svc := str(triage_result.get("service_type") or "").strip()):
        normalized_case["service_type"] = svc
    if (oct := (triage_result.get("office_case_title") or "").strip()):
        normalized_case["office_case_title"] = oct
    triage_still = [str(x).lower() for x in (triage_result.get("still_needed_fields") or []) if str(x).strip()]
    merged_still_l = [str(x).lower() for x in merged_still]
    if triage_still != merged_still_l and str(triage_result.get("service_type") or "").strip() == "add_car":
        normalized_case["office_broker_next_step"] = _office_broker_next_step_from_still(
            merged_still,
            primary_vehicle_summary=str(triage_result.get("primary_vehicle_summary") or "").strip() or None,
            handoff_ready=bool(triage_result.get("handoff_ready")),
        )
    elif (obs := (triage_result.get("office_broker_next_step") or "").strip()):
        normalized_case["office_broker_next_step"] = obs
    normalized_case["vehicle_key"] = triage_result.get("vehicle_key")
    normalized_case["additional_vehicle_mentioned"] = triage_result.get("additional_vehicle_mentioned")
    _pvs_a = triage_result.get("primary_vehicle_summary")
    normalized_case["primary_vehicle_summary"] = None if _pvs_a is None else (str(_pvs_a).strip() or None)
    normalized_case["additional_vehicle_count_hint"] = triage_result.get("additional_vehicle_count_hint")
    # ADD_CAR_IDENTITY_CONTACT_LITE: update contact from triage extraction on append
    if (en := (triage_result.get("extracted_contact_name") or "").strip()):
        normalized_case["customer_name"] = _truncate(en, MAX_CUSTOMER_NAME_LENGTH)
    if (ep := (triage_result.get("extracted_contact_phone") or "").strip()):
        normalized_case["customer_phone"] = _truncate(ep, MAX_CUSTOMER_PHONE_LENGTH)
    # Collecting-phase Case Memory must stay collecting; post-formal-submit append → office_followup.
    # A case already in handed_off state receiving a follow-up append → office_followup.
    triage_lc = str(triage_result.get("lifecycle_status") or "").strip()
    existing_lc = str(normalized_case.get("lifecycle_status") or "").strip()
    has_formal = bool(str(normalized_case.get("formal_submitted_at") or "").strip())
    if has_formal or existing_lc == "handed_off":
        normalized_case["lifecycle_status"] = "office_followup"
    elif triage_lc in ("collecting", "handoff_pending", "handed_off", "office_followup"):
        normalized_case["lifecycle_status"] = triage_lc
    elif existing_lc in ("collecting", "handoff_pending"):
        normalized_case["lifecycle_status"] = existing_lc
    else:
        normalized_case["lifecycle_status"] = triage_lc or existing_lc or "office_followup"
    # Client Identity Persistence: backfill client_id for legacy cases when provided
    if not normalized_case.get("client_id") and client_id and (cid := str(client_id or "").strip()):
        normalized_case["client_id"] = cid

    normalized_case["case_activity"] = [
        _build_activity_entry("follow_up_added", f"Customer follow-up added: {_preview_text(new_msg, 64)}"),
        *normalized_case.get("case_activity", []),
    ][:MAX_CASE_ACTIVITY]
    updated_case = normalized_case

    if not _persist_case_after_update(case_id, updated_case):
        return None
    return updated_case


def merge_add_car_packet_fields(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Gap-fill merge only — existing non-empty values win (Phase 1)."""
    merged = dict(existing)
    for key, incoming_field in incoming.items():
        if not isinstance(incoming_field, dict):
            continue
        inc_val = str(incoming_field.get("value") or "").strip()
        if not inc_val:
            continue
        ex_field = merged.get(key)
        if not isinstance(ex_field, dict):
            merged[key] = dict(incoming_field)
            continue
        ex_val = str(ex_field.get("value") or "").strip()
        if not ex_val:
            merged[key] = dict(incoming_field)
    return merged


def _append_evidence_event(
    case: dict[str, Any],
    *,
    channel: str,
    filename: str,
) -> None:
    events = list(case.get("evidence_events") or [])
    events.insert(
        0,
        {
            "time": _utc_now_iso(),
            "channel": (channel or "web").strip() or "web",
            "filename": (filename or "").strip() or "upload",
        },
    )
    case["evidence_events"] = events[:MAX_EVIDENCE_EVENTS]


def append_evidence_event_only(
    case_id: str,
    *,
    channel: str = "web",
    filename: str,
) -> None:
    """Record lightweight evidence on case without packet merge (first CREATE upload)."""
    _require_case_storage_path()
    normalized_case = _load_case_for_mutation(case_id)
    if normalized_case is None:
        return
    _append_evidence_event(normalized_case, channel=channel, filename=filename)
    normalized_case["updated_at"] = _utc_now_iso()
    _persist_case_after_update(case_id, normalized_case)


def attach_add_car_evidence(
    case_id: str,
    *,
    source_text: str,
    triage_result: dict[str, Any],
    p16_broker_packet: dict[str, Any],
    incoming_packet: dict[str, Any],
    garaging_zip: str = "",
    evidence_channel: str = "web",
    evidence_filename: str = "",
    merge_review_required: bool = False,
    conflict_reason: str = "",
) -> dict[str, Any] | None:
    """
    Append evidence to an existing Active Case (P17 Phase 1).

    When merge_review_required: log evidence, flag conflict, keep existing packet.
    Otherwise: merge packet, recompute readiness, update broker blob.
    """
    _require_case_storage_path()
    normalized_case = _load_case_for_mutation(case_id)
    if normalized_case is None:
        return None

    validated = _validate_triage_result(triage_result)
    timestamp = _utc_now_iso()
    upload_label = (evidence_filename or "").strip() or "upload"
    _append_evidence_event(
        normalized_case,
        channel=evidence_channel,
        filename=upload_label,
    )

    new_msg = (source_text or "").strip()
    if new_msg:
        messages = list(normalized_case.get("case_messages") or [])
        next_seq = max((m.get("sequence") or 0 for m in messages), default=0) + 1
        messages.append({
            "message_id": f"msg_{uuid4().hex[:12]}",
            "role": "customer",
            "text": new_msg,
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

    if merge_review_required:
        normalized_case["merge_review_required"] = True
        normalized_case["conflict_state"] = (conflict_reason or "broker_review").strip() or "broker_review"
        existing_blob = normalized_case.get("p16_broker_packet")
        if isinstance(existing_blob, dict):
            blob = dict(existing_blob)
            warnings = [str(w) for w in (blob.get("warnings") or []) if str(w).strip()]
            note = "New evidence conflicts with current packet — review required."
            if conflict_reason == "vin_conflict":
                note = "VIN conflict across evidence — broker review required."
            elif conflict_reason == "multiple_open_cases":
                note = "Multiple open cases for this customer — broker review required."
            if note not in warnings:
                warnings.append(note)
            blob["warnings"] = warnings
            blob["readiness_status"] = "BROKER_REVIEW"
            normalized_case["p16_broker_packet"] = blob
        normalized_case["case_activity"] = [
            _build_activity_entry(
                "evidence_append_review",
                f"Evidence appended — broker review required ({conflict_reason or 'conflict'}).",
            ),
            *normalized_case.get("case_activity", []),
        ][:MAX_CASE_ACTIVITY]
        if not _persist_case_after_update(case_id, normalized_case):
            return None
        return normalized_case

    existing_blob = normalized_case.get("p16_broker_packet")
    existing_packet: dict[str, Any] = {}
    if isinstance(existing_blob, dict):
        raw_pkt = existing_blob.get("packet")
        if isinstance(raw_pkt, dict):
            existing_packet = raw_pkt
    merged_packet = merge_add_car_packet_fields(existing_packet, incoming_packet)

    from services.fiqa_api.p16.packet_persist import derive_add_car_field_gaps, map_add_car_readiness

    new_blob = dict(p16_broker_packet)
    if isinstance(existing_blob, dict):
        prior_sources = list(existing_blob.get("sources") or [])
        new_sources = list(new_blob.get("sources") or [])
        seen = {json.dumps(s, sort_keys=True) for s in prior_sources if isinstance(s, dict)}
        merged_sources = list(prior_sources)
        for src in new_sources:
            if isinstance(src, dict):
                key = json.dumps(src, sort_keys=True)
                if key not in seen:
                    merged_sources.append(src)
                    seen.add(key)
        new_blob["sources"] = merged_sources
        prior_warnings = [str(w) for w in (existing_blob.get("warnings") or []) if str(w).strip()]
        for w in (new_blob.get("warnings") or []):
            ws = str(w).strip()
            if ws and ws not in prior_warnings:
                prior_warnings.append(ws)
        new_blob["warnings"] = prior_warnings
    new_blob["packet"] = merged_packet

    merged_collected, merged_still = derive_add_car_field_gaps(
        merged_packet,
        garaging_zip=garaging_zip,
    )
    merged_readiness = map_add_car_readiness(
        still_needed=merged_still,
        warnings=list(new_blob.get("warnings") or []),
        quote_ready_status=str(triage_result.get("quote_ready_status") or ""),
    )
    new_blob["readiness_status"] = merged_readiness
    normalized_case["collected_fields"] = merged_collected
    normalized_case["still_needed_fields"] = merged_still
    if merged_still:
        normalized_case["quote_ready_status"] = "need_more"
        normalized_case["handoff_ready"] = False
    elif merged_readiness == "BROKER_REVIEW":
        normalized_case["quote_ready_status"] = "almost_ready"
        normalized_case["handoff_ready"] = True
    else:
        normalized_case["quote_ready_status"] = "quote_ready"
        normalized_case["handoff_ready"] = True
    year_val = str((merged_packet.get("year") or {}).get("value") or "").strip() if isinstance(merged_packet.get("year"), dict) else ""
    make_val = str((merged_packet.get("make") or {}).get("value") or "").strip() if isinstance(merged_packet.get("make"), dict) else ""
    model_val = str((merged_packet.get("model") or {}).get("value") or "").strip() if isinstance(merged_packet.get("model"), dict) else ""
    vehicle_summary = " ".join(filter(None, [year_val, make_val, model_val])).strip() or None
    normalized_case["primary_vehicle_summary"] = vehicle_summary
    vin_val = str((merged_packet.get("vin") or {}).get("value") or "").strip() if isinstance(merged_packet.get("vin"), dict) else ""
    if vin_val:
        normalized_case["vehicle_key"] = vin_val.upper()
    normalized_case["merge_review_required"] = False
    normalized_case["conflict_state"] = "none"
    normalized_case["p16_broker_packet"] = new_blob

    if (en := (triage_result.get("extracted_contact_name") or "").strip()):
        normalized_case["customer_name"] = _truncate(en, MAX_CUSTOMER_NAME_LENGTH)
    if (ep := (triage_result.get("extracted_contact_phone") or "").strip()):
        normalized_case["customer_phone"] = _truncate(ep, MAX_CUSTOMER_PHONE_LENGTH)

    normalized_case["case_activity"] = [
        _build_activity_entry(
            "evidence_appended",
            f"Evidence appended: {_preview_text(upload_label, 64)}",
        ),
        *normalized_case.get("case_activity", []),
    ][:MAX_CASE_ACTIVITY]

    if not _persist_case_after_update(case_id, normalized_case):
        return None
    return normalized_case
