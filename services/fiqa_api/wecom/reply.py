"""Safe bilingual reply text for WeCom vertical slice (ADR-003 language)."""

from __future__ import annotations

from typing import Any

from services.fiqa_api.wecom.intent import WeComIntent

_GUIDED_MENU_HEAD = """\
您好，请选择您要办理的事项：

也可以直接回复：
「我要加车」/「我要理赔」/「查保单」"""

_GUIDED_MENU_TAIL = """\
经纪人会审核，我们不会自动修改您的保单。"""

_GUIDED_MENU_ITEMS: list[dict[str, str]] = [
    {"id": "add_vehicle", "content": "【加车资料补充】"},
    {"id": "claim", "content": "【事故/理赔】"},
    {"id": "policy_review", "content": "【保单检视】"},
    {"id": "other", "content": "【其他问题】"},
]

_GUIDED_MENU_TEXT = f"""\
{_GUIDED_MENU_HEAD}

• 【加车资料补充】
• 【事故/理赔】
• 【保单检视】
• 【其他问题】

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
    "coverage_risk_intake": (
        "Got it. This is a high-risk coverage status issue and must be reviewed by the broker. "
        "I can't confirm whether coverage is active or advise whether you can drive. "
        "Please provide the carrier notice, policy number, vehicle info, and cancellation or lapse date.\n"
        "收到，这个属于高风险保单状态问题，需要陈总人工核实。"
        "线上不能判断您是否仍有保障，也不能建议您是否可以开车。"
        "请补充保险公司通知、保单号和停保日期。"
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
    """WeCom native msgmenu: Start / Later / Talk to Broker (legacy fallback)."""
    return {
        "head_content": _START_CARD_HEAD,
        "list": [
            {"type": "click", "click": {"id": item["id"], "content": item["content"]}}
            for item in _START_CARD_ITEMS
        ],
        "tail_content": _START_CARD_TAIL,
    }


# ---------------------------------------------------------------------------
# P19D-3 / P19D-4A — H5 Add Vehicle photo flow Start Card
# ---------------------------------------------------------------------------

_H5_PHOTO_FLOW_START_HEAD = """\
【加车资料收集】

请先上传 3 类资料：
1. VIN 照片
2. 行驶证 / 登记证
3. 保险卡（没有可跳过）

点下面按钮开始上传。"""

_H5_PHOTO_FLOW_BUTTON = "开始上传资料"

_H5_PHOTO_FLOW_TAIL_PREFIX = """\
照片在页面里上传；提车日期、停放 ZIP、联系电话稍后回微信补充。
陈总会人工确认，不会自动修改您的保单。"""

_H5_PHOTO_FLOW_START_CARD_TAIL = """\
照片在页面里上传；提车日期、停放 ZIP、联系电话稍后回微信补充。
陈总会人工确认，不会自动修改您的保单。

