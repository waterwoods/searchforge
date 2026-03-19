#!/usr/bin/env python3
"""
Client-Aware Handoff — A/B variation API test

Verifies that client_id changes handoff phrases in triage output.
Usage:
  PYTHONPATH=. python3 scripts/test_client_aware_handoff.py
  PYTHONPATH=. python3 scripts/test_client_aware_handoff.py --url http://localhost:8001
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def test_direct(base_url: str) -> int:
    """Test via triage_conversation when no server."""
    from services.fiqa_api.inbox_triage.triage import triage_conversation

    errors = []

    # Chen Kui: should have 办公室 or 陈奎
    result_ck = triage_conversation(
        "我想联系陈奎办公室",
        [],
        client_id="chen_kui",
    )
    draft_ck = result_ck.get("client_reply_draft", "")
    if "陈奎" not in draft_ck and "办公室" not in draft_ck:
        errors.append(f"chen_kui expected 办公室/陈奎 in draft, got: {draft_ck[:80]}")

    # Demo broker: should have 客服团队
    result_db = triage_conversation(
        "我想联系客服",
        [],
        client_id="demo_broker",
    )
    draft_db = result_db.get("client_reply_draft", "")
    if "客服团队" not in draft_db:
        errors.append(f"demo_broker expected 客服团队 in draft, got: {draft_db[:80]}")

    # Add-car handoff: demo_broker vs chen_kui
    add_car_text = "2024 Tesla Model Y, 94102, 下周提车，我开"
    result_ck_ac = triage_conversation(add_car_text, [], client_id="chen_kui")
    result_db_ac = triage_conversation(add_car_text, [], client_id="demo_broker")
    draft_ck_ac = result_ck_ac.get("client_reply_draft", "")
    draft_db_ac = result_db_ac.get("client_reply_draft", "")
    if "办公室" not in draft_ck_ac and "陈奎" not in draft_ck_ac:
        errors.append(f"chen_kui add-car expected 办公室 in draft, got: {draft_ck_ac[:80]}")
    if "客服团队" not in draft_db_ac:
        errors.append(f"demo_broker add-car expected 客服团队 in draft, got: {draft_db_ac[:80]}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1
    print("PASS: Client-aware handoff A/B variation (direct)")
    return 0


def test_via_http(base_url: str) -> int:
    """Test via HTTP when server running."""
    try:
        import httpx
    except ImportError:
        return test_direct(base_url)

    url = f"{base_url.rstrip('/')}/api/inbox/triage"
    errors = []

    # demo_broker: 客服团队
    resp = httpx.post(
        url,
        json={"text": "我想联系客服", "soft_route": "talk_to_agent", "client_id": "demo_broker"},
        timeout=10.0,
    )
    if resp.status_code != 200:
        errors.append(f"demo_broker POST: {resp.status_code} {resp.text[:200]}")
    else:
        data = resp.json()
        draft = data.get("client_reply_draft", "")
        if "客服团队" not in draft:
            errors.append(f"demo_broker expected 客服团队, got: {draft[:80]}")

    # chen_kui: 办公室 or 陈奎
    resp = httpx.post(
        url,
        json={"text": "我想联系陈奎办公室", "soft_route": "talk_to_agent", "client_id": "chen_kui"},
        timeout=10.0,
    )
    if resp.status_code != 200:
        errors.append(f"chen_kui POST: {resp.status_code} {resp.text[:200]}")
    else:
        data = resp.json()
        draft = data.get("client_reply_draft", "")
        if "陈奎" not in draft and "办公室" not in draft:
            errors.append(f"chen_kui expected 办公室/陈奎, got: {draft[:80]}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1
    print("PASS: Client-aware handoff A/B variation (HTTP)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8001", help="Base URL (for HTTP test)")
    ap.add_argument("--direct", action="store_true", help="Only run direct (no HTTP)")
    args = ap.parse_args()

    if args.direct:
        return test_direct(args.url)

    # Try HTTP first; fallback to direct
    try:
        import httpx
        r = httpx.get(f"{args.url.rstrip('/')}/healthz", timeout=2.0)
        if r.status_code == 200:
            return test_via_http(args.url)
    except Exception:
        pass
    return test_direct(args.url)


if __name__ == "__main__":
    sys.exit(main())
