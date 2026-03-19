# Case Handoff Mainline Blueprint

**Purpose:** Define the third mainline — **case handoff** — so product output feels like a real office handoff object, not scattered UI/debug surfaces.

**Scope:** Customer Entry, Broker Workbench, Simulation Assistant. No CRM, no auth, no new business flows.

**Created:** 2026-03-13 — Case Handoff Mainline Sprint

---

## A. Why Current Case Output Can Still Feel Scattered

| Issue | Where | Impact |
|-------|-------|--------|
| Important info split across multiple cards | Broker Workbench: "Case created" card + Case Report + "Where this case stands" + "What client should prepare" + "Draft" + "Full conversation" | Broker must scan 6+ boxes to understand the case |
| Case meaning not obvious at first glance | Customer Entry handoff: only shows last message text, no "what this case is" | User switches to Workbench without knowing case focus |
| "What changed" not prominent enough | Workbench: small "What changed recently" block only when follow_up_added | Easy to miss after append |
| Human confirmation not grouped tightly | Workbench: human confirmation at bottom of Case Report | Trust boundary can be overlooked |
| Handoff moment in Customer Entry not explicit | Customer Entry: "查看工作台" with no case summary | Feels like "send and forget" not "hand off" |
| Simulation Assistant Case Report missing case focus | Sim: no one-line summary, no case focus label | Demo/QA outcome less office-like |

---

## B. What a Good Office-Style Case Handoff Should Contain

| Order | Element | Purpose |
|-------|---------|---------|
| 1 | **Case focus** | Add car quote · Premium review · Missing document · Payment risk · Claim intake |
| 2 | **Status / readiness** | Ready for handoff vs Collecting info |
| 3 | **One-line handoff summary** | "Ready for handoff: Add car quote — Collect vehicle details, confirm delivery, then quote" |
| 4 | **Broker next move** | One operational sentence |
| 5 | **Human confirmation** (when needed) | Verify before acting: VIN, customer_says_sent, etc. |
| 6 | **Collected** | Green chips: what customer already provided |
| 7 | **Still needed** | Orange chips: what broker should ask or verify |
| 8 | **What changed recently** | After append: next move, collected, still needed refreshed |
| 9 | **Conversation / replay** | Secondary — for verification, not first scan |

---

## C. What Must Be Shown First vs Secondary

**First (above the fold, one scan):**
- What this case is (case focus)
- Whether it is ready (status)
- What to do next (broker next move)
- What to verify (human confirmation when present)

**Secondary:**
- Detailed replay / conversation
- Client prep, draft to send
- "Where this case stands" (tracking) — useful for reopened cases, not first scan

---

## D. Startup-Grade Target

- **Not** a full CRM
- **Just** clear enough that a small office can understand and act in under 10 seconds
- One strong primary handoff block; fewer separate conceptual boxes
- Same structure across Customer Entry handoff moment, Broker Workbench, Simulation Assistant

---

## E. Implementation Principles

1. **Merge, don't add:** Combine "Case created/reopened" status with Case Report into one handoff block.
2. **Case focus first:** Show case focus label before one-line summary in all surfaces.
3. **Human confirmation up:** Move human confirmation next to "Your next move" when present.
4. **What changed prominent:** When follow_up_added, surface "What changed recently" near the top of the handoff block.
5. **Customer Entry handoff moment:** Add case focus + one-line summary before "查看工作台".
6. **Simulation Assistant:** Mirror same handoff structure: case focus → status → one-liner → next move → human confirm → collected → still needed.

---

*See also: `docs/BROKER_HANDOFF_CLARITY_GUIDE.md`, `docs/LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md`*
