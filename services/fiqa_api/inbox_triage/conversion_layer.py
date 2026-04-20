"""
Quote-ready → handoff conversion layer (customer reply only).

Conversion Flow V3: one customer-visible ending — completion + single contact ask
(no “quote_ready” wording, no broker jargon). Follow-up turns route on lightweight
post-quote intents. State is carried in triage/workflow_state for session parity.
"""

from __future__ import annotations

import re
from typing import Any

from services.fiqa_api.inbox_triage.config_loader import get_ui_copy

CS_NOT_READY = "not_ready"
CS_READY_ANNOUNCED = "ready_announced"
CS_WAITING_USER_RESPONSE = "waiting_user_response"
CS_USER_ENGAGED = "user_engaged_after_ready"
CS_HANDOFF_CONFIRMED = "handoff_confirmed"
CS_CONTACT_RECEIVED_ACK = "contact_received_ack"

_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?86[\s\-]?)?1[3-9]\d[\s\-]?\d{4}[\s\-]?\d{4}(?!\d)|(?<!\d)1[3-9]\d{9}(?!\d)"
)


def _default_flow_v3(lang: str) -> dict[str, str]:
    """Fallback if client pack omits conversion_flow_v3."""
    if (lang or "").strip().lower() == "zh":
        return {
            "step1_complete": "我们已经帮你准备好报价信息了 ✅",
            "step2_next": "现在只需要一步，我们就可以帮你完成报价",
            "step3_ask_phone": "直接发一个手机号即可",
            "step3_ask_name_phone": "发一下称呼和手机号即可",
            "step3_ask_name": "发一下怎么称呼即可",
            "step4_trust": "不会骚扰，仅用于本次报价",
            "step5_timing": "一般几分钟内会有结果",
            "ack_contact_received": "已收到 👍\n我们正在为你处理报价，一般几分钟内会有结果",
        }
    return {
        "step1_complete": "Your quote details are ready ✅",
        "step2_next": "One quick step left—we can finish your quote request",
        "step3_ask_phone": "Just send a mobile number here",
        "step3_ask_name_phone": "Send your name and mobile number here",
        "step3_ask_name": "Send how we should address you",
        "step4_trust": "No spam—only used for this quote",
        "step5_timing": "You’ll usually hear back within a few minutes",
        "ack_contact_received": "Got it 👍\nWe’re working on your quote now—you’ll usually hear back within a few minutes",
    }


def _get_flow_v3(client_id: str | None, language: str) -> dict[str, str]:
    ui = get_ui_copy(client_id)
    block = ui.get("conversion_flow_v3")
    lang = "zh" if (language or "").strip().lower() == "zh" else "en"
    if isinstance(block, dict):
        raw = block.get(lang)
        if isinstance(raw, dict) and raw:
            merged = {**_default_flow_v3(lang), **{str(k): str(v) for k, v in raw.items() if str(v).strip()}}
            return merged
    return _default_flow_v3(lang)


def _phone_like_token_in_message(text: str) -> bool:
    if not (text or "").strip():
        return False
    return bool(_PHONE_RE.search(text))


def _moment1_v3_no_contact_gap(language: str, client_id: str | None) -> str:
    """Quote slots + contact already satisfied in-thread — single ending, no extra ask."""
    flow = _get_flow_v3(client_id, language)
    return "\n".join([flow["step1_complete"], flow["step2_next"], flow["step4_trust"], flow["step5_timing"]])


def _moment1_v3_contact_gap(language: str, client_id: str | None, still: list[str]) -> str:
    """Quote-ready with only name/phone (or subset) missing — five-step V3 ladder."""
    flow = _get_flow_v3(client_id, language)
    st = {str(x).lower() for x in still if x}
    if "name" in st and "phone" in st:
        step3 = flow["step3_ask_name_phone"]
    elif "phone" in st:
        step3 = flow["step3_ask_phone"]
    elif "name" in st:
        step3 = flow.get("step3_ask_name") or (
            "发一下怎么称呼即可" if (language or "").strip().lower() == "zh" else "Send how we should address you"
        )
    else:
        step3 = flow["step3_ask_phone"]
    return "\n".join([flow["step1_complete"], flow["step2_next"], step3, flow["step4_trust"], flow["step5_timing"]])


