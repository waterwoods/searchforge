"""
refund_tool.py - Refund Tool Module

Refund tool module for the ecommerce after-sales agent.
Provides refund eligibility checking and refund amount calculation functionality.
Currently uses simplified mock rules that can be replaced with real business logic later.
"""

from typing import Optional

from ..schemas import Order, OrderItem, RefundReason, RefundCalculation


# Business rule constants
MAX_DAYS_NO_LONGER_WANTED = 7
MAX_DAYS_DAMAGED_OR_DEFECTIVE = 30
PARTIAL_REFUND_RATE = 0.8  # Refund rate for NO_LONGER_WANTED type (80%)


def _get_days_since_delivery(order: Order) -> int:
    """
    Get the number of days since order delivery.
    
    Attempts to retrieve from order.metadata, returns 0 if not available.
    This is a temporary implementation that needs to be improved later.
    
    Args:
        order: Order object
    
    Returns:
        Number of days since delivery, returns 0 if unavailable
    """
    # TODO: Real implementation should fetch days_since_delivery from order metadata or database
    # Current implementation: try to get from metadata, if not present assume within time limit (return 0)
    if hasattr(order, "metadata") and isinstance(order.metadata, dict):
        return order.metadata.get("days_since_delivery", 0)
    return 0


def check_refund_eligibility(order: Order, reason: RefundReason) -> bool:
    """
    Check if an order meets refund eligibility requirements.
    
    Business rules:
    - Only orders with status "delivered" or "shipped" are eligible for refunds
    - For "NO_LONGER_WANTED" reason type, requires days_since_delivery <= 7
    - For "DAMAGED_OR_DEFECTIVE" reason type, allows up to 30 days
    - All other cases return False
    
    Args:
        order: Order object
        reason: Refund reason
    
    Returns:
        True if order meets refund eligibility, False otherwise
    """
    # Only "delivered" or "shipped" orders are eligible for refunds
    if order.status not in ("delivered", "shipped"):
        return False
    
    # Check time limits based on refund reason type
    if reason.reason_type == "NO_LONGER_WANTED":
        if order.status == "delivered":
            days = _get_days_since_delivery(order)
            return days <= MAX_DAYS_NO_LONGER_WANTED
        return False
    
    elif reason.reason_type == "DAMAGED_OR_DEFECTIVE":
        if order.status == "delivered":
            days = _get_days_since_delivery(order)
            return days <= MAX_DAYS_DAMAGED_OR_DEFECTIVE
        elif order.status == "shipped":
            # Items that are shipped but not yet delivered can also request refunds
            return True
        return False
    
    # Other refund reason types are not currently supported
    return False


def calculate_refund_amount(
    order: Order,
    reason: RefundReason,
    items: Optional[list[OrderItem]] = None,
) -> RefundCalculation:
    """
    Calculate refund amount.
    
    Business rules:
    - If items is None, refunds the entire order (amount = sum of all item total_price)
    - If items are provided, only calculates refund for those items
    - "DAMAGED_OR_DEFECTIVE" reason allows full refund
    - "NO_LONGER_WANTED" reason allows 80% refund (20% deduction)
    
    Args:
        order: Order object
        reason: Refund reason
        items: Optional list of items to refund; if None, refunds entire order
    
    Returns:
        RefundCalculation instance containing calculated refund amount and related information
    """
    # Determine the list of items to calculate refund for
    if items is None:
        # Refund entire order
        refund_items = order.items
    else:
        # Refund only specified items
        refund_items = items
    
    # Calculate base refund amount (sum of total_price for all refund items)
    base_amount = sum(item.total_price for item in refund_items)
    
    # Calculate actual refund amount based on reason type
    if reason.reason_type == "DAMAGED_OR_DEFECTIVE":
        # Full refund for damaged or defective items
        eligible_amount = base_amount
        reason_desc = "full_refund_damaged"
    elif reason.reason_type == "NO_LONGER_WANTED":
        # 80% refund for change of mind
        eligible_amount = base_amount * PARTIAL_REFUND_RATE
        reason_desc = "partial_refund_change_of_mind"
    else:
        # Other reason types not supported, return 0
        eligible_amount = 0.0
        reason_desc = "refund_not_applicable"
    
    return RefundCalculation(
        eligible_amount=eligible_amount,
        reason=reason_desc,
        policy_reference="return_policy_v1",
    )