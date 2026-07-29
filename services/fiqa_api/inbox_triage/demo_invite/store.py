"""In-memory Demo Invite token + session overlay store.

No durable Customers table. No OpenID remapping.
Process-local only — acceptable for QA / Chen demo day.
"""

from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass, field
from typing import Any


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


class DemoInviteStore:
    """Thread-safe in-process invite + overlay index."""

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

    def put_invite(self, record: DemoInviteRecord) -> None:
        with self._lock:
            self._invites_by_hash[record.token_hash] = record
            self._invites_by_id[record.invite_id] = record

    def get_by_token_hash(self, token_hash: str) -> DemoInviteRecord | None:
        with self._lock:
            return self._invites_by_hash.get(token_hash)

    def get_by_invite_id(self, invite_id: str) -> DemoInviteRecord | None:
        with self._lock:
            return self._invites_by_id.get(str(invite_id or "").strip())

    def mark_revoked(self, invite: DemoInviteRecord, *, now: float | None = None) -> None:
        with self._lock:
            invite.revoked_at = float(now if now is not None else time.time())

    def increment_use(self, invite: DemoInviteRecord) -> None:
        with self._lock:
            invite.use_count += 1

    def put_overlay(self, overlay: SessionOverlayRecord) -> None:
        with self._lock:
            self._overlays_by_session[overlay.session_id] = overlay

    def get_overlay(self, session_id: str) -> SessionOverlayRecord | None:
        key = str(session_id or "").strip()[:80]
        if not key:
            return None
        with self._lock:
            return self._overlays_by_session.get(key)

    def clear_overlay(self, session_id: str) -> bool:
        key = str(session_id or "").strip()[:80]
        if not key:
            return False
        with self._lock:
            return self._overlays_by_session.pop(key, None) is not None

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
        return count


_STORE = DemoInviteStore()


def get_demo_invite_store() -> DemoInviteStore:
    return _STORE


def reset_demo_invite_store_for_tests() -> None:
    _STORE.reset_for_tests()
