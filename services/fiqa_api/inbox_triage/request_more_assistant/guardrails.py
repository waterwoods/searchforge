"""Post-LLM validation for Request More drafting.

Any failure returns a reason code; the caller then serves the office template.
The model can only lose — it can never widen, narrow, or re-authorize the
deterministic missing set.
"""

from __future__ import annotations

from typing import Any

from services.fiqa_api.inbox_triage.request_more_assistant.contract import (
    ITEM_KEYWORDS_ZH,
    MAX_DRAFT_TEXT_CHARS,
    MAX_ITEM_INSTRUCTION_CHARS,
    MAX_ITEM_LABEL_CHARS,
    contains_unsupported_detail,
)

# Coverage / liability / payment promises the broker may never send as AI copy.
FORBIDDEN_PHRASES: tuple[str, ...] = (
    "一定赔",
    "全额赔",
    "肯定能赔",
    "会赔付",
    "赔付金额",
    "理赔金额",
    "保险公司会赔",
    "责任在",
    "全责",
    "无责",
    "在保障范围内",
    "不在保障范围",
    "已承保",
    "免赔额",
    "报销",
    "打款",
    "付款",
    "covered",
    "coverage",
    "liability",
    "we will pay",
    "reimburse",
    "payout",
    "approved",
)

OUTCOME_PASSED = "passed"
OUTCOME_INVALID_SHAPE = "invalid_shape"
OUTCOME_EXTRA_ITEM = "extra_item_not_in_missing_set"
OUTCOME_MISSING_ITEM = "required_item_dropped"
OUTCOME_FORBIDDEN_LANGUAGE = "forbidden_language"
OUTCOME_UNSUPPORTED_DETAIL = "unsupported_case_detail"
OUTCOME_ITEM_NOT_REPRESENTED = "item_not_represented_in_text"
OUTCOME_TOO_LONG = "draft_text_too_long"


def _str(value: Any) -> str:
    return str(value or "").strip()


def find_forbidden_phrase(text: str) -> str | None:
    body = str(text or "").lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase.lower() in body:
            return phrase
    return None


def _item_is_named(text: str, item: dict[str, Any]) -> bool:
    body = str(text or "").lower()
    anchors = [item["customer_label"], *ITEM_KEYWORDS_ZH.get(_str(item.get("item_type")), ())]
    return any(anchor and anchor.lower() in body for anchor in anchors)


def validate_ai_draft(
    payload: Any,
    *,
    required_items: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    """Return ``(normalized_draft, outcome)``. Non-``passed`` means use template."""
    if not isinstance(payload, dict):
        return None, OUTCOME_INVALID_SHAPE

    draft_text = _str(payload.get("draft_text"))
    raw_items = payload.get("items")
    if not draft_text or not isinstance(raw_items, list):
        return None, OUTCOME_INVALID_SHAPE
    if len(draft_text) > MAX_DRAFT_TEXT_CHARS:
        return None, OUTCOME_TOO_LONG

    required_by_key = {item["field_key"]: item for item in required_items}
    seen: dict[str, dict[str, Any]] = {}
    for raw in raw_items:
        if not isinstance(raw, dict):
            return None, OUTCOME_INVALID_SHAPE
        field_key = _str(raw.get("field_key"))
        if field_key not in required_by_key:
            return None, OUTCOME_EXTRA_ITEM
        if field_key in seen:
            return None, OUTCOME_EXTRA_ITEM
        seen[field_key] = raw
    for field_key in required_by_key:
        if field_key not in seen:
            return None, OUTCOME_MISSING_ITEM

    checked_text = [draft_text]
    normalized: list[dict[str, Any]] = []
    for position, required in enumerate(required_items, start=1):
        raw = seen[required["field_key"]]
        label = _str(raw.get("label"))[:MAX_ITEM_LABEL_CHARS] or required["customer_label"]
        instructions = _str(raw.get("instructions"))[:MAX_ITEM_INSTRUCTION_CHARS]
        checked_text.extend([label, instructions])
        normalized.append(
            {
                "field_key": required["field_key"],
                "item_type": required["item_type"],
                "label": label,
                "instructions": instructions,
                # Mode and order stay deterministic — the model cannot reorder
                # the broker's request or change what kind of answer is needed.
                "request_mode": required["request_mode"],
                "position": position,
            }
        )

    for body in checked_text:
        if find_forbidden_phrase(body):
            return None, OUTCOME_FORBIDDEN_LANGUAGE
        if contains_unsupported_detail(body):
            return None, OUTCOME_UNSUPPORTED_DETAIL

    for required in required_items:
        if not _item_is_named(draft_text, required):
            return None, OUTCOME_ITEM_NOT_REPRESENTED

    return {"draft_text": draft_text, "items": normalized}, OUTCOME_PASSED
