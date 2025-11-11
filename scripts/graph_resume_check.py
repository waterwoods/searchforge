#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import Optional


def _load(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"missing required state file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"failed to parse {path}: {exc}")


def main() -> None:
    resume_path = Path(".runs/graph_resume.json")
    baseline_candidates = [
        Path(".runs/graph_full.json"),
        Path(".runs/graph_smoke.json"),
    ]

    baseline_payload = None
    baseline_path: Optional[Path] = None
    for candidate in baseline_candidates:
        if candidate.exists():
            baseline_payload = _load(candidate)
            baseline_path = candidate
            break

    if baseline_payload is None or baseline_path is None:
        expected = ", ".join(str(path) for path in baseline_candidates)
        sys.exit(f"missing required state file: expected one of [{expected}]")

    resumed = _load(resume_path)

    if not resumed.get("resume"):
        sys.exit("expected resume=true in steward response")

    def _normalized(payload: dict) -> dict:
        excluded = {"resume", "plan"}
        return {k: v for k, v in payload.items() if k not in excluded}

    if _normalized(baseline_payload) != _normalized(resumed):
        sys.exit(
            f"steward resume payload differs from previous run recorded in {baseline_path}"
        )


if __name__ == "__main__":
    main()

