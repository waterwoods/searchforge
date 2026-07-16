"""
Broker Inbox Triage — API route

POST /api/inbox/triage
Accepts: {"text": "..."}
Returns: structured triage output from the triage engine.

GET /api/inbox/scenario-logic-center
Returns: aggregated scenario inventory for founder/broker review.
"""
from __future__ import annotations

import asyncio
import functools
import json
import logging
import os
import re
import threading
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, Response
from pydantic import BaseModel, Field

from services.fiqa_api.inbox_triage.case_attachment_api import (
    consume_preview_gcs_ms,
    resolve_attachment_preview,
    sanitize_case_for_workbench_api,
)
from services.fiqa_api.inbox_triage.case_store import (
    CASE_STATUS_VALUES,
    CASE_WAITING_ON_VALUES,
    ClaimBrokerDoneError,
    add_attachment_to_case,
    add_case_note,
    append_follow_up_message,
    delete_case,
    get_attachment_file_path,
    mark_claim_broker_done,
    merge_light_identity_from_client_payload,
    save_case,
    update_case_customer,
    update_case_follow_up,
    update_case_status,
    update_case_workbench_flags,
)
from services.fiqa_api.wecom.active_case_bridge import BrokerConfirmError, confirm_case_by_broker
from services.fiqa_api.inbox_triage.case_binding import is_case_open_for_binding, resolve_active_case
from services.fiqa_api.inbox_triage.case_truth_repository import (
    count_cases_for_read,
    list_broker_workbench_cases_for_read,
    get_case_for_read,
    get_case_triage_stub_for_read,
    list_cases_for_phone_lookup,
    list_cases_for_office_enforcement_read,
    list_cases_for_client_scoped_read,
    list_recent_cases_for_binding,
    list_recent_cases_for_read,
    triage_stub_read_cache_scope,
)
from services.fiqa_api.inbox_triage.active_case_lookup import (
    active_add_car_case_summary,
    create_customer_first_add_car_draft,
    find_active_add_car_case_by_phone,
)
from services.fiqa_api.inbox_triage.phone_normalization import is_valid_customer_phone, normalize_phone_digits
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.inbox_triage import session_repository as intake_session_repository
from services.fiqa_api.inbox_triage.session_store import (
    get_in_progress_session,
    in_progress_session_view,
    light_identity_binding_from_in_progress_view,
    patch_session_case_binding,
    patch_session_light_identity_binding,
    save_in_progress_session,
    save_session_binding_after_case_created,
)
from services.fiqa_api.inbox_triage.config_loader import (
    can_publish_add_car_rules,
    get_active_client_id,
    get_add_car_rules,
    get_handoff_phrases,
    get_reply_templates,
    get_soft_route_inbox_copy,
    get_ui_copy,
    get_wechat_binding_mode_for_client,
    save_add_car_rules,
)
from services.fiqa_api.inbox_triage.wechat_binding import (
    build_authorize_url,
    build_frontend_return_url,
    exchange_code_for_openid,
    opaque_person_link_key,
    sign_state,
    simulate_allowed,
    verify_state,
    wechat_credentials_configured,
)
from services.fiqa_api.inbox_triage.role_c_simulation_service import (
    RoleCMaxTurnsReached,
    next_role_c_customer_line,
)
from services.fiqa_api.inbox_triage.assist_layer import (
    DEFAULT_ASSIST,
    _assist_layer_enabled,
    build_assist_layer,
)
from services.fiqa_api.inbox_triage.entity_repository import (
    active_vehicle_request_cache_scope,
    get_active_vehicle,
)
from services.fiqa_api.inbox_triage.case_lifecycle import _derive_case_lifecycle
from services.fiqa_api.inbox_triage.p20_slice1_command_service import default_slice1_service
from services.fiqa_api.analytics.minimal_events import track_event
from services.fiqa_api.analytics.funnel_events import append_session_analytics_event
from services.fiqa_api.analytics.triage_funnel import (
    emit_case_created_milestone,
    emit_funnel_from_triage_result,
    emit_session_milestones,
)
from services.fiqa_api.inbox_triage.v6_attachment_sidecar import (
    extract_ocr_from_inline_base64,
    merge_v6_ocr_signals,
)
from services.fiqa_api.inbox_triage.triage_handoff_reply_composer import (
    apply_client_reply_finalize_to_result,
    sync_add_car_client_reply_vehicle_to_primary_summary,
)
from services.fiqa_api.inbox_triage.add_car_vehicle_signals import (
    text_has_vehicle_make_model_signal,
    text_has_vehicle_year_signal,
)
from services.fiqa_api.security.request_identity import http_request_lineage, intake_tenant_truth
from services.fiqa_api.security.support_export_gate import (
    assert_support_export_authorized,
    support_export_auth_posture_dict,
)
from services.fiqa_api.security.case_office_access import (
    assert_case_office_access_allowed,
    case_office_enforcement_enabled,
    client_asserted_office_id,
    office_ownership_posture_dict,
)
from services.fiqa_api.security.case_client_access import (
    assert_case_client_access_allowed,
    case_client_enforcement_enabled,
    client_ownership_posture_dict,
    resolve_server_client_id,
)
from services.fiqa_api.security.intake_api_gate import intake_api_auth_posture_dict
from services.fiqa_api.security.minimal_signed_broker_token import (
    minimal_broker_token_posture_dict,
    minimal_broker_token_request_truth,
)
from services.fiqa_api.security.token_scope_posture import token_scope_registry_dict
from services.fiqa_api.inbox_triage.triage import (
    triage_conversation,
    triage_for_append,
    _add_car_enough_for_handoff,
    _derive_vehicle_key_from_add_car_text,
    _extract_add_car_fields_truth_safe,
    _is_add_vehicle_request,
    _is_premium_review_request,
    _is_claim_intake_request,
    _is_remove_vehicle_request,
    _primary_vehicle_summary_from_entity_payload,
    _vehicle_key_from_entity_payload,
)

logger = logging.getLogger(__name__)

# Support export / replay handoff — bump when manifest keys change materially.
SUPPORT_EXPORT_MANIFEST_VERSION = "support_export_v4"

router = APIRouter(prefix="/api/inbox", tags=["inbox-triage"])


def _support_replay_lineage_dict() -> dict[str, Any]:
    """Stable replay-handoff tuple for tickets (not a legal hold or WORM export)."""

    from services.fiqa_api.deployment_profile import intake_schema_epoch

    return {
        "support_export_manifest_version": SUPPORT_EXPORT_MANIFEST_VERSION,
        "intake_schema_epoch": intake_schema_epoch(),
        "triage_wire_contract_label": "triage_result_fe_grouping_v1",
        "semantics": "support_replay_handoff_metadata_v1_not_legal_hold",
        "office_ownership": office_ownership_posture_dict(),
        "client_ownership": client_ownership_posture_dict(),
        "token_scope_registry": token_scope_registry_dict(),
        "minimal_broker_token_posture": minimal_broker_token_posture_dict(),
    }




def _active_vehicle_cache_route(fn: Any) -> Any:
    """One PG read per request for get_active_vehicle (triage + post-triage identity sync)."""

    @functools.wraps(fn)
    async def _wrapped(*args: Any, **kwargs: Any) -> Any:
        with active_vehicle_request_cache_scope():
            return await fn(*args, **kwargs)

    return _wrapped


def _inbox_triage_request_cache_route(fn: Any) -> Any:
    """POST /api/inbox/triage: vehicle entity + triage stub reads deduped per request."""

    @functools.wraps(fn)
    async def _wrapped(*args: Any, **kwargs: Any) -> Any:
        with active_vehicle_request_cache_scope(), triage_stub_read_cache_scope():
            return await fn(*args, **kwargs)

    return _wrapped


