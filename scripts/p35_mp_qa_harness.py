#!/usr/bin/env python3
"""
P35.1 — Founder Mini Program QA reset harness CLI.

Usage:
  PYTHONPATH=. python3 scripts/p35_mp_qa_harness.py status
  PYTHONPATH=. python3 scripts/p35_mp_qa_harness.py inspect --session-id wx_xxxx
  PYTHONPATH=. python3 scripts/p35_mp_qa_harness.py fresh --session-id wx_xxxx --confirm FRESH
  PYTHONPATH=. python3 scripts/p35_mp_qa_harness.py active --session-id wx_xxxx --confirm ACTIVE
  PYTHONPATH=. python3 scripts/p35_mp_qa_harness.py request-more --session-id wx_xxxx --confirm REQUEST_MORE

How to get session_id on a real phone / DevTools:
  In WeChat DevTools console:
    wx.getStorageSync('mp_customer_session_id')

Enablement (required):
  ENABLE_P35_MP_QA_HARNESS=1
  UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1
  UNIFIED_INTAKE_SUPPORT_API_KEY=...   # when production-like / QA Cloud
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _configure_target(target: str) -> str:
    from scripts.demo_db_resolve import apply_qa_postgres_env, ensure_h5_task_token_secret

    t = (target or "local").strip().lower()
    if t in ("qa", "cloud", "gcp"):
        ident = apply_qa_postgres_env(for_write=True)
        os.environ.setdefault("ENV", "prod")
        ensure_h5_task_token_secret()
        os.environ["ENABLE_P35_MP_QA_HARNESS"] = "1"
        os.environ["UNIFIED_INTAKE_QA_FIXTURE_SURFACE"] = "1"
        return f"qa_cloud_sql ({ident.masked()})"
    os.environ.setdefault("ENV", "development")
    os.environ["ENABLE_P35_MP_QA_HARNESS"] = "1"
    os.environ["UNIFIED_INTAKE_QA_FIXTURE_SURFACE"] = "1"
    return "local"


def _print(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="P35.1 Mini Program Founder QA harness")
    parser.add_argument(
        "command",
        choices=["status", "inspect", "fresh", "active", "request-more", "audit"],
    )
    parser.add_argument("--session-id", default="", help="Exact wx_* session id from Mini Program storage")
    parser.add_argument("--sim-openid", default="", help="Local/test only when WECHAT_MP_ALLOW_SIMULATE=1")
    parser.add_argument("--confirm", default="", help="FRESH | ACTIVE | REQUEST_MORE")
    parser.add_argument("--target", default="local", choices=["local", "qa", "cloud", "gcp"])
    parser.add_argument("--actor", default="founder")
    args = parser.parse_args()

    storage = _configure_target(args.target)
    from services.fiqa_api.inbox_triage import p35_mp_qa_harness as hx

    if args.command == "status":
        out = hx.harness_status()
        out["storage"] = storage
        _print(out)
        return 0 if out.get("enabled") else 2

    session_id = (args.session_id or "").strip()
    if not session_id and args.sim_openid:
        session_id = hx.resolve_person_link_from_sim_openid(args.sim_openid)

    try:
        if args.command == "inspect":
            _print(hx.inspect_identity(session_id))
            return 0
        if args.command == "audit":
            _print({"ok": True, "events": hx.list_audit_events(limit=20), "storage": storage})
            return 0
        if args.command == "fresh":
            _print(
                hx.preset_fresh_customer(
                    session_id=session_id,
                    confirm=args.confirm,
                    actor=args.actor,
                )
            )
            return 0
        if args.command == "active":
            _print(
                hx.preset_active_claim(
                    session_id=session_id,
                    confirm=args.confirm,
                    actor=args.actor,
                )
            )
            return 0
        if args.command == "request-more":
            _print(
                hx.preset_request_more(
                    session_id=session_id,
                    confirm=args.confirm,
                    actor=args.actor,
                )
            )
            return 0
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 3

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
