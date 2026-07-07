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
加车资料收集

请点下方按钮，按顺序上传 3 张照片：
1. VIN 照片
2. 行驶证 / registration
3. 保险卡，可选

大约 2 分钟，不用填长表格。"""

_H5_PHOTO_FLOW_BUTTON = "开始上传照片"

_H5_PHOTO_FLOW_TAIL_PREFIX = """\
照片在页面里上传；提车日期、停车 ZIP、联系电话稍后回微信打字。
陈总会人工审核，不会自动修改您的保单。"""

_H5_PHOTO_FLOW_START_CARD_TAIL = """\
照片在页面里上传；提车日期、停车 ZIP、联系电话稍后回微信打字。
陈总会人工审核，不会自动修改您的保单。

如果按钮打不开，请回复：链接"""


def build_h5_vin_start_card_payload(*, h5_url: str, restart_intro: bool = False) -> dict[str, Any]:
    """WeCom msgmenu: H5 Add Vehicle photo flow view button + Later / Talk to Broker."""
    url = (h5_url or "").strip()
    tail = _H5_PHOTO_FLOW_START_CARD_TAIL
    head = _H5_PHOTO_FLOW_START_HEAD
    if restart_intro:
        head = "好的，我们重新开始一组加车资料收集。\n\n" + head
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
        f"开始上传照片：{url}\n\n"
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
    completed, skipped = _h5_photo_slots_from_case(case)
    lines = [
        "【第 1 阶段完成 ✅ · 照片资料】",
        "",
        "已收到：",
        f"✓ {_H5_PHOTO_SLOT_LABELS['vin_photo']}",
        f"✓ {_H5_PHOTO_SLOT_LABELS['registration_photo']}",
    ]
    if "insurance_card_photo" in completed:
        lines.append(f"✓ {_H5_PHOTO_SLOT_LABELS['insurance_card_photo']}")
    elif "insurance_card_photo" in skipped:
        lines.append("○ 保险卡 — 可稍后补")
    else:
        lines.append(f"✓ {_H5_PHOTO_SLOT_LABELS['insurance_card_photo']}")
    lines.extend(
        [
            "",
            "──────────",
            "【下一步 · 第 2 步：补充文字信息】",
            "",
            "请直接在本聊天打字发送：",
            "1. 提车日期（例：7月10日）",
            "2. 停放 ZIP（例：92705）",
            "3. 联系电话",
            "",
            "陈总会人工查看并确认，不会自动修改您的保单。",
        ]
    )
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
            "请直接在本聊天补充：",
            "1. 提车日期",
            "2. 停放 ZIP",
            "3. 联系电话",
        ]
        return "\n".join(lines)

    lines = ["【加车资料 · 第 2 步进行中】", "", "已收到："]
    for field in PHASE2_TEXT_FIELDS:
        if field in collected_names:
            lines.append(f"✓ {_FIELD_LABELS_ZH[field]} — {_field_display_value(case, field)}")
    lines.append("")
    if still:
        lines.append(f"还差 {len(still)} 项：")
        for field in still:
            lines.append(f"○ {_FIELD_LABELS_ZH[field]} — 请直接打字回复")
    return "\n".join(lines)


def build_phase2_stage_complete_s2_reply(case: dict[str, Any]) -> str:
    """Stage Complete S2 — Phase 2 text fields done; hand off to broker review."""
    from services.fiqa_api.wecom.add_vehicle_phase2 import _FIELD_LABELS_ZH, PHASE2_TEXT_FIELDS

    lines = [
        "【第 2 阶段完成 ✅ · 文字信息】",
        "",
        "已收到：",
    ]
    for field in PHASE2_TEXT_FIELDS:
        lines.append(f"✓ {_FIELD_LABELS_ZH[field]}")
    lines.extend(
        [
            "",
            "──────────",
            "【下一步 · 第 3 步：陈总人工确认】",
            "",
            "资料已基本收齐，已转陈总审核。",
            "陈总会人工查看，不会自动修改您的保单。",
            "确认后我们会通过微信或电话跟进，请留意消息。",
        ]
    )
    return "\n".join(lines)


def build_phase2_unrecognized_fields_reply() -> str:
    """When Phase 2 is active but no structured fields could be parsed from free text."""
    return "\n".join(
        [
            "【加车资料 · 第 2 步】",
            "",
            "我还没有识别到提车日期、停放 ZIP 或联系电话。",
            "请按这个格式直接回复，例如：",
            "7月10号提车，ZIP 92705，电话 949-123-4567",
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
        lines.append("请点击继续上传照片。")
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
                "✅ 第 1 步：照片资料已收到",
                "▶️ 第 2 步：补充文字信息",
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
        if phase == "phase2_partial":
            lines.append("请继续在本聊天打字回复。")
        else:
            lines.append("请直接在本聊天打字回复。")
        text = "\n".join(lines)
        if multiple_open_cases:
            text = f"{text}\n\n{_PROGRESS_MULTI_CAR_TAIL}"
        return text, None

    if phase == "phase3_broker_review":
        lines.extend(
            [
                "✅ 第 1 步：照片资料已收到",
                "✅ 第 2 步：文字信息已收到",
                "▶️ 第 3 步：陈总人工确认中",
                "",
                "目前不需要您补充资料。",
                "陈总会人工查看，不会自动修改您的保单。",
                "确认后我们会通过微信或电话跟进。",
            ]
        )
        text = "\n".join(lines)
        if multiple_open_cases:
            text = f"{text}\n\n{_PROGRESS_MULTI_CAR_TAIL}"
        return text, None

    if phase == "broker_done":
        lines.extend(
            [
                "✅ 第 1 步：照片资料已收到",
                "✅ 第 2 步：文字信息已收到",
                "✅ 第 3 步：陈总已处理 / 已确认",
                "",
                "陈总已处理或正在跟进，请留意微信/电话。",
                "如需办理其他事项，请直接回复。",
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


def build_guardrail_media_reply(
    *,
    reply_kind: str,
    bound: bool,
    service_lane: str | None = None,
    binding_confidence: str = "unknown",
) -> str:
    """Select safe customer reply for guardrail outcome. Never mentions OCR."""
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
) -> str:
    """Safe customer ack for WeCom image/file intake. Never mentions OCR."""
    lane = (service_lane or "").strip()
    if bound and lane == "coverage_risk":
        return _MEDIA_ACK_COVERAGE
    if bound and lane == "claim_lite":
        return _MEDIA_ACK_CLAIM
    if bound and binding_confidence in ("high", "medium"):
        return _MEDIA_ACK_BOUND
    return _MEDIA_ACK_UNASSIGNED
