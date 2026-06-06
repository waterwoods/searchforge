# Unified Intake MVP v1 – Product Definition Report

**Sprint:** Unified Intake MVP v1 – Product Definition Sprint  
**Date:** 2026-03-07  
**Mode:** Doc-first, narrow-scope product definition

---

## 1. Product definition docs created

| Doc | Path | Defines |
|-----|------|---------|
| **Master goal** | `docs/goals/UNIFIED_INTAKE_MVP_MASTER_GOAL.md` | Problem, user, what MVP does/doesn't do, value, input model, output model, "good enough" criteria |
| **Standard** | `docs/standards/UNIFIED_INTAKE_MVP_STANDARD.md` | Output shape, categories, urgency, client draft rules, escalation logic, weak output, regression |
| **Runbook** | `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | Workflow, dev loop, scenario runner, API, guardrail, Cursor/OpenClaw roles |
| **Guardrails** | `docs/guardrails/UNIFIED_INTAKE_MVP_GUARDRAILS.md` | Drift risks, scripts, when to run, fail vs warn |
| **Scenarios** | `docs/UNIFIED_INTAKE_MVP_SCENARIOS.md` | 12 scenarios with input, expected outputs, notes |
| **Boundaries** | `docs/UNIFIED_INTAKE_MVP_BOUNDARIES.md` | Business value, what must be true to pay, build next / do later / do not do now |

**Indexes updated:** `docs/goals/INDEX.md`, `docs/standards/INDEX.md`, `docs/runbooks/INDEX.md`, `docs/guardrails/INDEX.md`, `docs/PROJECT_DOC_SYSTEM_MAP.md`, `AGENTS.md`

---

## 2. MVP workflow definition

**End-to-end workflow:**

1. **Receive text input** — Broker pastes message (screenshot OCR, email, notice, client text)
2. **Normalize input** — Strip, collapse whitespace
3. **Detect issue category** — One of 10 categories (missing_signature, missing_document, cancellation_warning, etc.)
4. **Estimate urgency** — low / medium / high / critical
5. **Decide manual follow-up needed** — Boolean based on urgency, clarity, sensitivity
6. **Produce broker next step** — Actionable text for broker
7. **Produce client-prep guidance** — What client should gather/do
8. **Produce client-ready reply draft** — Editable by broker before sending

**Where AI/rules are used:** Classification, urgency, and draft generation use LLM when `LLM_GENERATION_ENABLED`; rule-based fallback otherwise.

**Where broker review is required:** Always. Broker reviews output, edits draft, decides and acts. No auto-send.

**Intentionally deferred:** Case/customer linking, email/WeChat integration, CRM, automatic outbound.

---

## 3. Input model

| Input Type | In Scope | Notes |
|------------|----------|-------|
| Pasted message text | **Yes** | Primary path |
| Pasted email text | **Yes** | Same as message |
| OCR-extracted screenshot text | **Yes** | Broker pastes OCR output; no built-in OCR in v1 |
| Short broker context | Optional | Not required for v1 |

**Out of scope for v1:** Raw image upload, case/customer identification, identity extraction, email/WeChat API integration.

**v1 assumption:** Broker provides text only. No automatic ingestion.

---

## 4. Output model

| Field | Required | Broker-only / Client-facing |
|-------|----------|-----------------------------|
| `issue_category` | Yes | Broker-only |
| `urgency` | Yes | Broker-only |
| `manual_followup_needed` | Yes | Broker-only |
| `broker_next_step` | Yes | Broker-only |
| `client_prep` | Yes | Broker-only |
| `client_reply_draft` | Yes | **Client-facing** (broker edits before sending) |

**Wording principles:** Professional, courteous; no legal/financial advice; no promises broker cannot keep.

---

## 5. Scenario pack

- **Count:** 12 scenarios (S1–S12)
- **Location:** `configs/inbox_triage_scenarios.json` (machine-readable); `docs/UNIFIED_INTAKE_MVP_SCENARIOS.md` (human-readable)
- **Categories covered:** missing_signature, missing_document, cancellation_warning, policy_delay_pending, underwriting_followup, renewal_reminder, customer_question, payment_lapse_expiration, informational, unclear

---

## 6. Business value definition

A broker like 陈奎 would say this is worth using when:

- **"This saves me time"** — One paste → structured triage; client-ready draft reduces copy-paste
- **"This reduces repeated explanation"** — Draft tailored to category; broker edits instead of writing from scratch
- **"This reduces missed follow-ups"** — Urgency + escalation flag surface same-day action items
- **"This is worth using again"** — Output consistent, predictable, actionable

**What must be true for it to feel worth paying for:**

1. Triage reliable — Category and urgency match broker intuition
2. Draft usable — Professional tone; broker edits, not rewrites
3. Escalation sensible — Critical/high flagged; low/informational not over-flagged
4. No surprises — Output shape stable; no random failures

---

## 7. Implementation boundaries

### Build next

- Expose Unified Intake via simple UI (paste box → triage result)
- Ensure scenario pack passes with LLM enabled
- Add broker-facing copy of triage result (for WeChat/email)
- Validate with 1–2 real broker messages

### Do later

- Email/WeChat/SMS integration
- Case/customer linking
- History or "similar past cases"
- Multi-broker / auth

### Do not do now

- Full CRM
- Automatic outbound messaging
- Stripe/billing integration
- Multi-tenant auth
- Broad customer support platform
- Huge UI overhaul

---

## 8. Recommended next sprint

**Unified Intake MVP v1 – UI & Validation Sprint**

- Add a simple paste-box UI that calls `POST /api/inbox/triage` and displays the structured result
- Run scenario pack with LLM enabled; fix any failures
- Validate with 1–2 real broker messages (陈奎 or proxy)
- Stop when broker can paste → review → act in a real workflow

---

*End of report*
