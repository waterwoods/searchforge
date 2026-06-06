# P16-Z0 Commercial Archaeology

**Date:** 2026-06-01  
**Sprint:** P16-Z0 — Phase 6  
**Search terms:** Day0, Day3, Day7, Observation Log, Commercial Pack, Invoice, Trial  
**Evidence:** `docs/trial/`, `P16K_*`, `P16{S,U,X}_*`, `scripts/trial_*`

---

## Executive summary

**Commercial documentation is among the most complete artifacts in the repo.** Payment execution is not — empty invoice IDs, zero observation log rows, Preview SSO blocking Day 0, and Cap 6 deploy score ~51 block first revenue.

P16-K closed the **doc gap**; P16-L/U/X closed the **reality gap**.

---

## Commercial Pack (P16-K)

| # | Deliverable | Path | Status |
|---|-------------|------|--------|
| 1 | Payment readiness audit | `P16K_PAYMENT_READINESS_AUDIT.md` | Complete |
| 2 | Broker one-pager v2 | `BROKER_ONE_PAGER_V2.md` | Complete |
| 3 | Pilot terms v1 | `docs/trial/PILOT_TERMS_V1.md` | Complete |
| 4 | Invoice $49 | `docs/trial/INVOICE_TEMPLATE_49.md` | Template — **IDs empty** |
| 5 | Invoice $99 | `docs/trial/INVOICE_TEMPLATE_99.md` | Template — **IDs empty** |
| 6 | Observation log v2 | `docs/trial/TRIAL_OBSERVATION_LOG_V2.md` | Complete |
| 7 | Chen Kui Day 0 script | `docs/trial/CHEN_KUI_DAY0_SCRIPT.md` | Complete |
| 8 | Day 7 payment checklist | `docs/trial/DAY7_PAYMENT_CHECKLIST.md` | Complete |
| 9 | First payment forecast | `FIRST_PAYMENT_FORECAST.md` | Complete |
| 10 | Commercial scorecard | `P16K_COMMERCIAL_SCORECARD.md` | Complete |

**P16-K verdict:** *"Can Andy ask for money today? **No — not confidently.**"*  
*Not missing: pricing, terms, invoice structure, Day 0/7 scripts, observation log fields.*

---

## Day 0 / Day 3 / Day 7

These are **journey milestones**, not separate code modules.

| Day | Definition | Artifacts | Product support | Blocker |
|-----|------------|-----------|-----------------|---------|
| **Day 0** | Paste real thread → useful draft in <5 min | `CHEN_KUI_DAY0_SCRIPT.md`, Reality Q13–14 | Broker paste path | **FP-004 Preview SSO**; cold URL 401 |
| **Day 3** | Draft language matches office (Chinese) | Reality Q15 | Partial — English `broker_next_step` on deploy (F-005) | i18n/product_only |
| **Day 7** | Would return without founder; payment ask | `DAY7_PAYMENT_CHECKLIST.md`, Cap 6 | No in-app minutes-saved (F-027) | Invoice IDs; observation evidence |

### Simulation quotes

- Assistant: *"reverts to WeChat-only by Day 3"* (`P16X_ASSISTANT_SIMULATION.md`)
- Chen Kui: Day 7 needs proof of time saved — no in-app counter (`P16X_CHENKUI_SIMULATION.md`)
- P16-V reality gate: Day 0 requires SSO fix (~5 min founder), E2E log, observation protocol start

---

## Observation Log

| Version | Path | Status |
|---------|------|--------|
| Template v1/v2/v3 | `docs/trial/TRIAL_OBSERVATION_LOG_*` | **Protocol exists** |
| Linked from product UI | — | **No** (F-047) |
| Real rows logged | — | **Zero** (`P16S_FOUNDER_REVIEW.md`) |
| Checked by script | `trial_readiness_check.sh` | Template file exists |

**Gap:** Docs without discipline = Day 7 surprise (*"Could have reached Day 7 and had nothing to send"* — P16-S).

---

## Invoice & payment

| Item | Status |
|------|--------|
| $49 / $99 structure | Documented |
| Zelle/Venmo/WeChat payee IDs | **Empty placeholders** (FP-009) |
| Stripe / in-app billing | **Not in repo** (constitution out-of-scope) |
| Cap 6 Day 7 payment path score | **38/100** deployed (P16-X) |

---

## Trial automation (scripts)

| Script | Purpose |
|--------|---------|
| `trial_readiness_check.sh` | Docs + guardrail + UI build |
| `trial_launch_check.sh` | Single gate before first broker trial |
| `founder_pre_trial_checklist.sh` | Founder manual steps |
| `summarize_readiness_posture.sh` | Readiness summary |
| `deploy_paid_pilot.sh` | Deploy tuple |
| `validate_pilot_deploy_env.py` | Env validation |

**TRIAL_ONE_PATH** — referenced across P16-T/U/X as unchanged process SSOT (`docs/trial/`).

---

## Capability 6 mapping

| Commercial artifact | Capability contract |
|--------------------|---------------------|
| Observation log | Evidence for trial conversion |
| Day 7 checklist | Payment gate |
| Invoice | First revenue instrument |
| Day 0 script | Activation proof |

Cap 6 deploy score **51** (P16-X) vs threshold **60+** with evidence.

---

## Timeline to first invoice (from P16-K)

```text
1. Fill invoice contact details (Andy)
2. Preview redeploy + Andy 15-min E2E log
3. Supervised Day 0 per CHEN_KUI_DAY0_SCRIPT.md
4. 7 days with TRIAL_OBSERVATION_LOG_V2.md
5. Day 7 per DAY7_PAYMENT_CHECKLIST.md → $49 if gates pass
Expected: 10–14 days from Day 0 scheduling
```

---

## Status matrix

| Item | Documented | Implemented (product) | Executed |
|------|------------|----------------------|----------|
| Commercial Pack | Yes | N/A | Partial |
| Day 0 script | Yes | Paste UI | **Blocked** |
| Day 3 quality bar | Yes | Partial i18n | Not validated |
| Day 7 checklist | Yes | No automation | Not reached |
| Observation log | Yes | Not in UI | **0 rows** |
| Invoice send | Yes | No | **No IDs** |
| Trial scripts | Yes | Yes | Runnable |

---

## Revival priorities (commercial)

1. **FP-004** — Preview SSO off (~5 min) — unblocks Day 0
2. **Fill invoice IDs** (~30 min Andy)
3. **First observation log row** on Day 0 — discipline, not code
4. **Do not build** billing SaaS — use templates + manual invoice

---

## Evidence index

| Artifact | Path |
|----------|------|
| P16-K verdict | `P16K_FINAL_VERDICT.md` |
| FP-009 | `FAILURE_PATTERN_LIBRARY.md` |
| Trial index | `docs/trial/INDEX.md` |
| P16-U GO/NO-GO | `P16U_GO_NO_GO.md` |

---

*End of P16-Z0 Commercial Archaeology*
