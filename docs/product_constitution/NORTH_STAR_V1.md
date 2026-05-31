# North Star V1 — Unified Intake

**Version:** V1 Ratified (P14-B Constitution Sprint)  
**Date:** 2026-05-31  
**Status:** Locked — product constitution SSOT  
**Authority:** When this document conflicts with sprint docs or master outline GTM framing, **this document wins for product/commercial truth**. Runtime/deploy conflicts: **`CURRENT_PRODUCT_SHAPE.md` wins**.

**Evidence base:** P10 Real Broker Trial Preparation, P11 Product Reality Audit, P14-A Constitution Discovery. P13 does not exist in the repository; P10/P11 are the latest discovery sprints.

---

## 1. What Is Unified Intake?

**Unified Intake** is broker-office intake SaaS for California auto insurance offices. It turns messy customer messages (WeChat, email, notices) into **office-ready service records** with urgency, next steps, collected facts, missing items, and an editable reply draft.

**Product name (broker-facing):** Unified Intake + Broker Workbench (办公室工作台)

**Core loop:**

```
Paste → structured case → draft → you send
```

The system **advises only**. The broker always reviews and sends. Nothing auto-sends.

**Category:** Narrow intake + triage workbench — not CRM, not RAG lookup, not a platform.

---

## 2. Who Is the Primary User?

| Role | Relationship |
|------|--------------|
| **Broker owner** (e.g., Chen Kui 陈魁) | Primary user — triage, queue, drafts, follow-up decisions |
| **Office assistant** | Secondary user — same workbench workflow; adoption doubles office ROI |
| **End customer** | Indirect beneficiary — only after broker sends improved reply |

**Office archetype:** Small California auto insurance broker office, Chinese-speaking clients, WeChat-heavy workflow, manual paste acceptable if triage clearly saves time.

**Not primary user v1:** Carriers, CRM buyers, multi-office franchise IT, enterprise procurement.

---

## 3. Who Is the Payer?

| | |
|--|--|
| **Payer** | Broker owner |
| **Price** | $49/mo starter pilot · **$99/mo standard pilot** (manual invoice) |
| **Payment method** | Manual invoice (Zelle/Venmo/WeChat) — no Stripe self-serve v1 |
| **Not sold** | $199 tier; per-seat billing; Stripe checkout |

---

## 4. What Problem Is Being Solved?

California auto broker offices receive urgent, unstructured customer messages daily — cancellations, payment failures, missing documents, add-car quotes. Brokers re-read threads, re-ask for information, and re-type replies in WeChat.

**Pain:** Urgent work gets buried. Same questions asked twice. Minutes lost on every cancellation or missing-doc message.

**Solution:** Paste raw text → system structures the case, surfaces same-day urgency, shows what's collected vs still needed, and produces an editable draft. Broker copies to WeChat after review.

**First value moment:** Open workbench → load demo queue → **cancellation case** → same-day urgency + Your next move + editable draft — in under 5 minutes (after front-door fixes).

---

## 5. What Is NOT the Product?

| Not the product | Why |
|-----------------|-----|
| WeChat/email inbox sync | Manual paste is v1 workflow — must be explicit |
| Auto-send of client replies | Trust model: broker always sends |
| In-product OCR / screenshot upload | Paste text only |
| SearchForge RAG `/demo` page | Separate wedge; confuses brokers |
| Platform/lab routers | Hidden in product-only mode |
| Full CRM or carrier integration | Deferred beyond v1 |
| Multi-tenant auth / Stripe self-serve | Deferred until first payment proof |
| Perfect edge-case handling | Broker verifies; system advises |

---

## 6. What Must Never Be Built in V1?

Locked for **90 days** (from P11 WHAT_NOT_TO_DO + constitution anti-goals):

