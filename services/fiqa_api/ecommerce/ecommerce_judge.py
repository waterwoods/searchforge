"""
ecommerce_judge.py - Rule-based Judge Module for Ecommerce Agent

A simple rule-based judge that validates refund decisions against policy rules.
This module performs deterministic checks to ensure consistency between actual
decisions and expected policy calculations.

Future extension: Can be replaced or augmented with LLM-as-judge for more
sophisticated reasoning.
"""

from typing import Optional, Dict, Any

from .schemas import Order, RefundCalculation, RefundReason
from .tools.refund_tool import check_refund_eligibility, calculate_refund_amount


class RefundJudgement:
    """
    Judge result model for refund decision validation.
    
    This model represents the outcome of rule-based validation checks.
    """
    
    def __init__(
        self,
        is_consistent_with_policy: bool,
        should_block: bool,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize RefundJudgement.
        
        Args:
            is_consistent_with_policy: Whether the decision matches policy rules
            should_block: Whether to block the decision and require manual review
            reason: Brief explanation of the judgement (in English)
            details: Optional dictionary with additional debug information
        """
        self.is_consistent_with_policy = is_consistent_with_policy
        self.should_block = should_block
        self.reason = reason
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert judgement to dictionary for state storage."""
        return {
            "is_consistent_with_policy": self.is_consistent_with_policy,
            "should_block": self.should_block,
            "reason": self.reason,
            "details": self.details,
        }


def judge_refund_decision(
    order: Optional[Order],
    refund: Optional[RefundCalculation],
    refund_eligible: Optional[bool],
    refund_reason: Optional[RefundReason],
) -> RefundJudgement:
    """
    Rule-based judge to validate refund decision against policy.
    
    This function performs deterministic checks:
    1. Validates that required inputs are present
    2. Recalculates expected eligibility and amount using policy tools
    3. Compares actual decision with expected policy calculation
    4. Performs safety checks (e.g., refund amount <= order total)
    
    Args:
        order: Order object (may be None)
        refund: Actual refund calculation result (may be None)
        refund_eligible: Actual refund eligibility decision (may be None)
        refund_reason: Refund reason object (may be None)
    
    Returns:
        RefundJudgement instance with validation results
    """
    # Check 1: Missing required inputs
    if order is None or refund_reason is None:
        return RefundJudgement(
            is_consistent_with_policy=False,
            should_block=True,
            reason="Missing order or refund reason",
            details={"missing_order": order is None, "missing_reason": refund_reason is None},
        )
    
    # Check 2: Recalculate expected values using policy tools
    expected_eligible = check_refund_eligibility(order, refund_reason)
    expected_refund: Optional[RefundCalculation] = None
    
    if expected_eligible:
        expected_refund = calculate_refund_amount(order, refund_reason, items=None)
    
    # Check 3: Compare eligibility consistency
    if refund_eligible != expected_eligible:
        return RefundJudgement(
            is_consistent_with_policy=False,
            should_block=True,
            reason="Refund eligibility does not match policy calculation",
            details={
                "actual_eligible": refund_eligible,
                "expected_eligible": expected_eligible,
            },
        )
    
    # Check 4: Compare amount consistency (only if both are eligible)
    if refund_eligible is True and expected_eligible is True:
        if refund is None and expected_refund is not None:
            return RefundJudgement(
                is_consistent_with_policy=False,
                should_block=True,
                reason="Refund calculation missing but expected by policy",
                details={
                    "expected_amount": expected_refund.eligible_amount,
                    "actual_amount": None,
                },
            )
        
        if refund is not None and expected_refund is not None:
            actual_amount = refund.eligible_amount
            expected_amount = expected_refund.eligible_amount
            amount_diff = abs(actual_amount - expected_amount)
            
            # Use tolerance of 0.01 for floating point comparison
            if amount_diff > 0.01:
                return RefundJudgement(
                    is_consistent_with_policy=False,
                    should_block=True,
                    reason="Refund amount does not match policy calculation",
                    details={
                        "actual_amount": actual_amount,
                        "expected_amount": expected_amount,
                        "difference": amount_diff,
                    },
                )
    
    # Check 5: Safety check - refund amount should not exceed order total
    if refund is not None and refund.eligible_amount > order.total_amount:
        return RefundJudgement(
            is_consistent_with_policy=False,
            should_block=True,
            reason="Refund amount exceeds order total",
            details={
                "refund_amount": refund.eligible_amount,
                "order_total": order.total_amount,
            },
        )
    
    # All checks passed
    return RefundJudgement(
        is_consistent_with_policy=True,
        should_block=False,
        reason="Decision is consistent with policy",
        details={
            "refund_eligible": refund_eligible,
            "refund_amount": refund.eligible_amount if refund else None,
        },
    )
