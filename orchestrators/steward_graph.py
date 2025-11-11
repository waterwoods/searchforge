from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph


RUNS_DIR = os.path.join(os.getcwd(), ".runs")
BLOB_DIR = os.path.join(RUNS_DIR, "blobs")
BASELINES_DIR = os.path.join(os.getcwd(), "baselines")
ENV_CURRENT_PATH = os.path.join(os.getcwd(), ".env.current")
DEFAULT_ARTIFACTS_ROOT = os.getenv("ARTIFACTS_PATH", os.path.join(os.getcwd(), "artifacts"))

os.makedirs(RUNS_DIR, exist_ok=True)
os.makedirs(BLOB_DIR, exist_ok=True)
os.makedirs(BASELINES_DIR, exist_ok=True)

_THRESHOLD_SPECS: Tuple[Dict[str, Any], ...] = (
    {"env": "ACCEPT_P95_MS", "default": 500.0, "metric": "p95_ms", "comparison": "lte"},
    {"env": "ACCEPT_RECALL", "default": 0.90, "metric": "recall@10", "comparison": "gte", "aliases": ("MIN_RECALL10",)},
    {"env": "MIN_DELTA", "default": 0.0, "metric": "delta_recall", "comparison": "gte"},
)
_DELTA_METRIC_KEYS: Tuple[str, ...] = (
    "recall_delta",
    "delta_recall",
    "delta_recall_abs",
)


def put_blob(job_id: str, step: str, payload: Dict[str, Any]) -> str:
    safe = f"{job_id}-{step}-{int(time.time() * 1000)}.json"
    path = os.path.join(BLOB_DIR, safe)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)
    return path


