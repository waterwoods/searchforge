# Founder Inspection Notes — Unified Intake Readiness

**Use:** Pre-demo / pre-pilot / pre-sales call — **5-minute** discipline check.  
**Date:** 2026-03-25

---

## What to say in one breath (English or 中文)

- Paste messy client text → get a **structured case** (what it is, how urgent, what’s collected, what’s missing, one next step, editable draft).  
- **You confirm before sending** — no auto-send, no inbox hook, no CRM replacement claim.

---

## What to show first

1. **Customer Entry** with **client-specific** URL or `?client=` if demoing a pack.  
2. One **add-car** path that matches `docs/STANDARD_SCENARIO_PACKAGE.md` flagship story.  
3. **Broker Workbench** only after the narrow job lands — otherwise the product looks bigger than the offer.

---

## What to verify mechanically (before a broker session)

- `bash scripts/guardrail_inbox_triage.sh` — expect **PASS** on dev machine.  
- `bash scripts/trial_readiness_check.sh` / `bash scripts/trial_launch_check.sh` — per `AGENTS.md` when approaching real pilot.  
- If claiming production: actually open the **same** frontend + backend pair you will give the broker (pre-broker report flagged URL alignment as unproven in that session).

---

## Known honest caveats (do not hide)

- **Flagship edge case:** dense one-message add-car may show **quote_ready** while **delivery_date** still listed as needed — either demo around it or narrate as “beta nuance under fix.”  
- **Second broker / hot-plug:** Voice swaps work for many paths; **not** honest to claim zero-effort hot-plug until isolation debt is cleared (see second broker drill).  
- **LLM:** Best results may need LLM; guardrails often run rules-only — pilot should assume **human review**.

---

## What not to demo as if it exists

- Inbox sync, OCR, auto-send, carrier completion, multi-tenant login, “we replace your AMS.”

---

## Evidence to collect during pilot

- 3–5 real pastes (redacted) where the broker **edited** the draft — proves workflow fit.  
- One “misfire” example — maps to the next engineering slice without argument.  
- Whether **office** actually used **next move + waiting_on** fields or ignored them.

---

## If you only fix three things next

1. Customer Entry **reads like the product you sell**.  
2. Case card **never contradicts itself** on flagship add-car.  
3. Deploy path **boringly reliable** for the pilot URL.

---

*End of founder inspection notes*
