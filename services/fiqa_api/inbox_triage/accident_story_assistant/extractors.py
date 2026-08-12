"""Deterministic accident-story extractors (bounded; no lifecycle writes)."""

from __future__ import annotations

import re
from typing import Any

from services.fiqa_api.inbox_triage.accident_story_assistant.contract import InjuryStatus

_INJURY_NO = re.compile(
    r"(没有受伤|无人受伤|没人受伤|无人员受伤|没有人受伤|人没事|no injur|nobody (was )?hurt|no one (was )?hurt|without injur)",
    re.I,
)
_INJURY_YES = re.compile(
    r"((?<!没)有人受伤|(?<!没)(?<!不)(?<!无)有受伤|(?<!没)受伤了|someone was injured|\binjur(?:y|ed)\b|\bhurt\b)",
    re.I,
)
_INJURY_UNKNOWN = re.compile(
    r"(不确定|不清楚|unknown|not sure|不确定有没有受伤|也可能没有|好像有人受伤|可能受伤也可能)",
    re.I,
)

# Chinese STT (Chirp) emits ASCII "," for spoken Chinese pauses, so clause
# boundaries must cover both full-width and ASCII punctuation. Without ASCII
# "," a bounded window silently runs across the whole narrative.
_CLAUSE_BREAK_CHARS = r"，。；、！？,;!?\n"
_CLAUSE_CHAR = rf"[^{_CLAUSE_BREAK_CHARS}]"
_CLAUSE_SPLIT = re.compile(rf"[{_CLAUSE_BREAK_CHARS}]+")

# Model sentinels that mean "I found nothing" — never a customer-visible value.
_SENTINEL_TEXT = frozenset(
    {
        "unknown", "n/a", "na", "none", "null", "nil", "-", "--", "?",
        "未知", "不详", "不明", "无", "没有", "不确定", "待确认", "暂无",
    }
)

# Narrative verbs that must stay in what_happened, never inside a location.
_LOCATION_NARRATIVE_CUT = re.compile(
    r"(被人|被一|被撞|被追尾|被|追尾|撞到|撞了|碰撞|剐蹭|倒车|开车|行驶|等红灯|"
    r"受伤|发生|出事|事故|的时候|时候|我们|对方|我感觉|感觉)"
)

_TIME = re.compile(
    r"("
    r"昨天|今天|前天|上周|星期[一二三四五六日天]|"
    r"\d{1,2}\s*月\s*\d{1,2}\s*日|"
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|"
    r"(morning|afternoon|evening|night|yesterday|today|last night)|"
    r"(早上|上午|中午|下午|傍晚|晚上|凌晨)"
    r")([^\n，。；;]{0,40})?",
    re.I,
)

_LOCATION = re.compile(
    r"("
    r"(在|于)\s*([^，。；;\n]{2,40})|"
    r"((San Jose|Los Angeles|Oakland|Fremont|Cupertino|Sunnyvale|Milpitas|"
    r"Mountain View|Palo Alto|Santa Clara|San Mateo|Irvine|San Francisco)[^，。；;\n]{0,40})|"
    r"([^，。；;\n]{0,20}(高速公路|路口|停车场|停车库|parking lot|freeway|intersection)[^，。；;\n]{0,20})"
    r")",
    re.I,
)

_VEHICLE = re.compile(
    r"("
    r"\b(Camry|Corolla|Civic|Accord|Tesla|Model\s?[3YXS]|Highlander|RAV4|Prius|CR-V|"
    r"pickup|truck|SUV|minivan|sedan)\b|"
    r"(丰田|本田|特斯拉|凯美瑞|雅阁|思域|皮卡|卡车|面包车)"
    r")",
    re.I,
)


def normalize_story(text: str) -> str:
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.strip() for ln in raw.split("\n")]
    cleaned = " ".join(ln for ln in lines if ln)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:2000]


def split_clauses(text: str) -> list[str]:
    """Split a story into clauses on full-width AND ASCII punctuation."""
    return [c.strip() for c in _CLAUSE_SPLIT.split(str(text or "")) if c.strip()]


def _has_injury_hedge(text: str) -> bool:
    """Hedged contradiction ("好像有人受伤，也可能没有") scoped to one clause.

    Unbounded `.*` across the whole story made any later "没有受伤" collide with
    an unrelated earlier "好像", so an explicit no-injury answer was discarded.
    """
    clauses = split_clauses(text)
    for index, clause in enumerate(clauses):
        if re.search(r"好像.{0,12}受伤.{0,12}没有", clause):
            return True
        if re.search(r"可能.{0,12}也可能", clause) and "受伤" in clause:
            return True
        if "也可能没有" in clause:
            prev = clauses[index - 1] if index else ""
            if "受伤" in clause or "受伤" in prev:
                return True
    return False


