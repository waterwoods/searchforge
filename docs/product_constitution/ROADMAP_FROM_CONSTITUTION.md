# Roadmap from Constitution V1

**Version:** V1 Ratified (P14-B Constitution Sprint)  
**Date:** 2026-05-31  
**Rule:** Only highest-ROI improvements. Every row maps Capability → Improvement → Sprint → Expected Impact.

**Excluded by constitution:** Platform work, repo cleanup, Stripe, OAuth, WeChat sync, CRM, enterprise features.

---

## Sprint 1 — Broker Front Door + Trust (Week 1)

**Goal:** Raise Front Door 35 → 75; unlock unsupervised Day 1 ≥70.

| Capability | Improvement | Sprint | Expected Impact |
|------------|-------------|--------|-----------------|
| **Broker Front Door** | Default trial URL to 办公室工作台 (`?tab=broker`) | Week 1 Day 1–2 | Fixes #1 Day-1 failure; +25 Front Door |
| **Broker Front Door** | Hide API endpoint, PG mirror tags, 路由/指标 in product_only | Week 1 Day 1–2 | Instant broker trust; +15 Front Door |
| **Broker Front Door** | One-line wayfinding: "经纪人：请在本页粘贴客户消息" | Week 1 Day 2 | Replaces tab confusion; +10 Front Door |
| **Broker Front Door** | Auto-open cancellation after demo queue load | Week 1 Day 3 | First value moment; +10 Front Door |
| **Broker Front Door** | Demo queue progress indicator (3/13…) | Week 1 Day 3 | Prevents 30s abandon; +5 Front Door |
| **Customer Intake Collection** | Paste copy: "原样粘贴微信/通知文字，不用整理" | Week 1 Day 2 | Sets workflow expectation; +8 Intake |
| **Customer Intake Collection** | First-request loading: "首次分析约30秒" | Week 1 Day 3 | Prevents "broken" abandon; +8 Intake |
| **Broker Front Door** | Inline 3 practice scenarios (replace Simulation) | Week 1 Day 4–5 | Playbook works on prod; +10 Front Door |

**Sprint 1 exit:** Founder dry-run PASS; Day 1 score ≥70 with kickoff.

---

## Sprint 2 — Deploy + Operator Gate (Week 1 overlap)

**Goal:** Raise Founder Control 68 → 85; enable payment trust.

| Capability | Improvement | Sprint | Expected Impact |
|------------|-------------|--------|-----------------|
| **Founder / Operator Control** | `validate_pilot_deploy_env.py` PASS + deploy + `/readyz` | Week 1 Day 3–4 | Cases persist; +10 Founder Control |
| **Founder / Operator Control** | Formalize broker UX launch checklist | Week 1 Day 4 | Two-gate launch; +8 Founder Control |
| **Founder / Operator Control** | Remove SIM1–SIM3 from broker-facing materials | Week 1 Day 4 | Playbook trust; +5 Founder Control |
| **Structured Case Record** | Prod Postgres-only path validated | Week 1 Day 4 | Trust killer removed; +8 Case Record |
| **Founder / Operator Control** | Founder dry-run with observation log | Week 1 Day 5 | Catches doc/UI gaps; +5 Founder Control |

**Sprint 2 exit:** Script PASS + UX checklist PASS + prod `/readyz` green.

---

## Sprint 3 — Commercial Pack (Week 1 end)

**Goal:** Raise Trial Conversion 45 → 65; unblock Day 7 conversation.

| Capability | Improvement | Sprint | Expected Impact |
|------------|-------------|--------|-----------------|
| **Trial Conversion** | Add $49/$99 to BROKER_ONE_PAGER | Week 1 Day 4 | Payment path clear; +10 Trial Conversion |
| **Trial Conversion** | 1-page pilot terms (Chinese) | Week 1 Day 5–6 | Trust + legal clarity; +10 Trial Conversion |
| **Trial Conversion** | Invoice template (WeChat/PDF) | Week 1 Day 6 | Expense path; +8 Trial Conversion |
| **Trial Conversion** | Extend observation log with "minutes saved" field | Week 1 Day 5 | Quantitative proof; +7 Trial Conversion |
| **Founder / Operator Control** | Update TRIAL_ONE_PATH — remove Simulation dependency | Week 1 Day 5 | Doc/UI parity; +5 Founder Control |

