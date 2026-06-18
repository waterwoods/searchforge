# P16-Z18 Seven Capacities V2

**Date:** 2026-06-03  
**Sprint:** P16-Z18 Product Constitution Refresh  
**Replaces:** Broker-centric Cap 1–7 (P16-Z9 `P16Z9_CAPACITY_REVIEW.md`)  
**Method:** Evidence from P16-Z3–Z17 · Z17 scorecard · P16-Y · Role D · live case proof

Scoring: 0 = missing · 100 = production-ready for first paying broker (supervised pilot)

---

## Capacity overview

| # | Capacity | Current | Target | Gap |
|---|----------|---------|--------|-----|
| 1 | Customer Intake | **75** | **92** | Post-submit rehydrate |
| 2 | AI Draft Case Builder | **86** | **90** | Generic lanes + edge lanes on deploy |
| 3 | Case Memory | **78** | **88** | Customer-visible merge proof |
| 4 | Timeline | **78** | **90** | Customer thread after return |
| 5 | Broker Workbench | **88** | **92** | Deploy parity + office value on prod |
| 6 | Office Coordination | **79** | **85** | waiting_on SOP + deploy |
| 7 | Reality Validation | **72** | **90** | Deploy + E2E + Chen Kui proof |

**Weighted pilot path (Cap 1+2+4+5):** **82 now → 91 target**

---

## Capacity 1 — Customer Intake

**Purpose:** Customer sends a message (text, multi-turn) and enters the office workflow — pre-submit session restore and post-submit case discovery. **Status visibility:** customer can answer **Did I submit?** · **What is missing?** · **What is the contact state?** without calling the office.

| | |
|---|---|
| **Current Score** | **75 / 100** |
| **Target Score** | **92 / 100** |

**Evidence:**
- ✅ `CustomerEntryTab` — multi-turn Add-Car triage, formal submit (`P16Z17`, score A=82)
- ✅ Pre-submit return: `session_id` + `GET /api/inbox/session/{id}` (2 turns proven)
- ✅ `MyRequestsTab` lists submitted cases with progress fields
- ❌ Post-submit refresh: Customer Entry empty; `clearSessionId()` on submit (`P16Z17_RETURN_LATER`)
- ❌ My Requests → Customer Entry does not pass `case_id` (`P16Z17_TRUE_MVP_GAPS` Blocker 2)
- ❌ Resume hint excludes `submitted` lifecycle (`P16Z17` Blocker 3)
- ⚠️ Session store needs Postgres for prod persistence (`P16Z17` Blocker 4)

**Target = 92 when:** Hydrate active `case_id`, My Requests handoff, resume submitted cases, 3-day browser walkthrough pass.

---

## Capacity 2 — AI Draft Case Builder

**Purpose:** Convert messy customer input into a structured draft case — category, collected fields, still needed, broker next step — before human confirmation.

| | |
|---|---|
| **Current Score** | **86 / 100** |
| **Target Score** | **90 / 100** |

**Evidence:**
- ✅ P16-Y battery **88.6 avg** single-turn (`P16Z3`, `P16Z10B`)
- ✅ `triage.py` + `case_draft_engine.py` — 48 modules, no microservice needed (`P16Z3`)
- ✅ Add-Car flagship: formal submit gate, VIN structural truth (`P16Z17` live case)
- ✅ Z6/Y44/Y45 correction merge shipped in repo; premium lane guard (`P16Z6`, `P16Z10A`)
- ✅ Z10B: claims retention 36%→71%, waiting_on suggest 9/9 (`P16Z10B`)
- ⚠️ Preview deploy stale — payment/remove/claim misroute on Cloud Run (`P16Z12`, `P16Z11`)
- ⚠️ Generic non–Add-Car customer lanes weaker than Add-Car (`P16Z16`)

**Target = 90 when:** Deployed backend matches local batteries; Add-Car + cancel/payment/claim acceptance cases pass on cold URL.

---

## Capacity 3 — Case Memory

**Purpose:** Same case accumulates facts across turns and days — merged fields, conversation summary, prior intent preserved on correction.

| | |
|---|---|
| **Current Score** | **78 / 100** |
| **Target Score** | **88 / 100** |

