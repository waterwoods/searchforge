#!/usr/bin/env python3
"""
Cross-client A/B isolation — Unified Intake stitched + handoff copy

Runs docs/sprints/CROSS_CLIENT_COMPATIBILITY_ISOLATION_SPRINT/cross_client_ab_scenario_battery.json
against triage_conversation / triage_for_append with explicit client_id (no reliance on CLIENT_ID).

Usage:
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_cross_client_ab_scenarios.py [--verbose]
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_cross_client_ab_scenarios.py --client socal_precision
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
    / "sprints"
    / "CROSS_CLIENT_COMPATIBILITY_ISOLATION_SPRINT"
    / "cross_client_ab_scenario_battery.json"
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
    from services.fiqa_api.inbox_triage.triage import triage_conversation, triage_for_append

    sid = s.get("id", "?")
    client_id = (s.get("client_id") or "").strip()
    mode = (s.get("mode") or "conversation").strip().lower()
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

    if mode == "append":
        existing = (s.get("existing_source_text") or "").strip()
        if not existing or not latest:
            return False, "append mode requires existing_source_text and latest_text"
        result = triage_for_append(existing, latest, client_id=client_id or None)
    else:
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
        return False, f"draft missing any of {must_any}; draft={draft[:200]}"

    must_none = s.get("draft_must_not_contain_any") or []
    if isinstance(must_none, str):
        must_none = [must_none]
    if not _check_substrings(draft, list(must_none), any_of=False):
        return False, f"draft must not contain {must_none}; draft={draft[:200]}"

    if verbose:
        print(f"\n--- {sid} client={client_id} ---")
        print(f"draft: {draft[:240]}{'…' if len(draft) > 240 else ''}")

    return True, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument(
        "--client",
        metavar="CLIENT_ID",
        default="",
        help="If set, run only scenarios whose client_id matches (short second-client pack).",
    )
    args = ap.parse_args()
    client_filter = (args.client or "").strip()

    if not BATTERY.exists():
        print(f"ERROR: battery missing: {BATTERY}", file=sys.stderr)
        return 1

    data = json.loads(BATTERY.read_text(encoding="utf-8"))
    scenarios = data.get("scenarios", [])
    if not scenarios:
        print("ERROR: no scenarios in battery", file=sys.stderr)
        return 1

    if client_filter:
        scenarios = [s for s in scenarios if (s.get("client_id") or "").strip() == client_filter]
        if not scenarios:
            print(
                f"ERROR: no scenarios for client_id={client_filter!r} in battery",
                file=sys.stderr,
            )
            return 1

    failed = 0
    for s in scenarios:
        ok, err = run_one(s, args.verbose)
        if not ok:
            failed += 1
            print(f"FAIL {s.get('id')}: {err}")

    n = len(scenarios)
    suffix = f" (client={client_filter})" if client_filter else ""
    print(f"Cross-client A/B battery: {n - failed}/{n} passed{suffix}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
