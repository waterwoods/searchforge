"""Demo Invite foundation — issue / validate / redeem / revoke / overlay resolve.

Presentation overlay only. Real wx person_link_key remains authoritative.
Never writes OpenID→fake customer maps. Never creates a Customers table.
QA / non-Production only.
"""

from __future__ import annotations

import os
import secrets
import time
import uuid
from typing import Any

from services.fiqa_api.db.service_record_settings import is_production_deployment
from services.fiqa_api.inbox_triage.demo_invite.catalog import (
    DEMO_NAME,
    get_approved_scenario,
    list_approved_scenarios,
)
from services.fiqa_api.inbox_triage.demo_invite.store import (
    DemoInviteRecord,
    SessionOverlayRecord,
    get_demo_invite_store,
    hash_invite_token,
    reset_demo_invite_store_for_tests,
)

FLAG_ENV = "CHEN_DEMO_INVITE_ENABLED"

# Default TTL: 4 hours (demo-day window).
DEFAULT_TTL_SECONDS = 4 * 3600
MIN_TTL_SECONDS = 60
MAX_TTL_SECONDS = 24 * 3600

TOKEN_PREFIX = "di_"


def _truthy_env(name: str) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def demo_invite_enabled() -> bool:
    """Hard-off on Production deployment. Explicit flag elsewhere."""
    if is_production_deployment():
        return False
    return _truthy_env(FLAG_ENV)


def assert_demo_invite_allowed() -> None:
    if is_production_deployment():
        raise ValueError("demo_invite_disabled_production")
    if not _truthy_env(FLAG_ENV):
        raise ValueError("demo_invite_disabled")


def _normalize_office_id(office_id: str | None) -> str:
    oid = str(office_id or "").strip()[:256]
    if not oid:
        raise ValueError("office_id_required")
    return oid


def _normalize_session_id(session_id: str | None) -> str:
    sid = str(session_id or "").strip()[:80]
    if not sid or len(sid) < 8:
        raise ValueError("session_id_required")
    return sid


def _mint_opaque_token() -> str:
    return f"{TOKEN_PREFIX}{secrets.token_urlsafe(32)}"


def list_catalog() -> list[dict[str, Any]]:
    assert_demo_invite_allowed()
    return list_approved_scenarios()


def issue_demo_invite(
    *,
    office_id: str,
    scenario_id: str,
    ttl_seconds: int | None = None,
    max_uses: int | None = None,
) -> dict[str, Any]:
    """Broker/support: mint opaque invite for an allowlisted scenario."""
    assert_demo_invite_allowed()
    oid = _normalize_office_id(office_id)
    entry = get_approved_scenario(scenario_id)
    if entry is None:
        raise ValueError("scenario_not_allowlisted")

    ttl = int(ttl_seconds if ttl_seconds is not None else DEFAULT_TTL_SECONDS)
    if ttl < MIN_TTL_SECONDS or ttl > MAX_TTL_SECONDS:
        raise ValueError("ttl_out_of_range")

    uses: int | None
    if max_uses is None:
        uses = None
    else:
        uses = int(max_uses)
        if uses < 1 or uses > 100:
            raise ValueError("max_uses_out_of_range")

    raw_token = _mint_opaque_token()
    now = time.time()
    invite_id = f"dinv_{uuid.uuid4().hex[:16]}"
    record = DemoInviteRecord(
        invite_id=invite_id,
        token_hash=hash_invite_token(raw_token),
        office_id=oid,
        scenario_id=entry["scenario_id"],
        mock_scenario=entry["mock_scenario"],
        demo_name=entry["demo_name"],
        created_at=now,
        expires_at=now + ttl,
        max_uses=uses,
    )
    get_demo_invite_store().put_invite(record)

    public = record.to_public_dict()
    public["token"] = raw_token  # returned once; never stored plaintext
    public["customer_display_name"] = entry["customer_display_name"]
    public["vehicle_summary"] = entry["vehicle_summary"]
    public["label"] = entry["label"]
    return public


