# P16-Z18 Founder Summary

**Date:** 2026-06-03  
**Sprint:** P16-Z18 Product Constitution Refresh  
**Constraint:** Reality only. No ambiguity. No future fantasy.

---

## 1. What is the product?

**Customer First Case Builder** for a California auto insurance office.

A customer sends a messy message → AI turns it into a **draft case** → the broker **confirms** it → the same case continues across days with a **timeline** until the request is closed.

It lives today as **`CustomerEntryTab`** (客户报送) + **`MyRequestsTab`** + **`BrokerWorkbenchTab`** inside Unified Intake — not a future build.

**Not:** CRM · chatbot · insurance software platform · SearchForge lab.

---

## 2. What is the North Star?

**NEW (Z18):**

> Turn a customer's messy message into a draft case the office can confirm — same case across days, clear next action, traceable timeline — until the request is closed and the office gets paid.

**One sentence:**

> Messy customer message → AI draft case → broker confirms → same case tomorrow → get paid.

**OLD (Z2–Z9, superseded as primary framing):**

> Turn messy client messages into a time-bound office obligation with a clear next action and a traceable close — in one paste, under one minute.

Broker paste remains a **valid wedge** for Chen Kui Day 0. Customer First is the **product definition**.

---

## 3. What are the Seven Capacities?

| # | Capacity | Current → Target |
|---|----------|------------------|
| 1 | **Customer Intake** | 75 → 92 |
| 2 | **AI Draft Case Builder** | 86 → 90 |
| 3 | **Case Memory** | 78 → 88 |
| 4 | **Timeline** | 78 → 90 |
| 5 | **Broker Workbench** | 88 → 92 |
| 6 | **Office Coordination** | 79 → 85 |
| 7 | **Reality Validation** | 72 → 90 |

**P0 for payment:** Cap 1 (return-later wiring) + Cap 7 (deploy + proof).

Full detail: `P16Z18_CAPACITY_MODEL.md`.

---

## 4. What is the MVP?

**IN:**

```
Customer Message → Draft Case → Broker Review → Return Later → Timeline
```

Concrete: `CustomerEntryTab` · formal submit · `case_id` · My Requests · append · broker workbench · validation batteries · manual invoice · Chen Kui single-office supervised pilot.

**OUT:**

CRM · Stripe · P17 · Voice Agent · GraphRAG · Platform Rebuild · new Customer Builder · new case/timeline/memory services · WeChat bot · multi-tenant auth.

Full lock: `P16Z18_MVP_SCOPE.md`.

---

## 5. What is AI responsible for?

**AI:**
1. Convert messy customer input into **draft case**
2. **Merge** new information into same case (append)
3. **Suggest** next action (broker_next_step, gaps, waiting_on suggest)

**Human:**
1. **Confirm**
2. **Correct**
3. **Execute** (carrier calls, WeChat send, close, invoice)

Full boundary: `P16Z18_AI_BOUNDARY.md`.

---

## 6. What should never be built?

Top never-build list:

1. New Customer Builder  
2. New Case Service  
3. New Timeline Service  
4. New Memory Service  
5. Case Intelligence microservice  
6. Platform rewrite / P17  
7. CRM  
8. Stripe (until 3+ offices)  
9. GraphRAG  
10. Voice agent  
11. Customer portal from scratch  
12. WaitingOnEngine / PaymentMemoryService / ClaimsIntakeService  

**Rule:** Wire `triage.py` + `case_store.py` + existing tabs.

Full list: `P16Z18_NEVER_BUILD.md`.

---

## 7. What should be built next?

**Nothing new. Finish wiring.**

| # | Task | Days |
|---|------|------|
| 1 | Hydrate `case_id` into Customer Entry after return | 1.0 |
| 2 | My Requests → pass `case_id` on continue | 0.5 |
| 3 | Resume hint for submitted cases | 0.5 |
| 4 | Session DB + demo env verification | 0.5 |
| 5 | 3-day Tesla browser walkthrough | 0.5 |
| 6 | Deploy backend (Z12 blockers: secrets, CORS) | 1–2 |
| 7 | Founder 3× observation log | 1 day |
| 8 | Chen Kui supervised demo | 0.5 day |

**Total engineering to 90+:** 3.0–3.5 days wiring + deploy ops.

Plan: `P16Z18_30_DAY_PLAN.md`.

---

## 8. How close are we to first payment?

**Close on code. Not close on proof.**