def _expose_route_perf_metrics() -> bool:
    return (os.environ.get("TRIAGE_RETURN_PERF_METRICS") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _case_bind_recent_limit() -> int:
    raw = (os.environ.get("CASE_BIND_RECENT_LIMIT") or "").strip()
    try:
        n = int(raw) if raw else 30
    except ValueError:
        n = 30
    return max(5, min(n, 50))


def _schedule_route_analytics(
    result: dict[str, Any],
    turns: list[ConversationTurn],
    *,
    session_id: str | None,
    text: str,
    org_id: str | None = None,
) -> None:
    """Best-effort analytics: do not block response on funnel buffer / track_event."""

    def _sync_emit() -> None:
        try:
            _emit_route_analytics_for_triage_result(
                result, turns, session_id=session_id, text=text, org_id=org_id
            )
        except Exception:
            logger.exception("route_analytics_background_failed")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        _sync_emit()
        return
    loop.create_task(asyncio.to_thread(_sync_emit))


def _attach_route_perf_ms(result: dict[str, Any], perf: dict[str, float]) -> None:
    """Attach optional perf breakdown when TRIAGE_RETURN_PERF_METRICS=1. All *_ms are wall milliseconds."""

    if not _expose_route_perf_metrics():
        return
    out = {k: round(float(v), 2) for k, v in perf.items()}
    triage_m = result.get("triage_turn_metrics")
    if isinstance(triage_m, dict):
        http_proxy = float(out.get("route_total_ms") or 0.0)
        core = float(triage_m.get("latency_ms") or 0.0)
        out["route_overhead_ms"] = round(max(0.0, http_proxy - core), 2)
    result["route_perf"] = out


def _emit_route_analytics_for_triage_result(
    result: dict[str, Any],
    turns: list[ConversationTurn],
    *,
    session_id: str | None = None,
    text: str = "",
    org_id: str | None = None,
) -> None:
    """Structured analytics: funnel milestones (deduped) + lightweight signals in the event buffer."""
    sid = (session_id or "").strip() or None
    cid = str(result.get("case_id") or "").strip() or None

    def _org_meta(meta: dict[str, Any]) -> dict[str, Any]:
        if not org_id:
            return meta
        m = dict(meta)
        m["org_id"] = org_id
        return m

    if result.get("append_allowed") is False:
        append_session_analytics_event(
            "append_blocked",
            session_id=sid,
            case_id=cid,
            metadata=_org_meta({"reason": result.get("case_boundary_action")}),
        )
        track_event("append_blocked", _org_meta({"reason": result.get("case_boundary_action")}))
    coll = result.get("collected_fields")
    miss = result.get("still_needed_fields")
    if not isinstance(coll, list):
        coll = []
    if not isinstance(miss, list):
        miss = []
    fp_meta = {
        "collected_count": len(coll),
        "missing_count": len(miss),
        "quote_ready_status": result.get("quote_ready_status"),
    }
    append_session_analytics_event("field_progress", session_id=sid, case_id=cid, metadata=_org_meta(fp_meta))
    track_event("field_progress", _org_meta(fp_meta))
    emit_funnel_from_triage_result(
        result,
        turns=turns,
        text=text,
        session_id=sid,
        case_id=cid,
        client_asserted_org_id=org_id,
    )
    if len(turns) + 1 <= 2:
        append_session_analytics_event("early_dropoff_signal", session_id=sid, case_id=cid, metadata=_org_meta({}))
        track_event("early_dropoff", _org_meta({}))


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


def _full_thread_lower(text: str, turns: list[ConversationTurn] | None) -> str:
    """All roles, for coarse intent detection across turns."""
    parts: list[str] = []
    if turns:
        for t in turns:
            p = _normalize_input(t.text or "")
            if p:
                parts.append(p.lower())
    tail = _normalize_input(text or "")
    if tail:
        parts.append(tail.lower())
    return " ".join(parts)


def _conversation_labeled_for_add_car_extract(text: str, turns: list[ConversationTurn] | None) -> str:
    """[客户]/[系统] merge so add-car extraction (customer-only) sees full thread."""
    parts: list[str] = []
    if turns:
        for t in turns:
            label = "客户" if (t.role or "").strip().lower() == "customer" else "系统"
            p = _normalize_input(t.text or "")
            if p:
                parts.append(f"[{label}] {p}")
    tail = _normalize_input(text or "")
    if tail:
        parts.append(f"[客户] {tail}")
    return "\n\n".join(parts)


def _add_car_customer_lane(soft_route: str | None, thread_lower: str) -> bool:
    if (soft_route or "").strip().lower() == "add_car":
        return True
    return _is_add_vehicle_request(thread_lower)


def _add_car_structurally_complete_for_persist(
    text: str,
    turns: list[ConversationTurn] | None,
    *,
    labeled_conversation: str | None = None,
) -> bool:
    labeled = (
        labeled_conversation
        if labeled_conversation is not None
        else _conversation_labeled_for_add_car_extract(text, turns)
    )
    fields = _extract_add_car_fields_truth_safe(labeled)
    return _add_car_enough_for_handoff(fields)


def _reply_truth_context_for_triage(
    *,
    case: dict[str, Any] | None,
    formal_submit: bool,
    add_car_lane: bool,
    session_id: str | None = None,
    case_id: str | None = None,
) -> dict[str, Any] | None:
    """
    Structured inputs for Add-Car reply routing (pre- vs post-submit phrasing).
    See triage.triage_conversation(reply_truth_context=...).
    When `case` is loaded (case_id / reopen), includes persisted collected/still_needed so
    triage can reconcile chat extraction with office-visible record truth (append coherence).
    Optional session_id / case_id: passed through for best-effort vehicle entity memory (MVP);
    does not change triage decisions.
    """
    ctx: dict[str, Any] = {}
    sid = (session_id or "").strip()
    if sid:
        ctx["session_id"] = sid
    cid_pass = (case_id or "").strip()
    if cid_pass:
        ctx["case_id"] = cid_pass
    if case:
        fsa = str(case.get("formal_submitted_at") or "").strip()
        if fsa:
            ctx["formal_submitted_at"] = fsa
        ls = str(case.get("lifecycle_status") or "").strip()
        if ls:
            ctx["lifecycle_status"] = ls
        # Service-record contact: sync still_needed / intent ceiling with persisted identity
        cn = str(case.get("customer_name") or "").strip()
        if cn:
            ctx["record_contact_name"] = cn
        cp = str(case.get("customer_phone") or "").strip()
        if cp:
            ctx["record_contact_phone"] = cp
        cf = case.get("collected_fields")
        if isinstance(cf, list) and cf:
            ctx["persisted_collected_fields"] = [str(x) for x in cf if str(x).strip()]
        sn = case.get("still_needed_fields")
        if isinstance(sn, list) and sn:
            ctx["still_needed_fields"] = [str(x) for x in sn if str(x).strip()]
        pq = str(case.get("quote_ready_status") or "").strip()
        if pq in ("quote_ready", "almost_ready", "need_more"):
            ctx["persisted_quote_ready_status"] = pq
        vk = str(case.get("vehicle_key") or "").strip()
        if vk:
            ctx["vehicle_key"] = vk
        if fsa:
            ctx["service_record_continuation"] = True
    if formal_submit and add_car_lane:
        ctx["formal_submit_this_turn"] = True
    return ctx or None


def _attach_assist_layer(
    result: dict[str, Any],
    latest_message: str,
    reply_truth_context: dict[str, Any] | None,
) -> None:
    """Add assist suggestions (additive only). Never blocks HTTP on LLM work."""
    result["assist"] = deepcopy(DEFAULT_ASSIST)
    if not _assist_layer_enabled():
        return
    snap = deepcopy(result)
    msg = latest_message
    ctx = deepcopy(reply_truth_context) if reply_truth_context else None

    def _run() -> None:
        try:
            build_assist_layer(msg, snap, reply_truth_ctx=ctx)
        except Exception:
            logger.debug("assist_layer_background_failed", exc_info=True)

    threading.Thread(target=_run, daemon=True).start()


def _apply_pg_active_vehicle_identity_last(
    result: dict[str, Any],
    session_id: str | None,
) -> None:
    """When Postgres has an active vehicle entity, force API vehicle fields to match it (source of truth)."""
    sid = (session_id or "").strip()
    if not sid:
        return
    row = get_active_vehicle(sid)
    if not row:
        return
    pld = row.get("payload")
    if not isinstance(pld, dict):
        pld = {}
    result["primary_vehicle_summary"] = _primary_vehicle_summary_from_entity_payload(pld)
    result["vehicle_key"] = _vehicle_key_from_entity_payload(pld)
    sync_add_car_client_reply_vehicle_to_primary_summary(result)
    apply_client_reply_finalize_to_result(result, None)


def _attach_case_lifecycle(
    result: dict[str, Any],
    *,
    persisted_case: dict[str, Any] | None = None,
) -> None:
    """Set derived case_lifecycle last (after gates and assist)."""
    view: dict[str, Any] = dict(result)
    if persisted_case:
        pfsa = str(persisted_case.get("formal_submitted_at") or "").strip()
        if pfsa and not str(view.get("formal_submitted_at") or "").strip():
            view["formal_submitted_at"] = persisted_case.get("formal_submitted_at")
    result["case_lifecycle"] = _derive_case_lifecycle(view)


def _finalize_triage_api_result(result: dict[str, Any]) -> None:
    """Stable client contract: append_allowed, lists, case_lifecycle present."""
    if "append_allowed" not in result:
        result["append_allowed"] = True
    sn = result.get("still_needed_fields")
    if not isinstance(sn, list):
        result["still_needed_fields"] = []
    result.setdefault("next_best_question", "")
    result.setdefault("conversion_layer_active", False)
    result.setdefault("conversion_flow_version", "")
    if "case_lifecycle" not in result:
        _attach_case_lifecycle(result)
    apply_client_reply_finalize_to_result(result, None)


def _finalize_triage_http_contract(
    result: dict[str, Any],
    session_id: str | None,
    *,
    persisted_case: dict[str, Any] | None = None,
) -> None:
    """Attach case_lifecycle, apply API contract defaults, then PG active-vehicle overlay."""
    _attach_case_lifecycle(result, persisted_case=persisted_case)
    _finalize_triage_api_result(result)
    _apply_pg_active_vehicle_identity_last(result, session_id)


def _collecting_case_memory_target(
    *,
    existing_case: dict[str, Any] | None,
    result: dict[str, Any],
    text: str,
    effective_case_id: str | None,
) -> str | None:
    """
    When triage runs against a bound open case, return case_id if the customer turn
    should append to Case Memory (case_messages + field lists).
    """
    if not existing_case or not (text or "").strip():
        return None
    bound_id = str(
        result.get("case_id") or effective_case_id or existing_case.get("case_id") or ""
    ).strip()
    if not bound_id:
        return None
    if result.get("append_allowed") is False:
        return None
    if str(result.get("case_boundary") or "").strip() == "new_issue":
        return None
    return bound_id


def _persist_collecting_case_memory(
    *,
    case_id: str,
    text: str,
    result: dict[str, Any],
    existing_case: dict[str, Any],
    client_id: str | None,
) -> dict[str, Any] | None:
    """Append customer turn to bound case; merge triage fields into persisted record."""
    case_client_id = (
        str(existing_case.get("client_id") or "").strip()
        or (client_id or "").strip()
        or None
    )
    return append_follow_up_message(
        case_id=case_id,
        new_message_text=text,
        triage_result=result,
        client_id=case_client_id,
    )


def _user_identity_hint_from_triage(result: dict[str, Any]) -> dict[str, str] | None:
    hint: dict[str, str] = {}
    phone = str(result.get("extracted_contact_phone") or "").strip()
    if phone:
        hint["phone"] = phone[:256]
    name = str(result.get("extracted_contact_name") or "").strip()
    if name:
        hint["name"] = name[:256]
    return hint if hint else None


def _reply_truth_context_from_case(case: dict[str, Any]) -> dict[str, Any] | None:
    """
    Truth bundle for POST .../append-message only.
    Includes persisted gaps for Intent ceiling merges and service_record_append so Add-Car
    replies stay in post-submit / continuation tone (not pre-submit formal-submit nag).
    """
    base = _reply_truth_context_for_triage(case=case, formal_submit=False, add_car_lane=False) or {}
    out: dict[str, Any] = dict(base)
    out["service_record_append"] = True
    return out if out else None


class ConversationTurn(BaseModel):
    """One turn in a customer intake conversation."""

    role: str = Field(..., description="'customer' or 'system'")
    text: str = Field(..., description="Message content")


class TriageRequest(BaseModel):
    """Request body for inbox triage."""

    text: str = Field(
        default="",
        description="Inbound message text. May be empty when inline_image_base64 supplies OCR text.",
    )
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
    formal_submit: bool = Field(
        default=False,
        description=(
            "Add-Car bounded: when triage is handoff_pending, set true to create the office-visible case. "
            "Customer portal sends true only on the formal-submit action; broker/workbench should set true for direct paste."
        ),
    )
    case_id: str | None = Field(
        default=None,
        description=(
            "Optional persisted Unified Intake case id. When set and found, reply routing uses formal_submitted_at / "
            "lifecycle for Add-Car post-submit phrasing (same thread / continued intake)."
        ),
    )
    identity_binding_state: str | None = Field(
        default=None,
        description="Optional Stage-1: unbound | prompted | deferred | linked (light identity stub; not auth).",
    )
    person_link_key: str | None = Field(default=None, description="Optional opaque person link key (nullable).")
    person_link_source: str | None = Field(
        default=None,
        description="Optional: wechat | phone | email when link metadata exists.",
    )
    person_link_confidence: float | None = Field(
        default=None,
        description="Optional 0..1 confidence for person_link (nullable).",
    )
    inline_image_base64: str | None = Field(
        default=None,
        description="Optional raw base64 image body (no data: URL prefix). OCR merges into v6_ocr_signals on triage.",
    )
    inline_image_content_type: str | None = Field(
        default=None,
        description="Optional MIME type for inline_image_base64 (e.g. image/jpeg).",
    )


def _merge_identity_with_session(
    request: TriageRequest,
    *,
    session_co_read_view: dict[str, Any] | None,
) -> dict[str, Any]:
    """Merge optional identity from in-progress session (e.g. WeChat callback) with request fields."""
    pending: dict[str, Any] = {}
    if request.session_id:
        pending_li = None
        if session_co_read_view is not None:
            pending_li = light_identity_binding_from_in_progress_view(session_co_read_view)
        if pending_li:
            pending = dict(pending_li)
    out = merge_light_identity_from_client_payload(
        identity_binding_state=(
            request.identity_binding_state
            if request.identity_binding_state is not None
            else pending.get("identity_binding_state")
        ),
        person_link_key=request.person_link_key if request.person_link_key is not None else pending.get("person_link_key"),
        person_link_source=request.person_link_source if request.person_link_source is not None else pending.get("person_link_source"),
        person_link_confidence=(
            request.person_link_confidence
            if request.person_link_confidence is not None
            else pending.get("person_link_confidence")
        ),
    )
    # If WeChat (or other) link exists on session but UI still sends deferred, keep linked.
    if out.get("person_link_key") and out.get("identity_binding_state") == "deferred":
        out["identity_binding_state"] = "linked"
    return out


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


class CaseWorkbenchRequest(BaseModel):
    """Lightweight workbench flags (test label, soft archive). JSON-first; no hard delete."""

    is_test: bool | None = Field(default=None, description="Mark case as test data for filtering")
    archived: bool | None = Field(default=None, description="Soft-hide / archive for cleanup views")


class RequestMoreItemBody(BaseModel):
    item_type: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=160)
    instructions: str = Field(default="", max_length=1000)
    required: bool = Field(default=True)
    position: int | None = Field(default=None, ge=1)
    request_item_id: str | None = Field(default=None, max_length=128)


