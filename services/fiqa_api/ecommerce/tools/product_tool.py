"""
product_tool.py - Product data loading and querying tools

This module loads product data from CSV and provides simple query functions
for products. Used by order generation scripts and potentially by frontend/agents.
"""

import csv
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Default CSV path relative to project root
# From tools/ -> ecommerce/ -> fiqa_api/ -> services/ -> project_root
DEFAULT_CSV_PATH = Path(__file__).parent.parent.parent.parent.parent / "data" / "amazon" / "products_sample_2023.csv"


class Product(BaseModel):
    """Product model matching CSV structure."""
    product_id: str = Field(..., description="Unique product identifier")
    title: str = Field(..., description="Product title/name")
    brand: Optional[str] = Field(None, description="Product brand")
    category: Optional[str] = Field(None, description="Product category")
    price: float = Field(..., ge=0, description="Product price")
    rating: Optional[float] = Field(None, description="Product rating")
    ratings_count: Optional[int] = Field(None, description="Number of ratings")
    image_url: str = Field(..., description="Product image URL")
    product_url: Optional[str] = Field(None, description="Product URL")


# Module-level cache for loaded products
_PRODUCTS_BY_ID: Dict[str, Product] = {}
_PRODUCTS_LIST: List[Product] = []


def _load_products_from_csv(csv_path: Path = DEFAULT_CSV_PATH) -> None:
    """
    Load products from CSV file into module-level cache.
    
    Args:
        csv_path: Path to the CSV file containing product data.
    """
    global _PRODUCTS_BY_ID, _PRODUCTS_LIST
    
    if not csv_path.exists():
        logger.warning(f"Product CSV file not found: {csv_path}. Products will be empty.")
        _PRODUCTS_BY_ID = {}
        _PRODUCTS_LIST = []
        return
    
    try:
        _PRODUCTS_BY_ID = {}
        _PRODUCTS_LIST = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Parse price (handle empty strings)
                    price_str = row.get('price', '0').strip()
                    price = float(price_str) if price_str else 0.0
                    
                    # Parse rating (optional)
                    rating_str = row.get('rating', '').strip()
                    rating = float(rating_str) if rating_str else None
                    
                    # Parse ratings_count (optional)
                    ratings_count_str = row.get('ratings_count', '').strip()
                    ratings_count = int(ratings_count_str) if ratings_count_str else None
                    
                    product = Product(
                        product_id=row.get('product_id', '').strip(),
                        title=row.get('title', '').strip(),
                        brand=row.get('brand', '').strip() or None,
                        category=row.get('category', '').strip() or None,
                        price=price,
                        rating=rating,
                        ratings_count=ratings_count,
                        image_url=row.get('image_url', '').strip(),
                        product_url=row.get('product_url', '').strip() or None,
                    )
                    
                    if product.product_id:
                        _PRODUCTS_BY_ID[product.product_id] = product
                        _PRODUCTS_LIST.append(product)
                
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid product row: {row.get('product_id', 'unknown')}, error: {e}")
                    continue
        
        logger.info(f"Loaded {len(_PRODUCTS_LIST)} products from {csv_path}")
    
    except Exception as e:
        logger.error(f"Error loading products from CSV: {e}", exc_info=True)
        _PRODUCTS_BY_ID = {}
        _PRODUCTS_LIST = []


# Load products on module import
_load_products_from_csv()


def get_product(product_id: str) -> Optional[Product]:
    """
    Get a product by its ID.
    
    Args:
        product_id: The product identifier to look up.
    
    Returns:
        The Product if found, otherwise None.
    """
    return _PRODUCTS_BY_ID.get(product_id)


def list_products(limit: int = 20, category: Optional[str] = None) -> List[Product]:
    """
    List products with optional category filter.
    
    Args:
        limit: Maximum number of products to return.
        category: Optional category filter. If provided, only products matching
                 this category will be returned.
    
    Returns:
        List of products, filtered by category if provided, limited to `limit` items.
    """
    products = _PRODUCTS_LIST
    
    if category:
        products = [p for p in products if p.category and p.category.lower() == category.lower()]
    
    return products[:limit]


def get_random_products(n: int = 5, category: Optional[str] = None) -> List[Product]:
    """
    Get random products from the available products.
    
    Args:
        n: Number of random products to return.
        category: Optional category filter. If provided, only products matching
                 this category will be considered.
    
    Returns:
        List of randomly selected products. If fewer than `n` products are available,
        returns all available products.
    """
    products = _PRODUCTS_LIST
    
    if category:
        products = [p for p in products if p.category and p.category.lower() == category.lower()]
    
    if len(products) <= n:
        return products
    
    return random.sample(products, n)