| Dimension | Status |
|-----------|--------|
| Engine (triage, case store, append) | **Ready** — P16-Y 88.6, Role D 82.6 |
| Customer Builder | **~76%** — return-later wiring missing |
| Broker workbench | **~88%** — works on same case_id |
| Deployed prod path | **Blocked** — Z12 FAIL (API keys, CORS, stale preview) |
| Chen Kui unsupervised trial | **Not run** |
| Invoice | **Not sent** |

**Honest estimate:** **2–4 weeks** to first payment if wiring + deploy + supervised Chen Kui happen sequentially with no scope creep.

**Not 6 months.** **Not 2 days.** **~15–20 working days** at current scope.

---

## 9. What is the fastest path to first payment?

```
Day 1–4:   Wire case_id hydrate + My Requests handoff (76 → 90)
Day 5–7:   Deploy + trial_launch_check PASS on cold URL
Day 8–10:  Andy 3-day customer walkthrough + observation log
Day 11–12: Chen Kui supervised 15-min demo
Day 13:    Invoice $49–99 sent
Day 14–20: Chen Kui one real case · payment received · testimonial
```

**Fastest blockers to remove (in order):**
1. Customer return UX (3–4 engineer-days) — **product proof**
2. Cloud Run deploy + CORS (founder + 1–2 dev days) — **access proof**
3. Founder observation log ritual (hours) — **commercial proof**

**Do not parallelize:** platform features, Stripe, second office, CRM.

---

## 10. What should Andy do for the next 3 working days?

### Day 1 — Unblock deploy

- [ ] Add `UNIFIED_INTAKE_INTAKE_API_KEY` + `UNIFIED_INTAKE_SUPPORT_API_KEY` to `.env.cloudrun`
- [ ] Run `bash scripts/deploy_paid_pilot.sh`
- [ ] Add Preview `ui-*.vercel.app` to `ALLOWED_ORIGINS`; redeploy backend
- [ ] Confirm FP-004 SSO off on preview
- [ ] Run `bash scripts/trial_launch_check.sh` — record PASS/FAIL honestly

### Day 2 — Wire review + founder test (local)

- [ ] Engineer ships or PRs: `case_id` hydrate + My Requests handoff (Blockers 1–3 from Z17)
- [ ] Andy runs 3-day Tesla walkthrough **in browser** on `:8001` — log PASS/FAIL per step
- [ ] Run P16-Y + Role D batteries — confirm ≥88 / ≥80
- [ ] Write observation log row 1 (real or simulated with timestamps)

### Day 3 — Chen Kui prep (supervised only)

- [ ] Cold URL works without Andy login
- [ ] Prepare 5-min SOP: customer link **or** broker paste — same case story
- [ ] Schedule supervised demo with Chen Kui (do **not** send unsupervised link yet)
- [ ] Draft invoice ($49–99 pilot) — IDs ready, do not send until demo PASS
- [ ] If walkthrough FAIL: fix wiring only — **no new features**

---

## Founder decision (no ambiguity)

# Customer Builder already exists at ~76%. Wire return-later. Deploy. Prove in browser. Chen Kui supervised. Invoice. Do not rebuild.

---

## P16-Z18 deliverables index

| Phase | Document |
|-------|----------|
| 1 | `P16Z18_NORTH_STAR.md` |
| 2 | `P16Z18_PRODUCT_SOUL.md` |
| 3 | `P16Z18_CAPACITY_MODEL.md` |
| 4 | `P16Z18_MVP_SCOPE.md` |
| 5 | `P16Z18_AI_BOUNDARY.md` |
| 6 | `P16Z18_CUSTOMER_FIRST_ARCHITECTURE.md` |
| 7 | `P16Z18_REUSE_ASSETS.md` |
| 8 | `P16Z18_NEVER_BUILD.md` |
| 9 | `P16Z18_30_DAY_PLAN.md` |
| 10 | `P16Z18_FOUNDER_SUMMARY.md` (this file) |

**Supersedes for daily decisions:** P16-Z25 north star/soul (broker-primary framing), P16-Z9 capacity names (broker-centric Cap 1–7), greenfield Customer Builder docs.

**Still authoritative for engine detail:** `CASE_INTELLIGENCE_MASTER_OUTLINE.md`, `P16Z9_DEVELOPMENT_OS.md`, `P16Z9_VALIDATION_OS.md`, `P16Z17_*` live proof.

---

*End of P16-Z18 Product Constitution Refresh*
