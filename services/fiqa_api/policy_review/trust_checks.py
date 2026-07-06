"""
Post-extraction trust checks for Policy Review — name verification and portal labels.

Principle: better empty than wrong; mark uncertain OCR fields for broker confirmation.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

_NAME_VERIFY_WARNING = "Driver / insured name may need verification."
_RELATIONSHIP_VERIFY_WARNING = "Relationship needs verification."
_NAME_CONFLICT_WARNING = "Possible name conflict — extracted driver/insured name differs from intake customer name."

# OCR relationship strings that may appear as broker-facing portal labels.
_APPROVED_RELATIONSHIP_LABELS: dict[str, str] = {
    "named insured": "Named Insured",
    "insured": "Named Insured",
    "policyholder": "Named Insured",
    "primary insured": "Named Insured",
    "driver": "Driver",
    "listed driver": "Driver",
    "additional driver": "Additional Driver",
    "other driver": "Additional Driver",
}

_CLOSE_MATCH_RATIO = 0.82
_EXACT_MATCH_RATIO = 0.97


def _normalize_name(name: str) -> str:
    cleaned = re.sub(r"[^\w\s]", "", (name or "").lower())
    return " ".join(cleaned.split())


def _name_similarity(a: str, b: str) -> float:
    na, nb = _normalize_name(a), _normalize_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


def _classify_name_match(customer_name: str, driver_name: str) -> str:
    """Returns match | close | mismatch."""
    if not _normalize_name(customer_name) or not _normalize_name(driver_name):
        return "match"
    ratio = _name_similarity(customer_name, driver_name)
    if ratio >= _EXACT_MATCH_RATIO:
        return "match"
    if ratio >= _CLOSE_MATCH_RATIO:
        return "close"
    return "mismatch"


def portal_label_for_driver(relationship: str, index: int) -> tuple[str, bool]:
    """
    Map OCR relationship to a safe broker-facing portal label.
    Returns (label, relationship_needs_verification).
    """
    rel = (relationship or "").strip()
    if not rel:
        return f"Driver {index}", False
    mapped = _APPROVED_RELATIONSHIP_LABELS.get(rel.lower())
    if mapped:
        return mapped, False
    return f"Driver {index}", True


def format_portal_driver_line(driver: dict[str, Any], index: int) -> str:
    """Single driver line for Copy Portal Format."""
    label = str(driver.get("portal_label") or f"Driver {index}").strip()
    name = str(driver.get("name") or "").strip()
    if driver.get("needs_verification"):
        if name:
            return f"{label}: {name} (verify)"
        return f"{label}: Needs verification"
    return f"{label}: {name or '—'}"


def _append_warning(warnings: list[str], message: str) -> None:
    if message not in warnings:
        warnings.append(message)


def apply_trust_checks(
    customer_name: str,
    drivers: list[dict[str, Any]],
    warnings: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Annotate drivers with trust metadata and append verification warnings.
    Does not mutate OCR values — only adds flags and safe portal labels.
    """
    out_warnings = list(warnings or [])
    annotated: list[dict[str, Any]] = []

    for i, driver in enumerate(drivers, 1):
        entry = dict(driver)
        rel = str(entry.get("relationship") or "").strip()
        portal_label, rel_needs_verify = portal_label_for_driver(rel, i)
        entry["portal_label"] = portal_label
        if rel_needs_verify and rel:
            entry["relationship_needs_verification"] = True
            _append_warning(out_warnings, _RELATIONSHIP_VERIFY_WARNING)

        driver_name = str(entry.get("name") or "").strip()
        if driver_name and customer_name.strip():
            match_kind = _classify_name_match(customer_name, driver_name)
            if match_kind == "close":
                entry["needs_verification"] = True
                _append_warning(out_warnings, _NAME_VERIFY_WARNING)
            elif match_kind == "mismatch":
                entry["needs_verification"] = True
                entry["possible_name_conflict"] = True
                _append_warning(out_warnings, _NAME_VERIFY_WARNING)
                _append_warning(out_warnings, _NAME_CONFLICT_WARNING)

        annotated.append(entry)

    return annotated, out_warnings
