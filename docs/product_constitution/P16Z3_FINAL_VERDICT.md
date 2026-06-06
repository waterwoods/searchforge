# P16-Z3 Final Verdict

**Date:** 2026-06-01  
**Sprint:** P16-Z3 Case Intelligence Maturity Model Sprint  
**Constraint honored:** Zero code written. Zero deploy. Zero P17. Zero UI implementation.

---

## Sprint success criteria

| Criterion | Met? |
|-----------|------|
| Maturity model designed and challenged | ✅ |
| Current state scored per level | ✅ |
| Repository archaeology complete | ✅ |
| Hidden capabilities ranked | ✅ |
| Reverse engineering map vs 6 companies | ✅ |
| Gap analysis (tech/UX/workflow/commercial) | ✅ |
| 30-day plan with Must/Should/Wait/Never | ✅ |
| 90-day plan with paying office assumption | ✅ |
| One capability test | ✅ |
| Andy can understand where we are | ✅ |
| Code produced | ❌ None (correct) |

---

## 1. Current maturity level

| Lens | Level | Meaning |
|------|-------|---------|
| **Engine (codebase)** | **L4.5** | Strong L1–L4 single-turn; partial L5–L7 backend |
| **Deployed product** | **L3.5** | Paste → glance → copy works; append/OCR hidden |
| **Chen Kui effective today** | **L2.5** | FP-004 SSO + undiscoverable append cap value |
| **P16-Y battery verified** | **L4.0** | 88.6/100 avg; multi-turn drags L5 |
| **30-day target** | **L5.0 deployed** | After access fix + append UX + summary merge |

**One-line:** You built an **L4.5 engine** deployed as an **L3.5 experience** with **L2.5 access**.

---

## 2. Highest-ROI hidden capability

**Post-copy append bridge + existing append API**

| | |
|---|---|
| **What** |「客户回复了？追加到此案件」CTA after copy — wires to existing `appendCaseMessage()` |
| **Why highest ROI** | Fixes continuity 41→70+; zero backend; unlocks multi-turn office workflow |
| **Effort** | 0.5 day UX copy |
| **Maturity** | Exposes hidden **L5** backend |

Runner-up: Chinese broker_next_step templates (L4, 1 day tune).

---

## 3. Most important missing capability

**Multi-turn summary merge (P16-Y P0)**

| | |
|---|---|
| **What** | Prior customer bubbles injected into `conversation_summary` on append |
| **Why most important** | Y44 fails; broker must re-read WeChat on corrections — breaks "office-executable case" promise |
| **Effort** | 1–2 days engine tune in `triage.py` — NOT new service |
| **Maturity** | Blocks **L5** distillation |

Note: **Access (FP-004)** is the most important **blocker** but not a missing capability — it's a 5-minute founder toggle.

---

## 4. Biggest waste of engineering time

**Rebuilding capabilities that already exist in `services/fiqa_api/inbox_triage/`**

| Waste pattern | Already exists | Est. wasted effort if rebuilt |
|---------------|----------------|-------------------------------|
| New Case Intelligence microservice | `triage.py` + `case_draft_engine.py` | Weeks |
| New conversation/append service | `triage_conversation()` + `triage_for_append()` | Weeks |
| New OCR pipeline | `image_input_pipeline.py` + `ocr_case_fusion.py` | Days |
| New risk engine | v4/v5 in `case_draft_engine.py` | Days |
| Customer portal from scratch | `CustomerEntryTab.tsx` + `MyRequestsTab.tsx` | Weeks |
| SimulationAssistant | `ScenarioReplayTab.tsx` exists; Assistant orphaned | Days |
| ~197 lab script batteries | guardrail + p16y battery sufficient | Ongoing cognitive load |
| P17 platform features | Constitution blocked | Months |

**Second biggest waste:** UI sprints (P16-M TOP50) before FP-004 off and append CTA — polishing a door that's locked.

---

## 5. Top 10 discoveries

1. **48 inbox_triage modules** form a complete Case Intelligence engine — no microservice needed.
2. **Append backend is production-grade** (`triage_for_append`, boundary enforcement, tests) — UX is the gap.
3. **P16-Y battery at 88.6** proves L1–L4 single-turn excellence on wedge lanes.
4. **Office Actionability rubric at ceiling (25/25)** — Chinese copy specificity is the remaining L4 gap, not architecture.
5. **OCR pipeline is built end-to-end** — Vision API → parse → fuse → triage; no product UI caller for inline image.
6. **v4/v5 risk scores computed every add-car turn** — zero UI rendering despite TS types existing.
7. **CustomerEntryTab + MyRequestsTab exist** — hidden by `productOnlyUi`, not missing.
8. **SimulationAssistant.tsx is orphaned** (zero imports) — ScenarioReplayTab is the real lab tool.
9. **Example maturity model was wrong** — multi-turn (L5) and document intel (L6) were underweighted vs risk (L7).
10. **Every benchmark company (Zendesk, Intercom, Salesforce, Stripe, Linear, HubSpot) implements the same L0–L4 pipeline** — SearchForge engine matches; deployed surface doesn't.