def _invite_status(invite: DemoInviteRecord, *, now: float | None = None) -> str:
    ts = float(now if now is not None else time.time())
    if invite.revoked_at is not None:
        return "revoked"
    if ts >= invite.expires_at:
        return "expired"
    if invite.max_uses is not None and invite.use_count >= invite.max_uses:
        return "exhausted"
    return "active"


def validate_demo_invite(
    token: str,
    *,
    office_id: str | None = None,
) -> dict[str, Any]:
    """Server-side validation without redeeming / without binding overlay."""
    assert_demo_invite_allowed()
    raw = str(token or "").strip()
    if not raw or not raw.startswith(TOKEN_PREFIX):
        return {
            "ok": False,
            "status": "invalid",
            "error_code": "invalid_token",
            "is_demo": True,
            "demo_name": DEMO_NAME,
        }

    invite = get_demo_invite_store().get_by_token_hash(hash_invite_token(raw))
    if invite is None:
        return {
            "ok": False,
            "status": "invalid",
            "error_code": "unknown_token",
            "is_demo": True,
            "demo_name": DEMO_NAME,
        }

    status = _invite_status(invite)
    if office_id is not None:
        oid = str(office_id or "").strip()
        if oid and oid != invite.office_id:
            return {
                "ok": False,
                "status": "office_mismatch",
                "error_code": "office_mismatch",
                "is_demo": True,
                "demo_name": DEMO_NAME,
                "invite": invite.to_public_dict(),
            }

    ok = status == "active"
    return {
        "ok": ok,
        "status": status,
        "error_code": None if ok else status,
        "is_demo": True,
        "demo_name": DEMO_NAME,
        "invite": invite.to_public_dict(),
    }


def _session_identity_key(session_id: str) -> str | None:
    """Opaque person_link used for One Active Case (wx_* only)."""
    from services.fiqa_api.inbox_triage.mp_customer_identity import person_link_from_session_id

    link = person_link_from_session_id(session_id)
    if link:
        return link
    sid = str(session_id or "").strip()[:80]
    if sid.startswith("wx_") and len(sid) >= 12:
        return sid
    return None


def _active_case_for_session(session_id: str) -> dict[str, Any] | None:
    from services.fiqa_api.inbox_triage.mp_customer_identity import (
        resolve_active_case_for_person_link,
    )

    key = _session_identity_key(session_id)
    if not key:
        return None
    try:
        return resolve_active_case_for_person_link(key)
    except Exception:
        return None


def _overlay_matches_invite(session_id: str, invite: DemoInviteRecord) -> bool:
    existing = get_demo_invite_store().get_overlay(session_id)
    if existing is None:
        return False
    if time.time() >= existing.expires_at:
        return False
    return (
        existing.scenario_id == invite.scenario_id
        and existing.mock_scenario == invite.mock_scenario
    )


