"""
Minimal Postgres persistence for Stage 1 service records.

Callers must ensure schema is applied (see db/schema/stage1_service_record.sql).
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Generator, Iterable

from services.fiqa_api.db.service_record_settings import service_record_database_url

logger = logging.getLogger(__name__)


@contextmanager
def service_record_connection() -> Generator[Any, None, None]:
    import psycopg

    url = service_record_database_url()
    if not url:
        raise RuntimeError("no service record database URL configured")
    conn = psycopg.connect(url, connect_timeout=10)
    try:
        yield conn
    finally:
        conn.close()


def _str(v: Any, default: str = "") -> str:
    if v is None:
        return default
    return str(v).strip()


def _build_structured_payload(case: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "issue_category",
        "urgency",
        "broker_next_step",
        "client_prep",
        "client_reply_draft",
        "manual_followup_needed",
        "conversation_summary",
        "secondary_issue_note",
        "collected_fields",
        "still_needed_fields",
        "quote_ready_status",
        "handoff_ready",
        "triage_mode",
        "case_creation_suggested",
        "human_confirmation_required",
        "human_confirmation_fields",
        "collection_stage",
        "follow_up_type",
        "next_best_question",
        "lifecycle_status",
        "case_boundary",
        "case_boundary_action",
        "boundary_reason",
        "service_type",
        "vehicle_key",
        "additional_vehicle_mentioned",
        "primary_vehicle_summary",
        "additional_vehicle_count_hint",
        "service_lane",
        # Stage-1 optional light identity (nullable)
        "identity_binding_state",
        "person_link_key",
        "person_link_source",
        "person_link_confidence",
    )
    out: dict[str, Any] = {}
    for k in keys:
        if k in case:
            out[k] = case[k]
    return out


def _build_extra(case: dict[str, Any]) -> dict[str, Any]:
    """Small JSONB bag for pilot fields not promoted to columns yet."""
    keys = (
        "origin_session_id",
        "case_attachments",
        "case_notes",
        "formal_submitted_at",
        "workbench_test",
        "workbench_archived",
    )
    return {k: case[k] for k in keys if k in case}


def _missing_fields_summary(case: dict[str, Any]) -> str | None:
    """Denormalized still-needed list for SQL filters and office skim (JSON remains authoritative)."""
    raw = case.get("still_needed_fields")
    if not isinstance(raw, list) or not raw:
        return None
    parts = [str(x).strip() for x in raw if str(x).strip()]
    if not parts:
        return None
    return ", ".join(parts[:50])


def _title_summary(case: dict[str, Any]) -> str:
    s = _str(case.get("conversation_summary"))
    if s:
        return s[:512]
    src = _str(case.get("source_text"))
    return src[:512] if src else ""


def persist_new_case(case: dict[str, Any]) -> None:
    """Insert a new service record row and related messages / structured / initial state event."""
    from psycopg.types.json import Json

    record_id = _str(case.get("case_id"))
    if not record_id:
        raise ValueError("case_id required for persist_new_case")

    messages: Iterable[dict[str, Any]] = case.get("case_messages") or []
    structured = _build_structured_payload(case)
    extra = _build_extra(case)
    now_created = _str(case.get("created_at"))
    now_updated = _str(case.get("updated_at")) or now_created

    with service_record_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO service_records (
                        record_id, client_id, intake_channel, issue_category, title_summary,
                        case_status, lifecycle_status, waiting_on, next_contact_by,
                        current_owner, current_next_action,
                        customer_name, customer_phone, customer_email, policy_number, contact_note,
                        origin_session_id, created_at, updated_at, closed_at, extra
                    ) VALUES (
                        %(record_id)s, %(client_id)s, %(intake_channel)s, %(issue_category)s, %(title_summary)s,
                        %(case_status)s, %(lifecycle_status)s, %(waiting_on)s, %(next_contact_by)s,
                        %(current_owner)s, %(current_next_action)s,
                        %(customer_name)s, %(customer_phone)s, %(customer_email)s, %(policy_number)s, %(contact_note)s,
                        %(origin_session_id)s, %(created_at)s, %(updated_at)s, %(closed_at)s, %(extra)s
                    )
                    """,
                    {
                        "record_id": record_id,
                        "client_id": _str(case.get("client_id")) or None,
                        "intake_channel": "portal",
                        "issue_category": _str(case.get("issue_category")) or None,
                        "title_summary": _title_summary(case) or None,
                        "case_status": _str(case.get("case_status")) or "new",
                        "lifecycle_status": _str(case.get("lifecycle_status")) or None,
                        "waiting_on": _str(case.get("waiting_on")) or "none",
                        "next_contact_by": _str(case.get("next_contact_by")),
                        "current_owner": None,
                        "current_next_action": _str(case.get("broker_next_step")) or None,
                        "customer_name": _str(case.get("customer_name")),
                        "customer_phone": _str(case.get("customer_phone")),
                        "customer_email": _str(case.get("customer_email")),
                        "policy_number": _str(case.get("policy_number")),
                        "contact_note": _str(case.get("contact_note")),
                        "origin_session_id": _str(case.get("origin_session_id")) or None,
                        "created_at": now_created,
                        "updated_at": now_updated,
                        "closed_at": None,
                        "extra": Json(extra),
                    },
                )

                for msg in messages:
                    if not isinstance(msg, dict):
                        continue
                    ext_id = _str(msg.get("message_id"))
                    text = _str(msg.get("text"))
                    if not ext_id or not text:
                        continue
                    role = _str(msg.get("role"), "customer").lower()
                    sender = "customer" if role == "customer" else "system"
                    cur.execute(
                        """
                        INSERT INTO record_messages (
                            record_id, external_message_id, sender_type, message_text,
                            source_channel, raw_payload, sequence_num, created_at
                        ) VALUES (
                            %(record_id)s, %(external_message_id)s, %(sender_type)s, %(message_text)s,
                            %(source_channel)s, %(raw_payload)s, %(sequence_num)s, %(created_at)s
                        )
                        """,
                        {
                            "record_id": record_id,
                            "external_message_id": ext_id,
                            "sender_type": sender,
                            "message_text": text,
                            "source_channel": "portal",
                            "raw_payload": Json(msg),
                            "sequence_num": int(msg.get("sequence") or 1),
                            "created_at": _str(msg.get("created_at")) or now_created,
                        },
                    )

                cur.execute(
                    """
                    INSERT INTO structured_record_data (
                        record_id, structured_payload, quote_readiness, missing_fields_summary,
                        extracted_at, updated_at
                    ) VALUES (
                        %(record_id)s, %(structured_payload)s, %(quote_readiness)s, %(missing_fields_summary)s,
                        %(extracted_at)s, %(updated_at)s
                    )
                    """,
                    {
                        "record_id": record_id,
                        "structured_payload": Json(structured),
                        "quote_readiness": _str(case.get("quote_ready_status")) or None,
                        "missing_fields_summary": _missing_fields_summary(case),
                        "extracted_at": now_updated,
                        "updated_at": now_updated,
                    },
                )

                cur.execute(
                    """
                    INSERT INTO state_history (
                        record_id, from_status, to_status, triggered_by, reason, snapshot_note, created_at
                    ) VALUES (
                        %(record_id)s, NULL, %(to_status)s, %(triggered_by)s, %(reason)s, %(snapshot_note)s, %(created_at)s
                    )
                    """,
                    {
                        "record_id": record_id,
                        "to_status": _str(case.get("case_status")) or "new",
                        "triggered_by": "system",
                        "reason": "case_created",
                        "snapshot_note": _title_summary(case)[:256] or None,
                        "created_at": now_created,
                    },
                )


