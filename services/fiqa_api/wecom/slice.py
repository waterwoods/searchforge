"""WeCom vertical slice orchestrator — callback → sync_msg → intent → reply."""

from __future__ import annotations

import json
import logging
from typing import Any

from services.fiqa_api.wecom.active_case_bridge import ingest_wecom_text_to_active_case
from services.fiqa_api.wecom.config import WeComKfConfig, wecom_kf_api_configured
from services.fiqa_api.wecom.intent import canonical_intent, classify_wecom_intent
from services.fiqa_api.wecom.normalize import normalize_text_message
from services.fiqa_api.wecom.reply import build_guided_menu_payload, build_slice_reply
from services.fiqa_api.wecom.send_msg import send_menu_reply, send_text_reply, wecom_slice_send_enabled
from services.fiqa_api.wecom.sync_msg import pull_customer_text_messages

logger = logging.getLogger(__name__)


def _log_slice(stage: str, payload: dict[str, Any]) -> None:
    logger.info("wecom_slice_%s %s", stage, json.dumps(payload, ensure_ascii=False))


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
        else:
            raw_messages = pull_customer_text_messages(
                cfg, token=callback_token, open_kf_id=open_kf_id
            )
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

    for raw in raw_messages:
        normalized = normalize_text_message(raw)

        intent_result = classify_wecom_intent(
            normalized.get("text") or "",
            menu_id=normalized.get("menu_id"),
        )
        guided_menu = intent_result.confidence == "low" or intent_result.intent == "unclear"
        detected = canonical_intent(intent_result.intent)
        reply_text = build_slice_reply(intent_result.intent, guided_menu=guided_menu)

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

        if send_enabled and normalized.get("external_userid") and normalized.get("open_kf_id"):
            try:
                if guided_menu:
                    send_menu_reply(
                        cfg,
                        external_userid=str(normalized["external_userid"]),
                        open_kf_id=str(normalized["open_kf_id"]),
                        menu=build_guided_menu_payload(),
                    )
                else:
                    send_text_reply(
                        cfg,
                        external_userid=str(normalized["external_userid"]),
                        open_kf_id=str(normalized["open_kf_id"]),
                        content=reply_text,
                    )
                outcome["reply_sent"] = True
                _log_slice("reply_sent_v1", {"msg_id": normalized.get("msg_id"), "sent": True})
            except Exception as exc:
                outcome["reply_send_error"] = str(exc)
                _log_slice(
                    "reply_send_failed_v1",
                    {"msg_id": normalized.get("msg_id"), "error": str(exc)},
                )
        else:
            _log_slice(
                "reply_logged_only_v1",
                {
                    "msg_id": normalized.get("msg_id"),
                    "send_enabled": send_enabled,
                    "reason": "WECOM_SLICE_SEND_REPLY not set" if not send_enabled else "missing_ids",
                },
            )

        results.append(outcome)

    return results
