# Scenario Logic Center Blueprint

**Sprint:** Scenario Logic Center Sprint  
**Created:** 2026-03-18  
**Purpose:** Explain why a logic center matters now, what this sprint will strengthen, and what it intentionally will not do.

---

## 1. Why a Logic Center Matters Now

The product has many important layers:
- common / industry / client configuration
- standard scenario package
- realistic simulation pack
- fix-now / fix-next / defer queue
- trial package
- trial kickoff flow
- client-aware UI wiring
- client-aware handoff / triage wiring
- client identity persistence across lifecycle

**The downside:** The founder and future reviewers risk losing the big picture. If the logic remains too distributed:
- leadership becomes harder
- broker review becomes harder
- future client migration becomes harder
- product evolution becomes slower and more fragile

**The founder's pain:** "We have many good parts now, but the logic is getting too spread out and harder to mentally hold."

---

## 2. Why This Is the Right Move After Configuration + Trial Prep

| Prior work | What it delivered |
|------------|-------------------|
| Configuration layer | Markers, reply templates, handoff phrases in config |
| Trial pack | Best 3–5 scenarios, order, value validation questions |
| Add-Car Rules Center | Editable add-car prompts; precedent for logic visibility |
| Fix-now queue spec | Observation → fix now / fix next / defer |

**Gap:** No single place shows *all* scenario logic as a system. The founder must mentally assemble from:
- `STANDARD_SCENARIO_PACKAGE.md`
- `MATURE_INTAKE_SKELETON.md`
- `inbox_triage_scenarios.json`
- `category_templates.json`
- `markers.json`
- `simulation_assistant_scenarios.json`
- `triage.py` (2500+ lines)

**This sprint:** Create a Scenario Logic Center that makes the system visible as a system.

---

## 3. What This Sprint Will Strengthen

1. **Founder clarity** — See top scenarios, what each does, what is strong/weak, at a glance
2. **Broker audit value** — Broker-side reviewers can understand what the system asks, when it hands off, what the broker gets
3. **Future client reuse** — Clear explanation of common / industry / client logic for A → B migration
4. **Reduced sprawl** — One place to start when planning, reviewing, or evolving

---

## 4. What This Sprint Intentionally Will NOT Do

| Not in scope | Why |
|--------------|-----|
| Full no-code rules platform | Overbuild; not needed for current leadership/review |
| Full rules editor | Add-Car Rules Center is precedent; we add *read-only* logic center first |
| Admin complexity | Keep it simple: view, understand, audit |
| Replacing existing docs | Logic center *references* and *aggregates*; docs remain source of truth |
| New business features | This is about visibility, not new flows |

---

## 5. Core Principle

**Do NOT build a giant no-code platform.**  
**Do NOT try to make a full rules editor.**  
**Do NOT overbuild admin complexity.**

This sprint is about: **a clear, readable, auditable, product-usable Scenario Logic Center.**

---

*See also: `02_SCENARIO_INVENTORY_SPEC.md`, `03_LOGIC_VISIBILITY_SPEC.md`, `04_SCENARIO_STATUS_HEALTH_SPEC.md`*
