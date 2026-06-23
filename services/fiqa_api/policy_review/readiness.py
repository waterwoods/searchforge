"""
Policy Review readiness rules, opportunity signals, and Chinese follow-up.
Uses only ADR-001 states: ready | needs_info | broker_review.
"""

from __future__ import annotations

from typing import Any

DECLARATION_TYPES = frozenset({"declaration_page", "policy_pdf", "renewal_notice"})
PARTIAL_DOC_TYPES = frozenset({"insurance_card", "premium_screenshot"})

SIGNAL_REQUOTE = "REQUOTE_RECOMMENDED"
SIGNAL_VIOLATION = "VIOLATION_PRESENT"
SIGNAL_FOLLOW_UP = "FOLLOW_UP_REQUIRED"
SIGNAL_CROSS_SELL = "CROSS_SELL_OPPORTUNITY"
SIGNAL_NO_OVERPROMISE = "DO_NOT_OVERPROMISE"

SIGNAL_MEANINGS = {
    SIGNAL_REQUOTE: "Policy appears complete enough for broker to manually re-shop.",
    SIGNAL_VIOLATION: "Document shows violation / accident / surcharge indicator, or driver record issue if explicitly visible.",
    SIGNAL_FOLLOW_UP: "Missing declaration page, premium, vehicles, drivers, or coverage.",
    SIGNAL_CROSS_SELL: "Evidence suggests home/umbrella/multi-policy, multiple vehicles, high liability limits, or home-related clue.",
    SIGNAL_NO_OVERPROMISE: "Visible risk factor such as violation, unclear coverage, or incomplete data; broker should explain before promising savings.",
}


def _val(fields: dict, key: str) -> str:
    return str((fields.get(key) or {}).get("value") or "").strip()


def _has_coverage_enough(fields: dict) -> bool:
    coverage_keys = (
        "bodily_injury",
        "property_damage",
        "uninsured_motorist",
        "comprehensive_deductible",
        "collision_deductible",
    )
    present = sum(1 for k in coverage_keys if _val(fields, k))
    return present >= 2


def _vehicle_present(vehicles: list[dict]) -> bool:
    for v in vehicles:
        if v.get("vin") or (v.get("year") and v.get("make")):
            return True
    return False


def _has_declaration_page(document_types: list[str]) -> bool:
    return any(t in DECLARATION_TYPES for t in document_types)


def _only_partial_docs(document_types: list[str]) -> bool:
    if not document_types:
        return True
    return not _has_declaration_page(document_types) and all(
        t in PARTIAL_DOC_TYPES or t in {"unknown", "mixed", "unrelated"} for t in document_types
    )


def _violation_visible(drivers: list[dict], warnings: list[str]) -> bool:
    for d in drivers:
        note = str(d.get("visible_violation_or_accident") or "").strip().lower()
        if note and note not in {"false", "no", "none", "n/a"}:
            return True
    blob = " ".join(warnings).lower()
    return any(w in blob for w in ("violation", "accident", "surcharge", "sr-22", "sr22"))


def _unclear_coverage(fields: dict, extraction_notes: list[str]) -> bool:
    if _has_coverage_enough(fields):
        return False
    notes = " ".join(extraction_notes).lower()
    return "unclear" in notes or "insurance card alone" in notes


def compute_readiness(
    fields: dict,
    vehicles: list[dict],
    document_types: list[str],
    warnings: list[str],
    conflicts: list[dict],
    extraction_notes: list[str],
) -> tuple[str, list[str]]:
    """
    Returns (readiness_status, internal_reasons).
    """
    reasons: list[str] = []
    carrier = _val(fields, "current_carrier")
    premium = _val(fields, "premium_amount")
    has_vehicle = _vehicle_present(vehicles)
    has_coverage = _has_coverage_enough(fields)
    has_dec = _has_declaration_page(document_types)

    if conflicts or any("Conflicting" in w for w in warnings):
        reasons.append("conflicting_documents")
        return "broker_review", reasons

    if _unclear_coverage(fields, extraction_notes) and carrier and premium:
        reasons.append("unclear_coverage")
        return "broker_review", reasons

    missing_critical: list[str] = []
    if not carrier:
        missing_critical.append("carrier")
    if not premium:
        missing_critical.append("premium")
    if not has_vehicle:
        missing_critical.append("vehicles")
    if not has_dec and _only_partial_docs(document_types):
        missing_critical.append("declaration_page")
    if missing_critical:
        reasons.extend(missing_critical)
        return "needs_info", reasons

    if not has_coverage:
        reasons.append("coverage")
        return "needs_info", reasons

    return "ready", reasons


