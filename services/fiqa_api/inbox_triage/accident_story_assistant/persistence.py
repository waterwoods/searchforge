"""Durable proposal + idempotency persistence for Accident Story (no Claim lifecycle).

Layers:
- ephemeral process cache (fast replay)
- durable backend (Postgres when configured; in-process durable memory otherwise)

Never stores phones/OpenIDs. Proposal payload may include customer story text only
because it is required to reconstruct the AI draft server-side.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

PROPOSAL_TABLE = "accident_story_proposals"
IDEMPOTENCY_TABLE = "accident_story_idempotency"

# Editable customer fields only — never trust arbitrary client keys.
ALLOWED_CUSTOMER_EDIT_KEYS: frozenset[str] = frozenset(
    {
        "incident_summary",
        "injury_status",
        "accident_time_text",
        "accident_location_text",
        "raw_story",
    }
)

_lock = threading.RLock()
_ephemeral_idem: dict[str, dict[str, Any]] = {}
_durable_memory_idem: dict[str, dict[str, Any]] = {}
_durable_memory_proposals: dict[str, dict[str, Any]] = {}

# Default retention for proposal + idempotency rows (hours).
_DEFAULT_TTL_HOURS = 72


def reset_accident_story_ephemeral_for_tests() -> None:
    """Clear process-local replay cache only (durable memory remains)."""
    with _lock:
        _ephemeral_idem.clear()


def reset_accident_story_durable_memory_for_tests() -> None:
    """Clear in-memory durable backends (tests without Postgres)."""
    with _lock:
        _durable_memory_idem.clear()
        _durable_memory_proposals.clear()


def reset_accident_story_persistence_for_tests() -> None:
    reset_accident_story_ephemeral_for_tests()
    reset_accident_story_durable_memory_for_tests()


def _pg_enabled() -> bool:
    try:
        from services.fiqa_api.db.service_record_settings import service_record_database_url

        return bool(service_record_database_url())
    except Exception:
        return False


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def request_digest(payload: dict[str, Any]) -> str:
    """Stable non-PII digest of request-critical fields (hashed)."""
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def story_digest(raw_story: str) -> str:
    return hashlib.sha256(str(raw_story or "").encode("utf-8")).hexdigest()


def filter_customer_edits(edits: dict[str, Any] | None) -> dict[str, Any]:
    """Allowlist + schema clamp for customer edits."""
    src = edits if isinstance(edits, dict) else {}
    out: dict[str, Any] = {}
    for key in ALLOWED_CUSTOMER_EDIT_KEYS:
        if key not in src:
            continue
        val = src.get(key)
        if val is None:
            continue
        text = str(val).strip()
        if key == "injury_status":
            low = text.lower()
            if low not in ("yes", "no", "unknown"):
                continue
            out[key] = low
        elif key == "raw_story":
            out[key] = text[:2000]
        elif key == "incident_summary":
            out[key] = text[:500]
        elif key == "accident_time_text":
            out[key] = text[:120]
        elif key == "accident_location_text":
            out[key] = text[:500]
    return out


def _ensure_tables(conn: Any) -> None:
    prev = bool(getattr(conn, "autocommit", False))
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {PROPOSAL_TABLE} (
                    proposal_id TEXT PRIMARY KEY,
                    proposal_version INT NOT NULL DEFAULT 1,
                    case_id TEXT,
                    session_id TEXT,
                    office_id TEXT,
                    story_digest TEXT NOT NULL,
                    proposal_json JSONB NOT NULL,
                    status TEXT NOT NULL DEFAULT 'proposed',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    expires_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_accident_story_proposals_case
                ON {PROPOSAL_TABLE} (case_id)
                """
            )
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {IDEMPOTENCY_TABLE} (
                    idem_key TEXT PRIMARY KEY,
                    request_digest TEXT NOT NULL,
                    response_json JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    expires_at TIMESTAMPTZ NOT NULL
                )
                """
            )
    finally:
        try:
            conn.autocommit = prev
        except Exception:
            pass


def store_proposal_record(
    *,
    proposal: dict[str, Any],
    case_id: str | None = None,
    session_id: str | None = None,
    office_id: str | None = None,
    ttl_hours: int = _DEFAULT_TTL_HOURS,
) -> dict[str, Any]:
    """Persist server-authoritative proposal; return ids stamped onto a copy."""
    proposal_id = str(proposal.get("proposal_id") or "").strip() or f"asp_{uuid.uuid4().hex[:20]}"
    version = int(proposal.get("proposal_version") or 1)
    now = _utc_now()
    expires = now + timedelta(hours=max(1, min(int(ttl_hours), 168)))
    record = {
        "proposal_id": proposal_id,
        "proposal_version": version,
        "case_id": str(case_id or "").strip() or None,
        "session_id": str(session_id or "").strip() or None,
        "office_id": str(office_id or "").strip() or None,
        "story_digest": story_digest(str(proposal.get("raw_story") or "")),
        "proposal": deepcopy(proposal),
        "status": "proposed",
        "created_at": _iso(now),
        "expires_at": _iso(expires),
    }
    # Stamp ids onto stored proposal body.
    record["proposal"]["proposal_id"] = proposal_id
    record["proposal"]["proposal_version"] = version

    with _lock:
        _durable_memory_proposals[proposal_id] = deepcopy(record)

    if _pg_enabled():
        try:
            from psycopg.types.json import Json

            from services.fiqa_api.db.service_record_repository import service_record_connection

            with service_record_connection() as conn:
                _ensure_tables(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {PROPOSAL_TABLE} (
                            proposal_id, proposal_version, case_id, session_id, office_id,
                            story_digest, proposal_json, status, created_at, expires_at
                        ) VALUES (
                            %(proposal_id)s, %(proposal_version)s, %(case_id)s, %(session_id)s,
                            %(office_id)s, %(story_digest)s, %(proposal_json)s, %(status)s,
                            %(created_at)s::timestamptz, %(expires_at)s::timestamptz
                        )
                        ON CONFLICT (proposal_id) DO UPDATE SET
                            proposal_json = EXCLUDED.proposal_json,
                            case_id = COALESCE(EXCLUDED.case_id, {PROPOSAL_TABLE}.case_id),
                            status = EXCLUDED.status
                        """,
                        {
                            "proposal_id": proposal_id,
                            "proposal_version": version,
                            "case_id": record["case_id"],
                            "session_id": record["session_id"],
                            "office_id": record["office_id"],
                            "story_digest": record["story_digest"],
                            "proposal_json": Json(record["proposal"]),
                            "status": record["status"],
                            "created_at": record["created_at"],
                            "expires_at": record["expires_at"],
                        },
                    )
                conn.commit()
        except Exception:
            logger.debug("accident_story_proposal_persist_failed", exc_info=True)

    return record


