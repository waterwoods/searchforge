"""Policy Review packet and copy-text builder."""

from __future__ import annotations

from typing import Any


def _fv(field: dict | None) -> str:
    v = str((field or {}).get("value") or "").strip()
    return v if v else "MISSING"


def build_policy_review_packet(
    *,
    customer_name: str,
    phone: str,
    garaging_zip: str,
    merged: dict,
    is_mock: bool = False,
) -> dict:
    """Build frontend-compatible packet + policy_snapshot structure."""
    fields = merged.get("fields") or {}

    def intake(value: str) -> dict:
        return {
            "value": value,
            "confidence": 1.0,
            "confidence_label": "high",
            "source_file": "intake_form",
            "is_mock": False,
        }

    def ext(key: str) -> dict:
        f = fields.get(key) or {}
        if is_mock and not f.get("value"):
            return {
                "value": "",
                "confidence": 0.0,
                "confidence_label": "low",
                "source_file": "MOCK_EXTRACTION_ONLY",
                "is_mock": True,
            }
        return {
            "value": f.get("value") or "",
            "confidence": float(f.get("confidence") or 0.0),
            "confidence_label": f.get("confidence_label") or "low",
            "source_file": f.get("source_file") or "",
            "is_mock": is_mock,
            "needs_confirmation": bool(f.get("needs_confirmation")),
        }

    packet: dict[str, Any] = {
        "customer_name": intake(customer_name),
        "phone": intake(phone),
        "garaging_zip": intake(garaging_zip),
        "current_carrier": ext("current_carrier"),
        "policy_number": ext("policy_number"),
        "policy_term_start": ext("policy_term_start"),
        "policy_term_end": ext("policy_term_end"),
        "premium_amount": ext("premium_amount"),
        "premium_period": ext("premium_period"),
        "bodily_injury": ext("bodily_injury"),
        "property_damage": ext("property_damage"),
        "uninsured_motorist": ext("uninsured_motorist"),
        "comprehensive_deductible": ext("comprehensive_deductible"),
        "collision_deductible": ext("collision_deductible"),
    }

    return {
        "packet": packet,
        "vehicles": merged.get("vehicles") or [],
        "drivers": merged.get("drivers") or [],
        "document_types_detected": merged.get("document_types") or [],
    }


def build_copy_text(
    *,
    packet: dict,
    vehicles: list[dict],
    drivers: list[dict],
    warnings: list[str],
    sources: list[dict],
    opportunity_signals: list[dict],
    broker_next_action: dict[str, str],
    mock_mode: bool,
) -> str:
    mock_label = "\n⚠ MOCK_EXTRACTION_ONLY — No real AI extraction performed.\n" if mock_mode else ""
    warning_lines = "\n".join(f"  ⚠ {w}" for w in warnings) if warnings else "  (none)"
    source_lines = (
        "\n".join(f"  {s['file']} → {s['fields']}" for s in sources) if sources else "  (none)"
    )

    lines = [
        f"{mock_label}Policy Review Packet / 当前保单分析资料包",
        "",
        "1. Customer",
        f"  Name: {_fv(packet.get('customer_name'))}",
        f"  Phone: {_fv(packet.get('phone'))}",
        f"  Garaging ZIP: {_fv(packet.get('garaging_zip'))}",
        "",
        "2. Current Policy",
        f"  Carrier: {_fv(packet.get('current_carrier'))}",
        f"  Policy Number: {_fv(packet.get('policy_number'))}",
        f"  Term Start: {_fv(packet.get('policy_term_start'))}",
        f"  Term End: {_fv(packet.get('policy_term_end'))}",
        "",
        "3. Vehicles",
    ]
    if vehicles:
        for i, v in enumerate(vehicles, 1):
            ymm = " ".join(filter(None, [v.get("year"), v.get("make"), v.get("model")])).strip() or "MISSING"
            lines.append(f"  [{i}] {ymm}")
            lines.append(f"      VIN: {v.get('vin') or 'MISSING'}")
            if v.get("vehicle_premium"):
                lines.append(f"      Vehicle Premium: {v['vehicle_premium']}")
            if v.get("source_file"):
                lines.append(f"      (from: {v['source_file']})")
    else:
        lines.append("  (none extracted)")

    lines.extend(["", "4. Drivers"])
    if drivers:
        for i, d in enumerate(drivers, 1):
            lines.append(f"  [{i}] {d.get('name') or 'MISSING'}")
            if d.get("relationship"):
                lines.append(f"      Relationship: {d['relationship']}")
            if d.get("license_state"):
                lines.append(f"      License State: {d['license_state']}")
            if d.get("visible_violation_or_accident"):
                lines.append(f"      Violation/Accident: {d['visible_violation_or_accident']}")
            if d.get("source_file"):
                lines.append(f"      (from: {d['source_file']})")
    else:
        lines.append("  (none extracted)")

    lines.extend([
        "",
        "5. Coverage",
        f"  Bodily Injury: {_fv(packet.get('bodily_injury'))}",
        f"  Property Damage: {_fv(packet.get('property_damage'))}",
        f"  Uninsured Motorist: {_fv(packet.get('uninsured_motorist'))}",
        f"  Comprehensive Deductible: {_fv(packet.get('comprehensive_deductible'))}",
        f"  Collision Deductible: {_fv(packet.get('collision_deductible'))}",
        "",
        "6. Premium",
        f"  Amount: {_fv(packet.get('premium_amount'))}",
        f"  Period: {_fv(packet.get('premium_period'))}",
        "",
        "7. Opportunity Signals",
    ])
    if opportunity_signals:
        for s in opportunity_signals:
            lines.append(f"  • {s['code']}: {s['meaning']}")
    else:
        lines.append("  (none)")

    lines.extend([
        "",
        "8. Broker Next Action",
        f"  {broker_next_action.get('en', '')}",
        f"  {broker_next_action.get('zh', '')}",
        "",
        "Warnings:",
        warning_lines,
        "",
        "Sources:",
        source_lines,
    ])
    return "\n".join(lines).strip()


def build_sources(packet: dict, vehicles: list[dict], drivers: list[dict], file_names: list[str]) -> list[dict]:
    sources: list[dict] = [{"file": "intake_form", "fields": "customer_name, phone, garaging_zip"}]
    source_map: dict[str, list[str]] = {}
    _synthetic = {"intake_form", "MOCK_EXTRACTION_ONLY"}

    for key, field in packet.items():
        src = (field or {}).get("source_file") or ""
        val = (field or {}).get("value") or ""
        if src and src not in _synthetic and val:
            source_map.setdefault(src, []).append(key)

    for v in vehicles:
        src = v.get("source_file") or ""
        if src:
            source_map.setdefault(src, []).append("vehicle")

    for d in drivers:
        src = d.get("source_file") or ""
        if src:
            source_map.setdefault(src, []).append("driver")

    for src, flds in source_map.items():
        sources.append({"file": src, "fields": ", ".join(sorted(set(flds)))})

    for fn in file_names:
        if fn not in source_map and fn not in {s["file"] for s in sources}:
            sources.append({"file": fn, "fields": "processed"})

    return sources
