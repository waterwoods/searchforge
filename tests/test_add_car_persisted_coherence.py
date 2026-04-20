"""Post-submit / case_id coherence: persisted record vs fresh extraction (Add-Car)."""

from services.fiqa_api.inbox_triage.triage import (
    _augment_add_car_fields_from_persisted_collected,
    _effective_persisted_for_add_car_merge,
    _extract_add_car_fields,
    _reconcile_add_car_lists_with_persisted_record,
    triage_conversation,
)


def test_reconcile_drops_still_needed_when_on_persisted_record():
    coll, still = _reconcile_add_car_lists_with_persisted_record(
        ["year"],
        ["zip", "primary_driver"],
        {"persisted_collected_fields": ["zip", "make_model", "delivery_date"]},
    )
    assert "zip" not in [x.lower() for x in still]
    assert "primary_driver" in [x.lower() for x in still]
    assert "zip" in [x.lower() for x in coll]


def test_augment_fields_marks_structural_slots_from_persisted():
    base = _extract_add_car_fields("[客户] 谢谢")
    aug = _augment_add_car_fields_from_persisted_collected(
        base,
        ["year", "make_model", "zip", "delivery_date", "primary_driver"],
    )
    assert aug.get("year") and aug.get("model") and aug.get("zip")
    assert aug.get("delivery") and aug.get("driver")


def test_effective_persisted_invalidates_vehicle_on_explicit_correction():
    ctx = {
        "formal_submitted_at": "2026-01-01T00:00:00Z",
        "persisted_collected_fields": [
            "year",
            "make_model",
            "zip",
            "delivery_date",
            "primary_driver",
        ],
    }
    eff, meta = _effective_persisted_for_add_car_merge(
        ctx,
        "不是 Honda Accord，是 Toyota Camry 2024",
        "correction",
    )
    assert meta["correction_turn"] is True
    assert set(meta["invalidated_slots"]) >= {"year", "make_model"}
    assert "zip" in [x.lower() for x in eff]


def test_effective_persisted_skips_vehicle_invalidation_on_topic_pivot():
    ctx = {
        "formal_submitted_at": "2026-01-01T00:00:00Z",
        "persisted_collected_fields": ["year", "make_model", "zip"],
    }
    eff, meta = _effective_persisted_for_add_car_merge(ctx, "不是理赔，是账单问题", "correction")
    assert meta.get("correction_turn") is False
    assert len(eff) == 3


def test_effective_persisted_invalidates_phone_on_contact_correction():
    ctx = {
        "formal_submitted_at": "2026-01-01T00:00:00Z",
        "persisted_collected_fields": ["year", "make_model", "zip", "phone", "name"],
    }
    eff, meta = _effective_persisted_for_add_car_merge(
        ctx,
        "电话不是这个，改成 650-555-0199",
        "correction",
    )
    assert meta["correction_turn"] is True
    assert "phone" in meta["invalidated_slots"]
    assert "phone" not in [x.lower() for x in eff]


def test_triage_post_submit_vehicle_correction_exposes_add_car_merge():
    ctx = {
        "formal_submitted_at": "2026-01-01T00:00:00Z",
        "lifecycle_status": "office_followup",
        "persisted_collected_fields": [
            "year",
            "make_model",
            "vin",
            "zip",
            "delivery_date",
            "primary_driver",
            "name",
            "phone",
        ],
        "record_contact_name": "张三",
        "record_contact_phone": "415-555-0100",
    }
    turns = [{"role": "customer", "text": "加车 2024 Honda Accord 90210 下周提车 我开"}]
    out = triage_conversation(
        "不是 Accord，是 Toyota Camry 2024",
        turns,
        client_id="chen_kui",
        reply_truth_context=ctx,
    )
    am = out.get("add_car_merge") or {}
    assert am.get("correction_turn") is True
    assert set(am.get("invalidated_slots") or []) >= {"year", "make_model"}
    # Vehicle correction clears persisted VIN until re-confirmed; without a fresh VIN, not quote-ready.
    assert out.get("quote_ready_status") == "need_more"


def test_triage_post_submit_continuation_lifecycle_and_still_needed():
    """Simulates POST /triage with case_id: short follow-up should stay office_followup, not handoff_pending."""
    ctx = {
        "formal_submitted_at": "2026-01-01T00:00:00Z",
        "lifecycle_status": "office_followup",
        "persisted_collected_fields": [
            "year",
            "make_model",
            "vin",
            "zip",
            "delivery_date",
            "primary_driver",
            "name",
            "phone",
        ],
        "record_contact_name": "张三",
        "record_contact_phone": "415-555-0100",
    }
    turns = [
        {"role": "customer", "text": "加车 2024 Tesla Model Y 90210 下周提车"},
    ]
    out = triage_conversation("谢谢", turns, client_id="chen_kui", reply_truth_context=ctx)
    assert out.get("lifecycle_status") == "office_followup"
    assert out.get("quote_ready_status") == "quote_ready"
    assert not (out.get("still_needed_fields") or [])


def test_add_car_api_envelope_from_reply_truth_on_short_message():
    """CASE_CONTRACT_V1: persisted Add-Car context forces lane so short replies still expose contract fields."""
    ctx = {
        "formal_submitted_at": "2026-01-01T00:00:00Z",
        "persisted_collected_fields": ["year", "make_model"],
        "still_needed_fields": ["vin", "zip"],
        "persisted_quote_ready_status": "need_more",
    }
    out = triage_conversation("好的", [], client_id="chen_kui", reply_truth_context=ctx)
    assert isinstance(out.get("collected_fields"), list)
    assert isinstance(out.get("still_needed_fields"), list)
    assert out.get("quote_ready_status") in ("need_more", "almost_ready", "quote_ready")
    assert out.get("triage_mode") == "greenfield"
    assert out.get("lifecycle_status") is not None
