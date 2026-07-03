#!/usr/bin/env python3
"""
Validate WeCom gettoken credentials (no secrets printed).

Loads .env.cloudrun (or current env), resolves secret in product order, calls gettoken.

Usage:
  PYTHONPATH=. python3 scripts/validate_wecom_gettoken.py
  PYTHONPATH=. python3 scripts/validate_wecom_gettoken.py --env-file .env.cloudrun
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.wecom.diagnostics import (  # noqa: E402
    SECRET_ENV_KEYS,
    gettoken_agent_fallback_warning,
    resolve_secret,
    secret_fingerprint,
)

_TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"

_CALLBACK_ENV_KEYS = (
    "WECOM_CORP_ID",
    "WECOM_KF_TOKEN",
    "WECOM_KF_ENCODING_AES_KEY",
)

Status = Literal["PASS", "WARNING", "FAIL", "SKIP"]


@dataclass(frozen=True)
class EnvPresence:
    key: str
    status: str
    detail: str = ""


@dataclass(frozen=True)
class CredentialReadiness:
    cloudrun_env: str
    env_file: Path | None
    callback_keys: tuple[EnvPresence, ...]
    secret_keys: tuple[EnvPresence, ...]
    resolved_secret_key: str | None
    secret_fingerprint: str
    secret_class_status: str
    secret_warning: str | None
    corp_id_fingerprint: str


@dataclass(frozen=True)
class GettokenResult:
    status: str
    errcode: int | None
    errmsg: str
    secret_key: str | None
    secret_fingerprint: str
    secret_warning: str | None
    access_token: str | None = None


@dataclass(frozen=True)
class CallbackProbeResult:
    base_url: str
    route_status: str
    verify_status: str
    decrypt_status: str
    route_detail: str = ""
    verify_detail: str = ""
    decrypt_detail: str = ""


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _presence(key: str, *, optional: bool = False) -> EnvPresence:
    present = bool((os.getenv(key) or "").strip())
    if present:
        return EnvPresence(key=key, status="PASS", detail="SET")
    if optional:
        return EnvPresence(key=key, status="WARNING", detail="NOT FOUND")
    return EnvPresence(key=key, status="FAIL", detail="NOT FOUND")


def check_credentials(*, env_file: Path | None = None) -> CredentialReadiness:
    env_path = env_file
    cloud_status: Status = "PASS" if env_path and env_path.is_file() else "WARNING"

    callback_keys = tuple(_presence(key) for key in _CALLBACK_ENV_KEYS)
    secret_keys = tuple(
        EnvPresence(
            key=key,
            status="PASS" if (os.getenv(key) or "").strip() else "WARNING",
            detail="SET" if (os.getenv(key) or "").strip() else "NOT FOUND",
        )
        for key in SECRET_ENV_KEYS
    )

    secret_key, secret = resolve_secret()
    kf_set = bool((os.getenv("WECOM_KF_SECRET") or "").strip())
    if not secret:
        secret_class_status: Status = "FAIL"
    elif not kf_set and secret_key == "WECOM_AGENT_SECRET":
        secret_class_status = "WARNING"
    else:
        secret_class_status = "PASS"

    warning = gettoken_agent_fallback_warning(secret_key)
    corp_id = (os.getenv("WECOM_CORP_ID") or "").strip()

    return CredentialReadiness(
        cloudrun_env=cloud_status,
        env_file=env_path if env_path and env_path.is_file() else None,
        callback_keys=callback_keys,
        secret_keys=secret_keys,
        resolved_secret_key=secret_key,
        secret_fingerprint=secret_fingerprint(secret or ""),
        secret_class_status=secret_class_status,
        secret_warning=warning,
        corp_id_fingerprint=secret_fingerprint(corp_id),
    )


def fetch_gettoken(*, corp_id: str, secret: str, secret_key: str | None) -> GettokenResult:
    warning = gettoken_agent_fallback_warning(secret_key)
    fp = secret_fingerprint(secret)
    if not corp_id or not secret:
        return GettokenResult(
            status="SKIP",
            errcode=None,
            errmsg="missing corpid or secret",
            secret_key=secret_key,
            secret_fingerprint=fp,
            secret_warning=warning,
        )

    try:
        import httpx
    except ImportError:
        return GettokenResult(
            status="SKIP",
            errcode=None,
            errmsg="httpx not installed",
            secret_key=secret_key,
            secret_fingerprint=fp,
            secret_warning=warning,
        )

    try:
        resp = httpx.get(
            _TOKEN_URL,
            params={"corpid": corp_id, "corpsecret": secret},
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return GettokenResult(
            status="FAIL",
            errcode=None,
            errmsg=str(exc),
            secret_key=secret_key,
            secret_fingerprint=fp,
            secret_warning=warning,
        )

    errcode = data.get("errcode")
    errmsg = str(data.get("errmsg") or "")
    if errcode == 0:
        token = str(data.get("access_token") or "")
        return GettokenResult(
            status="PASS",
            errcode=0,
            errmsg=errmsg,
            secret_key=secret_key,
            secret_fingerprint=fp,
            secret_warning=warning,
            access_token=token or None,
        )

    return GettokenResult(
        status="FAIL",
        errcode=int(errcode) if errcode is not None else None,
        errmsg=errmsg,
        secret_key=secret_key,
        secret_fingerprint=fp,
        secret_warning=warning,
    )


def _build_verify_params(crypto, token: str, corp_id: str) -> dict[str, str]:
    from services.fiqa_api.wecom.crypto.WXBizMsgCrypt3 import Prpcrypt, SHA1

    pc = Prpcrypt(crypto.key)
    ret, encrypted_echo = pc.encrypt("wecom_readiness_echo", corp_id)
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


_SAMPLE_KF_EVENT_XML = """<xml>
   <ToUserName><![CDATA[ww12345678910]]></ToUserName>
   <CreateTime>1348831860</CreateTime>
   <MsgType><![CDATA[event]]></MsgType>
   <Event><![CDATA[kf_msg_or_event]]></Event>
   <Token><![CDATA[readiness_probe_token]]></Token>
   <OpenKfId><![CDATA[wkxxxxxxx]]></OpenKfId>