def redeem_demo_invite(
    *,
    token: str,
    session_id: str,
    office_id: str | None = None,
) -> dict[str, Any]:
    """
    Bind a temporary mock_scenario overlay to session_id.

    Does NOT change person_link_key / OpenID. Overlay is TTL-bound presentation only.

    One Active Case rule:
      If this wx identity already has an Active Case, redeeming a *different*
      mock scenario is refused. Existing case remains authoritative. Support must
      explicitly reset the demo session/case before switching scenarios.
      Idempotent re-redeem of the *same* scenario is allowed (Continue path).
    """
    assert_demo_invite_allowed()
    sid = _normalize_session_id(session_id)
    validation = validate_demo_invite(token, office_id=office_id)
    if not validation.get("ok"):
        # Clear stale overlay only when no Active Case (avoid blank-relabel mid-case).
        if _active_case_for_session(sid) is None:
            get_demo_invite_store().clear_overlay(sid)
        return {
            "ok": False,
            "error_code": str(validation.get("error_code") or "invalid_token"),
            "status": str(validation.get("status") or "invalid"),
            "overlay": None,
            "is_demo": True,
            "demo_name": DEMO_NAME,
            # Explicit: do not pretend known-customer; caller must blank-degrade.
            "fallback": "blank_claim",
        }

    invite_public = validation.get("invite") or {}
    invite = get_demo_invite_store().get_by_invite_id(str(invite_public.get("invite_id") or ""))
    if invite is None:
        if _active_case_for_session(sid) is None:
            get_demo_invite_store().clear_overlay(sid)
        return {
            "ok": False,
            "error_code": "unknown_token",
            "status": "invalid",
            "overlay": None,
            "is_demo": True,
            "demo_name": DEMO_NAME,
            "fallback": "blank_claim",
        }

    # Office scope: if caller asserts office, it must match invite.
    if office_id is not None and str(office_id).strip():
        if str(office_id).strip() != invite.office_id:
            if _active_case_for_session(sid) is None:
                get_demo_invite_store().clear_overlay(sid)
            return {
                "ok": False,
                "error_code": "office_mismatch",
                "status": "office_mismatch",
                "overlay": None,
                "is_demo": True,
                "demo_name": DEMO_NAME,
                "fallback": "blank_claim",
            }

    active = _active_case_for_session(sid)
    if active is not None and not _overlay_matches_invite(sid, invite):
        # Do not bind/replace overlay; do not clear existing same-scenario overlay.
        case_id = str(
            active.get("case_id")
            or active.get("record_id")
            or active.get("id")
            or ""
        ).strip()
        existing = get_demo_invite_store().get_overlay(sid)
        return {
            "ok": False,
            "error_code": "active_case_blocks_scenario_switch",
            "status": "active_case_blocks_scenario_switch",
            "active_case_id": case_id or None,
            "requires_support_reset": True,
            "overlay": existing.to_public_dict() if existing else None,
            "is_demo": True,
            "demo_name": DEMO_NAME,
            "fallback": "continue_active_case",
        }

    # Idempotent same-scenario re-redeem while Active Case exists: refresh overlay TTL
    # metadata without treating as a switch.
    if active is not None and _overlay_matches_invite(sid, invite):
        existing = get_demo_invite_store().get_overlay(sid)
        entry = get_approved_scenario(invite.scenario_id)
        return {
            "ok": True,
            "status": "redeemed_idempotent",
            "error_code": None,
            "overlay": existing.to_public_dict() if existing else None,
            "customer_display_name": (entry or {}).get("customer_display_name"),
            "vehicle_summary": (entry or {}).get("vehicle_summary"),
            "is_demo": True,
            "demo_name": DEMO_NAME,
            "active_case_preserved": True,
        }

    store = get_demo_invite_store()
    store.increment_use(invite)
    # Re-check exhaustion after increment for max_uses == 1 races.
    if invite.max_uses is not None and invite.use_count > invite.max_uses:
        if active is None:
            store.clear_overlay(sid)
        return {
            "ok": False,
            "error_code": "exhausted",
            "status": "exhausted",
            "overlay": None,
            "is_demo": True,
            "demo_name": DEMO_NAME,
            "fallback": "blank_claim",
        }

    overlay = SessionOverlayRecord(
        session_id=sid,
        invite_id=invite.invite_id,
        office_id=invite.office_id,
        scenario_id=invite.scenario_id,
        mock_scenario=invite.mock_scenario,
        demo_name=invite.demo_name,
        expires_at=invite.expires_at,
    )
    store.put_overlay(overlay)

    entry = get_approved_scenario(invite.scenario_id)
    return {
        "ok": True,
        "status": "redeemed",
        "error_code": None,
        "overlay": overlay.to_public_dict(),
        "customer_display_name": (entry or {}).get("customer_display_name"),
        "vehicle_summary": (entry or {}).get("vehicle_summary"),
        "is_demo": True,
        "demo_name": DEMO_NAME,
        # person_link intentionally absent — identity unchanged.
    }


