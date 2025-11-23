"""Global AutoTuner singleton wiring for rag-api."""

import collections
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from modules.autotune import AutoTuner, TuningState
from modules.autotune.selector import select_strategy

_AUTOSAVE_INTERVAL_SEC = float(os.getenv("AUTOTUNER_AUTOSAVE_SEC", "30"))
STATE_PATH = os.getenv("TUNER_STATE_PATH", ".runs/tuner_state.json")
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "2000"))
COMPACT_EVERY = int(os.getenv("COMPACT_EVERY", "100"))
COMPACT_KEEP_EVERY = int(os.getenv("COMPACT_KEEP_EVERY", "5"))
_GLOBAL = {
    "tuner": None,
    "state": None,
    "last_autosave": 0.0,
    "history_len": 0,
    "last_params": None,
}
_POLICY_FILE = Path(".runs/policy.txt")
_STATE_FILE = Path(STATE_PATH)


def _runs_dir() -> Path:
    path = Path(".runs")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _persist_policy(name: str) -> None:
    try:
        _runs_dir()
        _POLICY_FILE.write_text(f"{name}\n", encoding="utf-8")
    except OSError:
        # Observability helper - failure to persist policy should not break flow
        pass


def _snapshot_state(state: TuningState) -> Dict[str, Any]:
    recent_metrics = list(state.recent_metrics)[-state.max_history :]
    parameter_history = list(getattr(state, "parameter_history", []))[-state.max_history :]
    recall_queue = list(getattr(state, "recent_recall_queue", []))
    maxlen = None
    queue = getattr(state, "recent_recall_queue", None)
    if isinstance(queue, collections.deque):
        maxlen = queue.maxlen
    return {
        "ef_search": state.ef_search,
        "rerank_k": state.rerank_k,
        "hnsw_ef_range": list(state.hnsw_ef_range),
        "rerank_range": list(state.rerank_range),
        "ema_alpha": state.ema_alpha,
        "p95_ms": state.p95_ms,
        "recall_at_10": state.recall_at_10,
        "coverage": state.coverage,
        "ema_p95_ms": state.ema_p95_ms,
        "ema_recall_at_10": state.ema_recall_at_10,
        "target_p95_ms": state.target_p95_ms,
        "target_recall": state.target_recall,
        "target_coverage": state.target_coverage,
        "recent_metrics": recent_metrics,
        "parameter_history": parameter_history,
        "max_history": state.max_history,
        "history_len": getattr(state, "history_len", 0),  # Cumulative counter
        "recent_recall_queue": recall_queue,
        "recent_recall_queue_maxlen": maxlen,
        "batches_since_decrease": state.batches_since_decrease,
        "is_emergency_mode": state.is_emergency_mode,
    }


def _reset_summary() -> None:
    _GLOBAL["history_len"] = 0
    _GLOBAL["last_params"] = None


def _update_summary(state: TuningState) -> Tuple[int, Optional[Dict[str, Any]]]:
    # Use history_len counter from state (monotonically increasing), fallback to array length
    history_len = getattr(state, "history_len", 0)
    if history_len == 0:
        history = list(getattr(state, "parameter_history", []))
        history_len = len(history)
    try:
        current_params = dict(state.get_current_params())
    except Exception:
        current_params = {}
    history = list(getattr(state, "parameter_history", []))
    last_params = history[-1] if history else current_params
    _GLOBAL["history_len"] = history_len
    _GLOBAL["last_params"] = last_params
    return history_len, last_params


def _load_state() -> Tuple[Optional[TuningState], Optional[str]]:
    if not _STATE_FILE.exists():
        return None, None
    try:
        payload = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None, None

    state_payload = payload.get("state")
    if not isinstance(state_payload, dict):
        return None, payload.get("policy")

    state = TuningState()
    state.ef_search = int(state_payload.get("ef_search", state.ef_search))
    state.rerank_k = int(state_payload.get("rerank_k", state.rerank_k))
    state.hnsw_ef_range = tuple(state_payload.get("hnsw_ef_range", state.hnsw_ef_range))
    state.rerank_range = tuple(state_payload.get("rerank_range", state.rerank_range))
    state.ema_alpha = float(state_payload.get("ema_alpha", state.ema_alpha))
    state.p95_ms = float(state_payload.get("p95_ms", state.p95_ms))
    state.recall_at_10 = float(state_payload.get("recall_at_10", state.recall_at_10))
    state.coverage = float(state_payload.get("coverage", state.coverage))
    state.ema_p95_ms = state_payload.get("ema_p95_ms", state.ema_p95_ms)
    state.ema_recall_at_10 = state_payload.get("ema_recall_at_10", state.ema_recall_at_10)
    state.target_p95_ms = float(state_payload.get("target_p95_ms", state.target_p95_ms))
    state.target_recall = float(state_payload.get("target_recall", state.target_recall))
    state.target_coverage = float(state_payload.get("target_coverage", state.target_coverage))
    state.max_history = int(state_payload.get("max_history", MAX_HISTORY))
    state.recent_metrics = list(state_payload.get("recent_metrics", []))[-state.max_history :]
    state.parameter_history = list(state_payload.get("parameter_history", []))[-state.max_history :]
    # Restore history_len counter (monotonically increasing)
    state.history_len = int(state_payload.get("history_len", len(state.parameter_history)))
    # Restore compact counter (internal, defaults to 0)
    state._compact_count = int(state_payload.get("_compact_count", 0))
    queue_items = list(state_payload.get("recent_recall_queue", []))
    queue_maxlen = state_payload.get("recent_recall_queue_maxlen")
    queue_maxlen = int(queue_maxlen) if queue_maxlen else None
    state.recent_recall_queue = collections.deque(queue_items, maxlen=queue_maxlen or None)
    state.batches_since_decrease = int(state_payload.get("batches_since_decrease", 0))
    state.is_emergency_mode = bool(state_payload.get("is_emergency_mode", False))
    state.emergency_mode = state.is_emergency_mode
    policy = payload.get("policy")
    return state, policy


