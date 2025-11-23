# experiments/nl_to_stress_request_smoke.py

"""
Smoke test for natural language to StressCheckRequest conversion.

This script tests the NLU layer that extracts mortgage parameters from English queries.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage.nl_to_stress_request import nl_to_stress_request


def print_output(output, user_text: str) -> None:
    """Pretty print the NLU output."""
    print("=" * 80)
    print(f"User Query: {user_text}")
    print("=" * 80)
    print(f"\nIntent Type: {output.intent_type}")
    
    # Print partial_request in compact form (one line for non-None fields)
    partial = output.partial_request
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
    print(f"\nMissing Required Fields: {output.missing_required_fields}")
    print(f"Low Confidence Fields: {output.low_confidence_fields}")
    print("\n" + "=" * 80 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test NLU to StressCheckRequest conversion")
    parser.add_argument(
        "--text",
        type=str,
        help="User query text to process (if not provided, runs hard-coded examples)",
    )
    args = parser.parse_args()

    if args.text:
        # Process single query from command line
        output = nl_to_stress_request(args.text)
        print_output(output, args.text)
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
            output = nl_to_stress_request(example)
            print_output(output, example)


if __name__ == "__main__":
    main()

