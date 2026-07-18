"""
P24 — Constitution Projection.

Pure read-model layer: derives a Customer + Broker Constitution DTO from the
existing Case + Slice1 + Claim Brief + Evidence Summary + claim phase stack.

Hard rules for this module:
- No DB writes, no network, no AI.
- Does not mutate Case persistence shape or Slice1 aggregates.
- Slice1 remains the workflow authority; Constitution only translates.
- P24B: customer Today / Why / After / Trust / current_stage are live.
- P24C: broker queue / conclusion / next_action / priority / current_stage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from services.fiqa_api.inbox_triage.claim_workbench_display import (
    build_claim_case_brief,
    build_claim_evidence_summary,
    is_claim_broker_done,
)
from services.fiqa_api.wecom.claim_state import (
    CLAIM_PHASE_BROKER_DONE,
    CLAIM_PHASE_BROKER_REVIEW,
    CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
    derive_claim_phase,
)

PROJECTION_VERSION = 1

# Minimal customer-facing stage vocabulary (not a universal workflow model).
STAGE_CUSTOMER_ACTION_NEEDED = "customer_action_needed"
STAGE_WAITING_BROKER = "waiting_broker"
STAGE_WAITING = "waiting"

# Deterministic customer copy lifted from Camry One Truth / sharedMockClaim.
_TODAY_WAIT = "先不用操作"
_TODAY_INSURANCE_CARD = "上传保险卡"
_WHY_INSURANCE_CARD = "事故经过和现场照片已经完成。"
_AFTER_INSURANCE_CARD = "陈总开始审核。"
_WHY_BROKER_REVIEW = "资料已齐，陈总正在审核。"
_AFTER_WAIT_CONFIRM = "请等待确认。"
_WHY_GENERIC_ACTION = "请先完成这一步，方便我们继续处理。"
_AFTER_GENERIC_ACTION = "完成后我们会继续处理。"
_WHY_NEUTRAL_WAIT = "目前没有需要您操作的事项。"
_AFTER_NEUTRAL_WAIT = "有进展时我们会联系您。"

_TRUST_CUSTOMER_ACTION = {
    "care_line": "陈总已收到资料",
    "care_note": "如有需要，我们会联系您",
}
_TRUST_WAITING_BROKER = {
    "care_line": "下一步由陈总审核",
    "care_note": "我们会联系您（如需要）",
}

_CUSTOMER_WORK_ACTION_TYPES = frozenset({"provide_evidence", "provide_fact"})
_WAIT_BROKER_ACTION_TYPES = frozenset({"wait_for_broker_review"})
_INSURANCE_CARD_INPUTS = frozenset({"policy_or_insurance_card"})
_SLICE1_REVIEW_READY_STATES = frozenset({"broker_review_ready"})
_BROKER_HOLD_PHASES = frozenset(
    {
        CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
        CLAIM_PHASE_BROKER_REVIEW,
        CLAIM_PHASE_BROKER_DONE,
    }
)

# P21 PRIORITY_BANDS (smallest port) — lower rank = higher in queue.
BAND_BROKER_NOW = "broker_now"
BAND_CUSTOMER_DONE_AWAITING = "customer_done_awaiting"
BAND_CUSTOMER_MISSING = "customer_missing"
BAND_RECENTLY_DONE = "recently_done"
BAND_NEUTRAL = "neutral"

PRIORITY_BANDS: dict[str, dict[str, Any]] = {
    BAND_BROKER_NOW: {
        "rank": 1,
        "label": "需要你现在处理",
        "plain_reason": "轮到你处理，且不能再拖。",
    },
    BAND_CUSTOMER_DONE_AWAITING: {
        "rank": 2,
        "label": "客户已完成，等你审核",
        "plain_reason": "客户做完了该做的事，正在等你看。",
    },
    BAND_CUSTOMER_MISSING: {
        "rank": 3,
        "label": "还缺客户关键资料",
        "plain_reason": "关键资料还在客户手里，案件暂时推不动。",
    },
    BAND_RECENTLY_DONE: {
        "rank": 5,
        "label": "最近已完成",
        "plain_reason": "已办妥，留在队列底部便于回看。",
    },
    BAND_NEUTRAL: {
        "rank": 6,
        "label": "暂无优先动作",
        "plain_reason": "当前没有需要立刻处理的事项。",
    },
}

_BROKER_IDLE_LABEL = "暂无动作"
_BROKER_REVIEW_INSURANCE_CARD_LABEL = "审核保险卡"
_BROKER_REVIEW_GENERIC_LABEL = "审核客户资料"
_BROKER_IDLE_NOTE_INSURANCE = "等客户上传保险卡后再开始审核。"
_BROKER_REVIEW_NOTE_INSURANCE = "审核通过后，客户会看到你在处理。"
_BROKER_IDLE_NOTE_GENERIC = "等客户完成今天的任务后再处理。"
_BROKER_REVIEW_NOTE_GENERIC = "请先核对客户刚提交的资料。"

_EVIDENCE_SLOT_LABELS = {
    "scene_photo": "现场照片",
    "customer_damage_photo": "车损照片",
    "other_party_vehicle_photo": "对方车辆照片",
    "policy_or_insurance_card": "保险卡照片",
}


@dataclass(frozen=True)
class ConstitutionInputs:
    """Typed dependency bundle for Constitution Projection.

    Reuses existing structures; does not duplicate Case / Slice1 / brief logic.
    """

    case: Mapping[str, Any]
    slice1: Mapping[str, Any] | None = None
    brief: Mapping[str, Any] | None = None
    evidence: Mapping[str, Any] | None = None
    claim_phase: str | None = None


@dataclass(frozen=True)
class _ResolvedDeps:
    case: dict[str, Any]
    slice1: dict[str, Any] | None
    brief: dict[str, Any] | None
    evidence: dict[str, Any] | None
    claim_phase: str | None


def _as_inputs(inputs: ConstitutionInputs | Mapping[str, Any]) -> ConstitutionInputs:
    if isinstance(inputs, ConstitutionInputs):
        return inputs
    case = inputs.get("case")
    if not isinstance(case, Mapping):
        raise TypeError("build_constitution_projection requires inputs.case mapping")
    slice1 = inputs.get("slice1")
    brief = inputs.get("brief")
    evidence = inputs.get("evidence")
    claim_phase = inputs.get("claim_phase")
    return ConstitutionInputs(
        case=case,
        slice1=slice1 if isinstance(slice1, Mapping) else None,
        brief=brief if isinstance(brief, Mapping) else None,
        evidence=evidence if isinstance(evidence, Mapping) else None,
        claim_phase=str(claim_phase).strip() if claim_phase else None,
    )


def _case_id(case: Mapping[str, Any]) -> str:
    return str(case.get("case_id") or "").strip()


def _resolve_slice1(
    case: Mapping[str, Any],
    explicit: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if isinstance(explicit, Mapping):
        return dict(explicit)
    for key in ("p20_slice1_projection", "slice1_projection"):
        raw = case.get(key)
        if isinstance(raw, Mapping):
            return dict(raw)
    return None


def _resolve_brief(
    case: Mapping[str, Any],
    explicit: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if isinstance(explicit, Mapping):
        return dict(explicit)
    raw = case.get("claim_case_brief")
    if isinstance(raw, Mapping):
        return dict(raw)
    try:
        built = build_claim_case_brief(dict(case))
    except Exception:
        return None
    return built if isinstance(built, dict) else None


def _resolve_evidence(
    case: Mapping[str, Any],
    explicit: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if isinstance(explicit, Mapping):
        return dict(explicit)
    raw = case.get("claim_evidence_summary")
    if isinstance(raw, Mapping):
        return dict(raw)
    try:
        built = build_claim_evidence_summary(dict(case))
    except Exception:
        return None
    return built if isinstance(built, dict) else None


def _resolve_claim_phase(
    case: Mapping[str, Any],
    explicit: str | None,
) -> str | None:
    if explicit:
        return explicit
    for key in ("workflow_phase", "claim_phase"):
        raw = case.get(key)
        if raw:
            return str(raw).strip()
    try:
        phase = str(derive_claim_phase(case) or "").strip()
        return phase or None
    except Exception:
        return None


def _resolve_deps(inputs: ConstitutionInputs | Mapping[str, Any]) -> _ResolvedDeps:
    resolved = _as_inputs(inputs)
    case = dict(resolved.case)
    return _ResolvedDeps(
        case=case,
        slice1=_resolve_slice1(case, resolved.slice1),
        brief=_resolve_brief(case, resolved.brief),
        evidence=_resolve_evidence(case, resolved.evidence),
        claim_phase=_resolve_claim_phase(case, resolved.claim_phase),
    )


def _mapping(value: Any) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, Mapping) else None


def _slice1_customer_action(slice1: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(slice1, Mapping):
        return None
    return _mapping(slice1.get("customer_next_action"))


def _open_request_active_item(slice1: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(slice1, Mapping):
        return None
    open_request = _mapping(slice1.get("open_request"))
    if not open_request:
        return None
    return _mapping(open_request.get("active_item"))


def _action_type(action: Mapping[str, Any] | None) -> str:
    if not action:
        return ""
    return str(action.get("action_type") or "").strip().lower()


def _action_title(action: Mapping[str, Any] | None) -> str:
    if not action:
        return ""
    return str(action.get("title") or "").strip()


def _required_input(action: Mapping[str, Any] | None) -> str:
    if not action:
        return ""
    return str(action.get("required_input") or "").strip().lower()


def _workflow_state(slice1: Mapping[str, Any] | None) -> str:
    if not isinstance(slice1, Mapping):
        return ""
    return str(slice1.get("workflow_state") or "").strip().lower()


def _is_insurance_card_task(
    *,
    today: str,
    action: Mapping[str, Any] | None,
    active_item: Mapping[str, Any] | None,
) -> bool:
    if today == _TODAY_INSURANCE_CARD:
        return True
    if _required_input(action) in _INSURANCE_CARD_INPUTS:
        return True
    if isinstance(active_item, Mapping):
        item_type = str(active_item.get("item_type") or "").strip().lower()
        if item_type in _INSURANCE_CARD_INPUTS:
            return True
        label = str(active_item.get("label") or "").strip()
        if label == _TODAY_INSURANCE_CARD:
            return True
    return False


def _is_waiting_broker(deps: _ResolvedDeps, action: Mapping[str, Any] | None) -> bool:
    if _action_type(action) in _WAIT_BROKER_ACTION_TYPES:
        return True
    if _workflow_state(deps.slice1) in _SLICE1_REVIEW_READY_STATES:
        return True
    broker_action = _mapping((deps.slice1 or {}).get("broker_next_action"))
    if broker_action:
        broker_type = str(broker_action.get("action_type") or "").strip().lower()
        broker_status = str(broker_action.get("status") or "").strip().lower()
        if broker_type == "review_customer_response" or broker_status == "review_ready":
            return True
    phase = str(deps.claim_phase or "").strip().lower()
    return phase in _BROKER_HOLD_PHASES and _action_type(action) not in _CUSTOMER_WORK_ACTION_TYPES


def _customer_today(deps: _ResolvedDeps) -> str:
    """Precedence: Slice1 action → open active item → phase fallback → safe wait."""
    action = _slice1_customer_action(deps.slice1)
    action_type = _action_type(action)

    # 1. Structured Slice1 customer_next_action
    if action_type in _CUSTOMER_WORK_ACTION_TYPES:
        title = _action_title(action)
        if title:
            return title
    if action_type in _WAIT_BROKER_ACTION_TYPES:
        return _TODAY_WAIT
    if _is_waiting_broker(deps, action):
        return _TODAY_WAIT

    # 2. Open request / missing-item evidence (active item only — never queued)
    active_item = _open_request_active_item(deps.slice1)
    if isinstance(active_item, Mapping):
        status = str(active_item.get("status") or "").strip().lower()
        if status in {"", "active"}:
            label = str(active_item.get("label") or active_item.get("title") or "").strip()
            if label:
                return label

    # 3. Deterministic phase fallback — never invent a concrete task
    phase = str(deps.claim_phase or "").strip().lower()
    if phase in _BROKER_HOLD_PHASES:
        return _TODAY_WAIT

    # 4. Safe neutral fallback
    return _TODAY_WAIT


def _customer_why(deps: _ResolvedDeps, today: str) -> str:
    action = _slice1_customer_action(deps.slice1)
    active_item = _open_request_active_item(deps.slice1)
    if _is_insurance_card_task(today=today, action=action, active_item=active_item):
        return _WHY_INSURANCE_CARD
    if today == _TODAY_WAIT or _is_waiting_broker(deps, action):
        if _is_waiting_broker(deps, action):
            return _WHY_BROKER_REVIEW
        return _WHY_NEUTRAL_WAIT
    return _WHY_GENERIC_ACTION


def _customer_after(deps: _ResolvedDeps, today: str) -> str:
    action = _slice1_customer_action(deps.slice1)
    active_item = _open_request_active_item(deps.slice1)
    if _is_insurance_card_task(today=today, action=action, active_item=active_item):
        return _AFTER_INSURANCE_CARD
    if today == _TODAY_WAIT or _is_waiting_broker(deps, action):
        if _is_waiting_broker(deps, action):
            return _AFTER_WAIT_CONFIRM
        return _AFTER_NEUTRAL_WAIT
    return _AFTER_GENERIC_ACTION


def _customer_trust(_deps: _ResolvedDeps, today: str) -> dict[str, str]:
    # Quiet Human Trust: who is caring for the case while customer acts vs waits.
    if today != _TODAY_WAIT:
        return dict(_TRUST_CUSTOMER_ACTION)
    return dict(_TRUST_WAITING_BROKER)


def _customer_current_stage(deps: _ResolvedDeps, today: str) -> str:
    action = _slice1_customer_action(deps.slice1)
    if today != _TODAY_WAIT and (
        _action_type(action) in _CUSTOMER_WORK_ACTION_TYPES
        or bool(_open_request_active_item(deps.slice1))
    ):
        return STAGE_CUSTOMER_ACTION_NEEDED
    if _is_waiting_broker(deps, action):
        return STAGE_WAITING_BROKER
    return STAGE_WAITING


def _customer_projection(deps: _ResolvedDeps) -> dict[str, Any]:
    today = _customer_today(deps)
    return {
        "today": today,
        "why": _customer_why(deps, today),
        "after": _customer_after(deps, today),
        "trust": _customer_trust(deps, today),
        "current_stage": _customer_current_stage(deps, today),
    }


def _placeholder_customer() -> dict[str, Any]:
    return {
        "today": None,
        "why": None,
        "after": None,
        "trust": {
            "care_line": None,
            "care_note": None,
        },
        "current_stage": None,
    }


def _placeholder_broker(*, current_stage: str | None = None) -> dict[str, Any]:
    return {
        "queue_summary": {
            "band": None,
            "label": None,
            "why_attention": None,
        },
        "case_conclusion": {
            "what_happened": None,
            "known": [],
            "uncertain": [],
            "evidence": [],
            "customer_focus": None,
            "customer_why": None,
            "customer_after": None,
            "customer_trust": None,
        },
        "next_action": {
            "label": None,
            "action_type": None,
            "enabled": False,
            "note": None,
        },
        "priority": {
            "band": None,
            "rank": None,
        },
        "current_stage": current_stage,
    }


def _slice1_broker_action(slice1: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(slice1, Mapping):
        return None
    return _mapping(slice1.get("broker_next_action"))


def _satisfied_item_types(slice1: Mapping[str, Any] | None) -> set[str]:
    if not isinstance(slice1, Mapping):
        return set()
    open_request = _mapping(slice1.get("open_request")) or {}
    items = open_request.get("items")
    if not isinstance(items, list):
        return set()
    out: set[str] = set()
    for item in items:
        if not isinstance(item, Mapping):
            continue
        if str(item.get("status") or "").strip().lower() != "satisfied":
            continue
        item_type = str(item.get("item_type") or "").strip().lower()
        if item_type:
            out.add(item_type)
    return out


def _customer_owes_active_task(deps: _ResolvedDeps, customer: Mapping[str, Any]) -> bool:
    if str(customer.get("current_stage") or "") == STAGE_CUSTOMER_ACTION_NEEDED:
        return True
    today = str(customer.get("today") or "").strip()
    if today and today != _TODAY_WAIT:
        return True
    action = _slice1_customer_action(deps.slice1)
    return _action_type(action) in _CUSTOMER_WORK_ACTION_TYPES


def _is_review_ready(deps: _ResolvedDeps) -> bool:
    broker_action = _slice1_broker_action(deps.slice1)
    broker_type = _action_type(broker_action)
    broker_status = str((broker_action or {}).get("status") or "").strip().lower()
    if broker_type == "review_customer_response" or broker_status == "review_ready":
        return True
    if _workflow_state(deps.slice1) in _SLICE1_REVIEW_READY_STATES:
        return True
    phase = str(deps.claim_phase or "").strip().lower()
    return phase in {
        CLAIM_PHASE_INTAKE_READY_FOR_BROKER,
        CLAIM_PHASE_BROKER_REVIEW,
    }


def _is_recently_done(deps: _ResolvedDeps) -> bool:
    phase = str(deps.claim_phase or "").strip().lower()
    if phase == CLAIM_PHASE_BROKER_DONE:
        return True
    try:
        return bool(is_claim_broker_done(deps.case))
    except Exception:
        return False


def _idle_next_action(*, note: str) -> dict[str, Any]:
    return {
        "label": _BROKER_IDLE_LABEL,
        "action_type": "none",
        "enabled": False,
        "note": note,
    }


def _review_next_action(deps: _ResolvedDeps) -> dict[str, Any]:
    satisfied = _satisfied_item_types(deps.slice1)
    if "policy_or_insurance_card" in satisfied:
        return {
            "label": _BROKER_REVIEW_INSURANCE_CARD_LABEL,
            "action_type": "review_insurance_card",
            "enabled": True,
            "note": _BROKER_REVIEW_NOTE_INSURANCE,
        }
    return {
        "label": _BROKER_REVIEW_GENERIC_LABEL,
        "action_type": "review_customer_response",
        "enabled": True,
        "note": _BROKER_REVIEW_NOTE_GENERIC,
    }


def _broker_next_action(deps: _ResolvedDeps, customer: Mapping[str, Any]) -> dict[str, Any]:
    """Precedence: Slice1 broker action → review-ready → customer owes → done → idle."""
    broker_action = _slice1_broker_action(deps.slice1)
    broker_type = _action_type(broker_action)
    customer_owes = _customer_owes_active_task(deps, customer)

    # Hard rule: never enable a broker CTA while customer owns the active task.
    if customer_owes:
        note = (
            _BROKER_IDLE_NOTE_INSURANCE
            if str(customer.get("today") or "") == _TODAY_INSURANCE_CARD
            else _BROKER_IDLE_NOTE_GENERIC
        )
        return _idle_next_action(note=note)

    # 1. Structured Slice1 broker_next_action
    if broker_type == "wait_for_customer_item":
        return _idle_next_action(note=_BROKER_IDLE_NOTE_GENERIC)
    if broker_type == "review_customer_response":
        return _review_next_action(deps)
    if broker_type == "none" and str((broker_action or {}).get("status") or "") == "none":
        pass  # fall through

    # 2. Review-ready evidence / workflow state
    if _is_review_ready(deps):
        return _review_next_action(deps)

    # 3. Customer-action-needed already handled above

    # 4. Done / recently done
    if _is_recently_done(deps):
        return _idle_next_action(note="本轮已完成，可回看记录。")

    # 5. Safe neutral fallback
    return _idle_next_action(note=_BROKER_IDLE_NOTE_GENERIC)


def _priority_band(
    deps: _ResolvedDeps,
    customer: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> str:
    if _is_recently_done(deps):
        return BAND_RECENTLY_DONE
    if _customer_owes_active_task(deps, customer):
        return BAND_CUSTOMER_MISSING
    if bool(next_action.get("enabled")) or _is_review_ready(deps):
        # P21 Camry after-upload uses customer_done_awaiting (not overdue scoring).
        return BAND_CUSTOMER_DONE_AWAITING
    stage = str(customer.get("current_stage") or "")
    if stage == STAGE_WAITING_BROKER:
        return BAND_CUSTOMER_DONE_AWAITING
    return BAND_NEUTRAL


def _queue_why_attention(
    *,
    band: str,
    customer: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> str:
    today = str(customer.get("today") or "").strip()
    if band == BAND_CUSTOMER_MISSING and today == _TODAY_INSURANCE_CARD:
        return "关键保险卡还在客户手里，今天案件推不动。"
    if band == BAND_CUSTOMER_DONE_AWAITING and next_action.get("label") == _BROKER_REVIEW_INSURANCE_CARD_LABEL:
        return "客户刚完成今天的任务，正在等你开始审核。"
    meta = PRIORITY_BANDS.get(band) or PRIORITY_BANDS[BAND_NEUTRAL]
    return str(meta["plain_reason"])


def _broker_queue_summary(
    *,
    band: str,
    customer: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    meta = PRIORITY_BANDS.get(band) or PRIORITY_BANDS[BAND_NEUTRAL]
    return {
        "band": band,
        "label": str(meta["label"]),
        "why_attention": _queue_why_attention(
            band=band,
            customer=customer,
            next_action=next_action,
        ),
    }


def _broker_priority(band: str) -> dict[str, Any]:
    meta = PRIORITY_BANDS.get(band) or PRIORITY_BANDS[BAND_NEUTRAL]
    return {"band": band, "rank": int(meta["rank"])}


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            out.append(text)
    return out


def _conclusion_known(deps: _ResolvedDeps) -> list[str]:
    known: list[str] = []
    facts = deps.case.get("known_facts")
    if isinstance(facts, Mapping):
        if str(facts.get("accident_description") or "").strip():
            known.append("事故经过")
        if str(facts.get("own_vehicle_info") or "").strip():
            known.append("车牌与车辆")
    evidence = deps.evidence or {}
    received = _str_list(evidence.get("received_slots"))
    if "scene_photo" in received:
        known.append("现场照片")
    if "customer_damage_photo" in received and "车损照片" not in known:
        known.append("车损照片")
    if "policy_or_insurance_card" in _satisfied_item_types(deps.slice1):
        known.append("保险卡（待审核）")
    # De-dupe preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for item in known:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _conclusion_uncertain(deps: _ResolvedDeps) -> list[str]:
    brief = deps.brief or {}
    uncertain = _str_list(brief.get("missing_info"))
    if uncertain:
        return uncertain
    open_request = _mapping((deps.slice1 or {}).get("open_request")) or {}
    queued = open_request.get("queued_items")
    if isinstance(queued, list):
        for item in queued:
            if isinstance(item, Mapping):
                label = str(item.get("label") or "").strip()
                if label:
                    uncertain.append(label)
    return uncertain


def _conclusion_evidence(deps: _ResolvedDeps) -> list[str]:
    evidence_rows: list[str] = []
    facts = deps.case.get("known_facts")
    if isinstance(facts, Mapping) and str(facts.get("accident_description") or "").strip():
        evidence_rows.append("事故描述")
    received = _str_list((deps.evidence or {}).get("received_slots"))
    for slot in received:
        evidence_rows.append(_EVIDENCE_SLOT_LABELS.get(slot, slot))
    if "policy_or_insurance_card" in _satisfied_item_types(deps.slice1):
        evidence_rows.append("保险卡照片")
    seen: set[str] = set()
    ordered: list[str] = []
    for item in evidence_rows:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _broker_case_conclusion(
    deps: _ResolvedDeps,
    customer: Mapping[str, Any],
) -> dict[str, Any]:
    brief = deps.brief or {}
    trust = customer.get("trust") if isinstance(customer.get("trust"), Mapping) else {}
    return {
        "what_happened": str(brief.get("summary") or "").strip() or None,
        "known": _conclusion_known(deps),
        "uncertain": _conclusion_uncertain(deps),
        "evidence": _conclusion_evidence(deps),
        # One Truth mirror — never recreate customer-facing copy here.
        "customer_focus": customer.get("today"),
        "customer_why": customer.get("why"),
        "customer_after": customer.get("after"),
        "customer_trust": trust.get("care_line"),
    }


def _broker_projection(
    deps: _ResolvedDeps,
    customer: Mapping[str, Any],
) -> dict[str, Any]:
    current_stage = str(customer.get("current_stage") or STAGE_WAITING)
    next_action = _broker_next_action(deps, customer)
    band = _priority_band(deps, customer, next_action)
    return {
        "queue_summary": _broker_queue_summary(
            band=band,
            customer=customer,
            next_action=next_action,
        ),
        "case_conclusion": _broker_case_conclusion(deps, customer),
        "next_action": next_action,
        "priority": _broker_priority(band),
        "current_stage": current_stage,
    }


def _inputs_from_case(case: Mapping[str, Any]) -> ConstitutionInputs:
    slice1 = None
    for key in ("p20_slice1_projection", "slice1_projection"):
        raw = case.get(key)
        if isinstance(raw, Mapping):
            slice1 = dict(raw)
            break
    brief = case.get("claim_case_brief") if isinstance(case.get("claim_case_brief"), Mapping) else None
    evidence = (
        case.get("claim_evidence_summary")
        if isinstance(case.get("claim_evidence_summary"), Mapping)
        else None
    )
    claim_phase = None
    for key in ("workflow_phase", "claim_phase"):
        raw = case.get(key)
        if raw:
            claim_phase = str(raw).strip()
            break
    return ConstitutionInputs(
        case=case,
        slice1=slice1,
        brief=dict(brief) if brief is not None else None,
        evidence=dict(evidence) if evidence is not None else None,
        claim_phase=claim_phase,
    )


def _resolve_deps_light(inputs: ConstitutionInputs | Mapping[str, Any]) -> _ResolvedDeps:
    """List/queue path: reuse already-loaded fields only — never rebuild brief/evidence."""
    resolved = _as_inputs(inputs)
    case = dict(resolved.case)
    brief = dict(resolved.brief) if isinstance(resolved.brief, Mapping) else None
    if brief is None and isinstance(case.get("claim_case_brief"), Mapping):
        brief = dict(case["claim_case_brief"])
    evidence = dict(resolved.evidence) if isinstance(resolved.evidence, Mapping) else None
    if evidence is None and isinstance(case.get("claim_evidence_summary"), Mapping):
        evidence = dict(case["claim_evidence_summary"])
    return _ResolvedDeps(
        case=case,
        slice1=_resolve_slice1(case, resolved.slice1),
        brief=brief,
        evidence=evidence,
        claim_phase=_resolve_claim_phase(case, resolved.claim_phase),
    )


def _broker_queue_projection(
    deps: _ResolvedDeps,
    customer: Mapping[str, Any],
) -> dict[str, Any]:
    """Broker queue slice only — same rules as full broker, no case_conclusion."""
    current_stage = str(customer.get("current_stage") or STAGE_WAITING)
    next_action = _broker_next_action(deps, customer)
    band = _priority_band(deps, customer, next_action)
    return {
        "queue_summary": _broker_queue_summary(
            band=band,
            customer=customer,
            next_action=next_action,
        ),
        "next_action": next_action,
        "priority": _broker_priority(band),
        "current_stage": current_stage,
    }


def build_constitution_projection(
    inputs: ConstitutionInputs | Mapping[str, Any],
) -> dict[str, Any]:
    """Build full Constitution Projection DTO (pure; no I/O; no Case mutation)."""
    deps = _resolve_deps(inputs)

    try:
        customer = _customer_projection(deps)
    except Exception:
        customer = _placeholder_customer()

    current_stage = customer.get("current_stage") or STAGE_WAITING
    try:
        broker = _broker_projection(deps, customer)
    except Exception:
        broker = _placeholder_broker(current_stage=current_stage)

    return {
        "projection_version": PROJECTION_VERSION,
        "case_id": _case_id(deps.case),
        "current_stage": current_stage,
        "customer": customer,
        "broker": broker,
    }


def build_constitution_customer_projection(
    inputs: ConstitutionInputs | Mapping[str, Any],
) -> dict[str, Any]:
    """Customer-facing Constitution slice for H5 / Mini Program reads."""
    deps = _resolve_deps(inputs)
    try:
        customer = _customer_projection(deps)
    except Exception:
        customer = _placeholder_customer()
    current_stage = customer.get("current_stage") or STAGE_WAITING
    return {
        "projection_version": PROJECTION_VERSION,
        "case_id": _case_id(deps.case),
        "current_stage": current_stage,
        "customer": customer,
    }


def build_constitution_queue_projection(
    inputs: ConstitutionInputs | Mapping[str, Any],
) -> dict[str, Any]:
    """Lightweight broker queue Constitution for Case list (no case_conclusion).

    Uses the same customer/broker rule helpers as detail. Does not rebuild
    brief/evidence builders — only reads fields already present on the Case.
    Freshness: uses stored/list Slice1 on the Case; detail remains authoritative.
    """
    deps = _resolve_deps_light(inputs)
    try:
        customer = _customer_projection(deps)
    except Exception:
        customer = _placeholder_customer()
    current_stage = customer.get("current_stage") or STAGE_WAITING
    try:
        broker = _broker_queue_projection(deps, customer)
    except Exception:
        broker = {
            "queue_summary": {"band": None, "label": None, "why_attention": None},
            "next_action": {
                "label": None,
                "action_type": None,
                "enabled": False,
                "note": None,
            },
            "priority": {"band": None, "rank": None},
            "current_stage": current_stage,
        }
    return {
        "projection_version": PROJECTION_VERSION,
        "case_id": _case_id(deps.case),
        "current_stage": current_stage,
        "broker": broker,
    }


def attach_constitution_projection(case: dict[str, Any]) -> dict[str, Any]:
    """Additively set full case['constitution_projection']. No persistence / network."""
    if not isinstance(case, dict):
        raise TypeError("attach_constitution_projection requires a case dict")
    case["constitution_projection"] = build_constitution_projection(_inputs_from_case(case))
    return case


def attach_constitution_queue_projection(case: dict[str, Any]) -> dict[str, Any]:
    """Additively set lightweight queue constitution_projection for list rows."""
    if not isinstance(case, dict):
        raise TypeError("attach_constitution_queue_projection requires a case dict")
    case["constitution_projection"] = build_constitution_queue_projection(_inputs_from_case(case))
    return case
