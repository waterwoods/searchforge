# already_sent Intent Guard Spec

## Problem

`follow_up_type` used loose markers including **`发你`**. The substring appears inside **questions** such as **`要不要发你`**, causing false **`already_sent`** and the wrong reply / handoff tone.

## Principle

**Intent guard before** treating the message as “materials already sent.” Do not rely on a single keyword that also appears in offers and questions.

## Guard: prospective send offer

`_is_prospective_send_offer_message(msg)` returns true when the utterance is clearly about **whether / whether I should** send, not **I already sent**:

| Pattern (concept) | Example |
|-------------------|---------|
| 要不要 … 发 | 要不要发你 |
| 要不要先 … + 发 | 要不要先发给你 |
| 要不我 … 发 | 要不我发你微信 |

When matched, `_derive_follow_up_type` returns **`new_info`** (not `already_sent`), **after** clarification markers and **before** `sent_markers`.

## Preserved true positives

| Example | Expected |
|---------|----------|
| 材料发你微信了 | `already_sent` |
| 我已经发你微信了 | `already_sent` |
| 截图发你 | Still `already_sent` (via `截图` / `发你` / `发了` as applicable) |

## Explicit non-goals

- NLP “deep understanding” of every Chinese modal.
- Removing all `发你` uses globally (would break short fast-path heuristics); **classification** is what was fixed first.
