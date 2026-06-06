# P16-Z2.5 30-Day Roadmap

**Date:** 2026-06-01  
**Sprint:** P16-Z2.5 Product Soul Synthesis  
**Team:** 1 founder · 1 developer · 1 pilot office (Chen Kui)  
**Frame:** Revive, wire, tune, deploy — zero new capabilities

---

## Ranking legend

| Tier | Meaning |
|------|---------|
| **Must Do** | Pilot blocked without it |
| **Should Do** | Strongly improves payment odds |
| **Can Wait** | Week 3+ or post-payment |
| **Never Do** | Distraction per constitution + P16-Z2 |

---

## Week 1 (Days 1–7): Access + Broker Loop

**Theme:** Chen Kui opens URL, pastes cancel notice, copies draft, knows what's next.

### Must Do

| # | Item | Owner | Effort |
|---|------|-------|--------|
| M1 | Disable Preview SSO (FP-004) | Founder | 5 min |
| M2 | Redeploy + `trial_launch_check.sh` PASS | Dev | 0.5 day |
| M3 | Chinese broker_next_step templates (cancel, payment, add-car) | Dev | 1 day |
| M4 | Fix EN/ZH mix in glance + queue | Dev | 0.5 day |
| M5 | Post-copy CTA: "客户回复了？追加到此案件" | Dev | 0.5 day |
| M6 | P16-Y P0: append summary merge | Dev | 1–2 days |
| M7 | Generic wording blocklist in case_draft_engine | Dev | 0.5 day |
| M8 | Fill invoice payment IDs | Founder | 30 min |
| M9 | Observation log protocol + row 1 | Founder | 1 hour |
| M10 | Founder E2E log on deployed URL | Founder | 1 hour |

### Should Do

| # | Item | Owner | Effort |
|---|------|-------|--------|
| S1 | P16-M TOP5 copy (trust line, demo demotion) | Dev | 0.5 day |
| S2 | waiting_on pill in broker glance | Dev | 0.5 day |
| S3 | Deadline countdown from deadline_mentioned | Dev | 0.5 day |
| S4 | Promote append box when case reopened | Dev | 0.5 day |
| S5 | Surface v4 risk as「需核实」badge | Dev | 0.5 day |

### Can Wait

- Customer tab on trial URL
- OCR upload
- Urgent-today filter
- Follow-up editor unhide

### Never Do

- P17, Stripe, new microservices, customer portal rewrite, full P16-M TOP50

### Week 1 exit criteria

- [ ] Cold Preview URL works without Andy
- [ ] Cancel paste → Chinese draft → copy in <45s
- [ ] Append to same case with merged summary
- [ ] `guardrail_inbox_triage.sh` PASS
- [ ] Observation log row 1 exists

---

## Week 2 (Days 8–14): Trial Live + Evidence

**Theme:** Supervised Chen Kui Day 0; collect proof; second case type.

### Must Do

| # | Item | Owner | Effort |
|---|------|-------|--------|
| M11 | Supervised Chen Kui Day 0 session | Founder | 2 hours |
| M12 | Chen Kui ui_copy.json deploy parity | Dev | 0.5 day |
| M13 | P16-Y battery ≥88 in CI or pre-deploy gate | Dev | 0.5 day |
| M14 | Correction keyword rules (Y44 fix) | Dev | 0.5 day |
| M15 | Duplicate-case UX fix | Dev | 0.5 day |
| M16 | "Mark sent / waiting on customer" after copy | Dev | 0.5 day |

### Should Do

| # | Item | Owner | Effort |
|---|------|-------|--------|
| S6 | Urgent-today queue filter or sort | Dev | 1 day |
| S7 | Vision API keys + OCR upload test | Dev/Ops | 0.5 day |
| S8 | OCR fields in glance with [OCR] tag | Dev | 0.5 day |
| S9 | Payment notice template excellence | Dev | 0.5 day |
| S10 | 5 real cases in observation log | Founder | ongoing |

### Can Wait

- CustomerEntryTab on separate route
- PDF extraction
- Full activity timeline
- Mobile optimization

### Week 2 exit criteria

- [ ] Chen Kui processed ≥3 real cases (supervised)
- [ ] ≥1 case used append path successfully
- [ ] Broker feedback in observation log
- [ ] Time-saved estimate documented
- [ ] Invoice sent

---

## Week 3 (Days 15–21): Payment + Testimonial

**Theme:** Prove ROI; get paid; decide post-pilot scope.

### Must Do

| # | Item | Owner | Effort |
|---|------|-------|--------|
| M17 | Payment received (Zelle/Venmo/WeChat) | Founder | — |
| M18 | Testimonial or written quote | Founder | — |
| M19 | Day 7 review: what worked / didn't | Founder | 1 hour |
| M20 | Fix top 3 friction items from observation log | Dev | 2 days |

### Should Do

| # | Item | Owner | Effort |
|---|------|-------|--------|
| S11 | Customer tab on shareable URL (if broker requests) | Dev | 1–2 days |
| S12 | 我的办理 status for customer self-check | Dev | 1 day |
| S13 | Add-car path polish (if broker request) | Dev | 1–2 days |
| S14 | Delete SimulationAssistant.tsx | Dev | 15 min |

### Can Wait

- WeChat official integration
- Multi-broker auth
- AMS export
- LLM path verification

### Week 3 exit criteria

- [ ] Payment received
- [ ] Testimonial captured
- [ ] Continue / expand / pivot documented

---

## Days 22–30: Buffer + Harden

| Activity | Purpose |
|----------|---------|
| P16-Y battery regression fix | Prevent drift |
| Document what shipped | Next sprint input |
| Archive lab scripts from operator path | Cognitive load |
| Post-pilot pricing conversation | Outcome-based framing |

---

## Master priority list

### Must Do (14)

1. FP-004 SSO off
2. Deploy + trial_launch_check PASS
3. Chinese broker_next_step templates
4. EN/ZH glance fix
5. Post-copy append CTA
6. Append summary merge (P16-Y P0)
7. Generic wording blocklist
8. Invoice + observation log
9. Founder E2E + supervised Day 0
10. Correction keyword rules
11. Duplicate-case UX fix
12. waiting_on after copy
13. Payment received
14. Testimonial

### Should Do (14)

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

### Can Wait (12)

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

### Never Do (10)

1. P17 platform
2. Stripe billing
3. Full CRM
4. Voice/IVR
5. Enterprise routing
6. IDP platform
7. Outcome billing infra
8. New conversation microservice
9. OCR-first primary intake
10. SimulationAssistant (delete, not build)

---

## Success metrics

| Metric | Target |
|--------|--------|
| Real cases processed | ≥10 |
| Append path used | ≥3 |
| Avg time paste → copy | <45s |
| P16-Y battery score | ≥88 |
| Chen Kui continues after Day 0 | Yes |
| Payment | Received |
| Testimonial | Captured |
| New capabilities built | **0** |

---

## Resource allocation

```
Week 1: 60% engine/templates · 30% UX/copy · 10% deploy
Week 2: 40% UX/queue · 30% OCR wire · 30% bug fixes from log
Week 3: 70% observation-log-driven fixes · 30% customer tab if requested
```

**Founder time:** Day 0, observation log, invoice, testimonial — not optional.

---

*End of P16-Z2.5 30-Day Roadmap*