def load_proposal_record(proposal_id: str) -> dict[str, Any] | None:
    pid = str(proposal_id or "").strip()
    if not pid:
        return None
    with _lock:
        mem = _durable_memory_proposals.get(pid)
        if mem:
            return deepcopy(mem)

    if not _pg_enabled():
        return None
    try:
        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            _ensure_tables(conn)
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT proposal_id, proposal_version, case_id, session_id, office_id,
                           story_digest, proposal_json, status, created_at, expires_at
                    FROM {PROPOSAL_TABLE}
                    WHERE proposal_id = %s
                    LIMIT 1
                    """,
                    (pid,),
                )
                row = cur.fetchone()
        if not row:
            return None
        proposal = row[6] if isinstance(row[6], dict) else {}
        record = {
            "proposal_id": str(row[0]),
            "proposal_version": int(row[1] or 1),
            "case_id": str(row[2]) if row[2] else None,
            "session_id": str(row[3]) if row[3] else None,
            "office_id": str(row[4]) if row[4] else None,
            "story_digest": str(row[5] or ""),
            "proposal": proposal,
            "status": str(row[7] or "proposed"),
            "created_at": _iso(row[8]) if isinstance(row[8], datetime) else str(row[8] or ""),
            "expires_at": _iso(row[9]) if isinstance(row[9], datetime) else str(row[9] or ""),
        }
        with _lock:
            _durable_memory_proposals[pid] = deepcopy(record)
        return record
    except Exception:
        logger.debug("accident_story_proposal_load_failed", exc_info=True)
        return None


def bind_proposal_case(proposal_id: str, case_id: str) -> None:
    pid = str(proposal_id or "").strip()
    cid = str(case_id or "").strip()
    if not pid or not cid:
        return
    with _lock:
        mem = _durable_memory_proposals.get(pid)
        if mem:
            mem["case_id"] = cid
    if not _pg_enabled():
        return
    try:
        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            _ensure_tables(conn)
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {PROPOSAL_TABLE}
                    SET case_id = %s
                    WHERE proposal_id = %s
                      AND (case_id IS NULL OR case_id = '' OR case_id = %s)
                    """,
                    (cid, pid, cid),
                )
            conn.commit()
    except Exception:
        logger.debug("accident_story_proposal_bind_failed", exc_info=True)


def mark_proposal_confirmed(proposal_id: str) -> None:
    pid = str(proposal_id or "").strip()
    if not pid:
        return
    with _lock:
        mem = _durable_memory_proposals.get(pid)
        if mem:
            mem["status"] = "confirmed"
    if not _pg_enabled():
        return
    try:
        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            _ensure_tables(conn)
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE {PROPOSAL_TABLE} SET status = 'confirmed' WHERE proposal_id = %s",
                    (pid,),
                )
            conn.commit()
    except Exception:
        logger.debug("accident_story_proposal_confirm_mark_failed", exc_info=True)