如果按钮打不开，请回复：链接"""


def build_h5_vin_start_card_payload(*, h5_url: str, restart_intro: bool = False) -> dict[str, Any]:
    """WeCom msgmenu: H5 Add Vehicle photo flow view button + Later / Talk to Broker."""
    url = (h5_url or "").strip()
    tail = _H5_PHOTO_FLOW_START_CARD_TAIL
    head = _H5_PHOTO_FLOW_START_HEAD
    if restart_intro:
        head = "好的，我们为您开始一辆新车的资料收集。\n\n" + head
    return {
        "head_content": head,
        "list": [
            {"type": "view", "view": {"url": url, "content": _H5_PHOTO_FLOW_BUTTON}},
            {"type": "click", "click": {"id": "start_add_car_decline", "content": "稍后"}},
            {
                "type": "click",
                "click": {"id": "start_add_car_broker", "content": "联系经纪人"},
            },
        ],
        "tail_content": tail,
    }


def build_h5_vin_start_text_fallback(*, h5_url: str) -> str:
    """Plain-text fallback when msgmenu view buttons are unavailable."""
    url = (h5_url or "").strip()
    return (
        f"{_H5_PHOTO_FLOW_START_HEAD}\n\n"
        f"开始上传资料：{url}\n\n"
        f"{_H5_PHOTO_FLOW_TAIL_PREFIX}\n\n"
        "如果按钮打不开，请复制链接在微信中打开。"
    )


# ---------------------------------------------------------------------------
# P19D-4B — H5 photo flow End Card (E2-photo phase)
# ---------------------------------------------------------------------------

_H5_PHOTO_SLOT_LABELS: dict[str, str] = {
    "vin_photo": "VIN 照片",
    "registration_photo": "行驶证照片",
    "insurance_card_photo": "保险卡照片",
}


def _h5_photo_slots_from_case(case: dict[str, Any]) -> tuple[set[str], set[str]]:
    completed: set[str] = set()
    for att in case.get("case_attachments") or []:
        if not isinstance(att, dict):
            continue
        if str(att.get("source") or "").strip().lower() != "h5_task":
            continue
        slot = str(att.get("slot_assignment") or "").strip().lower()
        if slot:
            completed.add(slot)
    state = case.get("h5_photo_flow_state") or {}
    skipped_raw = state.get("skipped_slots") or [] if isinstance(state, dict) else []
    skipped = {str(s).strip().lower() for s in skipped_raw if s}
    return completed, skipped


def build_h5_photo_phase_complete_reply(case: dict[str, Any]) -> str:
    """WeCom Stage Complete S1 — Phase 1 photos done; prompt Phase 2 text fields."""
    lines = [
        "【第 1 步完成 ✅】",
        "",
        "照片资料已收到。",
        "",
        "下一步请在微信里回复：",
        "提车日期、停放 ZIP、联系电话。",
        "",
        "例如：",
        "7月10号提车，ZIP 92705，电话 2031234567",
    ]
    return "\n".join(lines)


def build_phase2_current_step_reply(case: dict[str, Any]) -> str:
    """Current Step Card while Phase 2 text collection is in progress."""
    from services.fiqa_api.wecom.add_vehicle_phase2 import (
        PHASE2_TEXT_FIELDS,
        _FIELD_LABELS_ZH,
        _field_display_value,
        phase2_text_still_needed,
    )

    collected_names = {str(x).lower() for x in (case.get("collected_fields") or [])}
    still = phase2_text_still_needed(case)
    has_any = any(f in collected_names for f in PHASE2_TEXT_FIELDS)

    if not has_any:
        lines = [
            "【加车资料 · 第 2 步】",
            "",
            f"还差 {len(PHASE2_TEXT_FIELDS)} 个文字信息：",
            "",
            "1. 提车日期",
            "2. 停放 ZIP",
            "3. 联系电话",
            "",
            "可以直接这样回复：",
            "7月10号提车，ZIP 92705，电话 2031234567",
        ]
        return "\n".join(lines)

    lines = ["【加车资料 · 第 2 步】", "", "已收到："]
    for field in PHASE2_TEXT_FIELDS:
        if field in collected_names:
            lines.append(f"✓ {_FIELD_LABELS_ZH[field]} — {_field_display_value(case, field)}")
    lines.append("")
    if still:
        lines.append("还差：")
        for field in still:
            lines.append(f"○ {_FIELD_LABELS_ZH[field]}")
        lines.append("")
        if len(still) == 1 and still[0] == "phone":
            lines.append("请直接回复电话号码即可。")
        else:
            lines.append("请继续在微信里回复。")
    return "\n".join(lines)


def build_phase2_stage_complete_s2_reply(case: dict[str, Any]) -> str:
    """Stage Complete S2 — Phase 2 text fields done; hand off to broker review."""
    lines = [
        "【第 2 步完成 ✅】",
        "",
        "文字信息已收到。",
        "",
        "目前资料已基本收齐。",
        "下一步：陈总人工确认。",
        "",
        "系统不会自动修改您的保单。",
    ]
    return "\n".join(lines)


def build_phase2_unrecognized_fields_reply() -> str:
    """When Phase 2 is active but no structured fields could be parsed from free text."""
    return "\n".join(
        [
            "我还需要一点信息才能继续。",
            "",
            "还差：",
            "○ 提车日期",
            "○ 停放 ZIP",
            "○ 联系电话",
            "",
            "请直接这样回复：",
            "7月10号提车，ZIP 92705，电话 2031234567",
        ]
    )


def build_phase2_validation_reply(
    case: dict[str, Any],
    *,
    invalid_date: str | None = None,
    invalid_phone: str | None = None,
) -> str:
    """Ask customer to re-enter fields that failed validation."""
    from services.fiqa_api.wecom.add_vehicle_phase2 import (
        PHASE2_TEXT_FIELDS,
        _FIELD_LABELS_ZH,
        _field_display_value,
    )

    lines: list[str] = []
    collected_names = {str(x).lower() for x in (case.get("collected_fields") or [])}
    has_collected = any(f in collected_names for f in PHASE2_TEXT_FIELDS)
    if has_collected:
        lines.extend(["已收到："])
        for field in PHASE2_TEXT_FIELDS:
            if field in collected_names:
                lines.append(f"✓ {_FIELD_LABELS_ZH[field]} — {_field_display_value(case, field)}")
        lines.append("")

    if invalid_date:
        lines.extend(
            [
                "提车日期好像不对，我看到：",
                invalid_date,
                "",
                "请重新回复正确日期。",
                "例如：",
                "7月12号",
                "",
            ]
        )
    if invalid_phone:
        lines.extend(
            [
                "联系电话位数好像不对，我看到：",
                invalid_phone,
                "",
                "请重新回复 10 位电话号码。",
                "例如：",
                "2031234567",
            ]
        )
    return "\n".join(lines).rstrip()


# ---------------------------------------------------------------------------
# P19H-2 — Claim guided workflow replies (start / basics / C1)
# ---------------------------------------------------------------------------

_CLAIM_BASICS_LABELS: dict[str, str] = {
    "accident_datetime": "事故时间",
    "accident_location": "事故地点",
    "accident_description": "简单描述",
}

_CLAIM_SAFE_DISCLAIMER = "这不代表已经向保险公司正式报案。"
_CLAIM_C1_H5_BUTTON = "补充事故资料"
_CLAIM_C1_PHOTO_GUIDANCE_LINES: tuple[str, ...] = (
    "您可以继续在微信里补充说明或发照片，都会记到同一份记录里。",
    "陈总会整理确认后联系您。",
)
_CLAIM_C1_H5_TAIL = """\
如果按钮打不开，请回复：链接

