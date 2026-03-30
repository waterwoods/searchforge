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
        "case_creation_suggested",
        "human_confirmation_required",
        "human_confirmation_fields",
        "collection_stage",
        "follow_up_type",
        "next_best_question",
        "lifecycle_status",
        "case_boundary",
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
                    logger.warning("persist_case_append: no service_records row for %s", record_id)
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