def get_idempotent_result(idem_key: str) -> dict[str, Any] | None:
    key = str(idem_key or "").strip()
    if not key:
        return None
    with _lock:
        hit = _ephemeral_idem.get(key)
        if hit:
            return deepcopy(hit.get("response") or {})
    durable = _load_durable_idem(key)
    if durable:
        with _lock:
            _ephemeral_idem[key] = deepcopy(durable)
        return deepcopy(durable.get("response") or {})
    return None


def get_idempotent_record(idem_key: str) -> dict[str, Any] | None:
    key = str(idem_key or "").strip()
    if not key:
        return None
    with _lock:
        hit = _ephemeral_idem.get(key)
        if hit:
            return deepcopy(hit)
    durable = _load_durable_idem(key)
    if durable:
        with _lock:
            _ephemeral_idem[key] = deepcopy(durable)
        return durable
    return None


def put_idempotent_result(
    idem_key: str,
    *,
    request_digest_value: str,
    response: dict[str, Any],
    ttl_hours: int = _DEFAULT_TTL_HOURS,
) -> None:
    key = str(idem_key or "").strip()
    if not key:
        return
    now = _utc_now()
    record = {
        "idem_key": key,
        "request_digest": str(request_digest_value or ""),
        "response": deepcopy(response),
        "created_at": _iso(now),
        "expires_at": _iso(now + timedelta(hours=max(1, min(int(ttl_hours), 168)))),
    }
    with _lock:
        _ephemeral_idem[key] = deepcopy(record)
        _durable_memory_idem[key] = deepcopy(record)
    if not _pg_enabled():
        return
    try:
        from psycopg.types.json import Json

        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            _ensure_tables(conn)
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {IDEMPOTENCY_TABLE} (
                        idem_key, request_digest, response_json, created_at, expires_at
                    ) VALUES (
                        %(idem_key)s, %(request_digest)s, %(response_json)s,
                        %(created_at)s::timestamptz, %(expires_at)s::timestamptz
                    )
                    ON CONFLICT (idem_key) DO NOTHING
                    """,
                    {
                        "idem_key": key,
                        "request_digest": record["request_digest"],
                        "response_json": Json(record["response"]),
                        "created_at": record["created_at"],
                        "expires_at": record["expires_at"],
                    },
                )
            conn.commit()
    except Exception:
        logger.debug("accident_story_idempotency_persist_failed", exc_info=True)


def _load_durable_idem(key: str) -> dict[str, Any] | None:
    with _lock:
        mem = _durable_memory_idem.get(key)
        if mem:
            # Soft expiry check
            exp = str(mem.get("expires_at") or "")
            if exp and exp < _iso(_utc_now()):
                return None
            return deepcopy(mem)
    if not _pg_enabled():
        return None
    try:
        from services.fiqa_api.db.service_record_repository import service_record_connection

        with service_record_connection() as conn:
            _ensure_tables(conn)
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT idem_key, request_digest, response_json, created_at, expires_at
                    FROM {IDEMPOTENCY_TABLE}
                    WHERE idem_key = %s AND expires_at > now()
                    LIMIT 1
                    """,
                    (key,),
                )
                row = cur.fetchone()
        if not row:
            return None
        record = {
            "idem_key": str(row[0]),
            "request_digest": str(row[1] or ""),
            "response": row[2] if isinstance(row[2], dict) else {},
            "created_at": _iso(row[3]) if isinstance(row[3], datetime) else str(row[3] or ""),
            "expires_at": _iso(row[4]) if isinstance(row[4], datetime) else str(row[4] or ""),
        }
        with _lock:
            _durable_memory_idem[key] = deepcopy(record)
        return record
    except Exception:
        logger.debug("accident_story_idempotency_load_failed", exc_info=True)
        return None


def proposal_expired(record: dict[str, Any] | None) -> bool:
    if not record:
        return True
    exp = str(record.get("expires_at") or "").strip()
    if not exp:
        return False
    try:
        # Compare ISO strings lexicographically when Z-normalized.
        return exp < _iso(_utc_now())
    except Exception:
        return False


__all__ = [
    "ALLOWED_CUSTOMER_EDIT_KEYS",
    "bind_proposal_case",
    "filter_customer_edits",
    "get_idempotent_record",
    "get_idempotent_result",
    "load_proposal_record",
    "mark_proposal_confirmed",
    "proposal_expired",
    "put_idempotent_result",
    "request_digest",
    "reset_accident_story_durable_memory_for_tests",
    "reset_accident_story_ephemeral_for_tests",
    "reset_accident_story_persistence_for_tests",
    "store_proposal_record",
    "story_digest",
]
