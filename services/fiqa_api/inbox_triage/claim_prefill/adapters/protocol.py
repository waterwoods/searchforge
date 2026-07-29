"""Adapter protocol for C02 Claim Prefill.

Adapters own classification policy / enrichment rules.
Workflow depends only on PrefillResult — never on engine internals or CRM.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from services.fiqa_api.inbox_triage.claim_prefill.contract import PrefillResult
from services.fiqa_api.inbox_triage.customer_lookup.contract import LookupResult


@runtime_checkable
class PrefillClassifierAdapter(Protocol):
    """Classify Start Claim fields from LookupResult. Never writes CRM / cases."""

    adapter_id: str

    def classify(self, lookup: LookupResult) -> PrefillResult:
        """
        LookupResult → complete PrefillResult.

        Must not invent UNKNOWN values. Must not raise for weak/ambiguous lookup.
        """
        ...
