"""WeCom KF sync_msg — pull message bodies after callback notification."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from services.fiqa_api.wecom.config import WeComKfConfig
from services.fiqa_api.wecom.access_token import get_access_token

logger = logging.getLogger(__name__)

WECOM_ADMIN_BLOCKED_ERRCODE = 48002

_SYNC_MSG_URL = "https://qyapi.weixin.qq.com/cgi-bin/kf/sync_msg"
_CUSTOMER_ORIGIN = 3


@dataclass(frozen=True)
class SyncPullResult:
    """Customer text messages plus the final next_cursor from sync_msg pagination."""

    messages: list[dict[str, Any]]
    next_cursor: str


def sync_kf_messages(
    cfg: WeComKfConfig,
    *,
    token: str,
    open_kf_id: str,
    cursor: str = "",
    limit: int = 50,
) -> dict[str, Any]:
    """
    Call kf/sync_msg. Returns API JSON on success.
    Raises RuntimeError on transport or WeCom API errors.
    """
    access_token = get_access_token(cfg)
    if not access_token:
        raise RuntimeError("wecom_kf_secret_not_configured_v1")

    body: dict[str, Any] = {
        "token": token,
        "open_kfid": open_kf_id,
        "limit": limit,
    }
    if cursor:
        body["cursor"] = cursor

    resp = httpx.post(
        f"{_SYNC_MSG_URL}?access_token={access_token}",
        json=body,
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    errcode = data.get("errcode")
    if errcode == WECOM_ADMIN_BLOCKED_ERRCODE:
        logger.warning(
            "wecom_pipeline_blocked_admin_v1 %s",
            json.dumps(
                {
                    "errcode": errcode,
                    "errmsg": data.get("errmsg"),
                    "open_kf_id": open_kf_id,
                    "hint": "WeCom admin must grant kf/sync_msg API permission to the app secret",
                },
                ensure_ascii=False,
            ),
        )
        raise RuntimeError(
            f"wecom_sync_msg_admin_blocked_v1 errcode={errcode} errmsg={data.get('errmsg')}"
        )
    if errcode != 0:
        raise RuntimeError(
            f"wecom_sync_msg_api_error_v1 errcode={errcode} errmsg={data.get('errmsg')}"
        )
    return data


def pull_customer_text_messages(
    cfg: WeComKfConfig,
    *,
    token: str,
    open_kf_id: str,
    start_cursor: str = "",
) -> SyncPullResult:
    """
    Pull sync_msg pages until has_more=0; return customer-origin text messages only.

    ``start_cursor`` is the persisted watermark from a prior successful sync for
    this ``open_kf_id`` (Q0.10). When set, WeCom returns only messages after
    that cursor when the API honors incremental sync.
    """
    messages: list[dict[str, Any]] = []
    cursor = (start_cursor or "").strip()
    final_next_cursor = cursor
    while True:
        data = sync_kf_messages(cfg, token=token, open_kf_id=open_kf_id, cursor=cursor)
        for item in data.get("msg_list") or []:
            if not isinstance(item, dict):
                continue
            if int(item.get("origin") or 0) != _CUSTOMER_ORIGIN:
                continue
            if (item.get("msgtype") or "").lower() != "text":
                continue
            text_obj = item.get("text") or {}
            content = (text_obj.get("content") or "").strip()
            if not content:
                continue
            messages.append(item)

        next_cursor = str(data.get("next_cursor") or "").strip()
        if next_cursor:
            final_next_cursor = next_cursor

        if int(data.get("has_more") or 0) != 1:
            break
        if not next_cursor:
            break
        cursor = next_cursor

    logger.info(
        "wecom_sync_msg_pulled_v1 %s",
        {
            "open_kf_id": open_kf_id,
            "text_message_count": len(messages),
            "start_cursor_set": bool((start_cursor or "").strip()),
            "next_cursor_set": bool(final_next_cursor),
        },
    )
    return SyncPullResult(messages=messages, next_cursor=final_next_cursor)
