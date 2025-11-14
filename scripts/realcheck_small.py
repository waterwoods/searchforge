#!/usr/bin/env python3
"""
Lightweight real-traffic sampler for proxy ON/OFF comparison.
"""

import os
import time
import json
import uuid
import urllib.parse
import urllib.error
import urllib.request
import sys
import statistics
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.autotune.selector import select_strategy


def http_get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post_json(url, payload, headers=None, timeout=30):
    data = json.dumps(payload).encode("utf-8")
    req_headers = {"content-type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def p95(values_ms):
    if not values_ms:
        return None
    xs = sorted(values_ms)
    idx = int(round(0.95 * (len(xs) - 1)))
    idx = max(0, min(len(xs) - 1, idx))
    return xs[idx]


def run(mode, n=80, budget_ms=400, outfile=".runs/realcheck.json"):
    use_proxy = os.getenv("USE_PROXY", "false").lower() == "true"
    proxy_url = os.getenv("PROXY_URL", "http://localhost:7070")
    rag_api_url = os.getenv("RAG_API_URL", "http://localhost:8000")

    pool = [
        "what is inflation",
        "define gdp",
        "credit card interest",
        "mortgage rate today",
        "bitcoin price",
        "apple stock news",
        "bond yield meaning",
        "index fund vs etf",
        "how to hedge risk",
        "dividend yield",
        "federal reserve meeting",
        "unemployment rate",
        "recession indicator",
        "earnings surprise",
        "cash flow statement",
        "price to earnings",
        "gross margin",
        "revenue growth",
        "market cap",
        "option call vs put",
    ]

    lat_ms = []
    ok = degraded = 0
    last_trace = None

    if not use_proxy:
        time.sleep(3.0)
        warm_body = {"question": pool[0], "budget_ms": budget_ms}
        for attempt in range(3):
            try:
                http_post_json(
                    f"{rag_api_url}/api/query",
                    payload=warm_body,
                    headers={"X-Trace-Id": str(uuid.uuid4())},
                )
                break
            except Exception:
                time.sleep(1.0)

    for i in range(n):
        query = pool[i % len(pool)]
        trace_id = str(uuid.uuid4())
        t0 = time.perf_counter()

        try:
            if use_proxy:
                url = f"{proxy_url}/v1/search?q={urllib.parse.quote(query)}&budget_ms={budget_ms}"
                resp = http_get(url, headers={"X-Trace-Id": trace_id})
            else:
                body = {"question": query, "budget_ms": budget_ms}
                resp = None
                last_error = None
                for attempt in range(4):
                    try:
                        resp = http_post_json(
                            f"{rag_api_url}/api/query",
                            payload=body,
                            headers={"X-Trace-Id": trace_id},
                        )
                        break
                    except urllib.error.HTTPError as exc:
                        last_error = exc
                        if attempt < 3 and exc.code in {429, 500, 502, 503, 504}:
                            time.sleep(1.0)
                            continue
                        raise
                    except Exception as exc:
                        last_error = exc
                        if attempt < 3:
                            time.sleep(1.0)
                            continue
                        raise
                if resp is None:
                    raise last_error or RuntimeError("direct query failed without response")
            t1 = time.perf_counter()

            lat_ms.append((t1 - t0) * 1000.0)
            ok += 1

            if isinstance(resp, dict) and resp.get("degraded") is True:
                degraded += 1
            if isinstance(resp, dict) and resp.get("trace_url"):
                last_trace = resp["trace_url"]
        except Exception:
            lat_ms.append(10_000.0)

    payload = {
        "mode": mode,
        "n": n,
        "budget_ms": budget_ms,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "use_proxy_env": use_proxy,
        "p95_ms": p95(lat_ms),
        "p50_ms": statistics.median(lat_ms) if lat_ms else None,
        "mean_ms": (sum(lat_ms) / len(lat_ms)) if lat_ms else None,
        "success_rate": ok / n if n else 0.0,
        "degraded_rate": degraded / ok if ok else 0.0,
        "last_trace_url": last_trace,
        "samples": min(5, len(lat_ms)),
    }
    payload["arm"] = select_strategy(
        {
            "mode": mode,
            "p95_ms": payload["p95_ms"],
            "success_rate": payload["success_rate"],
            "degraded_rate": payload["degraded_rate"],
        }
    )

    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    with open(outfile, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    mode_arg = sys.argv[1] if len(sys.argv) > 1 else "proxy_on"
    n_arg = int(os.getenv("REALCHECK_N", "80"))
    budget_arg = int(os.getenv("REALCHECK_BUDGET_MS", "400"))
    outfile_arg = sys.argv[2] if len(sys.argv) > 2 else ".runs/realcheck.json"
    run(mode_arg, n=n_arg, budget_ms=budget_arg, outfile=outfile_arg)

