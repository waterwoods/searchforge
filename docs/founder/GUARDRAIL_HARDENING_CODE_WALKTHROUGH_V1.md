# Guardrail Hardening Code Walkthrough V1

**Audience:** Founder (smart non-specialist with Python/data background)  
**Time:** 10–15 minutes  
**Scope:** Three hardenings to Accident Story / Guided Intake  
**Code wins over older docs.**

---

## 1. Big Picture

```text
CUSTOMER RAW DATA
  "昨天被追尾。"
        │
        ▼
 Deterministic extraction (+ optional LLM)
        │
        ▼
 AI-PROPOSED DATA          ← model may be wrong
        │
        ▼
 Python HARD guardrails    ← reject unsupported injury / clamp fields
        │
        ▼
 LangGraph routing         ← missing facts → ≤3 questions (no Claim submit)
        │
        ▼
 VALIDATED PROPOSAL        ← stored server-side (proposal_id)
        │
        ▼
 Customer confirmation     ← edits allowlisted only
        │
        ▼
 Server proposal verify    ← never trust client AI body
        │
        ▼
 CUSTOMER-CONFIRMED DATA
        │
        ▼
 AUTHORITATIVE BUSINESS DATA  (Case known_facts + Brief layers)
```

**Hard boundary:** LangGraph / LLM never mutate Claim lifecycle (no submit/close).

---

## 2. Fix 1 — Unknown Injury

### Old data flow (risk)

1. Deterministic extract: no injury words → `injury=unknown` ✅  
2. LLM (when enabled) could overwrite → `injury=no` ❌  
3. Missing-fact gate would then **stop asking** about injury  
4. Customer might confirm a silent false “no injury”

### Exact risk

Customer: `昨天被追尾。`  
Model tries: `injury=no`  
Without a hard rule, office truth could become **no injury** though the customer never said that.

### New data flow

1. Extract + optional LLM merge  
2. **`enforce_injury_evidence_guardrail`** re-checks source text  
3. If source does not support yes/no → force `unknown` + warning  
4. LangGraph still derives missing → asks injury  
5. Only customer answer/confirm can make yes/no authoritative

### Exact file / function

`services/fiqa_api/inbox_triage/accident_story_assistant/guardrails.py`  
→ `enforce_injury_evidence_guardrail`  
Also called from:

- `graph.node_extract_fact_proposals` (post-LLM merge)
- `guardrails.apply_safety_guardrails` (defense in depth)

### Important excerpt

```python
det_injury, _, det_conflicts = extract_injury_status(source_text)
if det_injury == "unknown":
    if model in ("yes", "no"):
        warnings.append("injury_llm_unsupported_forced_unknown")
    return "unknown", conflicts, warnings
```

### Why HARD (not prompt)

Prompt says “use unknown if unclear.” Models ignore prompts.  
**Python refuses** unsupported yes/no regardless of model output.

### What LangGraph does after the block

`derive_missing_facts` sees `injury != yes/no` → keeps `injury_status` missing →  
`draft_followup_questions` asks at most 3 questions including injury.

**Result for the example:** `injury=unknown` → ask customer.

---

## 3. Fix 2 — Server Proposal Authority

### Before

Client returned a full proposal object → confirm largely used that body as the AI draft.

### After

1. **Propose:** server creates proposal, stores durable record, returns `proposal_id` + `proposal_version`  
2. **Client:** may edit allowlisted fields only  
3. **Confirm:** server loads proposal by id; **ignores** client AI body as truth  
4. Apply allowlisted `customer_edits`  
5. Stamp `customer_confirmed` into Case + three Brief layers

### Where validation occurs

`service._resolve_server_proposal` + `persistence.filter_customer_edits`

Checks:

- proposal exists / not expired  
- proposal `case_id` matches (or unbound then bind)  
- optional version match  
- edit allowlist: summary / injury / time / location / raw_story only  

### Where authoritative write occurs

`confirm_accident_story` → `patch_case_known_facts(..., status="customer_confirmed")`  
+ provenance bag `accident_story_assistant.layers` (raw / ai_draft / confirmed)

### Browser analogy

“Never trust the browser; server is the source of truth.”  
The Mini Program can display a draft; the **server record** is the AI proposal of record.

---

## 4. Fix 3 — Durable Idempotency

### Before

Process memory: “I already saw this key.”  
New Cloud Run instance / cold start → forgets → duplicate work risk.

### After

```text
Instance A ─┐
            ├→ durable idempotency record (PG if configured; else durable memory)
Instance B ─┘
```

Same key + same payload digest → **same result** (`outcome=replayed`)  
Same key + **different** payload → `idempotency_key_conflict`

### Code

`persistence.put_idempotent_result` / `get_idempotent_record`  
Wired in `propose_accident_story` and `confirm_accident_story`

Idempotency stores **hashed** request digests + response JSON — not phones/OpenIDs.

---

## 5. File Map

