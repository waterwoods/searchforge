# P9 Broker Surface Plan — Customer Journey Definition

**Sprint:** P9 BROKER_SURFACE_COLLAPSE  
**Purpose:** Define the minimum visible surface if Chen Kui became a paying customer tomorrow.  
**Authority for runtime:** [`CURRENT_PRODUCT_SHAPE.md`](./CURRENT_PRODUCT_SHAPE.md)

---

## 1. Who is the customer?

**Primary:** California auto insurance brokers who serve Chinese-speaking clients (e.g., Chen Kui / 陈奎).

**Profile:** Small office or solo broker. Handles high message volume via WeChat, email, and carrier notices. Needs faster triage, clearer next steps, and client-ready replies — not another enterprise CRM.

---

## 2. What problem are they paying to solve?

**Inbox chaos → missed urgency → repetitive manual work.**

Brokers paste messy inbound messages (WeChat threads, carrier notices, screenshots described in text). They manually figure out urgency, what was collected, what's still needed, and what to tell the client. Urgent cases get buried; follow-ups get lost.

---

## 3. What is Unified Intake in one sentence?

**Unified Intake turns messy customer messages into one structured broker case — with urgency, next move, collected/missing info, and a draft reply you review before sending.**

---

## 4. What are the 3 biggest customer outcomes?

| # | Outcome | What broker sees |
|---|---------|------------------|
| 1 | **Nothing urgent gets buried** | Same-day action cases surface first; cancellation/payment risk is obvious |
| 2 | **Less repetitive explanation** | Collected / Still needed chips; draft reply ready to copy |
| 3 | **Follow-up continuity** | Reopen saved cases; paste new customer message; resume where you left off |

---

## 5. What should the customer NEVER need to know?

- Postgres, Qdrant, Cloud Run, Vercel, deployment manifests
- `platform_full`, `schema_epoch`, `token_scope_registry`, `replay_lineage`
- Simulation Assistant IDs (SIM1–SIM15), guardrail scripts, pytest
- JSON vs PG case storage, dual-write flags, intake_core_readiness
- SearchForge lab, `/demo` RAG page, AutoTuner, GPU workers
- Multi-tenant auth, Stripe, carrier API integration (not shipped)

---

## 6. What should the founder NEVER need to explain?

- Which of 40+ docs to read first
- Difference between `/ready` and `/readyz`
- Why Qdrant is red but triage still works
- Which deploy script is canonical (answer: `deploy_paid_pilot.sh`)
- Lab vs product mode (`RUN_DEMO_LAB=1` vs default)
- Sprint archaeology under `docs/archive/sprints/`

**Founder reads one path:** [`FOUNDER_ONE_PATH.md`](./FOUNDER_ONE_PATH.md)

---

## 7. What should support NEVER need to explain?

- Internal triage category names vs broker-facing Case focus labels
- Why `intake_path_ready:true` when vectors are down
- Deployment identity keys in support manifest (use [`CUSTOMER_LANGUAGE_GUIDE.md`](./CUSTOMER_LANGUAGE_GUIDE.md))
- Simulation scenario JSON structure
- PG migration epochs or org continuity columns

**Support reads:** [`runbooks/SUPPORT_TRUTH_MAP.md`](./runbooks/SUPPORT_TRUTH_MAP.md) + customer language guide.

---

## 8. What is the ideal 15-minute demo?

See [`DEMO_STORY.md`](./DEMO_STORY.md) → **THE_15_MINUTE_DEMO**.

| Min | Step |
|-----|------|
| 0–1 | Open workbench; one-sentence promise (messy message → structured case; you send) |
| 1–5 | Load founder demo queue → Cancellation risk (urgency, same-day action) |
| 5–9 | Missing document follow-up (verify receipt, waiting on client) |
| 9–13 | Add-car quote (Collected / Still needed chips, multi-turn) |
| 13–15 | Ask: "Which scenario felt most useful? What still feels risky?" |

**URL:** http://localhost:5173/workbench/unified-intake

---

## 9. What is the ideal 7-day trial?

See [`TRIAL_ONE_PATH.md`](./TRIAL_ONE_PATH.md).

| Day | Focus |
|-----|-------|
| **0** | Founder runs `trial_launch_check.sh`; broker gets one-pager + URL |
| **1** | Broker runs SIM1–SIM3; pastes one real message |
| **3** | Broker uses 2–3 real cases; founder collects friction notes |
| **7** | Value validation questions; fix-now queue; pilot decision |

---

## 10. What is the ideal launch checklist?

Founder runs **one command:** `bash scripts/trial_launch_check.sh`

Then follows [`FOUNDER_ONE_PATH.md`](./FOUNDER_ONE_PATH.md) § Trial.

