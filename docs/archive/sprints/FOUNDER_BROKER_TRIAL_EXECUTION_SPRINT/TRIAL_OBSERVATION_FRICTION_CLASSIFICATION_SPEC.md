# Trial Observation / Friction Classification Spec

**Sprint:** Founder / Broker Trial Execution Sprint  
**Created:** 2026-03-20

---

## 1. How to record observations

For each scenario run, capture:

| Field | Content |
|-------|---------|
| Scenario ID | e.g. S3 Add-car + materials sent |
| Surface | Customer entry / Workbench / API-only |
| What happened | 2–4 bullets, factual |
| Backbone | Page / Flow / State / Handoff (tag one or more) |
| Broker one-liner | “If I were the broker, I would…” |

Store in sprint notes or `TRIAL_OBSERVATION_LOG_TEMPLATE` (`docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md`) if extending a live trial.

---

## 2. Classification buckets

| Bucket | Definition |
|--------|------------|
| **Fix-now** | Blocks trial, breaks trust, or causes wrong office action; small safe fix available |
| **Fix-next** | Real friction; broker would grumble; not blocking a serious review |
| **Acceptable-for-trial** | Imperfect but explainable in a 30-second caveat |
| **Defer** | Out of scope, expensive, or needs product strategy |

---

## 3. Trust-breaking (fix-now candidates)

Examples:

- Customer sees internal jargon or empty “next step.”
- `handoff_ready` or persistence behavior contradicts the UI (e.g. “saved” but no case).
- Urgency mismatch on cancellation/payment (low urgency on last notice).
- Workbench cannot answer “what do I do next?” in 10 seconds.

---

## 4. Acceptable-for-trial

Examples:

- Minor wording variance between EN/ZH templates.
- One extra click to copy draft.
- Occasional redundant field in `still_needed_fields` if broker_next_step clarifies.

---

## 5. Anti-patterns

- **Overreact:** Fixing every cosmetic issue.  
- **Underreact:** Dismissing “confusing quote-ready” or “append didn’t update case” as minor.  

---

*End of Spec*
