"""P16 broker packet blob for durable case reopen (structured_payload.p16_broker_packet)."""

from __future__ import annotations

from typing import Any


def map_add_car_readiness(
    *,
    still_needed: list[str] | None,
    warnings: list[str] | None,
    quote_ready_status: str | None = None,
) -> str:
    """ADR-001 office-facing readiness from add-car triage signals."""
    missing = still_needed or []
    has_conflict = any("Multiple VINs" in w for w in (warnings or []))
    if missing:
        return "NEED_INFO"
    if has_conflict or quote_ready_status == "almost_ready":
        return "BROKER_REVIEW"
    return "READY"


def _packet_field_str(packet: dict, key: str) -> str:
    raw = packet.get(key)
    if isinstance(raw, dict):
        return str(raw.get("value") or "").strip()
    return str(raw or "").strip()


def derive_add_car_field_gaps(packet: dict, *, garaging_zip: str = "") -> tuple[list[str], list[str]]:
    """Return (collected_fields, still_needed_fields) from a materialized packet."""
    vin_val = _packet_field_str(packet, "vin")
    year_val = _packet_field_str(packet, "year")
    make_val = _packet_field_str(packet, "make")
    model_val = _packet_field_str(packet, "model")
    zip_val = (garaging_zip or _packet_field_str(packet, "garaging_zip")).strip()

    missing: list[str] = []
    if not vin_val:
        missing.append("vin")
    if not year_val:
        missing.append("year")
    if not make_val or not model_val:
        missing.append("make_model")
    if not zip_val:
        missing.append("zip")

    collected = [f for f in ("vin", "year", "make_model", "zip") if f not in missing]
    return collected, missing


def map_policy_review_readiness(readiness: str) -> str:
    """Map policy_review lane readiness to ADR-001 office labels."""
    r = (readiness or "").strip().lower()
    if r == "ready":
        return "READY"
    if r == "broker_review":
        return "BROKER_REVIEW"
    return "NEED_INFO"


def _packet_field_value(packet: dict, key: str) -> str:
    raw = packet.get(key)
    if isinstance(raw, dict):
        return str(raw.get("value") or "").strip()
    return str(raw or "").strip()


def build_portal_copy_text_add_car(
    *,
    packet: dict,
    warnings: list[str] | None,
    request_type: str,
    broker_next_step: str = "",
) -> str:
    """Compact label:value block for AMS / carrier portal paste."""
    lines = [
        "Customer Name: " + (_packet_field_value(packet, "customer_name") or "—"),
        "Phone: " + (_packet_field_value(packet, "phone") or "—"),
        "Garaging ZIP: " + (_packet_field_value(packet, "garaging_zip") or "—"),
    ]
    if request_type == "replace_vehicle":
        lines.append("Request: Replace Vehicle")
        ov = _packet_field_value(packet, "old_vehicle_vin")
        op = _packet_field_value(packet, "old_vehicle_plate")
        if ov or op:
            lines.append(f"Old Vehicle: VIN {ov or '—'} · Plate {op or '—'}")
    else:
        lines.append("Request: Add Vehicle")
    vin = _packet_field_value(packet, "vin")
    ymm = " ".join(
        filter(
            None,
            [
                _packet_field_value(packet, "year"),
                _packet_field_value(packet, "make"),
                _packet_field_value(packet, "model"),
            ],
        )
    )
    if vin or ymm:
        lines.append(f"Vehicle 1: {ymm} VIN {vin or '—'}".strip())
    pd = _packet_field_value(packet, "primary_driver")
    if pd:
        lines.append(f"Driver 1: {pd}")
    eff = _packet_field_value(packet, "effective_date") or _packet_field_value(packet, "delivery_date")
    if eff:
        lines.append(f"Effective Date: {eff}")
    lien = _packet_field_value(packet, "finance_or_lienholder")
    if lien:
        lines.append(f"Lienholder: {lien}")
    if warnings:
        lines.append("Warnings: " + "; ".join(warnings[:5]))
    if broker_next_step:
        lines.append(f"Next Action: {broker_next_step}")
    return "\n".join(lines)


