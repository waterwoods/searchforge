#!/usr/bin/env python3
"""
WeCom KF callback spike — local round-trip test.

Generates signed GET/POST requests using the vendored Tencent crypto library,
then hits the running FastAPI server.

Usage:
  export WECOM_KF_TOKEN=...
  export WECOM_KF_ENCODING_AES_KEY=...
  export WECOM_CORP_ID=...
  bash scripts/run_demo_local.sh   # or uvicorn on 8001
  PYTHONPATH=. python3 scripts/test_wecom_kf_callback_local.py
  PYTHONPATH=. python3 scripts/test_wecom_kf_callback_local.py --url http://localhost:8001
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

SAMPLE_KF_EVENT_XML = """<xml>
   <ToUserName><![CDATA[ww12345678910]]></ToUserName>
   <CreateTime>1348831860</CreateTime>
   <MsgType><![CDATA[event]]></MsgType>
   <Event><![CDATA[kf_msg_or_event]]></Event>
   <Token><![CDATA[ENCApHxnGDNAVNY4AaSJKj4Tb5mwsEMzxhFmHVGcra996NR]]></Token>
   <OpenKfId><![CDATA[wkxxxxxxx]]></OpenKfId>
</xml>"""


def _build_verify_params(crypto, token: str, corp_id: str) -> dict[str, str]:
    from services.fiqa_api.wecom.crypto.WXBizMsgCrypt3 import Prpcrypt, SHA1

    pc = Prpcrypt(crypto.key)
    ret, encrypted_echo = pc.encrypt("local_spike_echo", corp_id)
    if ret != 0:
        raise RuntimeError(f"encrypt echostr failed: {ret}")
    echostr = encrypted_echo.decode("utf-8")
    nonce = str(random.randint(10000000, 99999999))
    timestamp = str(int(time.time()))
    sha1 = SHA1()
    ret, signature = sha1.getSHA1(token, timestamp, nonce, echostr)
    if ret != 0:
        raise RuntimeError(f"sha1 failed: {ret}")
    return {
        "msg_signature": signature,
        "timestamp": timestamp,
        "nonce": nonce,
        "echostr": echostr,
    }


def _build_post(crypto, plain_xml: str) -> tuple[bytes, dict[str, str]]:
    from services.fiqa_api.wecom.crypto.WXBizMsgCrypt3 import SHA1, XMLParse

    nonce = str(random.randint(10000000, 99999999))
    timestamp = str(int(time.time()))
    ret, encrypted_body = crypto.EncryptMsg(plain_xml, nonce, timestamp)
    if ret != 0:
        raise RuntimeError(f"EncryptMsg failed: {ret}")
    xml_parse = XMLParse()
    ret, encrypt = xml_parse.extract(encrypted_body.encode("utf-8"))
    if ret != 0:
        raise RuntimeError(f"extract failed: {ret}")
    sha1 = SHA1()
    ret, signature = sha1.getSHA1(crypto.m_sToken, timestamp, nonce, encrypt)
    if ret != 0:
        raise RuntimeError(f"sha1 failed: {ret}")
    params = {"msg_signature": signature, "timestamp": timestamp, "nonce": nonce}
    return encrypted_body.encode("utf-8"), params


def main() -> int:
    parser = argparse.ArgumentParser(description="WeCom KF callback local spike test")
    parser.add_argument("--url", default="http://localhost:8001", help="API base URL")
    args = parser.parse_args()

    from services.fiqa_api.wecom.config import load_wecom_kf_config

    cfg = load_wecom_kf_config()
    if cfg is None:
        print(
            "FAIL: set WECOM_KF_TOKEN, WECOM_KF_ENCODING_AES_KEY, WECOM_CORP_ID",
            file=sys.stderr,
        )
        return 1

    try:
        import httpx
    except ImportError:
        print("httpx not installed", file=sys.stderr)
        return 1

    crypto = cfg.crypto()
    base = args.url.rstrip("/")
    callback = f"{base}/api/wecom/kf/callback"

    # GET verify
    verify_params = _build_verify_params(crypto, cfg.token, cfg.corp_id)
    get_resp = httpx.get(callback, params=verify_params, timeout=10.0)
    print(f"GET  {get_resp.status_code} body={get_resp.text!r}")
    if get_resp.status_code != 200 or get_resp.text != "local_spike_echo":
        return 1

    # POST event
    body, post_params = _build_post(crypto, SAMPLE_KF_EVENT_XML)
    post_resp = httpx.post(
        callback,
        params=post_params,
        content=body,
        headers={"Content-Type": "text/xml"},
        timeout=10.0,
    )
    print(f"POST {post_resp.status_code} body={post_resp.text!r}")
    if post_resp.status_code != 200 or post_resp.text != "success":
        return 1

    print("PASS: WeCom KF callback spike round-trip OK")
    print("Check server logs for: wecom_kf_callback_event_v1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
