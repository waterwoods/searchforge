"""
Deterministic Intake Engine skeleton (field-driven state) — additive; triage remains authoritative for routing.

See docs/CASE_CONTRACT_V1.md and configs/common/add_car_stage1_field_contract.json.
"""

from __future__ import annotations

from typing import Any, TypedDict

from services.fiqa_api.inbox_triage.add_car_field_contract import (
    dedupe_preserve_order,
    label_zh,
    quote_ready_matches_still_needed,
)
from services.fiqa_api.inbox_triage.case_lifecycle import _derive_case_lifecycle

# First ask order: structural gaps before contact tail
_NEXT_ASK_ORDER: tuple[str, ...] = (
    "year",
    "make_model",
    "vin",
    "zip",
    "delivery_date",
    "primary_driver",
    "name",
    "phone",
)


class IntakeState(TypedDict):
    collected_fields: list[str]
    still_needed_fields: list[str]
    quote_ready_status: str
    case_lifecycle: str
    handoff_ready: bool


def compute_fields(
    triage_result: dict[str, Any],
    _persisted: dict[str, Any] | None,
) -> tuple[list[str], list[str]]:
    """
    Returns collected_fields, still_needed_fields.
    Triage already ran _add_car_structured_fields and _reconcile_add_car_lists_with_persisted_record
    (including correction overrides). Re-applying reconcile here without the same override can corrupt
    correction turns — use final triage lists as-is.
    """
    collected = dedupe_preserve_order(list(triage_result.get("collected_fields") or []))
    still = dedupe_preserve_order(list(triage_result.get("still_needed_fields") or []))
    return collected, still


def compute_quote_state(_collected_fields: list[str], still_needed_fields: list[str]) -> str:
    """
    Aligns with add_car_field_contract.quote_ready_matches_still_needed and pilot _add_car_quote_ready_status.
    VIN alone yields almost_ready (year/make may stay in still_needed for operator-visible gaps).
    """
    sn = {str(x).lower() for x in still_needed_fields if x}
    coll = {str(x).lower() for x in _collected_fields if x}
    if "vin" in sn:
        return "need_more"
    has_vin = "vin" in coll and "vin" not in sn
    if has_vin:
        pilot_gap = sn & {"zip", "delivery_date", "primary_driver"}
        if not pilot_gap:
            return "quote_ready"
        return "almost_ready"
    if "year" in sn and "make_model" in sn:
        return "need_more"
    pilot_gap = sn & {"zip", "delivery_date", "primary_driver"}
    if pilot_gap:
        return "almost_ready"
    return "quote_ready"


def compute_case_lifecycle(result: dict[str, Any]) -> str:
    return _derive_case_lifecycle(result)


def compute_handoff_ready(result: dict[str, Any]) -> bool:
    return bool(result.get("handoff_ready", False))


def _infer_language_for_next_ask(result: dict[str, Any]) -> str:
    from services.fiqa_api.inbox_triage.triage import _detect_client_language

    blob = " ".join(
        str(x)
        for x in (
            result.get("conversation_summary"),
            result.get("client_reply_draft"),
            result.get("next_best_question"),
        )
        if x
    )
    return _detect_client_language(blob or "[客户] hi")


def compute_next_step(still_needed_fields: list[str], *, language: str | None = None) -> str:
    if not still_needed_fields:
        return ""
    lang = language or "zh"
    order_index = {k: i for i, k in enumerate(_NEXT_ASK_ORDER)}
    still_norm = [str(x) for x in still_needed_fields if x]

    def _sort_key(fid: str) -> tuple[int, int]:
        fl = fid.lower()
        if fl in order_index:
            return (0, order_index[fl])
        return (1, 0)

    first = min(still_norm, key=_sort_key)
    fl = first.lower()
    lab_zh = label_zh(fl)
    if lang == "zh" and lab_zh:
        return f"请提供{lab_zh}。"
    if lang == "zh":
        return f"请提供{first}。"
    readable = lab_zh or first.replace("_", " ")
    return f"Please provide your {readable}."


def assert_state_consistency(result: dict[str, Any]) -> None:
    qrs = str(result.get("quote_ready_status") or "").strip()
    still = result.get("still_needed_fields")
    if str(result.get("service_type") or "").strip().lower() != "add_car":
        return
    assert quote_ready_matches_still_needed(qrs, still), (
        f"quote_ready_status={qrs!r} inconsistent with still_needed_fields={still!r}"
    )


def run_intake_engine(
    result: dict[str, Any],
    persisted: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Central state computation. Does not remove legacy keys. Reads final triage lists (post broker_next_step)."""
    collected, still = compute_fields(result, persisted)
    result["collected_fields"] = collected
    result["still_needed_fields"] = still

    if str(result.get("service_type") or "").strip().lower() == "add_car":
        result["quote_ready_status"] = compute_quote_state(collected, still)

    handoff = compute_handoff_ready(result)
    result["case_lifecycle"] = compute_case_lifecycle(result)

    lang = _infer_language_for_next_ask(result)
    next_step = compute_next_step(still, language=lang)
    result["intake_next_best_ask"] = next_step

    assert_state_consistency(result)
    return result
