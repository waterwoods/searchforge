"""Capability C03 — Smart Claim Start (Customer Trust presentation).

Input: Cap 01 LookupResult + Cap 02 PrefillResult.
Output: SmartClaimStartPlan (customer-ready Start Claim experience plan).

Does not write CRM, cases, or identity. Does not redesign C01/C02.
Does not implement AMS / Notification / Timeline.
Mini Program wires the plan via service + HTTP (flag OFF by default).
"""

from services.fiqa_api.inbox_triage.smart_claim_start.contract import (
    MUST_HAVE_ACCIDENT_KEYS,
    NEVER_PRIMARY_ASK_KEYS,
    OPTIONAL_ACCIDENT_KEYS,
    SmartClaimStartPlan,
    assert_smart_claim_start_plan_complete,
)
from services.fiqa_api.inbox_triage.smart_claim_start.engine import (
    build_smart_claim_start_plan,
)
from services.fiqa_api.inbox_triage.smart_claim_start.service import (
    build_smart_claim_start_response,
    resolve_mock_scenario_person_link,
)

__all__ = [
    "MUST_HAVE_ACCIDENT_KEYS",
    "NEVER_PRIMARY_ASK_KEYS",
    "OPTIONAL_ACCIDENT_KEYS",
    "SmartClaimStartPlan",
    "assert_smart_claim_start_plan_complete",
    "build_smart_claim_start_plan",
    "build_smart_claim_start_response",
    "resolve_mock_scenario_person_link",
]
