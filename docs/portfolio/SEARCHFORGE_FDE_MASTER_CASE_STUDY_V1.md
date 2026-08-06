# SearchForge FDE Master Case Study V1

**Audience:** Forward-Deployed Engineer / Applied AI interviews  
**Product:** California auto insurance broker assistant — Accident Story Guided Intake  
**Honest status:** Cloud QA restricted pilot ready for Founder GO/NO-GO; **not** Production AI; **not** real-customer accuracy proven  
**Freeze:** tag `accident-story-restricted-pilot-rehearsal-v1` @ `68f16d6`

---

## 1. Narrative arc (truthful)

| Stage | What happened |
|-------|---------------|
| Customer discovery | Chinese broker offices struggle with post-accident WeChat chaos; brokers need Must-Have facts without inventing them |
| Workflow mapping | Separate customer Mini Program journey from broker Workbench; map Request More / confirm / office accept |
| Deterministic system of record | Postgres Case + CaseEvent; commands own lifecycle |
| Bounded LangGraph | Propose → normalize → extract → validate → ≤3 follow-ups; **never** mutates claim status |
| Human confirmation | AI draft ≠ fact until customer confirms; Brief shows three layers |
| LangSmith evaluation | Node traces + redaction + golden dataset `accident_story_v1` 20/20 |
| Failure injection | Timeout / invalid / kill switch → manual intake |
| PII-safe tracing | Allow-listed meta; raw story forbidden; clean pilot project |
| Feature flags | Assistant / LLM / allowlist / tracing gates |
| Fallback + rollback | Documented QA kill switch; scale restore |
| Live synthetic canary | Cloud QA allowlist office; 20/20 live model |
| Measurable release gates | Explicit PILOT READY WITH RESTRICTIONS vocabulary |
| Unresolved limits | No Chen activation; no Production; synthetic accuracy only |

---

## 2. Thirty-second explanation

“I built a bounded LangGraph assist for auto-insurance claim intake: customers tell a messy accident story in WeChat, the model proposes structured facts, asks at most three missing questions, and only customer-confirmed facts become office truth. Claim lifecycle stays deterministic. We ship kill switches, deterministic fallback, PII-redacted LangSmith traces, golden evals, and a Cloud QA synthetic canary — ready for a five-case restricted pilot, not Production.”

---

## 3. Two-minute interview explanation

Broker offices lose time retyping WeChat accident stories and arguing about what the customer “meant.” We mapped the real workflow into a Mini Program customer path and a Broker Workbench, with Postgres as system of record.

The AI piece is deliberately small: a LangGraph subgraph that drafts accident facts and follow-ups. It cannot submit or close claims. Customer confirmation is the authority boundary. If the LLM times out or returns invalid JSON, intake continues manually.

Before any restricted pilot, we required: Founder-validated guided UX, 20/20 golden evals, redacted tracing, kill-switch rehearsal, live synthetic canary on Cloud QA, and a five-case office rehearsal. Production and the customer-facing waterwoods path were never touched for this AI enablement. Real Chen office accuracy remains unproven until Founder GO and five real cases.

---

## 4. Ten-minute technical walkthrough

1. **Surfaces:** `miniapp/pages/start-claim` → FastAPI H5/customer commands → `accident_story_assistant` → Postgres events → Vercel Workbench Brief.  
2. **Graph:** `graph.py` nodes with resource limits (`flags.py`: max chars, ≤3 questions, timeout, retries).  
3. **Authority model:** `ai_proposed` vs `customer_confirmed`; broker UI copy encodes the rule.  
4. **Safety:** `guardrails.py` + master kill switch `ACCIDENT_STORY_ASSISTANT_ENABLED`.  
5. **Eval:** `evaluators.py` + `scripts/run_accident_story_langsmith_eval.py` → 20/20.  
6. **Canary:** `scripts/run_accident_story_qa_canary.py` on `fiqa-api-qa`, office `qa_canary_synth`.  
7. **Rehearsal:** `scripts/run_accident_story_five_case_rehearsal.py` — 5/5 local + QA.  
8. **Ops:** activation prep UNEXECUTED; kill switch runbook in Go/No-Go doc.  
9. **Diagrams:** `docs/architecture/SEARCHFORGE_SYSTEM_AND_AI_MAP_V1.md`.  
10. **Limits:** historical LangSmith immutable runs; no real-customer metrics yet.

