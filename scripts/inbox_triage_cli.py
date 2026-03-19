#!/usr/bin/env python3
"""
Broker Inbox Triage — CLI for single message

Usage:
  python scripts/inbox_triage_cli.py "paste message here"
  echo "message" | python scripts/inbox_triage_cli.py

Requires: PYTHONPATH=. when run from repo root
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from services.fiqa_api.inbox_triage.triage import triage_message


def main() -> None:
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("Usage: python scripts/inbox_triage_cli.py \"message\"")
        sys.exit(1)

    result = triage_message(text)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
