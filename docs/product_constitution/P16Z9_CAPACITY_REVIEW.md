# P16-Z9 Phase 4 — Seven Capacity Review

**Date:** 2026-06-02  
**Sprint:** P16-Z9 SSOT Consolidation  
**Sources:** P16Z25_CAPACITY_RANKING, P16-Z0/Z3/Z5/Z7/Z8 verdicts, Role D, CURRENT_PRODUCT_SHAPE

---

## The seven capacities (definitions unchanged)

| # | Capacity | One-line job |
|---|----------|--------------|
| 1 | Broker Front Door | URL → paste → draft → copy in <2 min |
| 2 | Case Intelligence | Paste → category, urgency, summary, fields |
| 3 | Structured Case Record | Office acts without re-reading raw WeChat |
| 4 | Customer Intake Collection | Customer sends request; office gets handoff |
| 5 | Case Lifecycle Management | Turns 2–4 same case; waiting state clear |
| 6 | Trial Conversion | Andy → Chen Kui → invoice → testimonial |
| 7 | Founder / Operator Control | Ship with confidence; no silent regressions |

---

## Tier definitions (P16-Z9)

| Tier | Meaning | 90-day rule |
|------|---------|-------------|
| **Tier 1** | Pilot survival — must improve every sprint until trial paid | Active engineering + founder ops |
| **Tier 2** | Important — wire after Tier 1 gates pass | Scheduled; no greenfield |
| **Tier 3** | Defer — week 7+ or second office | No sprint unless broker asks |

---

## Tier 1 — Pilot survival (do first)

### Cap 2 — Case Intelligence ★ Product soul

| Signal | Score (Jun 2026) | Blocker |
|--------|------------------|---------|
| P16-Y battery | 88.6 avg Turn 1 | — |
| Role D multi-day | 60.7/75 memory | Y44/Y45 merge, D10/D07 lanes |
| Z8 archaeology | 65–70% built | Lane guards + collected merge |

**Tier 1 actions:** Chinese payment/lapse, remove-car guard, generic `_merge_persisted_collected`, claim field extensions (Z8 plan). **Do not** build CaseIntelligenceService.

---

### Cap 1 — Broker Front Door ★ Access blocker

| Signal | Score | Blocker |
|--------|-------|---------|
| Deployed | ~45 | FP-004 Preview SSO |
| Z6 shipped | Thread + append CTA (pending deploy) | Deploy parity |

**Tier 1 actions:** FP-004 off, post-copy append line, collapse paste when case open, Chinese-only glance. **15 min – 2 days** mostly UX/copy.

---

### Cap 5 — Case Lifecycle ★ Retention loop

| Signal | Score | Blocker |
|--------|-------|---------|
| P16-X continuity | 41–53 | Append hidden until reopen |
| Z5 memory UX | Thread not hero | Z6 UI deploy |
| Role D | 6/10 pass without WeChat | Engine lanes + waiting_on |

**Tier 1 actions:** Append on first persist, 对话记录 thread, 本轮更新 delta, one-click waiting_on, append in trial_launch_check. **Backend exists.**

---

### Cap 7 — Founder Control ★ Regression prevention

| Signal | Score | Blocker |
|--------|-------|---------|
| guardrail | Exists | Not in CI gate for all PRs |
| Batteries | p16y + role_d | Role D not pre-deploy gate yet |

**Tier 1 actions:** P16-Y ≥88 CI; Role D post-engine-slice; single pre-trial command `trial_launch_check.sh`.

---

## Tier 2 — Important (after Tier 1 gates)

### Cap 3 — Structured Case Record

| Signal | Score | Notes |
|--------|-------|-------|
| Office actionability | 25/25 ceiling (P16-Y) | Chinese specificity gap |
| broker_next_step | Partial EN leakage | product_only pass |

**Tier 2 actions:** Chinese templates, 还缺 chips adjacent to next step, v4 risk badge in glance (wire existing), duplicate-case prevention copy.

---

### Cap 6 — Trial Conversion

| Signal | Score | Notes |
|--------|-------|-------|
| Commercial docs | doc-complete (P16-K) | payment not ready |
| Day 0 | Blocked by SSO | Supervised ritual |

**Tier 2 actions:** Observation log 3× multi-turn real cases, invoice IDs, testimonial capture, time-saved evidence. **Process > code.**

---

## Tier 3 — Defer (90-day filter)

### Cap 4 — Customer Intake Collection

| Signal | Score | Notes |
|--------|-------|-------|
| CustomerEntryTab | Built, hidden | productOnlyUi |
| Chen Kui week 1–2 | Broker paste only | WeChat is channel |

**Tier 3 until:** Broker requests OR second office OR Cap 1+5 Role D pass.

**Tier 3 actions (when unlocked):** Separate customer route, 我的办理 prominence — **wire, not rebuild.**

---

## Ranked table (Tier × strategic rank)

| Tier | Rank | Cap | Why |
|------|------|-----|-----|
| 1 | 1 | **2** Case Intelligence | Defines product; engine gaps = Role D failures |
| 1 | 2 | **1** Broker Front Door | SSO blocks all value |
| 1 | 3 | **5** Case Lifecycle | Multi-turn = paid retention |
| 1 | 4 | **7** Founder Control | Prevents redeploying broken memory |
| 2 | 5 | **3** Structured Case Record | Polish after loop works |
| 2 | 6 | **6** Trial Conversion | Payment follows proof |
| 3 | 7 | **4** Customer Intake | Week 7+ asset |

---

## Execution vs strategic (unchanged from Z2.5)

| This week's execution order | Strategic importance |
|----------------------------|----------------------|
| Cap 1 (access, copy) | Cap 2 (soul) |
| Cap 5 (append UX) | Cap 5 (continuity) |
| Cap 7 (batteries) | Cap 3 (record) |
| Cap 6 (Day 0 log) | Cap 6 (payment) |

---

## Capacity health dashboard (Jun 2026)

| Cap | Engine | Deployed | Chen Kui effective | 90-day target |
|-----|--------|----------|-------------------|---------------|
| 1 | 80 | 45 | 40 | 75 |
| 2 | 88 | 85 | 70 | 90 |
| 3 | 78 | 72 | 65 | 80 |
| 4 | 70 | 55 | N/A | 65 |
| 5 | 75 | 50 | 45 | 70 |
| 6 | 60 | 51 | 50 | 75 |
| 7 | 70 | 65 | — | 80 |

---

## Sub-capabilities: stop rebuilding

See `P16Z0_FINAL_VERDICT.md` — all seven caps already have code paths. Z9 rule: **Tier 1 = wire + tune + deploy only.**

---

*End of P16-Z9 Phase 4 — Seven Capacity Review*
