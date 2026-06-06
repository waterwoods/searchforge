# P16-L Real Trial Plan — Chen Kui Supervised 7-Day Validation

**Date:** 2026-06-01  
**Sprint:** P16-L — Real Market Validation  
**Subject:** Chen Kui (陈魁) — first real broker trial  
**Authority:** `TRIAL_ONE_PATH.md`, `CHEN_KUI_DAY0_SCRIPT.md`, `DAY7_PAYMENT_CHECKLIST.md`, `NORTH_STAR_V1.md` §7–9  
**Constraint:** Feature-frozen. Fix-now only from observation log after Day 7.

---

## Trial frame

| Item | Value |
|------|-------|
| Duration | 7 days (+ Day 0 kickoff, Day 7 decision) |
| Mode | **Supervised Day 0** → **Founder nearby Days 1–6** → **Day 7 decision call** |
| URL | Broker-stable Preview OR Andy screen-share Day 0; **never** unsupervised drop |
| Log | `TRIAL_OBSERVATION_LOG_V3.md` |
| Payment lead | $49/mo; $99 only if assistant + 2 scenarios proven |

---

## Pre–Day 0 (founder, T-3 to T-0)

| Task | Owner | Done? |
|------|-------|-------|
| `trial_launch_check.sh` PASS | Andy | |
| `guardrail_inbox_triage.sh` PASS | Andy | |
| Preview redeploy `901b0df` + `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` | Eng/Andy | |
| Andy 15-min Preview E2E log (paste ×3, demo queue, copy, append) | Andy | |
| Fill invoice Zelle/Venmo/WeChat IDs | Andy | |
| Send packet: one-pager v2, PILOT_TERMS, blank log v3, URL | Andy | |
| Book Day 0 (30 min) + Day 7 (15 min) | Andy | |

---

## Day 0 — Kickoff (30 minutes, founder on call)

### Goal

Chen Kui completes **first real paste → draft copied** and understands the 7-day experiment.

### Success criteria

- [ ] Opens **办公室工作台** (not login wall, not wrong tab)
- [ ] Loads demo queue; sees cancellation case with urgency + draft
- [ ] Pastes ≥1 **real** message (cancellation preferred)
- [ ] Copies draft to WeChat (edit OK)
- [ ] Observation log v3 Day 0 row filled
- [ ] PILOT_TERMS_V1 acknowledged
- [ ] Day 7 call confirmed

### Failure criteria

- URL won't load → **stop**; fix deploy before Day 1
- Broker expected WeChat sync → reset expectations; if hard no, log fit risk
- Zero draft copies → reschedule Day 0; do not start Day 1 clock
- Trust broken on first real triage → log friction; continue only if structure still useful

### Required evidence

| Artifact | Location |
|----------|----------|
| Observation log v3 — Day 0 row | `results/trial_logs/chen_kui_{date}.md` |
| Screenshot: paste surface + case output | WeChat to Andy or `results/trial_logs/` |
| Screenshot: draft copied (WeChat compose, redact PII) | Same |
| Day 0 friction notes | Log v3 per-case section |
| PILOT_TERMS sent timestamp | WeChat screenshot |

### Required logs

- Andy checklist from `CHEN_KUI_DAY0_SCRIPT.md` (end of call)
- API case ID for first real paste (from case detail, founder only)

### Required broker feedback

- 「今天目标达到了吗？」 Y/N
- 「草稿能不能用？」 小改 / 中改 / 大改 / 没用
- 「明天你会再粘贴一条吗？」 Y/N/Maybe

---

## Day 1 — First solo use (founder async, not hovering)

### Goal

Chen Kui opens workbench **without a scheduled call** and pastes 1 real message.

### Success criteria

- [ ] Workbench opened (self-initiated)
- [ ] ≥1 real case pasted
- [ ] ≥1 draft copied OR explicit "structure useful, draft not" logged
- [ ] Broker can name one field that helped (urgency / next move / collected / still needed)

### Failure criteria

- Did not open workbench → founder WeChat check-in; classify: forgot / URL broken / no messages / no value
- Opened but did not paste → paste fatigue or confusion; founder 5-min async help
- Wrong triage on real case with no salvageable value → log as trust-breaking

### Required evidence

| Artifact | Minimum |
|----------|---------|
| Log v3 per-case entry | 1 row with scenario, minutes saved, draft used? |
| Screenshot | Paste → case output OR WeChat "I used it" message |
| Daily summary row | Day 1: cases, drafts, opened? |