def persist_case_append(case: dict[str, Any]) -> None:
    """Upsert core record + structured payload; insert only new messages (by external_message_id)."""
    from psycopg.types.json import Json

    record_id = _str(case.get("case_id"))
    if not record_id:
        raise ValueError("case_id required for persist_case_append")

    messages: Iterable[dict[str, Any]] = case.get("case_messages") or []
    structured = _build_structured_payload(case)
    extra = _build_extra(case)
    now_updated = _str(case.get("updated_at"))
    now_created = _str(case.get("created_at")) or now_updated

    with service_record_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE service_records SET
                        client_id = COALESCE(%(client_id)s, client_id),
                        issue_category = %(issue_category)s,
                        title_summary = %(title_summary)s,
                        case_status = %(case_status)s,
                        lifecycle_status = %(lifecycle_status)s,
                        waiting_on = %(waiting_on)s,
                        next_contact_by = %(next_contact_by)s,
                        current_next_action = %(current_next_action)s,
                        customer_name = %(customer_name)s,
                        customer_phone = %(customer_phone)s,
                        customer_email = %(customer_email)s,
                        policy_number = %(policy_number)s,
                        contact_note = %(contact_note)s,
                        updated_at = %(updated_at)s,
                        extra = %(extra)s
                    WHERE record_id = %(record_id)s
                    """,
                    {
                        "record_id": record_id,
                        "client_id": _str(case.get("client_id")) or None,
                        "issue_category": _str(case.get("issue_category")) or None,
                        "title_summary": _title_summary(case) or None,
                        "case_status": _str(case.get("case_status")) or "new",
                        "lifecycle_status": _str(case.get("lifecycle_status")) or None,
                        "waiting_on": _str(case.get("waiting_on")) or "none",
                        "next_contact_by": _str(case.get("next_contact_by")),
                        "current_next_action": _str(case.get("broker_next_step")) or None,
                        "customer_name": _str(case.get("customer_name")),
                        "customer_phone": _str(case.get("customer_phone")),
                        "customer_email": _str(case.get("customer_email")),
                        "policy_number": _str(case.get("policy_number")),
                        "contact_note": _str(case.get("contact_note")),
                        "updated_at": now_updated,
                        "extra": Json(extra),
                    },
                )
                if cur.rowcount == 0:
                    logger.warning(
                        "UNIFIED_INTAKE_DB_OBS signal=PG_APPEND_NO_ROW case_id=%s",
                        record_id,
                    )
                    return

                for msg in messages:
                    if not isinstance(msg, dict):
                        continue
                    ext_id = _str(msg.get("message_id"))
                    text = _str(msg.get("text"))
                    if not ext_id or not text:
                        continue
                    role = _str(msg.get("role"), "customer").lower()
                    sender = "customer" if role == "customer" else "system"
                    cur.execute(
                        """
                        INSERT INTO record_messages (
                            record_id, external_message_id, sender_type, message_text,
                            source_channel, raw_payload, sequence_num, created_at
                        ) VALUES (
                            %(record_id)s, %(external_message_id)s, %(sender_type)s, %(message_text)s,
                            %(source_channel)s, %(raw_payload)s, %(sequence_num)s, %(created_at)s
                        )
                        ON CONFLICT (record_id, external_message_id) DO NOTHING
                        """,
                        {
                            "record_id": record_id,
                            "external_message_id": ext_id,
                            "sender_type": sender,
                            "message_text": text,
                            "source_channel": "portal",
                            "raw_payload": Json(msg),
                            "sequence_num": int(msg.get("sequence") or 1),
                            "created_at": _str(msg.get("created_at")) or now_created,
                        },
                    )

                cur.execute(
                    """
                    INSERT INTO structured_record_data (
                        record_id, structured_payload, quote_readiness, missing_fields_summary,
                        extracted_at, updated_at
                    ) VALUES (
                        %(record_id)s, %(structured_payload)s, %(quote_readiness)s, %(missing_fields_summary)s,
                        %(extracted_at)s, %(updated_at)s
                    )
                    ON CONFLICT (record_id) DO UPDATE SET
                        structured_payload = EXCLUDED.structured_payload,
                        quote_readiness = EXCLUDED.quote_readiness,
                        missing_fields_summary = EXCLUDED.missing_fields_summary,
                        extracted_at = EXCLUDED.extracted_at,
                        updated_at = EXCLUDED.updated_at
                    """,
                    {
                        "record_id": record_id,
                        "structured_payload": Json(structured),
                        "quote_readiness": _str(case.get("quote_ready_status")) or None,
                        "missing_fields_summary": _missing_fields_summary(case),
                        "extracted_at": now_updated,
                        "updated_at": now_updated,
                    },
                )

                cur.execute(
                    """
                    INSERT INTO state_history (
                        record_id, from_status, to_status, triggered_by, reason, snapshot_note, created_at
                    ) VALUES (
                        %(record_id)s, %(from_status)s, %(to_status)s, %(triggered_by)s, %(reason)s, %(snapshot_note)s, %(created_at)s
                    )
                    """,
                    {
                        "record_id": record_id,
                        "from_status": None,
                        "to_status": _str(case.get("case_status")) or "new",
                        "triggered_by": "system",
                        "reason": "conversation_appended",
                        "snapshot_note": _str(case.get("lifecycle_status")) or None,
                        "created_at": now_updated,
                    },
                )


def fetch_service_records(record_ids: list[str]) -> dict[str, dict[str, Any]]:
    """
    Fetch minimal Postgres mirror view for consistency checks.

    Returns map keyed by record_id.
    """
    ids = [str(x).strip() for x in (record_ids or []) if str(x).strip()]
    if not ids:
        return {}

    with service_record_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    sr.record_id,
                    sr.customer_name,
                    sr.customer_phone,
                    sr.lifecycle_status,
                    sr.updated_at,
                    sr.extra,
                    srd.quote_readiness,
                    srd.missing_fields_summary,
                    srd.structured_payload
                FROM service_records sr
                LEFT JOIN structured_record_data srd
                    ON srd.record_id = sr.record_id
                WHERE sr.record_id = ANY(%s)
                """,
                (ids,),
            )
            rows = cur.fetchall()

    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        out[str(row[0])] = {
            "record_id": str(row[0]),
            "customer_name": _str(row[1]),
            "customer_phone": _str(row[2]),
            "lifecycle_status": _str(row[3]),
            "updated_at": str(row[4]) if row[4] is not None else "",
            "extra": row[5] if isinstance(row[5], dict) else {},
            "quote_readiness": _str(row[6]),
            "missing_fields_summary": _str(row[7]),
            "structured_payload": row[8] if isinstance(row[8], dict) else {},
        }
    return out


