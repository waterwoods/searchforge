#!/usr/bin/env python3
"""
Mortgage Programs MCP Server

A minimal MCP server that provides a single tool: search_mortgage_programs
to search for mortgage programs and assistance based on user criteria.
"""

import json
from pathlib import Path
from typing import List, Optional

from mcp.server.fastmcp import FastMCP


# Load mortgage programs data
def load_mortgage_programs() -> List[dict]:
    """Load mortgage programs from JSON file."""
    data_file = Path(__file__).parent / "mortgage_programs.json"
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)


# Store programs in memory
MORTGAGE_PROGRAMS = load_mortgage_programs()

# Create MCP server instance using FastMCP
mcp = FastMCP("Mortgage Programs MCP Server")


@mcp.tool()
def search_mortgage_programs(
    zip_code: str,
    state: Optional[str] = None,
    profile_tags: Optional[List[str]] = None,
    current_dti: Optional[float] = None
) -> str:
    """
    Search for matching mortgage programs based on location, profile, and financial criteria.
    
    Matching logic:
    1. State or zip_prefix must match
    2. If profile_tags provided, prioritize programs with matching tags
    3. If current_dti provided, filter programs where max_dti >= current_dti
    4. Sort by: tag match count (desc) -> DTI margin (desc)
    5. Return top 3-5 results
    
    Args:
        zip_code: ZIP code of the property location (e.g., '90803')
        state: State code (e.g., 'CA', 'TX'). Optional but helps narrow results.
        profile_tags: Profile tags such as 'first_time_buyer', 'veteran', 'low_income', 'high_dti', 'senior_60_plus'. Optional.
        current_dti: Current debt-to-income ratio (0.0 to 1.0, e.g., 0.57 for 57%). Optional.
    
    Returns:
        JSON string containing array of matching programs
    """
    if not zip_code:
        raise ValueError("zip_code is required")
    
    zip_prefix = zip_code[:2] if len(zip_code) >= 2 else zip_code
    
    # Filter programs
    candidates = []
    for program in MORTGAGE_PROGRAMS:
        # Check state match
        state_match = False
        if state:
            state_match = state.upper() in [s.upper() for s in program.get("states", [])]
        
        # Check zip prefix match
        zip_match = any(
            zip_prefix.startswith(prefix) 
            for prefix in program.get("zip_prefixes", [])
        )
        
        # Must match either state or zip
        if not (state_match or zip_match):
            continue
        
        # Check DTI if provided
        if current_dti is not None:
            if current_dti > program.get("max_dti", 0.0):
                continue
        
        # Calculate tag match count
        program_tags = set(program.get("profile_tags", []))
        user_tags = set(profile_tags or [])
        tag_match_count = len(program_tags & user_tags)
        
        # Calculate DTI margin
        dti_margin = program.get("max_dti", 0.0) - (current_dti or 0.0)
        
        candidates.append({
            "program": program,
            "state_match": state_match,
            "zip_match": zip_match,
            "tag_match_count": tag_match_count,
            "dti_margin": dti_margin
        })
    
    # Sort: tag match count (desc) -> DTI margin (desc)
    candidates.sort(
        key=lambda x: (x["tag_match_count"], x["dti_margin"]),
        reverse=True
    )
    
    # Take top 5
    top_candidates = candidates[:5]
    
    # Format results
    results = []
    for item in top_candidates:
        program = item["program"]
        
        # Build why_relevant explanation
        why_parts = []
        if item["tag_match_count"] > 0:
            matched_tags = set(program.get("profile_tags", [])) & set(profile_tags or [])
            why_parts.append(f"you match profile tags: {', '.join(matched_tags)}")
        if state and item["state_match"]:
            why_parts.append(f"you are in {state}")
        if current_dti is not None:
            why_parts.append(f"your DTI is {current_dti*100:.1f}% (program allows up to {program.get('max_dti', 0)*100:.1f}%)")
        
        why_relevant = "Because " + ", ".join(why_parts) + f", this program may help by {program.get('benefit_summary', '')}"
        
        result = {
            "id": program.get("id"),
            "name": program.get("name"),
            "description": program.get("description"),
            "benefit_summary": program.get("benefit_summary"),
            "why_relevant": why_relevant
        }
        results.append(result)
    
    # Return as JSON string
    return json.dumps(results, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()

