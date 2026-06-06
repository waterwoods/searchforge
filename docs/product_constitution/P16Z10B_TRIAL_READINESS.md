# P16-Z10B Phase 9 — Trial Readiness

**Date:** 2026-06-02  
**Persona:** Chen Kui (broker) · Assistant paste operator

---

## Can Chen Kui manage a 3-day claim?

| Day | Capability | Ready? |
|-----|------------|--------|
| 1 FNOL paste | Templates + evidence checklist | **Yes** |
| 2 Correction / plate fix | Persisted `plate_*`, summary hint | **Yes** |
| 3 Carrier/adjuster wait | `suggested_waiting_on: carrier` | **Yes** (with SOP PATCH) |

**Verdict:** **Yes for supervised pilot** — not unsupervised for total-loss legal disputes without broker review.

---

## Can he avoid reopening WeChat?

| Thread type | Z10B |
|-------------|------|
| Cancel/payment 3-day | Reread 74–80; payment tokens | **Mostly** |
| Claim 3-day | 71% keyword retention | **Mostly** |
| Add-car / remove | Z10A stable | **Yes** |
| UW questionnaire | Stable | **Yes** |

**Need WeChat: 0/10** on Role D journeys — maintained.

**Claims:** 2/10 cases still ≤60% (CL01, CL02, CL07, CL08, CL10) — broker may still peek WeChat for edge literals; core facts on card.

---

## Can he understand…

| Question | Source after Z10B |
|----------|-----------------|
| What happened? | `conversation_summary` + claim `Collected:` hint |
| What changed? | `Customer corrected/clarified` + persisted merge |
| What is waiting? | `suggested_waiting_on` + `still_needed_fields` |
| What to do next? | `broker_next_step` + carrier-verify copy |

---

## Assistant SOP (trial)

1. Paste → save case  
2. Append Day 2–3 → save  
3. If `suggested_waiting_on` present → PATCH match + `next_contact_by` (+1 business day)  
4. Claims: confirm `plate_*` / `claim_amount_*` on card before calling carrier  

---

## Blockers remaining

| Blocker | Severity |
|---------|----------|
| Auto-PATCH waiting_on | Low — intentional |
| Collapsed follow-up UI | Medium — process |
| CL07/CL08 keyword gaps | Low — edge cases |
| Live UI thread not re-run | Medium — run demo validate before broker |

---

## Phase 9 verdict

**TRIAL-READY for 3-day claim with assistant SOP** — Chen Kui can run claim + wait-state threads without reconstructing entire WeChat history, provided he confirms suggested responsibility on the case record.
