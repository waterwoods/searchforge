# P16-Z3 Reverse Engineering — Product Soul Extraction

**Date:** 2026-06-02  
**Sprint:** P16-Z3 — Case Intelligence Master Plan  
**Constraint:** No vendor product descriptions — soul, steal, skip, speed, Chen Kui only.  
**Sources:** P16-Z2 teardown, P16-Z2.5 synthesis, P16-Z0 archaeology, P16-X continuity audit.

---

## Method

For each benchmark company, answer five questions:

1. What is their **product soul** (one beat customers pay for)?
2. What should Unified Intake **steal**?
3. What should Unified Intake **never copy**?
4. What can ship in **< 1 week**?
5. What creates value for **Chen Kui immediately**?

---

## Zendesk

| Question | Answer |
|----------|--------|
| **Product soul** | *Prove the customer's problem actually ended* — not tickets closed, not deflection theater. |
| **Steal** | Outcome mindset in sales and observation log;「verified resolution」as future pricing unit; single queue with accountability. |
| **Never copy** | Per-seat enterprise maze; voice AI; 20B corpus training story; outcome billing infrastructure for one broker. |
| **< 1 week** | Observation log column:「客户是否确认解决」; urgency-sorted queue label. |
| **Chen Kui now** | Cancel case treated as **resolution deadline** — countdown +「办公室下一步：今天联系 Mercury」. |

---

## Intercom

| Question | Answer |
|----------|--------|
| **Product soul** | *Meet the customer where they already are* — conversation is the front door; structure is extracted, not demanded first. |
| **Steal** | Message-first intake (P16-O done); convert unstructured thread → typed record without re-asking; one thread ID per customer problem. |
| **Never copy** | Website messenger widget; Fin PLG; product-tour onboarding; B2B SaaS chat campaigns. |
| **< 1 week** | Hero paste box only on broker trial URL; demote category grid (customer side done). |
| **Chen Kui now** | Broker pastes WeChat — system is the **converter**, not a second chat app. |

---

## Salesforce Service Cloud

| Question | Answer |
|----------|--------|
| **Product soul** | *The case record is the office's memory* — every touch, field, owner, and SLA lives on one object until closed. |
| **Steal** | Auto-fill fields from message; Next Best Action on the record (`broker_next_step` + `waiting_on`); wrap-up discipline (copy = handoff moment). |
| **Never copy** | Full CRM; Flow Builder; Einstein platform; skill-based routing; org-wide ML training narrative. |
| **< 1 week** | Promote `waiting_on` + `still_needed` in glance; status pill after copy. |
| **Chen Kui now** | Paste → **case glance = mini Case record** — no Salesforce login, same mental model. |

---

## HubSpot

| Question | Answer |
|----------|--------|
| **Product soul** | *Let the customer see status without calling* — deflect repeat「办到哪了」into self-serve truth. |
| **Steal** | 我的办理 status tab (already built); receipt-style confirmation; KB loop deferred. |
| **Never copy** | Marketing Hub bundle; multi-hub CRM; IVR; credit-per-resolution pricing infra at SMB scale. |
| **< 1 week** | Enable customer route on separate URL if broker requests week 3. |
| **Chen Kui now** | **Week 1–2: broker is the portal** — copy draft to WeChat IS the status channel. |

---

## Stripe

| Question | Answer |
|----------|--------|
| **Product soul** | *Assemble the strongest evidence packet before the deadline* — pull auto + flag manual gaps + submit once. |
| **Steal** | Evidence packet pattern for insurance: notice + payment proof + policy fields → `collected` vs `still_needed`; deadline never missed. |
| **Never copy** | Payments; Radar; Connect; dispute network intelligence; Dashboard-as-product. |
| **< 1 week** | Wire existing OCR fusion to glance with `[OCR]` tags on broker upload (week 2). |
| **Chen Kui now** | Cancel notice paste → **packet view**: what we have / what we still need before calling carrier. |

---

## Linear

| Question | Answer |
|----------|--------|
| **Product soul** | *Context is the source of truth; the record is the output* — speed beats ceremony. |
| **Steal** | Inbound automation on arrival (triage on paste); same issue accretes context; agent/session checklist → `broker_next_step` as evolving plan. |
| **Never copy** | Git/PR workflow; cycles/roadmaps; eng issue types; 25% agent-authored issues metric chase. |
| **< 1 week** | Post-copy CTA:「客户回复了？追加」— continuity without new backend. |
| **Chen Kui now** | **Under 45s** paste-to-copy; append = same case, not new paste box hero. |

---

## Cross-vendor synthesis

### Universal product soul (what they share)

> **Chaos becomes a durable obligation with a next beat and a proof of closure.**

Unified Intake's soul is the **insurance-office slice** of that universal pattern — WeChat-native, one office, no platform.

### Steal matrix (priority for pilot)

| Pattern | Source | Unified Intake mapping | Week |
|---------|--------|------------------------|------|
| Paste → structured record | Salesforce | `triage_conversation` | 1 |
| Conversation → record | Intercom | Message-first broker paste | 1 |
| Evidence packet | Stripe | collected / still_needed | 1–2 |
| Context → same record | Linear | Append + summary merge | 1–2 |
| NBA on record | Salesforce | broker_next_step | 1 |
| Self-serve status | HubSpot | 我的办理 (week 3) | 3 |
| Verified outcome | Zendesk | Observation log | 1–4 |

### Never-copy matrix (constitution + pilot)

| Anti-pattern | Why fatal for Chen Kui |
|--------------|------------------------|
| Seat-based enterprise pricing | 1 broker, manual invoice |
| Omnichannel hub | WeChat only in pilot |
| CRM replacement | AMS exists |
| AI platform / P17 | Scope guardrail |
| OCR-first primary intake | Text wedge wins Day 0 |
| Smarter Turn-1-only AI | Continuity > intelligence |

### < 1 week implementation list (ranked)

1. FP-004 SSO off (5 min)
2. Post-copy append CTA (0.5 day)
3. Chinese broker_next_step templates (1 day)
4. Demo demotion / trust line (0.5 day)
5. waiting_on + deadline glance (0.5 day)
6. Observation log row 1 (1 hour)
7. Invoice IDs filled (30 min)
8. P16-Y append summary merge (1–2 days)
9. Risk「需核实」badge (0.5 day)
10. Guardrail + p16y battery in CI (0.5 day)

### Chen Kui immediate value list (behavioral, not feature)

| # | Value | Mechanism |
|---|-------|-----------|
| 1 | Send one cancel reply without re-reading paste | L1+L4 in <45s |
| 2 | Know what's missing before calling client | L2 glance |
| 3 | See deadline without emoji hunt | L3 countdown |
| 4 | Client replies — same case, second draft | L3+L5 append |
| 5 | Trust no auto-send to WeChat | Trust line + copy ceremony |
| 6 | Assistant can use same case ID | L1 persistence |
| 7 | Payment justification | Observation log time-saved |
| 8 | Beat「直接回微信」| Speed + Chinese specificity |

---

## Competitive positioning (one line)

We are **not** competing with Zendesk or Salesforce. We are implementing **their closure architecture** for **one WeChat-native insurance office** — smaller surface, higher context density, manual payment.

---

*End of P16-Z3 Reverse Engineering*
