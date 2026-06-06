#!/usr/bin/env python3
"""
Small-batch phrase-map A/B scenarios.

Runs docs/archive/sprints/SMALL_BATCH_PHRASE_MAP_EXTERNALIZATION_SPRINT/small_batch_ab_scenario_battery.json
with explicit client_id (no reliance on CLIENT_ID env).

Usage:
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_small_batch_phrase_map_ab_scenarios.py [--verbose]
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

BATTERY = (
    REPO
    / "docs"
    / "archive"
    / "sprints"
    / "SMALL_BATCH_PHRASE_MAP_EXTERNALIZATION_SPRINT"
    / "small_batch_ab_scenario_battery.json"
)


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _check_substrings(text: str, subs: list[str], any_of: bool) -> bool:
    if not subs:
        return True
    t = text or ""
    if any_of:
        return any(s in t for s in subs)
    return all(s not in t for s in subs)


def run_one(s: dict, verbose: bool) -> tuple[bool, str | None]:
    from services.fiqa_api.inbox_triage.triage import triage_conversation

    sid = s.get("id", "?")
    client_id = (s.get("client_id") or "").strip()
    latest = (s.get("latest_text") or s.get("latest") or "").strip()
    turns_in = s.get("conversation_turns") or s.get("turns") or []

    turns: list[dict[str, str]] = []
    for t in turns_in:
        if isinstance(t, dict):
            turns.append(
                {
                    "role": (t.get("role") or "customer").strip(),
                    "text": (t.get("text") or "").strip(),
                }
            )

    if not latest:
        return False, "missing latest_text"

    result = triage_conversation(latest, turns, client_id=client_id or None)
    draft = (result.get("client_reply_draft") or "").strip()

    if s.get("expected_handoff_ready") is not None:
        if bool(result.get("handoff_ready")) != bool(s["expected_handoff_ready"]):
            return (
                False,
                f"handoff_ready: got {result.get('handoff_ready')} expected {s['expected_handoff_ready']}",
            )

    lang = (s.get("expected_draft_language") or "").strip().lower()
    if lang == "zh" and not _contains_chinese(draft):
        return False, "expected Chinese draft"
    if lang == "en" and _contains_chinese(draft):
        return False, "expected English draft"

    must_any = s.get("draft_must_contain_any") or []
    if isinstance(must_any, str):
        must_any = [must_any]
    if not _check_substrings(draft, list(must_any), any_of=True):
        return False, f"draft missing any of {must_any}; draft={draft[:220]}"

    must_none = s.get("draft_must_not_contain_any") or []
    if isinstance(must_none, str):
        must_none = [must_none]
    if not _check_substrings(draft, list(must_none), any_of=False):
        return False, f"draft must not contain {must_none}; draft={draft[:220]}"

    if verbose:
        print(f"\n--- {sid} client={client_id} ---")
        print(f"draft: {draft[:260]}{'…' if len(draft) > 260 else ''}")

    return True, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    if not BATTERY.exists():
        print(f"ERROR: battery missing: {BATTERY}", file=sys.stderr)
        return 1

    data = json.loads(BATTERY.read_text(encoding="utf-8"))
    scenarios = data.get("scenarios", [])
    if not scenarios:
        print("ERROR: no scenarios in battery", file=sys.stderr)
        return 1

    failed = 0
    for s in scenarios:
        ok, err = run_one(s, args.verbose)
        if not ok:
            failed += 1
            print(f"FAIL {s.get('id', '?')}: {err}", file=sys.stderr)

    if failed:
        print(f"Small-batch phrase-map A/B: {failed}/{len(scenarios)} failed", file=sys.stderr)
        return 1

    print(f"Small-batch phrase-map A/B: {len(scenarios)} scenarios OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
