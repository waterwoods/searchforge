"""
ticket_tool.py - Support Ticket Tool Module

Support ticket tool module for the ecommerce after-sales agent.
Provides functionality to create refund tickets and return tickets.
Currently uses a pure in-memory mock implementation for creating and managing tickets in the after-sales workflow.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SupportTicket(BaseModel):
    """Support ticket model for tracking refund and return requests."""
    ticket_id: str = Field(..., description="Unique ticket identifier")
    order_id: str = Field(..., description="Associated order ID")
    ticket_type: Literal["refund", "return"] = Field(..., description="Ticket type: refund or return")
    status: Literal["open", "in_progress", "closed"] = Field(..., description="Ticket status")
    created_at: datetime = Field(..., description="Ticket creation time (UTC)")
    note: Optional[str] = Field(None, description="Ticket notes")


# Ticket ID auto-increment counter (pure in-memory implementation)
_ticket_counter = 0


def _generate_ticket_id() -> str:
    """
    Generate a unique ticket ID.
    
    Uses a simple auto-increment approach: T + incrementing number.
    
    Returns:
        Ticket ID in format "T{number}", e.g., "T1", "T2"
    """
    global _ticket_counter
    _ticket_counter += 1
    return f"T{_ticket_counter}"


def create_refund_ticket(order_id: str, amount: float, reason: str) -> SupportTicket:
    """
    Create a refund ticket.
    
    In the ecommerce after-sales agent, when a user requests a refund,
    use this function to create a refund ticket.
    The ticket is used to track the refund request processing flow, initial status is "open".
    
    Args:
        order_id: Order ID that needs refund
        amount: Refund amount
        reason: Refund reason description
    
    Returns:
        Created refund ticket object with status "open"
    
    Example:
        >>> ticket = create_refund_ticket("A10001", 79.99, "Item damaged")
        >>> ticket.ticket_id
        'T1'
        >>> ticket.status
        'open'
    """
    ticket_id = _generate_ticket_id()
    note = f"Refund amount: {amount:.2f}, Reason: {reason}"
    
    return SupportTicket(
        ticket_id=ticket_id,
        order_id=order_id,
        ticket_type="refund",
        status="open",
        created_at=datetime.utcnow(),
        note=note,
    )


def create_return_ticket(order_id: str, items: list[str], reason: str) -> SupportTicket:
    """
    Create a return ticket.
    
    In the ecommerce after-sales agent, when a user requests a return,
    use this function to create a return ticket.
    The ticket is used to track the return request processing flow, initial status is "open".
    
    Args:
        order_id: Order ID that needs return
        items: List of item IDs to return
        reason: Return reason description
    
    Returns:
        Created return ticket object with status "open"
    
    Example:
        >>> ticket = create_return_ticket("A10001", ["ITEM001", "ITEM002"], "No longer wanted")
        >>> ticket.ticket_id
        'T2'
        >>> ticket.ticket_type
        'return'
    """
    ticket_id = _generate_ticket_id()
    items_str = ", ".join(items)
    note = f"Return items: [{items_str}], Reason: {reason}"
    
    return SupportTicket(
        ticket_id=ticket_id,
        order_id=order_id,
        ticket_type="return",
        status="open",
        created_at=datetime.utcnow(),
        note=note,
    )