---

## 5. Five resume bullets (honest)

- Designed a **bounded LangGraph** accident-story assistant that proposes structured claim facts with ≤3 follow-ups and **never mutates** claim lifecycle.  
- Enforced **human confirmation** and a three-layer broker Brief (original / AI proposal / confirmed) so unconfirmed AI cannot become office truth.  
- Built **pilot safety**: kill switches, office allowlists, deterministic fallback, and PII-redacted LangSmith tracing.  
- Closed **measurable release gates**: golden evals 20/20, Cloud QA live synthetic canary 20/20, five-case rehearsal 5/5 — classified as pilot-ready with restrictions, not Production.  
- Instrumented **durable Postgres metrics** for proposals, fallbacks, latency, and completion to support restricted-pilot scorecards.

---

## 6. Likely interview questions + honest answers

| Question | Honest answer |
|----------|---------------|
| Is this in Production? | **No.** Cloud QA restricted pilot posture only; Production/waterwoods untouched for Accident Story enablement. |
| Did real customers use it? | Guided Intake Founder phone validated. Live LLM canary and five-case rehearsal are **synthetic**. Chen activation not executed. |
| How accurate is the model? | Golden + synthetic canary strong; **real-customer accuracy unknown**. |
| Why LangGraph? | Bounded multi-step propose/validate/follow-up with clear node boundaries for tracing/eval — not an autonomous agent. |
| What if the LLM fails? | Timeout/invalid → deterministic/manual path; claim intake still works. |
| How do you prevent PII leaks? | Redaction allow-list, suppress auto-trace of raw story, clean pilot project, support tickets use refs not raw text. |
| What’s the business outcome? | Technical readiness for ≤5 real cases; **no proven revenue or hours saved**. |
| What would you do next? | Founder GO → real cases → then broker Request-More follow-up drafting (reuse stack), not a rewrite. |

---

## 7. Synthetic vs real (cheat sheet)

| Claim | Synthetic | Real / Founder |
|-------|-----------|----------------|
| Guided Intake UX | | Founder PASS |
| Deterministic Claim + Request More | | Founder PASS (Stage 1/2) |
| Golden evals 20/20 | Yes | |
| Live LLM canary 20/20 | Yes (QA allowlist) | |
| Five-case rehearsal | Yes | |
| Chen office real cases | | **Not started** |
| Production AI | | **No** |
| Paid conversion | | **No** |

---

## 8. Portfolio artifacts to open in interview

| Artifact | Path |
|----------|------|
| This master case | `docs/portfolio/SEARCHFORGE_FDE_MASTER_CASE_STUDY_V1.md` |
| Architecture diagrams | `docs/architecture/SEARCHFORGE_SYSTEM_AND_AI_MAP_V1.md` |
| Capability catalog | `docs/founder/SEARCHFORGE_REUSABLE_CAPABILITY_CATALOG_V1.md` |
| Gates | `docs/release/ACCIDENT_STORY_RESTRICTED_PILOT_GATES_V1.md` |
| Prior deep-dive | `docs/portfolio/FDE_CASE_STUDY_LANGGRAPH_GUIDED_INTAKE_V1.md` |
| 3-min demo script | `docs/portfolio/ACCIDENT_STORY_THREE_MINUTE_DEMO_SCRIPT_V1.md` |

---

## 9. Unresolved limitations (say these first if asked)

1. No real Chen traffic yet  
2. No Production deploy of Accident Story  
3. No verified ROI dollars  
4. Historical LangSmith cleanup debt (8 immutable synthetic runs)  
5. AI accept/edit/reject rates not fully instrumented  

Owning these limitations is part of the FDE story.