def get_blob(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return None


def guard_state_size(state: Dict[str, Any], limit: int = 50_000) -> Dict[str, Any]:
    try:
        raw = json.dumps(state, ensure_ascii=False).encode("utf-8")
        if len(raw) <= limit:
            return state

        for key in ("plan", "reflection", "report"):
            if key in state and isinstance(state[key], (dict, list, str)):
                path = put_blob(state.get("job_id", "unknown"), key, {"data": state[key]})
                state[key] = {"blob": path}
                raw = json.dumps(state, ensure_ascii=False).encode("utf-8")
                if len(raw) <= limit:
                    return state

        important_keys = {
            "job_id",
            "dryrun_status",
            "errors",
            "metrics",
            "thresholds",
            "decision",
            "baseline_path",
            "baseline_latest_path",
            "resume",
        }
        keep = {k: v for k, v in state.items() if k in important_keys}
        keep["truncated"] = True
        return keep
    except Exception:
        return state


logger = logging.getLogger(__name__)


_sqlite_path = os.path.join(RUNS_DIR, "graph.db")
_sqlite_connection = sqlite3.connect(_sqlite_path, check_same_thread=False)
_checkpointer = SqliteSaver(_sqlite_connection)
logger.info("LangGraph steward graph using SqliteSaver at %s", _sqlite_path)


class GraphState(TypedDict, total=False):
    job_id: str
    plan: Optional[Any]
    dryrun_status: Optional[str]
    errors: List[str]
    metrics: Dict[str, Any]
    thresholds: Dict[str, Any]
    decision: Optional[str]
    baseline_path: Optional[str]
    baseline_latest_path: Optional[str]
    resume: bool


def _execute_with_timeout(fn: Callable[[], Dict[str, Any]], label: str, timeout: float = 5.0) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    error_holder: Dict[str, Exception] = {}

    def _runner() -> None:
        try:
            result.update(fn())
        except Exception as exc:  # pragma: no cover - defensive
            error_holder["error"] = exc

    thread = threading.Thread(target=_runner, name=f"{label}_worker", daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        raise TimeoutError(f"{label} timed out after {timeout} seconds")
    if "error" in error_holder:
        raise error_holder["error"]
    return result


def _ensure_errors(state: Dict[str, Any]) -> None:
    if "errors" not in state or state["errors"] is None:
        state["errors"] = []


def wrap(name: str, fn: Callable[[GraphState], Dict[str, Any]]) -> Callable[[GraphState], Dict[str, Any]]:
    def _inner(state: GraphState) -> Dict[str, Any]:
        _ensure_errors(state)
        try:
            out = fn(state) or {}
        except Exception as exc:
            errs = list(state.get("errors") or [])
            errs.append(f"{name}: {exc}")
            out = {"errors": errs}

        merged: Dict[str, Any] = {**state, **(out or {})}
        _ensure_errors(merged)
        sanitized = guard_state_size(merged)
        _ensure_errors(sanitized)
        return sanitized

    return _inner


def _coerce_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip().strip("\"'")
        if stripped == "":
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _load_manifest(job_id: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    errors: List[str] = []
    if not job_id:
        errors.append("evaluate: missing job_id")
        return None, errors

    artifacts_root = os.getenv("ARTIFACTS_PATH", DEFAULT_ARTIFACTS_ROOT)
    manifest_path = os.path.join(artifacts_root, job_id, "manifest.json")

    if not os.path.exists(manifest_path):
        errors.append(f"evaluate: manifest not found at {manifest_path}")
        return None, errors

    try:
        with open(manifest_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        errors.append(f"evaluate: failed to parse manifest: {exc}")
        return None, errors
    except OSError as exc:  # pragma: no cover - defensive filesystem error
        errors.append(f"evaluate: failed to read manifest: {exc}")
        return None, errors

    metrics_sources = []
    if isinstance(data, dict):
        metrics_sources.append(data)
        maybe_metrics = data.get("metrics")
        if isinstance(maybe_metrics, dict):
            metrics_sources.append(maybe_metrics)

    metrics: Dict[str, Any] = {}
    for source in metrics_sources:
        for key in ("p95_ms", "err_rate", "recall@10", "cost_tokens"):
            if key in source and key not in metrics:
                metrics[key] = source[key]

    normalized_metrics: Dict[str, Any] = {}
    for key, raw_value in metrics.items():
        coerced = _coerce_number(raw_value)
        if coerced is not None:
            normalized_metrics[key] = coerced

    missing_keys = [k for k in ("p95_ms", "err_rate", "recall@10", "cost_tokens") if k not in normalized_metrics]
    if missing_keys:
        errors.append(f"evaluate: missing metrics {', '.join(missing_keys)} in manifest {manifest_path}")

    return normalized_metrics if normalized_metrics else None, errors


def _load_thresholds() -> Tuple[Dict[str, float], List[str]]:
    errors: List[str] = []
    thresholds: Dict[str, float] = {}

    if not os.path.exists(ENV_CURRENT_PATH):
        errors.append(f"decide: thresholds file missing at {ENV_CURRENT_PATH}")
        return thresholds, errors

    try:
        with open(ENV_CURRENT_PATH, "r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                number = _coerce_number(value)
                if number is None:
                    continue
                thresholds[key] = number
    except OSError as exc:  # pragma: no cover - defensive filesystem error
        errors.append(f"decide: failed to read thresholds: {exc}")
        return thresholds, errors

    required = {
        "ACCEPT_P95_MS": "p95_ms",
        "ACCEPT_ERR_RATE": "err_rate",
        "MIN_RECALL10": "recall@10",
    }
    missing = [env_key for env_key in required if env_key not in thresholds]
    if missing:
        errors.append(f"decide: missing thresholds {', '.join(missing)} in {ENV_CURRENT_PATH}")

    normalized = {}
    for env_key, metric_key in required.items():
        if env_key in thresholds:
            normalized[metric_key] = thresholds[env_key]

    return normalized, errors


def review(state: GraphState) -> Dict[str, Any]:
    def _work() -> Dict[str, Any]:
        job_id = state.get("job_id", "")
        plan = f"Review plan for job {job_id}" if job_id else "Review plan unavailable"
        return {"plan": plan}

    return _execute_with_timeout(_work, "review")


def reflect(state: GraphState) -> Dict[str, Any]:
    def _work() -> Dict[str, Any]:
        plan = state.get("plan") or "No plan generated"
        reflected_plan = f"{plan} -> Reflected"
        return {"plan": reflected_plan}

    return _execute_with_timeout(_work, "reflect")


def dryrun(state: GraphState) -> Dict[str, Any]:
    def _work() -> Dict[str, Any]:
        plan = state.get("plan") or "No plan to dry-run"
        status = f"Dry-run scheduled for plan: {plan}"
        return {"dryrun_status": status}

    return _execute_with_timeout(_work, "dryrun")


def dryrun_decider(state: Dict[str, Any]) -> str:
    if state.get("errors"):
        return "fail"
    status = state.get("dryrun_status")
    if status in ("ok", "OK", "success"):
        return "ok"
    if isinstance(status, str) and status.strip():
        return "ok"
    return "fail"


def review_decider(state: Dict[str, Any]) -> str:
    decision = state.get("decision")
    if decision in ("accept", "reject"):
        return "halt"
    return "continue"


def evaluate(state: GraphState) -> Dict[str, Any]:
    job_id = state.get("job_id", "")
    metrics, eval_errors = _load_manifest(job_id)

    merged_errors = list(state.get("errors") or [])
    merged_errors.extend(eval_errors)

    output: Dict[str, Any] = {"errors": merged_errors}
    if metrics:
        output["metrics"] = metrics
    return output


def decide(state: GraphState) -> Dict[str, Any]:
    metrics = state.get("metrics") or {}
    thresholds, threshold_errors = _load_thresholds()

    merged_errors = list(state.get("errors") or [])
    merged_errors.extend(threshold_errors)

    decision = "reject"
    details: Dict[str, Any] = {"thresholds": thresholds}

    if metrics and not threshold_errors:
        p95_ok = metrics.get("p95_ms") is not None and thresholds.get("p95_ms") is not None and metrics["p95_ms"] <= thresholds["p95_ms"]
        err_ok = metrics.get("err_rate") is not None and thresholds.get("err_rate") is not None and metrics["err_rate"] <= thresholds["err_rate"]
        recall_ok = metrics.get("recall@10") is not None and thresholds.get("recall@10") is not None and metrics["recall@10"] >= thresholds["recall@10"]
        if p95_ok and err_ok and recall_ok:
            decision = "accept"
        else:
            merged_errors.append("decide: metrics did not meet acceptance thresholds")
    else:
        if not metrics:
            merged_errors.append("decide: metrics unavailable")

    if decision == "reject":
        details["halt_reason"] = "reject"

    output: Dict[str, Any] = {"decision": decision, "errors": merged_errors}
    output.update(details)
    return output


def decide_router(state: Dict[str, Any]) -> str:
    if state.get("decision") == "accept":
        return "persist"
    return "review"


def persist(state: GraphState) -> Dict[str, Any]:
    job_id = state.get("job_id", "")
    metrics = state.get("metrics") or {}
    decision = state.get("decision")

    merged_errors = list(state.get("errors") or [])
    if decision != "accept":
        merged_errors.append("persist: cannot persist without accepted decision")
        return {"errors": merged_errors}

    if not job_id:
        merged_errors.append("persist: missing job_id")
        return {"errors": merged_errors}

    if not metrics:
        merged_errors.append("persist: metrics unavailable")
        return {"errors": merged_errors}

    baseline_payload = {
        "job_id": job_id,
        "decision": decision,
        "metrics": metrics,
        "persisted_at": int(time.time()),
    }

    job_path = os.path.join(BASELINES_DIR, f"{job_id}.json")
    latest_path = os.path.join(BASELINES_DIR, "latest.json")

    try:
        os.makedirs(BASELINES_DIR, exist_ok=True)
        with open(job_path, "w", encoding="utf-8") as handle:
            json.dump(baseline_payload, handle, ensure_ascii=False, indent=2)
        with open(latest_path, "w", encoding="utf-8") as handle:
            json.dump(baseline_payload, handle, ensure_ascii=False, indent=2)
    except OSError as exc:  # pragma: no cover - filesystem error handling
        merged_errors.append(f"persist: failed to write baseline files: {exc}")
        return {"errors": merged_errors}

    return {
        "baseline_path": job_path,
        "baseline_latest_path": latest_path,
        "errors": merged_errors,
        "resume": state.get("resume", False),
    }


def notify(state: GraphState) -> Dict[str, Any]:
    job_id = state.get("job_id", "")
    decision = state.get("decision")
    metrics = state.get("metrics") or {}
    baseline_path = state.get("baseline_path")

    logger.info(
        "Steward notify job_id=%s decision=%s baseline=%s metrics=%s",
        job_id,
        decision,
        baseline_path,
        metrics,
    )

    return {"resume": state.get("resume", False)}


graph = StateGraph(GraphState)
graph.add_node("review", wrap("review", review))
graph.add_node("reflect", wrap("reflect", reflect))
graph.add_node("dryrun", wrap("dryrun", dryrun))
graph.add_node("evaluate", wrap("evaluate", evaluate))
graph.add_node("decide", wrap("decide", decide))
graph.add_node("persist", wrap("persist", persist))
graph.add_node("notify", wrap("notify", notify))

graph.set_entry_point("review")
graph.add_conditional_edges("review", review_decider, {"continue": "reflect", "halt": END})
graph.add_edge("reflect", "dryrun")
graph.add_conditional_edges("dryrun", dryrun_decider, {"ok": "evaluate", "fail": "review"})
graph.add_edge("evaluate", "decide")
graph.add_conditional_edges("decide", decide_router, {"persist": "persist", "review": "review"})
graph.add_edge("persist", "notify")
graph.add_edge("notify", END)

app = graph.compile(checkpointer=_checkpointer)

