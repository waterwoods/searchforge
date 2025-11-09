"""
Helpers for aggregating metrics.json artifacts produced by evaluation runs.
"""

from __future__ import annotations

import json
from pathlib import Path
import glob
import csv
from collections import Counter
from typing import Any, Dict, List, Mapping, Sequence, Union

MetricsSource = Union[str, Path]


class MetricsAggregationError(RuntimeError):
    """Raised when metrics aggregation cannot be completed."""


def _resolve_sources(source: Union[MetricsSource, Sequence[MetricsSource]]) -> List[Path]:
    if isinstance(source, (str, Path)):
        source = [source]

    paths: List[Path] = []
    for item in source or []:
        path = Path(item)
        if any(char in str(path) for char in ("*", "?", "[")):
            for match in glob.glob(str(path), recursive=True):
                match_path = Path(match)
                if match_path.is_file():
                    paths.append(match_path)
        else:
            if path.is_dir():
                candidate = path / "metrics.json"
                if candidate.exists():
                    paths.append(candidate)
            elif path.is_file():
                paths.append(path)
            else:
                raise MetricsAggregationError(f"Metrics source not found: {path}")
    if not paths:
        raise MetricsAggregationError("No metrics paths resolved from the provided sources.")
    return paths


def _load_metrics(path: Path) -> Mapping[str, object]:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def aggregate_metrics(sources: Union[MetricsSource, Sequence[MetricsSource]]) -> Dict[str, object]:
    """
    Aggregate metrics.json files into a concise summary.
    """
    paths = _resolve_sources(sources)

    total_weight = 0
    weighted_recall = 0.0
    weighted_p95 = 0.0
    total_cost = 0.0
    total_count = 0
    jobs: List[str] = []
    statuses: List[str] = []

    for path in paths:
        data = _load_metrics(path)
        metrics = data.get("metrics") or {}
        job_id = str(data.get("job_id", path.parent.name))
        status = str(data.get("status", "unknown"))
        jobs.append(job_id)
        statuses.append(status)

        count = int(metrics.get("count", 0) or 0)
        weight = count if count > 0 else 1
        recall = float(metrics.get("recall_at_10", 0.0) or 0.0)
        p95 = float(metrics.get("p95_ms", 0.0) or 0.0)
        cost_per_query = float(metrics.get("cost_per_query", 0.0) or 0.0)

        total_weight += weight
        weighted_recall += recall * weight
        weighted_p95 += p95 * weight
        total_cost += cost_per_query * weight
        total_count += count

    summary = {
        "jobs": jobs,
        "statuses": statuses,
        "count": total_count,
        "recall_at_10": weighted_recall / total_weight if total_weight else 0.0,
        "p95_ms": weighted_p95 / total_weight if total_weight else 0.0,
        "cost": total_cost,
    }
    return summary


def write_fail_topn_csv(
    results: Sequence[Mapping[str, Any]],
    output_path: Union[str, Path],
    *,
    top_n: int = 5,
) -> Path:
    """
    Write a CSV summarizing the most common failure reasons.
    """
    counter: Counter[str] = Counter()
    for item in results or []:
        status = str(item.get("status", "") or "").lower()
        if status == "ok":
            continue
        reason = item.get("error") or item.get("status") or "unknown"
        counter[str(reason)] += 1

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(["reason", "count"])
        for reason, count in counter.most_common(top_n):
            writer.writerow([reason, count])
    return output_path

