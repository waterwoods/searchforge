#!/usr/bin/env python3
"""
Case boundary append battery — new_issue vs same_case vs borderline.

Usage:
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_case_boundary_battery.py [--verbose]

Requires: configs/case_boundary_append_scenarios.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_for_append

CONFIG_PATH = REPO / "configs" / "case_boundary_append_scenarios.json"


def _draft_hits(draft: str, phrases: list[str]) -> bool:
    d = draft or ""
    for p in phrases:
        if p.lower() in d.lower() or p in d:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not CONFIG_PATH.exists():
        print(f"ERROR: {CONFIG_PATH} not found", file=sys.stderr)
        return 1

    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    scenarios = data.get("scenarios") or []
    failed = 0

    for s in scenarios:
        sid = s.get("id", "?")
        prior = s.get("prior_thread") or ""
        new_msg = s.get("new_message") or ""
        exp = (s.get("expected_boundary") or "").strip()
        result = triage_for_append(prior, new_msg)
        got = (result.get("case_boundary") or "").strip() or "same_case"
        errs: list[str] = []

        if got != exp:
            errs.append(f"boundary: got {got!r} expected {exp!r}")

        bns = (result.get("broker_next_step") or "").strip()
        draft = (result.get("client_reply_draft") or "").strip()

        if exp == "new_issue":
            if not bns.startswith("Case boundary:"):
                errs.append("broker_next_step should start with 'Case boundary:'")
        elif exp == "borderline":
            if "Case boundary unclear" not in bns:
                errs.append("broker_next_step should flag unclear boundary")
            if not result.get("human_confirmation_required"):
                errs.append("borderline should set human_confirmation_required")
        elif exp == "same_case":
            # Explicit contract: append-allowed paths may omit `case_boundary` or set it to
            # `same_case` (both mean "no split"); see triage_for_append + boundary sprint tests.
            cb = (result.get("case_boundary") or "").strip()
            if cb and cb != "same_case":
                errs.append(f"same_case expected omitted or 'same_case', got {cb!r}")
            if bns.startswith("Case boundary"):
                errs.append("same_case should not prefix broker_next_step with Case boundary")

        phrases = s.get("draft_must_contain_any") or []
        if phrases and not _draft_hits(draft, phrases):
            errs.append(f"client_reply_draft expected one of {phrases}")

        if errs:
            failed += 1
            print(f"FAIL {sid}: {'; '.join(errs)}")
            if args.verbose:
                print("  draft:", draft[:200])
                print("  broker_next_step:", bns[:200])
        else:
            print(f"OK   {sid}")

    print(f"\nCase boundary battery: {len(scenarios) - failed}/{len(scenarios)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
