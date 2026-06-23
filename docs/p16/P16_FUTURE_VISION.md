# P16 Future Vision — Loop-Based Evolution

**Date:** 2026-06-20  
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

**Purpose:** Move cases forward automatically.

**State: FUTURE VISION ONLY**

This loop does not exist today. In V1, the customer submits once. If information is missing, the broker follows up manually. The Business Loop imagines a system that detects gaps, prompts the customer, re-checks readiness, and iterates until a case is broker-ready — without broker intervention at each step.

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

If the Business Loop is real, P16 could close that gap: detect the missing VIN, prompt the customer automatically, re-run extraction on the new upload, and flip the case to READY — without the broker touching it.

**This is a hypothesis. It is not validated today.**

It may turn out that brokers prefer to handle follow-ups personally. It may turn out that most cases are READY on the first submission. It may turn out that the cost of automating follow-up is not worth the time savings. Pilot data will answer these questions. Speculation cannot.

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

*Related: `docs/p16/P16_DECISION_FREEZE_V1.md` · `docs/p16/P16_REQUEST_FRAMEWORK.md` · `docs/p16/adr/ADR_001_REQUEST_READINESS.md` · `docs/p16/adr/ADR_002_NO_TIMELINE_V1.md` · `docs/p16/adr/ADR_003_NO_CARRIER_API_V1.md`*