def _ts_to_iso(val: Any) -> str:
    if val is None:
        return ""
    if hasattr(val, "isoformat"):
        s = val.isoformat()
        if s.endswith("+00:00"):
            return s.replace("+00:00", "Z")
        return s
    return str(val).strip()


# Match case_store.MAX_CASE_ACTIVITY for list/detail parity.
_MAX_CASE_ACTIVITY = 40


def _state_history_row_message(
    reason: str | None,
    to_status: str | None,
    snapshot_note: str | None,
) -> str:
    r = _str(reason)
    if r == "case_created":
        return "Case record created."
    if r == "conversation_appended":
        sn = _str(snapshot_note)
        if sn:
            return f"Conversation updated (lifecycle: {sn})."
        return "Conversation updated."
    ts = _str(to_status)
    if ts:
        return f"Record state: {ts}."
    return "Record updated."


def _case_activity_from_state_history_rows(rows: list[Any]) -> list[dict[str, str]]:
    """Map state_history rows to case_activity-shaped entries (newest first)."""
    out: list[dict[str, str]] = []
    for row in rows:
        if not row:
            continue
        state_event_id = row[0]
        reason = row[1]
        to_status = row[2]
        snapshot_note = row[3]
        created_at = row[4]
        eid = str(state_event_id).replace("-", "")[:16]
        msg = _state_history_row_message(reason, to_status, snapshot_note)
        out.append(
            {
                "activity_id": f"act_pg_{eid}",
                "activity_type": _str(reason) or "state_event",
                "message": msg,
                "created_at": _ts_to_iso(created_at),
            }
        )
    return out[:_MAX_CASE_ACTIVITY]


