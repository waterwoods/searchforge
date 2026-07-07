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


def wecom_customer_display_label(
    external_userid: str | None,
    *,
    customer_name: str | None = None,
    customer_phone: str | None = None,
) -> str:
    """
    Broker-facing customer label for WeCom cases without CRM nickname.

    Priority: known name → phone → short external_userid suffix → generic fallback.
    """
    name = (customer_name or "").strip()
    if name:
        return name[:128]
    phone = (customer_phone or "").strip()
    if phone and is_valid_customer_phone(phone):
        digits = normalize_phone_digits(phone)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return phone[:32]
    ext = (external_userid or "").strip()
    if ext:
        suffix = ext[-4:] if len(ext) > 4 else ext
        return f"企业微信客户（尾号 {suffix}）"
    return "企业微信客户"

# Track B0.2 (contract §4.2) — ZIP, delivery date, primary driver.
# Same pattern as phone/VIN above: adapter-local regex, no triage import,
# no reuse of case_draft_engine.py's V4/V5 confidence machinery.
_ZIP_MARKER_PATTERNS = (
    r"(?:邮编|zip\s*code|zip)[：:\s]*(\d{5})\b",
)
_ZIP_STANDALONE_PATTERN = re.compile(r"(?<!\d)(\d{5})(?!\d)")

_DATE_PATTERN = re.compile(
    r"(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}[/-]\d{1,2})(?!\d)"
)
_CHINESE_MONTH_DAY_PATTERN = re.compile(r"(\d{1,2})月(\d{1,2})[日号]?")

_DRIVER_PATTERNS = (
    r"(?:driver name is|primary driver is|driver name|primary driver|driver is|driver)"
    r"[:：\s]+([A-Za-z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff\s]{0,30})",
    r"(?:主驾驶人是|主驾驶是|主驾驶人|主驾驶|司机是|司机)[:：\s]*([A-Za-z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff]{0,20})",
)


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


def extract_zip_from_text(text: str | None) -> str | None:
    """Return 5-digit US ZIP when found in free text (marker-first, then bare token)."""
    t = (text or "").strip()
    if not t:
        return None
    lowered = t.lower()
    for pat in _ZIP_MARKER_PATTERNS:
        m = re.search(pat, lowered)
        if m:
            return m.group(1)
    m = _ZIP_STANDALONE_PATTERN.search(t)
    if m:
        return m.group(1)
    return None


def extract_delivery_date_from_text(text: str | None) -> str | None:
    """Return a date token when present in free text (calendar, Chinese, or relative pickup)."""
    t = (text or "").strip()
    if not t:
        return None
    m = _DATE_PATTERN.search(t)
    if m:
        return m.group(1)
    cm = _CHINESE_MONTH_DAY_PATTERN.search(t)
    if cm:
        return f"{cm.group(1)}月{cm.group(2)}日"
    from services.fiqa_api.inbox_triage.date_normalization import normalize_delivery_date_or_flag

    resolved, mode = normalize_delivery_date_or_flag(t)
    if mode == "resolved" and resolved:
        return resolved
    if mode == "ask_exact":
        for phrase in ("明天", "后天", "大后天", "下周一", "下周二", "下周三", "下周四", "下周五", "下周六", "下周日", "下周天"):
            if phrase in t:
                return phrase
    pickup_markers = ("提车", "拿车", "delivery", "pickup", "pick up")
    if any(marker in t.lower() or marker in t for marker in pickup_markers):
        cm2 = _CHINESE_MONTH_DAY_PATTERN.search(t)
        if cm2:
            return f"{cm2.group(1)}月{cm2.group(2)}日"
    return None


def extract_primary_driver_from_text(text: str | None) -> str | None:
    """Return the primary driver's name when introduced by an explicit marker in free text."""
    t = (text or "").strip()
    if not t:
        return None
    for pat in _DRIVER_PATTERNS:
        m = re.search(pat, t, re.IGNORECASE)
        if not m:
            continue
        name = re.split(r"[，,。.\n]", m.group(1).strip())[0].strip()
        if name:
            return name[:60]
    return None
