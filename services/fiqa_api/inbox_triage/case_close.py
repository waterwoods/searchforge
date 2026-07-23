"""P0 Lifecycle — Broker Close → History (read-only).

Canonical Close is distinct from Workbench soft-archive (queue filter only).

Canonical fields stamped on close (persisted on the case row / extra JSONB):
  - case_status = "closed"          (terminal status; no further status exits)
  - admin_lifecycle = "closed"      (Cap2 lifecycle axis)
  - case_history_state = "history"  (explicit History marker)
  - closed_at                       (ISO-8601 UTC)
  - closed_by                       (broker/office actor string)
  - close_reason                    (optional short reason)

Soft archive (workbench_archived) is NOT Close and must not release Active Case.
"""

from __future__ import annotations

import logging
from typing import Any

from services.fiqa_api.inbox_triage.case_store import (
    _load_case_for_mutation,
    _persist_case_after_update,
    _require_case_storage_path,
    _utc_now_iso,
    _build_activity_entry,
    MAX_CASE_ACTIVITY,
)

logger = logging.getLogger(__name__)

ERROR_CASE_CLOSED_READ_ONLY = "case_closed_read_only"
ERROR_CASE_NOT_FOUND = "case_not_found"
ERROR_ALREADY_CLOSED = "already_closed"

CASE_HISTORY_STATE = "history"
ADMIN_LIFECYCLE_CLOSED = "closed"
CASE_STATUS_CLOSED = "closed"


def case_is_closed_history(case: dict[str, Any] | None) -> bool:
    """True when the case is immutable History (Broker Close)."""
    if not isinstance(case, dict):
        return False
    if str(case.get("case_history_state") or "").strip().lower() == CASE_HISTORY_STATE:
        return True
    if str(case.get("closed_at") or "").strip():
        return True
    if str(case.get("case_status") or "").strip().lower() == CASE_STATUS_CLOSED:
        return True
    lifecycle = str(case.get("admin_lifecycle") or "").strip().lower()
    if lifecycle in (ADMIN_LIFECYCLE_CLOSED, "history"):
        return True
    return False


def case_is_customer_writable(case: dict[str, Any] | None) -> bool:
    """Customer may mutate only when the case is not closed History."""
    if not isinstance(case, dict):
        return False
    return not case_is_closed_history(case)


def assert_customer_case_writable(case: dict[str, Any] | None) -> None:
    """Raise ValueError(case_closed_read_only) when History."""
    if case is None:
        raise ValueError(ERROR_CASE_NOT_FOUND)
    if not case_is_customer_writable(case):
        raise ValueError(ERROR_CASE_CLOSED_READ_ONLY)


def _clear_intake_session_active_pointers(case_id: str) -> int:
    """Best-effort: clear intake_sessions.active_case_id pointing at this case."""
    cid = (case_id or "").strip()
    if not cid:
        return 0
    cleared = 0
    try:
        from services.fiqa_api.db.service_record_settings import service_record_database_url
        from services.fiqa_api.inbox_triage.session_repository import intake_session_connection

        if not service_record_database_url():
            return 0
        with intake_session_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE intake_sessions
                    SET payload = payload - 'active_case_id',
                        updated_at = NOW()
                    WHERE payload->>'active_case_id' = %s
                    """,
                    (cid,),
                )
                cleared = int(cur.rowcount or 0)
            conn.commit()
    except Exception as exc:
        logger.warning(
            "close_case session pointer cleanup failed case_id=%s err=%s",
            cid,
            type(exc).__name__,
        )
    return cleared


def _stamp_intake_aggregate_closed(case_id: str) -> None:
    """Keep Cap2 claim_intake_aggregates.admin_lifecycle aligned with History Close.

    Case GET overlays intake projection admin_lifecycle onto the workbench case.
    Without this stamp, Close looks closed on case_status/history but still reads
    as admin_lifecycle=active from the Cap2 aggregate.
    """
    cid = (case_id or "").strip()
    if not cid:
        return
    try:
        from services.fiqa_api.db.service_record_settings import service_record_database_url
        from services.fiqa_api.db.service_record_repository import service_record_connection

        if service_record_database_url():
            with service_record_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE claim_intake_aggregates
                        SET admin_lifecycle = %s,
                            updated_at = NOW()
                        WHERE case_id = %s
                        """,
                        (ADMIN_LIFECYCLE_CLOSED, cid),
                    )
                conn.commit()
    except Exception as exc:
        logger.warning(
            "close_case intake aggregate stamp failed case_id=%s err=%s",
            cid,
            type(exc).__name__,
        )
    # In-memory Cap2 path (unit tests / local fixture without DB URL).
    try:
        from services.fiqa_api.inbox_triage.p20_case_intake_command_service import (
            default_case_intake_service,
        )

        svc = default_case_intake_service()
        store = getattr(svc, "store", None)
        aggregates = getattr(store, "aggregates", None)
        if isinstance(aggregates, dict) and cid in aggregates:
            agg = aggregates[cid]
            if hasattr(agg, "admin_lifecycle"):
                agg.admin_lifecycle = ADMIN_LIFECYCLE_CLOSED
    except Exception:
        pass


