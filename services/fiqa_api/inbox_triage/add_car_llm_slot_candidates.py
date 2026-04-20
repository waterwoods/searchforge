"""Bounded LLM candidate extraction for Add-Car (rules remain authoritative).

Env:
  ADD_CAR_LLM_SLOT_EXTRACTION — enable candidate calls (default off).
  ADD_CAR_LLM_SLOT_MODEL — optional model override (else LLM_MODEL or gpt-4o-mini).

LLM output is validated deterministically; only accepted literals are appended as a
synthetic [客户] line so existing _extract_add_car_fields / _extract_contact_fields apply.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from services.fiqa_api.inbox_triage.add_car_vehicle_signals import utterance_has_explicit_vehicle_identity

logger = logging.getLogger(__name__)

_CA_ZIP_RE = re.compile(r"(?<![0-9])(9[0-9]{4})(?![0-9])", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(20[12][0-9])\b")
_VIN_RE = re.compile(r"\b([0-9A-HJ-NPR-Z]{17})\b", re.IGNORECASE)

# Subset of rule-layer tokens: a candidate make/model must hit at least one for model=True.
_KNOWN_VEHICLE_TOKENS: frozenset[str] = frozenset(
    x.lower()
    for x in (
        "bmw",
        "x5",
        "x3",
        "x1",
        "x7",
        "tesla",
        "model y",
        "model 3",
        "model s",
        "model x",
        "honda",
        "accord",
        "civic",
        "cr-v",
        "crv",
        "pilot",
        "odyssey",
        "toyota",
        "camry",
        "corolla",
        "rav4",
        "highlander",
        "4runner",
        "sienna",
        "tacoma",
        "nissan",
        "altima",
        "rogue",
        "sentra",
        "pathfinder",
        "lexus",
        "rx",
        "es",
        "nx",
        "mercedes",
        "benz",
        "gla",
        "glc",
        "mazda",
        "cx-5",
        "cx5",
        "cx-9",
        "subaru",
        "outback",
        "forester",
        "ford",
        "f-150",
        "f150",
        "mustang",
        "ram",
        "chevy",
        "chevrolet",
        "silverado",
        "rivian",
        "lucid",
        "hyundai",
        "kia",
        "宝马",
        "特斯拉",
        "本田",
        "丰田",
        "凯美瑞",
        "思域",
        "马自达",
        "花冠",
        "雷克萨斯",
    )
)

_NAME_EXCLUDE = frozenset(
    x.lower()
    for x in (
        "bmw",
        "tesla",
        "honda",
        "toyota",
        "model",
        "zip",
        "90210",
        "accord",
        "camry",
    )
)

_DELIVERY_MARKERS_EN = ("pickup", "delivery", "picking up", "pick up", "tomorrow", "next week", "friday")
_DELIVERY_MARKERS_ZH = ("提车", "拿车", "下周", "明天", "delivery", "交车")


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def add_car_llm_slot_extraction_enabled() -> bool:
    return _env_truthy("ADD_CAR_LLM_SLOT_EXTRACTION")


def _api_key() -> str:
    return (os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") or "").strip()


def _slot_model_name() -> str:
    return (
        os.getenv("ADD_CAR_LLM_SLOT_MODEL", "").strip()
        or os.getenv("LLM_MODEL", "").strip()
        or "gpt-4o-mini"
    )


def _validate_year(y: Any) -> str | None:
    if y is None or not isinstance(y, str):
        return None
    s = y.strip()
    m = _YEAR_RE.search(s)
    if not m:
        return None
    return m.group(1)


def _validate_zip(z: Any) -> str | None:
    if z is None or not isinstance(z, str):
        return None
    m = _CA_ZIP_RE.search(z)
    return m.group(1) if m else None


def _validate_vin(v: Any) -> str | None:
    if v is None or not isinstance(v, str):
        return None
    s = re.sub(r"\s+", "", v.strip().upper())
    m = _VIN_RE.search(s)
    return m.group(1).upper() if m else None


def _validate_phone(p: Any) -> str | None:
    if p is None or not isinstance(p, str):
        return None
    for pat in (
        r"\(?(\d{3})\)?[-.\s]*(\d{3})[-.\s]*(\d{4})\b",
        r"\b(\d{3})[-.\s](\d{3})[-.\s](\d{4})\b",
    ):
        m = re.search(pat, p, re.IGNORECASE)
        if m and len(m.groups()) == 3:
            a, b, c = m.group(1), m.group(2), m.group(3)
            if a and b and c:
                return f"{a}-{b}-{c}"
    return None


def _validate_name(n: Any) -> str | None:
    if n is None or not isinstance(n, str):
        return None
    s = n.strip()
    if len(s) < 2 or len(s) > 48:
        return None
    if s.lower() in _NAME_EXCLUDE or re.match(r"^\d+$", s):
        return None
    return s[:120]


def _vehicle_tokens_acceptable(make: str | None, model: str | None) -> bool:
    blob = f"{make or ''} {model or ''}".lower()
    if not blob.strip():
        return False
    return any(tok in blob for tok in _KNOWN_VEHICLE_TOKENS)


def _delivery_note_triggers_field(note: str | None) -> bool:
    if not note or not isinstance(note, str):
        return False
    t = note.lower()
    if any(m in t for m in _DELIVERY_MARKERS_EN):
        return True
    if any(m in note for m in _DELIVERY_MARKERS_ZH):
        return True
    if re.search(r"\d{1,2}月\d{1,2}", note) and any(x in note for x in ("提", "拿", "到车", "取")):
        return True
    return False


def _driver_self_triggers(val: Any) -> bool:
    if val is True:
        return True
    if isinstance(val, str) and val.strip().lower() in ("true", "yes", "1", "self", "me"):
        return True
    return False


def _parse_llm_json(content: str) -> dict[str, Any] | None:
    raw = (content or "").strip()
    if not raw:
        return None
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return None
    try:
        out = json.loads(m.group())
        return out if isinstance(out, dict) else None
    except json.JSONDecodeError:
        return None


def _build_augmentation_fragments(
    parsed: dict[str, Any],
    *,
    last_customer_bubble: str,
) -> tuple[list[str], list[str]]:
    """Return (fragments for synthetic customer line, accepted_slot_keys for telemetry)."""
    parts: list[str] = []
    accepted: list[str] = []
    _allow_vehicle_slots = utterance_has_explicit_vehicle_identity(last_customer_bubble)
    y = _validate_year(parsed.get("candidate_year"))
    if y and _allow_vehicle_slots:
        parts.append(y)
        accepted.append("year")
    z = _validate_zip(parsed.get("candidate_zip"))
    if z:
        parts.append(z)
        accepted.append("zip")
    vin = _validate_vin(parsed.get("candidate_vin"))
    if vin:
        parts.append(vin)
        accepted.append("vin")
    mk = parsed.get("candidate_vehicle_make")
    md = parsed.get("candidate_vehicle_model")
    mk_s = mk.strip() if isinstance(mk, str) else ""
    md_s = md.strip() if isinstance(md, str) else ""
    if _allow_vehicle_slots and _vehicle_tokens_acceptable(mk_s or None, md_s or None):
        if mk_s:
            parts.append(mk_s)
        if md_s:
            parts.append(md_s)
        accepted.append("make_model")
    ph = _validate_phone(parsed.get("candidate_phone"))
    if ph:
        parts.append(ph)
        accepted.append("phone")
    nm = _validate_name(parsed.get("candidate_name"))
    if nm:
        parts.append(f"我叫{nm}" if any("\u4e00" <= c <= "\u9fff" for c in nm) else f"call me {nm}")
        accepted.append("name")
    if _delivery_note_triggers_field(
        parsed.get("candidate_delivery_note") if isinstance(parsed.get("candidate_delivery_note"), str) else None
    ):
        note = str(parsed.get("candidate_delivery_note")).strip()
        parts.append(note[:80])
        accepted.append("delivery_date")
    if _driver_self_triggers(parsed.get("candidate_primary_driver_self")):
        parts.append("我本人开")
        accepted.append("primary_driver")
    return parts, accepted


def _compact_prior_bubbles(merged_text: str, max_chars: int = 220) -> str:
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    bodies = [m.strip() for m in matches if m.strip()]
    if len(bodies) < 2:
        return ""
    prev = bodies[-2]
    if len(bodies) >= 3:
        prev2 = bodies[-3]
        chunk = f"{prev2[:100]} … {prev[:100]}"
    else:
        chunk = prev[:max_chars]
    return chunk[:max_chars]


def maybe_augment_merged_text_for_add_car_slots(
    merged_text: str,
    last_customer_bubble: str,
    *,
    rule_fields: dict[str, bool],
    invoke_llm: bool,
    skip_reason: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Optionally call LLM; append at most one synthetic [客户] line of validated literals.

    Caller (triage) sets invoke_llm using rule-layer heuristics to limit token spend.
    Returns (possibly augmented merged_text, observability dict).
    """
    meta: dict[str, Any] = {"called": False, "accepted_slots": [], "certainty": None, "skip_reason": None}
    if not add_car_llm_slot_extraction_enabled():
        meta["skip_reason"] = "disabled"
        return merged_text, meta
    if not invoke_llm:
        meta["skip_reason"] = skip_reason or "caller_skip"
        return merged_text, meta
    if not _api_key():
        meta["skip_reason"] = "no_api_key"
        return merged_text, meta

    last_c = (last_customer_bubble or "").strip()[:450]
    prior = _compact_prior_bubbles(merged_text)
    rf = rule_fields or {}
    hint = (
        f"regex_hints year={bool(rf.get('year'))} model={bool(rf.get('model'))} zip={bool(rf.get('zip'))} "
        f"vin={bool(rf.get('vin'))} delivery={bool(rf.get('delivery'))} driver={bool(rf.get('driver'))}"
    )
    user = (
        "Extract Add-Car quote-intake slots from the customer text. Output JSON ONLY, no markdown.\n"
        "Schema keys (use null when unknown):\n"
        '{"certainty":"high|medium|low",'
        '"candidate_year":null|string,'
        '"candidate_vehicle_make":null|string,'
        '"candidate_vehicle_model":null|string,'
        '"candidate_vin":null|string,'
        '"candidate_zip":null|string,'
        '"candidate_phone":null|string,'
        '"candidate_name":null|string,'
        '"candidate_delivery_note":null|string,'
        '"candidate_primary_driver_self":null|boolean,'
        '"correction_intent":null|boolean,'
        '"ambiguous_vehicle":null|boolean}\n'
        f"Hints (non-authoritative): {hint}\n"
        f"Latest customer message:\n{last_c}\n"
    )
    if prior:
        user += f"Prior customer snippet:\n{prior}\n"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=_api_key())
        resp = client.chat.completions.create(
            model=_slot_model_name(),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract structured candidate fields for a California auto insurance "
                        "add-vehicle quote request. Respond with a single JSON object only. "
                        "Use null for anything not clearly stated. Do not invent VIN, phone, or zip. "
                        "certainty reflects your confidence in the extracted candidates."
                    ),
                },
                {"role": "user", "content": user},
            ],
            temperature=0.1,
            max_tokens=220,
        )
        content = ""
        if resp.choices:
            content = (resp.choices[0].message.content or "").strip()
        parsed = _parse_llm_json(content)
        meta["called"] = True
        if not parsed:
            meta["error"] = "parse_failed"
            return merged_text, meta
        meta["certainty"] = parsed.get("certainty")
        frags, accepted = _build_augmentation_fragments(parsed, last_customer_bubble=last_c)
        meta["accepted_slots"] = accepted
        if not frags:
            meta["note"] = "no_validated_candidates"
            return merged_text, meta
        syn = " ".join(frags)
        # Prepend so the last [客户] segment stays the real latest bubble (correction / vehicle concrete).
        aug = "[客户] " + syn + "\n\n" + (merged_text or "").strip()
        return aug, meta
    except Exception as e:
        logger.warning("add_car LLM slot extraction failed: %s", e)
        meta["called"] = True
        meta["error"] = str(e)[:200]
        return merged_text, meta
