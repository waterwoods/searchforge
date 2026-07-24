#!/usr/bin/env python3
"""P4 Capability 03 — simulate Smart Claim Start from Cap 01 + Cap 02.

Usage:
  P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 scripts/simulate_p4_cap03_smart_claim_start.py

Reuses Cap 01 scenarios S1–S6. Does not call CRM or mutate cases.
Walks every scenario for minimal effort, graceful degradation, no dead ends.
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("P4_CUSTOMER_LOOKUP_MOCK", "1")

from services.fiqa_api.inbox_triage.claim_prefill import build_prefill_result  # noqa: E402
from services.fiqa_api.inbox_triage.customer_lookup import lookup_customer  # noqa: E402
from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import (  # noqa: E402
    SCENARIO_KEYS,
)
from services.fiqa_api.inbox_triage.smart_claim_start import (  # noqa: E402
    build_smart_claim_start_plan,
)

# Pre-smart-start world: identity + accident treated as 18 askable fields.
_BEFORE_CUSTOMER_ASKS = 18


def _visible_required(plan: dict) -> list[str]:
    return [
        q["field_key"]
        for q in plan["questions"]
        if q["visibility"] in ("VISIBLE_REQUIRED", "VISIBLE_CONFIRM") and q["blocks_submit"]
    ]


def _has_dead_end(plan: dict) -> bool:
    """Dead end = no primary CTA, or confirm with zero options, or empty screens."""
    if not plan.get("primary_cta_zh"):
        return True
    if not plan.get("screens"):
        return True
    for step in plan.get("confirm_steps") or []:
        if step.get("required_before_accident") and not step.get("options"):
            return True
    return False


def _row_for_scenario(scenario_id: str, key: str) -> dict:
    lookup = lookup_customer(key)
    prefill = build_prefill_result(lookup)
    plan = build_smart_claim_start_plan(lookup, prefill)
    after = plan["estimated_customer_inputs"]
    return {
        "scenario": scenario_id,
        "mode": plan["mode"],
        "headline_zh": plan["headline_zh"],
        "confidence_signal": plan["confidence_signal"],
        "known_chips": plan["known_chips"],
        "confirm_steps": plan["confirm_steps"],
        "blocking_questions": _visible_required(plan),
        "screens": [s["screen_id"] for s in plan["screens"]],
        "primary_cta_zh": plan["primary_cta_zh"],
        "estimated_customer_inputs": after,
        "customer_input_reduction": {
            "before_ask_fields": _BEFORE_CUSTOMER_ASKS,
            "after_estimated_inputs": after,
            "fields_removed_from_customer_ask": max(0, _BEFORE_CUSTOMER_ASKS - after),
        },
        "photos_placement": plan["photos_placement"],
        "failure_profile": plan["failure_profile"],
        "never_ask_again": plan["never_ask_again"],
        "adapter_boundary": plan["adapter_boundary"],
        "no_dead_end": not _has_dead_end(plan),
        "ok": True,
    }


def main() -> int:
    report: list[dict] = []
    for scenario_id, key in SCENARIO_KEYS.items():
        if scenario_id == "AMBIGUOUS":
            # Extra fixture — include for contact-broker path coverage.
            report.append(_row_for_scenario(scenario_id, key))
            continue
        report.append(_row_for_scenario(scenario_id, key))

    by_id = {r["scenario"]: r for r in report}
    checks = {
        "S1_continue_active": (
            by_id["S1_existing_active"]["mode"] == "CONTINUE_ACTIVE"
            and by_id["S1_existing_active"]["estimated_customer_inputs"] == 1
            and by_id["S1_existing_active"]["no_dead_end"]
        ),
        "S2_confirm_vehicle_then_accident": (
            by_id["S2_multi_vehicle"]["mode"] == "MATCHED_CONFIRM_VEHICLE"
            and by_id["S2_multi_vehicle"]["estimated_customer_inputs"] == 5
            and "confirm_vehicle" in by_id["S2_multi_vehicle"]["screens"]
            and "accident_facts" in by_id["S2_multi_vehicle"]["screens"]
        ),
        "S3_matched_known_four_plus": (
            by_id["S3_no_active"]["mode"] == "MATCHED_KNOWN"
            and by_id["S3_no_active"]["estimated_customer_inputs"] == 4
            and any(
                c["field_key"] == "customer_name" for c in by_id["S3_no_active"]["known_chips"]
            )
            and any(c["field_key"] == "vehicle" for c in by_id["S3_no_active"]["known_chips"])
        ),
        "S4_stale_policy_confirm": (
            by_id["S4_stale_policy"]["mode"] == "MATCHED_CONFIRM_POLICY"
            and by_id["S4_stale_policy"]["estimated_customer_inputs"] == 5
            and "confirm_policy" in by_id["S4_stale_policy"]["screens"]
        ),
        "S5_blank_degrade": (
            by_id["S5_no_mapping"]["mode"] == "BLANK_DEGRADE"
            and by_id["S5_no_mapping"]["estimated_customer_inputs"] == 4
            and by_id["S5_no_mapping"]["known_chips"] == []
            and "accident_facts" in by_id["S5_no_mapping"]["screens"]
        ),
        "S6_unavailable_degrade": (
            by_id["S6_unavailable"]["mode"] == "BLANK_DEGRADE"
            and by_id["S6_unavailable"]["no_dead_end"]
            and by_id["S6_unavailable"]["known_chips"] == []
        ),
        "no_technical_ids_in_chips": all(
            "mock_" not in json.dumps(r.get("known_chips") or [], ensure_ascii=False)
            and "person_link" not in json.dumps(r.get("known_chips") or [], ensure_ascii=False)
            and "openid" not in json.dumps(r.get("known_chips") or [], ensure_ascii=False).lower()
            for r in report
            if r["scenario"] != "AMBIGUOUS"
        ),
        "adapter_boundary_stable": all(
            r["adapter_boundary"] == "consumes_LookupResult_and_PrefillResult_only"
            for r in report
        ),
        "AMBIGUOUS_contact_broker": by_id["AMBIGUOUS"]["mode"] == "CONTACT_BROKER",
    }
    all_ok = all(r.get("ok") and r.get("no_dead_end") for r in report) and all(
        checks.values()
    )

    print("=== P4 Capability 03 — Smart Claim Start Simulation ===")
    print(json.dumps({"scenarios": report, "checks": checks}, ensure_ascii=False, indent=2))
    print()
    print("RESULT:", "PASS" if all_ok else "FAIL")
    if not all_ok:
        failed = [k for k, v in checks.items() if not v]
        dead = [r["scenario"] for r in report if not r.get("no_dead_end")]
        print("FAILED CHECKS:", ", ".join(failed) if failed else "(none)")
        if dead:
            print("DEAD ENDS:", ", ".join(dead))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
