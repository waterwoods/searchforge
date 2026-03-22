# Add-Car Hybrid Intake Recommendation Spec

## Decision

**Ship hybrid (Mode C)** for Add-Car as the default commercial posture: **optional structured short card** + **existing conversational triage** (single pipeline).

## What “hybrid” means (concrete)

1. **Entry choice (customer):**
   - Tap **获取报价** → sends one-line starter (existing).
   - Or fill **加车报价 · 快速填写** → composes a single first message and submits with `softRoute: add_car` (implemented in this sprint).
   - Or free-text / paste only (unchanged).

2. **Structured fields in the short intake (v1):**

   | Field | Purpose |
   |-------|---------|
   | Year | Rating / vehicle ID |
   | Make/model | Vehicle identification |
   | ZIP | Territory / garaging |
   | Delivery / pickup timing | Office scheduling |
   | Primary driver | Household / assignment |

   **Not in v1 card:** VIN (optional accelerator via attachment flow elsewhere), name/phone (contact-lite continues from text or follow-up).

3. **What stays free-text**

   - Corrections, “already sent,” side questions, emotional context, carrier emails pasted, multi-intent blobs.

4. **How follow-up works**

   - Unchanged: system replies use `next_best_question`, `still_needed_fields`, `quote_ready_status`; customer continues in the same thread.

5. **First commercial version includes**

   - Visible hybrid card on **empty** Customer Entry state (discovery).
   - Composed Chinese broker-style sentence: “我想给新车加保报价。年份：…；车型：…；…”
   - Same API as chat (`triageMessage` + conversation turns).

## What comes next (not this sprint)

- English mirror copy for the composed template if product is bilingual at entry.
- Collapse card by default after first use (A/B).
- Pre-fill from URL params for broker-sent links.