def extract_injury_status(text: str) -> tuple[InjuryStatus, float, list[str]]:
    t = str(text or "")
    conflicts: list[str] = []
    has_no = bool(_INJURY_NO.search(t))
    has_yes = bool(_INJURY_YES.search(t))
    has_unk = bool(_INJURY_UNKNOWN.search(t))
    # Hedged contradiction: "好像有人受伤也可能没有"
    if _has_injury_hedge(t):
        conflicts.append("injury_hedged_contradiction")
        return "unknown", 0.45, conflicts
    if has_yes and has_no:
        conflicts.append("injury_yes_and_no_mentioned")
        return "unknown", 0.4, conflicts
    if has_unk and not has_no and not has_yes:
        return "unknown", 0.7, conflicts
    if has_unk and (has_yes or has_no):
        conflicts.append("injury_uncertain_with_other_signal")
        return "unknown", 0.5, conflicts
    if has_no:
        return "no", 0.85, conflicts
    if has_yes:
        return "yes", 0.8, conflicts
    return "unknown", 0.2, conflicts


def extract_time_text(text: str) -> tuple[str, float]:
    t = str(text or "")
    # Prefer clock-bearing phrases before bare relative days (昨天 / yesterday).
    for pat in (
        # Spoken Chinese clock times arrive as numerals ("三点"), not digits.
        r"(昨天|今天|前天)[上下]午\s*[\d一二三四五六七八九十两]{1,3}\s*点半?\s*(左右|多|钟)?",
        r"(昨天|今天|前天)?早上\s*[\d一二三四五六七八九十两]{1,3}\s*点半?\s*(左右|多|钟)?",
        r"(昨天|今天|前天)?晚上\s*[\d一二三四五六七八九十两]{1,3}\s*点半?\s*(左右|多|钟)?",
        r"昨天[上下]午\s*\d{1,2}\s*点?",
        r"今天[上下]午\s*\d{1,2}\s*点?",
        r"今天早上\s*\d{1,2}\s*点?半?",
        r"昨天[上下]午",
        r"今天[上下]午",
        r"昨天晚上",
        r"今天早上",
        r"yesterday\s+at\s+\d{1,2}\s*(:\d{2})?\s*(am|pm)?",
        r"yesterday\s+\d{1,2}\s*(:\d{2})?\s*(am|pm)",
        r"(昨天|今天|前天)\s*\d{1,2}\s*(:\d{2})?\s*(am|pm)",
        r"(昨天|今天|前天)\s*\d{1,2}\s*点半?",
        r"\d{1,2}\s*月\s*\d{1,2}\s*日\s*[上下]午?\s*\d{0,2}\s*点?",
        r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
        r"yesterday\s+(morning|afternoon|evening|night)",
        r"\b\d{1,2}\s*(:\d{2})?\s*(am|pm)\b",
        r"昨天",
        r"今天",
        r"前天",
        r"yesterday",
        r"today",
        r"(早上|上午|中午|下午|傍晚|晚上|凌晨)",
    ):
        m = re.search(pat, t, re.I)
        if m:
            return re.sub(r"\s+", " ", m.group(0)).strip()[:120], 0.75
    return "", 0.0


_CITY_NAMES = (
    r"San Jose|Los Angeles|Oakland|Fremont|Cupertino|Sunnyvale|Milpitas|"
    r"Mountain View|Palo Alto|Santa Clara|San Mateo|Irvine|San Francisco|"
    r"Santa Ana|Anaheim|Long Beach|Pasadena|Riverside|San Diego|Sacramento|"
    r"Torrance|Fullerton|Costa Mesa|Garden Grove|Alhambra|Arcadia"
)
# Chinese STT transcribes city names phonetically, so Latin-only matching misses them.
_CITY_ZH = r"圣何塞|圣安纳|洛杉矶|尔湾|旧金山|奥克兰|库比蒂诺|山景城|帕洛阿尔托|圣地亚哥|阿罕布拉"


