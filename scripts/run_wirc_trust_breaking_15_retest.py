#!/usr/bin/env python3
"""
WIRC Trust-Breaking Fix — 15-case realistic retest (rule path, LLM off).

Reads:
  docs/sprints/WIRC_TRUST_BREAKING_FIX_15_CASE_RETEST/retest_scenarios.json

Usage:
  PYTHONPATH=. python3 scripts/run_wirc_trust_breaking_15_retest.py
  PYTHONPATH=. python3 scripts/run_wirc_trust_breaking_15_retest.py --verbose
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("LLM_GENERATION_ENABLED", "false")

from services.fiqa_api.inbox_triage.triage import triage_conversation  # noqa: E402

SPEC = ROOT / "docs" / "sprints" / "WIRC_TRUST_BREAKING_FIX_15_CASE_RETEST" / "retest_scenarios.json"


def _run_one(sc: dict, verbose: bool) -> tuple[bool, list[str], dict]:
    turns_in = sc.get("turns") or []
    errs: list[str] = []
    conversation: list[dict[str, str]] = []
    last_result: dict = {}

    for text in turns_in:
        text = (text or "").strip()
        if not text:
            continue
        last_result = triage_conversation(text, conversation)
        draft = last_result.get("client_reply_draft") or ""
        conversation.append({"role": "customer", "text": text})
        conversation.append({"role": "system", "text": draft})

    exp = sc.get("last_turn_expect") or {}
    draft = (last_result.get("client_reply_draft") or "").strip()

    for sub in exp.get("forbid_draft_substrings") or []:
        if sub in draft:
            errs.append(f"draft_forbidden:{sub!r}")

    for sub in exp.get("require_draft_substrings_any") or []:
        if sub not in draft:
            errs.append(f"draft_missing_any:{sub!r}")

    if "issue_category" in exp:
        if (last_result.get("issue_category") or "") != exp["issue_category"]:
            errs.append(f"issue_category got={last_result.get('issue_category')!r} want={exp['issue_category']!r}")

    if "handoff_ready" in exp:
        if bool(last_result.get("handoff_ready")) != bool(exp["handoff_ready"]):
            errs.append(f"handoff_ready got={last_result.get('handoff_ready')!r} want={exp['handoff_ready']!r}")

    fut = last_result.get("follow_up_type") or ""
    if exp.get("follow_up_type_not"):
        if fut == exp["follow_up_type_not"]:
            errs.append(f"follow_up_type got={fut!r} must_not={exp['follow_up_type_not']!r}")

    detail = {
        "id": sc.get("id"),
        "draft": draft[:500],
        "follow_up_type": fut,
        "issue_category": last_result.get("issue_category"),
        "handoff_ready": last_result.get("handoff_ready"),
    }
    if verbose:
        print(json.dumps({"scenario": sc.get("id"), **detail}, ensure_ascii=False, indent=2))

    return (len(errs) == 0, errs, detail)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    if not SPEC.exists():
        print(f"ERROR: missing {SPEC}", file=sys.stderr)
        return 1

    pack = json.loads(SPEC.read_text(encoding="utf-8"))
    scenarios = pack.get("scenarios") or []
    if len(scenarios) != 15:
        print(f"WARN: expected 15 scenarios, got {len(scenarios)}", file=sys.stderr)

    failed = 0
    for sc in scenarios:
        ok, errs, _ = _run_one(sc, args.verbose)
        if not ok:
            failed += 1
            print(f"FAIL {sc.get('id')}: {errs}")
        else:
            print(f"PASS {sc.get('id')}")

    print(f"\nResult: {len(scenarios) - failed}/{len(scenarios)} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