| File | Role | Founder should remember |
|------|------|-------------------------|
| `extractors.py` | Deterministic injury/time/location; LLM JSON allowlist | Evidence comes from text rules first |
| `guardrails.py` → `enforce_injury_evidence_guardrail` | HARD unknown-injury gate | **This blocks silent “no”** |
| `graph.py` → `node_extract_fact_proposals` | LangGraph extract + LLM merge | Calls injury hard rule after LLM |
| `service.py` → `propose_` / `confirm_accident_story` | API orchestration | Propose stores; confirm verifies |
| `persistence.py` | Proposal records + durable idempotency | Server truth + replay across instances |
| `flags.py` | Kill switches / LLM default OFF | Instant disable; LLM opt-in |
| `routes/h5_task_intake.py` | HTTP propose/confirm | Exposes `proposal_id` |
| `tests/test_accident_story_guardrail_hardening.py` | Proof for all three fixes | Run this when unsure |

---

## 6. 15-Minute Code Reading Order

**Minute 0–3** — open `guardrails.py`  
Find `enforce_injury_evidence_guardrail`.  
Look for: `det_injury == "unknown"` and `INJURY_LLM_UNSUPPORTED`.  
Understand: unsupported model yes/no cannot stick.

**Minute 3–6** — open `graph.py`  
Find `node_extract_fact_proposals` → call to `enforce_injury_evidence_guardrail`.  
Understand: LLM can fill location/time; injury is re-checked.

**Minute 6–9** — open `service.py`  
Find `propose_accident_story` → `store_proposal_record`.  
Find `confirm_accident_story` → `_resolve_server_proposal`.  
Understand: client proposal body is not AI authority.

**Minute 9–12** — open `persistence.py`  
Find `store_proposal_record`, `put_idempotent_result`, `filter_customer_edits`.  
Understand: durable proposal + replay + edit allowlist.

**Minute 12–15** — skim `flags.py` (`llm_extraction_enabled` default False)  
Then skim one test in `test_accident_story_guardrail_hardening.py` (`test_llm_no_without_evidence_forced_unknown`).

Do **not** read full files or LangGraph internals.

---

## 7. Data Flow Before vs After

| Problem | Before | After | Hard boundary |
|--------|--------|-------|---------------|
| Unknown injury | LLM could set `no` with no evidence | Force `unknown` + ask | Python evidence gate |
| Client proposal trust | Confirm used client AI body | Server `proposal_id` record | Persistence + confirm verify |
| Idempotency | Process memory only | Durable record + digest conflict | Persistence layer |

---

## 8. FDE Interview Story

### 30-second version

We run a bounded LangGraph assist for messy accident stories. The model may propose facts, but deterministic Python blocks unsupported injury guesses, the server owns the proposal record, and only customer confirmation becomes Case truth. Claim lifecycle stays outside the AI graph.

### 2-minute technical version

Raw story hits propose → normalize/extract (optional LLM) → **injury evidence hard rule** → missing Must-Haves → ≤3 follow-ups → store proposal with id. Confirm loads that server proposal, applies allowlisted edits, stamps `customer_confirmed`. Idempotent propose/confirm use durable digests so Cloud Run replays safely. Kill switches and LLM-default-off keep the pilot path rules-first.

**Key sentence:**  
“The LLM is allowed to be wrong; deterministic code prevents an unsupported model output from becoming authoritative business state.”

### 3 strong questions + answers

1. **Why not just improve the prompt?**  
   Prompts are soft; insurance cannot accept silent false “no injury.” Code must refuse.

2. **Why store proposals server-side?**  
   Same reason as web apps: never trust the client as the system of record for AI drafts.

3. **How do you avoid duplicate confirms on two instances?**  
   Durable idempotency key + request digest; same key returns replay; mismatched payload conflicts.

---

## 9. What Founder Does NOT Need to Memorize

- LangGraph `StateGraph` wiring boilerplate  
- LangSmith redaction helper internals  
- Exact regex lists in extractors (know they exist)  
- Test monkeypatch fixtures  
- Postgres DDL column lists  
- Mini Program WXML layout  

---

## 10. Remaining Gaps (honest)

| Gap | Notes |
|-----|------|
| Soft-only remnants | Prompt still asks model to use `unknown` — helpful, not sufficient |
| PG vs memory | Without DB URL, durable layer is process-global memory (survives ephemeral clear; not multi-host). With Postgres configured, proposals/idempotency persist across instances |
| Transaction races | First-write wins via unique keys; not a full serializable saga across Case + idempotency in one DB transaction |
| Production validation | Automated tests green locally; **no Production / waterwoods deploy** in this change |
| Client without `proposal_id` | Confirm regenerates from `raw_story` server-side (safe fallback; not ideal for long-lived draft fidelity) |

---

*End of walkthrough. Next Founder action: follow §6 reading order once, then run:*  
`PYTHONPATH=. python3 -m pytest tests/test_accident_story_guardrail_hardening.py -q`
