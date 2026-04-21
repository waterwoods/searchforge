"""
Strict Truth guardrails for Add-Car structured fields (Unified Intake).

When in doubt, do not write. See should_accept_field() for field-level rules.
"""

from __future__ import annotations

import logging
import os
import re
from contextvars import ContextVar
from typing import Any

from services.fiqa_api.inbox_triage.add_car_vehicle_signals import (
    _VIN_17_RE,
    text_has_vehicle_make_model_signal,
    text_has_vehicle_year_signal,
    utterance_has_explicit_vehicle_identity,
)

logger = logging.getLogger(__name__)

_truth_guardrail_debug_rows: ContextVar[list[dict[str, Any]] | None] = ContextVar(
    "truth_guardrail_debug_rows", default=None
)


def truth_guardrails_debug_enabled() -> bool:
    return os.environ.get("DEBUG_TRUTH_GUARDRAILS", "").strip().lower() in ("1", "true", "yes", "on")


def truth_guardrail_debug_session_start() -> None:
    """Initialize per-request capture lists when DEBUG_TRUTH_GUARDRAILS is on."""
    if not truth_guardrails_debug_enabled():
        return
    _truth_guardrail_debug_rows.set([])


def _collapse_truth_guardrail_rows(rows: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """One row per field: prefer an accept decision over reject when both appear (e.g. vehicle_key + apply_strict)."""
    if not rows:
        return []
    by_field: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for r in rows:
        f = str(r.get("field") or "").strip()
        if not f:
            continue
        if f not in by_field:
            order.append(f)
        prev = by_field.get(f)
        if prev is None:
            by_field[f] = dict(r)
        elif r.get("decision") == "accept":
            by_field[f] = dict(r)
        elif prev.get("decision") != "accept":
            by_field[f] = dict(r)
    return [by_field[f] for f in order if f in by_field]


def maybe_attach_truth_guardrail_debug_to_triage(result: dict[str, Any]) -> None:
    """Attach debug arrays to triage JSON when flag is on."""
    if not truth_guardrails_debug_enabled():
        return
    collapsed = _collapse_truth_guardrail_rows(_truth_guardrail_debug_rows.get())
    result["truth_guardrail_debug"] = collapsed
    result["truth_guardrail_accepted"] = [x for x in collapsed if x.get("decision") == "accept"]

_VIN_PARTIAL_RE = re.compile(r"\b([0-9a-hj-npr-z]{5,16})\b", re.IGNORECASE)
_CA_ZIP_RE = re.compile(r"(?<![0-9])(9[0-9]{4})(?![0-9])", re.IGNORECASE)

_CONTEXT_REUSE_MARKERS: tuple[str, ...] = (
    "same as my other car",
    "same as the other car",
    "like my other car",
    "same car as",
    "you already have it",
    "you already have",
    "you've already got",
    "same driver",
    "use previous info",
    "use the previous",
    "use what you have",
    "on file already",
    "跟另一辆一样",
    "和另一辆一样",
    "跟之前的车一样",
    "和之前的车一样",
    "跟那台一样",
    "和那台一样",
    "你们已有",
    "你们那边有",
    "你们那边已有",
    "资料你们那边有",
    "之前有给过",
    "用之前的",
    "用上次",
    "之前发过",
    "同一个驾驶人",
    "跟上次一样",
)

_VIN_DEFERRAL_MARKERS: tuple[str, ...] = (
    "vin later",
    "later vin",
    "send the vin later",
    "send vin later",
    "vin another time",
    "not now",
    "晚点给",
    "晚一点给",
    "等等发",
    "改天发",
    "稍后发",
    "回头发",
    "回头给你",
    "下次发",
    "先发别的",
    "vin晚点",
    "车架晚点",
    "晚点发vin",
    "vin等",
    "等会儿发",
)

_RELATIVE_TIME_MARKERS: tuple[str, ...] = (
    "tomorrow",
    "today",
    "tonight",
    "soon",
    "next week",
    "this week",
    "next month",
    "this month",
    "next monday",
    "next tuesday",
    "next wednesday",
    "next thursday",
    "next friday",
    "next saturday",
    "next sunday",
    "this monday",
    "this tuesday",
    "this wednesday",
    "this thursday",
    "this friday",
    "this saturday",
    "this sunday",
    "明天",
    "后天",
    "大后天",
    "下周",
    "本周",
    "这周",
    "下月",
    "本月",
    "尽快",
    "马上",
    "下礼拜",
    "这礼拜",
    "礼拜一",
    "礼拜二",
    "礼拜三",
    "礼拜四",
    "礼拜五",
    "礼拜六",
    "礼拜天",
    "下周一",
    "下周二",
    "下周五",
    "本周五",
    "这周五",
)

_DRIVER_AMBIGUITY_EN = (
    "mostly",
    "sometimes",
    "usually",
    "often",
    "primarily",
    "both drive",
    "we both drive",
    "we both",
    "either of us",
    "both of us",
)
_DRIVER_AMBIGUITY_ZH = (
    "有时候",
    "偶尔",
    "多半",
    "大多时候",
    "轮流",
    "都可能",
    "我俩都",
    "两个人都",
    "两人都",
    "开得多",
    "也会开",
)

_DRIVER_EXPLICIT_OK = (
    "主要驾驶人是我",
    "主要驾驶人是我老婆",
    "主要驾驶人是我老公",
    "primary driver is",
    "main driver is",
    "i am the primary driver",
    "就我开",
    "我一个人开",
    "only me",
    "only i drive",
    "i'm the only driver",
)


def log_truth_guardrail_blocked(field: str, reason: str, raw_snippet: str) -> None:
    snippet = (raw_snippet or "").replace("\n", " ").strip()[:240]
    logger.info("[TRUTH_GUARDRAIL_BLOCKED] field=%s reason=%s input=%r", field, reason, snippet)
    log_truth_guardrail_row(field, "reject", reason, snippet)


def log_truth_guardrail_row(field: str, decision: str, reason: str, raw_snippet: str) -> None:
    snippet = (raw_snippet or "").replace("\n", " ").strip()[:240]
    if not truth_guardrails_debug_enabled():
        return
    buf = _truth_guardrail_debug_rows.get()
    if buf is not None:
        buf.append(
            {
                "field": field,
                "decision": decision,
                "reason": reason,
                "input": snippet,
            }
        )


def _normalize_field_name(field_name: str) -> str:
    """Map legacy aliases at the guardrail entry only; API / Assist use canonical ids (PILOT_CONTRACT_ADD_CAR_V1)."""
    fn = (field_name or "").strip().lower()
    if fn == "effective_date":
        return "delivery_date"
    if fn == "garaging_zip":
        return "zip"
    return fn


def _context_reuse_signal(text: str, tl: str) -> bool:
    return any(m in tl for m in _CONTEXT_REUSE_MARKERS) or any(m in text for m in _CONTEXT_REUSE_MARKERS)


def _vin_deferral_signal(tl: str, text: str) -> bool:
    if any(m in tl for m in _VIN_DEFERRAL_MARKERS):
        return True
    if "晚点给" in text and ("vin" in tl or "车架" in text):
        return True
    if re.search(r"\bvin\b.*\b(later|soon)\b", tl) or re.search(r"\b(later|soon)\b.*\bvin\b", tl):
        return True
    if re.search(r"\b(i'?ll|i will|going to)\s+send\b.*\b(later|after|tomorrow)\b", tl) and "vin" in tl:
        return True
    return False


def _vin_intent_mentioned(tl: str, text: str) -> bool:
    return "vin" in tl or "车架" in text


def _partial_vin_attempt(tl: str) -> bool:
    if _VIN_17_RE.search(tl):
        return False
    if not _vin_intent_mentioned(tl, tl):
        return False
    for m in _VIN_PARTIAL_RE.finditer(tl):
        if 5 <= len(m.group(1)) <= 16:
            return True
    return False


def _has_absolute_calendar_date(text: str, tl: str) -> bool:
    if re.search(r"\b(19|20)\d{2}[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b", text):
        return True
    if re.search(r"\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(19|20)\d{2}\b", text):
        return True
    if re.search(r"\b20[12][0-9]\s*年\s*\d{1,2}\s*月\s*\d{1,2}", text):
        return True
    if re.search(
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?,?\s+(19|20)\d{2}\b",
        tl,
    ):
        return True
    if re.search(r"(?:\d{1,2}\s*月\s*\d{1,2}\s*[号日]).{0,24}(20[12][0-9]{2})", text):
        return True
    return False


def _relative_delivery_language(tl: str, text: str) -> bool:
    if any(m in tl for m in _RELATIVE_TIME_MARKERS):
        return True
    if re.search(r"\bnext\s+[a-z]{3,9}\b", tl) and any(
        d in tl for d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun", "week")
    ):
        return True
    return False


def _driver_context_word(tl: str) -> bool:
    return any(
        k in tl
        for k in (
            "drive",
            "driver",
            "driving",
            "开车",
            "驾驶",
            "驾驶人",
            "主驾",
            "老婆",
            "老公",
            "spouse",
            "wife",
            "husband",
        )
    )


def _driver_ambiguity_signal(tl: str) -> bool:
    if any(p in tl for p in _DRIVER_EXPLICIT_OK):
        return False
    if any(x in tl for x in _DRIVER_AMBIGUITY_EN):
        if _driver_context_word(tl):
            return True
    if any(x in tl for x in _DRIVER_AMBIGUITY_ZH):
        if any(k in tl for k in ("开", "驾驶", "driver", "驾驶人", "主驾")):
            return True
    if "都可能开" in tl or ("都可能" in tl and "开" in tl):
        return True
    return False


def _primary_driver_truth_ok(tl: str) -> bool:
    if _driver_ambiguity_signal(tl):
        return False
    if any(p in tl for p in _DRIVER_EXPLICIT_OK):
        return True
    return True


_NAMED_DRIVER_EN_RE = re.compile(
    r"(?i)\b(?:her|his|their)\s+name\s+is\s+([A-Za-z][A-Za-z'`\u2019-]*(?:\s+[A-Za-z][A-Za-z'`\u2019-]*)+)"
)
_NAMED_DRIVER_ZH_RE = re.compile(r"(?:她叫|他叫)([^\s，,。]{2,24})")
_ME_PRIMARY_DRIVER_RE = re.compile(
    r"(?i)\b(?:i\s+am|i'?m)\s+the\s+primary\s+driver\b|"
    r"\b(?:primary|main)\s+driver\s+is\s+me\b|"
    r"\bthe\s+primary\s+driver\s+is\s+me\b"
)

# Strong operational cues (substring) — ambiguity markers must be rejected first via _driver_ambiguity_signal.
_PRIMARY_DRIVER_OPERATIONAL_MARKERS: tuple[str, ...] = (
    "driver",
    "驾驶人",
    "主驾",
    "主驾驶人",
    "谁开",
    "main driver",
    "primary driver",
    "老婆开",
    "老公开",
    "我开",
    "我自己开",
    "本人开",
    "主要我本人",
    "主要本人",
    "我本人开",
    "孩子开",
    "儿子开",
    "女儿开",
    "我老婆开",
    "我老公开",
    "我一个人开",
    "only me",
    "就我",
    "我一个人",
    "主要驾驶人是我",
    "我跟老婆",
    "我跟我老婆",
)


def _current_turn_supplies_primary_driver_identity(ct: str, ctl: str) -> bool:
    """True when this turn alone asserts who the primary driver is (not merely context-reuse)."""
    if _context_reuse_signal(ct, ctl):
        return False
    if _driver_ambiguity_signal(ctl):
        return False
    if any(p in ctl for p in _DRIVER_EXPLICIT_OK):
        return True
    if _NAMED_DRIVER_EN_RE.search(ct):
        return True
    if _NAMED_DRIVER_ZH_RE.search(ct):
        return True
    if _ME_PRIMARY_DRIVER_RE.search(ct):
        return True
    return any(m in ctl for m in _PRIMARY_DRIVER_OPERATIONAL_MARKERS)


def _thread_explicit_accepts_field(
    fn: str,
    text: str,
    tl: str,
    customer_bubbles: list[str] | None,
) -> bool:
    """
    Explicit literals anywhere in the thread override earlier deferral/context-reuse for that slot.

    raw_input (joined bubbles) is enough for VIN/ZIP/calendar dates. Primary driver is evaluated
    per customer bubble so a context-reuse line does not suppress a later identity line.
    """
    if fn == "vin":
        return bool(_VIN_17_RE.search(tl))
    if fn == "zip":
        z = _CA_ZIP_RE.search(tl)
        return bool(z and re.fullmatch(r"9[0-9]{4}", z.group(1)))
    if fn == "delivery_date":
        return _has_absolute_calendar_date(text, tl)
    if fn == "primary_driver":
        segs = customer_bubbles if customer_bubbles is not None else ([text] if text else [])
        for seg in segs:
            s = (seg or "").strip()
            if not s:
                continue
            if _current_turn_supplies_primary_driver_identity(s, s.lower()):
                return True
        return False
    if fn == "year":
        segs = customer_bubbles if customer_bubbles is not None else ([text] if text else [])
        for seg in segs:
            s = (seg or "").strip()
            if not s:
                continue
            sl = s.lower()
            if utterance_has_explicit_vehicle_identity(s) and text_has_vehicle_year_signal(sl):
                return True
        return False
    if fn == "make_model":
        segs = customer_bubbles if customer_bubbles is not None else ([text] if text else [])
        for seg in segs:
            s = (seg or "").strip()
            if not s:
                continue
            sl = s.lower()
            if utterance_has_explicit_vehicle_identity(s) and text_has_vehicle_make_model_signal(sl):
                return True
        return False
    return False


def _last_customer_turn_text(customer_bubbles: list[str] | None, raw_input: str) -> str:
    if customer_bubbles:
        return (customer_bubbles[-1] or "").strip()
    return (raw_input or "").strip()


def _current_turn_explicit_accepts_field(fn: str, last_seg: str, last_tl: str) -> tuple[bool, str | None]:
    """Highest-priority evidence: latest customer bubble only."""
    if not last_seg:
        return False, None
    if fn == "vin":
        return (True, "explicit_literal_current_turn") if _VIN_17_RE.search(last_tl) else (False, None)
    if fn == "zip":
        z = _CA_ZIP_RE.search(last_tl)
        ok = bool(z and re.fullmatch(r"9[0-9]{4}", z.group(1)))
        return (True, "explicit_literal_current_turn") if ok else (False, None)
    if fn == "delivery_date":
        ok = _has_absolute_calendar_date(last_seg, last_tl)
        return (True, "explicit_literal_current_turn") if ok else (False, None)
    if fn == "primary_driver":
        if _current_turn_supplies_primary_driver_identity(last_seg, last_tl):
            return True, "explicit_literal_current_turn"
        return False, None
    if fn == "year":
        if utterance_has_explicit_vehicle_identity(last_seg) and text_has_vehicle_year_signal(last_tl):
            return True, "explicit_literal_current_turn"
        return False, None
    if fn == "make_model":
        if utterance_has_explicit_vehicle_identity(last_seg) and text_has_vehicle_make_model_signal(last_tl):
            return True, "explicit_literal_current_turn"
        return False, None
    return False, None


def should_accept_field(
    field_name: str,
    raw_input: str,
    extracted_value: Any,
    *,
    customer_bubbles: list[str] | None = None,
) -> tuple[bool, str | None, str | None]:
    """
    Gate for writing a single Add-Car truth field.

    Returns (accept, reject_reason, decisive_debug_reason). The third value is the operator-facing
    reason code when DEBUG_TRUTH_GUARDRAILS is on (matches reject_reason on blocks).
    """
    fn = _normalize_field_name(field_name)
    if not extracted_value:
        return True, None, None

    text = (raw_input or "").strip()
    tl = text.lower()
    if not text:
        return True, None, None

    last_seg = _last_customer_turn_text(customer_bubbles, raw_input)
    last_tl = last_seg.lower()

    cur_ok, cur_reason = _current_turn_explicit_accepts_field(fn, last_seg, last_tl)
    if cur_ok:
        return True, None, cur_reason

    if _thread_explicit_accepts_field(fn, text, tl, customer_bubbles):
        return True, None, "explicit_literal_prior_thread"

    if _context_reuse_signal(text, tl):
        if fn in ("vin", "zip", "primary_driver", "year", "make_model"):
            return False, "context_reuse_block", "context_reuse_block"

    if fn == "vin":
        if _vin_deferral_signal(tl, text):
            return False, "deferred_input", "deferred_input"
        if _partial_vin_attempt(tl):
            return False, "partial_value", "partial_value"
        if _vin_intent_mentioned(tl, text) and not _VIN_17_RE.search(tl):
            return False, "incomplete_vin", "incomplete_vin"
        return False, "incomplete_vin", "incomplete_vin"

    if fn == "zip":
        z = _CA_ZIP_RE.search(tl)
        if not z or not re.fullmatch(r"9[0-9]{4}", z.group(1)):
            return False, "partial_value", "partial_value"
        return True, None, "allowed"

    if fn == "delivery_date":
        if _relative_delivery_language(tl, text) and not _has_absolute_calendar_date(text, tl):
            return False, "relative_date", "relative_date"
        if not _has_absolute_calendar_date(text, tl):
            return False, "incomplete_delivery_date", "incomplete_delivery_date"
        return True, None, "allowed"

    if fn == "primary_driver":
        if not _primary_driver_truth_ok(tl):
            return False, "driver_ambiguity", "driver_ambiguity"
        return True, None, "allowed"

    if fn == "year":
        return False, "no_explicit_vehicle_identity", "no_explicit_vehicle_identity"

    if fn == "make_model":
        return False, "no_explicit_vehicle_identity", "no_explicit_vehicle_identity"

    return True, None, "allowed"


def apply_strict_truth_guardrails_to_add_car_fields(
    fields: dict[str, bool],
    raw_customer_text: str,
    *,
    merged_labeled_text: str | None = None,
) -> dict[str, bool]:
    """Return a copy of rule-extracted Add-Car flags with strict-truth slots zeroed when rejected."""
    out = dict(fields)
    raw = (raw_customer_text or "").strip()
    if not raw:
        return out
    bubbles: list[str] | None = None
    if merged_labeled_text:
        from services.fiqa_api.inbox_triage.triage import _customer_bodies_from_labeled_thread

        found = _customer_bodies_from_labeled_thread(merged_labeled_text)
        bubbles = found if found else None

    checks: tuple[tuple[str, str], ...] = (
        ("vin", "vin"),
        ("zip", "zip"),
        ("driver", "primary_driver"),
        ("delivery", "delivery_date"),
        ("year", "year"),
        ("model", "make_model"),
    )
    for key, field_id in checks:
        if not out.get(key):
            continue
        ok, reason, dbg = should_accept_field(field_id, raw, True, customer_bubbles=bubbles)
        if (
            not ok
            and field_id == "delivery_date"
            and key == "delivery"
            and reason in ("relative_date", "incomplete_delivery_date")
        ):
            from services.fiqa_api.inbox_triage.date_normalization import (
                augment_customer_text_for_resolved_delivery,
                normalize_delivery_date_or_flag,
            )

            last_only = _last_customer_turn_text(bubbles, raw) or raw
            iso, mode = normalize_delivery_date_or_flag(last_only)
            if iso and mode == "resolved":
                combined = augment_customer_text_for_resolved_delivery(raw, iso)
                ok2, _, dbg2 = should_accept_field(
                    field_id, combined, True, customer_bubbles=bubbles
                )
                if ok2:
                    ok = True
                    dbg = dbg2 or "relative_resolved_safe"
        if not ok:
            out[key] = False
            log_truth_guardrail_row(field_id, "reject", dbg or reason or "blocked", raw)
        elif truth_guardrails_debug_enabled():
            log_truth_guardrail_row(field_id, "accept", dbg or "allowed", raw)
    return out
