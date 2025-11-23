#!/usr/bin/env python3
"""
Minimal regression suite / quality gate for core Searchforge experiments.

Runs three experiments:
- AutoTuner SLA experiment        -> .runs/auto_tuner_on_off_sla.csv
- Go proxy concurrency/QPS        -> .runs/go_proxy_on_off.csv
- Fast trilines CI check (ci-fast)-> .runs/real_fast_trilines.csv

For each, compares metrics against a stored baseline CSV:
- .runs/baseline_auto_tuner_on_off_sla.csv
- .runs/baseline_go_proxy_on_off.csv
- .runs/baseline_real_fast_trilines.csv

If a baseline file does not exist, the current CSV is copied into place and
the run auto-passes with a clear message. This makes bootstrapping easy:
delete a baseline to re-baseline it.

The comparison logic is intentionally simple and human-readable so that it
can be extended later as we harden the gates.
"""

from __future__ import annotations

import csv
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


RUNS_DIR = Path(".runs")

AUTOTUNER_CURRENT = RUNS_DIR / "auto_tuner_on_off_sla.csv"
AUTOTUNER_BASELINE = RUNS_DIR / "baseline_auto_tuner_on_off_sla.csv"

GO_PROXY_CURRENT = RUNS_DIR / "go_proxy_on_off.csv"
GO_PROXY_BASELINE = RUNS_DIR / "baseline_go_proxy_on_off.csv"

CI_FAST_CURRENT = RUNS_DIR / "real_fast_trilines.csv"
CI_FAST_BASELINE = RUNS_DIR / "baseline_real_fast_trilines.csv"


