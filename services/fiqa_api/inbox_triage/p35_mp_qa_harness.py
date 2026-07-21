"""P35.1 — Mini Program Founder QA reset harness (test infrastructure only).

Resets / seeds Active Case state for ONE exact opaque person_link_key (wx_*).

Security (all required for mutating ops):
  ENABLE_P35_MP_QA_HARNESS=1
  UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1
  Support export key when production-like (ENV=prod / DB-primary writes)

Never:
  - wildcard / fuzzy customer lookup
  - bulk reset
  - hard-delete production (non-QA) cases
  - mutate an identity other than the exact session_id provided

Presets:
  fresh        — clear binding; soft-archive prior p35_mp_qa cases for that identity
  active       — seed one Active Claim + bind + resume token
  request_more — seed Active Claim + broker VIN request-more
"""

from __future__ import annotations

import logging
import os
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Final

logger = logging.getLogger(__name__)

DEMO_NAME: Final[str] = "p35_mp_qa"
_TRUTHY: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})

CONFIRM_FRESH: Final[str] = "FRESH"
CONFIRM_ACTIVE: Final[str] = "ACTIVE"
CONFIRM_REQUEST_MORE: Final[str] = "REQUEST_MORE"

_AUDIT_LOCK = threading.Lock()
_AUDIT_EVENTS: list[dict[str, Any]] = []
_AUDIT_MAX = 200

# Founder QA Console identity preference (process memory; no secrets).
# Keyed by actor + environment → exact wx_* person_link / session_id.
_PREF_LOCK = threading.Lock()
_IDENTITY_PREFS: dict[str, dict[str, Any]] = {}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _truthy(name: str) -> bool:
    return (os.getenv(name) or "").strip().lower() in _TRUTHY


def harness_enabled() -> bool:
    return _truthy("ENABLE_P35_MP_QA_HARNESS") and _truthy("UNIFIED_INTAKE_QA_FIXTURE_SURFACE")


def harness_status() -> dict[str, Any]:
    from services.fiqa_api.db.service_record_settings import is_production_mode
    from services.fiqa_api.security.support_export_gate import support_export_secret_configured

    enabled = harness_enabled()
    prod_like = is_production_mode()
    return {
        "ok": True,
        "enabled": enabled,
        "demo_name": DEMO_NAME,
        "environment": _environment_label(),
        "production_like": prod_like,
        "support_key_configured": support_export_secret_configured(),
        "require_support_key": prod_like,
        "notes": (
            "Requires ENABLE_P35_MP_QA_HARNESS=1 and UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1. "
            "Production-like runtimes also require UNIFIED_INTAKE_SUPPORT_API_KEY. "
            "Operations are scoped to one exact wx_* session_id / person_link_key."
        ),
    }


def assert_harness_allowed(*, require_support_key_in_prod: bool = True) -> None:
    """Raise ValueError with stable codes when the harness must refuse."""
    from services.fiqa_api.db.service_record_settings import is_production_mode
    from services.fiqa_api.security.support_export_gate import support_export_secret_configured

    if not _truthy("ENABLE_P35_MP_QA_HARNESS"):
        raise ValueError("p35_mp_qa_harness_disabled")
    if not _truthy("UNIFIED_INTAKE_QA_FIXTURE_SURFACE"):
        raise ValueError("p35_mp_qa_surface_disabled")
    if require_support_key_in_prod and is_production_mode() and not support_export_secret_configured():
        raise ValueError("p35_mp_qa_support_key_required")


def _environment_label() -> str:
    if _truthy("UNIFIED_INTAKE_QA_FIXTURE_SURFACE"):
        return "qa"
    env = (os.getenv("ENV") or "local").strip().lower() or "local"
    return env


def _mask_identity(session_id: str) -> str:
    s = (session_id or "").strip()
    if len(s) <= 12:
        return "wx_…"
    return f"{s[:6]}…{s[-4:]}"


def _mask_token(token: str) -> str:
    t = (token or "").strip()
    if len(t) <= 16:
        return "h5t1_…"
    return f"{t[:8]}…{t[-6:]}"


