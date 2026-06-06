> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/BROKER_ONE_PAGER.md`](../../../BROKER_ONE_PAGER.md), [`docs/DEMO_STORY.md`](../../../DEMO_STORY.md), [`docs/BROKER_TRIAL_PLAYBOOK.md`](../../../BROKER_TRIAL_PLAYBOOK.md)

# Chen Kui Trial Pack + Value Validation

**Purpose:** Package the current system into a practical trial that highlights the strongest 3–5 business scenarios, clarifies value, and helps the founder learn what Chen Kui would actually use and pay for.

**Created:** 2026-03-12 — Chen Kui Trial Pack + Value Validation Sprint

---

## 1. Trial Purpose

### What the founder wants to learn

- Does the system collect customer information well enough for real office use?
- Does the structured case output help the broker move faster?
- Which parts feel trustworthy vs risky to Chen Kui?
- What would he use daily? What would he pay for first?

### What Chen Kui should understand after trying it

- The system turns messy inbound messages into one structured case with urgency, next step, and a draft reply.
- The broker stays in control; nothing is auto-sent.
- Collected / Still needed chips show what the AI extracted from the conversation.
- "Human confirmation recommended" appears when AI collected data the broker should verify.

### What "trial success" means

- Chen Kui can see: customer message → system response → structured case → broker next move.
- He can answer: "Which scenario felt most useful?" and "Which part still feels risky?"
- He understands what the product does and does not do.

### What "trial failure" means

- He cannot understand what the system does.
- He finds the flow confusing or the output unreliable.
- He cannot tell what would happen in his real office.

### What should NOT be expected from the trial yet

- Inbox sync, email/WeChat integration, OCR upload
- Full CRM, carrier integration, multi-tenant
- Automated billing or Stripe

---

## 2. Best 3–5 Trial Scenarios (3–4 turn deep)

| # | Scenario | Turns | Why in trial | Business value |
|---|----------|-------|--------------|----------------|
| 1 | **Cancellation risk** | 3 | Urgency, same-day action; most obvious "must act" value | Proves urgency + clarification + broker handoff |
| 2 | **Missing document** | 3 | Operational, "client says already sent" — real office pain | Proves structured follow-up + verification clarity |
| 3 | **Add-car quote (Chinese)** | 3 | Revenue, multi-turn, Collected chips | Proves multi-turn quote collection; handoff at turn 3 |
| 4 | **Premium review** | 3 | Retention, repetitive office work | Proves retention-style follow-up |
| 5 | **Claim intake** | 3 | First-response guidance; robustness | Proves accident + hit-and-run + collected/still-needed |

---

## 3. Best Trial Order

### Best 3-scenario order (short trial)

1. **Cancellation risk** — first (urgency, same-day)
2. **Missing document** — second (operational follow-up)
3. **Add-car quote** — third (revenue, multi-turn, Collected)

### Best 5-scenario order (full trial)

1. Cancellation risk
2. Missing document
3. Add-car quote
4. Premium review
5. Claim intake

### Start with first

**Cancellation risk.** It is urgent, clear, and immediately shows "same-day action" and "Broker action required."

### Avoid leading with

- Generic vague question; DMV/SR-22 (unless Chen Kui asks); complex mixed-intent (save for later)

---

## 4. Trial Usability Review

| Area | Status | Notes |
|------|--------|-------|
| Customer Entry tab | **Strong** | Clear input, same-page conversational flow |
| Case focus | **Strong** | Case focus tag at top; queue shows case focus first |
| Your next move | **Strong** | One operational sentence, bold |
| Collected / Still needed | **Strong** | Green/orange chips for add-car, renewal, claim, missing-doc |
| Human confirmation badge | **Good** | Gold tag, visible when AI collected from conversation |
| Simulation Assistant | **Good** | 15 scenarios; clear Run/Next turn/Reset; evaluation tags; replay shows Collected/Still needed/Human confirmation per turn |
| Queue triage | **Good** | Work now / Waiting or parked; Ready to act / Needs more info / Verify receipt badges |
| Founder demo queue | **Good** | Load founder demo queue seeds 13 cases; cancellation opens first |

**Verdict:** Trial usability is **good to strong.** The product makes the chosen scenarios easy to follow. No major polish required for trial clarity.

---

## 5. Value Validation Questions (Post-Trial)

Ask Chen Kui after the trial:

1. **Which scenario felt most useful to your office?** (Reveals what he values most.)
2. **Which part still feels risky or not trustworthy?** (Reveals trust concerns.)
3. **Would this save you or your assistant time?** (Reveals time-saving perception.)
4. **What would you want it to do next?** (Reveals next feature priority.)
5. **What would you be willing to try first in a pilot?** (Reveals what he would pay for.)

---

## 6. Pilot Value Story

### What we are selling first

Unified Intake + Broker Workbench: faster triage, structured cases, draft replies, lightweight follow-up memory. Not a full CRM. Not automation of external systems.

### What value it creates first

- Less manual triage
- Fewer repetitive explanations
- Clearer next steps
- No lost follow-ups

### What we are NOT promising yet

- Full CRM, inbox sync, carrier integration
- Multi-tenant, auth, Stripe billing

### Why a small office would use this before a giant platform

Built for this niche (Chinese-speaking CA auto insurance). Rules + retrieval + human-backed. No enterprise bloat. Fast to pilot.

### One-sentence pilot offer

"试用一个月：帮你把客户发来的messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。"

---

## 7. Practical Chen Kui Trial Checklist

- [ ] Open: https://ui-smoky-beta.vercel.app/workbench/unified-intake (production) — or http://localhost:5173/workbench/unified-intake (local)
- [ ] Click **Load founder demo queue** — seeds 13 demo-safe cases; cancellation-risk case auto-opens
- [ ] **Simulation Assistant:** Click to open; use **Recommended trial (3–4 turn)** section first
- [ ] Run scenario 1: **Cancellation risk** (SIM1) — 3-turn; watch urgency, Same-day action, Broker action required
- [ ] Run scenario 2: **Missing document** (SIM2) — 3-turn; reopen from Recent cases; see waiting on, next contact, note
- [ ] Run scenario 3: **Add-car quote (Chinese)** (SIM3) — 3-turn; handoff at turn 3; see Collected / Still needed chips
- [ ] Optional: Run scenario 4: **Premium review** (SIM6) — 3-turn; retention-style follow-up
- [ ] Optional: Run scenario 5: **Claim intake** (SIM5) — 3-turn; first-response guidance
- [ ] Optional: Run **Add-car 3-turn (strongest multi-turn proof)** (SIM15) — proves turn-to-turn context preservation
- [ ] Watch for: Case focus, Your next move, Collected/Still needed, Human confirmation recommended
- [ ] Ask after trial: the 5 value validation questions above

---

## 8. COPY/PASTE TRIAL PACK BLOCK

```
Simulation Assistant — Recommended trial (3–4 turn)
Best 3-scenario order: SIM1 → SIM2 → SIM3
1. Cancellation risk (3-turn; urgency, same-day)
2. Missing document (3-turn; operational, "already sent")
3. Add-car quote (Chinese) (3-turn; handoff at turn 3; revenue, Collected)