def _last_system_reply_text(conversation_turns: list[dict[str, str]]) -> str:
    for t in reversed(conversation_turns or []):
        if (str(t.get("role") or "").strip().lower()) != "system":
            continue
        body = str(t.get("text") or "").strip()
        if body:
            return body
    return ""


def _infer_conversion_from_turns(
    conversation_turns: list[dict[str, str]],
) -> tuple[str | None, int | None]:
    for t in reversed(conversation_turns or []):
        if (str(t.get("role") or "").strip().lower() != "system"):
            continue
        tr = t.get("triageResult") or t.get("triage_result")
        if not isinstance(tr, dict):
            continue
        if str(tr.get("quote_ready_status") or "").strip() != "quote_ready":
            continue
        if not tr.get("conversion_layer_active"):
            continue
        st = str(tr.get("conversion_stage") or "").strip() or None
        li = tr.get("last_conversion_turn_index")
        try:
            idx = int(li) if li is not None else None
        except (TypeError, ValueError):
            idx = None
        return st, idx
    return None, None


def _resolve_prior_conversion(
    prior_workflow_state: dict[str, Any] | None,
    conversation_turns: list[dict[str, str]],
) -> tuple[str, int | None]:
    ws = prior_workflow_state or {}
    st = str(ws.get("conversion_stage") or "").strip()
    li = ws.get("last_conversion_turn_index")
    try:
        idx = int(li) if li is not None else None
    except (TypeError, ValueError):
        idx = None
    if st and st != CS_NOT_READY:
        return st, idx
    t_st, t_idx = _infer_conversion_from_turns(conversation_turns)
    if t_st:
        return t_st, t_idx
    return CS_NOT_READY, None


def _detect_post_quote_intent(last_msg: str, language: str) -> str:
    raw = (last_msg or "").strip()
    lang = (language or "").strip().lower()
    if not raw:
        return "silence"
    tl = raw.lower()

    # Short deferral — user is still engaged; avoid "unrelated" + generic fallback.
    if len(raw) <= 40:
        if lang == "zh":
            if any(
                x in raw
                for x in (
                    "等等",
                    "等下",
                    "晚点再说",
                    "待会再说",
                    "明天再说",
                    "一会儿再说",
                    "等会儿",
                    "先忙",
                    "等一下",
                )
            ):
                return "defer_ack"
        if any(
            x in tl
            for x in (
                "later",
                "not now",
                "in a bit",
                "in a minute",
                "hold on",
                "busy right now",
            )
        ):
            return "defer_ack"

    # Punctuation-only → silence (do not treat 好/ok as silence — use confirmation below)
    if len(raw) <= 2 and raw in (".", "。", "?", "？", "!", "！", "…"):
        return "silence"

    # Ultra-short acknowledgements (language detector can be "en" on mixed VIN/EN threads — CJK acks first)
    if raw in ("好", "行", "嗯", "哦", "好哒", "好滴", "嗯嗯") or (
        len(raw) <= 5 and raw.lower() in ("ok", "okay")
    ):
        return "confirmation"
    if tl in ("ok", "okay", "k", "kk", "yep", "yes", "ya", "yeah", "sure", "ty", "thx"):
        return "confirmation"

    if lang == "zh":
        if any(
            x in raw
            for x in (
                "多久",
                "几天",
                "什么时候",
                "何时",
                "多快",
                "啥时候",
                "出报价",
                "结果",
                "什么时候能",
                "几天能",
            )
        ):
            if any(x in raw for x in ("报价", "结果", "出", "多久", "几天", "什么时候", "多快")):
                return "timeline_question"
        if any(
            x in tl
            for x in (
                "how long",
                "when will",
                "how soon",
                "turnaround",
                "business day",
                "timeline",
            )
        ):
            return "timeline_question"
    else:
        if any(
            x in tl
            for x in (
                "how long",
                "when will",
                "how soon",
                "turnaround",
                "business day",
                "timeline",
            )
        ):
            return "timeline_question"

    if lang == "zh":
        if any(
            x in raw
            for x in (
                "不确定",
                "担心",
                "犹豫",
                "靠谱吗",
                "会不会",
                "太贵",
                "再想想",
                "有点怕",
            )
        ):
            return "hesitation"
    if any(
        x in tl
        for x in (
            "not sure",
            "worried",
            "concern",
            "hesitat",
            "too expensive",
            "is it safe",
            "scam",
        )
    ):
        return "hesitation"

    if lang == "zh":
        if any(
            x in raw
            for x in (
                "好的",
                "好",
                "谢谢",
                "感谢",
                "嗯嗯",
                "明白",
                "收到",
                "了解",
                "行",
                "OK",
                "ok",
            )
        ) and len(raw) <= 24:
            return "confirmation"
    if any(x in tl for x in ("thanks", "thank you", "ok", "okay", "got it", "sounds good", "great", "perfect")):
        if len(raw) <= 48:
            return "confirmation"

    if lang == "zh":
        if any(x in raw for x in ("下一步", "接下来", "怎么", "咋办")):
            return "timeline_question"
    if any(x in tl for x in ("what's next", "what next", "next step")):
        return "timeline_question"

    return "unrelated"


