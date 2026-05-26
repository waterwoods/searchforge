#!/usr/bin/env python3
"""
ADD_CAR_CLEAR_SUBMISSION_CONFIRMATION_HANDOFF — Founder scenario pack (triage simulation).

Usage:
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_add_car_submission_confirmation_sprint_scenarios.py [--verbose]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_conversation  # noqa: E402

PACK = REPO / "docs/sprints/archive/add_car_sprints/ADD_CAR_CLEAR_SUBMISSION_CONFIRMATION_HANDOFF/founder_scenario_pack.json"


def _run_one(sc: dict, verbose: bool) -> tuple[bool, str | None]:
    turns: list[str] = sc.get("turns") or []
    if not turns:
        return False, "no turns"
    cid = (sc.get("client_id") or "chen_kui").strip() or "chen_kui"
    conv: list[dict[str, str]] = []
    last: dict = {}
    for msg in turns:
        last = triage_conversation(msg, conv, client_id=cid)
        conv.append({"role": "customer", "text": msg})
        conv.append({"role": "system", "text": (last.get("client_reply_draft") or "").strip()})

    ex = sc.get("expect") or {}
    errs: list[str] = []

    if "handoff_ready" in ex and bool(last.get("handoff_ready")) != bool(ex["handoff_ready"]):
        errs.append(f"handoff_ready want {ex['handoff_ready']} got {last.get('handoff_ready')}")

    mc = ex.get("min_collected")
    if mc is not None:
        n = len(last.get("collected_fields") or [])
        if n < int(mc):
            errs.append(f"collected_fields length {n} < min {mc}")

    qrs = ex.get("quote_ready_status")
    if qrs is not None and (last.get("quote_ready_status") or "") != qrs:
        errs.append(f"quote_ready_status want {qrs!r} got {last.get('quote_ready_status')!r}")

    qrsi = ex.get("quote_ready_status_in")
    if qrsi:
        got = last.get("quote_ready_status") or ""
        if got not in qrsi:
            errs.append(f"quote_ready_status want one of {qrsi} got {got!r}")

    for needle in ex.get("client_reply_contains") or []:
        draft = last.get("client_reply_draft") or ""
        if needle not in draft:
            errs.append(f"draft missing {needle!r}: {draft[:120]!r}")

    sid = sc.get("id", "?")
    if verbose:
        print(f"\n=== {sid} ===")
        print("handoff_ready:", last.get("handoff_ready"))
        print("quote_ready_status:", last.get("quote_ready_status"))
        print("collected_fields:", last.get("collected_fields"))
        print("draft:", (last.get("client_reply_draft") or "")[:200])

    if errs:
        return False, f"{sid}: " + "; ".join(errs)
    return True, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()
    os.environ.setdefault("LLM_GENERATION_ENABLED", "0")

    if not PACK.exists():
        print(f"FAIL: pack not found: {PACK}", file=sys.stderr)
        return 1
    data = json.loads(PACK.read_text(encoding="utf-8"))
    scenarios = data.get("scenarios") or []
    failed = 0
    for sc in scenarios:
        ok, err = _run_one(sc, args.verbose)
        if not ok:
            failed += 1
            print(f"FAIL: {err}", file=sys.stderr)
        elif args.verbose:
            print(f"OK: {sc.get('id')}")
    if failed:
        print(f"Done: {failed}/{len(scenarios)} failed", file=sys.stderr)
        return 1
    print(f"PASS: {len(scenarios)} scenarios (Add-Car submission/confirmation sprint pack)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
