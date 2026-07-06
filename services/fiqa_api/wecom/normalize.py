"""Normalize WeCom sync_msg items into channel events (ADR-004 contract)."""

from __future__ import annotations

import json
import logging
from typing import Any

from services.fiqa_api.wecom.identity import extract_phone_from_text

logger = logging.getLogger(__name__)


def normalize_media_message(msg: dict[str, Any]) -> dict[str, Any]:
    """Map a sync_msg image/file row to a normalized channel event."""
    msgtype = (msg.get("msgtype") or "").lower()
    media_id = ""
    filename = ""
    if msgtype == "image":
        media_id = str((msg.get("image") or {}).get("media_id") or "").strip()
    elif msgtype == "file":
        fobj = msg.get("file") or {}
        media_id = str(fobj.get("media_id") or "").strip()
        filename = str(fobj.get("filename") or "").strip()
    send_time = msg.get("send_time")

    event = {
        "event_type": "message.received",
        "channel": "wecom_kf",
        "external_userid": msg.get("external_userid") or "",
        "open_kfid": msg.get("open_kfid") or "",
        "msg_id": msg.get("msgid") or "",
        "msgtype": msgtype,
        "media_id": media_id,
        "filename": filename or None,
        "text": "",
        "phone": None,
        "timestamp": send_time,
        "received_at": send_time,
        "raw": msg,
        "open_kf_id": msg.get("open_kfid") or "",
        "send_time": send_time,
        "origin": msg.get("origin"),
        "menu_id": None,
    }
    logger.info(
        "wecom_media_event_normalized_v1 %s",
        json.dumps(
            {k: v for k, v in event.items() if k not in ("raw", "external_userid")},
            ensure_ascii=False,
        ),
    )
    return event


def normalize_text_message(msg: dict[str, Any]) -> dict[str, Any]:
    """Map a sync_msg text row to a normalized channel event."""
    text_obj = msg.get("text") or {}
    content = (text_obj.get("content") or "").strip()
    menu_id = (text_obj.get("menu_id") or "").strip()
    phone = extract_phone_from_text(content)
    send_time = msg.get("send_time")

    event = {
        "event_type": "message.received",
        "channel": "wecom_kf",
        "external_userid": msg.get("external_userid") or "",
        "open_kfid": msg.get("open_kfid") or "",
        "msg_id": msg.get("msgid") or "",
        "msgtype": "text",
        "text": content,
        "phone": phone,
        "timestamp": send_time,
        "raw": msg,
        # backward-compatible aliases for slice / tests
        "open_kf_id": msg.get("open_kfid") or "",
        "send_time": send_time,
        "origin": msg.get("origin"),
        "menu_id": menu_id or None,
    }
    logger.info(
        "wecom_event_normalized_v1 %s",
        json.dumps(
            {k: v for k, v in event.items() if k != "raw"},
            ensure_ascii=False,
        ),
    )
    return event
