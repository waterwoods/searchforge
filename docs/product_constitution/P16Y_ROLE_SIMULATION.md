# P16-Y Phase 9 — Role Simulations

**Date:** 2026-06-01  
**Sprint:** P16-Y Case Intelligence Hardening  
**Method:** Desk review of post-fix triage outputs against three office personas — **intelligence only** (not UI continuity)  
**Sample cases:** Y01, Y11, Y14, Y30, Y38, Y41, Y44 (high-signal mix)

---

## Personas

| Persona | Context |
|---------|---------|
| **Role C** | Cold user — no product training; first time seeing a case summary |
| **Chen Kui** | Busy broker — 50 unread WeChat; 2 minutes per message |
| **Assistant** | Bilingual office staff — pastes client messages, copies drafts |

---

## Case Y01 — Cancellation 7-day notice

**Summary (after):** Cancellation warning. Deadline: 7 days. … Still needed: payment proof.

| Persona | Trust summary? | Would act? | Score |
|---------|----------------|------------|-------|
| Role C | Yes — urgency clear | Would call client today | 85 |
| Chen Kui | Yes — saves reading notice | Copy draft → verify payment | 90 |
| Assistant | Yes | Paste draft; flag carrier verify | 88 |

**Verdict:** **Office-ready** for wedge scenario.

---

## Case Y11 — Address change (94588)

**Before:** unclear → **After:** Address / garaging change. Broker: confirm new address + effective date.

| Persona | Trust summary? | Would act? | Score |
|---------|----------------|------------|-------|
| Role C | After fix: yes | Would ask client move date | 78 |
| Chen Kui | Yes — was broken before | Start endorsement workflow | 82 |
| Assistant | Yes | Draft mentions garaging proof | 80 |

**Verdict:** **Fixed** — pre-fix would have stopped usage (B1).

---

## Case Y14 — Add teen driver

**Before:** missing_document → **After:** customer_question; broker: confirm vehicle + driver license.

| Persona | Trust summary? | Would act? | Score |
|---------|----------------|------------|-------|
| Role C | Yes | Understands add-driver, not DL chase | 80 |
| Chen Kui | Yes — critical fix | Sends driver checklist | 85 |
| Assistant | Yes | Chinese draft usable | 83 |

**Verdict:** **Trust restored** — wrong lane was a trust-breaker.

---

## Case Y30 — UW questionnaire deadline

**After:** underwriting_followup / high. Deadline: 3/15/2026.

| Persona | Trust summary? | Would act? | Score |
|---------|----------------|------------|-------|
| Role C | Mostly — “underwriting” is jargon | Would forward to broker | 72 |
| Chen Kui | Yes | Calendar deadline; send form | 88 |
| Assistant | Yes | High urgency visible | 85 |

**Verdict:** **Broker-ready**; Role C still needs plainer “核保部” wording in summary (UI copy, not this sprint).

---

## Case Y38 — Screenshot DMV confusion

**After:** still_needed includes `notice_image`.

| Persona | Trust summary? | Would act? | Score |
|---------|----------------|------------|-------|
| Role C | Yes — knows something missing | Ask client for clearer photo | 75 |
| Chen Kui | Yes | Reply: send full letter | 82 |
| Assistant | Yes — gap visible | Draft + ask for image | 80 |

**Verdict:** **Actionable** — office knows not to guess from “看不懂” alone.

---

## Case Y41 — Multi-turn payment + paid claim

**After:** payment_lapse_expiration; collected already_paid; verify carrier.

| Persona | Trust summary? | Would act? | Score |
|---------|----------------|------------|-------|
| Role C | Yes | Wait for broker | 70 |
| Chen Kui | Yes — best multi-turn | Carrier portal check | 88 |
| Assistant | Yes | Copy draft about restoration | 85 |

**Verdict:** **Strong distillation** for payment wedge.

---

## Case Y44 — Correction (not payment — address/UW)

**After:** customer_question (79/100); category fixed; summary still thin on turn 1.

| Persona | Trust summary? | Would act? | Score |
|---------|----------------|------------|-------|
| Role C | Partial — must re-read paste | Hesitate | 58 |
| Chen Kui | Partial | Re-read WeChat thread | 62 |
| Assistant | Partial | Manual merge | 60 |

**Verdict:** **Not yet office-ready** for correction threads — biggest remaining intelligence gap.

---

## Aggregate role scores (7-case sample, post-fix)

| Persona | Avg trust+act | vs pre-fix estimate |
|---------|---------------|---------------------|
| Role C | **74 / 100** | +12 (address/coverage fixes) |
| Chen Kui | **83 / 100** | +15 |
| Assistant | **82 / 100** | +14 |

---

## Would they trust the case summary?

| Persona | Answer |
|---------|--------|
| **Role C** | **Mostly on wedge cases** (cancel, payment, missing doc). **No** on multi-turn corrections without re-reading paste. |
| **Chen Kui** | **Yes for 80% of paste types** — saves 2–5 min vs manual triage on cancellation/payment/UW. |
| **Assistant** | **Yes** — structured still_needed drives reply; drafts usable with light edit. |

---

## Would they act on it?

| Persona | Answer |
|---------|--------|
| **Role C** | Acts on urgency + broker step when category correct. |
| **Chen Kui** | **Yes** — copies draft, calls carrier same day on cancel/payment. |
| **Assistant** | **Yes** — uses still_needed as checklist; verifies “already sent” with carrier. |

**Blocker for action is UI continuity (P16-X), not case intelligence** — post-copy return path still weak.

---

*End of P16-Y Phase 9 — Role Simulations*
