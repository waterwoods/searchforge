"""Deterministic contract for AI Request More drafting.

Everything the model is allowed to know, and everything it is allowed to say,
is defined here. The missing set itself comes from the Cap2 checklist
(``derive_missing_information_checklist``) — this module never re-derives it.
"""

from __future__ import annotations

import re
from typing import Any

LANGUAGE_ZH = "zh"

AUTHORITY_AI_DRAFT = "ai_draft"
AUTHORITY_TEMPLATE = "office_template"

MAX_DRAFT_TEXT_CHARS = 400
MAX_ITEM_LABEL_CHARS = 60
MAX_ITEM_INSTRUCTION_CHARS = 200
MAX_ITEMS = 6

TEMPLATE_INTRO_ZH = "您好，为了继续处理您的案件，目前还需要："
TEMPLATE_OUTRO_ZH = "请方便时在这里补充上传，谢谢。"
NOTHING_MISSING_ZH = "无需补充"
CONFIRMATION_SUFFIX_ZH = "（请确认）"

# Office-approved default wording per requestable item type.
DEFAULT_ITEM_INSTRUCTIONS_ZH: dict[str, str] = {
    "vin": "VIN 是车辆识别码，共 17 位，通常在挡风玻璃左下角或驾驶座门框标签上。",
    "vehicle_information": "请提供车辆的年份、品牌和型号。",
    "policy_or_insurance_card": "请拍摄保险卡正面，确保文字清晰可读。",
}

# Wording anchors used by the representation guardrail: an AI draft must still
# name every deterministic item, even if it rephrases the label.
ITEM_KEYWORDS_ZH: dict[str, tuple[str, ...]] = {
    "vin": ("vin", "车架号", "车辆识别"),
    "vehicle_information": ("车辆", "车型"),
    "policy_or_insurance_card": ("保险卡", "保单"),
}

_DIGIT_RUN = re.compile(r"\d{6,}")
_URL = re.compile(r"(https?://|www\.)", re.IGNORECASE)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def _str(value: Any) -> str:
    return str(value or "").strip()


def derive_request_more_missing_items(
    checklist: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """The authoritative missing set the AI is allowed to draft for.

    Reuses the Cap2 checklist decision (``suggested_for_request``), which is
    already false for confirmed / not_applicable / non-sendable facts. This
    function filters and orders; it never decides.
    """
    items: list[dict[str, Any]] = []
    for row in checklist or []:
        if not isinstance(row, dict):
            continue
        if not bool(row.get("suggested_for_request")):
            continue
        field_key = _str(row.get("field_key"))
        item_type = _str(row.get("item_type"))
        if not field_key or not item_type:
            continue
        customer_label = _str(row.get("customer_label")) or _str(row.get("label")) or field_key
        items.append(
            {
                "field_key": field_key,
                "item_type": item_type,
                "customer_label": customer_label[:MAX_ITEM_LABEL_CHARS],
                "request_mode": _str(row.get("request_mode")) or "request_missing",
                "status": _str(row.get("status")),
            }
        )
        if len(items) >= MAX_ITEMS:
            break
    for position, item in enumerate(items, start=1):
        item["position"] = position
    return items


def _sanitized_vehicle_summary(case: dict[str, Any] | None) -> str:
    """Make/model only — no VIN, no plate, no long identifiers."""
    case = case if isinstance(case, dict) else {}
    facts = case.get("known_facts") if isinstance(case.get("known_facts"), dict) else {}
    parts = [_str(facts.get("vehicle_make")), _str(facts.get("vehicle_model"))]
    summary = " ".join(p for p in parts if p).strip()
    if not summary:
        summary = _str(facts.get("primary_vehicle_summary")) or _str(facts.get("vehicle_information"))
    summary = _DIGIT_RUN.sub("", summary)
    return summary[:40].strip()


def build_safe_context(
    *,
    case: dict[str, Any] | None,
    items: list[dict[str, Any]],
    language: str = LANGUAGE_ZH,
) -> dict[str, Any]:
    """Bounded snapshot for the model. Never the whole Case, never PII."""
    return {
        "language": language,
        "request_reason": "claim_intake_completion",
        "vehicle_summary": _sanitized_vehicle_summary(case),
        "items": [
            {
                "field_key": item["field_key"],
                "customer_label": item["customer_label"],
                "request_mode": item["request_mode"],
                "position": item["position"],
            }
            for item in items
        ],
    }


def default_instructions_for(item: dict[str, Any]) -> str:
    return DEFAULT_ITEM_INSTRUCTIONS_ZH.get(_str(item.get("item_type")), "")


def build_template_draft(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Office template wording — the always-available deterministic answer."""
    lines: list[str] = []
    out_items: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        label = item["customer_label"]
        suffix = CONFIRMATION_SUFFIX_ZH if item["request_mode"] == "request_confirmation" else ""
        lines.append(f"{index}. {label}{suffix}")
        out_items.append(
            {
                "field_key": item["field_key"],
                "item_type": item["item_type"],
                "label": label,
                "instructions": default_instructions_for(item)[:MAX_ITEM_INSTRUCTION_CHARS],
                "request_mode": item["request_mode"],
                "position": index,
            }
        )
    draft_text = "\n".join([TEMPLATE_INTRO_ZH, *lines, TEMPLATE_OUTRO_ZH])
    return {"draft_text": draft_text[:MAX_DRAFT_TEXT_CHARS], "items": out_items}


def contains_unsupported_detail(text: str) -> bool:
    """Long digit runs / links / emails would be invented or leaked identifiers."""
    body = str(text or "")
    return bool(_DIGIT_RUN.search(body) or _URL.search(body) or _EMAIL.search(body))
