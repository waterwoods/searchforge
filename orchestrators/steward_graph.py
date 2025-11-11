from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from typing import Any, Callable, Dict, List, Optional, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph


RUNS_DIR = os.path.join(os.getcwd(), ".runs")
BLOB_DIR = os.path.join(RUNS_DIR, "blobs")
os.makedirs(RUNS_DIR, exist_ok=True)
os.makedirs(BLOB_DIR, exist_ok=True)


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

        keep = {k: v for k, v in state.items() if k in ("job_id", "dryrun_status", "errors")}
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


graph = StateGraph(GraphState)
graph.add_node("review", wrap("review", review))
graph.add_node("reflect", wrap("reflect", reflect))
graph.add_node("dryrun", wrap("dryrun", dryrun))

graph.set_entry_point("review")
graph.add_edge("review", "reflect")
graph.add_edge("reflect", "dryrun")
graph.add_conditional_edges("dryrun", dryrun_decider, {"ok": END, "fail": "review"})

app = graph.compile(checkpointer=_checkpointer)

