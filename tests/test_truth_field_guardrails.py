"""Strict Truth guardrails for Add-Car (Unified Intake)."""

from services.fiqa_api.inbox_triage.triage import (
    _add_car_quote_ready_status,
    _add_car_structured_fields,
    _extract_add_car_fields_truth_safe,
    _get_next_ask_for_add_car,
    triage_conversation,
)


def _blob(line: str) -> str:
    return f"[客户] {line}"


def test_guardrail_case1_vin_later_not_collected():
    collected, still, _, _ = _add_car_structured_fields(_blob("VIN later"))
    assert "vin" not in collected


def test_guardrail_case2_same_as_other_car_blocks_vin_driver_zip():
    collected, still, _, _ = _add_car_structured_fields(_blob("same as my other car"))
    assert "vin" not in collected
    assert "primary_driver" not in collected
    assert "zip" not in collected


def test_guardrail_vin_accepted_after_deferred_then_explicit_vin():
    blob = _blob("VIN later") + "\n\n" + _blob("VIN JTDBR32E220012345")
    collected, still, _, _ = _add_car_structured_fields(blob)
    assert "vin" in collected


def test_guardrail_vin_accepted_after_context_reuse_then_explicit_vin():
    blob = _blob("same as my other car") + "\n\n" + _blob("VIN 4T1BE46K37U123456")
    collected, still, _, _ = _add_car_structured_fields(blob)
    assert "vin" in collected


def test_guardrail_explicit_named_driver_collected():
    collected, still, _, _ = _add_car_structured_fields(_blob("her name is Jane Doe"))
    assert "primary_driver" in collected


def test_guardrail_multi_turn_pilot_sequence():
    """Pre-pilot sequence: context reuse, deferred VIN zh, explicit VIN, zip, driver, date."""
    parts = [
        _blob("same as my other car"),
        _blob("VIN晚点给"),
        _blob("VIN JTDBT9238Y3012345"),
        _blob("zip 91789"),
        _blob("her name is Jane Doe"),
        _blob("start 04/18/2026"),
    ]
    blob = "\n\n".join(parts)
    collected, still, _, _ = _add_car_structured_fields(blob)
    assert "vin" in collected
    assert "zip" in collected
    assert "primary_driver" in collected
    assert "delivery_date" in collected
    fields = _extract_add_car_fields_truth_safe(blob)
    assert _add_car_quote_ready_status(fields) == "quote_ready"
    assert "vin" not in still


def test_guardrail_case3_start_tomorrow_no_delivery_date():
    collected, still, _, _ = _add_car_structured_fields(_blob("start tomorrow"))
    assert "delivery_date" not in collected


def test_guardrail_case4_wife_drives_mostly_no_primary_driver():
    collected, still, _, _ = _add_car_structured_fields(_blob("my wife drives mostly"))
    assert "primary_driver" not in collected


def test_issue1_no_spurious_make_model_from_wife_drives_or_add_car_intent():
    collected, _, _, _ = _add_car_structured_fields(_blob("my wife drives mostly"))
    assert "make_model" not in collected
    collected2, _, _, _ = _add_car_structured_fields(_blob("I want to add a car"))
    assert "make_model" not in collected2
    collected3, _, _, _ = _add_car_structured_fields(_blob("Toyota Corolla"))
    assert "make_model" in collected3


def test_issue2_quote_ready_requires_vin_and_rejects_relative_delivery():
    f = _extract_add_car_fields_truth_safe(
        _blob("2024 Tesla Model Y ZIP 92620 her name is Jane Doe start tomorrow")
    )
    assert _add_car_quote_ready_status(f) == "need_more"
    f2 = _extract_add_car_fields_truth_safe(
        _blob(
            "2024 Tesla Model Y ZIP 92620 her name is Jane Doe start 04/18/2026 "
            "VIN 1HGCM82633A123456"
        )
    )
    assert _add_car_quote_ready_status(f2) == "quote_ready"


def test_issue3_debug_shows_explicit_current_turn_after_defer(monkeypatch):
    monkeypatch.setenv("DEBUG_TRUTH_GUARDRAILS", "1")
    turns = [
        {"role": "customer", "text": "加车 2024 Tesla"},
        {"role": "customer", "text": "VIN later"},
    ]
    out = triage_conversation("VIN JTDBR32E220012345", turns, client_id="chen_kui", reply_truth_context=None)
    dbg = out.get("truth_guardrail_debug") or []
    vin_rows = [x for x in dbg if x.get("field") == "vin"]
    assert len(vin_rows) == 1
    assert vin_rows[0].get("decision") == "accept"
    assert vin_rows[0].get("reason") == "explicit_literal_current_turn"
    assert "vin" in (out.get("collected_fields") or [])


def test_guardrail_case4_zh_wife_drives_more_no_primary_driver():
    collected, still, _, _ = _add_car_structured_fields(_blob("我老婆开得多"))
    assert "primary_driver" not in collected


def test_guardrail_case5_vin_defer_zh():
    collected, still, _, _ = _add_car_structured_fields(_blob("VIN晚点给"))
    assert "vin" not in collected


def test_triage_end_to_end_guardrails_collected_fields():
    turns = [{"role": "customer", "text": "VIN later"}]
    out = triage_conversation("VIN later", turns, client_id="chen_kui", reply_truth_context=None)
    assert "vin" not in (out.get("collected_fields") or [])


