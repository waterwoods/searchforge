"""P19I-2b — Thin workflow kernel (pure Python, no I/O).

Framework-agnostic helpers for Andy's 4-question intake model:
1. What does this task need?
2. What has the customer already provided?
3. What is still missing?
4. Can this be handed to a human/system for processing?

Deterministic only — no DB, network, LLM, or orchestration framework imports.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

SlotType = Literal["field", "attachment", "yes_no", "composite"]

_YES_NO_VALUES = frozenset({"yes", "no", "true", "false", "y", "n"})


@dataclass(frozen=True)
class SlotDefinition:
    key: str
    label: str
    required: bool = False
    phase: str | None = None
    slot_type: SlotType = "field"
    aliases: tuple[str, ...] = ()
    description: str | None = None


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    lane: str
    display_name: str
    phases: tuple[str, ...]
    required_slots: tuple[SlotDefinition, ...]
    optional_slots: tuple[SlotDefinition, ...] = ()
    human_review_phase: str = "intake_ready_for_broker"
    done_phase: str = "broker_done"
    safety_rules: tuple[str, ...] = ()
    current_step_order: tuple[str, ...] = ()


@dataclass(frozen=True)
class MissingItem:
    key: str
    label: str
    phase: str | None
    required: bool
    reason: str = "missing"


@dataclass(frozen=True)
class GateResult:
    passed: bool
    gate_name: str
    missing_items: tuple[MissingItem, ...] = ()
    blocked_reason: str | None = None


@dataclass(frozen=True)
class CurrentStep:
    phase: str | None
    action: str
    missing_items: tuple[MissingItem, ...]
    customer_message_hint: str | None = None


@dataclass(frozen=True)
class WorkflowRuntimeSnapshot:
    workflow_id: str
    lane: str
    current_phase: str | None = None
    collected_fields: dict[str, Any] = field(default_factory=dict)
    attachments: dict[str, str] = field(default_factory=dict)
    safety_flags: tuple[str, ...] = ()
    human_task_status: str | None = None


@dataclass(frozen=True)
class HumanHandoffDecision:
    can_hand_off: bool
    reason: str
    ready_for_human_review: bool
    needs_manual_handle: bool = False


def _all_slots(defn: WorkflowDefinition) -> tuple[SlotDefinition, ...]:
    return (*defn.required_slots, *defn.optional_slots)


def _slot_lookup(defn: WorkflowDefinition) -> dict[str, SlotDefinition]:
    return {slot.key: slot for slot in _all_slots(defn)}


def _value_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def _yes_no_present(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return value.strip().lower() in _YES_NO_VALUES
    return False


def _attachment_received(attachments: dict[str, str], key: str) -> bool:
    status = attachments.get(key)
    if status is None:
        return False
    return str(status).strip().lower() == "received"


def _keys_for_slot(slot: SlotDefinition) -> tuple[str, ...]:
    if slot.aliases:
        return (slot.key, *slot.aliases)
    return (slot.key,)


def _slot_collected(slot: SlotDefinition, snapshot: WorkflowRuntimeSnapshot) -> bool:
    fields = snapshot.collected_fields or {}
    attachments = snapshot.attachments or {}

    if slot.slot_type == "attachment":
        return any(_attachment_received(attachments, key) for key in _keys_for_slot(slot))

    if slot.slot_type == "yes_no":
        for key in _keys_for_slot(slot):
            if key in fields and _yes_no_present(fields[key]):
                return True
        return False

    if slot.slot_type == "composite":
        for key in _keys_for_slot(slot):
            if key in fields and _value_present(fields[key]):
                return True
            if _attachment_received(attachments, key):
                return True
        return False

    # field
    for key in _keys_for_slot(slot):
        if key in fields and _value_present(fields[key]):
            return True
    return False


def what_does_task_need(defn: WorkflowDefinition) -> tuple[SlotDefinition, ...]:
    """Q1: all required + optional slots in stable order."""
    return _all_slots(defn)


def what_is_collected(defn: WorkflowDefinition, snapshot: WorkflowRuntimeSnapshot) -> tuple[str, ...]:
    """Q2: slot keys that are satisfied in the runtime snapshot."""
    collected: list[str] = []
    for slot in _all_slots(defn):
        if _slot_collected(slot, snapshot):
            collected.append(slot.key)
    return tuple(collected)


def what_is_missing(defn: WorkflowDefinition, snapshot: WorkflowRuntimeSnapshot) -> tuple[MissingItem, ...]:
    """Q3: required slots not yet collected."""
    missing: list[MissingItem] = []
    for slot in defn.required_slots:
        if _slot_collected(slot, snapshot):
            continue
        missing.append(
            MissingItem(
                key=slot.key,
                label=slot.label,
                phase=slot.phase,
                required=True,
            )
        )
    return tuple(missing)


def compute_completion_score(defn: WorkflowDefinition, snapshot: WorkflowRuntimeSnapshot) -> int:
    """0–100 richness score over required + optional slots. Never replaces required gate."""
    slots = _all_slots(defn)
    if not slots:
        return 100
    collected_count = sum(1 for slot in slots if _slot_collected(slot, snapshot))
    return int(round(collected_count / len(slots) * 100))


def evaluate_safety_gate(defn: WorkflowDefinition, snapshot: WorkflowRuntimeSnapshot) -> GateResult:
    flags = tuple(str(flag).strip() for flag in (snapshot.safety_flags or ()) if str(flag).strip())
    if flags:
        return GateResult(
            passed=False,
            gate_name="safety",
            blocked_reason=flags[0] if len(flags) == 1 else "; ".join(flags),
        )
    return GateResult(passed=True, gate_name="safety")


def evaluate_required_gate(defn: WorkflowDefinition, snapshot: WorkflowRuntimeSnapshot) -> GateResult:
    missing = what_is_missing(defn, snapshot)
    if missing:
        return GateResult(
            passed=False,
            gate_name="required",
            missing_items=missing,
            blocked_reason="missing required items",
        )
    return GateResult(passed=True, gate_name="required")


def evaluate_human_gate(defn: WorkflowDefinition, snapshot: WorkflowRuntimeSnapshot) -> HumanHandoffDecision:
    safety = evaluate_safety_gate(defn, snapshot)
    if not safety.passed:
        return HumanHandoffDecision(
            can_hand_off=True,
            reason=f"safety blocked: {safety.blocked_reason}; manual handle",
            ready_for_human_review=True,
            needs_manual_handle=True,
        )

    required = evaluate_required_gate(defn, snapshot)
    if required.passed:
        return HumanHandoffDecision(
            can_hand_off=True,
            reason="required gate passed",
            ready_for_human_review=True,
            needs_manual_handle=False,
        )

    return HumanHandoffDecision(
        can_hand_off=False,
        reason="missing required items",
        ready_for_human_review=False,
        needs_manual_handle=False,
    )


def _ordered_required_slots(defn: WorkflowDefinition) -> tuple[SlotDefinition, ...]:
    lookup = _slot_lookup(defn)
    if defn.current_step_order:
        ordered: list[SlotDefinition] = []
        seen: set[str] = set()
        for key in defn.current_step_order:
            slot = lookup.get(key)
            if slot is None or not slot.required or key in seen:
                continue
            ordered.append(slot)
            seen.add(key)
        for slot in defn.required_slots:
            if slot.key not in seen:
                ordered.append(slot)
        return tuple(ordered)
    return defn.required_slots


def get_current_step(defn: WorkflowDefinition, snapshot: WorkflowRuntimeSnapshot) -> CurrentStep:
    safety = evaluate_safety_gate(defn, snapshot)
    if not safety.passed:
        return CurrentStep(
            phase="manual_handle",
            action="manual_handle",
            missing_items=(),
            customer_message_hint="需要人工优先处理",
        )

    missing = what_is_missing(defn, snapshot)
    if not missing:
        return CurrentStep(
            phase=defn.human_review_phase,
            action="ready_for_human_review",
            missing_items=(),
            customer_message_hint="资料已收齐，等待人工确认",
        )

    missing_keys = {item.key for item in missing}
    focus_slot: SlotDefinition | None = None
    for slot in _ordered_required_slots(defn):
        if slot.key in missing_keys:
            focus_slot = slot
            break

    if focus_slot is None:
        focus_slot = defn.required_slots[0]

    focus_phase = focus_slot.phase
    if focus_phase:
        phase_missing = tuple(item for item in missing if item.phase == focus_phase)
        action = f"collect_{focus_phase}"
    else:
        phase_missing = (MissingItem(
            key=focus_slot.key,
            label=focus_slot.label,
            phase=focus_slot.phase,
            required=True,
        ),)
        action = f"collect_{focus_slot.key}"

    return CurrentStep(
        phase=focus_phase or focus_slot.phase,
        action=action,
        missing_items=phase_missing,
        customer_message_hint=f"请先补充：{focus_slot.label}",
    )


def _to_serializable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, tuple):
        return [_to_serializable(item) for item in value]
    if isinstance(value, list):
        return [_to_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_serializable(item) for key, item in value.items()}
    return value


def evaluate_workflow_snapshot(defn: WorkflowDefinition, snapshot: WorkflowRuntimeSnapshot) -> dict[str, Any]:
    """Aggregate kernel view for tests and future reply builders."""
    needs = what_does_task_need(defn)
    collected = what_is_collected(defn, snapshot)
    missing = what_is_missing(defn, snapshot)
    safety_gate = evaluate_safety_gate(defn, snapshot)
    required_gate = evaluate_required_gate(defn, snapshot)
    current_step = get_current_step(defn, snapshot)
    human_handoff = evaluate_human_gate(defn, snapshot)

    return {
        "workflow_id": defn.workflow_id,
        "lane": defn.lane,
        "needs": [slot.key for slot in needs],
        "collected": list(collected),
        "missing": [_to_serializable(item) for item in missing],
        "completion_score": compute_completion_score(defn, snapshot),
        "safety_gate": _to_serializable(safety_gate),
        "required_gate": _to_serializable(required_gate),
        "current_step": _to_serializable(current_step),
        "human_handoff": _to_serializable(human_handoff),
    }
