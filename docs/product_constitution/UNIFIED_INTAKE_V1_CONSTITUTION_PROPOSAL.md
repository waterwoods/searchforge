# Unified Intake V1 Constitution — Proposal

**Version:** V1 Proposal (P14-A Discovery Sprint)  
**Date:** 2026-05-31  
**Status:** Awaiting founder approval  
**Authority chain:** This document is proposed **product constitution SSOT**. When it conflicts with sprint docs or master outline GTM framing, **this document wins for product/commercial truth**. Runtime/deploy conflicts: **`CURRENT_PRODUCT_SHAPE.md` wins**.

---

## 1. North Star

**Turn messy California auto insurance customer messages into office-ready service records so brokers handle urgent work faster — with drafts they review before sending.**

**Core loop:** Paste → structured case → draft → **you send** (never auto-send).

---

## 2. Target Customer

| Attribute | Definition |
|-----------|------------|
| **Who** | California auto insurance broker offices |
| **Archetype** | Chen Kui (陈魁) — small office, Chinese-speaking clients, WeChat-heavy |
| **Users in office** | Broker owner + assistant (same workflow) |
| **Geography** | US/California only |
| **Not target v1** | Multi-office franchises, carriers, CRM buyers, enterprise IT |

---

## 3. Target Payer

| | |
|--|--|
| **Payer** | Broker owner |
| **Price** | $49/mo starter pilot · **$99/mo standard pilot** (manual invoice) |
| **Not sold** | $199 tier; per-seat billing; Stripe self-serve (v1) |
| **Payment proof** | Day 7 value conversation + ≥1 logged time-savings example |

---

## 4. Seven-Capability Model

| # | Capability | v1 scope |
|---|------------|----------|
| 1 | **Customer Intake** | Broker workbench paste (primary); Customer Entry secondary |
| 2 | **Message Understanding** | 6-field triage; 10+ issue categories; guardrail regression |
| 3 | **Case Structuring** | Case focus, urgency, Collected, Still needed, queue |
| 4 | **Office Workflow** | Work now / Waiting; reopen; notes; follow-up fields |
| 5 | **Draft Generation** | Editable client_reply_draft; bilingual; broker copies to WeChat |
| 6 | **Customer Identity** | Session/case continuity only — **no CRM v1** |
| 7 | **Trial ROI** | 7-day observation log; Day 7 five questions; fix-now queue |

See `PROPOSED_CAPABILITY_MAP.md` for inputs, outputs, maturity, gaps.

---

## 5. Business Model

| Element | Rule |
|---------|------|
| **Offer** | 7-day free evaluation → optional 30-day paid pilot month |
| **Wedge workflows** | (1) Cancellation/payment failed (2) Missing document (3) Add-car quote |
| **Value sold** | Minutes saved on urgent messages + structured cases + drafts |
| **Value NOT sold** | AI, vectors, platform, sync, OCR |
| **Delivery** | Vercel + Cloud Run + Postgres |
| **Support** | Founder L1; case snapshot for L2 |
| **Second broker** | After first testimonial from Chen Kui trial |

---

## 6. Trial Model

| Phase | Rule |
|-------|------|
| **Pre-Day 0** | `trial_launch_check.sh` PASS + broker UX checklist PASS + prod `/readyz` |
| **Day 0** | 30-min founder kickoff; **办公室工作台 only**; send one-pager + playbook |
| **Day 1** | Demo queue + 3 named scenarios + 1 real paste |
| **Day 3** | 2–3 real cases; friction log |
| **Day 7** | Five value questions; invoice or fix-now queue |
| **Success** | ≥3 real cases; draft copied ≥2×; opened ≥4/7 days; one "worked" line |
| **Failure** | Wrong-tab confusion; expects sync; stops after Day 1 |

**SSOT:** `TRIAL_ONE_PATH.md` (to be updated: remove Simulation dependency).

---

## 7. Anti-Goals (v1 and 90-day)

1. WeChat/email inbox sync  
2. In-product OCR / screenshot upload as primary path  
3. Auto-send of client messages  
4. Full CRM, carrier APIs, multi-office billing portal  
5. Stripe / self-serve signup / multi-tenant auth  
6. SearchForge RAG `/demo` as paid product surface  
7. Trusted Assistant Platform / agency OS / workflow engine  
8. $199 enterprise tier  
9. New features before first 7-day trial completes with evidence  
10. Repo cleanup / lab isolation during active trial weeks  

---

## 8. Founder Rules

