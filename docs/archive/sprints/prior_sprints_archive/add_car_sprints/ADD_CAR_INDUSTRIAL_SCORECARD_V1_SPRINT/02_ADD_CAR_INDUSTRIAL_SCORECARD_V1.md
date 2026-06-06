# Add-Car Industrial Scorecard V1

## 1. Scorecard definition (four skeletons)

| Skeleton | What “good” means for Add-Car |
|----------|-------------------------------|
| **PAGE** | Clear hierarchy: obvious that **加车报价** is the flagship path; one primary action; minimal demo noise; purpose reads as **报送 / 业务记录**, not “chat with AI”. |
| **FLOW** | User experiences **one task** (add vehicle quote intake) with understandable steps: start → clarify/supply info → submit to office; **same record vs new issue** is explicit after handoff. |
| **STATE** | **Case** reads like a record: quote readiness, collecting vs ready-to-handoff, office processing; missing fields and status are **scannable** (chips/cards, not only prose). |
| **HANDOFF** | Customer feels **received**; office next steps and timing are credible; **already sent / materials** situations feel natural; continuity (append vs new thread) feels trustworthy—not hollow bot closure. |

## 2. Scoring scale (1–5)

| Score | Meaning |
|-------|---------|
| **1** | Demo-like or unreliable; undermines pilot trust. |
| **2** | Emerging; inconsistent across turns or surfaces. |
| **3** | **Meaningful product shape**—usable for constrained pilot with known caveats. |
| **4** | **Strong pilot-grade**—credible to a broker with minimal apology. |
| **5** | Polished small-business industrial product (most dimensions would exceed current backend/ops reality). |

**Rule:** Default conservative; **5 is rare** without production-grade persistence, auth, and ops integration.

## 3. Current scores (Add-Car path, rule/guardrail-aligned behavior)

| Dimension | Score | One-line rationale |
|-----------|-------|-------------------|
| **PAGE** | **4 / 5** | Add-Car-first hero, empty-state guidance, recommended quick-start, structured intake card, compact in-session chrome, and flow track show deliberate page discipline; pilot alert + simulation + six intents still add noise. |
| **FLOW** | **3 / 5** | Three-step track and transaction ribbon frame the task, but the **center of gravity is still conversational turns**; “one task” is supported more by labels than by a non-chat interaction model. |
| **STATE** | **3 / 5** | Progress card, `AddCarCaseStatusStrip`, collected/still-needed fields, and handoff result card move toward ticket-like clarity; **full legibility still depends on triage populating fields**, and workbench queue parity for record ID/status is thinner than customer side. |
| **HANDOFF** | **3 / 5** | Rich configurable closure (headline, processing line, received summary, timing copy, boundary hints, same-case append) is strong; **system reply tone/length, acknowledgement echo, and `already_sent` behavior** still risk sounding procedural or repetitive per simulation audit. |

## 4. Evidence pointers (repo)

- **PAGE / FLOW / STATE / HANDOFF UI:** `ui/src/pages/UnifiedIntakePage.tsx` — hero, `IntakeFlowStepTrack`, Add-Car transaction card, progress + result cards, post-handoff collapse, closure copy wiring, append-to-same-record.
- **Copy defaults:** `ui/src/api/clientConfig.ts` — portal + handoff + Add-Car keys.
- **Product boundaries:** `docs/PROJECT_TRUTH_SWITCH.md`.
- **Recent sprint outcomes:** e.g. `ADD_CAR_FIRST_PILOT_CLOSING_SPRINT`, `FRONTEND_INDUSTRIALIZATION_SPRINT`, `ADD_CAR_RESULT_CARD_STATUS_FLOW_HARDENING_SPRINT`, `ADD_CAR_FIRST_WORKBENCH_ECHO_BROKER_DRY_RUN_SPRINT`, `ADD_CAR_REALISTIC_NA_CHINESE_SIMULATION_AUDIT_SPRINT` final reports.

## 5. Major gaps (what blocks “next level”)

### PAGE → 5

- Remove or **re-home persistent demo affordances** (e.g. collapse pilot alert after first successful handoff—already noted as follow-up in industrialization report).
- Reduce **parallel entry surfaces** competing for attention on first paint (six intents + structured form + examples + simulation)—pilot could narrow harder for customer-facing production.

### FLOW → 4

- Make the **dominant metaphor** closer to “guided intake task” than “thread,” without a full rewrite (e.g. stronger step ownership, less dependence on bubble history for understanding “where I am”).

### STATE → 4

- Ensure **workbench** list/header shows the same **record id + status strip** affordances as customer closure (result-card sprint and workbench echo reports both flagged parity gaps).
- Harden **backend consistency** so `lifecycle_status` / `broker_next_step` are populated on all Add-Car paths customers actually hit.

### HANDOFF → 4

- **Reply polish:** shorter acknowledgements, punctuation/tone cleanup, `already_sent` behavior when vehicle context is already complete (per realistic simulation audit).
- Optional: **LLM-on** spot-check separate from rule path guardrails.

## 6. What “next level” looks like (target picture)

- **PAGE:** Single unmistakable flagship lane for pilot customers; demo tools invisible or operator-only.
- **FLOW:** User can describe progress in one sentence without referring to “messages.”
- **STATE:** Customer and office see the **same case identity and state** at a glance.
- **HANDOFF:** Closure and follow-up replies read like a **careful human desk**, not a long system echo.
