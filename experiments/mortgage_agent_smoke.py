#!/usr/bin/env python3
"""
mortgage_agent_smoke.py - Mortgage Agent Smoke Test

Minimal smoke test for POST /api/mortgage-agent/run endpoint.

Usage:
    python experiments/mortgage_agent_smoke.py [--base-url http://localhost:8000]
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# ============================================================================
# Configuration Constants
# ============================================================================

DEFAULT_BASE_URL = "http://localhost:8000"

# Test payload
TEST_PAYLOAD = {
    "user_message": "Can I afford a 800k home in Seattle with 150k income?",
    "inputs": {
        "income": 150000,
        "debts": 500,
        "purchase_price": 800000,
        "down_payment_pct": 0.20,
        "state": "WA"
    }
}


# ============================================================================
# Helper Functions
# ============================================================================

def call_api(base_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call /api/mortgage-agent/run API.
    
    Args:
        base_url: API base URL
        payload: Request payload
        
    Returns:
        dict: API response
    """
    import requests
    
    url = f"{base_url}/api/mortgage-agent/run"
    
    try:
        start_time = time.perf_counter()
        response = requests.post(url, json=payload, timeout=30.0)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        response.raise_for_status()
        data = response.json()
        
        # Add measured latency
        data["_measured_latency_ms"] = elapsed_ms
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ API call failed: {e}", file=sys.stderr)
        raise


def format_plan(plan: Dict[str, Any], index: int) -> str:
    """
    Format mortgage plan for display.
    
    Args:
        plan: Plan dictionary
        index: Plan index (1-based)
        
    Returns:
        str: Formatted string
    """
    parts = []
    parts.append(f"\n  Plan {index}: {plan.get('name', 'Unknown')}")
    parts.append(f"    Plan ID: {plan.get('plan_id', 'N/A')}")
    parts.append(f"    Monthly Payment: ${plan.get('monthly_payment', 0):,.2f}")
    parts.append(f"    Interest Rate: {plan.get('interest_rate', 0):.2f}%")
    parts.append(f"    Loan Amount: ${plan.get('loan_amount', 0):,.0f}")
    parts.append(f"    Term: {plan.get('term_years', 0)} years")
    parts.append(f"    DTI Ratio: {plan.get('dti_ratio', 0):.2%}" if plan.get('dti_ratio') else "    DTI Ratio: N/A")
    parts.append(f"    Risk Level: {plan.get('risk_level', 'unknown').upper()}")
    
    # Pros
    pros = plan.get('pros', [])
    if pros:
        parts.append(f"    Pros:")
        for pro in pros:
            parts.append(f"      - {pro}")
    
    # Cons
    cons = plan.get('cons', [])
    if cons:
        parts.append(f"    Cons:")
        for con in cons:
            parts.append(f"      - {con}")
    
    return "\n".join(parts)


