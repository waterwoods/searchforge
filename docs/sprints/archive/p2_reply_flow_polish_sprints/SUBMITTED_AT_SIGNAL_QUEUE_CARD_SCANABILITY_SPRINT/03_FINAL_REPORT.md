# SUBMITTED AT SIGNAL + QUEUE CARD SCANABILITY — Final report

## What was implemented

- **Customer (post-handoff)**: Replaced single “送达时间 + created_at” with **primary `updated_at` label**, optional **first-create line** when `created_at ≠ updated_at`, and a **truth footnote** (no discrete submit event in DB).
- **Office `报送与送达`**: When lifecycle is formally submitted, **lead timestamp line uses `updated_at`**, then `created_at` if different; added **proxy explanation** string from client pack.
- **Queue cards (Add-Car)**: New **scan line** — phase label + **最近活动** + formatted `updated_at`; **compact preview** prefixes phase + activity for Add-Car.
- **Copy snapshot (workbench)**: Clipboard summary uses **updated_at-first** wording aligned with the above.

## What remains partial

- **True `submitted_at`** would require backend persistence of the lifecycle transition event; until then **`updated_at`** is the honest operational proxy (and moves on append).

## What still depends on backend/state quality

- If **`updated_at`** is missing on an edge response, UI falls back to **`created_at`** where coded; rare for persisted cases.
- **Lifecycle** must remain authoritative for “formally submitted” vs handoff_pending.

## Recommended next sprint

- **Persist optional `handed_off_at` (or lifecycle transition log)** when `handed_off` is first set—then swap primary line to that field without changing queue layout.
