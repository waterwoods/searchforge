# P16-Z9 Phase 9 — 90-Day Filter

**Date:** 2026-06-02  
**Sprint:** P16-Z9 SSOT Consolidation  
**Question:** Based on all discoveries (P16-Y through P16-Z8, Role D), what should **NOT** be built in the next 90 days?

---

## Filter principle

> **If it already exists in `inbox_triage/` or BrokerWorkbenchTab, the answer is wire — not build.**

90 days = **revive, deploy, validate, get paid** — not expand product surface.

---

## NEVER build (constitution + archaeology)

| # | Do not build | Use instead | Source |
|---|--------------|-------------|--------|
| 1 | P17 platform | product_only pilot | Constitution |
| 2 | Case Intelligence microservice | `triage.py` + `case_draft_engine.py` | Z0, Z3 |
| 3 | Conversation / append service | `triage_for_append`, append route | Z0 |
| 4 | OCR-first primary intake product | Text paste wedge; wire attachment path later | Z0, Z3 |
| 5 | PaymentMemoryService | Payment logic in triage.py | Z8 |
| 6 | WaitingOnEngine microservice | case_store + triage heuristic | Z8 |
| 7 | ClaimsIntakeService / greenfield FNOL | Tune `_extract_claim_fields` | Z6, Z7 |
| 8 | CollectedFieldsMergeService | Generalize add-car merge helper | Z8 |
| 9 | Stripe / in-app billing | Manual invoice until 3+ offices | Z3 |
| 10 | Full CRM / AMS replacement | Offices keep existing AMS | Z2 |
| 11 | WeChat integration / bot | Broker stays channel | Z4 |
| 12 | SimulationAssistant v2 | ScenarioReplayTab + Role D battery | Z0 |
| 13 | Customer portal from scratch | `CustomerEntryTab` exists | Z0 |
| 14 | Voice / IVR intake | Out of scope | Z3 |
| 15 | ML distillation experiment | Rules at 88.6 sufficient | Z0 |
| 16 | New add-car battery runners | p16y + role_d only | Z0 duplication |
| 17 | LLM generation rewrite | Unverified; rules-first | Y, Z3 |
| 18 | Multi-tenant auth platform | Single broker pilot | auto-evolution branches |
| 19 | Outcome / resolution product UI | Observation log first | MASTER_OUTLINE |
| 20 | Push notifications / email automation | WeChat is channel | Z2 |

---

## DO NOT build in days 1–30 (even if tempting)

| Item | Why wait | Do instead |
|------|----------|------------|
| P16-M full TOP50 UI sprint | FP-004 + append first | TOP10 copy batch |
| Customer tab on trial URL | Cap 4 Tier 3 | Broker paste Day 0 |
| Inline image paste UI | OCR path exists; no caller | Text wedge + deploy Z6 |
| Outcome pricing UI | No closure field process | Manual invoice |
| Second office onboarding | Chen Kui not paid | Supervised Day 0 |
| Risk dashboard | v4 score exists | Single glance badge |
| Audit export product | Scaffold only | Ignore |
| New simulation personas | Role D covers multi-day | Extend role_d_journeys.json |
| Architecture sprint | Z9 SSOT complete | Ship Z8 slice |
| Doc-only sprint | Z9 closes doc debt | Ship + validate |

---

## DO NOT build in days 31–60

| Item | Why wait | Unlock condition |
|------|----------|------------------|
| Customer tab exposure | Broker WeChat primary | Broker request OR Role D ≥80 |
| OCR production inline UI | Tier 3 | Claim/doc volume in observation log |
| Deadline countdown widget | Nice-to-have | waiting_on SOP working |
| Full activity timeline merge | Z6 thread sufficient first | Broker feedback |
| LLM path production | Cost + unverified | Rules plateau + founder decision |
| Second office GTM | One paid office first | Chen Kui renews |
| HubSpot-style sequences | Not wedge | Never in 90 days |
| Document intelligence L6 | Memory L5 incomplete | Role D sustained pass |

---

## DO NOT build in days 61–90 (unless gates pass)

| Item | Gate required |
|------|---------------|
| Customer message-first primary | 2 offices OR explicit broker demand |
| Outcome / resolution fields in UI | 50+ logged cases with observation outcomes |
| Outcome-based pricing automation | 3+ paying offices |
| Platform_full re-enable | Never in paid pilot |
| Auto-evolution branch resurrection | Never — learnings in SSOT |
| P17 features | Constitution |

---

## BUILD (allowed — Tier 1 only)

| # | Allowed work | Max effort | Cap |
|---|--------------|------------|-----|
| 1 | FP-004 off + redeploy | 1 day | 1, 6 |
| 2 | Post-copy append CTA + collapse paste | 1 day | 1, 5 |
| 3 | Z6 thread UI deploy | 0.5 day | 5 |
| 4 | Y44/Y45 summary merge + collected merge | 3 days | 2, 5 |
| 5 | Chinese payment/remove-car lane guards | 2 days | 2 |
| 6 | waiting_on triage heuristic | 0.5 day | 5 |
| 7 | Claim field extensions (plate, police, carrier) | 1 day | 2 |
| 8 | Chinese broker_next_step templates | 1 day | 3 |
| 9 | P16-Y + Role D CI gates | 1 day | 7 |
| 10 | Observation log + 3 real cases | founder | 6 |
| 11 | v4 risk badge in glance | 0.5 day | 3 |
| 12 | Append sim in trial_launch_check | 2 hr | 7 |

**Total engineering budget:** ~3 weeks focused + deploy — matches Z8 plan.

---

## Decision gates (90-day)

| Gate | Day | Pass criteria |
|------|-----|---------------|
| G1 Access | 7 | Cold URL, guardrail green |
| G2 Turn 1 | 14 | p16y ≥88, one supervised Day 0 |
| G3 Memory | 30 | Role D reread ≥80, ≤2/10 WeChat |
| G4 Commercial | 45 | Invoice sent, 3 logged multi-turn cases |
| G5 Retention | 90 | Renew OR second office OR pivot doc |

**If G3 fails:** No customer tab, no OCR product, no second office — engine slice only.

---

## One-line 90-day filter

> **Wire what exists, deploy what works, prove memory with Role D + observation log — do not invent services, personas, or platforms.**

---

*End of P16-Z9 Phase 9 — 90-Day Filter*
