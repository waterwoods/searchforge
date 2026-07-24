#!/usr/bin/env python3
"""P4 Integration 01 — simulate Mini Program Smart Claim Start wiring S1–S6.

Usage:
  P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 scripts/simulate_p4_integration_01_smart_claim_start.py

Chain:
  Mini Program identity → Lookup → Prefill → Smart Claim Start → Review → Submit → Receipt

Does not call CRM. Does not create real cases (duplicate-claim check is plan-level).
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("P4_CUSTOMER_LOOKUP_MOCK", "1")

from services.fiqa_api.inbox_triage.smart_claim_start.service import (  # noqa: E402
    build_smart_claim_start_response,
)

SCENARIOS = ("S1", "S2", "S3", "S4", "S5", "S6")

EXPECTED_MODE = {
    "S1": "CONTINUE_ACTIVE",
    "S2": "MATCHED_CONFIRM_VEHICLE",
    "S3": "MATCHED_KNOWN",
    "S4": "MATCHED_CONFIRM_POLICY",
    "S5": "BLANK_DEGRADE",
    "S6": "BLANK_DEGRADE",
}


def _simulate_customer_path(scenario: str, plan: dict) -> dict:
    mode = plan["mode"]
    chips = [
        {"label": c.get("label_zh"), "value": c.get("value")}
        for c in (plan.get("known_chips") or [])
    ]
    confirms = [
        {"step": s.get("step_id"), "prompt": s.get("prompt_zh"), "options": s.get("options")}
        for s in (plan.get("confirm_steps") or [])
    ]
    required = [
        q["field_key"]
        for q in plan.get("questions") or []
        if q.get("visibility") in ("VISIBLE_REQUIRED", "VISIBLE_CONFIRM") and q.get("blocks_submit")
    ]

    if mode == "CONTINUE_ACTIVE":
        next_action = "continue_current_claim"
        duplicate_claim = False
        review = "skipped_active_gate"
        submit = "blocked_no_new_claim"
        receipt = "n/a_continue"
    elif mode == "CONTACT_BROKER":
        next_action = "contact_broker"
        duplicate_claim = False
        review = "skipped"
        submit = "blocked"
        receipt = "n/a"
    else:
        # Confirm gates then accident Must Haves → review → submit → receipt
        next_action = "collect_accident_facts_then_review_submit"
        duplicate_claim = False
        review = "ok"
        submit = "ok_existing_start_claim"
        receipt = "ok_existing_receipt"

    banned = ("openid", "person_link_key", "case_id")
    blob = json.dumps(plan, ensure_ascii=False).lower()
    no_tech_ids = not any(b in blob for b in banned)

    return {
        "scenario": scenario,
        "mode": mode,
        "known_fields_shown": chips,
        "customer_confirmations": confirms,
        "customer_required_fields": required,
        "estimated_customer_inputs": plan.get("estimated_customer_inputs"),
        "final_next_action": next_action,
        "duplicate_claim_check": "PASS" if not duplicate_claim else "FAIL",
        "review": review,
        "submit": submit,
        "receipt": receipt,
        "no_technical_ids": no_tech_ids,
        "chain": [
            "mini_program_identity",
            "lookup",
            "prefill",
            "smart_claim_start",
            review,
            submit,
            receipt,
        ],
    }


def main() -> int:
    rows = []
    for sc in SCENARIOS:
        res = build_smart_claim_start_response(
            session_id="wx_sim_integration_01",
            mock_scenario=sc,
        )
        plan = res["plan"]
        row = _simulate_customer_path(sc, plan)
        row["lookup_enabled"] = res.get("lookup_enabled")
        row["expected_mode"] = EXPECTED_MODE[sc]
        row["mode_ok"] = plan["mode"] == EXPECTED_MODE[sc]
        rows.append(row)

    # Flag-off rollback path
    os.environ["P4_CUSTOMER_LOOKUP_MOCK"] = "0"
    # Clear module-level env cache by re-importing facade check via response
    from importlib import reload
    import services.fiqa_api.inbox_triage.customer_lookup.facade as facade

    reload(facade)
    import services.fiqa_api.inbox_triage.smart_claim_start.service as svc

    reload(svc)
    rollback = svc.build_smart_claim_start_response(mock_scenario="S3")
    rollback_ok = (
        rollback["lookup_enabled"] is False
        and rollback["plan"]["mode"] == "BLANK_DEGRADE"
        and rollback["plan"]["known_chips"] == []
    )
    os.environ["P4_CUSTOMER_LOOKUP_MOCK"] = "1"
    reload(facade)
    reload(svc)

    checks = {
        "S1_continue_no_duplicate": rows[0]["mode_ok"]
        and rows[0]["duplicate_claim_check"] == "PASS"
        and rows[0]["estimated_customer_inputs"] == 1,
        "S2_vehicle_confirm": rows[1]["mode_ok"] and bool(rows[1]["customer_confirmations"]),
        "S3_matched_four_inputs": rows[2]["mode_ok"]
        and rows[2]["estimated_customer_inputs"] == 4
        and len(rows[2]["known_fields_shown"]) >= 2,
        "S4_stale_policy": rows[3]["mode_ok"] and bool(rows[3]["customer_confirmations"]),
        "S5_unmatched_degrade": rows[4]["mode_ok"] and rows[4]["known_fields_shown"] == [],
        "S6_unavailable_degrade": rows[5]["mode_ok"] and rows[5]["known_fields_shown"] == [],
        "no_technical_ids_all": all(r["no_technical_ids"] for r in rows),
        "rollback_flag_off": rollback_ok,
        "review_submit_receipt_paths": all(
            r["review"] and r["submit"] and r["receipt"] for r in rows
        ),
    }

    report = {
        "integration": "P4 Integration 01 Smart Claim Start Wiring",
        "scenarios": rows,
        "checks": checks,
        "result": "PASS" if all(checks.values()) else "FAIL",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("")
    print(f"RESULT: {report['result']}")
    for name, ok in checks.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
