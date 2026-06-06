# P16-Z2 Phase 9 — 30-Day Strategic Roadmap

**Date:** 2026-06-01  
**Sprint:** P16-Z2 Case Intelligence Strategic Reverse Engineering  
**Constraints:** 1 founder + 1 developer · 2–3 weeks to paid pilot · 1 office (Chen Kui)

---

## Strategic frame

**Do not build new capabilities.** Revive, wire, tune, and deploy what archaeology found.

**Sell:** "Cases ready to act" — not messages processed, not platform features.

**Wedge scenario:** Cancellation / UW notice (urgent, deadline-driven, high pain).

---

## Ranking legend

| Tier | Meaning |
|------|---------|
| **Must Build** | Pilot blocked without it |
| **Should Build** | Strongly improves payment odds |
| **Can Wait** | Week 3+ or post-payment |
| **Never Build** | Distraction per P16Z2_TOP50 |

---

## Week 1 (Days 1–7): Access + Broker Loop

**Theme:** Chen Kui can open URL, paste cancel notice, copy draft, know what's next.

### Must Build

| # | Item | Owner | Cap | Effort |
|---|------|-------|-----|--------|
| M1 | Disable Preview SSO (FP-004) | Founder | 1, 7 | 5 min |
| M2 | Redeploy + `trial_launch_check.sh` PASS | Dev | 7 | 0.5 day |
| M3 | Chinese-only broker_next_step templates (cancel, payment, add-car) | Dev | 2, 3 | 1 day |
| M4 | Fix EN/ZH mix in glance + queue (F-005) | Dev | 1 | 0.5 day |
| M5 | Post-copy CTA: "客户回复了？追加到此案件" | Dev | 5 | 0.5 day |
| M6 | P16-Y P0: append summary merge | Dev | 2 | 1–2 days |
| M7 | Generic wording blocklist in case_draft_engine | Dev | 2 | 0.5 day |
| M8 | Andy: fill invoice payment IDs | Founder | 6 | 30 min |
| M9 | Andy: observation log protocol + row 1 | Founder | 6 | 1 hour |
| M10 | Andy: founder E2E log on deployed URL | Founder | 7 | 1 hour |

### Should Build

