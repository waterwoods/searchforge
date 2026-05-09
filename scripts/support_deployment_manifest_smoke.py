#!/usr/bin/env python3
"""Smoke-check support deployment-manifest + health deployment truth (optional running server).

Uses UNIFIED_INTAKE_SUPPORT_API_KEY from the environment when set (must match server).

Usage:
  PYTHONPATH=. python3 scripts/support_deployment_manifest_smoke.py
  PYTHONPATH=. python3 scripts/support_deployment_manifest_smoke.py --url http://127.0.0.1:8001
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _get(url: str, headers: dict[str, str]) -> tuple[int, dict]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            return e.code, {"_raw": raw}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--url",
        default=os.getenv("SUPPORT_SMOKE_BASE_URL", "http://127.0.0.1:8001"),
        help="API base URL (default 8001 demo port)",
    )
    args = p.parse_args()
    base = args.url.rstrip("/")
    key = (os.getenv("UNIFIED_INTAKE_SUPPORT_API_KEY") or "").strip()
    headers = {}
    if key:
        headers["X-Unified-Intake-Support-Key"] = key

    h_status, health = _get(f"{base}/health", {})
    if h_status != 200:
        print(f"FAIL /health -> {h_status}", file=sys.stderr)
        print(json.dumps(health, indent=2), file=sys.stderr)
        return 1
    dp = health.get("deployment_profile") or {}
    if not isinstance(dp, dict):
        print("FAIL deployment_profile missing on /health", file=sys.stderr)
        return 1
    hints = dp.get("operator_runtime_hints")
    if not isinstance(hints, dict):
        print("FAIL operator_runtime_hints missing on /health", file=sys.stderr)
        return 1
    if not isinstance(hints.get("operator_warnings"), list):
        print("FAIL operator_warnings missing or not a list on /health", file=sys.stderr)
        return 1
    persist = health.get("unified_intake_case_persistence")
    if not isinstance(persist, dict):
        print("WARN unified_intake_case_persistence missing (non-fatal)", file=sys.stderr)

    m_status, manifest = _get(f"{base}/api/inbox/support/deployment-manifest", headers)
    if m_status == 401 and not key:
        print(
            "SKIP deployment-manifest returned 401 — server requires UNIFIED_INTAKE_SUPPORT_API_KEY "
            "(set env and re-run)",
            file=sys.stderr,
        )
        print("OK /health deployment_profile + persistence truth")
        return 0
    if m_status != 200:
        print(f"FAIL deployment-manifest -> {m_status}", file=sys.stderr)
        print(json.dumps(manifest, indent=2), file=sys.stderr)
        return 1
    if not manifest.get("ok"):
        print("FAIL deployment-manifest ok=false", file=sys.stderr)
        return 1
    mh = manifest.get("operator_runtime_hints")
    if not isinstance(mh, dict):
        print("FAIL operator_runtime_hints missing on manifest", file=sys.stderr)
        return 1
    if not isinstance(mh.get("operator_warnings"), list):
        print("FAIL operator_warnings missing or not a list on manifest", file=sys.stderr)
        return 1

    print("OK support_deployment_manifest_smoke")
    print(json.dumps({"health_hints": hints, "manifest_git": manifest.get("git")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
