"""
Broker Inbox Triage — API route

POST /api/inbox/triage
Accepts: {"text": "..."}
Returns: structured triage output from the triage engine.

GET /api/inbox/scenario-logic-center
Returns: aggregated scenario inventory for founder/broker review.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.fiqa_api.inbox_triage.case_store import (
    CASE_STATUS_VALUES,
    CASE_WAITING_ON_VALUES,
    add_case_note,
    append_follow_up_message,
    get_case_by_id,
    list_recent_cases,
    save_case,
    update_case_customer,
    update_case_follow_up,
    update_case_status,
)
from services.fiqa_api.inbox_triage.session_store import (
    delete_in_progress_session,
    get_in_progress_session,
    save_in_progress_session,
)
from services.fiqa_api.inbox_triage.config_loader import (
    can_publish_add_car_rules,
    get_active_client_id,
    get_add_car_rules,
    get_handoff_phrases,
    get_reply_templates,
    get_ui_copy,
    save_add_car_rules,
)
from services.fiqa_api.inbox_triage.triage import (
    triage_conversation,
    triage_for_append,
    _is_add_vehicle_request,
    _is_premium_review_request,
    _is_claim_intake_request,
    _is_remove_vehicle_request,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inbox", tags=["inbox-triage"])


def _normalize_input(text: str) -> str:
    """Normalize input: strip, collapse runs of whitespace to single space."""
    if not text:
        return ""
    t = str(text).strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _infer_intent_from_result(text: str, result: dict[str, Any]) -> str | None:
    """Infer primary intent from triage result and text. Returns soft_route-style key or None."""
    lowered = (text or "").lower()
    cat = (result.get("issue_category") or "").lower()
    if _is_add_vehicle_request(lowered):
        return "add_car"
    if _is_remove_vehicle_request(lowered):
        return "remove_car"
    if _is_claim_intake_request(lowered):
        return "claim_intake"
    if cat in ("cancellation_warning", "payment_lapse_expiration"):
        return "cancellation_warning"
    if cat in ("missing_document", "underwriting_followup"):
        return "missing_document"
    if _is_premium_review_request(lowered) or cat == "renewal_reminder":
        return "renewal_premium"  # maps to remove_car or separate; treat as different from add_car/claim
    return None


REROUTE_MESSAGES: dict[str, str] = {
    "add_car": "看起来这是加车报价相关的问题，我先帮您处理这个。",
    "remove_car": "看起来这是保单变更相关的问题，我先帮您处理这个。",
    "claim_intake": "看起来这是事故理赔相关的问题，我先帮您处理这个。",
    "cancellation_warning": "看起来这是付款/取消相关的问题，我先帮您处理这个。",
    "missing_document": "看起来这是上传材料相关的问题，我先帮您处理这个。",
}

# Intent-specific first replies when soft_route is set but triage returned unclear/generic (button-starter fallback)
SOFT_ROUTE_STARTER_REPLIES: dict[str, str] = {
    "add_car": "好的，我来帮您看新车报价。先把年份和车型发我，我就能帮你算。",
    "remove_car": "好的，可以处理。把卖车日期、车辆信息和是否已经过户发我，我先帮你确认。",
    "claim_intake": "先别慌，我先按事故来帮您处理。先把事故经过、现场照片和对方车牌发我，我帮你确认下一步怎么报案。",
    "cancellation_warning": "这像是付款问题。先把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。",
    "missing_document": "好的，材料补交我来帮您处理。把完整通知和要补的材料发我，我整理后尽快帮你回复。",
}


class ConversationTurn(BaseModel):
    """One turn in a customer intake conversation."""

    role: str = Field(..., description="'customer' or 'system'")
    text: str = Field(..., description="Message content")


class TriageRequest(BaseModel):
    """Request body for inbox triage."""

    text: str = Field(..., description="Inbound message text to triage (screenshot OCR, email, notice, etc.)")
    persist_case: bool = Field(
        default=False,
        description="When true, save triage output as a lightweight Unified Intake case.",
    )
    conversation_turns: list[ConversationTurn] | None = Field(
        default=None,
        description="When provided, full conversation for progressive intake. Text is merged with latest for triage.",
    )
    soft_route: str | None = Field(
        default=None,
        description="Optional intent hint from quick-start button (add_car, remove_car, claim_intake, cancellation_warning, missing_document). Text overrides when intent conflicts.",
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session/conversation ID for in-progress continuity (client-generated UUID). Echoed as conversation_id when no case persisted.",
    )
    client_id: str | None = Field(
        default=None,
        description="Optional client ID for client-aware handoff phrases. When omitted, uses CLIENT_ID env or chen_kui.",
    )


class CaseStatusRequest(BaseModel):
    """Request body for case status updates."""

    status: str = Field(..., description=f"One of: {', '.join(CASE_STATUS_VALUES)}")


class CaseNoteRequest(BaseModel):
    """Request body for lightweight broker follow-up notes."""

    note: str = Field(..., description="Short broker follow-up note to save on the case.")


class CaseFollowUpRequest(BaseModel):
    """Request body for lightweight follow-up target + timing fields."""

    waiting_on: str = Field(default="none", description=f"One of: {', '.join(CASE_WAITING_ON_VALUES)}")
    next_contact_by: str = Field(
        default="",
        description="Short next-contact timing note, e.g. 2026-03-09 or tomorrow morning.",
    )


class CaseCustomerRequest(BaseModel):
    """Request body for lightweight customer linkage fields."""

    customer_name: str | None = Field(default=None, description="Customer display name")
    customer_phone: str | None = Field(default=None, description="Customer phone")
    customer_email: str | None = Field(default=None, description="Customer email")
    policy_number: str | None = Field(default=None, description="Policy number if known")
    contact_note: str | None = Field(default=None, description="Free-text contact note (e.g. WeChat)")


class AppendMessageRequest(BaseModel):
    """Request body for pasting a new customer follow-up into an existing case."""

    new_message: str = Field(..., description="New customer follow-up message to append to the case.")
    client_id: str | None = Field(
        default=None,
        description="Optional client ID when case has no client_id (legacy fallback).",
    )


class AddCarRulesOverride(BaseModel):
    """Optional rules override for Add-Car Quote preview."""

    ask_vehicle: dict[str, str] | None = Field(default=None, description="ask_vehicle.zh, ask_vehicle.en")
    ask_zip: dict[str, str] | None = Field(default=None, description="ask_zip.zh, ask_zip.en")
    ask_delivery_driver: dict[str, str] | None = Field(
        default=None, description="ask_delivery_driver.zh, ask_delivery_driver.en"
    )


class AddCarRulesPreviewRequest(BaseModel):
    """Request body for Add-Car Quote preview with optional rules override."""

    text: str = Field(..., description="Sample customer message to preview")
    conversation_turns: list[ConversationTurn] | None = Field(
        default=None,
        description="Optional prior turns for multi-turn preview.",
    )
    rules_override: AddCarRulesOverride | None = Field(
        default=None,
        description="Optional draft rules; when set, used instead of published config for preview.",
    )


class AddCarRulesPublishRequest(BaseModel):
    """Request body for publishing Add-Car Quote rules."""

    ask_vehicle: dict[str, str] = Field(..., description="ask_vehicle.zh, ask_vehicle.en")
    ask_zip: dict[str, str] = Field(..., description="ask_zip.zh, ask_zip.en")
    ask_delivery_driver: dict[str, str] = Field(
        ..., description="ask_delivery_driver.zh, ask_delivery_driver.en"
    )


def _load_scenario_logic_center() -> dict[str, Any]:
    """Load scenario logic center JSON from configs. Fallback to empty structure if missing."""
    # __file__ = services/fiqa_api/routes/inbox_triage.py; parents[3] = project root
    path = Path(__file__).resolve().parents[3] / "configs" / "scenario_logic_center.json"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Could not load scenario_logic_center.json: %s", e)
        return {"version": "1", "scenarios": [], "summary": {"total_scenarios": 0}}


@router.get("/scenario-logic-center")
async def get_scenario_logic_center() -> dict[str, Any]:
    """
    Return aggregated scenario inventory for Scenario Logic Center.
    Used by founder/broker review to see what scenarios exist, how they work, what is strong/weak.
    """
    return _load_scenario_logic_center()


@router.get("/client-config")
async def get_client_config(client: str | None = Query(default=None)) -> dict[str, Any]:
    """
    Return client UI copy for the given client ID.
    Used by frontend to render client-specific labels and copy.
    client: optional; when omitted, uses CLIENT_ID env or chen_kui.
    """
    client_id = (client or "").strip() or get_active_client_id()
    ui_copy = get_ui_copy(client_id)
    return {"client_id": client_id, "ui_copy": ui_copy}


@router.get("/add-car-rules")
async def get_add_car_rules_api() -> dict[str, Any]:
    """
    Return current Add-Car Quote rules (published config).
    Used by Rules Center to display and edit.
    """
    rules = get_add_car_rules()
    templates = get_reply_templates()
    handoff = get_handoff_phrases()
    add_car_template = templates.get("add_car") or {}
    add_car_handoff = handoff.get("add_car") or {}
    return {
        "ask_vehicle": rules.get("ask_vehicle", {}),
        "ask_zip": rules.get("ask_zip", {}),
        "ask_delivery_driver": rules.get("ask_delivery_driver", {}),
        "first_reply": {
            "zh": add_car_template.get("zh", ""),
            "en": add_car_template.get("en", ""),
        },
        "handoff": {
            "zh": add_car_handoff.get("zh", ""),
            "en": add_car_handoff.get("en", ""),
        },
        "publishable": can_publish_add_car_rules(),
    }


@router.post("/add-car-rules/preview")
async def preview_add_car_rules(request: AddCarRulesPreviewRequest) -> dict[str, Any]:
    """
    Preview Add-Car Quote flow with optional rules override.
    Returns triage result (client_reply_draft, collected_fields, etc.) as if rules were applied.
    """
    text = _normalize_input(request.text or "")
    if not text:
        raise HTTPException(
            status_code=400,
            detail="text is required and cannot be empty",
        )
    override = request.rules_override
    add_car_rules_override: dict[str, dict[str, str]] | None = None
    if override and (override.ask_vehicle or override.ask_zip or override.ask_delivery_driver):
        add_car_rules_override = {}
        if override.ask_vehicle:
            add_car_rules_override["ask_vehicle"] = {
                "zh": (override.ask_vehicle.get("zh") or "").strip(),
                "en": (override.ask_vehicle.get("en") or "").strip(),
            }
        if override.ask_zip:
            add_car_rules_override["ask_zip"] = {
                "zh": (override.ask_zip.get("zh") or "").strip(),
                "en": (override.ask_zip.get("en") or "").strip(),
            }
        if override.ask_delivery_driver:
            add_car_rules_override["ask_delivery_driver"] = {
                "zh": (override.ask_delivery_driver.get("zh") or "").strip(),
                "en": (override.ask_delivery_driver.get("en") or "").strip(),
            }
        # Merge with current config so partial overrides work
        current = get_add_car_rules()
        for k, v in add_car_rules_override.items():
            merged = dict(current.get(k, {}))
            for lang, val in v.items():
                if val:
                    merged[lang] = val
            add_car_rules_override[k] = merged
    turns = request.conversation_turns or []
    result = triage_conversation(
        text,
        [{"role": t.role, "text": t.text} for t in turns],
        add_car_rules_override=add_car_rules_override,
    )
    return result


@router.put("/add-car-rules")
async def publish_add_car_rules(request: AddCarRulesPublishRequest) -> dict[str, Any]:
    """
    Publish Add-Car Quote rules to config.
    Writes to configs/industries/insurance/add_car_rules.json.
    May fail in read-only environments (e.g. Cloud Run without writable volume).
    """
    rules = {
        "ask_vehicle": {
            "zh": (request.ask_vehicle.get("zh") or "").strip(),
            "en": (request.ask_vehicle.get("en") or "").strip(),
        },
        "ask_zip": {
            "zh": (request.ask_zip.get("zh") or "").strip(),
            "en": (request.ask_zip.get("en") or "").strip(),
        },
        "ask_delivery_driver": {
            "zh": (request.ask_delivery_driver.get("zh") or "").strip(),
            "en": (request.ask_delivery_driver.get("en") or "").strip(),
        },
    }
    try:
        save_add_car_rules(rules)
    except OSError as e:
        logger.warning("Publish failed (config may be read-only): %s", e)
        raise HTTPException(
            status_code=503,
            detail="Could not save rules (config directory may be read-only). Try local dev.",
        ) from e
    return {"ok": True, "message": "Rules published."}


@router.post("/triage")
async def triage_inbox(request: TriageRequest) -> dict[str, Any]:
    """
    Triage an inbound broker message.

    Accepts message text (e.g. from OCR, email body, or pasted notice).
    Returns structured triage output:
    - issue_category: one of missing_signature, missing_document, cancellation_warning, etc.
    - urgency: low, medium, high, critical
    - manual_followup_needed: bool
    - broker_next_step: actionable next step for broker
    - client_prep: what client should prepare
    - client_reply_draft: draft reply broker can send (editable)
    """
    text = _normalize_input(request.text or "")
    if not text:
        raise HTTPException(
            status_code=400,
            detail="text is required and cannot be empty",
        )

    soft_route = (request.soft_route or "").strip().lower() or None
    client_id = (request.client_id or "").strip() or get_active_client_id()
    if soft_route == "talk_to_agent":
        handoff_phrases = get_handoff_phrases(client_id)
        phrases = handoff_phrases.get("customer_requested_human", {}) if handoff_phrases else {}
        draft_zh = phrases.get("zh") or "好的，已帮您转给办公室，他们会尽快联系您。"
        result = {
            "issue_category": "customer_requested_human",
            "urgency": "medium",
            "manual_followup_needed": True,
            "broker_next_step": "Customer requested human contact. Call or message back promptly.",
            "client_prep": "Customer wants to speak with office.",
            "client_reply_draft": draft_zh,
            "handoff_ready": True,
            "conversation_summary": "Customer requested to speak with office / 客户要求联系人工",
            "collected_fields": ["customer_requested_human"],
            "still_needed_fields": [],
            "case_creation_suggested": True,
            # Phase 2.5: workflow_state contract consistency
            "next_best_question": "",
            "lifecycle_status": "handoff_pending",
            "collection_stage": "enough_for_handoff",
        }
        if request.persist_case:
            try:
                source = f"[客户] {text}"
                return save_case(source, result, client_id=client_id)
            except Exception as exc:
                logger.exception("Failed to persist Talk-to-Agent case: %s", exc)
                result["case_persisted"] = False
        return result

    # MULTI_TURN_CONTINUITY_GUARDRAIL: First message must go through triage_conversation,
    # not triage_message + forced handoff_ready. Use triage_conversation(text, []) for first turn.
    turns = request.conversation_turns or []
    result = triage_conversation(
        text,
        [{"role": t.role, "text": t.text} for t in turns],
        client_id=client_id,
    )

    # Rerouting: when soft_route from button conflicts with inferred intent from text, acknowledge
    soft_route = (request.soft_route or "").strip().lower() or None
    if soft_route:
        inferred = _infer_intent_from_result(text, result)
        # Compatible pairs: remove_car + renewal_premium (both policy-related)
        compatible = (soft_route == "remove_car" and inferred == "renewal_premium") or (
            soft_route == "renewal_premium" and inferred == "remove_car"
        )
        if inferred and inferred != soft_route and not compatible:
            result["reroute_occurred"] = True
            result["reroute_message"] = REROUTE_MESSAGES.get(inferred, "看起来这是不同的问题，我先帮您处理这个。")
            result["previous_soft_route"] = soft_route
            result["new_intent"] = inferred
        else:
            result["reroute_occurred"] = False

        # Button-starter fallback: when triage returned unclear or generic, use intent-specific first reply
        draft = result.get("client_reply_draft") or ""
        is_generic = (
            result.get("issue_category") == "unclear"
            or "内容不够完整" in draft
            or "请提供更多信息" in draft
            or "Could you please provide more" in draft
        )
        if is_generic and soft_route in SOFT_ROUTE_STARTER_REPLIES:
            result["client_reply_draft"] = SOFT_ROUTE_STARTER_REPLIES[soft_route]
            result["issue_category"] = (
                "payment_lapse_expiration" if soft_route == "cancellation_warning" else "customer_question"
            )
            if soft_route == "add_car":
                result["collected_fields"] = []
                result["still_needed_fields"] = ["year", "model", "zip"]
            elif soft_route == "claim_intake":
                result["collected_fields"] = []
                result["still_needed_fields"] = ["accident_time", "accident_location", "photos"]
            elif soft_route == "cancellation_warning":
                result["collected_fields"] = []
                result["still_needed_fields"] = ["payment_notice_or_screenshot"]
            elif soft_route == "missing_document":
                result["collected_fields"] = []
                result["still_needed_fields"] = ["full_notice", "requested_documents"]
            elif soft_route == "remove_car":
                result["collected_fields"] = []
                result["still_needed_fields"] = ["sale_date", "vehicle_info", "transfer_status"]

    if request.persist_case:
        # MULTI_TURN_CONTINUITY_GUARDRAIL: Only persist when handoff_ready to avoid
        # premature cases and duplicate cases across turns.
        should_persist = result.get("handoff_ready")
        if should_persist:
            try:
                if turns:
                    conv_parts = []
                    for t in turns:
                        label = "客户" if (t.role or "").strip().lower() == "customer" else "系统"
                        conv_parts.append(f"[{label}] {_normalize_input(t.text or '')}")
                    conv_parts.append(f"[客户] {text}")
                    source_for_case = "\n\n".join(p for p in conv_parts if p)
                else:
                    source_for_case = text
                saved = save_case(
                    source_for_case or text,
                    result,
                    origin_session_id=request.session_id.strip() if request.session_id else None,
                    client_id=client_id,
                )
                # In-progress persistence: clear session when case created
                if request.session_id:
                    delete_in_progress_session(request.session_id.strip())
                return saved
            except Exception as exc:
                logger.exception("Failed to persist Unified Intake case: %s", exc)
                result["case_persisted"] = False
        else:
            result["case_persisted"] = False

    # In-progress persistence: save turns + workflow_state when session_id and no case
    if request.session_id and not result.get("case_id"):
        reply_content = (result.get("client_reply_draft") or "").strip()
        if result.get("reroute_occurred") and result.get("reroute_message"):
            reply_content = f"{result['reroute_message']}\n\n{reply_content}"
        full_turns: list[dict[str, Any]] = []
        for t in turns:
            full_turns.append({"role": t.role, "text": t.text or ""})
        full_turns.append({"role": "customer", "text": text})
        full_turns.append({"role": "system", "text": reply_content, "triageResult": result})
        try:
            save_in_progress_session(
                request.session_id.strip(),
                full_turns,
                result,
            )
        except Exception as exc:
            logger.warning("Failed to save in-progress session: %s", exc)
        result["conversation_id"] = request.session_id.strip()
    return result


@router.get("/cases")
async def get_recent_cases(limit: int = Query(default=8, ge=1, le=50)) -> dict[str, list[dict[str, Any]]]:
    """Return recent persisted Unified Intake cases."""
    return {"cases": list_recent_cases(limit=limit)}


@router.get("/session/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    """
    Return in-progress session by session_id for refresh recovery.
    Returns { turns, workflow_state } or 404 if not found.
    """
    data = get_in_progress_session(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="session not found")
    return data


@router.patch("/cases/{case_id}/status")
async def patch_case_status(case_id: str, request: CaseStatusRequest) -> dict[str, Any]:
    """Update the lightweight broker workflow status for a saved case."""
    try:
        updated = update_case_status(case_id=case_id, status=request.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    return updated


@router.post("/cases/{case_id}/notes")
async def create_case_note(case_id: str, request: CaseNoteRequest) -> dict[str, Any]:
    """Add one lightweight broker note to a saved case."""
    try:
        updated = add_case_note(case_id=case_id, note_text=request.note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    return updated


@router.patch("/cases/{case_id}/follow-up")
async def patch_case_follow_up(case_id: str, request: CaseFollowUpRequest) -> dict[str, Any]:
    """Update lightweight follow-up target + timing for a saved case."""
    try:
        updated = update_case_follow_up(
            case_id=case_id,
            waiting_on=request.waiting_on,
            next_contact_by=request.next_contact_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    return updated


@router.patch("/cases/{case_id}/customer")
async def patch_case_customer(case_id: str, request: CaseCustomerRequest) -> dict[str, Any]:
    """Update lightweight customer linkage fields on a saved case."""
    updated = update_case_customer(
        case_id=case_id,
        customer_name=request.customer_name,
        customer_phone=request.customer_phone,
        customer_email=request.customer_email,
        policy_number=request.policy_number,
        contact_note=request.contact_note,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    return updated


@router.post("/cases/{case_id}/append-message")
async def append_case_message(case_id: str, request: AppendMessageRequest) -> dict[str, Any]:
    """
    Paste a new customer follow-up message into an existing case.
    Re-triages with case context, updates case fields (next step, collected, etc.),
    and preserves status, waiting_on, notes.
    """
    new_msg = _normalize_input(request.new_message or "")
    if not new_msg:
        raise HTTPException(
            status_code=400,
            detail="new_message is required and cannot be empty",
        )
    case = get_case_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    try:
        case_client_id = (case.get("client_id") or "").strip() or (request.client_id or "").strip() or None
        triage_result = triage_for_append(
            existing_source_text=case.get("source_text", ""),
            new_message=new_msg,
            client_id=case_client_id,
        )
        updated = append_follow_up_message(
            case_id=case_id,
            new_message_text=new_msg,
            triage_result=triage_result,
            client_id=case_client_id or (request.client_id or "").strip() or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    return updated
