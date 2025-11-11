#!/usr/bin/env python3

import json
import sys
from pathlib import Path


def _load(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"missing required state file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"failed to parse {path}: {exc}")


def main() -> None:
    smoke_path = Path(".runs/graph_smoke.json")
    resume_path = Path(".runs/graph_resume.json")

    earlier = _load(smoke_path)
    resumed = _load(resume_path)

    if not resumed.get("resume"):
        sys.exit("expected resume=true in steward response")

    def _normalized(payload: dict) -> dict:
        return {k: v for k, v in payload.items() if k != "resume"}

    if _normalized(earlier) != _normalized(resumed):
        sys.exit("steward resume payload differs from previous run")


if __name__ == "__main__":
    main()

