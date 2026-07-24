"""SmartClaimStartPlan contract for P4 Capability 03 — Smart Claim Start.

Consumes Cap 01 LookupResult + Cap 02 PrefillResult only.
Never CRM, never identity redesign, never DB redesign.

One responsibility: turn known context into a customer-ready Start Claim plan
so the customer primarily answers "What happened today?"
"""

from __future__ import annotations

from typing import Any, Final, Literal, TypedDict

StartMode = Literal[
    "CONTINUE_ACTIVE",
    "MATCHED_KNOWN",
    "MATCHED_CONFIRM_VEHICLE",
    "MATCHED_CONFIRM_POLICY",
    "BLANK_DEGRADE",
    "CONTACT_BROKER",
]

QuestionVisibility = Literal[
    "VISIBLE_REQUIRED",
    "VISIBLE_CONFIRM",
    "COLLAPSED_OPTIONAL",
    "HIDDEN",
    "BROKER_OWNED",
]

ChipEditability = Literal[
    "READ_ONLY",
    "EDIT_ON_REQUEST",
    "CONFIRM_REQUIRED",
]

START_MODE_VALUES: Final[frozenset[str]] = frozenset(
    {
        "CONTINUE_ACTIVE",
        "MATCHED_KNOWN",
        "MATCHED_CONFIRM_VEHICLE",
        "MATCHED_CONFIRM_POLICY",
        "BLANK_DEGRADE",
        "CONTACT_BROKER",
    }
)

# Business Contract Must Haves — always the core accident ask when starting new.
MUST_HAVE_ACCIDENT_KEYS: Final[tuple[str, ...]] = (
    "accident_story",
    "accident_time",
    "accident_location",
    "injury",
)

# Cap 02 marks damage as customer; Cap 03 keeps it optional/collapsed (not enablement).
OPTIONAL_ACCIDENT_KEYS: Final[tuple[str, ...]] = ("damage",)

# Never block Start Claim; never show as primary ask.
NEVER_PRIMARY_ASK_KEYS: Final[tuple[str, ...]] = (
    "vin",
    "license_plate",
    "email",
    "police_report",
    "photos",
    "documents",
    "policy_number",
    "insurance_company",
)


class KnownChip(TypedDict, total=False):
    field_key: str
    label_zh: str
    value: str
    editability: ChipEditability
    """Customer-facing only — never technical IDs."""


class ConfirmStep(TypedDict, total=False):
    step_id: str
    prompt_zh: str
    options: list[str]
    required_before_accident: bool
    reason_code: str


class QuestionDecision(TypedDict, total=False):
    field_key: str
    visibility: QuestionVisibility
    label_zh: str
    reason_code: str
    blocks_submit: bool


class ScreenStep(TypedDict, total=False):
    screen_id: str
    title_zh: str
    purpose: str
    primary_cta_zh: str


class SmartClaimStartPlan(TypedDict, total=False):
    mode: StartMode
    headline_zh: str
    subtitle_zh: str
    confidence_signal: str  # customer-safe: "我们已为您准备好信息" | degrade copy
    known_chips: list[KnownChip]
    confirm_steps: list[ConfirmStep]
    questions: list[QuestionDecision]
    screens: list[ScreenStep]
    primary_cta_zh: str
    secondary_cta_zh: str | None
    """Estimated deliberate customer inputs for this path (Founder success metric)."""
    estimated_customer_inputs: int
    """Fields never re-asked on this path."""
    never_ask_again: list[str]
    """Customer may expand edit for these AUTO chips without retyping blank forms."""
    edit_on_request_fields: list[str]
    photos_placement: Literal[
        "AFTER_SUBMIT_OPTIONAL",
        "INLINE_OPTIONAL",
        "HIDDEN_UNTIL_REQUEST_MORE",
    ]
    failure_profile: str
    lookup_match_status: str
    lookup_confidence: str
    lookup_next_action: str
    prefill_source: str
    reason_codes: list[str]
    """No CRM / adapter dependency marker for Founder review."""
    adapter_boundary: str


def assert_smart_claim_start_plan_complete(result: dict[str, Any]) -> None:
    required = (
        "mode",
        "headline_zh",
        "subtitle_zh",
        "confidence_signal",
        "known_chips",
        "confirm_steps",
        "questions",
        "screens",
        "primary_cta_zh",
        "estimated_customer_inputs",
        "never_ask_again",
        "edit_on_request_fields",
        "photos_placement",
        "failure_profile",
        "lookup_match_status",
        "lookup_confidence",
        "lookup_next_action",
        "prefill_source",
        "reason_codes",
        "adapter_boundary",
    )
    for key in required:
        if key not in result:
            raise AssertionError(f"SmartClaimStartPlan missing key: {key}")
    if result["mode"] not in START_MODE_VALUES:
        raise AssertionError(f"invalid mode: {result['mode']}")
    if not isinstance(result["questions"], list) or not result["questions"]:
        raise AssertionError("questions must be a non-empty list")
    if not isinstance(result["screens"], list) or not result["screens"]:
        raise AssertionError("screens must be a non-empty list")
    if int(result["estimated_customer_inputs"]) < 0:
        raise AssertionError("estimated_customer_inputs must be >= 0")
