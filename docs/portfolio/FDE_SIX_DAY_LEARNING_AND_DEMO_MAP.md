# FDE Six-Day Learning and Demo Map

**Status:** Founder-explainable module map for Case Builder Sunday V1  
**Date:** 2026-08-03  
**Audience:** Founder (primary), FDE/interview reviewers (secondary)  
**Rule:** Explain only what was personally reviewed or backed by evidence. Do not pretend expert depth on unreviewed internals.

**Related:**  
- Product promise: `docs/product/CASE_BUILDER_NORTH_STAR_2026-08-03.md`  
- Plan: `docs/roadmap/SIX_DAY_PILOT_RELEASE_PLAN_2026-08-03.md`  
- Existing case studies: `FDE_CASE_STUDY_METRICS_V1.md`, `FDE_CASE_STUDY_LANGGRAPH_V1.md`

---

## How to use this map

For each module, the Founder should be able to say:

1. What customer pain it reduces  
2. Where it sits in the workflow  
3. What happens when it fails  
4. What evidence proves it (or that it is not yet proven)

Interview depth is optional; customer honesty is mandatory.

---

## 1. Deterministic Case workflow

| Field | Content |
|-------|---------|
| What it is | Cap2 / claim kernel path: intake → submit → Request More → supplement → broker ack → office materials accept. |
| Why needed | Office trust requires repeatable state, not chat improvisation. |
| Workflow connection | Backbone of the canonical journey; AI and metrics hang off it. |
| Failure mode | Wrong status, duplicate accept, accept while Request More open. |
| Fallback/control | Idempotent commands; 409 when accept blocked; Timeline audit. |
| Customer benefit | Clear “what happens next” after sending materials. |
| Reusable delivery | Same kernel for a second office with config, not a rewrite. |
| Interview point | Deterministic workflow first; AI second. |
| 30-second explanation | “We freeze the claim steps the office already understands—collect, request more, confirm complete—so demos and pilots don’t depend on an agent guessing the process.” |
| Evidence/demo | `docs/evidence/STAGE1_FOUNDER_VALIDATED_CLOSEOUT.md`; tag `stage1-founder-validated-demo-2026-08-03` |

---

## 2. Timeline and projections

| Field | Content |
|-------|---------|
| What it is | Append-only Timeline events + customer/Broker projections (Task Home, Cap2, Workbench Brief). |
| Why needed | Customer and Broker must see one truth for the same case. |
| Workflow connection | Every meaningful confirm/supplement/accept leaves an auditable mark. |
| Failure mode | Projection drift (customer thinks saved; Broker cannot see). |
| Fallback/control | Read-after-write; server SSOT; Brief built from case + timeline. |
| Customer benefit | “I already sent it” becomes checkable. |
| Reusable delivery | New surfaces read projections instead of inventing state. |
| Interview point | Event-sourced-ish office memory without a heavy platform. |
| 30-second explanation | “One case record feeds the customer task view and the broker brief, so nobody argues from two different stories.” |
| Evidence/demo | Stage 1 timeline export in Fast Lane evidence; Workbench Brief on QA |

---

## 3. Idempotency

| Field | Content |
|-------|---------|
| What it is | First-wins keys on commands and activity events so retries don’t double-apply. |
| Why needed | Mobile networks retry; double accept/ack destroys trust. |
| Workflow connection | Ack, office accept, propose/confirm, timing stamps. |
| Failure mode | Duplicate Timeline noise or double state transition. |
| Fallback/control | Idempotency keys; replay returns same outcome. |
| Customer benefit | Safe tap-retry on phone. |
| Reusable delivery | Standard for any office API integration. |
| Interview point | Reliability detail interviewers undervalue until demos break. |
| 30-second explanation | “If the phone retries, the server does the business action once and answers consistently the second time.” |
| Evidence/demo | Stage 1 closeout idempotency notes; LangGraph propose/confirm tests |

---

## 4. Real usage metrics

| Field | Content |
|-------|---------|
| What it is | Durable `case_activity_events` + business timestamps exported read-only. |
| Why needed | Prove where cases stall without fabricating “time saved.” |
| Workflow connection | Observes intake open, first action, broker first open alongside Request More loops. |
| Failure mode | Confusing page-open with work; GET inventing broker-open. |
| Fallback/control | First-wins; exporter never stamps; blanks stay blank. |
| Customer benefit | Indirect—better product decisions, not a customer UI. |
| Reusable delivery | Same exporter for any office’s QA/pilot cohort. |
| Interview point | Measurement before AI hype. |
| 30-second explanation | “We record a few honest timestamps—when the customer starts, when the broker first opens—without claiming minutes saved until we have real volume.” |
| Evidence/demo | `docs/metrics/REAL_USAGE_TIMING_V1_CLOSEOUT.md`; `FDE_CASE_STUDY_METRICS_V1.md` |

