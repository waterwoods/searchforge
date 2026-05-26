#!/usr/bin/env python3
"""
ADD_CAR_TRANSACTION_CLARITY_SPRINT — Founder scenario pack (triage simulation).

Runs multi-turn conversations against rule-based triage (no HTTP server required).

Usage:
  PYTHONPATH=. python3 scripts/run_add_car_transaction_clarity_scenarios.py [--verbose]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_conversation  # noqa: E402

PACK = REPO / "docs/sprints/archive/add_car_sprints/ADD_CAR_TRANSACTION_CLARITY_SPRINT/founder_scenario_pack.json"


def _contains_any_zh(text: str, needles: list[str]) -> bool:
    t = text or ""
    return any(n in t for n in needles)


def run_scenario(sc: dict, verbose: bool) -> tuple[bool, str | None]:
    turns: list[str] = sc.get("turns") or []
    if not turns:
        return False, "no turns"

    conv: list[dict[str, str]] = []
    last_result: dict = {}
    for i, msg in enumerate(turns):
        last_result = triage_conversation(msg, conv, client_id="chen_kui")
        conv.append({"role": "customer", "text": msg})
        draft = last_result.get("client_reply_draft") or ""
        conv.append({"role": "system", "text": draft})

    sid = sc.get("id", "?")
    err_parts: list[str] = []

    exp_handoff = sc.get("expect_handoff_last_turn")
    if exp_handoff is True and not last_result.get("handoff_ready"):
        err_parts.append("expected handoff_ready on last turn")
    if exp_handoff is False and last_result.get("handoff_ready"):
        err_parts.append("expected handoff_ready=false on last turn")

    needles = sc.get("expect_draft_contains_any_zh") or []
    if needles:
        draft = last_result.get("client_reply_draft") or ""
        if not _contains_any_zh(draft, needles):
            err_parts.append(f"draft missing any of {needles}: {draft[:120]!r}")

    qrs = (sc.get("expect_quote_ready_status") or "").strip()
    if qrs and (last_result.get("quote_ready_status") or "") != qrs:
        err_parts.append(
            f"quote_ready_status got {last_result.get('quote_ready_status')!r} expected {qrs!r}",
        )

    if verbose:
        print(f"\n=== {sid} {sc.get('name', '')} ===")
        for i, msg in enumerate(turns):
            print(f"  C{i+1}: {msg[:100]}{'…' if len(msg) > 100 else ''}")
        print(f"  handoff_ready: {last_result.get('handoff_ready')}")
        print(f"  quote_ready_status: {last_result.get('quote_ready_status')}")
        print(f"  draft: {(last_result.get('client_reply_draft') or '')[:200]}…")

    if err_parts:
        return False, f"{sid}: " + "; ".join(err_parts)
    return True, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    data = json.loads(PACK.read_text())
    scenarios = data.get("scenarios", [])
    failed = 0
    for sc in scenarios:
        ok, err = run_scenario(sc, args.verbose)
        if not ok:
            failed += 1
            print(err or sc.get("id"))

    n = len(scenarios)
    passed = n - failed
    print(f"\nAdd-Car Transaction Clarity pack: {passed}/{n} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
