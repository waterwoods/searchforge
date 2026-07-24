"""P4 Capability 02 — Claim Prefill (mock classification).

Answers only: which fields AUTO_PREFILL vs still collect.
Input: Cap 01 LookupResult. Output: PrefillResult.
No CRM. No identity redesign. No case writes.
"""

from __future__ import annotations

from services.fiqa_api.inbox_triage.claim_prefill.contract import (
    FIELD_CLASS_VALUES,
    FIELD_LABELS,
    START_CLAIM_FIELD_KEYS,
    FieldClass,
    FieldPrefill,
    PrefillResult,
    assert_prefill_result_complete,
    founder_shorthand_for,
)
from services.fiqa_api.inbox_triage.claim_prefill.engine import (
    build_prefill_result,
    classification_map,
    founder_shorthand_map,
)

__all__ = [
    "FIELD_CLASS_VALUES",
    "FIELD_LABELS",
    "START_CLAIM_FIELD_KEYS",
    "FieldClass",
    "FieldPrefill",
    "PrefillResult",
    "assert_prefill_result_complete",
    "build_prefill_result",
    "classification_map",
    "founder_shorthand_for",
    "founder_shorthand_map",
]