Broker gets [`BROKER_ONE_PAGER.md`](./BROKER_ONE_PAGER.md) + [`BROKER_TRIAL_PLAYBOOK.md`](./BROKER_TRIAL_PLAYBOOK.md).

---

## TOP_30_BROKER_CONFUSIONS

| # | Confusion | Resolution |
|---|-----------|------------|
| 1 | "Is this connected to WeChat/email?" | No — paste messages manually for now |
| 2 | "Does it auto-send replies?" | No — you review and send |
| 3 | "Is this a CRM?" | No — lightweight case workbench only |
| 4 | "What is Unified Intake vs workbench?" | Same product — intake creates cases; workbench manages them |
| 5 | "What is Simulation Assistant?" | Practice mode with preset scenarios — optional for trial |
| 6 | "What is Load founder demo queue?" | Demo-safe sample cases — use Day 1 to learn |
| 7 | "What does Case focus mean?" | What the case is about: add car, missing doc, payment risk, etc. |
| 8 | "What is Your next move?" | One sentence: what your office should do next |
| 9 | "What are Collected chips?" | Info the system extracted from the conversation |
| 10 | "What are Still needed chips?" | Info you should ask or verify next |
| 11 | "Human confirmation recommended?" | AI collected something you should verify before trusting |
| 12 | "Customer Entry vs Broker Workbench?" | Customer-facing input vs your internal triage view |
| 13 | "Why two tabs?" | Optional customer front door + your workbench |
| 14 | "Does it read screenshots?" | Not yet — paste or describe the notice in text |
| 15 | "Does it connect to carriers?" | No carrier integration in v1 |
| 16 | "What languages work?" | Chinese and English inbound; drafts match client language |
| 17 | "Is `/demo` the product?" | No — that's optional Q&A lookup; product is workbench |
| 18 | "Why is backend warming slow?" | First request may be slow; retry or use demo queue |
| 19 | "What happens to my cases?" | Saved locally (demo) or in secure database (production) |
| 20 | "Can my assistant use it?" | Yes — same workflow; broker stays in control |
| 21 | "What scenarios are included?" | Cancellation, missing doc, add-car, premium review, claim intake |
| 22 | "What is SIM1?" | Internal label — broker sees scenario name, not SIM IDs |
| 23 | "Do I need to clean up the message?" | No — paste raw messy text |
| 24 | "What if the draft is wrong?" | Edit before copying; system is a starting point |
| 25 | "What is waiting on client?" | Case parked until customer responds |
| 26 | "What is Same-day action?" | Urgent — handle today |
| 27 | "Can I paste a follow-up message?" | Yes — Update with new customer message |
| 28 | "Is my data shared with other brokers?" | Single-broker pilot — your data only |
| 29 | "What am I paying for?" | Faster triage + structured cases + draft replies + follow-up memory |
| 30 | "What is NOT included yet?" | Inbox sync, OCR, full CRM, billing portal, multi-office |

---

## TOP_20_FOUNDER_CONFUSIONS

| # | Confusion | Resolution |
|---|-----------|------------|
| 1 | Which doc to read first? | `FOUNDER_ONE_PATH.md` |
| 2 | FOUNDER_LAUNCH_PATH vs FOUNDER_DEMO_SOP? | One path now — FOUNDER_ONE_PATH |
| 3 | Which port? | 8001 default (`run_demo_local.sh`) |
| 4 | `/ready` vs `/readyz`? | Use `/readyz`; check `intake_path_ready` |
| 5 | Qdrant required? | No for core intake triage |
| 6 | Which deploy script? | `deploy_paid_pilot.sh` only |
| 7 | platform_full vs product_only? | Paid pilot: always PRODUCT_ONLY=1 |
| 8 | JSON cases vs Postgres? | Prod: Postgres only; local demo may use JSON |
| 9 | RUN_DEMO_LAB=1 when? | R&D only — never for broker demo |
| 10 | demo_pre_checklist vs trial_launch_check? | Demo prep vs first trial launch |
| 11 | How many trial docs? | One: TRIAL_ONE_PATH + templates |
| 12 | CHEN_KUI_TRIAL_PACK vs trial specs? | Collapsed into BROKER_TRIAL_PLAYBOOK |
| 13 | Which demo URL? | `/workbench/unified-intake` not `/demo` |
| 14 | 503 embedding_warming? | `restore_8001_readiness.sh`; workbench may still work |
| 15 | How many scripts matter? | ~10 — see OPERATOR_SURFACE |
| 16 | What to archive? | See `docs/archive/p9_broker_surface/` |
| 17 | When to run guardrail? | Before demo and before trial |
| 18 | Support manifest keys? | CUSTOMER_LANGUAGE_GUIDE for broker-facing translation |
| 19 | Trial kickoff folder? | Optional depth — TRIAL_ONE_PATH is enough |
| 20 | Post-trial what? | FIX_NOW_QUEUE_TEMPLATE → results/trial_logs/ |

