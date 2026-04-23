"""
Customer-visible handoff reply composition (phrases + stitched overrides).

Orchestration and gating stay in triage.py; this module assembles copy from
handoff_phrases.json, stitched client blocks, and post-submit pools.
"""

from __future__ import annotations

import re
from typing import Any

from services.fiqa_api.inbox_triage.add_car_intent import ResolvedAddCarIntent

# Internal / staging markers that must never reach customer-visible copy.
_CLIENT_VISIBLE_MARKER_RE = re.compile(
    r"\[\s*(?:客户|系统|internal)\s*\]\s*",
    re.IGNORECASE,
)
from services.fiqa_api.inbox_triage.add_car_triage_post_submit import (
    ADD_CAR_OFFICE_RECEIPT_PRE_FALLBACK_EN,
    ADD_CAR_OFFICE_RECEIPT_PRE_FALLBACK_ZH,
    POST_SUBMIT_ADD_CAR_FALLBACK_POOLS,
    post_submit_add_car_fallback_line,
    post_submit_rot_idx,
)
from services.fiqa_api.inbox_triage.reply_template_composer import render_family
from services.fiqa_api.inbox_triage.reply_template_policy import (
    FAMILY_HANDOFF_CORRECTION_ACK,
    other_corrected_urgency_uses_stitched_line,
)


def stitched_customer_visible_line(
    stitched: dict[str, Any],
    key: str,
    lang: str,
    default_zh: str,
    default_en: str,
) -> str:
    """One zh/en line from a pre-loaded stitched map; defaults when client omits key."""
    block = stitched.get(key)
    if not isinstance(block, dict):
        return default_zh if lang == "zh" else default_en
    if lang == "zh":
        v = (block.get("zh") or "").strip()
        return v or default_zh
    v = (block.get("en") or "").strip()
    return v or default_en


def stitched_customer_visible_line_prefer(
    stitched: dict[str, Any],
    primary_key: str,
    post_submit_key: str,
    lang: str,
    default_zh: str,
    default_en: str,
    *,
    use_post_submit: bool,
    default_zh_post: str | None = None,
    default_en_post: str | None = None,
) -> str:
    """Prefer *_submitted stitched block when post-submit truth allows and pack provides it."""
    if use_post_submit:
        block = stitched.get(post_submit_key)
        if isinstance(block, dict):
            if lang == "zh":
                v = (block.get("zh") or "").strip()
                if v:
                    return v
            else:
                v = (block.get("en") or "").strip()
                if v:
                    return v
        if default_zh_post is not None:
            return default_zh_post if lang == "zh" else (default_en_post or default_en)
    return stitched_customer_visible_line(stitched, primary_key, lang, default_zh, default_en)


def finalize_client_reply(text: str, context: dict | None = None) -> str:
    """
    Last-mile cleanup for customer-visible client_reply_draft. Does not change triage policy.
    """
    t = (text or "").strip()
    if not t:
        return ""

    t = _CLIENT_VISIBLE_MARKER_RE.sub("", t)

    t = re.sub(r"(?<=\d)\.(?=[A-Za-z])", ". ", t)
    t = re.sub(r"(?<![0-9])(\d{5})([A-Z][a-z]+)", r"\1 \2", t)
    t = re.sub(r"(?<![0-9])(\d{4})([A-Z][a-z]+)", r"\1 \2", t)
    t = re.sub(r"([\u4e00-\u9fff])([A-Za-z0-9])", r"\1 \2", t)
    t = re.sub(r"([A-Za-z0-9])([\u4e00-\u9fff])", r"\1 \2", t)

    t = re.sub(r"(?i)\bThanks,\s*(\d{4})\b", r"Got it, \1 model.", t)

    t = re.sub(r"[\t\n]+", " ", t)
    t = re.sub(r" {2,}", " ", t).strip()
    return t


def apply_client_reply_finalize_to_result(
    result: dict[str, Any], context: dict | None = None
) -> None:
    d = result.get("client_reply_draft")
    if not isinstance(d, str):
        return
    result["client_reply_draft"] = finalize_client_reply(d, context)


