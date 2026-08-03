"""Demo Invite token + session overlay store.

In-memory cache with Postgres durability on QA/Cloud Run so cold starts and
redeploys cannot wipe active DIT tokens mid phone QA.

No durable Customers table. No OpenID remapping.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


def hash_invite_token(raw_token: str) -> str:
    return hashlib.sha256(str(raw_token or "").encode("utf-8")).hexdigest()


@dataclass
class DemoInviteRecord:
    invite_id: str
    token_hash: str
    office_id: str
    scenario_id: str
    mock_scenario: str
    demo_name: str
    created_at: float
    expires_at: float
    revoked_at: float | None = None
    max_uses: int | None = None
    use_count: int = 0
    is_demo: bool = True

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "invite_id": self.invite_id,
            "office_id": self.office_id,
            "scenario_id": self.scenario_id,
            "mock_scenario": self.mock_scenario,
            "demo_name": self.demo_name,
            "is_demo": True,
            "created_at": int(self.created_at),
            "expires_at": int(self.expires_at),
            "revoked": self.revoked_at is not None,
            "use_count": self.use_count,
            "max_uses": self.max_uses,
        }


@dataclass
class SessionOverlayRecord:
    session_id: str
    invite_id: str
    office_id: str
    scenario_id: str
    mock_scenario: str
    demo_name: str
    expires_at: float
    bound_at: float = field(default_factory=time.time)
    is_demo: bool = True

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "invite_id": self.invite_id,
            "office_id": self.office_id,
            "scenario_id": self.scenario_id,
            "mock_scenario": self.mock_scenario,
            "demo_name": self.demo_name,
            "is_demo": True,
            "expires_at": int(self.expires_at),
            "bound_at": int(self.bound_at),
        }


def _pg_enabled() -> bool:
    try:
        from services.fiqa_api.db.service_record_settings import (
            is_production_deployment,
            service_record_database_url,
        )

        if is_production_deployment():
            return False
        return bool(service_record_database_url())
    except Exception:
        return False


def _ensure_tables(conn: Any) -> None:
    """Create invite tables in autocommit so a later DML rollback cannot drop DDL."""
    prev = bool(getattr(conn, "autocommit", False))
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS demo_invite_tokens (
                    invite_id TEXT PRIMARY KEY,
                    token_hash TEXT NOT NULL UNIQUE,
                    office_id TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    mock_scenario TEXT NOT NULL,
                    demo_name TEXT NOT NULL,
                    created_at DOUBLE PRECISION NOT NULL,
                    expires_at DOUBLE PRECISION NOT NULL,
                    revoked_at DOUBLE PRECISION,
                    max_uses INTEGER,
                    use_count INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS demo_invite_overlays (
                    session_id TEXT PRIMARY KEY,
                    invite_id TEXT NOT NULL,
                    office_id TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    mock_scenario TEXT NOT NULL,
                    demo_name TEXT NOT NULL,
                    expires_at DOUBLE PRECISION NOT NULL,
                    bound_at DOUBLE PRECISION NOT NULL
                )
                """
            )
    finally:
        try:
            conn.autocommit = prev
        except Exception:
            pass


def _row_to_invite(row: Any) -> DemoInviteRecord:
    return DemoInviteRecord(
        invite_id=str(row[0]),
        token_hash=str(row[1]),
        office_id=str(row[2]),
        scenario_id=str(row[3]),
        mock_scenario=str(row[4]),
        demo_name=str(row[5]),
        created_at=float(row[6]),
        expires_at=float(row[7]),
        revoked_at=float(row[8]) if row[8] is not None else None,
        max_uses=int(row[9]) if row[9] is not None else None,
        use_count=int(row[10] or 0),
    )


def _row_to_overlay(row: Any) -> SessionOverlayRecord:
    return SessionOverlayRecord(
        session_id=str(row[0]),
        invite_id=str(row[1]),
        office_id=str(row[2]),
        scenario_id=str(row[3]),
        mock_scenario=str(row[4]),
        demo_name=str(row[5]),
        expires_at=float(row[6]),
        bound_at=float(row[7]),
    )