---

## 6. Top 10 actions (next 30 days)

| # | Action | Level | Owner | Days |
|---|--------|-------|-------|------|
| 1 | Disable FP-004 Preview SSO | L0 | Founder | 0 |
| 2 | Chinese broker_next_step templates + blocklist | L4 | Dev | 1 |
| 3 | Post-copy append CTA | L5 | Dev | 0.5 |
| 4 | Append summary merge (P16-Y P0) | L3/L5 | Dev | 1–2 |
| 5 | EN/ZH glance fix | L4 | Dev | 0.5 |
| 6 | Supervised Chen Kui Day 0 | L9 | Founder | 0.25 |
| 7 | Observation log row 1 + protocol | L9 | Founder | 0.25 |
| 8 | P16-Y battery ≥88 CI gate | L7 | Dev | 0.5 |
| 9 | Correction keyword rules (Y44) | L5 | Dev | 0.5 |
| 10 | Invoice sent + payment received | L9 | Founder | — |

**New capabilities to build: 0.**

---

## 7. Top 10 non-goals

1. **P17 platform** — constitution blocked
2. **Stripe in-app billing** — manual until 3+ offices
3. **Full CRM** — offices have AMS
4. **New Case Intelligence microservice** — triage.py exists
5. **New conversation/append backend** — append route exists
6. **OCR-first primary intake** — text paste is wedge
7. **Voice/IVR** — out of pilot scope
8. **Customer tab on Day 0** — broker paste first; week 3
9. **Full P16-M TOP50 UI sprint** — copy fixes only
10. **LLM generation path** — rules at 88.6; unverified path defer

---

## 8. 30-day roadmap

### Week 1: L3.5 → L4.5 (Access + Single-Turn Excellence)

- FP-004 off · deploy · Chinese templates · EN/ZH fix
- Post-copy append CTA · summary merge · blocklist
- Invoice IDs · observation log · founder E2E

**Exit:** Cold URL · cancel paste <45s · guardrail PASS

### Week 2: L4.5 → L5.0 (Multi-Turn Proof)

- Supervised Day 0 · correction rules · duplicate-case fix
- waiting_on after copy · OCR wire · CI gate ≥88
- 5 real cases logged · invoice sent

**Exit:** ≥3 real cases · ≥1 append success · broker feedback

### Week 3: L5.0 + Payment

- Payment received · testimonial · log-driven top-3 fixes
- Customer tab only if broker requests

**Exit:** Payment · testimonial · continue/expand/pivot documented

See `P16Z3_30_DAY_PLAN.md` for full Must/Should/Wait/Never tables.

---

## 9. 90-day roadmap

### Month 2 (Days 31–60): Retention + Office #2

- Weekly log review · append on 50%+ multi-turn · customer tab if needed
- Production URL stable · battery gate 90 · time-saved evidence
- Second broker intro · renewal conversation

**Target:** Deployed **L5.5** · Chen Kui renews unsupervised

### Month 3 (Days 61–90): Scale + Document Intel

- Second office Day 0 · OCR production · outcome pricing talk
- Customer message-first if Cap 4 deployed · cap scorecard re-baseline
- 2 offices paying OR $99 upsell

**Target:** Deployed **L6.5** · ≥50 cumulative cases · onboarding <30 min founder time

See `P16Z3_90_DAY_PLAN.md` for decision gates G1–G4.

---

## Document index (P16-Z3 deliverables)

| Phase | Document |
|-------|----------|
| 1 | `P16Z3_MATURITY_MODEL.md` |
| 2 | `P16Z3_CURRENT_STATE.md` |
| 3 | `P16Z3_ARCHAEOLOGY.md` |
| 4 | `P16Z3_HIDDEN_CAPABILITIES.md` |
| 5 | `P16Z3_REVERSE_ENGINEERING_MAP.md` |
| 6 | `P16Z3_GAP_ANALYSIS.md` |
| 7 | `P16Z3_30_DAY_PLAN.md` |
| 8 | `P16Z3_90_DAY_PLAN.md` |
| 9 | `P16Z3_ONE_CAPABILITY_TEST.md` |
| 10 | `P16Z3_FINAL_VERDICT.md` (this file) |

**Prior sprints (still authoritative):** P16-Y, P16-Z0, P16-Z2, P16-Z2.5 in same directory.

---

## One-line founder read

> **You are at maturity L4.5 in code and L3.5 deployed. The next 30 days are not a build sprint — they are a revival sprint: fix the URL, teach append, merge multi-turn summaries, tune Chinese next actions, run Day 0 with Chen Kui, get paid.**

---

*End of P16-Z3 — Case Intelligence Maturity Model Sprint*
