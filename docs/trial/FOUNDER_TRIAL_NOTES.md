# Founder Trial Notes

**Sprint:** Real Broker Trial Package Sprint  
**Created:** 2026-03-18

---

## 1. What to Inspect After This Sprint

1. **Trial package docs** — `docs/trial/` folder: Blueprint, Scope, Scenario Pack, Metrics, Workflow, Acceptance, Founder Notes
2. **10–20 point breakdown** — `docs/trial/TRIAL_PACKAGE_10_20_BREAKDOWN.md`
3. **Broker Day 1 checklist** — In Broker Trial Workflow Spec
4. **Observation log template** — `docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md`
5. **One-sentence pitch** — "试用一个月：帮你把客户发来的messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。"

---

## 1b. Founder Pre-Trial Checklist

Before approaching a broker:

- [ ] Run `bash scripts/trial_readiness_check.sh` — must PASS
- [ ] Run `bash scripts/run_demo_local.sh` — backend + frontend up
- [ ] Open http://localhost:5173/workbench/unified-intake
- [ ] Load founder demo queue — verify 13 cases load
- [ ] Run SIM1, SIM2, SIM3 in Simulation Assistant — verify pass
- [ ] Copy `docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md` for broker (or share link)
- [ ] Read Broker Trial Workflow Spec — know Day 1 flow

---

## 2. How to Pitch the Trial

**Opening:** "We have a 1-week pilot. You paste customer messages; the system turns them into structured cases with a next move, what's collected, what's still needed, and a draft reply. You review and send. No auto-send."

**Value:** "Less manual triage. Fewer repeated explanations. Clearer next steps. No lost follow-ups."

**Scope:** "5 core scenarios: cancellation risk, missing document, add-car quote, premium review, claim intake. You try them in Simulation Assistant first, then paste real messages."

---

## 3. What to Demo First

1. **Load founder demo queue** — 13 cases; cancellation opens first
2. **Cancellation risk** — Show urgency, Same-day action, Broker action required
3. **Reopen missing document** — Show waiting on, next contact, note
4. **Add-car quote** — Show Collected chips (year, model, zip)
5. **Simulation Assistant** — SIM1 → SIM2 → SIM3 (3-turn flows)

---

## 4. How to Explain Value in Simple Terms

| Term | Explanation |
|------|-------------|
| **One paste → structured case** | You paste; system triages and may ask 1–2 questions; you get a case card |
| **Your next move** | One sentence: what the office should do next |
| **Collected / Still needed** | Green = what customer gave; Orange = what to ask next |
| **Draft to edit** | System drafts reply; you edit and send; no auto-send |
| **Follow-up memory** | waiting_on, next_contact_by — no lost follow-ups |

---

## 5. Trial Success = Broker Can Answer

- Which scenario felt most useful?
- Which part still feels risky?
- Would this save time?
- What would you want it to do next?
- What would you try first in a pilot?

---

## 6. If Something Goes Wrong

- **503 / embedding_warming:** `bash scripts/restore_8001_readiness.sh`
- **Guardrail fails:** Fix per script output; see `docs/ANDY_IF_SOMETHING_GOES_WRONG.md`
- **Offline mode:** Use recommended questions; demo works with preset answers

---

*End of Founder Trial Notes*
