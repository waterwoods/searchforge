"""C01 — Customer Lookup Capability (P5 reference implementation).

READ ONLY. Answers only: "Who is this customer?"

Layering:
  Workflow  →  Capability (this package)  →  Adapter  →  LookupResult

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
    reset_customer_lookup_mock_for_tests,
    set_directory_adapter_for_tests,
)
from services.fiqa_api.inbox_triage.customer_lookup.qa_scenarios import (
    list_qa_scenario_keys,
    person_link_for_mock_scenario,
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
    "list_qa_scenario_keys",
    "lookup_customer",
    "lookup_customer_for_session",
    "person_link_for_mock_scenario",
    "reset_customer_lookup_mock_for_tests",
    "set_directory_adapter_for_tests",
]
