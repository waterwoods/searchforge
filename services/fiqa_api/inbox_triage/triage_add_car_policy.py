"""
Add-car triage policy: next-ask selection and handoff-readiness gating.

Core orchestration and result shape stay in `triage.py`; this module holds
client-evolvable ask order, exceptions (e.g. turn-2 driver path), and
V5/quote_ready contact gates so future client packs can override or branch here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.fiqa_api.inbox_triage.case_draft_engine import (
    evaluate_v5_case_usable,
    min_v5_case_usable_core_met,
)
from services.fiqa_api.inbox_triage.config_loader import get_add_car_rules
from services.fiqa_api.inbox_triage.field_strategy import should_skip_user_prompt_for_missing_field


# PILOT_CONTRACT_ADD_CAR_V1 — contact in-thread gate (≥ this customer turn, quote_ready, etc.)
ADD_CAR_QUOTE_READY_CONTACT_HANDOFF_MIN_CUSTOMER_TURN: int = 4


@dataclass(frozen=True)
class AddCarHandoffReadinessContext:
    """Inputs for add-car handoff gating; future client policies can accept/extend this bundle."""

    handoff: bool
    is_add_car: bool
    for_append: bool
    customer_turn: int
    """1-based index of the current customer message (same as triage's customer_count + 1)."""
    qrs: str
    still_needed: list
    v4_bundle: dict[str, Any] | None
    merged_for_add_car_extraction: str
    primary_vehicle_summary: str | None
    reply_truth_context: dict[str, Any] | None
    variant: str


def add_car_enough_for_handoff(fields: dict[str, bool]) -> bool:
    """Pilot: broker-visible completeness requires VIN + garaging zip + delivery + primary driver.

    Year/make alone must not unlock handoff (operator trust).
    """
    if not fields.get("vin"):
        return False
    if not fields.get("zip"):
        return False
    if not fields.get("delivery"):
        return False
    if not fields.get("driver"):
        return False
    return True


def add_car_near_dense_case_ready(fields: dict[str, bool]) -> bool:
    """VIN + ZIP + vehicle identity (explicit Y/M or VIN) — skip intermediate ladder; one critical ask at a time."""
    if not fields.get("vin") or not fields.get("zip"):
        return False
    vehicle_ok = (fields.get("year") and fields.get("model")) or fields.get("vin")
    return bool(vehicle_ok)


def get_next_ask_for_add_car(
    merged_text: str,
    fields: dict[str, bool],
    language: str,
    add_car_rules: dict[str, dict[str, str]] | None = None,
    customer_turn_count: int = 0,
    client_id: str | None = None,
    questioning_variant: str = "A",
) -> str | None:
    """Return the next most useful ask for add-car, or None if we should hand off.
    Ask order: vehicle (year+model) first when missing, then zip, then delivery/driver.
    When VIN+ZIP+dense identity (near one-shot), ask one critical slot at a time (delivery before driver).
    Adds acknowledgement of what customer just said for office-natural flow.
    Uses add_car_rules from config when not overridden.
    TOP_COMMERCIAL_DEEPENING: when we have delivery but not driver at turn 2 only,
    ask for driver to allow one more turn for corrections (LC-AC3: 我刚才说错了，是我老婆开那辆)."""
    # Late import: triage owns conversation helpers; avoids import cycles with triage.py.
    from services.fiqa_api.inbox_triage.triage import (  # noqa: PLC0415
        _ack_prefix_for_next_ask,
        _extract_primary_add_car_vehicle_concrete,
        _get_add_car_acknowledgement,
        _get_prospective_send_materials_lead,
        _is_prospective_send_offer_message,
        _last_labeled_customer_content,
        _maybe_append_add_car_price_caveat,
    )
    from services.fiqa_api.inbox_triage.date_normalization import (  # noqa: PLC0415
        focused_ask_for_delivery_date,
        normalize_delivery_date_or_flag,
    )

    if add_car_enough_for_handoff(fields):
        # One more ask at turn 2 only when delivery present but driver missing — captures driver corrections
        if (
            customer_turn_count == 2
            and fields.get("delivery")
            and not fields.get("driver")
        ):
            last_seg_raw = _last_labeled_customer_content(merged_text or "")
            last_customer = last_seg_raw.lower()
            # HANDOFF_TIMING_AUDIT: When customer asks document clarification (garaging, dec page) in same
            # turn as add-car info, answer the question and hand off — don't ask for driver.
            # ADD_CAR_QUOTE_EXCELLENCE: Same for coverage-adjust question — answer and hand off.
            # ADD_CAR_COMMERCIAL_FLOW_HARDENING: When customer says materials sent (发你微信了), hand off
            # — don't ask for driver; broker will verify materials and run quote.
            doc_clarification = any(
                m in last_customer
                for m in (
                    "garaging", "garaging proof", "declaration page", "dec page",
                    "是什么意思", "是什么", "要发什么", "what does", "what is",
                )
            )
            coverage_question = any(
                m in last_customer for m in ("coverage 可以调", "coverage 可以调吗", "coverage 能调", "顺便 coverage", "coverage 能改", "coverage adjust")
            )
            # Substring "发你" matches "要不要发你" — exclude prospective-send questions (PROSPECTIVE_SEND_AWARE_REPLY_POLISH).
            materials_sent = not _is_prospective_send_offer_message(
                last_customer
            ) and any(
                m in last_customer for m in ("发你", "发我", "sent", "发你微信", "发我微信", "发过了", "又发")
            )
            if doc_clarification or coverage_question or materials_sent:
                return None
            rules = add_car_rules or get_add_car_rules()
            ack = _get_add_car_acknowledgement(last_seg_raw, fields, language, merged_text)
            prefix = _ack_prefix_for_next_ask(ack, language)
            ps_lead = _get_prospective_send_materials_lead(last_seg_raw, language, client_id)
            if ps_lead:
                prefix = ps_lead + prefix
            ask = rules.get("ask_driver_only", {}).get(language) or (
                "主要驾驶人发我一下，我好安排报价。"
                if language == "zh"
                else "Send me the main driver so I can prepare the quote."
            )
            return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)
        return None
    rules = add_car_rules or get_add_car_rules()
    last_customer = _last_labeled_customer_content(merged_text or "")
    ps_lead = _get_prospective_send_materials_lead(last_customer, language, client_id)
    ack = _get_add_car_acknowledgement(last_customer, fields, language, merged_text)
    prefix = _ack_prefix_for_next_ask(ack, language)
    if ps_lead:
        prefix = ps_lead + prefix

    _iso_d, _dmode = normalize_delivery_date_or_flag(last_customer)
    if not fields.get("delivery") and _dmode == "ask_exact":
        return _maybe_append_add_car_price_caveat(
            merged_text,
            prefix + focused_ask_for_delivery_date(language),
            language,
            client_id,
        )

    vehicle_ok = (fields.get("year") and fields.get("model")) or fields.get("vin")
    if not vehicle_ok:
        pvc_for_confirm = (_extract_primary_add_car_vehicle_concrete(merged_text) or "").strip()
        qv = (questioning_variant or "A").strip().upper()
        if qv == "C" and pvc_for_confirm:
            ask = (
                f"我先按「{pvc_for_confirm}」理解这台车，对吗？不对请发年份+车型或 VIN。"
                if language == "zh"
                else f"Confirming the vehicle as «{pvc_for_confirm}»—reply OK or send year/make or VIN if wrong."
            )
        else:
            ask = rules.get("ask_vehicle", {}).get(language) or (
                "先把年份和车型发我，我就能继续帮您报价。"
                if language == "zh"
                else "Send me the year and make/model first so I can run the quote."
            )
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)
    # Multi-slot jump: ≥2 pilot-critical literals (VIN + ZIP) → skip year/make chat nag; office may still list ym.
    _skip_year_make_after_vin_zip = (
        fields.get("vin")
        and fields.get("zip")
        and (not fields.get("year") or not fields.get("model"))
    )
    if (
        not _skip_year_make_after_vin_zip
        and fields.get("vin")
        and (not fields.get("year") or not fields.get("model"))
    ):
        if not fields.get("year") and not fields.get("model"):
            ask = (
                "VIN 已收到。还请补一下年份和车型，方便办公室核对。"
                if language == "zh"
                else "Got the VIN—please send the year and make/model for our office records."
            )
        elif not fields.get("year"):
            ask = "再发一下车辆年份。" if language == "zh" else "Please send the vehicle year."
        else:
            ask = "再发一下车型（品牌/型号）。" if language == "zh" else "Please send the make and model."
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)
    if not fields.get("zip"):
        ask = rules.get("ask_zip", {}).get(language) or (
            "先把邮编发我，我就能继续帮您报价。"
            if language == "zh"
            else "Send me the zip or address first and I will run the quote."
        )
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)

    _near_dense = add_car_near_dense_case_ready(fields)

    # Exactly one of delivery / driver missing — ask that slot only (avoids silent None after combined branch).
    if not fields.get("delivery") and fields.get("driver"):
        ask = rules.get("ask_delivery_only", {}).get(language) or (
            "提车日期发我一下（或生效日），我好安排报价。"
            if language == "zh"
            else "Send the delivery or effective date so I can prepare the quote."
        )
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)
    if not fields.get("driver") and fields.get("delivery"):
        ask = rules.get("ask_driver_only", {}).get(language) or (
            "主要驾驶人发我一下，我好安排报价。"
            if language == "zh"
            else "Send me the main driver so I can prepare the quote."
        )
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)

    if not fields.get("delivery") and not fields.get("driver"):
        if _near_dense:
            ask = rules.get("ask_delivery_only", {}).get(language) or (
                "提车日期发我一下（或生效日），我好安排报价。"
                if language == "zh"
                else "Send the delivery or effective date so I can prepare the quote."
            )
        else:
            ask = rules.get("ask_delivery_driver", {}).get(language) or (
                "提车日期和主要驾驶人发我一下，我好安排报价。"
                if language == "zh"
                else "Send me the delivery date and main driver so I can prepare the quote."
            )
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)
    if not fields.get("vin"):
        # PTD §9: defer_to_broker — do not extend the chat interview for VIN when strategy defers.
        if should_skip_user_prompt_for_missing_field("vin"):
            return None
        ask = rules.get("ask_vin", {}).get(language) or (
            "VIN（17位车架号）发我一下，我好让办公室出正式报价。"
            if language == "zh"
            else "Send the 17-digit VIN when you have it so we can run the formal quote."
        )
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)
    return None


