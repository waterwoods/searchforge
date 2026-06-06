# Operator Value Spec — Small Office, Assistant, Front Desk

## Who benefits

- **Assistants and front-desk staff** who first see WeChat/email and must decide what to tell the broker.
- **Solo or family-run brokers** who context-switch between clients and need a **repeatable intake ritual**.
- **Anyone** who currently uses sticky notes, mental memory, or re-scrolling chat history to remember “what did we already ask?”

## Core operator value (what people are really paying for)

They are not buying “AI that runs the agency.” They are buying **less cognitive load at the handoff**:

1. **Time saved** — Less re-reading of long threads; structured fields surface **collected vs still needed** when the engine populates them reliably.
2. **Less back-and-forth** — Draft replies tuned to category reduce “write from zero”; broker edits instead of composing.
3. **Cleaner handoff** — One **broker_next_step** + case focus (“add car,” “missing doc,” “payment risk”) gives the producer a **starting point**, not a blank ticket.
4. **Fewer missed escalations** — Urgency + critical paths (cancellation, payment lapse) align with **same-day** office behavior when triage matches intuition.
5. **Better intake quality** — Multi-turn collection paths (when used) push toward **handoff-ready** information before the broker deep-dives.
6. **Works with manual completion** — The product is credible when the office still **enters the policy system**, calls the carrier, and sends the final message—the value is **upstream** of that work.

## What “good” looks like in the office (observable)

- Staff paste **5+ messages** in a session without abandoning the tool.
- **client_reply_draft** is **edited**, not thrown away—per `docs/UNIFIED_INTAKE_MVP_BOUNDARIES.md`.
- Broker says **“I would use this tomorrow”** after a short trial—not because it replaced AMS, but because **intake got faster and calmer**.

## Honest limitations (builds trust, not weakness)

- **LLM vs rules:** Quality and tone depend on configuration and model availability; guardrails and scenario packs exist because **regression matters**.
- **Demo vs ops:** MVP is still framed as **demo-safe work surface** in boundaries docs; production hardening is a **separate** claim from positioning.
- **Portability:** Second-broker drill showed **voice** can swap via client pack for many paths, but **engine-resident strings** still exist—hot-plug is **in progress**, not a finished “any broker in one click” story.

## Messaging principle for operators

Sell **calm handoffs and fewer fire drills**, not **full automation**.

---

*Evidence: `docs/STANDARD_SCENARIO_PACKAGE.md` (workbench as part of package), `docs/UNIFIED_INTAKE_MVP_BOUNDARIES.md`, `services/fiqa_api/inbox_triage/triage.py` (categories, workflow keys).*
