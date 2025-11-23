# experiments/single_home_graph_smoke.py

"""
Quick smoke test for the single-home LangGraph workflow.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage.schemas import (
    SingleHomeAgentRequest,
    StressCheckRequest,
)
from services.fiqa_api.mortgage.graphs import run_single_home_graph


def main() -> None:
    req = SingleHomeAgentRequest(
        stress_request=StressCheckRequest(
            monthly_income=12000,
            other_debts_monthly=500,
            list_price=900000,
            down_payment_pct=0.2,
            state="CA",
            zip_code="90803",
            hoa_monthly=300,
            risk_preference="neutral",
        ),
        user_message="I'm looking at this $900k home in Long Beach. Is this too tight for me?",
    )

    resp = run_single_home_graph(req)

    print("=== Stress band:", resp.stress_result.stress_band if resp.stress_result else None)
    print("=== DTI ratio:", resp.stress_result.dti_ratio if resp.stress_result else None)
    print("=== Safety upgrade present:", bool(resp.safety_upgrade))
    print("=== Borrower narrative (first 300 chars):")
    print((resp.borrower_narrative or "")[:300])


if __name__ == "__main__":
    main()

