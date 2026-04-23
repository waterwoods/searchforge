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
    get_intake_evolution_variant,
    get_v6_auto_input_variant,
    get_reply_templates,
    get_stitched_handoff_phrases,
    get_workflow_fallbacks,
)
from services.fiqa_api.inbox_triage.case_draft_engine import (
    action_ready_vin_soft_confirmation_warranted,
    augment_next_ask_with_variant,
    build_auto_progress_client_reply,
    build_generic_case_draft,
    build_v4_case_draft_bundle,
    build_v4_confirmation_client_reply_from_bundle,
    estimate_v4_error_risk_score,
    estimate_v5_handoff_risk_score,
    evaluate_action_ready_rule,
    evaluate_v5_case_usable,
    min_v5_case_usable_core_met,
)
from services.fiqa_api.inbox_triage.field_strategy import should_skip_user_prompt_for_missing_field
from services.fiqa_api.inbox_triage.add_car_field_contract import (
    dedupe_preserve_order,
    quote_ready_matches_still_needed,
    validate_add_car_field_lists,
)
from services.fiqa_api.inbox_triage.add_car_intent import (
    INTENT_CORRECTION,
    INTENT_GENERIC_FOLLOWUP,
    INTENT_MATERIALS_CLAIM,
    INTENT_OFFICE_RECEIPT_QUESTION,
    INTENT_QUOTE_DETAIL_QUESTION,
    INTENT_SUPPLEMENT_INFO,
    INTENT_TIMELINE_QUESTION,
    ResolvedAddCarIntent,
    nudge_append_generic_to_supplement_intent,
    resolve_add_car_turn_intent,
)
from services.fiqa_api.inbox_triage.add_car_llm_slot_candidates import (
    maybe_augment_merged_text_for_add_car_slots,
)
from services.fiqa_api.inbox_triage.add_car_vehicle_signals import (
    _VIN_17_RE,
    text_has_vehicle_make_model_signal,
    text_has_vehicle_year_signal,
)
from services.fiqa_api.inbox_triage.notice_retrieval import (
    format_retrieval_augment,
    retrieve_document_explanation,
    retrieve_notice_explanation,
)
from services.fiqa_api.inbox_triage.routing_guard import (
    append_turn_signals_extra_vehicle_intent,
    detect_vehicle_conflict,
    text_suggests_vehicle_scope_ambiguity,
)
from services.fiqa_api.inbox_triage.truth_field_guardrails import (
    _context_reuse_signal,
    _vin_deferral_signal,
    _vin_intent_mentioned,
    apply_strict_truth_guardrails_to_add_car_fields,
    log_truth_guardrail_blocked,
    maybe_attach_truth_guardrail_debug_to_triage,
    should_accept_field,
    truth_guardrail_debug_session_start,
)
from services.fiqa_api.inbox_triage.add_car_triage_post_submit import (
    ADD_CAR_OFFICE_RECEIPT_PRE_FALLBACK_EN as _ADD_CAR_OFFICE_RECEIPT_PRE_FALLBACK_EN,
    ADD_CAR_OFFICE_RECEIPT_PRE_FALLBACK_ZH as _ADD_CAR_OFFICE_RECEIPT_PRE_FALLBACK_ZH,
    POST_SUBMIT_ADD_CAR_FALLBACK_POOLS as _POST_SUBMIT_ADD_CAR_FALLBACK_POOLS,
    effective_add_car_handoff_storage_key as _effective_add_car_handoff_storage_key,
    post_submit_add_car_fallback_line as _post_submit_add_car_fallback_line,
    post_submit_rot_idx as _post_submit_rot_idx,
    prepend_add_car_post_submit_intent_head as _prepend_add_car_post_submit_intent_head,
    truth_allows_post_submit_handoff_phrasing as _truth_allows_post_submit_handoff_phrasing,
)
from services.fiqa_api.inbox_triage.append_case_boundary_copy import (
    merged_append_boundary_copy as _merged_append_boundary_copy,
)

logger = logging.getLogger(__name__)

# Config cache: loaded once, fallback to hardcoded when empty
_MARKERS_CACHE: dict[str, tuple[str, ...]] | None = None
_DOCUMENT_ITEMS_CACHE: tuple[tuple[tuple[str, ...], str, str], ...] | None = None
_HANDOFF_CACHE: dict[str, dict[str, dict[str, str]]] = {}  # client_id -> phrases
_STITCHED_CACHE: dict[str, dict[str, Any]] = {}  # client_id -> stitched phrase map
_REPLY_TEMPLATES_CACHE: dict[str, dict[str, Any]] = {}  # client_id -> merged templates
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
    "triage_mode",  # greenfield | append — disambiguates handoff_ready (see PILOT_CONTRACT_ADD_CAR_V1.md §4.3)
    "action_ready",  # V2.6: min-core truth bar met (VIN+ZIP+tier1+(driver|delivery), HT1)
    "intake_flow_milestone",  # collecting | near_usable | usable | action_ready
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


def _get_stitched_phrases(client_id: str | None = None) -> dict[str, Any]:
    """Per-client stitched copy (materials-sent, prospective-send, etc.); no cross-client fallback."""
    cid = (client_id or "").strip() or get_active_client_id()
    if cid not in _STITCHED_CACHE:
        _STITCHED_CACHE[cid] = get_stitched_handoff_phrases(cid)
    return _STITCHED_CACHE.get(cid, {})


def _stitched_customer_visible_line(
    client_id: str | None,
    key: str,
    lang: str,
    default_zh: str,
    default_en: str,
) -> str:
    """One zh/en line from stitched map; engine defaults when client omits key (no cross-client fallback)."""
    stitched = _get_stitched_phrases(client_id)
    block = stitched.get(key)
    if not isinstance(block, dict):
        return default_zh if lang == "zh" else default_en
    if lang == "zh":
        v = (block.get("zh") or "").strip()
        return v or default_zh
    v = (block.get("en") or "").strip()
    return v or default_en


