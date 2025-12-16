"""
ecommerce_chat_cli.py - Simple CLI for interacting with the ecommerce after-sales agent

This script provides a command-line interface to interact with the ecommerce agent.
Users can input an order ID and a natural language question/request, and receive
the agent's response along with a decision summary.

Now includes basic input validation for order ID and message.

How to run:
    python -m services.fiqa_api.ecommerce.experiments.ecommerce_chat_cli

Example order IDs: A10001, A10002, AMZ10001, AMZ10002, etc.

Example manual tests:
    - Input empty order_id → prompts MISSING_ORDER_ID
    - Input non-existent order_id (e.g., XYZ123) → ORDER_NOT_FOUND
    - Input "hi" → MESSAGE_TOO_SHORT or MESSAGE_NOT_REFUND_RELATED
    - Input valid order + refund request → proceeds to Agent flow normally.
"""

import sys
from typing import Dict, Any, Optional

from services.fiqa_api.ecommerce.schemas import EcommerceAgentRequest
from services.fiqa_api.ecommerce.graphs.ecommerce_agent_graph import (
    run_ecommerce_agent,
    EcommerceAgentState,
)
from services.fiqa_api.ecommerce.tools.order_tool import get_order
from services.fiqa_api.ecommerce.input_validation import (
    validate_ecommerce_request,
    InputValidationResult,
)


def print_decision_summary(state: EcommerceAgentState) -> None:
    """
    Print a concise decision summary from the agent state.
    
    Extracts and displays key information:
    - Order ID and status
    - Refund eligibility
    - Refund amount (if applicable)
    - Manual review requirement
    """
    order = state.get("order")
    refund_eligible = state.get("refund_eligible")
    refund = state.get("refund")
    requires_manual_review = state.get("requires_manual_review")
    
    # Order information
    if order:
        print(f"Order: {order.order_id} (status: {order.status})")
    else:
        print("Order: [Not found]")
    
    # Refund eligibility
    if refund_eligible is not None:
        print(f"Refund eligible: {refund_eligible}")
    else:
        print("Refund eligible: [Not determined]")
    
    # Refund amount
    if refund and refund.eligible_amount is not None:
        print(f"Refund amount: USD {refund.eligible_amount:.2f}")
    else:
        print("Refund amount: [N/A]")
    
    # Manual review requirement
    if requires_manual_review is not None:
        print(f"Requires manual review: {requires_manual_review}")
    else:
        print("Requires manual review: [Not determined]")


def main() -> None:
    """Main interactive loop for the CLI."""
    print("=" * 60)
    print("Ecommerce After-Sales Agent CLI")
    print("Type 'q' at any prompt to exit.")
    print("=" * 60)
    print()
    
    while True:
        try:
            # Step 1: Read order ID
            order_id = input("Enter order ID (e.g., AMZ10001, A10001) or 'q' to quit: ").strip()
            
            if order_id.lower() == "q":
                print("Goodbye!")
                break
            
            # Step 2: Read user message
            user_message = input("Describe your issue (e.g., damaged item, want a refund): ").strip()
            
            if user_message.lower() == "q":
                print("Goodbye!")
                break
            
            # Step 3: Construct request and validate
            request = EcommerceAgentRequest(user_message=user_message, order_id=order_id)
            validation_result = validate_ecommerce_request(request)
            
            if not validation_result.is_valid:
                err = validation_result.error
                print("\n" + "-" * 60)
                print("Input Validation Error:")
                print(f"- Code: {err.code}")
                print(f"- Message: {err.message}")
                if err.details:
                    print(f"- Details: {err.details}")
                print("-" * 60 + "\n")
                continue
            
            # Step 4: Call agent (only if validation passed)
            print("\nProcessing your request...")
            state = run_ecommerce_agent(request)
            
            # Step 5: Print results
            print("\n" + "=" * 60)
            print("Final Agent Response:\n")
            
            final_response = state.get("final_response", "")
            if final_response:
                print(final_response)
            else:
                print("[No response generated]")
            
            print("\nDecision Summary:")
            print_decision_summary(state)
            print("=" * 60)
            print()
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            print("Please check your configuration and try again.")
            print()


if __name__ == "__main__":
    main()