1. Read `FOUNDER_ONE_PATH.md` — one operational path  
2. Demo URL: `/workbench/unified-intake` — never lead with `/demo`  
3. Before demo/trial: `guardrail_inbox_triage.sh`  
4. Before first broker: `trial_launch_check.sh` + broker UX checklist  
5. Day 0 kickoff mandatory until unsupervised Day 1 proven  
6. Observation log → fix-now queue → **top 3 friction only**  
7. Manual payment OK for first pilot — speed over Stripe  
8. Do not reference SIM IDs, PG mirror, or API URLs with brokers  
9. Script PASS ≠ broker-ready — always dry-run UI walkthrough  
10. Time allocation: 40% trial support, 25% Week 1 UI fixes (P11 plan)  

---

## 9. Product Rules

1. **Broker sends everything** — system advises only  
2. **Paste raw text** — no cleanup required  
3. **Case focus / Your next move / Collected / Still needed** — broker-facing labels (see CUSTOMER_LANGUAGE_GUIDE)  
4. **Same-day action** cases must surface first in queue  
5. **Demo honesty** — distinguish real now vs deferred (UNIFIED_INTAKE_MVP_STANDARD §3)  
6. **Product-only UI** — hide lab, Simulation (until inline), engineer chrome  
7. **Trial default tab** — Broker Workbench (办公室工作台)  
8. **Scenario tiers:** 3 trial · 5 one-pager · 7 sellable package  
9. **6-field output** — always present per BROKER_INBOX_TRIAGE_STANDARD  
10. **Client pack** (chen_kui) — tune drafts, not architecture  

---

## 10. Capability Evolution Rules

| Horizon | Allowed | Forbidden |
|---------|---------|-----------|
| **0–14 days** | UI front door fixes; deploy prod; start trial | New capabilities, Stripe, sync |
| **15–30 days** | Fix-now from trial log; draft tuning; pricing/terms | Platform features, $199 tier |
| **31–90 days** | Second broker; inline practice scenarios; assistant playbook | CRM, OCR, multi-tenant |
| **90+ days** | Revisit Customer Entry GTM **only if** first payment + testimonial | Platform SKU without revenue proof |

**Evolution gate:** No capability promotion from Partial → Shipped without trial ROI evidence or explicit founder kill/continue decision.

---

## 11. Anti-Drift Rules

| Drift signal | Response |
|--------------|----------|
| New doc contradicts paste → case → draft loop | Reject or update constitution first |
| Sprint adds platform/router scope | Check SIMPLIFICATION_MASTER_PLAN |
| Demo uses `/demo` or Customer Entry as lead | Reset to workbench cancellation path |
| Master outline Add-Car-first used in sales | Subordinate to §5 wedge order |
| Agent reads insurance_paid_pilot_goal for product scope | Redirect to this constitution |
| guardrail regression | Block demo/trial until fixed |
| Engineer labels visible in product_only UI | P0 fix |

**Weekly north star test:** Can Chen Kui see cancellation value in 5 minutes without founder help?

---

## 12. Success Metrics

| Metric | Target | Source |
|--------|--------|--------|
| Triage regression | guardrail 13/13 PASS | scripts/guardrail_inbox_triage.sh |
| Trial completion | 7 days, ≥3 real cases | TRIAL_ONE_PATH |
| Behavioral | Draft copied ≥2×; open ≥4/7 days | P11 blockers |
| Qualitative | Day 7 Q3 "save time?" = yes + example | TRIAL_ONE_PATH |
| Commercial | First $49–99 payment OR ranked kill reasons | P11 verdict |
| Infrastructure | Prod `/readyz` intake_path_ready | CURRENT_PRODUCT_SHAPE |
| Second sale | 1 testimonial quote captured | P11 FOUNDER_REFLECTION |

---

## 13. Document Relationships

| This constitution | Links to |
|-------------------|----------|
| Runtime/deploy | `CURRENT_PRODUCT_SHAPE.md` |
| Founder ops | `FOUNDER_ONE_PATH.md` |
| Broker sales | `BROKER_ONE_PAGER.md` |
| Trial | `TRIAL_ONE_PATH.md` |
| Engineering | `standards/BROKER_INBOX_TRIAGE_STANDARD.md` |
| Macro (subordinate) | `UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` |
| Discovery evidence | `product_constitution/CONSTITUTION_DISCOVERY_REPORT.md` |

---

## 14. Approval Checklist (Founder)

- [ ] North Star accepted  
- [ ] Cancellation-first wedge overrides Add-Car-first GTM  
- [ ] $49/$99 pricing published to brokers  
- [ ] Anti-goals accepted for 90 days  
- [ ] Trial model (supervised → unsupervised path) accepted  
- [ ] Stale RAG goal docs scheduled for rewrite  
- [ ] Constitution added to PROJECT_DOC_SYSTEM_MAP START HERE  

---

*End of Unified Intake V1 Constitution Proposal*
