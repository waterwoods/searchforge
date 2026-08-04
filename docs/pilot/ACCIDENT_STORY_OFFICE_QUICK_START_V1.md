# Accident Story — Office Quick Start (1 page)

**Pilot:** Restricted · Cloud QA · max **5** initial cases · office `qa_canary_synth` (or Founder-approved allowlist)

## Eligible cases
Auto accident intake only. Synthetic / Founder-approved customers. Not Production.

## What AI does
Organizes the customer story into a draft (time / location / injury) and asks **at most 3** missing questions.

## What AI does **not** decide
Coverage, liability, settlement, Claim submit/close, or any lifecycle change.

## Broker confirms facts
In Workbench Brief, read three layers:
1. **客户原始描述**
2. **AI整理草稿** (never treat as fact alone)
3. **客户已确认事实** (office source of truth)

If you see **AI回退**, trust the confirmed layer.

## When AI is wrong
Ask the customer to edit/confirm. Use manual fields. Do not invent facts. Unknown injury stays unknown.

## Support
Use **支持编号** on the Brief. Never paste raw stories, phones, OpenIDs, or invite tokens into tickets.

## When to stop
Unknown→no, PII leak, >3 questions, lifecycle mutation, or fallback unusable → open Stop/Rollback card and disable AI.
