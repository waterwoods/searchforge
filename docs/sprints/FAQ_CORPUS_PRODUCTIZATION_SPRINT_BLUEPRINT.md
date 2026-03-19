# FAQ Corpus Productization Sprint — Blueprint

**Sprint:** FAQ Corpus Productization  
**Date:** 2026-03-14  
**Target:** Chen Kui Insurance Unified Entry

---

## Why Productizing the FAQ Corpus Matters Now

The auto-insurance FAQ intake corpus sprint identified 25 realistic question groups with handling frameworks and routing recommendations. That research is only valuable if it becomes **product material** the founder can inspect and the system can use.

- **Realism:** Corpus reflects real customer phrasing (mixed language, shorthand, broker-forwarded context).
- **Routing:** Each item has recommended route (FAST / LLM / human_confirmation).
- **Gap:** Corpus lives in config; product logic and scenarios are not fully aligned.

Productizing means: **select a smaller, sharper set → turn it into Simulation Assistant scenarios, routing improvements, and an operating doc → make it founder-visible.**

---

## How This Helps Realism, Routing, and Pilot Readiness

| Dimension | Before | After |
|-----------|--------|-------|
| **Realism** | Generic fallbacks for some high-frequency cases | Product responds with broker-natural wording for top 5–8 types |
| **Routing** | FAST path exists but not fully aligned with corpus | FAST candidates (already_sent, what_to_send, add_car_field) strengthened |
| **Pilot** | Founder sees internal logic only | Founder sees: customer asks → system responds → still need → route |

---

## What "Good Enough Productization" Looks Like

- **5–8 question types** selected and justified
- **Simulation Assistant:** 5–8 new or improved scenarios with realistic phrasing
- **FAST path:** Strengthened for already_sent, what_to_send, add_car_field where safe
- **FAQ handling matrix:** One doc the office can use: customer asks X → office says Y → still need Z → human confirms when
- **Founder showcase:** Each selected type has a founder-readable example (customer asks, system responds, still need, route)

---

## In Scope

- Selection of top 5–8 question types from corpus
- Simulation Assistant scenario additions/updates
- FAST path improvements for safest types
- FAQ handling matrix / operating doc
- Founder-readable examples for each selected type

---

## Out of Scope

- Expanding the corpus (25 items is enough)
- New API endpoints or UI changes
- Multi-tenant or auth
- Other verticals beyond auto insurance
