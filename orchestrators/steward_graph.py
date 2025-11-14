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

from services.fiqa_api import obs

RUNS_DIR = os.path.join(os.getcwd(), ".runs")
BLOB_DIR = os.path.join(RUNS_DIR, "blobs")
BASELINES_DIR = os.path.join(os.getcwd(), "baselines")
DEFAULT_ARTIFACTS_ROOT = os.getenv("ARTIFACTS_PATH", os.path.join(os.getcwd(), "artifacts"))

os.makedirs(RUNS_DIR, exist_ok=True)
os.makedirs(BLOB_DIR, exist_ok=True)
os.makedirs(BASELINES_DIR, exist_ok=True)

_THRESHOLD_SPECS: Tuple[Dict[str, Any], ...] = (
    {"env": "ACCEPT_P95_MS", "default": 500.0, "metric": "p95_ms", "comparison": "lte"},
    {
        "env": "ACCEPT_RECALL",
        "default": 0.90,
        "metric": "recall@10",
        "comparison": "gte",
        "aliases": ("MIN_RECALL10",),
    },
    {"env": "MIN_DELTA", "default": 0.0, "metric": "delta_recall", "comparison": "gte"},
)
_DELTA_METRIC_KEYS: Tuple[str, ...] = ("recall_delta", "delta_recall", "delta_recall_abs")
_METRIC_KEY_ALIASES = {
    "p95_ms": ("p95_ms", "p95", "latency_p95_ms"),
    "recall@10": ("recall@10", "recall_at10", "recall_at_10", "recall10"),
    "delta_recall": _DELTA_METRIC_KEYS + ("delta_recall_pct",),
}


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
    trace_id: str
    plan: Optional[Any]
    dryrun_status: Optional[str]
    errors: List[str]
    metrics: Dict[str, Any]
    thresholds: Dict[str, Any]
    decision: Optional[str]
    baseline_path: Optional[str]
    baseline_latest_path: Optional[str]
    resume: bool
    obs_ctx: Dict[str, Any]
    obs_url: str


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
        job_id = state.get("job_id")
        raw_obs_ctx = state.get("obs_ctx")
        obs_ctx_dict: Dict[str, Any] = {}
        obs_ctx_key: Optional[str] = None
        if isinstance(raw_obs_ctx, str) and raw_obs_ctx:
            obs_ctx_key = raw_obs_ctx
            obs_ctx_dict = obs.get_registered_ctx(obs_ctx_key) or {}
        elif isinstance(raw_obs_ctx, dict):
            obs_ctx_dict = raw_obs_ctx
            obs_ctx_key = job_id and f"steward:{job_id}" or None
            if obs_ctx_key and obs_ctx_dict:
                obs.register_ctx(obs_ctx_key, obs_ctx_dict)
            state["obs_ctx"] = obs_ctx_key or ""
        else:
            obs_ctx_key = job_id and f"steward:{job_id}" or None
            obs_ctx_dict = obs.get_registered_ctx(obs_ctx_key) or {}
            state["obs_ctx"] = obs_ctx_key or ""
        if job_id:
            obs_ctx_dict.setdefault("job_id", job_id)
        if not state.get("obs_url"):
            state["obs_url"] = obs_ctx_dict.get("obs_url", state.get("obs_url", ""))
        if not state.get("trace_id"):
            trace_id_value = obs_ctx_dict.get("trace_id")
            if trace_id_value:
                state["trace_id"] = trace_id_value

        attrs: Dict[str, Any] = {"node": name}
        if job_id:
            attrs["job_id"] = job_id
        metrics = state.get("metrics") if isinstance(state.get("metrics"), dict) else {}
        for metric_key in ("p95_ms", "recall@10", "err_rate"):
            metric_value = metrics.get(metric_key)
            if metric_value is not None:
                attrs[metric_key] = metric_value

        span_state = dict(state)
        span_state.pop("obs_ctx", None)
        span_input = obs.redact(span_state)

        with obs.span(obs_ctx_dict, f"steward.{name}", attrs=attrs) as span_obj:
            if span_obj:
                obs.io(span_obj, input=span_input)
            try:
                out = fn(state) or {}
            except Exception as exc:
                errs = list(state.get("errors") or [])
                errs.append(f"{name}: {exc}")
                out = {"errors": errs}
                if span_obj:
                    try:
                        span_obj.update(metadata={"status": "error"})
                        obs.io(span_obj, output=out)
                    except Exception:
                        pass
                merged_error_state: Dict[str, Any] = {**state, **(out or {})}
                _ensure_errors(merged_error_state)
                obs_ctx_value = merged_error_state.pop("obs_ctx", obs_ctx_key or "")
                sanitized_error = guard_state_size(merged_error_state)
                sanitized_error["obs_ctx"] = obs_ctx_value or ""
                _ensure_errors(sanitized_error)
                return sanitized_error

        if span_obj:
            metrics_sources = []
            if isinstance(out, dict):
                potential_metrics = out.get("metrics")
                if isinstance(potential_metrics, dict):
                    metrics_sources.append(potential_metrics)
            if isinstance(metrics, dict):
                metrics_sources.append(metrics)

            metric_updates: Dict[str, Any] = {}
            for metric_key in ("p95_ms", "recall@10", "err_rate"):
                for source in metrics_sources:
                    if source and source.get(metric_key) is not None:
                        metric_updates[metric_key] = source[metric_key]
                        break
            try:
                if metric_updates:
                    span_obj.update(metadata=metric_updates)
                obs.io(span_obj, output=out)
            except Exception:
                pass

        merged: Dict[str, Any] = {**state, **(out or {})}
        _ensure_errors(merged)
        obs_ctx_value = merged.pop("obs_ctx", obs_ctx_key or "")
        sanitized = guard_state_size(merged)
        sanitized["obs_ctx"] = obs_ctx_value or ""
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
        for key in ("p95_ms", "err_rate", "recall@10", "cost_tokens", "delta_recall"):
            if key in source and key not in metrics:
                metrics[key] = source[key]

    normalized_metrics: Dict[str, Any] = {}
    for key, raw_value in metrics.items():
        coerced = _coerce_number(raw_value)
        if coerced is not None:
            normalized_metrics[key] = coerced

    missing_keys = [
        k for k in ("p95_ms", "err_rate", "recall@10", "cost_tokens") if k not in normalized_metrics
    ]
    if missing_keys:
        errors.append(f"evaluate: missing metrics {', '.join(missing_keys)} in manifest {manifest_path}")

    return normalized_metrics if normalized_metrics else None, errors


