"""
P29B — Lightweight Mini Program identity for Resume Current Task.

Not a Customer Account system.

Chain:
  wx.login code → jscode2session openid (ephemeral)
    → opaque person_link_key (HMAC; stored)
    → optional customer contact on Active Case
    → at most one Active Case resume token

Rules:
  - OpenID is a technical identifier only; never returned to clients or Broker UI.
  - person_link_key may be stored on the case; never render OpenID.
  - No profile / history / multi-session / dashboard tables.
"""

from __future__ import annotations

import logging
import os
import urllib.parse
from typing import Any

import httpx

from services.fiqa_api.inbox_triage.wechat_binding import opaque_person_link_key

logger = logging.getLogger(__name__)

_JSCODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"

# person_link_key → case_id (One Active Case from customer session POV)
_ACTIVE_CASE_INDEX: dict[str, str] = {}


def reset_mp_active_case_index_for_tests() -> None:
    """Test-only reset of the in-process Active Case index."""
    _ACTIVE_CASE_INDEX.clear()


def mp_credentials_configured() -> bool:
    app_id = (os.getenv("WECHAT_MP_APP_ID") or os.getenv("WECHAT_APP_ID") or "").strip()
    secret = (os.getenv("WECHAT_MP_APP_SECRET") or os.getenv("WECHAT_APP_SECRET") or "").strip()
    return bool(app_id and secret)


def mp_simulate_allowed() -> bool:
    v = (
        os.getenv("WECHAT_MP_ALLOW_SIMULATE")
        or os.getenv("WECHAT_BINDING_ALLOW_SIMULATE")
        or ""
    ).strip().lower()
    return v in ("1", "true", "yes", "on")


def session_id_for_person_link(person_link_key: str) -> str:
    """Client session_id is the opaque person link — never raw openid."""
    key = (person_link_key or "").strip()
    if not key:
        raise ValueError("person_link_key_required")
    return key[:80]


def person_link_from_session_id(session_id: str | None) -> str | None:
    """Extract opaque wechat person link from Mini Program session_id when present."""
    sid = (session_id or "").strip()
    if sid.startswith("wx_") and len(sid) >= 12:
        return sid[:80]
    return None


def allow_prototype_anon_customer_create() -> bool:
    """anon-* / fixture session create is local/QA/harness only — never Production."""
    from services.fiqa_api.db.service_record_settings import is_production_deployment

    return not is_production_deployment()


def resolve_customer_identity_key(session_id: str | None) -> str | None:
    """
    Identity key used for One Active Case resolve/bind on customer create.

    Production: durable wx_* person_link only.
    Non-Production: also device/fixture keys (anon-*, p26h-*, p35-*) so local/QA
    cannot fork Active Cases after storage clear on the same session_id.
    """
    durable = person_link_from_session_id(session_id)
    if durable:
        return durable
    if not allow_prototype_anon_customer_create():
        return None
    sid = (session_id or "").strip()
    if not sid or len(sid) < 8:
        return None
    if sid.startswith("anon-") or sid.startswith("p26h-") or sid.startswith("p35-"):
        return sid[:80]
    return None


async def exchange_mp_code_for_openid(code: str) -> tuple[str | None, str | None]:
    """Mini Program jscode2session. Returns (openid, error_code). Never log openid."""
    raw = (code or "").strip()
    if not raw:
        return None, "code_required"

    if raw.startswith("sim:") and mp_simulate_allowed():
        simulated = raw[4:].strip() or "simulated-openid"
        return simulated, None

    app_id = (os.getenv("WECHAT_MP_APP_ID") or os.getenv("WECHAT_APP_ID") or "").strip()
    secret = (os.getenv("WECHAT_MP_APP_SECRET") or os.getenv("WECHAT_APP_SECRET") or "").strip()
    if not app_id or not secret:
        return None, "wechat_mp_not_configured"

    params = {
        "appid": app_id,
        "secret": secret,
        "js_code": raw,
        "grant_type": "authorization_code",
    }
    url = f"{_JSCODE2SESSION_URL}?{urllib.parse.urlencode(params)}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            data = response.json()
    except Exception as exc:
        logger.warning("MP jscode2session HTTP failed: %s", type(exc).__name__)
        return None, "token_http_error"

    if data.get("errcode"):
        logger.warning("MP jscode2session error errcode=%s", data.get("errcode"))
        return None, str(data.get("errmsg") or "wechat_error")

    openid = str(data.get("openid") or "").strip()
    if not openid:
        return None, "no_openid"
    return openid, None