**Evidence:**
- ✅ `case_store.py` — persistence **91/100** (`P16Z17` score F)
- ✅ `append_follow_up_message()` + `triage_for_append()` production-grade (`P16Z5`, `P16Z4`)
- ✅ `_merge_persisted_collected`, prior-turn prepend on correction (`P16Z10A`, `P16Z6`)
- ✅ 3-day append: merged VIN + driver, `formal_submitted_at` immutable (`P16Z16_REAL_FLOW`)
- ⚠️ Broker memory UX was ~41 before Z6 thread; engine strong, surface lagging (`P16Z5`)
- ❌ Customer does not see merge proof after return (`P16Z17` timeline test)

**Target = 88 when:** Customer append after return shows updated fields; Role D reread ≥80 sustained on deployed path.

---

## Capacity 4 — Timeline

**Purpose:** Traceable record of what the customer said, what the office did, and when — for broker trust and **customer status visibility** (submit state, missing fields, contact state).

| | |
|---|---|
| **Current Score** | **78 / 100** |
| **Target Score** | **90 / 100** |

**Evidence:**
- ✅ `case_messages[]` seq 1–11 + `case_activity[]` × 3 on live case (`P16Z17_TIMELINE_TEST`)
- ✅ Broker: thread UI after Z6 (`P16Z6_TIMELINE_ACTIVATION`)
- ✅ Multi-day continuity data layer **74/100** (`P16Z17` score G)
- ❌ Customer thread UI lost on refresh post-submit
- ⚠️ Customer sees progress fields in My Requests, not full message timeline

**Target = 90 when:** Broker timeline on prod; customer sees at least progress + append thread after rehydrate; 3-day story in browser without API-only proof.

---

## Capacity 5 — Broker Workbench

**Purpose:** Broker confirms draft case, copies client reply, appends follow-ups, sees updates without reopening WeChat.

| | |
|---|---|
| **Current Score** | **88 / 100** |
| **Target Score** | **92 / 100** |

**Evidence:**
- ✅ `BrokerWorkbenchTab` — same `case_id`, summary, fields, thread, next step (`P16Z17` score E=88)
- ✅ Append updates visible without reopening customer chat (`P16Z17_BROKER_VISIBILITY`)
- ✅ Z11 office value surface: avg 48→79 local (`P16Z11`)
- ✅ Role D reread **82.6**, need WeChat **0/10** (`P16Z10B`)
- ⚠️ Z12: preview deploy blocked — Chen Kui cannot test unsupervised on prod URL
- ⚠️ Activity panel still collapsed in `product_only` trial mode

**Target = 92 when:** Deployed parity + founder 3× two-turn observation log + Chen Kui supervised demo on cold URL.

---

## Capacity 6 — Office Coordination

**Purpose:** Office knows what's missing, who is waiting on whom, and the next action — in Chinese, scannable in 5 seconds. **`waiting_on` maps to customer-visible contact state** (broker expectation language allowed; hard system SLA promises forbidden).

| | |
|---|---|
| **Current Score** | **79 / 100** |
| **Target Score** | **85 / 100** |

**Evidence:**
- ✅ `broker_next_step`, `still_needed_fields`, `waiting_on` model in `case_store`
- ✅ Z10B `_suggest_waiting_on()` — 0/9→9/9 auto-detect on Role D phrases
- ✅ Z11 `_apply_office_value_surface()` — payment/remove/claim headlines local pass
- ✅ `office_case_title`, missing checklist, waiting pill in glance
- ⚠️ `waiting_on` PATCH manual — suggest only, not auto-set (`P16Z10B`)
- ❌ Deploy gap blocks Chen Kui seeing Z11 surface on preview

**Target = 85 when:** Office value surface live on prod; broker SOP for confirming `waiting_on` after copy.

---

## Capacity 7 — Reality Validation

**Purpose:** Prove the product works on deployed URL with batteries, guardrails, founder walkthrough, and broker trial — no fake success.

| | |
|---|---|
| **Current Score** | **72 / 100** |
| **Target Score** | **90 / 100** |

**Evidence:**
- ✅ `guardrail_inbox_triage.sh` — exists, PASS locally
- ✅ P16-Y ≥88, Role D reread 82.6, append sims 5/5 (`P16Z6`, `P16Z10B`)
- ✅ `trial_launch_check.sh`, `run_p16y_case_battery.py`, `run_role_d_memory_battery.py`
- ❌ Z12 GO/NO-GO **FAIL** — API keys, CORS, stale preview backend
- ❌ Chen Kui unsupervised 3× two-turn on prod **not run** (`P16Z6`)
- ❌ Customer Builder 3-day browser E2E **not run** (`P16Z17`)

