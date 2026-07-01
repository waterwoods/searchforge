"""Extract phone and VIN from WeCom plain text — adapter-local, no triage import."""

from __future__ import annotations

import re

from services.fiqa_api.inbox_triage.phone_normalization import (
    is_valid_customer_phone,
    normalize_phone_digits,
)

_PHONE_PATTERNS = (
    r"\(?(\d{3})\)?[-.\s]*(\d{3})[-.\s]*(\d{4})\b",
    r"\b(\d{3})[-.\s](\d{3})[-.\s](\d{4})\b",
    r"(?:电话|phone|call me|我电话|联系方式|手机)[：:\s]*\(?(\d{3})\)?[-.\s]*(\d{3})[-.\s]*(\d{4})\b",
)

_VIN_PATTERN = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b", re.IGNORECASE)


def extract_phone_from_text(text: str | None) -> str | None:
    """Return normalized 10-digit US phone when found in free text."""
    t = (text or "").strip()
    if not t:
        return None
    for pat in _PHONE_PATTERNS:
        m = re.search(pat, t, re.IGNORECASE)
        if m and len(m.groups()) == 3:
            candidate = f"{m.group(1)}{m.group(2)}{m.group(3)}"
            if is_valid_customer_phone(candidate):
                return normalize_phone_digits(candidate)
    digits = normalize_phone_digits(t)
    if is_valid_customer_phone(digits) and len(re.sub(r"\D", "", t)) >= 10:
        return digits
    return None


def extract_vin_from_text(text: str | None) -> str | None:
    """Return 17-char VIN when present in message text."""
    t = (text or "").strip()
    if not t:
        return None
    m = _VIN_PATTERN.search(t)
    if not m:
        return None
    vin = m.group(1).upper()
    return vin if len(vin) == 17 else None