class RequestMoreCreateBody(BaseModel):
    command_id: str = Field(..., min_length=8, max_length=128)
    idempotency_key: str = Field(..., min_length=8, max_length=128)
    expected_case_version: int = Field(..., ge=0)
    requested_items: list[RequestMoreItemBody] = Field(..., min_length=1)
    reason: str = Field(default="", max_length=1000)
    request_id: str | None = Field(default=None, max_length=128)
    correlation_id: str | None = Field(default=None, max_length=128)


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
    session_id: str | None = Field(
        default=None,
        description="Optional intake session id — when append is blocked (new vehicle), clears active_case_id.",
    )


def _build_new_issue_append_blocked_response(
    *,
    case: dict[str, Any],
    triage_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Build explicit non-mutating append response when boundary is a clear new issue.
    """
    response: dict[str, Any] = dict(triage_result)
    response.update(
        {
            "case_id": case.get("case_id"),
            "append_blocked_new_issue": True,
            "case_boundary_action": triage_result.get("case_boundary_action") or "requires_new_case",
            "case_boundary": "new_issue",
            "boundary_reason": triage_result.get("boundary_reason")
            or "Detected clear matter separation from current case.",
            "broker_next_step": triage_result.get("broker_next_step") or "",
            "client_reply_draft": triage_result.get("client_reply_draft") or "",
            "conversation_summary": triage_result.get("conversation_summary") or "",
            "service_type": triage_result.get("service_type"),
            "vehicle_key": triage_result.get("vehicle_key"),
            # Existing case stays untouched; lifecycle continues as-is.
            "lifecycle_status": case.get("lifecycle_status") or "office_followup",
            "old_case_mutated": False,
            # Append channel semantics: blocked = no broker-visible update on this record.
            "handoff_ready": False,
            "triage_mode": "append",
            "append_allowed": False,
        }
    )
    response["collected_fields"] = [str(x) for x in (response.get("collected_fields") or []) if str(x).strip()]
    response["still_needed_fields"] = [str(x) for x in (response.get("still_needed_fields") or []) if str(x).strip()]
    return response


def _build_append_blocked_no_mutation_response(
    *,
    case: dict[str, Any],
    triage_result: dict[str, Any],
) -> dict[str, Any]:
    """Non-mutating append response when triage disallows append (e.g. unclear vehicle scope)."""
    response: dict[str, Any] = dict(triage_result)
    response.update(
        {
            "case_id": case.get("case_id"),
            "append_blocked": True,
            "old_case_mutated": False,
            "handoff_ready": False,
            "triage_mode": "append",
            "lifecycle_status": case.get("lifecycle_status") or "office_followup",
            "append_allowed": False,
        }
    )
    response["collected_fields"] = [str(x) for x in (response.get("collected_fields") or []) if str(x).strip()]
    response["still_needed_fields"] = [str(x) for x in (response.get("still_needed_fields") or []) if str(x).strip()]
    return response


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


class SimulationRoleCCustomerRequest(BaseModel):
    """Bounded LLM customer line for Add-Car simulation tab (Role C)."""

    persona_id: str = Field(default="price_sensitive", description="Role C persona key")
    optional_note: str = Field(default="", max_length=220, description="Operator one-line note")
    difficulty: str = Field(default="realistic", description="smooth | realistic | tough")
    max_turns: int = Field(default=6, ge=3, le=12, description="Hard cap on customer turns (simulation; include inject buffer)")
    conversation_turns: list[ConversationTurn] = Field(
        default_factory=list,
        description="Completed replay turns before the next customer message (customer/system pairs).",
    )
    client_id: str | None = Field(
        default=None,
        description="Optional client id for copy context; simulation only.",
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


@router.post("/simulation-role-c-customer")
async def simulation_role_c_customer(request: SimulationRoleCCustomerRequest) -> dict[str, Any]:
    """
    Generate the next Role C (controlled LLM) customer message for Add-Car simulation.
    Requires OPENAI_API_KEY (or LLM_API_KEY) in the runtime; otherwise returns 503.

    Core logic lives in `role_c_simulation_service.next_role_c_customer_line` so scripts
    and the UI share the same bounded generation path.
    """
    prior = request.conversation_turns or []
    conv: list[dict[str, Any]] = [
        {"role": (t.role or "").strip(), "text": _normalize_input(t.text or "")} for t in prior
    ]
    try:
        out = next_role_c_customer_line(
            persona_id=request.persona_id,
            optional_note=request.optional_note or "",
            difficulty=request.difficulty,
            max_turns=request.max_turns,
            conversation_turns=conv,
            client_id=request.client_id,
        )
    except RoleCMaxTurnsReached:
        raise HTTPException(
            status_code=400,
            detail="max_turns reached for Role C replay",
        ) from None

    if not out.customer_message:
        if not out.llm_attempted:
            raise HTTPException(
                status_code=503,
                detail="Role C LLM unavailable (no API key or OpenAI import error). "
                "Set OPENAI_API_KEY on the backend to enable controlled LLM customer lines.",
            )
        raise HTTPException(
            status_code=503,
            detail="Role C LLM call failed or returned empty output; retry or check model availability.",
        )
    return {
        "customer_message": out.customer_message,
        "llm_used": True,
        "model": out.model,
        "turn_index": out.turn_index,
        "max_turns": out.max_turns,
    }


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
    active = get_active_client_id()
    templates = get_reply_templates(active)
    handoff = get_handoff_phrases(active)
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


async def triage_inbox(
    request: TriageRequest,
    org_id: str | None = None,
    http_request: Request | None = None,
) -> dict[str, Any]:
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
    org_id = (org_id or "").strip()[:256] or None
    inline_ocr: tuple[str, dict[str, Any], str] | None = None
    if (request.inline_image_base64 or "").strip():
        inline_ocr = extract_ocr_from_inline_base64(
            request.inline_image_base64 or "",
            request.inline_image_content_type,
        )

    text = _normalize_input(request.text or "")
    if not text and inline_ocr is not None:
        raw0 = str(inline_ocr[0] or "").strip()
        text = _normalize_input(raw0[:4000]) if raw0 else "[image intake]"
    if not text:
        raise HTTPException(
            status_code=400,
            detail="text is required unless inline_image_base64 provides OCR text",
        )

    route_t0 = time.perf_counter()
    _tp = route_t0

    def _route_mark() -> float:
        nonlocal _tp
        now = time.perf_counter()
        ms = (now - _tp) * 1000.0
        _tp = now
        return ms

    emit_session_milestones(
        session_id=request.session_id,
        text=text,
        turns=request.conversation_turns or [],
        client_asserted_org_id=org_id,
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
            "triage_mode": "greenfield",
        }
        _attach_assist_layer(result, text, None)
        _finalize_triage_http_contract(result, request.session_id)
        ta_turns = request.conversation_turns or []
        if request.persist_case:
            try:
                source = f"[客户] {text}"
                saved = save_case(
                    source,
                    result,
                    client_id=client_id,
                    asserted_org_id=org_id,
                )
                saved["assist"] = result.get("assist")
                _finalize_triage_http_contract(saved, request.session_id)
                cid = str(saved.get("case_id") or "")
                emit_case_created_milestone(
                    saved,
                    turns=ta_turns,
                    text=text,
                    session_id=request.session_id,
                    case_id=cid,
                    client_asserted_org_id=org_id,
                )
                track_event(
                    "case_created",
                    {"case_id": cid, "session_id": request.session_id}
                    | ({"org_id": org_id} if org_id else {}),
                )
                _schedule_route_analytics(
                    saved,
                    ta_turns,
                    session_id=request.session_id,
                    text=text,
                    org_id=org_id,
                )
                _attach_route_perf_ms(
                    saved,
                    {
                        "route_total_ms": (time.perf_counter() - route_t0) * 1000.0,
                        "triage_ms": 0.0,
                        "session_ms": 0.0,
                        "case_ms": 0.0,
                        "assist_ms": 0.0,
                        "conversion_ms": 0.0,
                        "postprocess_ms": 0.0,
                        "postprocess_finalize_ms": 0.0,
                        "postprocess_after_finalize_ms": 0.0,
                    },
                )
                return saved
            except Exception as exc:
                logger.exception("Failed to persist Talk-to-Agent case: %s", exc)
                result["case_persisted"] = False
        _schedule_route_analytics(
            result,
            ta_turns,
            session_id=request.session_id,
            text=text,
            org_id=org_id,
        )
        _attach_route_perf_ms(
            result,
            {
                "route_total_ms": (time.perf_counter() - route_t0) * 1000.0,
                "triage_ms": 0.0,
                "session_ms": 0.0,
                "case_ms": 0.0,
                "assist_ms": 0.0,
                "conversion_ms": 0.0,
                "postprocess_ms": 0.0,
                "postprocess_finalize_ms": 0.0,
                "postprocess_after_finalize_ms": 0.0,
            },
        )
        return result

    # MULTI_TURN_CONTINUITY_GUARDRAIL: First message must go through triage_conversation,
    # not triage_message + forced handoff_ready. Use triage_conversation(text, []) for first turn.
    _tp = time.perf_counter()
    turns = request.conversation_turns or []
    soft_route_hint = (request.soft_route or "").strip().lower() or None
    thread_lower = _full_thread_lower(text, turns)
    add_car_lane_pre = _add_car_customer_lane(soft_route_hint, thread_lower)

    sid = (request.session_id or "").strip()
    session_full_row = intake_session_repository.get_session(sid) if sid else None
    sess_raw = in_progress_session_view(session_full_row)
    # Session office assertion changed mid-flight — drop sticky case binding (honest multi-office UX).
    if sid and sess_raw and org_id:
        prev_sess_org = str(sess_raw.get("asserted_org_id") or "").strip()
        ro = str(org_id).strip()
        if prev_sess_org and ro and prev_sess_org != ro:
            cleared_so = patch_session_case_binding(
                sid, clear_active_case=True, reuse_session_row=session_full_row
            )
            if cleared_so is not None:
                session_full_row = cleared_so
                sess_raw = in_progress_session_view(session_full_row)
            logger.info(
                "session_office_assertion_shift_cleared_active_case session_id=%s prev_org=%s request_org=%s",
                sid,
                prev_sess_org,
                ro,
            )
    if sess_raw:
        prev_turns = sess_raw.get("turns") or []
        if isinstance(prev_turns, list):
            for t in reversed(prev_turns):
                if str(t.get("role") or "").strip().lower() != "system":
                    continue
                tr = t.get("triageResult") or t.get("triage_result")
                if isinstance(tr, dict) and str(tr.get("quote_ready_status") or "").strip() == "quote_ready":
                    append_session_analytics_event(
                        "user_response_after_quote_ready",
                        session_id=sid,
                        case_id=None,
                        metadata={},
                    )
                    track_event("user_response_after_quote_ready", {})
                break
    session_ms_seg1 = _route_mark()
    labeled_for_vk = _conversation_labeled_for_add_car_extract(text, turns)
    incoming_vehicle_key = _derive_vehicle_key_from_add_car_text(labeled_for_vk)
    explicit_case_id = (request.case_id or "").strip() or None
    resolved_case_id: str | None = None
    sess_for_resolve: dict[str, Any] | None = None
    session_active_case_row: dict[str, Any] | None = None
    recent_for_bind: list[dict[str, Any]] | None = None
    if sid and sess_raw:
        sess_for_resolve = dict(sess_raw)
        sac0 = str(sess_for_resolve.get("active_case_id") or "").strip()
        if sac0:
            sc0 = get_case_triage_stub_for_read(sac0)
            stale_office_bind = False
            if sc0 and org_id:
                co = str(sc0.get("asserted_org_id") or "").strip()
                ro = str(org_id).strip()
                if ro and co and co != ro:
                    stale_office_bind = True
            if not sc0 or not is_case_open_for_binding(sc0) or stale_office_bind:
                if stale_office_bind:
                    logger.info(
                        "active_case_cleared_wrong_office_hint session_id=%s case_id=%s case_org=%s request_org=%s",
                        sid,
                        sac0,
                        str((sc0 or {}).get("asserted_org_id") or ""),
                        str(org_id or ""),
                    )
                sess_for_resolve.pop("active_case_id", None)
                cleared = patch_session_case_binding(
                    sid, clear_active_case=True, reuse_session_row=session_full_row
                )
                if cleared is not None:
                    session_full_row = cleared
                    sess_raw = in_progress_session_view(session_full_row)
            else:
                session_active_case_row = sc0
    if not explicit_case_id and sid:
        # Fast path: session already has active_case_id — resolve without scanning recent cases
        if sess_for_resolve and str(sess_for_resolve.get("active_case_id") or "").strip():
            resolved_case_id = resolve_active_case(
                sess_for_resolve, [], incoming_vehicle_key
            )
        if resolved_case_id is None:
            recent_for_bind = list_recent_cases_for_binding(
                limit=_case_bind_recent_limit(),
                offset=0,
                client_asserted_org_id=org_id,
            )
            resolved_case_id = resolve_active_case(
                sess_for_resolve, recent_for_bind, incoming_vehicle_key
            )
        track_event("case_binding_decision", {"resolved": resolved_case_id is not None})
    effective_case_id = explicit_case_id or resolved_case_id
    existing_case: dict[str, Any] | None = None
    if effective_case_id:
        ec = (effective_case_id or "").strip()
        sac_id = (
            str(session_active_case_row.get("case_id") or "").strip()
            if isinstance(session_active_case_row, dict)
            else ""
        )
        if session_active_case_row and sac_id and sac_id == ec:
            existing_case = session_active_case_row
        else:
            picked: dict[str, Any] | None = None
            if recent_for_bind:
                for c in recent_for_bind:
                    if str(c.get("case_id") or "").strip() == ec:
                        picked = c
                        break
            if picked is not None:
                # Shallow copy: route + reply_truth only read case fields; v6 merge returns new dicts.
                existing_case = dict(picked)
            else:
                existing_case = get_case_triage_stub_for_read(ec)
    if effective_case_id and existing_case is None:
        effective_case_id = None

    if existing_case is not None and http_request is not None:
        assert_case_office_access_allowed(http_request, existing_case)

    reply_truth_ctx = _reply_truth_context_for_triage(
        case=existing_case,
        formal_submit=bool(request.formal_submit),
        add_car_lane=add_car_lane_pre,
        session_id=sid,
        case_id=effective_case_id or None,
    )
    prior_ws: dict[str, Any] | None = None
    if sess_raw and isinstance(sess_raw.get("workflow_state"), dict):
        prior_ws = dict(sess_raw["workflow_state"])
    _v6_ocr = None
    if existing_case and isinstance(existing_case.get("v6_ocr_signals"), dict):
        _v6_ocr = existing_case.get("v6_ocr_signals")
    if inline_ocr is not None:
        raw_txt, sf, eng = inline_ocr
        _v6_ocr = merge_v6_ocr_signals(
            _v6_ocr,
            raw_text=raw_txt,
            structured_fields=sf if isinstance(sf, dict) else {},
            engine=eng,
            attachment_id="inline_image",
        )
    case_ms_total = _route_mark()
    result = triage_conversation(
        text,
        [{"role": t.role, "text": t.text} for t in turns],
        client_id=client_id,
        reply_truth_context=reply_truth_ctx,
        prior_workflow_state=prior_ws,
        v6_ocr_signals=_v6_ocr,
        soft_route=soft_route_hint,
    )
    triage_ms_total = _route_mark()

    # Rerouting: when soft_route from button conflicts with inferred intent from text, acknowledge
    if soft_route_hint:
        reroute_messages, soft_route_starter_replies = get_soft_route_inbox_copy()
        inferred = _infer_intent_from_result(text, result)
        # Compatible pairs: remove_car + renewal_premium (both policy-related)
        compatible = (soft_route_hint == "remove_car" and inferred == "renewal_premium") or (
            soft_route_hint == "renewal_premium" and inferred == "remove_car"
        )
        if inferred and inferred != soft_route_hint and not compatible:
            result["reroute_occurred"] = True
            result["reroute_message"] = reroute_messages.get(
                inferred, "看起来这是不同的问题，我先帮您处理这个。"
            )
            result["previous_soft_route"] = soft_route_hint
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
        if is_generic and soft_route_hint in soft_route_starter_replies:
            skip_add_car_starter = soft_route_hint == "add_car" and (
                text_has_vehicle_make_model_signal(thread_lower)
                or text_has_vehicle_year_signal(thread_lower)
            )
            if skip_add_car_starter:
                pass
            else:
                result["client_reply_draft"] = soft_route_starter_replies[soft_route_hint]
                result["issue_category"] = (
                    "payment_lapse_expiration"
                    if soft_route_hint == "cancellation_warning"
                    else "customer_question"
                )
            if soft_route_hint == "add_car" and not skip_add_car_starter:
                result["collected_fields"] = []
                result["still_needed_fields"] = ["year", "make_model", "zip"]
            elif soft_route_hint == "add_car" and skip_add_car_starter:
                pass
            elif soft_route_hint == "claim_intake":
                result["collected_fields"] = []
                result["still_needed_fields"] = ["accident_time", "accident_location", "photos"]
            elif soft_route_hint == "cancellation_warning":
                result["collected_fields"] = []
                result["still_needed_fields"] = ["payment_notice_or_screenshot"]
            elif soft_route_hint == "missing_document":
                result["collected_fields"] = []
                result["still_needed_fields"] = ["full_notice", "requested_documents"]
            elif soft_route_hint == "remove_car":
                result["collected_fields"] = []
                result["still_needed_fields"] = ["sale_date", "vehicle_info", "transfer_status"]

    conversion_ms_total = _route_mark()

    if existing_case and existing_case.get("case_id") and not result.get("case_id"):
        result["case_id"] = existing_case.get("case_id")

    _attach_assist_layer(result, text, reply_truth_ctx)
    assist_ms_total = _route_mark()

    if sid:
        boundary_clear = result.get("append_allowed") is False and str(
            result.get("case_boundary_action") or ""
        ).strip() == "requires_new_case"
        if boundary_clear:
            logger.info(
                "append_blocked_reason case_boundary_action=%s boundary_reason=%s session_id=%s",
                result.get("case_boundary_action"),
                (result.get("boundary_reason") or "")[:500],
                sid,
            )
            cleared = patch_session_case_binding(sid, clear_active_case=True, reuse_session_row=session_full_row)
            if cleared is not None:
                session_full_row = cleared
                sess_raw = in_progress_session_view(session_full_row)
        else:
            patch_kw: dict[str, Any] = {}
            if effective_case_id:
                patch_kw["active_case_id"] = effective_case_id
            vk_r = result.get("vehicle_key")
            if isinstance(vk_r, str) and vk_r.strip():
                patch_kw["last_vehicle_key"] = vk_r.strip()
            uh = _user_identity_hint_from_triage(result)
            if uh:
                patch_kw["user_identity_hint"] = uh
            if patch_kw:
                patched = patch_session_case_binding(sid, reuse_session_row=session_full_row, **patch_kw)
                if patched is not None:
                    session_full_row = patched
                    sess_raw = in_progress_session_view(session_full_row)

    session_ms_seg2 = _route_mark()
    case_persist_ms_total = 0.0

    if request.persist_case:
        # MULTI_TURN_CONTINUITY_GUARDRAIL: Only persist when handoff_ready to avoid
        # premature cases and duplicate cases across turns.
        # PERSIST_FORMAL_SUBMIT_ALIGNMENT: Add-Car lane requires formal_submit before save_case.
        # Last turn may be boilerplate-only; triage can drop handoff_ready — still persist when
        # formal_submit + rule-complete thread (same structured bar as handoff).
        add_car_lane = add_car_lane_pre
        handoff_ready = bool(result.get("handoff_ready"))
        formal = bool(request.formal_submit)
        struct_ok = _add_car_structurally_complete_for_persist(
            text, turns, labeled_conversation=labeled_for_vk
        )
        if add_car_lane:
            should_persist = formal and (struct_ok or handoff_ready)
        else:
            should_persist = handoff_ready
        if should_persist:
            try:
                _t_p0 = time.perf_counter()
                if turns:
                    conv_parts = []
                    for t in turns:
                        label = "客户" if (t.role or "").strip().lower() == "customer" else "系统"
                        conv_parts.append(f"[{label}] {_normalize_input(t.text or '')}")
                    conv_parts.append(f"[客户] {text}")
                    source_for_case = "\n\n".join(p for p in conv_parts if p)
                else:
                    source_for_case = text
                identity_patch = _merge_identity_with_session(request, session_co_read_view=sess_raw)
                if identity_patch:
                    result.update(identity_patch)
                _apply_pg_active_vehicle_identity_last(result, request.session_id)
                saved = save_case(
                    source_for_case or text,
                    result,
                    origin_session_id=request.session_id.strip() if request.session_id else None,
                    client_id=client_id,
                    asserted_org_id=org_id,
                    service_lane=SERVICE_LANE_ADD_CAR if add_car_lane else None,
                )
                if request.session_id:
                    vk_save = saved.get("vehicle_key") if isinstance(saved.get("vehicle_key"), str) else None
                    save_session_binding_after_case_created(
                        request.session_id.strip(),
                        str(saved.get("case_id") or ""),
                        vk_save,
                        reuse_session_row=session_full_row,
                        asserted_org_id=str(saved.get("asserted_org_id") or "").strip()[:256]
                        or (org_id.strip() if org_id else None),
                    )
                case_persist_ms_total = (time.perf_counter() - _t_p0) * 1000.0
                logger.info(
                    "new_case_created case_id=%s client_id=%s",
                    saved.get("case_id"),
                    client_id,
                )
                cid = str(saved.get("case_id") or "")
                emit_case_created_milestone(
                    saved,
                    turns=turns,
                    text=text,
                    session_id=request.session_id,
                    case_id=cid,
                    client_asserted_org_id=org_id,
                )
                track_event(
                    "case_created",
                    {"case_id": cid, "session_id": request.session_id}
                    | ({"org_id": org_id} if org_id else {}),
                )
                saved["assist"] = result.get("assist")
                _finalize_triage_http_contract(saved, request.session_id)
                _schedule_route_analytics(
                    saved,
                    turns,
                    session_id=request.session_id,
                    text=text,
                    org_id=org_id,
                )
                _attach_route_perf_ms(
                    saved,
                    {
                        "route_total_ms": (time.perf_counter() - route_t0) * 1000.0,
                        "triage_ms": triage_ms_total,
                        "session_ms": session_ms_seg1 + session_ms_seg2,
                        "case_ms": case_ms_total + case_persist_ms_total,
                        "assist_ms": assist_ms_total,
                        "conversion_ms": conversion_ms_total,
                        "postprocess_ms": 0.0,
                        "postprocess_finalize_ms": 0.0,
                        "postprocess_after_finalize_ms": 0.0,
                    },
                )
                return saved
            except Exception as exc:
                logger.exception("Failed to persist Unified Intake case: %s", exc)
                result["case_persisted"] = False
        else:
            result["case_persisted"] = False

    collecting_memory_case: dict[str, Any] | None = None
    memory_target = _collecting_case_memory_target(
        existing_case=existing_case,
        result=result,
        text=text,
        effective_case_id=effective_case_id,
    )
    if memory_target:
        try:
            _t_cm0 = time.perf_counter()
            updated = _persist_collecting_case_memory(
                case_id=memory_target,
                text=text,
                result=result,
                existing_case=existing_case or {},
                client_id=client_id,
            )
            case_persist_ms_total += (time.perf_counter() - _t_cm0) * 1000.0
            if updated is not None:
                assist_snap = result.get("assist")
                result.update(updated)
                if assist_snap is not None:
                    result["assist"] = assist_snap
                collecting_memory_case = updated
                logger.info("collecting_case_memory_appended case_id=%s", memory_target)
        except ValueError:
            pass
        except Exception as exc:
            logger.warning("Failed to persist collecting case memory: %s", exc)

    _finalize_triage_http_contract(
        result,
        request.session_id,
        persisted_case=collecting_memory_case or existing_case,
    )
    postprocess_finalize_ms = _route_mark()
    _schedule_route_analytics(
        result,
        turns,
        session_id=request.session_id,
        text=text,
        org_id=org_id,
    )

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
                # Repo-shaped co-read only (not API view); None on cold session => assume_fresh_co_read.
                pre_read_raw=session_full_row,
                assume_fresh_co_read=True,
                asserted_org_id=org_id,
            )
        except Exception as exc:
            logger.warning("Failed to save in-progress session: %s", exc)
        result["conversation_id"] = request.session_id.strip()
    postprocess_after_finalize_ms = _route_mark()
    postprocess_ms_total = postprocess_finalize_ms + postprocess_after_finalize_ms
    _attach_route_perf_ms(
        result,
        {
            "route_total_ms": (time.perf_counter() - route_t0) * 1000.0,
            "triage_ms": triage_ms_total,
            "session_ms": session_ms_seg1 + session_ms_seg2,
            "case_ms": case_ms_total + case_persist_ms_total,
            "assist_ms": assist_ms_total,
            "conversion_ms": conversion_ms_total,
            "postprocess_ms": postprocess_ms_total,
            "postprocess_finalize_ms": postprocess_finalize_ms,
            "postprocess_after_finalize_ms": postprocess_after_finalize_ms,
        },
    )
    return result


@router.post("/triage")
@_inbox_triage_request_cache_route
async def triage_inbox_http(
    body: TriageRequest,
    http_request: Request,
    x_org_id: str | None = Header(default=None, alias="X-Org-Id"),
) -> dict[str, Any]:
    oid = getattr(http_request.state, "client_asserted_org_id", None)
    if oid is None:
        oid = (x_org_id or "").strip()[:256] or None
    return await triage_inbox(body, oid, http_request)


@router.get("/cases")
async def get_recent_cases(
    http_request: Request,
    limit: int = Query(default=50, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=5000),
    include_raw_inbound: bool = Query(
        default=False,
        description="P19H-3f-1c debug: include raw inbound (wecom_media_intake) in broker queue list",
    ),
) -> dict[str, Any]:
    """
    Return recent persisted Unified Intake cases (newest first), with pagination metadata.

    Default excludes pre-Start-Ceremony raw inbound (wecom_media_intake). Pass
    include_raw_inbound=true for technical/debug views only.

    total_count is the full persisted queue size; limit/offset describe this response slice only.
    """
    if case_office_enforcement_enabled():
        req_org = client_asserted_office_id(http_request)
        if not req_org:
            raise HTTPException(
                status_code=403,
                detail="office_assertion_required_for_case_list_v1",
            )
        raw, total = list_cases_for_office_enforcement_read(
            req_org,
            limit=limit,
            offset=offset,
            exclude_raw_inbound=not include_raw_inbound,
        )
    elif case_client_enforcement_enabled():
        raw, total = list_cases_for_client_scoped_read(
            resolve_server_client_id(),
            limit=limit,
            offset=offset,
            exclude_raw_inbound=not include_raw_inbound,
        )
    elif include_raw_inbound:
        total = count_cases_for_read()
        raw = list_recent_cases_for_read(limit=limit, offset=offset)
    else:
        raw, total = list_broker_workbench_cases_for_read(limit=limit, offset=offset)
    try:
        from services.fiqa_api.inbox_triage.workbench_enrichment import enrich_cases_for_workbench

        enriched = enrich_cases_for_workbench(raw)
    except Exception as exc:
        logger.warning("Workbench enrich failed, returning raw cases: %s", exc)
        enriched = raw
    from services.fiqa_api.inbox_triage.p20_slice1_command_service import (
        redact_case_slice1_responses_for_list,
    )

    safe_cases = [
        redact_case_slice1_responses_for_list(sanitize_case_for_workbench_api(c))
        for c in enriched
    ]
    return {
        "cases": safe_cases,
        "total_count": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(safe_cases) < total,
    }


@router.get("/customer/active-case")
async def get_customer_active_case_by_phone(
    phone: str = Query(..., min_length=1, max_length=32),
    client_id: str | None = Query(default=None, max_length=128),
) -> dict[str, Any]:
    """
    P16 Customer First — phone return-key lookup for one active add-car case.

    No auth; customer-facing. Returns has_active_case=false when none or phone invalid.
    """
    if not is_valid_customer_phone(phone):
        raise HTTPException(status_code=400, detail="invalid_phone")
    normalized = normalize_phone_digits(phone)
    cid = (client_id or "").strip() or None
    candidates = list_cases_for_phone_lookup(normalized, client_id=cid)
    match = find_active_add_car_case_by_phone(normalized, candidates, client_id=cid)
    if match is None:
        return {
            "has_active_case": False,
            "phone_normalized": normalized,
            "active_case": None,
        }
    return {
        "has_active_case": True,
        "phone_normalized": normalized,
        "active_case": active_add_car_case_summary(match),
    }


class CustomerStartAddCarRequest(BaseModel):
    """P16 Customer First — start new add-car draft after phone entry (Rule 7 enforced)."""

    phone: str = Field(..., min_length=1, max_length=32)
    customer_name: str | None = Field(default=None, max_length=128)
    client_id: str | None = Field(default=None, max_length=128)
    session_id: str | None = Field(default=None, max_length=128)


@router.post("/customer/start-add-car")
async def post_customer_start_add_car(body: CustomerStartAddCarRequest) -> dict[str, Any]:
    """
    Create a collecting-phase add-car draft with claimed phone, or reject when active case exists.
    """
    if not is_valid_customer_phone(body.phone):
        raise HTTPException(status_code=400, detail="invalid_phone")
    normalized = normalize_phone_digits(body.phone)
    cid = (body.client_id or "").strip() or None
    sid = (body.session_id or "").strip() or None
    candidates = list_cases_for_phone_lookup(normalized, client_id=cid)
    existing = find_active_add_car_case_by_phone(normalized, candidates, client_id=cid)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "active_case_exists",
                "active_case": active_add_car_case_summary(existing),
            },
        )
    try:
        saved = create_customer_first_add_car_draft(
            normalized,
            customer_name=body.customer_name,
            client_id=cid,
            origin_session_id=sid,
        )
    except ValueError as exc:
        if str(exc) == "active_case_exists":
            raise HTTPException(status_code=409, detail="active_case_exists") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if sid:
        vk = saved.get("vehicle_key") if isinstance(saved.get("vehicle_key"), str) else None
        save_session_binding_after_case_created(sid, str(saved.get("case_id") or ""), vk)
    return {
        "ok": True,
        "case_id": saved.get("case_id"),
        "case": active_add_car_case_summary(saved),
    }


@router.get("/cases/{case_id}")
async def get_saved_case(case_id: str, http_request: Request) -> dict[str, Any]:
    """Return one persisted case with full stored fields (messages/activity when available)."""
    cid = (case_id or "").strip()
    if not cid:
        raise HTTPException(status_code=400, detail="case_id required")
    case = get_case_for_read(cid)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    assert_case_office_access_allowed(http_request, case)
    assert_case_client_access_allowed(http_request, case)
    try:
        from services.fiqa_api.inbox_triage.workbench_enrichment import enrich_cases_for_workbench

        enriched = enrich_cases_for_workbench([case])
        case = enriched[0] if enriched else case
    except Exception as exc:
        logger.warning("Workbench enrich failed for case %s, returning raw case: %s", cid, exc)
    # Rebuild Slice 1 broker projection from companion/event SSOT so satisfied
    # item responses (e.g. submitted VIN) are visible on case detail.
    try:
        live_projection = default_slice1_service().fetch_projection(cid)
        if isinstance(live_projection, dict):
            case["p20_slice1_projection"] = live_projection
            case["slice1_projection"] = live_projection
            open_request = live_projection.get("open_request")
            if isinstance(open_request, dict):
                case["p20_slice1_request_summary"] = open_request
                case["slice1_request_summary"] = open_request
    except Exception as exc:
        logger.warning("Slice 1 projection refresh failed for case %s: %s", cid, exc)
    return sanitize_case_for_workbench_api(case)


def _broker_actor_identity(http_request: Request) -> str:
    office_id = client_asserted_office_id(http_request)
    if office_id:
        return f"office:{office_id}"
    client_id = resolve_server_client_id()
    if client_id:
        return f"client:{client_id}"
    raise HTTPException(status_code=403, detail="broker_actor_identity_required")


@router.post("/cases/{case_id}/request-more")
async def post_case_request_more(
    case_id: str,
    body: RequestMoreCreateBody,
    http_request: Request,
    http_response: Response,
) -> dict[str, Any]:
    """Slice 1 broker command: create one structured ordered Request More group."""
    row = get_case_for_read(case_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    assert_case_office_access_allowed(http_request, row)
    broker_identity = _broker_actor_identity(http_request)
    try:
        result = default_slice1_service().accept_request_more(
            case_id=case_id,
            broker_id=broker_identity,
            command_id=body.command_id,
            idempotency_key=body.idempotency_key,
            expected_case_version=body.expected_case_version,
            requested_items=[item.dict() for item in body.requested_items],
            reason=body.reason,
            request_id=body.request_id,
            correlation_id=body.correlation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": str(exc)}) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    outcome = str(result.get("outcome") or "")
    if outcome == "accepted":
        http_response.status_code = 201
        return result
    if outcome == "replayed":
        http_response.status_code = 200
        return result
    if outcome == "conflict":
        raise HTTPException(status_code=409, detail=result)
    raise HTTPException(status_code=422, detail=result)


@router.delete("/cases/{case_id}")
async def delete_saved_case_test_only(case_id: str, http_request: Request) -> dict[str, Any]:
    """
    Remove a persisted case from storage (JSON and/or Postgres when enabled).

    Allowed only for cases marked workbench_test — formal records cannot be deleted via this path.
    """
    cid = (case_id or "").strip()
    if not cid:
        raise HTTPException(status_code=400, detail="case_id required")
    existing = get_case_for_read(cid)
    if existing is None:
        raise HTTPException(status_code=404, detail="case not found")
    assert_case_office_access_allowed(http_request, existing)
    if not bool(existing.get("workbench_test")):
        raise HTTPException(
            status_code=403,
            detail="only test-marked service records can be deleted; mark as test first or archive instead",
        )
    if not delete_case(cid):
        raise HTTPException(status_code=500, detail="delete failed")
    return {"ok": True, "deleted_case_id": cid}


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
async def patch_case_status(
    case_id: str, request: CaseStatusRequest, http_request: Request
) -> dict[str, Any]:
    """Update the lightweight broker workflow status for a saved case."""
    row = get_case_for_read(case_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    assert_case_office_access_allowed(http_request, row)
    try:
        updated = update_case_status(case_id=case_id, status=request.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    return updated


@router.post("/cases/{case_id}/notes")
async def create_case_note(
    case_id: str, request: CaseNoteRequest, http_request: Request
) -> dict[str, Any]:
    """Add one lightweight broker note to a saved case."""
    row = get_case_for_read(case_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    assert_case_office_access_allowed(http_request, row)
    try:
        updated = add_case_note(case_id=case_id, note_text=request.note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    return updated


@router.patch("/cases/{case_id}/follow-up")
async def patch_case_follow_up(
    case_id: str, request: CaseFollowUpRequest, http_request: Request
) -> dict[str, Any]:
    """Update lightweight follow-up target + timing for a saved case."""
    row = get_case_for_read(case_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    assert_case_office_access_allowed(http_request, row)
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
async def patch_case_customer(
    case_id: str, request: CaseCustomerRequest, http_request: Request
) -> dict[str, Any]:
    """Update lightweight customer linkage fields on a saved case."""
    row = get_case_for_read(case_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    assert_case_office_access_allowed(http_request, row)
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


@router.patch("/cases/{case_id}/workbench")
async def patch_case_workbench(
    case_id: str, request: CaseWorkbenchRequest, http_request: Request
) -> dict[str, Any]:
    """Update workbench test/archive flags (soft-hide). With DB-primary writes, Postgres extra wins."""
    row = get_case_for_read(case_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    assert_case_office_access_allowed(http_request, row)
    updated = update_case_workbench_flags(
        case_id=case_id,
        is_test=request.is_test,
        archived=request.archived,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    try:
        from services.fiqa_api.inbox_triage.workbench_enrichment import enrich_cases_for_workbench

        enriched = enrich_cases_for_workbench([updated])
        return enriched[0] if enriched else updated
    except Exception:
        return updated


@router.patch("/cases/{case_id}/confirm")
async def patch_case_confirm(case_id: str, http_request: Request) -> dict[str, Any]:
    """
    Track B0.3 — Broker Confirm. Sets `broker_confirmed_at` (additive, once)
    and sends exactly ONE Done Card to the customer via existing WeCom send
    APIs. Idempotent: safe to call twice (second call is a no-op, no second
    Done Card). No resolver changes — `active_case_resolver.py` untouched.

    Governed by docs/p16/TRACK_B0_ACTIVE_WORKSPACE_CONTRACT.md §7/§9.
    """
    row = get_case_for_read(case_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    assert_case_office_access_allowed(http_request, row)
    try:
        result = confirm_case_by_broker(case_id)
    except BrokerConfirmError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result.get("outcome") == "case_not_found" or result.get("case") is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    updated = dict(result["case"])
    updated["done_card_sent"] = result.get("done_card_sent", False)
    updated["already_confirmed"] = result.get("already_confirmed", False)
    return updated


@router.post("/cases/{case_id}/broker-done")
async def post_case_broker_done(case_id: str, http_request: Request) -> dict[str, Any]:
    """
    P19H-3f-2 — Claim True End Card on broker/office done.

    Only formal Claim cases (service_lane=claim). Raw inbound rejected.
    Idempotent: second POST does not duplicate broker_done timeline or End Card.
    """
    row = get_case_for_read(case_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    assert_case_office_access_allowed(http_request, row)
    try:
        result = mark_claim_broker_done(case_id, source="workbench")
    except ClaimBrokerDoneError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result.get("outcome") == "case_not_found" or result.get("case") is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    updated = dict(result["case"])
    try:
        from services.fiqa_api.inbox_triage.workbench_enrichment import enrich_cases_for_workbench

        enriched = enrich_cases_for_workbench([updated])
        updated = enriched[0] if enriched else updated
    except Exception:
        pass
    updated["already_done"] = result.get("already_done", False)
    updated["end_card_sent"] = result.get("end_card_sent", False)
    updated["end_card_preview"] = result.get("end_card_preview")
    updated["end_card_send_skipped"] = result.get("send_skipped", True)
    if result.get("end_card_send_reason"):
        updated["end_card_send_reason"] = result.get("end_card_send_reason")
    return updated


@router.post("/cases/{case_id}/attachments")
async def upload_case_attachment(
    case_id: str, http_request: Request, file: UploadFile = File(...)
) -> dict[str, Any]:
    """
    Upload an attachment to a case. ADD_CAR_ATTACHMENT_READY_LITE.
    Accepts: image/*, application/pdf. Max 10 MB.
    """
    case = get_case_for_read(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    assert_case_office_access_allowed(http_request, case)
    content = await file.read()
    filename = file.filename or "attachment"
    content_type = file.content_type or ""
    try:
        updated = add_attachment_to_case(
            case_id=case_id,
            filename=filename,
            content=content,
            content_type=content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    return updated


@router.get("/cases/{case_id}/attachments/{attachment_id}")
async def download_case_attachment(
    case_id: str, attachment_id: str, http_request: Request
):
    """Download an attachment file. ADD_CAR_ATTACHMENT_READY_LITE."""
    row = get_case_for_read(case_id)
    if row is None:
        raise HTTPException(status_code=404, detail="case not found")
    assert_case_office_access_allowed(http_request, row)
    path = get_attachment_file_path(case_id, attachment_id)
    if path is None:
        raise HTTPException(status_code=404, detail="attachment not found")
    return FileResponse(path, filename=path.name.split("_", 1)[-1] if "_" in path.name else path.name)


@router.get("/cases/{case_id}/attachments/{attachment_id}/preview")
async def preview_case_attachment(
    case_id: str, attachment_id: str, http_request: Request
) -> Response:
    """
    Auth-gated attachment preview (P19B).

    Streams local filesystem or private GCS WeCom media — never exposes signed/public URL.
    """
    row = get_case_for_read(case_id)
    if row is None:
        raise HTTPException(status_code=404, detail="case not found")
    assert_case_office_access_allowed(http_request, row)
    t0 = time.perf_counter()
    try:
        content, media_type, filename = resolve_attachment_preview(row, attachment_id)
    except FileNotFoundError:
        total_ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.info(
            "PREVIEW_PERF case_id=%s attachment_id=%s total_ms=%s gcs_ms=0 bytes=0 status=not_found",
            case_id,
            attachment_id,
            total_ms,
        )
        raise HTTPException(status_code=404, detail="attachment not found") from None
    except ValueError:
        total_ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.info(
            "PREVIEW_PERF case_id=%s attachment_id=%s total_ms=%s gcs_ms=0 bytes=0 status=not_found",
            case_id,
            attachment_id,
            total_ms,
        )
        raise HTTPException(status_code=404, detail="attachment not found") from None
    except Exception as exc:
        total_ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.warning(
            "attachment_preview_failed case_id=%s attachment_id=%s err=%s",
            case_id,
            attachment_id,
            exc,
        )
        logger.info(
            "PREVIEW_PERF case_id=%s attachment_id=%s total_ms=%s gcs_ms=0 bytes=0 status=error",
            case_id,
            attachment_id,
            total_ms,
        )
        raise HTTPException(status_code=404, detail="attachment not found") from exc
    total_ms = round((time.perf_counter() - t0) * 1000, 1)
    gcs_ms = consume_preview_gcs_ms() or 0
    logger.info(
        "PREVIEW_PERF case_id=%s attachment_id=%s total_ms=%s gcs_ms=%s bytes=%s status=ok",
        case_id,
        attachment_id,
        total_ms,
        gcs_ms,
        len(content),
    )
    headers: dict[str, str] = {}
    if filename:
        headers["Content-Disposition"] = f'inline; filename="{filename}"'
    return Response(content=content, media_type=media_type, headers=headers)


@router.post("/cases/{case_id}/append-message")
@_active_vehicle_cache_route
async def append_case_message(
    case_id: str,
    request: AppendMessageRequest,
    http_request: Request,
) -> dict[str, Any]:
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
    case = get_case_for_read(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    assert_case_office_access_allowed(http_request, case)
    try:
        case_client_id = (case.get("client_id") or "").strip() or (request.client_id or "").strip() or None
        _v6_append = case.get("v6_ocr_signals")
        triage_result = triage_for_append(
            existing_source_text=case.get("source_text", ""),
            new_message=new_msg,
            client_id=case_client_id,
            reply_truth_context=_reply_truth_context_from_case(case),
            v6_ocr_signals=_v6_append if isinstance(_v6_append, dict) else None,
        )
        if str(triage_result.get("case_boundary") or "").strip() == "new_issue":
            blocked = _build_new_issue_append_blocked_response(case=case, triage_result=triage_result)
            _attach_assist_layer(blocked, new_msg, _reply_truth_context_from_case(case))
            _finalize_triage_http_contract(blocked, request.session_id, persisted_case=case)
            ap_sid = (request.session_id or "").strip() or None
            append_session_analytics_event(
                "append_blocked",
                session_id=ap_sid,
                case_id=case_id,
                metadata={"reason": blocked.get("case_boundary_action")},
            )
            track_event("append_blocked", {"reason": blocked.get("case_boundary_action")})
            if ap_sid and str(blocked.get("case_boundary_action") or "").strip() == "requires_new_case":
                logger.info(
                    "append_blocked_reason case_boundary_action=requires_new_case boundary_reason=%s session_id=%s",
                    (blocked.get("boundary_reason") or "")[:500],
                    ap_sid,
                )
                patch_session_case_binding(ap_sid, clear_active_case=True)
            return blocked
        if triage_result.get("append_allowed") is False:
            blocked = _build_append_blocked_no_mutation_response(case=case, triage_result=triage_result)
            _attach_assist_layer(blocked, new_msg, _reply_truth_context_from_case(case))
            _finalize_triage_http_contract(blocked, request.session_id, persisted_case=case)
            ap_sid = (request.session_id or "").strip() or None
            append_session_analytics_event(
                "append_blocked",
                session_id=ap_sid,
                case_id=case_id,
                metadata={"reason": blocked.get("case_boundary_action")},
            )
            track_event("append_blocked", {"reason": blocked.get("case_boundary_action")})
            if (
                ap_sid
                and str(blocked.get("case_boundary_action") or "").strip() == "requires_new_case"
            ):
                logger.info(
                    "append_blocked_reason case_boundary_action=requires_new_case boundary_reason=%s session_id=%s",
                    (blocked.get("boundary_reason") or "")[:500],
                    ap_sid,
                )
                patch_session_case_binding(ap_sid, clear_active_case=True)
            return blocked
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
    _attach_assist_layer(updated, new_msg, _reply_truth_context_from_case(updated))
    _finalize_triage_http_contract(updated, request.session_id)
    ap_sid = (request.session_id or "").strip() or None
    append_org = client_asserted_office_id(http_request)
    emit_funnel_from_triage_result(
        updated,
        turns=[],
        text=new_msg,
        session_id=ap_sid,
        case_id=case_id,
        client_asserted_org_id=append_org,
    )
    return updated


@router.get("/support/deployment-manifest")
async def support_deployment_manifest(request: Request) -> dict[str, Any]:
    """
    Operator/support manifest: build SHA, deployment profile, persistence posture.
    No customer PII. Intended for tickets and rollout provenance.
    """
    assert_support_export_authorized(request)
    from services.fiqa_api.db.service_record_settings import unified_intake_case_persistence_report
    from services.fiqa_api.deployment_profile import (
        intake_schema_epoch,
        is_unified_intake_product_only,
        operator_runtime_hints,
    )
    from services.fiqa_api.utils.gitinfo import get_git_sha

    sha, source = get_git_sha()
    persist = unified_intake_case_persistence_report()
    lineage = http_request_lineage(request)
    return {
        "ok": True,
        "support_export_manifest_version": SUPPORT_EXPORT_MANIFEST_VERSION,
        "triage_wire_contract_label": "triage_result_fe_grouping_v1",
        "intake_schema_epoch": intake_schema_epoch(),
        "replay_lineage": _support_replay_lineage_dict(),
        "git": {"commit": sha, "source": source},
        "unified_intake_product_only": is_unified_intake_product_only(),
        "case_persistence": persist,
        "auth_posture": support_export_auth_posture_dict(),
        "intake_perimeter": intake_api_auth_posture_dict(),
        "request_lineage": {"request_trace_id": lineage.request_trace_id},
        "tenant_truth": intake_tenant_truth(request).as_dict(),
        "minimal_broker_token_posture": minimal_broker_token_posture_dict(),
        "minimal_broker_token_request": minimal_broker_token_request_truth(request),
        "operator_runtime_hints": operator_runtime_hints(),
        "office_ownership": office_ownership_posture_dict(),
        "client_ownership": client_ownership_posture_dict(),
        "token_scope_registry": token_scope_registry_dict(),
    }


@router.get("/support/case-head/{case_id}")
async def support_case_head(case_id: str, request: Request) -> dict[str, Any]:
    """
    Minimal persisted case metadata for L2 replay handoff (no message bodies / attachments).
    """
    assert_support_export_authorized(request)
    from services.fiqa_api.deployment_profile import (
        intake_schema_epoch,
        is_unified_intake_product_only,
        operator_runtime_hints,
    )
    from services.fiqa_api.utils.gitinfo import get_git_sha

    cid = (case_id or "").strip()
    if not cid:
        raise HTTPException(status_code=400, detail="case_id required")
    case = get_case_for_read(cid)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    sha, source = get_git_sha()
    lineage = http_request_lineage(request)
    req_org = client_asserted_office_id(request)
    case_org = str(case.get("asserted_org_id") or "").strip() or None
    office_hint: dict[str, Any] | None = None
    if req_org and case_org and req_org != case_org:
        office_hint = {
            "code": "support_case_head_x_org_id_mismatch_case_asserted_org_v1",
            "semantics": "client_asserted_header_differs_from_persisted_case_hint_not_enforcement_v1",
            "request_client_asserted_org_id": req_org,
            "case_asserted_org_id": case_org,
        }

    out: dict[str, Any] = {
        "ok": True,
        "support_export_manifest_version": SUPPORT_EXPORT_MANIFEST_VERSION,
        "intake_schema_epoch": intake_schema_epoch(),
        "replay_lineage": _support_replay_lineage_dict(),
        "git": {"commit": sha, "source": source},
        "unified_intake_product_only": is_unified_intake_product_only(),
        "auth_posture": support_export_auth_posture_dict(),
        "intake_perimeter": intake_api_auth_posture_dict(),
        "request_lineage": {"request_trace_id": lineage.request_trace_id},
        "tenant_truth": intake_tenant_truth(request).as_dict(),
        "minimal_broker_token_posture": minimal_broker_token_posture_dict(),
        "minimal_broker_token_request": minimal_broker_token_request_truth(request),
        "operator_runtime_hints": operator_runtime_hints(),
        "office_ownership": office_ownership_posture_dict(),
        "client_ownership": client_ownership_posture_dict(),
        "case": {
            "case_id": case.get("case_id") or cid,
            "status": case.get("status"),
            "created_at": case.get("created_at"),
            "updated_at": case.get("updated_at"),
            "workflow_state": case.get("workflow_state"),
            "service_lane": case.get("service_lane"),
            "case_lifecycle": case.get("case_lifecycle"),
            "workbench_test": case.get("workbench_test"),
            "asserted_org_id": case.get("asserted_org_id"),
            "client_id": case.get("client_id"),
        },
    }
    if office_hint:
        out["support_office_hint_check"] = office_hint
    return out


@router.get("/wechat/binding/start")
async def wechat_binding_start(
    session_id: str = Query(..., min_length=8),
    client_id: str = Query(..., min_length=1),
) -> dict[str, Any]:
    """
    Start optional WeChat OAuth (live mode + client-pack). Returns authorize_url or dev_simulate flag.
    """
    if get_wechat_binding_mode_for_client(client_id) != "live":
        raise HTTPException(status_code=403, detail="wechat_binding_not_live_for_client")
    if wechat_credentials_configured():
        state = sign_state(session_id, client_id)
        return {"authorize_url": build_authorize_url(state), "state": state, "dev_simulate": False}
    if simulate_allowed():
        return {"authorize_url": None, "state": None, "dev_simulate": True}
    raise HTTPException(status_code=503, detail="wechat_oauth_not_configured")


@router.post("/wechat/binding/simulate-complete")
async def wechat_binding_simulate_complete(
    session_id: str = Query(..., min_length=8),
    client_id: str = Query(..., min_length=1),
) -> dict[str, Any]:
    """Dev/staging only: complete binding without WeChat (requires WECHAT_BINDING_ALLOW_SIMULATE)."""
    import secrets

    if get_wechat_binding_mode_for_client(client_id) != "live":
        raise HTTPException(status_code=403, detail="wechat_binding_not_live_for_client")
    if not simulate_allowed():
        raise HTTPException(status_code=403, detail="wechat_binding_simulate_disabled")
    try:
        patch_session_light_identity_binding(
            session_id,
            {
                "identity_binding_state": "linked",
                "person_link_key": f"sim_{secrets.token_hex(16)}",
                "person_link_source": "wechat",
                "person_link_confidence": 0.75,
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


@router.get("/wechat/binding/callback")
async def wechat_binding_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """WeChat OAuth redirect target; writes session identity and redirects to frontend."""
    if error:
        return RedirectResponse(
            url=build_frontend_return_url({"wechat_binding": "error", "reason": str(error)}),
            status_code=302,
        )
    parsed = verify_state(state or "")
    if not parsed:
        return RedirectResponse(
            url=build_frontend_return_url({"wechat_binding": "error", "reason": "invalid_state"}),
            status_code=302,
        )
    if not code:
        return RedirectResponse(
            url=build_frontend_return_url({"wechat_binding": "error", "reason": "missing_code"}),
            status_code=302,
        )
    openid, err = await exchange_code_for_openid(code)
    if not openid:
        return RedirectResponse(
            url=build_frontend_return_url({"wechat_binding": "error", "reason": err or "token_exchange"}),
            status_code=302,
        )
    link_key = opaque_person_link_key(openid)
    try:
        patch_session_light_identity_binding(
            parsed["session_id"],
            {
                "identity_binding_state": "linked",
                "person_link_key": link_key,
                "person_link_source": "wechat",
                "person_link_confidence": 0.9,
            },
        )
    except ValueError:
        return RedirectResponse(
            url=build_frontend_return_url({"wechat_binding": "error", "reason": "session_not_found"}),
            status_code=302,
        )
    return RedirectResponse(
        url=build_frontend_return_url({"wechat_binding": "linked"}),
        status_code=302,
    )