def load_full_case_from_postgres(record_id: str) -> dict[str, Any] | None:
    """
    Reconstruct a pilot case dict from Postgres mirror rows (dual-write shape).
    Returns None if no service_records row exists for record_id.
    """
    rid = _str(record_id)
    if not rid:
        return None

    with service_record_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    sr.record_id,
                    sr.client_id,
                    sr.issue_category,
                    sr.title_summary,
                    sr.case_status,
                    sr.lifecycle_status,
                    sr.waiting_on,
                    sr.next_contact_by,
                    sr.current_next_action,
                    sr.customer_name,
                    sr.customer_phone,
                    sr.customer_email,
                    sr.policy_number,
                    sr.contact_note,
                    sr.origin_session_id,
                    sr.created_at,
                    sr.updated_at,
                    sr.extra,
                    srd.structured_payload,
                    srd.quote_readiness
                FROM service_records sr
                LEFT JOIN structured_record_data srd ON srd.record_id = sr.record_id
                WHERE sr.record_id = %s
                """,
                (rid,),
            )
            row = cur.fetchone()
            if not row:
                return None

            cur.execute(
                """
                SELECT external_message_id, sender_type, message_text, sequence_num, created_at, raw_payload
                FROM record_messages
                WHERE record_id = %s
                ORDER BY sequence_num ASC, created_at ASC
                """,
                (rid,),
            )
            msg_rows = cur.fetchall()

            cur.execute(
                """
                SELECT state_event_id, reason, to_status, snapshot_note, created_at
                FROM state_history
                WHERE record_id = %s
                ORDER BY created_at DESC, state_event_id DESC
                LIMIT %s
                """,
                (rid, _MAX_CASE_ACTIVITY),
            )
            state_rows = cur.fetchall()

    extra = row[17] if isinstance(row[17], dict) else {}
    structured = row[18] if isinstance(row[18], dict) else {}
    q_readiness_col = _str(row[19])

    case: dict[str, Any] = {}
    for k, v in structured.items():
        case[k] = v

    case["case_id"] = str(row[0])
    if row[1]:
        case["client_id"] = str(row[1]).strip()
    case["issue_category"] = _str(row[2])
    case["conversation_summary"] = _str(row[3])
    case["case_status"] = _str(row[4]) or "new"
    case["lifecycle_status"] = _str(row[5])
    case["waiting_on"] = _str(row[6]) or "none"
    case["next_contact_by"] = _str(row[7])
    case["broker_next_step"] = _str(row[8])
    case["customer_name"] = _str(row[9])
    case["customer_phone"] = _str(row[10])
    case["customer_email"] = _str(row[11])
    case["policy_number"] = _str(row[12])
    case["contact_note"] = _str(row[13])
    if row[14]:
        case["origin_session_id"] = str(row[14]).strip()

    case["created_at"] = _ts_to_iso(row[15])
    case["updated_at"] = _ts_to_iso(row[16])

    if extra.get("formal_submitted_at"):
        case["formal_submitted_at"] = str(extra["formal_submitted_at"]).strip()
    else:
        case["formal_submitted_at"] = case["created_at"]

    if isinstance(extra.get("case_notes"), list):
        case["case_notes"] = extra["case_notes"]
    if isinstance(extra.get("case_attachments"), list):
        case["case_attachments"] = extra["case_attachments"]
    if "workbench_test" in extra:
        case["workbench_test"] = bool(extra.get("workbench_test"))
    if "workbench_archived" in extra:
        case["workbench_archived"] = bool(extra.get("workbench_archived"))

    if q_readiness_col:
        case["quote_ready_status"] = q_readiness_col
    elif "quote_ready_status" not in case:
        case["quote_ready_status"] = ""

    case_messages: list[dict[str, Any]] = []
    for mr in msg_rows:
        rawp = mr[5]
        if isinstance(rawp, dict) and (rawp.get("text") or "").strip():
            case_messages.append(dict(rawp))
            continue
        ext_id = _str(mr[0])
        sender = _str(mr[1]).lower()
        role = "customer" if sender == "customer" else "system"
        text = _str(mr[2])
        seq = int(mr[3] or 1)
        ca = _ts_to_iso(mr[4])
        case_messages.append({
            "message_id": ext_id or f"msg_{ext_id}",
            "role": role,
            "text": text,
            "created_at": ca,
            "sequence": seq,
        })

    case["case_messages"] = case_messages
    case["case_activity"] = _case_activity_from_state_history_rows(list(state_rows or []))

    from services.fiqa_api.inbox_triage.case_store import _build_source_from_messages

    case["source_text"] = _build_source_from_messages(case_messages)

    return case


def count_service_records() -> int:
    """Total rows in service_records (for workbench queue totals)."""
    with service_record_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM service_records")
            row = cur.fetchone()
            return int(row[0] or 0) if row else 0


def list_record_ids_recent(limit: int, offset: int = 0) -> list[str]:
    """Return record_ids ordered by updated_at descending (newest first)."""
    safe = max(1, min(int(limit or 8), 500))
    safe_offset = max(0, min(int(offset or 0), 10_000))
    with service_record_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT record_id FROM service_records
                ORDER BY updated_at DESC
                LIMIT %s OFFSET %s
                """,
                (safe, safe_offset),
            )
            return [str(r[0]) for r in cur.fetchall()]


