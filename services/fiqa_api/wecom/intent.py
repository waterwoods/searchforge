"""Rule-based WeCom slice intent — no LLM, no case creation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

WeComIntent = Literal[
    "add_car",
    "claim_intake",
    "coverage_risk_intake",
    "policy_review",
    "menu_selection",
    "unclear",
    # Track B0 — Start Card button clicks (WECOM_B0_ACTIVE_WORKSPACE only).
    # These are workspace actions, not conversation topics; they never re-enter
    # the add_car text-classification path.
    "start_add_car_click",
    "start_add_car_decline_click",
    "start_add_car_broker_click",
    # P19H-3e-1 — Claim injury quick-reply clicks
    "claim_injury_no_click",
    "claim_injury_yes_click",
    "claim_injury_unknown_click",
]

CanonicalIntent = Literal["add_vehicle", "claim", "coverage_risk", "policy_review", "unclear"]

Confidence = Literal["high", "low"]

_CANONICAL_INTENT: dict[WeComIntent, CanonicalIntent] = {
    "add_car": "add_vehicle",
    "claim_intake": "claim",
    "coverage_risk_intake": "coverage_risk",
    "policy_review": "policy_review",
    "menu_selection": "unclear",
    "unclear": "unclear",
    "start_add_car_click": "add_vehicle",
    "start_add_car_decline_click": "unclear",
    "start_add_car_broker_click": "unclear",
    "claim_injury_no_click": "claim",
    "claim_injury_yes_click": "claim",
    "claim_injury_unknown_click": "claim",
}

# Track B0.1 — Start Card click ids. Kept separate from `_MENU_CLICK_IDS`
# (which boosts confidence for the existing add_car/claim/policy guided menu)
# so a Start Card click can never be reclassified as a fresh add_car intent
# and re-trigger a new Start Card (Rule 8 — one flow, no loops).
START_CARD_CLICK_INTENTS = frozenset(
    {
        "start_add_car_click",
        "start_add_car_decline_click",
        "start_add_car_broker_click",
    }
)

CLAIM_INJURY_CLICK_INTENTS = frozenset(
    {"claim_injury_no_click", "claim_injury_yes_click", "claim_injury_unknown_click"}
)

_START_CARD_CLICK_IDS: dict[str, WeComIntent] = {
    "start_add_car": "start_add_car_click",
    "start_add_car_decline": "start_add_car_decline_click",
    "start_add_car_broker": "start_add_car_broker_click",
}

_CLAIM_INJURY_CLICK_IDS: dict[str, WeComIntent] = {
    "claim_injury_no": "claim_injury_no_click",
    "claim_injury_yes": "claim_injury_yes_click",
    "claim_injury_unknown": "claim_injury_unknown_click",
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

_COVERAGE_RISK_MARKERS = (
    "coverage lapse",
    "coverage lapsed",
    "coverage suspended",
    "policy cancelled",
    "policy canceled",
    "policy inactive",
    "policy suspended",
    "can i still drive",
    "can i drive",
    "am i covered",
    "no insurance",
    "my insurance expired",
    "my insurance was cancelled",
    "my insurance was canceled",
    "my policy is inactive",
    "reinstate my policy",
    "dmv says no insurance",
    "停保",
    "停保了",
    "已经停了",
    "好像停",
    "没保险",
    "保险断了",
    "保险失效",
    "保单被取消",
    "保单取消",
    "coverage lapse",
    "还能开",
    "能不能开",
    "还能不能开",
    "还能不能开车",
    "还能不能上路",
    "车还能不能上路",
    "现在还能不能开车",
    "帮我恢复保险",
    "恢复保险",
    "reinstate",
    "dmv",
    "registration",
)

_CLAIM_MARKERS = (
    "accident",
    "car accident",
    "file a claim",
    "claim",
    "hit and run",
    "rear-end",
    "rear ended",
    "collision",
    "got hit",
    "i had an accident",
    "should i file a claim",
    "neck hurts",
    "报事故",
    "出事故",
    "出车祸",
    "刚出事故",
    "出险",
    "理赔",
    "撞车",
    "撞了",
    "车祸",
    "事故",
    "被撞",
    "追尾",
    "要不要报保险",
    "对方跑了",
    "受伤",
    "脖子疼",
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
    "premium is too high",
    "insurance went up",
    "renewal premium",
    "cheaper insurance",
    "switch carrier",
    "保单",
    "检视",
    "看看保险",
    "保险怎么样",
    "保费",
    "太贵",
    "涨价",
    "续保",
    "便宜一点",
    "换保险",
    "coverage review",
)

_GENERIC_VAGUE_MARKERS = (
    "你好",
    "您好",
    "在吗",
    "有空吗",
    "帮我看看",
    "这个怎么办",
    "hello",
    "hi there",
    "hey there",
)

_STATUS_INQUIRY_MARKERS = (
    "进度",
    "查进度",
    "什么进度",
    "到哪了",
    "哪一步",
    "还差什么",
    "还差",
    "缺什么",
    "继续",
    "继续办",
    "继续上传",
    "还没完",
    "完成了吗",
    "好了吗",
    "交了吗",
    "提交了吗",
    "现在怎么样",
    "资料齐了吗",
    "还有什么要补",
    "下一步是什么",
    "已提交",
    "status",
    "progress",
    "continue",
    "what is next",
    "what else do you need",
    "did i submit",
    "where am i",
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


def is_vague_greeting_for_progress(text: str) -> bool:
    """Vague greeting that should rehydrate Progress Card when an add_car case is open."""
    raw = (text or "").strip()
    if not raw:
        return False
    lowered = raw.lower()
    return _contains_any(lowered, _GENERIC_VAGUE_MARKERS) and len(lowered) <= 24


def is_add_vehicle_status_inquiry(text: str) -> bool:
    """High-confidence status / progress inquiry (P19E-2)."""
    raw = (text or "").strip()
    if not raw:
        return False
    lowered = raw.lower()
    if is_explicit_add_car_restart(raw):
        return False
    return _contains_any(lowered, _STATUS_INQUIRY_MARKERS)


def is_explicit_add_car_restart(text: str) -> bool:
    """Delegate to H5 upload restart markers (single source of truth)."""
    from services.fiqa_api.inbox_triage.h5_task_upload import is_explicit_add_car_restart as _restart

    return _restart(text)


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
        start_card_intent = _START_CARD_CLICK_IDS.get((menu_id or "").strip().lower())
        if start_card_intent:
            return IntentResult(
                intent=start_card_intent, confidence="high", matched_by="start_card_click_id"
            )
        injury_intent = _CLAIM_INJURY_CLICK_IDS.get((menu_id or "").strip().lower())
        if injury_intent:
            return IntentResult(
                intent=injury_intent, confidence="high", matched_by="claim_injury_click_id"
            )
        from_menu = _menu_intent_from_id(menu_id)
        if from_menu and from_menu != "unclear":
            return IntentResult(intent=from_menu, confidence="high", matched_by="menu_id")

    if not raw:
        return IntentResult(intent="unclear", confidence="low", matched_by="empty")

    if _contains_any(lowered, _COVERAGE_RISK_MARKERS):
        return IntentResult(
            intent="coverage_risk_intake",
            confidence="high",
            matched_by="coverage_risk_markers",
        )

    claim = _contains_any(lowered, _CLAIM_MARKERS)
    add_car = _contains_any(lowered, _ADD_CAR_MARKERS)
    policy = _contains_any(lowered, _POLICY_REVIEW_MARKERS)
    hits = sum([claim, add_car, policy])
    if hits == 0 and _contains_any(lowered, _GENERIC_VAGUE_MARKERS) and len(lowered) <= 24:
        return IntentResult(intent="unclear", confidence="low", matched_by="generic_vague")
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
