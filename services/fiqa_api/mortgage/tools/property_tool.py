"""
property_tool.py - Property/Real Estate Tool
============================================
Tool for fetching property listings, sample properties, or market data.

Future: Replace stub implementation with real property database/API integration.
"""

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

from services.fiqa_api.mortgage.schemas import LocalListingSummary


class MortgageProperty(BaseModel):
    """Mortgage property model for sample listings."""
    id: str
    name: str
    city: str
    state: str
    purchase_price: float
    property_tax_rate_pct: float  # Annual tax rate as percentage (e.g., 1.2 for 1.2%)
    hoa_monthly: float
    note: Optional[str] = None


# Sample properties (mock data)
_SAMPLE_PROPERTIES = [
    MortgageProperty(
        id="prop_001",
        name="Long Beach condo near ocean",
        city="Long Beach",
        state="CA",
        purchase_price=750000.0,
        property_tax_rate_pct=1.2,
        hoa_monthly=350.0,
        note="2BR/2BA, ocean view, walkable to beach",
    ),
    MortgageProperty(
        id="prop_002",
        name="Seattle suburban family home",
        city="Bellevue",
        state="WA",
        purchase_price=950000.0,
        property_tax_rate_pct=1.0,
        hoa_monthly=0.0,
        note="3BR/2.5BA, good schools, quiet neighborhood",
    ),
    MortgageProperty(
        id="prop_003",
        name="Austin starter home",
        city="Austin",
        state="TX",
        purchase_price=450000.0,
        property_tax_rate_pct=2.0,
        hoa_monthly=150.0,
        note="2BR/1BA, fixer-upper potential, central location",
    ),
    MortgageProperty(
        id="prop_004",
        name="Portland modern townhouse",
        city="Portland",
        state="OR",
        purchase_price=650000.0,
        property_tax_rate_pct=1.1,
        hoa_monthly=280.0,
        note="3BR/2BA, new construction, energy efficient",
    ),
    MortgageProperty(
        id="prop_005",
        name="San Francisco luxury condo",
        city="San Francisco",
        state="CA",
        purchase_price=1500000.0,
        property_tax_rate_pct=1.3,
        hoa_monthly=850.0,
        note="2BR/2BA, downtown, high-end finishes",
    ),
]


