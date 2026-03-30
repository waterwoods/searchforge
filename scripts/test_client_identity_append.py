#!/usr/bin/env python3
"""
Client Identity Persistence — Append flow A/B test

Verifies that append uses case.client_id for handoff phrases.
- Create case with client_id=chen_kui
- Append follow-up → draft should use chen_kui phrases (办公室)
- Create case with client_id=demo_broker
- Append follow-up → draft should use demo_broker phrases (客服团队)

Usage:
  PYTHONPATH=. python3 scripts/test_client_identity_append.py
  PYTHONPATH=. python3 scripts/test_client_identity_append.py --url http://localhost:8001
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def test_direct() -> int:
    """Test via case_store + triage_for_append (no server)."""
    from services.fiqa_api.inbox_triage.case_store import save_case, get_case_by_id, append_follow_up_message
    from services.fiqa_api.inbox_triage.triage import triage_conversation, triage_for_append

    errors = []
    store_path = Path(tempfile.mkdtemp()) / "test_cases.json"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(store_path)

    try:
        # 1. Create case with chen_kui — use full add-car so handoff triggers
        source_ck = "[客户] 我想加新车报价\n\n[系统] 好的，先把年份和车型发我。\n\n[客户] 2021 Tesla Model Y, 90210, 下周提车，我开"
        result_ck = triage_conversation("2021 Tesla Model Y, 90210, 下周提车，我开", [
            {"role": "customer", "text": "我想加新车报价"},
            {"role": "system", "text": "好的，先把年份和车型发我。"},
        ], client_id="chen_kui")
        result_ck["handoff_ready"] = True
        saved_ck = save_case(source_ck, result_ck, client_id="chen_kui")
        case_id_ck = saved_ck["case_id"]

        # 2. Verify case has client_id
        case = get_case_by_id(case_id_ck)
        if not case or case.get("client_id") != "chen_kui":
            errors.append(f"Case should have client_id=chen_kui, got: {case.get('client_id') if case else 'None'}")

        # 3. Append to chen_kui case — triage_for_append should use case client_id
        triage_append = triage_for_append(
            existing_source_text=case.get("source_text", ""),
            new_message="好的，收到",
            client_id=case.get("client_id"),
        )
        draft_append = triage_append.get("client_reply_draft", "")
        if "办公室" not in draft_append and "陈奎" not in draft_append:
            errors.append(f"Append to chen_kui case expected 办公室/陈奎 in draft, got: {draft_append[:80]}")

        # 4. Create case with demo_broker
        result_db = triage_conversation("我想联系客服", [], client_id="demo_broker")
        result_db["handoff_ready"] = True
        saved_db = save_case("[客户] 我想联系客服", result_db, client_id="demo_broker")
        case_id_db = saved_db["case_id"]

        # 5. Append to demo_broker case (customer_requested_human + follow-up)
        case_db = get_case_by_id(case_id_db)
        triage_append_db = triage_for_append(
            existing_source_text=case_db.get("source_text", ""),
            new_message="好的，收到",
            client_id=case_db.get("client_id"),
        )
        draft_append_db = triage_append_db.get("client_reply_draft", "")
        if "客服团队" not in draft_append_db:
            errors.append(f"Append to demo_broker case expected 客服团队 in draft, got: {draft_append_db[:80]}")

    finally:
        if store_path.exists():
            store_path.unlink(missing_ok=True)
        os.environ.pop("UNIFIED_INTAKE_CASES_PATH", None)

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1
    print("PASS: Client identity persistence (append uses case client_id)")
    return 0


def test_via_http(base_url: str) -> int:
    """Test via HTTP when server running."""
    try:
        import httpx
    except ImportError:
        return test_direct()

    errors = []
    url_triage = f"{base_url.rstrip('/')}/api/inbox/triage"
    url_cases = f"{base_url.rstrip('/')}/api/inbox/cases"
    url_append = None  # set when we have case_id

    # 1. Create case with chen_kui (full add-car for handoff)
    resp = httpx.post(
        url_triage,
        json={
            "text": "2021 Tesla Model Y, 90210, 下周提车，我开",
            "persist_case": True,
            "formal_submit": True,
            "client_id": "chen_kui",
            "conversation_turns": [
                {"role": "customer", "text": "我想加新车报价"},
                {"role": "system", "text": "好的，先把年份和车型发我。"},
            ],
        },
        timeout=10.0,
    )
    if resp.status_code != 200:
        errors.append(f"Create chen_kui case: {resp.status_code} {resp.text[:200]}")
    else:
        data = resp.json()
        case_id = data.get("case_id")
        if not case_id:
            errors.append("Create chen_kui case: no case_id in response")
        else:
            # 2. Verify case has client_id
            resp_cases = httpx.get(url_cases, params={"limit": 20}, timeout=10.0)
            if resp_cases.status_code != 200:
                errors.append(f"GET cases: {resp_cases.status_code}")
            else:
                cases = resp_cases.json().get("cases", [])
                case_ck = next((c for c in cases if c.get("case_id") == case_id), None)
                if not case_ck or case_ck.get("client_id") != "chen_kui":
                    errors.append(f"Case should have client_id=chen_kui, got: {case_ck.get('client_id') if case_ck else 'None'}")

            # 3. Append — backend uses case.client_id
            url_append = f"{base_url.rstrip('/')}/api/inbox/cases/{case_id}/append-message"
            resp_append = httpx.post(
                url_append,
                json={"new_message": "好的，收到"},
                timeout=10.0,
            )
            if resp_append.status_code != 200:
                errors.append(f"Append: {resp_append.status_code} {resp_append.text[:200]}")
            else:
                updated = resp_append.json()
                draft = updated.get("client_reply_draft", "")
                if "办公室" not in draft and "陈奎" not in draft:
                    errors.append(f"Append to chen_kui case expected 办公室/陈奎, got: {draft[:80]}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1
    print("PASS: Client identity persistence (HTTP)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8001", help="Base URL (for HTTP test)")
    ap.add_argument("--direct", action="store_true", help="Only run direct (no HTTP)")
    args = ap.parse_args()

    if args.direct:
        return test_direct()

    try:
        import httpx
        r = httpx.get(f"{args.url.rstrip('/')}/healthz", timeout=2.0)
        if r.status_code == 200:
            return test_via_http(args.url)
    except Exception:
        pass
    return test_direct()


if __name__ == "__main__":
    sys.exit(main())
