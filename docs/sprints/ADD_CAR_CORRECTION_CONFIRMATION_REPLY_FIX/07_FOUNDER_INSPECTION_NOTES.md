# Founder Inspection Notes

## What to feel in the product

On the **second customer message** that corrects the car, the reply should **sound like the office switched to the right VIN/year/make in their head** — not like a generic bot that only heard “2024”.

## Quick live checks (after backend deploy)

1. **Honda → Tesla**  
   - T1: `我想加车 2021 Honda`  
   - T2: `不是这个，是 2024 Tesla`  
   - Expect lead: **好的，我按 2024 Tesla 这台车继续。** then zip ask.

2. **Comma correction**  
   - T1: `加车 2024 BMW X5`  
   - T2: `不是X5，是X3`  
   - Expect **BMW X3** (with year) in the lead.

3. **口语**  
   - T2: `不对，是 2024 Tesla` or `搞错了，是2024 Tesla`  
   - Same trust lead as (1).

## Broker checklist

- Conversation summary / structured fields should still show the **corrected** vehicle after correction turns (already merged-customer based).
- No change to **when** we hand off vs collect — only **copy** and **ack** quality.

## Red flags (should not see)

- `好的，2024的。先把…` when the customer clearly said **Tesla** in the same bubble.
- **No** acknowledgement at all on long paste threads right after a short correction line.
