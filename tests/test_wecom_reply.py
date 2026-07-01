"""Unit tests for WeCom slice safe replies (ADR-003)."""

from __future__ import annotations

from services.fiqa_api.wecom.reply import build_guided_menu_payload, build_slice_reply


def test_guided_menu_no_numbered_prompt():
    text = build_slice_reply("unclear", guided_menu=True)
    assert "broker" in text.lower()
    assert "1." not in text
    assert "2." not in text
    assert "Reply with the number" not in text
    assert "请回复数字" not in text


def test_claim_reply_adr003_safe_language():
    text = build_slice_reply("claim_intake", guided_menu=False)
    lower = text.lower()
    assert "broker" in lower
    assert "not filing a claim automatically" in lower
    assert "approved" not in lower
    assert "policy updated" not in lower


def test_guided_menu_payload_has_click_items():
    menu = build_guided_menu_payload()
    assert menu["list"]
    ids = {item["click"]["id"] for item in menu["list"]}
    assert ids == {"add_vehicle", "claim", "policy_review", "other"}
