"""Unit tests for WeCom slice rule-based intent."""

from __future__ import annotations

from services.fiqa_api.wecom.intent import classify_wecom_intent


def test_claim_intake_high_confidence():
    r = classify_wecom_intent("I was in an accident yesterday")
    assert r.intent == "claim_intake"
    assert r.confidence == "high"


def test_add_car_chinese():
    r = classify_wecom_intent("我买了一辆新车，想加到保险上")
    assert r.intent == "add_car"
    assert r.confidence == "high"


def test_policy_review_english():
    r = classify_wecom_intent("Can you review my policy?")
    assert r.intent == "policy_review"
    assert r.confidence == "high"


def test_unclear_gets_low_confidence():
    r = classify_wecom_intent("hello there")
    assert r.intent == "unclear"
    assert r.confidence == "low"


def test_menu_number_selection():
    r = classify_wecom_intent("2")
    assert r.intent == "claim_intake"
    assert r.confidence == "high"
    assert r.matched_by == "menu_number"


def test_menu_id_click_add_vehicle():
    r = classify_wecom_intent("", menu_id="add_vehicle")
    assert r.intent == "add_car"
    assert r.confidence == "high"


def test_canonical_intent_names():
    from services.fiqa_api.wecom.intent import canonical_intent

    assert canonical_intent("add_car") == "add_vehicle"
    assert canonical_intent("claim_intake") == "claim"
    assert canonical_intent("policy_review") == "policy_review"
    assert canonical_intent("unclear") == "unclear"


def test_multi_intent_is_unclear():
    r = classify_wecom_intent("I had an accident and bought a new car")
    assert r.intent == "unclear"
    assert r.confidence == "low"
