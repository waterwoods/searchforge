"""P19H-3h — WeCom customer ack when Claim H5 intake form is submitted (not broker_done)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from services.fiqa_api.inbox_triage.case_store import update_case_h5_intake_state
from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.reply import build_h5_submit_confirmation_reply
from services.fiqa_api.wecom.reply_outbox import enqueue_wecom_reply, wecom_reply_outbox_enabled
from services.fiqa_api.wecom.send_msg import send_text_reply, wecom_slice_send_enabled

logger = logging.getLogger(__name__)


def _log_event(event: str, payload: dict[str, Any]) -> None:
    logger.info("%s %s", event, json.dumps(payload, ensure_ascii=False, default=str))


def _h5_intake_state(case: dict[str, Any]) -> dict[str, Any]:
    raw = case.get("h5_intake_state") or {}
    return raw if isinstance(raw, dict) else {}


def _confirmation_already_sent(case: dict[str, Any]) -> bool:
    state = _h5_intake_state(case)
    return bool(str(state.get("h5_submit_confirmation_sent_at") or "").strip())


def _record_confirmation_status(
    case_id: str,
    *,
    send_status: str,
    sent_at: str | None = None,
) -> None:
    patch: dict[str, Any] = {"h5_submit_confirmation_send_status": (send_status or "").strip() or "unknown"}
    if sent_at:
        patch["h5_submit_confirmation_sent_at"] = sent_at
    update_case_h5_intake_state(case_id, patch)


def try_send_h5_submit_confirmation(case_id: str) -> dict[str, Any]:
    """
    Best-effort WeCom ack after customer H5 submit.
    Never raises — submit must succeed even if send fails.
    Deduped via h5_intake_state.h5_submit_confirmation_sent_at (no schema migration).
    This is NOT broker_done / End Card.
    """
    cid = (case_id or "").strip()
    if not cid:
        return {"sent": False, "reason": "missing_case_id"}

    case = get_case_for_read(cid)
    if case is None:
        return {"sent": False, "reason": "case_not_found"}

    if _confirmation_already_sent(case):
        _log_event(
            "h5_submit_confirmation_skipped_v1",
            {"case_id": cid, "reason": "already_sent"},
        )
        return {"sent": False, "reason": "already_sent", "deduped": True}

    external_userid = str(case.get("wecom_external_userid") or "").strip()
    open_kf_id = str(case.get("wecom_open_kf_id") or "").strip()
    if not external_userid or not open_kf_id:
        _log_event(
            "h5_submit_confirmation_skipped_v1",
            {"case_id": cid, "reason": "no_wecom_channel_binding"},
        )
        _record_confirmation_status(cid, send_status="skipped_no_channel")
        return {"sent": False, "reason": "no_wecom_channel_binding", "pending": True}

    content = build_h5_submit_confirmation_reply()

    if not wecom_slice_send_enabled():
        _log_event(
            "h5_submit_confirmation_skipped_v1",
            {"case_id": cid, "reason": "WECOM_SLICE_SEND_REPLY not set"},
        )
        _record_confirmation_status(cid, send_status="skipped_send_disabled")
        return {"sent": False, "reason": "send_disabled", "pending": True}

    cfg = load_wecom_kf_config()
    if cfg is None:
        _log_event(
            "h5_submit_confirmation_skipped_v1",
            {"case_id": cid, "reason": "wecom_kf_not_configured"},
        )
        _record_confirmation_status(cid, send_status="skipped_not_configured")
        return {"sent": False, "reason": "wecom_kf_not_configured", "pending": True}

    try:
        reply_payload = {"msgtype": "text", "text": {"content": content}}
        if wecom_reply_outbox_enabled():
            created = enqueue_wecom_reply(
                msg_id=None,
                external_userid=external_userid,
                open_kf_id=open_kf_id,
                case_id=cid,
                reply_type="h5_submit_confirmation",
                reply_payload=reply_payload,
            )
            if not created:
                _log_event(
                    "h5_submit_confirmation_skipped_v1",
                    {"case_id": cid, "reason": "outbox_dedup_key_exists"},
                )
                _record_confirmation_status(cid, send_status="deduped_outbox")
                return {"sent": False, "reason": "outbox_dedup", "deduped": True}
            sent_at = datetime.now(timezone.utc).isoformat()
            _record_confirmation_status(cid, send_status="enqueued", sent_at=sent_at)
            _log_event("h5_submit_confirmation_enqueued_v1", {"case_id": cid})
            return {"sent": True, "enqueued": True}

        send_text_reply(
            cfg,
            external_userid=external_userid,
            open_kf_id=open_kf_id,
            content=content,
        )
        sent_at = datetime.now(timezone.utc).isoformat()
        _record_confirmation_status(cid, send_status="sent", sent_at=sent_at)
        _log_event("h5_submit_confirmation_sent_v1", {"case_id": cid})
        return {"sent": True}
    except Exception as exc:
        _log_event(
            "h5_submit_confirmation_failed_v1",
            {"case_id": cid, "error": type(exc).__name__},
        )
        _record_confirmation_status(cid, send_status="failed")
        return {"sent": False, "reason": "send_failed", "pending": True, "error": type(exc).__name__}
