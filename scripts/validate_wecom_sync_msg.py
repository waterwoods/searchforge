#!/usr/bin/env python3
"""
Diagnose WeCom kf/sync_msg permission (no secrets or access_token printed).

Loads .env.cloudrun, resolves KF/agent secret, calls sync_msg once, maps errcodes.

Usage:
  PYTHONPATH=. python3 scripts/validate_wecom_sync_msg.py
  PYTHONPATH=. python3 scripts/validate_wecom_sync_msg.py --env-file .env.cloudrun
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.wecom.diagnostics import (  # noqa: E402
    SYNC_MSG_SECRET_KEYS,
    SyncMsgDiagnostic,
    map_sync_msg_errcode,
    parse_sync_msg_response,
    resolve_secret,
    secret_fingerprint,
    sync_msg_agent_fallback_warning,
)
from scripts.validate_wecom_gettoken import fetch_gettoken, load_dotenv  # noqa: E402

_TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
_SYNC_MSG_URL = "https://qyapi.weixin.qq.com/cgi-bin/kf/sync_msg"

_REQUIRED_ENV_KEYS = (
    "WECOM_CORP_ID",
    "WECOM_TEST_OPEN_KF_ID",
)

Status = Literal["PASS", "WARNING", "FAIL", "SKIP"]


@dataclass(frozen=True)
class SyncMsgCheckResult:
    status: str
    errcode: int | None
    errmsg: str
    message_count: int
    has_next: bool
    next_cursor: str | None
    secret_key: str | None
    secret_fingerprint: str
    secret_warning: str | None
    open_kf_id: str
    diagnosis: SyncMsgDiagnostic
    gettoken_errcode: int | None = None
    gettoken_errmsg: str = ""


def fetch_access_token(corp_id: str, secret: str) -> tuple[int, str, str]:
    result = fetch_gettoken(corp_id=corp_id, secret=secret, secret_key=None)
    if result.status == "SKIP":
        return -1, "", result.errmsg
    if result.status == "FAIL":
        return int(result.errcode if result.errcode is not None else -1), "", result.errmsg
    return 0, result.access_token or "", ""


def call_sync_msg(
    access_token: str,
    *,
    callback_token: str,
    open_kf_id: str,
) -> dict[str, Any]:
    try:
        import httpx
    except ImportError:
        return {"errcode": -1, "errmsg": "httpx not installed"}

    body = {
        "token": callback_token,
        "open_kfid": open_kf_id,
        "limit": 10,
    }
    try:
        resp = httpx.post(
            f"{_SYNC_MSG_URL}?access_token={access_token}",
            json=body,
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        return {"errcode": -1, "errmsg": str(exc)}


def run_sync_msg_check(
    *,
    corp_id: str | None = None,
    open_kf_id: str | None = None,
    callback_token: str | None = None,
) -> SyncMsgCheckResult:
    corp = (corp_id or os.getenv("WECOM_CORP_ID") or "").strip()
    open_kf = (open_kf_id or os.getenv("WECOM_TEST_OPEN_KF_ID") or "").strip()
    cb_token = (
        callback_token
        if callback_token is not None
        else (os.getenv("WECOM_TEST_CALLBACK_TOKEN") or "").strip()
    )

    missing = [k for k in _REQUIRED_ENV_KEYS if not (os.getenv(k) or "").strip()]
    if corp_id is not None and not corp:
        missing.append("WECOM_CORP_ID")
    if open_kf_id is not None and not open_kf:
        missing.append("WECOM_TEST_OPEN_KF_ID")

    secret_key, secret = resolve_secret(keys=SYNC_MSG_SECRET_KEYS)
    warning = sync_msg_agent_fallback_warning(secret_key)
    fp = secret_fingerprint(secret or "")

    if missing:
        diag = map_sync_msg_errcode(None)
        return SyncMsgCheckResult(
            status="SKIP",
            errcode=None,
            errmsg=f"missing {', '.join(missing)}",
            message_count=0,
            has_next=False,
            next_cursor=None,
            secret_key=secret_key,
            secret_fingerprint=fp,
            secret_warning=warning,
            open_kf_id=open_kf,
            diagnosis=diag,
        )

    if not secret:
        diag = map_sync_msg_errcode(None)
        return SyncMsgCheckResult(
            status="SKIP",
            errcode=None,
            errmsg="set WECOM_KF_SECRET or WECOM_AGENT_SECRET",
            message_count=0,
            has_next=False,
            next_cursor=None,
            secret_key=secret_key,
            secret_fingerprint=fp,
            secret_warning=warning,
            open_kf_id=open_kf,
            diagnosis=diag,
        )

    gt_err, access_token, gt_errmsg = fetch_access_token(corp, secret)
    if gt_err != 0:
        diag = map_sync_msg_errcode(40001 if gt_err == 40001 else gt_err)
        return SyncMsgCheckResult(
            status="SKIP",
            errcode=None,
            errmsg="gettoken failed",
            message_count=0,
            has_next=False,
            next_cursor=None,
            secret_key=secret_key,
            secret_fingerprint=fp,
            secret_warning=warning,
            open_kf_id=open_kf,
            diagnosis=diag,
            gettoken_errcode=gt_err,
            gettoken_errmsg=gt_errmsg,
        )

    raw = call_sync_msg(access_token, callback_token=cb_token, open_kf_id=open_kf)
    parsed = parse_sync_msg_response(raw)
    errcode = parsed.get("errcode")
    code_int = int(errcode) if isinstance(errcode, int) else None
    diag = map_sync_msg_errcode(code_int)

    status: Status = "PASS" if code_int == 0 else "FAIL"
    return SyncMsgCheckResult(
        status=status,
        errcode=code_int,
        errmsg=str(parsed.get("errmsg") or ""),
        message_count=int(parsed.get("message_count") or 0),
        has_next=bool(parsed.get("has_next")),
        next_cursor=parsed.get("next_cursor"),
        secret_key=secret_key,
        secret_fingerprint=fp,
        secret_warning=warning,
        open_kf_id=open_kf,
        diagnosis=diag,
        gettoken_errcode=0,
        gettoken_errmsg="",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose WeCom kf/sync_msg permission")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=REPO / ".env.cloudrun",
        help="Dotenv file to load (default: .env.cloudrun)",
    )
    args = parser.parse_args()

    load_dotenv(args.env_file)

    print("=== WeCom sync_msg diagnostic ===")
    for key in _REQUIRED_ENV_KEYS:
        present = bool((os.getenv(key) or "").strip())
        print(f"  {key}: {'SET' if present else 'MISSING'}")
    callback_token = (os.getenv("WECOM_TEST_CALLBACK_TOKEN") or "").strip()
    print(f"  WECOM_TEST_CALLBACK_TOKEN: {'SET' if callback_token else 'unset (optional)'}")

    secret_key, secret = resolve_secret(keys=SYNC_MSG_SECRET_KEYS)
    for key in SYNC_MSG_SECRET_KEYS:
        present = bool((os.getenv(key) or "").strip())
        print(f"  {key}: {'SET' if present else 'unset'}")
    print(f"  resolved_secret: {secret_key or '(none)'}")
    print(f"  secret_fingerprint: {secret_fingerprint(secret or '')}")

    warning = sync_msg_agent_fallback_warning(secret_key)
    if warning:
        print(f"\n  {warning}")

    corp_id = (os.getenv("WECOM_CORP_ID") or "").strip()
    open_kf_id = (os.getenv("WECOM_TEST_OPEN_KF_ID") or "").strip()
    print(f"  corp_id_fingerprint: {secret_fingerprint(corp_id)}")
    print(f"  open_kf_id: {open_kf_id}")

    result = run_sync_msg_check()
    if result.status == "SKIP":
        print("\n=== gettoken (for sync_msg) ===")
        if result.gettoken_errcode is not None:
            print(f"  gettoken_errcode: {result.gettoken_errcode}")
            if result.gettoken_errmsg:
                print(f"  gettoken_errmsg: {result.gettoken_errmsg}")
            print(f"  diagnosis: {result.diagnosis.summary}")
            print(f"  next_action: {result.diagnosis.next_action}")
        print("\n=== sync_msg result ===")
        print(f"  sync_msg: SKIP ({result.errmsg})")
        return 1

    print("\n=== gettoken (for sync_msg) ===")
    print(f"  gettoken_errcode: {result.gettoken_errcode}")
    print("  access_token: (received, not printed)")

    print("\n=== sync_msg result ===")
    print(f"  errcode: {result.errcode}")
    print(f"  errmsg: {result.errmsg}")
    print(f"  message_count: {result.message_count}")
    print(f"  has_next: {result.has_next}")
    if result.next_cursor:
        print(f"  next_cursor: {result.next_cursor}")

    print(f"\n=== diagnosis ===")
    print(f"  {result.diagnosis.summary}")
    print(f"\n=== next action ===")
    print(f"  {result.diagnosis.next_action}")

    if result.status == "PASS":
        print("\n  sync_msg: PASS")
        return 0
    print("\n  sync_msg: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