---

## 5. LangGraph (bounded accident-story assistant)

| Field | Content |
|-------|---------|
| What it is | Small graph that organizes a messy accident story into a **proposal** for human confirm. |
| Why needed | Brokers need structured Must Haves without AI owning the claim. |
| Workflow connection | Sits between raw story and deterministic completeness / Broker review. |
| Failure mode | Hallucinated fields, silent injury flip, lifecycle mutation. |
| Fallback/control | Validate → deterministic extractor; AI never submits/closes; unconfirmed ≠ fact. |
| Customer benefit | Faster clarification with fewer back-and-forth guesses. |
| Reusable delivery | Pattern: bounded assistive graph + human gate. |
| Interview point | Probabilistic assist inside a deterministic shell. |
| 30-second explanation | “LangGraph only drafts a structured accident summary. The customer must confirm before anything becomes case truth, and it never changes claim status.” |
| Evidence/demo | `FDE_CASE_STUDY_LANGGRAPH_V1.md`; `tests/test_accident_story_langgraph.py`; code under `accident_story_assistant/` — **phone freeze pending Day 1** |

---

## 6. LangSmith

| Field | Content |
|-------|---------|
| What it is | Tracing + golden dataset + evaluators for the accident-story graph (PR B — planned Day 2). |
| Why needed | Know why a proposal was bad before the office loses trust. |
| Workflow connection | Observes graph/model calls; does not drive lifecycle. |
| Failure mode | Traces leaking PII; flaky LLM judge blocking demos. |
| Fallback/control | Opt-in tracing; deterministic evaluators primary; judge optional. |
| Customer benefit | Indirect quality and faster fix loops. |
| Reusable delivery | Eval gate portable to next office’s scenario pack. |
| Interview point | Offline regression for AI, not vibe checks. |
| 30-second explanation | “LangSmith is our flight recorder and quiz for the story assistant—so we catch bad questions and hallucinations in CI before a broker sees them.” |
| Evidence/demo | After Day 2: `docs/evidence/langsmith-pr-b/`. Until then: say “planned / not closed.” |

---

## 7. Human-in-the-loop feedback

| Field | Content |
|-------|---------|
| What it is | Customer confirm/edit/reject of AI proposals; later Accept/Edit/Reject metrics (Day 3). |
| Why needed | AI quality is a hypothesis until humans vote with edits. |
| Workflow connection | Authority: `ai_proposed` → `customer_confirmed` (broker review later). |
| Failure mode | Treating proposals as facts; no instrumentation. |
| Fallback/control | Confirm flag; edits override; exporter honesty notes. |
| Customer benefit | Customer stays in control of their story. |
| Reusable delivery | Feedback events feed eval and prompt fixes. |
| Interview point | HITL as product law, not UI garnish. |
| 30-second explanation | “Every AI suggestion is temporary until the customer accepts or edits it—and we plan to count those accepts and edits so we don’t guess whether the AI helps.” |
| Evidence/demo | Confirm API behavior today; rates after Day 3 report |

---

## 8. Security and audit

| Field | Content |
|-------|---------|
| What it is | API keys, tenant/client boundaries, invite isolation, Timeline/office action logs, Day-4 audit. |
| Why needed | Soft pilot talk is unsafe without basic isolation and auditability. |
| Workflow connection | Guards every read/write of case evidence. |
| Failure mode | Cross-customer evidence; secrets in git/traces. |
| Fallback/control | Product-only keys; fail-closed invite redeem; audit checklist. |
| Customer benefit | Their accident materials stay in their office context. |
| Reusable delivery | Checklist becomes second-office entry ticket. |
| Interview point | FDE ships with blast-radius thinking. |
| 30-second explanation | “Before we talk pilot, we verify one office cannot see another’s cases, and sensitive broker actions leave an audit trail.” |
| Evidence/demo | Track C evidence; Stage 2 invite isolation; Day 4 audit (planned) |

---

## 9. Model fallback

| Field | Content |
|-------|---------|
| What it is | When LLM/graph path fails, deterministic extractors continue intake. |
| Why needed | Demo and pilot cannot hard-fail on model timeout. |
| Workflow connection | Inside propose path; customer still confirms facts. |
| Failure mode | Hard 500; empty story; invented coverage fields. |
| Fallback/control | Sequential/deterministic path; feature flag off LLM; guardrails strip hallucinations. |
| Customer benefit | They can always finish manually. |
| Reusable delivery | Same pattern for future assistive slices. |
| Interview point | Graceful degradation is the product. |
| 30-second explanation | “If the model times out or returns junk, we fall back to simple rules, keep the customer’s original words, and continue the form.” |
| Evidence/demo | LangGraph timeout/invalid JSON tests |

