"""
schemas.py - Ecommerce After-Sales Agent Data Models
=====================================================
Pydantic models for ecommerce after-sales agent request/response.

These models define the API contract for ecommerce after-sales service.
Keep design simple, clear, and extensible - only include essential fields
for after-sales scenarios (order, items, status, amount, user issue).
"""

from typing import Dict, Any, List, Literal, Optional

from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    """Order item model representing a single product in an order."""
    item_id: str = Field(..., description="Unique item identifier")
    product_name: str = Field(..., description="Product name")
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    unit_price: float = Field(..., ge=0, description="Unit price")
    total_price: float = Field(..., ge=0, description="Total price for this item (quantity * unit_price)")


class Order(BaseModel):
    """Order model containing order information."""
    order_id: str = Field(..., description="Unique order identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    items: List[OrderItem] = Field(..., description="List of order items")
    total_amount: float = Field(..., ge=0, description="Total order amount")
    status: Literal["pending", "processing", "shipped", "delivered", "cancelled", "refunded"] = Field(
        ..., description="Order status"
    )


class EcommerceAgentRequest(BaseModel):
    """Ecommerce after-sales agent request model."""
    user_message: str = Field(..., description="User's question or issue description")
    order_id: Optional[str] = Field(None, description="Order ID if user is inquiring about a specific order")
    order: Optional[Order] = Field(None, description="Order information if provided directly")


class EcommerceAgentResponse(BaseModel):
    """Ecommerce after-sales agent response model."""
    ok: bool = Field(..., description="Success status")
    response_message: str = Field(..., description="Agent's response to the user")
    suggested_actions: List[str] = Field(
        default_factory=list,
        description="List of suggested actions or next steps"
    )
    error: Optional[str] = Field(None, description="Error message if ok=False")


class RefundReason(BaseModel):
    """Refund reason model for refund requests."""
    reason_type: Literal["NO_LONGER_WANTED", "DAMAGED_OR_DEFECTIVE", "WRONG_ITEM", "OTHER"] = Field(
        ..., description="Type of refund reason"
    )
    description: Optional[str] = Field(None, description="Detailed description of the refund reason")


class RefundCalculation(BaseModel):
    """Refund calculation result model."""
    eligible_amount: float = Field(..., ge=0, description="Eligible refund amount")
    reason: str = Field(..., description="Reason description for the refund calculation")
    policy_reference: str = Field(..., description="Reference to the refund policy used")


class AgentStep(BaseModel):
    """Agent step log model for tracking each step in the ecommerce agent workflow."""
    step_id: str = Field(..., description="Unique step identifier")
    step_name: str = Field(..., description="Human-readable step name")
    status: Literal["pending", "in_progress", "completed", "failed", "done"] = Field(
        ..., description="Step execution status"
    )
    timestamp: str = Field(..., description="ISO timestamp when step was recorded")
    duration_ms: Optional[float] = Field(None, description="Step duration in milliseconds")
    inputs: Optional[Dict[str, Any]] = Field(None, description="Step inputs (lightweight, avoid large objects)")
    outputs: Optional[Dict[str, Any]] = Field(None, description="Step outputs (lightweight, avoid large objects)")
    error: Optional[str] = Field(None, description="Error message if status is 'failed'")


__all__ = [
    "OrderItem",
    "Order",
    "EcommerceAgentRequest",
    "EcommerceAgentResponse",
    "RefundReason",
    "RefundCalculation",
    "AgentStep",
]
