"""Targeted tests: soft_route add-car, year last-wins, vehicle summary richness, impatient replies."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.triage import (
    _customer_impatience_signal,
    triage_conversation,
)


def _cust_turns(*lines: str) -> list[dict[str, str]]:
    return [{"role": "customer", "text": t} for t in lines]


def test_soft_route_add_car_natural_vehicle_not_general_inquiry() -> None:
    r = triage_conversation(
        "2020 Toyota Camry zip 92618",
        [],
        client_id="chen_kui",
        soft_route="add_car",
    )
    assert r.get("service_type") == "add_car"
    draft = (r.get("client_reply_draft") or "").lower()
    assert "请提供更多信息" not in draft
    assert "could you please provide more" not in draft


def test_year_correction_sequence_last_wins_in_summary() -> None:
    prior = _cust_turns(
        "Honda Accord 2021 for zip 90012",
        "wait not Honda",
        "actually Toyota Camry",
    )
    latest = "no sorry the year is 2022 not 2021"
    r = triage_conversation(latest, prior, client_id="chen_kui", soft_route="add_car")
    assert r.get("service_type") == "add_car"
    pvs = (r.get("primary_vehicle_summary") or "").lower()
    assert "2022" in pvs
    assert "2021" not in pvs
    assert "toyota" in pvs and "camry" in pvs
    assert "honda" not in pvs


def test_camry_without_toyota_token_full_summary() -> None:
    r = triage_conversation("Camry 2020 zip 92618", [], client_id="chen_kui")
    assert r.get("service_type") == "add_car"
    pvs = (r.get("primary_vehicle_summary") or "").lower()
    assert "2020" in pvs
    assert "camry" in pvs


def test_vehicle_summary_holds_after_make_correction_and_zip_turn() -> None:
    """Later zip-only turn must not revert primary to VIN-decoded make (1HG→Honda)."""
    turns: list[dict[str, str]] = []
    script = [
        "I want to add a car Honda Accord 2021",
        "VIN 1HGCM82633A654321",
        "actually not Honda, it's Toyota Camry 2021",
        "zip 92618",
    ]
    r = None
    for line in script:
        r = triage_conversation(line, turns, client_id="chen_kui")
        turns.append({"role": "customer", "text": line})
    assert r is not None
    assert (r.get("primary_vehicle_summary") or "").strip() == "2021 Toyota Camry"
    assert "honda" not in (r.get("client_reply_draft") or "").lower()


def test_impatient_user_gets_explanation_prefix() -> None:
    assert _customer_impatience_signal("Why do you keep asking questions?")
    prior = _cust_turns("add car", "2017 Honda CR-V zip 94501")
    latest = "Why do you keep asking questions? I gave you the car and zip"
    r = triage_conversation(latest, prior, client_id="chen_kui")
    assert r.get("service_type") == "add_car"
    d = r.get("client_reply_draft") or ""
    assert "avoid guessing" in d.lower() or "避免猜" in d or "猜错" in d
