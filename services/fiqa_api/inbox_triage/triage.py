"""
Broker Inbox Triage — Core logic

Uses LLM when available; falls back to rule-based classification when disabled.
Loads markers and handoff phrases from config when available; falls back to hardcoded defaults.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from services.fiqa_api.inbox_triage.config_loader import (
    get_active_client_id,
    get_add_car_rules,
    get_category_templates,
    get_document_item_markers,
    get_handoff_phrases,
    get_insurance_markers,
    get_reply_templates,
    get_workflow_fallbacks,
)
from services.fiqa_api.inbox_triage.notice_retrieval import (
    format_retrieval_augment,
    retrieve_document_explanation,
    retrieve_notice_explanation,
)

logger = logging.getLogger(__name__)

# Config cache: loaded once, fallback to hardcoded when empty
_MARKERS_CACHE: dict[str, tuple[str, ...]] | None = None
_DOCUMENT_ITEMS_CACHE: tuple[tuple[tuple[str, ...], str, str], ...] | None = None
_HANDOFF_CACHE: dict[str, dict[str, dict[str, str]]] = {}  # client_id -> phrases
_REPLY_TEMPLATES_CACHE: dict[str, Any] | None = None
_CATEGORY_TEMPLATES_CACHE: dict[str, dict[str, str]] | None = None
_WORKFLOW_FALLBACKS_CACHE: dict[str, str] | None = None

# Required output fields per BROKER_INBOX_TRIAGE_STANDARD.md
REQUIRED_FIELDS = (
    "issue_category",
    "urgency",
    "broker_next_step",
    "client_prep",
    "client_reply_draft",
    "manual_followup_needed",
)

# Workflow state backbone (STATE_WORKFLOW_BACKBONE_SPRINT, Phase 2)
# All keys that define conversation/workflow progression. Persist in case_store.
WORKFLOW_STATE_KEYS = (
    "collection_stage",
    "follow_up_type",
    "handoff_ready",
    "case_creation_suggested",
    "collected_fields",
    "still_needed_fields",
    "human_confirmation_required",
    "human_confirmation_fields",
    "next_best_question",  # Phase 2: what to ask when handoff_ready=false
    "lifecycle_status",  # Phase 2: collecting | handoff_pending | handed_off | office_followup
)

VALID_URGENCIES = ("low", "medium", "high", "critical")
VALID_CATEGORIES = (
    "missing_signature",
    "missing_document",
    "cancellation_warning",
    "policy_delay_pending",
    "underwriting_followup",
    "renewal_reminder",
    "customer_question",
    "customer_requested_human",
    "payment_lapse_expiration",
    "informational",
    "unclear",
)

RULE_GUIDANCE_CATEGORIES = (
    "cancellation_warning",
    "payment_lapse_expiration",
    "missing_document",
    "underwriting_followup",
    "customer_question",
    "customer_requested_human",
    "unclear",
)

DRAFT_QUALITY_PHRASES: dict[str, tuple[str, ...]] = {
    "cancellation_warning": ("cancellation", "cancel", "urgent"),
    "payment_lapse_expiration": ("payment", "lapse", "coverage"),
    "missing_document": ("document", "copy", "send"),
}

FORMAL_DRAFT_MARKERS = (
    "dear ",
    "best regards",
    "sincerely",
    "thank you for reaching out",
    "尊敬的",
    "期待您的回复",
)

# Fallback markers when config is missing (configs/industries/insurance/markers.json)
_FALLBACK_MARKERS: dict[str, tuple[str, ...]] = {
    "question_help": (
        "什么意思", "what does this mean", "what does", "我需要做什么", "怎么办",
        "看不懂", "没看懂", "看不太懂", "不知道怎么弄", "can you check", "can you help", "please help",
        "是不是要处理", "一定要处理", "is this urgent", "urgent?",
    ),
    "strong_cancellation": (
        "cancelled", "cancellation", "non-payment", "last notice", "7 days due to non-payment",
        "cancel pending", "即将因未缴款而被取消", "未缴款",
    ),
    "weak_cancellation": ("cancel", "取消", "要取消"),
    "payment": (
        "payment failed", "auto pay failed", "autopay failed", "declined", "update payment",
        "update card", "card on file", "retry payment", "interruption in coverage",
        "avoid interruption in coverage",
    ),
    "payment_risk": ("overdue", "past due", "late payment", "billing overdue", "账单 overdue", "payment overdue"),
    "policy_stop": (
        "policy may lapse", "policy lapse", "policy may cancel", "policy will cancel",
        "保单要停", "保单要停了", "停保", "会停保", "要停了",
    ),
    "dmv_help": ("dmv", "sr-22", "sr22", "suspension", "suspension clearance"),
    "dmv_status": (
        "dmv已经收到", "dmv 收到", "dmv那边有没有收到", "dmv那边收到", "收到保险证明",
        "保险证明了吗", "proof of insurance", "dmv got", "dmv received",
    ),
    "premium_review": (
        "premium too high", "rate too high", "renewal review", "renewal premium",
        "保费太高", "保费太贵", "太高了", "太贵了", "怎么降一点", "怎么降保费",
        "能不能便宜一点", "能不能便宜", "lower the premium",
        "续保", "续保涨", "有办法", "其中一辆", "去掉会便宜", "保单我发",
    ),
    "add_vehicle": (
        "add a car", "add car", "add vehicle", "加车", "加一台", "加一辆", "新车", "提车", "拿车",
        "先出报价", "先报价", "报价", "多少钱", "new car", "bought a", "bought",
        "how much is insurance", "how much for insurance", "insurance for", "quote for", "how much",
        "买了", "保费多少钱", "保费多少", "保费是多少", "刚买车", "刚买", "才买", "保险大概", "保费大概", "多少钱左右",
        "picking up", "pick up",
    ),
    "remove_vehicle": (
        "remove car", "remove vehicle", "drop vehicle", "take it off", "拿掉", "删掉", "删车",
        "去掉", "卖掉旧车", "卖掉了", "卖车", "sold",
    ),
    "vehicle_context": (
        "vin", "vehicle", "model", "tesla", "toyota", "honda", "bmw", "mercedes", "lexus",
        "x5", "accord", "camry", "corolla", "花冠", "车", "车型", "宝马", "丰田", "sold",
    ),
    "missing_document_object": (
        "driver's license", "driver license", "declaration page", "dec page", "decl page",
        "garaging proof", "proof of garaging", "驾照", "document", "copy", "材料",
    ),
    "missing_document_request": (
        "request", "requested", "needs", "need", "missing", "still need", "还缺", "缺", "缺什么", "需要",
        "寄了", "already sent", "sent it last week", "sent it", "发过了", "上周发过了", "又发了",
        "resend", "re-send", "escrow", "underwriting", "uw", "follow up", "follow-up",
    ),
    "claim_intake": (
        "accident", "car accident", "accident just happened", "报事故", "出事故", "刚出事故", "出险", "理赔", "撞车", "撞了",
        "对方跑了", "出事了", "要拍什么",
        "claim", "file a claim", "what should i collect", "what to collect", "other driver",
        "other driver's insurance", "other driver's license", "photos", "拍照", "事故现场", "对方保险",
    ),
    "add_driver": (
        "add driver", "add a driver", "加个司机", "加司机", "加人开车", "加个人",
        "我儿子刚拿驾照", "我老婆开", "老公开", "孩子开", "teen driver", "add teen",
    ),
    "bundling": (
        "bundling", "bundle", "一起买", "一起买能打折", "home insurance", "房屋保险",
        "能打折", "discount",
    ),
}


def _get_markers(name: str) -> tuple[str, ...]:
    """Get marker set from config or fallback. Used for intent detection."""
    global _MARKERS_CACHE
    if _MARKERS_CACHE is None:
        loaded = get_insurance_markers()
        _MARKERS_CACHE = loaded if loaded else _FALLBACK_MARKERS
    return _MARKERS_CACHE.get(name, _FALLBACK_MARKERS.get(name, ()))


def _get_handoff_phrases(client_id: str | None = None) -> dict[str, dict[str, str]]:
    """Get handoff phrases from config or empty dict (caller uses hardcoded fallback)."""
    cid = (client_id or "").strip() or get_active_client_id()
    if cid not in _HANDOFF_CACHE:
        _HANDOFF_CACHE[cid] = get_handoff_phrases(cid)
    return _HANDOFF_CACHE.get(cid, {})


def _get_reply_templates() -> dict[str, Any]:
    """Get reply templates from config or empty dict (caller uses hardcoded fallback)."""
    global _REPLY_TEMPLATES_CACHE
    if _REPLY_TEMPLATES_CACHE is None:
        _REPLY_TEMPLATES_CACHE = get_reply_templates()
    return _REPLY_TEMPLATES_CACHE


def _get_category_templates_config() -> dict[str, dict[str, str]]:
    """Get category templates (broker_next_step, client_prep) from config or empty dict."""
    global _CATEGORY_TEMPLATES_CACHE
    if _CATEGORY_TEMPLATES_CACHE is None:
        _CATEGORY_TEMPLATES_CACHE = get_category_templates()
    return _CATEGORY_TEMPLATES_CACHE


def _get_workflow_fallbacks() -> dict[str, str]:
    """Get common workflow fallbacks from config or empty dict."""
    global _WORKFLOW_FALLBACKS_CACHE
    if _WORKFLOW_FALLBACKS_CACHE is None:
        _WORKFLOW_FALLBACKS_CACHE = get_workflow_fallbacks()
    return _WORKFLOW_FALLBACKS_CACHE

UNSENDABLE_DRAFT_MARKERS = (
    "[client's name]",
    "[your name]",
    "[broker's name]",
    "[contact information]",
    "best regards",
)

ROBOTIC_DRAFT_MARKERS = (
    "i understand your concern",
    "feel free to ask",
    "get back to you shortly",
    "we are reviewing your message",
    "we are reviewing this",
    "we'll notify you",
)

def _get_document_item_markers() -> tuple[tuple[tuple[str, ...], str, str], ...]:
    """Get document item markers from config or fallback."""
    global _DOCUMENT_ITEMS_CACHE
    if _DOCUMENT_ITEMS_CACHE is None:
        loaded = get_document_item_markers()
        if loaded:
            _DOCUMENT_ITEMS_CACHE = loaded
        else:
            _DOCUMENT_ITEMS_CACHE = (
                (("driver's license", "driver license", "驾照"), "driver's license copy", "驾照正反面"),
                (("declaration page", "dec page", "decl page"), "declaration page", "declaration page（保单首页）"),
                (("garaging proof", "proof of garaging"), "garaging proof", "garaging proof（车辆停放地址证明）"),
                (("questionnaire",), "questionnaire", "问卷"),
                (("sr-22 filing proof", "sr22 filing proof"), "SR-22 filing proof", "SR-22 filing proof（SR-22备案证明）"),
            )
    return _DOCUMENT_ITEMS_CACHE


def _is_llm_enabled() -> bool:
    """Check if LLM is available for triage."""
    value = os.getenv("LLM_GENERATION_ENABLED", "false").lower()
    if value not in ("1", "true", "yes", "on"):
        return False
    api_key = (os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") or "").strip()
    return bool(api_key)


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in (text or "") for marker in markers)


def _get_customer_content_for_language(text: str) -> str:
    """Extract customer message content for language detection, excluding [客户]/[系统] labels."""
    raw = text or ""
    if "[客户]" not in raw:
        return raw
    parts = re.findall(r"\[客户\]\s*([^[]+)", raw)
    return " ".join(parts).strip() if parts else raw


def _detect_client_language(text: str) -> str:
    raw = text or ""
    # When using merged conversation text, labels like [客户] contain Chinese; use only customer content
    content_for_lang = _get_customer_content_for_language(raw) if "[客户]" in raw else raw
    if not _contains_chinese(content_for_lang):
        return "en"

    zh_count = len(re.findall(r"[\u4e00-\u9fff]", content_for_lang))
    english_word_count = len(re.findall(r"[A-Za-z]+", content_for_lang))
    zh_context_markers = (
        "什么意思",
        "怎么办",
        "怎么弄",
        "看不懂",
        "帮我",
        "请问",
        "这个",
        "保单",
        "付款",
        "今天",
        "发我",
        "上周发过了",
    )
    if any(marker in content_for_lang for marker in zh_context_markers):
        return "zh"
    if zh_count >= 6 or zh_count * 2 >= max(english_word_count, 1):
        return "zh"
    return "en"


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _join_readable(items: list[str], language: str) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if language == "zh":
        return "、".join(items[:-1]) + f" 和 {items[-1]}"
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def _extract_requested_items(text: str, language: str) -> list[str]:
    lowered = (text or "").lower()
    items: list[str] = []
    for markers, english_label, chinese_label in _get_document_item_markers():
        if any(marker in lowered for marker in markers):
            items.append(chinese_label if language == "zh" else english_label)
    return _dedupe_preserve_order(items)


def _build_missing_document_client_prep(text: str) -> str:
    items = _extract_requested_items(text, "en")
    if items:
        if len(items) == 1 and items[0].endswith("copy"):
            return f"A clear {items[0]}."
        if len(items) == 1:
            return f"A clear copy of the {items[0]}."
        return f"Clear copies of {_join_readable(items, 'en')}."
    return "A clear copy of the requested item, such as a driver's license, declaration page, garaging proof, or questionnaire."


def _is_low_risk_dmv_status_question(text: str) -> bool:
    return (
        _contains_any(text, _get_markers("dmv_help"))
        and _contains_any(text, _get_markers("dmv_status"))
        and not _contains_any(text, ("sr-22", "sr22", "suspension", "clearance", "bring?", "带什么"))
    )


def _is_sr22_help_request(text: str) -> bool:
    return _contains_any(text, _get_markers("dmv_help")) and _contains_any(text, ("sr-22", "sr22", "suspension", "clearance"))


def _is_english_notice_confusion(text: str) -> bool:
    """Client confused by an English notice; wants explanation."""
    lowered = (text or "").lower()
    has_english_ref = any(x in lowered for x in ("英文", "english", "英 ")) or "notice" in lowered
    has_confusion = any(x in lowered for x in ("看不懂", "什么意思", "怎么办", "what does", "what do i"))
    return bool(has_english_ref and has_confusion)


def _is_document_confusion_request(text: str) -> bool:
    """Client asking what a document means (declaration page, garaging proof, etc.)."""
    lowered = (text or "").lower()
    has_doc_term = any(
        x in lowered
        for x in (
            "declaration page",
            "dec page",
            "decl page",
            "garaging proof",
            "proof of garaging",
            "保单首页",
            "车辆停放",
            "停放地址",
        )
    )
    has_question = any(
        x in lowered
        for x in (
            "什么",
            "是什么意思",
            "what is",
            "what does",
            "why",
            "为什么",
            "怎么",
            "什么意思",
        )
    )
    return bool(has_doc_term and has_question)


def _is_billing_clarification_request(text: str) -> bool:
    """Customer asking what a bill/notice means — clarification, NOT payment failure.
    TOP_SCENARIOS_HARDENING_PHASE2: 账单什么意思, bill 看不懂, what does this bill mean."""
    lowered = (text or "").lower()
    has_bill = any(x in lowered for x in ("账单", "bill", "billing", "invoice", "发票"))
    has_question = any(
        x in lowered
        for x in ("什么意思", "看不懂", "what does", "what is", "mean", "什么意思", "怎么理解")
    )
    # Exclude: payment failure / urgency markers
    has_payment_failure = any(
        x in lowered
        for x in (
            "payment failed",
            "autopay failed",
            "declined",
            "overdue",
            "past due",
            "停保",
            "保单要停",
            "cancelled",
            "cancellation",
        )
    )
    return bool(has_bill and has_question and not has_payment_failure)


def _is_premium_review_request(text: str) -> bool:
    return _contains_any(text, _get_markers("premium_review"))


def _is_add_vehicle_request(text: str) -> bool:
    """Add-car/quote: requires add_vehicle markers AND (vehicle_context OR quote/报价 OR delivery/pickup)."""
    lowered = (text or "").lower()
    if not _contains_any(lowered, _get_markers("add_vehicle")):
        return False
    if _contains_any(lowered, _get_markers("vehicle_context")) or "quote" in lowered or "报价" in lowered:
        return True
    delivery_pickup = ("下周", "提车", "拿车", "picking up", "pick up", "tomorrow", "明天", "delivery", "deliver")
    if _contains_any(lowered, delivery_pickup):
        return True
    return False


def _is_remove_vehicle_request(text: str) -> bool:
    return _contains_any(text, _get_markers("remove_vehicle")) and _contains_any(text, _get_markers("vehicle_context"))


def _is_claim_intake_request(text: str) -> bool:
    """Customer asking about accident / claim / what to collect after accident.
    Exclude underwriting 'prior claims' context."""
    lowered = (text or "").lower()
    if any(x in lowered for x in ("prior claims", "underwriting needs", "clarification on")):
        return False
    return _contains_any(text, _get_markers("claim_intake"))


def _is_add_driver_request(text: str) -> bool:
    """Customer asking to add driver to policy (teen, spouse, etc.)."""
    return _contains_any(text, _get_markers("add_driver"))


def _is_bundling_request(text: str) -> bool:
    """Customer asking about bundling (home+auto) or discount."""
    lowered = (text or "").lower()
    # Require bundling context: "一起买" or "bundling" or "home insurance" + discount
    has_bundle = any(
        m in lowered
        for m in ["bundling", "bundle", "一起买", "home insurance", "房屋保险", "房屋"]
    )
    has_discount = any(m in lowered for m in ["打折", "能打折", "discount", "便宜"])
    return has_bundle or (has_discount and ("一起" in lowered or "home" in lowered or "房屋" in lowered))


def _build_customer_question_broker_next_step(text: str) -> str:
    lowered = (text or "").lower()
    items = _extract_requested_items(text, "en")
    item_text = _join_readable(items, "en")
    if _is_low_risk_dmv_status_question(lowered):
        return "Check whether the proof of insurance already reached DMV, then send the client a short confirmation instead of a long explanation."
    if _is_sr22_help_request(lowered):
        return "Confirm whether DMV wants SR-22 filing proof, check any deadline, and tell the client exactly what to bring or what still needs to be filed."
    if _is_claim_intake_request(lowered):
        return "Guide client to collect evidence and start claim reporting; confirm photos and other-driver info received."
    if _is_premium_review_request(lowered):
        return "Review renewal notice and current premium; confirm remove-vehicle or coverage-adjust intent, then send 1–2 realistic options."
    if _is_add_vehicle_request(lowered):
        return "Confirm any missing driver, ZIP, or VIN if needed; then quote or add same day."
    if _is_remove_vehicle_request(lowered):
        return "Confirm the sold vehicle details and sale date, then remove it cleanly without leaving the client unclear on what stays covered."
    if _is_add_driver_request(lowered):
        return "Confirm which vehicle, driver details and license; then add driver to policy."
    if _is_bundling_request(lowered):
        return "Review current auto and home policies; confirm bundling discount options."
    if _is_billing_clarification_request(lowered):
        return "Read the bill or notice in plain language; confirm whether there is any deadline or action needed, and tell the client the next step clearly."
    if items:
        return f"Confirm why the {item_text} was requested, check whether it was already received, and explain to the client exactly what still needs to be sent."
    return "Read the notice in plain language, confirm whether there is any deadline or payment risk, and tell the client the next step clearly."


def _build_customer_question_client_prep(text: str) -> str:
    lowered = (text or "").lower()
    items = _extract_requested_items(text, "en")
    item_text = _join_readable(items, "en")
    if _is_low_risk_dmv_status_question(lowered):
        return "Policy number or the latest DMV notice if they have one."
    if _is_sr22_help_request(lowered):
        return "DMV notice, any suspension letter, and any SR-22 filing proof already received."
    if _is_claim_intake_request(lowered):
        return "Accident details, photos, other driver's license and insurance info, and policy number."
    if _is_premium_review_request(lowered):
        return "Current declaration page, latest bill, and any recent vehicle, driver, address, or coverage changes."
    if _is_add_vehicle_request(lowered):
        return "Year, make/model, VIN if available, delivery date, zip or address, lienholder if any, and primary driver details."
    if _is_remove_vehicle_request(lowered):
        return "Vehicle details, sale date, replacement-vehicle timing if any, and whether title or registration already transferred."
    if _is_add_driver_request(lowered):
        return "Which vehicle, driver name and license info."
    if _is_bundling_request(lowered):
        return "Current auto policy, home policy if any, and what they want to bundle."
    if _is_billing_clarification_request(lowered):
        return "The full bill or notice, or a clear photo of it."
    if items:
        return f"The full notice plus a clear copy of the {item_text} if they have it."
    return "The full text or a clear photo of the notice, plus any deadline shown on it."


def _build_client_reply_draft(text: str, category: str) -> str:
    language = _detect_client_language(text)
    items = _extract_requested_items(text, language)
    item_text = _join_readable(items, language)
    lowered = (text or "").lower()
    templates = _get_reply_templates()

    if language == "zh":
        if category == "cancellation_warning":
            t = templates.get("cancellation_warning", {})
            return t.get("zh") or "这个通知说明保单有取消风险。请把通知和付款记录发我，我先帮你确认；如果还没付，今天尽快处理。"
        if category == "payment_lapse_expiration":
            t = templates.get("payment_lapse_expiration", {})
            base = t.get("zh") or "这看起来是付款出了问题。请把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。"
            # Mixed-intent: payment + document already sent
            if any(x in lowered for x in _get_markers("missing_document_object")) and any(
                m in lowered for m in ["发过", "发过了", "又发", "sent"]
            ):
                base = base.rstrip("。") + "；如果材料说发过了，我这边也帮你核对。"
            return base
        if category == "missing_document":
            t = templates.get("missing_document", {})
            # Reassure-first: when customer says 发过了 first, lead with acknowledgment
            already_sent_lead = any(
                m in lowered for m in ["发过", "发过了", "发了", "又发", "sent", "already sent", "上周发", "上周寄"]
            )
            if already_sent_lead:
                if item_text:
                    base = (t.get("zh_already_sent_with_item") or "您说发过了，我这边帮你核对。把完整通知和 {item_text} 发我，核对好后就能往下推。").replace("{item_text}", item_text)
                else:
                    base = t.get("zh_already_sent_without_item") or "您说发过了，我这边帮你核对。把完整通知和您发过的材料发我，核对好后就能往下推。"
                return base
            if item_text:
                base = (t.get("zh_with_item") or "现在文件里还缺 {item_text}。请再发我一次；如果你之前已经发过，也跟我说一声，我这边帮你核对，核对好后就能往下推。").replace("{item_text}", item_text)
                if len(items) > 1:
                    base = base.replace("请再发我一次；", "请再发我一次（先发其中一个也行）；")
                if _is_document_confusion_request(lowered):
                    snippet = retrieve_document_explanation(text)
                    if snippet:
                        augment = format_retrieval_augment(snippet, "zh")
                        if augment:
                            return augment + base
                return base
            return t.get("zh_without_item") or "现在文件里还缺资料。请把资料再发我一次；如果你之前已经发过，也跟我说一声，我这边帮你核对。"
        if category == "missing_signature":
            return "看起来还有签名没完成。把要签名的那一页发我，我先帮你确认是哪一栏。"
        if category == "underwriting_followup":
            return "保险公司这边还要补一些资料。把通知里要的内容发我，我整理后尽快帮你回复。"
        if category == "renewal_reminder":
            return "这是续保提醒，目前先不用处理。到需要确认方案时我再联系你。"
        if category == "customer_question":
            if _is_low_risk_dmv_status_question(lowered):
                return "我先帮你确认 DMV 那边有没有收到保险证明。有结果我再回你，这种一般不用你先额外处理。"
            if _is_sr22_help_request(lowered):
                return "把 DMV 信件发我，我先帮你确认是不是要 SR-22 filing proof（SR-22备案证明），再告诉你要带什么。"
            if _is_claim_intake_request(lowered):
                t = templates.get("claim_intake", {})
                # Hit-and-run: tailor to 对方跑了 — emphasize plate, photos, what happened
                if any(m in lowered for m in ("对方跑了", "对方跑", "hit and run", "hit-and-run", "跑了")):
                    hit_t = templates.get("claim_intake_hit_and_run", {})
                    return hit_t.get("zh") or "刚出事故一定很着急，先别慌。对方跑了的话，最关键的是车牌号、现场照片和事故经过。先把这些发我，我帮你确认下一步怎么报案和报保险。"
                return t.get("zh") or "事故刚发生的话，先确保人没事，再拍现场照片、记下对方车牌和保险信息。把事故经过、对方信息和照片发我，我帮你确认下一步怎么报案。"
            if _is_premium_review_request(lowered):
                t = templates.get("premium_review", {})
                # "有办法吗" / "有办法" — add reassurance that options exist
                if any(m in lowered for m in ("有办法", "有办法吗")):
                    reas_t = templates.get("premium_review_reassurance", {})
                    base = reas_t.get("zh") or "一般有办法的。我先帮你看这次保费为什么变高，再看看有没有能调整的地方。把现在保单和最新账单发我（先发其中一个也行），我先帮你核对。"
                else:
                    base = t.get("zh") or "我先帮你看这次保费为什么变高，再看看有没有能调整的地方。把现在保单和最新账单发我（先发其中一个也行），我先帮你核对。"
                # Mixed-intent: premium + document already sent
                if any(x in lowered for x in _get_markers("missing_document_object")) and any(
                    m in lowered for m in ["发过", "发过了", "又发", "sent"]
                ):
                    base = base.rstrip("。") + "；如果材料说发过了，我这边也帮你核对。"
                return base
            if _is_add_vehicle_request(lowered):
                t = templates.get("add_car", {})
                # Progressive ask: acknowledge what customer said, ask 1–2 next things (not 6)
                single_ctx = f"[客户] {text}"
                fields = _extract_add_car_fields(single_ctx)
                vehicle_ok = (fields.get("year") and fields.get("model")) or fields.get("vin")
                if vehicle_ok and not fields.get("zip"):
                    base = "先把地址邮编发我，我就能帮你算报价。"
                elif vehicle_ok and fields.get("zip") and not fields.get("delivery") and not fields.get("driver"):
                    base = "提车日期和主要驾驶人发我一下，我好安排报价。"
                elif fields.get("model") and not vehicle_ok:
                    base = "先把年份和地址邮编发我，我就能帮你算报价。"
                elif fields.get("year") and not fields.get("model"):
                    base = "先把车型和地址邮编发我，我就能帮你算报价。"
                elif not vehicle_ok:
                    base = "可以先帮你看这台车的报价。先把年份和车型发我，我就能帮你算。"
                else:
                    base = t.get("zh") or "可以先帮你看这台车的报价。把车子的年份、车型、VIN（有的话）、提车日期、地址邮编和主要驾驶人发我，我先帮你算。"
                # Add acknowledgement when we have partial vehicle info (office-natural flow)
                ack = ""
                if fields.get("model") or fields.get("year"):
                    year_m = re.search(r"(20[12][0-9])", text)
                    model_m = re.search(
                        r"(宝马\s*[xX]?[0-9]{1,2}|特斯拉\s*[Mm]odel\s*[Yy3]|[Hh]onda\s+[Cc]r-[Vv]|[Tt]oyota\s+[Cc]amry|[Tt]oyota\s+[Cc]orolla|丰田\s*花冠|[Bb]mw\s+[xX][0-9])",
                        text,
                    )
                    if model_m:
                        ack = f"好的，{model_m.group(1).strip()}。"
                    elif year_m:
                        ack = f"好的，{year_m.group(1)}年的。"
                if ack:
                    base = ack + base
                # Mixed-intent: add-car + garaging proof confusion — add brief explanation
                if _is_document_confusion_request(lowered) and ("garaging" in lowered or "停放" in lowered):
                    snippet = retrieve_document_explanation(text)
                    if snippet:
                        augment = format_retrieval_augment(snippet, "zh")
                        if augment:
                            return augment + base
                    return "garaging proof（车辆停放地址证明）是证明车平时停哪里的材料。\n\n" + base
                return base
            if _is_remove_vehicle_request(lowered):
                t = templates.get("remove_vehicle", {})
                return t.get("zh") or "好的，可以处理。把卖车日期、车辆信息和是否已经过户发我，我先帮你确认。"
            if _is_add_driver_request(lowered):
                return "好的，可以加司机。把要加的是哪辆车、驾驶人信息和驾照发我，我先帮你确认下一步。"
            if _is_bundling_request(lowered):
                return "房屋险和车险一起买一般有折扣。把您现在的车险和房屋险（如果有）情况发我，我先帮你看有没有合适的方案。"
            if item_text:
                base = f"这个意思多半是还在要 {item_text}。把完整通知发我，我先帮你确认缺哪一份、要补给谁。"
                if _is_document_confusion_request(lowered):
                    snippet = retrieve_document_explanation(text)
                    if snippet:
                        augment = format_retrieval_augment(snippet, "zh")
                        if augment:
                            return augment + base
                    # When customer asks "what does garaging proof mean?", lead with definition
                    if "garaging" in lowered or "停放" in lowered:
                        return "garaging proof（车辆停放地址证明）是证明车平时停哪里的材料。把完整通知发我，我先帮你确认缺哪一份、要补给谁。"
                return base
            if _is_billing_clarification_request(lowered):
                return "把完整账单或通知发我，我先帮你看一下，再告诉你重点和下一步怎么处理。"
            if _is_english_notice_confusion(lowered):
                t = templates.get("english_notice_confusion", {})
                base = t.get("zh") or "英文通知有些术语看不懂很正常。把完整通知或更清楚的照片发我，我先帮你看一下，再告诉你重点和下一步怎么处理。"
                snippet = retrieve_notice_explanation(text)
                if snippet:
                    augment = format_retrieval_augment(snippet, "zh")
                    if augment:
                        return augment + base
                return base
            return "把完整通知或更清楚的照片发我。我先帮你看一下，再告诉你重点和下一步怎么处理。"
        if category == "unclear":
            # Minimal "发你了"/"发我" — acknowledge first, then ask (THREE_CRITICAL_ENTRY_SPRINT)
            if len((text or "").strip()) <= 20 and any(m in (text or "") for m in ["发你", "发我", "发您", "发了", "sent"]):
                return "您是说发过了吗？我这边帮你核对。把完整通知或相关材料也发我一下，我好确认。"
            return "这段内容还不够完整。把完整通知或前后内容再发我一下，我帮你确认下一步。"
        if category == "informational":
            return "这个目前看起来没问题，先不用额外处理。有新内容我再跟你说。"
        if category == "policy_delay_pending":
            return "这份保单还在处理中，先不用额外操作。有更新我会第一时间告诉你。"

    if category == "cancellation_warning":
        t = templates.get("cancellation_warning", {})
        return t.get("en") or "This notice means the policy could cancel. Send me the notice and any payment confirmation, and if it is still unpaid we will handle it today."
    if category == "payment_lapse_expiration":
        t = templates.get("payment_lapse_expiration", {})
        base = t.get("en") or "This looks like a payment issue. Send me the latest notice or any payment confirmation, and if it is still unpaid we will fix it today."
        # Mixed-intent: payment + document already sent
        if any(x in lowered for x in _get_markers("missing_document_object")) and any(
            m in lowered for m in ["sent", "already sent", "发过", "发过了"]
        ):
            base = base.rstrip(".") + "; if you already sent documents, I will check on my side."
        return base
    if category == "missing_document":
        t = templates.get("missing_document", {})
        # Reassure-first: when customer says already sent first, lead with acknowledgment
        already_sent_lead = any(
            m in lowered for m in ["sent", "already sent", "发过", "发过了", "发了", "又发", "last week"]
        )
        if already_sent_lead:
            if item_text:
                base = (t.get("en_already_sent_with_item") or "You said you already sent it—I will check on my side. Send me the full notice and the {item_text} so we can verify and move forward.").replace("{item_text}", item_text)
            else:
                base = t.get("en_already_sent_without_item") or "You said you already sent it—I will check on my side. Send me the full notice and what you sent so we can verify and move forward."
            return base
        if item_text:
            pronoun = "them" if len(items) > 1 else "it"
            base = (t.get("en_with_item") or "They still need the {item_text}. Please send {pronoun} again when you can, and if you already sent {pronoun}, tell me so I can check on my side.").replace("{item_text}", item_text).replace("{pronoun}", pronoun)
            if len(items) > 1:
                base = base.replace("when you can, and", "when you can (either one first is fine), and")
            if _is_document_confusion_request(lowered):
                snippet = retrieve_document_explanation(text)
                if snippet:
                    augment = format_retrieval_augment(snippet, "en")
                    if augment:
                        return augment + base
            return base
        return t.get("en_without_item") or "They still need one document on this file. Please send it again when you can, and if you already sent it, tell me so I can check on my side."
    if category == "missing_signature":
        return "It looks like one signature is still missing. Send me the page they flagged and I will help confirm what still needs to be signed."
    if category == "underwriting_followup":
        return "Underwriting still needs more information. Send me the requested details and I will help get this back to them before the deadline."
    if category == "renewal_reminder":
        return "This is just a renewal reminder, so nothing needs to be handled right now. I will reach out when it is time to review options."
    if category == "customer_question":
        if _is_low_risk_dmv_status_question(lowered):
            return "I can check whether DMV already received the proof of insurance. Send me the latest notice or policy number and I will confirm back."
        if _is_sr22_help_request(lowered):
            return "Send me the DMV notice and I will confirm whether they need SR-22 filing proof and what to bring."
        if _is_claim_intake_request(lowered):
            t = templates.get("claim_intake", {})
            if any(m in lowered for m in ("对方跑了", "对方跑", "hit and run", "hit-and-run", "跑了", "other driver left")):
                hit_t = templates.get("claim_intake_hit_and_run", {})
                return hit_t.get("en") or "Accidents can be stressful—first make sure everyone is okay. If the other driver left, the most important things are the license plate, photos, and what happened. Send me those and I will help you with the next steps to report the claim."
            return t.get("en") or "If the accident just happened, first make sure everyone is okay, then take photos and get the other driver's license and insurance info. Send me what happened, the other driver's info and photos, and I will help you with the next steps to report the claim."
        if _is_premium_review_request(lowered):
            t = templates.get("premium_review", {})
            if any(m in lowered for m in ("有办法", "有办法吗", "options", "any way", "anything we can")):
                reas_t = templates.get("premium_review_reassurance", {})
                base = reas_t.get("en") or "There are usually options. I can review why the premium went up and see what can realistically be adjusted. Send me the current policy page and latest bill and I will check."
            else:
                base = t.get("en") or "I can review why the premium went up and see what can realistically be adjusted. Send me the current policy page and latest bill and I will check."
            # Mixed-intent: premium + document already sent
            if any(x in lowered for x in _get_markers("missing_document_object")) and any(
                m in lowered for m in ["sent", "already sent", "发过", "发过了"]
            ):
                base = base.rstrip(".") + "; if you already sent documents, I will check on my side."
            return base
        if _is_add_vehicle_request(lowered):
            t = templates.get("add_car", {})
            # Progressive ask: acknowledge what customer said, ask 1–2 next things (not 6)
            single_ctx = f"[客户] {text}"
            fields = _extract_add_car_fields(single_ctx)
            vehicle_ok = (fields.get("year") and fields.get("model")) or fields.get("vin")
            if vehicle_ok and not fields.get("zip"):
                base = "Send me the zip or address and I will run the quote."
            elif vehicle_ok and fields.get("zip") and not fields.get("delivery") and not fields.get("driver"):
                base = "Send me the delivery date and main driver so I can prepare the quote."
            elif fields.get("model") and not vehicle_ok:
                base = "Send me the year and zip or address so I can run the quote."
            elif fields.get("year") and not fields.get("model"):
                base = "Send me the make/model and zip or address so I can run the quote."
            elif not vehicle_ok:
                base = "I can start a quote for the new car. Send me the year and make/model so I can run it."
            else:
                base = t.get("en") or "I can start a quote for the new car. Send me the year, make/model, VIN if you have it, delivery date, zip or address, and main driver and I will check it."
            # Add acknowledgement when we have partial vehicle info
            ack = ""
            if fields.get("model") or fields.get("year"):
                year_m = re.search(r"(20[12][0-9])", text)
                model_m = re.search(
                    r"([Bb][Mm][Ww]\s+[Xx][0-9]|[Tt]esla\s+[Mm]odel\s+[Yy3]|[Hh]onda\s+[Cc]r-[Vv]|[Tt]oyota\s+[Cc]amry)",
                    text,
                )
                if model_m:
                    ack = f"Got it, {model_m.group(1).strip()}. "
                elif year_m:
                    ack = f"Got it, {year_m.group(1)}. "
                elif fields.get("model"):
                    ack = "I can help with that. "
            if ack:
                base = ack + base
            # Mixed-intent: add-car + garaging proof confusion — add brief explanation
            if _is_document_confusion_request(lowered) and "garaging" in lowered:
                snippet = retrieve_document_explanation(text)
                if snippet:
                    augment = format_retrieval_augment(snippet, "en")
                    if augment:
                        return augment + base
                return "Garaging proof shows where the car is usually parked.\n\n" + base
            return base
        if _is_remove_vehicle_request(lowered):
            t = templates.get("remove_vehicle", {})
            return t.get("en") or "Got it, I can help with that. Send me the vehicle details, sale date, and whether title already transferred and I will confirm the next step."
        if _is_add_driver_request(lowered):
            return "Got it, I can help add a driver. Send me which vehicle, the driver's info and license, and I will confirm the next step."
        if _is_bundling_request(lowered):
            return "Bundling home and auto usually gets a discount. Send me your current auto and home (if any) policy info and I will check what options we have."
        if item_text:
            base = f"This usually means they still need the {item_text}. Send me the full notice and I will confirm exactly what is missing."
            if _is_document_confusion_request(lowered):
                snippet = retrieve_document_explanation(text)
                if snippet:
                    augment = format_retrieval_augment(snippet, "en")
                    if augment:
                        return augment + base
            return base
        if _is_billing_clarification_request(lowered):
            return "Send me the full bill or notice and I will tell you what it means and what to do next."
        if _is_english_notice_confusion(lowered):
            t = templates.get("english_notice_confusion", {})
            base = t.get("en") or "English notices can be confusing. Send me the full notice or a clearer photo and I will tell you what it means and what to do next."
            snippet = retrieve_notice_explanation(text)
            if snippet:
                augment = format_retrieval_augment(snippet, "en")
                if augment:
                    return augment + base
            return base
        return "Send me the full notice or a clearer photo and I will tell you what it means and what needs to be handled next."
    if category == "unclear":
        # Minimal "sent"/"I sent it" — acknowledge first (THREE_CRITICAL_ENTRY_SPRINT)
        if len((text or "").strip()) <= 20 and any(m in (text or "").lower() for m in ["sent", "already sent", "i sent"]):
            return "You said you sent it—I will check on my side. Send me the full notice or the document so I can verify."
        return "This part is still unclear. Send me the full notice or a little more context and I will confirm the next step."
    if category == "informational":
        return "This looks fine for now. No extra action is needed at the moment."
    if category == "policy_delay_pending":
        return "Your policy is still being processed, so no extra action is needed right now. I will update you as soon as there is movement."
    return "Send me the full notice or message and I will confirm the next step."


def _get_category_templates(
    category: str, text: str, client_id: str | None = None
) -> tuple[str | None, str | None, str | None]:
    """
    Return (broker_next_step, client_prep, client_reply_draft) for rule-based triage.
    Loads from configs/industries/insurance/category_templates.json when present;
    falls back to hardcoded for customer_question (dynamic) and missing config.
    """
    cfg = _get_category_templates_config()

    def _bns(cat: str) -> str | None:
        entry = cfg.get(cat, {})
        val = entry.get("broker_next_step", "").strip()
        return val if val else None

    def _cp(cat: str, dynamic_fn=None) -> str | None:
        entry = cfg.get(cat, {})
        val = entry.get("client_prep", "").strip()
        if val and val.lower() == "dynamic" and dynamic_fn:
            return dynamic_fn(text)
        return val if val else None

    # customer_question: always dynamic (broker_next_step, client_prep, draft)
    if category == "customer_question":
        return (
            _build_customer_question_broker_next_step(text),
            _build_customer_question_client_prep(text),
            _build_client_reply_draft(text, "customer_question"),
        )

    # missing_document: broker_next_step from config; client_prep dynamic
    if category == "missing_document":
        bns = _bns("missing_document") or "Verify whether customer-resubmitted items were received; request any still-missing items."
        return (
            bns,
            _build_missing_document_client_prep(text),
            _build_client_reply_draft(text, "missing_document"),
        )

    # customer_requested_human: broker_next_step, client_prep from config; draft from handoff_phrases
    if category == "customer_requested_human":
        bns = _bns("customer_requested_human") or "Customer requested human contact. Call or message back promptly."
        cp = _cp("customer_requested_human") or "Customer wants to speak with office."
        phrases = _get_handoff_phrases(client_id)
        draft = phrases.get("customer_requested_human", {}).get("zh") or "好的，已帮您转给办公室，他们会尽快联系您。"
        return (bns, cp, draft)

    # Static categories: use config when present, else hardcoded fallback
    _HARDCODED: dict[str, tuple[str, str]] = {
        "cancellation_warning": (
            "Confirm whether the cancellation is still active, verify any payment already made, and call or text the client today with the exact deadline.",
            "The cancellation notice, any payment confirmation, and the best callback number if they already paid.",
        ),
        "payment_lapse_expiration": (
            "Confirm whether the payment actually failed, check whether the carrier still shows the balance due, and help the client fix it today.",
            "Updated payment method details, payment confirmation, or the best number to reach them today.",
        ),
        "missing_signature": (
            "Verify which document and which field still need a signature, then point the client to the exact page to sign.",
            "Confirmation of which document they signed and where.",
        ),
        "underwriting_followup": (
            "Confirm exactly what underwriting still needs, send the client a short checklist, and respond before the stated deadline.",
            "The missing underwriting details, questionnaire answers, or supporting documents requested before the deadline.",
        ),
        "renewal_reminder": (
            "Optional outreach for retention. No immediate action required.",
            "None at this time.",
        ),
        "unclear": (
            "Ask for the missing part of the message so you can confirm whether this is routine, underwriting, or payment-related.",
            "Any additional context or the full original message if it was forwarded.",
        ),
        "informational": (
            "No action required. Optional brief confirmation to client.",
            "None.",
        ),
        "policy_delay_pending": (
            "No action needed right now. Keep the file parked and update the client if the carrier misses the stated timeline.",
            "None.",
        ),
    }
    bns = _bns(category) or (_HARDCODED.get(category, (None, None))[0] if category in _HARDCODED else None)
    cp = _cp(category) or (_HARDCODED.get(category, (None, None))[1] if category in _HARDCODED else None)
    draft = _build_client_reply_draft(text, category)
    return (bns, cp, draft)


def _is_talk_to_agent_request(text: str) -> bool:
    """
    Detect customer request for human contact (Talk to Agent).
    SALES_READINESS_HARDENING: free-text detection so "联系人工" works when typed, not only via button.
    """
    if not text or not isinstance(text, str):
        return False
    lowered = text.strip().lower()
    markers = _get_markers("talk_to_agent")
    if markers:
        return any(m in lowered for m in markers)
    # Fallback when config missing (REALISTIC_SIMULATION_SPRINT: add 找陈奎)
    fallback = (
        "联系人工", "联系陈奎", "找陈奎", "联系办公室", "我要找人工", "我想跟人说", "找经纪人", "找人工",
        "talk to agent", "want to speak to someone", "speak to a person",
    )
    return any(m in lowered for m in fallback)


def _classify_with_guardrails(text: str) -> tuple[str, str, bool]:
    """Deterministic category/urgency/manual follow-up for demo-safe validation."""
    t = (text or "").lower().strip()
    t = t.replace("autopay", "auto pay")
    t = t.replace("dec page", "declaration page")
    t = t.replace("decl page", "declaration page")

    if not t:
        return "unclear", "medium", True

    # SALES_READINESS_HARDENING: Talk to Agent free-text detection
    if _is_talk_to_agent_request(text):
        return "customer_requested_human", "medium", True

    if any(x in t for x in ["marketing footer", "generic footer"]):
        return "unclear", "medium", True

    has_question_marker = any(x in t for x in _get_markers("question_help"))
    has_strong_cancellation_marker = any(x in t for x in _get_markers("strong_cancellation")) or "7天后要cancel" in t
    has_weak_cancellation_marker = any(x in t for x in _get_markers("weak_cancellation"))
    has_payment_risk_marker = any(x in t for x in _get_markers("payment_risk"))
    has_policy_stop_marker = any(x in t for x in _get_markers("policy_stop"))

    if has_strong_cancellation_marker:
        return "cancellation_warning", "critical", True

    if has_weak_cancellation_marker and has_question_marker:
        return "customer_question", "medium", True

    # Mixed-intent: when claim + payment both present, prefer claim (accident first response)
    if _is_claim_intake_request(t) and any(x in t for x in _get_markers("payment")):
        return "customer_question", "medium", True

    # TOP_SCENARIOS_HARDENING: premium + "我发你账单了" = bill sent for review, NOT payment failure
    if _is_premium_review_request(t):
        return "customer_question", "medium", True

    if _is_billing_clarification_request(t):
        return "customer_question", "medium", True

    if any(x in t for x in _get_markers("payment")):
        return "payment_lapse_expiration", "high", True

    if has_payment_risk_marker and (has_policy_stop_marker or has_weak_cancellation_marker):
        return "payment_lapse_expiration", "high", True

    if has_policy_stop_marker and ("notice" in t or "通知" in t) and has_question_marker:
        return "payment_lapse_expiration", "high", True

    # REALISTIC_SIMULATION_SPRINT: policy_stop alone (e.g. "急死了 保单要停了") = cancellation risk, same-day
    if has_policy_stop_marker:
        return "cancellation_warning", "critical", True

    if "lienholder" in t and any(x in t for x in ["certificate of insurance", "coi"]):
        return "informational", "medium", False

    if _is_premium_review_request(t):
        return "customer_question", "medium", True

    if any(x in t for x in _get_markers("missing_document_object")) and any(x in t for x in _get_markers("missing_document_request")):
        return "missing_document", "medium", True

    if _is_claim_intake_request(t):
        return "customer_question", "medium", True

    if any(x in t for x in ["renewal", "renews in"]) and not _is_premium_review_request(t):
        return "renewal_reminder", "low", False

    if any(x in t for x in ["pending issuance", "5-7 business days"]):
        return "policy_delay_pending", "low", False

    if any(
        x in t
        for x in [
            "proof of insurance",
            "emailed to the dmv",
            "no further action",
            "no action needed",
        ]
    ):
        return "informational", "low", False

    if _is_low_risk_dmv_status_question(t):
        return "customer_question", "low", True

    if (
        _is_premium_review_request(t)
        or _is_add_vehicle_request(t)
        or _is_remove_vehicle_request(t)
        or _is_claim_intake_request(t)
        or _is_add_driver_request(t)
        or _is_bundling_request(t)
    ):
        return "customer_question", "medium", True

    if any(x in t for x in ["prior claims", "clarification", "respond within", "underwriting needs clarification"]):
        return "underwriting_followup", "high", True

    if any(x in t for x in _get_markers("dmv_help")) and (
        has_question_marker or "what should client bring" in t or "what should i bring" in t or "bring?" in t or "带什么" in t
    ):
        return "customer_question", "medium", True

    if has_question_marker:
        return "customer_question", "medium", True

    # Document confusion: asking what declaration page / garaging proof means
    if any(x in t for x in _get_markers("missing_document_object")) and any(
        x in t for x in ("什么", "是什么", "什么意思", "what is", "what does", "why", "为什么", "怎么")
    ):
        return "customer_question", "medium", True

    if any(x in t for x in ["签名", "签了", "signature", "signed"]):
        return "missing_signature", "medium", True

    if any(x in t for x in ["prior claims", "clarification", "respond within", "underwriting needs clarification"]):
        return "underwriting_followup", "high", True

    if any(x in t for x in ["important", "action required"]) and len(t) < 200:
        return "unclear", "medium", True

    return "unclear", "medium", True


def _rule_based_triage(text: str, client_id: str | None = None) -> dict[str, Any]:
    """
    Rule-based fallback when LLM is disabled.
    Uses keyword matching for category and urgency.
    """
    category, urgency, manual_followup = _classify_with_guardrails(text)

    # Category-specific broker guidance and client drafts (rule-based path)
    _broker_next_step, _client_prep, _client_reply_draft = _get_category_templates(category, text, client_id)
    fallbacks = _get_workflow_fallbacks()
    broker_next_step = _broker_next_step or fallbacks.get("broker_next_step", "Review and act on {category}.").replace("{category}", category.replace("_", " "))
    client_prep = _client_prep or fallbacks.get("client_prep", "Please have any relevant documents or information ready.")
    client_reply_draft = _client_reply_draft or fallbacks.get(
        "client_reply_draft",
        "Thank you for reaching out. We are reviewing your message and will follow up shortly. "
        "If you have any documents to share, please send them at your earliest convenience.",
    )

    return {
        "issue_category": category,
        "urgency": urgency,
        "broker_next_step": broker_next_step,
        "client_prep": client_prep,
        "client_reply_draft": client_reply_draft,
        "manual_followup_needed": manual_followup,
    }


def _has_tailored_draft(category: str, draft: str) -> bool:
    phrases = DRAFT_QUALITY_PHRASES.get(category)
    if not phrases:
        return True
    lowered = (draft or "").lower()
    return any(phrase in lowered for phrase in phrases)


def _is_sendable_client_draft(draft: str) -> bool:
    lowered = (draft or "").strip().lower()
    if not lowered:
        return False
    if lowered.startswith("dear "):
        return False
    if any(marker in lowered for marker in FORMAL_DRAFT_MARKERS):
        return False
    if "!" in lowered:
        return False
    return not any(marker in lowered for marker in UNSENDABLE_DRAFT_MARKERS)


def _merge_with_rule_guardrails(
    text: str, llm_result: dict[str, Any], client_id: str | None = None
) -> dict[str, Any]:
    """
    Keep demo-path classification deterministic while allowing richer LLM wording
    when it agrees with the guarded category.
    """
    rule_result = _rule_based_triage(text, client_id)
    merged = dict(llm_result)

    merged["issue_category"] = rule_result["issue_category"]
    merged["urgency"] = rule_result["urgency"]
    merged["manual_followup_needed"] = rule_result["manual_followup_needed"]
    guarded_category = rule_result["issue_category"]

    if guarded_category in RULE_GUIDANCE_CATEGORIES:
        merged["broker_next_step"] = rule_result["broker_next_step"]
        merged["client_prep"] = rule_result["client_prep"]

    merged["client_reply_draft"] = rule_result["client_reply_draft"]

    return merged


def _llm_triage(text: str, client_id: str | None = None) -> dict[str, Any]:
    """Call LLM for triage when enabled."""
    try:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        if not api_key:
            return _rule_based_triage(text, client_id)

        client = OpenAI(api_key=api_key)
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")

        system = """You are a triage assistant for a California auto insurance broker.
