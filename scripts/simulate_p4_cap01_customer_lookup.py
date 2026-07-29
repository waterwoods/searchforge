#!/usr/bin/env python3
"""P4 Capability 01 — simulate Customer Lookup mock harness (read-only).

Usage:
  P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 scripts/simulate_p4_cap01_customer_lookup.py

Does not call CRM, Epic, EZLynx, or mutate customers/policies/vehicles.
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("P4_CUSTOMER_LOOKUP_MOCK", "1")

from services.fiqa_api.inbox_triage.customer_lookup import (  # noqa: E402
    list_qa_scenario_keys,
    lookup_customer,
)
from services.fiqa_api.inbox_triage.customer_lookup.facade import (  # noqa: E402
    broker_header_fields_from_lookup,
)
from services.fiqa_api.inbox_triage.workflow_v2 import (  # noqa: E402
    simulate_main_chain_from_lookup,
)

SCENARIO_KEYS = list_qa_scenario_keys()


def main() -> int:
    report: list[dict] = []
    all_ok = True
    for scenario_id, key in SCENARIO_KEYS.items():
        if scenario_id == "AMBIGUOUS":
            continue
        result = lookup_customer(key)
        steps = simulate_main_chain_from_lookup(result)
        header = broker_header_fields_from_lookup(result)
        ok = all(s.get("ok") is True for s in steps)
        all_ok = all_ok and ok
        report.append(
            {
                "scenario": scenario_id,
                "match_status": result.get("match_status"),
                "lookup_confidence": result.get("lookup_confidence"),
                "next_action": result.get("next_action"),
                "broker_header": header,
                "prefill": result.get("prefill") or {},
                "steps": [s["step"] for s in steps],
                "ok": ok,
                "duplicate_customer": False,
                "duplicate_claim": False,
                "lookup_mutated_crm": False,
            }
        )

    print("=== P4 Capability 01 — Customer Lookup Simulation ===")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print()
    print("RESULT:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