Best 5-scenario order: SIM1 → SIM2 → SIM3 → SIM6 → SIM5
1. Cancellation risk
2. Missing document
3. Add-car quote (Chinese)
4. Premium review
5. Claim intake

Strongest multi-turn proof: SIM15 Add-car 3-turn — proves turn-to-turn context preservation
(All top 5 are 3-turn deep; SIM3 and SIM15 both show add-car handoff at turn 3)

What each scenario proves
• Cancellation risk: prioritizes urgent follow-up; same-day action; turn 3 clarifies payment confusion
• Missing document: structured follow-up; verify receipt; turn 3 asks what to send
• Add-car quote: collects year/model/zip across 3 turns; broker sees Collected chips
• Premium review: retention-style; turn 3 asks if removing vehicle helps
• Claim intake: first-response guidance; accident + hit-and-run; turn 3 asks what matters most

5 best post-trial questions
1. Which scenario felt most useful to your office?
2. Which part still feels risky or not trustworthy?
3. Would this save you or your assistant time?
4. What would you want it to do next?
5. What would you be willing to try first in a pilot?

One-sentence pilot offer
试用一个月：帮你把客户发来的messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。
```

---

*See also: `docs/STANDARD_SCENARIO_PACKAGE.md` (canonical package definition), `docs/UNIFIED_INTAKE_DEMO_READINESS.md`, `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md`*
