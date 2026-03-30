"""
Add-Car bounded Intent Layer (Truth → Intent → Reply).

Resolves what the current customer turn is trying to do for Add-Car only.
Rule-based, reviewable categories — not a general NLU framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Named intent families (API / regression / QA)
INTENT_SUPPLEMENT_INFO = "supplement_info"
INTENT_CORRECTION = "correction"
INTENT_TIMELINE_QUESTION = "timeline_question"
INTENT_QUOTE_DETAIL_QUESTION = "quote_detail_question"
INTENT_MATERIALS_CLAIM = "materials_claim"
INTENT_OFFICE_RECEIPT_QUESTION = "office_receipt_question"
INTENT_GENERIC_FOLLOWUP = "generic_followup"


@dataclass(frozen=True)
class ResolvedAddCarIntent:
    """Explicit current-turn intent for Add-Car reply routing."""

    intent_family: str
    handoff_base_key: str
    """Key stem in handoff_phrases.json (e.g. add_car_timeline). _submitted variant chosen by truth elsewhere."""
    truth_notes: tuple[str, ...] = field(default_factory=tuple)
    """Why truth may constrain wording (observability only)."""


def _truth_allows_post_submit_language(reply_truth_context: dict[str, Any] | None) -> bool:
    if not reply_truth_context:
        return False
    if reply_truth_context.get("formal_submit_this_turn") is True:
        return True
    fsa = str(reply_truth_context.get("formal_submitted_at") or "").strip()
    if fsa:
        return True
    ls = str(reply_truth_context.get("lifecycle_status") or "").strip()
    return ls in ("handed_off", "office_followup")


def _is_coverage_adjust_side_question(last_customer_lower: str) -> bool:
    t = (last_customer_lower or "").strip().lower()
    return any(
        m in t
        for m in (
            "coverage 可以调",
            "coverage 可以调吗",
            "coverage 能调",
            "顺便 coverage",
            "coverage 能改",
            "coverage adjust",
        )
    )


def _office_receipt_question(msg: str) -> bool:
    """Customer asks whether office received / saw submission / queue — not pure 'I already sent'."""
    raw = (msg or "").strip()
    if not raw:
        return False
    s = raw.lower()

    # High-precision: receipt / visibility / submit-status checks
    markers = (
        "收到吗",
        "收到了吗",
        "有收到吗",
        "有收到",
        "看到吗",
        "看到了吗",
        "查到吗",
        "收到了没",
        "收到没有",
        "办公室收到",
        "你们收到",
        "你们那边收到",
        "材料到了吗",
        "进系统了吗",
        "进队列了吗",
        "提交了吗",
        "提交成功",
        "有没有收到",
        "能查到吗",
        "did you receive",
        "have you received",
        "got my",
        "received my",
        "received the",
        "in the queue",
        "submitted?",
    )
    if any(m in raw or m in s for m in markers):
        return True
    if "收到" in raw and ("吗" in raw or "?" in raw or "？" in raw):
        return True
    return False


def _quote_detail_question(msg: str) -> bool:
    ml = (msg or "").strip().lower()
    if not ml:
        return False
    if _is_coverage_adjust_side_question(ml):
        return False
    quote_detail_markers = (
        "deductible",
        "免赔",
        "自付额",
        "自付",
        "保额",
        "三者",
        "全险",
        "半险",
        "liability",
        "comprehensive",
        "collision",
        "coverage option",
        "coverage 有什么",
        "coverage 能选",
        "免赔额",
        "垫底费",
    )
    return any(m in ml or m in (msg or "") for m in quote_detail_markers)


def _timeline_question(msg: str) -> bool:
    """Process / timing / what happens next — distinct from office receipt check."""
    raw = (msg or "").strip()
    if not raw:
        return False
    ml = raw.lower()
    if _office_receipt_question(raw):
        return False
    timeline_markers = (
        "多久",
        "什么时候",
        "几天",
        "要等",
        "流程",
        "进度",
        "下一步",
        "几天能",
        "多久能",
        "大概多久",
        "何时",
        "how long",
        "when will",
        "how soon",
        "timeline",
        "what happens next",
        "工作日",
        "营业日",
        "排队",
    )
    return any(m in raw or m in ml for m in timeline_markers)


def nudge_append_generic_to_supplement_intent(
    resolved: ResolvedAddCarIntent,
    reply_truth_context: dict[str, Any] | None,
) -> ResolvedAddCarIntent:
    """
    POST /append-message: generic flagship `add_car` key reads pre-submit in packs; once the record
    is office-visible, route ambiguous generic follow-ups to supplement tone instead.
    """
    if not reply_truth_context or reply_truth_context.get("service_record_append") is not True:
        return resolved
    if not _truth_allows_post_submit_language(reply_truth_context):
        return resolved
    if resolved.handoff_base_key != "add_car" or resolved.intent_family != INTENT_GENERIC_FOLLOWUP:
        return resolved
    notes = list(resolved.truth_notes) + ["append_continuation_supplement_tone"]
    return ResolvedAddCarIntent(
        intent_family=INTENT_SUPPLEMENT_INFO,
        handoff_base_key="add_car_supplement",
        truth_notes=tuple(notes),
    )


def resolve_add_car_turn_intent(
    last_customer_raw: str,
    follow_up_type: str,
    customer_turn_index: int,
    reply_truth_context: dict[str, Any] | None = None,
) -> ResolvedAddCarIntent:
    """
    Resolve bounded intent + handoff phrase key for Add-Car.

    Truth is applied as *ceiling* for wording (via triage reply_truth_context + phrase selection),
    not as a second classifier — intent must not assume office receipt when truth forbids it.
    """
    msg = (last_customer_raw or "").strip()
    fut = (follow_up_type or "unknown").strip()
    notes: list[str] = []
    post = _truth_allows_post_submit_language(reply_truth_context)

    if not msg:
        return ResolvedAddCarIntent(
            intent_family=INTENT_GENERIC_FOLLOWUP,
            handoff_base_key="add_car",
            truth_notes=tuple(notes),
        )

    ml = msg.lower()

    # Coverage side-question: keep existing behavior (dedicated stitched path in triage)
    if _is_coverage_adjust_side_question(ml):
        return ResolvedAddCarIntent(
            intent_family=INTENT_QUOTE_DETAIL_QUESTION,
            handoff_base_key="add_car",
            truth_notes=("coverage_adjust_side_question",),
        )

    # 1) Correction
    if fut == "correction":
        if not post:
            notes.append("correction_pre_submit")
        return ResolvedAddCarIntent(
            intent_family=INTENT_CORRECTION,
            handoff_base_key="add_car_correction",
            truth_notes=tuple(notes),
        )

    # 2) Office receipt / submit visibility — before materials, so "我发了，你们收到了吗" → receipt
    if _office_receipt_question(msg):
        if not post:
            notes.append("office_receipt_no_formal_submit_copy_must_not_claim_office_has_record")
        return ResolvedAddCarIntent(
            intent_family=INTENT_OFFICE_RECEIPT_QUESTION,
            handoff_base_key="add_car_office_receipt",
            truth_notes=tuple(notes),
        )

    # 3) Quote detail
    if _quote_detail_question(msg):
        if reply_truth_context and (reply_truth_context.get("still_needed_fields") or []):
            notes.append("still_needed_present_quote_detail_must_not_imply_full_quote_ready")
        return ResolvedAddCarIntent(
            intent_family=INTENT_QUOTE_DETAIL_QUESTION,
            handoff_base_key="add_car_quote_detail",
            truth_notes=tuple(notes),
        )

    # 4) Timeline / process
    if _timeline_question(msg):
        return ResolvedAddCarIntent(
            intent_family=INTENT_TIMELINE_QUESTION,
            handoff_base_key="add_car_timeline",
            truth_notes=tuple(notes),
        )

    # 5) Materials sent (claim only — no primary receipt question)
    if fut == "already_sent":
        if not post:
            notes.append("materials_claim_only_customer_said_no_office_verified")
        # Late turns: prefer supplement family over flagship default to reduce template collapse
        if customer_turn_index >= 2:
            return ResolvedAddCarIntent(
                intent_family=INTENT_MATERIALS_CLAIM,
                handoff_base_key="add_car_supplement",
                truth_notes=tuple(notes),
            )
        return ResolvedAddCarIntent(
            intent_family=INTENT_MATERIALS_CLAIM,
            handoff_base_key="add_car",
            truth_notes=tuple(notes),
        )

    # 6) New info / supplement (late thread)
    if fut == "new_info":
        if customer_turn_index <= 1:
            return ResolvedAddCarIntent(
                intent_family=INTENT_GENERIC_FOLLOWUP,
                handoff_base_key="add_car",
                truth_notes=tuple(notes),
            )
        q_markers = ("?", "？", "吗", "么", "怎么", "为什么", "哪", "是否")
        if any(m in msg for m in q_markers) and len(msg) > 18:
            return ResolvedAddCarIntent(
                intent_family=INTENT_GENERIC_FOLLOWUP,
                handoff_base_key="add_car",
                truth_notes=tuple(notes),
            )
        return ResolvedAddCarIntent(
            intent_family=INTENT_SUPPLEMENT_INFO,
            handoff_base_key="add_car_supplement",
            truth_notes=tuple(notes),
        )

    return ResolvedAddCarIntent(
        intent_family=INTENT_GENERIC_FOLLOWUP,
        handoff_base_key="add_car",
        truth_notes=tuple(notes),
    )
