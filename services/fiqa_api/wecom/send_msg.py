"""WeCom KF outbound send_msg (optional — gated by env)."""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import httpx

from services.fiqa_api.wecom.config import WeComKfConfig
from services.fiqa_api.wecom.access_token import get_access_token

logger = logging.getLogger(__name__)

_SEND_MSG_URL = "https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg"


def wecom_slice_send_enabled() -> bool:
    return (os.getenv("WECOM_SLICE_SEND_REPLY") or "").strip().lower() in ("1", "true", "yes")


def send_text_reply(
    cfg: WeComKfConfig,
    *,
    external_userid: str,
    open_kf_id: str,
    content: str,
) -> dict[str, Any]:
    """Send a text message to the customer via kf/send_msg."""
    return _send_kf_message(
        cfg,
        external_userid=external_userid,
        open_kf_id=open_kf_id,
        body={
            "msgtype": "text",
            "text": {"content": content},
        },
    )


def send_menu_reply(
    cfg: WeComKfConfig,
    *,
    external_userid: str,
    open_kf_id: str,
    menu: dict[str, Any],
) -> dict[str, Any]:
    """Send a native WeCom msgmenu (clickable topic buttons)."""
    return _send_kf_message(
        cfg,
        external_userid=external_userid,
        open_kf_id=open_kf_id,
        body={
            "msgtype": "msgmenu",
            "msgmenu": menu,
        },
    )


def _send_kf_message(
    cfg: WeComKfConfig,
    *,
    external_userid: str,
    open_kf_id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    access_token = get_access_token(cfg)
    if not access_token:
        raise RuntimeError("wecom_kf_secret_not_configured_v1")

    body = {
        "touser": external_userid,
        "open_kfid": open_kf_id,
        "msgid": f"slice_{uuid.uuid4().hex[:24]}",
        **body,
    }
    resp = httpx.post(
        f"{_SEND_MSG_URL}?access_token={access_token}",
        json=body,
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("errcode") != 0:
        raise RuntimeError(
            f"wecom_send_msg_api_error_v1 errcode={data.get('errcode')} errmsg={data.get('errmsg')}"
        )
    return data
