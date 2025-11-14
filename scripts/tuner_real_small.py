#!/usr/bin/env python3
"""Small-sample real-traffic tuner validation."""

from __future__ import annotations

import argparse
import json
import os
import statistics as st
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
import requests

sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.autotune.selector import select_strategy

API_BASE = os.getenv("API_BASE", os.getenv("RAG_API_URL", "http://localhost:8000")) or "http://localhost:8000"
API_BASE = API_BASE.rstrip("/")
RAG_API = API_BASE
PROXY_URL = os.getenv("PROXY_URL", os.getenv("RETRIEVAL_PROXY_URL", "http://localhost:7070")).rstrip("/")
DEFAULT_QUERY = os.getenv("TUNER_QUERY", "what is fiqa?")
RETRY_STATUS = {429, 500, 502, 503, 504}

_SESSION = requests.Session()


def _backoff(attempt: int, base: float = 0.5, cap: float = 4.0) -> None:
    delay = min(cap, base * (2 ** attempt))
    time.sleep(delay)


def fetch_json(method: str, path: str, session: Optional[requests.Session] = None, max_attempts: int = 4, timeout: int = 15, **kwargs):
    sess = session or _SESSION
    url = f"{API_BASE}{path}"
    return fetch_json_url(method, url, session=sess, max_attempts=max_attempts, timeout=timeout, **kwargs)


def fetch_json_url(method: str, url: str, session: Optional[requests.Session] = None, max_attempts: int = 4, timeout: int = 15, **kwargs):
    sess = session or _SESSION
    for attempt in range(max_attempts):
        try:
            response = sess.request(method, url, timeout=timeout, **kwargs)
            if response.status_code in RETRY_STATUS and attempt < max_attempts - 1:
                _backoff(attempt)
                continue
            response.raise_for_status()
            return response.json()
        except (requests.ConnectionError, requests.Timeout):
            if attempt == max_attempts - 1:
                raise
            _backoff(attempt)


def wait_ready(session: Optional[requests.Session] = None) -> None:
    sess = session or _SESSION
    sess.get(f"{API_BASE}/healthz", timeout=15).raise_for_status()
    ready = fetch_json("GET", "/readyz", session=sess)
    if isinstance(ready, dict) and ready.get("clients_ready") is True:
        return
    for attempt in range(30):
        time.sleep(1.0)
        ready = fetch_json("GET", "/readyz", session=sess)
        if isinstance(ready, dict) and ready.get("clients_ready") is True:
            return
    raise RuntimeError("Backend not ready after waiting for /readyz")


def _extract_latency(payload: Dict[str, Any]) -> float:
    for key in ("p95_ms", "latency_ms", "latency"):
        if key in payload and payload[key] is not None:
            try:
                return float(payload[key])
            except (TypeError, ValueError):
                continue
    timings = payload.get("timings") or {}
    try:
        return float(timings.get("total_ms", 0.0))
    except (TypeError, ValueError):
        return 0.0


def _set_policy(policy_name: str) -> str:
    resp = fetch_json(
        "POST",
        "/api/autotuner/set_policy",
        json={"policy": policy_name},
    )
    policy = resp.get("policy")
    if not policy:
        raise RuntimeError(f"Failed to set policy '{policy_name}': {resp}")
    return policy


