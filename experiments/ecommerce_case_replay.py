#!/usr/bin/env python3
"""
ecommerce_case_replay.py - Replay a Single Ecommerce Agent Evaluation Case

This script replays a single ecommerce agent evaluation case. It reads a case
from an eval cases JSON file (by case_id), re-runs the agent with the same input,
and prints the outcome. The run is traced with LangSmith, tagged for easy visualization.

Example:
  python -m experiments.ecommerce_case_replay \
      --cases-file experiments/data/ecommerce_eval_cases.json \
      --case-id case_001

With LangSmith tracing enabled, you can filter runs by run name or tags
to visualize the full execution trace for this replayed case.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ecommerce.schemas import EcommerceAgentRequest
from services.fiqa_api.ecommerce.graphs.ecommerce_agent_graph import (
    run_ecommerce_agent,
    EcommerceAgentState,
)


def load_cases(cases_path: Path) -> list[dict[str, Any]]:
    """
    Load evaluation cases from a JSON file.
    
    Args:
        cases_path: Path to the JSON file containing eval cases (expected to be a list of dicts)
    
    Returns:
        List of case dictionaries
    
    Raises:
        SystemExit: If file doesn't exist or is not a valid list structure
    """
    if not cases_path.exists():
        print(f"Error: cases file not found: {cases_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(cases_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in cases file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: failed to read cases file: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not isinstance(data, list):
        print(f"Error: cases file must contain a JSON array, got {type(data).__name__}", file=sys.stderr)
        sys.exit(1)
    
    return data


def find_case_by_id(cases: list[dict[str, Any]], case_id: str) -> Optional[dict[str, Any]]:
    """
    Find a case by its ID in the cases list.
    
    Args:
        cases: List of case dictionaries
        case_id: ID of the case to find
    
    Returns:
        Case dictionary if found, None otherwise
    """
    for case in cases:
        if case.get("id") == case_id:
            return case
    return None


def replay_case(case: Dict[str, Any]) -> EcommerceAgentState:
    """
    Re-run the ecommerce agent for a given eval case.
    
    Uses user_message and order_id from the case.
    
    Args:
        case: Case dictionary containing user_message and order_id
    
    Returns:
        EcommerceAgentState after execution completes
    
    Note:
        LangSmith tracing is automatically enabled if run_ecommerce_agent
        is wrapped with maybe_traceable (which it is). The trace will be
        visible in LangSmith UI if LANGSMITH_API_KEY is set.
    """
    # Extract inputs
    user_message = case.get("user_message", "")
    order_id = case.get("order_id", "")
    
    # Construct request
    request = EcommerceAgentRequest(
        user_message=user_message,
        order_id=order_id,
    )
    
    # Call agent
    state = run_ecommerce_agent(request)
    return state


def print_replay_summary(case: Dict[str, Any], state: EcommerceAgentState) -> None:
    """
    Print a human-readable summary of the replayed case and agent outcome.
    
    Args:
        case: Original case dictionary
        state: Agent state after execution
    """
    case_id = case.get("id", "unknown")
    user_message = case.get("user_message", "")
    order_id = case.get("order_id", "")
    
    refund_eligible = state.get("refund_eligible")
    refund = state.get("refund")
    refund_amount = None
    if refund:
        # refund may be a pydantic model or dict; handle both
        if hasattr(refund, "eligible_amount"):
            refund_amount = refund.eligible_amount
        elif isinstance(refund, dict):
            refund_amount = refund.get("eligible_amount")
    
    requires_manual_review = state.get("requires_manual_review")
    final_response = state.get("final_response") or ""
    
    print("\n" + "=" * 60)
    print(f"Case Replay: {case_id}")
    print("=" * 60)
    print(f"Order ID:    {order_id}")
    print(f"User Input:  {user_message}")
    print("-" * 60)
    print(f"Refund eligible: {refund_eligible}")
    if refund_amount is not None:
        print(f"Refund amount:   {refund_amount}")
    print(f"Requires manual review: {requires_manual_review}")
    print("-" * 60)
    print("Final Agent Response:\n")
    print(final_response)
    print("=" * 60 + "\n")
    print(
        "Note: The full execution trace can be viewed in LangSmith "
        "if tracing is enabled for run_ecommerce_agent."
    )


def main() -> None:
    """Main entry point for the replay script."""
    parser = argparse.ArgumentParser(
        description="Replay a single ecommerce eval case via the ecommerce agent."
    )
    parser.add_argument(
        "--cases-file",
        type=str,
        default="experiments/data/ecommerce_eval_cases.json",
        help="Path to the JSON file containing eval cases.",
    )
    parser.add_argument(
        "--case-id",
        type=str,
        required=True,
        help="ID of the case to replay (e.g., 'case_001').",
    )
    
    args = parser.parse_args()
    
    cases_path = Path(args.cases_file)
    if not cases_path.exists():
        print(f"Error: cases file not found: {cases_path}", file=sys.stderr)
        sys.exit(1)
    
    cases = load_cases(cases_path)
    case = find_case_by_id(cases, args.case_id)
    if case is None:
        print(f"Error: case_id '{args.case_id}' not found in {cases_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        state = replay_case(case)
    except Exception as e:
        print(f"Error while re-running agent for case '{args.case_id}': {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print_replay_summary(case, state)


if __name__ == "__main__":
    main()
