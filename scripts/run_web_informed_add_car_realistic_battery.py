#!/usr/bin/env python3
"""
Run Web-Informed Add-Car Realistic Chinese Customer Battery
(docs/sprints/WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY/scenario_battery.json).

Uses triage_conversation → rule path when LLM off.

Usage:
  PYTHONPATH=. python3 scripts/run_web_informed_add_car_realistic_battery.py
  PYTHONPATH=. python3 scripts/run_web_informed_add_car_realistic_battery.py --json > /tmp/wirc.json
  PYTHONPATH=. python3 scripts/run_web_informed_add_car_realistic_battery.py --single WIRC-001 -v
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

BATTERY_PATH = ROOT / "docs" / "sprints" / "WEB_INFORMED_ADD_CAR_REALISTIC_BATTERY" / "scenario_battery.json"


def load_battery() -> dict:
    if not BATTERY_PATH.exists():
        print(f"ERROR: Battery not found: {BATTERY_PATH}", file=sys.stderr)
        sys.exit(1)
    return json.loads(BATTERY_PATH.read_text(encoding="utf-8"))


def run_scenario(sc: dict, verbose: bool) -> dict:
    turns_in = sc.get("turns") or []
    customer_turns = [t for t in turns_in if (t.get("role") or "").strip().lower() == "customer"]

    out: dict = {
        "id": sc.get("id"),
        "name": sc.get("name"),
        "category_tags": sc.get("category_tags"),
        "turn_results": [],
    }

    conversation: list[dict[str, str]] = []

    for i, ct in enumerate(customer_turns):
        text = (ct.get("text") or "").strip()
        if not text:
            continue
        result = triage_conversation(text, conversation)
        draft = result.get("client_reply_draft") or ""
        tr = {
            "turn": i + 1,
            "customer_text": text,
            "issue_category": result.get("issue_category"),
            "urgency": result.get("urgency"),
            "handoff_ready": result.get("handoff_ready"),
            "triage_path": result.get("triage_path"),
            "quote_ready_status": result.get("quote_ready_status"),
            "collection_stage": result.get("collection_stage"),
            "follow_up_type": result.get("follow_up_type"),
            "next_best_question": (result.get("next_best_question") or "")[:240],
            "broker_next_step": result.get("broker_next_step"),
            "client_reply_draft": draft,
            "collected_fields": result.get("collected_fields"),
            "still_needed_fields": result.get("still_needed_fields"),
            "manual_followup_needed": result.get("manual_followup_needed"),
            "conversation_summary": (result.get("conversation_summary") or "")[:400],
        }
        out["turn_results"].append(tr)

        conversation.append({"role": "customer", "text": text})
        conversation.append({"role": "system", "text": draft})

        if verbose:
            print(f"\n--- {sc.get('id')} turn {tr['turn']} ---")
            print(f"customer: {text[:500]}")
            print(
                f"category={tr['issue_category']} handoff={tr['handoff_ready']} "
                f"path={tr['triage_path']} qrs={tr['quote_ready_status']}"
            )
            print(f"draft: {draft[:500]}...")
            print(f"broker_next_step: {(tr.get('broker_next_step') or '')[:320]}")

    last = out["turn_results"][-1] if out["turn_results"] else {}
    out["final_handoff"] = last.get("handoff_ready")
    out["final_category"] = last.get("issue_category")
    out["final_quote_ready_status"] = last.get("quote_ready_status")
    out["final_collected_fields"] = last.get("collected_fields")
    out["final_still_needed_fields"] = last.get("still_needed_fields")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Run web-informed add-car realistic battery")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--single", metavar="ID", help="Run one scenario id")
    ap.add_argument("--json", action="store_true", help="Print JSON only")
    args = ap.parse_args()

    data = load_battery()
    scenarios = data.get("scenarios", [])
    if args.single:
        scenarios = [s for s in scenarios if s.get("id") == args.single]
        if not scenarios:
            print(f"No scenario {args.single}", file=sys.stderr)
            return 1

    results = [run_scenario(s, args.verbose) for s in scenarios]

    if args.json:
        print(
            json.dumps(
                {"llm_enabled": os.getenv("LLM_GENERATION_ENABLED"), "battery": data.get("sprint"), "results": results},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    for r in results:
        print(f"\n{'='*60}\n{r['id']} — {r.get('name', '')}\n{'='*60}")
        for tr in r["turn_results"]:
            ho = "HANDOFF" if tr["handoff_ready"] else "collect"
            print(
                f"\n  Turn {tr['turn']} [{ho}] cat={tr['issue_category']} "
                f"path={tr['triage_path']} qrs={tr['quote_ready_status']}"
            )
            ct = tr["customer_text"]
            print(f"  customer: {ct[:180]}{'…' if len(ct) > 180 else ''}")
            d = tr["client_reply_draft"]
            print(f"  draft: {d[:240]}{'…' if len(d) > 240 else ''}")
            bns = tr.get("broker_next_step") or ""
            print(f"  broker: {bns[:240]}{'…' if len(bns) > 240 else ''}")
        print(
            f"\n  → final handoff={r['final_handoff']} category={r['final_category']} "
            f"qrs={r['final_quote_ready_status']}"
        )

    print(f"\n---\nRan {len(results)} scenarios (LLM_GENERATION_ENABLED={os.getenv('LLM_GENERATION_ENABLED')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
