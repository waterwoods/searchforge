"""Deterministic accident-story extractors (bounded; no lifecycle writes)."""

from __future__ import annotations

import re
from typing import Any

from services.fiqa_api.inbox_triage.accident_story_assistant.contract import InjuryStatus

_INJURY_NO = re.compile(
    r"(没有受伤|无人受伤|没人受伤|无人员受伤|没有人受伤|no injur|nobody (was )?hurt|no one (was )?hurt|without injur)",
    re.I,
)
_INJURY_YES = re.compile(
    r"((?<!没)有人受伤|(?<!没)(?<!不)(?<!无)有受伤|(?<!没)受伤了|someone was injured|\binjur(?:y|ed)\b|\bhurt\b)",
    re.I,
)
_INJURY_UNKNOWN = re.compile(r"(不确定|不清楚|unknown|not sure|不确定有没有受伤)", re.I)

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
    r"Mountain View|Palo Alto|Santa Clara|Irvine|San Francisco)[^，。；;\n]{0,40})|"
    r"([^，。；;\n]{0,20}(高速公路|路口|停车场|停车库|parking lot|freeway|intersection)[^，。；;\n]{0,20})"
    r")",
    re.I,
)

_VEHICLE = re.compile(
    r"("
    r"\b(Camry|Corolla|Civic|Accord|Tesla|Model\s?[3YXS]|Highlander|RAV4|Prius|CR-V)\b|"
    r"(丰田|本田|特斯拉|凯美瑞|雅阁|思域)"
    r")",
    re.I,
)


def normalize_story(text: str) -> str:
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.strip() for ln in raw.split("\n")]
    cleaned = " ".join(ln for ln in lines if ln)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:2000]


def extract_injury_status(text: str) -> tuple[InjuryStatus, float, list[str]]:
    t = str(text or "")
    conflicts: list[str] = []
    has_no = bool(_INJURY_NO.search(t))
    has_yes = bool(_INJURY_YES.search(t))
    has_unk = bool(_INJURY_UNKNOWN.search(t))
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
    # Prefer compact relative time phrases.
    for pat in (
        r"昨天[上下]午",
        r"今天[上下]午",
        r"昨天晚上",
        r"今天早上",
        r"昨天",
        r"今天",
        r"前天",
        r"\d{1,2}\s*月\s*\d{1,2}\s*日",
        r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
        r"yesterday\s+(morning|afternoon|evening|night)",
        r"yesterday",
        r"today",
        r"(早上|上午|中午|下午|傍晚|晚上|凌晨)",
    ):
        m = re.search(pat, t, re.I)
        if m:
            return re.sub(r"\s+", " ", m.group(0)).strip()[:120], 0.75
    return "", 0.0


def extract_location_text(text: str) -> tuple[str, float]:
    t = str(text or "")
    city = re.search(
        r"\b(San Jose|Los Angeles|Oakland|Fremont|Cupertino|Sunnyvale|Milpitas|"
        r"Mountain View|Palo Alto|Santa Clara|Irvine|San Francisco)\b"
        r"[^，。；;\n]{0,30}",
        t,
        re.I,
    )
    if city:
        return re.sub(r"\s+", " ", city.group(0)).strip(" ，。;；")[:200], 0.8
    parking = re.search(
        r"([^，。；;\n]{0,16}(高速公路|路口|停车场|停车库|parking lot|freeway|intersection)[^，。；;\n]{0,16})",
        t,
        re.I,
    )
    if parking:
        return re.sub(r"\s+", " ", parking.group(0)).strip(" ，。;；")[:200], 0.7
    at = re.search(r"(?:在|于)\s*([^，。；;\n]{2,40})", t)
    if at:
        return str(at.group(1)).strip()[:200], 0.65
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
            out[key] = str(raw[key]).strip()[:500]
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
