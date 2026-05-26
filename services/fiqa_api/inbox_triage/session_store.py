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
import json
import logging
from datetime import datetime, timezone
from typing import Any

from services.fiqa_api.db.service_record_settings import is_production_mode, service_record_database_url
from services.fiqa_api.inbox_triage import session_repository as repo

logger = logging.getLogger(__name__)

# When patch_session_case_binding omits reuse_session_row, behavior matches historical repo.get_session read.
_PATCH_SESSION_ROW_UNSPECIFIED = object()


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


def _in_progress_session_payload_unchanged(
    raw: dict[str, Any],
    normalized_turns: list[dict[str, Any]],
    workflow_state: dict[str, Any],
) -> bool:
    """True if persisted turns and workflow already match (skip no-op write)."""
    try:
        prev_t = raw.get("turns") or []
        prev_w = raw.get("workflow_state") or {}
        # Hot path: new turns are appended every triage step — avoid serializing
        # large nested triageResult blobs when lengths already differ.
        if len(prev_t) != len(normalized_turns):
            return False
        if prev_w != workflow_state:
            return False
        if prev_t == normalized_turns:
            return True
        return json.dumps(
            prev_t, sort_keys=True, default=str, ensure_ascii=False
        ) == json.dumps(
            normalized_turns, sort_keys=True, default=str, ensure_ascii=False
        )
    except (TypeError, ValueError):
        return False