def _load_thresholds() -> Tuple[Dict[str, float], List[str]]:
    thresholds: Dict[str, float] = {}
    errors: List[str] = []

    for spec in _THRESHOLD_SPECS:
        env_keys = (spec["env"],) + tuple(spec.get("aliases", ()))
        value: Optional[float] = None
        source = None

        for env_key in env_keys:
            raw = os.getenv(env_key)
            if raw is None:
                continue
            coerced = _coerce_number(raw)
            if coerced is None:
                fallback_msg = (
                    f"decide: invalid threshold {env_key}={raw!r}; using default {spec['default']}"
                )
                logger.warning(fallback_msg)
                errors.append(fallback_msg)
                continue
            value = coerced
            source = env_key
            break

        if value is None:
            value = float(spec["default"])
            source = "default"
            logger.info(
                "decide: threshold %s falling back to default %.3f",
                spec["metric"],
                value,
            )

        thresholds[spec["metric"]] = value
        logger.info(
            "decide: threshold %s=%.3f source=%s",
            spec["metric"],
            value,
            source,
        )

    return thresholds, errors


def _extract_from_mapping(container: Dict[str, Any], keys: Tuple[str, ...]) -> Optional[Any]:
    for key in keys:
        if key in container:
            return container[key]
    return None


def _resolve_metric(metrics: Dict[str, Any], metric_key: str) -> Optional[float]:
    aliases = _METRIC_KEY_ALIASES.get(metric_key, (metric_key,))

    value = _extract_from_mapping(metrics, aliases)
    if value is None and "deltas" in metrics and isinstance(metrics["deltas"], dict):
        value = _extract_from_mapping(metrics["deltas"], aliases)

    if value is None and metric_key == "delta_recall":
        for delta_key in _DELTA_METRIC_KEYS:
            if delta_key in metrics:
                value = metrics[delta_key]
                break
        if value is None and "deltas" in metrics and isinstance(metrics["deltas"], dict):
            for delta_key in _DELTA_METRIC_KEYS:
                if delta_key in metrics["deltas"]:
                    value = metrics["deltas"][delta_key]
                    break

    if value is None:
        return None

    coerced = _coerce_number(value)
    return coerced


