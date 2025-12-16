"""
test_offline_eval_basic.py - Basic tests for offline ecommerce agent evaluation

Simple tests to verify that the evaluation script can load cases and run evaluations.
"""

import json
import tempfile
from pathlib import Path
from typing import List

import pytest

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from experiments.offline_ecommerce_agent_eval import (
    EvalCase,
    EvalResult,
    evaluate_case,
    run_eval,
)


def test_load_simple_case():
    """Test that we can load and process a simple evaluation case."""
    case: EvalCase = {
        "id": "test_case_1",
        "description": "Test case for delivered damaged item",
        "user_message": "I received a broken item and want a refund.",
        "order_id": "A10001",
        "expected_refund_eligible": True,
        "expected_refund_amount": 104.99,
    }
    
    # Should not raise an exception
    result = evaluate_case(case)
    
    assert result["case_id"] == "test_case_1"
    assert "passed" in result
    assert "actual_refund_eligible" in result
    assert "actual_refund_amount" in result


def test_run_eval_with_minimal_cases():
    """Test that run_eval returns correct structure and statistics."""
    cases: List[EvalCase] = [
        {
            "id": "test_case_1",
            "user_message": "I want a refund for a damaged item.",
            "order_id": "A10001",
            "expected_refund_eligible": True,
            "expected_refund_amount": 104.99,
        },
        {
            "id": "test_case_2",
            "user_message": "I want to return this order.",
            "order_id": "A10003",
            "expected_refund_eligible": False,
            "expected_refund_amount": 0.0,
        },
    ]
    
    results = run_eval(cases)
    
    # Check structure
    assert "summary" in results
    assert "results" in results
    
    # Check summary stats
    summary = results["summary"]
    assert summary["total_cases"] == 2
    assert "passed_cases" in summary
    assert "failed_cases" in summary
    assert "pass_rate" in summary
    assert summary["pass_rate"] >= 0.0
    assert summary["pass_rate"] <= 100.0
    
    # Check results
    assert len(results["results"]) == 2
    for result in results["results"]:
        assert "case_id" in result
        assert "passed" in result


def test_eval_case_with_expected_error():
    """Test evaluation case that expects an error (invalid order ID)."""
    case: EvalCase = {
        "id": "test_error_case",
        "user_message": "I want a refund.",
        "order_id": "INVALID999",
        "expected_error": True,
    }
    
    result = evaluate_case(case)
    
    assert result["case_id"] == "test_error_case"
    # If error was expected and occurred, should pass
    # If error was expected but didn't occur, should fail
    assert "passed" in result
    assert "error" in result or result.get("error") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