def normalize_exact_person_link(session_id: str | None) -> str:
    """Accept only an exact opaque wx_* person_link / session_id — no fuzzy match."""
    sid = (session_id or "").strip()
    if "*" in sid or "%" in sid or "," in sid:
        raise ValueError("wildcard_identity_forbidden")
    if not sid.startswith("wx_") or len(sid) < 12:
        raise ValueError("exact_wx_session_id_required")
    if any(ch.isspace() for ch in sid):
        raise ValueError("exact_wx_session_id_required")
    return sid[:80]


def resolve_person_link_from_sim_openid(sim_openid: str | None) -> str:
    """Test/local helper — only when WeChat simulate login is allowed."""
    from services.fiqa_api.inbox_triage.mp_customer_identity import mp_simulate_allowed
    from services.fiqa_api.inbox_triage.wechat_binding import opaque_person_link_key

    if not mp_simulate_allowed():
        raise ValueError("sim_openid_not_allowed")
    raw = (sim_openid or "").strip()
    if not raw or "*" in raw or "%" in raw:
        raise ValueError("exact_sim_openid_required")
    return opaque_person_link_key(raw)[:80]


def _append_audit(event: dict[str, Any]) -> dict[str, Any]:
    row = dict(event)
    row.setdefault("at", _utc_now_iso())
    row.setdefault("environment", _environment_label())
    row.setdefault("demo_name", DEMO_NAME)
    with _AUDIT_LOCK:
        _AUDIT_EVENTS.insert(0, row)
        del _AUDIT_EVENTS[_AUDIT_MAX:]
    logger.info(
        "p35_mp_qa_audit preset=%s identity=%s ok=%s",
        row.get("preset"),
        row.get("identity_masked"),
        row.get("ok"),
    )
    return row


def list_audit_events(*, limit: int = 20) -> list[dict[str, Any]]:
    n = max(1, min(int(limit), 100))
    with _AUDIT_LOCK:
        return deepcopy(_AUDIT_EVENTS[:n])


def record_audit_event(event: dict[str, Any]) -> dict[str, Any]:
    """Public audit append for console/CLI rejected or partial outcomes."""
    return _append_audit(event)


def mask_identity(session_id: str) -> str:
    return _mask_identity(session_id)


def reset_audit_events_for_tests() -> None:
    with _AUDIT_LOCK:
        _AUDIT_EVENTS.clear()


def reset_identity_prefs_for_tests() -> None:
    with _PREF_LOCK:
        _IDENTITY_PREFS.clear()


def _pref_key(actor: str, environment: str | None = None) -> str:
    act = (actor or "founder").strip()[:64] or "founder"
    env = (environment or _environment_label()).strip().lower() or "local"
    return f"{act}:{env}"


def get_selected_identity(*, actor: str = "founder") -> dict[str, Any] | None:
    """Return saved exact identity for actor+environment, or None."""
    key = _pref_key(actor)
    with _PREF_LOCK:
        row = _IDENTITY_PREFS.get(key)
        return dict(row) if isinstance(row, dict) else None


def set_selected_identity(*, session_id: str, actor: str = "founder", label: str | None = None) -> dict[str, Any]:
    """Persist exact wx_* identity for actor+environment (no secrets)."""
    person_link = normalize_exact_person_link(session_id)
    env = _environment_label()
    key = _pref_key(actor, env)
    row = {
        "session_id": person_link,
        "identity_masked": _mask_identity(person_link),
        "actor": (actor or "founder").strip()[:64] or "founder",
        "environment": env,
        "label": (label or "").strip()[:64] or None,
        "selected_at": _utc_now_iso(),
    }
    with _PREF_LOCK:
        _IDENTITY_PREFS[key] = dict(row)
    return row


def forget_selected_identity(*, actor: str = "founder") -> dict[str, Any]:
    key = _pref_key(actor)
    with _PREF_LOCK:
        existed = key in _IDENTITY_PREFS
        _IDENTITY_PREFS.pop(key, None)
    return {"ok": True, "forgotten": existed, "actor": (actor or "founder").strip()[:64] or "founder"}


def _is_harness_case(case: dict[str, Any] | None) -> bool:
    if not isinstance(case, dict):
        return False
    if str(case.get("demo_name") or "").strip() != DEMO_NAME:
        return False
    if not bool(case.get("workbench_test")):
        return False
    return True


