# Acceptance / Reviewability Criteria

**Sprint:** Scenario Logic Center Sprint  
**Created:** 2026-03-18  
**Purpose:** Practical criteria for founder clarity, broker audit value, future client reuse.

---

## 1. Founder Clarity

| Criterion | Pass when |
|-----------|-----------|
| Top scenarios visible | Founder can list 7+ scenarios without opening code |
| Business goal clear | Each scenario has one-line business goal |
| Strong/weak visible | Maturity chip on each scenario |
| Fix-now/fix-next visible | If applicable, shown |

---

## 2. Broker Audit Value

| Criterion | Pass when |
|-----------|-----------|
| Broker next step visible | Each scenario shows what broker should do next |
| Handoff timing clear | When system hands off is understandable |
| Ask-next visible | What system asks before handoff is clear |

---

## 3. Future Client Reuse Explanation

| Criterion | Pass when |
|-----------|-----------|
| Common/industry/client visible | Config layer badge on each scenario |
| Config source visible | Expandable section shows file path |
| Hot-swap implication | Document explains: new client = new folder + handoff_phrases |

---

## 4. Reduced Project Sprawl

| Criterion | Pass when |
|-----------|-----------|
| Single entry point | One URL or doc index for scenario logic |
| No duplicate maintenance | Center aggregates; does not duplicate source configs |
| Links to sources | Expandable section links to markers.json, etc. |

---

## 5. What Remains Acceptable to Defer

- Full marker list in UI (link to file is enough)
- Last-changed timestamps (infer from sprints)
- Editable rules from logic center (Add-Car Rules Center remains separate)
- Simulation coverage counts (show badges only)

---

*See also: `07_FOUNDER_INSPECTION_NOTES.md`*
