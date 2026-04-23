"""
Select logical template family ids for the hot-swappable reply template layer.

Policy here is wording routing only. Engine/triage still decide category, handoff, slots, and
follow_up_type; this module only maps those facts to stable string ids consumed by
reply_template_composer.
"""

from __future__ import annotations

from typing import Any


# Missing document — customer said materials were already sent (reassure-first path)
FAMILY_MISSING_DOC_ALREADY_SENT_WITH_ITEM = "missing_doc.already_sent_with_item"
FAMILY_MISSING_DOC_ALREADY_SENT_NO_ITEM = "missing_doc.already_sent_no_item"


# Add-car quote intake — one clear next field (progressive ask)
FAMILY_ADD_CAR_ASK_ZIP = "add_car.collecting.ask_zip"
FAMILY_ADD_CAR_ASK_DRIVER_ONLY = "add_car.collecting.ask_driver_only"
FAMILY_ADD_CAR_ASK_DELIVERY_DRIVER = "add_car.collecting.ask_delivery_driver"
FAMILY_ADD_CAR_ASK_YEAR_AND_ZIP = "add_car.collecting.ask_year_and_zip"
FAMILY_ADD_CAR_ASK_MODEL_AND_ZIP = "add_car.collecting.ask_model_and_zip"
FAMILY_ADD_CAR_ASK_VEHICLE = "add_car.collecting.ask_vehicle"
FAMILY_ADD_CAR_ASK_FULL = "add_car.collecting.ask_full"


# Handoff — non-add-car correction acknowledged (optional overlay on other_corrected)
FAMILY_HANDOFF_CORRECTION_ACK = "handoff.correction_ack"


def select_missing_doc_already_sent_family_id(*, has_item: bool) -> str:
    """Which template family to use for missing_document when the lead is 'already sent'."""
    return FAMILY_MISSING_DOC_ALREADY_SENT_WITH_ITEM if has_item else FAMILY_MISSING_DOC_ALREADY_SENT_NO_ITEM


def select_add_car_collecting_family_id(fields: dict[str, Any]) -> str:
    """
    Map add-car slot booleans to one progressive-ask family. Mirrors triage._build_client_reply_draft
    customer_question / add-vehicle branch order (no policy change).
    """
    year = bool(fields.get("year"))
    model = bool(fields.get("model"))
    vehicle_ok = (year and model) or bool(fields.get("vin"))
    if vehicle_ok and not fields.get("zip"):
        return FAMILY_ADD_CAR_ASK_ZIP
    if vehicle_ok and fields.get("zip") and fields.get("delivery") and not fields.get("driver"):
        return FAMILY_ADD_CAR_ASK_DRIVER_ONLY
    if vehicle_ok and fields.get("zip") and not fields.get("delivery") and not fields.get("driver"):
        return FAMILY_ADD_CAR_ASK_DELIVERY_DRIVER
    if fields.get("model") and not vehicle_ok:
        return FAMILY_ADD_CAR_ASK_YEAR_AND_ZIP
    if year and not model:
        return FAMILY_ADD_CAR_ASK_MODEL_AND_ZIP
    if not vehicle_ok:
        return FAMILY_ADD_CAR_ASK_VEHICLE
    return FAMILY_ADD_CAR_ASK_FULL


_URGENCY_NEXT_MARKERS = (
    "最要紧",
    "先干嘛",
    "先看什么",
    "办公室先看什么",
    "what matters most",
    "what should i do",
    "is this urgent",
    "是不是今天",
    "一定要处理",
)


def other_corrected_urgency_uses_stitched_line(
    issue_category: str,
    last_customer_lower: str,
) -> bool:
    """If True, handoff uses stitched payment/cancel urgency copy instead of the generic correction ack."""
    if issue_category not in ("payment_lapse_expiration", "cancellation_warning"):
        return False
    return any(m in last_customer_lower for m in _URGENCY_NEXT_MARKERS)
