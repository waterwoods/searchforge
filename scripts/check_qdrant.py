#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict

import requests


def env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def main() -> None:
    base_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection = os.getenv("COLLECTION", "fiqa_50k_v1")
    vector_dim = env_int("VECTOR_DIM", env_int("QDRANT_VECTOR_DIM", 384))

    session = requests.Session()

    detail_resp = session.get(f"{base_url}/collections/{collection}", timeout=5)
    if detail_resp.status_code != 200:
        detail_resp.raise_for_status()

    detail = detail_resp.json().get("result") or {}
    points_count = detail.get("points_count")
    vectors_config = detail.get("config", {}).get("params", {}).get("vectors", {})
    size = vectors_config.get("size", vector_dim)

    start = time.perf_counter()
    search_resp = session.post(
        f"{base_url}/collections/{collection}/points/search",
        json={"vector": [0.0] * int(size), "limit": 1},
        timeout=10,
    )
    latency_ms = (time.perf_counter() - start) * 1000
    if search_resp.status_code != 200:
        search_resp.raise_for_status()
    search_result = search_resp.json().get("result") or []

    summary: Dict[str, Any] = {
        "collection": collection,
        "vector_dim": size,
        "points": points_count,
        "hits": len(search_result),
        "search_latency_ms": round(latency_ms, 2),
        "status": "ok",
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - CLI helper
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        raise SystemExit(1)

