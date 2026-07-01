"""
WeCom KF callback — verify, decrypt, sync_msg → Active Case bridge, respond.

GET  /api/wecom/kf/callback  — URL verification (echostr)
POST /api/wecom/kf/callback  — encrypted event → sync_msg → intent → Active Case
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, Response

from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.event_parser import parse_wecom_event_xml, structured_wecom_kf_log_payload
from services.fiqa_api.wecom.slice import process_kf_msg_or_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wecom/kf", tags=["WeCom KF Callback Spike"])

_WECOM_SUCCESS_BODY = "success"


def _require_config():
    cfg = load_wecom_kf_config()
    if cfg is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "wecom_kf_callback_not_configured_v1: set WECOM_KF_TOKEN, "
                "WECOM_KF_ENCODING_AES_KEY, WECOM_CORP_ID"
            ),
        )
    return cfg


def _crypto_error_to_http(ret: int) -> HTTPException:
    if ret == -40001:
        detail = "wecom_signature_invalid_v1"
    elif ret in (-40004, -40005):
        detail = "wecom_crypto_config_invalid_v1"
    elif ret in (-40002, -40007, -40008):
        detail = "wecom_decrypt_failed_v1"
    else:
        detail = f"wecom_crypto_error_v1 code={ret}"
    return HTTPException(status_code=403, detail=detail)


@router.get("/callback")
async def wecom_kf_callback_verify(
    msg_signature: str = Query(..., alias="msg_signature"),
    timestamp: str = Query(..., alias="timestamp"),
    nonce: str = Query(..., alias="nonce"),
    echostr: str = Query(..., alias="echostr"),
):
    """Verify WeCom callback URL and return decrypted echostr plaintext."""
    cfg = _require_config()
    crypto = cfg.crypto()
    ret, plain_echo = crypto.VerifyURL(msg_signature, timestamp, nonce, echostr)
    if ret != 0 or plain_echo is None:
        logger.warning(
            "wecom_kf_verify_failed_v1 %s",
            json.dumps({"ret": ret, "timestamp": timestamp}, ensure_ascii=False),
        )
        raise _crypto_error_to_http(ret)

    if isinstance(plain_echo, bytes):
        plain_text = plain_echo.decode("utf-8")
    else:
        plain_text = str(plain_echo)

    logger.info(
        "wecom_kf_verify_ok_v1 %s",
        json.dumps({"timestamp": timestamp, "nonce": nonce}, ensure_ascii=False),
    )
    return PlainTextResponse(content=plain_text)


@router.post("/callback")
async def wecom_kf_callback_event(
    request: Request,
    msg_signature: str = Query(..., alias="msg_signature"),
    timestamp: str = Query(..., alias="timestamp"),
    nonce: str = Query(..., alias="nonce"),
):
    """Verify signature, decrypt POST body, log structured JSON, return 200."""
    cfg = _require_config()
    raw_body = await request.body()
    if not raw_body:
        raise HTTPException(status_code=400, detail="wecom_empty_body_v1")

    crypto = cfg.crypto()
    ret, decrypted = crypto.DecryptMsg(raw_body, msg_signature, timestamp, nonce)
    if ret != 0 or decrypted is None:
        logger.warning(
            "wecom_kf_decrypt_failed_v1 %s",
            json.dumps({"ret": ret, "timestamp": timestamp}, ensure_ascii=False),
        )
        raise _crypto_error_to_http(ret)

    if isinstance(decrypted, bytes):
        decrypted_xml = decrypted
    else:
        decrypted_xml = decrypted.encode("utf-8")

    parsed = parse_wecom_event_xml(decrypted_xml)
    log_payload = structured_wecom_kf_log_payload(
        parsed_event=parsed,
        msg_signature=msg_signature,
        timestamp=timestamp,
        nonce=nonce,
    )
    logger.info("wecom_kf_callback_event_v1 %s", json.dumps(log_payload, ensure_ascii=False))

    if parsed.get("Event") == "kf_msg_or_event":
        process_kf_msg_or_event(
            cfg,
            callback_token=str(parsed.get("Token") or ""),
            open_kf_id=str(parsed.get("OpenKfId") or ""),
        )

    return Response(content=_WECOM_SUCCESS_BODY, media_type="text/plain", status_code=200)