def trim_location_narrative(value: str) -> str:
    """Cut a location candidate at the first accident-narrative marker."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    match = _LOCATION_NARRATIVE_CUT.search(raw)
    if match and match.start() > 0:
        raw = raw[: match.start()]
    return re.sub(r"\s+", " ", raw).strip(" ，。;；、,的和与及在于")[:200]


def looks_like_location_narrative(value: str) -> bool:
    """True when a candidate is story text rather than a place."""
    raw = str(value or "").strip()
    if not raw or len(raw) > 60:
        return True
    return bool(re.search(r"(追尾|撞到|撞了|碰撞|剐蹭|受伤|倒车的时候|开车的时候)", raw))


def extract_location_text(text: str) -> tuple[str, float]:
    t = str(text or "")
    city = re.search(rf"(\b(?:{_CITY_NAMES})\b|{_CITY_ZH}){_CLAUSE_CHAR}{{0,30}}", t, re.I)
    if city:
        trimmed = trim_location_narrative(city.group(0))
        if trimmed:
            return trimmed, 0.8
    place = re.search(
        rf"({_CLAUSE_CHAR}{{0,16}}(高速公路|路口|停车场|停车库|parking lot|freeway|intersection)"
        rf"{_CLAUSE_CHAR}{{0,16}})",
        t,
        re.I,
    )
    if place:
        trimmed = trim_location_narrative(place.group(0))
        if trimmed:
            return trimmed, 0.7
    at = re.search(rf"(?:在|于)\s*({_CLAUSE_CHAR}{{2,40}})", t)
    if at:
        trimmed = trim_location_narrative(at.group(1))
        if trimmed and not looks_like_location_narrative(trimmed):
            return trimmed, 0.65
    return "", 0.0


def extract_vehicles(text: str) -> list[str]:
    found: list[str] = []
    for m in _VEHICLE.finditer(str(text or "")):
        v = re.sub(r"\s+", " ", m.group(0)).strip()
        if v and v not in found:
            found.append(v)
    return found[:5]


def build_incident_summary(
    *,
    normalized: str,
    injury: InjuryStatus,
    time_text: str,
    location_text: str,
) -> str:
    bits: list[str] = []
    if normalized:
        bits.append(normalized if len(normalized) <= 180 else normalized[:177] + "…")
    else:
        bits.append("客户描述了事故经过。")
    meta: list[str] = []
    if time_text:
        meta.append(f"时间：{time_text}")
    if location_text:
        meta.append(f"地点：{location_text}")
    if injury == "no":
        meta.append("受伤：无")
    elif injury == "yes":
        meta.append("受伤：有")
    else:
        meta.append("受伤：不确定")
    if meta:
        bits.append("（" + "；".join(meta) + "）")
    return " ".join(bits)[:500]


def is_sentinel_text(value: str) -> bool:
    """True when a model returned a placeholder instead of a real value."""
    return str(value or "").strip().strip(".。").lower() in _SENTINEL_TEXT


def is_grounded_in_source(value: str, source: str) -> bool:
    """True when every meaningful token of `value` actually occurs in the story.

    The model may rephrase more cleanly than the deterministic rules, but it may
    never introduce a place, time, or vehicle the customer did not say.
    """
    val = str(value or "").strip()
    src = str(source or "")
    if not val or not src:
        return False
    src_low = src.lower()
    # Digits are the easiest way to invent precision ("3:00 PM" from "下午").
    for digit_run in re.findall(r"\d+", val):
        if digit_run not in src_low:
            return False
    for token in re.findall(r"[A-Za-z]{2,}", val):
        if token.lower() not in src_low:
            return False
    cjk = [ch for ch in val if "\u4e00" <= ch <= "\u9fff"]
    if cjk:
        present = sum(1 for ch in cjk if ch in src)
        if present / len(cjk) < 0.8:
            return False
    return True


def validate_model_proposals(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Reject hallucinated keys / invalid injury; return sanitized subset or raise."""
    if not isinstance(raw, dict):
        raise ValueError("invalid_model_json")
    allowed = {
        "incident_summary",
        "injury_status",
        "accident_time_text",
        "accident_location_text",
        "involved_parties",
        "involved_vehicles",
        "confidence_by_field",
        "warnings",
    }
    unknown = sorted(set(raw.keys()) - allowed - {"schema_version", "proposed_facts"})
    if unknown:
        raise ValueError(f"hallucinated_fields:{','.join(unknown)}")
    out: dict[str, Any] = {}
    if "injury_status" in raw:
        inj = str(raw.get("injury_status") or "").strip().lower()
        if inj not in ("yes", "no", "unknown"):
            raise ValueError("invalid_injury_status")
        out["injury_status"] = inj
    for key in ("incident_summary", "accident_time_text", "accident_location_text"):
        if key in raw and raw[key] is not None:
            text = str(raw[key]).strip()[:500]
            # "unknown" is the model saying it found nothing; it is not a value.
            if text and not is_sentinel_text(text):
                out[key] = text
    for key in ("involved_parties", "involved_vehicles"):
        if key in raw:
            vals = raw.get(key)
            if not isinstance(vals, list):
                raise ValueError(f"invalid_{key}")
            out[key] = [str(x).strip()[:80] for x in vals if str(x).strip()][:8]
    if "confidence_by_field" in raw:
        conf = raw.get("confidence_by_field")
        if not isinstance(conf, dict):
            raise ValueError("invalid_confidence_by_field")
        out["confidence_by_field"] = {
            str(k): float(v)
            for k, v in conf.items()
            if str(k).strip() and isinstance(v, (int, float))
        }
    if "warnings" in raw:
        warns = raw.get("warnings")
        if not isinstance(warns, list):
            raise ValueError("invalid_warnings")
        out["warnings"] = [str(x).strip()[:200] for x in warns if str(x).strip()][:10]
    return out
