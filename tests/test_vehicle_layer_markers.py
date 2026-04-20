"""Structured vehicle-layer markers (multi-vehicle honesty) for Add-Car."""

from services.fiqa_api.inbox_triage.triage import (
    _add_car_mentions_multiple_vehicles,
    triage_conversation,
)


def test_multi_vehicle_phrases_without_two_year_tokens():
    t = "我想同时给两辆车报价，麻烦都看一下"
    assert _add_car_mentions_multiple_vehicles(t) is True


def test_same_address_two_years():
    t = "同地址还有一辆2021 Toyota Prius，我这边是2024 Honda Civic 90210"
    assert _add_car_mentions_multiple_vehicles(t) is True


def test_single_vehicle_not_multi():
    t = "加车 2024 Tesla Model Y 94107 下周提车"
    assert _add_car_mentions_multiple_vehicles(t) is False


def test_triage_exposes_markers_on_two_car_message():
    text = (
        "我想同时给两辆车报价：2024 Honda Civic 90210 下周提车 我开；"
        "还有一辆2021 Toyota Prius 同地址 给我老婆开。电话 408-555-0404，姓名孙八。"
    )
    out = triage_conversation(text, [])
    assert out.get("additional_vehicle_mentioned") is True
    assert out.get("additional_vehicle_count_hint") == 2
    assert out.get("vehicle_key") == "ymz:2024|honda_civic|90210"
    assert out.get("primary_vehicle_summary")
    bns = out.get("broker_next_step") or ""
    assert "Multiple vehicles" in bns


def test_non_add_car_has_null_vehicle_markers():
    out = triage_conversation("我的账单有问题，能帮我看一下吗？", [])
    assert out.get("vehicle_key") is None
    assert out.get("additional_vehicle_mentioned") is None
    assert out.get("primary_vehicle_summary") is None
