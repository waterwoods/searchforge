from __future__ import annotations

import glob
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

ART_ROOTS = [
    "artifacts/sla/manifests",
    "artifacts/manifests",
    "artifacts",
]

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _expand(path: str) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        return str(candidate)
    return str(_PROJECT_ROOT / path)


def _read_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return None


def load_manifest(job_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    for root in ART_ROOTS:
        expanded_root = _expand(root)
        p1 = os.path.join(expanded_root, f"{job_id}.json")
        if os.path.isfile(p1):
            manifest = _read_json(p1)
            if manifest:
                return manifest, p1

        p2 = os.path.join(expanded_root, job_id, "manifest.json")
        if os.path.isfile(p2):
            manifest = _read_json(p2)
            if manifest:
                return manifest, p2

    return None, None


def extract_metrics_from_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    metrics = {"p95_ms": None, "err_rate": None, "recall_at_10": None, "cost_tokens": None}
    if not manifest:
        return metrics

    sources = [manifest, manifest.get("summary") or {}, manifest.get("metrics") or {}]
    for source in sources:
        if not isinstance(source, dict):
            continue

        if metrics["p95_ms"] is None:
            value = source.get("p95_ms")
            if value is None:
                value = source.get("latency_p95_ms")
            if value is not None:
                metrics["p95_ms"] = value

        if metrics["err_rate"] is None:
            value = source.get("err_rate")
            if value is None:
                value = source.get("error_rate")
            if value is not None:
                metrics["err_rate"] = value

        if metrics["recall_at_10"] is None:
            value = source.get("recall@10")
            if value is None:
                value = source.get("recall_at_10")
            if value is not None:
                metrics["recall_at_10"] = value

        if metrics["cost_tokens"] is None:
            value = source.get("cost_tokens")
            if value is None:
                value = source.get("tokens_used")
            if value is None:
                value = source.get("tokens")
            if value is None:
                value = source.get("total_tokens")
            if value is not None:
                metrics["cost_tokens"] = value

    return metrics


_RE_P95 = re.compile(r"(?:latency_)?p95(?:_ms)?\s*[:=]\s*([0-9]+(\.[0-9]+)?(?:ms)?)", re.I)
_RE_ERR = re.compile(r"(err(?:or)?_rate)\s*[:=]\s*([0-9]+(\.[0-9]+)?)", re.I)
_RE_REC10 = re.compile(r"(recall@?10)\s*[:=]\s*([0-9]+(\.[0-9]+)?)", re.I)
_RE_TOK = re.compile(r"(cost_tokens|tokens_used|tokens|total_tokens)\s*[:=]\s*([0-9]+)", re.I)
_RE_METRICS_LINE = re.compile(r"^METRICS\s+(.*)$", re.MULTILINE)
_RE_METRIC_PAIR = re.compile(r"([a-zA-Z0-9_@]+)=([^\s]+)")


def parse_metrics_from_log(text: str) -> Dict[str, Any]:
    metrics = {"p95_ms": None, "err_rate": None, "recall_at_10": None, "cost_tokens": None}
    if not text:
        return metrics

    def _coerce_p95(raw: str) -> Optional[float]:
        if not raw:
            return None
        raw_clean = raw.strip().rstrip("msMS")
        try:
            value = float(raw_clean)
        except (TypeError, ValueError):
            return None
        return value if value > 0 else None

    def _coerce_float(raw: str) -> Optional[float]:
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    try:
        metrics_lines = _RE_METRICS_LINE.findall(text)
        if metrics_lines:
            last_line = metrics_lines[-1]
            for key, raw_value in _RE_METRIC_PAIR.findall(last_line):
                key_lower = key.lower()
                if metrics["p95_ms"] is None and key_lower in ("p95_ms", "latency_p95_ms", "p95"):
                    value = _coerce_p95(raw_value)
                    if value is not None:
                        metrics["p95_ms"] = value
                elif metrics["err_rate"] is None and key_lower in ("err_rate", "error_rate"):
                    value = _coerce_float(raw_value)
                    if value is not None:
                        metrics["err_rate"] = max(0.0, min(1.0, value))
                elif metrics["recall_at_10"] is None and key_lower in ("recall@10", "recall_at_10", "recall10"):
                    value = _coerce_float(raw_value)
                    if value is not None:
                        metrics["recall_at_10"] = max(0.0, min(1.0, value))
                elif metrics["cost_tokens"] is None and key_lower in ("cost_tokens", "tokens_used", "tokens", "total_tokens"):
                    try:
                        metrics["cost_tokens"] = int(float(raw_value))
                    except (TypeError, ValueError):
                        continue
    except Exception:
        pass

    if metrics["p95_ms"] is None:
        match = _RE_P95.search(text)
        if match:
            value = _coerce_p95(match.group(1))
            if value is not None:
                metrics["p95_ms"] = value

    if metrics["err_rate"] is None:
        match = _RE_ERR.search(text)
        if match:
            value = _coerce_float(match.group(2))
            if value is not None:
                metrics["err_rate"] = max(0.0, min(1.0, value))

    if metrics["recall_at_10"] is None:
        match = _RE_REC10.search(text)
        if match:
            value = _coerce_float(match.group(2))
            if value is not None:
                metrics["recall_at_10"] = max(0.0, min(1.0, value))

    if metrics["cost_tokens"] is None:
        match = _RE_TOK.search(text)
        if match:
            try:
                metrics["cost_tokens"] = int(match.group(2))
            except (TypeError, ValueError):
                pass

    return metrics


def merge_metrics(primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(primary)
    for key, value in secondary.items():
        if merged.get(key) is None and value is not None:
            merged[key] = value
    return merged


def load_baseline() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    explicit = ["artifacts/sla/baseline.json", "artifacts/baseline.json"]
    for candidate in explicit:
        expanded = _expand(candidate)
        if os.path.isfile(expanded):
            data = _read_json(expanded)
            if data:
                return data, expanded

    files = []
    for root in ART_ROOTS:
        expanded_root = _expand(root)
        files.extend(glob.glob(os.path.join(expanded_root, "*.json")))
        files.extend(glob.glob(os.path.join(expanded_root, "*", "manifest.json")))

    files = sorted(files, key=lambda path: os.path.getmtime(path), reverse=True)

    for path in files[:50]:
        manifest = _read_json(path)
        status = manifest.get("status") if isinstance(manifest, dict) else None
        if isinstance(manifest, dict) and isinstance(status, str) and status.upper() == "SUCCEEDED":
            return manifest, path

    return None, None


__all__ = [
    "load_manifest",
    "extract_metrics_from_manifest",
    "parse_metrics_from_log",
    "merge_metrics",
    "load_baseline",
]