def in_progress_session_view(repo_row: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Shape a persisted intake session document into the API / route view (turns, workflow_state, hints).
    Caller should obtain repo_row via session_repository.get_session once per request when avoiding duplicate reads.
    """
    if not repo_row:
        return None
    s = repo_row
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
    ao = str(s.get("asserted_org_id") or "").strip()
    if ao:
        out["asserted_org_id"] = ao[:256]
    return out


def light_identity_binding_from_in_progress_view(view: dict[str, Any] | None) -> dict[str, Any] | None:
    """Normalized Stage-1 identity stub from an in-progress session view (no extra DB read)."""
    if not view:
        return None
    return _normalize_light_identity_binding(view.get("light_identity_binding"))


def save_in_progress_session(
    session_id: str,
    turns: list[dict[str, Any]],
    triage_result: dict[str, Any],
    *,
    pre_read_raw: dict[str, Any] | None = None,
    assume_fresh_co_read: bool = False,
    asserted_org_id: str | None = None,
) -> None:
    """
    Save or update an in-progress session with turns and workflow_state.
    Call when triage returns and no case was persisted.
    Preserves optional WeChat/light_identity_binding across saves.
    pre_read_raw: if the caller already loaded this session in the same request, pass it to avoid
    a second read; merged fields still apply.
    assume_fresh_co_read: when True and pre_read_raw is None, do not call get_session — the caller
    already determined the row is missing in the same request (avoids a duplicate DB read on cold session).
    """
    if is_production_mode() and not service_record_database_url():
        logger.warning("Postgres is required for intake session persistence in production")
        return
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
    raw: dict[str, Any] | None = pre_read_raw
    if raw is None and not assume_fresh_co_read:
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
    oid = (asserted_org_id or "").strip()[:256]
    if oid:
        row["asserted_org_id"] = oid
    elif raw:
        prev_o = str(raw.get("asserted_org_id") or "").strip()[:256]
        if prev_o:
            row["asserted_org_id"] = prev_o
    if raw and _in_progress_session_payload_unchanged(raw, normalized_turns, workflow_state):
        prev_org = str(raw.get("asserted_org_id") or "").strip()[:256]
        next_org = str(row.get("asserted_org_id") or "").strip()[:256]
        if prev_org == next_org:
            return
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
    return in_progress_session_view(repo.get_session(sid))


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


def _fresh_empty_session_row(session_id: str, updated_at: str) -> dict[str, Any]:
    """Mutable empty session shell (no deepcopy — only scalars and fresh list/dict instances)."""
    return {
        "session_id": session_id,
        "turns": [],
        "workflow_state": {},
        "updated_at": updated_at,
    }


def patch_session_case_binding(
    session_id: str,
    *,
    active_case_id: str | None = None,
    last_vehicle_key: str | None = None,
    user_identity_hint: dict[str, Any] | None = None,
    clear_active_case: bool = False,
    reuse_session_row: Any = _PATCH_SESSION_ROW_UNSPECIFIED,
) -> dict[str, Any] | None:
    """
    Update case binding / identity hints on an existing session row (creates row if missing).

    reuse_session_row: when this request already loaded the session document (e.g. route co-read),
    pass that dict to skip a duplicate repo.get_session. Pass None when the session row does not
    exist yet (same as DB miss — uses empty template without an extra read). When omitted, fetch from repo.

    Returns the merged session document written on success (caller may refresh co-read buffers).
    """
    sid = (session_id or "").strip()
    if not sid:
        return None
    updated_at = _utc_now_iso()
    hint = _normalize_user_identity_hint(user_identity_hint) if user_identity_hint else None

    base_from_repo: dict[str, Any] | None = None
    had_existing_row = False
    if reuse_session_row is _PATCH_SESSION_ROW_UNSPECIFIED:
        base_from_repo = repo.get_session(sid)
        if base_from_repo is None:
            new_row = _fresh_empty_session_row(sid, updated_at)
        else:
            had_existing_row = True
            new_row = copy.deepcopy(base_from_repo)
    elif reuse_session_row is None:
        new_row = _fresh_empty_session_row(sid, updated_at)
    else:
        had_existing_row = True
        new_row = copy.deepcopy(reuse_session_row)

    pre_semantic = {k: v for k, v in new_row.items() if k != "updated_at"}

    new_row["session_id"] = sid
    new_row["updated_at"] = updated_at
    if clear_active_case:
        new_row.pop("active_case_id", None)
    elif active_case_id is not None:
        ac = str(active_case_id).strip()
        if ac:
            new_row["active_case_id"] = ac
    if last_vehicle_key is not None:
        lv = str(last_vehicle_key).strip()
        if lv:
            new_row["last_vehicle_key"] = lv
        else:
            new_row.pop("last_vehicle_key", None)
    if hint:
        prev = _normalize_user_identity_hint(new_row.get("user_identity_hint")) or {}
        new_row["user_identity_hint"] = {**prev, **hint}

    post_semantic = {k: v for k, v in new_row.items() if k != "updated_at"}
    if had_existing_row and post_semantic == pre_semantic:
        if reuse_session_row is not _PATCH_SESSION_ROW_UNSPECIFIED and isinstance(reuse_session_row, dict):
            return reuse_session_row
        if base_from_repo is not None:
            return base_from_repo
        return new_row

    if not repo.upsert_session(sid, new_row, copy_payload=False):
        return None
    return new_row


def save_session_binding_after_case_created(
    session_id: str,
    case_id: str,
    vehicle_key: str | None = None,
    *,
    reuse_session_row: dict[str, Any] | None = None,
    asserted_org_id: str | None = None,
) -> None:
    """After persist_case: retain active_case_id + optional vehicle key; trim bulky turns.

    reuse_session_row: when the route already holds the repo-shaped session document for this
    request (post-binding patches), pass it to skip an extra get_session read.

    asserted_org_id: office hint to preserve on the trimmed row (case create org or prior session).
    """
    sid = (session_id or "").strip()
    cid = (case_id or "").strip()
    if not sid or not cid:
        return
    existing = reuse_session_row if reuse_session_row is not None else (repo.get_session(sid) or {})
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
    oid = (asserted_org_id or "").strip()[:256]
    if oid:
        row["asserted_org_id"] = oid
    else:
        prev_o = str(existing.get("asserted_org_id") or "").strip()[:256]
        if prev_o:
            row["asserted_org_id"] = prev_o
    ex_sem = {k: v for k, v in existing.items() if k != "updated_at"}
    row_sem = {k: v for k, v in row.items() if k != "updated_at"}
    if ex_sem == row_sem:
        return
    if not repo.upsert_session(sid, row, copy_payload=False):
        return
