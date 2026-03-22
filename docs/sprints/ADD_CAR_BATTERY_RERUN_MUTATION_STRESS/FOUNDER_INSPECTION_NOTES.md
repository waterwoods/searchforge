# Founder Inspection Notes — Add-Car Battery + Mutation Stress

**Date:** 2026-03-21  
**Branch context:** Chen Kui Insurance / Unified Entry (rule-path evaluation).

## TL;DR

- **17** original Add-Car battery scenarios + **18** ACE edge sims + **69** multi-turn sims (includes ACE) + full **guardrail** — **all green**.
- **10** new mutation cases around ZIP / driver / materials intent — **0 trust-breaking**, **8 strong**, **2 acceptable** (generic handoff on “要不要发” style questions—safe but not eloquent).

## What to skim in a demo

- **ZIP:** `邮编95131`, `zip95131`, bare `95131`, and dense single-bubble Chinese — all reach `quote_ready` with sensible broker text.
- **Materials intent:** “我已经发你微信了，截图发你了” → customer copy acknowledges sent materials + broker says verify WeChat (**good**).
- **Gap:** “材料要不要先发给你” / “要不我发你微信…” → **does not** falsely claim materials received (**good**), but reply could more directly answer the question (**polish**).

## Chen Kui angle

Add-Car is **more broker-safe** than before on the three hardened surfaces; remaining risk is **conversational polish** on material-send **questions**, not classification disasters.

## Out of scope reminder

Office-hours random questions (ACB-E07 turn 1) still look awkward—treat as separate FAQ routing, not Add-Car regression.