def _stitched_customer_visible_line_prefer(
    client_id: str | None,
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
    """Pick post_submit stitched block when allowed and present; else primary (or post defaults)."""
    if use_post_submit:
        stitched = _get_stitched_phrases(client_id)
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
    return _stitched_customer_visible_line(client_id, primary_key, lang, default_zh, default_en)


def _maybe_append_add_car_price_caveat(
    text_for_markers: str,
    draft: str,
    lang: str,
    client_id: str | None,
) -> str:
    """Append configurable caveat when customer asks ballpark/cheaper premium during add-car collection."""
    lowered = (text_for_markers or "").lower()
    if not any(
        m in lowered
        for m in (
            "便宜",
            "能便宜",
            "保费多少",
            "多少钱",
            "大概多少",
            "先帮我看看大概",
            "cheaper",
            "lower premium",
            "how much",
            "ballpark",
            "roughly",
        )
    ):
        return draft
    caveat = _stitched_customer_visible_line(
        client_id,
        "add_car_price_caveat",
        lang,
        "；具体数字要等办公室按车型和地址算出来。",
        "; exact premium depends on the vehicle and garaging—our office will run the numbers.",
    )
    if lang == "zh":
        return draft.rstrip("。") + caveat
    return draft.rstrip(".") + caveat


def _get_reply_templates(client_id: str | None = None) -> dict[str, Any]:
    """Get reply templates from config or empty dict (caller uses hardcoded fallback). Per-client cache."""
    global _REPLY_TEMPLATES_CACHE
    cid = (client_id or "").strip() or get_active_client_id()
    if cid not in _REPLY_TEMPLATES_CACHE:
        _REPLY_TEMPLATES_CACHE[cid] = get_reply_templates(cid)
    return _REPLY_TEMPLATES_CACHE[cid]


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


def _is_add_car_multi_driver_quote_question(text: str) -> bool:
    """NA-Chinese: spouse/secondary driver + how to quote — add-car intake, not missing DL resend."""
    tl = (text or "").lower()
    if not any(
        x in tl
        for x in (
            "老婆",
            "老公",
            "spouse",
            "也会开",
            "都会开",
            "都要开",
            "两个人开",
            "两人开",
            "她也开",
            "他也会开",
        )
    ):
        return False
    if not any(x in tl for x in ("quote", "报价", "怎么报")):
        return False
    return True


def _is_add_vehicle_request(text: str) -> bool:
    """Add-car/quote: requires add_vehicle markers AND (vehicle_context OR quote/报价 OR delivery/pickup)."""
    lowered = (text or "").lower()
    raw = text or ""
    # Pilot contract: literal VIN, VIN deferral, context-reuse, and thin English VIN lines must
    # still land in the Add-Car lane (truth remains guardrail-gated).
    if _VIN_17_RE.search(raw):
        return True
    if re.search(r"\bvin\s+is\b", lowered) or re.search(
        r"(?i)vin\s*是\s*[0-9a-hj-npr-z]", raw
    ):
        return True
    if _vin_intent_mentioned(lowered, raw) and _vin_deferral_signal(lowered, raw):
        return True
    if _context_reuse_signal(raw, lowered):
        return True
    if re.search(
        r"\b(my wife|my husband)\b.{0,48}\bdriv|\bwife drives\b|\bhusband drives\b|\bdrives mostly\b",
        lowered,
    ):
        return True
    if _is_add_car_multi_driver_quote_question(raw):
        return True
    # English colloquial add-car entry (minimal phrases — do not require vehicle_context / quote substring)
    _en_add_car = (
        r"\badd\s+car\b",
        r"\badd\s+a\s+car\b",
        r"\badd\s+another\s+car\b",
        r"\badd\s+vehicle\b",
        r"\badd\s+a\s+vehicle\b",
        r"\badd\s+my\s+car\b",
        r"\bneed\s+to\s+add\s+(my\s+)?car\b",
        r"\bneed\s+to\s+add\s+a\s+(car|vehicle)\b",
        r"\bquote\s+for\s+a\s+car\b",
        r"\bquote\s+for\s+a\s+vehicle\b",
        r"\binsurance\s+for\s+a\s+new\s+car\b",
    )
    if any(re.search(p, lowered) for p in _en_add_car):
        return True
    # Spouse / household vehicle quote ("老婆那台塞纳也报一下价") — 报+价 without contiguous "报价" substring
    if ("报" in raw and "价" in raw) and any(
        x in raw for x in ("老婆", "老公", "先生", "太太", "配偶")
    ):
        if _contains_any(lowered, _get_markers("vehicle_context")) or bool(re.search(r"[那这哪]台", raw)):
            return True
    # Second household vehicle ("家里还有一台…也要一起报")
    if any(x in raw for x in ("家里还有", "还有一台", "另一台", "也要一起报")) and (
        _contains_any(lowered, _get_markers("vehicle_context")) or "台" in raw or "辆" in raw
    ) and any(m in raw for m in ("报", "报价", "quote", "加车", "价")):
        return True
    # Thin turn: materials channel + already-sent + what's missing (handled as add-car for structured slots)
    if any(m in raw for m in ("还缺什么", "还缺啥", "现在还缺", "还要补什么", "还缺资料", "缺什么资料")) and (
        any(m in raw for m in ("发过了", "发了", "又发", "刚发", "已经发", "发了一次"))
        or any(m in lowered for m in ("微信发", "发你微信", "发我微信", "邮箱发", "邮件发"))
    ) and any(
        m in lowered
        for m in (
            "微信",
            "材料",
            "vin",
            "registration",
            "行驶证",
            "加车",
            "quote",
            "报价",
            "邮箱",
            "邮件",
        )
    ):
        return True
    # NA-Chinese / mixed: pushback on broker quote + re-shop or coverage tweak (not renewal-bill premium review)
    if (
        any(m in raw for m in ("报的价", "上次报的价"))
        or ("上次" in raw and "报价" in raw)
    ) and any(
        m in lowered
        for m in (
            "太贵",
            "太高",
            "别的company",
            "其他公司",
            "coverage",
            "换一家",
            "再看看",
            "能不能再",
        )
    ):
        return True
    # Re-shop / re-quote phrasing without explicit "上次报价" — still add-car when thread has vehicle/zip/year signals
    if any(
        m in raw
        for m in (
            "太贵",
            "太高",
            "换公司",
            "换一家",
            "换家",
            "别的公司",
            "其他公司",
            "再报",
            "再报价",
        )
    ) or any(m in lowered for m in ("too expensive", "another carrier", "other company", "re-shop", "reshop")):
        if any(
            m in lowered
            for m in (
                "quote",
                "报价",
                "加车",
                "company",
                "coverage",
                "保额",
                "提车",
                "拿车",
                "pick up",
                "pickup",
                "vin",
            )
        ):
            return True
        if bool(re.search(r"20[12][0-9]", raw)) or _text_has_ca_zip_signal(lowered):
            return True
        if _contains_any(lowered, _get_markers("vehicle_context")):
            return True
    # Spouse / referent vehicle: "我老婆那台也想加" — same thread second vehicle intent
    if any(x in raw for x in ("也想加", "也要加")) and (
        any(x in raw for x in ("老婆", "老公", "配偶", "先生", "太太"))
        or bool(re.search(r"[那这哪]台", raw))
    ):
        if (
            _contains_any(lowered, _get_markers("vehicle_context"))
            or "台" in raw
            or "辆" in raw
            or bool(re.search(r"20[12][0-9]", raw))
        ):
            return True
    # VIN + send-permission / materials question — add-car context without explicit 加车 (WIRC first-turn tolerance)
    if re.search(r"\bvin\b", lowered) or "vin码" in lowered:
        if _is_prospective_send_offer_message(lowered) and any(
            k in lowered for k in ("截图", "screenshot", "照片", "材料", "行驶证", "registration", "微信")
        ):
            return True
    # 行驶证 / registration + send-permission — common add-car doc offer, route off generic unclear
    if _is_prospective_send_offer_message(lowered) and (
        "行驶证" in (text or "") or "registration" in lowered
    ):
        return True
    if not _contains_any(lowered, _get_markers("add_vehicle")):
        return False
    if _contains_any(lowered, _get_markers("vehicle_context")) or "quote" in lowered or "报价" in lowered:
        return True
    delivery_pickup = (
        "下周",
        "提车",
        "拿车",
        "picking up",
        "pick up",
        "pickup",
        "pick-up",
        "tomorrow",
        "明天",
        "delivery",
        "deliver",
        "friday",
        "this friday",
        "next friday",
        "周五",
        "下周五",
        "本周五",
        "礼拜五",
    )
    if _contains_any(lowered, delivery_pickup):
        return True
    if re.search(r"\d{1,2}月\d{1,2}[号日]", text or "") and any(
        x in (text or "") for x in ("提", "拿车", "到车", "取车", "pick")
    ):
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
    # Add-car before premium review: mixed "加车 + 能便宜吗" stays on quote intake, not renewal review.
    if _is_add_vehicle_request(lowered):
        return "Confirm any missing driver, ZIP, or VIN if needed; then quote or add same day."
    if _is_premium_review_request(lowered):
        return "Review renewal notice and current premium; confirm remove-vehicle or coverage-adjust intent, then send 1–2 realistic options."
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
    if _is_add_vehicle_request(lowered):
        return "Year, make/model, VIN if available, delivery date, zip or address, lienholder if any, and primary driver details."
    if _is_premium_review_request(lowered):
        return "Current declaration page, latest bill, and any recent vehicle, driver, address, or coverage changes."
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


def _build_client_reply_draft(text: str, category: str, client_id: str | None = None) -> str:
    language = _detect_client_language(text)
    items = _extract_requested_items(text, language)
    item_text = _join_readable(items, language)
    lowered = (text or "").lower()
    templates = _get_reply_templates(client_id)

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
                tail = _stitched_customer_visible_line(
                    client_id,
                    "document_already_sent_tail",
                    "zh",
                    "；如果材料说发过了，我这边也帮你核对。",
                    "; if you already sent documents, I will check on my side.",
                )
                base = base.rstrip("。") + tail
            return base
        if category == "missing_document":
            t = templates.get("missing_document", {})
            # Reassure-first: when customer says 发过了 first, lead with acknowledgment
            already_sent_lead = any(
                m in lowered for m in ["发过", "发过了", "发了", "又发", "sent", "already sent", "上周发", "上周寄"]
            )
            if already_sent_lead:
                if item_text:
                    base = (t.get("zh_already_sent_with_item") or "收到。办公室会核对已有材料（含 {item_text}），一般不用重复整套发；若还缺项会明确告诉您。").replace("{item_text}", item_text)
                else:
                    base = t.get("zh_already_sent_without_item") or "收到。办公室会核对您已发的材料，一般不用重复整套发；若还缺项会明确告诉您。"
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
            t = templates.get("missing_signature", {})
            return t.get("zh") or "看起来还有签名没完成。把要签名的那一页发我，我先帮你确认是哪一栏。"
        if category == "underwriting_followup":
            t = templates.get("underwriting_followup", {})
            return t.get("zh") or "保险公司这边还要补一些资料。把通知里要的内容发我，我整理后尽快帮你回复。"
        if category == "renewal_reminder":
            t = templates.get("renewal_reminder", {})
            return t.get("zh") or "这是续保提醒，目前先不用处理。到需要确认方案时我再联系你。"
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
            if _is_add_vehicle_request(lowered):
                t = templates.get("add_car", {})
                # Progressive ask: acknowledge what customer said, ask 1–2 next things (not 6)
                merged_slots, _last_cust = _merged_and_last_customer_for_add_car_draft(text)
                fields = _extract_add_car_fields_truth_safe(merged_slots)
                vehicle_ok = (fields.get("year") and fields.get("model")) or fields.get("vin")
                if vehicle_ok and not fields.get("zip"):
                    base = "邮编发我一下，我好往下报价。"
                elif vehicle_ok and fields.get("zip") and fields.get("delivery") and not fields.get("driver"):
                    base = "主要驾驶人发我一下，我好安排报价。"
                elif vehicle_ok and fields.get("zip") and not fields.get("delivery") and not fields.get("driver"):
                    base = "提车日和主要驾驶人发我一下，我好安排报价。"
                elif fields.get("model") and not vehicle_ok:
                    base = "年份和邮编发我，我好继续报价。"
                elif fields.get("year") and not fields.get("model"):
                    base = "车型和邮编发我，我好继续报价。"
                elif not vehicle_ok:
                    base = "可以帮你看这台车报价。年份和车型先发我。"
                else:
                    base = t.get("zh") or "可以帮你看这台车报价。请发：年份、车型、VIN（有的话）、提车日、邮编、主要驾驶人。"
                lead_ps = _get_prospective_send_materials_lead(text, "zh", client_id)
                ack = _get_add_car_acknowledgement(text, fields, "zh", merged_slots)
                if ack:
                    base = ack + base
                if lead_ps:
                    base = lead_ps + base
                # Side question: price sensitivity during add-car — brief office-realistic line, still collect slots.
                base = _maybe_append_add_car_price_caveat(text, base, "zh", client_id)
                # Mixed-intent: add-car + garaging proof confusion — add brief explanation
                if _is_document_confusion_request(lowered) and ("garaging" in lowered or "停放" in lowered):
                    snippet = retrieve_document_explanation(text)
                    if snippet:
                        augment = format_retrieval_augment(snippet, "zh")
                        if augment:
                            return augment + base
                    return "garaging proof（车辆停放地址证明）是证明车平时停哪里的材料。\n\n" + base
                return base
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
                    tail = _stitched_customer_visible_line(
                        client_id,
                        "document_already_sent_tail",
                        "zh",
                        "；如果材料说发过了，我这边也帮你核对。",
                        "; if you already sent documents, I will check on my side.",
                    )
                    base = base.rstrip("。") + tail
                return base
            if _is_remove_vehicle_request(lowered):
                t = templates.get("remove_vehicle", {})
                return t.get("zh") or "好的，可以处理。把卖车日期、车辆信息和是否已经过户发我，我先帮你确认。"
            if _is_add_driver_request(lowered):
                ad_t = templates.get("add_driver", {})
                return ad_t.get("zh") or "好的，可以加司机。把要加的是哪辆车、驾驶人信息和驾照发我，我先帮你确认下一步。"
            if _is_bundling_request(lowered):
                bun_t = templates.get("bundling", {})
                return bun_t.get("zh") or "房屋险和车险一起买一般有折扣。把您现在的车险和房屋险（如果有）情况发我，我先帮你看有没有合适的方案。"
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
            tstrip = (text or "").strip()
            if len(tstrip) <= 20 and _message_claims_completed_material_send(tstrip) and not _is_prospective_send_offer_message(
                tstrip.lower()
            ):
                return "您是说发过了吗？我这边帮你核对。把完整通知或相关材料也发我一下，我好确认。"
            return "这段内容还不够完整。把完整通知或前后内容再发我一下，我帮你确认下一步。"
        if category == "informational":
            t = templates.get("informational", {})
            return t.get("zh") or "这个目前看起来没问题，先不用额外处理。有新内容我再跟你说。"
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
            tail = _stitched_customer_visible_line(
                client_id,
                "document_already_sent_tail",
                "en",
                "；如果材料说发过了，我这边也帮你核对。",
                "; if you already sent documents, I will check on my side.",
            )
            base = base.rstrip(".") + tail
        return base
    if category == "missing_document":
        t = templates.get("missing_document", {})
        # Reassure-first: when customer says already sent first, lead with acknowledgment
        already_sent_lead = any(
            m in lowered for m in ["sent", "already sent", "发过", "发过了", "发了", "又发", "last week"]
        )
        if already_sent_lead:
            if item_text:
                base = (t.get("en_already_sent_with_item") or "Got it. Our office will verify what is already on file (including the {item_text}). You usually do not need to resend everything—we will only ask if something is still missing.").replace("{item_text}", item_text)
            else:
                base = t.get("en_already_sent_without_item") or "Got it. Our office will verify what you already sent. You usually do not need to resend everything—we will only ask if something is still missing."
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
        t = templates.get("missing_signature", {})
        return t.get("en") or "It looks like one signature is still missing. Send me the page they flagged and I will help confirm what still needs to be signed."
    if category == "underwriting_followup":
        t = templates.get("underwriting_followup", {})
        return t.get("en") or "Underwriting still needs more information. Send me the requested details and I will help get this back to them before the deadline."
    if category == "renewal_reminder":
        t = templates.get("renewal_reminder", {})
        return t.get("en") or "This is just a renewal reminder, so nothing needs to be handled right now. I will reach out when it is time to review options."
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
        if _is_add_vehicle_request(lowered):
            t = templates.get("add_car", {})
            # Progressive ask: acknowledge what customer said, ask 1–2 next things (not 6)
            merged_slots, _last_cust = _merged_and_last_customer_for_add_car_draft(text)
            fields = _extract_add_car_fields_truth_safe(merged_slots)
            vehicle_ok = (fields.get("year") and fields.get("model")) or fields.get("vin")
            if vehicle_ok and not fields.get("zip"):
                base = "Send the zip and I will run the quote."
            elif vehicle_ok and fields.get("zip") and fields.get("delivery") and not fields.get("driver"):
                base = "Send me the main driver so I can prepare the quote."
            elif vehicle_ok and fields.get("zip") and not fields.get("delivery") and not fields.get("driver"):
                base = "Send the delivery date and main driver so I can prepare the quote."
            elif fields.get("model") and not vehicle_ok:
                base = "Send the year and zip so I can run the quote."
            elif fields.get("year") and not fields.get("model"):
                base = "Send the make/model and zip so I can run the quote."
            elif not vehicle_ok:
                base = "I can quote the new car—send year and make/model first."
            else:
                base = t.get("en") or "I can quote the new car. Send year, make/model, VIN if you have it, delivery date, zip, and main driver."
            lead_ps = _get_prospective_send_materials_lead(text, "en", client_id)
            ack = _get_add_car_acknowledgement(text, fields, "en", merged_slots)
            if ack:
                base = ack + base
            if lead_ps:
                base = lead_ps + base
            base = _maybe_append_add_car_price_caveat(text, base, "en", client_id)
            # Mixed-intent: add-car + garaging proof confusion — add brief explanation
            if _is_document_confusion_request(lowered) and "garaging" in lowered:
                snippet = retrieve_document_explanation(text)
                if snippet:
                    augment = format_retrieval_augment(snippet, "en")
                    if augment:
                        return augment + base
                return "Garaging proof shows where the car is usually parked.\n\n" + base
            return base
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
                tail = _stitched_customer_visible_line(
                    client_id,
                    "document_already_sent_tail",
                    "en",
                    "；如果材料说发过了，我这边也帮你核对。",
                    "; if you already sent documents, I will check on my side.",
                )
                base = base.rstrip(".") + tail
            return base
        if _is_remove_vehicle_request(lowered):
            t = templates.get("remove_vehicle", {})
            return t.get("en") or "Got it, I can help with that. Send me the vehicle details, sale date, and whether title already transferred and I will confirm the next step."
        if _is_add_driver_request(lowered):
            ad_t = templates.get("add_driver", {})
            return ad_t.get("en") or "Got it, I can help add a driver. Send me which vehicle, the driver's info and license, and I will confirm the next step."
        if _is_bundling_request(lowered):
            bun_t = templates.get("bundling", {})
            return bun_t.get("en") or "Bundling home and auto usually gets a discount. Send me your current auto and home (if any) policy info and I will check what options we have."
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
        _ut = (text or "").strip()
        if len(_ut) <= 20 and _message_claims_completed_material_send(_ut) and not _is_prospective_send_offer_message(
            _ut.lower()
        ):
            return "You said you sent it—I will check on my side. Send me the full notice or the document so I can verify."
        return "This part is still unclear. Send me the full notice or a little more context and I will confirm the next step."
    if category == "informational":
        t = templates.get("informational", {})
        return t.get("en") or "This looks fine for now. No extra action is needed at the moment."
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
            _build_client_reply_draft(text, "customer_question", client_id),
        )

    # missing_document: broker_next_step from config; client_prep dynamic
    if category == "missing_document":
        bns = _bns("missing_document") or "Verify whether customer-resubmitted items were received; request any still-missing items."
        return (
            bns,
            _build_missing_document_client_prep(text),
            _build_client_reply_draft(text, "missing_document", client_id),
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
    draft = _build_client_reply_draft(text, category, client_id)
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
        "联系人工", "转接人工", "联系陈奎", "找陈奎", "联系办公室", "我要找人工", "我想跟人说", "找经纪人", "找人工",
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

    # Add-car: multi-driver quote question hits 驾照 + 需要 before generic missing_document
    if _is_add_car_multi_driver_quote_question(text or ""):
        return "customer_question", "medium", True

    # Add-car continuation: "…quote…还缺什么" is quote-readiness ask, not missing-document / unclear
    raw_for_add = text or ""
    _add_car_still_needed_ask = any(
        m in raw_for_add
        for m in (
            "还缺什么",
            "还缺啥",
            "现在还缺",
            "还要补什么",
            "还缺资料",
            "缺什么资料",
        )
    )
    if _add_car_still_needed_ask and (
        _is_add_vehicle_request(t)
        or (
            _contains_any(t, _get_markers("vehicle_context"))
            and ("quote" in t or "报价" in raw_for_add or "加" in raw_for_add)
        )
    ):
        return "customer_question", "medium", True

    # Add-car quote-prep: "材料/微信已发 + 还缺什么" is readiness ask — not generic missing-doc resend
    if _add_car_still_needed_ask and (
        any(m in raw_for_add for m in ("发过了", "发了", "又发", "刚发", "已经发", "发了一次"))
        or any(m in raw_for_add.lower() for m in ("微信发", "发你微信", "发我微信", "邮箱发", "邮件发"))
    ) and any(
        m in raw_for_add.lower()
        for m in (
            "微信",
            "材料",
            "vin",
            "registration",
            "行驶证",
            "加车",
            "quote",
            "报价",
            "邮箱",
            "邮件",
        )
    ):
        return "customer_question", "medium", True

    # Registration / doc resend receipt check — office verifies inbox (NA-Chinese realistic follow-up)
    rl_doc = (text or "").lower()
    raw_doc = text or ""
    if (
        "registration" in rl_doc
        or "行驶证" in raw_doc
        or ("照片" in raw_doc and ("registration" in rl_doc or "行车" in raw_doc))
    ) and any(x in raw_doc for x in ("又发", "再发", "刚发", "发了一次", "重发", "补发")):
        if any(x in raw_doc for x in ("收到吗", "收到了吗", "看到吗", "有收到", "查一下", "有没有收到")):
            return "missing_document", "medium", True

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
    broker_next_step = _broker_next_step or fallbacks.get(
        "broker_next_step",
        "Review the {category} message; confirm what the client needs and take the next step.",
    ).replace("{category}", category.replace("_", " "))
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


def _add_car_mentions_multiple_vehicles(customer_only: str) -> bool:
    """True when customer text suggests two+ vehicles in one intake (MVP: single primary record)."""
    t = (customer_only or "").strip()
    if not t:
        return False
    if len(re.findall(r"(20[12][0-9])", t)) >= 2 and re.search(
        r"(还有|另一辆|第二辆|两辆|两台|两辆车|同时|and\s+also|plus\s+a)", t, re.I
    ):
        return True
    if re.search(r"(还有一辆|另一辆|第二辆)", t) and len(re.findall(r"(20[12][0-9])", t)) >= 2:
        return True
    # Explicit two-vehicle quote phrasing without relying on two year tokens
    if re.search(r"(两辆车|两台车|两辆|两台).{0,48}(报价|一起|同时|一起报)", t):
        return True
    if re.search(r"(同时|一起).{0,24}(两辆车|两台车|两辆|两台)", t):
        return True
    # Same-garage second vehicle ("同地址还有…") with a second year
    if re.search(r"同地址", t) and len(re.findall(r"(20[12][0-9])", t)) >= 2:
        return True
    return False


def _detect_secondary_intent_hint(merged_text: str, category: str, intent_hint: str) -> str:
    """Detect secondary intent when 2+ goals mixed. Returns ' Also asked: X. ' or ''."""
    last = merged_text.split("[客户]")[-1].strip() if "[客户]" in merged_text else (merged_text or "").strip()
    lowered = last.lower()
    flows = []
    if _is_add_vehicle_request(last):
        flows.append("add_car")
    if _is_premium_review_request(last):
        flows.append("premium_review")
    if _contains_any(lowered, _get_markers("payment")) or _contains_any(lowered, _get_markers("payment_risk")):
        flows.append("payment")
    if _contains_any(lowered, _get_markers("missing_document_object")) and _contains_any(lowered, _get_markers("missing_document_request")):
        flows.append("missing_document")
    if _is_claim_intake_request(last):
        flows.append("claim_intake")
    if _is_remove_vehicle_request(last):
        flows.append("remove_car")
    if _is_english_notice_confusion(lowered) or ("notice" in lowered and ("什么意思" in last or "what does" in lowered)):
        flows.append("notice_confusion")
    if _is_document_confusion_request(lowered) and ("garaging" in lowered or "dec page" in lowered):
        flows.append("document_confusion")
    if len(flows) < 2:
        return ""
    primary = None
    if intent_hint:
        if "Add car" in intent_hint or "New quote" in intent_hint:
            primary = "add_car"
        elif "Remove vehicle" in intent_hint:
            primary = "remove_car"
        elif "Premium review" in intent_hint:
            primary = "premium_review"
        elif "Payment" in intent_hint or "Cancellation" in intent_hint:
            primary = "payment"
        elif "Missing document" in intent_hint:
            primary = "missing_document"
        elif "Claim" in intent_hint:
            primary = "claim_intake"
        elif "notice" in intent_hint.lower() or "DMV" in intent_hint:
            primary = "notice_confusion"
    if primary is None:
        if category in ("payment_lapse_expiration", "cancellation_warning"):
            primary = "payment"
        elif category == "missing_document":
            primary = "missing_document"
        elif _is_claim_intake_request(last):
            primary = "claim_intake"
        elif _is_add_vehicle_request(last):
            primary = "add_car"
        elif _is_premium_review_request(last):
            primary = "premium_review"
        elif _is_remove_vehicle_request(last):
            primary = "remove_car"
    secondaries = [f for f in flows if f != primary]
    if not secondaries:
        return ""
    s = secondaries[0]
    labels = {"add_car": "add car", "premium_review": "premium review", "payment": "payment/notice", "missing_document": "missing document", "claim_intake": "claim", "remove_car": "remove vehicle", "notice_confusion": "notice meaning", "document_confusion": "garaging/dec page meaning"}
    label = labels.get(s, s.replace("_", " "))
    return f" Also asked: {label}. "


def _build_conversation_summary(merged_text: str, base_result: dict[str, Any], customer_count: int) -> tuple[str, str]:
    """Build a short broker-facing summary of the conversation. Returns (summary, secondary_issue_note)."""
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
        fields = _extract_add_car_fields_truth_safe(merged_text)
        vehicle_concrete = _extract_primary_add_car_vehicle_concrete(merged_text)
        parts: list[str] = []
        if vehicle_concrete:
            parts.append(vehicle_concrete)
        else:
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
        _pay_segs = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
        _pay_last_c = (_pay_segs[-1] if _pay_segs else (merged_text or "")).strip()
        if any(m in lowered for m in ["付了", "paid", "已经付", "already paid", "换了新卡", "updated card"]):
            collected_hint = " Collected: client says already paid. "
        elif _message_claims_completed_material_send(_pay_last_c) and not _is_prospective_send_offer_message(
            _pay_last_c.lower()
        ):
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
    cust_segs_for_sent = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    _sent_bodies = [x.strip() for x in cust_segs_for_sent] if cust_segs_for_sent else [customer_only.strip()]
    if any(_message_claims_completed_material_send(b) for b in _sent_bodies if b):
        context_hint += " Client says already sent. "

    # One-message multi-vehicle MVP: record stays single-primary; avoid implying full CRM coverage.
    if _is_add_vehicle_request(lowered) and _add_car_mentions_multiple_vehicles(customer_only):
        context_hint += (
            " MVP scope: one primary vehicle on this record; another vehicle was also mentioned—"
            "confirm which unit to quote first. "
        )

    # Mixed-intent: secondary issue note (MIXED_INTENT_SECONDARY_CASE_SPRINT)
    secondary_hint = _detect_secondary_intent_hint(merged_text, category, intent_hint)
    if secondary_hint:
        context_hint += secondary_hint

    msg_count = f"{customer_count} customer message(s)."
    latest_snip = (merged_text.split("[客户]")[-1].strip() if "[客户]" in merged_text else merged_text)[:80]
    if latest_snip:
        summary = f"{intent_hint}{collected_hint}{still_needed_hint}{context_hint}{msg_count} Latest: {latest_snip}..."
    else:
        summary = f"{intent_hint}{collected_hint}{still_needed_hint}{context_hint}{msg_count}"
    return summary, (secondary_hint.strip() if secondary_hint else "")


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


def _customer_bodies_from_labeled_thread(merged_text: str) -> list[str]:
    """Split [客户] bubbles; keeps text that starts with '[' (e.g. '[image intake]')."""
    raw = merged_text or ""
    if "[客户]" not in raw:
        return [raw.strip()] if raw.strip() else []
    out: list[str] = []
    for chunk in re.split(r"\[客户\]\s*", raw, flags=re.IGNORECASE)[1:]:
        body = chunk
        for stop in ("[系统]", "[客户]", "[OCR]", "[ocr]"):
            j = body.find(stop)
            if j >= 0:
                body = body[:j]
        b = body.strip()
        if b:
            out.append(b)
    return out


def _last_labeled_customer_content(merged_text: str) -> str:
    """Last customer bubble text (bracket-safe)."""
    bodies = _customer_bodies_from_labeled_thread(merged_text)
    return bodies[-1] if bodies else (merged_text or "").strip()


# --- Add-car field signals (ADD_CAR_HIGH_ROI_EXTRACTION_GUARD_FIX) ---
# CA garage ZIP focus: 9xxxx; (?<![0-9])/(?![0-9]) avoids \b failing beside Chinese (e.g. 邮编95131).
_CA_ZIP_STRICT_RE = re.compile(r"(?<![0-9])(9[0-9]{4})(?![0-9])", re.IGNORECASE)

_ADD_CAR_DRIVER_MARKERS: tuple[str, ...] = (
    "driver",
    "驾驶人",
    "主驾",
    "主驾驶人",
    "谁开",
    "main driver",
    "primary driver",
    "老婆开",
    "老公开",
    "我开",
    "我自己开",
    "本人开",
    "主要我本人",
    "主要本人",
    "我本人开",
    "孩子开",
    "儿子开",
    "女儿开",
    "我老婆开",
    "我老公开",
    "我一个人开",
    "spouse",
    "teen",
    "only me",
    "就我",
    "我一个人",
    "主要驾驶人是我",
    "都可能开",
    "我跟老婆",
    "我跟我老婆",
)

# Explicit primary-driver identity (narrow regex — not "my wife drives mostly" style ambiguity).
_EXPLICIT_NAMED_DRIVER_RE = re.compile(
    r"(?i)\b(?:her|his|their)\s+name\s+is\s+([A-Za-z][A-Za-z'`\u2019-]*(?:\s+[A-Za-z][A-Za-z'`\u2019-]*)+)"
)
_EXPLICIT_ZH_NAMED_DRIVER_RE = re.compile(
    r"(?:她叫|他叫|姓名\s*[:：]\s*|名字\s*[:：]\s*)([^\s，,。]{2,24})"
)
_EXPLICIT_ME_PRIMARY_DRIVER_RE = re.compile(
    r"(?i)\b(?:i\s+am|i'?m)\s+the\s+primary\s+driver\b|"
    r"\b(?:primary|main)\s+driver\s+is\s+me\b|"
    r"\bthe\s+primary\s+driver\s+is\s+me\b"
)


def _text_has_ca_zip_signal(t: str) -> bool:
    if not t:
        return False
    return bool(_CA_ZIP_STRICT_RE.search(t.lower()))


def _extract_ca_zip_from_message(msg: str) -> str | None:
    if not msg:
        return None
    m = _CA_ZIP_STRICT_RE.search(msg.lower())
    return m.group(1) if m else None


def _text_has_add_car_driver_signal(t: str) -> bool:
    """High-frequency primary/additional driver phrasing (CN/EN); substring match on lowered text."""
    raw = (t or "").strip()
    if not raw:
        return False
    tl = raw.lower()
    if any(m in tl for m in _ADD_CAR_DRIVER_MARKERS):
        return True
    if _EXPLICIT_NAMED_DRIVER_RE.search(raw):
        return True
    if _EXPLICIT_ZH_NAMED_DRIVER_RE.search(raw):
        return True
    if _EXPLICIT_ME_PRIMARY_DRIVER_RE.search(raw):
        return True
    return False


def _is_prospective_send_offer_message(msg: str) -> bool:
    """
    Question or suggestion about sending materials — NOT a completed 'already sent' statement.
    Intent guard: must run before loose '发你' / screenshot / sent-keyword matching.
    """
    raw = (msg or "").strip()
    if not raw:
        return False
    s = raw.lower()
    # Completed-send statements are never "prospective offer"
    if any(m in s for m in ("发你了", "发您了", "发过了", "又发了", "发过", "已经发", "已经给你发", "already sent")):
        return False
    if re.search(r"\b(i'?ve|i have)\s+sent\b", s) or re.search(r"\b(i\s+sent|sent\s+it|sent\s+them)\b", s):
        return False
    if re.search(r"要不要[^。！？\n]{0,28}发", s):
        return True
    # "要不要先给你看一下" has 给你 but not always 发
    if re.search(r"要不要先", s) and ("发" in s or "给你" in raw):
        return True
    if re.search(r"要不\s*我[^。！？\n]{0,22}发", s):
        return True
    # Permission / offer: can I / could I send first (CN)
    if re.search(r"(我可以|可不可以|能不能|可以吗).{0,22}先发", s):
        return True
    if re.search(r"(我可以|可不可以|能不能).{0,26}发[你我您]", s):
        return True
    if re.search(r"(我先)?发给你看看行吗?|先发给你看看行吗|发给你.{0,8}行吗", s):
        return True
    if re.search(r"先发[你我您].{0,18}(行吗|可以吗|好不好|吗|嘛|么)[?？]?\s*$", s):
        return True
    if re.search(r"先发[你我您].{0,20}(行吗|可以吗|好不好)", s):
        return True
    # "先给你看(一下)" offers
    if re.search(r"先给你.{0,8}看", s) and (
        re.search(r"[吗嘛呢吧?？]\s*$", raw.strip()) or "行吗" in s or "可不可以" in s
    ):
        return True
    if "行不行" in s and "发" in s and not any(m in s for m in ("发过了", "已经发", "发了", "发你了", "发您了")):
        return True
    # Question mark + send vocabulary (screenshot / VIN / 材料 / 行驶证) without past-tense send
    if (
        re.search(r"[?？]|吗\s*$|嘛\s*$|行吗\s*$|可以吗\s*$", raw)
        and ("发" in s or "给" in raw)
        and any(k in s for k in ("截图", "screenshot", "vin", "材料", "行驶证", "registration", "微信"))
        and not re.search(r"(发你了|发过了|已经发|又发了|发了|sent it|already sent)", s)
    ):
        return True
    # English permission-to-send
    if re.search(r"\b(can|could|should|may)\s+i\s+send\b", s):
        return True
    if re.search(r"\b(ok|okay)\s+(if|to)\s+i\s+send\b", s):
        return True
    return False


def _message_claims_completed_material_send(msg: str) -> bool:
    """
    True when the customer states materials were already sent — not asking permission to send.
    Uses high-precision phrases; avoids substring traps like 先发你 / bare 截图.
    """
    raw = (msg or "").strip()
    if not raw:
        return False
    s = raw.lower()
    if _is_prospective_send_offer_message(s):
        return False
    if re.search(r"\b(can|could|should|may)\s+i\s+send\b", s):
        return False
    if any(
        m in raw
        for m in (
            "发过了",
            "又发了",
            "又发了一次",
            "发你了",
            "发您了",
            "发过",
            "已经发",
            "已经给你发",
            "早就发",
            "刚才发",
            "刚发",
            "上午发",
            "昨天发",
            "寄了",
            "发你微信了",
            "发我微信了",
            "微信发你了",
            "微信发您了",
            "材料发你了",
            "截图发你了",
            "截图发过去了",
            "我已经把",
            "我早就发",
        )
    ):
        return True
    if "又发" in raw and "要不要" not in s and not re.search(r"又发.{0,8}[吗?？]", raw):
        return True
    if "发了" in raw and "发现" not in raw:
        if re.search(r"发了吗|发了没|发了么|发了没有", raw):
            return False
        return True
    if re.search(r"\b(i'?ve|i have)\s+sent\b", s) or re.search(
        r"\b(i\s+sent|already\s+sent|sent\s+it|sent\s+them|sent\s+via|sent\s+on\s+wechat)\b", s
    ):
        return True
    if re.search(r"\bsent\b", s) and len(raw) <= 36:
        if re.search(r"\b(can|could|should|may|want to|going to)\b", s):
            return False
        return True
    if ("截图" in raw or "screenshot" in s) and any(
        x in s for x in ("发了", "发你了", "发过了", "发过", "已经", "sent", "微信了", "给您了", "给你了")
    ):
        return True
    if re.search(r"发[你我您](微信)?[了过]", raw):
        return True
    if re.search(r"[材料证件单证].{0,8}发[你我您]了", raw):
        return True
    return False


def _get_prospective_send_materials_lead(
    last_customer_msg: str, language: str, client_id: str | None = None
) -> str:
    """
    Short office-style answer when the customer asks whether to send materials (WeChat/screenshot/etc.).
    Empty string when not a prospective-send question. Caller prepends before normal add-car ask/handoff.
    Optional client stitched overrides: handoff_phrases.json -> stitched.prospective_send
    """
    raw = (last_customer_msg or "").strip()
    if not raw:
        return ""
    msg = raw
    if "[客户]" in raw:
        segs = re.findall(r"\[客户\]\s*([^[]+)", raw)
        if segs:
            msg = (segs[-1] or "").strip()
    if not _is_prospective_send_offer_message(msg.lower()):
        return ""
    ml = msg.lower()
    stitched = _get_stitched_phrases(client_id)
    ps_raw = stitched.get("prospective_send")
    ps: dict[str, str] = ps_raw if isinstance(ps_raw, dict) else {}

    def _pick(key: str, default: str) -> str:
        v = (ps.get(key) or "").strip()
        return v if v else default

    if language == "zh":
        if "微信" in msg:
            return _pick("zh_wechat", "可以，微信发我就行。")
        if "截图" in msg:
            return _pick("zh_screenshot", "可以，截图先发我，办公室一起核。")
        if any(m in msg for m in ("行驶证", "照片", "材料")) or "dec" in ml or "declaration" in ml:
            return _pick("zh_bundle", "可以，先发我，办公室一起核。")
        return _pick("zh_bundle", "可以，先发我，办公室一起核。")
    if "wechat" in ml or "微信" in msg:
        return _pick("en_wechat", "Yes—WeChat works. ")
    if "screenshot" in ml or "截图" in msg:
        return _pick("en_screenshot", "Yes—send the screenshot and I will review it with your file. ")
    return _pick("en_bundle", "Yes—send it over and I will bundle it for the office. ")


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
    correction_markers = (
        "不是",
        "不是这个",
        "不是 payment",
        "不是续保",
        "是另一辆",
        "另一辆",
        "不是这辆",
        "说错了",
        "actually",
        "i meant",
        "其实已经",
        "更正",
        "更正一下",
        "写错了",
        "之前写错",
        "改一下",
        "vin 写错",
        "电话不是",
        "手机不是",
        "wrong number",
    )
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
        "还缺什么", "还缺啥", "还要补什么", "补什么吗", "你先看看", "先看下", "用不用再发", "还要不要发", "anything else", "what else",
    )
    if any(m in msg for m in clarification_markers):
        return "clarification_question"

    # Offer / question to send — not a claim that materials were already sent (guards e.g. 要不要发你).
    if _is_prospective_send_offer_message(msg):
        return "new_info"

    # Already sent: completed-send only (WIRC: bare 截图 / 先发你 substring is NOT enough).
    if _message_claims_completed_material_send((last_customer_msg or "").strip()):
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


