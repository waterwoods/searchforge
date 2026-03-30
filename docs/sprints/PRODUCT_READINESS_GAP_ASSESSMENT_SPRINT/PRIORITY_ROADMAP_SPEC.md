# Priority Roadmap Spec

**Audience:** Founder / operator  
**Horizon:** Next ~4–8 weeks of **highest ROI** work toward a **narrow paid pilot**  
**Date:** 2026-03-25

---

## Connection to business constraints

| Constraint | How this roadmap respects it |
|------------|------------------------------|
| **Charging a small office** | Prioritize **trust in first minute** + **credible case card** over new features |
| **Getting a pilot** | Close **launch/evidence** loop + **simple broker daily ritual** (paste → edit → handoff) |
| **Keeping product simple** | Prefer **mode clarity** and **copy discipline** over new modules |
| **Preserving hot-plug progress** | Batch **isolation fixes** that remove wrong-office and obvious engine leaks |

---

## Top priority now

1. **Customer Entry first impression + “narrow job” clarity (Goals 2, 12)**  
   - **Why:** Sellability and credibility in the first session; aligns UI with positioning docs already written.  
   - **Concrete direction:** Reduce ambiguity on Customer Entry; ensure top copy matches one-sentence offer; avoid looking like an internal ops console to a first-time broker.

2. **Handoff card truthfulness — fix or fence the known flagship inconsistency (Goals 3, 4)**  
   - **Why:** One visible contradiction on add-car can collapse trust in the structured fields.  
   - **Concrete direction:** Align `quote_ready` / `still_needed_fields` semantics **or** adjust UI labeling so brokers are not misled.

3. **Pilot operations closure — production URL / deploy checklist (Goal 8)**  
   - **Why:** Pre-broker acceptance explicitly left **Cloud Run + Vercel alignment** unproven in-session; pilots stall on logistics.  
   - **Concrete direction:** Run documented trial launch path; capture “known good” revision + frontend target.

---

## Important but not first

- **Targeted client-pack isolation debt (Goals 5, 6, 10):** Remove dangerous silent fallback where feasible; scrub remaining industry markers; continue externalizing high-visibility stitched strings **as touched by pilot pain**.  
- **Workbench polish for “office next action”** (Goals 3, 5): Improve scanability of next move + waiting_on without expanding scope.  
- **Persistence honesty pack (Goal 7):** Short founder note: backup JSON, limits, what “saved” means — reduces support risk.

---

## Later

- Broad second-broker **voice parity on every rare branch** (Goal 6) — after first paying pilot validates workflow.  
- Deeper DB architecture — only if pilot demands multi-user or hosting constraints appear.  
- Additional scenario packs beyond guardrail — after trial observations pinpoint real paste failures.

---

## Do not do yet

| Do not do | Why |
|-----------|-----|
| Build CRM/inbox sync | Violates narrow scope; high distraction |
| Stripe / multi-tenant | Explicit non-goal for v1 pilot |
| “Platform” features (analytics dashboards, heavy admin) | Undermines simplicity story before revenue proof |
| Aggressive cross-industry generalization | Same-industry replication is not finished **honestly** yet |
| Large UI framework rewrites | Poor ROI vs guided copy/mode work |

---

## “Next 3 sprints” recommendation sheet (summary)

| Order | Sprint theme | Primary goals |
|-------|--------------|---------------|
| 1 | **Service-entry clarity sprint** — Customer Entry shell, copy, optional “pilot mode” | 2, 12 |
| 2 | **Case card integrity sprint** — add-car semantic fix + broker-scannable handoff | 3, 4 |
| 3 | **Pilot launch + observation sprint** — deploy checklist, evidence capture, 2-week trial loop | 8 (+ 1, 11) |

*Rationale detail:* see `FINAL_REPORT.md` section 6.

---

*End of priority roadmap spec*
