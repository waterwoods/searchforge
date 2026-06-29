# P16 Future Vision — Loop-Based Evolution

**Date:** 2026-06-28 (§8 Long-term Product Philosophy added)  
**Type:** Future Vision — NOT a Decision Freeze, NOT an ADR, NOT a commitment  
**Authority:** This document has no authority. All scope and architecture decisions remain in `docs/p16/P16_DECISION_FREEZE_V1.md` and the ADR index.

---

## 1. Purpose

P16 V1 is intentionally small.

The current goal is:

```
Customer Request
→ Readiness
→ Broker Ready Packet
```

That is where P16 ends today. It does not quote. It does not update policies. It does not follow up automatically. This is deliberate.

**Insurance Case IQ** is the product name for the long-term direction: a case operator that helps broker offices move insurance work toward completion — starting with add-car intake and the **Trusted Packet** as today's deliverable.

Future ideas belong in this document — not in sprint scope, not in the backlog, and not in the code.

If an idea is compelling, the path is: pilot data first, then ADR, then build.

---

## 2. Two Loops

### Loop 1 — Development Loop

```
Code
→ QA
→ Fix
→ Deploy
→ Learn
→ Repeat
```

**Purpose:** Improve the product.

**State: ACTIVE TODAY**

This is the loop running now. Each sprint produces a tighter, more trustworthy product. The Development Loop is how Add Vehicle became live, how the Primary Driver fix shipped, and how Replace Vehicle V1 Safe will follow.

---

### Loop 2 — Business Loop

```
Customer Request
→ Readiness Check
→ Missing Information
→ Customer Update
→ Re-evaluate
→ Broker Ready
```

**Purpose:** Move cases toward broker-ready outcomes — with the broker as the final gate.

**State: FUTURE VISION ONLY**

This loop does not exist today. In V1, the customer submits once. If information is missing, the broker follows up manually. The Business Loop imagines a system that detects gaps, prompts the customer, re-checks readiness, and iterates — accumulating evidence in **Case Memory** until the **Trusted Packet** reaches a broker-ready state. The broker reviews and decides before any office action; the loop does not bypass broker judgment.

---

## 3. Why the Business Loop Matters (Hypothesis)

The long-term value of P16 may not be document extraction alone.

It may be **Continuous Readiness**:

```
Detect missing information
→ Request missing information
→ Validate response
→ Re-check readiness
→ Repeat until broker ready
```

Today, if the VIN is missing from a customer upload, the broker asks manually via WeChat. The customer replies. The broker re-reads the thread. The broker updates the case. That is the loop P16 currently interrupts at the intake step — but not at the follow-up step.

If the Business Loop is real, Insurance Case IQ could close that gap: detect the missing VIN, prompt the customer, re-run extraction on the new upload, update **Case Memory**, and surface a refreshed **Trusted Packet** for broker review — broker-in-the-loop at every gate that matters.

**This is a hypothesis. It is not validated today.**

It may turn out that brokers prefer to handle follow-ups personally. It may turn out that most cases are READY on the first submission. It may turn out that the cost of automating follow-up is not worth the time savings. **Reality Validation** — pilot data, not speculation — will answer these questions.

---

## 4. Validation Gate

The Business Loop cannot be reconsidered until all of the following are met:

- **10+ real pilot cases** completed (CK-001 through CK-010)
- **Time savings data** collected (average minutes saved per case)
- **Broker feedback** collected from Chen Kui and Wu Xiaojie
- **First paid validation** — at least one $49 invoice paid

Until all four gates are passed:

| What | Status |
|------|--------|
| AI Case Manager | Do not build |
| Workflow engine (Temporal, Camunda, etc.) | Do not build |
| Timeline engine | Do not build (see ADR-002) |
| Autonomous follow-up system | Do not build |
| Carrier API | Do not build (see ADR-003) |

The validation gate is not a timeline. There is no target date. The gate opens when the data exists — not before.

**Promotion discipline (unchanged):**

