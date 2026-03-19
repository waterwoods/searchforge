#!/usr/bin/env python3
"""
Run the Chen Kui proxy calibration pack against Unified Intake triage.

Usage:
  PYTHONPATH=. python3 scripts/run_chen_kui_proxy_calibration.py
  PYTHONPATH=. python3 scripts/run_chen_kui_proxy_calibration.py --verbose
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_message

PACK_PATH = REPO / "configs" / "chen_kui_proxy_calibration_cases.json"


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _draft_contains_expected_phrase(draft: str, phrases: list[str]) -> bool:
    lowered = (draft or "").lower()
    for phrase in phrases:
        if any("\u4e00" <= ch <= "\u9fff" for ch in phrase):
            if phrase in draft:
                return True
        elif phrase.lower() in lowered:
            return True
    return False


def load_cases() -> list[dict]:
    payload = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    return payload.get("cases", [])


def run_case(case: dict, verbose: bool) -> tuple[bool, list[str]]:
    result = triage_message(case.get("input", ""))
    errors: list[str] = []

    expected_category = (case.get("expected_category") or "").strip().lower()
    expected_urgency = (case.get("expected_urgency") or "").strip().lower()
    expected_manual_followup = case.get("expected_manual_followup")
    expected_draft_language = (case.get("expected_draft_language") or "").strip().lower()
    expected_draft_contains_any = case.get("expected_draft_contains_any") or []

    if (result.get("issue_category") or "").strip().lower() != expected_category:
        errors.append(
            f"category: got '{result.get('issue_category')}' expected '{expected_category}'"
        )
    if (result.get("urgency") or "").strip().lower() != expected_urgency:
        errors.append(f"urgency: got '{result.get('urgency')}' expected '{expected_urgency}'")
    if result.get("manual_followup_needed") != expected_manual_followup:
        errors.append(
            f"manual_followup: got {result.get('manual_followup_needed')} expected {expected_manual_followup}"
        )

    draft = result.get("client_reply_draft") or ""
    if expected_draft_language == "zh" and not _contains_chinese(draft):
        errors.append("draft language: expected Chinese draft")
    if expected_draft_language == "en" and _contains_chinese(draft):
        errors.append("draft language: expected English draft")
    if expected_draft_contains_any and not _draft_contains_expected_phrase(draft, expected_draft_contains_any):
        errors.append(f"draft content: expected one of {expected_draft_contains_any}")

    if verbose:
        print(f"\n--- {case.get('id', '?')} ---")
        print(f"Input: {case.get('input', '')}")
        print(
            "Expected:",
            f"category={expected_category}, urgency={expected_urgency}, manual_followup={expected_manual_followup}",
        )
        print(
            "Got:",
            f"category={result.get('issue_category')}, urgency={result.get('urgency')}, manual_followup={result.get('manual_followup_needed')}",
        )
        print(f"broker_next_step: {result.get('broker_next_step')}")
        print(f"client_reply_draft: {draft}")
        if errors:
            print("FAIL:", "; ".join(errors))
        else:
            print("PASS")

    return not errors, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Chen Kui proxy calibration pack")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show per-case output")
    args = parser.parse_args()

    passed = 0
    failed = 0
    for case in load_cases():
        ok, errors = run_case(case, verbose=args.verbose)
        if ok:
            passed += 1
        else:
            failed += 1
            if not args.verbose:
                print(f"FAIL {case.get('id')}: {'; '.join(errors)}")

    total = passed + failed
    print(f"\nResult: {passed}/{total} passed" + (f", {failed} failed" if failed else ""))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
