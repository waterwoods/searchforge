"""
Lightweight case binding for Unified Intake continuity (no login, no schema changes).

Decides which persisted case to attach to when the client does not send case_id.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _norm_vehicle_key(key: str | None) -> str | None:
    s = (key or "").strip()
    return s if s else None


def _case_id_from_row(case: dict[str, Any]) -> str | None:
    cid = str(case.get("case_id") or "").strip()
    return cid if cid else None


def is_case_open_for_binding(case: dict[str, Any]) -> bool:
    """Open = not archived and broker status is not terminal."""
    if bool(case.get("workbench_archived")):
        return False
    st = str(case.get("case_status") or "new").strip().lower()
    return st != "closed"


def _open_cases(recent_cases: list[dict]) -> list[dict[str, Any]]:
    return [c for c in recent_cases if isinstance(c, dict) and is_case_open_for_binding(c)]


def _vehicle_keys_equal(a: str | None, b: str | None) -> bool:
    na, nb = _norm_vehicle_key(str(a) if a is not None else None), _norm_vehicle_key(
        str(b) if b is not None else None
    )
    if not na or not nb:
        return False
    if na == nb:
        return True
    return na.lower() == nb.lower()


def resolve_active_case(
    session: dict | None,
    recent_cases: list[dict],
    incoming_vehicle_key: str | None,
) -> str | None:
    """
    Binding priority:
    1. session["active_case_id"] when set
    2. incoming_vehicle_key matches exactly one open recent case
    3. exactly one open recent case (no other signals)
    4. else None
    """
    sess = session if isinstance(session, dict) else None
    if sess:
        sid = str(sess.get("active_case_id") or "").strip()
        if sid:
            logger.info(
                "case_binding_decision reason=session_active case_id=%s incoming_vehicle_key=%s",
                sid,
                incoming_vehicle_key or "",
            )
            return sid

    open_rows = _open_cases(recent_cases)
    ivk = _norm_vehicle_key(incoming_vehicle_key)

    if ivk:
        matches = [c for c in open_rows if _vehicle_keys_equal(ivk, c.get("vehicle_key"))]
        if len(matches) == 1:
            cid = _case_id_from_row(matches[0])
            if cid:
                logger.info(
                    "case_binding_decision reason=vehicle_match case_id=%s vehicle_key=%s",
                    cid,
                    ivk,
                )
                return cid
        if len(matches) > 1:
            logger.info(
                "case_binding_decision reason=none ambiguous_vehicle_matches count=%s",
                len(matches),
            )
            return None

    if len(open_rows) == 1:
        cid = _case_id_from_row(open_rows[0])
        if cid:
            logger.info("case_binding_decision reason=single_open_case case_id=%s", cid)
            return cid

    logger.info(
        "case_binding_decision reason=none open_count=%s incoming_vehicle_key=%s",
        len(open_rows),
        ivk or "",
    )
    return None