def revoke_demo_invite(*, token: str | None = None, invite_id: str | None = None) -> dict[str, Any]:
    assert_demo_invite_allowed()
    store = get_demo_invite_store()
    invite: DemoInviteRecord | None = None
    if invite_id and str(invite_id).strip():
        invite = store.get_by_invite_id(str(invite_id).strip())
    elif token and str(token).strip():
        invite = store.get_by_token_hash(hash_invite_token(str(token).strip()))
    else:
        raise ValueError("token_or_invite_id_required")

    if invite is None:
        return {"ok": False, "error_code": "unknown_invite", "is_demo": True, "demo_name": DEMO_NAME}

    store.mark_revoked(invite)
    overlays_cleared = store.clear_overlays_for_invite(invite.invite_id)
    return {
        "ok": True,
        "revoked": True,
        "overlays_cleared": overlays_cleared,
        "invite": invite.to_public_dict(),
        "is_demo": True,
        "demo_name": DEMO_NAME,
    }


def reset_session_overlay(session_id: str) -> dict[str, Any]:
    """Clear temporary scenario overlay for one session (identity untouched)."""
    assert_demo_invite_allowed()
    sid = _normalize_session_id(session_id)
    cleared = get_demo_invite_store().clear_overlay(sid)
    return {
        "ok": True,
        "cleared": cleared,
        "session_id": sid,
        "is_demo": True,
        "demo_name": DEMO_NAME,
    }


def reset_office_demo_invites(office_id: str) -> dict[str, Any]:
    """Revoke all invites + clear overlays for one office (demo reset)."""
    assert_demo_invite_allowed()
    oid = _normalize_office_id(office_id)
    store = get_demo_invite_store()
    revoked = store.revoke_invites_for_office(oid)
    cleared = store.clear_overlays_for_office(oid)
    return {
        "ok": True,
        "office_id": oid,
        "invites_revoked": revoked,
        "overlays_cleared": cleared,
        "is_demo": True,
        "demo_name": DEMO_NAME,
    }


def resolve_overlay_mock_scenario(session_id: str | None) -> str | None:
    """
    Return allowlisted mock_scenario for session overlay, or None.

    Expired overlays are cleared and treated as absent (blank fallback).
    Never returns or mutates person_link_key.
    """
    if not demo_invite_enabled():
        return None
    sid = str(session_id or "").strip()[:80]
    if not sid:
        return None
    store = get_demo_invite_store()
    overlay = store.get_overlay(sid)
    if overlay is None:
        return None
    now = time.time()
    if now >= overlay.expires_at:
        store.clear_overlay(sid)
        return None
    # Defense: overlay scenario must still be allowlisted.
    entry = get_approved_scenario(overlay.scenario_id)
    if entry is None:
        store.clear_overlay(sid)
        return None
    return entry["mock_scenario"]


def peek_session_overlay(session_id: str | None) -> dict[str, Any] | None:
    if not demo_invite_enabled():
        return None
    sid = str(session_id or "").strip()[:80]
    if not sid:
        return None
    overlay = get_demo_invite_store().get_overlay(sid)
    if overlay is None:
        return None
    if time.time() >= overlay.expires_at:
        get_demo_invite_store().clear_overlay(sid)
        return None
    return overlay.to_public_dict()


__all__ = [
    "DEMO_NAME",
    "FLAG_ENV",
    "assert_demo_invite_allowed",
    "demo_invite_enabled",
    "issue_demo_invite",
    "list_catalog",
    "peek_session_overlay",
    "redeem_demo_invite",
    "reset_demo_invite_store_for_tests",
    "reset_office_demo_invites",
    "reset_session_overlay",
    "resolve_overlay_mock_scenario",
    "revoke_demo_invite",
    "validate_demo_invite",
]
