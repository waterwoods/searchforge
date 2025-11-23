"""
search_profiles.py - Search Profile Definitions
================================================
Defines search profiles that provide default filtering and sorting strategies
for specific use cases (e.g., Airbnb Search Lab).

Each profile can specify:
- Default collection
- Default filters (price_max, min_bedrooms, neighbourhood, room_type, etc.)
- Weighting configuration (for future use)

Profiles are merged with explicit request parameters, with request parameters
taking precedence over profile defaults.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class SearchProfile:
    """Search profile with default configuration."""
    collection: str
    default_filters: Dict[str, Any]
    weighting: Dict[str, float]
    
    def __post_init__(self):
        """Ensure default_filters and weighting are initialized."""
        if self.default_filters is None:
            self.default_filters = {}
        if self.weighting is None:
            self.weighting = {}


# Profile definitions
PROFILES: Dict[str, SearchProfile] = {
    "default": SearchProfile(
        collection="fiqa",
        default_filters={},
        weighting={},
    ),
    
    "airbnb_la_location_first": SearchProfile(
        collection="airbnb_la_demo",
        default_filters={
            # Reasonable defaults for Airbnb LA demo
            # These are suggestions, not strict filters
            "price_max": 200.0,
            "min_bedrooms": 1,
        },
        weighting={
            "location": 2.0,
            "semantic": 1.0,
        },
    ),
}


def get_search_profile(name: Optional[str] = None) -> SearchProfile:
    """
    Get search profile by name.
    
    Args:
        name: Profile name (e.g., "airbnb_la_location_first")
             If None or unknown, returns "default" profile.
    
    Returns:
        SearchProfile instance
    """
    if name is None or name not in PROFILES:
        return PROFILES["default"]
    return PROFILES[name]