def apply_add_car_handoff_readiness_gates(
    ctx: AddCarHandoffReadinessContext,
) -> bool:
    """V5 / pilot gates on add-car handoff: structural usability, pre-quote bar, and contact tail."""
    h = ctx.handoff
    if h and ctx.is_add_car and ctx.v4_bundle is not None:
        _vu, _, _ = evaluate_v5_case_usable(
            ctx.v4_bundle,
            merged_text=ctx.merged_for_add_car_extraction,
            primary_vehicle_summary=ctx.primary_vehicle_summary,
            variant=ctx.variant,
        )
        if not _vu:
            h = False
        elif (
            not ctx.for_append
            and ctx.customer_turn >= 2
            and ctx.qrs != "quote_ready"
            and any(
                x in {str(f).lower() for f in (ctx.still_needed or [])}
                for x in ("primary_driver", "vin")
            )
            and not min_v5_case_usable_core_met(
                list(ctx.v4_bundle.get("collected_fields") or []),
                list(ctx.v4_bundle.get("still_needed_fields") or []),
                merged_text=ctx.merged_for_add_car_extraction,
                primary_vehicle_summary=ctx.primary_vehicle_summary,
            )
        ):
            # Pre-quote handoff: require VIN + primary_driver unless min-core (VIN+ZIP+(delivery|driver)) is satisfied.
            h = False

    # PILOT_CONTRACT_ADD_CAR_V1 §4.2: from customer turn ≥4, quote_ready but name/phone still
    # missing in-thread → handoff_ready false (collecting) unless post-submit / on-record contact.
    if (
        h
        and ctx.is_add_car
        and not ctx.for_append
        and ctx.customer_turn >= ADD_CAR_QUOTE_READY_CONTACT_HANDOFF_MIN_CUSTOMER_TURN
        and ctx.qrs == "quote_ready"
    ):
        _gate_ctx = ctx.reply_truth_context or {}
        _post_submit_ex = bool(str(_gate_ctx.get("formal_submitted_at") or "").strip())
        _record_contact_ex = bool(
            str(_gate_ctx.get("record_contact_name") or "").strip()
            or str(_gate_ctx.get("record_contact_phone") or "").strip()
        )
        if not _post_submit_ex and not _record_contact_ex:
            _still_gate = {str(x).lower() for x in (ctx.still_needed or [])}
            if "name" in _still_gate or "phone" in _still_gate:
                h = False

    return h
