# Next Task — LangSmith Tracing + Golden Dataset + Evaluators

**Prerequisite:** Guided Intake UX V1 phone QA PASS (`docs/portfolio/FDE_CASE_STUDY_LANGGRAPH_GUIDED_INTAKE_V1.md`)  
**Do not start** until the dynamic-question customer experience is visibly proven on phone.  
**Scope:** QA / lab only — Production and waterwoods untouched.
**Status:** Implemented on `stage2/langsmith-tracing-golden-evals` — see `docs/evidence/langsmith-pr-b/`.

---

## Exact objective

Add LangSmith tracing and a golden evaluation dataset for the bounded accident-story LangGraph so regressions are caught before Founder phone QA.

---

## Deliverables

### 1. Trace boundaries (every graph node)

Instrument (or wrap) each node with a stable run name:

| Node | Trace name |
|------|------------|
| normalize_story | `accident_story.normalize_story` |
| extract_fact_proposals | `accident_story.extract_fact_proposals` |
| validate_proposals | `accident_story.validate_proposals` |
| derive_missing_facts | `accident_story.derive_missing_facts` |
| draft_followup_questions | `accident_story.draft_followup_questions` |
| apply_safety_guardrails | `accident_story.apply_safety_guardrails` |
| build_customer_confirmation_proposal | `accident_story.build_confirmation_proposal` |

Root run metadata (stable keys only):

- `assistant=accident_story_langgraph_v1`
- `schema_version`
- `proposal_version`
- `used_fallback`
- `fallback_reason_category`
- `question_count`
- `missing_count`
- `model_provider` / `model_name`
- `command_id_prefix` (never full raw story)

Reuse existing helper if present: `services/fiqa_api/observability/langsmith_tracing.py` (lab-safe, no-op when unset).

### 2. Redaction rules

**Never send to LangSmith inputs/outputs/metadata:**

- Full raw accident story text
- Customer phone / name / OpenID
- Resume tokens / session secrets
- Photo URLs or file paths

Allowed: hashed case_id prefix, field keys, missing key lists, question count, injury enum (`yes|no|unknown`), boolean flags, latency_ms, model ids.

If a node must log text for debug, store only **length + language hint**, not content.

### 3. Golden fixtures (15–20)

Expand `tests/fixtures/accident_story_langgraph/` to 15–20 JSON fixtures. Each fixture must declare:

```json
{
  "id": "missing_time_location_injury_known",
  "raw_story": "...",
  "expect": {
    "extracted": {
      "injury_status": "no",
      "accident_type": "追尾"
    },
    "missing_contains": ["accident_datetime", "accident_location"],
    "missing_excludes": ["injury_status"],
    "max_followup_questions": 2,
    "conflicts": [],
    "fallback": false
  }
}
```

Suggested coverage:

1. Complete story → 0 questions  
2. Missing time+location, injury known → 2 questions  
3. Missing injury only → 1 question  
4. All three missing → max 3  
5. Injury conflict → conflict flagged  
6. Explicit 没有受伤  
7. Uncertain injury  
8. Invalid model JSON → fallback  
9. Timeout → fallback  
10. Hallucinated field rejected  
11. English rear-end story  
12. Parking-lot location only  
13. Vague 昨天 time refinement  
14. Customer-edit override (service-level)  
15. Unconfirmed non-authority  
16–20. Edge: empty story, very long story, mixed CN/EN, side-swipe, no location preposition

### 4. Evaluators

LangSmith / offline evaluators (pass/fail):

| Evaluator | Rule |
|-----------|------|
| `max_questions_le_3` | `len(followup_questions) <= 3` |
| `missing_matches_expect` | expected keys ⊆ missing; excludes absent |
| `no_silent_injury_no` | never coerce unknown → no |
| `conflict_not_resolved` | if conflict fixture, conflicts non-empty and injury unknown |
| `fallback_on_bad_llm` | used_fallback true; proposal still usable |
| `guided_view_present` | `guided_view.followup_fields` length == question count |
| `no_pii_in_trace_meta` | meta keys ⊆ allow-list |

### 5. CI / gate sketch

```bash
PYTHONPATH=. python3 -m pytest tests/test_accident_story_langgraph.py -q
# Optional when LANGCHAIN_API_KEY set:
PYTHONPATH=. python3 scripts/run_accident_story_langsmith_eval.py --dataset accident_story_v1
```

Fail the PR if any golden expect fails. Tracing must remain optional (no key → local evaluators only).

---

## Out of scope for that PR

- Changing Cap2 lifecycle  
- Production deploy  
- Replacing deterministic Start Claim validation  
- Storing raw stories in LangSmith datasets without redaction review  

---

## Success gate

- 15–20 fixtures green locally  
- Node-level traces visible in LangSmith when key configured  
- Redaction checklist signed in PR  
- Guided Intake phone QA already PASS  

**Stop when PASS.** Do not auto-start broker analytics or multi-scenario voice work.