def build_portal_copy_text_policy_review(
    *,
    packet: dict,
    vehicles: list[dict] | None,
    drivers: list[dict] | None,
    broker_next_action: dict[str, str] | None = None,
) -> str:
    """Compact label:value block for policy review lane."""
    term_start = _packet_field_value(packet, "policy_term_start")
    term_end = _packet_field_value(packet, "policy_term_end")
    term = f"{term_start} – {term_end}".strip(" –") if term_start or term_end else "—"
    premium = _packet_field_value(packet, "premium_amount")
    period = _packet_field_value(packet, "premium_period")
    if premium and period:
        premium = f"{premium} / {period}"
    lines = [
        "Customer Name: " + (_packet_field_value(packet, "customer_name") or "—"),
        "Phone: " + (_packet_field_value(packet, "phone") or "—"),
        "Garaging ZIP: " + (_packet_field_value(packet, "garaging_zip") or "—"),
        "Carrier: " + (_packet_field_value(packet, "current_carrier") or "—"),
        "Policy Number: " + (_packet_field_value(packet, "policy_number") or "—"),
        f"Policy Term: {term}",
        f"Premium: {premium or '—'}",
    ]
    cov_parts = []
    for label, key in (
        ("BI", "bodily_injury"),
        ("PD", "property_damage"),
        ("UM", "uninsured_motorist"),
    ):
        v = _packet_field_value(packet, key)
        if v:
            cov_parts.append(f"{label} {v}")
    comp = _packet_field_value(packet, "comprehensive_deductible")
    coll = _packet_field_value(packet, "collision_deductible")
    if comp:
        cov_parts.append(f"Comp ded {comp}")
    if coll:
        cov_parts.append(f"Coll ded {coll}")
    if cov_parts:
        lines.append("Coverage: " + ", ".join(cov_parts))
    for i, v in enumerate(vehicles or [], 1):
        ymm = " ".join(filter(None, [v.get("year"), v.get("make"), v.get("model")]))
        vin = str(v.get("vin") or "").strip()
        lines.append(f"Vehicle {i}: {ymm} VIN {vin or '—'}".strip())
    from services.fiqa_api.policy_review.trust_checks import format_portal_driver_line

    for i, d in enumerate(drivers or [], 1):
        lines.append(format_portal_driver_line(d, i))
    action = (broker_next_action or {}).get("en") or ""
    if action:
        lines.append(f"Next Action: {action}")
    return "\n".join(lines)


def build_p16_broker_packet_blob(
    *,
    request_type: str,
    readiness_status: str,
    packet: dict | None = None,
    vehicles: list[dict] | None = None,
    drivers: list[dict] | None = None,
    copy_text: str = "",
    portal_copy_text: str = "",
    opportunity_signals: list[dict] | None = None,
    broker_next_action: dict[str, str] | None = None,
    follow_up_message_zh: str = "",
    sources: list[dict] | None = None,
    warnings: list[str] | None = None,
    document_types_detected: list[str] | None = None,
    mock_mode: bool = False,
) -> dict[str, Any]:
    """Single JSON blob stored on the case for broker inbox reopen."""
    return {
        "request_type": request_type,
        "readiness_status": readiness_status,
        "packet": packet or {},
        "vehicles": vehicles or [],
        "drivers": drivers or [],
        "copy_text": copy_text,
        "portal_copy_text": portal_copy_text,
        "opportunity_signals": opportunity_signals or [],
        "broker_next_action": broker_next_action or {},
        "follow_up_message_zh": follow_up_message_zh,
        "sources": sources or [],
        "warnings": warnings or [],
        "document_types_detected": document_types_detected or [],
        "mock_mode": bool(mock_mode),
    }
