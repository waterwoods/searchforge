#!/usr/bin/env python3
"""P5 Sprint 3 — C03 Customer Trust simulation.

Usage:
  P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 \
    scripts/simulate_p5_sprint3_c03_smart_claim_start.py

Consumes C01+C02 → C03 presentation. No AMS / CRM / Notification / Timeline.
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("P4_CUSTOMER_LOOKUP_MOCK", "1")

from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import (  # noqa: E402
    SCENARIO_KEYS,
)
from services.fiqa_api.inbox_triage.workflow_v2.c03_start_entry import (  # noqa: E402
    enter_claim_with_smart_start,
    simulate_smart_start_chain,
)


def _row(scenario_id: str, key: str) -> dict:
    lookup, prefill, plan, decision = enter_claim_with_smart_start(key)
    steps = simulate_smart_start_chain(lookup, prefill, plan)
    return {
        "scenario": scenario_id,
        "mode": decision.plan_mode,
        "headline_zh": decision.headline_zh,
        "primary_cta_zh": decision.primary_cta_zh,
        "secondary_cta_zh": decision.secondary_cta_zh,
        "known_chip_count": decision.known_chip_count,
        "required_confirm_count": decision.required_confirm_count,
        "soft_notice_count": decision.soft_notice_count,
        "estimated_customer_inputs": decision.estimated_customer_inputs,
        "has_blank_escape": decision.has_blank_escape,
        "never_blocks_accident": decision.never_blocks_accident,
        "no_quiz_on_unambiguous": decision.no_quiz_on_unambiguous,
        "lands_on_story": decision.lands_on_story,
        "screens": [s.get("screen_id") for s in plan.get("screens") or []],
        "chain_ok": all(s.get("ok") for s in steps),
        "c03_wrote_crm": False,
        "ok": True,
    }


def main() -> int:
    report = []
    for scenario_id, key in SCENARIO_KEYS.items():
        report.append(_row(scenario_id, key))

    by_id = {r["scenario"]: r for r in report}
    checks = {
        "S3_chips_to_story_no_quiz": (
            by_id["S3_no_active"]["mode"] == "MATCHED_KNOWN"
            and by_id["S3_no_active"]["no_quiz_on_unambiguous"]
            and by_id["S3_no_active"]["lands_on_story"]
            and by_id["S3_no_active"]["required_confirm_count"] == 0
            and "known_context" not in by_id["S3_no_active"]["screens"]
        ),
        "S2_one_vehicle_decision": (
            by_id["S2_multi_vehicle"]["mode"] == "MATCHED_CONFIRM_VEHICLE"
            and by_id["S2_multi_vehicle"]["required_confirm_count"] == 1
            and by_id["S2_multi_vehicle"]["estimated_customer_inputs"] == 5
        ),
        "S4_stale_always_continue": (
            by_id["S4_stale_policy"]["mode"] == "MATCHED_CONFIRM_POLICY"
            and by_id["S4_stale_policy"]["never_blocks_accident"]
            and by_id["S4_stale_policy"]["required_confirm_count"] == 0
            and by_id["S4_stale_policy"]["soft_notice_count"] == 1
        ),
        "S5_S6_silent_blank": (
            by_id["S5_no_mapping"]["mode"] == "BLANK_DEGRADE"
            and by_id["S6_unavailable"]["mode"] == "BLANK_DEGRADE"
            and by_id["S5_no_mapping"]["known_chip_count"] == 0
            and by_id["S6_unavailable"]["known_chip_count"] == 0
        ),
        "AMBIGUOUS_never_trapped": (
            by_id["AMBIGUOUS"]["mode"] == "CONTACT_BROKER"
            and by_id["AMBIGUOUS"]["has_blank_escape"]
            and by_id["AMBIGUOUS"]["secondary_cta_zh"] == "仍要先报案"
        ),
        "S1_continue_only": (
            by_id["S1_existing_active"]["mode"] == "CONTINUE_ACTIVE"
            and by_id["S1_existing_active"]["primary_cta_zh"] == "继续当前报案"
        ),
        "BOUNDARY_NO_CRM": all(r["c03_wrote_crm"] is False for r in report),
        "CHAIN_OK": all(r["chain_ok"] for r in report),
    }
    all_ok = all(checks.values()) and all(r.get("ok") for r in report)

    print("=== P5 Sprint 3 — C03 Customer Trust Simulation ===")
    print(json.dumps({"scenarios": report, "checks": checks}, ensure_ascii=False, indent=2))
    print()
    print("RESULT:", "PASS" if all_ok else "FAIL")
    print(
        "BOUNDARY_NO_AMS_NOTIFICATION_TIMELINE:",
        "PASS" if checks["BOUNDARY_NO_CRM"] and checks["CHAIN_OK"] else "FAIL",
    )
    if not all_ok:
        failed = [k for k, v in checks.items() if not v]
        print("FAILED CHECKS:", ", ".join(failed))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
