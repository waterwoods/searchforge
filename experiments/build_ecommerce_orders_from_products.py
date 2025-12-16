"""
build_ecommerce_orders_from_products.py - Generate mock orders from product data

This script generates mock orders from product data and saves them to JSON
for use by the order_tool module.

Usage:
    python -m experiments.build_ecommerce_orders_from_products

After running this script, the generated orders will be available at:
    data/ecommerce/orders_sample.json

You can then test the ecommerce agent with these new orders:
    python -m services.fiqa_api.ecommerce.experiments.ecommerce_agent_smoke
"""

import json
import random
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ecommerce.schemas import Order, OrderItem
from services.fiqa_api.ecommerce.tools.product_tool import get_random_products


def generate_orders(num_orders: int = 15) -> list[Dict[str, Any]]:
    """
    Generate mock orders from product data.
    
    Args:
        num_orders: Number of orders to generate.
    
    Returns:
        List of order dictionaries (JSON-serializable).
    """
    # Get random products to use as order items
    products = get_random_products(n=num_orders * 2)  # Get more products than orders
    
    if not products:
        raise ValueError("No products available. Please check product_tool.py and CSV file.")
    
    orders = []
    statuses = ["processing", "shipped", "delivered", "cancelled"]
    # Weight statuses: more delivered orders for refund testing
    status_weights = [0.1, 0.2, 0.6, 0.1]
    
    for i in range(num_orders):
        order_id = f"AMZ{10001 + i:05d}"
        
        # Random status with weights
        status = random.choices(statuses, weights=status_weights)[0]
        
        # Each order has 1-3 items
        num_items = random.randint(1, 3)
        order_products = random.sample(products, min(num_items, len(products)))
        
        items = []
        total_amount = 0.0
        
        for product in order_products:
            quantity = random.randint(1, 2)
            unit_price = product.price
            total_price = quantity * unit_price
            total_amount += total_price
            
            items.append({
                "item_id": product.product_id,
                "product_name": product.title,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price,
            })
        
        # Generate metadata with days_since_delivery for refund testing
        # Only add metadata for delivered orders
        metadata = {}
        if status == "delivered":
            # Distribute days: some within 7 days, some 7-30 days, some >30 days
            days_options = [0, 3, 5, 10, 15, 25, 40, 60]
            metadata["days_since_delivery"] = random.choice(days_options)
        
        order_dict = {
            "order_id": order_id,
            "user_id": f"user_{random.randint(10000, 99999)}",
            "items": items,
            "total_amount": round(total_amount, 2),
            "status": status,
            "metadata": metadata,
        }
        
        orders.append(order_dict)
    
    return orders


def main():
    """Main function to generate and save orders."""
    print("Generating orders from product data...")
    
    # Generate orders
    orders = generate_orders(num_orders=15)
    
    # Create output directory if it doesn't exist
    output_dir = Path(__file__).parent.parent / "data" / "ecommerce"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "orders_sample.json"
    
    # Save to JSON
    output_data = {"orders": orders}
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Count products loaded (use list_products with a large limit to count)
    from services.fiqa_api.ecommerce.tools.product_tool import list_products
    num_products = len(list_products(limit=10000))
    
    print(f"Loaded {num_products} products, generated {len(orders)} orders")
    print(f"Saved to {output_path}")
    print(f"\nOrder IDs: {', '.join([o['order_id'] for o in orders[:5]])}...")


if __name__ == "__main__":
    main()
