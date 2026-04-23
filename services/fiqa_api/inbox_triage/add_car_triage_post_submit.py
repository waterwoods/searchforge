"""
Add-car post-submit customer copy and light policy helpers.

Bounded default lines when client packs omit *_submitted keys; intent-specific openers after
formal submit. Engine classification and handoff assembly stay in triage.py.
"""

from __future__ import annotations

import hashlib
from typing import Any

from services.fiqa_api.inbox_triage.add_car_intent import (
    INTENT_CORRECTION,
    INTENT_GENERIC_FOLLOWUP,
    INTENT_MATERIALS_CLAIM,
    INTENT_OFFICE_RECEIPT_QUESTION,
    INTENT_QUOTE_DETAIL_QUESTION,
    INTENT_SUPPLEMENT_INFO,
    INTENT_TIMELINE_QUESTION,
)

# When pack omits *_submitted keys, keep post-submit replies truthful (bounded defaults, Add-Car only).
# Multiple variants per key reduce late-turn identical stems (REPLY_REPEATED_BLOCK) while staying truth-equivalent.
POST_SUBMIT_ADD_CAR_FALLBACK_POOLS: dict[str, list[tuple[str, str]]] = {
    "add_car": [
        (
            "这条记录已正式送达办公室；办公室会按当前记录继续核对与处理。",
            "This record has been formally delivered to our office; our team will verify and continue from the current details.",
        ),
        (
            "办公室已收到本条正式提交；后续核对与联系会以当前服务记录为准。",
            "Your formal submission is on file with our office; verification and follow-up will use your current service record.",
        ),
        (
            "同事已能在队列里看到本条正式提交；后续以当前记录为准继续处理。",
            "Your formal submission is visible in the office queue; next steps follow from your current service record.",
        ),
    ],
    "add_car_supplement": [
        (
            "已把这次补充记到当前服务记录里；办公室会按更新后的记录继续处理。",
            "I've added this update to your current service record; our office will continue from the updated details.",
        ),
        (
            "补充已写入同一条服务记录；办公室会按最新内容继续跟进。",
            "Your update is saved on the same service record; our office will continue from the latest details.",
        ),
    ],
    "add_car_timeline": [
        (
            "这条记录已在办公室处理中；后续时间以办公室核对与排队进度为准。",
            "This record is already with our office; timing depends on their verification queue.",
        ),
        (
            "进度与排队以办公室实际处理为准；有节点变化会联系您。",
            "Timing follows the office queue and verification steps; we will reach out when there is a meaningful update.",
        ),
        (
            "具体节点要看办公室核对顺序；有能对外说的进展会主动联系您。",
            "Exact timing follows the office verification order; we will reach out when there is a shareable update.",
        ),
        (
            "办公室侧会按队列核对；若出现可同步给您的节点，会主动联系。",
            "Our office verifies in queue order; we will reach out when there is a customer-visible milestone.",
        ),
        (
            "当前阶段以记录核对与排队为准；不建议用聊天承诺具体日期。",
            "At this stage timing follows verification and queue load; we avoid promising a fixed date in chat.",
        ),
    ],
    "add_car_quote_detail": [
        (
            "这类具体选项会结合当前记录继续核对；你的关注点已附到这条记录里，便于后续处理。",
            "Specific options will be confirmed against your current record; we've attached your note to this record for the next steps.",
        ),
        (
            "条款/额度类细节要办公室结合记录核对后才能定；你的问题已记在记录里便于报价时对照。",
            "Coverage and limit details must be confirmed against your record by our office; your question is noted for quoting.",
        ),
        (
            "免赔/保额组合要以核保与记录为准；你的偏好已记在案，便于同事对照。",
            "Deductible/limit combinations depend on underwriting and your record; your preferences are noted for the team.",
        ),
        (
            "比价时看到的数字往往不含全部条件；最终以办公室核对后的方案为准，你的问题已记在案。",
            "Quoted numbers you see online may omit conditions; final options follow office verification—your note is on the record.",
        ),
        (
            "这类取舍需要结合车辆与驾驶信息核对；你的关注点已写入记录，报价时会一并考虑。",
            "These tradeoffs need vehicle and driver context; your points are on the record for quoting.",
        ),
    ],
    "add_car_correction": [
        (
            "已按你这次的最新说法更新当前记录；办公室会按更新后的信息继续核对。",
            "We've updated the current record to match your latest message; our office will verify using the updated information.",
        ),
        (
            "已按你最新一条更正记录内容；办公室后续核对会以更新后的信息为准。",
            "Your latest correction is reflected on the record; verification will use the updated details.",
        ),
    ],
    "add_car_office_receipt": [
        (
            "这条记录已在办公室侧排队处理中；是否已送达以系统「正式提交办公室」为准，办公室会按队列核对并联系您。",
            "This record is in the office-side queue; delivery to the team follows formal submit—our office will verify in the queue and follow up.",
        ),
        (
            "若已点「正式提交办公室」，同事会在队列里按记录处理；入口提交状态可作为是否送达的参考。",
            "If you completed formal submit, our team processes it in the queue; use the portal submit status as the visibility check.",
        ),
    ],
}

