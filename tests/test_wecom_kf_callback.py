"""Unit tests for WeCom KF callback spike (crypto round-trip + routes)."""

from __future__ import annotations

import base64
import json
import os
import random
import time

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport

from services.fiqa_api.routes.wecom_kf_callback import router as wecom_kf_router
from services.fiqa_api.wecom.config import load_wecom_kf_config
from services.fiqa_api.wecom.crypto.WXBizMsgCrypt3 import Prpcrypt, SHA1, WXBizMsgCrypt

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _test_credentials() -> tuple[str, str, str]:
    token = "spike_test_token"
    corp_id = "wwspikecorp0001"
    raw_key = base64.b64encode(os.urandom(32)).decode("ascii")
    encoding_aes_key = raw_key.rstrip("=")[:43]
    return token, encoding_aes_key, corp_id


@pytest.fixture(autouse=True)
def _clear_config_cache():
    load_wecom_kf_config.cache_clear()
    yield
    load_wecom_kf_config.cache_clear()


@pytest.fixture
def wecom_env(monkeypatch):
    token, encoding_aes_key, corp_id = _test_credentials()
    monkeypatch.setenv("WECOM_KF_TOKEN", token)
    monkeypatch.setenv("WECOM_KF_ENCODING_AES_KEY", encoding_aes_key)
    monkeypatch.setenv("WECOM_CORP_ID", corp_id)
    load_wecom_kf_config.cache_clear()
    return token, encoding_aes_key, corp_id


@pytest.fixture
async def wecom_client():
    app = FastAPI()
    app.include_router(wecom_kf_router)
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


def _build_verify_query(crypto: WXBizMsgCrypt, token: str, corp_id: str) -> dict[str, str]:
    pc = Prpcrypt(crypto.key)
    ret, encrypted_echo = pc.encrypt("verify_echo_spike", corp_id)
    assert ret == 0
    echostr = encrypted_echo.decode("utf-8")
    nonce = str(random.randint(10000000, 99999999))
    timestamp = str(int(time.time()))
    sha1 = SHA1()
    ret, signature = sha1.getSHA1(token, timestamp, nonce, echostr)
    assert ret == 0
    return {
        "msg_signature": signature,
        "timestamp": timestamp,
        "nonce": nonce,
        "echostr": echostr,
    }


def _build_post_request(crypto: WXBizMsgCrypt, plain_xml: str) -> tuple[bytes, dict[str, str]]:
    nonce = str(random.randint(10000000, 99999999))
    timestamp = str(int(time.time()))
    ret, encrypted_body = crypto.EncryptMsg(plain_xml, nonce, timestamp)
    assert ret == 0
    params = {
        "msg_signature": "",
        "timestamp": timestamp,
        "nonce": nonce,
    }
    sha1 = SHA1()
    from services.fiqa_api.wecom.crypto.WXBizMsgCrypt3 import XMLParse

    xml_parse = XMLParse()
    ret, encrypt = xml_parse.extract(encrypted_body.encode("utf-8"))
    assert ret == 0
    ret, signature = sha1.getSHA1(crypto.m_sToken, timestamp, nonce, encrypt)
    assert ret == 0
    params["msg_signature"] = signature
    return encrypted_body.encode("utf-8"), params


SAMPLE_KF_EVENT_XML = """<xml>
   <ToUserName><![CDATA[wwspikecorp0001]]></ToUserName>
   <CreateTime>1348831860</CreateTime>
   <MsgType><![CDATA[event]]></MsgType>
   <Event><![CDATA[kf_msg_or_event]]></Event>
   <Token><![CDATA[ENCApHxnGDNAVNY4AaSJKj4Tb5mwsEMzxhFmHVGcra996NR]]></Token>
   <OpenKfId><![CDATA[wkxxxxxxx]]></OpenKfId>
</xml>"""


async def test_get_callback_verify_and_return_plaintext(wecom_env, wecom_client):
    token, encoding_aes_key, corp_id = wecom_env
    crypto = WXBizMsgCrypt(token, encoding_aes_key, corp_id)
    params = _build_verify_query(crypto, token, corp_id)

    resp = await wecom_client.get("/api/wecom/kf/callback", params=params)
    assert resp.status_code == 200
    assert resp.text == "verify_echo_spike"


async def test_post_callback_decrypt_log_and_return_success(wecom_env, wecom_client, caplog):
    token, encoding_aes_key, corp_id = wecom_env
    crypto = WXBizMsgCrypt(token, encoding_aes_key, corp_id)
    body, params = _build_post_request(crypto, SAMPLE_KF_EVENT_XML)

    with caplog.at_level("INFO"):
        resp = await wecom_client.post(
            "/api/wecom/kf/callback",
            params=params,
            content=body,
            headers={"Content-Type": "text/xml"},
        )
    assert resp.status_code == 200
    assert resp.text == "success"

    logged = [r.message for r in caplog.records if "wecom_kf_callback_event_v1" in r.message]
    assert logged
    payload = json.loads(logged[0].split("wecom_kf_callback_event_v1 ", 1)[1])
    assert payload["event_type"] == "wecom_kf_callback"
    assert payload["event"] == "kf_msg_or_event"
    assert payload["open_kf_id"] == "wkxxxxxxx"

    # Without WECOM_KF_SECRET, slice skips sync_msg but still logs skip reason
    skipped = [r.message for r in caplog.records if "wecom_slice_skipped_v1" in r.message]
    assert skipped


async def test_callback_returns_503_when_unconfigured(monkeypatch, wecom_client):
    monkeypatch.delenv("WECOM_KF_TOKEN", raising=False)
    monkeypatch.delenv("WECOM_TOKEN", raising=False)
    monkeypatch.delenv("WECOM_KF_ENCODING_AES_KEY", raising=False)
    monkeypatch.delenv("WECOM_ENCODING_AES_KEY", raising=False)
    monkeypatch.delenv("WECOM_CORP_ID", raising=False)
    monkeypatch.delenv("WECOM_KF_CORP_ID", raising=False)
    load_wecom_kf_config.cache_clear()

    resp = await wecom_client.get(
        "/api/wecom/kf/callback",
        params={
            "msg_signature": "x",
            "timestamp": "1",
            "nonce": "2",
            "echostr": "3",
        },
    )
    assert resp.status_code == 503
