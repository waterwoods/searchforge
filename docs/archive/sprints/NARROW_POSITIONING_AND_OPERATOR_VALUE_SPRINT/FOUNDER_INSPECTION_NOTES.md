# Founder Inspection Notes — Decisions & Wording

## 1. If we had to sell this next month, what exact version?

**Sell:** “Paste-based **Unified Intake + Broker Workbench** for one small CA auto office—**7 high-frequency scenarios**, structured case card, one next step, editable client draft, **no auto-send**.”  
**Do not sell:** CRM, carrier integration, OCR, multi-tenant SaaS, full agency automation.

## 2. Wording for Chen Kui (陈奎)

- **Chinese one-liner (from standard package):** 试用一个月：帮你把客户发来的messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。
- **English backup:** “We turn messy client messages into a structured case with next step and draft reply—you review before anything goes out.”
- **Tone:** Partner at the **front door**, not replacement for his judgment or carrier workflows.

## 3. What not to claim yet

- Inbox **connected** to WeChat/email automatically.
- **Screenshot** reading / OCR.
- **Automatic** outbound messages.
- **Full customer history** or policy data from AMS.
- **Instant** hot-plug for arbitrary brokers **without** config work—say **“same-industry pack + setup”** until audits are clean.

## 4. Next product / UI sprint should optimize for

- **Clarity of the narrow job** on first screen (paste → case → handoff), not feature breadth.
- **Operator speed:** fewer clicks from paste to “what do I tell the client?”
- **Honest labels** for demo vs production-ready surfaces if any UI still feels demo-only.

## 5. Next engineering sprint should optimize for

- **Client-pack isolation** where second broker drill still flags leaks (engine strings, defaults, industry markers with broker names).
- **Regression safety:** guardrails + A/B batteries green on every merge touching triage.
- **Not:** carrier APIs, multi-tenant auth, giant refactors.

## 6. Most important thing to keep simple

**One entry, one case shape, human approval on outbound.** Everything else is optional depth.

---

*Cross-check: [SCOPE_BOUNDARY_SPEC](./SCOPE_BOUNDARY_SPEC.md), [PRODUCT_POSITIONING_SPEC](./PRODUCT_POSITIONING_SPEC.md).*