```
10 cases
→ paid validation
→ promotion (ADR → Decision Freeze → build)
```

Future Vision defines direction. Pilot data determines timing. Do not weaken this gate.

---

## 5. Relationship to Current Documents

**Decision Freeze remains authoritative.**  
**ADRs remain authoritative.**  
**Request Framework remains authoritative.**

This document is a parking lot for ideas. It holds hypotheses until evidence exists to evaluate them. It does not change scope. It does not change architecture. It does not change what gets built in any current or upcoming sprint.

If this document ever conflicts with the SSOT documents:

> **SSOT wins. This document is wrong.**

To promote any idea from Future Vision to a real decision, the path is:
1. Collect pilot data that supports the idea
2. Write an ADR
3. Get the ADR accepted into the Decision Freeze
4. Then build

---

## 6. Current Recommendation

**Build now:**

- Add Vehicle (live — continue to stabilize)
- Replace Vehicle V1 Safe (Day 2 target)
- Pilot Cases CK-001 through CK-010
- Broker Feedback collection
- Time Savings Validation

**Do not build now:**

- AI Case Manager
- Autonomous follow-up loops
- Advanced workflow systems
- Carrier or AMS integrations
- Timeline UI (see ADR-002)

The 10-case gate is the next decision point. Until then, the Development Loop is the only active loop.

---

## 7. Active Case / Submission Data Hierarchy (P17+ North Star)

**Review date:** 2026-06-23  
**Status:** Future Vision only — no code, no migrations, no sprint commitment  
**Trigger:** Post–Chen Kui demo; pilot today uses `Request = Case`, which creates duplicate broker inbox rows when customers upload in multiple sessions.

### 7.1 Problem Today

```
Customer uploads insurance card   → Case A
Customer uploads dec page         → Case B
Customer uploads VIN screenshot   → Case C
Broker sees 3 rows for one add-car job.
```

Pilot tolerates this. Long-term it conflicts with broker mental model (one endorsement = one work item) and with the Blueprint re-upload model.

### 7.2 Proposed Canonical Hierarchy

```
Household / Customer          [P19+ — optional; not required for P17]
        ↓
Active Insurance Case         [Broker inbox: one row per work item]
        ↓
Submission                    [One customer interaction — append-only]
        ↓
Documents                     [Files attached to a submission]
        ↓
Current Broker Packet         [Materialized best state — broker primary view]
```

**Guiding principle:**

| Who | Sees / owns |
|-----|-------------|
| Broker | **Active Case** (inbox row) + **Current Packet** (action view) |
| System | **Submissions** (event log) |
| Packet | **Current best state** — readiness, vehicles, drivers, missing_items, copy_text |

**TurboTax analogy:** Uploading a W2 does not create a new tax return. Uploading a dec page should not create a new broker case.

**Example inbox (target):**

```
Andy Li · Policy Review · READY · 3 submissions
```

Not three identical rows.

### 7.3 Broker-Facing vs System-Facing vs Execution-Facing Units

Three layers serve different audiences. Do not collapse them into one object.

| Layer | Role | Audience |
|-------|------|----------|
| **Active Case** | Broker-facing unit | Broker inbox — what work exists |
| **Submission** | System-facing unit | Append-only event log — what the customer did |
| **Packet** | Execution-facing unit | Office action surface — what to copy and act on |

```
Broker sees Cases.
System records Submissions.
Office works from Packets.
```

**中文：**

- **Active Case** 是经纪人看到的工作单元。
- **Submission** 是系统记录的提交事件。
- **Packet** 是办公室实际执行和复制使用的数据包。

经纪人看 Case。系统记 Submission。办公室使用 Packet。

**Example — Policy Review Case**

Submissions (system record; broker does not open each one by default):

- Insurance Card
- Declaration Page
- VIN Screenshot

Current Packet (execution surface — office copies from here):

- Carrier: Progressive
- Premium: $844.76
- Vehicles: BMW X5 + Toyota Corolla
- Status: READY
- Broker Next Action: Re-shop