1. Stripe / billing portal / self-serve signup  
2. WeChat or email inbox sync  
3. Multi-tenant / SSO / per-broker isolation  
4. Full CRM or carrier API integration  
5. In-product OCR / screenshot upload as primary path  
6. Platform SKU / workflow engine / event bus  
7. $199 enterprise tier (features don't exist)  
8. Repo-wide cleanup / lab isolation sprints during active broker trial  
9. New feature work before one broker completes 7-day trial with logged evidence  
10. Auto-send of client replies  

**Allowed in 90 days:** Week 1 UI fixes, paid pilot deploy, Chen Kui supervised trial, pricing/terms on one-pager, fix-now queue from trial friction only.

---

## 7. What Is the Wedge Strategy?

**Paid pilot wedge (cancellation-first — overrides Add-Car-first master outline GTM):**

| Priority | Workflow | Why |
|----------|----------|-----|
| 1 | **Cancellation / payment failed** | Same-day action; highest urgency pain; Chen Kui pays for minutes here |
| 2 | **Missing document** | Stop re-asking; high frequency |
| 3 | **Add-car quote** | Revenue scenario; multi-turn collection |

Add-Car **customer portal** (客户报送) remains a product surface but is **not the sales lead** for Chen Kui archetype.

**Commercial package:** 7-day free evaluation → optional 30-day paid pilot month → manual invoice at Day 7 if value proven.

**Second broker:** Only after first testimonial from Chen Kui trial.

---

## 8. Why Would Chen Kui Pay $49–$99/Month?

| Price | Likelihood | Condition |
|-------|------------|-----------|
| **$49/mo** | Maybe yes | One workflow (cancellation or missing doc) clearly saved ~30+ min/week on real cases |
| **$99/mo** | Conditional yes | 2+ scenarios worked; draft copied with edits ≥2×; assistant uses workbench; prod cases persist |
| **$199/mo** | Unlikely no | No enterprise features; would churn in 30 days |

**What he pays for:** Minutes saved on **urgent messages** — structured cases, queue priority, editable drafts — not Add-Car portal, not RAG, not AI novelty.

**Competitive moat (P11):** Insurance-specific case structure + queue + scenarios — not generic ChatGPT drafts alone.

**Value framing:** "Less than one hour of assistant time per month" at $49; full office workflow at $99.

---

## 9. What Must Be True Before Charging Money?

All five proof layers (from P11 payment blockers):

| Layer | Requirement |
|-------|-------------|
| **Quantitative** | ≥1 logged "worked" line with approximate minutes saved on a **real** case |
| **Behavioral** | Workbench opened ≥4 of 7 days; draft copied with edits ≥2 times; ≥3 real cases logged |
| **Infrastructure** | Prod URL live; Postgres-primary; cases persist across sessions; `/readyz` intake_path_ready |
| **Commercial** | Invoice + 1-page pilot terms (Chinese) in broker's hands; pricing on one-pager |
| **Qualitative** | Day 7 Q3 "Would this save time?" = yes with specific example |

**Operational gates before Day 0:**

- `trial_launch_check.sh` PASS  
- Broker UX launch checklist PASS (script PASS ≠ broker-ready)  
- Prod `/readyz` validated  
- 30-min founder kickoff scheduled  

**Not required for v1 payment:** Stripe, multi-tenant, WeChat sync, OAuth.

---

## 10. One-Sentence Version

**Turn messy California auto insurance customer messages into office-ready service records so brokers handle urgent work faster — with drafts they review before sending.**

**Chinese (broker-facing):**

> 试用一周：帮你把客户发来的 messy 消息整理成结构化 case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。

---

## Anti-Drift North Star Tests

Ask weekly:

1. Can Chen Kui reach cancellation value in 5 minutes **without founder translating**?  
2. Does every new doc/sprint align with paste → case → draft → you send?  
3. Are we building for **one paying broker** or for platform fantasy?  
4. Is `/workbench/unified-intake` the demo URL — not `/demo`?  

---

## Document Relationships

| This document | Links to |
|---------------|----------|
| Capability contracts | `product_constitution/contracts/` |
| Capability map | `CAPABILITY_MAP_V1.md` |
| Runtime/deploy | `CURRENT_PRODUCT_SHAPE.md` |
| Founder ops | `FOUNDER_ONE_PATH.md` |
| Broker sales | `BROKER_ONE_PAGER.md` |
| Trial | `TRIAL_ONE_PATH.md` |
| Discovery evidence | P10/P11 sprint audits, P14-A proposal pack |

---

*End of North Star V1*
