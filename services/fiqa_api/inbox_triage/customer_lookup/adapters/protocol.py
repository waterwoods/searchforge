"""Adapter protocol for C01 Customer Lookup.

Adapters own vendor / directory protocols.
Workflow and Capability consumers depend only on LookupResult — never on AMS SDKs.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from services.fiqa_api.inbox_triage.customer_lookup.contract import LookupResult


@runtime_checkable
class CustomerDirectoryAdapter(Protocol):
    """Read-only directory lookup. Never writes CRM / Customer / Policy / Vehicle."""

    adapter_id: str

    def lookup_by_person_link(self, person_link_key: str) -> LookupResult:
        """
        Map opaque person_link_key → complete LookupResult.

        Must not raise for not-found / unavailable match outcomes.
        Must never include OpenID in the result payload.
        """
        ...
