#!/usr/bin/env python3
import json
import os
import time
import urllib.parse
import urllib.request


BASE = os.environ.get("RAG_API_URL", "http://localhost:8000").rstrip("/")


def _req(method: str, url: str, data=None):
    payload = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {"content-type": "application/json"} if data is not None else {}
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


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

