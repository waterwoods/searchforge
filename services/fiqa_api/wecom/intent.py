"""Rule-based WeCom slice intent — no LLM, no case creation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

WeComIntent = Literal[
    "add_car",
    "claim_intake",
    "policy_review",
    "menu_selection",
    "unclear",
]

CanonicalIntent = Literal["add_vehicle", "claim", "policy_review", "unclear"]

Confidence = Literal["high", "low"]

_CANONICAL_INTENT: dict[WeComIntent, CanonicalIntent] = {
    "add_car": "add_vehicle",
    "claim_intake": "claim",
    "policy_review": "policy_review",
    "menu_selection": "unclear",
    "unclear": "unclear",
}


def canonical_intent(intent: WeComIntent) -> CanonicalIntent:
    """Map internal slice intent to P16 channel contract names."""
    return _CANONICAL_INTENT.get(intent, "unclear")

_MENU_CLICK_IDS = {
    "add_car": {"add_car", "add_vehicle", "101", "1"},
    "claim_intake": {"claim_intake", "claim", "accident", "102", "2"},
    "policy_review": {"policy_review", "policy", "103", "3"},
    "unclear": {"other", "104", "4"},
}

_CLAIM_MARKERS = (
    "accident",
    "car accident",
    "file a claim",
    "claim",
    "hit and run",
    "rear-end",
    "rear ended",
    "collision",
    "报事故",
    "出事故",
    "刚出事故",
    "出险",
    "理赔",
    "撞车",
    "撞了",
    "车祸",
    "对方跑了",
)

_ADD_CAR_MARKERS = (
    "add a car",
    "add car",
    "new car",
    "bought a car",
    "buy a car",
    "加车",
    "加一辆",
    "一辆车",
    "加一台",
    "新车",
    "买了辆",
    "买了一辆",
    "加到保险",
    "加到保单",
)

_POLICY_REVIEW_MARKERS = (
    "policy review",
    "review my policy",
    "review policy",
    "check my policy",
    "保单",
    "检视",
    "看看保险",
    "保险怎么样",
    "保费",
    "coverage review",
)

_MENU_TEXT_MARKERS: list[tuple[WeComIntent, tuple[str, ...]]] = [
    ("add_car", ("add vehicle", "加车", "加一台车", "新车加保")),
    ("claim_intake", ("claim", "accident", "事故", "理赔", "出险")),
    ("policy_review", ("policy review", "保单检视", "保单", "检视")),
]


@dataclass(frozen=True)
class IntentResult:
    intent: WeComIntent
    confidence: Confidence
    matched_by: str


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(m in lowered for m in markers)


def _menu_intent_from_id(menu_id: str) -> WeComIntent | None:
    mid = (menu_id or "").strip().lower()
    for intent, ids in _MENU_CLICK_IDS.items():
        if mid in ids:
            return intent  # type: ignore[return-value]
    return None


def classify_wecom_intent(text: str, *, menu_id: str | None = None) -> IntentResult:
    """
    Classify customer text with simple rules first.
    Case creation must NOT happen on low confidence — caller gates on confidence.
    """
    raw = (text or "").strip()
    lowered = raw.lower()

    if menu_id:
        from_menu = _menu_intent_from_id(menu_id)
        if from_menu and from_menu != "unclear":
            return IntentResult(intent=from_menu, confidence="high", matched_by="menu_id")

    if not raw:
        return IntentResult(intent="unclear", confidence="low", matched_by="empty")

    claim = _contains_any(lowered, _CLAIM_MARKERS)
    add_car = _contains_any(lowered, _ADD_CAR_MARKERS)
    policy = _contains_any(lowered, _POLICY_REVIEW_MARKERS)
    hits = sum([claim, add_car, policy])
    if hits > 1:
        return IntentResult(intent="unclear", confidence="low", matched_by="multi_intent")

    # Explicit menu replies (number or short label)
    if re.fullmatch(r"[1-4]", lowered):
        mapping = {"1": "add_car", "2": "claim_intake", "3": "policy_review", "4": "unclear"}
        picked = mapping[lowered]
        if picked == "unclear":
            return IntentResult(intent="unclear", confidence="high", matched_by="menu_number_other")
        return IntentResult(intent=picked, confidence="high", matched_by="menu_number")  # type: ignore[arg-type]

    for intent, markers in _MENU_TEXT_MARKERS:
        if any(m in lowered for m in markers) and len(lowered) <= 24:
            return IntentResult(intent=intent, confidence="high", matched_by="menu_text")

    if claim:
        return IntentResult(intent="claim_intake", confidence="high", matched_by="claim_markers")
    if add_car:
        return IntentResult(intent="add_car", confidence="high", matched_by="add_car_markers")
    if policy:
        return IntentResult(intent="policy_review", confidence="high", matched_by="policy_review_markers")

    return IntentResult(intent="unclear", confidence="low", matched_by="no_match")