# Pre-submit office-receipt intent: pack may omit add_car_office_receipt; never claim office already has
# the record without formal submit.
ADD_CAR_OFFICE_RECEIPT_PRE_FALLBACK_ZH = (
    "若您关心办公室是否已看到本条记录：请先在入口完成「正式提交办公室」。提交后同事才会在处理队列里接收并核对；"
    "若尚未提交，我们无法代替办公室确认“已收到”。"
)
ADD_CAR_OFFICE_RECEIPT_PRE_FALLBACK_EN = (
    "If you are asking whether the office can see this record: please complete formal submit in the portal first—that is when "
    "our office can receive it in the queue. If you have not submitted yet, we cannot confirm office receipt."
)


def post_submit_rot_idx(turn: int, base_key: str, intent_family: str | None) -> int:
    """Spread pool / opener rotation so late-thread turns rarely align on the same slot."""
    h = int(hashlib.md5(f"{base_key}|{intent_family or ''}".encode()).hexdigest()[:8], 16)
    return turn * 7 + h


def post_submit_add_car_fallback_line(base_key: str, lang: str, *, rot_idx: int = 0) -> str | None:
    pool = POST_SUBMIT_ADD_CAR_FALLBACK_POOLS.get(base_key)
    if not pool:
        return None
    pair = pool[rot_idx % len(pool)]
    return pair[0] if lang == "zh" else pair[1]


# Late-turn post-submit: short intent-specific openers (rotate so long threads don't share one 96-char stem).
ADD_CAR_POST_SUBMIT_INTENT_HEADS: dict[str, list[tuple[str, str]]] = {
    INTENT_TIMELINE_QUESTION: [
        ("关于时间安排与进度：", "On timing and next steps—"),
        ("进度与排队：", "On queue timing—"),
        ("后续联络节奏：", "On follow-up cadence—"),
    ],
    INTENT_QUOTE_DETAIL_QUESTION: [
        ("关于保额、免赔或条款细节：", "On coverage limits and deductible details—"),
        ("关于比价/条款取舍：", "On tradeoffs and coverage options—"),
        ("关于自付额与保额组合：", "On deductible and limit combinations—"),
    ],
    INTENT_OFFICE_RECEIPT_QUESTION: [
        ("关于办公室是否已能看到本条记录：", "On whether the office can see this record yet—"),
        ("关于入口提交状态：", "On portal submit status—"),
        ("关于是否已进办公室队列：", "On whether this is in the office queue—"),
    ],
    INTENT_MATERIALS_CLAIM: [
        ("关于你提到的资料发送情况：", "On what you mentioned sending—"),
        ("关于材料与发送渠道：", "On materials and how you sent them—"),
    ],
    INTENT_SUPPLEMENT_INFO: [
        ("收到你补充的信息。", "Thanks for the additional detail—"),
        ("补充已看到。", "Thanks for the update—"),
    ],
    INTENT_CORRECTION: [
        ("已记录你希望更正的内容。", "Noted your correction—"),
        ("按你最新一条更新理解。", "Interpreting from your latest message—"),
    ],
}


def prepend_add_car_post_submit_intent_head(
    reply: str,
    *,
    lang: str,
    intent_family: str,
    variant_idx: int = 0,
) -> str:
    body = (reply or "").strip()
    if not body:
        return body
    if intent_family == INTENT_GENERIC_FOLLOWUP:
        return body
    variants = ADD_CAR_POST_SUBMIT_INTENT_HEADS.get(intent_family)
    if not variants:
        return body
    pair = variants[variant_idx % len(variants)]
    head = pair[0] if lang == "zh" else pair[1]
    if not head:
        return body
    if lang == "zh":
        prefix = head[: min(6, len(head))]
        if prefix and body.startswith(prefix):
            return body
        return head + body
    hl = head.rstrip("—").strip()
    if hl and body.lower().startswith(hl.lower()[: min(10, len(hl))].lower()):
        return body
    if head.endswith("—"):
        return f"{head}{body}"
    return f"{head} {body}"


def truth_allows_post_submit_handoff_phrasing(reply_truth_context: dict[str, Any] | None) -> bool:
    """
    True when customer-facing copy may use office-receipt / in-queue language for Add-Car.
    Requires formal office-visible time, persisted post-submit lifecycle, or this request's formal submit.
    Never inferred from handoff_ready alone (two-layer standard).
    """
    if not reply_truth_context:
        return False
    if reply_truth_context.get("formal_submit_this_turn") is True:
        return True
    fsa = str(reply_truth_context.get("formal_submitted_at") or "").strip()
    if fsa:
        return True
    ls = str(reply_truth_context.get("lifecycle_status") or "").strip()
    return ls in ("handed_off", "office_followup")


def effective_add_car_handoff_storage_key(
    base_key: str,
    handoff_phrases: dict[str, dict[str, str]],
    post_submit: bool,
) -> str:
    """Prefer handoff.add_car_*_submitted when post-submit truth holds and pack provides it."""
    if not post_submit:
        return base_key
    alt = f"{base_key}_submitted"
    if handoff_phrases.get(alt):
        return alt
    return base_key