def _handoff_confirm_signal(last_msg: str, language: str) -> bool:
    raw = (last_msg or "").strip()
    if not raw:
        return False
    lang = (language or "").strip().lower()
    tl = raw.lower()
    if lang == "zh":
        if any(x in raw for x in ("请打给我", "打给我", "联系我", "电话我", "方便联系", "可以打")):
            return True
    if any(x in tl for x in ("call me", "you can call", "reach me at", "feel free to call")):
        return True
    return False


def _short_defer_ack(language: str, client_id: str | None, *, contact_open: bool) -> str:
    """User asked to continue later — keep trust, restate timing, nudge contact once if needed."""
    flow = _get_flow_v3(client_id, language)
    lang = (language or "").strip().lower()
    if lang == "zh":
        base = f"没问题 👍 你先忙；有空随时发我。{flow['step5_timing']}内我们会尽力回复。"
        if contact_open:
            return f"{base} {flow['step3_ask_name_phone']}"
        return base
    base = f"No rush 👍 Reply whenever works. We’ll move as fast as we can—{flow['step5_timing'].lower()}."
    if contact_open:
        return f"{base} {flow['step3_ask_name_phone']}"
    return base


def _short_timeline(language: str, client_id: str | None, *, contact_open: bool) -> str:
    flow = _get_flow_v3(client_id, language)
    lang = (language or "").strip().lower()
    base = f"{flow['step5_timing']} 👍"
    if contact_open:
        if lang == "zh":
            return f"{base} {flow['step3_ask_phone']}"
        return f"{base} {flow['step3_ask_phone']}"
    return base


def _short_confirmation(language: str, client_id: str | None, *, contact_open: bool) -> str:
    flow = _get_flow_v3(client_id, language)
    if not contact_open:
        return flow["ack_contact_received"]
    lang = (language or "").strip().lower()
    if lang == "zh":
        return f"好的 👍 {flow['step3_ask_phone']}"
    return f"Got it 👍 {flow['step3_ask_phone']}"


def _short_hesitation(language: str, client_id: str | None, *, contact_open: bool) -> str:
    flow = _get_flow_v3(client_id, language)
    lang = (language or "").strip().lower()
    tail = f"不着急 👍 {flow['step4_trust']}；有问题随时发我。"
    if contact_open:
        if lang == "zh":
            return f"{tail} {flow['step3_ask_phone']}"
        return f"{tail} {flow['step3_ask_phone']}"
    return tail


