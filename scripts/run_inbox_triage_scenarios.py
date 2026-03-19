#!/usr/bin/env python3
"""
Broker Inbox Triage — Scenario runner

Runs the scenario pack and reports pass/fail.
Usage:
  python scripts/run_inbox_triage_scenarios.py [--verbose] [--single ID]
  PYTHONPATH=. python scripts/run_inbox_triage_scenarios.py

Requires: configs/inbox_triage_scenarios.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Ensure repo root in path for services.fiqa_api imports
REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_message

SCENARIOS_PATH = REPO / "configs" / "inbox_triage_scenarios.json"


def load_scenarios() -> list[dict]:
    if not SCENARIOS_PATH.exists():
        print(f"ERROR: Scenario pack not found: {SCENARIOS_PATH}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(SCENARIOS_PATH.read_text())
    return data.get("scenarios", [])


REQUIRED_FIELDS = (
    "issue_category",
    "urgency",
    "broker_next_step",
    "client_prep",
    "client_reply_draft",
    "manual_followup_needed",
)

# Draft quality: for these categories, draft must contain at least one phrase (tailored, not generic)
DRAFT_QUALITY_PHRASES: dict[str, list[str]] = {
    "cancellation_warning": ["cancellation", "cancel", "urgent", "取消", "今天", "付款"],
    "payment_lapse_expiration": ["payment", "lapse", "coverage", "付款", "停保", "今天"],
    "missing_document": ["document", "copy", "send", "发我", "核对", "declaration page", "garaging proof", "驾照"],
}

DRAFT_TONE_BLOCKLIST = [
    "dear ",
    "best regards",
    "sincerely",
    "尊敬的",
    "期待您的回复",
]


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _draft_contains_expected_phrase(draft: str, phrases: list[str]) -> bool:
    lowered = (draft or "").lower()
    for phrase in phrases:
        if any(ch >= "\u4e00" and ch <= "\u9fff" for ch in phrase):
            if phrase in draft:
                return True
        elif phrase.lower() in lowered:
            return True
    return False


def _validate_output_shape(result: dict) -> str | None:
    """Return error message if output shape is invalid."""
    for k in REQUIRED_FIELDS:
        if k not in result:
            return f"missing field: {k}"
    for k in ("issue_category", "urgency", "broker_next_step", "client_prep", "client_reply_draft"):
        v = result.get(k)
        if not isinstance(v, str) or not str(v).strip():
            return f"empty or invalid: {k}"
    if not isinstance(result.get("manual_followup_needed"), bool):
        return "manual_followup_needed must be boolean"
    return None


def run_scenario(s: dict, verbose: bool) -> tuple[bool, dict, str | None]:
    """Run one scenario. Returns (passed, result, error_msg)."""
    sid = s.get("id", "?")
    input_text = s.get("input", "")
    expected_cat = (s.get("expected_category") or "").strip().lower()
    expected_urg = (s.get("expected_urgency") or "").strip().lower()
    expected_mf = s.get("expected_manual_followup")
    expected_draft_language = (s.get("expected_draft_language") or "").strip().lower()
    expected_draft_contains_any = s.get("expected_draft_contains_any") or []

    result = triage_message(input_text)

    shape_err = _validate_output_shape(result)
    if shape_err:
        if verbose:
            print(f"\n--- {sid} ---")
            print(f"Output shape FAIL: {shape_err}")
        return False, result, f"output shape: {shape_err}"

    got_cat = (result.get("issue_category") or "").strip().lower()
    got_urg = (result.get("urgency") or "").strip().lower()
    got_mf = result.get("manual_followup_needed")
    if isinstance(got_mf, str):
        got_mf = got_mf.lower() in ("true", "1", "yes")

    errors = []
    if got_cat != expected_cat:
        errors.append(f"category: got '{got_cat}' expected '{expected_cat}'")
    if got_urg != expected_urg:
        errors.append(f"urgency: got '{got_urg}' expected '{expected_urg}'")
    if got_mf != expected_mf:
        errors.append(f"manual_followup: got {got_mf} expected {expected_mf}")

    # Draft quality: high-impact categories must have tailored draft (not generic)
    if got_cat in DRAFT_QUALITY_PHRASES:
        draft = result.get("client_reply_draft") or ""
        phrases = DRAFT_QUALITY_PHRASES[got_cat]
        if not _draft_contains_expected_phrase(draft, phrases):
            errors.append(f"draft quality: expected one of {phrases} in client_reply_draft for {got_cat}")
    draft = (result.get("client_reply_draft") or "").lower()
    blocked_marker = next((marker for marker in DRAFT_TONE_BLOCKLIST if marker in draft), None)
    if blocked_marker:
        errors.append(f"draft tone: blocked marker '{blocked_marker}' found in client_reply_draft")
    if expected_draft_language == "zh" and not _contains_chinese(result.get("client_reply_draft") or ""):
        errors.append("draft language: expected Chinese draft")
    if expected_draft_language == "en" and _contains_chinese(result.get("client_reply_draft") or ""):
        errors.append("draft language: expected English draft")
    if expected_draft_contains_any and not _draft_contains_expected_phrase(
        result.get("client_reply_draft") or "",
        expected_draft_contains_any,
    ):
        errors.append(f"draft content: expected one of {expected_draft_contains_any} in client_reply_draft")

    passed = len(errors) == 0
    err_msg = "; ".join(errors) if errors else None

    if verbose:
        print(f"\n--- {sid} ---")
        print(f"Input: {input_text[:120]}...")
        print(f"Expected: category={expected_cat}, urgency={expected_urg}, manual_followup={expected_mf}")
        print(f"Got: category={got_cat}, urgency={got_urg}, manual_followup={got_mf}")
        print(f"broker_next_step: {result.get('broker_next_step', '')[:80]}...")
        print(f"client_reply_draft: {result.get('client_reply_draft', '')[:80]}...")
        if err_msg:
            print(f"FAIL: {err_msg}")
        else:
            print("PASS")

    return passed, result, err_msg


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Broker Inbox Triage scenario pack")
    ap.add_argument("--verbose", "-v", action="store_true", help="Show per-scenario output")
    ap.add_argument("--single", "-s", metavar="ID", help="Run only scenario with this ID (e.g. S1)")
    args = ap.parse_args()

    scenarios = load_scenarios()
    if args.single:
        scenarios = [s for s in scenarios if s.get("id") == args.single]
        if not scenarios:
            print(f"ERROR: No scenario with id '{args.single}'", file=sys.stderr)
            return 1

    passed = 0
    failed = 0
    for s in scenarios:
        ok, _, err = run_scenario(s, verbose=args.verbose)
        if ok:
            passed += 1
        else:
            failed += 1
            if not args.verbose:
                print(f"FAIL {s.get('id')}: {err}")

    total = passed + failed
    print(f"\nResult: {passed}/{total} passed" + (f", {failed} failed" if failed else ""))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
