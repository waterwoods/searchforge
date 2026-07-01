"""Parse decrypted WeCom callback XML into structured dicts."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any


def parse_wecom_event_xml(xml_content: bytes | str) -> dict[str, Any]:
    """Return flat tag→text mapping from WeCom callback XML."""
    if isinstance(xml_content, bytes):
        root = ET.fromstring(xml_content)
    else:
        root = ET.fromstring(xml_content.encode("utf-8"))
    parsed: dict[str, Any] = {}
    for child in root:
        parsed[child.tag] = child.text or ""
    return parsed


def structured_wecom_kf_log_payload(
    *,
    parsed_event: dict[str, Any],
    msg_signature: str,
    timestamp: str,
    nonce: str,
) -> dict[str, Any]:
    """Build stable JSON log payload for kf callback spike."""
    return {
        "event_type": "wecom_kf_callback",
        "channel": "wecom_kf",
        "msg_type": parsed_event.get("MsgType"),
        "event": parsed_event.get("Event"),
        "to_user_name": parsed_event.get("ToUserName"),
        "create_time": parsed_event.get("CreateTime"),
        "token": parsed_event.get("Token"),
        "open_kf_id": parsed_event.get("OpenKfId"),
        "msg_signature_prefix": (msg_signature or "")[:12],
        "timestamp": timestamp,
        "nonce": nonce,
        "raw_fields": parsed_event,
    }
