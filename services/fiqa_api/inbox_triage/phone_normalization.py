"""
P16 Customer First — phone normalization for return-key lookup.

US-focused pilot: strip to digits; accept 10-digit or leading-1 eleven-digit.
"""

from __future__ import annotations

import re


def normalize_phone_digits(raw: str | None) -> str:
    """Return digits-only normalized phone, or empty when insufficient."""
    s = (raw or "").strip()
    if not s:
        return ""
    digits = re.sub(r"\D", "", s)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def normalize_us_phone_10_digits(raw: str | None) -> str | None:
    """Return exactly 10 US digits when valid; None if not a clear US phone."""
    digits = re.sub(r"\D", "", (raw or "").strip())
    if len(digits) == 10:
        return digits
    if len(digits) == 11 and digits.startswith("1"):
        return digits[1:]
    return None


def is_valid_customer_phone(raw: str | None) -> bool:
    """Phase 1: US 10-digit minimum bar for customer entry Continue."""
    digits = normalize_phone_digits(raw)
    return len(digits) == 10
