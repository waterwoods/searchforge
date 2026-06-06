# Trial Readiness Score — P10

**Date:** 2026-05-30  
**Evidence:** `trial_readiness_check.sh` PASS, `trial_launch_check.sh` PASS, doc review, UI inspection, env posture

---

## Overall score: **62 / 100**

**Interpretation:** Safe to run a **founder-supervised** trial locally or on staging. **Not** safe to drop Chen Kui on production URL tomorrow without founder on call and UI fixes. Scripts pass; broker experience and production posture have gaps.

---

## Breakdown

| Dimension | Score | Weight | Weighted | Rationale |
|-----------|-------|--------|----------|-----------|
| **Product clarity** | 55 | 25% | 13.75 | Strong docs; UI default tab and Add-Car vs cancellation story conflict |
| **Trial readiness** | 78 | 25% | 19.50 | Scripts PASS; guardrail 13/13; templates exist; Simulation hidden in prod UI |
| **Support readiness** | 65 | 20% | 13.00 | SUPPORT_TRUTH_MAP + manifest exist; single-founder L1–L4; no broker self-serve |
| **Founder readiness** | 70 | 15% | 10.50 | FOUNDER_ONE_PATH collapsed; must rehearse tab navigation |
| **Operator readiness** | 58 | 15% | 8.70 | Local env full_stack not product_only; .env.cloudrun not production-validated |

**Weighted total:** ~65.5 → rounded **62** after broker-experience penalty (doc/UI misalignment is trial-breaking)

---

## Product clarity (55/100)

**Strengths**
- BROKER_ONE_PAGER, TRIAL_ONE_PATH, DEMO_STORY aligned on core promise
- CUSTOMER_LANGUAGE_GUIDE maps engineer → broker terms
- Clear "what we don't promise" lists

**Gaps**
- UI opens Customer Entry; trial assumes Broker Workbench
- Add-Car-first pilot intro vs cancellation-first demo
- English "case", PG tags, API URL visible to broker
- BROKER_TRIAL_PLAYBOOK Day 1 requires Simulation Assistant — unavailable in product-only UI

---

## Trial readiness (78/100)

**Strengths**
- `trial_launch_check.sh` PASS (docs, guardrail, UI build, chen_kui pack)
- Guardrail: 13/13 scenarios + client A/B batteries
- TRIAL_OBSERVATION_LOG + FIX_NOW_QUEUE templates
- 6 canonical trial docs verified

**Gaps**
- Manual checklist still references SIM1–SIM3 by ID
- No automated "production URL live" probe in launch check
- Demo queue load 15–30s with no broker-facing progress

---

## Support readiness (65/100)

**Strengths**
- `GET /api/inbox/support/deployment-manifest` documented
- `summarize_support_posture.sh` for human summary
- Escalation L1–L4 in TRIAL_ONE_PATH
- Copy case snapshot workflow documented

**Gaps**
- Support = founder WeChat (no SLA, no hours)
- No broker-facing status page
- Chen Kui can't self-diagnose downtime
- Postgres backup not automated (FOUNDER_ONE_PATH rollback)

---

## Founder readiness (70/100)

**Strengths**
- Single path: FOUNDER_ONE_PATH → trial_launch_check
- 15-min orientation table exists
- Demo backup scripts (restore_8001, guardrail)

**Gaps**
- Must manually redirect broker to correct tab
- Must explain paste workflow vs WeChat sync again
- Product-only Simulation backup unavailable

---

## Operator readiness (58/100)

**Strengths**
- deploy_paid_pilot.sh + validate_pilot_deploy_env.py exist
- OPERATOR_SURFACE defines 10 scripts / 5 endpoints
- trial_readiness_check validates deploy entry

**Gaps (observed this run)**
- Readiness posture: `full_stack`, `Product-only: no` on dev machine
- `.env.cloudrun` present but **SKIP** — not production-validated
- No live `/readyz` probe (API not running during check)
- Production Vercel URL in BROKER_DEMO_FLOW — not verified live in this sprint

---

## Script results (2026-05-30)

```
trial_readiness_check.sh → PASS
trial_launch_check.sh    → PASS
Guardrail                → PASS (13/13 + client A/B)
UI build                 → PASS
Pilot .env.cloudrun      → SKIP (not production-like)
Local /readyz probe      → SKIP (API not running)
```

---

## Minimum bar to reach 75 (trial-ready without founder hovering)

1. Product-only UI hides engineer chrome (PG, API URL, debug tags)  
2. Broker tab default + playbook updated (no Simulation dependency)  
3. Production deploy validated: `validate_pilot_deploy_env.py` PASS + `/readyz` `intake_path_ready:true`  
4. One successful founder dry-run with observation log filled  

---

*End of trial readiness score*