Broker normally works from the **Packet** in the **Broker Workbench**, not from individual submissions. Submissions exist for audit, merge, and future Business Loop (§2); the Packet is the materialized best state after all evidence is combined in **Case Memory**.

### 7.4 Verdict

**Adopt as P17/P18 North Star.** Compatible with existing ADRs:

- ADR-001: READY / NEED_INFO / BROKER_REVIEW apply to **Packet**, not per-submission
- ADR-002: Submissions enable future timeline; Timeline UI still deferred
- ADR-003: Packet remains product end state; no carrier API

**Phased intent (concept only):**

| Phase | Focus |
|-------|-------|
| **P17** | Active Case + Submission; lightweight `person_link_key` (phone hash / broker ref); inbox dedup; packet merge rules documented |
| **P18** | Business Loop (§2): auto re-readiness on new submission; optional light timeline |
| **P19+** | Household (multi-policy, multi-vehicle, home/umbrella) — only if broker pays for it |

**Household is not required before Active Case.** P17 can match cases via `person_link` without a full CRM graph.

### 7.5 What Stays Unchanged

- Trusted Packet as broker primary view
- Three readiness states (ADR-001)
- 7-step customer flow + Driver / Vehicle / Policy buckets (Request Framework)
- Source attribution per field
- Customer language: "sent to broker" (ADR-003)
- New request type = new schema, not new product
- No carrier API, no AMS write-back, no customer login (V1 constraints)

### 7.6 What to Defer

| Defer | Until |
|-------|-------|
| Full Household / CRM | P19+ or explicit broker demand |
| Timeline UI | ADR-002 gate (10 cases or broker asks) |
| Document classification / quality scoring | P18+ |
| Autonomous follow-up (Business Loop) | P17 end / P18; after validation gate (§4) |
| Workflow engine (Temporal, etc.) | Not before Business Loop is validated |

### 7.7 Key Risks

1. **Case matching ambiguity** — same phone, different intents (Add Vehicle vs Replace Vehicle): merge rules must be explicit before build.
2. **Packet merge complexity** — conflicting VINs across submissions → more BROKER_REVIEW, not silent resolution.
3. **Scope creep toward CRM** — Household layer is the main temptation; keep deferring until paid signal.
4. **No-account continuity** — customer must return to same case via magic link / token without login.

### 7.8 Industry Alignment (reference)

| System | Closest mapping |
|--------|-----------------|
| TurboTax | Return → Documents → Current state (**best analogy**) |
| Insurance AMS | Policy → Endorsement/Transaction → Supporting docs |
| Salesforce / HubSpot | Account → Case/Ticket → Activity → current stage |

Broker inbox unit should align with **endorsement work item**, not **document upload event**.

### 7.9 Promotion Path

This section does not change runtime. To implement:

1. Pass validation gate (§4) + Chen Kui pilot learnings
2. ~~Write **ADR-005**~~ **Done (2026-06-29):** `docs/p16/adr/ADR_005_ACTIVE_CASE_CONSOLIDATION.md` — Accepted Architecture; implementation gated
3. ~~Accept into Decision Freeze~~ **Done:** ADR index updated in `P16_DECISION_FREEZE_V1.md`
4. Then build (P17 Phase 1 coding)

---

## 8. Long-term Product Philosophy

This section is the highest-level guidance for future evolution. It is concise, timeless, and independent of any specific technology or channel. It clarifies long-term direction without changing today's execution plan (§6) or validation gates (§4).

---

### Principle 1 — AI Worker, not AI Feature

Insurance Case IQ is gradually evolving from isolated AI features (extraction, triage, readiness check) into an **AI case operator** that continuously helps brokers move insurance cases toward completion.

| What it means | What it does not mean |
|---------------|----------------------|
| Works beside the broker | Replaces broker judgment |
| Proposes drafts, gaps, and next steps | Gives autonomous insurance advice |
| Evidence-first — documents and fields, not chat alone | An autonomous chatbot customers talk to instead of the office |
| Broker-in-the-loop at every consequential gate | Hands cases to carriers or customers without review |

