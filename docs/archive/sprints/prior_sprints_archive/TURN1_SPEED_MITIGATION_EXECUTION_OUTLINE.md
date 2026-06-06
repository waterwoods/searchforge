# Turn 1 Speed Mitigation — Execution Outline

**Theme:** Turn 1 Actual Speed Mitigation

---

## Workstreams

| # | Workstream | Role | Deliverable |
|---|------------|------|-------------|
| 1 | Root-cause audit | Runtime/backend analyst | Latency breakdown: LLM vs cold start vs retrieval vs frontend |
| 2 | Option analysis | Cost/tradeoff analyst | 6 options with impact, effort, cost, recommendation |
| 3 | Tradeoff comparison | Product critic | Best quick win, best medium-cost, what to postpone |
| 4 | Optional implementation | Planner | Warmup helper or runbook step if clearly worthwhile |
| 5 | Validation | QA runner | Guardrail + scenarios + smoke check |

## What will be measured

- Turn 1 request path: frontend → POST /api/inbox/triage → triage_conversation → _llm_triage
- Cold start: Cloud Run idle → first request
- Retrieval: when triggered (notice/document confusion)
- Loading feedback: "正在整理 case..." present in Customer Entry + Simulation Assistant

## Decisions to make

1. Which 1–3 mitigations to implement now
2. Whether pre-demo warmup script is worth adding
3. Whether min_instances=1 cost is acceptable at current stage

---

*See: `docs/sprints/TURN1_SPEED_MITIGATION_ACCEPTANCE_CRITERIA.md`*
