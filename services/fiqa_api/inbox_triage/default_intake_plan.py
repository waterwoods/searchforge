"""P26G — Default customer intake plan (server SSOT).

Claim type / intake policy → default task identities.
Constitution merges this plan with broker follow-ups.
Clients must not invent a parallel checklist.

task_source values:
- system_default — normal intake; never requires a broker request row
- broker_requested — exceptional follow-up from Request More / Send Request
"""

from __future__ import annotations

from typing import Any, Mapping

TASK_SOURCE_SYSTEM_DEFAULT = "system_default"
TASK_SOURCE_BROKER_REQUESTED = "broker_requested"

# Stable semantic identities (not display text).
TASK_ID_ACCIDENT_STORY = "accident_story"
TASK_ID_ACCIDENT_PHOTOS = "accident_photos"
TASK_ID_INSURANCE_CARD = "insurance_card"
TASK_ID_VEHICLE_INFORMATION = "vehicle_information"
TASK_ID_VEHICLE_VIN = "vehicle_vin"
TASK_ID_ACCIDENT_DATE = "accident_date"
TASK_ID_ACCIDENT_LOCATION = "accident_location"
TASK_ID_INJURY_STATUS = "injury_status"

# Visibility / requirement classes for the default plan.
REQUIREMENT_AVAILABLE = "available"  # customer may complete now
REQUIREMENT_BEFORE_REVIEW = "before_broker_review"
REQUIREMENT_OPTIONAL = "optional"
REQUIREMENT_CONDITIONAL = "conditional"

# Auto-claim default plan order (Today picks first incomplete actionable).
# Start Claim already collects story/date/location/injury as Must Have facts;
# those remain available as editable tasks when still empty.
DEFAULT_AUTO_CLAIM_INTAKE_PLAN: tuple[dict[str, str], ...] = (
    {
        "task_id": TASK_ID_ACCIDENT_STORY,
        "title": "事故经过",
        "requirement": REQUIREMENT_BEFORE_REVIEW,
        "route": "story",
        "canonical_fact": "accident_description",
    },
    {
        "task_id": TASK_ID_ACCIDENT_PHOTOS,
        "title": "事故照片",
        "requirement": REQUIREMENT_OPTIONAL,
        "route": "photos",
        "canonical_evidence": "accident_photo_slots",
    },
    {
        "task_id": TASK_ID_INSURANCE_CARD,
        "title": "保险卡",
        "requirement": REQUIREMENT_AVAILABLE,
        "route": "request_item",
        "canonical_evidence": "policy_or_insurance_card",
    },
)


def default_intake_plan_for_case(case: Mapping[str, Any] | None) -> tuple[dict[str, str], ...]:
    """Return the default intake plan for this case type.

    Currently one auto-claim policy. Future claim types can branch here without
    duplicating plan definitions into Mini Program pages.
    """
    _ = case  # reserved for claim-type / policy branching
    return DEFAULT_AUTO_CLAIM_INTAKE_PLAN


def default_task_ids() -> frozenset[str]:
    return frozenset(row["task_id"] for row in DEFAULT_AUTO_CLAIM_INTAKE_PLAN)