def _short_unrelated(language: str, client_id: str | None, *, contact_open: bool) -> str:
    flow = _get_flow_v3(client_id, language)
    lang = (language or "").strip().lower()
    msg = f"收到 👍 {flow['step5_timing']}我们会继续推进。"
    if contact_open:
        if lang == "zh":
            return f"{msg} {flow['step3_ask_phone']}"
        return f"{msg} {flow['step3_ask_phone']}"
    return msg


def _short_silence(language: str, client_id: str | None, *, contact_open: bool, passive_nudge: bool) -> str:
    flow = _get_flow_v3(client_id, language)
    lang = (language or "").strip().lower()
    if contact_open:
        if lang == "zh":
            return f"我们在这边继续处理 👍 {flow['step3_ask_name_phone']}"
        return f"We’re on it 👍 {flow['step3_ask_name_phone']}"
    if passive_nudge:
        return f"{flow['step5_timing']} 👍 有更新会第一时间同步你。"
    if lang == "zh":
        return f"好的 👍 {flow['step5_timing']}"
    return f"Sounds good 👍 {flow['step5_timing']}"


def _dedupe_against_last_reply(text: str, last_system: str) -> str:
    if not last_system or not text:
        return text
    if text.strip() == last_system.strip():
        if text.endswith("👍"):
            return text + "\n（如有其他问题也可以直接发我。）"
        return text + " 👍"
    return text


