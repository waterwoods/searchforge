"""Mock AMS/directory adapter for C01 — simulates office customer directory.

Owns mock fixture resolution only. Swappable later with a real AMS adapter
that returns the same LookupResult shape.
"""

from __future__ import annotations

from services.fiqa_api.inbox_triage.customer_lookup.contract import (
    LookupResult,
    empty_lookup_result,
)
from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import (
    MOCK_KEY_S5_NO_MAPPING,
    MOCK_KEY_S6_UNAVAILABLE,
    get_fixture,
)


class MockCustomerDirectoryAdapter:
    """In-memory mock directory. READ ONLY — never mutates CRM."""

    adapter_id = "mock_directory"

    def lookup_by_person_link(self, person_link_key: str) -> LookupResult:
        key = str(person_link_key or "").strip()

        # Reserved QA keys — adapter-owned simulate paths.
        if key == MOCK_KEY_S6_UNAVAILABLE:
            result = empty_lookup_result(
                match_status="LOOKUP_UNAVAILABLE",
                lookup_confidence="LOW",
                next_action="start_blank_claim",
                reason_codes=["mock_lookup_unavailable"],
            )
            result["lookup_source"] = "unavailable"
            return result

        if key == MOCK_KEY_S5_NO_MAPPING:
            return empty_lookup_result(
                match_status="NOT_FOUND",
                lookup_confidence="LOW",
                next_action="start_blank_claim",
                reason_codes=["identity_without_customer_mapping"],
            )

        fixture = get_fixture(key)
        if fixture is None:
            return empty_lookup_result(
                match_status="NOT_FOUND",
                lookup_confidence="LOW",
                next_action="start_blank_claim",
                reason_codes=["no_mock_directory_row"],
            )
        return fixture


def get_default_directory_adapter() -> MockCustomerDirectoryAdapter:
    """Factory used by the Capability facade. Future: AMS when flag/config says so."""
    return MockCustomerDirectoryAdapter()