def get_sample_properties(
    location: Optional[str] = None,
    price_range: Optional[Tuple[float, float]] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get sample property listings.
    
    Args:
        location: Optional location filter (e.g., "Seattle, WA", "CA")
        price_range: Optional tuple of (min_price, max_price)
        limit: Maximum number of properties to return
    
    Returns:
        List of property dictionaries with keys:
            - property_id: str
            - address: str
            - price: float
            - bedrooms: int
            - bathrooms: float
            - sqft: int
            - location: str
    
    Note: This is a stub implementation. Future versions will fetch
    real property data from databases or external APIs.
    """
    # Return empty list for now - will be populated with real data later
    return []


def get_sample_properties_list() -> List[MortgageProperty]:
    """
    Get sample property listings as MortgageProperty objects.
    
    Returns:
        List of MortgageProperty instances (3-5 sample properties)
    """
    return _SAMPLE_PROPERTIES.copy()


def get_property_by_id(property_id: str) -> Optional[MortgageProperty]:
    """
    Get a property by its ID from the sample list.
    
    Args:
        property_id: Property ID string
    
    Returns:
        MortgageProperty instance if found, None otherwise
    """
    for prop in _SAMPLE_PROPERTIES:
        if prop.id == property_id:
            return prop
    return None


# ========================================
# Local Listings (Mock Data)
# ========================================

MOCK_LOCAL_LISTINGS: List[LocalListingSummary] = [
    # Southern California - 90803 (Long Beach area)
    LocalListingSummary(
        listing_id="ca_90803_001",
        title="2BR condo near beach",
        city="Long Beach",
        state="CA",
        zip_code="90803",
        list_price=680000.0,
        hoa_monthly=350.0,
        beds=2,
        baths=2.0,
        sqft=1100,
    ),
    LocalListingSummary(
        listing_id="ca_90803_002",
        title="1BR waterfront studio",
        city="Long Beach",
        state="CA",
        zip_code="90803",
        list_price=485000.0,
        hoa_monthly=280.0,
        beds=1,
        baths=1.0,
        sqft=750,
    ),
    LocalListingSummary(
        listing_id="ca_90803_003",
        title="3BR townhouse with garage",
        city="Long Beach",
        state="CA",
        zip_code="90803",
        list_price=825000.0,
        hoa_monthly=420.0,
        beds=3,
        baths=2.5,
        sqft=1450,
    ),
    # Southern California - 92648 (Huntington Beach)
    LocalListingSummary(
        listing_id="ca_92648_001",
        title="2BR beach condo",
        city="Huntington Beach",
        state="CA",
        zip_code="92648",
        list_price=750000.0,
        hoa_monthly=380.0,
        beds=2,
        baths=2.0,
        sqft=1200,
    ),
    LocalListingSummary(
        listing_id="ca_92648_002",
        title="1BR modern apartment",
        city="Huntington Beach",
        state="CA",
        zip_code="92648",
        list_price=525000.0,
        hoa_monthly=220.0,
        beds=1,
        baths=1.0,
        sqft=850,
    ),
    LocalListingSummary(
        listing_id="ca_92648_003",
        title="3BR family home",
        city="Huntington Beach",
        state="CA",
        zip_code="92648",
        list_price=980000.0,
        hoa_monthly=0.0,
        beds=3,
        baths=2.0,
        sqft=1650,
    ),
    # Austin, TX - 78701
    LocalListingSummary(
        listing_id="tx_78701_001",
        title="2BR downtown loft",
        city="Austin",
        state="TX",
        zip_code="78701",
        list_price=525000.0,
        hoa_monthly=320.0,
        beds=2,
        baths=2.0,
        sqft=1100,
    ),
    LocalListingSummary(
        listing_id="tx_78701_002",
        title="1BR modern studio",
        city="Austin",
        state="TX",
        zip_code="78701",
        list_price=420000.0,
        hoa_monthly=180.0,
        beds=1,
        baths=1.0,
        sqft=750,
    ),
    LocalListingSummary(
        listing_id="tx_78701_003",
        title="3BR historic home",
        city="Austin",
        state="TX",
        zip_code="78701",
        list_price=675000.0,
        hoa_monthly=0.0,
        beds=3,
        baths=2.5,
        sqft=1600,
    ),
    # Austin, TX - 73301
    LocalListingSummary(
        listing_id="tx_73301_001",
        title="2BR starter home",
        city="Austin",
        state="TX",
        zip_code="73301",
        list_price=450000.0,
        hoa_monthly=150.0,
        beds=2,
        baths=1.5,
        sqft=1100,
    ),
    LocalListingSummary(
        listing_id="tx_73301_002",
        title="3BR ranch style",
        city="Austin",
        state="TX",
        zip_code="73301",
        list_price=580000.0,
        hoa_monthly=0.0,
        beds=3,
        baths=2.0,
        sqft=1450,
    ),
    # Irvine, CA - 92705
    LocalListingSummary(
        listing_id="ca_92705_001",
        title="2BR modern condo",
        city="Irvine",
        state="CA",
        zip_code="92705",
        list_price=650000.0,
        hoa_monthly=350.0,
        beds=2,
        baths=2.0,
        sqft=1150,
    ),
    LocalListingSummary(
        listing_id="ca_92705_002",
        title="1BR apartment near UCI",
        city="Irvine",
        state="CA",
        zip_code="92705",
        list_price=480000.0,
        hoa_monthly=250.0,
        beds=1,
        baths=1.0,
        sqft=800,
    ),
    LocalListingSummary(
        listing_id="ca_92705_003",
        title="3BR townhouse with yard",
        city="Irvine",
        state="CA",
        zip_code="92705",
        list_price=850000.0,
        hoa_monthly=400.0,
        beds=3,
        baths=2.5,
        sqft=1500,
    ),
    LocalListingSummary(
        listing_id="ca_92705_004",
        title="2BR starter home",
        city="Irvine",
        state="CA",
        zip_code="92705",
        list_price=720000.0,
        hoa_monthly=300.0,
        beds=2,
        baths=2.0,
        sqft=1200,
    ),
]


def search_listings_for_zip(
    zip_code: str,
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
    limit: int = 10,
) -> List[LocalListingSummary]:
    """
    Search for listings in a given ZIP code with optional price filtering.
    
    Args:
        zip_code: ZIP code to search (case-insensitive, trimmed)
        max_price: Optional maximum price filter
        min_price: Optional minimum price filter
        limit: Maximum number of results to return (default: 10)
    
    Returns:
        List of LocalListingSummary instances matching the criteria,
        sorted by list_price ascending, limited to `limit` results.
        Returns empty list if no matches found.
    
    Examples:
        >>> listings = search_listings_for_zip("90803", max_price=700000)
        >>> len(listings) > 0
        True
        
        >>> listings = search_listings_for_zip("99999")
        >>> len(listings) == 0
        True
    """
    # Normalize ZIP code (trim whitespace, convert to string)
    zip_code_clean = str(zip_code).strip()
    
    # Filter by ZIP code (case-insensitive matching)
    matching_listings = [
        listing for listing in MOCK_LOCAL_LISTINGS
        if listing.zip_code == zip_code_clean
    ]
    
    # Apply price filters if provided
    if min_price is not None:
        matching_listings = [
            listing for listing in matching_listings
            if listing.list_price >= min_price
        ]
    
    if max_price is not None:
        matching_listings = [
            listing for listing in matching_listings
            if listing.list_price <= max_price
        ]
    
    # Sort by list_price ascending
    matching_listings.sort(key=lambda x: x.list_price)
    
    # Apply limit
    return matching_listings[:limit]


__all__ = [
    "get_sample_properties",
    "get_sample_properties_list",
    "get_property_by_id",
    "MortgageProperty",
    "search_listings_for_zip",
    "MOCK_LOCAL_LISTINGS",
]