You receive inbound messages (screenshots, emails, notices, client questions) and produce structured triage output.

Output MUST be valid JSON with exactly these keys:
- issue_category: one of missing_signature, missing_document, cancellation_warning, policy_delay_pending, underwriting_followup, renewal_reminder, customer_question, payment_lapse_expiration, informational, unclear
- urgency: one of low, medium, high, critical
- broker_next_step: 1-2 sentences, actionable for the broker
- client_prep: what the client should prepare or have ready
- client_reply_draft: professional, courteous draft the broker can send to the client (editable)
- manual_followup_needed: true or false (true when unclear, high/critical urgency, or client explicitly asked for broker)

Rules:
- client_reply_draft: no legal/financial advice; no promises broker cannot keep
- broker_next_step: one operational sentence for the broker, not a generic summary
- client_reply_draft: keep it short and natural, max 2 short sentences, no salutations/sign-offs, no exclamation marks
- manual_followup_needed: true for cancellation_warning, payment_lapse_expiration, underwriting_followup, customer_question, unclear
- manual_followup_needed: false for informational, renewal_reminder, policy_delay_pending when message is clear
- If a message requests a driver's license, declaration page, or other missing file, prefer missing_document over underwriting_followup
- If a message only says "important" or "action required" but the body is unclear or generic, use unclear
- Lienholder / certificate of insurance requests are usually informational, not missing_document
- Cancellation / non-payment / cancel notices should be critical
- Overdue or late-payment wording plus concern that the policy may stop should be payment_lapse_expiration, high
- DMV / SR-22 / suspension help wording with a client question should usually be customer_question
- Pending issuance / 5-7 business days should be low urgency unless a deadline is explicit
- Respond ONLY with the JSON object, no other text."""

        user = f"""Triage this inbound message:

