"""C02 — Claim Prefill Capability (P5 Sprint 2 reference).

Answers only: "What do we already know vs still need?"

Layering:
  Workflow  →  Capability (this package)  →  Adapter  →  PrefillResult

Suggestion only. No CRM write-back. No Start Claim screens (C03).
Input: Cap 01 LookupResult. Output: complete PrefillResult.
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
    empty_prefill_result,
    founder_shorthand_for,
)
from services.fiqa_api.inbox_triage.claim_prefill.engine import (
    classification_map,
    founder_shorthand_map,
)
from services.fiqa_api.inbox_triage.claim_prefill.facade import (
    build_prefill_result,
    customer_visible_effects,
    prefill_from_lookup,
    reset_claim_prefill_for_tests,
    set_classifier_adapter_for_tests,
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
    "customer_visible_effects",
    "empty_prefill_result",
    "founder_shorthand_for",
    "founder_shorthand_map",
    "prefill_from_lookup",
    "reset_claim_prefill_for_tests",
    "set_classifier_adapter_for_tests",
]
