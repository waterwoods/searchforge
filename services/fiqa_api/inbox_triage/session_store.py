"""
In-progress session store for Unified Intake.

Lightweight JSON persistence for pre-handoff conversation turns + workflow_state.
Enables refresh recovery: frontend can restore conversation by session_id.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SESSIONS_PATH = REPO_ROOT / "data" / "unified_intake_sessions.json"
MAX_STORED_SESSIONS = 50


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _store_path() -> Path:
    raw_path = (os.getenv("UNIFIED_INTAKE_SESSIONS_PATH") or "").strip()
    if not raw_path:
        return DEFAULT_SESSIONS_PATH
    path = Path(raw_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def _empty_payload() -> dict[str, Any]:
    return {"sessions": []}


def _read_payload() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return _empty_payload()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_payload()
    if not isinstance(payload, dict):
        return _empty_payload()
    sessions = payload.get("sessions")
    if not isinstance(sessions, list):
        return _empty_payload()
    return {"sessions": [s for s in sessions if isinstance(s, dict) and s.get("session_id")]}


def _write_payload(payload: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


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

    payload = _read_payload()
    sessions = payload["sessions"]
    existing_li: dict[str, Any] | None = None
    existing_active: str | None = None
    existing_lv: str | None = None
    existing_uh: dict[str, str] | None = None
    for s in sessions:
        if (s.get("session_id") or "").strip() == sid:
            raw_li = s.get("light_identity_binding")
            existing_li = _normalize_light_identity_binding(raw_li)
            ac = str(s.get("active_case_id") or "").strip()
            existing_active = ac if ac else None
            lv = str(s.get("last_vehicle_key") or "").strip()
            existing_lv = lv if lv else None
            existing_uh = _normalize_user_identity_hint(s.get("user_identity_hint"))
            break
    # Update existing or append
    found = False
    for i, s in enumerate(sessions):
        if (s.get("session_id") or "").strip() == sid:
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
            sessions[i] = row
            found = True
            break
    if not found:
        row = {
            "session_id": sid,
            "turns": normalized_turns,
            "workflow_state": workflow_state,
            "updated_at": updated_at,
        }
        if existing_li:
            row["light_identity_binding"] = existing_li
        sessions.append(row)
    # Evict oldest if over limit
    sessions.sort(key=lambda s: s.get("updated_at") or "", reverse=True)
    payload["sessions"] = sessions[:MAX_STORED_SESSIONS]
    _write_payload(payload)


def get_in_progress_session(session_id: str) -> dict[str, Any] | None:
    """
    Return in-progress session by session_id, or None if not found.
    Returns { turns, workflow_state, light_identity_binding?, active_case_id?, ... } for frontend restore.
    """
    sid = (session_id or "").strip()
    if not sid:
        return None
    payload = _read_payload()
    for s in payload["sessions"]:
        if (s.get("session_id") or "").strip() == sid:
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
    return None


def get_session_light_identity_binding(session_id: str) -> dict[str, Any] | None:
    """Pending identity fields for triage merge before formal submit (JSON truth)."""
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
    payload = _read_payload()
    sessions = payload["sessions"]
    found = False
    for i, s in enumerate(sessions):
        if (s.get("session_id") or "").strip() != sid:
            continue
        prev = _normalize_light_identity_binding(s.get("light_identity_binding")) or {}
        prev.update(merged)
        sessions[i] = {**s, "light_identity_binding": prev}
        found = True
        break
    if not found:
        raise ValueError("session_not_found")
    sessions.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    payload["sessions"] = sessions[:MAX_STORED_SESSIONS]
    _write_payload(payload)


def delete_in_progress_session(session_id: str) -> bool:
    """Remove session. Prefer binding-preserving paths; full delete drops continuity hints."""
    sid = (session_id or "").strip()
    if not sid:
        return False
    payload = _read_payload()
    before = len(payload["sessions"])
    payload["sessions"] = [s for s in payload["sessions"] if (s.get("session_id") or "").strip() != sid]
    if len(payload["sessions"]) < before:
        _write_payload(payload)
        return True
    return False


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
    payload = _read_payload()
    sessions = payload["sessions"]
    updated_at = _utc_now_iso()
    hint = _normalize_user_identity_hint(user_identity_hint) if user_identity_hint else None

    def _apply_to_row(row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
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
            merged = {**prev, **hint}
            out["user_identity_hint"] = merged
        return out

    found = False
    for i, s in enumerate(sessions):
        if (s.get("session_id") or "").strip() != sid:
            continue
        sessions[i] = _apply_to_row(s)
        found = True
        break
    if not found:
        base: dict[str, Any] = {
            "session_id": sid,
            "turns": [],
            "workflow_state": {},
            "updated_at": updated_at,
        }
        sessions.append(_apply_to_row(base))
    sessions.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    payload["sessions"] = sessions[:MAX_STORED_SESSIONS]
    _write_payload(payload)


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
    payload = _read_payload()
    sessions = payload["sessions"]
    updated_at = _utc_now_iso()
    vk = str(vehicle_key or "").strip() or None
    for i, s in enumerate(sessions):
        if (s.get("session_id") or "").strip() != sid:
            continue
        prev_li = _normalize_light_identity_binding(s.get("light_identity_binding"))
        uh = _normalize_user_identity_hint(s.get("user_identity_hint"))
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
        sessions[i] = row
        break
    else:
        row = {
            "session_id": sid,
            "turns": [],
            "workflow_state": {},
            "updated_at": updated_at,
            "active_case_id": cid,
        }
        if vk:
            row["last_vehicle_key"] = vk
        sessions.append(row)
    sessions.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    payload["sessions"] = sessions[:MAX_STORED_SESSIONS]
    _write_payload(payload)
