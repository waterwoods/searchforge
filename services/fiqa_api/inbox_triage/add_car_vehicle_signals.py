"""Explicit vehicle-identity detection for Add-Car (rule layer + guardrails).

Substring markers like ``es`` must not match inside ``drives``. Use word-boundary
regexes for short English tokens; keep Chinese multi-character phrases as substring checks.
"""

from __future__ import annotations

import re

# Avoid ``\\b`` for VIN boundaries: CJK glue (e.g. ``VIN是1HG...``) is ``\\w`` in Python,
# so ``\\b`` fails between ``是`` and the first digit. Use explicit VIN-charset boundaries.
# Same charset as legacy VIN checks: digits + letters excluding I/O/Q (case-insensitive).
_VIN_17_CLASS = r"0-9a-hj-npr-z"
_VIN_17_RE = re.compile(
    rf"(?<![{_VIN_17_CLASS}])([{_VIN_17_CLASS}]{{17}})(?![{_VIN_17_CLASS}])",
    re.IGNORECASE,
)

# English / numeric vehicle cues — word-bounded (order: longer phrases first for alternation).
_VEHICLE_PHRASES_EN: tuple[str, ...] = (
    "model y",
    "model 3",
    "model s",
    "model x",
    "cr-v",
    "f-150",
    "cx-5",
    "cx-9",
    "pick up",
    "pickup",
    "pick-up",
    "tesla",
    "toyota",
    "honda",
    "nissan",
    "bmw",
    "lexus",
    "mazda",
    "subaru",
    "ford",
    "chevy",
    "chevrolet",
    "mercedes",
    "benz",
    "hyundai",
    "kia",
    "rivian",
    "lucid",
    "ram",
    "mustang",
    "silverado",
    "highlander",
    "4runner",
    "sienna",
    "tacoma",
    "pathfinder",
    "outback",
    "forester",
    "accord",
    "civic",
    "pilot",
    "odyssey",
    "camry",
    "corolla",
    "rav4",
    "altima",
    "rogue",
    "sentra",
    "gla",
    "glc",
    "crv",
    "cx5",
    "f150",
    "x5",
    "x3",
    "x1",
    "x7",
    "rx",
    "nx",
    "es",
)

_PARTS: list[str] = []
for _p in _VEHICLE_PHRASES_EN:
    if " " in _p:
        _PARTS.append(r"\b" + r"\s+".join(re.escape(x) for x in _p.split()) + r"\b")
    else:
        _PARTS.append(r"\b" + re.escape(_p) + r"\b")
_VEHICLE_PHRASE_BOUNDARY_RE = re.compile("|".join(_PARTS), re.IGNORECASE)

# Standalone "model" / "year" as vehicle words (not inside mostly/model number noise without make).
_MODEL_WORD_RE = re.compile(r"\bmodel\b", re.IGNORECASE)

_VEHICLE_ZH_MARKERS: tuple[str, ...] = (
    "宝马",
    "特斯拉",
    "本田",
    "丰田",
    "凯美瑞",
    "思域",
    "马自达",
    "花冠",
    "雷克萨斯",
    "车型",
    "雅阁",
    "日产",
    "奔驰",
    "奥迪",
    "保时捷",
    "路虎",
    "吉普",
    "雪弗兰",
    "雪佛兰",
    "现代",
    "起亚",
    "斯巴鲁",
    "福特",
    "车架",
)


def _strip_likely_calendar_dates_for_year_scan(t: str) -> str:
    """Remove MM/DD/YYYY and YYYY-MM-DD style fragments so years are not mistaken for vehicle MY."""
    s = t
    s = re.sub(r"\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(20[12][0-9])\b", " ", s)
    s = re.sub(r"\b(20[12][0-9])[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b", " ", s)
    return s


def text_has_vehicle_year_signal(t: str) -> bool:
    """True when a 20xx token appears in a non-calendar-date context (vehicle model year)."""
    cleaned = _strip_likely_calendar_dates_for_year_scan(t)
    return bool(re.search(r"(?<![0-9])(20[12][0-9])(?:\s*款)?(?![0-9])", cleaned))


def text_has_vehicle_make_model_signal(t: str) -> bool:
    """True when text explicitly names a make/model or vehicle-type cue (bounded English tokens)."""
    tl = (t or "").lower()
    if any(m in t for m in _VEHICLE_ZH_MARKERS):
        return True
    if _VEHICLE_PHRASE_BOUNDARY_RE.search(tl):
        return True
    if _MODEL_WORD_RE.search(tl):
        return True
    return False


def utterance_has_explicit_vehicle_identity(text: str) -> bool:
    """Customer explicitly stated vehicle identity (VIN, year+make/model cues, or make/model literals)."""
    raw = (text or "").strip()
    if not raw:
        return False
    tl = raw.lower()
    if _VIN_17_RE.search(tl):
        return True
    if text_has_vehicle_year_signal(tl) and text_has_vehicle_make_model_signal(tl):
        return True
    if text_has_vehicle_make_model_signal(tl):
        return True
    return False
