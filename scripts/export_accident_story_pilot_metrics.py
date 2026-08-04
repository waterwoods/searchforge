#!/usr/bin/env python3
"""Read-only Accident Story pilot metrics exporter (non-sensitive).

Durable Postgres is the pilot SSOT when SERVICE_RECORD_DATABASE_URL is set.
In-memory counters remain convenience-only.

Usage:
  PYTHONPATH=. python3 scripts/export_accident_story_pilot_metrics.py
  PYTHONPATH=. python3 scripts/export_accident_story_pilot_metrics.py --json
  PYTHONPATH=. python3 scripts/export_accident_story_pilot_metrics.py \\
      --since 2026-08-04T00:00:00Z --until 2026-08-05T00:00:00Z --json
  PYTHONPATH=. python3 scripts/export_accident_story_pilot_metrics.py --source memory
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--since", default=None, help="ISO timestamp lower bound (inclusive)")
    parser.add_argument("--until", default=None, help="ISO timestamp upper bound (inclusive)")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument(
        "--source",
        choices=("auto", "postgres", "memory"),
        default="auto",
        help="auto=postgres then memory fallback; postgres=durable only; memory=in-process only",
    )
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))

    from services.fiqa_api.inbox_triage.accident_story_assistant.events import (
        list_ai_story_events_for_tests,
    )
    from services.fiqa_api.inbox_triage.accident_story_assistant.metrics import (
        summarize_durable_pilot_metrics,
        summarize_pilot_metrics,
    )

    if args.source == "memory":
        summary = summarize_pilot_metrics(events=list_ai_story_events_for_tests())
        summary["source"] = "memory"
        summary["window"] = {"since": args.since, "until": args.until, "limit": args.limit}
    elif args.source == "postgres":
        summary = summarize_durable_pilot_metrics(
            since=args.since,
            until=args.until,
            limit=args.limit,
            include_memory_fallback=False,
        )
    else:
        summary = summarize_durable_pilot_metrics(
            since=args.since,
            until=args.until,
            limit=args.limit,
            include_memory_fallback=True,
        )

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"Accident Story Pilot Metrics (source={summary.get('source')})")
        if summary.get("window"):
            print(f"  window: {summary.get('window')}")
        for k in (
            "proposals_created",
            "accepted",
            "edited",
            "rejected",
            "fallbacks",
            "provider_timeouts",
            "invalid_output_failures",
            "avg_latency_ms",
            "p95_latency_ms",
            "avg_question_count",
            "unknown_injury_safety_violations",
            "completion_after_fallback",
        ):
            print(f"  {k}: {summary.get(k)}")
        print(f"  fallback_reason_categories: {summary.get('fallback_reason_categories')}")
        print(f"  pii_policy: {summary.get('pii_policy')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
