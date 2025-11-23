#!/usr/bin/env python3
"""Direct test of prompt construction"""
import sys
sys.path.insert(0, '/home/andy/searchforge')

from services.fiqa_api.utils.llm_client import build_rag_prompt

# Simulate context from actual query results
context = [
    {
        "title": "West LA 2/1 HOUSE with CHEF'S KITCHEN and GARDENS",
        "text": "Beautiful house with chef's kitchen...",
        "price": 263.0,
        "bedrooms": 2,
        "neighbourhood": "West Los Angeles",
        "room_type": "Entire home/apt"
    },
    {
        "title": "Huge 2nd flr bd rm, high ceilings bed & breakfast",
        "text": "Spacious room with high ceilings...",
        "price": 57.0,
        "bedrooms": 1,
        "neighbourhood": "Sawtelle",
        "room_type": "Private room"
    },
    {
        "title": "One Bedroom for rent",
        "text": "Cozy bedroom...",
        "price": 0.0,  # This should be filtered out
        "bedrooms": 0,
        "neighbourhood": "Hollywood Hills West",
        "room_type": "Private room"
    }
]

question = "Find a 2 bedroom place in West LA under $200 per night"

prompt = build_rag_prompt(question, context)

print("=" * 80)
print("PROMPT OUTPUT:")
print("=" * 80)
print(prompt)
print("=" * 80)
print(f"\nPrompt length: {len(prompt)} chars")
print(f"Context items: {len(context)}")

# Check if price appears
if "Price:" in prompt:
    print("\n✅ Price field found in prompt!")
    # Find all price mentions
    import re
    prices = re.findall(r'Price: \$(\d+)/night', prompt)
    print(f"   Prices found: {prices}")
else:
    print("\n❌ Price field NOT found in prompt!")

