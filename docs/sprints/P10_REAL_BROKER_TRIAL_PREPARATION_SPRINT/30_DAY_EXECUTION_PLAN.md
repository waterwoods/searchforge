# 30-Day Execution Plan — Real Users Only

**Scope:** Trial, feedback, workbench, support. **No** platform work, architecture, or future SaaS fantasy.

**North star:** Chen Kui (or next broker) completes 7-day trial and can honestly say whether to pay $99/month.

---

## Week 1 — Unblock tomorrow's trial

**Goal:** Broker lands on right screen; engineer chrome hidden; production path verified.

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Mon | UI quick wins | Hide API URL, PG tags, 路由/指标 in product-only; broker tab default (`?tab=broker`) |
| Tue | Doc sync | Update BROKER_TRIAL_PLAYBOOK: remove Simulation dependency; match 加载演示队列 label |
| Wed | Deploy verify | `validate_pilot_deploy_env.py` PASS; deploy_paid_pilot if needed; `/readyz` intake_path_ready |
| Thu | Founder dry-run | Full 15-min demo + Day-1 playbook; fill observation log template |
| Fri | Chen Kui kickoff | Send URL + one-pager + playbook; 30-min call; Day 0 checklist |

**Exit criteria:** Founder demo without mentioning SIM IDs; broker opens workbench tab first try.

---

## Week 2 — Real office use

**Goal:** 3+ real cases logged; friction captured.

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Mon–Wed | Broker self-serve | Chen Kui pastes 2–3 real messages; founder async support only |
| Thu | Check-in | 15-min call; review observation log: friction / worked |
| Fri | Fix-now triage | Top 3 friction items → ship or defer with broker-visible note |

**Exit criteria:** At least one "worked" line per scenario type in observation log.

---

## Week 3 — Workbench ROI

**Goal:** Measurable time savings on one workflow.

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Mon | Cancellation path | Auto-open cancellation after demo queue; queue filter 需今天处理 |
| Tue | Follow-up path | Promote 更新客户新消息; test reopen + append on real case |
| Wed | Draft quality | Review chen_kui handoff_phrases; fix top 2 draft complaints |
| Thu | Inline practice | Minimal 练习场景 panel (3 scenarios) for product-only UI |
| Fri | Mid-trial review | Broker answers 3 value questions early |

**Exit criteria:** Broker names Monday-morning scenario; draft used with edits at least twice.

---

## Week 4 — Payment decision

**Goal:** Yes/no on $99/month with evidence.

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Mon–Tue | Day 7 validation | 5 value questions (TRIAL_ONE_PATH) |
| Wed | FIX_NOW_QUEUE | Post-trial template → results/trial_logs/chen_kui_*.md |
| Thu | Commercial | If yes: invoice + 1-page pilot terms; if no: top blockers documented |
| Fri | Retrospective | Update TRIAL_READINESS_SCORE; plan next broker or next sprint |

**Exit criteria:** Payment received OR written "not yet" with ranked blockers.

---

## Weekly metrics (founder tracks manually)

| Metric | Target |
|--------|--------|
| Real cases pasted | ≥5 in 7 days |
| Days broker opened workbench | ≥4 of 7 |
| Cases with draft copied | ≥2 |
| Support escalations | Log all; <3 L3 outages |
| Time-to-first-value (guided) | <5 min |

---

## Explicitly out of scope (30 days)

- Stripe / billing portal  
- WeChat/email inbox sync  
- OCR / screenshot reading  
- Multi-tenant auth  
- Repo cleanup / archive / platform convergence  
- Qdrant / RAG lab / `/demo` investment  
- New verticals  

---

*End of 30-day execution plan*
