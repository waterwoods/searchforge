#!/usr/bin/env python3
"""P4 Capability 02 — simulate Claim Prefill from Cap 01 LookupResult.

Usage:
  P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 scripts/simulate_p4_cap02_claim_prefill.py

Reuses Cap 01 scenarios S1–S6. Does not call CRM or mutate cases.
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("P4_CUSTOMER_LOOKUP_MOCK", "1")

from services.fiqa_api.inbox_triage.claim_prefill import (  # noqa: E402
    build_prefill_result,
    founder_shorthand_map,
)
from services.fiqa_api.inbox_triage.customer_lookup import lookup_customer  # noqa: E402
from services.fiqa_api.inbox_triage.customer_lookup.mock_directory import (  # noqa: E402
    SCENARIO_KEYS,
)

# Baseline: blank Start Claim path asks all identity + accident (pre-prefill world).
# Cap 02 reduces customer asks to accident facts (+ confirms when needed).
_BEFORE_CUSTOMER_ASKS = 18  # every founder field treated as askable without lookup


def _row_for_scenario(scenario_id: str, key: str) -> dict:
    lookup = lookup_customer(key)
    prefill = build_prefill_result(lookup)
    shorthand = founder_shorthand_map(prefill)
    fields_compact = {
        f["field_key"]: {
            "class": f["classification"],
            "shorthand": f["founder_shorthand"],
            "value": f.get("value"),
            "needs_confirm": f.get("needs_confirm"),
            "reason": f.get("reason_code"),
        }
        for f in prefill["fields"]
    }
    after_asks = prefill["customer_required_count"]
    return {
        "scenario": scenario_id,
        "match_status": prefill["lookup_match_status"],
        "lookup_confidence": prefill["lookup_confidence"],
        "lookup_next_action": prefill["lookup_next_action"],
        "counts": {
            "AUTO_PREFILL": prefill["auto_prefill_count"],
            "CUSTOMER_REQUIRED": prefill["customer_required_count"],
            "BROKER_REQUIRED": prefill["broker_required_count"],
            "UNKNOWN": prefill["unknown_count"],
        },
        "customer_input_reduction": {
            "before_ask_fields": _BEFORE_CUSTOMER_ASKS,
            "after_customer_required": after_asks,
            "fields_removed_from_customer_ask": _BEFORE_CUSTOMER_ASKS - after_asks,
        },
        "auto_fields": prefill["auto_fields"],
        "customer_ask_fields": prefill["customer_ask_fields"],
        "founder_shorthand": shorthand,
        "fields": fields_compact,
        "ok": True,
    }


def main() -> int:
    report: list[dict] = []
    for scenario_id, key in SCENARIO_KEYS.items():
        if scenario_id == "AMBIGUOUS":
            continue
        report.append(_row_for_scenario(scenario_id, key))

    all_ok = all(r.get("ok") for r in report)
    # Founder spot-checks
    by_id = {r["scenario"]: r for r in report}
    checks = {
        "S1_auto_name_vehicle": (
            by_id["S1_existing_active"]["fields"]["customer_name"]["class"]
            == "AUTO_PREFILL"
            and by_id["S1_existing_active"]["fields"]["vehicle"]["class"]
            == "AUTO_PREFILL"
            and by_id["S1_existing_active"]["fields"]["accident_story"]["class"]
            == "CUSTOMER_REQUIRED"
        ),
        "S2_vehicle_ask": (
            by_id["S2_multi_vehicle"]["fields"]["vehicle"]["class"]
            == "CUSTOMER_REQUIRED"
            and by_id["S2_multi_vehicle"]["fields"]["customer_name"]["class"]
            == "AUTO_PREFILL"
        ),
        "S3_prefill_ready": (
            by_id["S3_no_active"]["fields"]["policy_number"]["class"]
            == "AUTO_PREFILL"
            and "accident_time" in by_id["S3_no_active"]["customer_ask_fields"]
        ),
        "S4_stale_policy_confirm": (
            by_id["S4_stale_policy"]["fields"]["policy_number"]["class"]
            == "CUSTOMER_REQUIRED"
            and by_id["S4_stale_policy"]["fields"]["policy_number"].get("needs_confirm")
            is True
        ),
        "S5_no_auto_identity": (
            by_id["S5_no_mapping"]["counts"]["AUTO_PREFILL"] == 0
            and by_id["S5_no_mapping"]["fields"]["accident_story"]["class"]
            == "CUSTOMER_REQUIRED"
        ),
        "S6_degrade": (
            by_id["S6_unavailable"]["counts"]["AUTO_PREFILL"] == 0
            and by_id["S6_unavailable"]["fields"]["injury"]["class"]
            == "CUSTOMER_REQUIRED"
        ),
    }
    all_ok = all_ok and all(checks.values())

    print("=== P4 Capability 02 — Claim Prefill Simulation ===")
    print(json.dumps({"scenarios": report, "checks": checks}, ensure_ascii=False, indent=2))
    print()
    print("RESULT:", "PASS" if all_ok else "FAIL")
    if not all_ok:
        failed = [k for k, v in checks.items() if not v]
        print("FAILED CHECKS:", ", ".join(failed))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
