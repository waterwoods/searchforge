# P16-Z2.5 Capacity Ranking

**Date:** 2026-06-01  
**Sprint:** P16-Z2.5 Product Soul Synthesis  
**Sources:** P16-Z0, P16-Z2 capability maps + all sprint verdicts  
**Filter:** Impact on paid pilot and first paying customer

---

## The seven capacities

| # | Capacity | Job |
|---|----------|-----|
| 1 | Broker Front Door | Chen Kui opens URL → paste → draft → copy in 2 min |
| 2 | Case Intelligence | Messy paste → category, urgency, summary, fields |
| 3 | Structured Case Record | Office acts without re-reading raw WeChat |
| 4 | Customer Intake Collection | Customer sends request; office gets structured handoff |
| 5 | Case Lifecycle Management | Message 2–4 updates same case; office knows what's waiting |
| 6 | Trial Conversion | Andy → Chen Kui → invoice → testimonial |
| 7 | Founder / Operator Control | Andy ships with confidence; no silent regressions |

---

## Ranked: Most important → Least important (for pilot)

| Rank | Cap | Current | Pilot target | Why this rank |
|------|-----|---------|--------------|---------------|
| **1** | **2 — Case Intelligence** | ~85 | 88 | Core engine; without understanding, nothing else matters |
| **2** | **1 — Broker Front Door** | ~45 deploy | 75 | Access + paste loop; FP-004 blocks everything |
| **3** | **5 — Case Lifecycle** | 41–53 | 70 | Multi-turn = real office workflow; append discoverability |
| **4** | **3 — Structured Case Record** | ~72 | 80 | broker_next_step Chinese specificity; office actionability |
| **5** | **6 — Trial Conversion** | ~51 | 75 | Payment evidence; observation log; Day 0 |
| **6** | **7 — Founder Control** | ~65 | 80 | guardrail + battery CI; prevents FP-008 regressions |
| **7** | **4 — Customer Intake** | ~55 | 65 | Week 3 asset; broker paste is Day 0 GTM |

---

## Why Cap 4 ranks last (for pilot)

Chen Kui simulation and P16-Z2 agree: **broker paste path is Day 0; customer self-serve is Day 7+**. Customers interact through broker's WeChat in weeks 1–2. Cap 4 is high customer value but low pilot blocker value until broker loop proven and paid.

---

## Why Cap 2 ranks first (not Cap 1)

Cap 1 is the **deployment blocker** (SSO, copy, discoverability). Cap 2 is the **product soul** — the transformation from chaos to case. Without Cap 2, Cap 1 is an empty paste box. Cap 2 is built at 85; Cap 1 is broken at 45 deployed. **Rank 1 = what customers pay for; Rank 2 = what blocks access to it.**

For execution priority this week: **Cap 1 fixes first** (FP-004, append CTA). For strategic importance: **Cap 2 defines the product.**

---

## Execution priority vs strategic importance

| Execution this week | Strategic soul |
|--------------------|----------------|
| Cap 1 (access, copy, Chinese) | Cap 2 (triage engine) |
| Cap 5 (append UX) | Cap 3 (office record) |
| Cap 6 (Day 0, log, invoice) | Cap 5 (continuity loop) |
| Cap 7 (guardrail, battery) | Cap 6 (payment proof) |

---

## Sub-capability priority within each cap

### Cap 1 — Broker Front Door

| Priority | Sub-capability |
|----------|----------------|
| Critical | Cold URL (FP-004), paste→triage→draft, copy-to-WeChat, post-copy CTA |
| High | Chinese-only glance, Chen Kui ui_copy parity, urgent queue |
| Medium | Demo demotion, mobile usable |
| Low | Full design system |

### Cap 2 — Case Intelligence

| Priority | Sub-capability |
|----------|----------------|
| Critical | Classification, collected/still_needed fields, multi-turn summary merge |
| High | Deadline extraction, correction handling, conversation_summary |
| Medium | OCR fusion, risk score surfacing |
| Low | LLM path, ML distillation |

### Cap 3 — Structured Case Record

| Priority | Sub-capability |
|----------|----------------|
| Critical | Case persist, queue+reopen, broker_next_step wording |
| High | client_prep, glance「还缺什么」, duplicate-case prevention |
| Medium | case_messages thread visibility, attachments |
| Low | Full draft card, audit export |

### Cap 4 — Customer Intake

| Priority | Sub-capability |
|----------|----------------|
| High (week 3) | Message-first landing, 我的办理 status |
| Medium | CustomerEntryTab multi-turn, separate customer URL |
| Low | Customer file upload, add-car structured flow |

### Cap 5 — Case Lifecycle

| Priority | Sub-capability |
|----------|----------------|
| Critical | Append API (backend ✅), append discoverability (UX ❌) |
| High | waiting_on field, multi-turn continuity UX |
| Medium | follow-up editor, boundary detection |
| Low | Activity timeline |

### Cap 6 — Trial Conversion

| Priority | Sub-capability |
|----------|----------------|
| Critical | FP-004, observation log, invoice IDs, supervised Day 0 |
| High | Testimonial capture, time-saved evidence |
| Medium | 15-min demo script |
| Low | Stripe billing |

### Cap 7 — Founder Control

| Priority | Sub-capability |
|----------|----------------|
| Critical | guardrail_inbox_triage.sh, Preview SSO audit |
| High | P16-Y battery gate, P16-T health runner |
| Medium | ScenarioReplayTab, deploy parity script |
| Low | 197 lab scripts, audit export |

---

## Impact × effort matrix

```
                    IMPACT ON PAID PILOT
                    Low         High
              ┌──────────┬──────────┐
         Low  │ Cap 7    │ Cap 4    │
    EFFORT    │ (lab)    │ (customer│
              │          │  tab)    │
              ├──────────┼──────────┤
         High │ Cap 6    │ Cap 1,2  │
              │ (process)│ Cap 3,5  │
              └──────────┴──────────┘
```

---

*End of P16-Z2.5 Capacity Ranking*
