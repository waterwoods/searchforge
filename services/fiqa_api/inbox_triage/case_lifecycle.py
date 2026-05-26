"""
Derived primary progress axis for API responses (additive; non-authoritative over gates).

Authoritative emission: ``routes/inbox_triage._attach_case_lifecycle`` runs after triage
and may overlay ``formal_submitted_at`` from the persisted case; always prefer the API
``case_lifecycle`` field on the client when present.

Legacy client fallback (must stay in lockstep with ``_derive_case_lifecycle``):
``ui/src/components/intake/caseLifecycleDisplay.ts`` — same predicate order; use strict
``handoff_ready is True`` and ``triage_mode == greenfield`` for ready_for_handoff.

See docs/CASE_CONTRACT_V1.md — does not replace quote_ready_status, handoff_ready, or lifecycle_status.
"""

from __future__ import annotations

from typing import Any


def _derive_case_lifecycle(result: dict[str, Any]) -> str:
    """
    Strict-order derivation from existing triage/case fields only.

    Order:
    1. formal_submitted_at present -> submitted
    2. triage_mode greenfield AND handoff_ready is True -> ready_for_handoff
    3. quote_ready_status almost_ready -> almost_ready
    4. default -> collecting
    """
    if str(result.get("formal_submitted_at") or "").strip():
        return "submitted"
    if str(result.get("triage_mode") or "").strip().lower() == "greenfield" and result.get("handoff_ready") is True:
        return "ready_for_handoff"
    if str(result.get("quote_ready_status") or "").strip().lower() == "almost_ready":
        return "almost_ready"
    return "collecting"
