"""
Render hot-swappable reply template families: substitute variables and fall back safely.

The template layer only assembles final visible text. Callers pass industry/config fallbacks
unchanged from existing behavior so missing JSON keys are a no-op.
"""

from __future__ import annotations

import re
from typing import Any

from services.fiqa_api.inbox_triage.reply_template_policy import (
    FAMILY_ADD_CAR_ASK_DELIVERY_DRIVER,
    FAMILY_ADD_CAR_ASK_DRIVER_ONLY,
    FAMILY_ADD_CAR_ASK_FULL,
    FAMILY_ADD_CAR_ASK_MODEL_AND_ZIP,
    FAMILY_ADD_CAR_ASK_VEHICLE,
    FAMILY_ADD_CAR_ASK_YEAR_AND_ZIP,
    FAMILY_ADD_CAR_ASK_ZIP,
)

# Mirrors triage._build_client_reply_draft add-car customer_question defaults (regression safety).
ADD_CAR_COLLECTING_FALLBACKS: dict[str, dict[str, str]] = {
    FAMILY_ADD_CAR_ASK_ZIP: {
        "zh": "邮编发我一下，我好往下报价。",
        "en": "Send the zip and I will run the quote.",
    },
    FAMILY_ADD_CAR_ASK_DRIVER_ONLY: {
        "zh": "主要驾驶人发我一下，我好安排报价。",
        "en": "Send me the main driver so I can prepare the quote.",
    },
    FAMILY_ADD_CAR_ASK_DELIVERY_DRIVER: {
        "zh": "提车日和主要驾驶人发我一下，我好安排报价。",
        "en": "Send the delivery date and main driver so I can prepare the quote.",
    },
    FAMILY_ADD_CAR_ASK_YEAR_AND_ZIP: {
        "zh": "年份和邮编发我，我好继续报价。",
        "en": "Send the year and zip so I can run the quote.",
    },
    FAMILY_ADD_CAR_ASK_MODEL_AND_ZIP: {
        "zh": "车型和邮编发我，我好继续报价。",
        "en": "Send the make/model and zip so I can run the quote.",
    },
    FAMILY_ADD_CAR_ASK_VEHICLE: {
        "zh": "可以帮你看这台车报价。年份和车型先发我。",
        "en": "I can quote the new car—send year and make/model first.",
    },
    FAMILY_ADD_CAR_ASK_FULL: {
        "zh": "可以帮你看这台车报价。请发：年份、车型、VIN（有的话）、提车日、邮编、主要驾驶人。",
        "en": "I can quote the new car. Send year, make/model, VIN if you have it, delivery date, zip, and main driver.",
    },
}

_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def apply_template_variables(template: str, variables: dict[str, str] | None) -> str:
    """Replace {key} placeholders; unknown keys left intact."""

    if not template or not variables:
        return template or ""

    def sub(m: re.Match[str]) -> str:
        key = m.group(1)
        if key in variables:
            return variables[key]
        return m.group(0)

    return _PLACEHOLDER_RE.sub(sub, template)


def pick_language_text(block: dict[str, Any] | None, language: str) -> str:
    """zh vs en; empty string if missing."""
    if not isinstance(block, dict):
        return ""
    lang_key = "zh" if (language or "").strip().lower() == "zh" else "en"
    return (block.get(lang_key) or "").strip()


def render_family(
    families: dict[str, Any] | None,
    family_id: str,
    language: str,
    variables: dict[str, str] | None,
    fallback: str,
) -> str:
    """
    Look up family_id in merged template layer; substitute variables; if absent or empty, return fallback.
    `families` is the merged map (common + client) from get_reply_template_layer.
    """
    fb = (fallback or "").strip()
    if not families or not family_id:
        return fb
    block = families.get(family_id)
    raw = pick_language_text(block, language) if isinstance(block, dict) else ""
    if not raw:
        return fb
    out = apply_template_variables(raw, variables or {})
    return (out or "").strip() or fb


def add_car_collecting_fallback_line(family_id: str, language: str) -> str:
    """Code-default line for the progressive add-car ask; used when layer JSON is missing a family."""
    b = ADD_CAR_COLLECTING_FALLBACKS.get(family_id) or ADD_CAR_COLLECTING_FALLBACKS[FAMILY_ADD_CAR_ASK_FULL]
    is_zh = (language or "").strip().lower() == "zh"
    return (b.get("zh") if is_zh else b.get("en")) or ""