**Target = 90 when:** Deploy unblocked · Z12 acceptance cases pass · 3-day Tesla in browser · observation log ≥3 real cases · invoice sent.

---

## Tier priority (next 30 days)

| Tier | Capacities | Rule |
|------|------------|------|
| **P0** | 1, 4, 7 | Close customer return loop + prove in browser + deploy |
| **P1** | 2, 5, 6 | Deploy engine + office surface on prod URL |
| **P2** | 3 | Tune only if batteries regress |

**Do not open new capacity work** until Cap 1 ≥90 and Cap 7 deploy gate passes.

---

## Customer First interpretation (P16-CUSTOMER-FIRST-CONSTITUTION-P0)

**Constitution:** `P16_CUSTOMER_FIRST_CONSTITUTION.md`  
**North star umbrella:** **Customer Must Always Know The Status** — the customer answers submit state, missing fields, and contact state **without calling the office**.

For each capacity: how it supports Customer First, Phone Is The Return Key, and One Customer = One Active Case.

### 1 — Customer Intake

| Lens | Support |
|------|---------|
| **Customer Must Always Know The Status** | Customer can answer without calling the office: **Did I submit?** (submit state on return) · **What is missing?** (`still_needed_fields`) · **What is the contact state?** (customer-visible waiting-on / next-step copy). |
| **Customer First** | Anonymous entry; status copy and progress fields surface all three dimensions — not only missing fields. |
| **Phone Is The Return Key** | Phase 2 target: phone lookup rehydrates active case — replaces session-only return (`P16Z17` blockers). |
| **One Active Case** | Phase 1–2: collect phone early; Phase 2: lookup returns single active add-car case, not a picker. |

### 2 — AI Draft Case Builder

| Lens | Support |
|------|---------|
| **Customer First** | Turns messy messages into structured draft with explicit `still_needed_fields` — progress = missing fields. |
| **Phone Is The Return Key** | Extracts phone into `customer_phone`; Phase 3 gates formal submit on valid phone. |
| **One Active Case** | Append path merges into same `case_id` when phone + lane match; new vehicle while active → broker split (Rule 7). |

### 3 — Case Memory

| Lens | Support |
|------|---------|
| **Customer First** | Same case accumulates facts — customer sees merge proof after return (Cap 1+4 gap). |
| **Phone Is The Return Key** | Phone keys durable record; session is ephemeral until phone binds case. |
| **One Active Case** | Memory attaches to one active `case_id` per phone; closed cases read-only. |

### 4 — Timeline Continuity

| Lens | Support |
|------|---------|
| **Customer Must Always Know The Status** | Timeline and status surfaces support **status visibility**: submit milestones, field collection history, and contact-state changes — so return visits answer all three north-star questions without a phone call. |
| **Customer First** | Customer sees what happened, what is missing, and current contact state — not only a message log. |
| **Phone Is The Return Key** | Return visit loads same timeline via phone-linked case, not new session thread. |
| **One Active Case** | Timeline is continuous within active case; fork only on broker close + new open. |

### 5 — Broker Workbench

| Lens | Support |
|------|---------|
| **Customer First** | Broker confirms draft — customer path feeds workbench; broker controls final action. |
| **Phone Is The Return Key** | Workbench shows claimed phone; broker confirms identity before high-trust steps. |
| **One Active Case** | Broker closes/reopens (Rule 5); prevents duplicate active queue entries for same phone. |

### 6 — Office Coordination

| Lens | Support |
|------|---------|
| **Customer Must Always Know The Status** | Internal `waiting_on` maps to **customer-visible contact state** (e.g. waiting on customer / office / broker) — same coordination truth, customer-safe wording. Broker expectation language allowed; hard system SLA promises forbidden. |
| **Customer First** | Office answers “what’s missing?” in 10 seconds via glance + checklist; customer surface mirrors contact state derived from office coordination. |
| **Phone Is The Return Key** | Every formal submit includes phone — office can callback without broker relay. |
| **One Active Case** | One desk row per active add-car matter per phone — no duplicate handoffs. |

### 7 — Reality Validation

| Lens | Support |
|------|---------|
| **Customer First** | Browser E2E: customer submit → return via phone → see missing fields (Phase 2–3 proof). |
| **Phone Is The Return Key** | Batteries must include phone lookup + rehydrate, not only `session_id` restore. |
| **One Active Case** | Stress tests: second “start over” with same phone resumes or blocks per Rule 7 — no silent duplicate. |

---

*End of P16-Z18 Phase 3 — Seven Capacities V2*