---

## 10. MCP tools

| Field | Content |
|-------|---------|
| What it is | Thin Broker tools (planned Day 5): three read-only + one draft/write requiring human confirm. |
| Why needed | Forward-deployed delivery without giving agents silent case mutation. |
| Workflow connection | Reads Brief/Timeline/missing items; draft Request More still needs Broker. |
| Failure mode | Write tool that persists without human. |
| Fallback/control | Product does not depend on MCP; tools optional/lab-adjacent. |
| Customer benefit | Indirect—faster office ops tooling later. |
| Reusable delivery | Second-office integration surface. |
| Interview point | MCP with least privilege. |
| 30-second explanation | “MCP here means a few safe broker tools—look up a case, see what’s missing—and any draft change still needs a human confirm. It is not the product we sell to 陈总.” |
| Evidence/demo | Today: `mcp/` is LAB ONLY. After Day 5: case-builder broker tools README |

---

## 11. Configuration / playbook

| Field | Content |
|-------|---------|
| What it is | Client/office packs, demo invite catalog (Chen Camry scenarios), Prepare Demo / Fast Lane, second-office checklist. |
| Why needed | Founder continuity and multi-office delivery without rewriting code. |
| Workflow connection | Selects persona, prefill, copy, and demo reset behavior. |
| Failure mode | Tribal setup; wrong office config in QA. |
| Fallback/control | Documented checklist; scenario_id catalog. |
| Customer benefit | Familiar Chen office language and vehicles. |
| Reusable delivery | Template + checklist for office #2. |
| Interview point | Configuration over customization chaos. |
| 30-second explanation | “Chen’s Camry demo is a scenario pack and invite—not a one-off fork—so we can reset and replay the same story cleanly.” |
| Evidence/demo | `demo_invite/catalog.py`; Stage 1/2 scenarios; Day 5 checklist (planned) |

---

## 12. GCP deployment and rollback

| Field | Content |
|-------|---------|
| What it is | Cloud Run QA (`fiqa-api-qa`), Postgres, Vercel UI; cost-saving scale; deploy/rollback via existing scripts. |
| Why needed | Demos need a stable URL; cost must not burn the company. |
| Workflow connection | Hosts the entire Founder QA path. |
| Failure mode | Wrong service retarget; leaving max scale high; CORS drift. |
| Fallback/control | QA-only this week; minScale=0/maxScale=2 after demos; deployment QA gate scripts. |
| Customer benefit | Reliable phone preview when configured. |
| Reusable delivery | Same pattern for next environment with explicit promotion. |
| Interview point | Ops discipline is part of FDE work. |
| 30-second explanation | “We demo on a QA Cloud Run service, keep Production untouched, and scale QA back down after phone tests so the bill stays sane.” |
| Evidence/demo | `docs/CURRENT_PRODUCT_SHAPE.md`; `docs/ops/GCP_COST_AUDIT_2026-08-03.md`; Stage closeouts ops posture |

---

## Founder rehearsal card (keep honest)

| Say | Don’t say |
|-----|-----------|
| Founder-validated Stage 1/2 on Cloud QA | Production-validated / paid-pilot proven |
| Timing instrumentation is honest and incomplete | We save brokers 30 minutes |
| LangGraph proposes; humans confirm | Autonomous claim AI |
| LangSmith/MCP are engineering leverage | We sell LangSmith/MCP to brokers |
| Sunday label per gates doc only | PRODUCTION READY |

---

## Module readiness snapshot (2026-08-03 audit)

| Module | Implemented | Tested | Deployed QA | Founder-validated |
|--------|:-----------:|:------:|:-----------:|:-----------------:|
| Deterministic workflow | Yes | Yes | Yes | Yes (Stage 1) |
| Timeline/projections | Yes | Yes | Yes | Yes (Stage 1/2) |
| Idempotency | Yes | Yes | Yes | Partial (Stage 1 path) |
| Real usage metrics | Yes | Yes | Yes | Integrity pack; not phone product feature |
| LangGraph | Yes | Yes (local) | Code on branch; QA deploy TBD Day 1 | No phone freeze yet |
| LangSmith Case Builder | No | No | No | No |
| HITL confirm path | Yes | Yes | Branch | Pending Day 1 phone |
| HITL Accept/Edit/Reject metrics | No | No | No | No |
| Security/audit baseline | Partial | Partial | Partial | Day 4 strengthens |
| Model fallback | Yes | Yes | Branch | Via tests |
| MCP broker tools | Lab only | Lab | No | No |
| Config/playbook | Partial | Partial | Yes (Chen invite) | Stage demos |
| GCP deploy/rollback | Yes | Ops scripts | QA yes | Ops posture in closeouts |