def list_binding_stub_rows_recent(limit: int, offset: int = 0) -> list[dict[str, Any]]:
    """
    One round-trip: rows shaped for :func:`resolve_active_case` / :func:`is_case_open_for_binding`
    without loading messages, state history, or full structured hydration per row.
    """
    from psycopg.rows import dict_row

    safe = max(1, min(int(limit or 8), 500))
    safe_offset = max(0, min(int(offset or 0), 10_000))
    out: list[dict[str, Any]] = []
    with service_record_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    sr.record_id,
                    sr.case_status,
                    sr.extra,
                    srd.structured_payload
                FROM service_records sr
                LEFT JOIN structured_record_data srd ON srd.record_id = sr.record_id
                ORDER BY sr.updated_at DESC
                LIMIT %s OFFSET %s
                """,
                (safe, safe_offset),
            )
            for r in cur.fetchall():
                rid = _str(r.get("record_id"))
                if not rid:
                    continue
                extra = r.get("extra") if isinstance(r.get("extra"), dict) else {}
                sp = r.get("structured_payload") if isinstance(r.get("structured_payload"), dict) else {}
                vk = sp.get("vehicle_key")
                if vk is None and isinstance(extra, dict):
                    vk = extra.get("vehicle_key")
                out.append(
                    {
                        "case_id": rid,
                        "case_status": _str(r.get("case_status") or "new") or "new",
                        "workbench_archived": bool(extra.get("workbench_archived")),
                        "vehicle_key": vk,
                    }
                )
    return out


def _case_dict_from_pg_join_dict_row(row: dict[str, Any]) -> dict[str, Any]:
    """Build pilot case dict from one ``dict_row`` join of service_records + structured_record_data."""
    extra = row["extra"] if isinstance(row.get("extra"), dict) else {}
    structured = row["structured_payload"] if isinstance(row.get("structured_payload"), dict) else {}
    q_readiness_col = _str(row.get("quote_readiness") or "")

    case: dict[str, Any] = {}
    for k, v in structured.items():
        case[k] = v

    case["case_id"] = str(row["record_id"])
    if row.get("client_id"):
        case["client_id"] = str(row["client_id"]).strip()
    case["issue_category"] = _str(row.get("issue_category"))
    case["conversation_summary"] = _str(row.get("title_summary"))
    case["case_status"] = _str(row.get("case_status") or "new") or "new"
    case["lifecycle_status"] = _str(row.get("lifecycle_status"))
    case["waiting_on"] = _str(row.get("waiting_on") or "none") or "none"
    case["next_contact_by"] = _str(row.get("next_contact_by"))
    case["broker_next_step"] = _str(row.get("current_next_action"))
    case["customer_name"] = _str(row.get("customer_name"))
    case["customer_phone"] = _str(row.get("customer_phone"))
    case["customer_email"] = _str(row.get("customer_email"))
    case["policy_number"] = _str(row.get("policy_number"))
    case["contact_note"] = _str(row.get("contact_note"))
    if row.get("origin_session_id"):
        case["origin_session_id"] = str(row.get("origin_session_id")).strip()

    case["created_at"] = _ts_to_iso(row.get("created_at"))
    case["updated_at"] = _ts_to_iso(row.get("updated_at"))

    if extra.get("formal_submitted_at"):
        case["formal_submitted_at"] = str(extra["formal_submitted_at"]).strip()
    else:
        case["formal_submitted_at"] = case["created_at"]

    if isinstance(extra.get("case_notes"), list):
        case["case_notes"] = extra["case_notes"]
    if isinstance(extra.get("case_attachments"), list):
        case["case_attachments"] = extra["case_attachments"]
    if "workbench_test" in extra:
        case["workbench_test"] = bool(extra.get("workbench_test"))
    if "workbench_archived" in extra:
        case["workbench_archived"] = bool(extra.get("workbench_archived"))

    if q_readiness_col:
        case["quote_ready_status"] = q_readiness_col
    elif "quote_ready_status" not in case:
        case["quote_ready_status"] = ""

    case["case_messages"] = []
    case["case_activity"] = []
    return case


_PG_LIST_SELECT = """
                SELECT
                    sr.record_id,
                    sr.client_id,
                    sr.issue_category,
                    sr.title_summary,
                    sr.case_status,
                    sr.lifecycle_status,
                    sr.waiting_on,
                    sr.next_contact_by,
                    sr.current_next_action,
                    sr.customer_name,
                    sr.customer_phone,
                    sr.customer_email,
                    sr.policy_number,
                    sr.contact_note,
                    sr.origin_session_id,
                    sr.created_at,
                    sr.updated_at,
                    sr.extra,
                    srd.structured_payload,
                    srd.quote_readiness
                FROM service_records sr
                LEFT JOIN structured_record_data srd ON srd.record_id = sr.record_id
