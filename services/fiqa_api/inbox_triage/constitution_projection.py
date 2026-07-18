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
from services.fiqa_api.inbox_triage.default_intake_plan import (
    TASK_SOURCE_BROKER_REQUESTED,
    TASK_SOURCE_SYSTEM_DEFAULT,
    default_intake_plan_for_case,
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

# P26A — Customer Task Home cards (projection only; Slice1 remains workflow authority).
TASK_STATE_PENDING = "pending"
TASK_STATE_IN_PROGRESS = "in_progress"
TASK_STATE_COMPLETED = "completed"
TASK_STATE_WAITING_BROKER = "waiting_broker"
TASK_STATE_BLOCKED = "blocked"

TASK_ID_INSURANCE = "insurance_card"
TASK_ID_PHOTOS = "accident_photos"
TASK_ID_STORY = "accident_story"
TASK_ID_DRIVER_LICENSE = "driver_license"

_ROUTE_REQUEST_ITEM = "request_item"
_ROUTE_PHOTOS = "photos"
_ROUTE_STORY = "story"

_PHOTO_SLOTS = frozenset(
    {"scene_photo", "customer_damage_photo", "other_party_vehicle_photo"}
)
_DRIVER_LICENSE_LABELS = frozenset({"驾驶证", "驾驶员信息", "驾照"})
_DRIVER_LICENSE_TYPES = frozenset({"driver_license", "drivers_license"})

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


def _case_has_live_photo_evidence(case: Mapping[str, Any]) -> bool:
    """True when Case carries attachment/slot rows that must beat a stale summary cache."""
    slots = case.get("claim_attachment_slots")
    if isinstance(slots, Mapping) and slots:
        return True
    for att in case.get("case_attachments") or []:
        if not isinstance(att, Mapping):
            continue
        source = str(att.get("source") or "").strip().lower()
        if source not in {"h5_task", "wecom", "broker_upload", "claim_h5"}:
            continue
        mime = str(att.get("mime_type") or "").lower()
        msgtype = str(att.get("msgtype") or "").lower()
        if mime.startswith("image/") or msgtype == "image":
            return True
    return False


def _resolve_evidence(
    case: Mapping[str, Any],
    explicit: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Resolve evidence for Constitution.

    When the Case has live photo attachments/slots, always rebuild from those
    rows so Task Home cannot stay on a stale claim_evidence_summary cache
    (P26F One Truth). Seeded summary is used only when no live signal exists.
    """
    stored = dict(explicit) if isinstance(explicit, Mapping) else None
    if stored is None and isinstance(case.get("claim_evidence_summary"), Mapping):
        stored = dict(case["claim_evidence_summary"])

    built: dict[str, Any] | None = None
    try:
        raw_built = build_claim_evidence_summary(dict(case))
        if isinstance(raw_built, dict):
            built = raw_built
    except Exception:
        built = None

    if built is not None and _case_has_live_photo_evidence(case):
        return built
    if stored is not None:
        return stored
    return built


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


def _insurance_satisfied_from_evidence(deps: _ResolvedDeps) -> bool:
    """True when canonical insurance evidence exists without a Slice1 row."""
    if "policy_or_insurance_card" in _received_slots(deps):
        return True
    slots = deps.case.get("claim_attachment_slots")
    if isinstance(slots, Mapping):
        row = slots.get("policy_or_insurance_card")
        if isinstance(row, Mapping) and str(row.get("status") or "").strip().lower() == "received":
            return True
    for att in deps.case.get("case_attachments") or []:
        if not isinstance(att, Mapping):
            continue
        for key in ("slot_assignment", "claim_slot", "evidence_category", "document_type"):
            if str(att.get(key) or "").strip().lower() in _INSURANCE_CARD_INPUTS | {
                "insurance_card",
                "insurance_card_photo",
            }:
                status = str(att.get("evidence_status") or "confirmed").strip().lower()
                if status in {"", "confirmed", "uploaded", "received"}:
                    return True
    return False


def _insurance_satisfied(deps: _ResolvedDeps) -> bool:
    if "policy_or_insurance_card" in _satisfied_item_types(deps.slice1):
        return True
    return _insurance_satisfied_from_evidence(deps)


def _has_incomplete_default_intake(deps: _ResolvedDeps) -> bool:
    """True when required system_default intake remains (not optional photos).

    Optional photos stay available on Task Home but must not block
    waiting_broker after required defaults (story + insurance) are done.
    """
    if not _has_accident_story(deps):
        return True
    if not _insurance_satisfied(deps):
        return True
    return False


def _default_today_title(deps: _ResolvedDeps) -> str | None:
    """First incomplete default-plan task title. None when required defaults done.

    Order: story → insurance → optional photos (only when nothing required remains
    and photos are still open — keeps motion without blocking broker wait).
    """
    if not _has_accident_story(deps):
        return "填写事故经过"
    if not _insurance_satisfied(deps):
        return _TODAY_INSURANCE_CARD
    photo_completed, photo_total, any_photo = _photo_progress(deps)
    if photo_completed < photo_total or not any_photo:
        # Optional: surface only when not already in a broker-hold wait path.
        action = _slice1_customer_action(deps.slice1)
        if _action_type(action) in _WAIT_BROKER_ACTION_TYPES:
            return None
        if _workflow_state(deps.slice1) in _SLICE1_REVIEW_READY_STATES:
            return None
        return "补充照片"
    return None


def _is_waiting_broker(deps: _ResolvedDeps, action: Mapping[str, Any] | None) -> bool:
    # P26G: default intake incompleteness must never collapse to "waiting broker".
    if _has_incomplete_default_intake(deps):
        return False
    if _action_type(action) in _CUSTOMER_WORK_ACTION_TYPES:
        return False
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
    return phase in _BROKER_HOLD_PHASES


def _customer_today(deps: _ResolvedDeps) -> str:
    """Precedence: Slice1 action → open active item → default intake → phase wait."""
    action = _slice1_customer_action(deps.slice1)
    action_type = _action_type(action)

    # 1. Structured Slice1 customer_next_action (broker follow-up)
    if action_type in _CUSTOMER_WORK_ACTION_TYPES:
        title = _action_title(action)
        if title:
            return title

    # 2. Open request / missing-item evidence (active item only — never queued)
    active_item = _open_request_active_item(deps.slice1)
    if isinstance(active_item, Mapping):
        status = str(active_item.get("status") or "").strip().lower()
        if status in {"", "active"}:
            label = str(active_item.get("label") or active_item.get("title") or "").strip()
            if label:
                return label

    # 3. P26G — system_default intake plan (no broker request required)
    default_today = _default_today_title(deps)
    if default_today:
        return default_today

    if action_type in _WAIT_BROKER_ACTION_TYPES:
        return _TODAY_WAIT
    if _is_waiting_broker(deps, action):
        return _TODAY_WAIT

    # 4. Deterministic phase fallback
    phase = str(deps.claim_phase or "").strip().lower()
    if phase in _BROKER_HOLD_PHASES:
        return _TODAY_WAIT

    # 5. Safe neutral fallback
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
        or _has_incomplete_default_intake(deps)
    ):
        return STAGE_CUSTOMER_ACTION_NEEDED
    if _is_waiting_broker(deps, action):
        return STAGE_WAITING_BROKER
    return STAGE_WAITING


def _open_request_items(slice1: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(slice1, Mapping):
        return []
    open_request = _mapping(slice1.get("open_request")) or {}
    items = open_request.get("items")
    if isinstance(items, list) and items:
        return [dict(item) for item in items if isinstance(item, Mapping)]
    out: list[dict[str, Any]] = []
    active = _mapping(open_request.get("active_item"))
    if active:
        out.append(dict(active))
    queued = open_request.get("queued_items")
    if isinstance(queued, list):
        for item in queued:
            if isinstance(item, Mapping):
                out.append(dict(item))
    return out


def _received_slots(deps: _ResolvedDeps) -> set[str]:
    return {s.lower() for s in _str_list((deps.evidence or {}).get("received_slots"))}


def _has_accident_story(deps: _ResolvedDeps) -> bool:
    facts = deps.case.get("known_facts")
    if not isinstance(facts, Mapping):
        return False
    return bool(str(facts.get("accident_description") or "").strip())


def _photo_progress(deps: _ResolvedDeps) -> tuple[int, int, bool]:
    """Return (completed, total, any_received) from evidence slots — no new upload service."""
    received = _received_slots(deps)
    photo_received = sorted(slot for slot in received if slot in _PHOTO_SLOTS)
    completed = len(photo_received)
    # Skeleton total: at least scene; prefer observed required missing when present.
    missing = {
        s.lower()
        for s in _str_list((deps.evidence or {}).get("missing_required_slots"))
        if s.lower() in _PHOTO_SLOTS
    }
    total = max(completed + len(missing), 1 if completed or missing else 1)
    if completed == 0 and not missing:
        # No photo signal yet — still expose the card as one pending unit.
        total = 1
    return completed, total, completed > 0


def _item_looks_driver_license(item: Mapping[str, Any]) -> bool:
    item_type = str(item.get("item_type") or "").strip().lower()
    if item_type in _DRIVER_LICENSE_TYPES:
        return True
    label = str(item.get("label") or item.get("title") or "").strip()
    return label in _DRIVER_LICENSE_LABELS


def _driver_license_open(deps: _ResolvedDeps) -> dict[str, Any] | None:
    """Return open DL item when production path is unfinished; else None (card omitted)."""
    for item in _open_request_items(deps.slice1):
        if not _item_looks_driver_license(item):
            continue
        status = str(item.get("status") or "").strip().lower()
        if status in {"satisfied", "withdrawn", "superseded"}:
            continue
        return item
    # Brief missing_info may still list 驾驶证 before Slice1 item materializes.
    brief = deps.brief or {}
    for label in _str_list(brief.get("missing_info")):
        if label in _DRIVER_LICENSE_LABELS:
            return {"label": label, "status": "queued", "item_type": "driver_license"}
    return None


def _task_card(
    *,
    task_id: str,
    title: str,
    state: str,
    completed: int,
    total: int,
    is_today: bool,
    route: str | None,
    actionable: bool,
    primary_action: str | None = None,
    task_source: str = TASK_SOURCE_SYSTEM_DEFAULT,
    reason: str | None = None,
) -> dict[str, Any]:
    card: dict[str, Any] = {
        "task_id": task_id,
        "title": title,
        "state": state,
        "progress": {
            "completed": max(0, int(completed)),
            "total": max(1, int(total)),
        },
        "is_today": bool(is_today),
        "route": route,
        "actionable": bool(actionable),
        "primary_action": primary_action,
        "task_source": task_source,
    }
    if reason:
        card["reason"] = reason
    return card


def _broker_insurance_open(deps: _ResolvedDeps, *, today: str) -> bool:
    """True only when Slice1 / open request owns insurance — not Today title alone."""
    _ = today  # Today text is not a broker-source signal (P26G).
    action = _slice1_customer_action(deps.slice1)
    if _required_input(action) in _INSURANCE_CARD_INPUTS:
        return True
    active_item = _open_request_active_item(deps.slice1)
    if isinstance(active_item, Mapping):
        item_type = str(active_item.get("item_type") or "").strip().lower()
        if item_type in _INSURANCE_CARD_INPUTS:
            return True
        label = str(active_item.get("label") or "").strip()
        if label in {_TODAY_INSURANCE_CARD, "保险卡"}:
            return True
    for item in _open_request_items(deps.slice1):
        item_type = str(item.get("item_type") or "").strip().lower()
        if item_type in _INSURANCE_CARD_INPUTS:
            return True
        label = str(item.get("label") or "").strip()
        if label in {_TODAY_INSURANCE_CARD, "保险卡"}:
            return True
    return "policy_or_insurance_card" in {
        s.lower() for s in _str_list((deps.evidence or {}).get("missing_required_slots"))
    }


def _has_open_insurance_path(deps: _ResolvedDeps, *, today: str) -> bool:
    """Insurance is open via broker request OR system_default plan (P26G)."""
    if _broker_insurance_open(deps, today=today):
        return True
    # Default intake: never require a broker request row to unlock insurance.
    return not _insurance_satisfied(deps)


def _insurance_task_source(deps: _ResolvedDeps, *, today: str) -> str:
    if _broker_insurance_open(deps, today=today):
        return TASK_SOURCE_BROKER_REQUESTED
    return TASK_SOURCE_SYSTEM_DEFAULT


def _insurance_task_state(
    deps: _ResolvedDeps,
    *,
    today: str,
    stage: str,
    is_today: bool,
) -> tuple[str, bool]:
    satisfied = _insurance_satisfied(deps)
    if satisfied:
        if stage == STAGE_WAITING_BROKER or _is_waiting_broker(
            deps, _slice1_customer_action(deps.slice1)
        ):
            return TASK_STATE_WAITING_BROKER, False
        if _is_recently_done(deps):
            return TASK_STATE_COMPLETED, False
        return TASK_STATE_COMPLETED, False
    open_path = _has_open_insurance_path(deps, today=today)
    if is_today or _is_insurance_card_task(
        today=today,
        action=_slice1_customer_action(deps.slice1),
        active_item=_open_request_active_item(deps.slice1),
    ):
        return TASK_STATE_IN_PROGRESS, open_path
    return TASK_STATE_PENDING, open_path


def _customer_tasks(deps: _ResolvedDeps, customer: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Derive visible Task Cards from Case + Slice1 + Evidence (Constitution read-model).

    Hard rules:
    - No hard-coded page list on the client — this list is the authority.
    - Insurance uses existing Slice1 / request_item path.
    - Photos use existing upload slots only.
    - Story is a task entry (voice/AI later).
    - Driver License appears only while its production path is unfinished.
    """
    today = str(customer.get("today") or "").strip()
    stage = str(customer.get("current_stage") or "").strip()
    action = _slice1_customer_action(deps.slice1)
    active_item = _open_request_active_item(deps.slice1)
    insurance_is_today = _is_insurance_card_task(
        today=today, action=action, active_item=active_item
    )

    tasks: list[dict[str, Any]] = []
    # Bind default plan SSOT so Task Home never invents a parallel checklist.
    _ = default_intake_plan_for_case(deps.case)
    insurance_source = _insurance_task_source(deps, today=today)

    # 1) Insurance Card — system_default or broker_requested (never broker-gated for default)
    insurance_state, insurance_actionable = _insurance_task_state(
        deps, today=today, stage=stage, is_today=insurance_is_today
    )
    insurance_done = insurance_state in {
        TASK_STATE_COMPLETED,
        TASK_STATE_WAITING_BROKER,
    }
    insurance_reason = None
    if insurance_source == TASK_SOURCE_BROKER_REQUESTED and not insurance_done:
        action = _slice1_customer_action(deps.slice1)
        insurance_reason = str(
            (action or {}).get("instructions")
            or (action or {}).get("title")
            or "陈总需要保险卡"
        ).strip() or None
    tasks.append(
        _task_card(
            task_id=TASK_ID_INSURANCE,
            title="保险卡",
            state=insurance_state,
            completed=1 if insurance_done else 0,
            total=1,
            is_today=insurance_is_today and not insurance_done,
            route=_ROUTE_REQUEST_ITEM if insurance_actionable else None,
            actionable=insurance_actionable,
            primary_action="上传保险卡" if insurance_actionable else None,
            task_source=insurance_source,
            reason=insurance_reason,
        )
    )

    # 2) Accident Photos — existing upload capability only
    photo_completed, photo_total, any_photo = _photo_progress(deps)
    if insurance_is_today:
        # One Truth with Why (_WHY_INSURANCE_CARD): do not compete with Today Focus.
        photo_state = TASK_STATE_COMPLETED
        photo_actionable = False
        photo_is_today = False
        if not any_photo:
            photo_completed, photo_total = 1, 1
    elif any_photo and photo_completed >= photo_total:
        photo_state = TASK_STATE_COMPLETED
        photo_actionable = False
        photo_is_today = False
    elif today in {"补充车辆照片", "上传现场照片", "补充照片"} or (
        _required_input(action) == "photo_evidence"
    ):
        photo_state = TASK_STATE_IN_PROGRESS
        photo_actionable = True
        photo_is_today = True
    elif any_photo:
        photo_state = TASK_STATE_IN_PROGRESS if photo_completed < photo_total else TASK_STATE_COMPLETED
        photo_actionable = photo_state != TASK_STATE_COMPLETED
        photo_is_today = False
    else:
        photo_state = TASK_STATE_PENDING
        photo_actionable = True
        photo_is_today = False
    photo_source = (
        TASK_SOURCE_BROKER_REQUESTED
        if _required_input(action) == "photo_evidence"
        else TASK_SOURCE_SYSTEM_DEFAULT
    )
    tasks.append(
        _task_card(
            task_id=TASK_ID_PHOTOS,
            title="事故照片",
            state=photo_state,
            completed=photo_completed,
            total=photo_total,
            is_today=photo_is_today,
            route=_ROUTE_PHOTOS if photo_actionable else None,
            actionable=photo_actionable,
            primary_action="补充照片" if photo_actionable else None,
            task_source=photo_source,
        )
    )

    # 3) Accident Story — task entry + placeholder for future voice/AI
    story_done = _has_accident_story(deps)
    if story_done or insurance_is_today:
        # One Truth: insurance Today implies story already finished for Focus/Why.
        story_state = TASK_STATE_COMPLETED
        story_actionable = False
        story_is_today = False
    elif today in {"填写事故经过", "补充事故经过", "事故经过"}:
        story_state = TASK_STATE_IN_PROGRESS
        story_actionable = True
        story_is_today = True
    else:
        story_state = TASK_STATE_PENDING
        story_actionable = True
        story_is_today = False
    tasks.append(
        _task_card(
            task_id=TASK_ID_STORY,
            title="事故经过",
            state=story_state,
            completed=1 if story_done else 0,
            total=1,
            is_today=story_is_today,
            route=_ROUTE_STORY if story_actionable else None,
            actionable=story_actionable,
            primary_action="填写事故经过" if story_actionable else None,
            task_source=TASK_SOURCE_SYSTEM_DEFAULT,
        )
    )

    # 4) Driver License — only while unfinished (no permanent stub card)
    dl_item = _driver_license_open(deps)
    if dl_item is not None:
        dl_status = str(dl_item.get("status") or "").strip().lower()
        dl_is_active = dl_status == "active" or (
            today in _DRIVER_LICENSE_LABELS
            or today in {"确认驾驶员", "上传驾驶证"}
        )
        if dl_is_active and insurance_is_today:
            # One Truth: today's Focus stays insurance; DL waits behind it.
            dl_state = TASK_STATE_BLOCKED
            dl_actionable = False
            dl_is_today = False
        elif dl_is_active:
            dl_state = TASK_STATE_IN_PROGRESS
            dl_actionable = False  # production path not finished — card only
            dl_is_today = True
        else:
            dl_state = TASK_STATE_BLOCKED if insurance_is_today else TASK_STATE_PENDING
            dl_actionable = False
            dl_is_today = False
        tasks.append(
            _task_card(
                task_id=TASK_ID_DRIVER_LICENSE,
                title="驾驶证",
                state=dl_state,
                completed=0,
                total=1,
                is_today=dl_is_today,
                route=None,
                actionable=dl_actionable,
                primary_action=None,
                task_source=TASK_SOURCE_BROKER_REQUESTED,
                reason="陈总需要驾驶证",
            )
        )

    # Ensure exactly one is_today when customer owes work.
    if stage == STAGE_CUSTOMER_ACTION_NEEDED:
        today_marks = [t for t in tasks if t.get("is_today")]
        if not today_marks:
            for task in tasks:
                if task.get("actionable") and task.get("state") in {
                    TASK_STATE_IN_PROGRESS,
                    TASK_STATE_PENDING,
                }:
                    if insurance_is_today and task["task_id"] == TASK_ID_INSURANCE:
                        task["is_today"] = True
                        break
                    if not insurance_is_today:
                        task["is_today"] = True
                        break
        else:
            # Keep first today mark only.
            seen = False
            for task in tasks:
                if task.get("is_today"):
                    if seen:
                        task["is_today"] = False
                    seen = True

    return tasks


def _customer_projection(deps: _ResolvedDeps) -> dict[str, Any]:
    today = _customer_today(deps)
    customer = {
        "today": today,
        "why": _customer_why(deps, today),
        "after": _customer_after(deps, today),
        "trust": _customer_trust(deps, today),
        "current_stage": _customer_current_stage(deps, today),
    }
    customer["tasks"] = _customer_tasks(deps, customer)
    return customer


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
        "tasks": [],
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
