#!/usr/bin/env python3
"""
Deterministic sanity check for a Unified Intake client pack (no server, no LLM).

Validates: required JSON files parse; handoff + reply templates load for client_id;
one Add-Car triage turn satisfies Stage 1 field contract (same bar as tests).

Usage:
  PYTHONPATH=. python3 scripts/validate_client_pack_minimal.py [client_id]
  # default client_id: socal_precision
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "client_id",
        nargs="?",
        default="socal_precision",
        help="configs/clients/<id>/ pack to validate (default: socal_precision)",
    )
    args = ap.parse_args()
    cid = (args.client_id or "").strip()
    if not cid:
        print("FAIL: empty client_id", file=sys.stderr)
        return 1

    pack = REPO / "configs" / "clients" / cid
    if not pack.is_dir():
        print(f"FAIL: missing client pack directory {pack}", file=sys.stderr)
        return 1

    for name in ("handoff_phrases.json", "ui_copy.json"):
        path = pack / name
        if not path.is_file():
            print(f"FAIL: missing {path.relative_to(REPO)}", file=sys.stderr)
            return 1
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"FAIL: invalid JSON {path.relative_to(REPO)}: {e}", file=sys.stderr)
            return 1

    ro = pack / "reply_overrides.json"
    if ro.is_file():
        try:
            json.loads(ro.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"FAIL: invalid JSON {ro.relative_to(REPO)}: {e}", file=sys.stderr)
            return 1

    from services.fiqa_api.inbox_triage.config_loader import (
        get_handoff_phrases,
        get_reply_templates,
    )

    hp = get_handoff_phrases(cid)
    add_car = hp.get("add_car") if isinstance(hp, dict) else None
    if not isinstance(add_car, dict) or not (add_car.get("zh") or "").strip():
        print(f"FAIL: handoff.add_car.zh missing for client {cid!r}", file=sys.stderr)
        return 1

    rt = get_reply_templates(cid)
    if not isinstance(rt, dict) or not rt:
        print(f"FAIL: merged reply templates empty for client {cid!r}", file=sys.stderr)
        return 1

    from services.fiqa_api.inbox_triage.add_car_field_contract import (
        quote_ready_matches_still_needed,
        validate_add_car_field_lists,
    )
    from services.fiqa_api.inbox_triage.triage import triage_conversation

    turns = [{"role": "customer", "text": "加车 2024 BMW X5 90210 下周提车 就我开"}]
    latest = "加车 2024 BMW X5 90210 下周提车 就我开"
    out = triage_conversation(latest, turns, client_id=cid, reply_truth_context=None)

    if out.get("issue_category") != "customer_question":
        print(
            f"FAIL: expected issue_category customer_question for add-car probe, got {out.get('issue_category')!r}",
            file=sys.stderr,
        )
        return 1

    try:
        validate_add_car_field_lists(
            out.get("collected_fields"),
            out.get("still_needed_fields"),
            strict=True,
        )
    except Exception as e:
        print(f"FAIL: Add-Car field contract: {e}", file=sys.stderr)
        return 1

    if not quote_ready_matches_still_needed(
        str(out.get("quote_ready_status") or ""),
        out.get("still_needed_fields"),
    ):
        print("FAIL: quote_ready_status inconsistent with still_needed_fields", file=sys.stderr)
        return 1

    draft = (out.get("client_reply_draft") or "").strip()
    if not draft:
        print("FAIL: empty client_reply_draft on add-car probe", file=sys.stderr)
        return 1

    print(f"PASS: client pack minimal validation ({cid})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