"""


def load_workbench_queue_cases_from_postgres(record_ids: list[str]) -> list[dict[str, Any]]:
    """
    One round-trip hydration for GET /api/inbox/cases list rows: no record_messages or state_history.

    ``source_text`` is a queue skim line (summary / draft / category), not full conversation replay.
    """
    ids = [str(x).strip() for x in (record_ids or []) if str(x).strip()]
    if not ids:
        return []

    from psycopg.rows import dict_row

    with service_record_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                _PG_LIST_SELECT + " WHERE sr.record_id = ANY(%s)",
                (ids,),
            )
            rows = list(cur.fetchall())
    by_id = {str(r["record_id"]): r for r in rows}
    out: list[dict[str, Any]] = []
    missing: list[str] = []
    for rid in ids:
        r = by_id.get(rid)
        if not r:
            missing.append(rid)
            continue
        case = _case_dict_from_pg_join_dict_row(r)
        src = _str(case.get("conversation_summary"))
        if not src:
            src = _str(case.get("client_reply_draft"))[:512]
        if not src:
            src = _str(case.get("issue_category"))
        case["source_text"] = src
        out.append(case)
    if missing:
        logger.warning(
            "load_workbench_queue_cases_from_postgres missing_rows=%s sample=%s",
            len(missing),
            ",".join(missing[:12]),
        )
    return out


def load_case_triage_stub_from_postgres(record_id: str) -> dict[str, Any] | None:
    """
    Triage hot path: same truth fields as :func:`load_full_case_from_postgres` for reply/routing
    without second round-trips to record_messages or state_history (no case_activity, no
    case_messages, empty source_text).
    """
    from psycopg.rows import dict_row

    rid = _str(record_id)
    if not rid:
        return None
    with service_record_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                _PG_LIST_SELECT + " WHERE sr.record_id = %s",
                (rid,),
            )
            row = cur.fetchone()
    if not row:
        return None
    case = _case_dict_from_pg_join_dict_row(row)
    case["source_text"] = ""
    return case


def delete_service_record(record_id: str) -> bool:
    """Delete one service record (child rows CASCADE). Returns True if a row was removed."""
    rid = (record_id or "").strip()
    if not rid:
        return False
    with service_record_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM service_records WHERE record_id = %s", (rid,))
            deleted = cur.rowcount or 0
        conn.commit()
        return deleted > 0
