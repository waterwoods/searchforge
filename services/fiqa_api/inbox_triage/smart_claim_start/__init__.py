"""P4 Capability 03 — Smart Claim Start (design + mock planner).

Input: Cap 01 LookupResult + Cap 02 PrefillResult.
Output: SmartClaimStartPlan (customer-ready Start Claim experience plan).

Does not write CRM, cases, or identity.
P4 Integration 01 wires the plan into Mini Program via service + HTTP.
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