def _load_case(case_id: str) -> dict[str, Any] | None:
    cid = (case_id or "").strip()
    if not cid:
        return None
    try:
        from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read

        case = get_case_for_read(cid)
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
        from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
            default_case_intake_service,
        )

        store = getattr(default_case_intake_service(), "store", None)
        cases = getattr(store, "cases", None)
        if isinstance(cases, dict):
            row = cases.get(cid)
            if isinstance(row, dict):
                return row
    except Exception:
        pass
    return None


def _tag_harness_case(case: dict[str, Any], *, person_link: str, preset: str) -> dict[str, Any]:
    out = dict(case)
    out["workbench_test"] = True
    out["demo_name"] = DEMO_NAME
    out["demo_flags"] = {"demo_name": DEMO_NAME, "p35_mp_qa": True}
    out["harness_environment"] = _environment_label()
    out["harness_cleanup_eligible"] = True
    out["exclude_from_production_metrics"] = True
    out["person_link_key"] = person_link
    out["p35_mp_qa_preset"] = preset
    out["p35_mp_qa_tagged_at"] = _utc_now_iso()
    return out


def _soft_archive_case(case_id: str) -> bool:
    cid = (case_id or "").strip()
    if not cid:
        return False
    case = _load_case(cid)
    if isinstance(case, dict):
        tagged = dict(case)
        tagged["workbench_archived"] = True
        tagged["workbench_test"] = True
        tagged["admin_lifecycle"] = "archived"
        _persist_tagged_case(cid, tagged)
        # Also try durable workbench flag path when available.
        try:
            from services.fiqa_api.inbox_triage.case_store import update_case_workbench_flags

            update_case_workbench_flags(cid, archived=True, is_test=True)
        except Exception:
            pass
        return True
    try:
        from services.fiqa_api.inbox_triage.case_store import update_case_workbench_flags

        return update_case_workbench_flags(cid, archived=True, is_test=True) is not None
    except Exception:
        return False


def _persist_tagged_case(case_id: str, case: dict[str, Any]) -> None:
    # Prefer in-memory intake store (unit tests / ephemeral).
    try:
        from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
            default_case_intake_service,
        )

        store = getattr(default_case_intake_service(), "store", None)
        cases = getattr(store, "cases", None)
        if isinstance(cases, dict) and case_id in cases:
            cases[case_id] = dict(case)
            return
    except Exception:
        pass

    from services.fiqa_api.inbox_triage.case_store import _persist_case_after_update

    if _persist_case_after_update(case_id, case):
        return
    # Local JSON fallback path used by fixture-style tests.
    try:
        from services.fiqa_api.inbox_triage.case_store import (
            _read_payload,
            _sort_recent,
            _write_payload,
        )

        payload = _read_payload()
        cases = payload.get("cases") or []
        replaced = False
        for index, existing in enumerate(cases):
            if existing.get("case_id") == case_id:
                cases[index] = case
                replaced = True
                break
        if not replaced:
            cases.append(case)
        payload["cases"] = _sort_recent(cases)
        _write_payload(payload)
    except Exception:
        logger.warning("p35_mp_qa persist tagged case failed case_id=%s", case_id[:20])