def maybe_apply_quote_ready_conversion_reply(
    result: dict[str, Any],
    *,
    language: str,
    client_id: str | None,
    merged_text: str | None,
    post_submit_phrasing: bool,
    customer_turn_index: int = 1,
    last_customer_message: str = "",
    prior_workflow_state: dict[str, Any] | None = None,
    conversation_turns: list[dict[str, str]] | None = None,
) -> None:
    """
    If quote_ready for add_car (handoff_ready or contact-only gap), set client_reply_draft to V3 conversion copy.
    Tracks conversion_stage / last_conversion_turn_index on result for workflow persistence.
    """
    turns = conversation_turns or []
    result["conversion_layer_active"] = False
    result["conversion_flow_version"] = ""
    result["post_quote_followup_intent"] = ""
    if post_submit_phrasing:
        result["conversion_stage"] = CS_NOT_READY
        return
    if str(result.get("service_type") or "").strip().lower() != "add_car":
        result["conversion_stage"] = CS_NOT_READY
        return
    if str(result.get("quote_ready_status") or "").strip() != "quote_ready":
        result["conversion_stage"] = CS_NOT_READY
        return

    try:
        _ct_v5 = int(customer_turn_index)
    except (TypeError, ValueError):
        _ct_v5 = 1
    # Turn 1 quote_ready: full handoff copy stays on triage draft; contact-only gap still uses conversion ladder.
    if _ct_v5 == 1:
        _s1 = {str(x).lower() for x in (result.get("still_needed_fields") or []) if x}
        _contact_only_t1 = _s1.issubset({"name", "phone"}) and bool(_s1)
        if not result.get("handoff_ready"):
            result["conversion_stage"] = CS_NOT_READY
            return
        # Quote-ready + contact-only gap on turn 1: triage already stitched broker/office handoff copy
        # (IDENTITY_CONTACT_LITE tail). Replacing it with conversion_flow_v3 hides client-pack office lines.
        if _contact_only_t1:
            result["conversion_stage"] = CS_NOT_READY
            return
        if not _contact_only_t1:
            if (result.get("client_reply_draft") or "").strip():
                result["conversion_stage"] = CS_NOT_READY
                return

    still = [str(x).lower() for x in (result.get("still_needed_fields") or []) if x]
    still_set = set(still)
    contact_only_gap = still_set.issubset({"name", "phone"}) and bool(still_set)
    if not result.get("handoff_ready") and not contact_only_gap:
        result["conversion_stage"] = CS_NOT_READY
        return

    contact_open = "name" in still_set or "phone" in still_set
    follow = str(result.get("follow_up_type") or "").strip().lower()
    mt = merged_text or ""
    if follow == "clarification_question" and "[系统]" in mt:
        result["conversion_stage"] = CS_NOT_READY
        return
    # Materials-sent / vehicle-correction handoffs use triage stitched copy (office vs conversion CTA).
    if result.get("handoff_ready") and follow in ("already_sent", "correction"):
        result["conversion_stage"] = CS_NOT_READY
        return

    lang = (language or "").strip().lower()
    ui = get_ui_copy(client_id)
    custom = (ui.get("conversion_quote_ready_reply_zh") or "").strip() if lang == "zh" else (
        ui.get("conversion_quote_ready_reply_en") or ""
    ).strip()

    prior_stage, _ = _resolve_prior_conversion(prior_workflow_state, turns)
    last_system = _last_system_reply_text(turns)
    announced_before = prior_stage in (
        CS_READY_ANNOUNCED,
        CS_WAITING_USER_RESPONSE,
        CS_USER_ENGAGED,
        CS_HANDOFF_CONFIRMED,
        CS_CONTACT_RECEIVED_ACK,
    )
    try:
        ct_idx = int(customer_turn_index)
    except (TypeError, ValueError):
        ct_idx = 1

    # First full block only when quote_ready has not been announced yet in persisted/inferred state.
    first_moment = not announced_before

    intent = _detect_post_quote_intent(last_customer_message, language)
    if _handoff_confirm_signal(last_customer_message, language):
        intent = "confirmation"

    result["post_quote_followup_intent"] = intent if announced_before else ""

    passive_nudge = bool(ct_idx >= 3)

    draft = ""

    if first_moment:
        if custom:
            draft = custom
        elif contact_open:
            draft = _moment1_v3_contact_gap(language, client_id, still)
        else:
            draft = _moment1_v3_no_contact_gap(language, client_id)
        new_stage = CS_WAITING_USER_RESPONSE
    else:
        # Follow-up turns: never repeat the full Moment 1 block (or long custom).
        if not contact_open and _phone_like_token_in_message(last_customer_message):
            draft = _get_flow_v3(client_id, language)["ack_contact_received"]
            new_stage = CS_CONTACT_RECEIVED_ACK
        elif intent == "timeline_question":
            draft = _short_timeline(language, client_id, contact_open=contact_open)
            new_stage = CS_USER_ENGAGED
        elif intent == "hesitation":
            draft = _short_hesitation(language, client_id, contact_open=contact_open)
            new_stage = CS_USER_ENGAGED
        elif intent == "defer_ack":
            draft = _short_defer_ack(language, client_id, contact_open=contact_open)
            new_stage = CS_USER_ENGAGED
        elif intent == "confirmation":
            draft = _short_confirmation(language, client_id, contact_open=contact_open)
            new_stage = CS_CONTACT_RECEIVED_ACK if not contact_open else CS_USER_ENGAGED
        elif intent == "silence":
            draft = _short_silence(
                language,
                client_id,
                contact_open=contact_open,
                passive_nudge=passive_nudge,
            )
            new_stage = CS_USER_ENGAGED
        else:
            draft = _short_unrelated(language, client_id, contact_open=contact_open)
            new_stage = CS_USER_ENGAGED

        if new_stage != CS_CONTACT_RECEIVED_ACK and _handoff_confirm_signal(last_customer_message, language):
            new_stage = CS_HANDOFF_CONFIRMED

    draft = _dedupe_against_last_reply(draft, last_system)

    result["client_reply_draft"] = draft
    result["conversion_layer_active"] = True
    result["conversion_flow_version"] = "v3"
    result["conversion_stage"] = new_stage
    result["last_conversion_turn_index"] = ct_idx