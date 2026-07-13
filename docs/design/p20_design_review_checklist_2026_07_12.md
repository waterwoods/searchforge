# P20 Design Review Checklist

> Reusable checklist that **every P20 feature, change, or track deliverable must answer before merge.**
> Governed by `docs/design/p20_production_constitution_master_design_2026_07_12.md`. Copy this block into the feature's STOP report / handoff summary and answer each item with **YES / NO / N-A + one line of evidence**.

**Date:** 2026-07-12 · **Status:** RATIFIED (with the Constitution)

---

## 1. How to use

1. Read the P20 Constitution and the relevant module SSOT first.
2. Fill this checklist **before** writing code (design intent) and **again** before merge (evidence).
3. Any **NO** on a Frozen-boundary item (§21 of the Constitution) is a **STOP** — escalate to Founder.
4. Never mark a manual/compliance item PASS without real verification.

---

## 2. Checklist

### Product principle

| # | Question | Answer | Evidence |
|---|----------|--------|----------|
| 1 | **Customer Task First** — is there exactly one current task, no customer-managed cases/lanes? | | |
| 2 | **Structured Input First** — is selection/photo/confirm preferred over free typing? | | |
| 3 | **One Primary CTA** — exactly one primary action on each page? | | |
| 4 | **Backend owns state** — are phase/missing/gates computed & persisted server-side (no client authority)? | | |
| 5 | **AI stays advisory** — does AI only suggest (no phase/submit/broker_done/coverage/liability, no silent overwrite)? | | |
| 6 | **Timeline/evidence preserved** — append-only timeline, durable evidence, nothing silently lost? | | |
| 7 | **Customer-confirmed facts protected** — is the write provenance-guarded? | | |

### Architecture & reuse

| # | Question | Answer | Evidence |
|---|----------|--------|----------|
| 8 | **Task Contract reused** — does the client render the server-driven descriptor (no hardcoded fields/steps/routes)? | | |
| 9 | **UI Kit reused** — shared behavior/components, not per-page lifecycle copy? | | |
| 10 | **No new unnecessary framework** — no Taro/React/Vue/uni-app; no premature Temporal/Camunda; no new service/portal? | | |
| 11 | **Reuse over rewrite** — am I extracting/wiring existing assets rather than rebuilding? | | |
| 12 | **Framework-vs-feature** — is this a new task/field/config (data) rather than a new code path? | | |

### Multi-tenant & security

| # | Question | Answer | Evidence |
|---|----------|--------|----------|
| 13 | **Tenant-scoped** — is `tenant_id` server-derived and are queries/workbench scoped? (No spoofable header trust.) | | |
| 14 | **Security reviewed** — auth on every broker endpoint; signed links; no secrets/customer data in Git; PII-safe logs? | | |

### Reliability

| # | Question | Answer | Evidence |
|---|----------|--------|----------|
| 15 | **Idempotent** — logical submissions/uploads/field writes carry idempotency keys? | | |
| 16 | **Resume-safe** — does the flow return to the same task/case after interruption? | | |
| 17 | **Retry-bounded** — bounded retries, no infinite loops, exponential backoff? | | |
| 18 | **Error actionable** — every failure has a visible, recoverable, non-silent outcome? | | |
| 19 | **Concurrency-safe** — optimistic concurrency / transaction / advisory-lock where multi-step or multi-user? | | |

### Quality & operability

| # | Question | Answer | Evidence |
|---|----------|--------|----------|
| 20 | **Test coverage added** — unit/contract/idempotency/isolation as applicable; existing tests still green? | | |
| 21 | **Observability added** — correlation/tenant/case IDs, result, latency, error class logged (no sensitive content)? | | |
| 22 | **Manual acceptance identified** — DevTools/real-device/compliance items listed, none auto-marked PASS? | | |
| 23 | **Persistence durable** — does state survive a PG-primary reload (no dev-JSON-only truth)? | | |

### Scope & governance

| # | Question | Answer | Evidence |
|---|----------|--------|----------|
| 24 | **No hidden scope expansion** — only the stated files/goals touched; unrelated work preserved? | | |
| 25 | **No schema migration / deploy / push / secret commit** unless explicitly approved? | | |
| 26 | **File ownership respected** — within Track A/B/C boundaries; no *silent* cross-track edits, and any necessary cross-track interface change was STOPped + reported (why/files/coordination/sequence) before proceeding? | | |
| 27 | **Findings classified** — KEEP / HARDEN / EXTRACT / DEFER / BLOCKER? | | |
| 28 | **Unverified WeChat capabilities labeled** — CONFIRMED / ASSUMED FOR PROTOTYPE / OFFICIAL VALIDATION REQUIRED? | | |

---

## 3. STOP conditions

Escalate to Founder and pause if any of these is true:

- A Frozen-boundary item (Constitution §21) would change.
- A schema migration, deploy, publish, or push would be required.
- An unverified WeChat capability would become a hard dependency.
- The change makes AI authoritative over workflow state.
- Tenant isolation would be weakened.
- A manual/compliance item cannot be honestly marked verified.

---

*P20 Design Review Checklist — reusable. Answer all items in the feature handoff before merge.*