def bind_active_case(person_link_key: str, case_id: str) -> None:
    """Bind opaque person link to exactly one Active Case (overwrite = Start New Claim)."""
    key = (person_link_key or "").strip()
    cid = (case_id or "").strip()
    if not key or not cid:
        return
    _ACTIVE_CASE_INDEX[key[:80]] = cid[:128]
    _persist_bind(key[:80], cid[:128])


def clear_active_case_binding(person_link_key: str) -> None:
    key = (person_link_key or "").strip()[:80]
    if not key:
        return
    _ACTIVE_CASE_INDEX.pop(key, None)
    _persist_clear(key)


def clear_active_case_bindings_for_case(case_id: str) -> int:
    """Clear all person_link bindings that point at case_id (in-process + DB).

    Used after hard-delete so Workbench delete cannot leave ghost Continue state.
    Returns number of in-process index entries removed (DB delete is best-effort).
    """
    cid = (case_id or "").strip()[:128]
    if not cid:
        return 0
    removed_keys = [key for key, bound in list(_ACTIVE_CASE_INDEX.items()) if bound == cid]
    for key in removed_keys:
        _ACTIVE_CASE_INDEX.pop(key, None)
    _persist_clear_for_case(cid)
    return len(removed_keys)


def lookup_bound_case_id(person_link_key: str) -> str | None:
    key = (person_link_key or "").strip()[:80]
    if not key:
        return None
    cached = _ACTIVE_CASE_INDEX.get(key)
    if cached:
        return cached
    loaded = _persist_load(key)
    if loaded:
        _ACTIVE_CASE_INDEX[key] = loaded
    return loaded


def _persist_bind(person_link_key: str, case_id: str) -> None:
    try:
        from services.fiqa_api.db.service_record_settings import service_record_database_url

        if not service_record_database_url():
            return
        from services.fiqa_api.inbox_triage.session_repository import intake_session_connection

        with intake_session_connection() as conn:
            with conn.cursor() as cur:
                _ensure_active_case_table(cur)
                cur.execute(
                    """
                    INSERT INTO mp_customer_active_case (person_link_key, case_id, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (person_link_key) DO UPDATE
                    SET case_id = EXCLUDED.case_id, updated_at = NOW()
                    """,
                    (person_link_key, case_id),
                )
            conn.commit()
    except Exception as exc:
        logger.warning("mp_customer_active_case persist bind failed: %s", type(exc).__name__)


def _persist_clear(person_link_key: str) -> None:
    try:
        from services.fiqa_api.db.service_record_settings import service_record_database_url

        if not service_record_database_url():
            return
        from services.fiqa_api.inbox_triage.session_repository import intake_session_connection

        with intake_session_connection() as conn:
            with conn.cursor() as cur:
                _ensure_active_case_table(cur)
                cur.execute(
                    "DELETE FROM mp_customer_active_case WHERE person_link_key = %s",
                    (person_link_key,),
                )
            conn.commit()
    except Exception as exc:
        logger.warning("mp_customer_active_case persist clear failed: %s", type(exc).__name__)


def _persist_clear_for_case(case_id: str) -> None:
    try:
        from services.fiqa_api.db.service_record_settings import service_record_database_url

        if not service_record_database_url():
            return
        from services.fiqa_api.inbox_triage.session_repository import intake_session_connection

        with intake_session_connection() as conn:
            with conn.cursor() as cur:
                _ensure_active_case_table(cur)
                cur.execute(
                    "DELETE FROM mp_customer_active_case WHERE case_id = %s",
                    (case_id,),
                )
            conn.commit()
    except Exception as exc:
        logger.warning(
            "mp_customer_active_case persist clear-for-case failed: %s",
            type(exc).__name__,
        )


