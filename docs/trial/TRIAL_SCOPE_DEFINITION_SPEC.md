# Trial Scope Definition Spec

**Sprint:** Real Broker Trial Package Sprint  
**Created:** 2026-03-18

---

## 1. Trial Package Name

**Real Broker Trial Package** (or **Chen Kui 1-Week Pilot** for client-specific use)

---

## 2. Target Broker Profile

- **Primary:** California auto insurance brokers serving Chinese-speaking clients
- **Office size:** 1–5 people
- **Channels:** WeChat, email as primary; manual copy-paste into system
- **Pain:** Manual triage, repeated explanations, missed follow-ups

---

## 3. Target Use Case

**Unified Intake + Broker Workbench:** Paste inbound customer messages → structured case → broker next move → draft reply. Broker reviews and sends; no auto-send.

---

## 4. Trial Duration

**1 week** (5 business days). Can extend to 2 weeks if broker requests.

---

## 5. Included Product Surfaces

| Surface | Included | Notes |
|---------|----------|-------|
| Customer Entry (paste box) | ✅ | Primary entry; multi-turn conversation |
| Case handoff card | ✅ | Case focus, next move, Collected, Still needed |
| Broker Workbench | ✅ | Queue, status, follow-up, reopen |
| Load founder demo queue | ✅ | Seeds 13 demo cases for trial |
| Simulation Assistant | ✅ | 15 trial scenarios for broker to try |
| Copy to client | ✅ | Copy draft to clipboard for WeChat/email |

---

## 6. Included Scenario Types

| # | Scenario | Why included |
|---|----------|--------------|
| 1 | Cancellation risk / payment failed | Urgency, same-day action; highest "must act" value |
| 2 | Missing document / already sent | Operational pain; verification clarity |
| 3 | Add-car quote | Revenue; multi-turn; Collected chips |
| 4 | Premium review / renewal | Retention; repetitive office work |
| 5 | Claim intake | First-response guidance; robustness |
| 6 | Billing clarification | Payment risk; same-day action |
| 7 | Talk to Agent / case handoff | Customer wants human; broker takes over |

---

## 7. Excluded / Deferred

- Email/WeChat/SMS integration
- OCR upload
- Full CRM
- Multi-tenant
- Stripe billing
- Carrier API integration
- DMV/SR-22 deep-dive (unless broker asks)

---

## 8. What "Good Enough for Trial" Means

1. **Broker can paste** a real or simulated message and get a structured case
2. **Broker sees** Case focus, Your next move, Collected, Still needed
3. **Broker can** reopen cases, update status, save follow-up, add notes
4. **Broker gets** a draft to edit (not write from scratch)
5. **No auto-send** — broker stays in control
6. **Guardrail passes** — scenario pack, multi-turn, adversarial, simulation assistant

---

*End of Trial Scope Definition Spec*
