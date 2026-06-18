# P16 Visibility Rule Design

**Principle:** Smallest UI-only change. No scoring redesign, no DB/API/triage edits.

---

## Rule A — Recent customer formal submission boost

**When all true:**

1. `formal_submitted_at` within last **24 hours** (`isWithinLast24Hours`)
2. `lifecycle_status` ∈ `{ handed_off, office_followup }`
3. Not `workbench_test`

**Then:** add **`+165`** to `getCaseWorkbenchScore()`.

**Constant:** `RECENT_FORMAL_SUBMISSION_VISIBILITY_BOOST = 165`

**Rationale:**

- Fresh handed-off add-car parked cases score ~8; boost → ~173.
- Beats founder demo seeds at 150–175 **without** `formal_submitted_at`.
- Stays below critical/high same-day cancellation (180) and high payment-fail due today (175).

---

## Rule B — Founder demo seed deprioritization

**When:** `source_text` matches a `FOUNDER_DEMO_QUEUE` seed (normalized text compare)  
**And:** not `workbench_test`

**Then:** subtract **`300`** from workbench score.

**Constant:** `FOUNDER_DEMO_SEED_WORKBENCH_PENALTY = 300`

**Rationale:**

- Demo seeds are training noise in product-only pilot.
- Real customer messages never match seed text exactly.
- Demos drop to bottom (score ≈ −125) without hiding real cancellation/payment cases.

---

## Sort order (unchanged structure)

```typescript
orderCasesForWorkbench(cases):
  sort by getCaseWorkbenchScore DESC
  tie-break: updated_at DESC
```

No new lanes, filters, or API parameters.

---

## Explicit non-goals

| Out of scope | Reason |
|--------------|--------|
| DB schema / persistence | Certified healthy |
| API sort change | Server order already correct |
| Triage / append / binding | Sprint boundary |
| New workbench filters | Scope guard |
| Rescore all urgency semantics | Not a triage sprint |

---

## Observability

`explainCaseWorkbenchScore(case)` returns component breakdown for audits and simulations.

---

## Design sign-off

| Criterion | Met |
|-----------|-----|
| Recent submit outranks demo noise | Yes |
| Urgent cancel/pay stay on top | Yes |
| ≤30 lines effective logic | Yes |
| UI-only | Yes |
