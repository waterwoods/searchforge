#!/usr/bin/env python3
"""
ecommerce_agent_smoke.py - Ecommerce Agent Smoke Test

Minimal smoke test script to verify that the ecommerce after-sales agent runs end-to-end correctly.
Directly calls LangGraph's run_ecommerce_agent, does not require API service.

Usage:
    python -m services.fiqa_api.ecommerce.experiments.ecommerce_agent_smoke
"""

# Load environment variables from .env file
from pathlib import Path
from dotenv import load_dotenv

# Load .env from repository root
repo_root = Path(__file__).parent.parent.parent.parent.parent
env_path = repo_root / '.env'
if env_path.exists():
    load_dotenv(env_path, override=False)

from services.fiqa_api.ecommerce.schemas import EcommerceAgentRequest
from services.fiqa_api.ecommerce.graphs.ecommerce_agent_graph import run_ecommerce_agent


def run_case(label: str, order_id: str, user_message: str) -> None:
    """
    Run a test case and print results.
    
    Args:
        label: Test case label to distinguish different test scenarios
        order_id: Order ID
        user_message: User message
    """
    print("=" * 80)
    print(f"Test Case: {label}")
    print("=" * 80)
    print(f"\nOrder ID: {order_id}")
    print(f"User Message: {user_message}")
    print()
    
    try:
        # Construct request
        request = EcommerceAgentRequest(
            user_message=user_message,
            order_id=order_id
        )
        
        # Call agent
        result = run_ecommerce_agent(request)
        
        # Print results
        print("📋 Execution Results:")
        print("-" * 80)
        
        # Intent
        intent = result.get("intent")
        if intent:
            print(f"  Intent: {intent}")
        
        # Order status
        order = result.get("order")
        if order:
            print(f"  Order Status: {order.status}")
            print(f"  Order Amount: ${order.total_amount:.2f}")
        
        # Refund reason
        refund_reason = result.get("refund_reason")
        if refund_reason:
            print(f"  Refund Reason Type: {refund_reason.reason_type}")
        
        # Refund eligibility
        refund_eligible = result.get("refund_eligible")
        if refund_eligible is not None:
            eligible_symbol = "✅" if refund_eligible else "❌"
            print(f"  Refund Eligible: {eligible_symbol} {refund_eligible}")
        
        # Refund amount
        refund = result.get("refund")
        if refund:
            print(f"  Refund Amount: ${refund.eligible_amount:.2f}")
            print(f"  Refund Reason: {refund.reason}")
        
        # Policy context (RAG)
        policy_context = result.get("policy_context")
        if policy_context:
            print(f"\n📚 Policy Context (RAG):")
            print(f"  Retrieved {len(policy_context)} policy snippets")
            for idx, snippet in enumerate(policy_context[:2], 1):  # Show first 2
                source = snippet.get("source", "unknown")
                text_preview = snippet.get("text", "")[:100] + "..." if len(snippet.get("text", "")) > 100 else snippet.get("text", "")
                print(f"  {idx}. [{source}] {text_preview}")
        else:
            print(f"\n⚠️  Policy Context: Not retrieved (RAG may not be configured)")
        
        # Final response
        final_response = result.get("final_response")
        if final_response:
            print(f"\n💬 Final Response:")
            print(f"  {final_response}")
        
        # Agent steps
        agent_steps = result.get("agent_steps", [])
        if agent_steps:
            print(f"\n📝 Execution Steps ({len(agent_steps)} steps):")
            for idx, step in enumerate(agent_steps, 1):
                step_name = step.step_name
                status = step.status
                status_symbol = "✅" if status in ["completed", "done"] else "⚠️"
                print(f"  {idx}. {status_symbol} {step_name} ({status})")
        
        print("\n✅ Test case executed successfully\n")
        
    except Exception as e:
        print(f"\n❌ Test case execution failed:")
        print(f"  Error Type: {type(e).__name__}")
        print(f"  Error Message: {str(e)}")
        print("\n⚠️  Test case execution error\n")


if __name__ == "__main__":
    print("=" * 80)
    print("Ecommerce After-Sales Agent Smoke Test")
    print("=" * 80)
    print("\nThis script verifies that the ecommerce after-sales agent basic functionality works correctly.")
    print("Tests will directly call LangGraph, no API service startup required.\n")
    
    # Test case 1: Normal refund scenario
    run_case(
        label="Normal Refund Scenario",
        order_id="A10001",
        user_message="我想退货/退款，这个耳机有点问题，音质不好"
    )
    
    # Test case 2: Different order status (shipped)
    run_case(
        label="Shipped Order Refund",
        order_id="A10002",
        user_message="这个订单已经发货了，但我还是想退款，可以吗？"
    )
    
    # Test case 3: Error scenario (order not found)
    run_case(
        label="Error Scenario - Order Not Found",
        order_id="UNKNOWN",
        user_message="我想查询订单 UNKNOWN 的退款信息"
    )
    
    # Test case 4: Within time window + damaged → should have refund_eligible=True and refund amount
    run_case(
        label="Eligible - Delivered 3 Days Ago + Damage Reason",
        order_id="A10004",
        user_message="我收到的智能手表坏了，屏幕不亮，我想退款"
    )
    
    # Test case 5: Status not allowed (processing status) → refund_eligible=False
    run_case(
        label="Not Eligible - Order Status Does Not Allow Refund",
        order_id="A10003",
        user_message="我想退货，这个机械键盘不想要了"
    )
    
    # Test case 6: Within time window but no longer wanted (delivered 10 days ago, exceeds 7-day limit) → refund_eligible=False
    run_case(
        label="Not Eligible - Exceeded Refund Time Window (No Longer Wanted)",
        order_id="A10005",
        user_message="我后悔买了这个游戏鼠标，不想要了"
    )
    
    # Test case 7: Within time window but damaged (delivered 10 days ago, but within 30-day limit) → refund_eligible=True
    run_case(
        label="Eligible - Delivered 10 Days Ago + Damage Reason (Within 30 Days)",
        order_id="A10005",
        user_message="这个鼠标坏了，右键点击不灵"
    )
    
    print("=" * 80)
    print("All test cases completed")
    print("=" * 80)
