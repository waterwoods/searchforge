#!/usr/bin/env python3
"""
Verify add-car + materials-sent scenarios in production.
Scenarios from Redeploy Backend for Add-Car Materials-Sent Hardening sprint.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

try:
    import httpx
except ImportError:
    print("pip install httpx")
    sys.exit(1)


def triage(url: str, text: str, conv: list[dict] | None = None) -> dict:
    payload = {"text": text}
    if conv:
        payload["conversation_turns"] = conv
    r = httpx.post(f"{url.rstrip('/')}/api/inbox/triage", json=payload, timeout=30.0)
    r.raise_for_status()
    return r.json()


def run_scenario(url: str, name: str, turns: list[str]) -> dict:
    conv = []
    last = None
    for i, text in enumerate(turns):
        last = triage(url, text, conv if conv else None)
        conv.append({"role": "customer", "text": text})
        conv.append({"role": "system", "text": last.get("client_reply_draft", "")})
    return last


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="https://fiqa-api-1013093472160.us-west1.run.app", help="Production API base URL")
    args = p.parse_args()
    url = args.url.rstrip("/")

    print(f"Verifying materials-sent scenarios against {url}\n")

    # Scenario 1 — Add-car + materials sent
    print("=" * 60)
    print("Scenario 1 — Add-car + materials sent")
    print("=" * 60)
    turns1 = [
        "我想加车",
        "2024 Tesla Model Y 90210",
        "下周提车 registration 发你微信了",
    ]
    print("Input sequence:")
    for i, t in enumerate(turns1, 1):
        print(f"  {i}. {t}")
    r1 = run_scenario(url, "1", turns1)
    print("\nObserved:")
    print(f"  issue_category: {r1.get('issue_category')}")
    print(f"  handoff_ready: {r1.get('handoff_ready')}")
    print(f"  broker_next_step: {r1.get('broker_next_step', '')}")
    print(f"  collected_fields: {r1.get('collected_fields', [])}")
    print(f"  still_needed_fields: {r1.get('still_needed_fields', [])}")
    print(f"  client_reply_draft: {r1.get('client_reply_draft', '')[:200]}...")
    verify1 = "Verify materials received" in (r1.get("broker_next_step") or "")
    handoff1 = r1.get("handoff_ready") is True
    collected_ok1 = "customer_says_sent_materials" in (r1.get("collected_fields") or [])
    print(f"\n  PASS checks: broker_next_step has 'Verify materials received'={verify1}, handoff_ready={handoff1}, customer_says_sent_materials in collected={collected_ok1}")
    print()

    # Scenario 2 — Add-car + correction + materials sent
    print("=" * 60)
    print("Scenario 2 — Add-car + correction + materials sent")
    print("=" * 60)
    turns2 = [
        "我想加车 2021 Honda",
        "不是这个 是 2024 Tesla",
        "90210 下周提车 材料发你微信了",
    ]
    print("Input sequence:")
    for i, t in enumerate(turns2, 1):
        print(f"  {i}. {t}")
    r2 = run_scenario(url, "2", turns2)
    print("\nObserved:")
    print(f"  issue_category: {r2.get('issue_category')}")
    print(f"  handoff_ready: {r2.get('handoff_ready')}")
    print(f"  broker_next_step: {r2.get('broker_next_step', '')}")
    print(f"  collected_fields: {r2.get('collected_fields', [])}")
    summary2 = r2.get("conversation_summary", "")
    print(f"  conversation_summary: {summary2[:200]}...")
    verify2 = "Verify materials received" in (r2.get("broker_next_step") or "")
    handoff2 = r2.get("handoff_ready") is True
    has_tesla = "Tesla" in (r2.get("broker_next_step") or "") or "Tesla" in summary2
    print(f"\n  PASS checks: broker_next_step has 'Verify materials received'={verify2}, handoff_ready={handoff2}, vehicle is Tesla (not Honda)={has_tesla}")
    print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    s1_pass = verify1 and handoff1
    s2_pass = verify2 and handoff2
    print(f"  Scenario 1: {'PASS' if s1_pass else 'FAIL'}")
    print(f"  Scenario 2: {'PASS' if s2_pass else 'FAIL'}")
    sys.exit(0 if (s1_pass and s2_pass) else 1)


if __name__ == "__main__":
    main()