---

## TOP_20_TRIAL_CONFUSIONS

| # | Confusion | Resolution |
|---|-----------|------------|
| 1 | Trial length? | 7 days recommended; 1-week package |
| 2 | Trial vs pilot? | Trial = evaluate; pilot = paid month |
| 3 | How many scenarios? | Start with 3 (cancellation, missing doc, add-car) |
| 4 | Must broker use Simulation Assistant? | Recommended Day 1; real messages Day 1+ |
| 5 | Founder demo queue vs real cases? | Queue for learning; real messages for validation |
| 6 | Success criteria? | Broker can answer 4 value questions (see TRIAL_ONE_PATH) |
| 7 | Failure criteria? | Broker can't explain what product does |
| 8 | What to collect? | Friction, confusion, value signal per case |
| 9 | When to escalate to founder? | Trust-breaking bug or broker stuck >15 min |
| 10 | Offline mode during trial? | Use Simulation Assistant; note in observation log |
| 11 | Production URL vs local? | Either; production preferred for real trial |
| 12 | Who runs trial_launch_check? | Founder before Day 0 |
| 13 | Observation log required? | Yes — copy template |
| 14 | Post-trial fix queue? | FIX_NOW_QUEUE_TEMPLATE |
| 15 | Can broker invite assistant? | Yes — same one-pager |
| 16 | Billing during trial? | Free trial; manual payment if pilot continues |
| 17 | Data retention after trial? | Discuss with founder; prod uses Postgres |
| 18 | Extended scenarios (SIM4+)? | Optional after core 3 |
| 19 | Kickoff blueprint needed? | No — TRIAL_ONE_PATH sufficient |
| 20 | 12 trial spec docs? | Archived — TRIAL_ONE_PATH replaces |

---

## TOP_20_DEMO_CONFUSIONS

| # | Confusion | Resolution |
|---|-----------|------------|
| 1 | `/demo` vs workbench? | Workbench is the product demo |
| 2 | RAG 5 questions vs intake? | Legacy wedge — don't lead with it |
| 3 | Live vs Offline mode? | Live = real triage; Offline = preset RAG answers on `/demo` only |
| 4 | 15 min vs 5 min demo? | See DEMO_STORY variants |
| 5 | Which scenario first? | Always cancellation risk |
| 6 | Show Customer Entry? | Optional — strong for "customer front door" story |
| 7 | How many cases to show? | 3 minimum: cancel, missing doc, add-car |
| 8 | What not to promise? | WeChat sync, auto-send, OCR, CRM |
| 9 | demo_pre_checklist required? | Yes before every demo |
| 10 | guardrail required? | Yes before demo |
| 11 | BROKER_MEETING_PACKAGE vs DEMO_STORY? | DEMO_STORY is canonical |
| 12 | Chen Kui specific script? | Folded into DEMO_STORY + BROKER_DEMO_FLOW |
| 13 | Chinese or English demo? | Match broker preference; product supports both |
| 14 | Production demo URL? | https://ui-smoky-beta.vercel.app/workbench/unified-intake |
| 15 | Load founder demo queue when? | Start of demo after one-sentence promise |
| 16 | Simulation Assistant in demo? | Backup if live API slow |
| 17 | Feedback questions? | 3–5 from BROKER_DEMO_FLOW |
| 18 | Follow-up message template? | In BROKER_DEMO_FLOW § Post-demo |
| 19 | Multiple demo docs? | One story: DEMO_STORY |
| 20 | Value validation meeting pack? | Operator depth — broker sees DEMO_STORY only |

---

## P9 Deliverables

| Doc | Audience |
|-----|----------|
| [`BROKER_ONE_PAGER.md`](./BROKER_ONE_PAGER.md) | Broker — what it is, why pay, how to try |
| [`BROKER_DEMO_FLOW.md`](./BROKER_DEMO_FLOW.md) | Founder → broker demo steps |
| [`BROKER_TRIAL_PLAYBOOK.md`](./BROKER_TRIAL_PLAYBOOK.md) | Broker trial week |
| [`FOUNDER_ONE_PATH.md`](./FOUNDER_ONE_PATH.md) | Founder — one path |
| [`DEMO_STORY.md`](./DEMO_STORY.md) | Demo narrative + 15/5/60 sec variants |
| [`TRIAL_ONE_PATH.md`](./TRIAL_ONE_PATH.md) | Trial day-by-day |
| [`CUSTOMER_LANGUAGE_GUIDE.md`](./CUSTOMER_LANGUAGE_GUIDE.md) | Engineer → broker vocabulary |

**Archived overlap:** `docs/archive/p9_broker_surface/`

---

*End of P9 broker surface plan*