{text[:2000]}"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=512,
        )

        content = ""
        if response.choices:
            content = (response.choices[0].message.content or "").strip()

        # Parse JSON from response (handle markdown code blocks)
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            parsed = json.loads(json_match.group())
            result = _normalize_output(parsed)
            if result:
                return _merge_with_rule_guardrails(text, result, client_id)
    except Exception as e:
        logger.warning(f"LLM triage failed, falling back to rules: {e}")

    return _rule_based_triage(text, client_id)


def _normalize_output(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Ensure output has all required fields and valid values."""
    out = {}
    for k in REQUIRED_FIELDS:
        v = raw.get(k)
        if v is None:
            return None
        out[k] = v

    # Normalize types
    if isinstance(out.get("manual_followup_needed"), str):
        out["manual_followup_needed"] = out["manual_followup_needed"].lower() in (
            "true",
            "1",
            "yes",
        )
    out["manual_followup_needed"] = bool(out.get("manual_followup_needed", True))

    # Validate urgency
    u = str(out.get("urgency", "medium")).lower()
    out["urgency"] = u if u in VALID_URGENCIES else "medium"

    # Validate category
    c = str(out.get("issue_category", "unclear")).lower().replace(" ", "_")
    out["issue_category"] = c if c in VALID_CATEGORIES else "unclear"

    return out


def _build_conversation_summary(merged_text: str, base_result: dict[str, Any], customer_count: int) -> str:
    """Build a short broker-facing summary of the conversation."""
    category = base_result.get("issue_category", "unclear")
    lowered = (merged_text or "").lower()

    intent_hint = ""
    if _is_add_vehicle_request(lowered):
        # Distinguish new quote vs add-car when detectable
        if any(m in lowered for m in ("加车", "加一台", "加一辆", "add car", "add vehicle")):
            intent_hint = "Add car to existing policy. "
        else:
            intent_hint = "New quote / new vehicle. "
    elif _is_remove_vehicle_request(lowered):
        intent_hint = "Remove vehicle from policy. "
    elif _is_premium_review_request(lowered):
        intent_hint = "Premium review / too high. "
    elif category == "payment_lapse_expiration":
        intent_hint = "Payment failed / lapse risk. "
    elif category == "cancellation_warning":
        intent_hint = "Cancellation warning. "
    elif _is_english_notice_confusion(lowered):
        intent_hint = "English notice confusion. "
    elif category == "missing_document":
        intent_hint = "Missing document follow-up. "
    elif _is_sr22_help_request(lowered):
        intent_hint = "DMV / SR-22 help. "
    elif _is_claim_intake_request(lowered):
        intent_hint = "Claim intake / accident first response. "

    collected_hint = ""
    still_needed_hint = ""
    if _is_add_vehicle_request(lowered):
        fields = _extract_add_car_fields(merged_text)
        parts: list[str] = []
        if fields.get("year"):
            parts.append("year")
        if fields.get("model"):
            parts.append("model")
        if fields.get("vin"):
            parts.append("VIN")
        if fields.get("zip"):
            parts.append("zip")
        if fields.get("delivery"):
            parts.append("delivery")
        if fields.get("driver"):
            parts.append("driver")
        if parts:
            collected_hint = f" Collected: {', '.join(parts)}. "
        if _add_car_enough_for_handoff(fields):
            still_parts = []
            if not fields.get("delivery"):
                still_parts.append("delivery date")
            if not fields.get("driver"):
                still_parts.append("main driver")
            if still_parts:
                still_needed_hint = f" Still needed: {', '.join(still_parts)}. "
    elif _is_remove_vehicle_request(lowered):
        fields = _extract_remove_car_fields(merged_text)
        parts = []
        if fields.get("vehicle"):
            parts.append("vehicle")
        if fields.get("sale_date"):
            parts.append("sale date")
        if fields.get("transfer"):
            parts.append("transfer")
        if parts:
            collected_hint = f" Collected: {', '.join(parts)}. "
    elif _is_premium_review_request(lowered):
        if any(m in lowered for m in ["发你", "发我", "sent", "发过了", "already sent", "微信", "发你微信", "发我微信"]):
            collected_hint = " Collected: policy/bill sent. "
        elif any(m in lowered for m in ["发", "bill", "policy", "续保", "账单"]):
            collected_hint = " Collected: policy/bill mentioned. "
    elif category == "missing_document":
        items_mentioned, items_sent = _extract_missing_doc_status(merged_text)
        if items_mentioned:
            still = [i for i in items_mentioned if i not in items_sent]
            _h = lambda s: s.replace("_", " ")
            if items_sent:
                collected_hint = f" Collected: {', '.join(_h(i) for i in items_sent)} resent. "
            if still:
                collected_hint += f"Still needed: {', '.join(_h(i) for i in still)}. "
    elif category in ("payment_lapse_expiration", "cancellation_warning"):
        if any(m in lowered for m in ["付了", "paid", "已经付", "already paid", "换了新卡", "updated card"]):
            collected_hint = " Collected: client says already paid. "
        elif any(m in lowered for m in ["发", "sent", "截图", "screenshot", "发你", "发我"]):
            collected_hint = " Collected: client says sent notice/screenshot. "

    # Context hints: corrections, "already sent"
    context_hint = ""
    customer_only = " ".join(re.findall(r"\[客户\]\s*([^[]+)", merged_text or ""))
    if (
        re.search(r"不是[^，。]*[，,]?\s*是", customer_only)
        or "不是这个" in customer_only
        or "不是 payment" in customer_only
        or "不是续保" in customer_only
        or "说错了" in customer_only
        or "说错" in customer_only
    ):
        context_hint = " Customer corrected/clarified. "
    if any(m in customer_only for m in ["又发了", "又发了一次", "发你了", "发你", "我发你"]):
        context_hint += " Client says already sent. "

    msg_count = f"{customer_count} customer message(s)."
    latest_snip = (merged_text.split("[客户]")[-1].strip() if "[客户]" in merged_text else merged_text)[:80]
    if latest_snip:
        return f"{intent_hint}{collected_hint}{still_needed_hint}{context_hint}{msg_count} Latest: {latest_snip}..."
    return f"{intent_hint}{collected_hint}{still_needed_hint}{context_hint}{msg_count}"


def _build_conversation_text_for_triage(turns: list[dict[str, str]], latest_text: str) -> str:
    """Merge conversation turns + latest message for triage context."""
    parts: list[str] = []
    for t in turns:
        role = (t.get("role") or "").strip().lower()
        txt = (t.get("text") or "").strip()
        if not txt:
            continue
        label = "客户" if role == "customer" else "系统"
        parts.append(f"[{label}] {txt}")
    if latest_text.strip():
        parts.append(f"[客户] {latest_text.strip()}")
    return "\n\n".join(parts) if parts else latest_text.strip()


# Follow-up type constants (LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT)
FOLLOW_UP_TYPES = (
    "new_info",
    "correction",
    "already_sent",
    "clarification_question",
    "urgency_question",
    "next_step_question",
    "office_review_question",
    "unknown",
)


def _derive_follow_up_type(last_customer_msg: str) -> str:
    """
    Derive follow-up type from the last customer message.
    Used for reply strategy: clarification → answer first; already_sent → warmer handoff.
    """
    msg = (last_customer_msg or "").strip().lower()
    if not msg:
        return "unknown"

    # Correction: "不是", "不是这个", "说错了", "其实已经" (actually already paid/sent)
    correction_markers = ("不是", "不是这个", "不是 payment", "不是续保", "是另一辆", "说错了", "actually", "i meant", "其实已经")
    if any(m in msg for m in correction_markers):
        return "correction"

    # "Why still chasing" (发过了，怎么还在追) → already_sent for reassure-first handoff
    why_still_chasing = any(
        m in msg for m in ("怎么还在追", "为什么还在追", "为什么还追", "怎么还追", "why still", "why are they still")
    )
    if why_still_chasing:
        return "already_sent"

    # Clarification question: what does X mean (SIM2: "declaration page 发你了，garaging 是什么意思")
    # Check before already_sent so mixed "I sent X + what does Y mean?" gets answer-first reply.
    clarification_markers = (
        "什么意思", "要发什么", "发什么", "需要再发", "再发什么", "what does", "what is", "garaging 是什么意思", "garaging proof 是什么意思",
        "declaration page 是什么", "decl page 是什么", "为什么", "why", "怎么", "how",
        "够了吗", "够吗", "enough", "these enough", "is that enough",
    )
    if any(m in msg for m in clarification_markers):
        return "clarification_question"

    # Already sent: "发了", "发你", "sent" (after clarification so "发你了，garaging 是什么意思" → clarification)
    sent_markers = ("发了", "发你", "发我", "sent", "截图", "screenshot", "发你微信", "发我微信", "又发", "发过了")
    if any(m in msg for m in sent_markers):
        return "already_sent"

    # Urgency question: is this urgent, what matters most today
    urgency_markers = ("最要紧", "是不是今天", "一定要处理", "is this urgent", "urgent?", "due today")
    if any(m in msg for m in urgency_markers):
        return "urgency_question"

    # Next-step / office-review question
    next_step_markers = ("先看什么", "办公室先看什么", "what matters most", "what should i do", "先干嘛", "现在先干嘛")
    if any(m in msg for m in next_step_markers):
        return "next_step_question"

    return "new_info"


def _is_turn1_lightweight_candidate(merged_text: str) -> bool:
    """
    Turn 1 can use rule path when message is short and has high-confidence markers.
    Avoid mixed intent, adversarial, or ambiguous first messages.
    TURN1_LIGHTWEIGHT_COLDSTART_SPRINT: industrial best-practice for first impression.
    """
    if not merged_text or len(merged_text.strip()) > 200:
        return False
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    last = (matches[-1] or "").strip() if matches else merged_text.strip()
    if len(last) > 120:
        return False
    # Mixed intent: 2+ distinct flow markers → use LLM
    lowered = last.lower()
    flow_count = sum(
        [
            bool(_is_add_vehicle_request(last)),
            bool(_is_premium_review_request(last)),
            bool(_contains_any(lowered, _get_markers("payment")) or _contains_any(lowered, _get_markers("payment_risk"))),
            bool(
                _contains_any(lowered, _get_markers("missing_document_object"))
                and _contains_any(lowered, _get_markers("missing_document_request"))
            ),
            bool(_is_claim_intake_request(last)),
        ]
    )
    if flow_count >= 2:
        return False
    category, _, _ = _classify_with_guardrails(last)
    if category == "unclear":
        return False
    # High-confidence categories: rule handles these well for short Turn 1
    if category in (
        "cancellation_warning",
        "payment_lapse_expiration",
        "policy_delay_pending",
        "renewal_reminder",
        "informational",
        "missing_document",
        "missing_signature",
        "underwriting_followup",
    ):
        return True
    if category == "customer_question":
        # Sub-types with clear markers: add_vehicle, claim_intake, premium_review, add_driver, bundling
        if (
            _is_add_vehicle_request(last)
            or _is_claim_intake_request(last)
            or _is_premium_review_request(last)
            or _is_add_driver_request(last)
            or _is_bundling_request(last)
        ):
            return True
        if _is_document_confusion_request(last) or _is_english_notice_confusion(last):
            return True
        if _is_low_risk_dmv_status_question(last) or _is_sr22_help_request(last):
            return True
    return False


def _is_fast_path_candidate(merged_text: str, customer_count: int) -> bool:
    """
    Decide if this turn can use rule-based triage instead of LLM (SIMULATION_ASSISTANT_SPEED_LAYER_BLUEPRINT).
    Turn 1: use lightweight path when high-confidence (TURN1_LIGHTWEIGHT_COLDSTART_SPRINT).
    Turn 2+: simple turns (already_sent, clarification, add-car field) → fast.
    Complex turns: mixed intent, unclear → use LLM.
    """
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    last_customer = (matches[-1] or "").strip() if matches else ""
    last_lower = last_customer.lower()

    # Turn 1: lightweight path when high-confidence; else LLM
    if customer_count <= 1:
        return _is_turn1_lightweight_candidate(merged_text)

    follow_up = _derive_follow_up_type(last_customer)

    # Simple follow-up types: rules handle these well
    if follow_up in (
        "already_sent",
        "clarification_question",
        "urgency_question",
        "next_step_question",
        "office_review_question",
        "correction",
    ):
        return True

    # Simple add-car field: short message with year/zip/delivery/model/driver
    if follow_up == "new_info" and len(last_customer) <= 80:
        has_year = bool(re.search(r"20[12][0-9]", last_lower))
        has_zip = bool(re.search(r"\b9[0-9]{4}\b", last_lower))
        has_delivery = any(
            m in last_lower
            for m in ["下周", "提车", "拿车", "next week", "picking up", "pick up", "delivery", "明天"]
        )
        has_model = any(
            m in last_lower
            for m in [
                "bmw", "x5", "tesla", "honda", "toyota", "accord", "camry", "宝马", "本田", "丰田", "车型",
            ]
        )
        has_driver = any(m in last_lower for m in ["driver", "驾驶人", "谁开", "main driver", "primary driver", "我老公开", "我开"])
        if has_year or has_zip or has_delivery or has_model or has_driver:
            return True

    # Minimal "发你了" / "发您" style (short already-sent)
    if len(last_customer) <= 15 and any(m in last_lower for m in ("发你", "发我", "发您", "sent", "发了")):
        return True

    # Handoff confirmation: "可以了", "就这样", "好了", "ok" (short)
    if len(last_customer) <= 30 and any(
        m in last_lower for m in ("可以了", "就这样", "就这样吧", "好了", "ok", "okay", "够了")
    ):
        return True

    return False


def _derive_collection_stage(
    category: str,
    merged_text: str,
    customer_count: int,
    would_handoff: bool,
) -> str:
    """
    Derive collection_stage: collecting | enough_for_handoff.
    Lightweight signal for state visibility.
    """
    if would_handoff:
        return "enough_for_handoff"
    return "collecting"


def _parse_source_to_turns(source_text: str) -> list[dict[str, str]]:
    """Parse existing source_text into conversation turns for triage_conversation."""
    raw = (source_text or "").strip()
    if not raw:
        return []
    if "[客户]" not in raw and "[系统]" not in raw:
        return [{"role": "customer", "text": raw}]
    turns: list[dict[str, str]] = []
    pattern = re.compile(r"\[(客户|系统)\]\s*", re.IGNORECASE)
    parts = pattern.split(raw)
    if len(parts) < 2:
        return [{"role": "customer", "text": raw}]
    i = 1
    while i < len(parts) - 1:
        role_label = (parts[i] or "").strip()
        content = (parts[i + 1] or "").split("[")[0].strip() if i + 1 < len(parts) else ""
        role = "customer" if role_label == "客户" else "system"
        if content:
            turns.append({"role": role, "text": content})
        i += 2
    return turns if turns else [{"role": "customer", "text": raw}]


def triage_for_append(
    existing_source_text: str,
    new_message: str,
    client_id: str | None = None,
) -> dict[str, Any]:
    """
    Triage a new customer follow-up in the context of an existing case.
    Returns full triage result suitable for append_follow_up_message.
    For append flow we always treat as handoff-ready (broker receives updated case).
    client_id: when provided (e.g. from case.client_id), uses client-aware handoff phrases.
    """
    turns = _parse_source_to_turns(existing_source_text)
    result = triage_conversation(new_message.strip(), turns, client_id=client_id)
    result["handoff_ready"] = True
    result["lifecycle_status"] = "handoff_pending"
    result["next_best_question"] = ""
    return result


def _extract_add_car_fields(merged_text: str) -> dict[str, bool]:
    """Extract add-car quote fields from CUSTOMER messages only (exclude system replies)."""
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    customer_text = " ".join(matches).lower()
    t = customer_text
    has_year = bool(re.search(r"20[12][0-9]", t))  # 2010-2029
    has_zip = bool(re.search(r"\b9[0-9]{4}\b", t)) or ("zip" in t and "9" in t)
    has_model = any(
        m in t
        for m in [
            "bmw", "x5", "x3", "x1", "x7", "tesla", "model y", "model 3", "model s", "model x",
            "honda", "accord", "civic", "cr-v", "crv", "pilot", "odyssey", "hr-v", "hrv",
            "toyota", "camry", "corolla", "rav4", "highlander", "4runner", "sienna", "tacoma",
            "lexus", "rx", "es", "nx", "mercedes", "benz", "gla", "glc",
            "mazda", "cx-5", "cx5", "cx-9", "subaru", "outback", "forester",
            "ford", "f-150", "f150", "mustang", "ram", "chevy", "chevrolet", "silverado",
            "rivian", "lucid", "hyundai", "kia",
            "宝马", "特斯拉", "本田", "丰田", "车型", "model", "凯美瑞", "思域", "马自达", "花冠",
        ]
    )
    has_delivery = any(
        m in t
        for m in [
            "next week", "下周", "提车", "拿车", "picking up", "pick up", "delivery", "deliver",
            "明天", "tomorrow", "下周拿", "明天拿", "下周提", "明天提",
        ]
    )
    has_driver = any(
        m in t
        for m in [
            "driver", "驾驶人", "谁开", "main driver", "primary driver",
            "老婆开", "老公开", "我开", "孩子开", "我老婆开", "我老公开",
            "spouse", "teen", "only me", "就我", "我一个人",
        ]
    )
    # VIN: 17 alphanumeric (excluding I,O,Q) or explicit "vin" mention
    has_vin = bool(re.search(r"\b[0-9a-hj-npr-z]{17}\b", t)) or "vin" in t
    # Insurance status: add-to-existing vs new customer
    has_add_to_existing = any(
        m in t for m in ["加车", "加一台", "加一辆", "add car", "add to policy", "existing policy", "想加"]
    )
    has_new_customer = any(
        m in t for m in ["新车", "new car", "刚买", "才买", "bought", "new policy", "新保单"]
    ) and not has_add_to_existing
    # Additional drivers
    has_additional_drivers = any(
        m in t for m in ["还有别人", "别人开", "老婆开", "老公开", "孩子开", "spouse", "teen", "other driver"]
    )
    has_only_me = any(
        m in t for m in ["就我", "我一个人", "only me", "only i"]
    )
    return {
        "year": has_year,
        "zip": has_zip,
        "model": has_model,
        "delivery": has_delivery,
        "driver": has_driver,
        "vin": has_vin,
        "add_to_existing": has_add_to_existing,
        "new_customer": has_new_customer,
        "additional_drivers": has_additional_drivers,
        "only_me": has_only_me,
    }


def _extract_remove_car_fields(merged_text: str) -> dict[str, bool]:
    """Extract remove-car fields from CUSTOMER messages only."""
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    customer_text = " ".join(matches).lower()
    t = customer_text
    has_vehicle = any(
        m in t
        for m in [
            "honda", "accord", "toyota", "camry", "bmw", "tesla", "2014", "2021",
            "卖", "拿掉", "车",
        ]
    ) and ("卖" in t or "拿掉" in t or "remove" in t or "drop" in t)
    has_sale_date = any(
        m in t
        for m in ["上个月", "last month", "上周", "last week", "昨天", "yesterday", "卖了", "sold"]
    )
    has_transfer = any(
        m in t
        for m in ["过户", "transferred", "transfer", "已经过户"]
    )
    return {
        "vehicle": has_vehicle,
        "sale_date": has_sale_date,
        "transfer": has_transfer,
    }


def _extract_missing_doc_status(merged_text: str) -> tuple[list[str], list[str]]:
    """
    Extract (items_mentioned, items_sent_status) from conversation text.
    Returns (items mentioned like dec page, garaging proof), (items client says they sent).
    Uses full merged text so broker-forwarded context (e.g. "UW need dec page. 客户说发过了") is included.
    """
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    t = " ".join(matches).lower() if matches else (merged_text or "").lower()
    items_mentioned: list[str] = []
    items_sent: list[str] = []
    if any(m in t for m in ["dec page", "declaration page", "decl page", "保单首页"]):
        items_mentioned.append("declaration_page")
        # Clarification only when question is about THIS item (e.g. "declaration page 是什么")
        is_dec_clarification = any(
            p in t for p in ["declaration page 是什么", "decl page 是什么", "declaration 是什么意思", "保单首页 是什么"]
        )
        if not is_dec_clarification and any(m in t for m in ["发", "sent", "发过", "又发", "resend", "already sent"]):
            items_sent.append("declaration_page")
    if any(m in t for m in ["garaging proof", "garaging", "停放"]):
        items_mentioned.append("garaging_proof")
        # Clarification only when question is about garaging (e.g. "garaging 是什么意思")
        is_garaging_clarification = any(
            p in t for p in ["garaging 是什么意思", "garaging proof 是什么", "garaging 是什么", "停放 是什么意思"]
        )
        if (
            not is_garaging_clarification
            and any(m in t for m in ["发", "sent", "发过", "又发", "already sent"])
            and "还没" not in t
            and "没弄" not in t
        ):
            items_sent.append("garaging_proof")
        elif any(m in t for m in ["还没", "没弄", "还没弄"]):
            pass  # explicitly not sent
    if any(m in t for m in ["driver's license", "driver license", "驾照", "dl copy", "dl "]):
        items_mentioned.append("driver_license")
        is_dl_clarification = any(
            p in t for p in ["驾照 是什么", "driver license 是什么", "dl 是什么", "驾照 是什么意思"]
        )
        if not is_dl_clarification and any(m in t for m in ["发", "sent", "发过", "正反面", "already sent"]):
            items_sent.append("driver_license")
    if any(m in t for m in ["questionnaire", "问卷"]):
        items_mentioned.append("questionnaire")
        if any(m in t for m in ["发", "sent", "发过", "又发"]):
            items_sent.append("questionnaire")
    return (items_mentioned, items_sent)


def _missing_document_structured_fields(merged_text: str) -> tuple[list[str], list[str]]:
    """
    Return (collected_fields, still_needed_fields) for missing-document broker handoff.
    Selective structured intake: requested items, customer-says-sent, still needed, verify step.
    """
    items_mentioned, items_sent = _extract_missing_doc_status(merged_text)
    collected: list[str] = []
    for item in items_mentioned:
        collected.append(f"requested_{item}")
    for item in items_sent:
        collected.append(f"customer_says_sent_{item}")
    if items_sent:
        collected.append("already_sent_claimed")
    lowered = (merged_text or "").lower()
    if any(m in lowered for m in ["uw", "underwriting", "escrow", "follow up", "follow-up", "followup"]):
        collected.append("underwriting_followup")

    still_needed: list[str] = []
    for item in items_mentioned:
        if item not in items_sent:
            still_needed.append(item)
    if items_sent and not still_needed:
        still_needed.append("verify_carrier_received")
    return (collected, still_needed)


def _extract_cancellation_fields(merged_text: str) -> dict[str, bool]:
    """Extract cancellation/payment-risk fields from customer messages."""
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    t = " ".join(matches).lower() if matches else (merged_text or "").lower()
    notice_present = any(
        m in t for m in ["notice", "通知", "final notice", "last notice", "cancellation", "cancel"]
    )
    screenshot_sent = any(
        m in t for m in ["截图", "screenshot", "发你", "发我", "发过", "sent", "发你微信", "发我微信"]
    )
    already_paid = any(
        m in t for m in ["付了", "paid", "已经付", "already paid", "换了新卡", "updated card"]
    )
    urgency_due = any(
        m in t for m in ["今天", "today", "due", "7天", "7 days", "最要紧", "urgent"]
    )
    return {
        "notice_present": notice_present,
        "screenshot_sent": screenshot_sent,
        "already_paid_claimed": already_paid,
        "urgency_due_confusion": urgency_due,
    }


def _cancellation_structured_fields(merged_text: str) -> tuple[list[str], list[str]]:
    """Return (collected_fields, still_needed_fields) for cancellation/payment-risk handoff."""
    fields = _extract_cancellation_fields(merged_text)
    collected: list[str] = []
    if fields.get("notice_present"):
        collected.append("notice_present")
    if fields.get("screenshot_sent"):
        collected.append("screenshot_sent")
    if fields.get("already_paid_claimed"):
        collected.append("already_paid_claimed")
    if fields.get("urgency_due_confusion"):
        collected.append("urgency_due_confusion")
    still_needed: list[str] = []
    if not fields.get("screenshot_sent") and not fields.get("already_paid_claimed"):
        still_needed.append("payment_proof_or_screenshot")
    if fields.get("already_paid_claimed") or fields.get("screenshot_sent"):
        still_needed.append("verify_carrier_received")
    return (collected, still_needed)


def _add_car_enough_for_handoff(fields: dict[str, bool]) -> bool:
    """Add-car case is ready when we have vehicle (year+model or VIN) + zip + (delivery or driver).
    Stricter than before: zip alone is not enough; office needs delivery or driver context for quote.
    See docs/sprints/add_car_quote_80_completion/03_CONVERSATION_SLOT_COLLECTION_SPEC.md"""
    vehicle_ok = (fields.get("year") and fields.get("model")) or fields.get("vin")
    if not vehicle_ok:
        return False
    has_zip = bool(fields.get("zip"))
    has_delivery_or_driver = bool(fields.get("delivery") or fields.get("driver"))
    return has_zip and has_delivery_or_driver


def _add_car_structured_fields(merged_text: str) -> tuple[list[str], list[str]]:
    """Return (collected_fields, still_needed_fields) for add-car broker handoff.
    Used for structured broker output; complements conversation_summary free text.
    Includes insurance_status and additional_drivers when detected (80% completion)."""
    fields = _extract_add_car_fields(merged_text)
    collected: list[str] = []
    if fields.get("year"):
        collected.append("year")
    if fields.get("model"):
        collected.append("make_model")
    if fields.get("vin"):
        collected.append("vin")
    if fields.get("zip"):
        collected.append("zip")
    if fields.get("delivery"):
        collected.append("delivery_date")
    if fields.get("driver"):
        collected.append("primary_driver")
    if fields.get("add_to_existing"):
        collected.append("insurance_status_add_to_existing")
    if fields.get("new_customer"):
        collected.append("insurance_status_new_customer")
    if fields.get("additional_drivers"):
        collected.append("additional_drivers_yes")
    if fields.get("only_me"):
        collected.append("additional_drivers_no")
    still_needed: list[str] = []
    if not _add_car_enough_for_handoff(fields):
        vehicle_ok = (fields.get("year") and fields.get("model")) or fields.get("vin")
        if not vehicle_ok:
            still_needed.extend(["year", "make_model"])
        if not fields.get("zip"):
            still_needed.append("zip")
        if not fields.get("delivery"):
            still_needed.append("delivery_date")
        if not fields.get("driver"):
            still_needed.append("primary_driver")
    else:
        if not fields.get("delivery"):
            still_needed.append("delivery_date")
        if not fields.get("driver"):
            still_needed.append("primary_driver")
    return (collected, still_needed)


def _extract_renewal_fields(merged_text: str) -> dict[str, bool]:
    """Extract renewal/premium-review fields from customer messages only."""
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    customer_text = " ".join(matches).lower()
    t = customer_text
    premium_concern = any(
        m in t
        for m in [
            "premium too high", "rate too high", "保费太高", "保费太贵", "太高了", "太贵了",
            "怎么降", "怎么降一点", "怎么降保费", "lower", "cheaper", "便宜",
        ]
    )
    renewal_context = any(
        m in t
        for m in [
            "renewal", "续保", "续保涨", "renewal premium", "renewal review",
        ]
    )
    remove_vehicle_interest = any(
        m in t
        for m in [
            "去掉", "拿掉", "去掉会便宜", "其中一辆", "remove one", "remove a car",
            "remove vehicle", "drop vehicle", "删掉",
        ]
    )
    coverage_adjust_interest = any(
        m in t
        for m in [
            "coverage", "adjust", "adjustment", "调整", "coverage change",
        ]
    )
    policy_bill_sent = any(
        m in t
        for m in [
            "发", "sent", "发你", "发我", "微信", "bill", "policy", "账单", "保单",
            "发过了", "already sent",
        ]
    )
    return {
        "premium_concern": premium_concern,
        "renewal_context": renewal_context,
        "remove_vehicle_interest": remove_vehicle_interest,
        "coverage_adjust_interest": coverage_adjust_interest,
        "policy_bill_sent": policy_bill_sent,
    }


def _renewal_structured_fields(merged_text: str) -> tuple[list[str], list[str]]:
    """Return (collected_fields, still_needed_fields) for renewal/premium-review broker handoff."""
    fields = _extract_renewal_fields(merged_text)
    collected: list[str] = []
    if fields.get("premium_concern"):
        collected.append("premium_concern")
    if fields.get("renewal_context"):
        collected.append("renewal_context")
    if fields.get("remove_vehicle_interest"):
        collected.append("remove_vehicle_interest")
    if fields.get("coverage_adjust_interest"):
        collected.append("coverage_adjust_interest")
    if fields.get("policy_bill_sent"):
        collected.append("policy_bill_sent")
    still_needed: list[str] = []
    if not fields.get("policy_bill_sent"):
        still_needed.append("renewal_notice_or_bill")
        still_needed.append("current_premium_details")
    if fields.get("remove_vehicle_interest"):
        still_needed.append("which_vehicle_to_remove")
    if fields.get("coverage_adjust_interest"):
        still_needed.append("target_coverage_preference")
    return (collected, still_needed)


def _extract_claim_fields(merged_text: str) -> dict[str, bool]:
    """Extract claim intake fields from customer messages only."""
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    customer_text = " ".join(matches).lower()
    t = customer_text
    accident_reported = any(
        m in t
        for m in [
            "accident", "car accident", "出事故", "刚出事故", "出险", "理赔", "撞车", "撞了",
            "出事了", "claim", "file a claim",
        ]
    )
    hit_and_run = any(
        m in t
        for m in [
            "对方跑了", "hit and run", "hit-and-run", "跑了",
        ]
    )
    photos = any(
        m in t
        for m in [
            "照片", "photos", "拍照", "拍了", "took photos",
        ]
    )
    other_driver_info = any(
        m in t
        for m in [
            "对方", "other driver", "license", "insurance", "车牌", "对方保险",
        ]
    )
    police_report = any(
        m in t
        for m in [
            "police", "警察", "报案", "report",
        ]
    )
    injuries = any(
        m in t
        for m in [
            "injuries", "受伤", "injury", "人没事",
        ]
    )
    return {
        "accident_reported": accident_reported,
        "hit_and_run": hit_and_run,
        "photos": photos,
        "other_driver_info": other_driver_info,
        "police_report": police_report,
        "injuries": injuries,
    }


def _claim_structured_fields(merged_text: str) -> tuple[list[str], list[str]]:
    """Return (collected_fields, still_needed_fields) for claim intake broker handoff."""
    fields = _extract_claim_fields(merged_text)
    collected: list[str] = []
    if fields.get("accident_reported"):
        collected.append("accident_reported")
    if fields.get("hit_and_run"):
        collected.append("hit_and_run")
    if fields.get("photos"):
        collected.append("photos")
    if fields.get("other_driver_info"):
        collected.append("other_driver_info")
    if fields.get("police_report"):
        collected.append("police_report")
    if fields.get("injuries"):
        collected.append("injuries")
    still_needed: list[str] = []
    if not fields.get("photos"):
        still_needed.append("photos")
    if not fields.get("other_driver_info"):
        still_needed.append("other_driver_insurance_license")
    still_needed.append("accident_time_location")
    if not fields.get("police_report"):
        still_needed.append("police_report_if_applicable")
    return (collected, still_needed)


def _derive_human_confirmation_fields(
    issue_category: str, collected_fields: list[str] | None, still_needed_fields: list[str] | None
) -> list[str]:
    """
    Derive which structured fields should be treated as "human confirmation required".

    This is a lightweight, rule-based layer aligned with LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT:
    - High‑risk fields (VIN, primary_driver, payment / cancellation, customer_says_sent_*)
    - Flows where broker must always double‑check before acting.
    """
    collected = collected_fields or []
    still_needed = still_needed_fields or []
    cat = (issue_category or "").lower()

    # Always require confirmation for cancellation / payment‑risk flows
    if cat in ("cancellation_warning", "payment_lapse_expiration"):
        # Surface any payment / already‑sent style markers
        high_risk = [
            f
            for f in collected
            if (
                f in ("already_paid_claimed", "screenshot_sent")
                or f.startswith("customer_says_sent")
                or "already_sent" in f
                or "payment" in f
            )
        ]
        # Also flag generic "verify_carrier_received" type needs
        high_risk.extend(
            f
            for f in still_needed
            if "verify_carrier_received" in f or "payment" in f
        )
        # Deduplicate while preserving order
        seen: set[str] = set()
        ordered: list[str] = []
        for f in high_risk:
            if f not in seen:
                seen.add(f)
                ordered.append(f)
        return ordered

    high_risk_fields: list[str] = []

    # Generic "customer says sent" style fields — broker must verify
    for f in collected:
        if f.startswith("customer_says_sent") or "already_sent" in f:
            high_risk_fields.append(f)

    # Vehicle / quote‑critical identifiers
    for f in collected:
        if f in ("vin", "primary_driver"):
            high_risk_fields.append(f)

    # Renewal: bill / policy sent is high‑leverage but must be sanity‑checked
    if cat == "customer_question" or cat == "missing_document" or cat == "renewal_premium":
        for f in collected:
            if f in ("policy_bill_sent", "renewal_context"):
                high_risk_fields.append(f)

    # Deduplicate while preserving order
    seen_generic: set[str] = set()
    ordered_generic: list[str] = []
    for f in high_risk_fields:
        if f not in seen_generic:
            seen_generic.add(f)
            ordered_generic.append(f)
    return ordered_generic


def _get_add_car_acknowledgement(last_customer_msg: str, fields: dict[str, bool], language: str) -> str:
    """Build a short acknowledgement of what the customer just said, for office-natural flow.
    E.g. '2024年的' -> '好的，2024年的。' ; '90210' -> '好的，邮编90210。'"""
    msg = (last_customer_msg or "").strip()
    if not msg or len(msg) > 80:
        return ""
    lowered = msg.lower()
    parts: list[str] = []
    if fields.get("year") and re.search(r"20[12][0-9]", msg):
        m = re.search(r"(20[12][0-9][年的]*)", msg)
        if m:
            parts.append(m.group(1) + ("的。" if "的" not in m.group(1) else "。"))
    if fields.get("zip") and re.search(r"\b9[0-9]{4}\b", msg):
        m = re.search(r"(9[0-9]{4})", msg)
        if m:
            if language == "zh":
                parts.append(f"邮编{m.group(1)}。")
            else:
                parts.append(f"zip {m.group(1)}.")
    if fields.get("model") and not parts:
        model_snippets = [
            (r"宝马\s*[xX]?[3571]", "宝马"),
            (r"tesla\s*model\s*[yY3sSxX]", "Tesla"),
            (r"honda\s*(accord|civic|cr-v|crv)", "Honda"),
            (r"toyota\s*(camry|corolla|rav4)", "Toyota"),
            (r"丰田\s*花冠", "丰田花冠"),
            (r"202[0-9]\s*(bmw|honda|toyota|tesla)", "year+make"),
        ]
        for pat, _ in model_snippets:
            m = re.search(pat, msg, re.I)
            if m:
                parts.append(m.group(0) + "。")
                break
    if not parts and len(msg) <= 40:
        parts.append(msg.rstrip("。，, ") + "。")
    if not parts:
        return ""
    ack = "好的，" + " ".join(parts) if language == "zh" else "Got it, " + " ".join(parts).rstrip(".")
    return ack if ack.endswith("。") or ack.endswith(".") else ack + ("。" if language == "zh" else ".")


def _get_next_ask_for_add_car(
    merged_text: str,
    fields: dict[str, bool],
    language: str,
    add_car_rules: dict[str, dict[str, str]] | None = None,
    customer_turn_count: int = 0,
) -> str | None:
    """Return the next most useful ask for add-car, or None if we should hand off.
    Ask order: vehicle (year+model) first when missing, then zip, then delivery+driver.
    Adds acknowledgement of what customer just said for office-natural flow.
    Uses add_car_rules from config when not overridden.
    TOP_COMMERCIAL_DEEPENING: when we have delivery but not driver at turn 2 only,
    ask for driver to allow one more turn for corrections (LC-AC3: 我刚才说错了，是我老婆开那辆)."""
    if _add_car_enough_for_handoff(fields):
        # One more ask at turn 2 only when delivery present but driver missing — captures driver corrections
        if (
            customer_turn_count == 2
            and fields.get("delivery")
            and not fields.get("driver")
        ):
            rules = add_car_rules or get_add_car_rules()
            matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
            last_customer = matches[-1].strip() if matches else ""
            ack = _get_add_car_acknowledgement(last_customer, fields, language)
            prefix = (ack.rstrip("。") + "。") if ack else ""
            prefix = prefix + " " if prefix else ""
            ask = rules.get("ask_driver_only", {}).get(language) or (
                "主要驾驶人发我一下，我好安排报价。"
                if language == "zh"
                else "Send me the main driver so I can prepare the quote."
            )
            return prefix + ask
        return None
    rules = add_car_rules or get_add_car_rules()
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    last_customer = matches[-1].strip() if matches else ""
    ack = _get_add_car_acknowledgement(last_customer, fields, language)
    prefix = (ack.rstrip("。") + "。") if ack else ""
    prefix = prefix + " " if prefix else ""

    vehicle_ok = (fields.get("year") and fields.get("model")) or fields.get("vin")
    if not vehicle_ok:
        ask = rules.get("ask_vehicle", {}).get(language) or (
            "先把年份和车型发我，我就能帮你算。"
            if language == "zh"
            else "Send me the year and make/model first so I can run the quote."
        )
        return prefix + ask
    if not fields.get("zip"):
        ask = rules.get("ask_zip", {}).get(language) or (
            "先把地址邮编发我，我就能帮你算。"
            if language == "zh"
            else "Send me the zip or address first and I will run the quote."
        )
        return prefix + ask
    if not fields.get("delivery") and not fields.get("driver"):
        ask = rules.get("ask_delivery_driver", {}).get(language) or (
            "提车日期和主要驾驶人发我一下，我好安排报价。"
            if language == "zh"
            else "Send me the delivery date and main driver so I can prepare the quote."
        )
        return prefix + ask
    return None


def _get_next_ask_draft(
    merged_text: str,
    category: str,
    base_result: dict[str, Any],
    customer_turn_count: int,
    add_car_rules: dict[str, dict[str, str]] | None = None,
) -> str | None:
    """
    If we should ask one more thing instead of handing off, return the draft.
    Otherwise return None (hand off).
    Only applies when customer_turn_count >= 2 (second or third turn).
    Focus: add-car quote (ask for zip/delivery/driver when missing).
    Other categories: hand off after 2 turns to avoid repeating the same ask.
    """
    if customer_turn_count < 2:
        return None
    language = "zh" if _contains_chinese(merged_text) else "en"
    lowered = (merged_text or "").lower()

    if _is_add_vehicle_request(lowered):
        fields = _extract_add_car_fields(merged_text)
        return _get_next_ask_for_add_car(
            merged_text, fields, language, add_car_rules, customer_turn_count
        )

    return None


def _should_handoff(
    customer_turn_count: int,
    manual_followup_needed: bool,
    category: str,
) -> bool:
    """Decide if we have enough info to hand off to broker."""
    if not manual_followup_needed:
        return True
    if customer_turn_count >= 2:
        return True
    return False


def triage_conversation(
    latest_text: str,
    conversation_turns: list[dict[str, str]],
    add_car_rules_override: dict[str, dict[str, str]] | None = None,
    client_id: str | None = None,
) -> dict[str, Any]:
    """
    Triage within a multi-turn conversation.
    Merges conversation context with latest message for triage.
    Returns handoff_ready=True when broker should receive the case.
    add_car_rules_override: optional rules for preview; when set, used instead of config.
    client_id: optional; when omitted, uses CLIENT_ID env or chen_kui for handoff phrases.
    """
    resolved_client_id = (client_id or "").strip() or get_active_client_id()
    customer_turns = [t for t in conversation_turns if (t.get("role") or "").strip().lower() == "customer"]
    customer_count = len(customer_turns)

    merged_text = _build_conversation_text_for_triage(conversation_turns, latest_text)
    if not merged_text.strip():
        return {
            "issue_category": "unclear",
            "urgency": "medium",
            "broker_next_step": "Request clarification from sender.",
            "client_prep": "N/A",
            "client_reply_draft": "Could you please provide more details about your inquiry?",
            "manual_followup_needed": True,
            "handoff_ready": False,
            "conversation_summary": "",
        }

    # SALES_READINESS_HARDENING: Talk to Agent free-text detection.
    # If last customer message requests human contact, hand off immediately (any turn).
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    last_customer_msg = (matches[-1] or "").strip() if matches else (latest_text or "").strip()
    if _is_talk_to_agent_request(last_customer_msg):
        handoff_phrases = _get_handoff_phrases(resolved_client_id)
        phrases = handoff_phrases.get("customer_requested_human", {}) if handoff_phrases else {}
        draft_zh = phrases.get("zh") or "好的，已帮您转给办公室，他们会尽快联系您。"
        draft_en = phrases.get("en") or "Got it. We've forwarded your request to the office. They will contact you shortly."
        prior_context = ""
        if customer_count > 0:
            prior_parts = []
            for t in conversation_turns:
                role = (t.get("role") or "").strip().lower()
                txt = (t.get("text") or "").strip()
                if role == "customer" and txt:
                    prior_parts.append(txt[:80] + ("…" if len(txt) > 80 else ""))
            if prior_parts:
                prior_context = " Prior context: " + "; ".join(prior_parts[-2:])
        return {
            "issue_category": "customer_requested_human",
            "urgency": "medium",
            "manual_followup_needed": True,
            "broker_next_step": "Customer requested human contact. Call or message back promptly.",
            "client_prep": "Customer wants to speak with office.",
            "client_reply_draft": draft_zh,
            "handoff_ready": True,
            "conversation_summary": "Customer requested to speak with office / 客户要求联系人工" + prior_context,
            "collected_fields": ["customer_requested_human"],
            "still_needed_fields": [],
            "case_creation_suggested": True,
            "next_best_question": "",
            "lifecycle_status": "handoff_pending",
            "collection_stage": "enough_for_handoff",
        }

    # Selective LLM routing: simple turns use fast path (SIMULATION_ASSISTANT_SPEED_LAYER_BLUEPRINT)
    use_fast_path = (
        _is_llm_enabled()
        and _is_fast_path_candidate(merged_text, customer_count + 1)
    )
    if _is_llm_enabled() and use_fast_path:
        base_result = _rule_based_triage(merged_text, resolved_client_id)
        base_result["triage_path"] = "fast"
    elif _is_llm_enabled():
        base_result = _llm_triage(merged_text, resolved_client_id)
        base_result["triage_path"] = "llm"
    else:
        base_result = _rule_based_triage(merged_text, resolved_client_id)
        base_result["triage_path"] = "rule"

    would_handoff = _should_handoff(
        customer_count + 1,
        base_result.get("manual_followup_needed", True),
        base_result.get("issue_category", "unclear"),
    )

    # Add-car: first turn with enough info → hand off immediately (MATURE_INTAKE_SKELETON)
    if (
        base_result.get("issue_category") == "customer_question"
        and _is_add_vehicle_request((merged_text or "").lower())
        and customer_count + 1 == 1
    ):
        fields = _extract_add_car_fields(merged_text)
        if _add_car_enough_for_handoff(fields):
            would_handoff = True

    next_ask = _get_next_ask_draft(
        merged_text,
        base_result.get("issue_category", "unclear"),
        base_result,
        customer_count + 1,
        add_car_rules_override,
    )

    if would_handoff and next_ask:
        handoff = False
        result_draft = next_ask
    else:
        handoff = would_handoff
        result_draft = base_result.get("client_reply_draft", "")

    handoff_phrases = _get_handoff_phrases(resolved_client_id)
    lowered_merged = (merged_text or "").lower()
    is_add_car = _is_add_vehicle_request(lowered_merged)
    is_remove_car = _is_remove_vehicle_request(lowered_merged)
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    last_customer_raw = (matches[-1] or "").strip() if matches else ""
    follow_up_type = _derive_follow_up_type(last_customer_raw)
    collection_stage = _derive_collection_stage(
        base_result.get("issue_category", "unclear"),
        merged_text,
        customer_count + 1,
        handoff,
    )
    if is_add_car:
        key = "add_car"
    elif is_remove_car:
        key = "remove_car" if handoff_phrases.get("remove_car") else "other"
    else:
        # Use derived follow_up_type for reply strategy (LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT)
        if follow_up_type in ("clarification_question", "urgency_question", "next_step_question", "office_review_question"):
            key = "other_clarification" if handoff_phrases.get("other_clarification") else "other"
        elif follow_up_type == "already_sent":
            key = "other_received" if handoff_phrases.get("other_received") else "other"
        elif follow_up_type == "correction":
            key = "other_corrected" if handoff_phrases.get("other_corrected") else "other"
        else:
            key = "other"
    phrases = handoff_phrases.get(key, {}) if handoff_phrases else {}
    # Reassure-first: when already_sent + "why still chasing", answer first then hand off
    why_still_chasing = any(
        m in last_customer_raw.lower()
        for m in ("怎么还在追", "为什么还在追", "为什么还追", "怎么还追", "why still", "why are they still")
    )
    if handoff and key == "other_received" and why_still_chasing:
        handoff_reply_zh = "可能是材料还没到或者没对上。好的，收到了。办公室会尽快核实，有结果会联系您。"
        handoff_reply_en = "It may be that the documents have not arrived or did not match. Got it, thanks. Our office will verify and follow up with you."
    else:
        handoff_reply_zh = phrases.get("zh") or (
            "报价资料已收集，办公室会尽快出价，有结果会联系您。" if is_add_car
            else "您说的卖车信息已整理好了，办公室会尽快处理，有结果会联系您。" if is_remove_car
            else "您说的情况已整理好了，办公室会尽快处理，有结果会联系您。"
        )
        handoff_reply_en = phrases.get("en") or (
            "Quote details received. Our office will review and follow up with you." if is_add_car
            else "Got your vehicle removal details. Our office will process this and follow up with you." if is_remove_car
            else "Got it. We've noted your info—our office will review and follow up with you."
        )

    language = _detect_client_language(merged_text)
    handoff_reply = handoff_reply_zh if language == "zh" else handoff_reply_en

    # Document clarification: when customer asks "what does garaging proof mean? what to send?"
    # after handoff, answer the question first instead of generic handoff (SIM2 fix)
    if handoff and key == "other_clarification":
        last_customer_lower = last_customer_raw.lower() if last_customer_raw else ""
        if _is_document_confusion_request(last_customer_lower) and any(
            m in last_customer_lower for m in ("garaging", "garaging proof", "停放", "declaration page", "dec page", "保单首页")
        ):
            # Build explanation as customer_question (document confusion) not missing_document
            tailored = _build_client_reply_draft(merged_text, "customer_question")
            if tailored and len(tailored) > 30 and (
                "garaging" in tailored.lower() or "停放" in tailored or "declaration" in tailored.lower()
            ):
                handoff_suffix_zh = "。办公室会尽快处理，有结果会联系您。"
                handoff_suffix_en = ". Our office will process this and follow up with you."
                handoff_suffix = handoff_suffix_zh if language == "zh" else handoff_suffix_en
                handoff_reply = tailored.rstrip("。.") + handoff_suffix

    # Correction + embedded urgency/next-step question: answer the question first (SIM1 Turn 3 fix)
    # When user says "其实已经付了...那我现在最要紧做什么？", don't just say "好的明白了" — answer the ask
    if handoff and key == "other_corrected":
        last_customer_lower = last_customer_raw.lower() if last_customer_raw else ""
        urgency_next_markers = (
            "最要紧", "先干嘛", "先看什么", "办公室先看什么", "what matters most",
            "what should i do", "is this urgent", "是不是今天", "一定要处理",
        )
        has_embedded_question = any(m in last_customer_lower for m in urgency_next_markers)
        cat = base_result.get("issue_category", "")
        if has_embedded_question and cat in ("payment_lapse_expiration", "cancellation_warning"):
            if language == "zh":
                handoff_reply = (
                    "您这边最要紧的是等办公室确认付款是否到账；如果确认了您这边就不用再做什么。"
                    "办公室会尽快处理，有结果会联系您。"
                )
            else:
                handoff_reply = (
                    "The most important thing for you now is to wait for our office to confirm "
                    "whether the payment was received; if confirmed, you don't need to do anything else. "
                    "Our office will process this and follow up with you."
                )

    result = dict(base_result)
    result["handoff_ready"] = handoff
    result["follow_up_type"] = follow_up_type
    result["collection_stage"] = collection_stage
    # Phase 2: next_best_question when still collecting
    result["next_best_question"] = (result_draft or "") if not handoff else ""
    # Phase 2: lifecycle_status for triage (no case yet)
    result["lifecycle_status"] = "handoff_pending" if handoff else "collecting"
    # Reassure-then-route: signal when case creation is appropriate (for UI confirmation)
    result["case_creation_suggested"] = (
        handoff
        and (
            len(result.get("collected_fields") or []) > 0
            or base_result.get("issue_category") in ("cancellation_warning", "payment_lapse_expiration", "missing_document")
        )
    )
    result["conversation_summary"] = _build_conversation_summary(
        merged_text, base_result, customer_count + 1
    )
    if handoff:
        result["client_reply_draft"] = handoff_reply
    else:
        result["client_reply_draft"] = result_draft

    lowered = (merged_text or "").lower()
    if is_add_car:
        collected, still_needed = _add_car_structured_fields(merged_text)
        result["collected_fields"] = collected
        result["still_needed_fields"] = still_needed
    elif _is_premium_review_request(lowered):
        collected, still_needed = _renewal_structured_fields(merged_text)
        result["collected_fields"] = collected
        result["still_needed_fields"] = still_needed
    elif _is_claim_intake_request(lowered):
        collected, still_needed = _claim_structured_fields(merged_text)
        result["collected_fields"] = collected
        result["still_needed_fields"] = still_needed
    elif base_result.get("issue_category") == "missing_document":
        collected, still_needed = _missing_document_structured_fields(merged_text)
        result["collected_fields"] = collected
        result["still_needed_fields"] = still_needed
    elif base_result.get("issue_category") in ("cancellation_warning", "payment_lapse_expiration"):
        collected, still_needed = _cancellation_structured_fields(merged_text)
        result["collected_fields"] = collected
        result["still_needed_fields"] = still_needed
    else:
        result["collected_fields"] = []
        result["still_needed_fields"] = []

    # Human‑confirmation signals for broker / UI visibility
    human_fields = _derive_human_confirmation_fields(
        base_result.get("issue_category", ""),
        result.get("collected_fields"),
        result.get("still_needed_fields"),
    )
    result["human_confirmation_fields"] = human_fields
    result["human_confirmation_required"] = bool(human_fields)

    # Package 2.0: When client says "already sent" or "already paid", make broker_next_step
    # explicitly actionable so broker knows to verify with carrier (reduces manual follow-up).
    collected_list = result.get("collected_fields") or []
    already_sent_or_paid = (
        follow_up_type == "already_sent"
        or "already_paid_claimed" in collected_list
        or "customer_says_sent_" in str(collected_list)
    )
    if handoff and already_sent_or_paid:
        cat = base_result.get("issue_category", "")
        if cat == "missing_document":
            result["broker_next_step"] = (
                "Verify with carrier that resubmitted documents were received; "
                "request any still-missing items."
            )
        elif cat in ("payment_lapse_expiration", "cancellation_warning"):
            result["broker_next_step"] = (
                "Confirm with carrier that payment was received; "
                "if not, process payment today to avoid lapse."
            )

    # Package 2.0 Loop 2: Renewal handoff when policy/bill sent — clearer broker_next_step.
    if handoff and _is_premium_review_request(lowered) and "policy_bill_sent" in collected_list:
        result["broker_next_step"] = (
            "Review renewal notice and quote options; "
            "confirm remove-vehicle intent if client asked, then send 1–2 realistic options."
        )

    # Package 2.0 Loop 2: Add-car handoff — more concrete broker_next_step when we have vehicle+zip.
    if handoff and is_add_car:
        fields = _extract_add_car_fields(merged_text)
        if _add_car_enough_for_handoff(fields):
            result["broker_next_step"] = (
                "Run quote for collected vehicle details (year, model, zip). "
                "Confirm delivery date and driver with client before binding."
            )

    return result


def triage_message(text: str) -> dict[str, Any]:
    """
    Triage an inbound message.

    Returns dict with: issue_category, urgency, broker_next_step, client_prep,
    client_reply_draft, manual_followup_needed.
    """
    if not text or not str(text).strip():
        return {
            "issue_category": "unclear",
            "urgency": "medium",
            "broker_next_step": "Request clarification from sender.",
            "client_prep": "N/A",
            "client_reply_draft": "Could you please provide more details about your inquiry?",
            "manual_followup_needed": True,
        }

    if _is_llm_enabled():
        return _llm_triage(text)
    return _rule_based_triage(text)
