"""Safe bilingual reply text for WeCom vertical slice (ADR-003 language)."""

from __future__ import annotations

from typing import Any

from services.fiqa_api.wecom.intent import WeComIntent

_GUIDED_MENU_HEAD = """\
Thanks. I can help you review your request.
To make sure we route this correctly, please tap a topic below or reply with a short phrase.
感谢您联系我们。为确保正确分类，请点击下方选项或回复简短说明。

Your broker will review — we will not change your policy automatically.
经纪人会审核，我们不会自动修改您的保单。"""

_GUIDED_MENU_TAIL = """\
Tap a topic above, or reply with a short phrase (e.g. 加车, claim, 保单检视).
请点击上方选项，或回复简短说明。"""

_GUIDED_MENU_ITEMS: list[dict[str, str]] = [
    {"id": "add_vehicle", "content": "Add Vehicle / 加车"},
    {"id": "claim", "content": "Claim / Accident / 事故理赔"},
    {"id": "policy_review", "content": "Policy Review / 保单检视"},
    {"id": "other", "content": "Other / 其他"},
]

_GUIDED_MENU_TEXT = f"""\
{_GUIDED_MENU_HEAD}

• Add Vehicle / 加车
• Claim / Accident / 事故理赔
• Policy Review / 保单检视
• Other / 其他

{_GUIDED_MENU_TAIL}"""

_INTENT_REPLIES: dict[WeComIntent, str] = {
    "add_car": (
        "Got it — sounds like you want to add a vehicle. Your broker will review and confirm next steps. "
        "Please send your purchase agreement or registration when you can.\n"
        "了解，您想加车。经纪人会审核并确认后续步骤。请尽量发送购车合同或行驶证。"
    ),
    "claim_intake": (
        "I'm sorry to hear about the accident. Please stay safe. If you can, take photos and exchange insurance "
        "info with the other driver. Your broker will follow up — we are not filing a claim automatically.\n"
        "抱歉得知您出事故。请先注意安全。如方便请拍照并交换对方保险信息。经纪人会跟进，我们不会自动报案。"
    ),
    "policy_review": (
        "I can help start a policy review. Please send your current insurance card or declaration page. "
        "Your broker will review and follow up — this is not a quote or policy change.\n"
        "可以帮您开始保单检视。请发送当前保险卡或 declaration page。经纪人会审核并跟进，这不是报价或保单变更。"
    ),
    "menu_selection": _GUIDED_MENU_TEXT,
    "unclear": _GUIDED_MENU_TEXT,
}


def build_slice_reply(intent: WeComIntent, *, guided_menu: bool) -> str:
    """Return one safe bilingual customer reply. Never promises policy change."""
    if guided_menu or intent == "unclear":
        return _GUIDED_MENU_TEXT
    return _INTENT_REPLIES.get(intent, _GUIDED_MENU_TEXT)


def build_guided_menu_payload() -> dict[str, Any]:
    """WeCom native msgmenu structure for low-confidence routing."""
    return {
        "head_content": _GUIDED_MENU_HEAD,
        "list": [
            {"type": "click", "click": {"id": item["id"], "content": item["content"]}}
            for item in _GUIDED_MENU_ITEMS
        ],
        "tail_content": _GUIDED_MENU_TAIL,
    }
