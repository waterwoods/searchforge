#!/usr/bin/env python3
"""
P16 Phase 1 — Customer First Screen simulations (Li Hua persona).

Run: PYTHONPATH=. python3 scripts/run_p16_customer_first_screen_simulations.py
Requires API on localhost:8001 (or BASE_URL).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8001").rstrip("/")
INTAKE_API_KEY = os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY", "").strip()
if not INTAKE_API_KEY:
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env.cloudrun")
    if os.path.isfile(env_file):
        with open(env_file, encoding="utf-8") as f:
            for line in f:
                if line.startswith("UNIFIED_INTAKE_INTAKE_API_KEY="):
                    INTAKE_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
LI_HUA_PHONE = "6265550199"
LI_HUA_WRONG_PHONE = "6265550198"
LI_HUA_NAME = "李华"
SIM1_PHONE = "6265550101"
SIM2_PHONE = "6265550102"
SIM4_PHONE = "6265550104"


def _req(method: str, path: str, body: dict | None = None) -> tuple[int, Any]:
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers: dict[str, str] = {}
    if data:
        headers["Content-Type"] = "application/json"
    if INTAKE_API_KEY:
        headers["X-Unified-Intake-Api-Key"] = INTAKE_API_KEY
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"detail": raw}


def _delete_test_cases_for_phone(phone: str) -> None:
    status, data = _req("GET", "/api/inbox/cases?limit=50&offset=0")
    if status != 200:
        return
    for c in data.get("cases") or []:
        if str(c.get("customer_phone") or "").replace("-", "")[-10:] == phone[-10:]:
            cid = c.get("case_id")
            if cid:
                _req("PATCH", f"/api/inbox/cases/{cid}/workbench", {"is_test": True})
                _req("DELETE", f"/api/inbox/cases/{cid}")


def sim1_new_customer() -> dict[str, Any]:
    """Li Hua new customer → Scenario A (no active case)."""
    q = urllib.parse.urlencode({"phone": SIM1_PHONE})
    status, data = _req("GET", f"/api/inbox/customer/active-case?{q}")
    return {
        "simulation": 1,
        "name": "Li Hua — new customer",
        "expected": "Scenario A — no active case",
        "http_status": status,
        "has_active_case": data.get("has_active_case") if isinstance(data, dict) else None,
        "pass": status == 200 and isinstance(data, dict) and data.get("has_active_case") is False,
    }


def sim2_returning_customer() -> dict[str, Any]:
    """Li Hua returns — Tesla active, missing VIN → Scenario B."""
    seed_body = {
        "phone": SIM2_PHONE,
        "customer_name": LI_HUA_NAME,
    }
    st, seeded = _req("POST", "/api/inbox/customer/start-add-car", seed_body)
    if st not in (200, 409):
        return {"simulation": 2, "name": "Li Hua returns", "pass": False, "error": "seed failed", "seed_status": st}
    q = urllib.parse.urlencode({"phone": SIM2_PHONE})
    status, data = _req("GET", f"/api/inbox/customer/active-case?{q}")
    active = (data or {}).get("active_case") if isinstance(data, dict) else None
    return {
        "simulation": 2,
        "name": "Li Hua returns — Tesla active, missing VIN",
        "expected": "Scenario B — active case with missing fields",
        "http_status": status,
        "has_active_case": (data or {}).get("has_active_case"),
        "missing_fields": (active or {}).get("missing_fields"),
        "submit_state": (active or {}).get("submit_state"),
        "pass": (
            status == 200
            and isinstance(data, dict)
            and data.get("has_active_case") is True
            and (active or {}).get("submit_state") == "not_yet"
        ),
    }


def sim3_wrong_phone() -> dict[str, Any]:
    """Wrong phone — empty lookup; documents wrong-key risk."""
    q = urllib.parse.urlencode({"phone": LI_HUA_WRONG_PHONE})
    status, data = _req("GET", f"/api/inbox/customer/active-case?{q}")
    return {
        "simulation": 3,
        "name": "Li Hua wrong phone digit",
        "expected": "No match — customer may start duplicate (risk documented)",
        "http_status": status,
        "has_active_case": (data or {}).get("has_active_case") if isinstance(data, dict) else None,
        "risk": "Customer enters wrong phone → cannot find Tesla case → may create second matter if broker has not closed first",
        "pass": status == 200 and isinstance(data, dict) and data.get("has_active_case") is False,
    }


def sim4_second_vehicle_blocked() -> dict[str, Any]:
    """Active case exists — second start-add-car rejected (Rule 7)."""
    _req("POST", "/api/inbox/customer/start-add-car", {"phone": SIM4_PHONE, "customer_name": LI_HUA_NAME})
    status, data = _req(
        "POST",
        "/api/inbox/customer/start-add-car",
        {"phone": SIM4_PHONE, "customer_name": LI_HUA_NAME},
    )
    detail = (data or {}).get("detail") if isinstance(data, dict) else None
    return {
        "simulation": 4,
        "name": "Li Hua — second vehicle while active",
        "expected": "409 active_case_exists — Contact Broker path",
        "http_status": status,
        "detail": detail,
        "pass": status == 409,
    }


def main() -> int:
    print(f"P16 Customer First Screen simulations @ {BASE}\n")
    results = [sim1_new_customer(), sim2_returning_customer(), sim3_wrong_phone(), sim4_second_vehicle_blocked()]
    passed = 0
    for r in results:
        ok = r.get("pass")
        passed += 1 if ok else 0
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] Sim {r['simulation']}: {r['name']}")
        for k, v in r.items():
            if k not in ("simulation", "name", "pass"):
                print(f"       {k}: {v}")
        print()
    print(f"Summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
