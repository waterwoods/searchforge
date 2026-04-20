"""
V6: Never block submission on weak OCR; surface low-confidence as soft flags only.
"""

from __future__ import annotations

from typing import Any


def apply_error_tolerance(
    case_draft: dict[str, Any],
    *,
    quote_ready_status: str,
) -> dict[str, Any]:
    """
    Mutates a shallow copy of case_draft with v6_error_tolerance block.
    Policy: missing critical fields do not block handoff (broker backfill); low confidence → highlight list.
    """
    cd = dict(case_draft or {})
    inferred = cd.get("inferred_fields")
    if not isinstance(inferred, dict):
        inferred = {}

    low_conf: list[str] = []
    for k, v in inferred.items():
        if not isinstance(v, dict):
            continue
        c = float(v.get("confidence") or 0.0)
        if v.get("v6_highlight") and c < 0.55:
            low_conf.append(str(k))
        elif c < 0.42:
            low_conf.append(str(k))

    cd["v6_error_tolerance"] = {
        "low_confidence_field_keys": low_conf[:24],
        "submission_blocked": False,
        "quote_ready_status": quote_ready_status,
        "policy_note": "OCR/low-confidence items are advisory; office verifies before bind.",
    }
    return cd