### Required logs

- Founder async check-in message + broker reply (WeChat export or screenshot)

### Required broker feedback

- One line: what worked / what confused
- Continue tomorrow? Y/N/Maybe

---

## Day 3 — Habit checkpoint (15-min call or async review)

### Goal

2–3 real cases logged; broker has tried **follow-up paste** or **reopen from queue**.

### Success criteria

- [ ] ≥2 real cases total (Days 0–3)
- [ ] ≥1 draft copied with edits
- [ ] Broker attempted follow-up (追加客户补充 OR reopen case)
- [ ] Scenario mix named (e.g. 1 cancellation, 1 missing-doc)
- [ ] Aggregate minutes saved estimate ≥15 min (week-to-date)

### Failure criteria

- Only demo queue used, zero real pastes since Day 0 → trial is invalid; reset with real-message mandate
- &lt;2 workbench opens since Day 0 → abandonment risk; diagnose before Day 7
- Broker says "too much paste vs WeChat alone" → log; may be fit issue not bug

### Required evidence

| Artifact | Minimum |
|----------|---------|
| Log v3 | ≥2 per-case rows + Day 3 daily summary |
| Screenshot | Follow-up paste OR queue with real cases |
| Minutes saved total | Running sum in log |

### Required logs

- Day 3 check-in notes (founder)
- Any friction rows in classification table

### Required broker feedback

- Which scenario saved the most time? (specific example)
- Would assistant use this? Y/N/Maybe
- Biggest friction one line

---

## Day 7 — Value validation + payment decision (15 minutes)

### Goal

Decide: **$49 invoice**, **$99 invoice**, **extend 3 days**, or **no fit** — based on evidence, not optimism.

### Success criteria (North Star §9 behavioral gates)

| Gate | Target |
|------|--------|
| Real cases pasted | ≥3 |
| Draft copied with edits | ≥2 |
| Workbench opened | ≥4 of 7 days |
| "Worked" line with minutes | ≥1 (≥5 min single case OR ≥30 min/week aggregate) |
| Day 7 Q3 "Would this save time?" | Yes with specific example |

**If ≥3 gates pass:** Andy may ask for $49 with confidence.

### Failure criteria

- &lt;2 gates pass → **do not ask for payment**; ranked blockers + optional 3-day extension
- Trust-breaking wrong triage on cancellation → fix-now or kill
- Broker expected sync/OCR/CRM → fit mismatch; document kill reason

### Required evidence

| Artifact | Minimum |
|----------|---------|
| Completed log v3 | All daily rows + per-case entries |
| Day 7 checklist | `DAY7_PAYMENT_CHECKLIST.md` filled |
| Payment decision | $49 / $99 / Not yet / No fit |
| Invoice sent screenshot | If Yes |
| Testimonial quote | If positive (optional) |

### Required logs

- `results/trial_logs/chen_kui_day7_{date}.md`
- Behavioral gates table (actual vs target)

### Required broker feedback

All 7 questions from `DAY7_PAYMENT_CHECKLIST.md` Part B, especially:
- Would you continue using this?
- Would you pay $49? $99?
- Why not? (if No/Maybe)

---

## Founder intervention rules (anti–over-helping)

| Situation | Do | Don't |
|-----------|-----|-------|
| Day 0 | Walk through once; real paste together | Click every button; defend bad triage |
| Day 1–6 | Async WeChat; 5-min unblock | Daily scheduled calls unless broker asks |
| Draft bad | Log friction; highlight structure value | Rewrite draft for broker |
| URL broken | Fix within 24h | Ask broker to use Production |
| Broker silent Day 2 | One ping: "有真实消息可以粘贴吗？" | Guilt or daily reminders |

**Over-helping invalidates validation.** Log founder assists as friction if they change broker behavior.

---

## What this trial does NOT include

- New features, prompts, or UI changes during the 7 days
- Assistant mandatory rollout (optional observation only)
- Production promote mid-trial (unless Preview fails and rollback plan exists)
- $99 push unless assistant evidence exists

---

## Post-trial outcomes

| Outcome | Next action |
|---------|-------------|
| $49 paid | Promote Production bundle; fix-now top 3 from log only |
| $99 paid | Same + assistant training script execution |
| Not yet | 3-day extension OR fix-now queue → one fix sprint max |
| No fit | Export data offer; document kill reason; no P17 |

---

*End of P16-L Real Trial Plan*
