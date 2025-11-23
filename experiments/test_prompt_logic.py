#!/usr/bin/env python3
"""Test prompt construction logic directly"""

# Simulate the build_rag_prompt logic
context = [
    {
        "title": "West LA 2/1 HOUSE with CHEF'S KITCHEN and GARDENS",
        "text": "Beautiful house with chef's kitchen and gardens. Perfect for families.",
        "price": 263.0,
        "bedrooms": 2,
        "neighbourhood": "West Los Angeles",
        "room_type": "Entire home/apt"
    },
    {
        "title": "Huge 2nd flr bd rm, high ceilings bed & breakfast",
        "text": "Spacious room with high ceilings. Great location near restaurants.",
        "price": 57.0,
        "bedrooms": 1,
        "neighbourhood": "Sawtelle",
        "room_type": "Private room"
    },
    {
        "title": "One Bedroom for rent",
        "text": "Cozy bedroom in shared house.",
        "price": 0.0,  # This should be filtered out
        "bedrooms": 0,
        "neighbourhood": "Hollywood Hills West",
        "room_type": "Private room"
    }
]

question = "Find a 2 bedroom place in West LA under $200 per night"

# Replicate build_rag_prompt logic
context_lines = [
    "You are a helpful assistant that answers questions based on the provided context.",
    "The context may include structured fields (e.g., price, bedrooms, location) in addition to text descriptions.",
    "Use ALL available information from the context to answer the question.",
    "If the context doesn't contain enough information, say so clearly. Do not make up information.\n",
    f"Question: {question}\n",
    "Context:",
]

limited_context = context[:10]

for i, item in enumerate(limited_context, 1):
    title = item.get("title", f"Document {i}")
    text = item.get("text", item.get("content", ""))
    if len(text) > 1000:
        text = text[:1000] + "..."
    
    context_parts = [f"\n[{i}] {title}"]
    
    structured_info = []
    if "neighbourhood" in item and item.get("neighbourhood"):
        structured_info.append(f"Neighbourhood: {item['neighbourhood']}")
    if "room_type" in item and item.get("room_type"):
        structured_info.append(f"Room Type: {item['room_type']}")
    if "price" in item and item.get("price") is not None:
        price_val = item.get("price")
        if isinstance(price_val, (int, float)) and price_val > 0:
            structured_info.append(f"Price: ${price_val:.0f}/night")
    if "bedrooms" in item and item.get("bedrooms") is not None:
        bedrooms_val = item.get("bedrooms")
        if isinstance(bedrooms_val, (int, float)) and bedrooms_val > 0:
            bedrooms_str = f"{int(bedrooms_val)} bedroom{'s' if bedrooms_val > 1 else ''}"
            structured_info.append(f"Bedrooms: {bedrooms_str}")
    
    if structured_info:
        context_parts.append(", ".join(structured_info))
    if text:
        context_parts.append(text)
    
    context_lines.append("\n".join(context_parts))

context_lines.append("\nAnswer based on the context above:")

prompt = "\n".join(context_lines)

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
    import re
    prices = re.findall(r'Price: \$(\d+)/night', prompt)
    print(f"   Prices found: {prices}")
    if "263" in prompt:
        print("   ⚠️  Price $263 found (but query asks for under $200)")
    if "57" in prompt:
        print("   ✅ Price $57 found (under $200 requirement)")
else:
    print("\n❌ Price field NOT found in prompt!")

# Check format visibility
print("\n" + "=" * 80)
print("FORMAT ANALYSIS:")
print("=" * 80)
lines = prompt.split('\n')
for i, line in enumerate(lines):
    if "Price:" in line or "Bedrooms:" in line:
        print(f"Line {i+1}: {line[:100]}")

