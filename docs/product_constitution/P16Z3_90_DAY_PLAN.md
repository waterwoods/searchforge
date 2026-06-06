# P16-Z3 90-Day Plan

**Date:** 2026-06-02  
**Sprint:** P16-Z3 — Case Intelligence Master Plan  
**Goal:** **3 offices paying** — same product soul, no platform pivot.  
**Assumption:** Office 1 (Chen Kui) closes in 30-day plan; days 31–90 replicate **process + tune**, not rebuild.

---

## Success definition (day 90)

| Outcome | Measurable criterion |
|---------|---------------------|
| **Paying offices** | **3** (manual invoice each) |
| **MRR equivalent** | ~$150–300/mo (3 × $50–100) |
| **Replication kit** | Day 0 script + observation log template used on office 2 & 3 |
| **Maturity** | L1–L4 ≥85 deployed; L5 ≥70 |
| **Engine stability** | P16-Y CI gate ≥88; no P17 |

---

## What to build (days 31–90)

| Priority | Build (wire/tune only) | Why | When |
|----------|------------------------|-----|------|
| P0 | Append + summary merge hardening from office 1 log | Retention across offices | Days 31–45 |
| P0 | Chinese template pack per lane (from 30+ real cases) | L4 specificity | Days 31–45 |
| P1 | Customer tab on dedicated URL for office 2 | HubSpot soul — deflect「办到哪了」| Days 45–60 |
| P1 | OCR in glance for notice screenshots | Stripe soul — office 2 wedge | Days 45–60 |
| P1 | Observation log → weekly founder review ritual | L5 outcome | Ongoing |
| P2 | Second broker seat (assistant) on same office | Same case ID handoff | Days 60–75 |
| P2 | Urgent queue + waiting_on filters | L3 at scale | Days 60–75 |
| P2 | Lightweight outcome field (resolved / waiting / escalated) | L5 | Days 75–90 |
| P3 | v4 risk badge polish | L4 trust | If log asks |

**Total new architecture:** still **zero**.

---

## What NOT to build (days 31–90)

| Never | Defer past day 90 |
|-------|-------------------|
| P17 platform | Multi-tenant auth |
| Stripe in-app billing | WeChat API sync |
| Full CRM / AMS replacement | Voice/IVR |
| New microservices | PDF-primary intake |
| LLM generation path (unless rules fail battery) | Enterprise SLA admin |
| Full P16-M 50-item UI sprint | Marketing site |
| Claims-first GTM | OCR-first primary intake |
| SimulationAssistant revival | 10+ overlapping batteries |

---

## What to delay (explicit)

| Item | Delay until | Trigger to unpause |
|------|-------------|-------------------|
| Office 3 sales outreach | Day 60 | Office 2 paid |
| Customer self-serve on trial URL | Day 45 | Office 1 testimonial |
| OCR inline paste | Day 50 | ≥3 screenshot cases in log |
| learning_signals product loop | Day 90 | 50+ logged cases |
| Verified resolution billing | Day 90+ | 3 paying + outcome enum |
| Second vertical | Never in 90d | — |

---

## Phase map (days 31–90)

### Days 31–45 — Replicate office 1 (office 2 pipeline)

**Theme:** Prove payment was not a friendship anomaly.

| Work | Measurable outcome |
|------|-------------------|
| Package Day 0 + Day 7 scripts from Chen Kui run | Playbook doc updated with 3 frictions |
| Prospect office 2 (similar profile) | 1 supervised Day 0 scheduled |
| Deploy parity check (`ui_copy`, cold URL) | PASS |
| Tune templates from office 1 log top 5 | Battery ≥88 |
| **Target:** Office 2 **trial started** | Observation log ≥5 rows office 2 |

---

### Days 46–60 — Office 2 payment + customer surface

**Theme:** Reduce broker「办到哪了」load.

| Work | Measurable outcome |
|------|-------------------|
| Customer tab on `*/customer` route (office 2) | 5-second test ≥75 |
| Enable 提交补充 on customer path | ≥1 customer append logged |
| OCR wire if office 2 uses screenshots | ≥2 OCR cases in log |
| Office 2 invoice conversation | Invoice sent |
| **Target:** Office 2 **paid** OR logged objection | 2 paying offices cumulative |

---

### Days 61–75 — Office 3 + assistant seat

**Theme:** Same case, two humans.

| Work | Measurable outcome |
|------|-------------------|
| Assistant uses same case ID (training) | ≥1 handoff row in log |
| Office 3 prospect + Day 0 | Trial started |
| Queue urgency sort shipped | Broker names top-3 urgent without scroll |
| Outcome field lightweight (resolved/waiting) | Logged on ≥5 cases |
| **Target:** 2 paying + office 3 in trial** | 20+ total observation rows |

---

### Days 76–90 — Close third office + harden

**Theme:** Three paying offices, one engine.

| Work | Measurable outcome |
|------|-------------------|
| Office 3 payment close | **3 paying** |
| Testimonials | **2+** (one per office min) |
| CI battery gate on every deploy | No regressions <88 |
| Retire duplicate scripts to OPERATOR_IGNORE_LIST | Operator path ≤10 scripts |
| Maturity rescore | L1–L4 ≥85 |
| **NO-GO check:** If office 2 unpaid day 75 | Pause office 3; fix L3 continuity only |

---

## Build vs process ratio (90 days)

| Category | % of effort |
|----------|-------------|
| Founder process (Day 0, log, invoice) | **55%** |
| Engineer wire/tune | **30%** |
| Engineer new capability | **0%** |
| Strategy/docs | **15%** |

---

## Revenue model (90 days)

| Office | Target monthly | Payment method |
|--------|----------------|----------------|
| 1 Chen Kui | $50–100 | Manual |
| 2 TBD | $50–100 | Manual |
| 3 TBD | $50–100 | Manual |

**Not in 90 days:** Stripe, outcome-based AI pricing, seat expansion.

**Price narrative:** Time saved on cancel + payment + missing-doc lanes — 5+ hours/month at office owner rate.

---

## Kill criteria (stop and fix, do not add offices)

| Signal | Action |
|--------|--------|
| Office 1 churns before day 45 | Stop sales; fix append only |
| Zero two-turn cases across 2 offices | L3 sprint — no new features |
| Battery drops below 85 on deploy | Freeze UI; tune engine |
| All 3 trials fail on SSO/access again | Founder ops failure — not product |

---

## 30-day vs 90-day contrast

| Dimension | 30-day | 90-day |
|-----------|--------|--------|
| Goal | 1 paying | 3 paying |
| Customer tab | Optional week 3 | Office 2 default |
| OCR | Optional | If log proves need |
| Offices in parallel | 1 | Max 1 new trial at a time until 2 paid |
| New capabilities | 0 | 0 |
| Risk | Access/append | Replication + support load |

---

## Document outputs at day 90

| Artifact | Purpose |
|----------|---------|
| Updated `CASE_INTELLIGENCE_MASTER_OUTLINE.md` | SSOT refresh with 3-office learnings |
| Maturity rescore in `CASE_INTELLIGENCE_MATURITY_MODEL.md` | Evidence-based levels |
| `docs/trial/` playbook append | Replicable Day 0 |
| P16-Z4 recommendation (if needed) | **Continuity at scale** — not P17 |

---

*End of P16-Z3 90-Day Plan*