The product is not positioned as a chatbot. It is a case operator: AI does the repetitive evidence work; the broker decides what reaches the customer and the carrier.

---

### Principle 2 — Business Loop, not One-shot Workflow

Every capability should strengthen a measurable **Business Loop** (§2), not a one-time intake form that ends at submission.

```
Customer
    ↓
Evidence (uploads, messages, channel events)
    ↓
Case Memory (merged facts across turns and days)
    ↓
Reality Validation (readiness, missing items, conflicts)
    ↓
Trusted Packet (broker-ready materialized state)
    ↓
Broker Gate (review, confirm, copy, act)
    ↓
Customer Follow-up (when gaps remain)
    ↓
Case Memory (updated — loop repeats)
```

The goal is to **move cases toward broker-ready outcomes**, not to always complete every case without human involvement. The **Broker Gate** stays explicit. Automation may handle gap detection and customer prompts; the broker remains accountable for what the office sends and quotes.

---

### Principle 3 — Business KPI, not Model Capability

Future AI investments should be justified by **measurable business outcomes**, not by model sophistication for its own sake.

| Justify by | Examples |
|------------|----------|
| Broker time saved | Minutes per case vs manual WeChat re-read |
| Broker-ready packet rate | % of cases reaching READY / actionable NEED_INFO on first or second pass |
| Missing-item detection | Gaps surfaced before broker opens WeChat |
| Follow-up efficiency | Reduction of repetitive broker ↔ customer ping-pong |
| Case completion efficiency | Time from first evidence to broker-ready packet |

LLM upgrades and prompt tuning are means, not ends. Prefer investments that move a KPI over investments that only improve benchmark scores.

Some infrastructure enables KPIs indirectly — and is worth building for that reason:

| Infrastructure | Indirect KPI effect |
|----------------|---------------------|
| **Case Memory** | Fewer re-asks; faster second-pass readiness |
| **Channel Adapter** (ADR-004) | Same loop on Web, WeCom, Email — no per-channel rework |
| **Active Case** hierarchy (§7) | One inbox row per work item; less broker confusion |
| **Reality Validation** | Guardrails and pilot proof before scope expands |

---

### Supporting Principles

These principles are woven through §2–§7 and the three principles above. They are stated here for clarity.

**Broker-in-the-loop.** AI proposes. Broker decides. Autonomy expands only after pilot evidence demonstrates sufficient trust — never by default.

**Evidence-first.** Evidence is more valuable than conversation. **Case Memory** + **Reality Validation** + **Trusted Packet** form the trust layer. Conversation alone is not the product; messages and uploads are evidence attached to cases.

**Case-centric.** The product operates on **Active Cases** (§7). Messages, channels, uploads, and conversations are evidence attached to cases. The case — not the message — is the fundamental business object.

**Channel-agnostic delivery.** Insurance Case IQ is the product; channels are adapters. Web Intake, Enterprise WeCom (ADR-004), and future Email/SMS integrate through the **Channel Adapter** contract — one AI engine, many transports. New channel = new adapter, never a forked product.

**Promote by evidence.** Future Vision defines direction. Pilot data determines timing. The path remains: **10 cases → paid validation → ADR → Decision Freeze → build** (§4). Speculation does not override the gate.

---

*Related: `docs/p16/P16_DECISION_FREEZE_V1.md` · `docs/p16/P16_REQUEST_FRAMEWORK.md` · `docs/p16/P16_CUSTOMER_FLOW_BLUEPRINT.md` · `docs/p16/adr/ADR_001_REQUEST_READINESS.md` · `docs/p16/adr/ADR_002_NO_TIMELINE_V1.md` · `docs/p16/adr/ADR_003_NO_CARRIER_API_V1.md` · `docs/p16/adr/ADR_004_ENTERPRISE_WECOM_CHANNEL_INTEGRATION.md` · `docs/p16/adr/ADR_005_ACTIVE_CASE_CONSOLIDATION.md`*
