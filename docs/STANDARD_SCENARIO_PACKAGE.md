# Broker Standard Scenario Package

**Purpose:** Single canonical definition of the sellable standard scenario package for small auto insurance brokers. Use this when explaining the product to Chen Kui or another prospect.

**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Package Name

**Broker Standard Package** (or **Chen Kui Broker Standard Package** for client-specific use)

**What it is:** Chat + case + office follow-up. Not just chat. The package delivers: (1) Customer Entry — paste message, multi-turn collection; (2) Case handoff — structured case with next move, collected, still needed; (3) Broker Workbench — queue, status, follow-up memory, reopen context.

---

## 2. One-Sentence Offer

试用一个月：帮你把客户发来的messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。

---

## 3. Target User

- California auto insurance brokers serving Chinese-speaking clients
- Small office (1–5 people); manual triage; WeChat/email as primary channels

---

## 4. Included Scenarios (7 Core)

| # | Scenario | Business value |
|---|----------|----------------|
| 1 | **Quote / Add-car** | New vehicle quote; revenue; high-frequency |
| 2 | **Policy change (add/remove)** | Add/remove vehicle; routine |
| 3 | **Material collection / already sent** | Missing document; client says already sent; common pain |
| 4 | **Renewal increase / premium review** | Premium too high; retention |
| 5 | **Billing clarification** | Payment failed; cancellation risk; same-day action |
| 6 | **Claim first notice** | Accident; hit-and-run; first-response guidance |
| 7 | **Talk to Agent / case handoff** | Customer wants human; broker takes over |

---

## 5. What the Broker Gets

- One paste → structured case
- One next move per case
- One draft to edit (not write from scratch)
- Lightweight follow-up memory (waiting on, next contact)
- No auto-send; broker stays in control

---

## 6. What the Office Gets (Part of the Package)

**The workbench is not an add-on — it is part of the standard package.** When a case is handed off, the broker gets:

| Item | What it means |
|------|---------------|
| **Case focus** | Add car quote · Premium review · Claim intake · Missing document · Payment risk |
| **Your next move** | One operational sentence: what the office should do next |
| **Collected** | Green chips: what the customer already provided (avoid re-asking) |
| **Still needed** | Orange chips: what the broker should ask or verify next |
| **Client reply draft** | Editable; broker confirms before sending; no auto-send |
| **Queue triage** | Work now / Waiting or parked; urgency; readiness |
| **Follow-up memory** | waiting_on, next_contact_by, broker note — no lost follow-ups |
| **Reopen context** | "Resume here" with waiting on + latest note when reopening a case |

**How this reduces manual follow-up:** One paste → structured case. One next move. One draft to edit. Lightweight status + follow-up target. Broker stays in control.

---

## 7. Not Included (Deferred)

- Email/WeChat/SMS integration
- OCR upload
- Full CRM
- Multi-tenant
- Stripe billing
- Carrier API integration

---

## 8. Best Demo Path

1. Load founder demo queue
2. Cancellation risk (opens first)
3. Reopen missing document from Recent cases
4. Reopen add-car quote or premium review
5. Simulation Assistant: SIM1 → SIM2 → SIM3

---

## 9. Founder Demo Checklist (5–10 min)

| Step | Action |
|------|--------|
| 1 | Open `/workbench/unified-intake` |
| 2 | Click **Load founder demo queue** |
| 3 | Cancellation risk case opens first — show urgency, same-day action |
| 4 | Reopen **missing document** from Recent cases — show operational follow-up |
| 5 | Reopen **add-car quote** or **premium review** — show Collected chips |
| 6 | Optional: Simulation Assistant → SIM1 → SIM2 → SIM3 |

**What to say:** "This is the Broker Standard Package. One paste → structured case. One next move. One draft to edit. The workbench is part of the package. No auto-send."

---

## 10. Related Docs

- `docs/CHEN_KUI_TRIAL_PACK.md` — Trial scenarios, value validation questions
- `docs/UNIFIED_INTAKE_MVP_BOUNDARIES.md` — Business value, boundaries
- `docs/sprints/SELLABLE_STANDARD_SCENARIO_PACKAGE/` — Full sprint spec
- `docs/sprints/STANDARD_SCENARIO_PACKAGE_2/` — **Package 2.0** — deepened handoff, broker_next_step verify guidance

---

*End of Standard Scenario Package*
