"""
Scenario C product finish: materials-claim acknowledgment in collecting replies;
VIN-only correction should not drop persisted year/make_model without vehicle contradiction.
"""

from services.fiqa_api.inbox_triage.triage import (
    _effective_persisted_for_add_car_merge,
    triage_conversation,
)

ZH_MAT_ACK = "你发过资料我这边先记上"


def test_already_sent_add_car_reply_acknowledges_materials_and_can_ask_zip():
    """User claims docs sent; follow_up already_sent; draft must ack materials, still ask for zip if missing."""
    # Omit delivery/driver on turn 1 so we stay collecting (V5 one-shot handoff would skip zip ask).
    turns = [
        {
            "role": "customer",
            "text": "想加一台新车 2024 Tesla Model Y VIN 1HGBH41JXMN109186",
        },
    ]
    out = triage_conversation("行驶证和材料我发你微信了", turns, client_id="chen_kui", reply_truth_context=None)
    assert out.get("follow_up_type") == "already_sent"
    assert "customer_says_materials_sent" in (out.get("collected_fields") or [])
    assert ZH_MAT_ACK in (out.get("client_reply_draft") or "")
    assert "邮编" in (out.get("client_reply_draft") or "")
    assert out.get("handoff_ready") is False


def test_vin_field_correction_does_not_invalidate_persisted_year_make_model():
    """Post-submit VIN literal correction: invalidate VIN only; keep year/make for coherent lists."""
    ctx = {
        "formal_submitted_at": "2026-01-01T00:00:00Z",
        "persisted_collected_fields": ["year", "make_model", "vin", "zip", "delivery_date", "primary_driver"],
    }
    eff, meta = _effective_persisted_for_add_car_merge(
        ctx,
        "VIN写错了，正确车架是1HGBH41JXMN109186",
        "correction",
    )
    assert meta.get("correction_turn") is True
    assert set(meta.get("invalidated_slots") or []) == {"vin"}
    assert "year" in [x.lower() for x in eff]
    assert "make_model" in [x.lower() for x in eff]
    assert "vin" not in [x.lower() for x in eff]


def test_add_car_no_premature_handoff_materials_zip_path():
    """Collecting + materials claim: not handoff; reply still asks for a missing critical field (zip)."""
    turns = [
        {
            "role": "customer",
            "text": "加车 2024 Honda Accord VIN 1HGBH41JXMN109186",
        },
    ]
    out = triage_conversation("材料我昨天发你微信了", turns, client_id="chen_kui", reply_truth_context=None)
    assert out.get("follow_up_type") == "already_sent"
    assert out.get("handoff_ready") is False
    assert ZH_MAT_ACK in (out.get("client_reply_draft") or "")
    draft = out.get("client_reply_draft") or ""
    assert "邮编" in draft or "zip" in draft.lower()
    # No empty / broken client draft
    assert len(draft.strip()) > 20