def _resolve_add_car_handoff_phrase_key(
    last_customer_raw: str,
    follow_up_type: str,
    handoff_phrases: dict[str, dict[str, str]],
    customer_turn_index: int,
    merged_text: str,
    reply_truth_context: dict[str, Any] | None,
) -> tuple[str, ResolvedAddCarIntent]:
    """
    Pick handoff_phrases.json key for add-car using bounded Intent Layer (add_car_intent.py).
    Merges still_needed_fields from merged_text with persisted case gaps (append / case_id) for intent ceiling checks.
    """
    truth_for_intent: dict[str, Any] = dict(reply_truth_context or {})
    _, still_gap, _, _ = _add_car_structured_fields(merged_text)
    prior_still = list((reply_truth_context or {}).get("still_needed_fields") or [])
    merged_still: list[str] = []
    _seen_still: set[str] = set()
    for x in list(still_gap or []) + prior_still:
        xs = str(x).strip()
        if not xs:
            continue
        key = xs.lower()
        if key in _seen_still:
            continue
        _seen_still.add(key)
        merged_still.append(xs)
    if merged_still:
        truth_for_intent["still_needed_fields"] = merged_still
    resolved = resolve_add_car_turn_intent(
        last_customer_raw,
        follow_up_type,
        customer_turn_index,
        truth_for_intent,
    )
    resolved = nudge_append_generic_to_supplement_intent(resolved, reply_truth_context)
    base = resolved.handoff_base_key
    if handoff_phrases.get(base):
        return base, resolved
    return "add_car", resolved


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
        has_zip = _text_has_ca_zip_signal(last_lower)
        has_delivery = any(
            m in last_lower
            for m in [
                "下周",
                "提车",
                "拿车",
                "next week",
                "picking up",
                "pick up",
                "pickup",
                "delivery",
                "明天",
                "friday",
                "周五",
            ]
        )
        has_model = any(
            m in last_lower
            for m in [
                "bmw", "x5", "tesla", "honda", "toyota", "accord", "camry", "宝马", "本田", "丰田", "车型",
            ]
        )
        has_driver = _text_has_add_car_driver_signal(last_lower)
        if has_year or has_zip or has_delivery or has_model or has_driver:
            return True

    # Minimal completed-send style (short) — not bare 发你 / 先发你 questions
    if len(last_customer) <= 18 and _message_claims_completed_material_send(last_customer):
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


# --- Case boundary / new-issue separation (append / office_followup flow) ---
_SYSTEM_ADD_CAR_HANDOFF_MARKERS: tuple[str, ...] = (
    "办公室会尽快出价",
    "报价资料",
    "安排报价",
    "帮您报价",
    "尽快出价",
    "Run quote",
    "prepare the quote",
    "quote details received",
)

_TOPIC_PIVOT_STRONG: tuple[str, ...] = (
    "另外一个",
    "另一個",
    "另一个问题",
    "另一个事情",
    "另一个保险",
    "另外一个保险",
    "别的保险",
    "不是这个车",
    "不是这车",
    "不是这个加车",
    "再问",
    "还想问",
    "顺便问",
    "加车先这样",
    "那这个先这样",
    "我先问个",
    "我再问",
    "我还有个账单",
    "账单的问题",
    "理赔的事",
    "还有一个问题",
    "另外一件事",
    "另外个事",
)

_BILLING_PIVOT_MARKERS: tuple[str, ...] = (
    "账单",
    "扣款",
    "缴费",
    "付款问题",
    "自动扣款",
    "billing",
    "autopay",
    "invoice",
    "past due",
    "overdue",
)

_OFFICE_HOURS_MARKERS: tuple[str, ...] = (
    "office",
    "周末",
    "周六",
    "周日",
    "营业时间",
    "几点下班",
    "放假",
    "开门吗",
    "open on",
    "office hour",
)

_SAME_THREAD_EXTRA_VEHICLE_MARKERS: tuple[str, ...] = (
    "另一台",
    "还有一台",
    "第二辆",
    "另一辆",
    "再加",
    "还有一辆",
    "两台车",
    "第二台",
)


def _is_add_car_price_reshop_or_requote_followup(msg: str) -> bool:
    """
    Last bubble looks like quote price pushback or re-shop on an open add-car thread.
    Keeps append boundary on the same service record (premium_review markers alone are ambiguous).
    """
    raw = (msg or "").strip()
    if not raw:
        return False
    ml = raw.lower()
    if any(x in raw for x in ("续保到期", "renewal notice", "renewal premium")) and not any(
        x in ml for x in ("quote", "报价", "加车", "再报", "company", "换公司", "换一家", "coverage")
    ):
        return False
    # Same-car same-day re-confirm / re-quote (deictic vehicle + quote ask — not a separate renewal case).
    if ("确认" in raw or "再看看" in raw or "给我看看" in raw) and (
        "报价" in raw or "保费" in raw or "coverage" in ml
    ) and any(x in raw for x in ("那辆", "那台", "这辆", "这台", "刚才", "那部")):
        return True
    if "那台车再报" in raw or "那辆车再报" in raw or "再报一次" in raw:
        return True
    # High-frequency NA-Chinese price pushback often omits 报价/保费 but still targets the same vehicle.
    if any(x in raw for x in ("便宜", "便宜点", "便宜一点", "能不能便宜")):
        if any(
            x in raw
            for x in ("那辆", "那台", "这辆", "这台", "刚才", "那部", "那台车", "那辆车", "这台车")
        ) or any(x in raw for x in ("保费", "报价", "全险", "半险")):
            return True
    return any(
        x in raw
        for x in (
            "太贵",
            "太高",
            "换公司",
            "换一家",
            "换家",
            "别的公司",
            "其他公司",
            "再报",
            "再报价",
            "报一下价",
            "company",
            "coverage",
            "保额",
            "调低",
            "调高",
            "上次报",
            "报的价",
        )
    ) or any(x in ml for x in ("too expensive", "another carrier", "re-shop", "reshop", "re-quote", "requote"))


def _is_renewal_policy_coordination_followup(msg: str) -> bool:
    """
    Customer asks to coordinate a *different* renewal policy with the current add-car thread.
    Hard-split is unsafe; prefer borderline so the office can confirm whether to track together.
    """
    raw = (msg or "").strip()
    if not raw:
        return False
    if not ("续保" in raw or "renewal" in raw.lower()):
        return False
    if not any(x in raw for x in ("另一张", "另一条", "别的保单", "另外一张", "另一份")):
        return False
    return any(x in raw for x in ("一起", "同时", "办公室", "能不能", "可以不可以", "一并"))


def _source_customer_concat(source_text: str) -> str:
    """All [客户] bubbles joined; if none, treat whole thread as customer (persisted cases often omit tags)."""
    parts = re.findall(r"\[客户\]\s*([^[]+)", source_text or "", flags=re.IGNORECASE)
    if parts:
        return " ".join(p.strip() for p in parts if p.strip())
    raw = (source_text or "").strip()
    if raw and "[客户]" not in raw and "[系统]" not in raw:
        return raw
    return ""


def _source_system_concat(source_text: str) -> str:
    parts = re.findall(r"\[系统\]\s*([^[]+)", source_text or "", flags=re.IGNORECASE)
    return " ".join(p.strip() for p in parts if p.strip())


def _prior_thread_signals_add_car(source_text: str) -> bool:
    cust = _source_customer_concat(source_text)
    sys_t = _source_system_concat(source_text)
    cl = cust.lower()
    if _is_add_vehicle_request(cl):
        return True
    return any(m in sys_t for m in _SYSTEM_ADD_CAR_HANDOFF_MARKERS)


# Add-Car lane beyond literal _is_add_vehicle_request: CASE_CONTRACT_V1 envelope must stay
# when an office-visible / in-flight Add-Car record exists or the labeled thread already signals add-car.
_ADD_CAR_LANE_STRUCTURAL_FIELD_IDS: frozenset[str] = frozenset(
    {
        "year",
        "make_model",
        "zip",
        "delivery_date",
        "primary_driver",
        "vin",
    }
)
_ADD_CAR_LANE_AUX_FIELD_IDS: frozenset[str] = frozenset(
    {
        "materials_send_question",
        "materials_still_pending",
        "customer_says_materials_sent",
        "customer_says_sent_materials",
        "insurance_status_add_to_existing",
        "insurance_status_new_customer",
        "additional_drivers_yes",
        "additional_drivers_no",
    }
)


def _field_list_implies_add_car_lane(field_list: object) -> bool:
    if not isinstance(field_list, list) or not field_list:
        return False
    for x in field_list:
        s = str(x).strip().lower()
        if s in _ADD_CAR_LANE_STRUCTURAL_FIELD_IDS or s in _ADD_CAR_LANE_AUX_FIELD_IDS:
            return True
    return False


def _reply_truth_context_implies_add_car_lane(ctx: dict[str, Any] | None) -> bool:
    if not ctx:
        return False
    pq = str(ctx.get("persisted_quote_ready_status") or "").strip().lower()
    if pq in ("need_more", "almost_ready", "quote_ready"):
        return True
    if _field_list_implies_add_car_lane(ctx.get("persisted_collected_fields")):
        return True
    if _field_list_implies_add_car_lane(ctx.get("still_needed_fields")):
        return True
    return False


def _last_customer_turn_blocks_add_car_context_carryover(last_customer_raw: str) -> bool:
    """Strong same-turn pivot away from Add-Car; do not force lane from persisted context."""
    t = (last_customer_raw or "").strip()
    if not t:
        return False
    tl = t.lower()
    if _is_remove_vehicle_request(tl):
        return True
    if _is_claim_intake_request(t):
        return True
    return False


def _is_image_intake_placeholder(msg: str) -> bool:
    """True when the customer line is the synthetic image-upload placeholder (not user prose)."""
    t = (msg or "").strip().lower()
    return t in ("[image intake]", "image intake")


def _v6_weak_inline_image_intake(
    last_customer_raw: str,
    v6: dict[str, Any] | None,
) -> bool:
    """
    IMAGE_FIRST: inline image with no structured field values and empty/weak OCR.
    Used to avoid confidently routing add_car without VIN, explicit intent, or strong OCR.
    """
    raw = (last_customer_raw or "").strip().lower()
    if raw not in ("[image intake]", "image intake"):
        return False
    if not v6 or not isinstance(v6, dict):
        return False
    hist = v6.get("attachment_history") or []
    if not isinstance(hist, list):
        return False
    if not any(
        isinstance(h, dict) and str(h.get("attachment_id") or "").strip() == "inline_image" for h in hist
    ):
        return False
    sf = v6.get("structured_fields")
    if isinstance(sf, dict) and any(
        isinstance(v, dict) and str(v.get("value") or "").strip() for v in sf.values()
    ):
        return False
    eng = str(v6.get("last_engine") or "").lower()
    raw_txt = str(v6.get("last_raw_text") or "").strip()
    if eng in ("none", "stub_forced", "empty"):
        return True
    if len(raw_txt) < 12:
        return True
    return False


def _weak_image_service_clarify_reply(language: str) -> str:
    """Single-turn clarification when an image is present but OCR is too weak to infer service lane."""
    is_zh = (language or "").strip().lower() == "zh"
    if is_zh:
        return "图片信息读不清楚。请重拍清晰照片，或简单说一下需要哪类帮助（例如加车报价、理赔、账单）。"
    return (
        "The image isn't readable. Retake a clearer photo, or briefly say what you need "
        "(e.g. adding a vehicle, a claim, or billing)."
    )


def _v6_structured_has_vin(v6: dict[str, Any] | None) -> bool:
    if not v6 or not isinstance(v6, dict):
        return False
    sf = v6.get("structured_fields")
    if not isinstance(sf, dict):
        return False
    vin_e = sf.get("vin")
    return isinstance(vin_e, dict) and bool(str(vin_e.get("value") or "").strip())


def _effective_add_car_lane_active(
    *,
    lowered_merged: str,
    merged_text: str,
    reply_truth_context: dict[str, Any] | None,
    last_customer_raw: str,
    v6_ocr_signals: dict[str, Any] | None = None,
) -> bool:
    if _is_add_vehicle_request(lowered_merged):
        return True
    if _last_customer_turn_blocks_add_car_context_carryover(last_customer_raw):
        return False
    if _reply_truth_context_implies_add_car_lane(reply_truth_context):
        return True
    if _prior_thread_signals_add_car(merged_text):
        return True
    return False


def _infer_prior_case_domain(source_text: str) -> str:
    """Coarse domain for boundary checks."""
    cust = _source_customer_concat(source_text)
    sys_t = _source_system_concat(source_text)
    cl = cust.lower()
    if _prior_thread_signals_add_car(source_text):
        return "add_car"
    if _is_claim_intake_request(cust):
        return "claim"
    if _is_remove_vehicle_request(cl):
        return "remove_car"
    if _is_premium_review_request(cl):
        return "premium"
    if _contains_any(cl, _get_markers("payment")) or _contains_any(cl, _get_markers("payment_risk")):
        return "payment"
    if _contains_any(cl, _get_markers("strong_cancellation")) or _contains_any(cl, _get_markers("weak_cancellation")):
        return "payment"
    md_obj = _contains_any(cl, _get_markers("missing_document_object"))
    md_req = _contains_any(cl, _get_markers("missing_document_request"))
    if md_obj and md_req:
        return "missing_doc"
    return "generic"


def _last_message_issue_domains(last_msg: str) -> set[str]:
    out: set[str] = set()
    raw = (last_msg or "").strip()
    if not raw:
        return out
    ml = raw.lower()
    if _is_claim_intake_request(raw):
        out.add("claim")
    if _is_remove_vehicle_request(ml):
        out.add("remove_car")
    if _is_add_vehicle_request(ml):
        out.add("add_car")
    if _is_premium_review_request(raw) or _is_premium_review_request(ml):
        out.add("premium")
    if any(m in raw for m in _BILLING_PIVOT_MARKERS) or any(
        m in ml for m in ("billing", "autopay", "invoice", "past due", "overdue")
    ):
        out.add("billing")
    if any(m in raw for m in _OFFICE_HOURS_MARKERS) or "office hour" in ml or "open saturday" in ml:
        out.add("office")
    return out


def _has_topic_pivot_phrase(last_msg: str) -> bool:
    t = (last_msg or "").strip()
    return any(p in t for p in _TOPIC_PIVOT_STRONG)


def _correction_is_cross_topic_pivot_not_vehicle_fix(msg: str) -> bool:
    """'不是理赔，是账单' / '另外一个保险问题' — topic pivot; not a vehicle-field correction."""
    t = (msg or "").strip()
    return any(
        x in t
        for x in (
            "另外一个保险",
            "另一个保险",
            "另外一个事情",
            "另外一个问题",
            "另一个事情",
            "另一个问题",
            "不是理赔",
            "不是这个车",
            "不是这车",
        )
    )


def _cross_issue_domains_for_prior(prior: str) -> set[str]:
    if prior == "add_car":
        return {"claim", "billing", "remove_car", "premium"}
    if prior == "claim":
        return {"add_car", "billing", "remove_car", "premium", "payment", "missing_doc"}
    if prior == "remove_car":
        return {"add_car", "claim", "billing", "premium"}
    if prior == "premium":
        return {"add_car", "claim", "billing", "remove_car"}
    if prior == "payment":
        return {"add_car", "claim", "remove_car", "premium", "missing_doc"}
    if prior == "missing_doc":
        return {"add_car", "claim", "billing", "remove_car", "premium"}
    return {"add_car", "claim", "billing", "remove_car", "payment", "premium", "missing_doc"}


def _classify_append_case_boundary(source_text: str, last_msg: str) -> str:
    """
    Returns:
      '' = continue current case (no boundary override)
      'new_issue' = clear pivot to a different operational issue
      'borderline' = pivot unclear; broker should confirm
    """
    prior = _infer_prior_case_domain(source_text)
    domains_quick = _last_message_issue_domains(last_msg)
    cross_early = _cross_issue_domains_for_prior(prior)
    if domains_quick & cross_early:
        # Open add-car quote: last bubble may hit BOTH premium_review and add_vehicle markers
        # ("太贵…那台车再报价") — still the same add-car matter; do not hard-split.
        if prior == "add_car" and _is_add_car_price_reshop_or_requote_followup(last_msg) and (
            domains_quick <= {"premium"} or ({"premium", "add_car"} <= domains_quick)
        ):
            pass
        elif (
            prior == "add_car"
            and "premium" in domains_quick
            and _is_renewal_policy_coordination_followup(last_msg)
            and not _is_add_car_price_reshop_or_requote_followup(last_msg)
        ):
            # Renewal-of-other-policy + this add-car thread: domains may be {premium} only or {premium, add_car}.
            return "borderline"
        else:
            return "new_issue"

    fu = _derive_follow_up_type(last_msg)
    if fu == "correction" and not _correction_is_cross_topic_pivot_not_vehicle_fix(last_msg):
        return ""
    if fu in ("already_sent", "clarification_question"):
        return ""
    last_lower = (last_msg or "").strip().lower()
    # Add-car quote thread: coverage / quote-side questions stay same-case even if "顺便问" appears
    if prior == "add_car" and any(
        m in last_lower
        for m in (
            "coverage 可以调",
            "coverage 能调",
            "coverage 能改",
            "顺便 coverage",
            "保额",
            "collision",
            "deductible",
            "全险",
            "半险",
        )
    ):
        return ""
    domains = domains_quick
    pivot = _has_topic_pivot_phrase(last_msg)

    # Same add-car thread: factual slot fill or extra vehicle on same quote
    if prior == "add_car":
        if not domains:
            if len((last_msg or "").strip()) <= 96 and (
                re.search(r"20[12][0-9]", last_msg or "")
                or _text_has_ca_zip_signal(last_lower)
                or _text_has_add_car_driver_signal(last_lower)
            ):
                return ""
        if domains <= {"add_car"} and not pivot:
            return ""
        if domains <= {"add_car"} and pivot and any(m in (last_msg or "") for m in _SAME_THREAD_EXTRA_VEHICLE_MARKERS):
            # Do not silently absorb an extra-vehicle pivot into the same case (vehicle routing + broker confirm).
            return "borderline"

    cross_new: set[str]
    if prior == "add_car":
        cross_new = {"claim", "billing", "remove_car", "premium"}
    elif prior == "claim":
        cross_new = {"add_car", "billing", "remove_car", "premium", "payment", "missing_doc"}
    elif prior == "remove_car":
        cross_new = {"add_car", "claim", "billing", "premium"}
    elif prior == "premium":
        cross_new = {"add_car", "claim", "billing", "remove_car"}
    elif prior == "payment":
        cross_new = {"add_car", "claim", "remove_car", "premium", "missing_doc"}
    elif prior == "missing_doc":
        cross_new = {"add_car", "claim", "billing", "remove_car", "premium"}
    else:
        cross_new = {"add_car", "claim", "billing", "remove_car", "payment", "premium", "missing_doc"}

    hit = domains & cross_new
    if prior == "add_car" and hit:
        if hit <= {"premium"} and _is_add_car_price_reshop_or_requote_followup(last_msg):
            return ""
        return "new_issue"
    if prior != "generic" and prior != "add_car" and hit:
        return "new_issue"

    if "office" in domains and prior == "add_car":
        return "borderline"

    if pivot and not domains:
        return "borderline"
    if pivot and domains <= {"add_car"} and prior == "add_car":
        return "borderline"

    if prior == "generic" and hit and pivot:
        return "borderline"

    return ""