这只是资料收集，不代表 claim 已正式提交。
陈总会人工确认。"""


def _claim_fact_display(case: dict[str, Any], field: str) -> str:
    facts = case.get("known_facts") or {}
    if isinstance(facts, dict):
        raw = facts.get(field)
        if raw:
            return str(raw).strip()
    return _CLAIM_BASICS_LABELS.get(field, field)


def build_claim_start_card_reply(*, injury_mentioned: bool = False) -> str:
    lines = [
        "您好，我是陈总办公室的值班助手。",
        "",
        "请先确认：您和车上的人现在都安全吗？有没有受伤？",
    ]
    if injury_mentioned:
        lines.extend(
            [
                "",
                "如果有人受伤，请优先联系紧急服务，并尽快联系陈总。",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "如果安全，请用一条消息告诉我：",
                "大概什么时候、在哪里、发生了什么事。",
                "",
                "我会先帮您记录下来，陈总会人工确认后联系您。",
            ]
        )
    lines.extend(
        [
            "",
            _CLAIM_SAFE_DISCLAIMER,
        ]
    )
    return "\n".join(lines)


def build_claim_start_injury_menu_payload() -> dict[str, Any]:
    """WeCom msgmenu: injury quick replies on Claim start (P19H-3e-1)."""
    return {
        "head_content": build_claim_start_card_reply(injury_mentioned=False),
        "list": [
            {"type": "click", "click": {"id": "claim_injury_no", "content": "没有受伤"}},
            {"type": "click", "click": {"id": "claim_injury_yes", "content": "有人受伤"}},
            {"type": "click", "click": {"id": "claim_injury_unknown", "content": "不确定"}},
        ],
        "tail_content": _CLAIM_SAFE_DISCLAIMER,
    }


def build_claim_missing_basics_reply(case: dict[str, Any]) -> str:
    from services.fiqa_api.wecom.claim_state import CLAIM_ACCIDENT_BASICS_FIELDS, is_accident_basics_complete

    collected_names = {str(x).lower() for x in (case.get("collected_fields") or [])}
    still = [f for f in CLAIM_ACCIDENT_BASICS_FIELDS if f.lower() not in collected_names]
    has_any = any(f.lower() in collected_names for f in CLAIM_ACCIDENT_BASICS_FIELDS)

    if not has_any:
        return build_claim_start_card_reply(injury_mentioned=False)

    lines = ["【理赔资料收集】", ""]
    lines.append("已收到：")
    for field in CLAIM_ACCIDENT_BASICS_FIELDS:
        if field.lower() in collected_names:
            lines.append(f"✅ {_CLAIM_BASICS_LABELS[field]}：{_claim_fact_display(case, field)}")
    lines.append("")
    if still:
        lines.append("还需要：")
        for field in still:
            lines.append(f"○ {_CLAIM_BASICS_LABELS[field]}")
        lines.append("")
        lines.append("请直接回复，例如：")
        lines.append("今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门。")
        lines.append("")
    lines.append("这只是资料收集，不代表已经正式报案。")
    if is_accident_basics_complete(case):
        return build_claim_basics_already_complete_reply(case)
    return "\n".join(lines)


def _claim_c1_stage_complete_head_lines(case: dict[str, Any]) -> list[str]:
    return [
        "【事故信息已记录 ✅】",
        "",
        f"时间：{_claim_fact_display(case, 'accident_datetime')}",
        f"地点：{_claim_fact_display(case, 'accident_location')}",
        f"经过：{_claim_fact_display(case, 'accident_description')}",
        "",
        *_CLAIM_C1_PHOTO_GUIDANCE_LINES,
        "",
        "如果想分步补充资料，也可以点下面「补充事故资料」。",
    ]


def _claim_basics_already_complete_head_lines(case: dict[str, Any]) -> list[str]:
    return [
        "【事故信息已记录 ✅】",
        "",
        f"时间：{_claim_fact_display(case, 'accident_datetime')}",
        f"地点：{_claim_fact_display(case, 'accident_location')}",
        f"经过：{_claim_fact_display(case, 'accident_description')}",
        "",
        *_CLAIM_C1_PHOTO_GUIDANCE_LINES,
        "",
        "如果想分步补充资料，也可以点下面「补充事故资料」。",
    ]


def build_claim_c1_h5_evidence_card_payload(
    *,
    h5_url: str,
    case: dict[str, Any],
    already_complete: bool = False,
) -> dict[str, Any]:
    """WeCom msgmenu: Claim C1 H5 evidence upload view button + contact broker."""
    url = (h5_url or "").strip()
    head_lines = (
        _claim_basics_already_complete_head_lines(case)
        if already_complete
        else _claim_c1_stage_complete_head_lines(case)
    )
    return {
        "head_content": "\n".join(head_lines),
        "list": [
            {"type": "view", "view": {"url": url, "content": _CLAIM_C1_H5_BUTTON}},
            {
                "type": "click",
                "click": {"id": "claim_contact_broker", "content": "联系陈总"},
            },
        ],
        "tail_content": _CLAIM_C1_H5_TAIL,
    }


def build_claim_stage_complete_c1_reply(case: dict[str, Any]) -> str:
    lines = [
        *_claim_c1_stage_complete_head_lines(case),
        "",
        "这只是资料收集，不代表 claim 已正式提交。",
        "陈总会人工确认。",
    ]
    return "\n".join(lines)


def build_claim_basics_already_complete_reply(case: dict[str, Any]) -> str:
    lines = [
        *_claim_basics_already_complete_head_lines(case),
        "",
        _CLAIM_SAFE_DISCLAIMER,
    ]
    return "\n".join(lines)


def build_claim_safety_manual_reply() -> str:
    return "\n".join(
        [
            "【理赔 · 安全优先】",
            "",
            "请先确保人身安全。",
            "",
            "如有紧急情况，请联系当地紧急服务（如 911）。",
            "请尽快联系陈总，我们会优先人工跟进。",
            "",
            "我们不能在系统里判断事故责任或 coverage。",
            _CLAIM_SAFE_DISCLAIMER,
        ]
    )


def build_claim_interrupt_safety_manual_reply() -> str:
    """P19H-2.1 — Injury override when Add Vehicle flow is active."""
    return "\n".join(
        [
            "【安全提醒】",
            "",
            "如果有人受伤，请先确保人身安全。",
            "如有紧急情况，请联系当地紧急服务，并尽快联系陈总。",
            "",
            "我们不会在系统里判断责任或 coverage。",
            "陈总会人工跟进。",
        ]
    )


def build_claim_identity_broker_confirm_reply() -> str:
    """P19H-3c-R3 — Ask customer to confirm same vs new accident."""
    return "\n".join(
        [
            "【理赔资料收集】",
            "",
            "我看到您这边可能已经有一个未完成的理赔记录。",
            "为了避免把两次事故资料混在一起，请回复：",
            "1 同一个事故，继续补资料",
            "2 新的事故，重新开始",
            "或直接联系陈总。",
            "",
            _CLAIM_SAFE_DISCLAIMER,
        ]
    )


def build_claim_lane_switch_reply() -> str:
    """P19H-2.1 — Claim interrupt prompt while Add Vehicle flow is active."""
    return "\n".join(
        [
            "【理赔资料收集】",
            "",
            "您当前还有一个加车资料流程正在进行。",
            "",
            "如果这是新的事故 / 理赔事项，我们可以先开始理赔资料收集。",
            "",
            "请回复：",
            "1. 开始理赔",
            "2. 继续加车",
            "3. 联系陈总",
            "",
            "我们只会先帮您整理资料，陈总会人工确认。",
            _CLAIM_SAFE_DISCLAIMER,
        ]
    )


def build_claim_question_safe_reply_during_add_vehicle() -> str:
    """P19H-2.1 — Safe claim Q&A while Add Vehicle flow is active."""
    return "\n".join(
        [
            "这是理赔/事故相关问题。我们不能判断责任或 coverage。",
            "您可以回复『开始理赔』开始资料收集，或回复『继续加车』回到当前流程。",
            "",
            _CLAIM_SAFE_DISCLAIMER,
        ]
    )


def build_add_vehicle_continue_reply() -> str:
    """P19H-2.1 — Resume Add Vehicle after lane-switch choice."""
    return "好的，我们继续加车资料流程。您可以回复：进度。"


def build_lane_switch_broker_contact_reply() -> str:
    """P19H-2.1 — Broker contact after lane-switch choice."""
    return "\n".join(
        [
            "明白了，我们会告知陈总您希望直接沟通。",
            "陈总会尽快人工跟进。",
        ]
    )


def build_claim_question_safe_reply() -> str:
    return "\n".join(
        [
            "很抱歉听到您遇到事故相关的问题。",
            "",
            "我们不能判断事故责任，也不能承诺 coverage 或是否该报案。",
            "是否报案、是否能赔，需要陈总人工确认。",
            "",
            "如果您愿意，我们可以先帮您整理事故基本资料（时间、地点、简要描述）。",
            "请直接回复，例如：",
            "今天上午10点，在 Irvine Blvd 附近，对方变道刮到我左前门。",
            "",
            _CLAIM_SAFE_DISCLAIMER,
        ]
    )


# ---------------------------------------------------------------------------
# P19E-2 — Add Vehicle Progress Card (status / resume layer)
# ---------------------------------------------------------------------------

_PROGRESS_CARD_TITLE = "【加车资料进度】"
_PROGRESS_MULTI_CAR_TAIL = "如果您同时办理多台车，请联系陈总。"
_PROGRESS_H5_TAIL = "如果按钮打不开，请回复：链接"
_PROGRESS_H5_FALLBACK = "请回复：重新加车 重新开始上传，或联系经纪人。"


def build_add_vehicle_progress_card(
    case: dict[str, Any],
    *,
    progress: dict[str, Any],
    h5_url: str | None = None,
    multiple_open_cases: bool = False,
) -> tuple[str | None, dict[str, Any] | None]:
    """WeCom Progress Card — query-driven status for open add_car cases."""
    phase = str(progress.get("phase") or "").strip()
    lines: list[str] = [_PROGRESS_CARD_TITLE, ""]

    if phase == "phase1_in_progress":
        lines.append("▶️ 第 1 步：上传照片")
        missing = progress.get("missing_photo_labels") or []
        if missing:
            lines.append("还差：")
            for label in missing:
                lines.append(f"○ {label}")
        lines.append("")
        lines.append("请点下面按钮继续上传。")
        body = "\n".join(lines)
        if multiple_open_cases:
            body = f"{body}\n\n{_PROGRESS_MULTI_CAR_TAIL}"
        url = (h5_url or "").strip()
        if url:
            return None, {
                "head_content": body,
                "list": [
                    {"type": "view", "view": {"url": url, "content": "继续上传照片"}},
                    {
                        "type": "click",
                        "click": {"id": "start_add_car_broker", "content": "联系经纪人"},
                    },
                ],
                "tail_content": _PROGRESS_H5_TAIL,
            }
        fallback = f"{body}\n\n{_PROGRESS_H5_FALLBACK}"
        return fallback, None

    if phase in ("phase2_incomplete", "phase2_partial"):
        lines.extend(
            [
                "✅ 照片资料已收到",
                "▶️ 还差文字信息",
                "",
            ]
        )
        collected = progress.get("collected_fields") or []
        if collected:
            lines.append("已收到：")
            for item in collected:
                lines.append(f"✓ {item['label']} — {item['value']}")
            lines.append("")
        missing_fields = progress.get("missing_field_labels") or []
        if missing_fields:
            lines.append("还差：")
            for label in missing_fields:
                lines.append(f"○ {label}")
            lines.append("")
        lines.append("请直接在微信里回复。")
        text = "\n".join(lines)
        if multiple_open_cases:
            text = f"{text}\n\n{_PROGRESS_MULTI_CAR_TAIL}"
        return text, None

    if phase == "phase3_broker_review":
        lines.extend(
            [
                "✅ 照片资料已收到",
                "✅ 文字信息已收到",
                "▶️ 陈总人工确认中",
                "",
                "目前不需要您补资料。",
                "确认后会通过微信或电话跟进。",
            ]
        )
        text = "\n".join(lines)
        if multiple_open_cases:
            text = f"{text}\n\n{_PROGRESS_MULTI_CAR_TAIL}"
        return text, None

    if phase == "broker_done":
        lines.extend(
            [
                "✅ 照片资料已收到",
                "✅ 文字信息已收到",
                "✅ 陈总已处理",
                "",
                "请留意微信或电话。",
                "如需办理其他事项，直接回复即可。",
            ]
        )
        text = "\n".join(lines)
        if multiple_open_cases:
            text = f"{text}\n\n{_PROGRESS_MULTI_CAR_TAIL}"
        return text, None

    return build_slice_reply("unclear", guided_menu=True), build_guided_menu_payload()


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


# ---------------------------------------------------------------------------
# P19A — WeCom media intake safe replies (no OCR, no coverage/driving advice)
# ---------------------------------------------------------------------------

_MEDIA_ACK_BOUND = (
    "收到图片，我先把它放到您的服务 case 里，陈总会人工查看确认。"
)

_MEDIA_ACK_UNASSIGNED = (
    "收到图片。为了放到正确的服务事项里，请问这是加车资料、保单/续保资料、理赔照片，还是 DMV/停保通知？"
)

_MEDIA_ACK_COVERAGE = (
    "收到通知图片。这个属于高风险保单状态问题，需要陈总人工核实。"
    "线上不能判断您是否仍有保障，也不能建议您是否可以开车。"
)

_MEDIA_ACK_CLAIM = (
    "收到事故照片。请先确认人是否安全，我会把照片放到理赔服务 case 里，陈总会人工联系您。"
)

_MEDIA_ACK_CLAIM_GUIDED_BOUND = (
    "收到照片，已记到这份事故记录里 ✅\n"
    "陈总会整理确认，不用重复发同一张。\n"
    "您也可以继续用文字补充说明。"
)

_MEDIA_ACK_CLAIM_BROKER_CONFIRM = (
    "照片已收到。为了避免把两次事故资料混在一起，陈总会人工确认后整理。"
)

_MEDIA_ACK_CLAIM_NO_OPEN = (
    "照片已收到。如果这是理赔相关，请简单回复「我要理赔」，我会帮您开始整理。"
)


# P19D-1 — strict upload guardrail customer copy (no OCR language)
_GUARD_BULK_CONFIRM = (
    "已收到多张图片。为了避免资料放错或误传隐私照片，请确认这些图片是否都属于同一个服务事项。"
    "当前系统会先处理第一张，其余先标记为待确认。"
)

_GUARD_BULK_PAUSE = (
    "已收到多张图片。为了避免误传隐私照片或资料放错，请先暂停上传。"
    "请确认这些图片是否都属于同一个服务事项，陈总会人工查看。"
)

_GUARD_CLAIM_BATCH = (
    "已收到这一批事故照片。请确认这些都是同一次事故的照片，确认后再继续上传下一批。"
)

_GUARD_ONE_PHOTO = (
    "为了避免资料放错，请一次只上传当前这一步需要的一张图片。"
)


def build_claim_wecom_media_reply(*, tier: str) -> str:
    """P19H-3d — Tier A/B/C customer ack for WeCom claim image binding."""
    normalized = (tier or "").strip().upper()
    if normalized == "A":
        return _MEDIA_ACK_CLAIM_GUIDED_BOUND
    if normalized == "B":
        return _MEDIA_ACK_CLAIM_BROKER_CONFIRM
    if normalized == "C":
        return _MEDIA_ACK_CLAIM_NO_OPEN
    return _MEDIA_ACK_UNASSIGNED


def build_guardrail_media_reply(
    *,
    reply_kind: str,
    bound: bool,
    service_lane: str | None = None,
    binding_confidence: str = "unknown",
    claim_media_reply_tier: str | None = None,
) -> str:
    """Select safe customer reply for guardrail outcome. Never mentions OCR."""
    if claim_media_reply_tier:
        return build_claim_wecom_media_reply(tier=claim_media_reply_tier)
    kind = (reply_kind or "single_image").strip().lower()
    if kind == "bulk_pause":
        return _GUARD_BULK_PAUSE
    if kind == "bulk_confirm":
        return _GUARD_BULK_CONFIRM
    if kind in ("claim_batch", "claim_over_limit"):
        return _GUARD_CLAIM_BATCH
    if kind == "one_photo":
        return _GUARD_ONE_PHOTO
    return build_media_intake_reply(
        bound=bound,
        service_lane=service_lane,
        binding_confidence=binding_confidence,
    )


def build_media_intake_reply(
    *,
    bound: bool,
    service_lane: str | None = None,
    binding_confidence: str = "unknown",
    claim_media_reply_tier: str | None = None,
) -> str:
    """Safe customer ack for WeCom image/file intake. Never mentions OCR."""
    if claim_media_reply_tier:
        return build_claim_wecom_media_reply(tier=claim_media_reply_tier)
    lane = (service_lane or "").strip()
    if bound and lane == "coverage_risk":
        return _MEDIA_ACK_COVERAGE
    if bound and lane == "claim_lite":
        return _MEDIA_ACK_CLAIM
    if bound and lane == "claim" and binding_confidence in ("high", "medium"):
        return _MEDIA_ACK_CLAIM_GUIDED_BOUND
    if bound and binding_confidence in ("high", "medium"):
        return _MEDIA_ACK_BOUND
    return _MEDIA_ACK_UNASSIGNED