def _metric_satisfied(metric_value: float, threshold: float, comparison: str) -> bool:
    if comparison == "lte":
        return metric_value <= threshold
    if comparison == "gte":
        return metric_value >= threshold
    raise ValueError(f"Unknown comparison {comparison}")


def _build_threshold_summary(thresholds: Dict[str, float]) -> Dict[str, float]:
    return {key: round(value, 6) for key, value in thresholds.items()}


def _missing_metric_error(metric_key: str) -> str:
    return f"decide: metric '{metric_key}' missing or invalid"


def _normalize_metrics(metrics: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(metrics, dict):
        return {}
    normalized: Dict[str, Any] = {}
    for key, value in metrics.items():
        if isinstance(value, dict):
            normalized[key] = _normalize_metrics(value)
        else:
            normalized[key] = value
    return normalized


def _evaluate_thresholds(metrics: Dict[str, Any], thresholds: Dict[str, float]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    all_satisfied = True

    normalized_metrics = _normalize_metrics(metrics)

    for spec in _THRESHOLD_SPECS:
        metric_key = spec["metric"]
        metric_value = _resolve_metric(normalized_metrics, metric_key)
        if metric_value is None:
            errors.append(_missing_metric_error(metric_key))
            all_satisfied = False
            continue

        threshold_value = thresholds.get(metric_key, spec["default"])
        comparison = spec["comparison"]
        satisfied = _metric_satisfied(metric_value, threshold_value, comparison)
        logger.info(
            "decide: metric %s=%.4f vs threshold %.4f (%s) -> %s",
            metric_key,
            metric_value,
            threshold_value,
            comparison,
            "ok" if satisfied else "fail",
        )

        if not satisfied:
            direction = "<=" if comparison == "lte" else ">="
            errors.append(
                f"decide: metric '{metric_key}'={metric_value:.4f} not {direction} threshold {threshold_value:.4f}"
            )
            all_satisfied = False

    return all_satisfied, errors


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
    else:
        merged_errors.append("evaluate: metrics unavailable")
    return output


def decide(state: GraphState) -> Dict[str, Any]:
    metrics = state.get("metrics") or {}
    thresholds, threshold_errors = _load_thresholds()

    merged_errors = list(state.get("errors") or [])
    merged_errors.extend(threshold_errors)

    adopted_thresholds = _build_threshold_summary(thresholds)

    decision = "reject"
    details: Dict[str, Any] = {"thresholds": adopted_thresholds}

    if not metrics:
        merged_errors.append("decide: metrics unavailable")
    else:
        satisfied, metric_errors = _evaluate_thresholds(metrics, thresholds)
        merged_errors.extend(metric_errors)
        if satisfied and not metric_errors:
            decision = "accept"
        else:
            merged_errors.append("decide: metrics did not meet acceptance thresholds")

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
        return {
            "errors": merged_errors,
            "resume": state.get("resume", False),
        }

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

    os.makedirs(BASELINES_DIR, exist_ok=True)

    def _atomic_write(target_path: str) -> None:
        tmp_path = f"{target_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(baseline_payload, handle, ensure_ascii=False, indent=2)
        os.replace(tmp_path, target_path)

    success_paths: Dict[str, str] = {}
    for target in (job_path, latest_path):
        try:
            _atomic_write(target)
            success_paths[target] = target
        except (OSError, json.JSONDecodeError) as exc:
            merged_errors.append(f"persist: failed to write {target}: {exc}")
            logger.warning("persist: failed atomic write for %s: %s", target, exc)

    result: Dict[str, Any] = {
        "errors": merged_errors,
        "resume": state.get("resume", False),
    }
    if job_path in success_paths:
        result["baseline_path"] = job_path
    if latest_path in success_paths:
        result["baseline_latest_path"] = latest_path
    return result


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

