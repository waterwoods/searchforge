"""JSON-safe serialization helpers for graph/SSE payloads."""

from __future__ import annotations


def json_safe(value: object, _seen: set[int] | None = None) -> object:
    """
    Convert arbitrary Python objects into JSON-serializable structures while
    preventing circular references.
    """
    if _seen is None:
        _seen = set()

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    obj_id = id(value)
    if obj_id in _seen:
        return "[Circular]"
    _seen.add(obj_id)

    if isinstance(value, dict):
        out: dict[str, object] = {}
        for k, v in value.items():
            key = k if isinstance(k, str) else str(k)
            out[key] = json_safe(v, _seen)
        return out

    if isinstance(value, (list, tuple, set)):
        return [json_safe(v, _seen) for v in value]

    try:
        import numpy as _np  # type: ignore

        if isinstance(value, (_np.generic,)):
            return value.item()
    except Exception:
        pass

    try:
        maybe_id = getattr(value, "id", None)
        if isinstance(maybe_id, (str, int)):
            return str(maybe_id)
    except Exception:
        pass

    return str(value)
