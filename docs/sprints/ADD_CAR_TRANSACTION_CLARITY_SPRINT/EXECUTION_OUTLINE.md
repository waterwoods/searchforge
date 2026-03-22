# Execution Outline — Add-Car Transaction Clarity Sprint

## Phase A — Control docs (this folder)

1. Blueprint, title spec, progress/handoff spec, customer UX, workbench spec.  
2. Founder scenario pack JSON + runner script.  
3. Acceptance criteria + founder inspection notes.  
4. Final report (after implementation).

## Phase B — Roles (conceptual)

| Role | Work |
|------|------|
| Product / planner | Blueprint + acceptance |
| Transaction-boundary analyst | Detection rules + boundary copy |
| UX / copy | `ui_copy.json` + handoff card structure |
| Rule / triage | `handoff_phrases.json` + `triage.py` edge strings |
| UI | `UnifiedIntakePage.tsx` |
| QA | Guardrail, `npm run build`, scenario runner |

## Phase C — Loops

1. **Audit** — Read customer entry, triage handoff, workbench tags; answer required audit questions (in final report).  
2. **Loop 1** — Transaction title: ribbon + progress title + composer label.  
3. **Loop 2** — Closure: handoff card layers + toast + phrase updates.  
4. **Loop 3** — Founder pack + guardrail + build + judgment.  
5. **Loop 4** — Skip unless a one-line high-ROI fix remains (none planned).

## Time budget

Target 45–90 minutes: favor one strong pass over speculative refactors.