def _slugify_policy(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    return "".join(ch for ch in name.lower() if ch.isalnum() or ch in ("-", "_"))


def run_once(use_proxy: bool, n: int, budget_ms: int, policy_name: Optional[str], policy_slug: Optional[str]) -> Dict[str, Any]:
    mode = "proxy_on" if use_proxy else "proxy_off"
    ef_hist, rr_hist, latencies = [], [], []
    success = 0
    arm_selected = "baseline"
    session = _SESSION

    for _ in range(n):
        trace_id = str(uuid.uuid4())
        params = {"q": DEFAULT_QUERY, "budget_ms": budget_ms, "k": 10}
        headers = {"X-Trace-Id": trace_id}

        if use_proxy:
            query_url = f"{PROXY_URL}/v1/search"
            resp = fetch_json_url("GET", query_url, params=params, headers=headers)
            items = resp.get("items") or resp.get("results") or []
            trace_url = resp.get("trace_url")
            if not items:
                # Fallback to direct query for evaluation purposes
                fallback = fetch_json_url("GET", f"{RAG_API}/api/query", params=params, headers=headers)
                items = fallback.get("items") or []
                trace_url = fallback.get("trace_url") or trace_url
                resp = fallback
        else:
            query_url = f"{RAG_API}/api/query"
            resp = fetch_json_url("GET", query_url, params=params, headers=headers)
            items = resp.get("items") or []
            trace_url = resp.get("trace_url")

        if items:
            success += 1

        latencies.append(_extract_latency(resp))

        metrics = {
            "p95_ms": float(latencies[-1] if latencies[-1] is not None else 0.0),
            "recall_at_10": 1.0 if items else 0.0,
            "coverage": 1.0,
            "trace_url": trace_url,
        }
        arm_selected = select_strategy(metrics)
        metrics["arm"] = arm_selected
        suggest_resp = fetch_json_url(
            "POST",
            f"{RAG_API}/api/autotuner/suggest",
            headers=headers,
            json=metrics,
        )
        params_snapshot = suggest_resp.get("next_params", {})
        ef_hist.append(params_snapshot.get("ef_search"))
        rr_hist.append(params_snapshot.get("rerank_k"))
        time.sleep(0.05)

    bounds_ok = all(4 <= (x or 0) <= 256 for x in ef_hist if x is not None) and \
                all(100 <= (y or 0) <= 1200 for y in rr_hist if y is not None)

    def _safe_sum(values):
        return sum(v for v in values if isinstance(v, (int, float)))

    stable_detune = False
    if len(ef_hist) >= 20:
        stable_detune = _safe_sum(ef_hist[-10:]) <= _safe_sum(ef_hist[:10])

    try:
        p95_sample = st.quantiles(latencies, n=20)[-1]
    except (ValueError, st.StatisticsError):
        p95_sample = latencies[-1] if latencies else None

    result = {
        "mode": mode,
        "n": n,
        "success_rate": success / n if n else 0.0,
        "p95_ms": p95_sample,
        "ef_search_hist": ef_hist,
        "rerank_hist": rr_hist,
        "bounds_ok": bounds_ok,
        "stable_detune": stable_detune,
        "arm": arm_selected,
        "policy": policy_name,
    }

    Path(".runs").mkdir(exist_ok=True)
    filename = f"tuner_{mode}.json"
    if policy_slug:
        filename = f"tuner_{mode}_{policy_slug}.json"
    (Path(".runs") / filename).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description="Run small-sample tuner validation.")
    parser.add_argument("--policy", type=str, help="Force AutoTuner policy before running.")
    args = parser.parse_args()

    wait_ready()

    policy_env = args.policy or os.getenv("POLICY") or os.getenv("TUNER_POLICY")
    policy_env = policy_env.strip() if policy_env else None
    policy_active = None
    policy_slug = None

    summary_name = "tuner_small_report.json"
    if policy_env:
        try:
            policy_active = _set_policy(policy_env)
        except Exception as exc:
            Path(".runs").mkdir(exist_ok=True)
            policy_slug = _slugify_policy(policy_env)
            failure = {
                "ok": False,
                "policy": policy_env,
                "error": str(exc),
            }
            filename = f"tuner_small_{policy_slug or 'unknown'}.json"
            (Path(".runs") / filename).write_text(json.dumps(failure, indent=2), encoding="utf-8")
            print(f"TUNER SMALL [{policy_env}] FAIL (set_policy): {exc}")
            return 1
        policy_slug = _slugify_policy(policy_active)
        summary_name = f"tuner_small_{policy_slug or 'unknown'}.json"

    n = int(os.getenv("N", os.getenv("TUNER_N", "80")))
    budget_ms = int(os.getenv("BUDGET_MS", "400"))

    try:
        on = run_once(True, n, budget_ms, policy_active, policy_slug)
        off = run_once(False, n, budget_ms, policy_active, policy_slug)
    except Exception as exc:
        Path(".runs").mkdir(exist_ok=True)
        failure = {
            "ok": False,
            "policy": policy_active,
            "error": str(exc),
        }
        (Path(".runs") / summary_name).write_text(json.dumps(failure, indent=2), encoding="utf-8")
        print(f"TUNER SMALL [{policy_active or 'default'}] FAIL: {exc}")
        return 1

    ok = on["bounds_ok"] and off["bounds_ok"] and on.get("stable_detune", False)
    report = {
        "ok": ok,
        "on": on,
        "off": off,
        "policy": policy_active,
        "bounds_ok": on["bounds_ok"] and off["bounds_ok"],
        "success_rate": min(on["success_rate"], off["success_rate"]),
        "stable_detune": on.get("stable_detune", False),
        "p95_ms": {"proxy_on": on.get("p95_ms"), "proxy_off": off.get("p95_ms")},
    }
    if policy_active:
        report["ok"] = report["bounds_ok"] and report["success_rate"] >= 0.95

    Path(".runs").mkdir(exist_ok=True)
    (Path(".runs") / summary_name).write_text(json.dumps(report, indent=2), encoding="utf-8")

    if policy_active:
        print(f"TUNER SMALL [{policy_active}] {'PASS' if report['ok'] else 'FAIL'}")
        return 0 if report["ok"] else 1

    print("TUNER SMALL PASS" if ok else "TUNER SMALL FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
