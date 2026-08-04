# FDE Case Study — LangGraph Guided Intake UX V1

**Branch:** `stage2/langgraph-accident-story-assistant`  
**Environment:** Cloud QA only — Production / waterwoods untouched  
**Status:** Guided UX slice shipped for phone QA — does **not** claim production AI accuracy

This document is interview/portfolio evidence for the customer-visible LangGraph path.

---

## Why the first UI failed to demonstrate LangGraph value

Backend LangGraph (propose → missing facts → ≤3 follow-up questions → confirm) passed automated and phone tests. The phone UX still rendered the **full static Must Have form** (time / location / injury) and the grey deterministic banner:

`请先填写：事故时间、事故地点`

That message comes from Mini Program form validation (`startClaimValidation.ts`), not from LangGraph `followup_questions`. Follow-up questions were fetched and shown as a weak secondary note under the story — easy to miss. Founders correctly could not tell where LangGraph was used.

**Classification of prior phone evidence:**

| Layer | Status |
|-------|--------|
| LangGraph backend contract | Validated |
| Customer-facing LangGraph value | Not clearly demonstrated |
| UX slice | Incomplete |

---

## How customer feedback changed the design

Customer/founder feedback: “I need to see the AI working — organize what it knows, ask only what’s missing, then let me confirm.”

New customer-visible flow:

1. **Customer description** — voice or text (e.g. `昨天开车的时候被追尾，没有受伤。`)
2. **AI understanding panel** — `AI已帮您整理` with fact rows labeled as AI draft
3. **Missing-information message** — `还需要确认 N 项` + only LangGraph `followup_questions` / `followup_fields`
4. **Customer confirmation** — `请确认这些事故事实` (original + AI draft + structured facts)
5. **Deterministic Claim workflow** — Cap2 CreateClaim continues; LangGraph never mutates lifecycle

Secondary escape: `查看或修改全部信息` → full static form without abandoning intake.

---

## Deterministic vs probabilistic boundaries

| Deterministic (unchanged) | Probabilistic / assistive |
|---------------------------|---------------------------|
| Cap2 CreateClaim / submit | Story normalize + fact proposals |
| Must Have enablement rules | Follow-up drafting (≤3) |
| Request More / office accept | Optional LLM merge (off by default) |
| Claim status transitions | Never |

Facts become authoritative only after **customer confirmation** (`customer_confirmed`). Unconfirmed AI drafts stay `ai_proposed`.

---

## Dynamic-question architecture

```mermaid
flowchart LR
  A[Customer story] --> B[propose API / LangGraph]
  B --> C[guided_view]
  C --> D{missing_count}
  D -->|0| E[Confirm screen]
  D -->|1-3| F[Dynamic follow-up inputs only]
  F --> E
  E --> G[Start Claim + stamp layers]
  G --> H[Case Status]
```

- `guided_view.followup_fields` drives which inputs render
- Known injury (`没有受伤`) is not re-asked
- Vague day-only time (`昨天`) still asks for clock/period
- Conflicts surface explicitly — never silently picked

---

## Customer confirmation gate

- Confirm screen required before submit when an AI proposal exists
- Actions: `信息正确，提交` / `修改` / `重新描述`
- Start Claim accepts `ai_story_confirmed` + proposal + edits and stamps Broker layers after CreateClaim
- Original customer text retained

---

## Fallback behavior

Invalid JSON / timeout / LLM failure → deterministic extractor path (`used_fallback=true`). Manual full form remains available. Intake never blocks on AI.

---

## Metrics (non-sensitive)

Events (in-memory + case bag / exporter hooks):

- `ai_story_proposal_created`
- `ai_story_proposal_accepted`
- `ai_story_proposal_edited`
- `ai_story_proposal_rejected`
- `ai_story_fallback_used`

Meta allow-list: case_id, proposal version, question count, edited field names, fallback reason category, latency, model/provider, server timestamp. **No raw story text in telemetry.**

Exporter fields: `ai_story_proposal_confirmed`, `ai_story_proposal_edited`, `ai_story_fallback_used`.

---

## Broker Brief — three layers

1. `客户原始描述`
2. `AI整理草稿`
3. `客户已确认事实` (only when confirmed)

Never display an unconfirmed AI proposal as a customer fact. Model/provider stays in technical detail only.

---

## Business value (hypothesis)

Faster Must Have capture with fewer “请先填写” dead-ends and a visible AI assist story for demos and FDE interviews. **Not yet proven with real pilot traffic.**

---

## Three-minute demo path

1. Incomplete story: `昨天开车的时候被追尾，没有受伤。`
2. AI panel shows 追尾 / 昨天待确认 / 地点待确认 / 没有受伤
3. Exactly two questions: 几点？ / 哪里？
4. Customer answers → confirm screen → submit
5. Broker Brief shows confirmed structured facts + three layers

---

## What still requires real-pilot validation

- Live CA claim accuracy
- Reduction in Request More loops
- Broker time saved
- Production reliability under load
- Full LangSmith golden eval gate

**Next task:** `docs/portfolio/LANGSMITH_TRACING_GOLDEN_DATASET_NEXT_TASK.md`
