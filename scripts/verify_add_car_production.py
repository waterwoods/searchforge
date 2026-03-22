#!/usr/bin/env python3
"""
Verify add-car scenarios on production API.
Usage: PYTHONPATH=. python3 scripts/verify_add_car_production.py [--url URL]
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

BASE_URL = "https://fiqa-api-1013093472160.us-west1.run.app"


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
    p.add_argument("--url", default=BASE_URL, help="Production API base URL")
    args = p.parse_args()
    url = args.url.rstrip("/")

    print(f"Verifying against {url}\n")
    results = {}

    # Scenario A — Normal add-car flow
    print("=== Scenario A: Normal add-car flow ===")
    turns_a = ["我想加一台车", "2024 Tesla Model Y，92620", "下周提车，我自己开"]
    r_a = run_scenario(url, "A", turns_a)
    results["A"] = r_a
    print(f"  issue_category: {r_a.get('issue_category')}")
    print(f"  handoff_ready: {r_a.get('handoff_ready')}")
    print(f"  broker_next_step: {r_a.get('broker_next_step', '')[:120]}...")
    print(f"  conversation_summary: {r_a.get('conversation_summary', '')[:120]}...")
    print()

    # Scenario B — Add-car + coverage side question
    print("=== Scenario B: Add-car + coverage side question ===")
    turns_b = ["我想加一台车", "2024 Tesla Model Y，92620，下周提车", "对了，coverage 能不能调一下？"]
    r_b = run_scenario(url, "B", turns_b)
    results["B"] = r_b
    draft_b = r_b.get("client_reply_draft", "")
    has_coverage = "保额" in draft_b or "coverage" in draft_b.lower() or "adjust" in draft_b.lower()
    print(f"  issue_category: {r_b.get('issue_category')}")
    print(f"  handoff_ready: {r_b.get('handoff_ready')}")
    print(f"  client_reply_draft (has coverage answer): {bool(has_coverage)}")
    print(f"  draft preview: {draft_b[:150]}...")
    print()

    # Scenario C — Add-car + garaging proof question
    print("=== Scenario C: Add-car + garaging proof question ===")
    turns_c = ["我想加一台车", "2024 BMW X5，90210，下周提车", "对了，garaging proof 是什么？"]
    r_c = run_scenario(url, "C", turns_c)
    results["C"] = r_c
    draft_c = r_c.get("client_reply_draft", "")
    has_garaging = "garaging" in draft_c.lower() or "停放" in draft_c
    print(f"  issue_category: {r_c.get('issue_category')}")
    print(f"  handoff_ready: {r_c.get('handoff_ready')}")
    print(f"  client_reply_draft (has garaging answer): {bool(has_garaging)}")
    print(f"  draft preview: {draft_c[:150]}...")
    print()

    # Scenario D — Add-car correction
    print("=== Scenario D: Add-car correction ===")
    turns_d = ["我想加一台 2024 BMW X5", "不是 X5，是 X3", "92620，我老婆开"]
    r_d = run_scenario(url, "D", turns_d)
    results["D"] = r_d
    summary_d = r_d.get("conversation_summary", "")
    next_d = r_d.get("broker_next_step", "")
    has_x3 = "X3" in next_d or "X3" in summary_d
    print(f"  issue_category: {r_d.get('issue_category')}")
    print(f"  handoff_ready: {r_d.get('handoff_ready')}")
    print(f"  broker_next_step (has X3): {bool(has_x3)}")
    print(f"  broker_next_step: {next_d[:120]}...")
    print()

    # Summary
    print("=== Summary ===")
    for k, r in results.items():
        print(f"  {k}: handoff={r.get('handoff_ready')} category={r.get('issue_category')}")


if __name__ == "__main__":
    main()