def _persist_state(tuner: AutoTuner, state: TuningState) -> None:
    """
    Atomically persist state to disk using tmp file + rename pattern.
    On failure, roll back (tmp file is not renamed, so old file remains).
    """
    snapshot = {
        "ts": time.time(),
        "policy": getattr(tuner, "policy_name", ""),
        "state": _snapshot_state(state),
    }
    tmp_path = None
    try:
        _runs_dir()
        tmp_path = _STATE_FILE.with_suffix(".tmp")
        # Write to tmp file first
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())  # Force flush to disk
        # Atomic rename (move)
        tmp_path.replace(_STATE_FILE)
        tmp_path = None  # Mark as successfully renamed
    except OSError as e:
        # Rollback: if tmp_path exists, remove it (don't rename to main file)
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        # Fail silently (observability helper)
        pass
    finally:
        _update_summary(state)
        _GLOBAL["last_autosave"] = time.time()


def _should_autosave(now: float) -> bool:
    if _AUTOSAVE_INTERVAL_SEC <= 0:
        return True
    last = _GLOBAL.get("last_autosave", 0.0) or 0.0
    return (now - last) >= _AUTOSAVE_INTERVAL_SEC


def _maybe_autosave(tuner: AutoTuner, state: TuningState, force: bool = False) -> None:
    if tuner is None or state is None:
        return
    now = time.time()
    if force or _should_autosave(now):
        _persist_state(tuner, state)


def _state_file_mtime_iso() -> Optional[str]:
    if not _STATE_FILE.exists():
        return None
    try:
        mtime = _STATE_FILE.stat().st_mtime
    except OSError:
        return None
    return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()


def _create_autotuner(policy_name: Optional[str] = None, state: Optional[TuningState] = None) -> Tuple[AutoTuner, TuningState]:
    loaded_state, saved_policy = (None, None)
    if state is None:
        loaded_state, saved_policy = _load_state()
        state = loaded_state or TuningState()
        # Set max_history from env if not loaded
        if state.max_history == 100:  # Default value
            state.max_history = MAX_HISTORY
    else:
        # Ensure max_history is set from env
        if state.max_history == 100:  # Default value
            state.max_history = MAX_HISTORY
    configured_policy = policy_name or saved_policy or os.getenv("TUNER_POLICY", "RecallFirst")
    tuner = AutoTuner(engine="hnsw", policy=configured_policy, state=state)
    _persist_policy(tuner.policy_name)
    _persist_state(tuner, tuner.state)
    return tuner, tuner.state


def get_global_autotuner():
    """Return the process-wide AutoTuner and its backing state."""
    if _GLOBAL["tuner"] is None or _GLOBAL["state"] is None:
        tuner, state = _create_autotuner()
        _GLOBAL.update({"tuner": tuner, "state": state})
    else:
        _maybe_autosave(_GLOBAL["tuner"], _GLOBAL["state"])
    return _GLOBAL["tuner"], _GLOBAL["state"]


def _remove_state_file() -> None:
    try:
        if _STATE_FILE.exists():
            _STATE_FILE.unlink()
    except OSError:
        pass


def reset_global_autotuner(clear_file: bool = True):
    """Re-initialize the global AutoTuner and return the fresh pair."""
    if clear_file:
        _remove_state_file()
        _reset_summary()
        _GLOBAL["last_autosave"] = 0.0
    tuner, state = _create_autotuner()
    _GLOBAL.update({"tuner": tuner, "state": state})
    return tuner, state


def set_policy(name: str) -> Tuple[AutoTuner, TuningState]:
    """Re-create the global AutoTuner with the provided policy while keeping state."""
    _, state = get_global_autotuner()
    tuner, state = _create_autotuner(policy_name=name, state=state)
    _GLOBAL.update({"tuner": tuner, "state": state})
    return tuner, state


def _serialize_state(state) -> Dict[str, Any]:
    metrics = state.get_smoothed_metrics()
    arm = select_strategy(metrics)
    params = state.get_current_params()
    params.update(state.get_convergence_status())
    history = list(getattr(state, "parameter_history", []))
    metrics["arm"] = arm
    return {
        "params": params,
        "history_len": len(history),
        "parameter_history": history,
        "metrics": metrics,
        "arm": arm,
    }


def persist_state_snapshot(tuner: AutoTuner, state: TuningState) -> None:
    """Persist current autotuner state to disk."""
    _maybe_autosave(tuner, state, force=True)


def clear_autotuner_state() -> None:
    """Clear persisted state without recreating the tuner."""
    _remove_state_file()
    _reset_summary()
    _GLOBAL["last_autosave"] = 0.0


def get_state_summary() -> Dict[str, Any]:
    tuner, state = get_global_autotuner()
    history_len, last_params = _update_summary(state)
    return {
        "history_len": history_len,
        "last_params": last_params,
        "file_mtime": _state_file_mtime_iso(),
        "last_autosave": _GLOBAL.get("last_autosave", 0.0),
        "policy": getattr(tuner, "policy_name", None),
    }

