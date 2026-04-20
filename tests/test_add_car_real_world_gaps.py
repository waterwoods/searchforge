"""Stabilization: relative dates, English entry, VIN+structure, VIN correction, conversion, focused asks."""

from __future__ import annotations

import os
from unittest import mock

import pytest

from services.fiqa_api.inbox_triage.conversion_layer import maybe_apply_quote_ready_conversion_reply
from services.fiqa_api.inbox_triage.date_normalization import (
    normalize_delivery_date_or_flag,
    relative_delivery_should_invalidate_persisted_calendar,
)
from services.fiqa_api.inbox_triage.triage import (
    _derive_vehicle_key_from_add_car_text,
    triage_conversation,
)


def _cust(msg: str) -> list[dict[str, str]]:
    return [{"role": "customer", "text": msg}]


@pytest.mark.parametrize(
    "msg,expected_mode",
    [
        ("明天提车", "resolved"),
        ("下周一提车", "resolved"),
        ("Friday pickup", "ask_exact"),
    ],
)
def test_relative_delivery_normalize_or_ask(msg: str, expected_mode: str) -> None:
    with mock.patch.dict(os.environ, {"TRIAGE_REFERENCE_DATE": "2026-04-19"}, clear=False):
        _iso, mode = normalize_delivery_date_or_flag(msg)
        if expected_mode == "resolved":
            assert mode == "resolved"
            assert _iso is not None
        else:
            assert mode == "ask_exact"


def test_relative_delivery_invalidates_persisted_calendar() -> None:
    assert relative_delivery_should_invalidate_persisted_calendar("明天提车") is True
    assert relative_delivery_should_invalidate_persisted_calendar("2026-05-01 提车") is False


def test_english_add_car_lane_and_fields() -> None:
    for msg in ("add car", "add a vehicle", "quote for a car"):
        r = triage_conversation(msg, _cust(msg), client_id="chen_kui")
        assert r.get("service_type") == "add_car"
        assert isinstance(r.get("still_needed_fields"), list)


def test_vin_zip_still_needs_year_make() -> None:
    vin = "1HGBH41JXMN109186"
    zipc = "90210"
    msg = f"{vin} zip {zipc}"
    r = triage_conversation(msg, _cust(msg), client_id="chen_kui")
    assert r.get("service_type") == "add_car"
    sn = [str(x).lower() for x in (r.get("still_needed_fields") or [])]
    assert "year" in sn or "make_model" in sn


def test_vin_correction_updates_vehicle_key() -> None:
    vin_a = "1HGBH41JXMN109186"
    vin_b = "5YJ3E1EA1KF123456"
    t1 = f"VIN {vin_a}"
    t2 = f"sorry the VIN is actually {vin_b}"
    turns = [
        {"role": "customer", "text": t1},
        {"role": "customer", "text": t2},
    ]
    merged_style = "\n".join(f"[客户] {t['text']}" for t in turns)
    vk = _derive_vehicle_key_from_add_car_text(merged_style)
    assert vk == f"vin:{vin_b}"


def test_conversion_contact_gap_copy() -> None:
    base = {
        "service_type": "add_car",
        "quote_ready_status": "quote_ready",
        "handoff_ready": True,
        "still_needed_fields": ["name", "phone"],
        "follow_up_type": "",
        "client_reply_draft": "办公室同事会尽快核对您的加车材料。",
    }
    maybe_apply_quote_ready_conversion_reply(
        base,
        language="zh",
        client_id="chen_kui",
        merged_text="[客户] hi",
        post_submit_phrasing=False,
        customer_turn_index=1,
        last_customer_message="hi",
        prior_workflow_state=None,
        conversation_turns=[],
    )
    draft = base.get("client_reply_draft") or ""
    assert "手机" in draft or "电话" in draft or "称呼" in draft
    assert "准备好" in draft or "报价" in draft
    assert "信息已经齐全" not in draft
    assert "办公室" not in draft


def test_conversion_full_handoff_strong_copy() -> None:
    base = {
        "service_type": "add_car",
        "quote_ready_status": "quote_ready",
        "handoff_ready": True,
        "still_needed_fields": [],
        "follow_up_type": "",
    }
    maybe_apply_quote_ready_conversion_reply(
        base,
        language="zh",
        client_id="chen_kui",
        merged_text="[客户] hi",
        post_submit_phrasing=False,
        customer_turn_index=1,
        last_customer_message="hi",
        prior_workflow_state=None,
        conversation_turns=[],
    )
    draft = base.get("client_reply_draft") or ""
    assert "报价" in draft
    assert "信息已经齐全" not in draft


def test_spam_reduction_single_gap_uses_focused_ask() -> None:
    # Multi-turn: only phone missing → still_needed small; intake_next_best_ask should drive draft.
    z = "90210"
    vin = "1HGBH41JXMN109186"
    long_thread = [
        {
            "role": "customer",
            "text": (
                f"add car {vin} zip {z} delivery 05/15/2026 "
                f"primary driver is me only me name John Smith"
            ),
        },
    ]
    r = triage_conversation("same", long_thread, client_id="chen_kui")
    # If phone is the only gap and handoff is false, draft should be short / focused.
    sn = [str(x).lower() for x in (r.get("still_needed_fields") or [])]
    if "phone" in sn and len(sn) <= 2 and not r.get("handoff_ready"):
        d = (r.get("client_reply_draft") or "").strip()
        assert len(d) < 500
        assert (
            "phone" in d.lower()
            or "mobile" in d.lower()
            or "电话" in d
            or "Please" in d
        )
