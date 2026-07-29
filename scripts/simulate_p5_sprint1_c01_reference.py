#!/usr/bin/env python3
"""P5 Sprint 1 — C01 reference simulation (Workflow → Capability → Adapter).

Usage:
  P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 scripts/simulate_p5_sprint1_c01_reference.py

Does not call CRM / AMS. Does not import adapter fixtures into Workflow.
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
from services.fiqa_api.inbox_triage.workflow_v2 import (  # noqa: E402
    enter_claim_with_lookup,
    simulate_main_chain_from_lookup,
)


def main() -> int:
    report: list[dict] = []
    all_ok = True
    for scenario_id, key in list_qa_scenario_keys().items():
        result, decision = enter_claim_with_lookup(key)
        steps = simulate_main_chain_from_lookup(result)
        ok = all(s.get("ok") is True for s in steps) and (
            decision.blocks_accident_report is False or decision.journey_mode == "relogin"
        )
        # Accident reporting must remain open for all mock scenarios except invalid identity.
        if scenario_id != "AMBIGUOUS" and decision.journey_mode != "relogin":
            ok = ok and decision.blocks_accident_report is False
        all_ok = all_ok and ok
        report.append(
            {
                "scenario": scenario_id,
                "match_status": result.get("match_status"),
                "lookup_source": result.get("lookup_source"),
                "journey_mode": decision.journey_mode,
                "customer_next_screen": decision.customer_next_screen,
                "primary_cta": decision.primary_cta,
                "blocks_accident_report": decision.blocks_accident_report,
                "allows_manual_claim": decision.allows_manual_claim,
                "vehicle_count": decision.vehicle_count,
                "steps": [s["step"] for s in steps],
                "ok": ok,
                "workflow_knows_adapter": False,
            }
        )

    # Prove Workflow path never needs mock directory import.
    wf_src = open(
        os.path.join(
            ROOT,
            "services/fiqa_api/inbox_triage/workflow_v2/c01_lookup_entry.py",
        ),
        encoding="utf-8",
    ).read()
    boundary_ok = "mock_directory" not in wf_src and "adapters" not in wf_src
    all_ok = all_ok and boundary_ok

    print("=== P5 Sprint 1 — C01 Reference (Workflow → Capability → Adapter) ===")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print()
    print("BOUNDARY_WORKFLOW_NO_ADAPTER_IMPORT:", "PASS" if boundary_ok else "FAIL")
    print("RESULT:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
