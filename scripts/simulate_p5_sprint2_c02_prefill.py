#!/usr/bin/env python3
"""P5 Sprint 2 — C02 Prefill reference simulation (Workflow → Capability → Adapter).

Usage:
  P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 scripts/simulate_p5_sprint2_c02_prefill.py

Does not call CRM / AMS. Does not call C03 Smart Claim Start.
Does not import Prefill adapters into Workflow.
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
)
from services.fiqa_api.inbox_triage.workflow_v2 import (  # noqa: E402
    enter_claim_with_prefill,
    simulate_prefill_chain,
)


def main() -> int:
    report: list[dict] = []
    all_ok = True
    for scenario_id, key in list_qa_scenario_keys().items():
        lookup, prefill, decision = enter_claim_with_prefill(key)
        steps = simulate_prefill_chain(lookup, prefill)
        ok = (
            all(s.get("ok") is True for s in steps)
            and decision.blocks_accident_report is False
            and decision.owns_start_claim_screens is False
            and int(prefill.get("auto_prefill_count") or 0) == decision.auto_prefill_count
        )
        # Weak / ambiguous / unavailable → zero AUTO
        status = str(prefill.get("lookup_match_status") or "")
        if status in (
            "NOT_FOUND",
            "LOOKUP_UNAVAILABLE",
            "AMBIGUOUS_MATCH",
            "UNMATCHED_IDENTITY",
        ):
            ok = ok and decision.zero_auto is True
        all_ok = all_ok and ok
        report.append(
            {
                "scenario": scenario_id,
                "match_status": prefill.get("lookup_match_status"),
                "lookup_journey_mode": decision.lookup_journey_mode,
                "auto_prefill_count": decision.auto_prefill_count,
                "customer_required_count": decision.customer_required_count,
                "customer_ask_fields": list(decision.customer_ask_fields),
                "typing_reduction_removed": decision.typing_reduction_removed,
                "auto_chip_values": list(decision.auto_chip_values),
                "needs_vehicle_confirm": decision.needs_vehicle_confirm,
                "needs_stale_policy_confirm": decision.needs_stale_policy_confirm,
                "zero_auto": decision.zero_auto,
                "blocks_accident_report": decision.blocks_accident_report,
                "deferred_presentation": "C03",
                "steps": [s["step"] for s in steps],
                "ok": ok,
                "workflow_knows_adapter": False,
                "prefill_wrote_crm": False,
            }
        )

    wf_src = open(
        os.path.join(
            ROOT,
            "services/fiqa_api/inbox_triage/workflow_v2/c02_prefill_entry.py",
        ),
        encoding="utf-8",
    ).read()
    boundary_ok = (
        "claim_prefill.adapters" not in wf_src
        and "claim_prefill.engine" not in wf_src
        and "smart_claim_start" not in wf_src
        and "mock_directory" not in wf_src
    )
    all_ok = all_ok and boundary_ok

    print("=== P5 Sprint 2 — C02 Prefill (Workflow → Capability → Adapter) ===")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print()
    print("BOUNDARY_WORKFLOW_NO_ADAPTER_OR_C03:", "PASS" if boundary_ok else "FAIL")
    print("RESULT:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