def compose_handoff_reply(
    *,
    language: str,
    handoff: bool,
    key: str,
    is_add_car: bool,
    is_remove_car: bool,
    follow_up_type: str,
    post_submit_phrasing: bool,
    customer_turn_index: int,
    last_customer_raw: str,
    merged_text: str,
    handoff_phrases: dict[str, dict[str, str]],
    stitched_cfg: dict[str, Any],
    add_car_handoff_base_key: str,
    add_car_resolved_intent: ResolvedAddCarIntent | None,
    phrases: dict[str, str],
    issue_category: str,
    tailored_doc_clarification_reply: str,
    has_doc_clarification: bool,
    prospective_send_prefix: str,
    last_customer_lower: str,
    add_car_materials_sent: bool,
    reply_template_families: dict[str, Any] | None = None,
) -> str:
    """
    Assemble final handoff string for the current language. Expects triage to pass
    precomputed doc-clarification and prospective-send prefixes where applicable.
    """
    if not handoff:
        return ""

    _intent_f = add_car_resolved_intent.intent_family if add_car_resolved_intent is not None else None
    _rot = post_submit_rot_idx(customer_turn_index, add_car_handoff_base_key or "", _intent_f)

    why_still_chasing = any(
        m in last_customer_raw.lower()
        for m in ("怎么还在追", "为什么还在追", "为什么还追", "怎么还追", "why still", "why are they still")
    )
    if key == "other_received" and why_still_chasing:
        wsc = stitched_cfg.get("why_still_chasing_reassurance")
        wsc_d: dict[str, str] = wsc if isinstance(wsc, dict) else {}
        handoff_reply_zh = (wsc_d.get("zh") or "").strip() or (
            "有时提醒和实际到账不同步。办公室会尽快核实；有结果会联系您。"
        )
        handoff_reply_en = (wsc_d.get("en") or "").strip() or (
            "Reminders sometimes arrive before the file updates. Our office will verify and follow up with you."
        )
    else:
        zh_alt = (phrases.get("zh_alt") or "").strip() if isinstance(phrases, dict) else ""
        en_alt = (phrases.get("en_alt") or "").strip() if isinstance(phrases, dict) else ""
        use_alt = (
            key == "add_car"
            and not post_submit_phrasing
            and customer_turn_index >= 2
            and bool(zh_alt or en_alt)
            and (customer_turn_index % 2 == 0)
        )
        _engine_post_submit_pool = bool(
            is_add_car
            and post_submit_phrasing
            and add_car_handoff_base_key
            and add_car_handoff_base_key in POST_SUBMIT_ADD_CAR_FALLBACK_POOLS
        )
        fb_zh = (
            post_submit_add_car_fallback_line(add_car_handoff_base_key, "zh", rot_idx=_rot)
            if _engine_post_submit_pool
            else None
        )
        fb_en = (
            post_submit_add_car_fallback_line(add_car_handoff_base_key, "en", rot_idx=_rot)
            if _engine_post_submit_pool
            else None
        )
        if _engine_post_submit_pool and fb_zh:
            handoff_reply_zh = fb_zh
        else:
            handoff_reply_zh = (phrases.get("zh") or "").strip() or (
                ADD_CAR_OFFICE_RECEIPT_PRE_FALLBACK_ZH
                if (is_add_car and key == "add_car_office_receipt" and not post_submit_phrasing)
                else (
                    "加车要点已整理进本条服务记录；请在入口完成正式提交办公室后，同事才会在队列里接收并核对，随后出价并联系您。"
                    if is_add_car
                    else "您说的卖车信息已整理好了，办公室会尽快处理，有结果会联系您。" if is_remove_car
                    else "您说的情况已整理好了，办公室会尽快处理，有结果会联系您。"
                )
            )
        if _engine_post_submit_pool and fb_en:
            handoff_reply_en = fb_en
        else:
            handoff_reply_en = (phrases.get("en") or "").strip() or (
                ADD_CAR_OFFICE_RECEIPT_PRE_FALLBACK_EN
                if (is_add_car and key == "add_car_office_receipt" and not post_submit_phrasing)
                else (
                    "Your add-car details are on this service record—after formal submit in the portal, our office will receive it in the queue, verify, price, and follow up."
                    if is_add_car
                    else "Got your vehicle removal details. Our office will process this and follow up with you." if is_remove_car
                    else "Got it. We've noted your info—our office will review and follow up with you."
                )
            )
        if use_alt:
            if zh_alt and language == "zh":
                handoff_reply_zh = zh_alt
            elif en_alt and language != "zh":
                handoff_reply_en = en_alt
        use_alt_post_submit = (
            post_submit_phrasing
            and is_add_car
            and customer_turn_index >= 3
            and bool(zh_alt or en_alt)
            and (customer_turn_index % 2 == 0)
            and not _engine_post_submit_pool
        )
        if use_alt_post_submit:
            if zh_alt and language == "zh":
                handoff_reply_zh = zh_alt
            elif en_alt and language != "zh":
                handoff_reply_en = en_alt

    handoff_reply = handoff_reply_zh if language == "zh" else handoff_reply_en

    if (
        is_add_car
        and follow_up_type == "clarification_question"
        and "[系统]" in (merged_text or "")
    ):
        hr_zh = stitched_customer_visible_line_prefer(
            stitched_cfg,
            "add_car_clarification_followup",
            "add_car_clarification_followup_submitted",
            "zh",
            "收到。办公室按您已发资料逐条核对；仅在有缺项时再联系您。",
            "Got it. Our office will check what you sent line by line and only follow up if something is still missing.",
            use_post_submit=post_submit_phrasing,
            default_zh_post="收到。办公室会按当前服务记录与您已发资料继续核对；仅在有缺项时再联系您。",
            default_en_post="Got it. Our office will continue checking against your current service record and what you sent, and will follow up only if something is still missing.",
        )
        hr_en = stitched_customer_visible_line_prefer(
            stitched_cfg,
            "add_car_clarification_followup",
            "add_car_clarification_followup_submitted",
            "en",
            "收到。办公室按您已发资料逐条核对；仅在有缺项时再联系您。",
            "Got it. Our office will check what you sent line by line and only follow up if something is still missing.",
            use_post_submit=post_submit_phrasing,
            default_zh_post="收到。办公室会按当前服务记录与您已发资料继续核对；仅在有缺项时再联系您。",
            default_en_post="Got it. Our office will continue checking against your current service record and what you sent, and will follow up only if something is still missing.",
        )
        handoff_reply = hr_zh if language == "zh" else hr_en

    if has_doc_clarification and (key == "other_clarification" or is_add_car):
        tailored = tailored_doc_clarification_reply
        if tailored and len(tailored) > 30 and (
            "garaging" in tailored.lower() or "停放" in tailored or "declaration" in tailored.lower()
        ):
            handoff_suffix_zh = (
                stitched_customer_visible_line_prefer(
                    stitched_cfg,
                    "handoff_doc_clarification_suffix_add_car",
                    "handoff_doc_clarification_suffix_add_car_submitted",
                    "zh",
                    "。加车要点已记入本条记录；请在入口完成正式提交办公室后，由同事在队列中跟进，有结果会联系您。",
                    " Your add-car details are on this record—after formal submit, our office will pick it up in the queue and follow up.",
                    use_post_submit=post_submit_phrasing,
                    default_zh_post="。加车要点已记入本条办公室可见记录；办公室会按当前记录继续核对，有结果会联系您。",
                    default_en_post=" Your add-car details are on the office-visible record; our office will continue verification from the current record and follow up.",
                )
                if is_add_car
                else stitched_customer_visible_line(
                    stitched_cfg,
                    "handoff_doc_clarification_suffix_other",
                    "zh",
                    "。办公室会尽快处理，有结果会联系您。",
                    ". Our office will process this and follow up with you.",
                )
            )
            handoff_suffix_en = (
                stitched_customer_visible_line_prefer(
                    stitched_cfg,
                    "handoff_doc_clarification_suffix_add_car",
                    "handoff_doc_clarification_suffix_add_car_submitted",
                    "en",
                    "。加车要点已记入本条记录；请在入口完成正式提交办公室后，由同事在队列中跟进，有结果会联系您。",
                    " Your add-car details are on this record—after formal submit, our office will pick it up in the queue and follow up.",
                    use_post_submit=post_submit_phrasing,
                    default_zh_post="。加车要点已记入本条办公室可见记录；办公室会按当前记录继续核对，有结果会联系您。",
                    default_en_post=" Your add-car details are on the office-visible record; our office will continue verification from the current record and follow up.",
                )
                if is_add_car
                else stitched_customer_visible_line(
                    stitched_cfg,
                    "handoff_doc_clarification_suffix_other",
                    "en",
                    "。办公室会尽快处理，有结果会联系您。",
                    ". Our office will process this and follow up with you.",
                )
            )
            handoff_suffix = handoff_suffix_zh if language == "zh" else handoff_suffix_en
            handoff_reply = tailored.rstrip("。.") + handoff_suffix

    has_coverage_question = any(
        m in last_customer_lower
        for m in (
            "coverage 可以调",
            "coverage 可以调吗",
            "coverage 能调",
            "顺便 coverage",
            "coverage 能改",
            "coverage adjust",
        )
    )
    if is_add_car and has_coverage_question:
        coverage_answer_zh = stitched_customer_visible_line(
            stitched_cfg,
            "handoff_add_car_coverage_answer",
            "zh",
            "保额可以调整，报价时办公室会跟您确认。",
            "Coverage can be adjusted; the office will confirm options when quoting.",
        )
        coverage_answer_en = stitched_customer_visible_line(
            stitched_cfg,
            "handoff_add_car_coverage_answer",
            "en",
            "保额可以调整，报价时办公室会跟您确认。",
            "Coverage can be adjusted; the office will confirm options when quoting.",
        )
        coverage_answer = coverage_answer_zh if language == "zh" else coverage_answer_en
        handoff_suffix_zh = stitched_customer_visible_line_prefer(
            stitched_cfg,
            "handoff_add_car_coverage_suffix",
            "handoff_add_car_coverage_suffix_submitted",
            "zh",
            "要点已记入本条记录；正式提交办公室后，同事会在队列中核对并尽快出价，有结果会联系您。",
            "Details are on this record—after formal submit, our office will verify in the queue, price, and follow up.",
            use_post_submit=post_submit_phrasing,
            default_zh_post="要点已在办公室可见记录里；办公室会结合当前记录继续核对与报价准备，有结果会联系您。",
            default_en_post="The details are on the office-visible record; our office will continue verification and quote prep from the current record and follow up.",
        )
        handoff_suffix_en = stitched_customer_visible_line_prefer(
            stitched_cfg,
            "handoff_add_car_coverage_suffix",
            "handoff_add_car_coverage_suffix_submitted",
            "en",
            "要点已记入本条记录；正式提交办公室后，同事会在队列中核对并尽快出价，有结果会联系您。",
            "Details are on this record—after formal submit, our office will verify in the queue, price, and follow up.",
            use_post_submit=post_submit_phrasing,
            default_zh_post="要点已在办公室可见记录里；办公室会结合当前记录继续核对与报价准备，有结果会联系您。",
            default_en_post="The details are on the office-visible record; our office will continue verification and quote prep from the current record and follow up.",
        )
        handoff_suffix = handoff_suffix_zh if language == "zh" else handoff_suffix_en
        handoff_reply = coverage_answer + " " + handoff_suffix

    if is_add_car and prospective_send_prefix:
        handoff_reply = prospective_send_prefix + handoff_reply

    if is_add_car and add_car_materials_sent:
        ams = stitched_cfg.get("add_car_materials_sent")
        ams_sub = stitched_cfg.get("add_car_materials_sent_submitted")
        ams_d: dict[str, str] = ams if isinstance(ams, dict) else {}
        ams_sub_d: dict[str, str] = ams_sub if isinstance(ams_sub, dict) else {}
        if post_submit_phrasing:
            handoff_reply_zh = (ams_sub_d.get("zh") or "").strip() or (
                "收到。办公室正按当前服务记录核对您已发的加车材料；无需整套重发，缺项会主动联系您。"
            )
            handoff_reply_en = (ams_sub_d.get("en") or "").strip() or (
                "Thanks—our office is verifying what you sent against your current add-car record. "
                "No need to resend the full set; we will reach out only if something is still missing."
            )
        else:
            handoff_reply_zh = (ams_d.get("zh") or "").strip() or (
                "收到。办公室正核对您已发的加车材料；无需整套重发，缺项会主动联系您。"
            )
            handoff_reply_en = (ams_d.get("en") or "").strip() or (
                "Thanks—our office is verifying what you sent for this add-car quote. "
                "No need to resend the full set; we will reach out only if something is still missing."
            )
        handoff_reply = handoff_reply_zh if language == "zh" else handoff_reply_en

    if key == "other_corrected":
        urgency_next_markers = (
            "最要紧",
            "先干嘛",
            "先看什么",
            "办公室先看什么",
            "what matters most",
            "what should i do",
            "is this urgent",
            "是不是今天",
            "一定要处理",
        )
        has_embedded_question = any(m in last_customer_lower for m in urgency_next_markers)
        if has_embedded_question and issue_category in ("payment_lapse_expiration", "cancellation_warning"):
            if language == "zh":
                handoff_reply = stitched_customer_visible_line(
                    stitched_cfg,
                    "handoff_payment_correction_urgency",
                    "zh",
                    "您这边最要紧的是等办公室确认付款是否到账；如果确认了您这边就不用再做什么。办公室会尽快处理，有结果会联系您。",
                    "The most important thing for you now is to wait for our office to confirm whether the payment was received; if confirmed, you don't need to do anything else. Our office will process this and follow up with you.",
                )
            else:
                handoff_reply = stitched_customer_visible_line(
                    stitched_cfg,
                    "handoff_payment_correction_urgency",
                    "en",
                    "您这边最要紧的是等办公室确认付款是否到账；如果确认了您这边就不用再做什么。办公室会尽快处理，有结果会联系您。",
                    "The most important thing for you now is to wait for our office to confirm whether the payment was received; if confirmed, you don't need to do anything else. Our office will process this and follow up with you.",
                )

    if (
        key == "other_corrected"
        and reply_template_families
        and not other_corrected_urgency_uses_stitched_line(issue_category, last_customer_lower)
    ):
        handoff_reply = render_family(
            reply_template_families,
            FAMILY_HANDOFF_CORRECTION_ACK,
            language,
            None,
            handoff_reply,
        )

    return handoff_reply