def _customer_text_for_add_car_extraction(merged_text: str) -> str:
    """Customer-only body text (same convention as _extract_add_car_fields)."""
    bodies = _customer_bodies_from_labeled_thread(merged_text)
    base = " ".join(bodies).strip() if bodies else (merged_text or "").strip()
    ocr_m = re.search(r"\[OCR\]\s*([\s\S]*)$", merged_text or "", flags=re.IGNORECASE)
    if ocr_m:
        ocr_part = ocr_m.group(1).strip()
        if ocr_part:
            base = f"{base} {ocr_part}".strip()
    return base


def _extract_add_car_fields_truth_safe(merged_text: str) -> dict[str, bool]:
    """Rule extract + strict Truth guardrails (Add-Car slots only)."""
    raw = _customer_text_for_add_car_extraction(merged_text)
    fields = _extract_add_car_fields(merged_text)
    return apply_strict_truth_guardrails_to_add_car_fields(fields, raw, merged_labeled_text=merged_text)


def _extract_vehicle_identity_for_key_scoped(
    scope: str, full_customer_lower: str
) -> dict[str, str | None]:
    """
    Identity for vehicle_key from one customer bubble (e.g. correction turn).
    Prefer last 20xx in the bubble; zip from bubble first, else full thread.
    """
    tl = (scope or "").lower()
    if not tl.strip():
        return {"vin": None, "year": None, "model": None, "zip": None}
    vin_all = list(_VIN_17_RE.finditer(tl))
    if vin_all:
        if len(vin_all) >= 2 and re.search(r"(?i)\bvin\s+is\s+[a-z0-9]{17}.+\bnot\b", tl):
            return {"vin": vin_all[0].group(1).upper(), "year": None, "model": None, "zip": None}
        return {"vin": vin_all[-1].group(1).upper(), "year": None, "model": None, "zip": None}
    year = ""
    year_m = None
    for m in re.finditer(r"(?<![0-9])(20[12][0-9])(?:\s*款)?", tl):
        year_m = m
    if year_m:
        year = year_m.group(1)
        sub = tl[year_m.end() :]
    else:
        # No year in correction bubble — inherit latest year from full customer text
        for m in re.finditer(r"(?<![0-9])(20[12][0-9])(?:\s*款)?", full_customer_lower):
            year_m = m
        if year_m:
            year = year_m.group(1)
            sub = tl
        else:
            z_only = _CA_ZIP_STRICT_RE.search(tl) or _CA_ZIP_STRICT_RE.search(full_customer_lower)
            return {
                "vin": None,
                "year": None,
                "model": None,
                "zip": z_only.group(1) if z_only else None,
            }
    seg = re.split(r"还有|另一辆|第二辆|;", sub, maxsplit=1)[0]
    zip_code = None
    z_m = _CA_ZIP_STRICT_RE.search(seg)
    if z_m:
        zip_code = z_m.group(1)
        mid = seg[: z_m.start()].strip()
    else:
        z_tl = _CA_ZIP_STRICT_RE.search(tl)
        if z_tl:
            zip_code = z_tl.group(1)
            mid = seg[: z_tl.start()].strip() if z_tl.start() < len(seg) else seg.strip()
        else:
            z_full = _CA_ZIP_STRICT_RE.search(full_customer_lower)
            if z_full:
                zip_code = z_full.group(1)
            mid = re.split(r"[,，]|还有", seg, maxsplit=1)[0].strip()
    mid = re.sub(r"^\s*款\s*", "", mid)
    mid = re.sub(r"\(?\d{3}\)?[-.\s]*\d{3}[-.\s]*\d{4}\b", " ", mid, flags=re.IGNORECASE)
    mid = re.sub(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b", " ", mid)
    mid = re.sub(r"\s+", " ", mid).strip()
    parts = re.findall(r"[a-z0-9]+", mid)
    model_slug = "_".join(parts)[:96].strip("_") if parts else ""
    return {"vin": None, "year": year or None, "model": model_slug or None, "zip": zip_code}


def _extract_vehicle_identity_for_key(merged_text: str) -> dict[str, str | None]:
    """
    Pull literal vehicle identity strings from customer text for vehicle_key.

    Must NOT use _extract_add_car_fields() here: that dict maps slot names to booleans
    (e.g. year=True), which stringifies to junk keys like ymz:True|true|True.

    When the latest customer bubble is a vehicle correction, scope identity to that bubble
    (last year/model in the bubble) so vehicle_key stays aligned with broker_next_step /
    conversation_summary — same policy as _extract_add_car_vehicle_concrete.
    """
    raw = _customer_text_for_add_car_extraction(merged_text)
    tl = raw.lower()
    if not tl.strip():
        return {"vin": None, "year": None, "model": None, "zip": None}
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    last_seg = (matches[-1] or "").strip() if matches else ""
    if last_seg and _is_add_car_vehicle_correction_signal(last_seg):
        return _extract_vehicle_identity_for_key_scoped(last_seg, tl)

    vin_matches = list(_VIN_17_RE.finditer(tl))
    if vin_matches:
        return {"vin": vin_matches[-1].group(1).upper(), "year": None, "model": None, "zip": None}
    # 款 immediately after year has no ASCII \\b boundary (Unicode "word" char); allow optional 款.
    year_m = re.search(r"(?<![0-9])(20[12][0-9])(?:\s*款)?", tl)
    if not year_m:
        z_only = _CA_ZIP_STRICT_RE.search(tl)
        return {
            "vin": None,
            "year": None,
            "model": None,
            "zip": z_only.group(1) if z_only else None,
        }
    year = year_m.group(1)
    sub = tl[year_m.end() :]
    seg = re.split(r"还有|另一辆|第二辆|;", sub, maxsplit=1)[0]
    z_m = _CA_ZIP_STRICT_RE.search(seg)
    if z_m:
        zip_code = z_m.group(1)
        mid = seg[: z_m.start()].strip()
    else:
        z_m2 = _CA_ZIP_STRICT_RE.search(sub)
        if z_m2:
            zip_code = z_m2.group(1)
            mid = sub[: z_m2.start()].strip()
        else:
            zip_code = None
            mid = re.split(r"[,，]|还有", seg, maxsplit=1)[0].strip()
    mid = re.sub(r"^\s*款\s*", "", mid)
    # Drop US phone patterns so digits do not become part of model_slug (e.g. Tesla line + phone before zip).
    mid = re.sub(r"\(?\d{3}\)?[-.\s]*\d{3}[-.\s]*\d{4}\b", " ", mid, flags=re.IGNORECASE)
    mid = re.sub(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b", " ", mid)
    mid = re.sub(r"\s+", " ", mid).strip()
    parts = re.findall(r"[a-z0-9]+", mid)
    model_slug = "_".join(parts)[:96].strip("_") if parts else ""
    return {"vin": None, "year": year, "model": model_slug or None, "zip": zip_code}


def _derive_vehicle_key_from_add_car_text(merged_text: str) -> str | None:
    """Build a lightweight Add-Car vehicle identity key (nullable) from merged triage text."""
    ident = dict(_extract_vehicle_identity_for_key(merged_text))
    raw = _customer_text_for_add_car_extraction(merged_text)
    vin = (ident.get("vin") or "").strip().upper()
    _bubbles = [m.strip() for m in re.findall(r"\[客户\]\s*([^[]+)", merged_text or "") if m.strip()]
    _cb = _bubbles or None
    if vin:
        v_ok, v_rs, _v_dbg = should_accept_field("vin", raw, vin, customer_bubbles=_cb)
        if not v_ok:
            log_truth_guardrail_blocked("vin", v_rs or "blocked", raw)
            ident["vin"] = None
            vin = ""
    if vin:
        return f"vin:{vin}"
    zip_code = (ident.get("zip") or "").strip()
    if zip_code:
        z_ok, z_rs, _z_dbg = should_accept_field("zip", raw, zip_code, customer_bubbles=_cb)
        if not z_ok:
            log_truth_guardrail_blocked("zip", z_rs or "blocked", raw)
            ident["zip"] = None
            zip_code = ""
    year = (ident.get("year") or "").strip()
    model_norm = (ident.get("model") or "").strip().lower()
    if year and not re.fullmatch(r"20[12][0-9]", year):
        year = ""
    if zip_code and not re.fullmatch(r"9[0-9]{4}", zip_code):
        zip_code = ""
    if model_norm in {"", "true", "false", "none"}:
        model_norm = ""
    if year and model_norm and zip_code:
        return f"ymz:{year}|{model_norm}|{zip_code}"
    if year and model_norm:
        return f"ym:{year}|{model_norm}"
    return None


def _derive_service_type(
    *,
    issue_category: str,
    lowered_text: str,
    is_add_car: bool,
    is_remove_car: bool,
) -> str:
    """Return explicit lightweight service type for Stage-1 boundary and storage."""
    cat = (issue_category or "").strip().lower()
    if is_add_car:
        return "add_car"
    if is_remove_car:
        return "remove_car"
    if _is_claim_intake_request(lowered_text):
        return "claim_intake"
    if _is_premium_review_request(lowered_text):
        return "renewal_premium"
    if cat in ("cancellation_warning", "payment_lapse_expiration"):
        return "billing"
    if cat == "missing_document":
        return "missing_document"
    return "general_inquiry"


def _apply_append_case_boundary(
    result: dict[str, Any],
    existing_source_text: str,
    new_message: str,
    client_id: str | None = None,
) -> None:
    """Mutates triage result for append flow: clearer portal-style boundary semantics."""
    if str(result.get("case_boundary_action") or "").strip() == "requires_new_case":
        result["append_allowed"] = False
        return
    boundary = _classify_append_case_boundary(existing_source_text, new_message)
    if not boundary:
        return
    prior = _infer_prior_case_domain(existing_source_text)
    domains = _last_message_issue_domains(new_message)
    merged_for_lang = f"{existing_source_text}\n\n{new_message}"
    language = _detect_client_language(merged_for_lang)
    bc = _merged_append_boundary_copy(client_id, _get_stitched_phrases(client_id))
    cz = bc["continuity_zh"]
    tzh = bc["new_issue_tail_zh"]
    ten = bc["new_issue_tail_en"]

    if boundary == "new_issue":
        result["case_boundary"] = "new_issue"
        if language == "zh":
            continuity = cz.get(prior) or cz["generic"]
            if "claim" in domains or _is_claim_intake_request(new_message):
                tail = tzh["claim"]
            elif "billing" in domains:
                tail = tzh["billing"]
            elif "remove_car" in domains:
                tail = tzh["remove_car"]
            elif "premium" in domains:
                tail = tzh["premium"]
            elif "add_car" in domains or _is_add_vehicle_request((new_message or "").lower()):
                tail = tzh["add_car"]
            else:
                tail = tzh["default"]
            draft = continuity + tail
        else:
            continuity = (
                bc["continuity_en_add_car"] if prior == "add_car" else bc["continuity_en_other"]
            )
            if "claim" in domains or _is_claim_intake_request(new_message):
                tail = ten["claim"]
            elif "billing" in domains:
                tail = ten["billing"]
            elif "remove_car" in domains:
                tail = ten["remove_car"]
            elif "premium" in domains:
                tail = ten["premium"]
            elif "add_car" in domains or _is_add_vehicle_request((new_message or "").lower()):
                tail = ten["add_car"]
            else:
                tail = ten["default"]
            draft = continuity + tail
        if language == "zh" and prior == "add_car":
            draft = (draft or "").rstrip() + bc["add_car_split_hint_zh"]
        elif language != "zh" and prior == "add_car":
            draft = (draft or "").rstrip() + bc["add_car_split_hint_en"]
        result["client_reply_draft"] = draft
        prefix = (
            "Case boundary: possible new issue in the same thread—confirm whether to split. "
        )
        cur = (result.get("broker_next_step") or "").strip()
        if not cur.startswith("Case boundary:"):
            result["broker_next_step"] = (prefix + cur).strip()
        summary = (result.get("conversation_summary") or "").strip()
        dom = ",".join(sorted(domains)) or "unspecified"
        tag = f"Boundary: new_issue (prior={prior}; last={dom}). "
        if not summary.startswith("Boundary:"):
            result["conversation_summary"] = (tag + summary).strip()

    elif boundary == "borderline":
        result["case_boundary"] = "borderline"
        draft = bc["borderline_zh"] if language == "zh" else bc["borderline_en"]
        result["client_reply_draft"] = draft
        prefix2 = (
            "Case boundary unclear—office should confirm topic scope; "
            "customer message is still appended to this record for traceability. "
        )
        cur = (result.get("broker_next_step") or "").strip()
        if not cur.startswith("Case boundary"):
            result["broker_next_step"] = (prefix2 + cur).strip()
        hf = list(result.get("human_confirmation_fields") or [])
        if "case_topic_boundary" not in hf:
            hf.append("case_topic_boundary")
        result["human_confirmation_fields"] = hf
        result["human_confirmation_required"] = True
        summary = (result.get("conversation_summary") or "").strip()
        tag2 = f"Boundary: borderline (prior={prior}). "
        if not summary.startswith("Boundary:"):
            result["conversation_summary"] = (tag2 + summary).strip()


def _append_last_turn_carries_vehicle_identity(last_msg: str) -> bool:
    """True when the latest customer line plausibly asserts year/make/VIN (vs ack / zip-only)."""
    t = (last_msg or "").strip()
    if not t:
        return False
    if _VIN_17_RE.search(t.lower()):
        return True
    return bool(re.search(r"(?<![0-9])(20[12][0-9])(?:\s*款)?", t))


def triage_for_append(
    existing_source_text: str,
    new_message: str,
    client_id: str | None = None,
    reply_truth_context: dict[str, Any] | None = None,
    *,
    v6_ocr_signals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Triage a new customer follow-up in the context of an existing case.
    Returns full triage result suitable for append_follow_up_message.
    For append flow we always treat as handoff-ready (broker receives updated case).
    client_id: when provided (e.g. from case.client_id), uses client-aware handoff phrases.
    reply_truth_context: pass persisted truth (formal_submitted_at, lifecycle) so Add-Car replies
        use post-submit phrasing; when omitted, pre-submit handoff lines may incorrectly persist.
    """
    turns = _parse_source_to_turns(existing_source_text)
    result = triage_conversation(
        new_message.strip(),
        turns,
        client_id=client_id,
        reply_truth_context=reply_truth_context,
        for_append=True,
        v6_ocr_signals=v6_ocr_signals,
    )
    result["triage_mode"] = "append"
    # Append path: broker must see the update on the service record; not the same semantic as greenfield quote_ready gating.
    result["handoff_ready"] = True
    # Append continues an office-visible service record — do not surface pre-submit lifecycle.
    ctx = reply_truth_context or {}
    if str(ctx.get("formal_submitted_at") or "").strip() or ctx.get("service_record_append") is True:
        result["lifecycle_status"] = "office_followup"
    else:
        result["lifecycle_status"] = "handoff_pending"
    result["next_best_question"] = ""
    merged_for_lane = _build_conversation_text_for_triage(turns, new_message.strip())
    lowered_merged = (merged_for_lane or "").lower()
    ocr_blob_app = ""
    if v6_ocr_signals and isinstance(v6_ocr_signals, dict):
        from services.fiqa_api.inbox_triage.ocr_case_fusion import build_supplemental_extraction_blob

        ocr_blob_app = build_supplemental_extraction_blob(v6_ocr_signals)
    lowered_lane_app = lowered_merged
    if ocr_blob_app:
        lowered_lane_app = f"{lowered_merged}\n[ocr]\n{ocr_blob_app.lower()}"
    _lane_matches = re.findall(r"\[客户\]\s*([^[]+)", merged_for_lane or "")
    _last_cust_lane = (_lane_matches[-1] or "").strip() if _lane_matches else new_message.strip()
    is_add_car_lane = _effective_add_car_lane_active(
        lowered_merged=lowered_lane_app,
        merged_text=merged_for_lane,
        reply_truth_context=ctx,
        last_customer_raw=_last_cust_lane,
        v6_ocr_signals=v6_ocr_signals if isinstance(v6_ocr_signals, dict) else None,
    )
    if is_add_car_lane:
        pv_raw = ctx.get("vehicle_key")
        persisted_vk = str(pv_raw).strip() if isinstance(pv_raw, str) and str(pv_raw).strip() else None
        extra_signal = bool(result.get("additional_vehicle_mentioned")) or append_turn_signals_extra_vehicle_intent(
            new_message.strip()
        )
        amb = text_suggests_vehicle_scope_ambiguity(new_message.strip())
        last_turn = new_message.strip()
        # Short acknowledgements should not lose persisted VIN scope when merged extract yields ymz vs vin:*.
        short_scope_carryover = bool(persisted_vk) and not extra_signal and not amb and (
            not _append_last_turn_carries_vehicle_identity(last_turn)
        )
        conflict = (
            "same_vehicle"
            if short_scope_carryover
            else detect_vehicle_conflict(
                persisted_vehicle_key=persisted_vk,
                new_vehicle_key=result.get("vehicle_key"),
                additional_vehicle_mentioned=extra_signal,
                message_suggests_vehicle_scope_ambiguity=amb,
            )
        )
        if conflict == "new_vehicle":
            result["case_boundary"] = "new_issue"
            result["case_boundary_action"] = "requires_new_case"
            result["append_allowed"] = False
            if not (result.get("boundary_reason") or "").strip():
                result["boundary_reason"] = (
                    "Vehicle scope differs from this case; open a new service record for the other vehicle."
                )
        elif conflict == "ambiguous":
            result["case_boundary"] = "borderline"
            result["case_boundary_action"] = "requires_confirmation"
            result["append_allowed"] = False
            if not (result.get("boundary_reason") or "").strip():
                result["boundary_reason"] = (
                    "Vehicle scope is unclear on this thread; confirm with the customer before updating this record."
                )
            hf = list(result.get("human_confirmation_fields") or [])
            if "case_topic_boundary" not in hf:
                hf.append("case_topic_boundary")
            result["human_confirmation_fields"] = hf
            result["human_confirmation_required"] = True

    _apply_append_case_boundary(result, existing_source_text, new_message.strip(), client_id=client_id)
    boundary = str(result.get("case_boundary") or "").strip()
    if boundary == "new_issue":
        result["case_boundary_action"] = "requires_new_case"
        result["append_allowed"] = False
        if not (result.get("boundary_reason") or "").strip():
            result["boundary_reason"] = "Detected clear matter separation from current case."
        bns_pre = (result.get("broker_next_step") or "").strip()
        if not bns_pre.startswith("Case boundary:"):
            prefix_nb = (
                "Case boundary: possible new issue in the same thread—confirm whether to split. "
            )
            result["broker_next_step"] = (prefix_nb + bns_pre).strip()
        summ = (result.get("conversation_summary") or "").strip()
        if not summ.startswith("Boundary:"):
            result["conversation_summary"] = (
                "Boundary: new_issue (matter or vehicle scope). " + summ
            ).strip()
    elif boundary == "borderline":
        result["case_boundary_action"] = "requires_confirmation"
        if result.get("append_allowed") is not False:
            result["append_allowed"] = True
        if not (result.get("boundary_reason") or "").strip():
            result["boundary_reason"] = (
                "Topic continuity is borderline; message was appended to this record for audit; "
                "office should confirm whether it belongs on the same matter."
            )
    else:
        result["case_boundary"] = "same_case"
        result["case_boundary_action"] = "append_allowed"
        result["append_allowed"] = True
        result["boundary_reason"] = "No clear boundary conflict detected; append stays on current case."
    return result


def _merged_and_last_customer_for_add_car_draft(raw: str) -> tuple[str, str]:
    """
    Normalize triage text for add-car slot extraction and acknowledgements.
    When `raw` is already merged ([客户] lines), use it as-is and take the last bubble.
    Otherwise wrap a single utterance as one customer line.
    """
    s = (raw or "").strip()
    if not s:
        return ("", "")
    if "[客户]" in s:
        matches = re.findall(r"\[客户\]\s*([^[]+)", s)
        last = (matches[-1] or "").strip() if matches else s
        return (s, last)
    return (f"[客户] {s}", s.strip())


def _extract_add_car_material_signals(merged_text: str) -> dict[str, bool]:
    """Prospective send / not-yet-ready / already-sent claims for Add-Car broker visibility."""
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    bodies = [m.strip() for m in matches] if matches else [(merged_text or "").strip()]
    t_joined = " ".join(bodies).lower()
    prospective = False
    for b in bodies:
        bl = (b or "").strip().lower()
        if bl and _is_prospective_send_offer_message(bl):
            prospective = True
            break
    already_sent = any(_message_claims_completed_material_send(b) for b in bodies if b)
    not_ready = any(
        m in t_joined
        for m in (
            "还没拿到",
            "还没出",
            "还没出来",
            "购车文件还没",
            "车牌还没有",
            "车牌还没",
            "vin还没",
            "还没vin",
            "拿不到vin",
            "材料还没",
            "可以先报",
            "等等发",
            "晚一点发",
            "晚点发",
            "还没齐",
        )
    )
    return {
        "prospective_send_question": prospective,
        "materials_not_ready_claimed": not_ready,
        "already_sent_claimed": already_sent,
    }


def _extract_add_car_fields(merged_text: str) -> dict[str, bool]:
    """Extract add-car fields from customer text plus [OCR] supplement (image intake)."""
    scan = _customer_text_for_add_car_extraction(merged_text)
    t = (scan or "").lower()
    has_year = text_has_vehicle_year_signal(t)
    has_zip = _text_has_ca_zip_signal(t)
    has_model = text_has_vehicle_make_model_signal(t)
    has_delivery = any(
        m in t
        for m in [
            "next week",
            "下周",
            "提车",
            "拿车",
            "picking up",
            "pick up",
            "pickup",
            "pick-up",
            "delivery",
            "deliver",
            "明天",
            "tomorrow",
            "下周拿",
            "明天拿",
            "下周提",
            "明天提",
            "friday",
            "this friday",
            "next friday",
            "周五",
            "下周五",
            "本周五",
            "礼拜五",
        ]
    )
    if not has_delivery:
        has_delivery = bool(re.search(r"\d{1,2}月\d{1,2}[号日]", t)) and any(
            x in t for x in ("提", "拿车", "到车", "取车", "pick")
        )
    if not has_delivery:
        # Effective / policy start date (delivery-equivalent for quote readiness).
        if re.search(r"(?i)\b(start|effective|begin)\b", t) and re.search(
            r"\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(19|20)\d{2}\b", t
        ):
            has_delivery = True
    has_driver = _text_has_add_car_driver_signal(t)
    # VIN: 17-char VIN, or explicit VIN intent — exclude "VIN还没拿到" / "VIN 还没拿到" style negatives
    has_vin_17 = bool(_VIN_17_RE.search(t))
    _t_no_ws = re.sub(r"\s+", "", t)
    _vin_negative = any(
        m in _t_no_ws
        for m in (
            "vin还没",
            "还没vin",
            "没vin",
            "vin没",
            "没有vin",
            "拿不到vin",
            "vin没有",
            "还没拿到vin",
            "vin拿不到",
        )
    )
    # Dealer / third party still preparing VIN (spacing-tolerant: "VIN 车行说还要等")
    if (
        "vin" in t
        and not has_vin_17
        and not _vin_negative
        and any(m in t for m in ("还要等", "等两天", "过几天", "才有", "还没出", "还没有"))
        and any(m in t for m in ("车行", "dealer", "销售", "店里"))
    ):
        _vin_negative = True
    # Offering / asking whether to send VIN — not "already have VIN"
    _vin_send_question = (
        not has_vin_17
        and "vin" in t
        and any(m in t for m in ("要不要", "可以吗", "行吗", "先发", "发你vin", "vin发你", "先把vin"))
    )
    has_vin = has_vin_17 or ("vin" in t and not _vin_negative and not _vin_send_question)
    # Insurance status: add-to-existing vs new customer
    has_add_to_existing = any(
        m in t for m in ["加车", "加一台", "加一辆", "add car", "add to policy", "existing policy", "想加"]
    )
    has_new_customer = any(
        m in t for m in ["新车", "new car", "刚买", "才买", "bought", "new policy", "新保单"]
    ) and not has_add_to_existing
    # Additional drivers
    has_additional_drivers = any(
        m in t
        for m in [
            "还有别人",
            "别人开",
            "老婆开",
            "老公开",
            "孩子开",
            "儿子开",
            "女儿开",
            "主要驾驶人是我老婆",
            "主要驾驶人是我老公",
            "我跟老婆",
            "我跟我老婆",
            "和老婆",
            "夫妻",
            "都可能开",
            "都可以开",
            "spouse",
            "teen",
            "other driver",
            "either of us",
            "both of us",
        ]
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


def _extract_contact_fields(merged_text: str) -> tuple[str | None, str | None]:
    """Extract name and phone from customer messages. ADD_CAR_IDENTITY_CONTACT_LITE.
    Returns (name, phone); each is None if not found. Uses customer messages only."""
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    customer_text = " ".join(matches)
    if not customer_text:
        return (None, None)
    t = customer_text
    extracted_name: str | None = None
    extracted_phone: str | None = None

    # Phone: US format (xxx) xxx-xxxx, xxx-xxx-xxxx, xxx.xxx.xxxx, xxx xxx xxxx, xxxxxxxxxx
    phone_patterns = [
        r"\(?(\d{3})\)?[-.\s]*(\d{3})[-.\s]*(\d{4})\b",
        r"\b(\d{3})[-.\s](\d{3})[-.\s](\d{4})\b",
        r"(?:电话|phone|call me|我电话|联系方式|手机)[：:\s]*\(?(\d{3})\)?[-.\s]*(\d{3})[-.\s]*(\d{4})\b",
    ]
    for pat in phone_patterns:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            g = m.groups()
            if len(g) == 3:
                extracted_phone = f"{g[0]}-{g[1]}-{g[2]}"
            break

    # Name: 我是X, 我姓X, 我叫X, 姓名/名字 labeled (with or without :), call me X, I'm X, — X at end
    name_patterns = [
        (r"(?:姓名|名字)\s*[:：]?\s*([^\s,，.。手机电话\d:：]{2,24})", 1, 2),
        (r"我是\s*([^\s,，.。]+)", 1, 2),
        (r"我姓\s*([^\s,，.。]+)", 1, 1),
        (r"我叫\s*([^\s,，.。]+)", 1, 2),
        (r"姓名\s*[:：]\s*([^\s手机电话:：]{2,24})", 1, 2),
        (r"名字\s*[:：]\s*([^\s手机电话:：]{2,24})", 1, 2),
        (r"call me\s+([a-zA-Z][a-zA-Z\s-]{1,20})\b", 1, 2),
        (r"i'?m\s+([a-zA-Z][a-zA-Z\s-]{1,20})\b", 1, 2),
        (r"this is\s+([a-zA-Z][a-zA-Z\s-]{1,20})\b", 1, 2),
        (r"[—\-]\s*([^\s\d,，.。]{2,6})\s*$", 1, 2),
    ]
    exclude = {"bmw", "tesla", "honda", "toyota", "model", "zip", "90210", "accord", "camry"}
    for pat, grp, min_len in name_patterns:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            name_cand = m.group(grp).strip()
            if len(name_cand) >= min_len and name_cand.lower() not in exclude and not re.match(r"^\d+$", name_cand):
                extracted_name = name_cand[:120]
                break

    return (extracted_name, extracted_phone)


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
    if any(m in t for m in ["registration", "行驶证"]) or ("registration" in t and "照片" in t):
        items_mentioned.append("registration")
        if any(m in t for m in ["发", "sent", "发过", "又发", "already sent", "resend", "邮箱", "email"]):
            items_sent.append("registration")
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
    _cx_bodies = [x.strip() for x in matches] if matches else [(merged_text or "").strip()]
    screenshot_sent = any(_message_claims_completed_material_send(b) for b in _cx_bodies if b)
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


def _is_add_car_vehicle_correction_signal(text: str) -> bool:
    """
    True when the customer is clearly correcting *which vehicle* (not e.g. driver-only fixes).
    Used for correction-aware customer-facing replies (trust / office-realism).
    """
    raw = (text or "").strip()
    if not raw:
        return False
    tl = raw.lower()
    # Chinese: negation + correction clause (allow comma between 不是…是, e.g. 不是X5，是X3)
    if re.search(r"不是[^，。\n]{0,40}是\s*", raw):
        return True
    if re.search(r"不是.{1,48}是\s*", raw) and re.search(
        r"(20[12][0-9]|tesla|特斯拉|bmw|x[0-9]\b|宝马|本田|丰田|雷克萨斯|honda|toyota|lexus|accord|civic|camry|corolla)",
        tl,
    ):
        return True
    if re.search(r"不对[,，]?\s*是\s*", raw) and re.search(
        r"(20[12][0-9]|tesla|特斯拉|bmw|x[0-9]\b|宝马|本田|丰田|honda|toyota)",
        tl,
    ):
        return True
    if "搞错了" in raw and re.search(
        r"是\s*(20[12][0-9]|tesla|特斯拉|bmw|宝马|本田|丰田|honda|toyota|x[0-9]\b)",
        tl,
    ):
        return True
    if any(m in raw for m in ("不是这个", "不是这辆", "不是那辆", "不是这台车", "不是那台", "另一辆")):
        return True
    if any(m in tl for m in ("not that one", "wrong car", "wrong vehicle", "meant the", "meant a")):
        return True
    if re.search(r"\b(i meant|actually)\b.+\b(20[12][0-9]|tesla|bmw|honda|toyota|lexus)\b", tl):
        return True
    # 说错了 only when the same bubble also re-specifies the car (avoid driver-only 说错了)
    if "说错了" in raw and re.search(
        r"(20[12][0-9]|特斯拉|宝马|本田|丰田|雷克萨斯|[xX][35]\b|tesla|bmw|honda|toyota|lexus|accord|civic|camry)",
        tl,
    ):
        return True
    if _is_add_car_vin_field_correction_signal(raw) and _VIN_17_RE.search(tl):
        return True
    return False


def _add_car_vehicle_concrete_from_scope(scope: str, year_pool: str) -> str:
    """Resolve year (prefer digits in scope, else latest in year_pool) + model from scope text."""
    if not (scope or "").strip():
        return ""
    customer_text = scope
    t = scope.lower()
    ys = re.findall(r"(20[12][0-9])", scope)
    yp = re.findall(r"(20[12][0-9])", year_pool)
    year = ys[-1] if ys else (yp[-1] if yp else "")
    model = ""
    if "model y" in t or ("tesla" in t and re.search(r"\by\b", t) and "model" in t):
        model = "Tesla Model Y"
    elif "model 3" in t or ("tesla" in t and re.search(r"\b3\b", t) and "model" in t):
        model = "Tesla Model 3"
    elif "tesla" in t or "特斯拉" in customer_text:
        model = "Tesla" if "特斯拉" not in customer_text else "特斯拉"
    elif list(re.finditer(r"[xX]([35])(?![0-9])", scope)):
        xi = list(re.finditer(r"[xX]([35])(?![0-9])", scope))[-1].group(1)
        model = f"BMW X{xi}"
    elif "宝马" in customer_text:
        model = "宝马"
    elif "honda" in t and ("accord" in t or "civic" in t or "cr-v" in t):
        model = "Honda " + ("Accord" if "accord" in t else "Civic" if "civic" in t else "CR-V")
    elif "toyota" in t and ("camry" in t or "corolla" in t or "rav4" in t):
        model = "Toyota " + ("Camry" if "camry" in t else "Corolla" if "corolla" in t else "RAV4")
    elif "nissan" in t and "altima" in t:
        model = "Nissan Altima"
    elif any(m in t for m in ["bmw", "honda", "toyota", "lexus", "nissan"]):
        model = next((m.title() for m in ["tesla", "bmw", "honda", "toyota", "lexus", "nissan"] if m in t), "")
    elif any(m in customer_text for m in ["特斯拉", "宝马", "本田", "丰田"]):
        model = next((m for m in ["特斯拉", "宝马", "本田", "丰田"] if m in customer_text), "")
    if year and model:
        return f"{year} {model}"
    if year:
        return year
    return model if model else ""


def _count_prior_system_contact_gap_tails_in_thread(merged_text: str, language: str) -> int:
    """Count prior [系统] turns that already included a name/phone contact-gap reminder.

    Used to avoid repeating the same tail across consecutive assistant turns (REPLY_CONTACT_GAP_TAIL_MISMATCH).
    """
    segs = re.findall(r"\[系统\]\s*([^[]+)", merged_text or "")
    markers_zh = (
        "若姓名或电话尚未",
        "（若方便：请在本对话补一行姓名与电话",
        "办公室后续联系时可能会先确认联系方式",
    )
    markers_en = (
        "name or phone isn't clear on this record",
        "add your name and phone in one line",
        "confirm contact details when they reach out",
    )
    n = 0
    for seg in segs:
        s = (seg or "").strip()
        if not s:
            continue
        if language == "zh":
            if any(m in s for m in markers_zh):
                n += 1
        else:
            lo = s.lower()
            if any(m.lower() in lo for m in markers_en):
                n += 1
    return n


def _extract_add_car_vehicle_concrete(merged_text: str) -> str:
    """Extract concrete vehicle string (e.g. '2024 Tesla Model Y') for broker summary.
    Uses customer messages only; on vehicle-correction turns, model/year resolve from the last bubble
    so X5→X3 and similar overrides beat earlier mentions."""
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    customer_text = " ".join(matches).replace("\n", " ")
    if not customer_text:
        return ""
    last_seg = (matches[-1] or "").strip() if matches else ""
    if last_seg and _is_add_car_vehicle_correction_signal(last_seg):
        hit = _add_car_vehicle_concrete_from_scope(last_seg, customer_text)
        if hit:
            return hit
    return _add_car_vehicle_concrete_from_scope(customer_text, customer_text)


def _extract_primary_add_car_vehicle_concrete(merged_text: str) -> str:
    """Office-facing primary vehicle line: matches vehicle_key first-segment policy when multi-vehicle."""
    matches = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    customer_text = " ".join(matches).replace("\n", " ")
    if not customer_text:
        return ""
    last_seg = (matches[-1] or "").strip() if matches else ""
    if last_seg and _is_add_car_vehicle_correction_signal(last_seg):
        hit = _add_car_vehicle_concrete_from_scope(last_seg, customer_text)
        if hit:
            return hit
    cust_only = customer_text.strip()
    if _add_car_mentions_multiple_vehicles(cust_only):
        first = re.split(r"还有|另一辆|第二辆|;", cust_only, maxsplit=1)[0]
        hit = _add_car_vehicle_concrete_from_scope(first, first)
        if hit:
            return hit
    return _add_car_vehicle_concrete_from_scope(customer_text, customer_text)


def _add_car_enough_for_handoff(fields: dict[str, bool]) -> bool:
    """Pilot: broker-visible completeness requires VIN + garaging zip + delivery + primary driver.

    Year/make alone must not unlock handoff (operator trust).
    """
    if not fields.get("vin"):
        return False
    if not fields.get("zip"):
        return False
    if not fields.get("delivery"):
        return False
    if not fields.get("driver"):
        return False
    return True


def _add_car_near_dense_case_ready(fields: dict[str, bool]) -> bool:
    """VIN + ZIP + vehicle identity (explicit Y/M or VIN) — skip intermediate ladder; one critical ask at a time."""
    if not fields.get("vin") or not fields.get("zip"):
        return False
    vehicle_ok = (fields.get("year") and fields.get("model")) or fields.get("vin")
    return bool(vehicle_ok)


def _add_car_llm_slot_should_invoke(
    rule_fields: dict[str, bool], merged_text: str, last_bubble: str
) -> tuple[bool, str]:
    """Token discipline: call bounded slot LLM only when rules/contact are incomplete or bubble is long."""
    enough = _add_car_enough_for_handoff(rule_fields)
    en, ph = _extract_contact_fields(merged_text)
    if enough and en and ph:
        return False, "rule_complete_with_contact"
    if not enough:
        return True, "structural_incomplete"
    if enough and (not en or not ph) and len((last_bubble or "").strip()) >= 8:
        return True, "contact_gap"
    if len((last_bubble or "").strip()) > 140:
        return True, "long_bubble"
    return False, "no_heuristic"


def _add_car_quote_ready_status(fields: dict[str, bool]) -> str:
    """Return quote_ready_status for add-car: quote_ready | almost_ready | need_more.

    Pilot: ``quote_ready`` requires truth-gated VIN + ZIP + primary driver + explicit calendar
    delivery/effective date. Never ``almost_ready`` without VIN (avoid false operator readiness).
    """
    has_zip = bool(fields.get("zip"))
    has_delivery = bool(fields.get("delivery"))
    has_driver = bool(fields.get("driver"))
    has_vin = bool(fields.get("vin"))

    if not has_vin:
        return "need_more"
    if has_vin and has_zip and has_driver and has_delivery:
        return "quote_ready"
    return "almost_ready"


def _add_car_is_quote_ready(fields: dict[str, bool]) -> bool:
    """True iff all four pilot quote slots are truth-complete (same bar as quote_ready_status == quote_ready)."""
    return _add_car_quote_ready_status(fields) == "quote_ready"


# Persisted-case coherence: merge office-visible collected slots with fresh extraction (case_id / append).
_PERSISTED_LIST_FIELD_TO_EXTRACT_FLAG: dict[str, str] = {
    "year": "year",
    "make_model": "model",
    "vin": "vin",
    "zip": "zip",
    "delivery_date": "delivery",
    "primary_driver": "driver",
}


def _augment_add_car_fields_from_persisted_collected(
    fields: dict[str, bool],
    persisted: list[str] | None,
) -> dict[str, bool]:
    """Treat structural slots saved on the service record as satisfied for quote_ready_status."""
    if not persisted:
        return fields
    out = dict(fields)
    pl = {str(x).lower() for x in persisted}
    for lid, fk in _PERSISTED_LIST_FIELD_TO_EXTRACT_FLAG.items():
        if lid.lower() in pl:
            out[fk] = True
    return out


def _reconcile_add_car_lists_with_persisted_record(
    collected: list[str],
    still_needed: list[str],
    reply_truth_context: dict[str, Any] | None,
    *,
    persisted_collected_override: list[str] | None = None,
) -> tuple[list[str], list[str]]:
    """
    Drop still_needed entries already satisfied on the persisted case; extend collected for UI/API.
    Keeps post-submit and same-record continuation from contradicting durable record truth.
    When persisted_collected_override is set (e.g. after correction invalidation), use that list instead.
    """
    ctx = reply_truth_context or {}
    if persisted_collected_override is not None:
        persisted = list(persisted_collected_override)
    else:
        persisted = list(ctx.get("persisted_collected_fields") or [])
    if not persisted:
        return collected, still_needed
    pers_l = {str(x).lower() for x in persisted}
    new_still = [x for x in still_needed if str(x).lower() not in pers_l]
    coll_seen = {str(x).lower() for x in collected}
    new_collected = list(collected)
    for p in persisted:
        pl = str(p).lower()
        if pl and pl not in coll_seen:
            new_collected.append(p)
            coll_seen.add(pl)
    return dedupe_preserve_order(new_collected), dedupe_preserve_order(new_still)


def _compute_add_car_collected_still_lists(
    merged_for_add_car_extraction: str,
    last_customer_raw: str,
    reply_truth_context: dict[str, Any] | None,
    follow_up_type: str,
) -> tuple[list[str], list[str], dict[str, Any], str | None, str | None]:
    """Single spine for add-car collected/still lists (structured extraction + persisted reconcile)."""
    collected, still_needed, extracted_name, extracted_phone = _add_car_structured_fields(
        merged_for_add_car_extraction
    )
    if last_customer_raw:
        lt_n, lt_p = _extract_contact_fields(f"[客户] {last_customer_raw.strip()}")
        if lt_n:
            extracted_name = extracted_name or lt_n
            if "name" not in collected:
                collected.append("name")
        if lt_p:
            extracted_phone = extracted_phone or lt_p
            if "phone" not in collected:
                collected.append("phone")
    pc = reply_truth_context or {}
    if str(pc.get("record_contact_name") or "").strip():
        still_needed = [x for x in still_needed if str(x).lower() != "name"]
    if str(pc.get("record_contact_phone") or "").strip():
        still_needed = [x for x in still_needed if str(x).lower() != "phone"]
    if extracted_name:
        still_needed = [x for x in still_needed if str(x).lower() != "name"]
    if extracted_phone:
        still_needed = [x for x in still_needed if str(x).lower() != "phone"]
    if str(pc.get("formal_submitted_at") or "").strip():
        still_needed = [x for x in still_needed if str(x).lower() not in ("name", "phone")]
    effective_persisted, merge_meta = _effective_persisted_for_add_car_merge(
        reply_truth_context, last_customer_raw, follow_up_type
    )
    collected, still_needed = _reconcile_add_car_lists_with_persisted_record(
        collected,
        still_needed,
        reply_truth_context,
        persisted_collected_override=effective_persisted,
    )
    return collected, still_needed, merge_meta, extracted_name, extracted_phone


_VEHICLE_CORRECTION_TOKEN_RE = re.compile(
    r"(20[12][0-9]|accord|camry|corolla|civic|cr-v|crv|tesla|model\s*y|model\s*3|bmw|x[357]|honda|toyota|lexus|"
    r"vin|车架|车型|雅阁|凯美瑞|思域|特斯拉|宝马|丰田|本田|另一辆|这辆|那辆|雷克萨斯|suv|sedan|vehicle|car\b)",
    re.IGNORECASE,
)


def _is_add_car_vehicle_correction_for_merge(last_msg: str) -> bool:
    """When invalidating persisted vehicle slots: require vehicle-industry cues; skip topic pivots."""
    raw = (last_msg or "").strip()
    if not raw:
        return False
    if _correction_is_cross_topic_pivot_not_vehicle_fix(raw):
        return False
    tl = raw.lower()
    if not _VEHICLE_CORRECTION_TOKEN_RE.search(tl):
        return False
    if _is_add_car_vehicle_correction_signal(raw):
        return True
    if re.search(r"不是[^，。\n]{0,40}是\s*", raw):
        return True
    if any(m in raw for m in ("不是这个", "不是这辆", "另一辆", "不是那辆", "不是这台车")):
        return True
    return False


def _is_add_car_zip_correction_signal(last_msg: str) -> bool:
    raw = (last_msg or "").strip()
    if not raw:
        return False
    tl = raw.lower()
    has_zip_sig = bool(re.search(r"\b9[0-9]{4}\b", raw)) or "邮编" in raw or re.search(r"\bzip\b", tl)
    if not has_zip_sig:
        return False
    return any(
        m in raw
        for m in (
            "不是",
            "更正",
            "改",
            "写错",
            "写错了",
            "换成",
            "不对",
            "更正一下",
            "改一下",
            "其实",
        )
    ) or any(m in tl for m in ("wrong zip", "wrong area code"))


def _is_add_car_contact_phone_correction_signal(last_msg: str) -> bool:
    raw = (last_msg or "").strip()
    if not raw:
        return False
    tl = raw.lower()
    has_phone = bool(re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", raw))
    if not has_phone:
        return False
    if any(
        m in raw
        for m in (
            "不是",
            "更正",
            "改",
            "换成",
            "写错",
            "写错了",
            "之前",
            "电话",
            "手机",
            "更正电话",
            "新的电话",
            "新手机",
            "新号码",
        )
    ):
        return True
    if "phone" in tl and any(m in tl for m in ("wrong", "not the", "not this", "new number", "update")):
        return True
    if "wrong number" in tl:
        return True
    return False


def _is_add_car_contact_name_correction_signal(last_msg: str) -> bool:
    raw = (last_msg or "").strip()
    if not raw:
        return False
    tl = raw.lower()
    if any(m in raw for m in ("名字写错", "姓名写错", "名字更正", "实际我是", "更正名字")):
        return True
    if "我是" in raw and any(m in raw for m in ("不是", "更正", "改", "其实")):
        return True
    if any(m in tl for m in ("correct name", "wrong name", "my name is actually")):
        return True
    return False


def _is_add_car_vin_field_correction_signal(last_msg: str) -> bool:
    raw = (last_msg or "").strip()
    if not raw:
        return False
    tl = raw.lower()
    if not any(m in tl for m in ("vin", "车架")):
        return False
    if any(
        m in tl
        for m in (
            "wrong vin",
            "vin is wrong",
            "incorrect vin",
            "vin should be",
            "actually the vin",
            "the vin is actually",
            "correct vin",
            "sorry the vin",
            "vin is actually",
        )
    ):
        return True
    return any(m in raw for m in ("写错", "错了", "不对", "更正", "改", "不是", "改一下"))


def _is_add_car_delivery_or_driver_correction_signal(last_msg: str) -> bool:
    raw = (last_msg or "").strip()
    if not raw:
        return False
    tl = raw.lower()
    has_dd = any(
        m in raw
        for m in ("提车", "拿车", "delivery", "driver", "驾驶人", "下周", "明天", "primary", "老婆开", "老公开")
    ) or bool(re.search(r"\d{1,2}月\d{1,2}", raw))
    if not has_dd:
        return False
    return any(
        m in raw
        for m in ("不是", "更正", "改", "写错", "写错了", "说错了", "其实", "更正一下")
    ) or any(m in tl for m in ("wrong", "actually", "meant", "i meant"))


def _effective_persisted_for_add_car_merge(
    reply_truth_context: dict[str, Any] | None,
    last_customer_raw: str,
    follow_up_type: str,
) -> tuple[list[str], dict[str, Any]]:
    """
    Correction vs persisted record (Add-Car): drop selected persisted slot ids so fresh extraction
    wins for those fields instead of blindly merging stale office-visible lists.
    """
    meta: dict[str, Any] = {"correction_turn": False, "invalidated_slots": []}
    ctx = reply_truth_context or {}
    persisted = [str(x) for x in (ctx.get("persisted_collected_fields") or []) if str(x).strip()]
    if not persisted:
        return persisted, meta
    if not str(ctx.get("formal_submitted_at") or "").strip():
        return persisted, meta

    last = (last_customer_raw or "").strip()
    ft = (follow_up_type or "").strip().lower()
    strip: set[str] = set()

    if _is_add_car_vehicle_correction_for_merge(last):
        strip.update(["year", "make_model", "vin"])
        meta["correction_turn"] = True
    elif (
        not _correction_is_cross_topic_pivot_not_vehicle_fix(last)
        and ft == "correction"
        and _VEHICLE_CORRECTION_TOKEN_RE.search(last.lower())
    ):
        strip.update(["year", "make_model", "vin"])
        meta["correction_turn"] = True
    elif _is_add_car_vin_field_correction_signal(last):
        strip.update({"vin", "year", "make_model"})
        meta["correction_turn"] = True

    if _is_add_car_zip_correction_signal(last):
        strip.add("zip")
        meta["correction_turn"] = True

    if _is_add_car_delivery_or_driver_correction_signal(last):
        strip.update(["delivery_date", "primary_driver"])
        meta["correction_turn"] = True

    if _is_add_car_contact_phone_correction_signal(last):
        strip.add("phone")
        meta["correction_turn"] = True

    if _is_add_car_contact_name_correction_signal(last):
        strip.add("name")
        meta["correction_turn"] = True

    from services.fiqa_api.inbox_triage.date_normalization import (
        relative_delivery_should_invalidate_persisted_calendar,
    )

    if relative_delivery_should_invalidate_persisted_calendar(last):
        strip.add("delivery_date")
        meta["correction_turn"] = True

    if not strip:
        return persisted, meta

    new_p = [x for x in persisted if str(x).lower() not in strip]
    meta["invalidated_slots"] = sorted(strip)
    return new_p, meta


def _add_car_augmented_truth_fields(
    merged_text: str,
    reply_truth_context: dict[str, Any] | None,
    last_customer_raw: str,
    follow_up_type: str,
) -> dict[str, bool]:
    """Chat extraction after strict Truth guardrails, merged with persisted collected_fields (office truth)."""
    effective_persisted, _ = _effective_persisted_for_add_car_merge(
        reply_truth_context, last_customer_raw, follow_up_type
    )
    base = _extract_add_car_fields_truth_safe(merged_text)
    return _augment_add_car_fields_from_persisted_collected(base, effective_persisted)


def _add_car_structured_fields(merged_text: str) -> tuple[list[str], list[str], str | None, str | None]:
    """Return (collected_fields, still_needed_fields, extracted_name, extracted_phone) for add-car broker handoff.
    ADD_CAR_IDENTITY_CONTACT_LITE: Includes name/phone in collected when extracted; in still_needed when quote-ready but missing."""
    fields = _extract_add_car_fields_truth_safe(merged_text)
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

    mat = _extract_add_car_material_signals(merged_text)
    if mat.get("prospective_send_question"):
        collected.append("materials_send_question")
    if mat.get("materials_not_ready_claimed"):
        collected.append("materials_still_pending")
    if mat.get("already_sent_claimed"):
        collected.append("customer_says_materials_sent")

    # ADD_CAR_IDENTITY_CONTACT_LITE: contact extraction
    extracted_name, extracted_phone = _extract_contact_fields(merged_text)
    if extracted_name:
        collected.append("name")
    if extracted_phone:
        collected.append("phone")

    still_needed: list[str] = []
    if not _add_car_enough_for_handoff(fields):
        vehicle_ok = (fields.get("year") and fields.get("model")) or fields.get("vin")
        if not vehicle_ok:
            still_needed.extend(["year", "make_model"])
        elif fields.get("vin"):
            # VIN alone does not remove year/make from operator-visible gaps (contract structural_still_needed_ids).
            if not fields.get("year"):
                still_needed.append("year")
            if not fields.get("model"):
                still_needed.append("make_model")
        if not fields.get("vin"):
            still_needed.append("vin")
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

    # Contact still needed only when truth-derived quote state is almost_ready or quote_ready (no rule-layer shortcuts).
    qrs = _add_car_quote_ready_status(fields)
    contact_tail = qrs in ("quote_ready", "almost_ready")
    if contact_tail:
        if not extracted_name:
            still_needed.append("name")
        if not extracted_phone:
            still_needed.append("phone")

    collected = dedupe_preserve_order(collected)
    still_needed = dedupe_preserve_order(still_needed)
    validate_add_car_field_lists(collected, still_needed)
    return (collected, still_needed, extracted_name, extracted_phone)


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


def _get_add_car_acknowledgement(
    last_customer_msg: str,
    fields: dict[str, bool],
    language: str,
    merged_text_for_vehicle: str | None = None,
) -> str:
    """Build a short acknowledgement of what the customer just said, for office-natural flow.
    Correction turns: explicitly confirm the effective vehicle (trust). Uses merged conversation
    for concrete vehicle so corrections override earlier messages."""
    raw_in = (last_customer_msg or "").strip()
    msg = raw_in
    # Callers sometimes pass full merged triage text here; always anchor on the latest bubble.
    if "[客户]" in raw_in:
        segs = re.findall(r"\[客户\]\s*([^[]+)", raw_in)
        if segs:
            msg = (segs[-1] or "").strip()
    if _is_image_intake_placeholder(msg):
        # Leads into the VIN / vehicle follow-up without echoing the placeholder token.
        return "收到您发的图片，" if (language or "").strip().lower() == "zh" else "Thanks for the photo — "
    if not msg or len(msg) > 120:
        return ""
    # Completed-send statements: do not echo customer wording; office handoff / next-ask handles tone.
    if _message_claims_completed_material_send(msg):
        return ""
    ctx = (
        merged_text_for_vehicle.strip()
        if (merged_text_for_vehicle and merged_text_for_vehicle.strip())
        else f"[客户] {msg}"
    )
    concrete = _extract_add_car_vehicle_concrete(ctx)

    if _is_add_car_vehicle_correction_signal(msg) and concrete:
        if language == "zh":
            lead = f"收到，按 {concrete} 这台车继续。"
        else:
            lead = f"Noted—we'll proceed with the {concrete}."
        zm_zip = _extract_ca_zip_from_message(msg)
        if fields.get("zip") and zm_zip:
            if language == "zh":
                lead += f" 邮编{zm_zip}也收到了。"
            else:
                lead += f" I have zip {zm_zip} as well."
        return lead if language == "zh" else lead + " "

    parts: list[str] = []
    # Prefer full year+make over year-only (fixes thin “好的，2024年的。” when model is known)
    if concrete and fields.get("year") and fields.get("model"):
        parts.append(f"{concrete}。" if language == "zh" else f"{concrete}.")
    elif concrete and len(concrete.strip()) >= 5 and language == "zh":
        # Merged text resolved a vehicle label but slot flags are incomplete — still echo it (trust).
        parts.append(f"{concrete}。")
    elif concrete and len(concrete.strip()) >= 5 and language != "zh":
        parts.append(f"{concrete}.")
    elif fields.get("year") and re.search(r"20[12][0-9]", msg):
        m = re.search(r"(20[12][0-9][年的]*)", msg)
        if m:
            parts.append(m.group(1) + ("的。" if "的" not in m.group(1) else "。"))
    ack_zip = _extract_ca_zip_from_message(msg)
    if fields.get("zip") and ack_zip:
        if language == "zh":
            parts.append(f"邮编{ack_zip}。")
        else:
            parts.append(f"zip {ack_zip}.")
    if fields.get("model") and not parts:
        model_snippets = [
            (r"宝马\s*[xX]?[3571]", "宝马"),
            (r"tesla\s*model\s*[yY3sSxX]", "Tesla"),
            (r"\btesla\b", "Tesla"),
            (r"特斯拉", "特斯拉"),
            (r"honda\s*(accord|civic|cr-v|crv)", "Honda"),
            (r"toyota\s*(camry|corolla|rav4)", "Toyota"),
            (r"丰田\s*花冠", "丰田花冠"),
            (r"202[0-9]\s*(bmw|honda|toyota|tesla)", "year+make"),
        ]
        for pat, _ in model_snippets:
            m = re.search(pat, msg, re.I)
            if m:
                parts.append(m.group(0) + "。" if language == "zh" else m.group(0) + ".")
                break
    # Do not echo short prospective-send questions ("要不要发你") — answered via _get_prospective_send_materials_lead.
    if not parts and len(msg) <= 40 and not _is_prospective_send_offer_message(msg.lower()):
        parts.append(msg.rstrip("。，, ") + "。" if language == "zh" else msg.rstrip("。，, ") + ".")
    if not parts:
        return ""
    ack = "收到，" + " ".join(parts) if language == "zh" else "Thanks, " + " ".join(parts).rstrip(".")
    return ack if ack.endswith("。") or ack.endswith(".") else ack + ("。" if language == "zh" else ".")


def _ack_prefix_for_next_ask(ack: str, language: str) -> str:
    """Glue acknowledgement to the following question without wrong-script punctuation (EN vs ZH)."""
    if not (ack or "").strip():
        return ""
    lang = (language or "").strip().lower()
    a = ack.rstrip()
    if lang == "zh":
        if a.endswith(("，", ",")):
            return a
        if a.endswith("。"):
            return a[:-1] + "，"
        if a.endswith(("吗", "么", "嘛")) or a.endswith("？"):
            return a + " "
        return a + "，"
    if a.endswith(("—", "–")):
        return a + " "
    if a.endswith((".", "!", "?")):
        return a + " "
    a = a.rstrip("。").rstrip()
    return a + ". "


def _get_next_ask_for_add_car(
    merged_text: str,
    fields: dict[str, bool],
    language: str,
    add_car_rules: dict[str, dict[str, str]] | None = None,
    customer_turn_count: int = 0,
    client_id: str | None = None,
    questioning_variant: str = "A",
) -> str | None:
    """Return the next most useful ask for add-car, or None if we should hand off.
    Ask order: vehicle (year+model) first when missing, then zip, then delivery/driver.
    When VIN+ZIP+dense identity (near one-shot), ask one critical slot at a time (delivery before driver).
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
            last_seg_raw = _last_labeled_customer_content(merged_text or "")
            last_customer = last_seg_raw.lower()
            # HANDOFF_TIMING_AUDIT: When customer asks document clarification (garaging, dec page) in same
            # turn as add-car info, answer the question and hand off — don't ask for driver.
            # ADD_CAR_QUOTE_EXCELLENCE: Same for coverage-adjust question — answer and hand off.
            # ADD_CAR_COMMERCIAL_FLOW_HARDENING: When customer says materials sent (发你微信了), hand off
            # — don't ask for driver; broker will verify materials and run quote.
            doc_clarification = any(
                m in last_customer
                for m in (
                    "garaging", "garaging proof", "declaration page", "dec page",
                    "是什么意思", "是什么", "要发什么", "what does", "what is",
                )
            )
            coverage_question = any(
                m in last_customer for m in ("coverage 可以调", "coverage 可以调吗", "coverage 能调", "顺便 coverage", "coverage 能改", "coverage adjust")
            )
            # Substring "发你" matches "要不要发你" — exclude prospective-send questions (PROSPECTIVE_SEND_AWARE_REPLY_POLISH).
            materials_sent = not _is_prospective_send_offer_message(
                last_customer
            ) and any(
                m in last_customer for m in ("发你", "发我", "sent", "发你微信", "发我微信", "发过了", "又发")
            )
            if doc_clarification or coverage_question or materials_sent:
                return None
            rules = add_car_rules or get_add_car_rules()
            ack = _get_add_car_acknowledgement(last_seg_raw, fields, language, merged_text)
            prefix = _ack_prefix_for_next_ask(ack, language)
            ps_lead = _get_prospective_send_materials_lead(last_seg_raw, language, client_id)
            if ps_lead:
                prefix = ps_lead + prefix
            ask = rules.get("ask_driver_only", {}).get(language) or (
                "主要驾驶人发我一下，我好安排报价。"
                if language == "zh"
                else "Send me the main driver so I can prepare the quote."
            )
            return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)
        return None
    rules = add_car_rules or get_add_car_rules()
    last_customer = _last_labeled_customer_content(merged_text or "")
    ps_lead = _get_prospective_send_materials_lead(last_customer, language, client_id)
    ack = _get_add_car_acknowledgement(last_customer, fields, language, merged_text)
    prefix = _ack_prefix_for_next_ask(ack, language)
    if ps_lead:
        prefix = ps_lead + prefix

    from services.fiqa_api.inbox_triage.date_normalization import (
        focused_ask_for_delivery_date,
        normalize_delivery_date_or_flag,
    )

    _iso_d, _dmode = normalize_delivery_date_or_flag(last_customer)
    if not fields.get("delivery") and _dmode == "ask_exact":
        return _maybe_append_add_car_price_caveat(
            merged_text,
            prefix + focused_ask_for_delivery_date(language),
            language,
            client_id,
        )

    vehicle_ok = (fields.get("year") and fields.get("model")) or fields.get("vin")
    if not vehicle_ok:
        pvc_for_confirm = (_extract_primary_add_car_vehicle_concrete(merged_text) or "").strip()
        qv = (questioning_variant or "A").strip().upper()
        if qv == "C" and pvc_for_confirm:
            ask = (
                f"我先按「{pvc_for_confirm}」理解这台车，对吗？不对请发年份+车型或 VIN。"
                if language == "zh"
                else f"Confirming the vehicle as «{pvc_for_confirm}»—reply OK or send year/make or VIN if wrong."
            )
        else:
            ask = rules.get("ask_vehicle", {}).get(language) or (
                "先把年份和车型发我，我就能继续帮您报价。"
                if language == "zh"
                else "Send me the year and make/model first so I can run the quote."
            )
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)
    # Multi-slot jump: ≥2 pilot-critical literals (VIN + ZIP) → skip year/make chat nag; office may still list ym.
    _skip_year_make_after_vin_zip = (
        fields.get("vin")
        and fields.get("zip")
        and (not fields.get("year") or not fields.get("model"))
    )
    if (
        not _skip_year_make_after_vin_zip
        and fields.get("vin")
        and (not fields.get("year") or not fields.get("model"))
    ):
        if not fields.get("year") and not fields.get("model"):
            ask = (
                "VIN 已收到。还请补一下年份和车型，方便办公室核对。"
                if language == "zh"
                else "Got the VIN—please send the year and make/model for our office records."
            )
        elif not fields.get("year"):
            ask = "再发一下车辆年份。" if language == "zh" else "Please send the vehicle year."
        else:
            ask = "再发一下车型（品牌/型号）。" if language == "zh" else "Please send the make and model."
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)
    if not fields.get("zip"):
        ask = rules.get("ask_zip", {}).get(language) or (
            "先把邮编发我，我就能继续帮您报价。"
            if language == "zh"
            else "Send me the zip or address first and I will run the quote."
        )
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)

    _near_dense = _add_car_near_dense_case_ready(fields)

    # Exactly one of delivery / driver missing — ask that slot only (avoids silent None after combined branch).
    if not fields.get("delivery") and fields.get("driver"):
        ask = rules.get("ask_delivery_only", {}).get(language) or (
            "提车日期发我一下（或生效日），我好安排报价。"
            if language == "zh"
            else "Send the delivery or effective date so I can prepare the quote."
        )
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)
    if not fields.get("driver") and fields.get("delivery"):
        ask = rules.get("ask_driver_only", {}).get(language) or (
            "主要驾驶人发我一下，我好安排报价。"
            if language == "zh"
            else "Send me the main driver so I can prepare the quote."
        )
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)

    if not fields.get("delivery") and not fields.get("driver"):
        if _near_dense:
            ask = rules.get("ask_delivery_only", {}).get(language) or (
                "提车日期发我一下（或生效日），我好安排报价。"
                if language == "zh"
                else "Send the delivery or effective date so I can prepare the quote."
            )
        else:
            ask = rules.get("ask_delivery_driver", {}).get(language) or (
                "提车日期和主要驾驶人发我一下，我好安排报价。"
                if language == "zh"
                else "Send me the delivery date and main driver so I can prepare the quote."
            )
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)
    if not fields.get("vin"):
        # PTD §9: defer_to_broker — do not extend the chat interview for VIN when strategy defers.
        if should_skip_user_prompt_for_missing_field("vin"):
            return None
        ask = rules.get("ask_vin", {}).get(language) or (
            "VIN（17位车架号）发我一下，我好让办公室出正式报价。"
            if language == "zh"
            else "Send the 17-digit VIN when you have it so we can run the formal quote."
        )
        return _maybe_append_add_car_price_caveat(merged_text, prefix + ask, language, client_id)
    return None


