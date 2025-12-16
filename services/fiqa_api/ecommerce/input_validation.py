"""
input_validation.py - Input Validation for Ecommerce Agent Requests
====================================================================
Lightweight validation layer for EcommerceAgentRequest before entering LangGraph.

This module provides deterministic validation rules (no LLM) to check:
- Order ID format and existence
- User message completeness and relevance

All validation returns structured results rather than raising exceptions.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field

from services.fiqa_api.ecommerce.schemas import EcommerceAgentRequest
from services.fiqa_api.ecommerce.tools.order_tool import get_order


class InputValidationError(BaseModel):
    """Structured error result for validation failures."""
    code: Literal[
        "MISSING_ORDER_ID",
        "INVALID_ORDER_ID_FORMAT",
        "ORDER_NOT_FOUND",
        "EMPTY_MESSAGE",
        "MESSAGE_TOO_SHORT",
        "MESSAGE_NOT_REFUND_RELATED",
    ] = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="User-friendly error message.")
    details: Optional[str] = Field(None, description="Optional technical detail for logging.")


class InputValidationResult(BaseModel):
    """Validation result model."""
    is_valid: bool = Field(..., description="Whether the input is considered valid.")
    error: Optional[InputValidationError] = Field(
        None, description="Present if validation failed."
    )


def validate_ecommerce_request(request: EcommerceAgentRequest) -> InputValidationResult:
    """
    Validate an EcommerceAgentRequest before processing.
    
    Performs deterministic checks on:
    1. Order ID: presence, format, and existence
    2. User message: presence, length, and basic relevance
    
    Args:
        request: The ecommerce agent request to validate.
    
    Returns:
        InputValidationResult with is_valid flag and optional error details.
    
    Raises:
        Exception: Only in extreme cases (e.g., get_order call fails unexpectedly).
    """
    # 1. Validate order_id
    order_id = request.order_id
    if not order_id or not order_id.strip():
        return InputValidationResult(
            is_valid=False,
            error=InputValidationError(
                code="MISSING_ORDER_ID",
                message="Please provide an order ID so we can look up your purchase.",
            ),
        )
    
    order_id = order_id.strip()
    
    # Format check: at least 6 characters, starts with "A" or "AMZ"
    if len(order_id) < 6 or not (order_id.startswith("A") or order_id.startswith("AMZ")):
        return InputValidationResult(
            is_valid=False,
            error=InputValidationError(
                code="INVALID_ORDER_ID_FORMAT",
                message="The order ID format looks unusual. Please check and try again.",
                details=f"Expected format: starts with 'A' or 'AMZ', at least 6 characters. Got: '{order_id}'",
            ),
        )
    
    # Check if order exists
    try:
        order = get_order(order_id)
        if order is None:
            return InputValidationResult(
                is_valid=False,
                error=InputValidationError(
                    code="ORDER_NOT_FOUND",
                    message="We could not find this order. Please double-check the order ID.",
                    details=f"Order ID '{order_id}' not found in database.",
                ),
            )
    except Exception as e:
        # Re-raise unexpected errors from get_order
        raise Exception(f"Unexpected error while checking order existence: {e}") from e
    
    # 2. Validate user_message
    user_message = request.user_message
    if not user_message or not user_message.strip():
        return InputValidationResult(
            is_valid=False,
            error=InputValidationError(
                code="EMPTY_MESSAGE",
                message="Please briefly describe your issue so we can help you.",
            ),
        )
    
    user_message = user_message.strip()
    
    # Check minimum length
    if len(user_message) < 5:
        return InputValidationResult(
            is_valid=False,
            error=InputValidationError(
                code="MESSAGE_TOO_SHORT",
                message="Your message is too short. Please add a bit more detail.",
                details=f"Message length: {len(user_message)} characters (minimum: 5).",
            ),
        )
    
    # Simple relevance check: look for refund/return related keywords
    message_lower = user_message.lower()
    refund_keywords = [
        "refund", "return", "exchange", "broken", "damaged", "defective",
        "不想要", "退货", "退款"
    ]
    
    has_refund_keyword = any(keyword in message_lower for keyword in refund_keywords)
    if not has_refund_keyword:
        return InputValidationResult(
            is_valid=False,
            error=InputValidationError(
                code="MESSAGE_NOT_REFUND_RELATED",
                message="It seems your message may not be about a refund or return. Please clarify your request.",
                details="Message does not contain common refund/return keywords.",
            ),
        )
    
    # All checks passed
    return InputValidationResult(is_valid=True, error=None)