def close_case(
    case_id: str,
    *,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """
    Broker-only Close: Active → History (read-only).

    Idempotent: if already History, returns outcome=already_closed with the case.
    Clears mp_customer_active_case bindings and intake session active pointers.
    Does not delete evidence/timeline.
    """
    cid = (case_id or "").strip()
    if not cid:
        return {"ok": False, "outcome": ERROR_CASE_NOT_FOUND, "case": None, "error_code": ERROR_CASE_NOT_FOUND}

    _require_case_storage_path()
    normalized = _load_case_for_mutation(cid)
    if normalized is None:
        return {"ok": False, "outcome": ERROR_CASE_NOT_FOUND, "case": None, "error_code": ERROR_CASE_NOT_FOUND}

    actor_id = (actor or "").strip()[:128] or "broker:unknown"
    reason_text = (reason or "").strip()[:500] or None

    if case_is_closed_history(normalized):
        # Ensure bindings are cleared even if a prior close was partial.
        try:
            from services.fiqa_api.inbox_triage.mp_customer_identity import (
                clear_active_case_bindings_for_case,
            )

            clear_active_case_bindings_for_case(cid)
        except Exception:
            logger.warning("close_case already_closed binding cleanup failed case_id=%s", cid)
        _clear_intake_session_active_pointers(cid)
        _stamp_intake_aggregate_closed(cid)
        # Re-assert closed axes on the durable case row when a prior close drifted.
        if str(normalized.get("admin_lifecycle") or "").strip().lower() != ADMIN_LIFECYCLE_CLOSED:
            normalized["admin_lifecycle"] = ADMIN_LIFECYCLE_CLOSED
            normalized["case_status"] = CASE_STATUS_CLOSED
            normalized["case_history_state"] = CASE_HISTORY_STATE
            _persist_case_after_update(cid, normalized)
        return {
            "ok": True,
            "outcome": ERROR_ALREADY_CLOSED,
            "case": normalized,
            "case_id": cid,
            "bindings_cleared": True,
        }

    now = _utc_now_iso()
    normalized["case_status"] = CASE_STATUS_CLOSED
    normalized["admin_lifecycle"] = ADMIN_LIFECYCLE_CLOSED
    normalized["case_history_state"] = CASE_HISTORY_STATE
    normalized["closed_at"] = now
    normalized["closed_by"] = actor_id
    if reason_text:
        normalized["close_reason"] = reason_text
    normalized["updated_at"] = now
    activity_msg = "Broker closed case — moved to read-only History."
    if reason_text:
        activity_msg = f"{activity_msg} Reason: {reason_text}"
    normalized["case_activity"] = [
        _build_activity_entry("case_closed", activity_msg),
        *list(normalized.get("case_activity") or []),
    ][:MAX_CASE_ACTIVITY]

    if not _persist_case_after_update(cid, normalized):
        return {
            "ok": False,
            "outcome": "persist_failed",
            "case": None,
            "error_code": "persist_failed",
        }

    _stamp_intake_aggregate_closed(cid)

    bindings_removed = 0
    try:
        from services.fiqa_api.inbox_triage.mp_customer_identity import (
            clear_active_case_bindings_for_case,
        )

        bindings_removed = int(clear_active_case_bindings_for_case(cid) or 0)
    except Exception:
        logger.warning("close_case binding cleanup failed case_id=%s", cid)

    sessions_cleared = _clear_intake_session_active_pointers(cid)

    return {
        "ok": True,
        "outcome": "closed",
        "case": normalized,
        "case_id": cid,
        "closed_at": now,
        "closed_by": actor_id,
        "bindings_cleared": bindings_removed,
        "sessions_cleared": sessions_cleared,
    }
