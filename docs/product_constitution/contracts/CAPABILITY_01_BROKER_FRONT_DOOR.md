# Capability Contract 01 — Broker Front Door

**Capability:** Broker Front Door  
**Version:** V1 Ratified  
**Date:** 2026-05-31  
**Maps to:** Capability Map V1 §1

---

## SECTION 1 — Purpose

Why this capability exists.

The broker must reach **cancellation triage value** in under 5 minutes without founder translation. P10 and P11 agree: the triage engine is trial-ready; the **broker front door is not**. This capability owns the path from URL open → correct tab → clean UI → demo queue → first cancellation case visible.

Without a working front door, every downstream capability is invisible on Day 1.

---

## SECTION 2 — Primary User

Who uses it.

| User | Usage |
|------|-------|
| **Broker owner** (Chen Kui) | Opens trial URL daily; lands on workbench first |
| **Office assistant** | Same entry path; must not require separate training doc |
| **Founder** | Validates front door before Day 0 kickoff |

---

## SECTION 3 — Inputs

What enters the capability.

| Input | Source |
|-------|--------|
| Trial URL | `/workbench/unified-intake` (optionally `?tab=broker`) |
| Product mode | `product_only` — no lab/simulation chrome |
| Demo queue request | Broker clicks 加载演示队列 |
| Broker context | First visit vs returning; supervised vs unsupervised |

---

## SECTION 4 — Outputs

What must come out.

| Output | Requirement |
|--------|-------------|
| **Correct default tab** | 办公室工作台 (Broker Workbench) — not 客户报送 |
| **Clean broker surface** | No PG mirror tags, API URL, debug routes visible |
| **Wayfinding** | One-line: "经纪人：请在本页粘贴客户消息" |
| **Demo queue loaded** | Progress indicator during 15–30s load |
| **First value case open** | Cancellation case auto-selected after demo queue load |
| **Trust signals** | Footer: 不自动发送; no engineer labels |

---

## SECTION 5 — Success Metrics

How success is measured.

| Metric | Target | Source |
|--------|--------|--------|
| Unsupervised Day 1 score | ≥70 / 100 | P11 TRIAL_REALITY_AUDIT |
| Time to cancellation value | ≤5 min without founder | North Star anti-drift test |
| Wrong-tab abandonment | 0 on trial Day 1 | Observation log |
| Engineer chrome visible | 0 instances in product_only | Broker UX checklist |
| Demo queue load abandon | &lt;10% during kickoff | Founder dry-run |

---

## SECTION 6 — Acceptance Criteria

How we know it works.

- [ ] Trial URL opens **办公室工作台** by default (no manual tab click)  
- [ ] product_only UI hides: PG 镜像 tags, API endpoint URL, 路由/指标 debug tag, engineer filters  
- [ ] Broker can load 加载演示队列 and see progress (e.g., "3/13…")  
- [ ] Cancellation case opens automatically after demo queue completes  
- [ ] Founder dry-run completes playbook Day 0 steps without mentioning Simulation Assistant tab  
- [ ] Chen Kui archetype broker reaches Case focus + Your next move + draft without founder on screen  

---

## SECTION 7 — Current State

Score **0–100** today.

### Score: **35 / 100**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Default tab | 15 | UI defaults to 客户报送 (Add-Car) |
| Engineer chrome | 20 | PG tags, API URL visible |
| Demo queue UX | 45 | Works but slow; no progress |
| First value moment | 40 | Cancellation not auto-opened |
| Wayfinding | 30 | Four tabs; no broker start-here |
| Trust surface | 50 | Draft copy works if reached |

**P11 reference:** Product surface UX scored 35/100; Day 1 unsupervised 28/100.

---

## SECTION 8 — Gap Analysis

What's missing.

| Gap | Severity |
|-----|----------|
| Wrong default tab (Customer Entry vs Workbench) | **P0** |
| Engineer artifacts (PG 镜像, API URL, debug tags) | **P0** |
| No broker wayfinding banner | **P0** |
| Demo queue load with no progress feedback | **P1** |
| Cancellation not auto-opened after demo load | **P1** |
| Simulation Assistant required in playbook but hidden | **P1** |
| Add-Car-first messaging vs cancellation-first trial | **P1** |
| English "case" / "Unified Intake" in nav | **P2** |
| Pilot intro alert wall of text | **P2** |
| 我的办理 tab unclear in trial mode | **P2** |

---

## SECTION 9 — Top 10 Improvements

Ranked.

| # | Improvement | ROI |
|---|-------------|-----|
| 1 | Default trial URL to 办公室工作台 (`?tab=broker`) | Critical — fixes #1 Day-1 failure |
| 2 | Hide API endpoint label in product-only UI | Instant trust |
| 3 | Hide PG mirror tags + trust line in product-only | "Not finished" signal removed |
| 4 | Hide 路由/指标 debug tag in product-only | Pure broker surface |
| 5 | One-line wayfinding: "经纪人：请在本页粘贴客户消息" | Replaces tab confusion |
| 6 | Auto-open cancellation case after demo queue load | First value moment |
| 7 | Demo queue progress: "正在加载13条示例 (3/13…)" | Prevents 30s abandon |
| 8 | Inline 练习场景 panel (3 scenarios) — replace hidden Simulation | Playbook works on prod |
| 9 | Collapse pilot intro alert by default (production) | Less Day-0 overwhelm |
| 10 | Hide 我的办理 tab in broker-only trial mode | Single front door |

---

## SECTION 10 — Must Not Build

Prevent scope creep.

- New tabs or navigation redesign beyond trial-mode simplification  
- Customer Entry portal as **default** landing for Chen Kui trial  
- Simulation Assistant tab dependency in broker-facing playbook  
- WeChat sync as "front door" replacement  
- Mobile-first redesign (desktop-only acceptable in v1 terms)  
- Stripe checkout or signup flow on front door  
- RAG `/demo` page as trial entry URL  
- Platform/lab sidebar routes in product_only  
- Custom branding / white-label per broker  
- OAuth / login wall before paste  

---

*End of Capability Contract 01*
