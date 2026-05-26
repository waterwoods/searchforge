#!/usr/bin/env python3
"""Issue a minimal signed broker token (stdout). Pilot ops helper — not IAM.

Requires UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET in the environment (or .env).

Usage:
  export UNIFIED_INTAKE_BROKER_TOKEN_HMAC_SECRET='...'
  export UNIFIED_INTAKE_BROKER_TOKEN_DEPLOY_BINDING='my-prod-label'   # recommended
  PYTHONPATH=. python3 scripts/issue_minimal_broker_token.py --office-slug main-street

  PYTHONPATH=. python3 scripts/issue_minimal_broker_token.py --ttl-seconds 7200 --no-office
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = Path(__file__).resolve().parents[1]
    for name in (".env.cloudrun", ".env"):
        p = root / name
        if p.exists():
            load_dotenv(p, override=False)


def main() -> int:
    _load_dotenv()
    if str(os.getcwd()) not in sys.path:
        sys.path.insert(0, os.getcwd())

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--office-slug", default="", help="Optional office slug claim (max 256 chars)")
    p.add_argument("--no-office", action="store_true", help="Omit office_slug claim")
    p.add_argument("--ttl-seconds", type=int, default=3600, help="Token lifetime (default 3600)")
    p.add_argument(
        "--deploy-binding",
        default="",
        help="Override deploy_binding in payload (defaults to effective server binding)",
    )
    args = p.parse_args()

    from services.fiqa_api.security.minimal_signed_broker_token import issue_minimal_broker_token

    office = None if args.no_office else (args.office_slug.strip() or None)
    bind = args.deploy_binding.strip() or None
    try:
        tok = issue_minimal_broker_token(
            office_slug=office,
            ttl_seconds=max(60, int(args.ttl_seconds)),
            deploy_binding=bind,
        )
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(tok)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
