"""WeCom vertical slice orchestrator — callback → sync_msg → intent → reply."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from services.fiqa_api.wecom.active_case_bridge import (
    create_or_attach_draft_case_for_start_click,
    find_open_draft_case_by_external_userid,
    ingest_wecom_text_to_active_case,
    ingest_wecom_text_to_draft_case,
)
from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
from services.fiqa_api.inbox_triage.intake_service_lanes import SERVICE_LANE_ADD_CAR
from services.fiqa_api.wecom.config import WeComKfConfig, wecom_kf_api_configured
from services.fiqa_api.wecom.identity import (
    extract_delivery_date_from_text,
    extract_phone_from_text,
    extract_primary_driver_from_text,
    extract_vin_from_text,
    extract_zip_from_text,
)
from services.fiqa_api.wecom.intent import (
    START_CARD_CLICK_INTENTS,
    canonical_intent,
    classify_wecom_intent,
)
from services.fiqa_api.wecom.message_processed import (
    claim_message_processed,
    release_message_processed,
    update_message_processed_outcome,
)
from services.fiqa_api.wecom.minimal_lanes import (
    find_open_minimal_lane_case_by_external_userid,
    ingest_wecom_text_to_minimal_lane,
)
from services.fiqa_api.inbox_triage.h5_task_link import (
    mask_h5_task_url,
    mint_h5_add_vehicle_photo_flow_link,
)
from services.fiqa_api.inbox_triage.h5_task_upload import (
    h5_photo_flow_is_complete,
    is_explicit_add_car_restart,
)
from services.fiqa_api.wecom.h5_photo_end_card import try_send_h5_photo_flow_end_card
from services.fiqa_api.wecom.reply import (
    build_guided_menu_payload,
    build_h5_photo_phase_complete_reply,
    build_h5_vin_start_card_payload,
    build_secondary_topic_deferred_reply,
    build_slice_reply,
    build_start_card_payload,
)
from services.fiqa_api.wecom.reply_dedup import claim_reply_send, release_reply_claim
from services.fiqa_api.wecom.reply_outbox import enqueue_wecom_reply, wecom_reply_outbox_enabled
from services.fiqa_api.wecom.send_msg import send_menu_reply, send_text_reply, wecom_slice_send_enabled
from services.fiqa_api.wecom.sync_cursor import load_sync_cursor, save_sync_cursor
from services.fiqa_api.wecom.media_intake import ingest_wecom_media_message, is_supported_media_msgtype
from services.fiqa_api.wecom.normalize import normalize_media_message, normalize_text_message
from services.fiqa_api.wecom.sync_msg import pull_customer_messages

logger = logging.getLogger(__name__)

_MINIMAL_LANE_INTENTS = frozenset({"policy_review", "claim_intake", "coverage_risk_intake"})


def wecom_b0_active_workspace_enabled() -> bool:
    """Track B0 gate — Start Card before any case creation. Default OFF.

    When off, behavior is unchanged from Track A (immediate case creation on
    high-confidence add_car + phone, no Start Card, no click handling).
    """
    return (os.getenv("WECOM_B0_ACTIVE_WORKSPACE") or "").strip().lower() in ("1", "true", "yes")


def _normalized_has_draft_collection_fields(normalized: dict[str, Any]) -> bool:
    """True when text carries VIN/ZIP/phone/date/driver fields for Draft merge."""
    text = str(normalized.get("text") or "").strip()
    if normalized.get("phone") or extract_phone_from_text(text):
        return True
    if extract_vin_from_text(text):
        return True
    if extract_zip_from_text(text):
        return True
    if extract_delivery_date_from_text(text):
        return True
    if extract_primary_driver_from_text(text):
        return True
    return False


def _build_add_car_h5_start_menu(
    normalized: dict[str, Any],
    *,
    case_id: str | None,
) -> tuple[dict[str, Any] | None, str | None, str | None]:
    """Build H5 photo Start Card, or follow-up text when photo flow already complete."""
    cid = (case_id or "").strip()
    if not cid:
        return build_start_card_payload(), None, None

    case = get_case_for_read(cid)
    if case and h5_photo_flow_is_complete(case):
        try_send_h5_photo_flow_end_card(cid)
        return None, build_h5_photo_phase_complete_reply(case), None

    ext_uid = str(normalized.get("external_userid") or "").strip() or None
    try:
        h5_url = mint_h5_add_vehicle_photo_flow_link(case_id=cid, external_userid=ext_uid)
    except ValueError:
        return build_start_card_payload(), None, None
    masked = mask_h5_task_url(h5_url)
    restart_intro = is_explicit_add_car_restart(str(normalized.get("text") or ""))
    return build_h5_vin_start_card_payload(h5_url=h5_url, restart_intro=restart_intro), None, masked


def _should_route_add_car_h5_start_instead_of_draft_merge(
    *,
    b0_enabled: bool,
    intent_result: Any,
    normalized: dict[str, Any],
    open_add_car_draft_id: str | None,
    open_bound_case: dict[str, Any] | None,
) -> bool:
    """Route to H5 Start / completed follow-up instead of generic draft merge."""
    if not b0_enabled:
        return False
    if intent_result.intent != "add_car" or intent_result.confidence != "high":
        return False
    if _normalized_has_draft_collection_fields(normalized):
        return False
    text = str(normalized.get("text") or "")
    if is_explicit_add_car_restart(text):
        return True
    if (
        open_add_car_draft_id
        and open_bound_case
        and h5_photo_flow_is_complete(open_bound_case)
    ):
        return False
    return False


def _add_car_start_active_outcome(
    *,
    menu_payload: dict[str, Any] | None,
    text_content: str | None,
) -> str:
    if menu_payload is None and text_content:
        return "photo_flow_complete_followup"
    return "start_card_sent"


def _log_slice(stage: str, payload: dict[str, Any]) -> None:
    logger.info("wecom_slice_%s %s", stage, json.dumps(payload, ensure_ascii=False))


def _dispatch_reply(
    cfg: WeComKfConfig,
    normalized: dict[str, Any],
    *,
    send_enabled: bool,
    menu_payload: dict[str, Any] | None,
    text_content: str | None,
    outcome: dict[str, Any],
) -> None:
    """Send a menu or text reply (or log-only), mutating outcome in place.

    Idempotency (P0 fix): a given WeCom msg_id may trigger at most ONE
    outbound send, no matter how many times this function runs for it —
    WeCom callback retry, `sync_msg` re-delivering an already-processed
    message (no persisted cursor), or a concurrent duplicate request on
    another Cloud Run instance. See `wecom.reply_dedup.claim_reply_send`,
    which is the single choke point every reply-sending branch in
    `process_kf_msg_or_event` routes through via this function.
    """
    msg_id = str(normalized.get("msg_id") or "")

    if not (send_enabled and normalized.get("external_userid") and normalized.get("open_kf_id")):
        _log_slice(
            "reply_logged_only_v1",
            {
                "msg_id": msg_id,
                "send_enabled": send_enabled,
                "reason": "WECOM_SLICE_SEND_REPLY not set" if not send_enabled else "missing_ids",
            },
        )
        return

    if not claim_reply_send(msg_id):
        outcome["reply_sent"] = False
        outcome["reply_duplicate_skipped"] = True
        _log_slice(
            "reply_skipped_duplicate_v1",
            {"msg_id": msg_id, "reason": "already_sent_or_in_flight"},
        )
        return

    try:
        if wecom_reply_outbox_enabled():
            reply_type = "msgmenu" if menu_payload is not None else "text"
            if menu_payload is not None:
                reply_payload = {"msgtype": "msgmenu", "msgmenu": menu_payload}
            else:
                reply_payload = {"msgtype": "text", "text": {"content": text_content or ""}}
            created = enqueue_wecom_reply(
                msg_id=msg_id or None,
                external_userid=str(normalized["external_userid"]),
                open_kf_id=str(normalized["open_kf_id"]),
                case_id=str(outcome.get("case_id") or "").strip() or None,
                reply_type=reply_type,
                reply_payload=reply_payload,
            )
            if not created:
                release_reply_claim(msg_id)
                outcome["reply_sent"] = False
                outcome["reply_duplicate_skipped"] = True
                _log_slice(
                    "reply_skipped_duplicate_v1",
                    {"msg_id": msg_id, "reason": "outbox_dedup_key_exists"},
                )
                return
            outcome["reply_sent"] = True
            outcome["reply_enqueued"] = True
            _log_slice("reply_enqueued_v1", {"msg_id": msg_id, "reply_type": reply_type})
            return

        if menu_payload is not None:
            send_menu_reply(
                cfg,
                external_userid=str(normalized["external_userid"]),
                open_kf_id=str(normalized["open_kf_id"]),
                menu=menu_payload,
            )
        else:
            send_text_reply(
                cfg,
                external_userid=str(normalized["external_userid"]),
                open_kf_id=str(normalized["open_kf_id"]),
                content=text_content or "",
            )
        outcome["reply_sent"] = True
        _log_slice("reply_sent_v1", {"msg_id": msg_id, "sent": True})
    except Exception as exc:
        release_reply_claim(msg_id)
        outcome["reply_send_error"] = str(exc)
        _log_slice(
            "reply_send_failed_v1",
            {"msg_id": msg_id, "error": str(exc)},
        )


def process_kf_msg_or_event(
    cfg: WeComKfConfig,
    *,
    callback_token: str,
    open_kf_id: str,
    pull_messages: Any | None = None,
) -> list[dict[str, Any]]:
    """
    Run the minimal vertical slice for one kf_msg_or_event callback.
    Never raises — errors are logged; callback must still return 200.
    """
    results: list[dict[str, Any]] = []

    if not callback_token or not open_kf_id:
        _log_slice(
            "skipped_v1",
            {"reason": "missing_callback_token_or_open_kf_id", "open_kf_id": open_kf_id},
        )
        return results

    if not wecom_kf_api_configured():
        _log_slice(
            "skipped_v1",
            {
                "reason": "wecom_kf_secret_not_configured",
                "hint": "set WECOM_KF_SECRET (or WECOM_CORP_SECRET / WECOM_SECRET / WECOM_AGENT_SECRET) to enable sync_msg",
                "open_kf_id": open_kf_id,
            },
        )
        return results

    try:
        if pull_messages is not None:
            raw_messages = pull_messages(cfg, token=callback_token, open_kf_id=open_kf_id)
            sync_next_cursor = ""
        else:
            start_cursor = load_sync_cursor(open_kf_id)
            pull_result = pull_customer_messages(
                cfg,
                token=callback_token,
                open_kf_id=open_kf_id,
                start_cursor=start_cursor,
            )
            raw_messages = pull_result.messages
            sync_next_cursor = pull_result.next_cursor
    except Exception as exc:
        err = str(exc)
        if "wecom_sync_msg_admin_blocked_v1" in err:
            _log_slice(
                "pipeline_blocked_admin_v1",
                {"open_kf_id": open_kf_id, "error": err},
            )
        else:
            _log_slice(
                "sync_msg_failed_v1",
                {"open_kf_id": open_kf_id, "error": err},
            )
        return results

    _log_slice(
        "sync_msg_ok_v1",
        {"open_kf_id": open_kf_id, "message_count": len(raw_messages)},
    )

    send_enabled = wecom_slice_send_enabled()
    b0_enabled = wecom_b0_active_workspace_enabled()
    batch_had_processing_failure = False

    for raw in raw_messages:
        msgtype = (raw.get("msgtype") or "").lower()
        if is_supported_media_msgtype(msgtype):
            normalized = normalize_media_message(raw)
        elif msgtype == "text":
            normalized = normalize_text_message(raw)
        else:
            _log_slice(
                "unsupported_msgtype_skipped_v1",
                {"msgtype": msgtype, "msg_id": raw.get("msgid")},
            )
            continue

        msg_id = str(normalized.get("msg_id") or "").strip()

        if not claim_message_processed(
            msg_id,
            open_kf_id=str(normalized.get("open_kf_id") or open_kf_id).strip() or None,
            external_userid=str(normalized.get("external_userid") or "").strip() or None,
            event_type="message.received",
        ):
            _log_slice(
                "message_skipped_already_processed_v1",
                {"msg_id": msg_id, "open_kf_id": open_kf_id},
            )
            results.append(
                {
                    "msg_id": msg_id or None,
                    "external_userid": normalized.get("external_userid"),
                    "processing_skipped": True,
                    "skip_reason": "already_processed",
                    "reply_sent": False,
                }
            )
            continue

        try:
            if is_supported_media_msgtype(msgtype):
                media_result = ingest_wecom_media_message(normalized, cfg)
                outcome = {
                    "msg_id": normalized.get("msg_id"),
                    "external_userid": normalized.get("external_userid"),
                    "msgtype": msgtype,
                    "reply_text": media_result.get("reply_text"),
                    "reply_sent": False,
                    "reply_send_error": None,
                    "case_created": media_result.get("case_created", False),
                    "case_id": media_result.get("case_id"),
                    "active_case_outcome": media_result.get("active_case_outcome"),
                    "attachment_id": media_result.get("attachment_id"),
                    "binding_confidence": media_result.get("binding_confidence"),
                    "service_lane": media_result.get("service_lane"),
                }
                _log_slice(
                    "media_intake_v1",
                    {k: v for k, v in outcome.items() if k != "reply_text"},
                )
                if media_result.get("reply_text"):
                    _dispatch_reply(
                        cfg,
                        normalized,
                        send_enabled=send_enabled,
                        menu_payload=None,
                        text_content=str(media_result["reply_text"]),
                        outcome=outcome,
                    )
                results.append(outcome)
                update_message_processed_outcome(
                    msg_id,
                    outcome=str(outcome.get("active_case_outcome") or media_result.get("outcome") or ""),
                    case_id=str(outcome.get("case_id") or "").strip() or None,
                )
                continue

            intent_result = classify_wecom_intent(
                normalized.get("text") or "",
                menu_id=normalized.get("menu_id"),
            )

            # --- Track B0.1/B0.2: Start Card button click (Start / Later / Talk to Broker) ---
            # "Start" now creates (or attaches to) the ONE Draft Case for this
            # external_userid — no Broker Confirm, no Done Card (B0.3 scope).
            # "Later" / "Talk to Broker" remain routing-only acks, no case.
            if b0_enabled and intent_result.intent in START_CARD_CLICK_INTENTS:
                start_outcome = intent_result.intent
                if intent_result.intent == "start_add_car_click":
                    draft_result = create_or_attach_draft_case_for_start_click(normalized)
                    menu_payload, text_content, h5_masked = _build_add_car_h5_start_menu(
                        normalized,
                        case_id=str(draft_result.get("case_id") or ""),
                    )
                    start_outcome = _add_car_start_active_outcome(
                        menu_payload=menu_payload,
                        text_content=text_content,
                    )
                    if menu_payload is None and not text_content:
                        reply_text = build_slice_reply(intent_result.intent, guided_menu=False)
                        menu_payload = None
                    elif menu_payload is not None:
                        reply_text = None
                    else:
                        reply_text = text_content or build_slice_reply(intent_result.intent, guided_menu=False)
                else:
                    draft_result = {"outcome": intent_result.intent, "case_id": None, "case_created": False}
                    menu_payload = None
                    reply_text = build_slice_reply(intent_result.intent, guided_menu=False)
                    h5_masked = None
                outcome = {
                    "msg_id": normalized.get("msg_id"),
                    "external_userid": normalized.get("external_userid"),
                    "detected_intent": canonical_intent(intent_result.intent),
                    "internal_intent": intent_result.intent,
                    "confidence": intent_result.confidence,
                    "matched_by": intent_result.matched_by,
                    "guided_menu_required": False,
                    "reply_text": reply_text,
                    "reply_sent": False,
                    "reply_send_error": None,
                    "case_created": draft_result.get("case_created", False),
                    "case_id": draft_result.get("case_id"),
                    "active_case_outcome": start_outcome,
                    "readiness_gate": None,
                    "h5_task_link_masked": h5_masked,
                }
                _log_slice(
                    "start_card_click_v1",
                    {
                        "msg_id": normalized.get("msg_id"),
                        "click_intent": intent_result.intent,
                        "case_id": outcome["case_id"],
                        "case_created": outcome["case_created"],
                        "h5_task_link_masked": h5_masked,
                    },
                )
                _log_slice(
                    "reply_generated_v1",
                    {
                        "reply_text": reply_text or "<h5_vin_start_card_msgmenu>",
                        "guided_menu": False,
                        "reply_format": "msgmenu" if menu_payload else "text",
                    },
                )
                _dispatch_reply(
                    cfg,
                    normalized,
                    send_enabled=send_enabled,
                    menu_payload=menu_payload,
                    text_content=reply_text,
                    outcome=outcome,
                )
                results.append(outcome)
                update_message_processed_outcome(
                    msg_id,
                    outcome=str(outcome.get("active_case_outcome") or intent_result.intent),
                    case_id=str(outcome.get("case_id") or "").strip() or None,
                )
                continue
            # --- Loop 2: Premium Review / Claim Lite minimal lane (before add_car draft merge) ---
            guided_menu = intent_result.confidence == "low" or intent_result.intent == "unclear"
            open_bound_case_id = (
                find_open_draft_case_by_external_userid(str(normalized.get("external_userid") or ""))
                if b0_enabled
                else None
            )
            open_bound_case = get_case_for_read(open_bound_case_id) if open_bound_case_id else None
            if b0_enabled and open_bound_case_id and open_bound_case is None:
                _log_slice(
                    "stale_draft_binding_cleared_v1",
                    {
                        "msg_id": msg_id,
                        "stale_case_id": open_bound_case_id,
                        "external_userid": normalized.get("external_userid"),
                    },
                )
                open_bound_case_id = None
                open_bound_case = None

            open_minimal_lane_id = (
                find_open_minimal_lane_case_by_external_userid(str(normalized.get("external_userid") or ""))
                if b0_enabled
                else None
            )
            minimal_lane_trigger = (
                intent_result.confidence == "high" and intent_result.intent in _MINIMAL_LANE_INTENTS
            ) or (
                b0_enabled
                and open_minimal_lane_id
                and not guided_menu
                and intent_result.intent in _MINIMAL_LANE_INTENTS
            )
            if minimal_lane_trigger:
                minimal_result = ingest_wecom_text_to_minimal_lane(normalized, intent_result)
                if minimal_result.get("outcome") == "secondary_topic_deferred":
                    reply_text = build_secondary_topic_deferred_reply()
                else:
                    reply_text = build_slice_reply(intent_result.intent, guided_menu=False)
                outcome = {
                    "msg_id": normalized.get("msg_id"),
                    "external_userid": normalized.get("external_userid"),
                    "detected_intent": canonical_intent(intent_result.intent),
                    "internal_intent": intent_result.intent,
                    "confidence": intent_result.confidence,
                    "matched_by": intent_result.matched_by,
                    "guided_menu_required": False,
                    "reply_text": reply_text,
                    "reply_sent": False,
                    "reply_send_error": None,
                    "case_created": minimal_result.get("case_created", False),
                    "case_id": minimal_result.get("case_id"),
                    "active_case_outcome": minimal_result.get("outcome"),
                    "readiness_gate": minimal_result.get("readiness_gate"),
                    "service_lane": minimal_result.get("service_lane"),
                }
                _log_slice(
                    "minimal_lane_v1",
                    {k: outcome[k] for k in outcome if k not in ("reply_text", "internal_intent")},
                )
                _log_slice(
                    "reply_generated_v1",
                    {"reply_text": reply_text, "guided_menu": False, "reply_format": "text"},
                )
                _dispatch_reply(
                    cfg,
                    normalized,
                    send_enabled=send_enabled,
                    menu_payload=None,
                    text_content=reply_text,
                    outcome=outcome,
                )
                results.append(outcome)
                update_message_processed_outcome(
                    msg_id,
                    outcome=str(outcome.get("active_case_outcome") or intent_result.intent),
                    case_id=str(outcome.get("case_id") or "").strip() or None,
                )
                continue

            # Track B0.2 — reuse open add_car Draft only (not Premium/Claim cases).
            open_add_car_draft_id = (
                open_bound_case_id
                if open_bound_case and open_bound_case.get("service_lane") == SERVICE_LANE_ADD_CAR
                else None
            )

            # P19E-1 — Phase 2 text collection after H5 photo flow complete.
            from services.fiqa_api.wecom.add_vehicle_phase2 import (
                ingest_phase2_text_collection,
                resolve_add_car_case_for_phase2,
                should_handle_phase2_incoming_text,
            )

            phase2_case_id, phase2_case = resolve_add_car_case_for_phase2(
                bound_case_id=open_add_car_draft_id,
                bound_case=open_bound_case,
                external_userid=str(normalized.get("external_userid") or ""),
            )
            if (
                b0_enabled
                and phase2_case_id
                and phase2_case
                and h5_photo_flow_is_complete(phase2_case)
                and not is_explicit_add_car_restart(str(normalized.get("text") or ""))
            ):
                if should_handle_phase2_incoming_text(phase2_case, normalized, intent_result):
                    phase2_result = ingest_phase2_text_collection(normalized, phase2_case_id)
                    reply_text = phase2_result.get("reply_text")
                    outcome = {
                        "msg_id": normalized.get("msg_id"),
                        "external_userid": normalized.get("external_userid"),
                        "detected_intent": canonical_intent(intent_result.intent),
                        "internal_intent": intent_result.intent,
                        "confidence": intent_result.confidence,
                        "matched_by": intent_result.matched_by,
                        "guided_menu_required": False,
                        "reply_text": reply_text,
                        "reply_sent": False,
                        "reply_send_error": None,
                        "case_created": phase2_result.get("case_created", False),
                        "case_id": phase2_result.get("case_id"),
                        "active_case_outcome": phase2_result.get("active_case_outcome"),
                        "still_needed_fields": phase2_result.get("still_needed_fields"),
                        "guided_workflow_state": phase2_result.get("guided_workflow_state"),
                        "add_vehicle_phase": phase2_result.get("add_vehicle_phase"),
                    }
                    _log_slice(
                        "phase2_text_collection_v1",
                        {k: outcome[k] for k in outcome if k not in ("reply_text", "internal_intent")},
                    )
                    if reply_text:
                        _log_slice(
                            "reply_generated_v1",
                            {"reply_text": reply_text, "guided_menu": False, "reply_format": "text"},
                        )
                        _dispatch_reply(
                            cfg,
                            normalized,
                            send_enabled=send_enabled,
                            menu_payload=None,
                            text_content=reply_text,
                            outcome=outcome,
                        )
                    results.append(outcome)
                    update_message_processed_outcome(
                        msg_id,
                        outcome=str(outcome.get("active_case_outcome") or ""),
                        case_id=str(outcome.get("case_id") or "").strip() or None,
                    )
                    continue

            # P19E-2 — Progress Card before draft merge / duplicate H5 Start.
            from services.fiqa_api.wecom.add_vehicle_progress import (
                build_add_vehicle_progress_reply,
                find_active_add_car_case_for_progress,
                should_route_add_vehicle_progress,
            )

            if b0_enabled and should_route_add_vehicle_progress(
                normalized,
                intent_result,
                guided_menu=guided_menu,
            ):
                progress_case, open_count = find_active_add_car_case_for_progress(
                    str(normalized.get("external_userid") or "")
                )
                if progress_case:
                    text_content, menu_payload, h5_masked = build_add_vehicle_progress_reply(
                        progress_case,
                        external_userid=str(normalized.get("external_userid") or ""),
                        open_case_count=open_count,
                    )
                    outcome = {
                        "msg_id": normalized.get("msg_id"),
                        "external_userid": normalized.get("external_userid"),
                        "detected_intent": canonical_intent(intent_result.intent),
                        "internal_intent": intent_result.intent,
                        "confidence": intent_result.confidence,
                        "matched_by": intent_result.matched_by,
                        "guided_menu_required": False,
                        "reply_text": text_content,
                        "reply_sent": False,
                        "reply_send_error": None,
                        "case_created": False,
                        "case_id": progress_case.get("case_id"),
                        "active_case_outcome": "add_vehicle_progress_card",
                        "h5_task_link_masked": h5_masked,
                    }
                    _log_slice(
                        "add_vehicle_progress_card_v1",
                        {k: outcome[k] for k in outcome if k not in ("reply_text", "internal_intent")},
                    )
                    _log_slice(
                        "reply_generated_v1",
                        {
                            "reply_text": text_content or "<add_vehicle_progress_card_msgmenu>",
                            "guided_menu": False,
                            "reply_format": "msgmenu" if menu_payload else "text",
                        },
                    )
                    _dispatch_reply(
                        cfg,
                        normalized,
                        send_enabled=send_enabled,
                        menu_payload=menu_payload,
                        text_content=text_content,
                        outcome=outcome,
                    )
                    results.append(outcome)
                    update_message_processed_outcome(
                        msg_id,
                        outcome="add_vehicle_progress_card",
                        case_id=str(outcome.get("case_id") or "").strip() or None,
                    )
                    continue

            route_add_car_h5_start = _should_route_add_car_h5_start_instead_of_draft_merge(
                b0_enabled=b0_enabled,
                intent_result=intent_result,
                normalized=normalized,
                open_add_car_draft_id=open_add_car_draft_id,
                open_bound_case=open_bound_case,
            )
            if b0_enabled and open_add_car_draft_id and (
                not guided_menu or _normalized_has_draft_collection_fields(normalized)
            ) and not route_add_car_h5_start:
                reply_text = build_slice_reply(intent_result.intent, guided_menu=False)
                draft_result = ingest_wecom_text_to_draft_case(normalized, open_add_car_draft_id)
                outcome = {
                    "msg_id": normalized.get("msg_id"),
                    "external_userid": normalized.get("external_userid"),
                    "detected_intent": canonical_intent(intent_result.intent),
                    "internal_intent": intent_result.intent,
                    "confidence": intent_result.confidence,
                    "matched_by": intent_result.matched_by,
                    "guided_menu_required": guided_menu,
                    "reply_text": reply_text,
                    "reply_sent": False,
                    "reply_send_error": None,
                    "case_created": draft_result.get("case_created", False),
                    "case_id": draft_result.get("case_id"),
                    "active_case_outcome": draft_result.get("outcome"),
                    "readiness_gate": draft_result.get("readiness_gate"),
                    "quote_ready_status": draft_result.get("quote_ready_status"),
                    "still_needed_fields": draft_result.get("still_needed_fields"),
                }
                _log_slice(
                    "draft_case_merge_v1",
                    {k: outcome[k] for k in outcome if k not in ("reply_text", "internal_intent")},
                )
                _log_slice(
                    "reply_generated_v1",
                    {
                        "reply_text": reply_text,
                        "guided_menu": guided_menu,
                        "reply_format": "msgmenu" if guided_menu else "text",
                    },
                )
                _dispatch_reply(
                    cfg,
                    normalized,
                    send_enabled=send_enabled,
                    menu_payload=None,
                    text_content=reply_text,
                    outcome=outcome,
                )
                results.append(outcome)
                update_message_processed_outcome(
                    msg_id,
                    outcome=str(outcome.get("active_case_outcome") or ""),
                    case_id=str(outcome.get("case_id") or "").strip() or None,
                )
                continue

            # --- Track B0.1 + P19D-3: high-confidence add_car -> H5 VIN Start Card ---
            if b0_enabled and intent_result.intent == "add_car" and intent_result.confidence == "high":
                draft_result = create_or_attach_draft_case_for_start_click(normalized)
                menu_payload, text_content, h5_masked = _build_add_car_h5_start_menu(
                    normalized,
                    case_id=str(draft_result.get("case_id") or ""),
                )
                start_outcome = _add_car_start_active_outcome(
                    menu_payload=menu_payload,
                    text_content=text_content,
                )
                outcome = {
                    "msg_id": normalized.get("msg_id"),
                    "external_userid": normalized.get("external_userid"),
                    "detected_intent": canonical_intent(intent_result.intent),
                    "internal_intent": intent_result.intent,
                    "confidence": intent_result.confidence,
                    "matched_by": intent_result.matched_by,
                    "guided_menu_required": False,
                    "reply_text": text_content,
                    "reply_sent": False,
                    "reply_send_error": None,
                    "case_created": draft_result.get("case_created", False),
                    "case_id": draft_result.get("case_id"),
                    "active_case_outcome": start_outcome,
                    "readiness_gate": None,
                    "h5_task_link_masked": h5_masked,
                }
                _log_slice(
                    "start_card_triggered_v1",
                    {
                        "msg_id": normalized.get("msg_id"),
                        "matched_by": intent_result.matched_by,
                        "case_id": outcome["case_id"],
                        "case_created": outcome["case_created"],
                        "h5_task_link_masked": h5_masked,
                    },
                )
                _log_slice(
                    "reply_generated_v1",
                    {
                        "reply_text": "<h5_vin_start_card_msgmenu>",
                        "guided_menu": False,
                        "reply_format": "msgmenu",
                    },
                )
                _dispatch_reply(
                    cfg,
                    normalized,
                    send_enabled=send_enabled,
                    menu_payload=menu_payload,
                    text_content=text_content,
                    outcome=outcome,
                )
                results.append(outcome)
                update_message_processed_outcome(
                    msg_id,
                    outcome=str(outcome.get("active_case_outcome") or "start_card_sent"),
                    case_id=str(outcome.get("case_id") or "").strip() or None,
                )
                continue

            detected = canonical_intent(intent_result.intent)
            reply_text = build_slice_reply(intent_result.intent, guided_menu=guided_menu)

            if guided_menu and b0_enabled:
                active_case_result = {
                    "outcome": "intent_not_actionable",
                    "case_id": None,
                    "case_created": False,
                    "readiness_gate": None,
                }
            else:
                active_case_result = ingest_wecom_text_to_active_case(normalized, intent_result)

            outcome: dict[str, Any] = {
                "msg_id": normalized.get("msg_id"),
                "external_userid": normalized.get("external_userid"),
                "detected_intent": detected,
                "internal_intent": intent_result.intent,
                "confidence": intent_result.confidence,
                "matched_by": intent_result.matched_by,
                "guided_menu_required": guided_menu,
                "reply_text": reply_text,
                "reply_sent": False,
                "reply_send_error": None,
                "case_created": active_case_result.get("case_created", False),
                "case_id": active_case_result.get("case_id"),
                "active_case_outcome": active_case_result.get("outcome"),
                "readiness_gate": active_case_result.get("readiness_gate"),
            }

            _log_slice(
                "intent_v1",
                {k: outcome[k] for k in outcome if k not in ("reply_text", "internal_intent")},
            )
            _log_slice(
                "reply_generated_v1",
                {
                    "reply_text": reply_text,
                    "guided_menu": guided_menu,
                    "reply_format": "msgmenu" if guided_menu else "text",
                },
            )

            _dispatch_reply(
                cfg,
                normalized,
                send_enabled=send_enabled,
                menu_payload=build_guided_menu_payload() if guided_menu else None,
                text_content=None if guided_menu else reply_text,
                outcome=outcome,
            )

            results.append(outcome)
            update_message_processed_outcome(
                msg_id,
                outcome=str(outcome.get("active_case_outcome") or detected),
                case_id=str(outcome.get("case_id") or "").strip() or None,
            )
        except Exception as exc:
            batch_had_processing_failure = True
            release_message_processed(msg_id)
            # Belt-and-suspenders for the module docstring's "never raises"
            # contract: a DB hiccup (e.g. Postgres cold-start / transient
            # network failure) partway through one message's processing must
            # not crash the whole callback. An uncaught exception here used
            # to propagate to the route handler as an unhandled 500, which
            # (a) starved the customer of any reply for this message and
            # (b) took so long to fail that WeCom retried the callback,
            # producing duplicate sends for other messages in the batch.
            _log_slice(
                "message_processing_failed_v1",
                {
                    "msg_id": normalized.get("msg_id"),
                    "external_userid": normalized.get("external_userid"),
                    "error": str(exc),
                },
            )
            results.append(
                {
                    "msg_id": normalized.get("msg_id"),
                    "external_userid": normalized.get("external_userid"),
                    "reply_sent": False,
                    "reply_send_error": str(exc),
                    "processing_error": str(exc),
                }
            )
            continue

    if pull_messages is None and sync_next_cursor and not batch_had_processing_failure:
        save_sync_cursor(open_kf_id, sync_next_cursor)

    return results
