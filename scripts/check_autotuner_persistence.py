#!/usr/bin/env python3
"""Smoke-check autotuner state persistence across rag-api restarts."""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional


ROOT = Path(__file__).resolve().parent.parent
BASE_URL = os.getenv("AUTOTUNER_BASE_URL", "http://localhost:8000")
RETRIES = int(os.getenv("AUTOTUNER_CHECK_RETRIES", "8"))
SLEEP_SEC = float(os.getenv("AUTOTUNER_CHECK_DELAY", "1.0"))


def _request(method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    last_exc: Optional[Exception] = None
    for _ in range(RETRIES):
        try:
            req = urllib.request.Request(
                BASE_URL + path,
                data=data,
                headers=headers,
                method=method,
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as exc:
            last_exc = exc
            time.sleep(SLEEP_SEC)
    raise RuntimeError(f"request failed: {method} {path}") from last_exc


def post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return _request("POST", path, payload)


def get(path: str) -> Dict[str, Any]:
    return _request("GET", path)


def main() -> int:
    post("/api/autotuner/reset", {})
    post("/api/autotuner/suggest", {"p95_ms": 15.0, "recall_at_10": 0.95, "coverage": 0.99})
    second = post("/api/autotuner/suggest", {"p95_ms": 13.5, "recall_at_10": 0.97, "coverage": 0.99})
    history_before = int(second.get("history_len", 0))
    if history_before <= 0:
        raise SystemExit("autotuner history_len did not increase after suggestions")

    subprocess.run(
        ["docker", "compose", "--env-file", ".env.current", "restart", "rag-api"],
        check=True,
        cwd=str(ROOT),
    )
    subprocess.run(["make", "wait-ready"], check=True, cwd=str(ROOT))

    status = get("/api/autotuner/status")
    history_after = int(status.get("history_len", 0))
    if history_after < history_before:
        raise SystemExit(
            f"autotuner history_len regressed after restart (before={history_before}, after={history_after})"
        )

    state = get("/api/autotuner/state")
    if int(state.get("history_len", 0)) < history_before:
        raise SystemExit("autotuner state endpoint lost history after restart")

    print("AUTOTUNER persistence check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

