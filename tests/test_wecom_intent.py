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
    assert canonical_intent("coverage_risk_intake") == "coverage_risk"
    assert canonical_intent("policy_review") == "policy_review"
    assert canonical_intent("unclear") == "unclear"


def test_coverage_risk_high_confidence_chinese():
    r = classify_wecom_intent("我保险停了还能开吗")
    assert r.intent == "coverage_risk_intake"
    assert r.confidence == "high"


def test_coverage_risk_no_insurance():
    r = classify_wecom_intent("我现在没保险怎么办")
    assert r.intent == "coverage_risk_intake"
    assert r.confidence == "high"


def test_coverage_risk_english_cancelled_drive():
    r = classify_wecom_intent("policy cancelled can I still drive")
    assert r.intent == "coverage_risk_intake"
    assert r.confidence == "high"


def test_coverage_risk_dmv():
    r = classify_wecom_intent("DMV says no insurance")
    assert r.intent == "coverage_risk_intake"
    assert r.confidence == "high"


def test_premium_not_coverage():
    r = classify_wecom_intent("我保险太贵了")
    assert r.intent == "policy_review"
    assert r.confidence == "high"


def test_claim_not_coverage():
    r = classify_wecom_intent("我撞车了")
    assert r.intent == "claim_intake"
    assert r.confidence == "high"


def test_add_car_not_coverage():
    r = classify_wecom_intent("明天提新车")
    assert r.intent == "add_car"
    assert r.confidence == "high"


def test_mixed_premium_and_coverage_prefers_coverage():
    r = classify_wecom_intent("我保险太贵了，而且好像停保了，现在还能开车吗？")
    assert r.intent == "coverage_risk_intake"
    assert r.confidence == "high"


def test_mixed_claim_and_coverage_prefers_coverage():
    r = classify_wecom_intent("我昨天撞车了，保险好像已经停了")
    assert r.intent == "coverage_risk_intake"
    assert r.confidence == "high"


def test_multi_intent_is_unclear():
    r = classify_wecom_intent("I had an accident and bought a new car")
    assert r.intent == "unclear"
    assert r.confidence == "low"
