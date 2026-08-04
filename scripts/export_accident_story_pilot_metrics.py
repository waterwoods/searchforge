#!/usr/bin/env python3
"""Read-only Accident Story pilot metrics exporter (non-sensitive).

Usage:
  PYTHONPATH=. python3 scripts/export_accident_story_pilot_metrics.py
  PYTHONPATH=. python3 scripts/export_accident_story_pilot_metrics.py --json
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
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    from services.fiqa_api.inbox_triage.accident_story_assistant.metrics import (
        summarize_pilot_metrics,
    )

    summary = summarize_pilot_metrics()
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print("Accident Story Pilot Metrics (in-process window)")
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
