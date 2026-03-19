# Real Broker Trial Package Blueprint

**Sprint:** Real Broker Trial Package Sprint  
**Created:** 2026-03-18  
**Purpose:** Explain why a real broker trial package matters now and what this sprint will strengthen.

---

## 1. Why a Real Broker Trial Package Matters Now

The product has evolved from demo → sellable package → scenario hardening. The next step is **operationalization**: turning the strongest capabilities into something a real broker can actually use for a 1-week pilot.

**Current state:**
- Customer Entry, multi-turn continuity, workflow_state, case creation/handoff, workbench are implemented
- Standard Scenario Package (7 scenarios) is defined
- Chen Kui Trial Pack defines best 3–5 trial scenarios and value validation questions
- Simulation Assistant has 15 trial + 8 real-customer scenarios
- Guardrails and validation scripts exist

**Gap:** The product is organized around *demo* and *scenario validation*, not around *real trial use*. A broker cannot yet answer: "What exactly am I trialing? What do I do each day? What counts as success?"

---

## 2. Why This Is the Correct Move Now

| Prior step | Outcome |
|------------|---------|
| Package definition | STANDARD_SCENARIO_PACKAGE.md, 7 scenarios |
| Scenario hardening | inbox_triage, multi-turn, adversarial, simulation assistant pass |
| Chen Kui trial pack | Best 3–5 scenarios, value validation questions, trial checklist |

**Next logical step:** Define a **Real Broker Trial Package** — a coherent, bounded package that:
- A broker can understand in 5 minutes
- A founder can pitch in one sentence
- Has clear setup, workflow, and success criteria
- Does NOT expand scope into a giant platform

---

## 3. What This Sprint Will Strengthen

1. **Trial package clarity** — One canonical definition: what the broker is trialing, which scenarios, what they experience
2. **Broker workflow** — How the broker uses the system daily during trial
3. **Metrics / observations** — What to measure and record during trial
4. **Setup / checklist** — What must be true before trial starts
5. **Founder pitch** — How to explain and demo the trial

---

## 4. What This Sprint Will NOT Do

- Add new features beyond trial-readiness
- Build email/WeChat/SMS integration
- Add Stripe, multi-tenant, auth
- Improve docs without improving trial-readiness
- Expand into other verticals

---

## 5. Success Definition for This Sprint

At the end of this sprint:
- A founder can hand a broker a single document set that defines the trial
- The broker knows what to do, what to expect, and what success looks like
- The product changes are minimal and focused on packaging, not new features

---

*End of Blueprint*
