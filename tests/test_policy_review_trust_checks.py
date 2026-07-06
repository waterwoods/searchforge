"""Unit tests for Policy Review trust checks — name verification and portal labels."""

from __future__ import annotations

from services.fiqa_api.p16.packet_persist import build_portal_copy_text_policy_review
from services.fiqa_api.policy_review.trust_checks import (
    apply_trust_checks,
    format_portal_driver_line,
    portal_label_for_driver,
)


def _packet_stub() -> dict:
    return {
        "customer_name": {"value": "nanxin li"},
        "phone": {"value": "6265550100"},
        "garaging_zip": {"value": "91101"},
        "current_carrier": {"value": "Progressive"},
        "policy_number": {"value": "CA-1"},
        "policy_term_start": {"value": "2025-01-01"},
        "policy_term_end": {"value": "2025-07-01"},
        "premium_amount": {"value": "844.76"},
        "premium_period": {"value": "6 months"},
        "bodily_injury": {"value": "100/300"},
        "property_damage": {"value": "100"},
    }


def test_close_name_mismatch_adds_warning() -> None:
    drivers = [{"name": "Namin Li", "relationship": "Named Insured"}]
    updated, warnings = apply_trust_checks("nanxin li", drivers, [])
    assert updated[0]["needs_verification"] is True
    assert any("name may need verification" in w for w in warnings)


def test_large_name_mismatch_adds_warning() -> None:
    drivers = [{"name": "Meiyuan Li", "relationship": "Parent"}]
    updated, warnings = apply_trust_checks("nanxin li", drivers, [])
    assert updated[0]["needs_verification"] is True
    assert updated[0].get("possible_name_conflict") is True
    assert any("name may need verification" in w for w in warnings)
    assert any("Possible name conflict" in w for w in warnings)


def test_parent_relationship_becomes_driver_n() -> None:
    label, needs_verify = portal_label_for_driver("Parent", 2)
    assert label == "Driver 2"
    assert needs_verify is True


def test_verify_suffix_present() -> None:
    driver = {
        "name": "Meiyuan Li",
        "relationship": "Parent",
        "portal_label": "Driver 2",
        "needs_verification": True,
    }
    line = format_portal_driver_line(driver, 2)
    assert line == "Driver 2: Meiyuan Li (verify)"
    assert "Parent:" not in line


def test_portal_copy_never_uses_parent_label() -> None:
    drivers = [{
        "name": "Meiyuan Li",
        "relationship": "Parent",
        "portal_label": "Driver 2",
        "needs_verification": True,
        "relationship_needs_verification": True,
    }]
    text = build_portal_copy_text_policy_review(
        packet=_packet_stub(),
        vehicles=[{"year": "2020", "make": "Toyota", "model": "Corolla", "vin": "X"}],
        drivers=drivers,
    )
    assert "Parent:" not in text
    assert "Driver 2: Meiyuan Li (verify)" in text


def test_matching_name_no_verification_flag() -> None:
    drivers = [{"name": "nanxin li", "relationship": "Named Insured"}]
    updated, warnings = apply_trust_checks("nanxin li", drivers, [])
    assert not updated[0].get("needs_verification")
    assert not any("name may need verification" in w for w in warnings)


def test_trust_checks_do_not_mutate_driver_name() -> None:
    drivers = [{"name": "Meiyuan Li", "relationship": "Parent"}]
    updated, _ = apply_trust_checks("nanxin li", drivers, [])
    assert updated[0]["name"] == "Meiyuan Li"
    assert updated[0]["relationship"] == "Parent"
