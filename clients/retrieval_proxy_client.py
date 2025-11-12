import os
import uuid
from typing import Any, Dict, Optional

import requests

DEFAULT_BASE = "http://retrieval-proxy:7070"

BASE_URL = os.getenv("RETRIEVAL_PROXY_URL", DEFAULT_BASE)
USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"


def _legacy_search(query: str, k: int) -> Dict[str, Any]:
    from services.fiqa_api.services.search_core import perform_search

    return perform_search(query=query, top_k=k)


def search(
    query: str,
    k: int,
    budget_ms: int,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    if not USE_PROXY:
        return _legacy_search(query, k)

    trace = trace_id or str(uuid.uuid4())
    timeout = (2, max(0.5, budget_ms / 1000.0 + 0.5))

    try:
        response = requests.get(
            f"{BASE_URL}/v1/search",
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
        payload.setdefault("trace_id", trace)
        return payload
    except Exception:
        return _legacy_search(query, k)


__all__ = ["search", "USE_PROXY", "BASE_URL"]