@dataclass
class CsvTable:
    rows: List[Dict[str, str]]

    @classmethod
    def from_path(cls, path: Path) -> "CsvTable":
        with path.open("r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        return cls(rows=rows)


def _ensure_runs_dir() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def _bootstrap_baseline(baseline: Path, current: Path, label: str) -> bool:
    """
    Ensure a baseline exists.

    Returns True if a comparison should be performed, False if we just
    bootstrapped the baseline and should auto-pass this check.
    """
    if baseline.exists():
        return True

    if not current.exists():
        print(f"[REGRESSION] ❌ Expected current CSV for {label} at {current}, but it does not exist.")
        return True

    shutil.copy2(current, baseline)
    print(
        f"[REGRESSION][{label}] No baseline; created baseline from current CSV "
        f"({current.name} -> {baseline.name}) (auto-pass this run)."
    )
    return False


def _pct_change(current: float, baseline: float) -> float:
    if baseline == 0:
        # Avoid division by zero; treat any non-zero as 100% change.
        if current == 0:
            return 0.0
        return 1.0
    return (current - baseline) / baseline


def _float(row: Dict[str, str], key: str) -> float:
    try:
        return float(row[key])
    except (KeyError, ValueError):
        return float("nan")


def check_autotuner_sla(baseline_csv: Path, current_csv: Path) -> List[str]:
    """
    For mode="autotuner":
      - p95_ms must NOT increase by more than +20% for same budget_ms
        (simple relative latency guard).
      - timeout_rate must remain <= baseline timeout_rate + 0.02
        (allow small noise, block obvious SLA blow-ups).

    For mode="baseline":
      - Only gate on timeout_rate: must not jump by more than +10% absolute
        (heavy baseline is allowed to fluctuate more in latency but not in timeouts).

    Additionally, if an error_rate column is present:
      - error_rate_current must not exceed error_rate_baseline + 0.05 for any mode
        (simple conservative 5% absolute error-rate guard).
    """
    errors: List[str] = []

    baseline = CsvTable.from_path(baseline_csv)
    current = CsvTable.from_path(current_csv)

    def index_by_mode_budget(rows: Iterable[Dict[str, str]]) -> Dict[Tuple[str, str], Dict[str, str]]:
        out: Dict[Tuple[str, str], Dict[str, str]] = {}
        for r in rows:
            mode = r.get("mode")
            budget = r.get("budget_ms") or r.get("budget")
            if mode is None or budget is None:
                continue
            out[(mode, str(budget))] = r
        return out

    base_idx = index_by_mode_budget(baseline.rows)
    cur_idx = index_by_mode_budget(current.rows)

    # Detect keys present in current but not in baseline; we log them as info
    # but do not fail the regression. This keeps the suite forward-compatible
    # with new rows while still requiring that all baseline keys exist.
    extra_keys = set(cur_idx.keys()) - set(base_idx.keys())
    for mode, budget in sorted(extra_keys):
        print(
            f"[auto-tuner-sla] Info: new row in current CSV not in baseline: "
            f"mode={mode}, budget_ms={budget} (ignored for regression)."
        )

    has_error_rate = any("error_rate" in r for r in baseline.rows) and any(
        "error_rate" in r for r in current.rows
    )

    for key, base_row in base_idx.items():
        mode, budget = key
        cur_row = cur_idx.get(key)
        if cur_row is None:
            errors.append(
                f"[auto-tuner-sla] Missing row for mode={mode}, budget_ms={budget} in current CSV (present in baseline)."
            )
            continue

        p95_base = _float(base_row, "p95_ms")
        p95_cur = _float(cur_row, "p95_ms")
        timeout_base = _float(base_row, "timeout_rate")
        timeout_cur = _float(cur_row, "timeout_rate")

        if mode == "autotuner":
            # p95_ms gate (+20% relative)
            p95_delta = _pct_change(p95_cur, p95_base)
            if p95_delta > 0.20:
                pct = p95_delta * 100.0
                errors.append(
                    f"[auto-tuner-sla] autotuner p95_ms at {budget}ms budget regressed +{pct:.1f}% "
                    f"(baseline={p95_base:.3f}, current={p95_cur:.3f})."
                )

            # timeout_rate gate (+0.02 absolute)
            if timeout_cur > timeout_base + 0.02:
                diff = timeout_cur - timeout_base
                errors.append(
                    f"[auto-tuner-sla] autotuner timeout_rate at {budget}ms budget increased by "
                    f"+{diff:.3f} abs (baseline={timeout_base:.3f}, current={timeout_cur:.3f}, max_delta=0.020)."
                )
        elif mode == "baseline":
            # Only gate on timeout_rate (+0.10 absolute)
            if timeout_cur > timeout_base + 0.10:
                diff = timeout_cur - timeout_base
                errors.append(
                    f"[auto-tuner-sla] baseline timeout_rate at {budget}ms budget increased by "
                    f"+{diff:.3f} abs (baseline={timeout_base:.3f}, current={timeout_cur:.3f}, max_delta=0.100)."
                )

        if has_error_rate:
            err_base = _float(base_row, "error_rate")
            err_cur = _float(cur_row, "error_rate")
            if err_cur > err_base + 0.05:
                diff = err_cur - err_base
                errors.append(
                    f"[auto-tuner-sla] error_rate at mode={mode}, budget_ms={budget} increased by "
                    f"+{diff:.3f} abs (baseline={err_base:.3f}, current={err_cur:.3f}, max_delta=0.050)."
                )

    return errors


def check_go_proxy_on_off(baseline_csv: Path, current_csv: Path) -> List[str]:
    """
    For mode="proxy":
      - qps must NOT drop more than −20% vs baseline for each concurrency
        (proxy should not lose too much throughput).
      - p95_ms must NOT increase more than +30% vs baseline
        (latency guard for the proxy path).

    For mode="baseline":
      - Gate only on qps: must not drop more than −20% (latency is mostly
        observed, not gated).

    Additionally for both modes:
      - error_rate_current must not exceed error_rate_baseline + 0.02
      - timeout_rate_current must not exceed timeout_rate_baseline + 0.02
        (small tolerance for noise, but block new errors/timeouts).
    """
    errors: List[str] = []

    baseline = CsvTable.from_path(baseline_csv)
    current = CsvTable.from_path(current_csv)

    def index_by_mode_conc(rows: Iterable[Dict[str, str]]) -> Dict[Tuple[str, str], Dict[str, str]]:
        out: Dict[Tuple[str, str], Dict[str, str]] = {}
        for r in rows:
            mode = r.get("mode")
            conc = r.get("concurrency")
            if mode is None or conc is None:
                continue
            out[(mode, str(conc))] = r
        return out

    base_idx = index_by_mode_conc(baseline.rows)
    cur_idx = index_by_mode_conc(current.rows)

    extra_keys = set(cur_idx.keys()) - set(base_idx.keys())
    for mode, conc in sorted(extra_keys):
        print(
            f"[go-proxy-on-off] Info: new row in current CSV not in baseline: "
            f"mode={mode}, concurrency={conc} (ignored for regression)."
        )

    for key, base_row in base_idx.items():
        mode, conc = key
        cur_row = cur_idx.get(key)
        if cur_row is None:
            errors.append(
                f"[go-proxy-on-off] Missing row for mode={mode}, concurrency={conc} in current CSV (present in baseline)."
            )
            continue

        qps_base = _float(base_row, "qps")
        qps_cur = _float(cur_row, "qps")
        p95_base = _float(base_row, "p95_ms")
        p95_cur = _float(cur_row, "p95_ms")
        err_base = _float(base_row, "error_rate")
        err_cur = _float(cur_row, "error_rate")
        timeout_base = _float(base_row, "timeout_rate")
        timeout_cur = _float(cur_row, "timeout_rate")

        # qps gate: do not allow drop more than 20%
        qps_delta = _pct_change(qps_cur, qps_base)
        if qps_delta < -0.20:
            pct = -qps_delta * 100.0
            errors.append(
                f"[go-proxy-on-off] {mode} qps at concurrency={conc} dropped {pct:.1f}% "
                f"(baseline={qps_base:.3f}, current={qps_cur:.3f}, max_drop=20%)."
            )

        if mode == "proxy":
            # p95_ms gate for proxy: +30% max
            p95_delta = _pct_change(p95_cur, p95_base)
            if p95_delta > 0.30:
                pct = p95_delta * 100.0
                errors.append(
                    f"[go-proxy-on-off] proxy p95_ms at concurrency={conc} regressed +{pct:.1f}% "
                    f"(baseline={p95_base:.3f}, current={p95_cur:.3f}, max_increase=30%)."
                )

        # error_rate and timeout_rate guards (+0.02 absolute)
        if err_cur > err_base + 0.02:
            diff = err_cur - err_base
            errors.append(
                f"[go-proxy-on-off] error_rate at mode={mode}, concurrency={conc} increased by "
                f"+{diff:.3f} abs (baseline={err_base:.3f}, current={err_cur:.3f}, max_delta=0.020)."
            )

        if timeout_cur > timeout_base + 0.02:
            diff = timeout_cur - timeout_base
            errors.append(
                f"[go-proxy-on-off] timeout_rate at mode={mode}, concurrency={conc} increased by "
                f"+{diff:.3f} abs (baseline={timeout_base:.3f}, current={timeout_cur:.3f}, max_delta=0.020)."
            )

    return errors


def check_ci_fast(baseline_csv: Path, current_csv: Path) -> List[str]:
    """
    For policy=\"Balanced\" rows:
      - p95_ms must not regress more than +20% (simple latency guard).
      - recall_or_success_rate must not drop more than −0.05 absolute
        (protect basic success/recall quality).

    Additionally, if error_rate/timeout_rate columns are present:
      - error_rate_current must not exceed error_rate_baseline + 0.05
      - timeout_rate_current must not exceed timeout_rate_baseline + 0.05
        (looser than proxy, since this is a summarized fast CI check).
    """
    errors: List[str] = []

    baseline = CsvTable.from_path(baseline_csv)
    current = CsvTable.from_path(current_csv)

    def index_by_policy_budget(rows: Iterable[Dict[str, str]]) -> Dict[Tuple[str, str], Dict[str, str]]:
        out: Dict[Tuple[str, str], Dict[str, str]] = {}
        for r in rows:
            policy = r.get("policy")
            budget = r.get("budget_ms") or r.get("budget")
            if policy is None or budget is None:
                continue
            out[(policy, str(budget))] = r
        return out

    base_idx = index_by_policy_budget(baseline.rows)
    cur_idx = index_by_policy_budget(current.rows)

    extra_keys = set(cur_idx.keys()) - set(base_idx.keys())
    for policy, budget in sorted(extra_keys):
        print(
            f"[ci-fast] Info: new row in current CSV not in baseline: "
            f"policy={policy}, budget_ms={budget} (ignored for regression)."
        )

    has_error_rate = any("error_rate" in r for r in baseline.rows) and any(
        "error_rate" in r for r in current.rows
    )
    has_timeout_rate = any("timeout_rate" in r for r in baseline.rows) and any(
        "timeout_rate" in r for r in current.rows
    )

    for key, base_row in base_idx.items():
        policy, budget = key
        if policy != "Balanced":
            continue

        cur_row = cur_idx.get(key)
        if cur_row is None:
            errors.append(
                f"[ci-fast] Missing row for policy={policy}, budget_ms={budget} in current CSV (present in baseline)."
            )
            continue

        p95_base = _float(base_row, "p95_ms")
        p95_cur = _float(cur_row, "p95_ms")
        recall_base = _float(base_row, "recall_or_success_rate")
        recall_cur = _float(cur_row, "recall_or_success_rate")

        p95_delta = _pct_change(p95_cur, p95_base)
        if p95_delta > 0.20:
            pct = p95_delta * 100.0
            errors.append(
                f"[ci-fast] Balanced p95_ms at {budget}ms budget regressed +{pct:.1f}% "
                f"(baseline={p95_base:.3f}, current={p95_cur:.3f}, max_increase=20%)."
            )

        # recall/success gate: absolute drop <= 0.05
        if recall_cur < recall_base - 0.05:
            diff = recall_base - recall_cur
            errors.append(
                f"[ci-fast] Balanced recall_or_success_rate at {budget}ms budget dropped "
                f"-{diff:.3f} abs (baseline={recall_base:.3f}, current={recall_cur:.3f}, max_drop=0.050)."
            )

        if has_error_rate:
            err_base = _float(base_row, "error_rate")
            err_cur = _float(cur_row, "error_rate")
            if err_cur > err_base + 0.05:
                diff = err_cur - err_base
                errors.append(
                    f"[ci-fast] Balanced error_rate at {budget}ms budget increased by "
                    f"+{diff:.3f} abs (baseline={err_base:.3f}, current={err_cur:.3f}, max_delta=0.050)."
                )

        if has_timeout_rate:
            timeout_base = _float(base_row, "timeout_rate")
            timeout_cur = _float(cur_row, "timeout_rate")
            if timeout_cur > timeout_base + 0.05:
                diff = timeout_cur - timeout_base
                errors.append(
                    f"[ci-fast] Balanced timeout_rate at {budget}ms budget increased by "
                    f"+{diff:.3f} abs (baseline={timeout_base:.3f}, current={timeout_cur:.3f}, max_delta=0.050)."
                )

    return errors


def main() -> int:
    _ensure_runs_dir()

    all_errors: List[str] = []

    # 1) AutoTuner SLA
    print("[REGRESSION] Running auto-tuner-sla-all...")
    subprocess.run(["make", "auto-tuner-sla-all"], check=True)

    if _bootstrap_baseline(AUTOTUNER_BASELINE, AUTOTUNER_CURRENT, "auto-tuner-sla"):
        auto_errors = check_autotuner_sla(AUTOTUNER_BASELINE, AUTOTUNER_CURRENT)
        if auto_errors:
            print(f"[REGRESSION][auto-tuner-sla] FAIL ({len(auto_errors)} issues):")
            for err in auto_errors:
                print(f"- {err}")
            all_errors.extend(auto_errors)
        else:
            print("[REGRESSION][auto-tuner-sla] PASS (no regressions detected).")
    else:
        print("[REGRESSION][auto-tuner-sla] PASS (baseline bootstrapped from current run).")

    # 2) Go proxy on/off
    print("[REGRESSION] Running go-proxy-on-off...")
    subprocess.run(["make", "go-proxy-on-off"], check=True)

    if _bootstrap_baseline(GO_PROXY_BASELINE, GO_PROXY_CURRENT, "go-proxy-on-off"):
        proxy_errors = check_go_proxy_on_off(GO_PROXY_BASELINE, GO_PROXY_CURRENT)
        if proxy_errors:
            print(f"[REGRESSION][go-proxy-on-off] FAIL ({len(proxy_errors)} issues):")
            for err in proxy_errors:
                print(f"- {err}")
            all_errors.extend(proxy_errors)
        else:
            print("[REGRESSION][go-proxy-on-off] PASS (no regressions detected).")
    else:
        print("[REGRESSION][go-proxy-on-off] PASS (baseline bootstrapped from current run).")

    # 3) ci-fast
    print("[REGRESSION] Running ci-fast...")
    subprocess.run(["make", "ci-fast"], check=True)

    if _bootstrap_baseline(CI_FAST_BASELINE, CI_FAST_CURRENT, "ci-fast"):
        ci_errors = check_ci_fast(CI_FAST_BASELINE, CI_FAST_CURRENT)
        if ci_errors:
            print(f"[REGRESSION][ci-fast] FAIL ({len(ci_errors)} issues):")
            for err in ci_errors:
                print(f"- {err}")
            all_errors.extend(ci_errors)
        else:
            print("[REGRESSION][ci-fast] PASS (no regressions detected).")
    else:
        print("[REGRESSION][ci-fast] PASS (baseline bootstrapped from current run).")

    # Final summary
    if not all_errors:
        print("[REGRESSION] ✅ All checks passed (no significant regressions).")
        return 0

    print("[REGRESSION] ❌ Detected regressions:")
    for err in all_errors:
        print(f"- {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())