def _persist_load(person_link_key: str) -> str | None:
    try:
        from services.fiqa_api.db.service_record_settings import service_record_database_url

        if not service_record_database_url():
            return None
        from services.fiqa_api.inbox_triage.session_repository import intake_session_connection

        with intake_session_connection() as conn:
            with conn.cursor() as cur:
                _ensure_active_case_table(cur)
                cur.execute(
                    "SELECT case_id FROM mp_customer_active_case WHERE person_link_key = %s",
                    (person_link_key,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return str(row[0] or "").strip() or None
    except Exception as exc:
        logger.warning("mp_customer_active_case persist load failed: %s", type(exc).__name__)
        return None


_ACTIVE_CASE_DDL_CHECKED = False


def _ensure_active_case_table(cur: Any) -> None:
    global _ACTIVE_CASE_DDL_CHECKED
    if _ACTIVE_CASE_DDL_CHECKED:
        return
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mp_customer_active_case (
            person_link_key TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_mp_customer_active_case_case_id
        ON mp_customer_active_case (case_id)
        """
    )
    _ACTIVE_CASE_DDL_CHECKED = True


def case_is_resumable_active(case: dict[str, Any] | None) -> bool:
    """True when the bound case should still surface Continue Current Task.

    Soft archive (workbench_archived) is a queue filter only — it must NOT
    release Active Case. Broker Close / History does.
    """
    if not isinstance(case, dict):
        return False
    try:
        from services.fiqa_api.inbox_triage.case_close import case_is_closed_history

        if case_is_closed_history(case):
            return False
    except Exception:
        if str(case.get("case_status") or "").strip().lower() == "closed":
            return False
    status = str(case.get("case_status") or "new").strip().lower()
    if status in ("done", "cancelled"):
        return False
    return True


def resolve_active_case_for_person_link(person_link_key: str) -> dict[str, Any] | None:
    """Return resumable Active Case dict, or None (clears stale/missing bindings)."""
    key = (person_link_key or "").strip()
    case_id = lookup_bound_case_id(key)
    if not case_id:
        return None
    case = _load_case(case_id)
    if case is None or not case_is_resumable_active(case):
        # Missing, hard-deleted, archived, or closed — never fabricate an active case.
        clear_active_case_binding(key)
        return None
    return case


def _load_case(case_id: str) -> dict[str, Any] | None:
    """Load a real case row. Returns None when missing — never invents a fake active case."""
    cid = (case_id or "").strip()
    if not cid:
        return None
    try:
        from services.fiqa_api.inbox_triage.case_truth_repository import get_case_triage_stub_for_read

        case = get_case_triage_stub_for_read(cid)
        if isinstance(case, dict):
            return case
    except Exception:
        pass
    try:
        from services.fiqa_api.inbox_triage.case_store import get_case_by_id

        case = get_case_by_id(cid)
        if isinstance(case, dict):
            return case
    except Exception:
        pass
    try:
        from services.fiqa_api.inbox_triage import p20_case_intake_command_service as intake_mod

        svc = intake_mod.default_case_intake_service()
        store = getattr(svc, "store", None)
        cases = getattr(store, "cases", None)
        if isinstance(cases, dict):
            row = cases.get(cid)
            if isinstance(row, dict):
                return row
        get_case = getattr(store, "get_case", None)
        if callable(get_case):
            row = get_case(cid)
            if isinstance(row, dict):
                return row
    except Exception:
        pass
    return None


def issue_resume_for_case(case_id: str) -> dict[str, str]:
    """Issue opaque resume token for an Active Case (never expose bare case_id to MP)."""
    from services.fiqa_api.inbox_triage.p20_customer_launch import issue_customer_launch_token

    launch = issue_customer_launch_token(case_id=case_id)
    return {
        "resume_token": launch.token,
        "resume_expires_at": launch.expires_at_iso,
    }


async def establish_mp_customer_session(code: str) -> dict[str, Any]:
    """
    OpenID login → session lookup → Active Case lookup → optional resume.

    Customer-safe response: no openid, no case_id.
    """
    openid, err = await exchange_mp_code_for_openid(code)
    if not openid:
        return {"ok": False, "error_code": err or "login_failed"}

    person_link_key = opaque_person_link_key(openid)
    session_id = session_id_for_person_link(person_link_key)
    active = resolve_active_case_for_person_link(person_link_key)
    body: dict[str, Any] = {
        "ok": True,
        "session_id": session_id,
        "has_active_case": False,
        "identity_binding_state": "linked",
        "person_link_source": "wechat",
    }
    if not active:
        return body

    case_id = str(active.get("case_id") or "").strip()
    if not case_id:
        return body
    try:
        resume = issue_resume_for_case(case_id)
    except Exception:
        logger.warning("resume token issue failed for bound active case")
        return body

    body["has_active_case"] = True
    body["resume_token"] = resume["resume_token"]
    body["resume_expires_at"] = resume["resume_expires_at"]
    return body


BROKER_ENTRY_SOURCE_LABEL = "WeChat Mini Program"


def broker_entry_source_for_case(case: dict[str, Any] | None) -> str | None:
    """Human broker-facing source label — never OpenID / person_link_key."""
    if not isinstance(case, dict):
        return None
    if str(case.get("created_by_actor") or "").strip().lower() == "customer":
        return BROKER_ENTRY_SOURCE_LABEL
    channel = str(case.get("entry_channel") or case.get("source_channel") or "").strip().lower()
    if channel in ("mini_program", "wechat_mp", "wechat_mini_program"):
        return BROKER_ENTRY_SOURCE_LABEL
    return None
