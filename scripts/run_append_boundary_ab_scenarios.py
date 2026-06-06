#!/usr/bin/env python3
"""
Append / boundary A/B scenario battery — client_reply_draft + case_boundary isolation.

Runs docs/archive/sprints/prior_sprints_archive/p2_reply_flow_polish_sprints/APPEND_BOUNDARY_STRINGS_EXTERNALIZATION_SPRINT/append_boundary_ab_scenario_battery.json
via triage_for_append(..., client_id=...).

Usage:
  LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_append_boundary_ab_scenarios.py [--verbose]
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
    / "prior_sprints_archive"
    / "p2_reply_flow_polish_sprints"
    / "APPEND_BOUNDARY_STRINGS_EXTERNALIZATION_SPRINT"
    / "append_boundary_ab_scenario_battery.json"
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
    from services.fiqa_api.inbox_triage.triage import triage_for_append

    sid = s.get("id", "?")
    client_id = (s.get("client_id") or "").strip()
    existing = (s.get("existing_source_text") or "").strip()
    latest = (s.get("latest_text") or "").strip()
    if not existing or not latest:
        return False, "missing existing_source_text or latest_text"

    result = triage_for_append(existing, latest, client_id=client_id or None)
    draft = (result.get("client_reply_draft") or "").strip()
    cb = (result.get("case_boundary") or "").strip()

    exp_cb = (s.get("expected_case_boundary") or "").strip().lower()
    if exp_cb == "same_case":
        # Omitted or explicit `same_case` both mean append-allowed / no split.
        if cb and cb != "same_case":
            return False, f"expected same_case (omit or 'same_case'), got {cb!r}"
    elif exp_cb:
        if cb != exp_cb:
            return False, f"case_boundary: got {cb!r} expected {exp_cb!r}"

    if exp_cb == "borderline" and not result.get("human_confirmation_required"):
        return False, "borderline expected human_confirmation_required"

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
        print(f"\n--- {sid} client={client_id} boundary={cb or 'same_case'} ---")
        print(f"draft: {draft[:280]}{'…' if len(draft) > 280 else ''}")

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
            print(f"FAIL {s.get('id')}: {err}")

    n = len(scenarios)
    print(f"Append boundary A/B battery: {n - failed}/{n} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
