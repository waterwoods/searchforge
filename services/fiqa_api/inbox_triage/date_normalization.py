"""
Deterministic relative pickup / delivery phrasing for Add-Car (Unified Intake).

Resolves a small safe subset to calendar dates; otherwise flags a focused follow-up ask.
Does not replace truth guardrails — triage/guardrails call these helpers explicitly.
"""

from __future__ import annotations

import os
import re
from datetime import date, timedelta
from typing import Literal

# Subset aligned with truth_field_guardrails._RELATIVE_TIME_MARKERS (high-confidence only here).
_REL_NEXT_WEEKDAY_ZH = (
    "下周一",
    "下周二",
    "下周三",
    "下周四",
    "下周五",
    "下周六",
    "下周日",
    "下周天",
)

PickupMode = Literal["resolved", "ask_exact", "none"]


def detect_relative_delivery_phrase(text: str) -> bool:
    """True when text looks like relative pickup timing (not necessarily resolvable)."""
    from services.fiqa_api.inbox_triage.truth_field_guardrails import (
        _has_absolute_calendar_date,
        _relative_delivery_language,
    )

    raw = (text or "").strip()
    if not raw:
        return False
    tl = raw.lower()
    if _has_absolute_calendar_date(raw, tl):
        return False
    return _relative_delivery_language(tl, raw)


def _pickup_context(tl: str) -> bool:
    return any(
        m in tl
        for m in (
            "提",
            "拿车",
            "pickup",
            "pick up",
            "pick-up",
            "picking up",
            "delivery",
            "deliver",
            "effective",
            "start date",
        )
    )


def _reference_today() -> date:
    env = (os.environ.get("TRIAGE_REFERENCE_DATE") or "").strip()
    if env:
        try:
            y, m, d = [int(x) for x in env.split("-", 2)]
            return date(y, m, d)
        except (ValueError, TypeError):
            pass
    return date.today()


def _next_weekday_from(d: date, weekday: int) -> date:
    """weekday: Monday=0 .. Sunday=6 (datetime.weekday convention)."""
    days_ahead = (weekday - d.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return d + timedelta(days=days_ahead)


def _this_week_weekday_from(d: date, weekday: int) -> date:
    days_ahead = (weekday - d.weekday()) % 7
    return d + timedelta(days=days_ahead)


def normalize_delivery_date_or_flag(
    text: str,
    *,
    now_context: date | None = None,
) -> tuple[str | None, PickupMode]:
    """
    Return (YYYY-MM-DD or None, mode).

    mode:
      resolved   — calendar day inferred safely
      ask_exact  — relative/boundary pickup language without safe resolution
      none       — no relative pickup signal (caller may use other extraction)
    """
    from services.fiqa_api.inbox_triage.truth_field_guardrails import (
        _has_absolute_calendar_date,
        _relative_delivery_language,
    )

    raw = (text or "").strip()
    if not raw:
        return None, "none"
    tl = raw.lower()
    if _has_absolute_calendar_date(raw, tl):
        return None, "none"
    _weekday_pickup_only = bool(
        re.search(r"\b(friday|monday|tuesday|wednesday|thursday|saturday|sunday)\b", tl)
        and _pickup_context(tl)
    )
    if not _relative_delivery_language(tl, raw) and not _weekday_pickup_only:
        return None, "none"
    if not _pickup_context(tl) and not any(
        m in tl for m in ("tomorrow", "today", "next week", "下周", "明天", "后天")
    ):
        # Relative time without pickup/effective cue — still ask for exact date if it's clearly delivery-ish
        if not any(m in tl for m in ("friday", "monday", "tuesday", "wednesday", "thursday", "saturday", "sunday")):
            return None, "none"

    today = now_context or _reference_today()

    # 明天 / tomorrow
    if "明天" in raw or re.search(r"\btomorrow\b", tl):
        resolved = today + timedelta(days=1)
        return resolved.isoformat(), "resolved"
    # 后天
    if "后天" in raw:
        resolved = today + timedelta(days=2)
        return resolved.isoformat(), "resolved"
    # 大后天
    if "大后天" in raw:
        resolved = today + timedelta(days=3)
        return resolved.isoformat(), "resolved"

    # English: next monday / next friday
    m_en = re.search(
        r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        tl,
    )
    if m_en:
        wd = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"].index(
            m_en.group(1)
        )
        resolved = _next_weekday_from(today, wd)
        return resolved.isoformat(), "resolved"

    # Chinese: 下周一 … 下周日 (Monday=0 .. Sunday=6)
    for idx, phrase in enumerate(_REL_NEXT_WEEKDAY_ZH[:7]):
        if phrase in raw:
            resolved = _next_weekday_from(today, idx)
            return resolved.isoformat(), "resolved"

    # 本周五 / 这周五 (this week's Friday)
    if any(m in raw for m in ("本周五", "这周五", "这周周五")):
        resolved = _this_week_weekday_from(today, 4)  # Friday
        if resolved < today:
            resolved += timedelta(days=7)
        return resolved.isoformat(), "resolved"

    # Friday / Monday standalone → ambiguous which week
    if re.search(r"\b(friday|monday|tuesday|wednesday|thursday|saturday|sunday)\s+(pickup|pick\s*up)\b", tl):
        return None, "ask_exact"
    if re.search(
        r"(周五|周一|周二|周三|周四|周六|周日|礼拜五|礼拜一).{0,6}(提|拿车|取车)",
        raw,
    ):
        return None, "ask_exact"

    # Generic relative week without weekday anchor
    if "下周" in raw and not any(x in raw for x in _REL_NEXT_WEEKDAY_ZH):
        return None, "ask_exact"
    if re.search(r"\bnext\s+week\b", tl) and not m_en:
        return None, "ask_exact"

    return None, "ask_exact"


def focused_ask_for_delivery_date(language: str) -> str:
    if (language or "").strip().lower() == "zh":
        return "具体是几月几号提车？"
    return "What exact calendar date is the pickup (month/day/year)?"


def augment_customer_text_for_resolved_delivery(
    raw_customer_text: str,
    resolved_iso: str,
) -> str:
    """Append a calendar literal so truth calendar checks can pass (same thread scope)."""
    r = (raw_customer_text or "").strip()
    if not r:
        return f"pickup {resolved_iso}"
    return f"{r} {resolved_iso}"


def relative_delivery_should_invalidate_persisted_calendar(last_customer_segment: str) -> bool:
    """
    When the latest bubble is relative-only pickup language, do not keep a persisted calendar delivery_date
    as satisfied for this turn (customer changed commitment to non-calendar wording).
    """
    from services.fiqa_api.inbox_triage.truth_field_guardrails import (
        _has_absolute_calendar_date,
        _relative_delivery_language,
    )

    raw = (last_customer_segment or "").strip()
    if not raw:
        return False
    tl = raw.lower()
    if _has_absolute_calendar_date(raw, tl):
        return False
    if not _relative_delivery_language(tl, raw):
        return False
    return _pickup_context(tl) or "提" in raw or "pick" in tl