class DemoInviteStore:
    """Thread-safe invite + overlay index with optional Postgres durability."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._invites_by_hash: dict[str, DemoInviteRecord] = {}
        self._invites_by_id: dict[str, DemoInviteRecord] = {}
        self._overlays_by_session: dict[str, SessionOverlayRecord] = {}

    def reset_for_tests(self) -> None:
        with self._lock:
            self._invites_by_hash.clear()
            self._invites_by_id.clear()
            self._overlays_by_session.clear()

    def _cache_invite(self, record: DemoInviteRecord) -> None:
        self._invites_by_hash[record.token_hash] = record
        self._invites_by_id[record.invite_id] = record

    def _persist_invite(self, record: DemoInviteRecord) -> None:
        if not _pg_enabled():
            return
        try:
            from services.fiqa_api.inbox_triage.session_repository import (
                intake_session_connection,
            )

            with intake_session_connection() as conn:
                _ensure_tables(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO demo_invite_tokens (
                            invite_id, token_hash, office_id, scenario_id, mock_scenario,
                            demo_name, created_at, expires_at, revoked_at, max_uses, use_count
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (invite_id) DO UPDATE SET
                            token_hash = EXCLUDED.token_hash,
                            office_id = EXCLUDED.office_id,
                            scenario_id = EXCLUDED.scenario_id,
                            mock_scenario = EXCLUDED.mock_scenario,
                            demo_name = EXCLUDED.demo_name,
                            created_at = EXCLUDED.created_at,
                            expires_at = EXCLUDED.expires_at,
                            revoked_at = EXCLUDED.revoked_at,
                            max_uses = EXCLUDED.max_uses,
                            use_count = EXCLUDED.use_count
                        """,
                        (
                            record.invite_id,
                            record.token_hash,
                            record.office_id,
                            record.scenario_id,
                            record.mock_scenario,
                            record.demo_name,
                            record.created_at,
                            record.expires_at,
                            record.revoked_at,
                            record.max_uses,
                            record.use_count,
                        ),
                    )
                conn.commit()
        except Exception as exc:
            logger.warning("demo_invite persist invite failed: %s", type(exc).__name__)

    def _load_invite_by_hash(self, token_hash: str) -> DemoInviteRecord | None:
        if not _pg_enabled():
            return None
        try:
            from services.fiqa_api.inbox_triage.session_repository import (
                intake_session_connection,
            )

            with intake_session_connection() as conn:
                _ensure_tables(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT invite_id, token_hash, office_id, scenario_id, mock_scenario,
                               demo_name, created_at, expires_at, revoked_at, max_uses, use_count
                        FROM demo_invite_tokens WHERE token_hash = %s
                        """,
                        (token_hash,),
                    )
                    row = cur.fetchone()
                    if not row:
                        return None
                    return _row_to_invite(row)
        except Exception as exc:
            logger.warning("demo_invite load by hash failed: %s", type(exc).__name__)
            return None

    def _load_invite_by_id(self, invite_id: str) -> DemoInviteRecord | None:
        if not _pg_enabled():
            return None
        try:
            from services.fiqa_api.inbox_triage.session_repository import (
                intake_session_connection,
            )

            with intake_session_connection() as conn:
                _ensure_tables(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT invite_id, token_hash, office_id, scenario_id, mock_scenario,
                               demo_name, created_at, expires_at, revoked_at, max_uses, use_count
                        FROM demo_invite_tokens WHERE invite_id = %s
                        """,
                        (invite_id,),
                    )
                    row = cur.fetchone()
                    if not row:
                        return None
                    return _row_to_invite(row)
        except Exception as exc:
            logger.warning("demo_invite load by id failed: %s", type(exc).__name__)
            return None

    def _persist_overlay(self, overlay: SessionOverlayRecord) -> None:
        if not _pg_enabled():
            return
        try:
            from services.fiqa_api.inbox_triage.session_repository import (
                intake_session_connection,
            )

            with intake_session_connection() as conn:
                _ensure_tables(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO demo_invite_overlays (
                            session_id, invite_id, office_id, scenario_id, mock_scenario,
                            demo_name, expires_at, bound_at
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (session_id) DO UPDATE SET
                            invite_id = EXCLUDED.invite_id,
                            office_id = EXCLUDED.office_id,
                            scenario_id = EXCLUDED.scenario_id,
                            mock_scenario = EXCLUDED.mock_scenario,
                            demo_name = EXCLUDED.demo_name,
                            expires_at = EXCLUDED.expires_at,
                            bound_at = EXCLUDED.bound_at
                        """,
                        (
                            overlay.session_id,
                            overlay.invite_id,
                            overlay.office_id,
                            overlay.scenario_id,
                            overlay.mock_scenario,
                            overlay.demo_name,
                            overlay.expires_at,
                            overlay.bound_at,
                        ),
                    )
                conn.commit()
        except Exception as exc:
            logger.warning("demo_invite persist overlay failed: %s", type(exc).__name__)

    def _load_overlay(self, session_id: str) -> SessionOverlayRecord | None:
        if not _pg_enabled():
            return None
        try:
            from services.fiqa_api.inbox_triage.session_repository import (
                intake_session_connection,
            )

            with intake_session_connection() as conn:
                _ensure_tables(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT session_id, invite_id, office_id, scenario_id, mock_scenario,
                               demo_name, expires_at, bound_at
                        FROM demo_invite_overlays WHERE session_id = %s
                        """,
                        (session_id,),
                    )
                    row = cur.fetchone()
                    if not row:
                        return None
                    return _row_to_overlay(row)
        except Exception as exc:
            logger.warning("demo_invite load overlay failed: %s", type(exc).__name__)
            return None

    def _delete_overlay_pg(self, session_id: str) -> None:
        if not _pg_enabled():
            return
        try:
            from services.fiqa_api.inbox_triage.session_repository import (
                intake_session_connection,
            )

            with intake_session_connection() as conn:
                _ensure_tables(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM demo_invite_overlays WHERE session_id = %s",
                        (session_id,),
                    )
                conn.commit()
        except Exception as exc:
            logger.warning("demo_invite delete overlay failed: %s", type(exc).__name__)

    def put_invite(self, record: DemoInviteRecord) -> None:
        with self._lock:
            self._cache_invite(record)
        self._persist_invite(record)

    def get_by_token_hash(self, token_hash: str) -> DemoInviteRecord | None:
        key = str(token_hash or "").strip()
        if not key:
            return None
        with self._lock:
            cached = self._invites_by_hash.get(key)
            if cached is not None:
                return cached
        loaded = self._load_invite_by_hash(key)
        if loaded is not None:
            with self._lock:
                self._cache_invite(loaded)
        return loaded

    def get_by_invite_id(self, invite_id: str) -> DemoInviteRecord | None:
        iid = str(invite_id or "").strip()
        if not iid:
            return None
        with self._lock:
            cached = self._invites_by_id.get(iid)
            if cached is not None:
                return cached
        loaded = self._load_invite_by_id(iid)
        if loaded is not None:
            with self._lock:
                self._cache_invite(loaded)
        return loaded

    def mark_revoked(self, invite: DemoInviteRecord, *, now: float | None = None) -> None:
        with self._lock:
            invite.revoked_at = float(now if now is not None else time.time())
        self._persist_invite(invite)

    def increment_use(self, invite: DemoInviteRecord) -> None:
        with self._lock:
            invite.use_count += 1
        self._persist_invite(invite)

    def put_overlay(self, overlay: SessionOverlayRecord) -> None:
        with self._lock:
            self._overlays_by_session[overlay.session_id] = overlay
        self._persist_overlay(overlay)

    def get_overlay(self, session_id: str) -> SessionOverlayRecord | None:
        key = str(session_id or "").strip()[:80]
        if not key:
            return None
        with self._lock:
            cached = self._overlays_by_session.get(key)
            if cached is not None:
                return cached
        loaded = self._load_overlay(key)
        if loaded is not None:
            with self._lock:
                self._overlays_by_session[key] = loaded
        return loaded

    def clear_overlay(self, session_id: str) -> bool:
        key = str(session_id or "").strip()[:80]
        if not key:
            return False
        with self._lock:
            removed = self._overlays_by_session.pop(key, None) is not None
        self._delete_overlay_pg(key)
        return removed

    def clear_overlays_for_invite(self, invite_id: str) -> int:
        iid = str(invite_id or "").strip()
        if not iid:
            return 0
        with self._lock:
            keys = [
                sid
                for sid, ov in self._overlays_by_session.items()
                if ov.invite_id == iid
            ]
            for sid in keys:
                self._overlays_by_session.pop(sid, None)
        if _pg_enabled():
            try:
                from services.fiqa_api.inbox_triage.session_repository import (
                    intake_session_connection,
                )

                with intake_session_connection() as conn:
                    _ensure_tables(conn)
                    with conn.cursor() as cur:
                        cur.execute(
                            "DELETE FROM demo_invite_overlays WHERE invite_id = %s",
                            (iid,),
                        )
                        count = cur.rowcount or 0
                    conn.commit()
                return max(len(keys), int(count))
            except Exception as exc:
                logger.warning(
                    "demo_invite clear overlays for invite failed: %s", type(exc).__name__
                )
        return len(keys)

    def clear_overlays_for_office(self, office_id: str) -> int:
        oid = str(office_id or "").strip()
        if not oid:
            return 0
        with self._lock:
            keys = [
                sid
                for sid, ov in self._overlays_by_session.items()
                if ov.office_id == oid
            ]
            for sid in keys:
                self._overlays_by_session.pop(sid, None)
        if _pg_enabled():
            try:
                from services.fiqa_api.inbox_triage.session_repository import (
                    intake_session_connection,
                )

                with intake_session_connection() as conn:
                    _ensure_tables(conn)
                    with conn.cursor() as cur:
                        cur.execute(
                            "DELETE FROM demo_invite_overlays WHERE office_id = %s",
                            (oid,),
                        )
                        count = cur.rowcount or 0
                    conn.commit()
                return max(len(keys), int(count))
            except Exception as exc:
                logger.warning(
                    "demo_invite clear overlays for office failed: %s", type(exc).__name__
                )
        return len(keys)

    def revoke_invites_for_office(self, office_id: str, *, now: float | None = None) -> int:
        oid = str(office_id or "").strip()
        if not oid:
            return 0
        ts = float(now if now is not None else time.time())
        count = 0
        with self._lock:
            for invite in self._invites_by_id.values():
                if invite.office_id == oid and invite.revoked_at is None:
                    invite.revoked_at = ts
                    count += 1
        if _pg_enabled():
            try:
                from services.fiqa_api.inbox_triage.session_repository import (
                    intake_session_connection,
                )

                with intake_session_connection() as conn:
                    _ensure_tables(conn)
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE demo_invite_tokens
                            SET revoked_at = %s
                            WHERE office_id = %s AND revoked_at IS NULL
                            """,
                            (ts, oid),
                        )
                        count = max(count, int(cur.rowcount or 0))
                    conn.commit()
            except Exception as exc:
                logger.warning(
                    "demo_invite revoke office failed: %s", type(exc).__name__
                )
        return count


_STORE = DemoInviteStore()


def get_demo_invite_store() -> DemoInviteStore:
    return _STORE


def reset_demo_invite_store_for_tests() -> None:
    _STORE.reset_for_tests()
