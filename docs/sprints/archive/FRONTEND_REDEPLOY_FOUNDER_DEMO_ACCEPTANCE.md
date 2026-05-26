# Acceptance / SLA Criteria — Frontend Redeploy + Founder Demo Sprint

**Sprint:** Frontend Redeploy + Founder Demo + Top Feedback Fixes  
**Created:** 2026-03-14

---

## What must pass

| Criterion | Pass condition |
|-----------|----------------|
| Build | `cd ui && npm run build` exits 0 |
| Deploy | `vercel --prod` succeeds |
| Production alias | Production domain serves new deployment |
| Build info bar | Visible in header top-right; version, LA build time, build id, env readable |
| No layout breakage | Unified Intake page loads; no major visual break |

---

## What must be visible online

| Element | Expected |
|---------|----------|
| Direct customer voice | In CUSTOMER_ENTRY_EXAMPLES, QUICK_FILL_EXAMPLES, FOUNDER_DEMO_QUEUE |
| 不自动发送 | In draft card, PILOT_INTRO trust tag |
| Human confirmation wording | "Human confirmation recommended" when AI collected from conversation |
| Pilot intro | PILOT_INTRO Alert with value, trust, does, doesNot, demoPath |
| Simulation Assistant | 15 scenarios; Recommended trial, Real customer, Multi-turn, Edge cases |

---

## What counts as successful founder demo

- First impression good enough for small-client prospect
- Product feels believable
- Case handoff feels office-like
- Trust boundaries obvious (不自动发送, Human confirmation)
- Value proposition comes through
- At least one scenario run end-to-end without confusion

---

## What counts as top-priority issue worth fixing now

| Factor | Examples |
|--------|----------|
| Trust | Phrasing that undermines "broker in control" |
| First impression | Confusing entry, unclear value |
| Clarity | Ambiguous labels, wrong demo path |
| Sellability | Missing pilot offer, weak value story |
| Demo smoothness | Broken flow, wrong order, missing scenario |

**Must be:** Small, high-value, low-risk. No major refactors.

---

## What can be deferred

- Major UX redesign
- New features
- Backend changes
- Full scenario expansion
- Performance optimization
- Accessibility polish (unless blocking demo)

---

## Iteration log requirement

Every loop **must** answer:

1. What exactly changed?
2. What got better?
3. What did NOT get better?
4. Did anything get worse?
5. Was this loop worth it?
6. What is the best next step after this loop?

**No loop ends with just "deployed" or "demo completed."**
