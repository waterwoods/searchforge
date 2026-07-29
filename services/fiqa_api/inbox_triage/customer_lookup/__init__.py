"""P4 Capability 01 — Customer Lookup (mock harness).

READ ONLY. Answers only: "Who is this customer?"

Does not create/merge/update customers, policies, vehicles, or CRM.
Identity remains person_link_key (P29B). Future AMS adapters swap behind the facade.
"""

from __future__ import annotations

from services.fiqa_api.inbox_triage.customer_lookup.contract import (
    LOOKUP_CONFIDENCE_VALUES,
    MATCH_STATUS_VALUES,
    NEXT_ACTION_VALUES,
    LookupConfidence,
    LookupResult,
    MatchStatus,
    NextAction,
    empty_lookup_result,
)
from services.fiqa_api.inbox_triage.customer_lookup.facade import (
    FLAG_ENV,
    FORCE_UNAVAILABLE_ENV,
    customer_lookup_mock_enabled,
    lookup_customer,
    lookup_customer_for_session,
    lookup_demo_invite_fixture,
    reset_customer_lookup_mock_for_tests,
)

__all__ = [
    "FLAG_ENV",
    "FORCE_UNAVAILABLE_ENV",
    "LOOKUP_CONFIDENCE_VALUES",
    "MATCH_STATUS_VALUES",
    "NEXT_ACTION_VALUES",
    "LookupConfidence",
    "LookupResult",
    "MatchStatus",
    "NextAction",
    "customer_lookup_mock_enabled",
    "empty_lookup_result",
    "lookup_customer",
    "lookup_customer_for_session",
    "lookup_demo_invite_fixture",
    "reset_customer_lookup_mock_for_tests",
]