def _open_request_summary(case: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(case, dict):
        return None

    open_request: dict[str, Any] | None = None
    # Prefer denormalized request summaries written by Slice1 command service.
    for key in ("p20_slice1_request_summary", "slice1_request_summary"):
        row = case.get(key)
        if isinstance(row, dict) and row:
            open_request = row
            break
    if open_request is None:
        for key in ("p20_slice1_projection", "slice1_projection", "p20_slice1", "slice1"):
            proj = case.get(key)
            if isinstance(proj, dict) and isinstance(proj.get("open_request"), dict):
                open_request = proj.get("open_request")  # type: ignore[assignment]
                break
    if not isinstance(open_request, dict):
        return None

    active = open_request.get("active_item")
    if not isinstance(active, dict):
        items = open_request.get("items")
        if isinstance(items, list) and items:
            first = items[0]
            active = first if isinstance(first, dict) else None
    if not isinstance(active, dict):
        # Some projections nest next action without active_item on summary.
        for key in ("p20_slice1_projection", "slice1_projection"):
            proj = case.get(key)
            if not isinstance(proj, dict):
                continue
            nxt = proj.get("customer_next_action")
            if isinstance(nxt, dict) and nxt.get("request_item_id"):
                active = {
                    "request_item_id": nxt.get("request_item_id"),
                    "item_type": nxt.get("item_type") or "vin",
                    "label": nxt.get("title") or nxt.get("label"),
                    "status": "open",
                }
                break
    if not isinstance(active, dict):
        return None
    item_id = str(active.get("request_item_id") or active.get("item_id") or "").strip() or None
    item_type = str(active.get("item_type") or "").strip() or None
    label = str(active.get("label") or active.get("title") or "").strip() or None
    status = str(active.get("status") or open_request.get("status") or "open").strip() or "open"
    return {
        "request_item_id": item_id,
        "item_type": item_type,
        "label": label,
        "status": status,
    }


def _case_task_summary(case: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(case, dict):
        return {
            "claim_status": None,
            "current_task": None,
            "next_action": None,
            "qa_fixture_demo_name": None,
            "last_preset_applied": None,
            "last_reset_time": None,
        }
    claim_status = (
        str(
            case.get("claim_phase")
            or case.get("case_status")
            or case.get("lifecycle_status")
            or case.get("status")
            or ""
        ).strip()
        or None
    )
    waiting = str(case.get("waiting_on") or "").strip() or None
    if waiting in ("none", "None"):
        waiting = None
    next_action = str(case.get("next_action") or "").strip() or None
    if next_action in ("none", "None"):
        next_action = None
    # Slice1 customer_next_action title when present.
    for key in ("p20_slice1_projection", "slice1_projection"):
        proj = case.get(key)
        if isinstance(proj, dict):
            nxt = proj.get("customer_next_action")
            if isinstance(nxt, dict):
                title = str(nxt.get("title") or nxt.get("label") or "").strip()
                if title and not next_action:
                    next_action = title
                break
    open_rm = _open_request_summary(case)
    if not next_action and waiting:
        next_action = waiting
    if not next_action and open_rm and open_rm.get("item_type"):
        next_action = f"request_more:{open_rm['item_type']}"
    current_task = waiting
    if not current_task and open_rm:
        current_task = open_rm.get("label")
    return {
        "claim_status": claim_status,
        "current_task": current_task,
        "next_action": next_action,
        "qa_fixture_demo_name": str(case.get("demo_name") or "").strip() or None,
        "last_preset_applied": str(case.get("p35_mp_qa_preset") or "").strip() or None,
        "last_reset_time": str(case.get("p35_mp_qa_tagged_at") or "").strip() or None,
    }


def inspect_identity(session_id: str) -> dict[str, Any]:
    assert_harness_allowed()
    person_link = normalize_exact_person_link(session_id)
    from services.fiqa_api.inbox_triage.mp_customer_identity import (
        lookup_bound_case_id,
        resolve_active_case_for_person_link,
    )

    bound_id = lookup_bound_case_id(person_link)
    active = resolve_active_case_for_person_link(person_link)
    active_id = str((active or {}).get("case_id") or "").strip() or None
    case = _load_case(active_id or bound_id or "") if (active_id or bound_id) else None
    task = _case_task_summary(case)
    open_rm = _open_request_summary(case)
    resume_bound = bool(active_id)
    return {
        "ok": True,
        "environment": _environment_label(),
        "identity_masked": _mask_identity(person_link),
        "session_id_prefix": person_link[:10],
        "person_link_key_masked": _mask_identity(person_link),
        "has_active_case": bool(active_id),
        "bound_case_id": bound_id,
        "active_case_id": active_id,
        "bound_case_is_harness": _is_harness_case(case) if case else False,
        "demo_name": (case or {}).get("demo_name"),
        "workbench_archived": bool((case or {}).get("workbench_archived")),
        "claim_status": task["claim_status"],
        "current_task": task["current_task"],
        "next_action": task["next_action"],
        "resume_token_bound": resume_bound,
        "resume_token_masked": None,
        "open_request_more": open_rm,
        "qa_fixture_demo_name": task["qa_fixture_demo_name"],
        "last_preset_applied": task["last_preset_applied"],
        "last_reset_time": task["last_reset_time"],
    }


def sanitize_preset_result_for_console(result: dict[str, Any]) -> dict[str, Any]:
    """Strip raw secrets/tokens before returning preset results to browser UI."""
    out = dict(result)
    out.pop("resume_token", None)
    if out.get("resume_token_masked") is None and result.get("resume_token"):
        out["resume_token_masked"] = _mask_token(str(result.get("resume_token") or ""))
    # Never echo exact session_id in mutation results — masked only.
    out.pop("session_id", None)
    return out


def console_status(*, actor: str = "founder", authorized: bool = True) -> dict[str, Any]:
    """Normalized Founder QA Console status (safe for browser; no support secrets)."""
    from services.fiqa_api.db.service_record_settings import is_production_mode
    from services.fiqa_api.security.intake_api_gate import intake_api_secret_configured
    from services.fiqa_api.security.support_export_gate import support_export_secret_configured

    base = harness_status()
    prod_like = bool(base.get("production_like")) or is_production_mode()
    enabled = bool(base.get("enabled"))
    pref = get_selected_identity(actor=actor)
    identity_block: dict[str, Any] | None = None
    active_case: dict[str, Any] | None = None
    resume_binding: dict[str, Any] | None = None
    open_rm: dict[str, Any] | None = None
    inspect_error: str | None = None
    selected_session_id: str | None = None

    if pref and pref.get("session_id"):
        selected_session_id = str(pref["session_id"])
        identity_block = {
            "label": pref.get("label"),
            "identity_masked": pref.get("identity_masked") or _mask_identity(selected_session_id),
            "session_id": selected_session_id,  # exact — Founder needs copy; not a secret
            "person_link_key_masked": _mask_identity(selected_session_id),
            "selected_at": pref.get("selected_at"),
            "environment": pref.get("environment"),
        }
        if enabled:
            try:
                inspected = inspect_identity(selected_session_id)
                identity_block["active_case_id"] = inspected.get("active_case_id")
                identity_block["bound_case_id"] = inspected.get("bound_case_id")
                identity_block["last_seen"] = pref.get("selected_at")
                active_case = {
                    "has_active_case": inspected.get("has_active_case"),
                    "case_id": inspected.get("active_case_id") or inspected.get("bound_case_id"),
                    "claim_status": inspected.get("claim_status"),
                    "current_task": inspected.get("current_task"),
                    "next_action": inspected.get("next_action"),
                    "qa_fixture_demo_name": inspected.get("qa_fixture_demo_name"),
                    "last_preset_applied": inspected.get("last_preset_applied"),
                    "last_reset_time": inspected.get("last_reset_time"),
                    "bound_case_is_harness": inspected.get("bound_case_is_harness"),
                }
                resume_binding = {
                    "bound": bool(inspected.get("resume_token_bound")),
                    "resume_token_masked": inspected.get("resume_token_masked"),
                }
                open_rm = inspected.get("open_request_more")
            except ValueError as exc:
                inspect_error = str(exc)
            except Exception:
                inspect_error = "status_inspect_failed"

    latest_audit = None
    latest_preset = None
    try:
        events = list_audit_events(limit=1)
        if events:
            latest_audit = {
                "at": events[0].get("at"),
                "preset": events[0].get("preset"),
                "ok": events[0].get("ok"),
                "identity_masked": events[0].get("identity_masked"),
                "case_id": events[0].get("case_id"),
                "actor": events[0].get("actor"),
            }
            latest_preset = events[0].get("preset")
    except Exception:
        latest_audit = None

    safety = "qa_reset_enabled" if enabled and not prod_like else (
        "production_qa_reset_forced_disabled" if prod_like and not enabled else (
            "harness_disabled" if not enabled else "production_like_harness_gated"
        )
    )

    return {
        "ok": True,
        "environment": base.get("environment"),
        "enabled": enabled,
        "authorized": bool(authorized),
        "production_like": prod_like,
        "production_safety": safety,
        "support_key_configured": support_export_secret_configured(),
        "require_support_key": bool(base.get("require_support_key")),
        "intake_api_configured": intake_api_secret_configured(),
        "actor": (actor or "founder").strip()[:64] or "founder",
        "selected_identity": identity_block,
        "active_case": active_case,
        "resume_binding": resume_binding,
        "open_request_more": open_rm,
        "latest_qa_preset": latest_preset or (active_case or {}).get("last_preset_applied"),
        "latest_qa_audit_event": latest_audit,
        "inspect_error": inspect_error,
        "mutations_allowed": bool(enabled and authorized and selected_session_id),
        "notes": base.get("notes"),
    }


def preset_fresh_customer(*, session_id: str, confirm: str, actor: str = "founder") -> dict[str, Any]:
    """Clear Active Case binding for exact identity; soft-archive prior harness cases only."""
    assert_harness_allowed()
    if (confirm or "").strip() != CONFIRM_FRESH:
        raise ValueError("confirm_fresh_required")
    person_link = normalize_exact_person_link(session_id)
    from services.fiqa_api.inbox_triage.mp_customer_identity import (
        clear_active_case_binding,
        lookup_bound_case_id,
    )

    prior_id = lookup_bound_case_id(person_link)
    archived: list[str] = []
    retained_non_qa: list[str] = []
    if prior_id:
        case = _load_case(prior_id)
        if _is_harness_case(case):
            if _soft_archive_case(prior_id):
                archived.append(prior_id)
        elif case is not None:
            # Do not hard-delete / archive production cases — only detach from MP Continue.
            retained_non_qa.append(prior_id)
        clear_active_case_binding(person_link)

    # Idempotent: clear again even if already empty.
    clear_active_case_binding(person_link)

    result = {
        "ok": True,
        "preset": "fresh",
        "identity_masked": _mask_identity(person_link),
        "has_active_case": False,
        "cleared_binding": True,
        "archived_harness_case_ids": archived,
        "retained_non_qa_case_ids": retained_non_qa,
        "local_client_hint": (
            "Relaunch Mini Program Service Home. Server returns has_active_case=false; "
            "client clears resume token. No Active Claim card; 我要报案 is primary."
        ),
        "data_effects": {
            "reset": [
                "mp_customer_active_case binding for this exact identity",
                "soft-archive of prior p35_mp_qa harness cases for this identity (if any)",
            ],
            "retained": [
                "non-QA case rows (binding cleared only — not deleted)",
                "timeline/evidence on retained cases",
                "unrelated identities",
            ],
            "recreated": [],
        },
    }
    audit = _append_audit(
        {
            "preset": "fresh",
            "ok": True,
            "actor": actor,
            "identity_masked": result["identity_masked"],
            "archived_harness_case_ids": archived,
            "retained_non_qa_case_ids": retained_non_qa,
        }
    )
    result["audit"] = audit
    return result


def _seed_active_case(*, person_link: str, preset: str) -> dict[str, Any]:
    """Create one harness claim, tag it, bind identity, return resume token."""
    from services.fiqa_api.inbox_triage.mp_customer_identity import (
        bind_active_case,
        clear_active_case_binding,
        lookup_bound_case_id,
    )
    from services.fiqa_api.inbox_triage.p20_customer_start_claim import start_customer_claim

    prior_id = lookup_bound_case_id(person_link)
    archived: list[str] = []
    if prior_id:
        case = _load_case(prior_id)
        if _is_harness_case(case):
            if _soft_archive_case(prior_id):
                archived.append(prior_id)
        clear_active_case_binding(person_link)

    cmd = f"p35-mp-qa-{preset}-{uuid.uuid4().hex[:12]}"
    created = start_customer_claim(
        command_id=cmd,
        idempotency_key=cmd,
        session_id=person_link,
        accident_description="P35.1 QA：停车场倒车碰撞，前保险杠受损",
        accident_datetime="2026-07-20 10:00",
        accident_location="洛杉矶停车场",
        injury_status="no",
        is_test=True,
        force_new=False,
    )
    outcome = str(created.get("outcome") or "")
    if outcome not in ("accepted", "replayed"):
        # Binding may still have been empty; surface create failure.
        raise RuntimeError(f"seed_claim_failed:{created.get('error_code') or outcome}")

    case_id = str(created.get("case_id") or "").strip()
    token = str(created.get("resume_token") or "").strip()
    if not case_id or not token:
        raise RuntimeError("seed_claim_missing_case_or_token")

    case = _load_case(case_id) or {"case_id": case_id}
    tagged = _tag_harness_case(case, person_link=person_link, preset=preset)
    _persist_tagged_case(case_id, tagged)
    bind_active_case(person_link, case_id)

    return {
        "case_id": case_id,
        "resume_token": token,
        "resume_token_masked": _mask_token(token),
        "resume_expires_at": created.get("resume_expires_at"),
        "archived_harness_case_ids": archived,
        "outcome": outcome,
    }


def preset_active_claim(*, session_id: str, confirm: str, actor: str = "founder") -> dict[str, Any]:
    assert_harness_allowed()
    if (confirm or "").strip() != CONFIRM_ACTIVE:
        raise ValueError("confirm_active_required")
    person_link = normalize_exact_person_link(session_id)
    seeded = _seed_active_case(person_link=person_link, preset="active")
    result = {
        "ok": True,
        "preset": "active",
        "identity_masked": _mask_identity(person_link),
        "has_active_case": True,
        "case_id": seeded["case_id"],
        "resume_token": seeded["resume_token"],
        "resume_token_masked": seeded["resume_token_masked"],
        "resume_expires_at": seeded.get("resume_expires_at"),
        "archived_harness_case_ids": seeded["archived_harness_case_ids"],
        "local_client_hint": (
            "Relaunch Mini Program. Session restore binds Continue to this case. "
            "Do not Start Claim again — One Active Case applies."
        ),
        "data_effects": {
            "reset": ["prior binding; soft-archive prior p35_mp_qa case for this identity"],
            "retained": ["unrelated identities", "non-QA cases (detached only)"],
            "recreated": ["one workbench_test claim demo_name=p35_mp_qa", "resume token", "binding"],
        },
    }
    audit = _append_audit(
        {
            "preset": "active",
            "ok": True,
            "actor": actor,
            "identity_masked": result["identity_masked"],
            "case_id": seeded["case_id"],
            "archived_harness_case_ids": seeded["archived_harness_case_ids"],
        }
    )
    result["audit"] = audit
    return result


def _apply_vin_request_more(case_id: str) -> dict[str, Any]:
    from services.fiqa_api.inbox_triage.p20_slice1_command_service import default_slice1_service

    cmd = f"p35-mp-qa-rm-{uuid.uuid4().hex[:12]}"
    result = default_slice1_service().accept_request_more(
        case_id=case_id,
        broker_id="office:p35_mp_qa",
        command_id=cmd,
        idempotency_key=cmd,
        expected_case_version=0,
        requested_items=[
            {
                "request_item_id": f"item_p35_vin_{uuid.uuid4().hex[:10]}",
                "item_type": "vin",
                "label": "补充车架号（VIN）",
                "instructions": "请填写17位车架号（VIN）",
                "required": True,
                "position": 1,
            }
        ],
        reason="P35.1 QA Request More VIN",
    )
    if result.get("outcome") != "accepted":
        raise RuntimeError(f"request_more_failed:{result.get('error_code') or result.get('outcome')}")
    return result


def preset_request_more(*, session_id: str, confirm: str, actor: str = "founder") -> dict[str, Any]:
    assert_harness_allowed()
    if (confirm or "").strip() != CONFIRM_REQUEST_MORE:
        raise ValueError("confirm_request_more_required")
    person_link = normalize_exact_person_link(session_id)
    seeded = _seed_active_case(person_link=person_link, preset="request_more")
    followup = _apply_vin_request_more(seeded["case_id"])
    result = {
        "ok": True,
        "preset": "request_more",
        "identity_masked": _mask_identity(person_link),
        "has_active_case": True,
        "case_id": seeded["case_id"],
        "resume_token": seeded["resume_token"],
        "resume_token_masked": seeded["resume_token_masked"],
        "resume_expires_at": seeded.get("resume_expires_at"),
        "archived_harness_case_ids": seeded["archived_harness_case_ids"],
        "request_more_outcome": followup.get("outcome"),
        "requested_item_type": "vin",
        "local_client_hint": (
            "Relaunch Mini Program → Continue → Task Home should surface VIN / 车架号 request. "
            "Broker and customer share One Truth on this case."
        ),
        "data_effects": {
            "reset": ["prior binding; soft-archive prior p35_mp_qa case for this identity"],
            "retained": ["unrelated identities"],
            "recreated": [
                "one p35_mp_qa claim",
                "broker request-more for VIN",
                "resume token + binding",
            ],
        },
    }
    audit = _append_audit(
        {
            "preset": "request_more",
            "ok": True,
            "actor": actor,
            "identity_masked": result["identity_masked"],
            "case_id": seeded["case_id"],
            "requested_item_type": "vin",
        }
    )
    result["audit"] = audit
    return result
