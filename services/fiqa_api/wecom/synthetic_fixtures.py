"""Synthetic sync_msg payloads for WeCom Track A readiness tests."""

from __future__ import annotations

from typing import Any

OPEN_KF_ID = "wktest001"
EXTERNAL_USER = "wmexternal001"


def _text_msg(
    msg_id: str,
    content: str,
    *,
    open_kfid: str = OPEN_KF_ID,
    external_userid: str = EXTERNAL_USER,
) -> dict[str, Any]:
    return {
        "msgid": msg_id,
        "open_kfid": open_kfid,
        "external_userid": external_userid,
        "origin": 3,
        "msgtype": "text",
        "send_time": 1719750000,
        "text": {"content": content},
    }


SYNTHETIC_ADD_CAR_NO_PHONE = _text_msg("msg_add_car_001", "我想加一辆车")

SYNTHETIC_ADD_CAR_WITH_PHONE = _text_msg(
    "msg_add_car_002",
    "我想加一辆车，电话626-555-0101",
)

SYNTHETIC_FOLLOWUP_VIN = _text_msg(
    "msg_add_car_003",
    "VIN 5YJ3E1EA8PF123456 6265550101",
)

SYNTHETIC_UNRELATED = _text_msg("msg_unrelated_001", "hello there")

SYNTHETIC_DUPLICATE = SYNTHETIC_ADD_CAR_WITH_PHONE
