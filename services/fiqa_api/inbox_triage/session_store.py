"""
In-progress session store for Unified Intake.

Persists pre-handoff conversation turns + workflow_state to Postgres when
SERVICE_RECORD_DATABASE_URL / DATABASE_URL is set.

Without a DB URL, persistence uses the in-process repository only if
UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS is explicitly enabled; otherwise
writes are no-ops and reads return None (see session_repository).
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from services.fiqa_api.inbox_triage import session_repository as repo


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _extract_workflow_state(triage_result: dict[str, Any]) -> dict[str, Any]:
    """Extract WORKFLOW_STATE_KEYS from triage result."""
    keys = (
        "collection_stage",
        "follow_up_type",
        "handoff_ready",
        "case_creation_suggested",
        "collected_fields",
        "still_needed_fields",
        "human_confirmation_required",
        "human_confirmation_fields",
        "next_best_question",
        "lifecycle_status",
        "triage_mode",
        "conversion_stage",
        "last_conversion_turn_index",
        "action_ready",
        "intake_flow_milestone",
    )
    out: dict[str, Any] = {}
    for k in keys:
        if k in triage_result:
            out[k] = triage_result[k]
    return out


def _normalize_turn(turn: Any) -> dict[str, Any] | None:
    """Normalize a turn for storage."""
    if not isinstance(turn, dict):
        return None
    role = (str(turn.get("role") or "customer").strip().lower())
    if role not in ("customer", "system"):
        role = "customer"
    text = str(turn.get("text") or turn.get("content") or "").strip()
    if not text:
        return None
    out: dict[str, Any] = {"role": role, "text": text}
    if role == "system" and "triageResult" in turn:
        out["triageResult"] = turn["triageResult"]
    elif role == "system" and "triage_result" in turn:
        out["triageResult"] = turn["triage_result"]
    return out


def _normalize_user_identity_hint(raw: Any) -> dict[str, str] | None:
    """Optional session hints from extracted name/phone (not auth)."""
    if not isinstance(raw, dict):
        return None
    out: dict[str, str] = {}
    for k in ("phone", "name"):
        v = raw.get(k)
        if isinstance(v, str) and v.strip():
            out[k] = v.strip()[:256]
    return out if out else None


def _normalize_light_identity_binding(raw: Any) -> dict[str, Any] | None:
    """Keep only valid Stage-1 identity keys for session pending merge."""
    if not isinstance(raw, dict):
        return None
    out: dict[str, Any] = {}
    ibs = str(raw.get("identity_binding_state") or "").strip().lower()
    if ibs in ("unbound", "prompted", "deferred", "linked"):
        out["identity_binding_state"] = ibs
    pk = raw.get("person_link_key")
    if isinstance(pk, str) and pk.strip():
        out["person_link_key"] = pk.strip()[:256]
    src = str(raw.get("person_link_source") or "").strip().lower()
    if src in ("wechat", "phone", "email"):
        out["person_link_source"] = src
    pc = raw.get("person_link_confidence")
    try:
        if pc is not None:
            c = float(pc)
            if 0.0 <= c <= 1.0:
                out["person_link_confidence"] = c
    except (TypeError, ValueError):
        pass
    return out if out else None


def save_in_progress_session(
    session_id: str,
    turns: list[dict[str, Any]],
    triage_result: dict[str, Any],
) -> None:
    """
    Save or update an in-progress session with turns and workflow_state.
    Call when triage returns and no case was persisted.
    Preserves optional WeChat/light_identity_binding across saves.
    """
    sid = (session_id or "").strip()
    if not sid:
        return
    normalized_turns: list[dict[str, Any]] = []
    for t in turns:
        nt = _normalize_turn(t)
        if nt:
            normalized_turns.append(nt)
    workflow_state = _extract_workflow_state(triage_result)
    updated_at = _utc_now_iso()

    existing_li: dict[str, Any] | None = None
    existing_active: str | None = None
    existing_lv: str | None = None
    existing_uh: dict[str, str] | None = None
    raw = repo.get_session(sid)
    if raw:
        raw_li = raw.get("light_identity_binding")
        existing_li = _normalize_light_identity_binding(raw_li)
        ac = str(raw.get("active_case_id") or "").strip()
        existing_active = ac if ac else None
        lv = str(raw.get("last_vehicle_key") or "").strip()
        existing_lv = lv if lv else None
        existing_uh = _normalize_user_identity_hint(raw.get("user_identity_hint"))

    row: dict[str, Any] = {
        "session_id": sid,
        "turns": normalized_turns,
        "workflow_state": workflow_state,
        "updated_at": updated_at,
    }
    if existing_li:
        row["light_identity_binding"] = existing_li
    if existing_active:
        row["active_case_id"] = existing_active
    if existing_lv:
        row["last_vehicle_key"] = existing_lv
    if existing_uh:
        row["user_identity_hint"] = existing_uh
    if not repo.upsert_session(sid, row):
        return


def get_in_progress_session(session_id: str) -> dict[str, Any] | None:
    """
    Return in-progress session by session_id, or None if not found.
    Returns { turns, workflow_state, light_identity_binding?, active_case_id?, ... } for frontend restore.
    """
    sid = (session_id or "").strip()
    if not sid:
        return None
    s = repo.get_session(sid)
    if s is None:
        return None
    turns = s.get("turns") or []
    workflow_state = s.get("workflow_state") or {}
    out: dict[str, Any] = {
        "turns": turns,
        "workflow_state": workflow_state,
        "updated_at": s.get("updated_at", ""),
    }
    li = _normalize_light_identity_binding(s.get("light_identity_binding"))
    if li:
        out["light_identity_binding"] = li
    ac = str(s.get("active_case_id") or "").strip()
    if ac:
        out["active_case_id"] = ac
    lv = str(s.get("last_vehicle_key") or "").strip()
    if lv:
        out["last_vehicle_key"] = lv
    uh = _normalize_user_identity_hint(s.get("user_identity_hint"))
    if uh:
        out["user_identity_hint"] = uh
    return out


def get_session_light_identity_binding(session_id: str) -> dict[str, Any] | None:
    """Pending identity fields for triage merge before formal submit (session truth)."""
    sid = (session_id or "").strip()
    if not sid:
        return None
    data = get_in_progress_session(sid)
    if not data:
        return None
    return _normalize_light_identity_binding(data.get("light_identity_binding"))


def patch_session_light_identity_binding(session_id: str, identity: dict[str, Any]) -> None:
    """
    Merge validated identity into existing session (e.g. after WeChat OAuth callback).
    Raises ValueError if session_id is unknown — caller must persist at least one triage turn first.
    """
    sid = (session_id or "").strip()
    if not sid:
        raise ValueError("session_id required")
    merged = _normalize_light_identity_binding(identity)
    if not merged:
        return
    raw = repo.get_session(sid)
    if not raw:
        raise ValueError("session_not_found")
    prev = _normalize_light_identity_binding(raw.get("light_identity_binding")) or {}
    prev.update(merged)
    new_row = {**raw, "light_identity_binding": prev, "updated_at": _utc_now_iso()}
    if not repo.upsert_session(sid, new_row):
        return


def delete_in_progress_session(session_id: str) -> bool:
    """Remove session. Prefer binding-preserving paths; full delete drops continuity hints."""
    sid = (session_id or "").strip()
    if not sid:
        return False
    return repo.delete_session(sid)


def patch_session_case_binding(
    session_id: str,
    *,
    active_case_id: str | None = None,
    last_vehicle_key: str | None = None,
    user_identity_hint: dict[str, Any] | None = None,
    clear_active_case: bool = False,
) -> None:
    """
    Update case binding / identity hints on an existing session row (creates row if missing).
    """
    sid = (session_id or "").strip()
    if not sid:
        return
    updated_at = _utc_now_iso()
    hint = _normalize_user_identity_hint(user_identity_hint) if user_identity_hint else None

    raw = repo.get_session(sid) or {
        "session_id": sid,
        "turns": [],
        "workflow_state": {},
        "updated_at": updated_at,
    }

    def _apply_to_row(row: dict[str, Any]) -> dict[str, Any]:
        out = copy.deepcopy(row)
        out["session_id"] = sid
        out["updated_at"] = updated_at
        if clear_active_case:
            out.pop("active_case_id", None)
        elif active_case_id is not None:
            ac = str(active_case_id).strip()
            if ac:
                out["active_case_id"] = ac
        if last_vehicle_key is not None:
            lv = str(last_vehicle_key).strip()
            if lv:
                out["last_vehicle_key"] = lv
            else:
                out.pop("last_vehicle_key", None)
        if hint:
            prev = _normalize_user_identity_hint(out.get("user_identity_hint")) or {}
            out["user_identity_hint"] = {**prev, **hint}
        return out

    new_row = _apply_to_row(raw)
    if not repo.upsert_session(sid, new_row):
        return


def save_session_binding_after_case_created(
    session_id: str,
    case_id: str,
    vehicle_key: str | None = None,
) -> None:
    """After persist_case: retain active_case_id + optional vehicle key; trim bulky turns."""
    sid = (session_id or "").strip()
    cid = (case_id or "").strip()
    if not sid or not cid:
        return
    existing = repo.get_session(sid) or {}
    updated_at = _utc_now_iso()
    vk = str(vehicle_key or "").strip() or None
    prev_li = _normalize_light_identity_binding(existing.get("light_identity_binding"))
    uh = _normalize_user_identity_hint(existing.get("user_identity_hint"))
    row: dict[str, Any] = {
        "session_id": sid,
        "turns": [],
        "workflow_state": {},
        "updated_at": updated_at,
        "active_case_id": cid,
    }
    if vk:
        row["last_vehicle_key"] = vk
    if prev_li:
        row["light_identity_binding"] = prev_li
    if uh:
        row["user_identity_hint"] = uh
    if not repo.upsert_session(sid, row):
        return
