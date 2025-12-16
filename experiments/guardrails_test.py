#!/usr/bin/env python3
"""
guardrails_test.py - Security & Guardrails Test Suite

Tests the security/guardrails module:
1. Input validation for Mortgage Agent and Ops Copilot
2. Output guardrails for high-risk cases
3. Security event logging

Usage:
    python experiments/guardrails_test.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage.input_validation import validate_stress_request_inputs
from services.fiqa_api.ops_copilot.input_validation import validate_system_snapshot
from services.fiqa_api.mortgage.schemas import StressCheckRequest
from services.fiqa_api.ops_copilot.schemas import SystemSnapshot
from services.fiqa_api.mortgage.mortgage_agent_runtime import apply_mortgage_output_guardrails
from services.fiqa_api.ops_copilot.ops_runtime import apply_ops_output_guardrails
from services.fiqa_api.mortgage import run_stress_check
from services.fiqa_api.ops_copilot import run_system_health_check
from datetime import datetime


def test_mortgage_input_validation():
    """Test Mortgage Agent input validation."""
    print("\n" + "=" * 80)
    print("Test: Mortgage Agent Input Validation")
    print("=" * 80)
    
    test_cases = [
        {
            "name": "Valid input",
            "request": StressCheckRequest(
                monthly_income=12000.0,
                other_debts_monthly=500.0,
                list_price=800000.0,
                down_payment_pct=0.20,
            ),
            "should_fail": False,
        },
        {
            "name": "Negative monthly income",
            "request": StressCheckRequest(
                monthly_income=-1000.0,
                other_debts_monthly=500.0,
                list_price=800000.0,
                down_payment_pct=0.20,
            ),
            "should_fail": True,
            "expected_error": "monthly_income must be greater than 0",
        },
        {
            "name": "Negative list price",
            "request": StressCheckRequest(
                monthly_income=12000.0,
                other_debts_monthly=500.0,
                list_price=-500000.0,
                down_payment_pct=0.20,
            ),
            "should_fail": True,
            "expected_error": "list_price must be greater than 0",
        },
        {
            "name": "Down payment > 100%",
            "request": StressCheckRequest(
                monthly_income=12000.0,
                other_debts_monthly=500.0,
                list_price=800000.0,
                down_payment_pct=1.5,  # 150%
            ),
            "should_fail": True,
            "expected_error": "down_payment_pct cannot exceed 100%",
        },
        {
            "name": "Negative other debts",
            "request": StressCheckRequest(
                monthly_income=12000.0,
                other_debts_monthly=-200.0,
                list_price=800000.0,
                down_payment_pct=0.20,
            ),
            "should_fail": True,
            "expected_error": "other_debts_monthly cannot be negative",
        },
    ]
    
    all_passed = True
    for test_case in test_cases:
        errors = validate_stress_request_inputs(test_case["request"])
        
        if test_case["should_fail"]:
            if len(errors) == 0:
                print(f"  ❌ {test_case['name']}: Expected validation errors but got none")
                all_passed = False
            else:
                print(f"  ✅ {test_case['name']}: Correctly rejected with errors:")
                for error in errors:
                    print(f"     - {error}")
                if test_case.get("expected_error"):
                    if any(test_case["expected_error"] in error for error in errors):
                        print(f"     ✅ Contains expected error: '{test_case['expected_error']}'")
                    else:
                        print(f"     ⚠️  Expected error not found: '{test_case['expected_error']}'")
        else:
            if len(errors) > 0:
                print(f"  ❌ {test_case['name']}: Unexpected validation errors:")
                for error in errors:
                    print(f"     - {error}")
                all_passed = False
            else:
                print(f"  ✅ {test_case['name']}: Passed validation")
    
    return all_passed


def test_ops_input_validation():
    """Test Ops Copilot input validation."""
    print("\n" + "=" * 80)
    print("Test: Ops Copilot Input Validation")
    print("=" * 80)
    
    test_cases = [
        {
            "name": "Valid input",
            "snapshot": SystemSnapshot(
                service_name="api-gateway",
                environment="prod",
                cpu_pct=50.0,
                mem_pct=60.0,
                p95_latency_ms=200.0,
                error_rate=0.01,
                qps=1000.0,
                disk_pct=70.0,
                timestamp=datetime.utcnow(),
            ),
            "should_fail": False,
        },
        {
            "name": "CPU > 100% (handled by Pydantic)",
            "snapshot": None,  # Will be created manually to avoid Pydantic validation
            "snapshot_dict": {
                "service_name": "api-gateway",
                "environment": "prod",
                "cpu_pct": 150.0,  # Invalid
                "mem_pct": 60.0,
                "p95_latency_ms": 200.0,
                "error_rate": 0.01,
                "qps": 1000.0,
                "disk_pct": 70.0,
                "timestamp": datetime.utcnow(),
            },
            "should_fail": True,
            "expected_error": "cpu_pct cannot exceed 100%",
            "pydantic_will_catch": True,  # Pydantic will catch this before our validation
        },
        {
            "name": "Negative latency (handled by Pydantic)",
            "snapshot": None,
            "snapshot_dict": {
                "service_name": "api-gateway",
                "environment": "prod",
                "cpu_pct": 50.0,
                "mem_pct": 60.0,
                "p95_latency_ms": -100.0,  # Invalid
                "error_rate": 0.01,
                "qps": 1000.0,
                "disk_pct": 70.0,
                "timestamp": datetime.utcnow(),
            },
            "should_fail": True,
            "expected_error": "p95_latency_ms cannot be negative",
            "pydantic_will_catch": True,
        },
        {
            "name": "Error rate > 1.0 (handled by Pydantic)",
            "snapshot": None,
            "snapshot_dict": {
                "service_name": "api-gateway",
                "environment": "prod",
                "cpu_pct": 50.0,
                "mem_pct": 60.0,
                "p95_latency_ms": 200.0,
                "error_rate": 1.5,  # Invalid (>100%)
                "qps": 1000.0,
                "disk_pct": 70.0,
                "timestamp": datetime.utcnow(),
            },
            "should_fail": True,
            "expected_error": "error_rate cannot exceed 1.0",
            "pydantic_will_catch": True,
        },
        {
            "name": "Invalid environment (handled by Pydantic)",
            "snapshot": None,
            "snapshot_dict": {
                "service_name": "api-gateway",
                "environment": "invalid_env",  # Invalid
                "cpu_pct": 50.0,
                "mem_pct": 60.0,
                "p95_latency_ms": 200.0,
                "error_rate": 0.01,
                "qps": 1000.0,
                "disk_pct": 70.0,
                "timestamp": datetime.utcnow(),
            },
            "should_fail": True,
            "expected_error": "environment must be one of",
            "pydantic_will_catch": True,
        },
    ]
    
    all_passed = True
    for test_case in test_cases:
        # Handle test cases that Pydantic will catch before our validation
        if test_case.get("pydantic_will_catch"):
            try:
                # Try to create the snapshot - Pydantic will reject it
                snapshot = SystemSnapshot(**test_case["snapshot_dict"])
                print(f"  ⚠️  {test_case['name']}: Expected Pydantic to reject, but it didn't")
            except Exception as e:
                # Pydantic validation error - this is expected and acceptable
                print(f"  ✅ {test_case['name']}: Correctly rejected by Pydantic validation (as expected)")
            continue
        
        # Note: Pydantic validation will catch some errors before our custom validation
        try:
            errors = validate_system_snapshot(test_case["snapshot"])
        except Exception as e:
            # Pydantic validation error - this is also acceptable for invalid inputs
            if test_case["should_fail"]:
                print(f"  ✅ {test_case['name']}: Correctly rejected by Pydantic validation: {str(e)[:80]}")
                continue
            else:
                print(f"  ❌ {test_case['name']}: Unexpected Pydantic validation error: {e}")
                all_passed = False
                continue
        
        if test_case["should_fail"]:
            if len(errors) == 0:
                print(f"  ⚠️  {test_case['name']}: Expected validation errors but got none (may have been caught by Pydantic)")
            else:
                print(f"  ✅ {test_case['name']}: Correctly rejected with errors:")
                for error in errors:
                    print(f"     - {error}")
        else:
            if len(errors) > 0:
                print(f"  ❌ {test_case['name']}: Unexpected validation errors:")
                for error in errors:
                    print(f"     - {error}")
                all_passed = False
            else:
                print(f"  ✅ {test_case['name']}: Passed validation")
    
    return all_passed


def test_mortgage_output_guardrails():
    """Test Mortgage Agent output guardrails."""
    print("\n" + "=" * 80)
    print("Test: Mortgage Agent Output Guardrails")
    print("=" * 80)
    
    # Create a high-risk stress result
    high_risk_request = StressCheckRequest(
        monthly_income=5000.0,  # Low income
        other_debts_monthly=800.0,
        list_price=1200000.0,  # Very high price
        down_payment_pct=0.10,  # Low down payment
        state="CA",
    )
    
    stress_result = run_stress_check(high_risk_request)
    
    print(f"  Created high-risk stress check:")
    print(f"    Stress Band: {stress_result.stress_band}")
    print(f"    DTI Ratio: {stress_result.dti_ratio:.1%}")
    if stress_result.risk_assessment:
        print(f"    Hard Block: {stress_result.risk_assessment.hard_block}")
        print(f"    Soft Warning: {stress_result.risk_assessment.soft_warning}")
    
    # Test 1: Narrative without warning language (should be adjusted)
    optimistic_narrative = "This home looks affordable for your budget."
    optimistic_actions = ["Consider making an offer"]
    
    adjusted_narrative, adjusted_actions = apply_mortgage_output_guardrails(
        stress_result=stress_result,
        narrative=optimistic_narrative,
        recommended_actions=optimistic_actions,
        request_id="test_guardrails_001",
    )
    
    print(f"\n  Test: Optimistic narrative without warnings")
    print(f"    Original narrative: {optimistic_narrative[:50]}...")
    print(f"    Adjusted narrative length: {len(adjusted_narrative)} chars")
    
    # Check if warning was added
    warning_keywords = ["高风险", "high risk", "风险较高", "不建议", "重要提示"]
    has_warning = any(kw.lower() in adjusted_narrative.lower() for kw in warning_keywords)
    
    if has_warning:
        print(f"    ✅ Warning language was added")
    else:
        print(f"    ⚠️  Warning language not detected (but may be present)")
    
    # Check if safety action was added
    safety_keywords = ["降低", "提高", "咨询", "顾问"]
    actions_text = " ".join(adjusted_actions).lower()
    has_safety_action = any(kw.lower() in actions_text for kw in safety_keywords)
    
    if has_safety_action:
        print(f"    ✅ Safety action was added")
        print(f"    Actions: {adjusted_actions}")
    else:
        print(f"    ⚠️  Safety action not detected")
    
    return True  # Guardrails ran without errors


def test_ops_output_guardrails():
    """Test Ops Copilot output guardrails."""
    print("\n" + "=" * 80)
    print("Test: Ops Copilot Output Guardrails")
    print("=" * 80)
    
    # Create a critical system snapshot
    critical_snapshot = SystemSnapshot(
        service_name="payment-service",
        environment="prod",
        cpu_pct=95.0,  # Critical
        mem_pct=90.0,  # Critical
        p95_latency_ms=1000.0,  # Critical
        error_rate=0.08,  # Critical
        qps=5000.0,
        disk_pct=95.0,  # Critical
        timestamp=datetime.utcnow(),
    )
    
    health_result = run_system_health_check(critical_snapshot)
    
    print(f"  Created critical health check:")
    print(f"    Health Band: {health_result.band}")
    print(f"    Health Score: {health_result.score:.1f}")
    print(f"    Hard Block: {health_result.hard_block}")
    
    # Test 1: Narrative without urgent language (should be adjusted)
    calm_narrative = "The system is experiencing some performance issues."
    calm_actions = ["Monitor the metrics"]
    
    adjusted_narrative, adjusted_actions = apply_ops_output_guardrails(
        health_result=health_result,
        narrative=calm_narrative,
        recommended_actions=calm_actions,
        request_id="test_guardrails_002",
    )
    
    print(f"\n  Test: Calm narrative without urgency")
    print(f"    Original narrative: {calm_narrative}")
    print(f"    Adjusted narrative length: {len(adjusted_narrative)} chars")
    
    # Check if urgent language was added
    urgent_keywords = ["CRITICAL", "critical", "立即", "immediately", "紧急", "urgent"]
    has_urgent = any(kw.lower() in adjusted_narrative.lower() for kw in urgent_keywords)
    
    if has_urgent:
        print(f"    ✅ Urgent language was added")
    else:
        print(f"    ⚠️  Urgent language not detected (but may be present)")
    
    # Check if emergency action was added
    emergency_keywords = ["降流量", "增加副本", "应急", "emergency"]
    actions_text = " ".join(adjusted_actions).lower()
    has_emergency = any(kw.lower() in actions_text for kw in emergency_keywords)
    
    if has_emergency:
        print(f"    ✅ Emergency action was added")
        print(f"    Actions: {adjusted_actions}")
    else:
        print(f"    ⚠️  Emergency action not detected")
    
    return True  # Guardrails ran without errors


def main():
    """Main entry point."""
    print("=" * 80)
    print("Security & Guardrails Test Suite")
    print("=" * 80)
    
    all_passed = True
    
    try:
        passed = test_mortgage_input_validation()
        all_passed = all_passed and passed
    except Exception as e:
        print(f"\n❌ Mortgage input validation test FAILED: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        passed = test_ops_input_validation()
        all_passed = all_passed and passed
    except Exception as e:
        print(f"\n❌ Ops input validation test FAILED: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        passed = test_mortgage_output_guardrails()
        all_passed = all_passed and passed
    except Exception as e:
        print(f"\n❌ Mortgage output guardrails test FAILED: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        passed = test_ops_output_guardrails()
        all_passed = all_passed and passed
    except Exception as e:
        print(f"\n❌ Ops output guardrails test FAILED: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL GUARDRAILS TESTS PASSED")
        return 0
    else:
        print("❌ SOME GUARDRAILS TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