**Sprint 3 exit:** Commercial artifacts in broker's hands before Day 0.

---

## Sprint 4 — Chen Kui Supervised Trial (Week 2)

**Goal:** Prove or kill; raise Trial Conversion 65 → 80+ with evidence.

| Capability | Improvement | Sprint | Expected Impact |
|------------|-------------|--------|-----------------|
| **Trial Conversion** | Day 0: 30-min founder kickoff | Week 2 Day 0 | Day 1 score 72 vs 28; critical |
| **Trial Conversion** | 7-day observation log — no new features | Week 2 Days 1–7 | Proof or kill; +15 Trial Conversion |
| **Case Lifecycle Management** | 15-min assistant training script | Week 2 Day 0 | $99 tier justification; +5 Lifecycle |
| **Structured Case Record** | Fix-now: top 3 draft failures from trial only | Week 2 async | Payment blocker #4; +8 Case Record |
| **Trial Conversion** | Day 7: invoice or ranked blockers | Week 2 Day 7 | Revenue decision; +10 Trial Conversion |
| **Trial Conversion** | Capture Day 7 quote if positive | Week 2 Day 7 | Second broker gate; +5 Trial Conversion |

**Sprint 4 exit:** Payment received OR written kill reasons with ranked blockers.

---

## Sprint 5 — Fix-Now Only (Week 3–4, conditional)

**Goal:** Top 3 friction from trial log only. No new capabilities.

| Capability | Improvement | Sprint | Expected Impact |
|------------|-------------|--------|-----------------|
| **Case Lifecycle Management** | Simplify queue filters; highlight 更新客户新消息 | Week 3 | Follow-up habit; +10 Lifecycle |
| **Structured Case Record** | Load chen_kui ui_copy.json; replace "case" with 服务记录 | Week 3 | Label trust; +7 Case Record |
| **Urgent Message Triage** | Fix-now category/draft tuning from trial failures | Week 3 | Real-message accuracy; +5 Triage |
| **Broker Front Door** | Collapse pilot intro alert; hide 我的办理 in trial mode | Week 3 | Less overwhelm; +5 Front Door |

**Sprint 5 gate:** Only items from trial observation log. Max 3.

---

## Not on Roadmap (Constitution Locked)

| Item | Reason |
|------|--------|
| Stripe / billing portal | Anti-goal v1 |
| WeChat sync | Anti-goal v1 |
| CRM / carrier APIs | Anti-goal v1 |
| Multi-tenant / OAuth | Anti-goal v1 |
| Repo cleanup / lab isolation | Anti-goal during trial |
| $199 tier | Features don't exist |
| Platform / RAG features | Out of product scope |
| New scenarios beyond fix-now | No expansion before payment proof |
| P12/P13 strategy sprints | Don't exist; defer until first payment |

---

## Recommended First Implementation Sprint

**Sprint 1: Broker Front Door + Trust (Week 1, Days 1–5)**

This is the highest-ROI cluster because P10/P11 agree: triage is ready; front door kills Day 1. Without Sprint 1, trial conversion cannot succeed regardless of engine quality.

**Minimum viable Week 1 bundle (P11 order):**

1. Trust pass: hide API URL, PG tags, debug tags  
2. Front door: broker tab default + wayfinding banner  
3. First value: auto-open cancellation + loading states  
4. Playbook parity: inline practice + doc label sync  

**Parallel track:** Sprint 2 deploy validation must complete before Chen Kui Day 0.

---

*End of Roadmap from Constitution V1*
