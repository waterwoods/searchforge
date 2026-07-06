#!/usr/bin/env python3
"""
Manual WeCom queue drain / status — operator smoke path (Q0.5).

Drains existing Postgres inbox and reply-outbox rows in order. Does not enable
WECOM_INBOX_QUEUE or WECOM_REPLY_OUTBOX — only processes rows already queued.

Usage:
  PYTHONPATH=. python3 scripts/wecom_drain_queues.py --status
  PYTHONPATH=. python3 scripts/wecom_drain_queues.py --limit 10
  PYTHONPATH=. python3 scripts/wecom_drain_queues.py --limit 5 --json

Requires SERVICE_RECORD_DATABASE_URL (or DATABASE_URL).

Smoke test runbook: docs/wecom_q0_smoke_test.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.wecom.queue_admin import (  # noqa: E402
    drain_wecom_queues,
    fetch_wecom_queue_status,
    format_wecom_queue_report,
    repair_stale_wecom_queue_rows,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Manually drain or inspect WeCom inbox/outbox Postgres queues",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Status only — count rows by status; do not drain",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Max rows to claim per queue per run (default: 10)",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Skip rows at or above this attempt_count (default: 3)",
    )
    parser.add_argument(
        "--stale-timeout-seconds",
        type=int,
        default=600,
        help="Reclaim processing/sending rows older than this (default: 600)",
    )
    parser.add_argument(
        "--repair-stale",
        action="store_true",
        help="Reset stale processing/sending rows to pending (see --dry-run)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --repair-stale, count stale rows without updating them",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text report",
    )
    args = parser.parse_args()

    try:
        if args.repair_stale:
            result = repair_stale_wecom_queue_rows(
                stale_timeout_seconds=args.stale_timeout_seconds,
                dry_run=args.dry_run,
            )
        elif args.status:
            result = fetch_wecom_queue_status(
                max_attempts=args.max_attempts,
                stale_timeout_seconds=args.stale_timeout_seconds,
            )
        else:
            result = drain_wecom_queues(
                limit=args.limit,
                max_attempts=args.max_attempts,
                stale_timeout_seconds=args.stale_timeout_seconds,
            )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_wecom_queue_report(result))

    if result.get("mode") == "drain":
        inbox = result.get("inbox") or {}
        outbox = result.get("outbox") or {}
        if (inbox.get("failed") or 0) > 0 or (outbox.get("failed") or 0) > 0:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
