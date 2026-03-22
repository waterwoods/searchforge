# Driver Phrase Coverage Spec

## Problem

Driver detection relied on a short substring list. Phrases like **`我自己开`** do not contain **`我开`** as consecutive characters, so they were missed. Family / relation micro-phrases (`儿子开`, `女儿开`) were thin vs `孩子开`.

## Approach

Maintain a **single tuple** `_ADD_CAR_DRIVER_MARKERS` used by:

- `_extract_add_car_fields` (via `_text_has_add_car_driver_signal`)
- `_is_fast_path_candidate` (same helper — no drift)

## Minimum phrases (this sprint)

| Phrase | Notes |
|--------|--------|
| 我自己开 | Self-driver, very common |
| 本人开 | Formal self |
| 我一个人开 | Redundant with `我一个人` but explicit |
| 我老婆开 / 我老公开 | Already partially present; kept |
| 儿子开 / 女儿开 | Explicit children |
| 主要驾驶人是我 | Covers 主要驾驶人是我老婆 / 我老公 via prefix match |

## Design rule

High-frequency broker WeChat wording should be **one lexicon edit**, not a new LLM prompt.

## Out of scope

- Parsing structured driver name / license (identity sprint territory).
- Distinguishing primary vs occasional driver beyond boolean “driver context present.”
