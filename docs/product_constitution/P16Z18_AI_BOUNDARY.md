# P16-Z18 AI Responsibility Boundary

**Date:** 2026-06-03  
**Sprint:** P16-Z18 Product Constitution Refresh  
**Sources:** P16-Z2 soul · P16-Z5 memory · P16-Z16/Z17 Customer Builder · product constitution

---

## Principle

AI is a **draft case engine**, not the office. Humans **confirm, correct, and execute**. The product fails if AI tries to be CRM, chatbot, or autonomous agent.

---

## What AI should do

### 1. Convert messy customer input into draft case

| AI owns | Implementation |
|---------|----------------|
| Category / lane classification | `triage.py`, P16-Y lanes |
| Structured extraction | `collected_fields`, `still_needed_fields` |
| Conversation summary | `_build_conversation_summary()` |
| Urgency / risk signals | v4/v5 in `case_draft_engine.py` |
| Draft broker next step | `broker_next_step` templates |
| Draft client reply | `client_reply_draft` (broker copies) |

**Customer path:** `CustomerEntryTab` → `POST /api/inbox/triage` → draft bubbles + field chips before formal submit.

**Broker path:** Paste → same triage engine → draft glance.

AI output is always labeled **draft** until broker confirms via copy, edit, or formal accept.

---

### 2. Merge new information into same case

| AI owns | Implementation |
|---------|----------------|
| Append re-triage with prior context | `triage_for_append()` |
| Field merge across turns | `_merge_persisted_collected`, `append_follow_up_message()` |
| Correction detection | `follow_up_type: correction`, Y44/Y45 prepend |
| Thread persistence | `case_messages[]` append |
| Lane re-anchor on pivot | Premium, cancel→address, claim guards (Z6, Z10A/B) |
| Suggested waiting party | `_suggest_waiting_on()` (Z10B) |

AI **never** creates a duplicate case when append is the correct path. Boundary enforcement (`requires_new_case`) is AI + rules; broker sees clear copy when split is required.

---

### 3. Suggest next action

| AI owns | Implementation |
|---------|----------------|
| `broker_next_step` — office action in Chinese | Lane templates + Z11 office surface |
| `still_needed_fields` — what's missing | Gap list for customer and broker |
| `client_prep` — what to tell customer | Copy draft support |
| `suggested_waiting_on` | Heuristic only — **not auto-PATCH** |
| `office_case_title` — 5-second scan headline | Z11 `_apply_office_value_surface()` |

AI suggests; broker **chooses** whether to copy, edit, call carrier, or wait.

---

## What humans should do

### 1. Confirm

| Human owns | Why |
|------------|-----|
| Accept draft case as office record | Formal submit / broker persist |
| Verify classification on edge cases | AI misroutes on deploy gaps — human catches |
| Confirm `waiting_on` state | Suggest is not auto-set (Z10B) |
| Send client reply | Broker copies `client_reply_draft` to WeChat |
| Carrier / UW calls | Outside product scope |

**UI moment:** Broker reads glance → copies or edits → acts. Customer reads draft → submits to office when ready.

---

### 2. Correct

| Human owns | Why |
|------------|-----|
| Fix wrong category or fields | Learning signal; may trigger re-triage |
| Override generic next step | Chinese specificity is trust |
| Split case when boundary says new case | Mixed claim+payment, unrelated topics |
| Add facts AI missed | Append with new message |
| VIN / structural gates | Partial submit blocked correctly — human completes |

AI learns from corrections via append merge and optional `learning_signals.jsonl` — **not** autonomous retraining in MVP.

---

### 3. Execute

| Human owns | Why |
|------------|-----|
| Call carrier, UW, DMV | Real insurance work |
| Collect signatures, proofs | Documents may attach later |
| Close case / mark outcome | No closure UI in MVP — observation log |
| Invoice and payment | Manual until 3+ offices |
| Trial onboarding Chen Kui | Founder SOP |

Product **ends at office-executable case with timeline**. Execution is the broker's job.

---

## Boundary matrix

| Task | AI | Human |
|------|-----|-------|
| Read customer message | ✅ Draft | — |
| Classify lane | ✅ Draft | ✅ Confirm on edge |
| Extract VIN, plate, policy # | ✅ Draft | ✅ Verify |
| Merge Turn 2+ into same case | ✅ | — |
| Choose waiting party | ✅ Suggest | ✅ Confirm PATCH |
| Copy reply to WeChat | — | ✅ Execute |
| Call insurance company | — | ✅ Execute |
| Formal submit to office | — | ✅ Customer or broker trigger |
| Close / get paid | — | ✅ Founder + broker |

---

## What AI must NOT do (MVP)

| Forbidden | Reason |
|-----------|--------|
| Autonomous outbound messages to customer | Broker is trusted interface |
| Auto-PATCH `waiting_on` without broker | Z10B deliberate design |
| Replace AMS / CRM | Not our scope |
| Promise coverage or quote prices | Regulatory + judgment |
| Invent facts not in message | Draft only from input |
| Run voice / IVR | OUT of MVP |
| Multi-tenant policy admin | Platform fantasy |

---

## Rules-first, not LLM-first

| Fact | Source |
|------|--------|
| P16-Y **88.6** on rules path | Z3, Z10B |
| LLM generation path unverified | Z3 non-goals |
| `LLM_GENERATION_ENABLED=0` in batteries | Z9 validation OS |

AI responsibility = **rules + extractors + merge in `triage.py`**. LLM is optional future — not MVP dependency.

---

## One-line boundary

> **AI drafts and merges the case; humans confirm, correct, and execute.**

---

*End of P16-Z18 Phase 5 — AI Responsibility Boundary*