| # | Item | Owner | Cap | Effort |
|---|------|-------|-----|--------|
| S1 | P16-M TOP5 copy fixes (trust line, demo demotion) | Dev | 1 | 0.5 day |
| S2 | waiting_on pill in broker glance | Dev | 5 | 0.5 day |
| S3 | Deadline countdown from deadline_mentioned | Dev | 2 | 0.5 day |
| S4 | Promote append box when case reopened (P16-M #28) | Dev | 5 | 0.5 day |
| S5 | Surface v4 risk as「需核实」badge | Dev | 3 | 0.5 day |

### Can Wait

- Customer tab on trial URL
- OCR upload
- Urgent-today filter
- Follow-up editor unhide

### Never Build

- P17, Stripe, new microservices, customer portal rewrite

### Week 1 exit criteria

- [ ] Cold Preview URL works without Andy
- [ ] Cancel notice paste → Chinese draft → copy in <45s
- [ ] Append to same case works with merged summary
- [ ] `guardrail_inbox_triage.sh` PASS
- [ ] Observation log row 1 exists

---

## Week 2 (Days 8–14): Trial Live + Evidence

**Theme:** Supervised Chen Kui Day 0; collect proof; second case type.

### Must Build

| # | Item | Owner | Cap | Effort |
|---|------|-------|-----|--------|
| M11 | Supervised Chen Kui Day 0 session | Founder | 6 | 2 hours |
| M12 | Chen Kui ui_copy.json deploy parity | Dev | 1 | 0.5 day |
| M13 | P16-Y battery ≥88 in CI or pre-deploy gate | Dev | 2, 7 | 0.5 day |
| M14 | Correction keyword rules (Y44 fix) | Dev | 2 | 0.5 day |
| M15 | Duplicate-case UX fix (top paste when case open) | Dev | 3 | 0.5 day |
| M16 | "Mark sent / waiting on customer" after copy | Dev | 5 | 0.5 day |

### Should Build

| # | Item | Owner | Cap | Effort |
|---|------|-------|-----|--------|
| S6 | Urgent-today queue filter or sort | Dev | 1, 5 | 1 day |
| S7 | Vision API keys on pilot + OCR upload test | Dev/Ops | 2 | 0.5 day |
| S8 | OCR fields in glance with [OCR] tag | Dev | 2, 3 | 0.5 day |
| S9 | Payment notice template excellence | Dev | 2 | 0.5 day |
| S10 | 5 real cases in observation log | Founder | 6 | ongoing |

### Can Wait

- CustomerEntryTab on separate route
- PDF extraction
- Full activity timeline
- Mobile optimization pass

### Week 2 exit criteria

- [ ] Chen Kui processed ≥3 real cases (supervised)
- [ ] ≥1 case used append path successfully
- [ ] Broker feedback captured in observation log
- [ ] Time-saved estimate documented (even manual)
- [ ] Invoice sent

---

## Week 3 (Days 15–21): Payment + Testimonial

**Theme:** Prove ROI; get paid; decide post-pilot scope.

### Must Build

| # | Item | Owner | Cap | Effort |
|---|------|-------|-----|--------|
| M17 | Payment received (Zelle/Venmo/WeChat) | Founder | 6 | — |
| M18 | Testimonial or written quote | Founder | 6 | — |
| M19 | Day 7 review: what worked / what didn't | Founder | 6 | 1 hour |
| M20 | Fix top 3 friction items from observation log | Dev | 1–5 | 2 days |

### Should Build

| # | Item | Owner | Cap | Effort |
|---|------|-------|-----|--------|
| S11 | Customer tab on shareable URL (if broker requests) | Dev | 4 | 1–2 days |
| S12 | 我的办理 status for customer self-check | Dev | 4 | 1 day |
| S13 | Add-car path polish (if primary broker request) | Dev | 2, 4 | 1–2 days |
| S14 | Delete SimulationAssistant.tsx | Dev | 7 | 15 min |

### Can Wait

- WeChat official integration
- Multi-broker
- AMS export
- LLM path verification

### Week 3 exit criteria

- [ ] Payment received
- [ ] Testimonial captured
- [ ] Decision: continue / expand / pivot documented

---

## Days 22–30: Buffer + Harden (not new features)

| Activity | Purpose |
|----------|---------|
| P16-Y battery regression fix | Prevent drift |
| Documentation of what shipped | Next sprint input |
| Archive lab scripts from operator path | Cognitive load |
| Post-pilot pricing conversation | Outcome-based framing |

---

## Master priority list (Must / Should / Can Wait / Never)

### Must Build (14 items)

1. FP-004 SSO off
2. Deploy + trial_launch_check PASS
3. Chinese broker_next_step templates
4. EN/ZH glance fix
5. Post-copy append CTA
6. Append summary merge (P16-Y P0)
7. Generic wording blocklist
8. Invoice + observation log
9. Founder E2E + Day 0 supervised
10. Correction keyword rules
11. Duplicate-case UX fix
12. waiting_on after copy
13. Payment received
14. Testimonial

### Should Build (14 items)

1. P16-M TOP5 copy
2. waiting_on pill
3. Deadline countdown
4. Append box promotion on reopen
5. v4 risk badge
6. Urgent-today filter
7. OCR upload + glance
8. Payment notice templates
9. Chen Kui ui_copy parity
10. P16-Y CI gate
11. Customer tab (week 3)
12. 我的办理 exposure
13. Add-car polish
14. SimulationAssistant cleanup

### Can Wait (12 items)

1. Customer tab Day 0
2. PDF extraction
3. Full activity timeline
4. Follow-up editor
5. Mobile pass
6. Separate customer route
7. Customer file upload
8. LLM path
9. AMS integration
10. WeChat API
11. Multi-broker auth
12. Audit export

### Never Build (10 items)

1. P17 platform
2. Stripe billing
3. Full CRM
4. Voice/IVR
5. Enterprise routing
6. IDP platform
7. Outcome billing infra
8. New conversation microservice
9. OCR-first primary intake
10. SimulationAssistant (delete not build)

---

## Resource allocation (1 developer)

```
Week 1: 60% engine/templates · 30% UX/copy · 10% deploy
Week 2: 40% UX/queue · 30% OCR wire · 30% bug fixes from log
Week 3: 70% observation-log-driven fixes · 30% customer tab if requested
```

**Founder time:** Day 0 session, observation log, invoice, testimonial — not optional.

---

## Success metrics (30-day)

| Metric | Target |
|--------|--------|
| Real cases processed | ≥10 |
| Append path used | ≥3 |
| Avg time paste → copy | <45s |
| P16-Y battery score | ≥88 |
| Chen Kui continues after Day 0 | Yes |
| Payment | Received |
| Testimonial | Captured |
| New capabilities built | **0** (revive only) |

---

## What this roadmap explicitly rejects

- P17 sprint
- UI redesign sprint (P16-M full TOP50)
- New feature development
- Platform/lab expansion
- Customer-first before broker-first proof

---

*End of P16-Z2 Phase 9 — 30-Day Strategic Roadmap*
