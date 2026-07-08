#!/usr/bin/env python3
"""Run predefined WeCom workflow routing scenarios locally (no deploy, no external services)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Repo root on PYTHONPATH when invoked as: PYTHONPATH=. python3 scripts/run_workflow_scenarios.py
from services.fiqa_api.wecom.workflow_scenario_simulator import (
    format_scenario_report,
    run_all_predefined_scenarios,
)


def _bootstrap_json_store() -> None:
    tmp = tempfile.mkdtemp(prefix="workflow_scenarios_")
    path = Path(tmp) / "cases.json"
    path.write_text(json.dumps({"cases": []}), encoding="utf-8")
    os.environ["ENV"] = "development"
    os.environ["UNIFIED_INTAKE_CASES_PATH"] = str(path)
    os.environ["UNIFIED_INTAKE_JSON_CASE_WRITES"] = "1"
    os.environ.pop("UNIFIED_INTAKE_DB_PRIMARY_WRITES", None)
    os.environ.pop("SERVICE_RECORD_DATABASE_URL", None)


def main() -> int:
    _bootstrap_json_store()
    results = run_all_predefined_scenarios()
    failed = [r for r in results if not r.passed]
    if failed:
        print(f"\n{len(failed)} scenario(s) FAILED", file=sys.stderr)
        return 1
    print(f"\nAll {len(results)} scenarios PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
