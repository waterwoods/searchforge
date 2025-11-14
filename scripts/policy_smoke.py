#!/usr/bin/env python3
"""Run smoke tests across all autotuner policies and summarize results."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

POLICIES = ["LatencyFirst", "RecallFirst", "Balanced"]
DEFAULT_BATCHES = os.getenv("POLICY_SMOKE_N", "50")
PYTHON = os.getenv("PYTHON", sys.executable or "python3")
RUNS_DIR = Path(".runs")


def _slugify(name: str) -> str:
    return "".join(ch.lower() for ch in name if ch.isalnum() or ch in ("-", "_"))


def _load_report(policy: str) -> dict:
    slug = _slugify(policy)
    report_path = RUNS_DIR / f"tuner_small_{slug}.json"
    if not report_path.exists():
        raise FileNotFoundError(f"missing report for {policy}: {report_path}")
    with report_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    data["report_path"] = str(report_path)
    return data


def _run_policy(policy: str) -> dict:
    env = os.environ.copy()
    env.setdefault("N", DEFAULT_BATCHES)
    cmd = [PYTHON, "scripts/tuner_real_small.py", "--policy", policy]
    subprocess.run(cmd, check=True, env=env)
    report = _load_report(policy)
    result = {
        "policy": policy,
        "success_rate": float(report.get("success_rate", 0.0)),
        "bounds_ok": bool(report.get("bounds_ok", False)),
        "stable_detune": bool(report.get("stable_detune", False)),
        "p95_ms": report.get("p95_ms"),
        "ok": bool(report.get("bounds_ok", False))
        and bool(report.get("stable_detune", False))
        and float(report.get("success_rate", 0.0)) >= 0.95,
        "report": report["report_path"],
    }
    return result


def main() -> int:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for policy in POLICIES:
        print(f">>> policy-smoke {policy}")
        try:
            results.append(_run_policy(policy))
        except subprocess.CalledProcessError as exc:
            print(f"policy {policy} failed with exit code {exc.returncode}", file=sys.stderr)
            return exc.returncode or 1
        except Exception as exc:  # pragma: no cover - defensive
            print(f"policy {policy} failed: {exc}", file=sys.stderr)
            return 1

    summary = {
        "timestamp": time.time(),
        "ok": all(item["ok"] for item in results),
        "policies": results,
    }
    summary_path = RUNS_DIR / "policy_summary.json"
    tmp_path = summary_path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")
    tmp_path.replace(summary_path)
    print(json.dumps(summary, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

