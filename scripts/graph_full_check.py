#!/usr/bin/env python3

import json
import sys
from pathlib import Path


def main() -> None:
    resp_path = Path(".runs/graph_full.json")
    if not resp_path.exists():
        sys.exit("missing .runs/graph_full.json; run make graph-full first")

    try:
        payload = json.loads(resp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"failed to parse steward response: {exc}")

    if payload.get("decision") != "accept":
        sys.exit("baseline decision not accepted")

    metrics = payload.get("metrics") or {}
    for key in ("p95_ms", "err_rate", "recall@10", "cost_tokens"):
        if key not in metrics:
            sys.exit(f"missing metric {key}")

    baseline_path_value = payload.get("baseline_path")
    if not baseline_path_value:
        sys.exit("missing baseline_path in response")

    job_id = payload.get("job_id")
    baseline_path = Path("baselines") / f"{job_id}.json"
    if not baseline_path.exists() or baseline_path.stat().st_size <= 0:
        sys.exit(f"baseline file missing or empty: {baseline_path}")

    latest = Path("baselines/latest.json")
    if not latest.exists() or latest.stat().st_size <= 0:
        sys.exit("baselines/latest.json missing or empty")

    db_path = Path(".runs/graph.db")
    if not db_path.exists():
        sys.exit(".runs/graph.db missing")


if __name__ == "__main__":
    main()

