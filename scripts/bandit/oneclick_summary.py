#!/usr/bin/env python3
"""Generate consolidated one-click bandit summary and verification."""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping


REPORTS_DIR = Path("reports")
BANDIT_STATE_PATH = Path(os.environ.get("BANDIT_STATE", Path.home() / "data" / "searchforge" / "bandit" / "bandit_state.json"))
SLA_P95 = float(os.environ.get("SLA_P95", "1500"))
SLA_ERR = float(os.environ.get("SLA_ERR", "0.01"))
AB_TOLERANCE = float(os.environ.get("AB_TOLERANCE", "0.2"))


def _latest(glob: str) -> Path:
    candidates = sorted(REPORTS_DIR.glob(glob), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(f"No files found for pattern {glob}")
    return candidates[-1]


def _parse_markdown_table(path: Path) -> List[List[str]]:
    rows: List[List[str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or not line.startswith("|"):
            continue
        if line.startswith("| ---"):
            continue
        parts = [part.strip() for part in line.split("|")[1:-1]]
        rows.append(parts)
    return rows


def _load_summary_json(path: Path) -> Mapping[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_bandit_state() -> Mapping[str, object]:
    with BANDIT_STATE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _average_router_stats(rows: Iterable[Mapping[str, object]]) -> Dict[str, Dict[str, float]]:
    totals: Dict[str, Dict[str, float]] = defaultdict(lambda: {"p95": 0.0, "recall": 0.0, "err": 0.0, "samples": 0, "rounds": 0})
    for row in rows:
        arm = str(row["arm"])
        totals[arm]["p95"] += float(row["p95_ms"])
        totals[arm]["recall"] += float(row["recall"])
        totals[arm]["err"] += float(row["err"])
        totals[arm]["samples"] += int(row["samples"])
        totals[arm]["rounds"] += 1
    averages: Dict[str, Dict[str, float]] = {}
    for arm, data in totals.items():
        rounds = max(data["rounds"], 1)
        averages[arm] = {
            "p95": data["p95"] / rounds,
            "recall": data["recall"] / rounds,
            "err": data["err"] / rounds,
            "samples": data["samples"],
            "rounds": rounds,
        }
    return averages


def _parse_router_md(path: Path) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    for row in _parse_markdown_table(path):
        if not row or row[0].lower() == "round":
            continue
        records.append(
            {
                "round": int(row[0]),
                "arm": row[1],
                "samples": int(row[2]),
                "p95_ms": float(row[3]),
                "recall": float(row[4]),
                "err": float(row[5]),
                "reward": float(row[6]),
                "meets_min": row[7].lower() == "yes",
                "winner": row[8],
                "metrics": row[9],
            }
        )
    return records


def _parse_ab_csv(path: Path) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            arm = row["policy"]
            out[arm] = {
                "p95": float(row.get("p95_ms", 0.0)),
                "recall": float(row.get("recall_at_10", 0.0)),
                "reward": float(row.get("reward", 0.0)),
                "metrics_path": row.get("metrics_path", ""),
            }
    return out


def _within_ratio(a: float, b: float, tolerance: float) -> bool:
    denom = max(abs(a), abs(b), 1e-6)
    return abs(a - b) / denom <= tolerance


def main() -> None:
    REPORTS_DIR.mkdir(exist_ok=True, parents=True)

    migrate_md = _latest("BANDIT_MIGRATE_*.md")
    router_md = _latest("BANDIT_ROUNDS_*.md")
    ab_csv = _latest("AB_*.csv")
    ab_md = _latest("AB_*.md")
    summary_json_path = Path("reports/BANDIT_SUMMARY_LATEST.json")

    summary_payload = _load_summary_json(summary_json_path)
    bandit_state = _load_bandit_state()

    migration_rows = _parse_markdown_table(migrate_md)
    router_rows = _parse_router_md(router_md)
    ab_results = _parse_ab_csv(ab_csv)
    router_avg = _average_router_stats(router_rows)

    # Validation checks
    migration_ok = True
    for row in migration_rows:
        if len(row) < 5 or row[0].lower() == "arm":
            continue
        delta = row[3]
        status = row[4].lower()
        if status != "aligned":
            try:
                if abs(float(delta)) > 0.1:
                    migration_ok = False
            except ValueError:
                migration_ok = False
        elif delta not in {"n/a", ""}:
            try:
                if abs(float(delta)) > 0.1:
                    migration_ok = False
            except ValueError:
                pass

    last_metrics_ok = True
    state_snapshot_lines: List[str] = ["arm\tn\tavg_reward\tlast_p95\tlast_recall"]
    for arm in ["fast_v1", "balanced_v1", "quality_v1"]:
        entry = bandit_state.get(arm, {})
        counts = entry.get("counts")
        avg_reward = entry.get("avg_reward")
        last_metrics = entry.get("last_metrics")
        p95 = None
        recall = None
        if isinstance(last_metrics, Mapping):
            p95 = last_metrics.get("p95_ms")
            recall = last_metrics.get("recall_at_10")
        if not isinstance(last_metrics, Mapping):
            last_metrics_ok = False
        else:
            if p95 in (None, "") or recall in (None, ""):
                last_metrics_ok = False
        state_snapshot_lines.append(
            "\t".join(
                [
                    arm,
                    str(counts),
                    f"{avg_reward:.6f}" if isinstance(avg_reward, (int, float)) else "n/a",
                    f"{p95:.2f}" if isinstance(p95, (int, float)) else "n/a",
                    f"{recall:.6f}" if isinstance(recall, (int, float)) else "n/a",
                ]
            )
        )

    sla_ok = True
    for row in router_rows:
        if row["p95_ms"] > SLA_P95 + 1e-6 or row["err"] > SLA_ERR + 1e-6:
            sla_ok = False
            break

    router_table_lines = [
        "| round | arm | samples | p95_ms | recall | err | reward | metrics |",
        "| --- | --- | ---:| ---:| ---:| ---:| ---:| --- |",
    ]
    for row in router_rows:
        router_table_lines.append(
            "| {round} | {arm} | {samples} | {p95:.1f} | {recall:.4f} | {err:.4f} | {reward:.4f} | {metrics} |".format(
                round=row["round"],
                arm=row["arm"],
                samples=row["samples"],
                p95=row["p95_ms"],
                recall=row["recall"],
                err=row["err"],
                reward=row["reward"],
                metrics=row["metrics"],
            )
        )

    ab_alignment_ok = True
    alignment_lines: List[str] = ["| arm | router_p95 | ab_p95 | router_recall | ab_recall | within_tol |"]
    alignment_lines.append("| --- | ---:| ---:| ---:| ---:| --- |")
    for arm in ["fast_v1", "balanced_v1", "quality_v1"]:
        router_stats = router_avg.get(arm, {})
        ab_stats = ab_results.get(arm, {})
        router_p95 = router_stats.get("p95")
        router_recall = router_stats.get("recall")
        ab_p95 = ab_stats.get("p95")
        ab_recall = ab_stats.get("recall")
        within = (
            _within_ratio(router_p95 or 0.0, ab_p95 or 0.0, AB_TOLERANCE)
            and _within_ratio(router_recall or 0.0, ab_recall or 0.0, AB_TOLERANCE)
        )
        if not within:
            ab_alignment_ok = False
        alignment_lines.append(
            "| {arm} | {rp95:.1f} | {ap95:.1f} | {rrecall:.4f} | {arecall:.4f} | {status} |".format(
                arm=arm,
                rp95=router_p95 or 0.0,
                ap95=ab_p95 or 0.0,
                rrecall=router_recall or 0.0,
                arecall=ab_recall or 0.0,
                status="yes" if within else "no",
            )
        )

    freeze_recommendation = summary_payload.get("best_arm")
    freeze_lines = summary_payload.get("conclusion", [])

    overall_ok = migration_ok and last_metrics_ok and ab_alignment_ok and sla_ok

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_path = REPORTS_DIR / f"BANDIT_ONECLICK_SUMMARY_{timestamp}.md"
    checklist_lines = [
        f"- {'✅' if migration_ok else '❌'} 迁移完成且 Δ≤0.1",
        f"- {'✅' if last_metrics_ok else '❌'} 三臂 last_metrics 已写入",
        f"- {'✅' if ab_alignment_ok else '❌'} 路由 vs A/B 指标量级一致 (tol={AB_TOLERANCE:.0%})",
        f"- {'✅' if sla_ok else '❌'} 无 SLA 违规 (p95≤{SLA_P95}, err≤{SLA_ERR})",
    ]

    content = [
        "# Bandit One-click Summary",
        "",
        f"- generated_at: {datetime.now(timezone.utc).isoformat()}",
        f"- migrate_report: {migrate_md}",
        f"- router_report: {router_md}",
        f"- ab_csv: {ab_csv}",
        f"- ab_md: {ab_md}",
        f"- summary_json: {summary_json_path}",
        "",
        *checklist_lines,
        "",
        f"整体状态：{'✅ ALL PASS' if overall_ok else '⚠️ 请复核'}",
        "",
        "## 迁移对比",
        "| arm | before_avg | after_avg | delta | status |",
        "| --- | ---:| ---:| ---:| --- |",
    ]
    # Append migration table from lines (skip header already added)
    for row in migration_rows:
        if len(row) == 5 and row[0].lower() != "arm":
            content.append("| " + " | ".join(row) + " |")

    content.extend(
        [
            "",
            "## 路由轮次概览",
            f"- source: {router_md}",
            "",
        ]
    )
    content.extend(router_table_lines)
    content.extend(
        [
            "",
            "## 路由 vs A/B 量级对比",
        ]
    )
    content.extend(alignment_lines)
    content.extend(
        [
            "",
            "## A/B 明细",
            "",
            ab_md.read_text(encoding="utf-8"),
            "",
            "## 冻结建议",
            f"- 推荐冻结: `{freeze_recommendation}`" if freeze_recommendation else "- 暂无冻结建议",
        ]
    )
    if isinstance(freeze_lines, list):
        content.extend(freeze_lines)
    content.extend(
        [
            "",
            "## 状态快照",
            "```\n" + "\n".join(state_snapshot_lines) + "\n```",
        ]
    )

    out_path.write_text("\n".join(content) + "\n", encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()

