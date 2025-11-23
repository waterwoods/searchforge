"""
mortgage.tools - Mortgage Tools Package
========================================
Tools for mortgage-related data (rates, properties, etc.)
"""

from services.fiqa_api.mortgage.tools.property_tool import (
    search_listings_for_zip,
    MOCK_LOCAL_LISTINGS,
)

from services.fiqa_api.mortgage.schemas import LocalListingSummary

__all__ = [
    "search_listings_for_zip",
    "MOCK_LOCAL_LISTINGS",
    "LocalListingSummary",
]

