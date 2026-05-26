#!/usr/bin/env python3
"""
Unified production regression: guardrail (shell) → ASGI chaos → latency rollup + hard assertions.

  PYTHONPATH=. python3 scripts/run_full_regression.py

Writes:
  results/FULL_REGRESSION.json
  results/LATEST_SYSTEM_STATUS.md  (overwrite with latest rollup)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RESULTS_DIR = ROOT / "results"
CHAOS_OUT = RESULTS_DIR / "REGRESSION_CHAOS.json"
FULL_OUT = RESULTS_DIR / "FULL_REGRESSION.json"
STATUS_MD = RESULTS_DIR / "LATEST_SYSTEM_STATUS.md"

HTTP_P95_MAX_MS = 6000


def _run_guardrail() -> dict[str, Any]:
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", str(ROOT))
    r = subprocess.run(
        ["bash", str(ROOT / "scripts" / "guardrail_inbox_triage.sh")],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    return {
        "ok": r.returncode == 0,
        "exit_code": r.returncode,
        "stderr_tail": (r.stderr or "")[-4000:],
        "stdout_tail": (r.stdout or "")[-4000:],
    }


def _run_chaos() -> tuple[dict[str, Any], int]:
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", str(ROOT))
    env.setdefault("TRIAGE_RETURN_PERF_METRICS", "1")
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "llm_chaos_live_triage_check.py"),
            "--asgi",
            "--max-sessions",
            "35",
            "--out",
            str(CHAOS_OUT),
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    doc: dict[str, Any]
    try:
        doc = json.loads((CHAOS_OUT).read_text(encoding="utf-8"))
    except Exception as e:
        doc = {"ok": False, "error": str(e)}
    doc["_subprocess_exit"] = r.returncode
    return doc, r.returncode


def _rollup_latency(doc: dict[str, Any]) -> dict[str, Any]:
    """Percentiles over per-turn latency_ms without re-running chaos (same formula as scripts/profile_live_latency.py)."""

    def _pct(vals: list[float], p: float) -> float:
        if not vals:
            return 0.0
        s = sorted(vals)
        n = len(s)
        i = min(n - 1, max(0, int(round(p * (n - 1)))))
        return round(s[i], 2)

    http_ms: list[float] = []
    triage_ms: list[float] = []
    for sess in doc.get("sessions") or []:
        if not isinstance(sess, dict):
            continue
        for row in sess.get("turns") or []:
            if not isinstance(row, dict):
                continue
            http_ms.append(float(row.get("latency_ms") or 0))
            tm = row.get("triage_turn_metrics")
            if isinstance(tm, dict):
                triage_ms.append(float(tm.get("latency_ms") or 0))
            else:
                rp = row.get("route_perf") if isinstance(row.get("route_perf"), dict) else None
                if rp and float(rp.get("triage_ms") or 0) > 0:
                    triage_ms.append(float(rp.get("triage_ms") or 0))
    http_ms.sort()
    triage_ms.sort()
    return {
        "http_p50_ms": _pct(http_ms, 0.5),
        "http_p95_ms": _pct(http_ms, 0.95),
        "http_max_ms": _pct(http_ms, 1.0),
        "triage_p50_ms": _pct(triage_ms, 0.5),
        "triage_p95_ms": _pct(triage_ms, 0.95),
        "source": str(CHAOS_OUT),
    }


def _rollup_chaos_turn_stats(doc: dict[str, Any]) -> dict[str, Any]:
    """When chaos JSON has no ``summary`` block, derive stats from session pass/fail + per-turn PG flags."""
    pg_mismatch = 0
    inactive_leaks = 0
    for sess in doc.get("sessions") or []:
        if not isinstance(sess, dict):
            continue
        for row in sess.get("turns") or []:
            if not isinstance(row, dict):
                continue
            if row.get("pg_truth_match") is False:
                pg_mismatch += 1
            if row.get("inactive_vehicle_leak"):
                inactive_leaks += 1
    sess_total = int(doc.get("session_count") or 0) or len(
        [s for s in (doc.get("sessions") or []) if isinstance(s, dict)]
    )
    sess_passed = int(doc.get("passed") or 0)
    pass_rate_pct = (100.0 * sess_passed / sess_total) if sess_total else 0.0
    return {
        "pg_truth_mismatch_turns": pg_mismatch,
        "pass_rate_pct": pass_rate_pct,
        "inactive_vehicle_leak_turns": inactive_leaks,
        "sessions_scored": sess_total,
    }


def _assert_bundle(
    guard: dict[str, Any],
    chaos_doc: dict[str, Any],
    latency: dict[str, Any],
) -> dict[str, Any]:
    summ = chaos_doc.get("summary") if isinstance(chaos_doc.get("summary"), dict) else {}
    derived = _rollup_chaos_turn_stats(chaos_doc) if not summ else {}
    pg_mismatch = int(summ.get("pg_truth_mismatch_turns") or derived.get("pg_truth_mismatch_turns") or 0)
    pass_rate_pct = float(summ.get("pass_rate_pct") or derived.get("pass_rate_pct") or 0)
    inactive_leaks = int(summ.get("inactive_vehicle_leak_turns") or derived.get("inactive_vehicle_leak_turns") or 0)
    http_p95 = float(latency.get("http_p95_ms") or 0)
    clarify_rate = float(summ.get("clarify_rate") or 0)
    clarify_missed = False  # requires product-level oracle — see docs/PRODUCTION_METRICS.md

    failures: list[str] = []
    if not guard.get("ok"):
        failures.append("guardrail_shell_failed")
    if chaos_doc.get("ok") is False or int(chaos_doc.get("failed") or 0):
        failures.append("chaos_sessions_failed_nonzero")
    if pg_mismatch > 0:
        failures.append("pg_mismatch_turns_gt_0")
    if inactive_leaks > 0:
        failures.append("wrong_vehicle_or_inactive_leak")
    if pass_rate_pct < 100.0:
        failures.append("pass_rate_below_100")
    if http_p95 > HTTP_P95_MAX_MS:
        failures.append(f"http_p95_gt_{HTTP_P95_MAX_MS}ms")

    return {
        "passed": len(failures) == 0,
        "failures": failures,
        "threshold_http_p95_max_ms": HTTP_P95_MAX_MS,
        "clarify_missed_placeholder": clarify_missed,
        "explain": (
            "clarify_missed_rate requires a dedicated ambiguity oracle — documented in docs/PRODUCTION_METRICS.md; "
            "not asserted automatically here."
        ),
        "rollup": {
            "wrong_vehicle_related": pg_mismatch + inactive_leaks,
            "pg_mismatch_turns": pg_mismatch,
            "pass_rate_pct": pass_rate_pct,
            "http_p95_ms": http_p95,
            "clarify_rate": clarify_rate,
        },
    }


def _write_latest_status(latency: dict[str, Any], chaos_doc: dict[str, Any], assertions: dict[str, Any]) -> None:
    summ = chaos_doc.get("summary") if isinstance(chaos_doc.get("summary"), dict) else {}
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    pr = assertions.get("rollup", {}).get("pass_rate_pct", "")
    p95 = latency.get("http_p95_ms", "")
    mismatch = assertions.get("rollup", {}).get("pg_mismatch_turns", "")
    clarify = assertions.get("rollup", {}).get("clarify_rate", "")
    verdict = assertions.get("passed", "")
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = (
        "# Latest system status (auto-written by `scripts/run_full_regression.py`)\n\n"
        f"**generated**: {iso}\n\n"
        "| metric | value |\n"
        "|--------|-------|\n"
        f"| regression passed | {verdict} |\n"
        f"| pass rate % | {pr} |\n"
        f"| http p95 (ms) | {p95} |\n"
        f"| PG mismatch turns | {mismatch} |\n"
        f"| clarify rate | {clarify} |\n\n"
        f"Chaos pass/fail summary: `{summ.get('pass_fail')}`\n\n"
        f"Judgment tag: **`PRODUCTION_SAFE_WITH_GUARDRAILS`** (only when assertions passed).\n"
    )
    STATUS_MD.write_text(body, encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    print("FULL_REGRESSION [1/3] guardrail_inbox_triage.sh ...", flush=True)
    guard = _run_guardrail()
    print("FULL_REGRESSION [2/3] llm_chaos_live_triage_check --asgi ...", flush=True)
    chaos_doc, chaos_exit = _run_chaos()
    print("FULL_REGRESSION [3/3] rollup + assertions ...", flush=True)
    latency = _rollup_latency(chaos_doc if isinstance(chaos_doc, dict) else {})
    assertions = _assert_bundle(guard, chaos_doc if isinstance(chaos_doc, dict) else {}, latency)

    out: dict[str, Any] = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "judgment_tag": (
            "PRODUCTION_SAFE_WITH_GUARDRAILS" if assertions["passed"] else "REGRESSION_FAILURE"
        ),
        "guardrail": guard,
        "chaos": chaos_doc if isinstance(chaos_doc, dict) else {"error": "invalid_chaos"},
        "chaos_subprocess_exit": chaos_exit,
        "latency_rollup_from_chaos_turns": latency,
        "assertions": assertions,
    }
    FULL_OUT.parent.mkdir(parents=True, exist_ok=True)
    FULL_OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    try:
        _write_latest_status(latency, chaos_doc if isinstance(chaos_doc, dict) else {}, assertions)
    except Exception:
        pass

    print(json.dumps({"assertions": assertions, "latency_rollup_from_chaos_turns": latency}, indent=2))
    return 0 if assertions["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
