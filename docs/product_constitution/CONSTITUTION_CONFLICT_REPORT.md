# Constitution Conflict Report — P14-A

**Date:** 2026-05-31  
**Method:** Cross-document evidence scan; conflicts ranked P0 (blocks trial/payment), P1 (strategic drift), P2 (cosmetic/historical).

---

## Conflict Summary

| Priority | Count | Theme |
|----------|-------|-------|
| **P0** | 6 | Blocks broker trial or payment without founder intervention |
| **P1** | 8 | Strategic direction split; requires constitution resolution |
| **P2** | 10 | Naming, counts, historical artifacts |

---

## P0 — Must Resolve Before Unsupervised Trial

### C-P0-1: Add-Car-first vs Cancellation-first wedge

| Side A | Side B |
|--------|--------|
| `UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` §2: "Add-Car-first intake and handoff assistant" as flagship commercial wedge | `P10/P11`, `BROKER_ONE_PAGER`, `DEMO_STORY`, `TRIAL_ONE_PATH`: cancellation → missing doc → add-car demo triangle; "Chen Kui pays for minutes on urgent messages" |

**Evidence:**
- Master outline §2: "The first commercial / monetizable wedge… **Add-Car / add vehicle quote intake**"
- P11 final audit: "Chen Kui pays for **minutes saved on urgent messages**, not Add-Car portal"
- P10 friction audit #8: "Add-Car-first banner vs cancellation demo story"

**Impact:** Broker sees Add-Car portal; docs sell cancellation triage. Payment conversation fails on Day 7.

**Resolution direction:** Constitution must declare **paid pilot wedge = broker paste triage (cancellation/missing doc first)**; Add-Car = secondary scenario + future customer portal, not primary GTM story.

---

### C-P0-2: Customer Entry (客户报送) vs Broker Workbench (办公室工作台) default

| Side A | Side B |
|--------|--------|
| UI default: Customer Entry tab with Add-Car-first intro | All trial/demo docs: broker opens **办公室工作台** first |

**Evidence:**
- P10 CURRENT_TRIAL_MODEL §3: "Page opens on **客户报送** — not cancellation triage story"
- P11 TRIAL_REALITY_AUDIT: "Day 1 unsupervised score: 28/100"
- DEMO_AUDIT: "Founder demo SOP adds step 0: Click 办公室工作台 before speaking"

**Impact:** #1 trial killer per P10/P11/TOP_50_REASONS.

**Resolution direction:** Constitution rule: **trial URL defaults to broker workbench tab**; Customer Entry is Phase 2 customer-facing surface, not broker GTM.

---

### C-P0-3: RAG Demo Product vs Unified Intake Workbench

| Side A | Side B |
|--------|--------|
| `insurance_paid_pilot_goal.md`, `insurance_broker_pilot_rules.md`: 5 validated questions, gov+insurer citations, `/demo` RAG, `demo_quick_validate.sh` | `CURRENT_PRODUCT_SHAPE`, P11, BROKER_ONE_PAGER: Unified Intake workbench, paste triage, guardrail_inbox_triage |

**Evidence:**
- Paid pilot goal §4: "`auto_insurance_demo_core` ≥20 docs; 5 sample questions"
- Business rules R1–R5: retrieval, citations, offline fallback
- CURRENT_PRODUCT_SHAPE: "Not the product: SearchForge R&D endpoints"
- P10 CURRENT_TRIAL_MODEL §6: "Mis-set expectations from old RAG demo"

**Impact:** Stale goals mislead agents/engineers; broker confusion if shown `/demo`.

**Resolution direction:** Archive or rewrite `insurance_paid_pilot_goal.md` and `insurance_broker_pilot_rules.md` to reference workbench constitution. Explicit anti-goal: **RAG `/demo` is not the paid product**.

---

### C-P0-4: Simulation Assistant required vs hidden in product-only UI

| Side A | Side B |
|--------|--------|
| `BROKER_TRIAL_PLAYBOOK`, `P9_BROKER_SURFACE_PLAN` §9 Day 1: run SIM1–SIM3 via Simulation Assistant | Product-only UI hides Simulation tab (`VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`) |

**Evidence:**
- P10 discovery #3: "Simulation Assistant required in playbook but hidden"
- TRIAL_ONE_PATH Day 1 still references Simulation Assistant scenarios
- P11: "Day 1 playbook fails unsupervised"

**Impact:** Broker follows playbook → feature missing → churn Day 1.

**Resolution direction:** Constitution trial model: **demo queue + 3 named scenarios inline in workbench**; remove Simulation dependency from trial SSOT.

---

### C-P0-5: Pricing absent vs payment anchor documented internally

| Side A | Side B |
|--------|--------|
| `BROKER_ONE_PAGER`: no price; "7 days free → optional paid pilot" | P10/P11/PAYMENT_READINESS: **$49–99/mo** manual invoice; $99 anchor |

**Evidence:**
- P11 blocker #10: "Pricing not on one-pager"
- P11 FOUNDER_REFLECTION #9: "Stop hiding pricing"

**Impact:** Broker asks "then what?" on Day 3; payment conversation unprepared.

**Resolution direction:** Constitution commercial model must publish **$49 starter / $99 standard pilot** on broker-facing SSOT.

---

### C-P0-6: Script PASS ≠ broker-ready

| Side A | Side B |
|--------|--------|
| `trial_launch_check.sh` PASS | P10/P11: broker front door not ready unsupervised |

