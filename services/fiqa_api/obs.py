from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set

import io as py_io
import json
import logging

# mvp-5

_client_lock = threading.Lock()
_client: Optional["Langfuse"] = None
logger = logging.getLogger(__name__)

_REDACTION_KEYS: Set[str] = {"api_key", "authorization", "input_text", "raw_prompt"}
_REDACTED_VALUE = "[REDACTED]"
_DEFAULT_MAX_LEN = 256


class SpanGuard:
    __slots__ = ("span", "ctx", "metadata", "output", "error", "active")

    def __init__(self, span: Any, ctx: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        self.span = span
        self.ctx = ctx
        self.metadata = metadata or {}
        self.output: Optional[Any] = None
        self.error: Optional[str] = None
        self.active = span is not None

    def set_output(self, value: Optional[Dict[str, Any]]) -> None:
        if not self.active:
            return
        self.output = redact(value)

    def add_metadata(self, updates: Optional[Dict[str, Any]]) -> None:
        if not self.active or not updates:
            return
        clean = redact(updates)
        if isinstance(clean, dict):
            self.metadata.update(clean)


def _enabled() -> bool:
    return os.getenv("OBS_ENABLED", "0") == "1" and bool(os.getenv("LANGFUSE_SECRET_KEY"))


def _get_client():
    global _client
    if not _enabled():
        return None

    if _client is None:
        with _client_lock:
            if _client is None:
                from langfuse import Langfuse

                _client = Langfuse(
                    host=os.getenv("LANGFUSE_HOST"),
                    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                    timeout_ms=int(os.getenv("OBS_TIMEOUT_MS", "200")),
                )
    return _client


def build_obs_url(job_id: Optional[str]) -> str:
    if not job_id:
        return ""
    host = (os.getenv("LANGFUSE_HOST") or "https://cloud.langfuse.com").rstrip("/")
    return f"{host}/traces?query={job_id}"


def trace_start(
    trace_id: str,
    name: str,
    input: Dict[str, Any] | None = None,
    metadata: Dict[str, Any] | None = None,
    *,
    force_sample: bool = False,
):
    try:
        if not _enabled():
            return None

        if not force_sample:
            sample_rate = float(os.getenv("OBS_SAMPLE_RATE", "1"))
            if sample_rate < 1.0:
                import random

                if random.random() > sample_rate:
                    return None

        client = _get_client()
        if not client:
            return None

        clean_input = redact(input or {})
        clean_metadata = redact(metadata or {})

        return client.trace(
            id=trace_id,
            name=name,
            input=clean_input or {},
            metadata=clean_metadata or None,
        )
    except Exception:
        return None


def trace_end(trace, output: Dict[str, Any] | None = None, scores: Dict[str, float] | None = None):
    try:
        if not trace:
            return

        payload: Dict[str, Any] = {}
        if output is not None:
            safe_output = redact(output)
            payload["output"] = safe_output

        if payload:
            trace.update(**payload)

        if scores:
            for key, value in scores.items():
                try:
                    trace.score(name=key, value=float(value))
                except Exception:
                    continue

        trace.end()
    except Exception:
        pass


def _truncate_text(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + "..."


def _redact(obj: Any, sensitive: Set[str], max_len: int) -> Any:
    if obj is None:
        return None

    if isinstance(obj, dict):
        cleaned: Dict[Any, Any] = {}
        for key, value in obj.items():
            lowered = key.lower() if isinstance(key, str) else None
            if lowered and lowered in sensitive:
                cleaned[key] = _REDACTED_VALUE
            else:
                cleaned[key] = _redact(value, sensitive, max_len)
        return cleaned

    if isinstance(obj, list):
        return [_redact(item, sensitive, max_len) for item in obj]

    if isinstance(obj, tuple):
        return tuple(_redact(item, sensitive, max_len) for item in obj)

    if isinstance(obj, set):
        return {_redact(item, sensitive, max_len) for item in obj}

    if isinstance(obj, str):
        return _truncate_text(obj, max_len)

    return obj


def redact(
    obj: Any,
    keys: Iterable[str] | None = None,
    *,
    max_len: int = _DEFAULT_MAX_LEN,
) -> Any:
    try:
        sensitive = {k.lower() for k in (keys or _REDACTION_KEYS)}
        return _redact(obj, sensitive, max_len)
    except Exception:
        return obj


@contextmanager
def span(
    ctx: Optional[Dict[str, Any]],
    name: str,
    attrs: Optional[Dict[str, Any]] = None,
    input: Optional[Dict[str, Any]] = None,
):
    if not ctx:
        yield SpanGuard(None, {}, {})
        return

    parent = ctx.get("span") or ctx.get("trace")
    safe_metadata = redact(attrs or {})
    safe_input = redact(input or {})
    span_obj = None
    try:
        if parent is not None:
            span_obj = parent.span(
                name=name,
                input=safe_input or {},
                metadata=safe_metadata or None,
            )
    except Exception:
        span_obj = None

    guard = SpanGuard(span_obj, ctx, safe_metadata or {})

    try:
        yield guard
    except Exception as exc:
        guard.error = str(exc)
        if guard.active:
            try:
                guard.metadata.setdefault("status", "error")
                guard.metadata["error"] = _truncate_text(guard.error, _DEFAULT_MAX_LEN)
                guard.span.update(metadata=guard.metadata)
            except Exception:
                pass
            try:
                guard.span.log(level="error", message=str(exc))
            except Exception:
                pass
        raise
    finally:
        if guard.active:
            try:
                payload: Dict[str, Any] = {}
                if guard.metadata:
                    payload["metadata"] = guard.metadata
                if guard.output is not None:
                    payload["output"] = guard.output
                if payload:
                    guard.span.update(**payload)
            except Exception:
                pass
            try:
                guard.span.end()
            except Exception:
                pass


def _runs_dir() -> Path:
    path = Path(".runs")
    path.mkdir(parents=True, exist_ok=True)
    return path


def persist_trace_id(job_or_trace: Optional[str], trace_id: Optional[str] = None) -> None:
    if trace_id is None:
        trace_id = job_or_trace
    if not trace_id:
        return
    try:
        (_runs_dir() / "trace_id.txt").write_text(f"{trace_id}\n", encoding="utf-8")
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("failed to persist trace_id.txt: %s", exc)


def append_trace(obs_url: Optional[str], limit: int = 200) -> None:
    """
    Append trace URL to obs_url.txt with rolling limit.
    
    If file exceeds limit lines, keeps only the latest limit lines (atomic write).
    """
    if not obs_url:
        return
    try:
        runs_dir = _runs_dir()
        obs_file = runs_dir / "obs_url.txt"
        timestamp = datetime.now(timezone.utc).isoformat()
        value = obs_url.strip()
        line = f"{timestamp} {value}\n"
        
        # Read existing lines
        lines = []
        if obs_file.exists():
            try:
                lines = obs_file.read_text(encoding="utf-8").splitlines()
            except Exception:
                lines = []
        
        # Append new line
        lines.append(line.rstrip())
        
        # Keep only latest `limit` lines
        if len(lines) > limit:
            lines = lines[-limit:]
        
        # Atomic write (write to temp then replace)
        tmp_file = obs_file.with_suffix(".tmp")
        tmp_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        tmp_file.replace(obs_file)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("failed to append trace to obs_url.txt: %s", exc)


def persist_obs_url(obs_url: Optional[str]) -> None:
    """Backward-compatible wrapper for append_trace."""
    append_trace(obs_url, limit=200)


def finalize_root(*args, **kwargs) -> Dict[str, Any] | None:
    """
    Backward-compatible finalize helper.

    - Existing callers may pass (ctx: dict, meta: dict)
    - New usage can pass keyword arguments (job_id=..., trace_id=..., trace_url=..., plan=..., decision=...)
    """
    if args and isinstance(args[0], dict):
        ctx: Dict[str, Any] = args[0] or {}
        meta: Optional[Dict[str, Any]] = args[1] if len(args) > 1 else None
        if meta:
            ctx.setdefault("metadata", {}).update(meta)

        trace_id = ctx.get("trace_id")
        if trace_id and not isinstance(trace_id, str):
            trace_id = str(trace_id)

        if not trace_id:
            root = ctx.get("trace") or ctx.get("span")
            if root is not None:
                trace_id = getattr(root, "id", None) or getattr(root, "trace_id", None)
                if trace_id and not isinstance(trace_id, str):
                    trace_id = str(trace_id)
                if trace_id:
                    ctx["trace_id"] = trace_id
        job_id = ctx.get("job_id")
        if not trace_id and isinstance(job_id, str):
            trace_id = job_id
            ctx["trace_id"] = trace_id

        trace_url = ""
        if isinstance(ctx.get("trace_url"), str) and ctx["trace_url"]:
            trace_url = ctx["trace_url"]
        else:
            trace_url = build_obs_url(trace_id)

        if trace_url:
            ctx["trace_url"] = trace_url
        try:
            if trace_id:
                persist_trace_id(trace_id)
            persist_obs_url(trace_url)
        except Exception:
            pass
        return ctx

    job_id = kwargs.get("job_id") or ""
    trace_id = kwargs.get("trace_id") or job_id or ""
    trace_url = kwargs.get("trace_url") or build_obs_url(trace_id)
    payload = {
        "job_id": job_id,
        "plan": kwargs.get("plan") or "",
        "decision": kwargs.get("decision") or "",
        "trace_id": trace_id,
        "trace_url": trace_url,
    }
    if kwargs.get("metrics") is not None:
        payload["metrics"] = kwargs["metrics"]
    try:
        if trace_id:
            persist_trace_id(job_id or trace_id, trace_id=trace_id)
        persist_obs_url(trace_url or "")
        buffer = py_io.StringIO()
        json.dump(payload, buffer, ensure_ascii=False)
        (_runs_dir() / "finalize.json").write_text(buffer.getvalue(), encoding="utf-8")
    except Exception:
        pass
    return payload


def io(span_or_ctx: Any, *, input: Any = None, output: Any = None) -> None:
    """Safe helper for recording span I/O without raising."""
    try:
        guard = span_or_ctx
        if guard is None:
            return
        if input is not None:
            data = {"input": redact(input)}
            if hasattr(guard, "add_metadata"):
                guard.add_metadata(data)
            elif isinstance(guard, dict):
                guard.setdefault("metadata", {}).update(data)
        if output is not None:
            if hasattr(guard, "set_output"):
                guard.set_output(output if isinstance(output, dict) else {"value": output})
            elif isinstance(guard, dict):
                guard["output"] = redact(output)
    except Exception:
        pass
