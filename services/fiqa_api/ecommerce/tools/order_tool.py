"""
order_tool.py - Order lookup tools for e-commerce after-sales agent

This module provides simple tool functions to look up order information
from a mock in-memory database. Used by LangGraph workflows.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from ..schemas import Order, OrderItem

logger = logging.getLogger(__name__)


class OrderQueryResult(BaseModel):
    """Query result containing order information for agent use."""
    order_id: str = Field(..., description="Unique order identifier")
    status: str = Field(..., description="Order status")
    total_amount: float = Field(..., ge=0, description="Total order amount")
    items: list[OrderItem] = Field(..., description="List of order items")
    created_at: Optional[str] = Field(None, description="Order creation timestamp (ISO format)")
    user_id: Optional[str] = Field(None, description="User identifier")


# Default JSON path relative to project root
# From tools/ -> ecommerce/ -> fiqa_api/ -> services/ -> project_root
DEFAULT_ORDERS_JSON_PATH = Path(__file__).parent.parent.parent.parent.parent / "data" / "ecommerce" / "orders_sample.json"


def _load_orders_from_file(json_path: Path = DEFAULT_ORDERS_JSON_PATH) -> dict[str, Order]:
    """
    Load orders from JSON file.
    
    Args:
        json_path: Path to the JSON file containing orders.
    
    Returns:
        Dictionary mapping order_id to Order objects.
    """
    if not json_path.exists():
        logger.debug(f"Orders JSON file not found: {json_path}")
        return {}
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        orders = {}
        orders_list = data.get("orders", [])
        
        for order_dict in orders_list:
            try:
                # Extract metadata if present (not part of Order model)
                metadata = order_dict.pop("metadata", {})
                
                # Convert items to OrderItem objects
                items = [
                    OrderItem(**item_dict)
                    for item_dict in order_dict.get("items", [])
                ]
                
                # Create Order object
                order = Order(
                    order_id=order_dict["order_id"],
                    user_id=order_dict.get("user_id"),
                    items=items,
                    total_amount=order_dict["total_amount"],
                    status=order_dict["status"],
                )
                
                # Dynamically add metadata if present
                if metadata:
                    object.__setattr__(order, "metadata", metadata)
                
                orders[order.order_id] = order
            
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid order: {order_dict.get('order_id', 'unknown')}, error: {e}")
                continue
        
        logger.info(f"Loaded {len(orders)} orders from {json_path}")
        return orders
    
    except Exception as e:
        logger.error(f"Error loading orders from JSON: {e}", exc_info=True)
        return {}


# Mock in-memory database (fallback)
MOCK_ORDERS: dict[str, Order] = {
    "A10001": Order(
        order_id="A10001",
        user_id="user_12345",
        items=[
            OrderItem(
                item_id="ITEM001",
                product_name="Wireless Headphones",
                quantity=1,
                unit_price=79.99,
                total_price=79.99,
            ),
            OrderItem(
                item_id="ITEM002",
                product_name="USB-C Cable",
                quantity=2,
                unit_price=12.50,
                total_price=25.00,
            ),
        ],
        total_amount=104.99,
        status="delivered",
    ),
    "A10002": Order(
        order_id="A10002",
        user_id="user_67890",
        items=[
            OrderItem(
                item_id="ITEM003",
                product_name="Laptop Stand",
                quantity=1,
                unit_price=45.00,
                total_price=45.00,
            ),
        ],
        total_amount=45.00,
        status="shipped",
    ),
    "A10003": Order(
        order_id="A10003",
        user_id="user_11111",
        items=[
            OrderItem(
                item_id="ITEM004",
                product_name="Mechanical Keyboard",
                quantity=1,
                unit_price=129.99,
                total_price=129.99,
            ),
            OrderItem(
                item_id="ITEM005",
                product_name="Mouse Pad",
                quantity=1,
                unit_price=15.00,
                total_price=15.00,
            ),
        ],
        total_amount=144.99,
        status="processing",
    ),
    "A10004": Order(
        order_id="A10004",
        user_id="user_22222",
        items=[
            OrderItem(
                item_id="ITEM006",
                product_name="Smart Watch",
                quantity=1,
                unit_price=199.99,
                total_price=199.99,
            ),
        ],
        total_amount=199.99,
        status="delivered",
    ),
    "A10005": Order(
        order_id="A10005",
        user_id="user_33333",
        items=[
            OrderItem(
                item_id="ITEM007",
                product_name="Gaming Mouse",
                quantity=1,
                unit_price=59.99,
                total_price=59.99,
            ),
        ],
        total_amount=59.99,
        status="delivered",
    ),
}

# Mock creation timestamps (for demo purposes)
MOCK_ORDER_TIMESTAMPS: dict[str, str] = {
    "A10001": "2024-01-15T10:30:00Z",
    "A10002": "2024-01-20T14:22:00Z",
    "A10003": "2024-01-25T09:15:00Z",
    "A10004": "2024-01-15T10:30:00Z",
    "A10005": "2024-01-01T10:30:00Z",  # Early order for testing timeout scenarios
}

# Add metadata to certain orders (for refund time window checks)
# Since Order model doesn't have a metadata field, we dynamically add the attribute
def _setup_order_metadata():
    """Set up metadata (days_since_delivery) for test orders."""
    # A10001: Delivered, assumed within time window (for testing)
    order_a10001 = MOCK_ORDERS.get("A10001")
    if order_a10001:
        object.__setattr__(order_a10001, "metadata", {"days_since_delivery": 5})
    
    # A10004: Delivered 3 days ago (eligible for refund)
    order_a10004 = MOCK_ORDERS.get("A10004")
    if order_a10004:
        object.__setattr__(order_a10004, "metadata", {"days_since_delivery": 3})
    
    # A10005: Delivered 10 days ago (exceeds 7-day limit for NO_LONGER_WANTED, but within 30-day limit for DAMAGED_OR_DEFECTIVE)
    order_a10005 = MOCK_ORDERS.get("A10005")
    if order_a10005:
        object.__setattr__(order_a10005, "metadata", {"days_since_delivery": 10})

# Initialize order metadata
_setup_order_metadata()

# Try to load orders from JSON file, fallback to MOCK_ORDERS
ORDER_DB: dict[str, Order] = _load_orders_from_file()
if not ORDER_DB:
    logger.info("No orders loaded from JSON file, using fallback MOCK_ORDERS")
    ORDER_DB = MOCK_ORDERS
else:
    # Merge MOCK_ORDERS into ORDER_DB for backward compatibility
    # (in case some tests still use A10001, A10002, etc.)
    for order_id, order in MOCK_ORDERS.items():
        if order_id not in ORDER_DB:
            ORDER_DB[order_id] = order


def get_order(order_id: str) -> Optional[Order]:
    """
    Look up an order by ID in the mock database.
    
    Args:
        order_id: The order identifier to look up.
    
    Returns:
        The Order if found, otherwise None.
    """
    return ORDER_DB.get(order_id)


def get_order_or_raise(order_id: str) -> Order:
    """
    Same as get_order, but raises a ValueError if the order is not found.
    
    Args:
        order_id: The order identifier to look up.
    
    Returns:
        The Order if found.
    
    Raises:
        ValueError: If the order_id does not exist in MOCK_ORDERS.
    """
    order = get_order(order_id)
    if order is None:
        raise ValueError(f"Order not found: {order_id}")
    # Ensure returned order has metadata (set to empty dict if missing)
    if not hasattr(order, "metadata"):
        object.__setattr__(order, "metadata", {})
    return order


def get_order_query_result(order_id: str) -> OrderQueryResult:
    """
    Build an OrderQueryResult for the given order_id.
    
    This is the main function that the LangGraph node / tools layer will call.
    It looks up the order, maps Order -> OrderQueryResult, and fills in
    status, total_amount, items, created_at, etc.
    
    Args:
        order_id: The order identifier to look up.
    
    Returns:
        OrderQueryResult containing the order information.
    
    Raises:
        ValueError: If the order_id does not exist in ORDER_DB.
    """
    order = get_order_or_raise(order_id)
    
    # Try to get created_at from MOCK_ORDER_TIMESTAMPS (for backward compatibility)
    # For new orders from JSON, created_at will be None
    created_at = MOCK_ORDER_TIMESTAMPS.get(order_id)
    
    return OrderQueryResult(
        order_id=order.order_id,
        status=order.status,
        total_amount=order.total_amount,
        items=order.items,
        created_at=created_at,
        user_id=order.user_id,
    )