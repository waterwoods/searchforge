# experiments/nl_entry_graph_smoke.py

"""
Smoke test for NLU entry graph.

This script tests the LangGraph integration that:
1. Takes a natural language query
2. Extracts mortgage fields via NLU
3. Decides whether we have enough info to run a stress check
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage.graphs.nl_entry_graph import run_nl_entry_graph


def print_result(result: dict, user_text: str) -> None:
    """Pretty print the NLU graph result."""
    print("=" * 80)
    print(f"User Query: {user_text}")
    print("=" * 80)
    
    print(f"\nIntent Type: {result.get('nl_intent_type', 'unknown')}")
    
    # Print partial_request in compact form
    partial = result.get("partial_request")
    if partial:
        filled_fields = []
        if partial.income_monthly is not None:
            filled_fields.append(f"income_monthly={partial.income_monthly:,.0f}")
        if partial.other_debt_monthly is not None:
            filled_fields.append(f"other_debt_monthly={partial.other_debt_monthly:,.0f}")
        if partial.list_price is not None:
            filled_fields.append(f"list_price={partial.list_price:,.0f}")
        if partial.down_payment_pct is not None:
            filled_fields.append(f"down_payment_pct={partial.down_payment_pct:.2%}")
        if partial.interest_rate_annual is not None:
            filled_fields.append(f"interest_rate_annual={partial.interest_rate_annual:.2%}")
        if partial.loan_term_years is not None:
            filled_fields.append(f"loan_term_years={partial.loan_term_years}")
        if partial.zip_code is not None:
            filled_fields.append(f"zip_code={partial.zip_code}")
        if partial.state is not None:
            filled_fields.append(f"state={partial.state}")
        
        print(f"\nPartial Request: {' | '.join(filled_fields) if filled_fields else '(empty)'}")
    else:
        print("\nPartial Request: (empty)")
    
    print(f"\nMissing Required Fields: {result.get('missing_required_fields', [])}")
    print(f"\nRouter Decision: {result.get('router_decision', 'unknown')}")
    
    if result.get("router_decision") == "have_enough_info":
        print("\n✓ Ready to run stress check (all required fields present)")
    else:
        print("\n✗ Need more info (missing required fields)")
    
    print("\n" + "=" * 80 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test NLU entry graph")
    parser.add_argument(
        "--text",
        type=str,
        help="User query text to process (if not provided, runs hard-coded examples)",
    )
    args = parser.parse_args()

    if args.text:
        # Process single query from command line
        result = run_nl_entry_graph(args.text)
        print_result(result, args.text)
    else:
        # Run hard-coded examples
        examples = [
            "I make $150k a year and I'm looking at a $750k home in 90803 with 20% down.",
            "We earn around 6k per month and want to buy a 300k starter home in Texas.",
            "What if I try to buy an 900k place with almost no down payment?",
            "I have an annual income of $120,000 and I'm considering a $500,000 home in California with 15% down payment.",
            "Can I afford a 1.2 million dollar house if I make 8,000 dollars monthly?",
        ]

        print("Running hard-coded examples...\n")
        for example in examples:
            result = run_nl_entry_graph(example)
            print_result(result, example)


if __name__ == "__main__":
    main()

