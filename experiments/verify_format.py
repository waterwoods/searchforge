#!/usr/bin/env python3
"""Verify the new prompt format is being used"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the actual function
from services.fiqa_api.utils.llm_client import build_rag_prompt

context = [
    {
        "title": "West LA 2/1 HOUSE",
        "text": "Beautiful house...",
        "price": 263.0,
        "bedrooms": 2,
        "neighbourhood": "West Los Angeles",
        "room_type": "Entire home/apt"
    }
]

prompt = build_rag_prompt("Find a 2 bedroom place", context)

print("=" * 80)
print("NEW PROMPT FORMAT:")
print("=" * 80)
print(prompt)
print("=" * 80)

# Check format
if "\nPrice:" in prompt or "Price: $" in prompt and "\n" in prompt.split("Price:")[1].split("\n")[0]:
    print("\n✅ NEW FORMAT: Price is on its own line!")
    if "Neighbourhood:" in prompt and "\nNeighbourhood:" in prompt:
        print("✅ NEW FORMAT: Each field on separate line!")
else:
    print("\n❌ OLD FORMAT: Still using comma-separated format")

