#!/usr/bin/env python3
"""
Second Broker / Client-Pack Drill — run triage_conversation against socal_precision.

Loads scenarios from docs/sprints/SECOND_BROKER_CLIENT_PACK_DRILL/drill_scenarios.json.
Uses rule/LLM-off path by default for determinism (set LLM_GENERATION_ENABLED=0).

Usage:
  PYTHONPATH=. python3 scripts/run_second_broker_drill.py [--verbose]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

os.environ.setdefault("LLM_GENERATION_ENABLED", "0")

from services.fiqa_api.inbox_triage.config_loader import (  # noqa: E402
    get_handoff_phrases,
    get_ui_copy,
)
from services.fiqa_api.inbox_triage.triage import triage_conversation  # noqa: E402

SCENARIOS_PATH = REPO / "docs/sprints/SECOND_BROKER_CLIENT_PACK_DRILL/drill_scenarios.json"


def _contains_any(text: str, phrases: list[str]) -> bool:
    t = text or ""
    return any(p in t for p in phrases if p)


def _contains_none(text: str, banned: list[str]) -> bool:
    t = text or ""
    return not any(b in t for b in banned if b)


def _check_expect(result: dict, exp: dict, sid: str, step_i: int | None, verbose: bool) -> list[str]:
    errs: list[str] = []
    prefix = f"{sid}" + (f" step {step_i}" if step_i is not None else "")
    draft = result.get("client_reply_draft") or ""

    if "handoff_ready" in exp and result.get("handoff_ready") is not bool(exp["handoff_ready"]):
        errs.append(f"{prefix}: handoff_ready got {result.get('handoff_ready')} expected {exp['handoff_ready']}")

    if "issue_category" in exp:
        got = (result.get("issue_category") or "").strip().lower()
        want = (exp["issue_category"] or "").strip().lower()
        if got != want:
            errs.append(f"{prefix}: issue_category got {got!r} expected {want!r}")

    any_p = exp.get("draft_contains_any") or []
    if any_p and not _contains_any(draft, any_p):
        errs.append(f"{prefix}: draft missing any of {any_p!r}\n  draft: {draft[:280]!r}")

    banned = exp.get("draft_must_not_contain") or []
    if banned and not _contains_none(draft, banned):
        found = [b for b in banned if b in draft]
        errs.append(f"{prefix}: draft must not contain {found}\n  draft: {draft[:280]!r}")

    if verbose:
        print(f"  --- {prefix} ---")
        print(f"  handoff_ready={result.get('handoff_ready')} category={result.get('issue_category')}")
        print(f"  draft: {draft[:400]}...")

    return errs


def run_config_check(s: dict, client_id: str, verbose: bool) -> list[str]:
    errs: list[str] = []
    sid = s.get("id", "?")
    ui = get_ui_copy(client_id)
    blob = json.dumps(ui, ensure_ascii=False)
    any_p = s.get("expect_ui_contains_any") or []
    if any_p and not _contains_any(blob, any_p):
        errs.append(f"{sid}: ui_copy missing any of {any_p!r}")
    banned = s.get("expect_ui_must_not_contain") or []
    if banned and not _contains_none(blob, banned):
        errs.append(f"{sid}: ui_copy must not contain {[b for b in banned if b in blob]}")
    ho = get_handoff_phrases(client_id)
    h_blob = json.dumps(ho, ensure_ascii=False)
    if "陈奎" in h_blob:
        errs.append(f"{sid}: handoff_phrases still contain 陈奎")
    if verbose:
        print(f"  {sid}: ui keys={len(ui)} handoff keys={len(ho)}")
    return errs


def main() -> int:
    parser = argparse.ArgumentParser(description="Second broker client-pack drill runner")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if not SCENARIOS_PATH.exists():
        print(f"ERROR: {SCENARIOS_PATH} not found", file=sys.stderr)
        return 1

    data = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    client_id = (data.get("client_id") or "socal_precision").strip()
    all_errs: list[str] = []

    for s in data.get("scenarios", []):
        sid = s.get("id", "?")
        if s.get("type") == "config_check":
            all_errs.extend(run_config_check(s, client_id, args.verbose))
            continue

        steps = s.get("steps")
        if not steps:
            print(f"WARN: {sid} has no steps, skip", file=sys.stderr)
            continue

        for i, step in enumerate(steps, start=1):
            turns = step.get("conversation_turns") or []
            latest = (step.get("latest_text") or "").strip()
            exp = step.get("expect") or {}
            result = triage_conversation(latest, turns, client_id=client_id)
            all_errs.extend(_check_expect(result, exp, sid, i, args.verbose))

    if all_errs:
        print("SECOND BROKER DRILL FAILED", file=sys.stderr)
        for e in all_errs:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("SECOND BROKER DRILL OK (all scenarios passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
