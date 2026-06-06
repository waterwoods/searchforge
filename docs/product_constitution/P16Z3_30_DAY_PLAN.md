# P16-Z3 30-Day Plan

**Date:** 2026-06-02  
**Sprint:** P16-Z3 — Case Intelligence Master Plan  
**Goal:** **First paying office** (Chen Kui) — not platform, not P17, not enterprise.  
**Team:** 1 founder · 1 engineer · 1 pilot office  
**Method:** Revive · wire · tune · deploy · observe — **zero new capabilities**

---

## Success definition (day 30)

| Outcome | Measurable criterion |
|---------|---------------------|
| **First payment received** | Manual invoice paid (Zelle/Venmo/WeChat) |
| **Behavioral proof** | Chen Kui sent ≥1 client draft **without Andy on phone** |
| **Continuity proof** | ≥1 two-turn case in observation log (paste → copy → append → copy) |
| **Quality gate** | `guardrail_inbox_triage.sh` PASS + P16-Y battery ≥88 on deploy |
| **Maturity** | L1–L4 composite ≥78; L5 process ≥60 |

---

## Week 1 — Access + single-turn wedge (L1, L2, L4)

**Theme:** Chen Kui can open URL, paste cancel chaos, copy Chinese draft in <45s.

### Deliverables

| # | Work | Owner | Type |
|---|------|-------|------|
| 1 | FP-004 Preview SSO disabled | Founder | Ops |
| 2 | Redeploy + `trial_launch_check.sh` PASS | Dev | Deploy |
| 3 | Cold URL curl E2E (founder) | Founder | QA |
| 4 | Chinese broker_next_step templates (cancel, payment, missing-doc) | Dev | Tune |
| 5 | EN/ZH mix removed from glance + queue | Dev | Copy |
| 6 | P16-M TOP5: trust line, demo demotion, cancel-first tagline | Dev | Copy |
| 7 | Generic broker_next_step blocklist | Dev | Tune |
| 8 | Invoice payment IDs filled | Founder | Commercial |
| 9 | Observation log protocol started — row 1 | Founder | Process |

### Measurable outcomes (end of week 1)

| Metric | Target |
|--------|--------|
| Trial URL reachable without SSO | **100%** |
| Cancel paste → copy latency (founder timed) | **<45s** |
| P16-Y battery on deployed build | **≥88 avg** |
| Observation log rows | **≥1** |
| Supervised Day 0 scheduled | **Date set** |

### Do NOT do week 1

- Customer tab on trial URL  
- OCR-first intake  
- P17 / new pages  
- LLM path rewrite  

---

## Week 2 — Continuity + supervised trial (L3, L5)

**Theme:** Chen Kui returns when client replies; Andy logs real cases.

### Deliverables

| # | Work | Owner | Type |
|---|------|-------|------|
| 10 | Post-copy CTA:「客户回复了？追加到此案件」| Dev | Wire |
| 11 | P16-Y P0: append summary merge | Dev | Tune |
| 12 | Promote append box on case reopen | Dev | Wire |
| 13 | waiting_on pill + deadline countdown in glance | Dev | Wire |
| 14 | deadline_mentioned → still_needed (cancel/UW) | Dev | Tune |
| 15 | **Supervised Chen Kui Day 0** (30–120 min) | Founder | Process |
| 16 | Andy logs 3 real cases in observation log | Founder | Process |
| 17 | P16-Y battery gate in CI pre-deploy | Dev | Automate |
| 18 | Surface v4 risk as「需核实」badge (optional) | Dev | Wire |

### Measurable outcomes (end of week 2)

| Metric | Target |
|--------|--------|
| Supervised Day 0 completed | **Yes** |
| Real cases in observation log | **≥3** |
| Two-turn case logged (Andy or Chen Kui) | **≥1** |
| Append CTA visible after copy | **Yes** |
| Chen Kui used product Day 2 without Andy | **Attempted** (OK if guided once) |

### Do NOT do week 2

- Unsupervised multi-office rollout  
- Stripe  
- Full P16-M UI sprint  
- Claims/OCR as primary story  

---

## Week 3 — Payment conversation + optional depth (L5, L6 partial)

**Theme:** Convert evidence to invoice; wire OCR only if broker asks.

### Deliverables

| # | Work | Owner | Type |
|---|------|-------|------|
| 19 | Day 7 check-in script executed | Founder | Process |
| 20 | Observation log ≥7 rows | Founder | Process |
| 21 | Invoice sent with time-saved narrative | Founder | Commercial |
| 22 | `bill_sent_claimed` heuristic (Y45) | Dev | Tune |
| 23 | OCR wire on broker upload + [OCR] tags (if cancel screenshots needed) | Dev | Wire |
| 24 | Customer tab on separate URL (only if Chen Kui requests) | Dev | Expose |
| 25 | Urgent-today queue sort | Dev | Wire |

### Measurable outcomes (end of week 3)

| Metric | Target |
|--------|--------|
| Observation log rows | **≥7** |
| Chen Kui unsupervised client draft sent | **≥1** |
| Invoice delivered | **Yes** |
| Payment conversation held | **Yes** |
| Testimonial ask made | **Yes** (even if deferred) |

---

## Week 4 — Close payment + harden (L5)

**Theme:** First paying office or explicit NO-GO with logged reasons.

### Deliverables

| # | Work | Owner | Type |
|---|------|-------|------|
| 26 | Payment received OR structured objection logged | Founder | Commercial |
| 27 | Observation log ≥10 rows | Founder | Process |
| 28 | Fix only top-3 items from log (no feature sprawl) | Dev | Tune/wire |
| 29 | Testimonial captured (1 sentence) | Founder | Commercial |
| 30 | P16-Z3 retrospective: maturity rescore | Founder | Strategy |

### Measurable outcomes (end of week 30)

| Metric | Target |
|--------|--------|
| **Paying offices** | **1** |
| Testimonial | **1** (or written objection) |
| Two-turn cases logged | **≥2** |
| guardrail PASS on production | **Yes** |
| Maturity L1–L4 | **≥78** |

---

## Resource split

| Role | Week 1 | Week 2 | Week 3 | Week 4 |
|------|--------|--------|--------|--------|
| **Engineer** | Deploy + L4 copy + L2 tune | L3 append UX + merge | OCR optional + tune | Log-driven fixes only |
| **Founder** | SSO + log + E2E | Day 0 + 3 cases | Invoice + Day 7 | Payment + testimonial |

**Engineer days (total):** ~8–10 focused days — not 30 days of building.

---

## Risk triggers (week-level)

| Signal | Response |
|--------|----------|
| SSO still on day 3 | Stop all dev; fix ops |
| Day 0 no-show week 2 | Reschedule; do not add features |
| Chen Kui reverts to WeChat-only week 2 | Fix append CTA + merge before new features |
| Battery <85 on deploy | No new UI until tune passes |
| Payment refused week 4 | Log objection; sell continuity not Cap 4 |

---

## One-line week summary

| Week | One line |
|------|----------|
| 1 | **Open the door** — URL works, cancel paste wins |
| 2 | **Teach the loop** — append + Day 0 |
| 3 | **Ask for money** — invoice + evidence |
| 4 | **Get paid or learn** — payment + testimonial |

---

*End of P16-Z3 30-Day Plan*
