"""
Vehicle entity persistence (MVP) — Postgres JSONB, single active vehicle per session.

Schema: services/fiqa_api/db/schema/intake_entities.sql
Contract: docs/VEHICLE_ENTITY_MEMORY_MVP.md
"""

from __future__ import annotations

import json
import logging
from typing import Any

from services.fiqa_api.db.service_record_repository import service_record_connection
from services.fiqa_api.db.service_record_settings import service_record_database_url

logger = logging.getLogger(__name__)

ENTITY_TYPE_VEHICLE = "vehicle"


def _stable_vehicle_entity_id(session_id: str) -> str:
    return f"veh:{session_id}"


_VEHICLE_SCALAR_KEYS = frozenset({"year", "make", "model", "vin", "zip", "driver"})


def _merge_payload(existing: Any, incoming: dict[str, Any]) -> dict[str, Any]:
    """Shallow dict merge: incoming overwrites; nested dicts under confidence merged.

    Vehicle scalars: empty/whitespace strings do not clobber non-empty stored values.
    VIN: non-empty incoming always wins (normalized uppercase).
    """
    base: dict[str, Any] = {}
    if isinstance(existing, dict):
        base = dict(existing)
    for k, v in incoming.items():
        if v is None:
            continue
        if k == "vin" and isinstance(v, str) and v.strip():
            base["vin"] = v.strip().upper()
            continue
        if k in _VEHICLE_SCALAR_KEYS:
            if isinstance(v, str) and not v.strip():
                continue
        if k == "confidence" and isinstance(v, dict) and isinstance(base.get("confidence"), dict):
            base["confidence"] = {**base["confidence"], **v}
        elif isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = {**base[k], **v}
        else:
            base[k] = v
    return base


def get_active_vehicle(session_id: str) -> dict[str, Any] | None:
    """Return the active vehicle entity row for this session, or None."""
    sid = (session_id or "").strip()
    if not sid:
        return None
    if not service_record_database_url():
        return None
    from psycopg.rows import dict_row

    with service_record_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, session_id, case_id, entity_type, entity_id, payload, is_active, updated_at
                FROM intake_entities
                WHERE session_id = %s AND entity_type = %s AND is_active = true
                ORDER BY id DESC
                LIMIT 1
                """,
                (sid, ENTITY_TYPE_VEHICLE),
            )
            row = cur.fetchone()
    if not row:
        return None
    out = dict(row)
    p = out.get("payload")
    if isinstance(p, (bytes, str)):
        try:
            out["payload"] = json.loads(p)
        except (json.JSONDecodeError, TypeError):
            out["payload"] = {}
    return out


def _upsert_vehicle_entity(
    session_id: str,
    payload: dict[str, Any],
    *,
    case_id: str | None = None,
) -> None:
    sid = (session_id or "").strip()
    if not sid:
        raise ValueError("session_id is required")
    if not service_record_database_url():
        raise RuntimeError("no service record database URL configured")
    from psycopg.types.json import Json

    eid = _stable_vehicle_entity_id(sid)
    with service_record_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, payload FROM intake_entities
                    WHERE session_id = %s AND entity_type = %s AND is_active = true
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (sid, ENTITY_TYPE_VEHICLE),
                )
                found = cur.fetchone()
                merged = _merge_payload(found[1] if found else None, payload)
                if found:
                    cid = (case_id or "").strip() or None
                    cur.execute(
                        """
                        UPDATE intake_entities
                        SET payload = %s,
                            case_id = COALESCE(%s, case_id),
                            updated_at = now()
                        WHERE id = %s
                        """,
                        (Json(merged), cid, found[0]),
                    )
                else:
                    cid_ins = (case_id or "").strip() or None
                    cur.execute(
                        """
                        INSERT INTO intake_entities
                            (session_id, case_id, entity_type, entity_id, payload, is_active, updated_at)
                        VALUES (%s, %s, %s, %s, %s, true, now())
                        """,
                        (sid, cid_ins, ENTITY_TYPE_VEHICLE, eid, Json(merged)),
                    )


def save_vehicle_entity(session_id: str, payload: dict[str, Any], case_id: str | None = None) -> None:
    """Create or replace-merge the active vehicle entity for this session."""
    _upsert_vehicle_entity(session_id, payload, case_id=case_id)


def update_vehicle_entity(session_id: str, payload: dict[str, Any], case_id: str | None = None) -> None:
    """Merge `payload` into the active vehicle entity (same as save for MVP)."""
    _upsert_vehicle_entity(session_id, payload, case_id=case_id)
