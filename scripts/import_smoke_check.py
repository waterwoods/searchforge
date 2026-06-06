#!/usr/bin/env python3
"""Fail fast on missing imports / wiring for Unified Intake hot modules."""

from __future__ import annotations

MODULES = [
    "services.fiqa_api.app_main",
    "services.fiqa_api.routes.inbox_triage",
    "services.fiqa_api.inbox_triage.triage",
    "services.fiqa_api.inbox_triage.entity_repository",
    "services.fiqa_api.inbox_triage.case_truth_repository",
    "services.fiqa_api.inbox_triage.session_store",
]


def main() -> None:
    for m in MODULES:
        __import__(m)
    print("IMPORT_SMOKE_OK")


if __name__ == "__main__":
    main()