def test_debug_truth_guardrails_triage_payload(monkeypatch):
    monkeypatch.setenv("DEBUG_TRUTH_GUARDRAILS", "1")
    # Add-car thread so guardrails run on merged customer text
    turns = [{"role": "customer", "text": "加车 2020 Honda Civic 95131"}]
    out = triage_conversation("VIN晚点给", turns, client_id="chen_kui", reply_truth_context=None)
    assert "vin" not in (out.get("collected_fields") or [])
    dbg = out.get("truth_guardrail_debug") or []
    vin_rows = [x for x in dbg if x.get("field") == "vin"]
    assert len(vin_rows) == 1
    assert vin_rows[0].get("reason") == "deferred_input"
    assert vin_rows[0].get("decision") == "reject"


def test_triage_truth_guardrail_debug_deferred_vin_when_flag_on(monkeypatch):
    monkeypatch.setenv("DEBUG_TRUTH_GUARDRAILS", "1")
    out = triage_conversation(
        "VIN晚点给",
        [{"role": "customer", "text": "加车 报价 2024 Tesla"}],
        client_id="chen_kui",
        reply_truth_context=None,
    )
    dbg = out.get("truth_guardrail_debug") or []
    vin_rows = [r for r in dbg if r.get("field") == "vin"]
    assert len(vin_rows) == 1
    assert vin_rows[0].get("reason") == "deferred_input"
    assert vin_rows[0].get("decision") == "reject"
    assert "vin" not in (out.get("collected_fields") or [])
    assert "truth_guardrail_accepted" in out


def test_triage_truth_guardrail_debug_absent_when_flag_off(monkeypatch):
    monkeypatch.delenv("DEBUG_TRUTH_GUARDRAILS", raising=False)
    out = triage_conversation(
        "VIN晚点给",
        [{"role": "customer", "text": "加车 报价 2024 Tesla"}],
        client_id="chen_kui",
        reply_truth_context=None,
    )
    assert "truth_guardrail_debug" not in out
    assert "truth_guardrail_accepted" not in out


def test_multi_slot_ocr_year_make_truth_ok_image_turn_then_asks_zip_only():
    """OCR block counts as explicit vehicle literals so ym are not stripped on image-heavy turns."""
    merged = _blob("想加车") + "\n\n[OCR]\nVIN 1HGCM82633A004352\n2020 Toyota Camry"
    fields = _extract_add_car_fields_truth_safe(merged)
    assert fields.get("vin") and fields.get("year") and fields.get("model")
    ask = _get_next_ask_for_add_car(merged, fields, "zh", customer_turn_count=1)
    assert ask and "邮编" in ask


def test_multi_slot_jump_vin_zip_skips_year_make_nag():
    """When VIN and ZIP are already literal, do not spend a turn on year/make; ask one critical slot (delivery first)."""
    merged = _blob("add car") + "\n\n[OCR]\nVIN 1HGCM82633A004352\n92602"
    fields = _extract_add_car_fields_truth_safe(merged)
    assert fields.get("vin") and fields.get("zip")
    ask = _get_next_ask_for_add_car(merged, fields, "en", customer_turn_count=1)
    assert ask
    al = ask.lower()
    assert "year" not in al
    assert "make" not in al
    assert "delivery" in al or "effective" in al
    assert "driver" not in al


def test_near_one_shot_vin_zip_partial_vehicle_asks_delivery_only_not_year_make():
    """VIN + ZIP + partial Y/M from OCR: skip year/make ladder; single delivery ask."""
    merged = _blob("想加车") + "\n\n[OCR]\nVIN 1HGCM82633A004352\n92602\n2020 Toyota Camry"
    fields = _extract_add_car_fields_truth_safe(merged)
    assert fields.get("vin") and fields.get("zip")
    ask = _get_next_ask_for_add_car(merged, fields, "zh", customer_turn_count=1)
    assert ask
    assert "年份" not in ask and "车型" not in ask
    assert "提车" in ask or "生效" in ask
    assert "驾驶人" not in ask


def test_year_make_zip_no_vin_still_combined_delivery_driver_when_both_missing():
    """Without VIN (Y/M+ZIP identity), keep one message for both gaps when both delivery and driver are missing."""
    merged = _blob("2020 Toyota Camry zip 92602")
    fields = _extract_add_car_fields_truth_safe(merged)
    assert fields.get("year") and fields.get("model") and fields.get("zip")
    assert not fields.get("vin")
    ask = _get_next_ask_for_add_car(merged, fields, "en", customer_turn_count=1)
    assert ask
    al = ask.lower()
    assert "delivery" in al and "driver" in al


def test_near_one_shot_vin_zip_driver_present_asks_delivery_only():
    """Dense thread: VIN+ZIP+driver present, delivery missing — one delivery ask (not driver+VIN noise)."""
    merged = _blob("VIN 1HGCM82633A004352 zip 92602 primary driver is Jane")
    fields = _extract_add_car_fields_truth_safe(merged)
    assert fields.get("vin") and fields.get("zip") and fields.get("driver")
    assert not fields.get("delivery")
    ask = _get_next_ask_for_add_car(merged, fields, "en", customer_turn_count=1)
    assert ask
    al = ask.lower()
    assert ("delivery" in al or "effective" in al) and "driver" not in al
