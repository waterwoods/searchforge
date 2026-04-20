#!/usr/bin/env python3
"""Multi-turn pilot rehearsal against POST /api/inbox/triage (real LLM)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import httpx  # noqa: E402

BASE = "http://127.0.0.1:8001"
URL = f"{BASE}/api/inbox/triage"


def post(turns: list[dict], text: str, label: str) -> dict:
    body = {
        "text": text,
        "soft_route": "add_car",
        "conversation_turns": turns,
    }
    print(f"\n{'='*60}\n{label}\nCUSTOMER: {text!r}\n")
    r = httpx.post(URL, json=body, timeout=120.0)
    print("HTTP", r.status_code)
    r.raise_for_status()
    data = r.json()
    keys = (
        "issue_category",
        "still_needed_fields",
        "collected_fields",
        "quote_ready_status",
        "handoff_ready",
        "lifecycle_status",
        "collection_stage",
    )
    snap = {k: data.get(k) for k in keys if k in data}
    print("SNAPSHOT:", json.dumps(snap, indent=2, ensure_ascii=False))
    assist = data.get("assist") or {}
    if assist:
        print(
            "ASSIST:",
            json.dumps(
                {k: assist.get(k) for k in ("suggested_question", "customer_facing_rephrase", "clarification_needed")},
                indent=2,
                ensure_ascii=False,
            ),
        )
    dbg = data.get("truth_guardrail_debug")
    if dbg:
        print("truth_guardrail_debug:", json.dumps(dbg, indent=2, ensure_ascii=False))
    acc = data.get("truth_guardrail_accepted")
    if acc:
        print("truth_guardrail_accepted:", json.dumps(acc, indent=2, ensure_ascii=False))
    draft = (data.get("client_reply_draft") or "")[:500]
    if draft:
        print("client_reply_draft (prefix):", draft[:400], "..." if len(draft) > 400 else "")
    return data


def main() -> None:
    # --- STEP 3: minimal validation ---
    print("\n" + "#" * 60 + "\nSTEP 3 — CASE 1: add-car opener\n")
    d1 = post([], "I want to add a car", "CASE1")
    r1 = (d1.get("client_reply_draft") or "").strip()
    t_after_1: list[dict] = [{"role": "customer", "text": "I want to add a car"}]
    if r1:
        t_after_1.append({"role": "system", "text": r1})

    print("\n" + "#" * 60 + "\nSTEP 3 — CASE 2: reuse after add-car intent\n")
    post(t_after_1, "It's the same as my other car", "CASE2")

    print("\n" + "#" * 60 + "\nSTEP 3 — CASE 3: VIN deferral (add-car lane only)\n")
    post([], "VIN later", "CASE3")

    turns: list[dict] = []

    script = [
        ("T1", "I want to add a car"),
        ("T2", "It's the same as my other car"),
        ("T3", "My wife drives mostly"),
        ("T4", "her name is Jane Doe"),
        ("T5", "ZIP is 92620"),
        ("T6", "start 04/18/2026"),
        ("T7", "VIN later"),
        ("T8", "VIN is 1HGCM82633A123456"),
    ]

    last_reply = ""
    for tag, msg in script:
        data = post(turns, msg, tag)
        last_reply = (data.get("client_reply_draft") or "").strip()
        turns.append({"role": "customer", "text": msg})
        if last_reply:
            turns.append({"role": "system", "text": last_reply})

    print("\nSTEP 4 — Multi-turn pilot complete.\n")


if __name__ == "__main__":
    main()
