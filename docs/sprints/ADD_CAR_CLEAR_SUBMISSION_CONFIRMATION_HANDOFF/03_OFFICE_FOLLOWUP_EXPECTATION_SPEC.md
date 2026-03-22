# Office Follow-Up Expectation Spec

## Purpose

Make **waiting** feel operationally real: office has the case, work happens in **business time**, response is **likely within a bounded window**—without guarantees that create liability.

## Wording rules

1. **No false precision** — Prefer “一至两个工作日” / “one to two business days” over exact hours.
2. **Holiday / weekend caveat** — Explicitly allow extension (“周末及公共假期顺延”).
3. **Separate from broker draft** — Timing lives primarily in **UI copy** so founders can tune without changing triage logic.
4. **Align with handoff phrase** — `handoff_phrases.add_car` should not contradict the UI timing line; both may reference business-day processing.

## Placement

- Customer closure card: **office expectation banner** after “received snapshot,” before or adjacent to “办公室回复摘要” (implementation: banner before reply summary for scan order: submit → confirm → wait → read reply).

## Broker alignment

- Workbench urgency / `getResponseWindow` unchanged this sprint; customer copy is **additive**.
