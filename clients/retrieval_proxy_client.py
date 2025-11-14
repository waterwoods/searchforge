import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

import requests

# mvp-5

DEFAULT_BASE = "http://retrieval-proxy:7070"
PROXY_URL = os.getenv("PROXY_URL") or os.getenv("RETRIEVAL_PROXY_URL", DEFAULT_BASE)
USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
DEFAULT_BUDGET_MS = int(os.getenv("DEFAULT_BUDGET_MS", "400"))


def _legacy_search(
    query: str,
    k: int,
    *,
    trace_id: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], bool, Optional[str]]:
    from services.fiqa_api.services.search_core import perform_search

    obs_ctx = {"trace_id": trace_id, "job_id": trace_id} if trace_id else None
    result = perform_search(query=query, top_k=k, obs_ctx=obs_ctx)
    timings: Dict[str, Any] = {
        "total_ms": result.get("latency_ms"),
        "per_source_ms": {},
        "cache_hit": False,
        "ret_code": "OK",
        "route": result.get("route"),
    }
    items: List[Dict[str, Any]] = list(result.get("results", []))
    degraded = bool(result.get("fallback"))
    return items, timings, degraded, None


def search(
    query: str,
    k: int,
    budget_ms: int,
    trace_id: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], bool, Optional[str]]:
    if not USE_PROXY:
        return _legacy_search(query, k, trace_id=trace_id)

    trace = trace_id or str(uuid.uuid4())
    timeout = (2, max(0.5, budget_ms / 1000.0 + 0.5))

    try:
        response = requests.get(
            f"{PROXY_URL}/v1/search",
            params={
                "q": query,
                "k": k,
                "budget_ms": budget_ms,
                "trace_id": trace,
            },
            headers={"X-Trace-Id": trace},
            timeout=timeout,
        )
        response.raise_for_status()
        payload: Dict[str, Any] = response.json()
        items = payload.get("items") or []
        timings = payload.get("timings") or {}
        timings.setdefault("ret_code", payload.get("ret_code"))
        timings.setdefault("total_ms", payload.get("timings", {}).get("total_ms"))
        degraded = bool(payload.get("degraded"))
        trace_url = payload.get("trace_url") or None
        return items, timings, degraded, trace_url
    except Exception:
        return _legacy_search(query, k, trace_id=trace)


__all__ = ["search", "USE_PROXY", "PROXY_URL", "DEFAULT_BUDGET_MS"]

