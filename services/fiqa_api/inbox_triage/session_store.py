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


def save_in_progress_session(
    session_id: str,
    turns: list[dict[str, Any]],
    triage_result: dict[str, Any],
) -> None:
    """
    Save or update an in-progress session with turns and workflow_state.
    Call when triage returns and no case was persisted.
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
    # Update existing or append
    found = False
    for i, s in enumerate(sessions):
        if (s.get("session_id") or "").strip() == sid:
            sessions[i] = {
                "session_id": sid,
                "turns": normalized_turns,
                "workflow_state": workflow_state,
                "updated_at": updated_at,
            }
            found = True
            break
    if not found:
        sessions.append({
            "session_id": sid,
            "turns": normalized_turns,
            "workflow_state": workflow_state,
            "updated_at": updated_at,
        })
    # Evict oldest if over limit
    sessions.sort(key=lambda s: s.get("updated_at") or "", reverse=True)
    payload["sessions"] = sessions[:MAX_STORED_SESSIONS]
    _write_payload(payload)


def get_in_progress_session(session_id: str) -> dict[str, Any] | None:
    """
    Return in-progress session by session_id, or None if not found.
    Returns { turns, workflow_state } for frontend restore.
    """
    sid = (session_id or "").strip()
    if not sid:
        return None
    payload = _read_payload()
    for s in payload["sessions"]:
        if (s.get("session_id") or "").strip() == sid:
            turns = s.get("turns") or []
            workflow_state = s.get("workflow_state") or {}
            return {
                "turns": turns,
                "workflow_state": workflow_state,
                "updated_at": s.get("updated_at", ""),
            }
    return None


def delete_in_progress_session(session_id: str) -> bool:
    """Remove session (e.g. after case created). Optional; orphaned sessions are harmless."""
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
