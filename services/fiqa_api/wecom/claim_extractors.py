"""P19H-2 — deterministic accident basics extraction for Claim guided workflow."""

from __future__ import annotations

import re

_CLAIM_COMMAND_PHRASES: tuple[str, ...] = (
    "我要理赔",
    "我撞车了",
    "出事故了",
    "发生事故了",
    "车祸了",
    "事故理赔",
    "file a claim",
    "i had an accident",
    "accident claim",
)

_INSUFFICIENT_DESCRIPTION_ONLY: tuple[str, ...] = (
    "我要理赔",
    "我撞车了",
    "出事故了",
    "发生事故了",
    "车祸了",
    "事故理赔",
    "理赔",
    "撞车",
    "车祸",
)

_DATETIME_PATTERN = re.compile(
    r"(今天上午?\s*\d{1,2}\s*点|今天下午\s*\d{1,2}\s*点|今天晚上\s*\d{1,2}\s*点|"
    r"今天上午|今天下午|今天晚上|昨天\s*\d{1,2}\s*点|昨天|刚才|"
    r"this morning|this afternoon|just now|yesterday|"
    r"\d{1,2}[：:]\d{2}\s*(?:am|pm)?|\d{1,2}\s*点|"
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
    re.IGNORECASE,
)

_LOCATION_PATTERN = re.compile(
    r"(?:在|at|near|around|附近)\s*([^，,。.?！!；;]{3,80})|"
    r"([A-Za-z][A-Za-z0-9\s]*(?:Blvd|Boulevard|Ave|Avenue|St|Street|Rd|Road|Dr|Drive|Freeway|freeway)\b[^，,。.?！!]{0,40})|"
    r"\b(Irvine|Santa Ana|Costa Mesa|Newport Beach|Anaheim|405|5\s*号|高速|freeway|路口)\b[^，,。.?！!]{0,30}",
    re.IGNORECASE,
)

_INJURY_YES_MARKERS: tuple[str, ...] = (
    "有人受伤",
    "人受伤",
    "受伤了",
    "受伤",
    "脖子疼",
    "头疼",
    "injured",
    "injury",
    "hurt",
    "hospital",
    "ambulance",
    "医院",
    "紧急",
)


def _strip_command_phrases(text: str) -> str:
    cleaned = (text or "").strip()
    for phrase in _CLAIM_COMMAND_PHRASES:
        cleaned = cleaned.replace(phrase, " ")
    return re.sub(r"\s+", " ", cleaned).strip(" ，,。.")


def _is_insufficient_description(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or len(raw) < 8:
        return True
    return any(raw == phrase or raw.startswith(phrase) for phrase in _INSUFFICIENT_DESCRIPTION_ONLY)


def message_mentions_injury(text: str) -> bool:
    lowered = (text or "").lower()
    return any(m in lowered or m in (text or "") for m in _INJURY_YES_MARKERS)


def has_accident_basics_signals(text: str) -> bool:
    """True when message likely carries one or more accident basic fields."""
    parsed = extract_accident_basics_fields(text)
    return any(parsed.get(k) for k in ("accident_datetime", "accident_location", "accident_description"))


def extract_accident_basics_fields(text: str) -> dict[str, str | None]:
    """Extract accident_datetime / accident_location / accident_description from free text."""
    raw = (text or "").strip()
    if not raw:
        return {
            "accident_datetime": None,
            "accident_location": None,
            "accident_description": None,
        }

    accident_datetime: str | None = None
    dt_match = _DATETIME_PATTERN.search(raw)
    if dt_match:
        accident_datetime = dt_match.group(0).strip()

    accident_location: str | None = None
    loc_match = _LOCATION_PATTERN.search(raw)
    if loc_match:
        accident_location = (loc_match.group(1) or loc_match.group(2) or loc_match.group(0) or "").strip()
        accident_location = accident_location.rstrip("附近").strip()

    remainder = _strip_command_phrases(raw)
    accident_description: str | None = None
    if not _is_insufficient_description(remainder):
        accident_description = remainder
    elif len(raw) >= 20 and accident_datetime and accident_location:
        accident_description = remainder if len(remainder) >= 8 else raw

    return {
        "accident_datetime": accident_datetime,
        "accident_location": accident_location,
        "accident_description": accident_description,
    }
