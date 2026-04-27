"""Unit tests for add-car active vehicle resolution priority and ambiguity."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.active_vehicle_resolver import resolve_add_car_active_vehicle


def test_explicit_model_overrides_order() -> None:
    r = resolve_add_car_active_vehicle(
        last_customer_message="Please quote the Camry.",
        customer_bubbles=[
            "2020 Toyota Camry zip 90210",
            "2022 Tesla Model Y same zip",
        ],
    )
    assert not r.is_ambiguous
    assert r.segment_index == 0
    assert r.kind == "explicit_model"


def test_first_car_reanchor() -> None:
    r = resolve_add_car_active_vehicle(
        last_customer_message="最开始那辆，做报价。",
        customer_bubbles=[
            "2020 Toyota Camry zip 90210",
            "Actually 2022 Tesla Model Y.",
        ],
    )
    assert not r.is_ambiguous
    assert r.segment_index == 0
    assert r.kind == "first_created"


def test_the_one_before_phrase() -> None:
    r = resolve_add_car_active_vehicle(
        last_customer_message="Use the one before, first car in the thread.",
        customer_bubbles=[
            "2019 Honda Civic 94103",
            "Switch to 2021 BMW X3.",
        ],
    )
    assert r.kind == "first_created"
    assert r.segment_index == 0


def test_ignore_tesla_single_remainder() -> None:
    r = resolve_add_car_active_vehicle(
        last_customer_message="Ignore Tesla, 不要特斯拉 — quote the other car.",
        customer_bubbles=[
            "2020 Toyota Camry zip 90210",
            "2022 Tesla Model Y same zip",
        ],
    )
    assert not r.is_ambiguous
    assert r.segment_index == 0
    assert r.kind == "ignore_remainder"


def test_ignore_tesla_two_gas_cars_ambiguous() -> None:
    r = resolve_add_car_active_vehicle(
        last_customer_message="Ignore Tesla.",
        customer_bubbles=[
            "2020 Toyota Camry",
            "2018 Honda Civic",
            "2022 Tesla Model Y",
        ],
    )
    assert r.is_ambiguous


def test_explicit_vin_last_turn() -> None:
    r = resolve_add_car_active_vehicle(
        last_customer_message="VIN is 1HGBH41JXMN109186",
        customer_bubbles=["2020 Camry", "wrong bubble"],
    )
    assert r.kind == "explicit_vin"
    assert r.segment_index == 1


def test_same_model_refinement_chain_latest_wins() -> None:
    r = resolve_add_car_active_vehicle(
        last_customer_message="Actually it's a 2020 Camry.",
        customer_bubbles=[
            "I want to add a Toyota Camry, garaging ZIP 94103, picking up next Friday, I'm the primary driver.",
            "Actually it's a 2020 Camry.",
        ],
    )
    assert not r.is_ambiguous
    assert r.segment_index == 1
    assert r.kind == "explicit_model"


def test_first_mentioned_chinese_car_phrase() -> None:
    r = resolve_add_car_active_vehicle(
        last_customer_message="第一个车为准。",
        customer_bubbles=["2021 Corolla 94110", "2023 Model Y"],
    )
    assert r.kind == "first_created"
    assert r.segment_index == 0
