#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

# Import HTTP utility with retry logic
sys.path.insert(0, str(Path(__file__).parent))
from _http_util import fetch_json, wait_ready

BASE = os.environ.get("RAG_API_URL", "http://localhost:8000").rstrip("/")


def _req(method: str, url: str, data=None):
    return fetch_json(url, method=method, json=data, timeout=15.0)


def items_len(obj):
    return len(obj.get("items", []))


def main():
    out = {}

    out["post_question"] = items_len(
        _req(
            "POST",
            f"{BASE}/api/query",
            {"question": "what is fiqa?", "budget_ms": 400},
        )
    )

    out["post_q"] = items_len(
        _req(
            "POST",
            f"{BASE}/api/query",
            {"q": "what is fiqa?", "budget_ms": 400},
        )
    )

    encoded = urllib.parse.quote("what is fiqa?")
    out["get_q"] = items_len(
        _req(
            "GET",
            f"{BASE}/api/query?q={encoded}&budget_ms=400",
        )
    )

    ok = all(v >= 1 for v in out.values())
    res = {"ok": ok, "counts": out, "ts": int(time.time())}

    os.makedirs(".runs", exist_ok=True)
    with open(".runs/direct_compat.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print(res)


if __name__ == "__main__":
    main()