</xml>"""


def probe_wecom_callback(base_url: str) -> CallbackProbeResult:
    from services.fiqa_api.wecom.config import load_wecom_kf_config

    base = base_url.rstrip("/")
    callback = f"{base}/api/wecom/kf/callback"

    try:
        import httpx
    except ImportError:
        return CallbackProbeResult(
            base_url=base,
            route_status="FAIL",
            verify_status="SKIP",
            decrypt_status="SKIP",
            route_detail="httpx not installed",
        )

    try:
        route_resp = httpx.get(f"{base}/health/live", timeout=10.0)
        if route_resp.status_code >= 500:
            return CallbackProbeResult(
                base_url=base,
                route_status="FAIL",
                verify_status="SKIP",
                decrypt_status="SKIP",
                route_detail=f"health/live HTTP {route_resp.status_code}",
            )
    except Exception as exc:
        return CallbackProbeResult(
            base_url=base,
            route_status="FAIL",
            verify_status="SKIP",
            decrypt_status="SKIP",
            route_detail=str(exc),
        )

    route_status: Status = "PASS"
    route_detail = "reachable"

    cfg = load_wecom_kf_config()
    if cfg is None:
        return CallbackProbeResult(
            base_url=base,
            route_status=route_status,
            verify_status="FAIL",
            decrypt_status="SKIP",
            route_detail=route_detail,
            verify_detail="callback credentials not configured",
        )

    crypto = cfg.crypto()
    try:
        verify_params = _build_verify_params(crypto, cfg.token, cfg.corp_id)
        get_resp = httpx.get(callback, params=verify_params, timeout=10.0)
        if get_resp.status_code == 200 and get_resp.text == "wecom_readiness_echo":
            verify_status: Status = "PASS"
            verify_detail = "echostr round-trip OK"
        else:
            verify_status = "FAIL"
            verify_detail = f"HTTP {get_resp.status_code} body={get_resp.text!r}"
    except Exception as exc:
        verify_status = "FAIL"
        verify_detail = str(exc)

    if verify_status != "PASS":
        return CallbackProbeResult(
            base_url=base,
            route_status=route_status,
            verify_status=verify_status,
            decrypt_status="SKIP",
            route_detail=route_detail,
            verify_detail=verify_detail,
        )

    try:
        body, post_params = _build_post(crypto, _SAMPLE_KF_EVENT_XML)
        post_resp = httpx.post(
            callback,
            params=post_params,
            content=body,
            headers={"Content-Type": "text/xml"},
            timeout=10.0,
        )
        if post_resp.status_code == 200 and post_resp.text == "success":
            decrypt_status: Status = "PASS"
            decrypt_detail = "encrypted event accepted"
        else:
            decrypt_status = "FAIL"
            decrypt_detail = f"HTTP {post_resp.status_code} body={post_resp.text!r}"
    except Exception as exc:
        decrypt_status = "FAIL"
        decrypt_detail = str(exc)

    return CallbackProbeResult(
        base_url=base,
        route_status=route_status,
        verify_status=verify_status,
        decrypt_status=decrypt_status,
        route_detail=route_detail,
        verify_detail=verify_detail,
        decrypt_detail=decrypt_detail,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate WeCom gettoken credentials")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=REPO / ".env.cloudrun",
        help="Dotenv file to load (default: .env.cloudrun)",
    )
    args = parser.parse_args()

    load_dotenv(args.env_file)
    creds = check_credentials(env_file=args.env_file)

    print("=== WeCom credential readiness ===")
    for item in creds.callback_keys:
        print(f"  {item.key}: {item.detail}")
    for item in creds.secret_keys:
        print(f"  {item.key}: {item.detail}")
    print(f"  resolved_secret_class: {creds.resolved_secret_key or '(none)'}")
    print(f"  secret_fingerprint: {creds.secret_fingerprint}")
    if creds.secret_warning:
        print(f"\n  {creds.secret_warning}")
    print(f"  corp_id_fingerprint: {creds.corp_id_fingerprint}")
    callback_ok = all(i.status != "FAIL" for i in creds.callback_keys)
    secret_ok = creds.resolved_secret_key is not None
    print(f"  credential_readiness: {'PASS' if callback_ok and secret_ok else 'FAIL'}")

    corp_id = (os.getenv("WECOM_CORP_ID") or "").strip()
    _, secret = resolve_secret()
    if not corp_id or not secret:
        print("\n=== gettoken result ===")
        print("  gettoken: SKIP (missing corpid or secret)")
        return 1

    print("\n=== gettoken result ===")
    result = fetch_gettoken(corp_id=corp_id, secret=secret, secret_key=creds.resolved_secret_key)
    if result.errcode is not None:
        print(f"  errcode: {result.errcode}")
    elif result.status == "FAIL":
        print("  errcode: (request failed)")
    print(f"  errmsg: {result.errmsg}")
    print(f"  secret_class_used: {result.secret_key}")
    print(f"  secret_fingerprint: {result.secret_fingerprint}")
    if result.secret_warning:
        print(f"  secret_warning: {result.secret_warning}")

    if result.status == "PASS":
        print("  gettoken: PASS")
        return 0
    if result.status == "SKIP":
        print(f"  gettoken: SKIP ({result.errmsg})")
        return 1

    print("  gettoken: FAIL")
    if result.errcode == 40001:
        print("\n=== remediation (40001 invalid credential) ===")
        print("  Re-copy or reset Secret from:")
        print("    Enterprise WeCom Admin → App Management → Apps → Self-built")
        print("    → CaseIQ AI Adapter → Secret")
        print("  Confirm CorpID from:")
        print("    My Company → Company Information → Enterprise ID")
        print("  Also confirm WeChat Customer Service → API → callable apps")
        print("    includes CaseIQ AI Adapter.")
        print(
            f"  Update .env.cloudrun: set {result.secret_key or 'WECOM_AGENT_SECRET'}=<new secret>"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
