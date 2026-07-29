"""Mock Prefill classifier adapter for C02.

Owns classification rules via the pure engine. Swappable later when richer
LookupResult fields promote UNKNOWN → AUTO without Workflow rewrite.
Never writes CRM / cases.
"""

from __future__ import annotations

from services.fiqa_api.inbox_triage.claim_prefill.contract import PrefillResult
from services.fiqa_api.inbox_triage.claim_prefill.engine import build_prefill_result
from services.fiqa_api.inbox_triage.customer_lookup.contract import LookupResult


class MockPrefillClassifierAdapter:
    """Rule-based mock classifier. Suggestion only — claim case remains SoR."""

    adapter_id = "mock_prefill_classifier"

    def classify(self, lookup: LookupResult) -> PrefillResult:
        return build_prefill_result(lookup)


def get_default_classifier_adapter() -> MockPrefillClassifierAdapter:
    return MockPrefillClassifierAdapter()
