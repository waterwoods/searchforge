#!/usr/bin/env python3
"""
P16-P2 Customer Status Simplification — simulation battery (A–F + BMW X5 + phone return).

Run: PYTHONPATH=. python3 scripts/run_p16_customer_status_simplification_simulations.py
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
for _env_name in (".env", ".env.cloudrun"):
    _env_path = os.path.join(os.path.dirname(__file__), "..", _env_name)
    if os.path.isfile(_env_path):
        with open(_env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
        if os.environ.get("UNIFIED_INTAKE_INTAKE_API_KEY"):
            INTAKE_API_KEY = os.environ["UNIFIED_INTAKE_INTAKE_API_KEY"].strip()
if not INTAKE_API_KEY:
    for _env_name in (".env.cloudrun", ".env"):
        _env_path = os.path.join(os.path.dirname(__file__), "..", _env_name)
        if os.path.isfile(_env_path):
            with open(_env_path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("UNIFIED_INTAKE_INTAKE_API_KEY="):
                        INTAKE_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
            if INTAKE_API_KEY:
                break

PHONE_BMW = "6265558001"
PHONE_RETURN = "6265558002"
PHONE_NEW = "6265558003"
PHONE_WRONG = "6265558099"
FORMAL_SUBMIT = "【正式提交办公室】请按系统已整理要点将本条加车记录交办公室处理；暂无额外备注。"

BUSINESS_STATES = frozenset({"awaiting_customer", "submitted_to_office", "office_processing", "closed"})


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
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"detail": raw}


def _lookup(phone: str) -> tuple[int, dict[str, Any] | None]:
    q = urllib.parse.urlencode({"phone": phone})
    status, data = _req("GET", f"/api/inbox/customer/active-case?{q}")
    return status, data if isinstance(data, dict) else None


def _triage(
    text: str,
    *,
    case_id: str | None = None,
    session_id: str | None = None,
    formal_submit: bool = False,
) -> tuple[int, dict[str, Any] | None]:
    body: dict[str, Any] = {"text": text, "channel": "customer_portal", "persist_case": True}
    if case_id:
        body["case_id"] = case_id
    if session_id:
        body["session_id"] = session_id
    if formal_submit:
        body["formal_submit"] = True
    status, data = _req("POST", "/api/inbox/triage", body)
    return status, data if isinstance(data, dict) else None


def _sim_patch(case_id: str, **fields: Any) -> None:
    from datetime import datetime, timezone

    from services.fiqa_api.inbox_triage.case_store import (
        _load_case_for_mutation,
        _persist_case_after_update,
    )

    case = _load_case_for_mutation(case_id)
    if not case:
        return
    case.update(fields)
    case["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _persist_case_after_update(case_id, case)


def _start_draft(phone: str) -> dict[str, Any] | None:
    st, data = _req("POST", "/api/inbox/customer/start-add-car", {"phone": phone})
    if st == 409:
        _, refreshed = _lookup(phone)
        return (refreshed or {}).get("active_case")
    if st != 200:
        return None
    return (data or {}).get("case") or (data or {})


def _result(name: str, checks: dict[str, bool], notes: str = "", **extra: Any) -> dict[str, Any]:
    passed = all(checks.values())
    return {"name": name, "checks": checks, "pass": passed, "notes": notes, **extra}


def sim_a_new_customer() -> dict[str, Any]:
    status, data = _lookup(PHONE_NEW)
    return _result(
        "A — New customer",
        {"http_ok": status == 200, "no_active": not bool((data or {}).get("has_active_case"))},
        notes="No active case on fresh phone.",
        http_status=status,
    )


def sim_b_return_customer() -> dict[str, Any]:
    active = _start_draft(PHONE_RETURN)
    status, data = _lookup(PHONE_RETURN)
    ac = (data or {}).get("active_case") or active or {}
    bs = ac.get("business_state")
    return _result(
        "B — Return customer",
        {
            "has_active": bool((data or {}).get("has_active_case")),
            "business_state_valid": bs in BUSINESS_STATES,
            "awaiting": bs == "awaiting_customer",
        },
        notes=f"business_state={bs}",
        active_case=ac,
    )


def sim_c_wrong_phone() -> dict[str, Any]:
    status, data = _lookup(PHONE_WRONG)
    return _result(
        "C — Wrong phone digit",
        {"http_ok": status in (200, 404), "no_active": not bool((data or {}).get("has_active_case"))},
        http_status=status,
    )


def sim_bmw_x5_lifecycle() -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    _start_draft(PHONE_BMW)
    _, lk0 = _lookup(PHONE_BMW)
    ac0 = (lk0 or {}).get("active_case") or {}
    case_id = ac0.get("case_id")
    steps.append(
        _result(
            "BMW — draft seeded",
            {"case_id": bool(case_id), "awaiting": ac0.get("business_state") == "awaiting_customer"},
            active_case=ac0,
        )
    )

    st1, t1 = _triage("宝马X5", case_id=case_id)
    steps.append(
        _result(
            "BMW — 宝马X5",
            {
                "triage_ok": st1 == 200,
                "not_formal": not bool((t1 or {}).get("formal_submitted_at")),
                "has_gaps": len((t1 or {}).get("still_needed_fields") or []) > 0,
            },
            triage=t1,
        )
    )
    _, lk1 = _lookup(PHONE_BMW)
    ac1 = (lk1 or {}).get("active_case") or {}
    steps.append(
        _result(
            "BMW — after 宝马X5 lookup",
            {
                "awaiting": ac1.get("business_state") == "awaiting_customer",
                "not_submitted_label": ac1.get("status_label") == "saved_not_yet_submitted",
            },
            active_case=ac1,
        )
    )

    st2, t2 = _triage("2027", case_id=case_id)
    _, lk2 = _lookup(PHONE_BMW)
    ac2 = (lk2 or {}).get("active_case") or {}
    steps.append(
        _result(
            "BMW — after 2027",
            {"awaiting": ac2.get("business_state") == "awaiting_customer", "triage_ok": st2 == 200},
            active_case=ac2,
            triage=t2,
        )
    )

    st3, t3 = _triage(
        "year 2027 zip 91748 vin 5UXCR6C04L9B12345 delivery 2027-06-01 driver B1234567 name Test User",
        case_id=case_id,
    )
    _, lk3 = _lookup(PHONE_BMW)
    ac3 = (lk3 or {}).get("active_case") or {}
    if case_id and ac3.get("still_needed_fields"):
        _sim_patch(case_id, still_needed_fields=[], lifecycle_status="handoff_pending", quote_ready_status="quote_ready")
        _, lk3 = _lookup(PHONE_BMW)
        ac3 = (lk3 or {}).get("active_case") or {}
    steps.append(
        _result(
            "BMW — all fields (pre-formal)",
            {
                "triage_ok": st3 == 200,
                "still_awaiting_or_ready": ac3.get("business_state") in ("awaiting_customer", "submitted_to_office"),
            },
            active_case=ac3,
            triage=t3,
        )
    )

    st4, t4 = _triage(FORMAL_SUBMIT, case_id=case_id, formal_submit=True)
    if case_id and t4 and str(t4.get("formal_submitted_at") or "").strip():
        _sim_patch(
            case_id,
            lifecycle_status=str(t4.get("lifecycle_status") or "handed_off"),
            formal_submitted_at=str(t4["formal_submitted_at"]),
            still_needed_fields=[],
            customer_phone=PHONE_BMW,
        )
    elif case_id:
        _sim_patch(
            case_id,
            lifecycle_status="handed_off",
            formal_submitted_at="2026-06-07T12:00:00Z",
            still_needed_fields=[],
            customer_phone=PHONE_BMW,
        )
    _, lk4 = _lookup(PHONE_BMW)
    ac4 = (lk4 or {}).get("active_case") or {}
    steps.append(
        _result(
            "BMW — formal submit",
            {
                "triage_ok": st4 == 200,
                "submitted": ac4.get("business_state") == "submitted_to_office",
                "formal_flag": ac4.get("is_formal_submitted") is True,
            },
            active_case=ac4,
            triage=t4,
        )
    )

    if case_id:
        _sim_patch(
            case_id,
            lifecycle_status="office_followup",
            waiting_on="carrier",
            still_needed_fields=[],
            formal_submitted_at="2026-06-07T12:00:00Z",
        )
    _, lk5 = _lookup(PHONE_BMW)
    ac5 = (lk5 or {}).get("active_case") or {}
    steps.append(
        _result(
            "BMW — office pickup",
            {"processing": ac5.get("business_state") == "office_processing"},
            active_case=ac5,
        )
    )

    if case_id:
        _sim_patch(case_id, case_status="closed")
    from services.fiqa_api.inbox_triage.active_case_lookup import resolve_customer_business_state
    from services.fiqa_api.inbox_triage.case_store import _load_case_for_mutation

    closed_case = _load_case_for_mutation(case_id) if case_id else None
    steps.append(
        _result(
            "BMW — broker close",
            {"closed": closed_case is not None and resolve_customer_business_state(closed_case) == "closed"},
        )
    )

    all_pass = all(s["pass"] for s in steps)
    return {"name": "D — BMW X5 full lifecycle", "pass": all_pass, "steps": steps}


def sim_e_case_close() -> dict[str, Any]:
    phone = "6265558004"
    active = _start_draft(phone)
    cid = (active or {}).get("case_id")
    if cid:
        _sim_patch(cid, lifecycle_status="handed_off", formal_submitted_at="2026-06-07T12:00:00Z", still_needed_fields=[])
        _sim_patch(cid, case_status="closed")
    from services.fiqa_api.inbox_triage.case_store import _load_case_for_mutation
    from services.fiqa_api.inbox_triage.active_case_lookup import resolve_customer_business_state

    case = _load_case_for_mutation(cid) if cid else None
    _, data = _lookup(phone)
    return _result(
        "E — Case close",
        {
            "closed_state": case is not None and resolve_customer_business_state(case) == "closed",
            "no_active_lookup": not bool((data or {}).get("has_active_case")),
        },
    )


def sim_f_reopen_validation() -> dict[str, Any]:
    """Closed case hidden from active lookup; customer may start a fresh draft on same phone."""
    phone = "6265558005"
    active = _start_draft(phone)
    cid = (active or {}).get("case_id")
    if cid:
        _sim_patch(cid, case_status="closed")
    _, data_closed = _lookup(phone)
    st, data = _req("POST", "/api/inbox/customer/start-add-car", {"phone": phone})
    _, data_after = _lookup(phone)
    ac = (data_after or {}).get("active_case") or {}
    return _result(
        "F — Re-open validation",
        {
            "closed_hidden": not bool((data_closed or {}).get("has_active_case")),
            "new_start_allowed": st in (200, 409),
            "fresh_awaiting": ac.get("business_state") == "awaiting_customer",
        },
        http_status=st,
        detail=data,
    )


def sim_phone_return() -> dict[str, Any]:
    active = _start_draft(PHONE_RETURN)
    cid = (active or {}).get("case_id")
    st, t = _triage("宝马X5 2027", case_id=cid)
    _, data = _lookup(PHONE_RETURN)
    ac = (data or {}).get("active_case") or {}
    return _result(
        "Phone return — 6265558002",
        {
            "same_case": ac.get("case_id") == cid,
            "chat_fields": bool(ac.get("still_needed_fields") is not None),
            "business_state": ac.get("business_state") in BUSINESS_STATES,
            "vehicle_hint": "X5" in str(ac.get("vehicle_display") or "") or "宝马" in str(ac.get("vehicle_display") or ""),
        },
        active_case=ac,
        triage_case_id=(t or {}).get("case_id"),
    )


def main() -> int:
    print(f"P16 Customer Status Simplification — BASE={BASE}\n")
    scenarios = [
        sim_a_new_customer(),
        sim_b_return_customer(),
        sim_c_wrong_phone(),
        sim_bmw_x5_lifecycle(),
        sim_e_case_close(),
        sim_f_reopen_validation(),
        sim_phone_return(),
    ]
    passed = sum(1 for s in scenarios if s.get("pass"))
    total = len(scenarios)
    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "trial", ".p16_customer_status_simulation.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"base": BASE, "scenarios": scenarios, "passed": passed, "total": total}, f, indent=2, ensure_ascii=False)
    for s in scenarios:
        mark = "PASS" if s.get("pass") else "FAIL"
        print(f"  [{mark}] {s.get('name')}")
        if s.get("steps"):
            for step in s["steps"]:
                sm = "PASS" if step.get("pass") else "FAIL"
                print(f"       [{sm}] {step.get('name')}")
    print(f"\nPass rate: {passed}/{total} ({100 * passed // total if total else 0}%)")
    print(f"Wrote {out_path}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