def print_response(data: Dict[str, Any], payload: Optional[Dict[str, Any]] = None) -> None:
    """
    Print API response in a readable format.
    
    Args:
        data: API response dictionary
        payload: Optional request payload for sanity checks
    """
    print("=" * 80)
    print("Mortgage Agent API Response")
    print("=" * 80)
    
    # Status
    ok = data.get("ok", False)
    status_icon = "✅" if ok else "❌"
    print(f"\n{status_icon} Status: {'OK' if ok else 'ERROR'}")
    
    if not ok:
        error = data.get("error", "Unknown error")
        print(f"   Error: {error}")
        return
    
    # Agent version
    agent_version = data.get("agent_version", "unknown")
    print(f"\n📋 Agent Version: {agent_version}")
    
    # Disclaimer
    disclaimer = data.get("disclaimer", "")
    if disclaimer:
        print(f"\n⚠️  Disclaimer:")
        print(f"   {disclaimer}")
    
    # Input summary
    input_summary = data.get("input_summary", "")
    if input_summary:
        print(f"\n📊 Input Summary:")
        print(f"   {input_summary}")
    
    # Hard warning
    hard_warning = data.get("hard_warning")
    if hard_warning:
        print(f"\n🚨 [HARD WARNING]:")
        print(f"   {hard_warning}")
    else:
        print(f"\n✅ Hard Warning: None (no high-risk scenario detected)")
    
    # Max affordability
    max_affordability = data.get("max_affordability")
    if max_affordability:
        print(f"\n💰 Max Affordability Summary:")
        print(f"   Max Monthly Payment: ${max_affordability.get('max_monthly_payment', 0):,.2f}")
        print(f"   Max Loan Amount: ${max_affordability.get('max_loan_amount', 0):,.0f}")
        print(f"   Max Home Price: ${max_affordability.get('max_home_price', 0):,.0f}")
        print(f"   Assumed Interest Rate: {max_affordability.get('assumed_interest_rate', 0):.2f}%")
        print(f"   Target DTI: {max_affordability.get('target_dti', 0):.1%}")
        
        # Sanity check: monthly payment should not exceed monthly income
        monthly_payment = max_affordability.get('max_monthly_payment', 0)
        if monthly_payment > 0 and payload:
            try:
                inputs = payload.get('inputs', {})
                annual_income = inputs.get('income')
                if annual_income:
                    monthly_income = annual_income / 12.0
                    payment_pct = (monthly_payment / monthly_income * 100) if monthly_income > 0 else 0
                    print(f"\n   ✅ Sanity Check:")
                    print(f"      Max monthly payment: ${monthly_payment:,.2f}")
                    print(f"      Monthly income: ${monthly_income:,.2f}")
                    print(f"      Payment as % of income: {payment_pct:.1f}%")
                    if monthly_payment > monthly_income:
                        print(f"      ⚠️  WARNING: Monthly payment exceeds monthly income!")
                    elif payment_pct > 50:
                        print(f"      ⚠️  WARNING: Monthly payment is >50% of income (high risk)")
                    else:
                        print(f"      ✓ Monthly payment is within reasonable range")
            except (KeyError, TypeError, ZeroDivisionError):
                pass
    else:
        print(f"\n⚠️  Max Affordability: Not computed (may require income and debts)")
    
    # Plans
    plans = data.get("plans", [])
    if plans:
        print(f"\n🏠 Mortgage Plans ({len(plans)} plans):")
        for idx, plan in enumerate(plans, 1):
            print(format_plan(plan, idx))
    else:
        print("\n⚠️  No plans generated")
    
    # Follow-ups
    followups = data.get("followups", [])
    if followups:
        print(f"\n💡 Follow-up Questions ({len(followups)} questions):")
        for idx, question in enumerate(followups, 1):
            print(f"   {idx}. {question}")
    
    # LLM explanation
    llm_explanation = data.get("llm_explanation")
    if llm_explanation:
        print(f"\n🤖 LLM Explanation:")
        # Print first 400 characters as preview
        preview = llm_explanation[:400]
        if len(llm_explanation) > 400:
            preview += "..."
        print(f"   {preview}")
    else:
        print(f"\n🤖 LLM Explanation: None (maybe disabled or failed)")
    
    # LLM usage
    llm_usage = data.get("llm_usage")
    if llm_usage:
        print(f"\n📊 LLM Usage:")
        print(f"   Model: {llm_usage.get('model', 'N/A')}")
        print(f"   Prompt Tokens: {llm_usage.get('prompt_tokens', 'N/A')}")
        print(f"   Completion Tokens: {llm_usage.get('completion_tokens', 'N/A')}")
        print(f"   Total Tokens: {llm_usage.get('total_tokens', 'N/A')}")
        cost = llm_usage.get('cost_usd_est')
        if cost is not None:
            print(f"   Cost Estimate: ${cost:.6f}")
        else:
            print(f"   Cost Estimate: N/A")
    else:
        print(f"\n📊 LLM Usage: None (maybe disabled or failed)")
    
    # LO Summary
    lo_summary = data.get("lo_summary")
    if lo_summary:
        print(f"\n📋 Loan Officer Summary:")
        # Print first 400 characters as preview
        preview = lo_summary[:400]
        if len(lo_summary) > 400:
            preview += "..."
        print(f"   {preview}")
    else:
        print(f"\n📋 Loan Officer Summary: None (maybe not generated)")
    
    # Case State (new field)
    case_state = data.get("case_state")
    if case_state:
        print(f"\n📸 Case State (Snapshot):")
        print(f"   Case ID: {case_state.get('case_id', 'N/A')}")
        print(f"   Timestamp: {case_state.get('timestamp', 'N/A')}")
        risk_summary = case_state.get('risk_summary', {})
        if risk_summary:
            highest_dti = risk_summary.get('highest_dti')
            if highest_dti is not None:
                print(f"   Highest DTI: {highest_dti:.1%}")
            risk_levels = risk_summary.get('risk_levels', [])
            if risk_levels:
                print(f"   Risk Levels: {', '.join(risk_levels)}")
            hard_warning = risk_summary.get('hard_warning')
            print(f"   Hard Warning Present: {hard_warning is not None}")
    else:
        print(f"\n📸 Case State: None (not available)")
    
    # Agent Steps (new field)
    agent_steps = data.get("agent_steps")
    if agent_steps:
        print(f"\n🔍 Agent Steps (Execution Log) - {len(agent_steps)} steps:")
        for idx, step in enumerate(agent_steps[:8], 1):  # Show first 8 steps
            status_icon = {
                "completed": "✅",
                "failed": "❌",
                "pending": "⏳",
                "in_progress": "🔄",
            }.get(step.get('status', 'unknown'), "❓")
            step_name = step.get('step_name', 'Unknown')
            status = step.get('status', 'unknown')
            duration_ms = step.get('duration_ms')
            print(f"   {idx}. {status_icon} {step_name} [{status}]", end="")
            if duration_ms is not None:
                print(f" ({duration_ms:.1f}ms)")
            else:
                print()
    else:
        print(f"\n🔍 Agent Steps: None (not available)")
    
    # Latency
    latency_ms = data.get("_measured_latency_ms")
    if latency_ms:
        print(f"\n⏱️  Latency: {latency_ms:.1f} ms")
    
    print("\n" + "=" * 80)


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Smoke test for Mortgage Agent API"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--payload",
        type=str,
        default=None,
        help="Path to JSON file with custom payload (optional)"
    )
    
    args = parser.parse_args()
    
    # Load payload
    if args.payload:
        payload_path = Path(args.payload)
        if not payload_path.exists():
            print(f"❌ Payload file not found: {payload_path}", file=sys.stderr)
            sys.exit(1)
        with open(payload_path, "r") as f:
            payload = json.load(f)
    else:
        payload = TEST_PAYLOAD.copy()
    
    # Print test info
    print("=" * 80)
    print("Mortgage Agent Smoke Test")
    print("=" * 80)
    print(f"\n📍 Base URL: {args.base_url}")
    print(f"📝 Endpoint: POST /api/mortgage-agent/run")
    print(f"\n📤 Request Payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    # Call API
    try:
        data = call_api(args.base_url, payload)
        print_response(data, payload=payload)
        
        # Check if OK
        if not data.get("ok", False):
            print("\n❌ Test FAILED: Response indicates error", file=sys.stderr)
            sys.exit(1)
        
        # Check if plans were generated
        plans = data.get("plans", [])
        if not plans:
            print("\n⚠️  Test WARNING: No plans generated", file=sys.stderr)
            sys.exit(0)
        
        # Check new fields: case_state and agent_steps
        case_state = data.get("case_state")
        agent_steps = data.get("agent_steps")
        
        if case_state:
            print("\n✅ Case State: Present and structure looks correct")
        else:
            print("\n⚠️  Case State: Not present (may be None by design)")
        
        if agent_steps:
            step_count = len(agent_steps)
            if 6 <= step_count <= 8:
                print(f"✅ Agent Steps: Present with {step_count} steps (expected range: 6-8)")
            else:
                print(f"⚠️  Agent Steps: Present with {step_count} steps (expected range: 6-8)")
        else:
            print("\n⚠️  Agent Steps: Not present (may be None by design)")
        
        print("\n✅ Test PASSED")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