def _get_next_ask_draft(
    merged_text: str,
    category: str,
    base_result: dict[str, Any],
    customer_turn_count: int,
    add_car_rules: dict[str, dict[str, str]] | None = None,
    client_id: str | None = None,
    *,
    add_car_lane_active: bool = False,
    questioning_variant: str = "A",
) -> str | None:
    """
    If we should ask one more thing instead of handing off, return the draft.
    Otherwise return None (hand off).
    Add-car: from turn 1 onward (minimal-question path). Other categories: turn >= 2 only.
    """
    if (not add_car_lane_active) and customer_turn_count < 2:
        return None
    language = "zh" if _contains_chinese(merged_text) else "en"
    lowered = (merged_text or "").lower()

    if _is_add_vehicle_request(lowered) or add_car_lane_active:
        fields = _extract_add_car_fields_truth_safe(merged_text)
        return _get_next_ask_for_add_car(
            merged_text,
            fields,
            language,
            add_car_rules,
            customer_turn_count,
            client_id,
            questioning_variant,
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
    reply_truth_context: dict[str, Any] | None = None,
    *,
    for_append: bool = False,
    prior_workflow_state: dict[str, Any] | None = None,
    v6_ocr_signals: dict[str, Any] | None = None,
    v6_auto_input_variant: str | None = None,
) -> dict[str, Any]:
    """
    Triage within a multi-turn conversation.
    Merges conversation context with latest message for triage.
    Returns handoff_ready=True when broker should receive the case.
    add_car_rules_override: optional rules for preview; when set, used instead of config.
    client_id: optional; when omitted, uses CLIENT_ID env or chen_kui for handoff phrases.
    reply_truth_context: optional structured truth for reply layer — formal_submitted_at,
        lifecycle_status (handed_off | office_followup), formal_submit_this_turn (API formal submit).
        Handoff phrasing stays pre-submit unless this context allows post-submit office-receipt language.
    prior_workflow_state: optional prior session workflow (e.g. conversion_stage) for quote-ready
        conversion progression without repeating the same announcement block each turn.
    """
    resolved_client_id = (client_id or "").strip() or get_active_client_id()
    intake_evolution_variant = get_intake_evolution_variant(resolved_client_id)
    v6_variant_eff = (v6_auto_input_variant or "").strip().upper() or get_v6_auto_input_variant(resolved_client_id)
    if v6_variant_eff not in ("A", "B", "C"):
        v6_variant_eff = "A"
    v4_bundle_early: dict[str, Any] | None = None
    _turn1_action_ready_lift = False
    truth_guardrail_debug_session_start()
    customer_turns = [t for t in conversation_turns if (t.get("role") or "").strip().lower() == "customer"]
    customer_count = len(customer_turns)

    merged_text = _build_conversation_text_for_triage(conversation_turns, latest_text)
    if not merged_text.strip():
        out_empty = {
            "issue_category": "unclear",
            "urgency": "medium",
            "broker_next_step": "Request clarification from sender.",
            "client_prep": "N/A",
            "client_reply_draft": "Could you please provide more details about your inquiry?",
            "manual_followup_needed": True,
            "handoff_ready": False,
            "conversation_summary": "",
            "triage_mode": "greenfield",
            "action_ready": False,
            "intake_flow_milestone": "collecting",
        }
        maybe_attach_truth_guardrail_debug_to_triage(out_empty)
        return out_empty

    # SALES_READINESS_HARDENING: Talk to Agent free-text detection.
    # If last customer message requests human contact, hand off immediately (any turn).
    last_customer_raw = _last_labeled_customer_content(merged_text)
    if _is_talk_to_agent_request(last_customer_raw):
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
        out_human = {
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
            "triage_mode": "greenfield",
            "action_ready": False,
            "intake_flow_milestone": "collecting",
        }
        maybe_attach_truth_guardrail_debug_to_triage(out_human)
        return out_human

    lowered_merged = (merged_text or "").lower()
    ocr_blob = ""
    if v6_ocr_signals and isinstance(v6_ocr_signals, dict):
        from services.fiqa_api.inbox_triage.ocr_case_fusion import build_supplemental_extraction_blob

        ocr_blob = build_supplemental_extraction_blob(v6_ocr_signals)
    lowered_lane = lowered_merged
    if ocr_blob:
        lowered_lane = f"{lowered_merged}\n[ocr]\n{ocr_blob.lower()}"

    is_add_car = _effective_add_car_lane_active(
        lowered_merged=lowered_lane,
        merged_text=merged_text,
        reply_truth_context=reply_truth_context,
        last_customer_raw=last_customer_raw,
        v6_ocr_signals=v6_ocr_signals if isinstance(v6_ocr_signals, dict) else None,
    )
    weak_inline_first_turn = (
        not for_append
        and customer_count == 0
        and _v6_weak_inline_image_intake(
            last_customer_raw,
            v6_ocr_signals if isinstance(v6_ocr_signals, dict) else None,
        )
    )

    merged_text_for_ocr = merged_text
    if ocr_blob:
        merged_text_for_ocr = f"{merged_text}\n\n[OCR]\n{ocr_blob}"

    merged_for_add_car_extraction = merged_text_for_ocr
    add_car_llm_slot_meta: dict[str, Any] = {"called": False, "skip_reason": "not_add_car_lane"}
    if is_add_car:
        _rf_slot = _extract_add_car_fields_truth_safe(merged_text_for_ocr)
        _invoke_slot_llm, _skip_slot = _add_car_llm_slot_should_invoke(
            _rf_slot, merged_text_for_ocr, last_customer_raw
        )
        merged_for_add_car_extraction, add_car_llm_slot_meta = maybe_augment_merged_text_for_add_car_slots(
            merged_text_for_ocr,
            last_customer_raw,
            rule_fields=_rf_slot,
            invoke_llm=_invoke_slot_llm,
            skip_reason=_skip_slot,
        )

    _follow_v4_pre = _derive_follow_up_type(last_customer_raw)
    _col_v4_pre, _still_v4_pre, _, _, _ = _compute_add_car_collected_still_lists(
        merged_for_add_car_extraction,
        last_customer_raw,
        reply_truth_context,
        _follow_v4_pre,
    )
    _tf_v4_pre = _add_car_augmented_truth_fields(
        merged_for_add_car_extraction,
        reply_truth_context,
        last_customer_raw,
        _follow_v4_pre,
    )
    _qrs_v4_pre = _add_car_quote_ready_status(_tf_v4_pre)
    # Latest customer segment for language — merged_text includes [客户] labels (Chinese chars).
    _lang_v4_pre = "zh" if _contains_chinese(last_customer_raw) else "en"

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

    # V5: turn-1 confirm-first when customer opens conversationally (e.g. 我想加车 / mixed EN facts).
    # Lift to broker handoff when quote_ready and: empty still, EN "add car" opener, or fact-dense ZH with
    # only name/phone gaps (cross-client / pilot paste — not VIN-first EN blobs).
    _turn1_qr_handoff_lift = False
    if is_add_car and customer_count + 1 == 1:
        _raw_t1 = (last_customer_raw or "").strip()
        _en_add_car_opener = bool(re.match(r"(?i)add\s*car\b", _raw_t1))
        _no_struct_still = not bool(_still_v4_pre)
        _still_lo = {str(x).lower() for x in (_still_v4_pre or [])}
        _contact_only_still = _still_lo <= {"name", "phone"} and bool(_still_lo)
        # Require punctuation after opener so "我想加车 2024 …" (dense same-line facts) can still hand off.
        _zh_conv_add_opener = bool(
            re.match(
                r"^\s*(我?想加车|我要加车|帮忙加车|想加一台车|想加一辆车|加一台车|加一辆车|我想加一台|我想加一辆)([。．，,])",
                _raw_t1,
            )
        )
        if _qrs_v4_pre == "quote_ready":
            if _no_struct_still:
                _turn1_qr_handoff_lift = True
            elif _lang_v4_pre == "en" and _en_add_car_opener:
                _turn1_qr_handoff_lift = True
            elif _contact_only_still and _lang_v4_pre == "zh" and not _zh_conv_add_opener:
                _turn1_qr_handoff_lift = True
        if _turn1_qr_handoff_lift:
            would_handoff = True
        elif _qrs_v4_pre != "quote_ready":
            would_handoff = False
    _pvc_raw = _extract_primary_add_car_vehicle_concrete(merged_for_add_car_extraction)
    _pvc_v4_pre_arg = None
    if isinstance(_pvc_raw, str) and _pvc_raw.strip():
        _pvc_v4_pre_arg = _pvc_raw.strip()
    if is_add_car:
        v4_bundle_early = build_v4_case_draft_bundle(
            merged_text=merged_for_add_car_extraction,
            collected_fields=_col_v4_pre,
            missing_fields=_still_v4_pre,
            primary_vehicle_summary=_pvc_v4_pre_arg,
            quote_ready_status=_qrs_v4_pre,
            human_confirmation_fields=[],
            issue_category=str(base_result.get("issue_category") or ""),
            language=_lang_v4_pre,
            variant=intake_evolution_variant,
            ocr_context=v6_ocr_signals if isinstance(v6_ocr_signals, dict) else None,
            v6_auto_input_variant=v6_variant_eff,
        )
        if customer_count + 1 == 1:
            # quote_ready turn 1 is owned by conversion / confirm-first flow — do not auto-handoff here.
            _turn1_action_ready_lift = _qrs_v4_pre != "quote_ready" and evaluate_action_ready_rule(
                list(v4_bundle_early.get("collected_fields") or []),
                list(v4_bundle_early.get("still_needed_fields") or []),
                merged_text=merged_for_add_car_extraction,
                primary_vehicle_summary=_pvc_v4_pre_arg,
            )
            if _turn1_action_ready_lift:
                would_handoff = True

    if is_add_car and v4_bundle_early is not None:
        if customer_count + 1 == 1:
            if _turn1_action_ready_lift:
                next_ask = ""
            else:
                next_ask = build_v4_confirmation_client_reply_from_bundle(
                    v4_bundle_early,
                    merged_text=merged_for_add_car_extraction,
                    primary_vehicle_summary=_pvc_v4_pre_arg,
                    language=_lang_v4_pre,
                    variant=intake_evolution_variant,
                )
                next_ask = _maybe_append_add_car_price_caveat(
                    merged_for_add_car_extraction,
                    next_ask or "",
                    _lang_v4_pre,
                    resolved_client_id,
                )
            # VIN present from merged extraction (incl. raw [OCR] lines) or v6 structured VIN;
            # pilot bar not met → single highest-value ask (minimal back-and-forth).
            # Raw OCR often has a 17-char VIN in last_raw_text without structured_fields.vin.
            _vin_for_slim_ask = bool(_tf_v4_pre.get("vin")) or _v6_structured_has_vin(v6_ocr_signals)
            if (
                _vin_for_slim_ask
                and _qrs_v4_pre != "quote_ready"
                and not _turn1_action_ready_lift
            ):
                _usable_t1, _, _ = evaluate_v5_case_usable(
                    v4_bundle_early,
                    merged_text=merged_for_add_car_extraction,
                    primary_vehicle_summary=_pvc_v4_pre_arg,
                    variant=intake_evolution_variant,
                )
                # Min-core / V5 usable: prefer one confirmation block over a slot chase on turn 1.
                if not _usable_t1:
                    slim = _get_next_ask_for_add_car(
                        merged_for_add_car_extraction,
                        _extract_add_car_fields_truth_safe(merged_for_add_car_extraction),
                        _lang_v4_pre,
                        add_car_rules_override,
                        customer_turn_count=customer_count + 1,
                        client_id=resolved_client_id,
                        questioning_variant=intake_evolution_variant,
                    )
                    if slim:
                        next_ask = slim
        else:
            _usable, _, _ = evaluate_v5_case_usable(
                v4_bundle_early,
                merged_text=merged_for_add_car_extraction,
                primary_vehicle_summary=_pvc_v4_pre_arg,
                variant=intake_evolution_variant,
            )
            if _usable:
                next_ask = None
            else:
                next_ask = _get_next_ask_draft(
                    merged_for_add_car_extraction,
                    base_result.get("issue_category", "unclear"),
                    base_result,
                    customer_count + 1,
                    add_car_rules_override,
                    resolved_client_id,
                    add_car_lane_active=is_add_car,
                    questioning_variant=intake_evolution_variant,
                )
    else:
        next_ask = _get_next_ask_draft(
            merged_for_add_car_extraction,
            base_result.get("issue_category", "unclear"),
            base_result,
            customer_count + 1,
            add_car_rules_override,
            resolved_client_id,
            add_car_lane_active=is_add_car,
            questioning_variant=intake_evolution_variant,
        )
    _next_lang_pre = "zh" if _contains_chinese(merged_text) else "en"
    if is_add_car and next_ask and customer_count + 1 > 1:
        _f_aug = _extract_add_car_fields_truth_safe(merged_for_add_car_extraction)
        _pvc_aug = (_extract_primary_add_car_vehicle_concrete(merged_for_add_car_extraction) or "").strip() or None
        _soft_tone = (
            _next_lang_pre == "zh"
            and bool(_f_aug.get("vin"))
            and bool(_f_aug.get("zip"))
            and (
                (bool(_f_aug.get("driver")) and not bool(_f_aug.get("delivery")))
                or (bool(_f_aug.get("delivery")) and not bool(_f_aug.get("driver")))
            )
        )
        next_ask = augment_next_ask_with_variant(
            next_ask,
            variant=intake_evolution_variant,
            language=_next_lang_pre,
            primary_vehicle_summary=_pvc_aug,
            fields=_f_aug,
            pre_quote_soft_handoff_tone=_soft_tone,
        )

    if would_handoff and next_ask and not (
        is_add_car
        and customer_count + 1 == 1
        and (_turn1_qr_handoff_lift or _turn1_action_ready_lift)
    ):
        handoff = False
        result_draft = next_ask
    else:
        handoff = would_handoff
        result_draft = base_result.get("client_reply_draft", "")
        if is_add_car and next_ask and not handoff:
            result_draft = next_ask
    if weak_inline_first_turn and not is_add_car:
        _wlang = "zh" if _contains_chinese(merged_text) else "en"
        result_draft = _weak_image_service_clarify_reply(_wlang)
        handoff = False

    _matches_gate = re.findall(r"\[客户\]\s*([^[]+)", merged_text or "")
    _last_c_gate = (_matches_gate[-1] or "").strip() if _matches_gate else (latest_text or "").strip()
    _follow_gate = _derive_follow_up_type(_last_c_gate)
    if handoff and is_add_car and v4_bundle_early is not None:
        _vu, _, _ = evaluate_v5_case_usable(
            v4_bundle_early,
            merged_text=merged_for_add_car_extraction,
            primary_vehicle_summary=_pvc_v4_pre_arg,
            variant=intake_evolution_variant,
        )
        if not _vu:
            handoff = False
        elif (
            not for_append
            and customer_count + 1 >= 2
            and _qrs_v4_pre != "quote_ready"
            and any(
                x in {str(f).lower() for f in (_still_v4_pre or [])}
                for x in ("primary_driver", "vin")
            )
            and not min_v5_case_usable_core_met(
                list(v4_bundle_early.get("collected_fields") or []),
                list(v4_bundle_early.get("still_needed_fields") or []),
                merged_text=merged_for_add_car_extraction,
                primary_vehicle_summary=_pvc_v4_pre_arg,
            )
        ):
            # Pre-quote handoff: require VIN + primary_driver unless min-core (VIN+ZIP+(delivery|driver)) is satisfied.
            handoff = False

    # PILOT_CONTRACT_ADD_CAR_V1 §4.2: from customer turn ≥4, quote_ready but name/phone still
    # missing in-thread → handoff_ready false (collecting) unless post-submit / on-record contact.
    if (
        handoff
        and is_add_car
        and not for_append
        and (customer_count + 1) >= 4
        and _qrs_v4_pre == "quote_ready"
    ):
        _gate_ctx = reply_truth_context or {}
        _post_submit_ex = bool(str(_gate_ctx.get("formal_submitted_at") or "").strip())
        _record_contact_ex = bool(
            str(_gate_ctx.get("record_contact_name") or "").strip()
            or str(_gate_ctx.get("record_contact_phone") or "").strip()
        )
        if not _post_submit_ex and not _record_contact_ex:
            _still_gate = {str(x).lower() for x in (_still_v4_pre or [])}
            if "name" in _still_gate or "phone" in _still_gate:
                handoff = False

    handoff_phrases = _get_handoff_phrases(resolved_client_id)
    stitched_cfg = _get_stitched_phrases(resolved_client_id)
    is_remove_car = _is_remove_vehicle_request(lowered_merged)
    post_submit_phrasing = _truth_allows_post_submit_handoff_phrasing(reply_truth_context)
    follow_up_type = _derive_follow_up_type(last_customer_raw)
    collection_stage = _derive_collection_stage(
        base_result.get("issue_category", "unclear"),
        merged_text,
        customer_count + 1,
        handoff,
    )
    add_car_handoff_base_key = ""
    add_car_resolved_intent: ResolvedAddCarIntent | None = None
    if is_add_car:
        add_car_handoff_base_key, add_car_resolved_intent = _resolve_add_car_handoff_phrase_key(
            last_customer_raw,
            follow_up_type,
            handoff_phrases,
            customer_count + 1,
            merged_for_add_car_extraction,
            reply_truth_context,
        )
        key = _effective_add_car_handoff_storage_key(
            add_car_handoff_base_key,
            handoff_phrases,
            post_submit_phrasing,
        )
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
    language = _detect_client_language(merged_text)
    _turn_idx = customer_count + 1
    _intent_f = (
        add_car_resolved_intent.intent_family
        if add_car_resolved_intent is not None
        else None
    )
    _rot = _post_submit_rot_idx(_turn_idx, add_car_handoff_base_key or "", _intent_f)
    # Reassure-first: when already_sent + "why still chasing", answer first then hand off
    why_still_chasing = any(
        m in last_customer_raw.lower()
        for m in ("怎么还在追", "为什么还在追", "为什么还追", "怎么还追", "why still", "why are they still")
    )
    if handoff and key == "other_received" and why_still_chasing:
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
            and (customer_count + 1) >= 2
            and bool(zh_alt or en_alt)
            and ((customer_count + 1) % 2 == 0)
        )
        _engine_post_submit_pool = bool(
            is_add_car
            and post_submit_phrasing
            and add_car_handoff_base_key
            and add_car_handoff_base_key in _POST_SUBMIT_ADD_CAR_FALLBACK_POOLS
        )
        fb_zh = _post_submit_add_car_fallback_line(
            add_car_handoff_base_key, "zh", rot_idx=_rot
        ) if _engine_post_submit_pool else None
        fb_en = _post_submit_add_car_fallback_line(
            add_car_handoff_base_key, "en", rot_idx=_rot
        ) if _engine_post_submit_pool else None
        # Engine pool beats static *_submitted pack lines (otherwise key != base_key skips pool → REPLY_REPEATED_BLOCK).
        if _engine_post_submit_pool and fb_zh:
            handoff_reply_zh = fb_zh
        else:
            handoff_reply_zh = (phrases.get("zh") or "").strip() or (
                _ADD_CAR_OFFICE_RECEIPT_PRE_FALLBACK_ZH
                if (
                    is_add_car
                    and key == "add_car_office_receipt"
                    and not post_submit_phrasing
                )
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
                _ADD_CAR_OFFICE_RECEIPT_PRE_FALLBACK_EN
                if (
                    is_add_car
                    and key == "add_car_office_receipt"
                    and not post_submit_phrasing
                )
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
        # Late-turn variety for post-submit Add-Car: alternate zh/en when pack provides zh_alt (truth-equivalent).
        use_alt_post_submit = (
            post_submit_phrasing
            and is_add_car
            and (customer_count + 1) >= 3
            and bool(zh_alt or en_alt)
            and ((customer_count + 1) % 2 == 0)
            and not _engine_post_submit_pool
        )
        if use_alt_post_submit:
            if zh_alt and language == "zh":
                handoff_reply_zh = zh_alt
            elif en_alt and language != "zh":
                handoff_reply_en = en_alt

    handoff_reply = handoff_reply_zh if language == "zh" else handoff_reply_en

    # Add-car thread, after system has spoken: "还缺什么 / 你先看看" → office review, not repeat flagship handoff
    if (
        handoff
        and is_add_car
        and follow_up_type == "clarification_question"
        and "[系统]" in (merged_text or "")
    ):
        hr_zh = _stitched_customer_visible_line_prefer(
            resolved_client_id,
            "add_car_clarification_followup",
            "add_car_clarification_followup_submitted",
            "zh",
            "收到。办公室按您已发资料逐条核对；仅在有缺项时再联系您。",
            "Got it. Our office will check what you sent line by line and only follow up if something is still missing.",
            use_post_submit=post_submit_phrasing,
            default_zh_post="收到。办公室会按当前服务记录与您已发资料继续核对；仅在有缺项时再联系您。",
            default_en_post="Got it. Our office will continue checking against your current service record and what you sent, and will follow up only if something is still missing.",
        )
        hr_en = _stitched_customer_visible_line_prefer(
            resolved_client_id,
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

    # Document clarification: when customer asks "what does garaging proof mean? what to send?"
    # after handoff, answer the question first instead of generic handoff (SIM2 fix)
    # HANDOFF_TIMING_AUDIT: Same for add-car when customer asks doc question in same turn as vehicle info
    last_customer_lower = last_customer_raw.lower() if last_customer_raw else ""
    has_doc_clarification = (
        _is_document_confusion_request(last_customer_lower)
        and any(
            m in last_customer_lower
            for m in ("garaging", "garaging proof", "停放", "declaration page", "dec page", "保单首页")
        )
    )
    if handoff and has_doc_clarification and (key == "other_clarification" or is_add_car):
        tailored = _build_client_reply_draft(merged_text, "customer_question", resolved_client_id)
        if tailored and len(tailored) > 30 and (
            "garaging" in tailored.lower() or "停放" in tailored or "declaration" in tailored.lower()
        ):
            handoff_suffix_zh = (
                _stitched_customer_visible_line_prefer(
                    resolved_client_id,
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
                else _stitched_customer_visible_line(
                    resolved_client_id,
                    "handoff_doc_clarification_suffix_other",
                    "zh",
                    "。办公室会尽快处理，有结果会联系您。",
                    ". Our office will process this and follow up with you.",
                )
            )
            handoff_suffix_en = (
                _stitched_customer_visible_line_prefer(
                    resolved_client_id,
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
                else _stitched_customer_visible_line(
                    resolved_client_id,
                    "handoff_doc_clarification_suffix_other",
                    "en",
                    "。办公室会尽快处理，有结果会联系您。",
                    ". Our office will process this and follow up with you.",
                )
            )
            handoff_suffix = handoff_suffix_zh if language == "zh" else handoff_suffix_en
            handoff_reply = tailored.rstrip("。.") + handoff_suffix

    # ADD_CAR_QUOTE_EXCELLENCE: Coverage-adjust side question in same turn — brief answer, then hand off.
    has_coverage_question = any(
        m in last_customer_lower
        for m in ("coverage 可以调", "coverage 可以调吗", "coverage 能调", "顺便 coverage", "coverage 能改", "coverage adjust")
    )
    if handoff and is_add_car and has_coverage_question:
        coverage_answer_zh = _stitched_customer_visible_line(
            resolved_client_id,
            "handoff_add_car_coverage_answer",
            "zh",
            "保额可以调整，报价时办公室会跟您确认。",
            "Coverage can be adjusted; the office will confirm options when quoting.",
        )
        coverage_answer_en = _stitched_customer_visible_line(
            resolved_client_id,
            "handoff_add_car_coverage_answer",
            "en",
            "保额可以调整，报价时办公室会跟您确认。",
            "Coverage can be adjusted; the office will confirm options when quoting.",
        )
        coverage_answer = coverage_answer_zh if language == "zh" else coverage_answer_en
        handoff_suffix_zh = _stitched_customer_visible_line_prefer(
            resolved_client_id,
            "handoff_add_car_coverage_suffix",
            "handoff_add_car_coverage_suffix_submitted",
            "zh",
            "要点已记入本条记录；正式提交办公室后，同事会在队列中核对并尽快出价，有结果会联系您。",
            "Details are on this record—after formal submit, our office will verify in the queue, price, and follow up.",
            use_post_submit=post_submit_phrasing,
            default_zh_post="要点已在办公室可见记录里；办公室会结合当前记录继续核对与报价准备，有结果会联系您。",
            default_en_post="The details are on the office-visible record; our office will continue verification and quote prep from the current record and follow up.",
        )
        handoff_suffix_en = _stitched_customer_visible_line_prefer(
            resolved_client_id,
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

    # Prospective-send question + quote-ready handoff: answer "要不要发你" style asks before office line.
    prospective_send_lead = _get_prospective_send_materials_lead(
        last_customer_raw, language, resolved_client_id
    )
    if handoff and is_add_car and prospective_send_lead:
        handoff_reply = prospective_send_lead + handoff_reply

    # ADD_CAR_COMMERCIAL_FLOW_HARDENING: Warmer handoff when customer says materials sent (发你微信了)
    add_car_materials_sent = handoff and is_add_car and follow_up_type == "already_sent" and _message_claims_completed_material_send(
        last_customer_raw
    )
    if add_car_materials_sent:
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
                handoff_reply = _stitched_customer_visible_line(
                    resolved_client_id,
                    "handoff_payment_correction_urgency",
                    "zh",
                    "您这边最要紧的是等办公室确认付款是否到账；如果确认了您这边就不用再做什么。办公室会尽快处理，有结果会联系您。",
                    "The most important thing for you now is to wait for our office to confirm whether the payment was received; if confirmed, you don't need to do anything else. Our office will process this and follow up with you.",
                )
            else:
                handoff_reply = _stitched_customer_visible_line(
                    resolved_client_id,
                    "handoff_payment_correction_urgency",
                    "en",
                    "您这边最要紧的是等办公室确认付款是否到账；如果确认了您这边就不用再做什么。办公室会尽快处理，有结果会联系您。",
                    "The most important thing for you now is to wait for our office to confirm whether the payment was received; if confirmed, you don't need to do anything else. Our office will process this and follow up with you.",
                )

    # Correction-aware add-car handoff: lead with effective vehicle when customer just corrected it.
    if (
        handoff
        and is_add_car
        and last_customer_raw
        and _is_add_car_vehicle_correction_signal(last_customer_raw)
    ):
        vc = _extract_add_car_vehicle_concrete(merged_for_add_car_extraction)
        if vc:
            if language == "zh" and "这台车继续" not in handoff_reply:
                handoff_reply = f"收到，按 {vc} 这台车继续。" + handoff_reply
            elif language != "zh" and "proceeding with the" not in handoff_reply.lower():
                handoff_reply = f"Noted—proceeding with the {vc}. " + handoff_reply

    # Truth: quote-ready / almost-ready but name or phone not on the record — do not imply contact is complete
    if handoff and is_add_car:
        _col_gap, _still_gap, _gap_name, _gap_phone = _add_car_structured_fields(merged_for_add_car_extraction)
        if last_customer_raw:
            _ltn, _ltp = _extract_contact_fields(f"[客户] {last_customer_raw.strip()}")
            if _ltn:
                _gap_name = _gap_name or _ltn
            if _ltp:
                _gap_phone = _gap_phone or _ltp
        _pcg = reply_truth_context or {}
        if str(_pcg.get("record_contact_name") or "").strip():
            _gap_name = _gap_name or "on_record"
        if str(_pcg.get("record_contact_phone") or "").strip():
            _gap_phone = _gap_phone or "on_record"
        _sg_adj = list(_still_gap)
        if _gap_name:
            _sg_adj = [x for x in _sg_adj if str(x).lower() != "name"]
        if _gap_phone:
            _sg_adj = [x for x in _sg_adj if str(x).lower() != "phone"]
        if _sg_adj and ("name" in _sg_adj or "phone" in _sg_adj):
            # Long contact-gap tails drown timeline / quote-detail / receipt questions (Role C).
            # Also lighten for materials/supplement/correction turns—main answer stays primary (outline §4.10).
            _intent_short_contact_tail = (
                add_car_resolved_intent is not None
                and add_car_resolved_intent.intent_family
                in (
                    INTENT_TIMELINE_QUESTION,
                    INTENT_QUOTE_DETAIL_QUESTION,
                    INTENT_OFFICE_RECEIPT_QUESTION,
                    INTENT_MATERIALS_CLAIM,
                    INTENT_SUPPLEMENT_INFO,
                    INTENT_CORRECTION,
                )
            )
            gap = stitched_cfg.get("handoff_add_car_contact_gap_tail")
            gap_d: dict[str, str] = gap if isinstance(gap, dict) else {}
            gap_line = (
                (gap_d.get("zh") or "").strip()
                if language == "zh"
                else (gap_d.get("en") or "").strip()
            ) or (
                " 若姓名或电话尚未在本对话中写清，办公室后续联系时可能会先确认联系方式。"
                if language == "zh"
                else " If your name or phone isn't clear on this record yet, the office may confirm contact details when they reach out."
            )
            if _intent_short_contact_tail:
                gap_line = (
                    (gap_d.get("zh_short") or "").strip()
                    if language == "zh"
                    else (gap_d.get("en_short") or "").strip()
                ) or (
                    "（若方便：请在本对话补一行姓名与电话，便于办公室联系。）"
                    if language == "zh"
                    else " (If you can, add your name and phone in one line here so the office can reach you.)"
                )
            hr = handoff_reply or ""
            _prior_contact_tails = _count_prior_system_contact_gap_tails_in_thread(merged_text, language)
            # After two prior reminders in-thread, stop appending—truth/ office summary still carry gaps (§4.10).
            if _prior_contact_tails >= 2:
                gap_line = ""
            if gap_line and gap_line.strip() not in hr:
                handoff_reply = hr.rstrip() + gap_line

    # Post-submit late turns: intent-specific opener + template body (reduces generic office-block collapse)
    if (
        handoff
        and is_add_car
        and post_submit_phrasing
        and add_car_resolved_intent is not None
    ):
        handoff_reply = _prepend_add_car_post_submit_intent_head(
            handoff_reply,
            lang=language,
            intent_family=add_car_resolved_intent.intent_family,
            variant_idx=_rot,
        )

    result = dict(base_result)
    if is_add_car and add_car_resolved_intent is not None:
        result["add_car_turn_intent"] = {
            "intent_family": add_car_resolved_intent.intent_family,
            "handoff_base_key": add_car_handoff_base_key,
            "truth_notes": list(add_car_resolved_intent.truth_notes),
            "phrase_storage_key": key,
        }
    result["handoff_ready"] = handoff
    result["follow_up_type"] = follow_up_type
    result["collection_stage"] = collection_stage
    # Phase 2: next_best_question when still collecting
    result["next_best_question"] = (result_draft or "") if not handoff else ""
    # Phase 2: lifecycle_status for triage (no case yet)
    result["lifecycle_status"] = "handoff_pending" if handoff else "collecting"
    # Same-record continuation after office-visible submit: avoid regressing to pre-submit lifecycle
    _pc_ls = reply_truth_context or {}
    if (
        is_add_car
        and not handoff
        and str(_pc_ls.get("formal_submitted_at") or "").strip()
        and _pc_ls.get("formal_submit_this_turn") is not True
    ):
        _ols = str(_pc_ls.get("lifecycle_status") or "").strip()
        if _ols in ("office_followup", "handed_off"):
            result["lifecycle_status"] = "office_followup"
    # Formal submit this request: align lifecycle with imminent office-visible persist (Add-Car).
    if (
        handoff
        and is_add_car
        and reply_truth_context
        and reply_truth_context.get("formal_submit_this_turn") is True
    ):
        result["lifecycle_status"] = "handed_off"
    # Persisted case + same-thread continuation: handoff_ready must not read as "awaiting first submit".
    elif (
        handoff
        and is_add_car
        and reply_truth_context
        and str(reply_truth_context.get("formal_submitted_at") or "").strip()
        and reply_truth_context.get("formal_submit_this_turn") is not True
    ):
        result["lifecycle_status"] = "office_followup"
    # Reassure-then-route: signal when case creation is appropriate (for UI confirmation)
    result["case_creation_suggested"] = (
        handoff
        and (
            len(result.get("collected_fields") or []) > 0
            or base_result.get("issue_category") in ("cancellation_warning", "payment_lapse_expiration", "missing_document")
        )
    )
    summary, secondary_note = _build_conversation_summary(
        merged_for_add_car_extraction, base_result, customer_count + 1
    )
    result["conversation_summary"] = summary
    if secondary_note:
        result["secondary_issue_note"] = secondary_note
    if handoff:
        result["client_reply_draft"] = handoff_reply
    else:
        result["client_reply_draft"] = result_draft

    lowered = (merged_text or "").lower()
    if is_add_car:
        collected, still_needed, merge_meta, extracted_name, extracted_phone = _compute_add_car_collected_still_lists(
            merged_for_add_car_extraction,
            last_customer_raw,
            reply_truth_context,
            follow_up_type,
        )
        result["collected_fields"] = collected
        result["still_needed_fields"] = still_needed
        if merge_meta.get("correction_turn"):
            result["add_car_merge"] = merge_meta
        result["add_car_llm_slot_layer"] = add_car_llm_slot_meta
        # ADD_CAR_REAL_INTAKE_LITE: quote_ready_status for broker visibility
        truth_fields = _add_car_augmented_truth_fields(
            merged_for_add_car_extraction,
            reply_truth_context,
            last_customer_raw,
            follow_up_type,
        )
        result["quote_ready_status"] = _add_car_quote_ready_status(truth_fields)
        # ADD_CAR_IDENTITY_CONTACT_LITE: extracted contact for case persistence
        if extracted_name:
            result["extracted_contact_name"] = extracted_name
        if extracted_phone:
            result["extracted_contact_phone"] = extracted_phone
        # Contact completion for handoff: §4.2 gate above (turn ≥4 + quote_ready + missing name/phone).
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
    # Reduce noisy "double caution" when structural quote bar is met: driver already captured
    # and broker_next_step already says to confirm — still flag VIN / payment-risk as before.
    if (
        is_add_car
        and str(result.get("quote_ready_status") or "").strip() == "quote_ready"
        and human_fields == ["primary_driver"]
    ):
        human_fields = []
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

    # Package 2.0 Loop 2: Remove-vehicle handoff — concrete broker_next_step (WORKBENCH_HANDOFF_PROFESSIONALIZATION).
    if handoff and is_remove_car:
        result["broker_next_step"] = (
            "Verify sale date and transfer status; process removal and confirm what stays covered."
        )

    # Package 2.0 Loop 2: Add-car handoff — more concrete broker_next_step when we have vehicle+zip.
    # ADD_CAR_QUOTE_EXCELLENCE: Include concrete vehicle when extractable.
    # ADD_CAR_REAL_INTAKE_LITE: Tailor confirm step — only ask for what's still missing.
    # ADD_CAR_IDENTITY_CONTACT_LITE: Mention contact when quote-ready but name/phone missing.
    # ADD_CAR_COMMERCIAL_FLOW_HARDENING: When customer says "发你微信了" / "sent" in add-car context,
    # broker_next_step must say "Verify materials received" — reduces broker rework, feels office-ready.
    if handoff and is_add_car:
        truth_fields = _add_car_augmented_truth_fields(
            merged_for_add_car_extraction,
            reply_truth_context,
            last_customer_raw,
            follow_up_type,
        )
        if _add_car_is_quote_ready(truth_fields):
            vehicle_concrete = _extract_primary_add_car_vehicle_concrete(merged_for_add_car_extraction)
            has_delivery = bool(truth_fields.get("delivery"))
            has_driver = bool(truth_fields.get("driver"))
            if has_delivery and not has_driver:
                confirm_step = "Confirm main driver with client before binding."
            elif has_driver and not has_delivery:
                confirm_step = "Confirm delivery date with client before binding."
            else:
                confirm_step = "Confirm delivery date and driver with client before binding."
            # ADD_CAR_COMMERCIAL_FLOW_HARDENING: already_sent (materials) in add-car context
            add_car_already_sent = follow_up_type == "already_sent" and _message_claims_completed_material_send(
                last_customer_raw
            )
            if add_car_already_sent:
                verify_lead = "Verify materials received via WeChat; "
                if vehicle_concrete:
                    result["broker_next_step"] = f"{verify_lead}run quote for {vehicle_concrete} when confirmed."
                else:
                    result["broker_next_step"] = f"{verify_lead}run quote for collected vehicle details when confirmed."
                collected_list = result.get("collected_fields") or []
                collected_list = list(collected_list)
                if "customer_says_sent_materials" not in collected_list:
                    collected_list.append("customer_says_sent_materials")
                result["collected_fields"] = collected_list
            else:
                if vehicle_concrete:
                    result["broker_next_step"] = f"Run quote for {vehicle_concrete}. {confirm_step}"
                else:
                    result["broker_next_step"] = (
                        f"Run quote for collected vehicle details (year, model, zip). {confirm_step}"
                    )
            # Contact hint when quote-ready but name or phone missing (unless already_sent branch)
            if not add_car_already_sent:
                collected_list = result.get("collected_fields") or []
                has_name = "name" in collected_list
                has_phone = "phone" in collected_list
                if not has_name or not has_phone:
                    contact_hint = "Confirm name and phone for follow-up."
                    result["broker_next_step"] = f"{result['broker_next_step']} {contact_hint}"
            elif add_car_already_sent:
                collected_list = result.get("collected_fields") or []
                has_name = "name" in collected_list
                has_phone = "phone" in collected_list
                if not has_name or not has_phone:
                    result["broker_next_step"] = f"{result['broker_next_step']} Confirm name and phone for follow-up."

    result["service_type"] = _derive_service_type(
        issue_category=str(base_result.get("issue_category") or ""),
        lowered_text=lowered,
        is_add_car=is_add_car,
        is_remove_car=is_remove_car,
    )
    if is_add_car:
        result["vehicle_key"] = _derive_vehicle_key_from_add_car_text(merged_for_add_car_extraction)
        cust_only = " ".join(
            re.findall(r"\[客户\]\s*([^[]+)", merged_for_add_car_extraction or "")
        ).strip()
        multi = _add_car_mentions_multiple_vehicles(cust_only)
        result["additional_vehicle_mentioned"] = multi
        pvc = (_extract_primary_add_car_vehicle_concrete(merged_for_add_car_extraction) or "").strip()
        result["primary_vehicle_summary"] = pvc if pvc else None
        result["additional_vehicle_count_hint"] = 2 if multi else None
        if multi and is_add_car:
            bns = (result.get("broker_next_step") or "").strip()
            suffix = "Multiple vehicles mentioned—confirm primary quote scope vs any second vehicle."
            if suffix not in bns:
                result["broker_next_step"] = f"{bns} {suffix}".strip() if bns else suffix
    else:
        result["vehicle_key"] = None
        result["additional_vehicle_mentioned"] = None
        result["primary_vehicle_summary"] = None
        result["additional_vehicle_count_hint"] = None

    result["triage_mode"] = "greenfield"

    from services.fiqa_api.inbox_triage.conversion_layer import maybe_apply_quote_ready_conversion_reply
    from services.fiqa_api.inbox_triage.intake_engine import run_intake_engine

    result = run_intake_engine(result, persisted=reply_truth_context)

    if is_add_car:
        maybe_apply_quote_ready_conversion_reply(
            result,
            language=language,
            client_id=resolved_client_id,
            merged_text=merged_text,
            post_submit_phrasing=post_submit_phrasing,
            customer_turn_index=customer_count + 1,
            last_customer_message=last_customer_raw,
            prior_workflow_state=prior_workflow_state,
            conversation_turns=conversation_turns,
        )
        validate_add_car_field_lists(result.get("collected_fields"), result.get("still_needed_fields"))
        if not quote_ready_matches_still_needed(
            str(result.get("quote_ready_status") or ""),
            result.get("still_needed_fields"),
        ):
            logger.warning(
                "add_car quote_ready_status vs still_needed_fields mismatch (contract check): qrs=%s still=%s",
                result.get("quote_ready_status"),
                result.get("still_needed_fields"),
            )

    # Greenfield /triage with persisted vehicle_key: mirror append vehicle boundary signals.
    # Only when a persisted vehicle scope exists — otherwise triage_for_append / office flow
    # owns boundary copy (e.g. borderline matter without VIN on file yet).
    if is_add_car:
        _ctx_pc = reply_truth_context or {}
        pv_raw = _ctx_pc.get("vehicle_key")
        persisted_vk = str(pv_raw).strip() if isinstance(pv_raw, str) and str(pv_raw).strip() else None
        if persisted_vk:
            extra_signal = bool(result.get("additional_vehicle_mentioned")) or append_turn_signals_extra_vehicle_intent(
                last_customer_raw.strip()
            )
            amb = text_suggests_vehicle_scope_ambiguity(last_customer_raw.strip())
            last_turn = last_customer_raw.strip()
            short_scope_carryover = bool(persisted_vk) and not extra_signal and not amb and (
                not _append_last_turn_carries_vehicle_identity(last_turn)
            )
            conflict = (
                "same_vehicle"
                if short_scope_carryover
                else detect_vehicle_conflict(
                    persisted_vehicle_key=persisted_vk,
                    new_vehicle_key=result.get("vehicle_key"),
                    additional_vehicle_mentioned=extra_signal,
                    message_suggests_vehicle_scope_ambiguity=amb,
                )
            )
            if conflict == "new_vehicle":
                result["case_boundary"] = "new_issue"
                result["case_boundary_action"] = "requires_new_case"
                result["append_allowed"] = False
                if not (result.get("boundary_reason") or "").strip():
                    result["boundary_reason"] = (
                        "Vehicle scope differs from this case; open a new service record for the other vehicle."
                    )
            elif conflict == "ambiguous":
                result["case_boundary"] = "borderline"
                result["case_boundary_action"] = "requires_confirmation"
                result["append_allowed"] = False
                if not (result.get("boundary_reason") or "").strip():
                    result["boundary_reason"] = (
                        "Vehicle scope is unclear on this thread; confirm with the customer before updating this record."
                    )
                hf = list(result.get("human_confirmation_fields") or [])
                if "case_topic_boundary" not in hf:
                    hf.append("case_topic_boundary")
                result["human_confirmation_fields"] = hf
                result["human_confirmation_required"] = True
            else:
                result["case_boundary"] = "same_case"
                result["case_boundary_action"] = "append_allowed"
                result["append_allowed"] = True
                result["boundary_reason"] = (
                    "No clear boundary conflict detected; continuation stays on current case."
                )

    maybe_attach_truth_guardrail_debug_to_triage(result)
    result["intake_evolution_variant"] = intake_evolution_variant
    result["v6_auto_input_variant"] = v6_variant_eff
    _lang_cd = "zh" if _contains_chinese(merged_text) else "en"
    if str(result.get("service_type") or "").strip().lower() == "add_car":
        result["case_draft"] = build_v4_case_draft_bundle(
            merged_text=merged_for_add_car_extraction,
            collected_fields=list(result.get("collected_fields") or []),
            missing_fields=list(result.get("still_needed_fields") or []),
            primary_vehicle_summary=result.get("primary_vehicle_summary"),
            quote_ready_status=str(result.get("quote_ready_status") or ""),
            human_confirmation_fields=list(result.get("human_confirmation_fields") or []),
            issue_category=str(result.get("issue_category") or ""),
            language=_lang_cd,
            variant=intake_evolution_variant,
            ocr_context=v6_ocr_signals if isinstance(v6_ocr_signals, dict) else None,
            v6_auto_input_variant=v6_variant_eff,
        )
        _cd = result["case_draft"]
        result["case_usable"] = bool(_cd.get("case_usable"))
        result["still_needed_user_flow"] = list(_cd.get("still_needed_user_flow") or [])
        result["deferred_to_broker_fields"] = list(_cd.get("deferred_to_broker_fields") or [])
        result["broker_completion"] = dict(_cd.get("broker_completion") or {})
        result["v4_error_risk_score"] = estimate_v4_error_risk_score(
            _cd,
            quote_ready_status=str(result.get("quote_ready_status") or ""),
        )
        result["v5_handoff_risk_score"] = estimate_v5_handoff_risk_score(
            _cd,
            quote_ready_status=str(result.get("quote_ready_status") or ""),
            case_usable=bool(_cd.get("case_usable")),
        )
        result["zero_question_intake"] = True
        _ar = evaluate_action_ready_rule(
            list(_cd.get("collected_fields") or []),
            list(_cd.get("still_needed_fields") or []),
            merged_text=merged_for_add_car_extraction,
            primary_vehicle_summary=result.get("primary_vehicle_summary"),
        )
        result["action_ready"] = bool(_ar)
        if _ar:
            result["intake_flow_milestone"] = "action_ready"
        elif bool(_cd.get("case_usable")):
            result["intake_flow_milestone"] = "usable"
        else:
            _coll = {str(x).lower() for x in (_cd.get("collected_fields") or []) if x}
            if "vin" in _coll and "zip" in _coll:
                result["intake_flow_milestone"] = "near_usable"
            else:
                result["intake_flow_milestone"] = "collecting"
        _qrs_fin = str(result.get("quote_ready_status") or "").strip()
        if _ar and _qrs_fin != "quote_ready":
            _auto_lang = "zh" if _contains_chinese(last_customer_raw) else "en"
            result["client_reply_draft"] = build_auto_progress_client_reply(
                _cd,
                language=_auto_lang,
                soft_vin_confirm=action_ready_vin_soft_confirmation_warranted(_cd),
            )
    else:
        result["case_draft"] = build_generic_case_draft(
            merged_text=merged_text,
            issue_category=str(result.get("issue_category") or ""),
            language=_lang_cd,
        )
        result["action_ready"] = False
        result["intake_flow_milestone"] = "collecting"
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