**Evidence:**
- P10 FINAL_VERDICT: "Conditional go for founder-supervised trial"
- P11: "Day 1 unsupervised: 28/100"

**Impact:** False confidence in launch readiness.

**Resolution direction:** Constitution acceptance: **two gates** — operator script PASS + broker UX checklist PASS.

---

## P1 — Strategic Drift (Resolve in Constitution)

### C-P1-1: Platform vs SaaS

| Platform framing | SaaS framing |
|------------------|--------------|
| Master outline: "hot-swappable common base + client packs", "Trusted Assistant Platform" (archived) | SIMPLIFICATION: "ONE PRODUCT · ONE DEPLOY · ONE DATABASE" |
| SIMPLIFICATION §1: "Stop pretending… Trusted Assistant Platform as separate SKU" |

**Resolution:** Constitution anti-goal: no platform SKU before first paid broker.

---

### C-P1-2: Customer Identity — in scope vs out of scope

| In scope | Out of scope |
|----------|--------------|
| Master outline §2A: light identity, session, service record, formal submit | UNIFIED_INTAKE_MVP_MASTER_GOAL §4: "Customer identification: No case/customer linking in v1" |

**Resolution:** Constitution: **session/case continuity yes; CRM identity no** for v1 paid pilot.

---

### C-P1-3: Demo Product vs Paid Pilot deployment

| Demo/local | Paid pilot |
|------------|------------|
| JSON cases, platform_full, DEMO_MODE | Postgres-only, PRODUCT_ONLY=1, API keys |

**Evidence:** CURRENT_PRODUCT_SHAPE table — well documented, not conflicting, but operators confuse modes.

**Resolution:** Constitution deployment section mirrors CURRENT_PRODUCT_SHAPE; add founder rule: **never run broker trial on localhost without persistence disclaimer**.

---

### C-P1-4: Broker User vs Customer User

| Broker path | Customer path |
|-------------|---------------|
| Paste in workbench — primary GTM | Customer Entry tab — Add-Car structured portal |

**Evidence:** P9 confusion #11–13; friction audit #7.

**Resolution:** Constitution: **broker is payer and primary user v1**; customer portal is supporting surface, not trial entry.

---

### C-P1-5: Scenario count inconsistency

| Source | Count |
|--------|-------|
| BROKER_ONE_PAGER | 5 core scenarios |
| STANDARD_SCENARIO_PACKAGE | 7 scenarios |
| Demo queue | 13 cases |
| TRIAL_ONE_PATH | 3-scenario triangle |

**Resolution:** Constitution capability map: **3 trial scenarios, 5 broker-facing, 7 sellable package** — explicit tiers.

---

### C-P1-6: Trial length wording

| Source | Wording |
|--------|---------|
| BROKER_ONE_PAGER, TRIAL_ONE_PATH | 7-day trial |
| STANDARD_SCENARIO_PACKAGE one-liner | "试用一个月" (one month) |

**Resolution:** Constitution: **7-day evaluation trial → optional 30-day paid pilot month**.

---

### C-P1-7: Assistant as user vs broker-only

| View A | View B |
|--------|--------|
| P11: "Assistant adoption doubles office value" | MVP goals: single broker pilot, no multi-user |

**Resolution:** Constitution: assistant may use same login/workflow; **no separate seat billing v1**.

---

### C-P1-8: OCR / screenshot reading

| Implied | Stated |
|---------|--------|
| MVP goal input: "OCR-extracted screenshot text" (broker pastes OCR output) | CURRENT_PRODUCT_TRUTH: "don't upload images expecting OCR" |

**Resolution:** Constitution: **paste text only; no in-product OCR v1**.

---

## P2 — Naming, Historical, Cosmetic

| ID | Conflict | Resolution |
|----|----------|------------|
| C-P2-1 | "Load founder demo queue" vs UI "加载演示队列" | Doc label sync |
| C-P2-2 | SIM1–SIM3 vs scenario names in trial_launch_check output | Remove SIM IDs from broker path |
| C-P2-3 | Repo name SearchForge vs Unified Intake | Accept; not customer-facing |
| C-P2-4 | `/ready` vs `/readyz` | OPERATOR docs already resolve |
| C-P2-5 | 13 vs 10 demo queue cases | Say "sample cases" not exact count |
| C-P2-6 | FOUNDER_LAUNCH_PATH archived vs FOUNDER_ONE_PATH | Already resolved P9 |
| C-P2-7 | Multiple 30-day execution plans (P10 + P11) | Merge into one post-constitution plan |
| C-P2-8 | BROKER_INBOX_TRIAGE vs Unified Intake naming | Unified Intake is product name |
| C-P2-9 | Engineer field names vs Case focus / Your next move | CUSTOMER_LANGUAGE_GUIDE |
| C-P2-10 | P12/P13 referenced in mission but don't exist | Note absence; P10/P11 are latest |

---

## Conflict Resolution Matrix

| Conflict | Winner (evidence-weighted) | Constitution action |
|----------|---------------------------|---------------------|
| Wedge story | Cancellation-first triage (P10/P11 + trial docs) | Demote Add-Car-first in GTM |
| Default tab | Broker Workbench | UI + trial URL rule |
| Product surface | Workbench intake (CURRENT_PRODUCT_SHAPE) | Archive RAG goal docs |
| Identity v1 | Light session/case only | Explicit in capability map |
| Pricing | $49/$99 published | Update BROKER_ONE_PAGER |
| Simulation | Inline scenarios in workbench | Update TRIAL_ONE_PATH |

---

*End of constitution conflict report*
