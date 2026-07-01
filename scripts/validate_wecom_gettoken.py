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
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

_TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"

_SECRET_ENV_KEYS = (
    "WECOM_KF_SECRET",
    "WECOM_CORP_SECRET",
    "WECOM_SECRET",
    "WECOM_AGENT_SECRET",
)

_CALLBACK_ENV_KEYS = (
    "WECOM_CORP_ID",
    "WECOM_KF_TOKEN",
    "WECOM_KF_ENCODING_AES_KEY",
)


def _mask(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return "(unset)"
    if len(v) <= 8:
        return f"{v[:2]}…{v[-2:]}" if len(v) > 4 else "****"
    return f"{v[:4]}…{v[-4:]}"


def _load_dotenv(path: Path) -> None:
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


def _resolve_secret() -> tuple[str | None, str | None]:
    for key in _SECRET_ENV_KEYS:
        val = (os.getenv(key) or "").strip()
        if val:
            return key, val
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate WeCom gettoken credentials")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=REPO / ".env.cloudrun",
        help="Dotenv file to load (default: .env.cloudrun)",
    )
    args = parser.parse_args()

    _load_dotenv(args.env_file)

    print("=== WeCom credential readiness ===")
    callback_ok = True
    for key in _CALLBACK_ENV_KEYS:
        present = bool((os.getenv(key) or "").strip())
        print(f"  {key}: {'SET' if present else 'MISSING'}")
        if not present:
            callback_ok = False

    secret_key, secret = _resolve_secret()
    secret_ok = bool(secret)
    for key in _SECRET_ENV_KEYS:
        present = bool((os.getenv(key) or "").strip())
        print(f"  {key}: {'SET' if present else 'unset'}")
    print(f"  resolved_secret: {secret_key or '(none)'}")

    corp_id = (os.getenv("WECOM_CORP_ID") or "").strip()
    print(f"  masked_corp_id: {_mask(corp_id)}")
    print(f"  masked_secret: {_mask(secret or '')}")
    print(f"  credential_readiness: {'PASS' if callback_ok and secret_ok else 'FAIL'}")

    if not corp_id or not secret:
        print("\n=== gettoken result ===")
        print("  gettoken: SKIP (missing corpid or secret)")
        return 1

    try:
        import httpx
    except ImportError:
        print("\n=== gettoken result ===")
        print("  gettoken: SKIP (httpx not installed)")
        return 1

    print("\n=== gettoken result ===")
    try:
        resp = httpx.get(
            _TOKEN_URL,
            params={"corpid": corp_id, "corpsecret": secret},
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"  errcode: (request failed)")
        print(f"  errmsg: {exc}")
        print("  gettoken: FAIL")
        return 1

    errcode = data.get("errcode")
    errmsg = data.get("errmsg", "")
    print(f"  errcode: {errcode}")
    print(f"  errmsg: {errmsg}")
    print(f"  masked_corp_id: {_mask(corp_id)}")
    print(f"  masked_secret: {_mask(secret)}")
    print(f"  secret_source: {secret_key}")

    if errcode == 0:
        print("  gettoken: PASS")
        return 0

    print("  gettoken: FAIL")
    if errcode == 40001:
        print("\n=== remediation (40001 invalid credential) ===")
        print("  Re-copy or reset Secret from:")
        print("    Enterprise WeCom Admin → App Management → Apps → Self-built")
        print("    → CaseIQ AI Adapter → Secret")
        print("  Confirm CorpID from:")
        print("    My Company → Company Information → Enterprise ID")
        print("  Also confirm WeChat Customer Service → API → callable apps")
        print("    includes CaseIQ AI Adapter.")
        print(f"  Update .env.cloudrun: set {secret_key or 'WECOM_AGENT_SECRET'}=<new secret>")
    return 1


if __name__ == "__main__":
    sys.exit(main())