def build_opportunity_signals(
    readiness: str,
    fields: dict,
    vehicles: list[dict],
    drivers: list[dict],
    warnings: list[str],
    cross_sell_clues: list[str],
    extraction_notes: list[str],
) -> list[dict[str, str]]:
    signals: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(code: str) -> None:
        if code in seen:
            return
        seen.add(code)
        signals.append({"code": code, "meaning": SIGNAL_MEANINGS[code]})

    if readiness == "needs_info":
        add(SIGNAL_FOLLOW_UP)
    if readiness == "ready":
        add(SIGNAL_REQUOTE)

    if _violation_visible(drivers, warnings):
        add(SIGNAL_VIOLATION)
        add(SIGNAL_NO_OVERPROMISE)

    if readiness == "broker_review" or _unclear_coverage(fields, extraction_notes):
        add(SIGNAL_NO_OVERPROMISE)

    if len(vehicles) >= 2:
        add(SIGNAL_CROSS_SELL)
    bi = _val(fields, "bodily_injury")
    if bi and any(x in bi.replace("/", "") for x in ("250", "300", "500")):
        add(SIGNAL_CROSS_SELL)
    for clue in cross_sell_clues:
        cl = clue.lower()
        if any(k in cl for k in ("home", "umbrella", "multi-policy", "bundle", "renters", "property")):
            add(SIGNAL_CROSS_SELL)
            break

    return signals


def build_chinese_follow_up(readiness: str, reasons: list[str]) -> str:
    if readiness != "needs_info":
        return ""

    if "declaration_page" in reasons and "premium" not in reasons:
        return (
            "您好，为了帮您检查现在的保费是否有更好的方案，请发一下您当前保单首页 Declaration Page，"
            "最好包含保费、车辆、驾驶员、保额和生效日期。收到后我们可以继续帮您查看，谢谢。"
        )
    if "premium" in reasons and "declaration_page" in reasons:
        return (
            "您好，如果您是因为续保价格上涨想重新比较，请也发一下最新的 Renewal Notice 或保费截图，"
            "这样我们可以更准确地帮您判断是否值得重新报价，谢谢。"
        )
    if "vehicles" in reasons or "coverage" in reasons:
        return (
            "您好，目前资料里还缺少部分车辆或驾驶员信息。请补充车辆信息、驾驶员信息，"
            "或上传完整保单首页，我们收到后继续处理，谢谢。"
        )
    if "carrier" in reasons:
        return (
            "您好，为了帮您检查现在的保费是否有更好的方案，请发一下您当前保单首页 Declaration Page 或续保通知，"
            "最好包含保险公司名称、保费和车辆信息。收到后我们可以继续帮您查看，谢谢。"
        )
    return (
        "您好，为了帮您检查现在的保费是否有更好的方案，请补充保单首页 Declaration Page 或续保通知。"
        "收到后我们可以继续帮您查看，谢谢。"
    )


BROKER_NEXT_ACTION = {
    "ready": {
        "en": "Packet is substantially complete — broker can enter carrier portal for manual re-shop.",
        "zh": "资料基本齐全，可以进入 carrier portal 手动重新比价。",
    },
    "needs_info": {
        "en": "Send the Chinese follow-up below; ask customer for declaration page or renewal notice.",
        "zh": "请先发送下方中文跟进消息，让客户补充保单首页或续保通知。",
    },
    "broker_review": {
        "en": "Data has conflicts or uncertainty — verify premium, coverage, or violations before re-shopping.",
        "zh": "资料存在不确定或冲突，请先人工核对保费、保额或违章信息，再决定是否比价。",
    },
}
