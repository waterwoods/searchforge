"""Rule-based fact extraction for Premium Review / Claim Lite WeCom minimal lanes."""

from __future__ import annotations

import re
from typing import Any

from services.fiqa_api.wecom.identity import extract_zip_from_text

_PREMIUM_AMOUNT_PATTERN = re.compile(
    r"(?:\$|usd\s*)?(\d{1,3}(?:,\d{3})+|\d{4,6})(?:\s*(?:/|per\s*)?(?:year|yr|annual|年))?",
    re.IGNORECASE,
)
_CARRIER_MARKERS = (
    "state farm",
    "geico",
    "progressive",
    "allstate",
    "farmers",
    "mercury",
    "national general",
    "中国人保",
    "平安",
    "太平洋",
)
_COMMERCIAL_USE_MARKERS = ("uber black", "uber", "tcp", "lyft", "rideshare", "commercial driver")
_INJURY_MARKERS = ("受伤", "脖子疼", "头疼", "hurt", "injury", "injured", "pain", "疼")
_NO_INJURY_MARKERS = ("人没事", "没受伤", "没有受伤", "no injury", "not hurt", "i'm ok", "i am ok")
_LOCATION_PATTERN = re.compile(
    r"(?:在|at|near|around|附近)\s*([^\s，,。.?！!]{2,40}(?:405|freeway|高速|公路| Blvd| Ave| St| Rd)?)",
    re.IGNORECASE,
)
_TIME_PATTERN = re.compile(
    r"(今天上午?\s*\d{1,2}\s*点|今天\s*\d{1,2}[：:]\d{2}|"
    r"昨天|yesterday|just now|刚才|this morning|this afternoon|\d{1,2}[：:]\d{2}\s*(?:am|pm)?)",
    re.IGNORECASE,
)
_VEHICLE_BRAND_PATTERN = re.compile(
    r"\b(BMW|Mercedes|Toyota|Honda|Tesla|Audi|Lexus|Ford|Chevrolet|宝马|奔驰|丰田|本田)\b",
    re.IGNORECASE,
)


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(m in lowered for m in markers)


def extract_premium_facts(text: str) -> dict[str, Any]:
    """Extract minimal Premium Review facts from customer free text."""
    raw = (text or "").strip()
    lowered = raw.lower()
    facts: dict[str, Any] = {"customer_message": raw}
    known: list[str] = []
    missing = [
        "renewal_notice",
        "dec_page",
        "current_premium",
        "renewal_date",
        "vin_or_vehicle",
        "recent_claim_ticket",
    ]

    m = _PREMIUM_AMOUNT_PATTERN.search(raw.replace("，", ","))
    if m:
        amount = m.group(1).replace(",", "")
        facts["premium_amount"] = amount
        known.append(f"premium_{amount}")
        if "current_premium" in missing:
            missing.remove("current_premium")

    zip_code = extract_zip_from_text(raw)
    if zip_code:
        facts["zip"] = zip_code
        known.append(f"zip_{zip_code}")

    for carrier in _CARRIER_MARKERS:
        if carrier in lowered:
            facts["carrier"] = carrier.title() if carrier.isascii() else carrier
            known.append("carrier")
            break

    if _contains_any(lowered, _COMMERCIAL_USE_MARKERS):
        facts["usage"] = "Uber Black / TCP" if "uber" in lowered or "tcp" in lowered else "Commercial / Rideshare"
        known.append("usage_commercial")

    if "renewal" in lowered or "续保" in raw or "renew" in lowered:
        facts["renewal_mentioned"] = True
        known.append("renewal_mentioned")
        if "renewal_date" in missing:
            missing.remove("renewal_date")

    return {"facts": facts, "collected_keys": known, "still_needed": missing}


def extract_claim_facts(text: str) -> dict[str, Any]:
    """Extract minimal Claim Lite facts from customer free text."""
    raw = (text or "").strip()
    lowered = raw.lower()
    facts: dict[str, Any] = {"customer_message": raw}
    known: list[str] = []
    missing = [
        "accident_time",
        "location",
        "injury_status",
        "other_party_info",
        "photos",
        "police_report",
        "carrier_contacted",
    ]

    tm = _TIME_PATTERN.search(raw)
    if tm:
        facts["accident_time"] = tm.group(1).strip()
        known.append("accident_time")
        missing.remove("accident_time")

    lm = _LOCATION_PATTERN.search(raw)
    if lm:
        facts["location"] = lm.group(1).strip()
        known.append("location")
        missing.remove("location")
    elif "405" in raw:
        facts["location"] = "405 area"
        known.append("location")
        missing.remove("location")

    if _contains_any(lowered, _NO_INJURY_MARKERS):
        facts["injury"] = "None reported"
        known.append("no_injury")
        missing.remove("injury_status")
    elif _contains_any(lowered, _INJURY_MARKERS):
        facts["injury"] = "Injury mentioned — broker must call"
        known.append("injury")
        missing.remove("injury_status")

    vm = _VEHICLE_BRAND_PATTERN.search(raw)
    if vm:
        facts["other_vehicle"] = vm.group(1)
        known.append("other_vehicle")
        missing.remove("other_party_info")

    if "对方" in raw or "other driver" in lowered or "other party" in lowered:
        known.append("other_party_mentioned")
        if "other_party_info" in missing and "other_vehicle" not in facts:
            pass  # still need details

    if "照片" in raw or "photo" in lowered or "picture" in lowered:
        known.append("photos_mentioned")
        missing.remove("photos")

    if "警察" in raw or "police" in lowered or "报案" in raw:
        known.append("police_mentioned")
        missing.remove("police_report")

    if "报保险" in raw or "called insurance" in lowered or "carrier" in lowered:
        known.append("carrier_contact_mentioned")

    return {"facts": facts, "collected_keys": known, "still_needed": missing}
