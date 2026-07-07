"""Unit tests for WeCom slice safe replies (ADR-003)."""

from __future__ import annotations

from services.fiqa_api.wecom.reply import (
    build_guided_menu_payload,
    build_h5_photo_phase_complete_reply,
    build_h5_vin_start_card_payload,
    build_slice_reply,
)


def test_guided_menu_no_numbered_prompt():
    text = build_slice_reply("unclear", guided_menu=True)
    assert "经纪人" in text
    assert "1." not in text
    assert "2." not in text
    assert "Reply with the number" not in text
    assert "请回复数字" not in text


def test_guided_menu_concise_chinese_task_options():
    menu = build_guided_menu_payload()
    head = menu["head_content"]
    assert "您好" in head
    assert "我要加车" in head
    assert "Add Vehicle / 加车" not in head
    labels = [item["click"]["content"] for item in menu["list"]]
    assert "【加车资料补充】" in labels
    assert "【事故/理赔】" in labels
    assert "【保单检视】" in labels
    assert "【其他问题】" in labels
    ids = {item["click"]["id"] for item in menu["list"]}
    assert ids == {"add_vehicle", "claim", "policy_review", "other"}
    assert "经纪人会审核" in menu["tail_content"]


def test_h5_start_card_concise_photo_steps():
    menu = build_h5_vin_start_card_payload(h5_url="https://example.test/task/upload/h5t1.abc")
    head = menu["head_content"]
    tail = menu["tail_content"]
    assert "加车资料收集" in head
    assert "开始上传照片" in menu["list"][0]["view"]["content"]
    assert "VIN 照片" in head
    assert "https://example.test" not in tail
    assert "请回复：链接" in tail
    assert menu["list"][0]["view"]["url"].startswith("https://example.test")


def test_h5_end_card_checklist_and_text_fields():
    case = {
        "case_attachments": [
            {"source": "h5_task", "slot_assignment": "vin_photo"},
            {"source": "h5_task", "slot_assignment": "registration_photo"},
            {"source": "h5_task", "slot_assignment": "insurance_card_photo"},
        ],
        "h5_photo_flow_state": {},
    }
    text = build_h5_photo_phase_complete_reply(case)
    assert "第 1 阶段完成" in text
    assert "✓ VIN 照片" in text
    assert "✓ 行驶证照片" in text
    assert "✓ 保险卡照片" in text
    assert "提车日期" in text
    assert "停放 ZIP" in text
    assert "联系电话" in text
    assert "不会自动修改您的保单" in text
    assert "OCR" not in text


def test_h5_end_card_insurance_skipped():
    case = {
        "case_attachments": [
            {"source": "h5_task", "slot_assignment": "vin_photo"},
            {"source": "h5_task", "slot_assignment": "registration_photo"},
        ],
        "h5_photo_flow_state": {"skipped_slots": ["insurance_card_photo"]},
    }
    text = build_h5_photo_phase_complete_reply(case)
    assert "○ 保险卡 — 可稍后补" in text
    assert "✓ 保险卡照片" not in text


def test_claim_reply_adr003_safe_language():
    text = build_slice_reply("claim_intake", guided_menu=False)
    lower = text.lower()
    assert "broker" in lower
    assert "cannot advise whether to file a claim" in lower or "不能替您决定是否报保险" in text
    assert "approved" not in lower
    assert "policy updated" not in lower


def test_coverage_reply_conservative():
    text = build_slice_reply("coverage_risk_intake", guided_menu=False)
    lower = text.lower()
    assert "broker" in lower
    assert "can't confirm" in lower or "不能判断" in text or "不能建议您" in text
    assert "you can drive now" not in lower
    assert "你现在可以开" not in text
    assert "已恢复" not in text
    assert "不用担心" not in text


def test_guided_menu_payload_has_click_items():
    menu = build_guided_menu_payload()
    assert menu["list"]
    ids = {item["click"]["id"] for item in menu["list"]}
    assert ids == {"add_vehicle", "claim", "policy_review", "other"}
