# Proposed North Star — P14-A

**Date:** 2026-05-31  
**Source:** Discovered evidence only — primarily P11 CURRENT_PRODUCT_TRUTH, P10/P11 audits, BROKER_ONE_PAGER, CURRENT_PRODUCT_SHAPE, P9 broker surface plan, TRIAL_ONE_PATH.  
**Explicitly subordinates:** `UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` Add-Car-first GTM framing where it conflicts with trial/payment evidence.

---

## One-Sentence North Star

**Turn messy California auto insurance customer messages into office-ready service records so brokers handle urgent work faster — with drafts they review before sending.**

Chinese (broker-facing, discovered from BROKER_ONE_PAGER):

> 试用一周：帮你把客户发来的 messy 消息整理成结构化 case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。

---

## What Are We Selling?

| Layer | Answer |
|-------|--------|
| **Product name** | Unified Intake + Broker Workbench |
| **Category** | Broker-office intake SaaS (not CRM, not RAG lookup, not platform) |
| **Core loop** | Paste → structured case → draft → broker sends |
| **Deployment** | Vercel UI + Cloud Run API + Postgres (paid pilot) |
| **Commercial package** | 7-day free trial → optional paid pilot month |

**We are NOT selling (evidence: CURRENT_PRODUCT_TRUTH, P11, SIMPLIFICATION):**
- SearchForge R&D / `/demo` RAG Q&A
- Trusted Assistant Platform / agency OS
- WeChat/email sync, OCR, auto-send
- Full CRM, carrier integration, multi-office billing portal
- Stripe self-serve billing (v1)

---

## Who Pays?

| Role | Pays? | Gets value? |
|------|-------|-------------|
| **Broker owner** (e.g., Chen Kui) | **Yes — primary payer** | Triage, queue, drafts, follow-up memory |
| **Office assistant** | No | Daily paste/triage workflow; doubles ROI if adopted |
| **End customer** | No | Better/faster broker replies (indirect) |
| **Carriers / CRM vendors** | No | N/A |

**Payment model (discovered):** Manual invoice $49–99/month (Zelle/Venmo/WeChat). No Stripe v1.

---

## Who Gets Value First?

**Priority order (P10/P11 evidence):**

1. **Broker owner** — sees cancellation urgency + next move in &lt;2 minutes (if on workbench tab)
2. **Office assistant** — same workbench; reduces re-asking and re-typing
3. **End customer** — only after broker sends improved reply (broker-controlled)

**First value moment (must work unsupervised after Week 1 UI fixes):**
Open workbench → load demo queue → **cancellation case** → same-day urgency + Your next move + editable draft.

**Not first value moment:** Add-Car customer portal, RAG lookup, Simulation Assistant tab.

---

## What Is NOT the Product?

Consolidated from CURRENT_PRODUCT_TRUTH §2, P11 WHAT_NOT_TO_DO, SIMPLIFICATION §1:

| Not the product | Why it matters |
|-----------------|----------------|
| Inbox sync | Manual paste is v1 workflow — must be explicit |
| Auto-send | Trust model: broker always sends |
| In-product OCR | Paste text only |
| `/demo` RAG page | Separate wedge; confuses brokers |
| Platform/lab routers | Hidden in product_only mode |
| Multi-tenant auth / Stripe | Deferred until first payment proof |
| Perfect edge cases | Broker verifies; system advises |

---

## What Must Never Be Built in the Next 90 Days?

From P11 FINAL_AUDIT WHAT_NOT_TO_DO + FOUNDER_REFLECTION + SIMPLIFICATION:

1. **Stripe / billing portal / self-serve signup**
2. **WeChat or email inbox sync**
3. **Multi-tenant / SSO / per-broker isolation**
4. **Full CRM or carrier API integration**
5. **In-product OCR / screenshot upload as primary path**
6. **Platform SKU / workflow engine / event bus**
7. **$199 enterprise tier** (features don't exist)
8. **Repo-wide cleanup / lab isolation sprints** during active broker trial
9. **New feature work before one broker completes 7-day trial with logged evidence**
10. **Auto-send of client replies**

**Allowed in 90 days (P11 30-day plan):**
- Week 1 UI fixes (tab default, hide engineer chrome, inline practice scenarios)
- Paid pilot deploy + `/readyz` validation
- Chen Kui supervised trial + observation log
- Pricing/terms on one-pager
- Fix-now queue from trial friction only

---

## Commercial Wedge (Resolved)

**Paid pilot wedge (P11 > master outline for GTM):**

| Priority | Workflow | Why |
|----------|----------|-----|
| 1 | **Cancellation / payment failed** | Same-day action; highest urgency pain |
| 2 | **Missing document** | Stop re-asking; high frequency |
| 3 | **Add-car quote** | Revenue scenario; multi-turn collection |

Add-Car **customer portal** remains a product surface but is **not the sales lead** for Chen Kui archetype.

---

## Success Definition (North Star Metrics)

| Metric | Target (discovered) |
|--------|---------------------|
| Trial completion | 7 days with ≥3 real cases logged |
| Behavioral proof | Draft copied with edits ≥2 times |
| Retention signal | Workbench opened ≥4 of 7 days |
| Time proof | ≥1 "worked" line with approximate minutes saved |
| Payment | $49–99 manual invoice after Day 7 if above met |
| Engine quality | guardrail_inbox_triage 13/13 PASS |

---

## Anti-Drift North Star Tests

Ask weekly (from P11 FOUNDER_REFLECTION):

1. Can Chen Kui reach cancellation value in 5 minutes **without founder translating**?
2. Does every new doc/sprint align with paste → case → draft → you send?
3. Are we building for **one paying broker** or for platform fantasy?
4. Is `/workbench/unified-intake` the demo URL — not `/demo`?

---

*End of proposed north star*
