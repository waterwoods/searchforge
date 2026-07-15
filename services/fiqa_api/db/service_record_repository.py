"""
Minimal Postgres persistence for Stage 1 service records.

Callers must ensure schema is applied (see db/schema/stage1_service_record.sql).
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Generator, Iterable

from services.fiqa_api.db.service_record_settings import service_record_database_url

logger = logging.getLogger(__name__)

# First-connection DDL: promoted office ownership column (nullable, indexed).
_OFFICE_OWNER_SCHEMA_READY = False


def _ensure_office_owner_org_schema(cur: Any) -> None:
    """Add ``office_owner_org_id`` + index when missing; backfill from ``extra.asserted_org_id``."""

    global _OFFICE_OWNER_SCHEMA_READY
    if _OFFICE_OWNER_SCHEMA_READY:
        return
    cur.execute(
        """
        ALTER TABLE service_records
        ADD COLUMN IF NOT EXISTS office_owner_org_id TEXT
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_service_records_office_owner_updated
        ON service_records (office_owner_org_id, updated_at DESC)
        """
    )
    cur.execute(
        """
        UPDATE service_records sr
        SET office_owner_org_id = TRIM(sr.extra->>'asserted_org_id')
        WHERE (office_owner_org_id IS NULL OR TRIM(office_owner_org_id) = '')
          AND sr.extra ? 'asserted_org_id'
          AND TRIM(sr.extra->>'asserted_org_id') <> ''
        """
    )
    _OFFICE_OWNER_SCHEMA_READY = True
    logger.info(
        "service_records office_owner_org_id schema verified (IFF adds column; backfill from extra)"
    )


def _office_owner_org_id_from_case(case: dict[str, Any]) -> str | None:
    raw = case.get("asserted_org_id")
    if raw is None:
        return None
    s = str(raw).strip()[:256]
    return s or None


@contextmanager
def service_record_connection() -> Generator[Any, None, None]:
    import psycopg

    url = service_record_database_url()
    if not url:
        raise RuntimeError("no service record database URL configured")
    readonly = (os.getenv("LEGACY_NEON_READONLY") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    # Short timeout so a cold-starting / transiently unreachable Postgres
    # (e.g. Neon compute wake-up, or an unroutable resolved address) fails
    # fast instead of holding a customer-facing WeCom callback open for
    # 10s+ per attempt across multiple DB calls in one message's processing.
    conn = psycopg.connect(url, connect_timeout=3)
    try:
        if readonly:
            with conn.cursor() as cur:
                cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        yield conn
    finally:
        conn.close()


def _str(v: Any, default: str = "") -> str:
    if v is None:
        return default
    return str(v).strip()


def _hydrate_case_asserted_org_id(
    case: dict[str, Any],
    office_owner_col: Any,
    extra: dict[str, Any],
) -> None:
    """Prefer promoted ``office_owner_org_id`` column; fall back to legacy ``extra.asserted_org_id``."""

    col = _str(office_owner_col)
    if col:
        case["asserted_org_id"] = col[:256]
        return
    if extra.get("asserted_org_id"):
        case["asserted_org_id"] = str(extra["asserted_org_id"]).strip()[:256]


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
        "office_case_title",
        "office_broker_next_step",
        "p16_broker_packet",
        # P18 Loop 1 — demo/workbench intelligence (JSONB pass-through; no migration)
        "workbench_tags",
        "risk_flags",
        "conflict_flags",
        "demo_summary",
        "known_facts",
        "claim_phase",
        "slice1_capability_version",
        "p20_slice1_projection",
        "p20_slice1_request_summary",
        "manual_handle",
        "urgent",
    )
    out: dict[str, Any] = {}
    for k in keys:
        if k in case:
            out[k] = case[k]
    return out


def _hydrate_extra_pilot_fields(case: dict[str, Any], extra: dict[str, Any]) -> None:
    """Merge JSONB extra bag fields into case dict (P17 evidence + conflict flags)."""
    if isinstance(extra.get("case_notes"), list):
        case["case_notes"] = extra["case_notes"]
    if isinstance(extra.get("case_attachments"), list):
        case["case_attachments"] = extra["case_attachments"]
    if "workbench_test" in extra:
        case["workbench_test"] = bool(extra.get("workbench_test"))
    if "workbench_archived" in extra:
        case["workbench_archived"] = bool(extra.get("workbench_archived"))
    if isinstance(extra.get("evidence_events"), list):
        case["evidence_events"] = extra["evidence_events"]
    if "merge_review_required" in extra:
        case["merge_review_required"] = bool(extra.get("merge_review_required"))
    if extra.get("conflict_state"):
        case["conflict_state"] = str(extra.get("conflict_state")).strip() or "none"
    if extra.get("wecom_external_userid"):
        case["wecom_external_userid"] = str(extra.get("wecom_external_userid")).strip()
    if extra.get("wecom_open_kf_id"):
        case["wecom_open_kf_id"] = str(extra.get("wecom_open_kf_id")).strip()
    if isinstance(extra.get("h5_photo_flow_state"), dict):
        case["h5_photo_flow_state"] = dict(extra.get("h5_photo_flow_state") or {})
    if isinstance(extra.get("claim_attachment_slots"), dict):
        case["claim_attachment_slots"] = dict(extra.get("claim_attachment_slots") or {})
    if extra.get("guided_workflow_state"):
        case["guided_workflow_state"] = str(extra.get("guided_workflow_state")).strip()
    if extra.get("add_vehicle_phase"):
        case["add_vehicle_phase"] = str(extra.get("add_vehicle_phase")).strip()
    if extra.get("demo_name"):
        case["demo_name"] = str(extra.get("demo_name")).strip()
    if isinstance(extra.get("demo_flags"), dict):
        case["demo_flags"] = dict(extra.get("demo_flags") or {})
    if "broker_confirmed_at" in extra:
        v = extra.get("broker_confirmed_at")
        case["broker_confirmed_at"] = str(v).strip() if v else None
    if isinstance(extra.get("claim_timeline"), list):
        case["claim_timeline"] = [e for e in extra.get("claim_timeline") or [] if isinstance(e, dict)]
    if isinstance(extra.get("claim_collision_pending"), dict):
        case["claim_collision_pending"] = dict(extra.get("claim_collision_pending") or {})
    if isinstance(extra.get("lane_switch_pending"), dict):
        case["lane_switch_pending"] = dict(extra.get("lane_switch_pending") or {})
    if isinstance(extra.get("claim_end_card_state"), dict):
        case["claim_end_card_state"] = dict(extra.get("claim_end_card_state") or {})
    if isinstance(extra.get("claim_flow_state"), dict):
        case["claim_flow_state"] = dict(extra.get("claim_flow_state") or {})
    if isinstance(extra.get("h5_intake_state"), dict):
        case["h5_intake_state"] = dict(extra.get("h5_intake_state") or {})
    if isinstance(extra.get("known_fact_provenance"), dict):
        case["known_fact_provenance"] = dict(extra.get("known_fact_provenance") or {})
    if isinstance(extra.get("known_fact_conflicts"), list):
        case["known_fact_conflicts"] = [
            item for item in extra.get("known_fact_conflicts") or [] if isinstance(item, dict)
        ]
    if "slice1_capability_version" in extra:
        try:
            case["slice1_capability_version"] = int(extra.get("slice1_capability_version") or 0)
        except (TypeError, ValueError):
            case["slice1_capability_version"] = 0
    if isinstance(extra.get("p20_slice1_projection"), dict):
        case["p20_slice1_projection"] = dict(extra.get("p20_slice1_projection") or {})
    if isinstance(extra.get("p20_slice1_request_summary"), dict):
        case["p20_slice1_request_summary"] = dict(extra.get("p20_slice1_request_summary") or {})


def _build_extra(case: dict[str, Any]) -> dict[str, Any]:
    """Small JSONB bag for pilot fields not promoted to columns yet."""
    keys = (
        "origin_session_id",
        "case_attachments",
        "case_notes",
        "formal_submitted_at",
        "workbench_test",
        "workbench_archived",
        "asserted_org_id",
        "evidence_events",
        "merge_review_required",
        "conflict_state",
        "wecom_external_userid",
        "wecom_open_kf_id",
        "h5_photo_flow_state",
        "claim_attachment_slots",
        "guided_workflow_state",
        "add_vehicle_phase",
        "demo_name",
        "demo_flags",
        "broker_confirmed_at",
        "claim_mentioned_at",
        "claim_timeline",
        "claim_collision_pending",
        "lane_switch_pending",
        "claim_end_card_state",
        "claim_flow_state",
        # P20 Track B R2/R4: explicit bounded Claim task resume and trust fields.
        "h5_intake_state",
        "known_fact_provenance",
        "known_fact_conflicts",
        # P20 Slice 1 compatibility projection; canonical truth is in companion tables.
        "slice1_capability_version",
        "p20_slice1_projection",
        "p20_slice1_request_summary",
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

    oid_col = _office_owner_org_id_from_case(case)

    with service_record_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                _ensure_office_owner_org_schema(cur)
                cur.execute(
                    """
                    INSERT INTO service_records (
                        record_id, client_id, intake_channel, issue_category, title_summary,
                        case_status, lifecycle_status, waiting_on, next_contact_by,
                        current_owner, current_next_action,
                        customer_name, customer_phone, customer_email, policy_number, contact_note,
                        origin_session_id, created_at, updated_at, closed_at,
                        office_owner_org_id, extra
                    ) VALUES (
                        %(record_id)s, %(client_id)s, %(intake_channel)s, %(issue_category)s, %(title_summary)s,
                        %(case_status)s, %(lifecycle_status)s, %(waiting_on)s, %(next_contact_by)s,
                        %(current_owner)s, %(current_next_action)s,
                        %(customer_name)s, %(customer_phone)s, %(customer_email)s, %(policy_number)s, %(contact_note)s,
                        %(origin_session_id)s, %(created_at)s, %(updated_at)s, %(closed_at)s,
                        %(office_owner_org_id)s, %(extra)s
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
                        "current_next_action": (
                            _str(case.get("office_broker_next_step"))
                            or _str(case.get("broker_next_step"))
                            or None
                        ),
                        "customer_name": _str(case.get("customer_name")),
                        "customer_phone": _str(case.get("customer_phone")),
                        "customer_email": _str(case.get("customer_email")),
                        "policy_number": _str(case.get("policy_number")),
                        "contact_note": _str(case.get("contact_note")),
                        "origin_session_id": _str(case.get("origin_session_id")) or None,
                        "created_at": now_created,
                        "updated_at": now_updated,
                        "closed_at": None,
                        "office_owner_org_id": oid_col,
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
    extra_patch = _build_extra(case)
    now_updated = _str(case.get("updated_at"))
    now_created = _str(case.get("created_at")) or now_updated

    oid_incoming = _office_owner_org_id_from_case(case) or ""

    with service_record_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                _ensure_office_owner_org_schema(cur)
                cur.execute(
                    "SELECT extra FROM service_records WHERE record_id = %s FOR UPDATE",
                    (record_id,),
                )
                existing_row = cur.fetchone()
                existing_extra = (
                    existing_row[0] if existing_row and isinstance(existing_row[0], dict) else {}
                )
                extra = {**existing_extra, **extra_patch}
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
                        office_owner_org_id = COALESCE(
                            NULLIF(TRIM(%(office_owner_patch)s), ''),
                            office_owner_org_id
                        ),
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
                        "current_next_action": (
                            _str(case.get("office_broker_next_step"))
                            or _str(case.get("broker_next_step"))
                            or None
                        ),
                        "customer_name": _str(case.get("customer_name")),
                        "customer_phone": _str(case.get("customer_phone")),
                        "customer_email": _str(case.get("customer_email")),
                        "policy_number": _str(case.get("policy_number")),
                        "contact_note": _str(case.get("contact_note")),
                        "updated_at": now_updated,
                        "office_owner_patch": oid_incoming,
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
            _ensure_office_owner_org_schema(cur)
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
                    sr.office_owner_org_id,
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

    office_owner_col = row[17]
    extra = row[18] if isinstance(row[18], dict) else {}
    structured = row[19] if isinstance(row[19], dict) else {}
    q_readiness_col = _str(row[20])

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
    elif str(case.get("lifecycle_status") or "").strip() not in ("collecting", "handoff_pending"):
        case["formal_submitted_at"] = case["created_at"]
    else:
        case["formal_submitted_at"] = ""

    if isinstance(extra.get("case_notes"), list):
        case["case_notes"] = extra["case_notes"]
    if isinstance(extra.get("case_attachments"), list):
        case["case_attachments"] = extra["case_attachments"]
    if "workbench_test" in extra:
        case["workbench_test"] = bool(extra.get("workbench_test"))
    if "workbench_archived" in extra:
        case["workbench_archived"] = bool(extra.get("workbench_archived"))
    _hydrate_extra_pilot_fields(case, extra)
    _hydrate_case_asserted_org_id(case, office_owner_col, extra)

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


_PG_OFFICE_LIST_FILTER = """
(
  (
    NULLIF(TRIM(COALESCE(sr.office_owner_org_id, sr.extra->>'asserted_org_id')), '') IS NULL
    AND NOT %(strict)s
  )
  OR NULLIF(TRIM(COALESCE(sr.office_owner_org_id, sr.extra->>'asserted_org_id')), '') = %(req_org)s
)
"""


def count_service_records_office_scoped(req_org: str, strict_exclude_unstamped: bool) -> int:
    """Row count for GET /cases under office enforcement (matches :func:`case_visible_in_office_list`)."""

    org = (req_org or "").strip()[:256]
    if not org:
        return 0
    with service_record_connection() as conn:
        with conn.cursor() as cur:
            _ensure_office_owner_org_schema(cur)
            cur.execute(
                f"SELECT COUNT(*) FROM service_records sr WHERE {_PG_OFFICE_LIST_FILTER}",
                {"strict": strict_exclude_unstamped, "req_org": org},
            )
            row = cur.fetchone()
            return int(row[0] or 0) if row else 0


def list_record_ids_office_scoped(
    req_org: str,
    strict_exclude_unstamped: bool,
    limit: int,
    offset: int,
) -> list[str]:
    """Indexed-path record ids for office-scoped workbench lists (newest first)."""

    org = (req_org or "").strip()[:256]
    if not org:
        return []
    safe = max(1, min(int(limit or 8), 500))
    safe_offset = max(0, min(int(offset or 0), 10_000))
    with service_record_connection() as conn:
        with conn.cursor() as cur:
            _ensure_office_owner_org_schema(cur)
            cur.execute(
                f"""
                SELECT sr.record_id FROM service_records sr
                WHERE {_PG_OFFICE_LIST_FILTER}
                ORDER BY sr.updated_at DESC
                LIMIT %(lim)s OFFSET %(off)s
                """,
                {
                    "strict": strict_exclude_unstamped,
                    "req_org": org,
                    "lim": safe,
                    "off": safe_offset,
                },
            )
            return [str(r[0]) for r in cur.fetchall()]


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
                    sr.office_owner_org_id,
                    sr.extra,
                    srd.structured_payload,
                    srd.quote_readiness
                FROM service_records sr
                LEFT JOIN structured_record_data srd ON srd.record_id = sr.record_id
"""


def list_binding_stub_rows_recent(limit: int, offset: int = 0) -> list[dict[str, Any]]:
    """
    One round-trip: rows shaped for :func:`resolve_active_case` / :func:`is_case_open_for_binding`,
    with the same **triage stub** payload as :func:`load_case_triage_stub_from_postgres` (join +
    structured fields, **no** ``record_messages`` / ``state_history``). Enables the inbox route to
    reuse one row as ``existing_case`` and skip a duplicate stub read for the same ``case_id``.
    """
    from psycopg.rows import dict_row

    safe = max(1, min(int(limit or 8), 500))
    safe_offset = max(0, min(int(offset or 0), 10_000))
    out: list[dict[str, Any]] = []
    with service_record_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            _ensure_office_owner_org_schema(cur)
            cur.execute(
                _PG_LIST_SELECT
                + """
                ORDER BY sr.updated_at DESC
                LIMIT %s OFFSET %s
                """,
                (safe, safe_offset),
            )
            for row in cur.fetchall():
                case = _case_dict_from_pg_join_dict_row(row)
                case["source_text"] = ""
                rid = str(case.get("case_id") or "").strip()
                if rid:
                    out.append(case)
    return out


def list_binding_stub_rows_office_scoped(
    req_org: str,
    strict_exclude_unstamped: bool,
    limit: int,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Same stub shape as :func:`list_binding_stub_rows_recent`, filtered by office ownership hint
    (matches :func:`case_visible_in_office_list` / GET /cases enforcement semantics).
    """
    from psycopg.rows import dict_row

    org = (req_org or "").strip()[:256]
    if not org:
        return []
    safe = max(1, min(int(limit or 8), 500))
    safe_offset = max(0, min(int(offset or 0), 10_000))
    out: list[dict[str, Any]] = []
    with service_record_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            _ensure_office_owner_org_schema(cur)
            cur.execute(
                _PG_LIST_SELECT
                + f"""
                WHERE {_PG_OFFICE_LIST_FILTER}
                ORDER BY sr.updated_at DESC
                LIMIT %(lim)s OFFSET %(off)s
                """,
                {
                    "strict": strict_exclude_unstamped,
                    "req_org": org,
                    "lim": safe,
                    "off": safe_offset,
                },
            )
            for row in cur.fetchall():
                case = _case_dict_from_pg_join_dict_row(row)
                case["source_text"] = ""
                rid = str(case.get("case_id") or "").strip()
                if rid:
                    out.append(case)
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
    col_action = _str(row.get("current_next_action"))
    case["broker_next_step"] = _str(structured.get("broker_next_step")) or col_action
    if not _str(case.get("office_broker_next_step")) and col_action:
        case["office_broker_next_step"] = col_action
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
    elif str(case.get("lifecycle_status") or "").strip() not in ("collecting", "handoff_pending"):
        case["formal_submitted_at"] = case["created_at"]
    else:
        case["formal_submitted_at"] = ""

    if isinstance(extra.get("case_notes"), list):
        case["case_notes"] = extra["case_notes"]
    if isinstance(extra.get("case_attachments"), list):
        case["case_attachments"] = extra["case_attachments"]
    if "workbench_test" in extra:
        case["workbench_test"] = bool(extra.get("workbench_test"))
    if "workbench_archived" in extra:
        case["workbench_archived"] = bool(extra.get("workbench_archived"))
    _hydrate_extra_pilot_fields(case, extra)
    _hydrate_case_asserted_org_id(case, row.get("office_owner_org_id"), extra)

    if q_readiness_col:
        case["quote_ready_status"] = q_readiness_col
    elif "quote_ready_status" not in case:
        case["quote_ready_status"] = ""

    case["case_messages"] = []
    case["case_activity"] = []
    return case


def list_binding_stub_rows_by_phone_digits(phone_digits: str, limit: int = 24) -> list[dict[str, Any]]:
    """
    Postgres stub rows whose customer_phone normalizes to the given 10-digit US number.
    """
    from psycopg.rows import dict_row

    digits = "".join(ch for ch in (phone_digits or "") if ch.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return []

    safe = max(1, min(int(limit or 24), 50))
    eleven = f"1{digits}"
    out: list[dict[str, Any]] = []
    with service_record_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            _ensure_office_owner_org_schema(cur)
            cur.execute(
                _PG_LIST_SELECT
                + """
                WHERE regexp_replace(coalesce(sr.customer_phone, ''), '[^0-9]', '', 'g') IN (%s, %s)
                ORDER BY sr.updated_at DESC
                LIMIT %s
                """,
                (digits, eleven, safe),
            )
            for row in cur.fetchall():
                case = _case_dict_from_pg_join_dict_row(row)
                case["source_text"] = ""
                rid = str(case.get("case_id") or "").strip()
                if rid:
                    out.append(case)
    return out


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
            _ensure_office_owner_org_schema(cur)
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
            _ensure_office_owner_org_schema(cur)
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


# Tables cleared by P20 Track C QA reset (no schema drop). service_records CASCADE
# removes record_messages, structured_record_data, state_history, office_actions.
_PURGE_AUX_TABLES = (
    "wecom_message_processed",
    "wecom_reply_outbox",
    "wecom_inbox_events",
    "wecom_sync_cursors",
    "intake_sessions",
)


def purge_case_domain_data(*, dry_run: bool = False) -> dict[str, int]:
    """Delete all Case-domain QA rows. Idempotent. Preserves schema and config tables."""

    counts: dict[str, int] = {}
    with service_record_connection() as conn:
        with conn.cursor() as cur:
            for table in _PURGE_AUX_TABLES:
                if dry_run:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    counts[table] = int(cur.fetchone()[0] or 0)
                else:
                    cur.execute(f"DELETE FROM {table}")
                    counts[table] = int(cur.rowcount or 0)
            if dry_run:
                cur.execute("SELECT COUNT(*) FROM service_records")
                counts["service_records"] = int(cur.fetchone()[0] or 0)
            else:
                cur.execute("DELETE FROM service_records")
                counts["service_records"] = int(cur.rowcount or 0)
        if not dry_run:
            conn.commit()
    return counts


# ---------------------------------------------------------------------------
# P20 Slice 1 — narrow transactional command storage
# ---------------------------------------------------------------------------

_SLICE1_SCHEMA_READY = False


def _ensure_slice1_schema(cur: Any) -> None:
    """Create the Slice 1 companion schema when migrations have not been pre-applied."""

    global _SLICE1_SCHEMA_READY
    if _SLICE1_SCHEMA_READY:
        return
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS claim_slice1_aggregates (
            case_id TEXT PRIMARY KEY REFERENCES service_records (record_id) ON DELETE CASCADE,
            workflow_state TEXT NOT NULL,
            aggregate_version INTEGER NOT NULL DEFAULT 0,
            active_request_id TEXT,
            customer_projection JSONB NOT NULL DEFAULT '{}'::jsonb,
            broker_projection JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS claim_request_groups (
            request_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL REFERENCES service_records (record_id) ON DELETE CASCADE,
            status TEXT NOT NULL,
            reason TEXT NOT NULL DEFAULT '',
            created_by TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_request_groups_one_open
        ON claim_request_groups (case_id)
        WHERE status = 'open'
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS claim_request_items (
            request_item_id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL REFERENCES claim_request_groups (request_id) ON DELETE CASCADE,
            case_id TEXT NOT NULL REFERENCES service_records (record_id) ON DELETE CASCADE,
            item_type TEXT NOT NULL,
            label TEXT NOT NULL,
            instructions TEXT NOT NULL DEFAULT '',
            required BOOLEAN NOT NULL DEFAULT true,
            position INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            satisfied_at TIMESTAMPTZ,
            satisfied_by_event_id TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_request_items_position
        ON claim_request_items (request_id, position)
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS claim_slice1_events (
            event_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL REFERENCES service_records (record_id) ON DELETE CASCADE,
            event_type TEXT NOT NULL,
            command_id TEXT NOT NULL,
            correlation_id TEXT NOT NULL,
            sequence_number INTEGER NOT NULL,
            aggregate_version INTEGER NOT NULL,
            expected_state_version INTEGER,
            actor TEXT NOT NULL,
            actor_identity TEXT NOT NULL,
            state_before TEXT NOT NULL,
            state_after TEXT NOT NULL,
            visibility TEXT NOT NULL,
            evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
            idempotency_key TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_slice1_events_sequence
        ON claim_slice1_events (case_id, sequence_number)
        """
    )
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_slice1_events_command_type
        ON claim_slice1_events (case_id, command_id, event_type)
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS claim_slice1_command_outcomes (
            outcome_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            case_id TEXT NOT NULL REFERENCES service_records (record_id) ON DELETE CASCADE,
            actor_identity TEXT NOT NULL,
            command_id TEXT NOT NULL,
            correlation_id TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            command_type TEXT NOT NULL,
            outcome TEXT NOT NULL,
            aggregate_version INTEGER NOT NULL,
            event_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
            response JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_slice1_command_outcome_idempotency
        ON claim_slice1_command_outcomes (case_id, actor_identity, idempotency_key)
        """
    )
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_slice1_command_outcome_command
        ON claim_slice1_command_outcomes (case_id, command_id)
        """
    )
    _SLICE1_SCHEMA_READY = True


def _slice1_iso(val: Any) -> str:
    if val is None:
        return ""
    if hasattr(val, "isoformat"):
        s = val.isoformat()
        return s.replace("+00:00", "Z") if s.endswith("+00:00") else s
    return str(val)


class _PostgresSlice1Store:
    """Postgres-backed Slice 1 store; domain decisions remain in the command service."""

    def _case_from_row(self, row: dict[str, Any]) -> dict[str, Any]:
        extra = row.get("extra") if isinstance(row.get("extra"), dict) else {}
        structured = row.get("structured_payload") if isinstance(row.get("structured_payload"), dict) else {}
        case: dict[str, Any] = {}
        case.update(structured)
        case.update(extra)
        case["case_id"] = str(row.get("record_id") or "")
        if row.get("client_id"):
            case["client_id"] = str(row.get("client_id") or "").strip()
        case["lifecycle_status"] = _str(row.get("lifecycle_status"))
        case["updated_at"] = _slice1_iso(row.get("updated_at"))
        case["broker_next_step"] = _str(row.get("current_next_action")) or _str(case.get("broker_next_step"))
        return case

    def _snapshot(self, cur: Any, case_id: str, *, lock_case: bool) -> Any:
        from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
            Slice1Aggregate,
            Slice1Group,
            Slice1Item,
            Slice1Snapshot,
        )

        lock_sql = " FOR UPDATE OF sr" if lock_case else ""
        cur.execute(
            """
            SELECT
                sr.record_id,
                sr.client_id,
                sr.lifecycle_status,
                sr.updated_at,
                sr.current_next_action,
                sr.extra,
                srd.structured_payload
            FROM service_records sr
            LEFT JOIN structured_record_data srd ON srd.record_id = sr.record_id
            WHERE sr.record_id = %s
            """
            + lock_sql,
            (case_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        case = self._case_from_row(dict(row))

        cur.execute(
            """
            SELECT case_id, workflow_state, aggregate_version, active_request_id,
                   customer_projection, broker_projection
            FROM claim_slice1_aggregates
            WHERE case_id = %s
            FOR UPDATE
            """,
            (case_id,),
        )
        agg_row = cur.fetchone()
        aggregate = None
        if agg_row:
            a = dict(agg_row)
            aggregate = Slice1Aggregate(
                case_id=str(a["case_id"]),
                workflow_state=str(a["workflow_state"]),
                aggregate_version=int(a["aggregate_version"] or 0),
                active_request_id=_str(a.get("active_request_id")) or None,
                customer_projection=a.get("customer_projection") if isinstance(a.get("customer_projection"), dict) else {},
                broker_projection=a.get("broker_projection") if isinstance(a.get("broker_projection"), dict) else {},
            )

        cur.execute(
            """
            SELECT request_id, case_id, status, reason, created_by, created_at, completed_at, updated_at
            FROM claim_request_groups
            WHERE case_id = %s AND status = 'open'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (case_id,),
        )
        group_row = cur.fetchone()
        group = None
        if group_row:
            g = dict(group_row)
            group = Slice1Group(
                request_id=str(g["request_id"]),
                case_id=str(g["case_id"]),
                status=str(g["status"]),
                reason=str(g.get("reason") or ""),
                created_by=str(g.get("created_by") or ""),
                created_at=_slice1_iso(g.get("created_at")),
                updated_at=_slice1_iso(g.get("updated_at")),
                completed_at=_slice1_iso(g.get("completed_at")) or None,
            )
        elif aggregate and aggregate.active_request_id:
            cur.execute(
                """
                SELECT request_id, case_id, status, reason, created_by, created_at, completed_at, updated_at
                FROM claim_request_groups
                WHERE request_id = %s
                """,
                (aggregate.active_request_id,),
            )
            group_row = cur.fetchone()
            if group_row:
                g = dict(group_row)
                group = Slice1Group(
                    request_id=str(g["request_id"]),
                    case_id=str(g["case_id"]),
                    status=str(g["status"]),
                    reason=str(g.get("reason") or ""),
                    created_by=str(g.get("created_by") or ""),
                    created_at=_slice1_iso(g.get("created_at")),
                    updated_at=_slice1_iso(g.get("updated_at")),
                    completed_at=_slice1_iso(g.get("completed_at")) or None,
                )

        items: list[Slice1Item] = []
        if group:
            cur.execute(
                """
                SELECT request_item_id, request_id, case_id, item_type, label, instructions,
                       required, position, status, created_at, satisfied_at, satisfied_by_event_id
                FROM claim_request_items
                WHERE request_id = %s
                ORDER BY position ASC
                """,
                (group.request_id,),
            )
            for raw_item in cur.fetchall():
                i = dict(raw_item)
                items.append(
                    Slice1Item(
                        request_item_id=str(i["request_item_id"]),
                        request_id=str(i["request_id"]),
                        case_id=str(i["case_id"]),
                        item_type=str(i["item_type"]),
                        label=str(i["label"]),
                        instructions=str(i.get("instructions") or ""),
                        required=bool(i.get("required")),
                        position=int(i["position"]),
                        status=str(i["status"]),
                        created_at=_slice1_iso(i.get("created_at")),
                        satisfied_at=_slice1_iso(i.get("satisfied_at")) or None,
                        satisfied_by_event_id=_str(i.get("satisfied_by_event_id")) or None,
                    )
                )

        cur.execute(
            """
            SELECT event_id, case_id, event_type, command_id, correlation_id, sequence_number,
                   aggregate_version, expected_state_version, actor, actor_identity,
                   state_before, state_after, visibility, evidence, idempotency_key, created_at
            FROM claim_slice1_events
            WHERE case_id = %s
            ORDER BY sequence_number ASC
            LIMIT 100
            """,
            (case_id,),
        )
        events = []
        for raw_event in cur.fetchall():
            e = dict(raw_event)
            e["created_at"] = _slice1_iso(e.get("created_at"))
            events.append(e)
        return Slice1Snapshot(case=case, aggregate=aggregate, group=group, items=items, latest_events=events)

    def read_snapshot(self, case_id: str) -> Any:
        from psycopg.rows import dict_row

        cid = _str(case_id)
        if not cid:
            return None
        with service_record_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                _ensure_office_owner_org_schema(cur)
                _ensure_slice1_schema(cur)
                return self._snapshot(cur, cid, lock_case=False)

    def accept(
        self,
        *,
        case_id: str,
        actor_identity: str,
        command_id: str,
        idempotency_key: str,
        command_type: str,
        handler: Any,
    ) -> dict[str, Any]:
        from psycopg.rows import dict_row
        from psycopg.types.json import Json

        cid = _str(case_id)
        if not cid:
            raise ValueError("case_id_required")
        with service_record_connection() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    _ensure_office_owner_org_schema(cur)
                    _ensure_slice1_schema(cur)
                    snapshot = self._snapshot(cur, cid, lock_case=True)
                    if snapshot is None:
                        raise ValueError("case_not_found")
                    cur.execute(
                        """
                        SELECT response
                        FROM claim_slice1_command_outcomes
                        WHERE case_id = %s
                          AND (
                            (actor_identity = %s AND idempotency_key = %s)
                            OR command_id = %s
                          )
                        ORDER BY created_at ASC
                        LIMIT 1
                        """,
                        (cid, actor_identity, idempotency_key, command_id),
                    )
                    prior = cur.fetchone()
                    if prior and isinstance(prior.get("response"), dict):
                        setattr(snapshot, "stored_outcome", prior["response"])
                        return handler(self, snapshot)

                    self._cur = cur
                    response = handler(self, snapshot)
                    event_ids = [str(x) for x in (response.get("event_ids") or []) if str(x)]
                    cur.execute(
                        """
                        INSERT INTO claim_slice1_command_outcomes (
                            case_id, actor_identity, command_id, correlation_id, idempotency_key,
                            command_type, outcome, aggregate_version, event_ids, response
                        ) VALUES (
                            %(case_id)s, %(actor_identity)s, %(command_id)s, %(correlation_id)s,
                            %(idempotency_key)s, %(command_type)s, %(outcome)s,
                            %(aggregate_version)s, %(event_ids)s, %(response)s
                        )
                        """,
                        {
                            "case_id": cid,
                            "actor_identity": actor_identity,
                            "command_id": command_id,
                            "correlation_id": str(response.get("correlation_id") or command_id),
                            "idempotency_key": idempotency_key,
                            "command_type": command_type,
                            "outcome": str(response.get("outcome") or ""),
                            "aggregate_version": int(response.get("aggregate_version") or 0),
                            "event_ids": event_ids,
                            "response": Json(response),
                        },
                    )
                    return response

    def insert_group(self, group: Any) -> None:
        self._cur.execute(
            """
            INSERT INTO claim_request_groups (
                request_id, case_id, status, reason, created_by, created_at, completed_at, updated_at
            ) VALUES (
                %(request_id)s, %(case_id)s, %(status)s, %(reason)s, %(created_by)s,
                %(created_at)s, %(completed_at)s, %(updated_at)s
            )
            """,
            group.__dict__,
        )

    def insert_items(self, items: list[Any]) -> None:
        for item in items:
            self._cur.execute(
                """
                INSERT INTO claim_request_items (
                    request_item_id, request_id, case_id, item_type, label, instructions,
                    required, position, status, created_at, satisfied_at, satisfied_by_event_id
                ) VALUES (
                    %(request_item_id)s, %(request_id)s, %(case_id)s, %(item_type)s, %(label)s,
                    %(instructions)s, %(required)s, %(position)s, %(status)s, %(created_at)s,
                    %(satisfied_at)s, %(satisfied_by_event_id)s
                )
                """,
                item.__dict__,
            )

    def update_items(self, items: list[Any]) -> None:
        for item in items:
            self._cur.execute(
                """
                UPDATE claim_request_items SET
                    status = %(status)s,
                    satisfied_at = %(satisfied_at)s,
                    satisfied_by_event_id = %(satisfied_by_event_id)s
                WHERE request_item_id = %(request_item_id)s
                """,
                item.__dict__,
            )

    def update_group(self, group: Any) -> None:
        self._cur.execute(
            """
            UPDATE claim_request_groups SET
                status = %(status)s,
                reason = %(reason)s,
                completed_at = %(completed_at)s,
                updated_at = %(updated_at)s
            WHERE request_id = %(request_id)s
            """,
            group.__dict__,
        )

    def insert_events(self, events: list[dict[str, Any]]) -> None:
        from psycopg.types.json import Json

        for event in events:
            payload = dict(event)
            payload["evidence"] = Json(payload.get("evidence") if isinstance(payload.get("evidence"), dict) else {})
            self._cur.execute(
                """
                INSERT INTO claim_slice1_events (
                    event_id, case_id, event_type, command_id, correlation_id, sequence_number,
                    aggregate_version, expected_state_version, actor, actor_identity,
                    state_before, state_after, visibility, evidence, idempotency_key, created_at
                ) VALUES (
                    %(event_id)s, %(case_id)s, %(event_type)s, %(command_id)s, %(correlation_id)s,
                    %(sequence_number)s, %(aggregate_version)s, %(expected_state_version)s,
                    %(actor)s, %(actor_identity)s, %(state_before)s, %(state_after)s,
                    %(visibility)s, %(evidence)s, %(idempotency_key)s, %(created_at)s
                )
                """,
                payload,
            )

    def upsert_aggregate(self, aggregate: Any) -> None:
        from psycopg.types.json import Json

        self._cur.execute(
            """
            INSERT INTO claim_slice1_aggregates (
                case_id, workflow_state, aggregate_version, active_request_id,
                customer_projection, broker_projection, updated_at
            ) VALUES (
                %(case_id)s, %(workflow_state)s, %(aggregate_version)s, %(active_request_id)s,
                %(customer_projection)s, %(broker_projection)s, now()
            )
            ON CONFLICT (case_id) DO UPDATE SET
                workflow_state = EXCLUDED.workflow_state,
                aggregate_version = EXCLUDED.aggregate_version,
                active_request_id = EXCLUDED.active_request_id,
                customer_projection = EXCLUDED.customer_projection,
                broker_projection = EXCLUDED.broker_projection,
                updated_at = now()
            """,
            {
                "case_id": aggregate.case_id,
                "workflow_state": aggregate.workflow_state,
                "aggregate_version": aggregate.aggregate_version,
                "active_request_id": aggregate.active_request_id,
                "customer_projection": Json(aggregate.customer_projection),
                "broker_projection": Json(aggregate.broker_projection),
            },
        )

    def update_legacy_projection(self, case_id: str, patch: dict[str, Any]) -> None:
        from psycopg.types.json import Json

        cid = _str(case_id)
        # psycopg Json() adapts as json; Cloud SQL columns are jsonb — cast for ||.
        self._cur.execute(
            """
            UPDATE service_records SET
                lifecycle_status = COALESCE(NULLIF(%(lifecycle_status)s, ''), lifecycle_status),
                current_next_action = COALESCE(NULLIF(%(current_next_action)s, ''), current_next_action),
                updated_at = now(),
                extra = COALESCE(extra, '{}'::jsonb) || %(extra_patch)s::jsonb
            WHERE record_id = %(case_id)s
            """,
            {
                "case_id": cid,
                "lifecycle_status": _str(patch.get("claim_phase")),
                "current_next_action": _str(patch.get("broker_next_step")),
                "extra_patch": Json(patch),
            },
        )
        self._cur.execute(
            """
            UPDATE structured_record_data SET
                structured_payload = COALESCE(structured_payload, '{}'::jsonb) || %(structured_patch)s::jsonb,
                updated_at = now()
            WHERE record_id = %(case_id)s
            """,
            {"case_id": cid, "structured_patch": Json(patch)},
        )


def make_slice1_postgres_store() -> _PostgresSlice1Store:
    if not service_record_database_url():
        raise RuntimeError("p20_slice1_requires_service_record_database_url")
    return _PostgresSlice1Store()


_PG_CLIENT_LIST_FILTER = """
(
  (
    NULLIF(TRIM(sr.client_id), '') IS NULL
    AND NOT %(strict)s
  )
  OR NULLIF(TRIM(sr.client_id), '') = %(req_client)s
)
"""


def count_service_records_client_scoped(req_client: str, strict_exclude_unstamped: bool) -> int:
    """Row count for GET /cases under client enforcement."""

    cid = (req_client or "").strip()[:128]
    if not cid:
        return 0
    with service_record_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) FROM service_records sr WHERE {_PG_CLIENT_LIST_FILTER}",
                {"strict": strict_exclude_unstamped, "req_client": cid},
            )
            row = cur.fetchone()
            return int(row[0] or 0) if row else 0


def list_record_ids_client_scoped(
    req_client: str,
    strict_exclude_unstamped: bool,
    limit: int,
    offset: int,
) -> list[str]:
    """Indexed-path record ids for client-scoped workbench lists (newest first)."""

    cid = (req_client or "").strip()[:128]
    if not cid:
        return []
    safe = max(1, min(int(limit or 8), 500))
    safe_offset = max(0, min(int(offset or 0), 10_000))
    with service_record_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT sr.record_id FROM service_records sr
                WHERE {_PG_CLIENT_LIST_FILTER}
                ORDER BY sr.updated_at DESC
                LIMIT %(lim)s OFFSET %(off)s
                """,
                {
                    "strict": strict_exclude_unstamped,
                    "req_client": cid,
                    "lim": safe,
                    "off": safe_offset,
                },
            )
            return [str(r[0]) for r in cur.fetchall()]
