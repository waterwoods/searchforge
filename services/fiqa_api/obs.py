from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Optional, Set

_client_lock = threading.Lock()
_client: Optional["Langfuse"] = None

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
    if not job_id or not _enabled():
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

