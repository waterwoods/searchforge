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
        "Please confirm everyone is safe first. I will record the accident details for your broker — "
        "Chen Kui's team will contact you soon. We cannot advise whether to file a claim online.\n"
        "收到，请先确认人是否安全。我先帮您记录事故信息，陈总会尽快人工联系您。"
        "请补充事故时间、地点、是否有人受伤。线上不能替您决定是否报保险。"
    ),
    "policy_review": (
        "I will organize your premium/renewal details for broker review — Chen Kui's team will "
        "follow up manually. This is not an online quote or policy change.\n"
        "收到，我先帮您整理保费/续保情况，陈总会人工帮您查看是否有更合适的方案。"
        "请您方便时补充当前保费、续保日期或 renewal notice。不会线上直接报价。"
    ),
    "menu_selection": _GUIDED_MENU_TEXT,
    "unclear": _GUIDED_MENU_TEXT,
}


def build_slice_reply(intent: WeComIntent, *, guided_menu: bool) -> str:
    """Return one safe bilingual customer reply. Never promises policy change."""
    if intent in _START_CARD_CLICK_REPLIES:
        return _START_CARD_CLICK_REPLIES[intent]
    if guided_menu or intent == "unclear":
        return _GUIDED_MENU_TEXT
    return _INTENT_REPLIES.get(intent, _GUIDED_MENU_TEXT)


def build_secondary_topic_deferred_reply() -> str:
    """One-flow-at-a-time ack when customer raises a second topic mid add_car flow."""
    return _SECONDARY_TOPIC_DEFERRED


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


# ---------------------------------------------------------------------------
# Track B0.1 — Start Card (WECOM_B0_ACTIVE_WORKSPACE only)
#
# Sent instead of immediately calling ingest_wecom_text_to_active_case() when
# a high-confidence add_car intent is detected. No case exists yet — creating
# a Draft Case on "Start" is B0.2 scope, not this card.
# ---------------------------------------------------------------------------

_START_CARD_HEAD = """\
I can help you add a vehicle to your policy. Want me to start a request for your broker?
我可以帮您把新车加到保单里。要现在开始一个请求给经纪人吗？"""

_START_CARD_TAIL = """\
Your broker reviews everything before anything changes.
经纪人会先审核，任何变更前都会确认。"""

_START_CARD_ITEMS: list[dict[str, str]] = [
    {"id": "start_add_car", "content": "Start / 开始"},
    {"id": "start_add_car_decline", "content": "Later / 稍后"},
    {"id": "start_add_car_broker", "content": "Talk to Broker / 联系经纪人"},
]

_START_CLICK_ACK = (
    "Thanks — let's get started. Your broker will follow up shortly.\n"
    "谢谢，我们开始吧。经纪人会尽快跟进。"
)

_START_DECLINE_ACK = (
    "No problem — reply anytime when you're ready to start.\n"
    "没关系，准备好的时候随时回复我们即可。"
)

_START_BROKER_ACK = (
    "Understood — we'll let your broker know you'd like to talk directly.\n"
    "明白了，我们会告知经纪人您希望直接沟通。"
)

_SECONDARY_TOPIC_DEFERRED = (
    "Got it — I noted your other question. Let's finish your current request first; "
    "your broker will follow up on the other topic.\n"
    "收到，我已记录您的其他问题。我们先完成当前请求，陈总会人工跟进其他事项。"
)

_START_CARD_CLICK_REPLIES: dict[WeComIntent, str] = {
    "start_add_car_click": _START_CLICK_ACK,
    "start_add_car_decline_click": _START_DECLINE_ACK,
    "start_add_car_broker_click": _START_BROKER_ACK,
}


def build_start_card_payload() -> dict[str, Any]:
    """WeCom native msgmenu: Start / Later / Talk to Broker. No case exists yet."""
    return {
        "head_content": _START_CARD_HEAD,
        "list": [
            {"type": "click", "click": {"id": item["id"], "content": item["content"]}}
            for item in _START_CARD_ITEMS
        ],
        "tail_content": _START_CARD_TAIL,
    }


# ---------------------------------------------------------------------------
# Track B0.3 — Done Card (WECOM_B0_ACTIVE_WORKSPACE only)
#
# Sent exactly once, only from `active_case_bridge.confirm_case_by_broker()`,
# only after the broker clicks Confirm. Never sent before, never automatic.
#
# Tone guardrail (contract §6 + product review): the broker has received and
# reviewed the request — nothing on the policy has changed yet. Must NOT say
# "Insurance updated" or "Completed successfully"; that would not be true.
# ---------------------------------------------------------------------------

DONE_CARD_TEXT = """\
Chen Kui's team has received your request. We will follow up with next steps.
陈奎团队已收到您的请求，我们会跟进后续步骤。"""
