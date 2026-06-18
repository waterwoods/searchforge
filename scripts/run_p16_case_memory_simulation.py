#!/usr/bin/env python3
"""
P16 Case Memory Persistence — end-to-end simulation battery (A–D).

Requires API on BASE_URL (default http://127.0.0.1:8001).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

BASE = os.environ.get("CASE_MEMORY_SIM_BASE", "http://127.0.0.1:8001").rstrip("/")
CLIENT = "p16_case_memory_sim"
INTAKE_API_KEY = os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY", "").strip()
if not INTAKE_API_KEY:
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env.cloudrun")
    if os.path.isfile(env_file):
        with open(env_file, encoding="utf-8") as f:
            for line in f:
                if line.startswith("UNIFIED_INTAKE_INTAKE_API_KEY="):
                    INTAKE_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break


def _req(method: str, path: str, body: dict | None = None) -> dict[str, Any]:
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers: dict[str, str] = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if INTAKE_API_KEY:
        headers["X-Unified-Intake-Api-Key"] = INTAKE_API_KEY
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        raise RuntimeError(f"{method} {path} -> {e.code}: {detail}") from e


def _triage(text: str, *, case_id: str | None = None, turns: list | None = None) -> dict:
    payload: dict[str, Any] = {
        "text": text,
        "persist_case": True,
        "client_id": CLIENT,
        "conversation_turns": turns or [],
    }
    if case_id:
        payload["case_id"] = case_id
    return _req("POST", "/api/inbox/triage", payload)


def _delete_cases_for_phone(phone: str) -> None:
    try:
        out = _req("GET", "/api/inbox/cases?limit=50&offset=0")
    except RuntimeError:
        return
    tail = phone.replace("-", "")[-10:]
    for c in out.get("cases") or []:
        cp = str(c.get("customer_phone") or "").replace("-", "")[-10:]
        if cp == tail:
            cid = c.get("case_id")
            if cid:
                try:
                    _req("PATCH", f"/api/inbox/cases/{cid}/workbench", {"is_test": True})
                    _req("DELETE", f"/api/inbox/cases/{cid}")
                except RuntimeError:
                    pass


def _start_draft(phone: str) -> str:
    _delete_cases_for_phone(phone)
    out = _req(
        "POST",
        "/api/inbox/customer/start-add-car",
        {"phone": phone, "client_id": CLIENT},
    )
    return str(out["case_id"])


def _active_case(phone: str) -> dict | None:
    import urllib.parse

    q = urllib.parse.urlencode({"phone": phone, "client_id": CLIENT})
    out = _req("GET", f"/api/inbox/customer/active-case?{q}")
    return out.get("active_case")


def _get_case(case_id: str) -> dict:
    return _req("GET", f"/api/inbox/cases/{case_id}")


def _customer_texts(case: dict) -> list[str]:
    msgs = case.get("case_messages") or []
    return [str(m.get("text") or "") for m in msgs if m.get("role") == "customer"]


def _assert_order(texts: list[str], expected: list[str], label: str) -> None:
    indices = []
    for exp in expected:
        try:
            indices.append(texts.index(exp))
        except ValueError:
            raise AssertionError(f"{label}: missing message {exp!r} in {texts!r}")
    for i in range(1, len(indices)):
        if indices[i] <= indices[i - 1]:
            raise AssertionError(f"{label}: order wrong for {expected!r} in {texts!r}")


def sim_a() -> None:
    phone = "6265553001"
    print(f"\n=== Simulation A — phone {phone} ===")
    case_id = _start_draft(phone)
    turns: list[dict] = []
    for msg in ["I bought a BMW X5", "2027", "ZIP 92620"]:
        _triage(msg, case_id=case_id, turns=turns)
        turns.append({"role": "customer", "text": msg})
    case = _get_case(case_id)
    texts = _customer_texts(case)
    _assert_order(texts, ["I bought a BMW X5", "2027", "ZIP 92620"], "A persist")
    active = _active_case(phone)
    assert active and active.get("case_id") == case_id, "A: active case missing"
    # Simulate return: fresh read
    reloaded = _get_case(case_id)
    reloaded_texts = _customer_texts(reloaded)
    _assert_order(reloaded_texts, ["I bought a BMW X5", "2027", "ZIP 92620"], "A reload")
    print("PASS Simulation A")


def sim_b() -> None:
    phone = "6265553002"
    print(f"\n=== Simulation B — phone {phone} (refresh) ===")
    case_id = _start_draft(phone)
    _triage("Tesla Model Y", case_id=case_id)
    case = _get_case(case_id)
    assert "Tesla Model Y" in _customer_texts(case), "B: message not persisted"
    assert _active_case(phone), "B: active case missing"
    reloaded = _get_case(case_id)
    assert "Tesla Model Y" in _customer_texts(reloaded), "B: reload lost message"
    print("PASS Simulation B")


def sim_c() -> None:
    phone = "6265553003"
    print(f"\n=== Simulation C — phone {phone} (new tab) ===")
    case_id = _start_draft(phone)
    _triage("Honda Accord 2024", case_id=case_id)
    active = _active_case(phone)
    assert active and active.get("case_id") == case_id
    reloaded = _get_case(active["case_id"])
    assert "Honda Accord 2024" in _customer_texts(reloaded)
    print("PASS Simulation C")


def sim_d() -> None:
    phone = "6265553004"
    print(f"\n=== Simulation D — phone {phone} (timeline order) ===")
    case_id = _start_draft(phone)
    turns: list[dict] = []
    supplements = [
        "First: Lexus RX 350",
        "Second: model year 2025",
        "Third: ZIP 90210",
        "Fourth: delivery next Monday, I am the primary driver",
    ]
    for msg in supplements:
        _triage(msg, case_id=case_id, turns=turns)
        turns.append({"role": "customer", "text": msg})
    case = _get_case(case_id)
    texts = _customer_texts(case)
    _assert_order(texts, supplements, "D timeline")
    print("PASS Simulation D")


def main() -> int:
    print(f"Case Memory simulation against {BASE}")
    try:
        health = _req("GET", "/health")
        print(f"Health: {health.get('status', health)}")
    except Exception as e:
        print(f"API not reachable at {BASE}: {e}", file=sys.stderr)
        return 1
    sim_a()
    sim_b()
    sim_c()
    sim_d()
    print("\nAll simulations PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
