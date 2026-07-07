"""P19D-4B — WeCom Stage Complete S1 when H5 Add Vehicle photo flow completes."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from services.fiqa_api.inbox_triage.case_store import (
    record_h5_photo_flow_end_card_status,
)
from services.fiqa_api.inbox_triage.case_truth_repository import get_case_for_read
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.reply import build_h5_photo_phase_complete_reply
from services.fiqa_api.wecom.reply_outbox import enqueue_wecom_reply, wecom_reply_outbox_enabled
from services.fiqa_api.wecom.send_msg import send_text_reply, wecom_slice_send_enabled

logger = logging.getLogger(__name__)


def _log_event(event: str, payload: dict[str, Any]) -> None:
    logger.info("%s %s", event, json.dumps(payload, ensure_ascii=False, default=str))


def _end_card_already_sent(case: dict[str, Any]) -> bool:
    state = case.get("h5_photo_flow_state") or {}
    if not isinstance(state, dict):
        return False
    return bool(str(state.get("end_card_sent_at") or "").strip())


def try_send_h5_photo_flow_end_card(case_id: str) -> dict[str, Any]:
    """
    Best-effort E2-photo End Card send when H5 flow completes.
    Never raises — upload completion must succeed even if send fails.
    Deduped via h5_photo_flow_state.end_card_sent_at on the case JSON.
    """
    cid = (case_id or "").strip()
    if not cid:
        return {"sent": False, "reason": "missing_case_id"}

    case = get_case_for_read(cid)
    if case is None:
        return {"sent": False, "reason": "case_not_found"}

    if _end_card_already_sent(case):
        _log_event("h5_flow_complete_notify_skipped_v1", {"case_id": cid, "reason": "already_sent"})
        return {"sent": False, "reason": "already_sent", "deduped": True}

    external_userid = str(case.get("wecom_external_userid") or "").strip()
    open_kf_id = str(case.get("wecom_open_kf_id") or "").strip()
    if not external_userid or not open_kf_id:
        _log_event(
            "h5_flow_complete_notify_skipped_v1",
            {"case_id": cid, "reason": "no_wecom_channel_binding"},
        )
        record_h5_photo_flow_end_card_status(
            cid,
            send_status="skipped_no_channel",
        )
        return {"sent": False, "reason": "no_wecom_channel_binding"}

    content = build_h5_photo_phase_complete_reply(case)

    if not wecom_slice_send_enabled():
        _log_event(
            "h5_flow_complete_notify_skipped_v1",
            {"case_id": cid, "reason": "WECOM_SLICE_SEND_REPLY not set"},
        )
        record_h5_photo_flow_end_card_status(cid, send_status="skipped_send_disabled")
        return {"sent": False, "reason": "send_disabled"}

    cfg = load_wecom_kf_config()
    if cfg is None:
        _log_event(
            "h5_flow_complete_notify_skipped_v1",
            {"case_id": cid, "reason": "wecom_kf_not_configured"},
        )
        record_h5_photo_flow_end_card_status(cid, send_status="skipped_not_configured")
        return {"sent": False, "reason": "wecom_kf_not_configured"}

    try:
        reply_payload = {"msgtype": "text", "text": {"content": content}}
        if wecom_reply_outbox_enabled():
            created = enqueue_wecom_reply(
                msg_id=None,
                external_userid=external_userid,
                open_kf_id=open_kf_id,
                case_id=cid,
                reply_type="h5_photo_end_card",
                reply_payload=reply_payload,
            )
            if not created:
                _log_event(
                    "h5_flow_complete_notify_skipped_v1",
                    {"case_id": cid, "reason": "outbox_dedup_key_exists"},
                )
                record_h5_photo_flow_end_card_status(cid, send_status="deduped_outbox")
                return {"sent": False, "reason": "outbox_dedup", "deduped": True}
            record_h5_photo_flow_end_card_status(
                cid,
                send_status="enqueued",
                sent_at=datetime.now(timezone.utc).isoformat(),
            )
            _log_event("h5_flow_complete_notify_enqueued_v1", {"case_id": cid})
            return {"sent": True, "enqueued": True}

        send_text_reply(
            cfg,
            external_userid=external_userid,
            open_kf_id=open_kf_id,
            content=content,
        )
        record_h5_photo_flow_end_card_status(
            cid,
            send_status="sent",
            sent_at=datetime.now(timezone.utc).isoformat(),
        )
        _log_event("h5_flow_complete_notify_sent_v1", {"case_id": cid})
        return {"sent": True}
    except Exception as exc:
        _log_event(
            "h5_flow_complete_notify_failed_v1",
            {"case_id": cid, "error": type(exc).__name__},
        )
        record_h5_photo_flow_end_card_status(cid, send_status="failed")
        return {"sent": False, "reason": "send_failed", "error": type(exc).__name__}
