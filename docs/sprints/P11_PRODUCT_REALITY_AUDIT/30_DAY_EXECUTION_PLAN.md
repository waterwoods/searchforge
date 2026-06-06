# 30-Day Execution Plan — P11 (Customers Only)

**Scope:** Trial, feedback, workbench, support. **Ignore:** architecture, platform, RAG, vectors, future SaaS.  
**North star:** Chen Kui completes 7-day trial and can honestly say whether to pay $99/month.

---

## Week 1 — Unblock tomorrow's trial

**Goal:** Broker lands on right screen; engineer chrome hidden; production path verified.

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Mon | UI trust pass | Hide API URL, PG tags, 路由/指标 in product-only |
| Tue | UI front door | Broker tab default (`?tab=broker`); wayfinding banner; auto-open cancellation after demo queue |
| Wed | Doc sync | Update BROKER_TRIAL_PLAYBOOK: no Simulation dependency; match 加载演示队列; add $99/mo to one-pager |
| Thu | Deploy verify | `validate_pilot_deploy_env.py` PASS; `deploy_paid_pilot` if needed; `/readyz` intake_path_ready |
| Fri | Chen Kui kickoff | 30-min call: 办公室工作台 only; send URL + one-pager + playbook; Day 0 checklist |

**Exit criteria:** Founder demo without SIM IDs; broker opens workbench tab on first try; loading states on demo queue.

---

## Week 2 — Real office use

**Goal:** 3+ real cases logged; friction captured.

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Mon–Wed | Broker self-serve | Chen Kui pastes 2–3 real messages; founder async support only |
| Thu | Check-in | 15-min call; review observation log: friction / worked |
| Fri | Fix-now triage | Top 3 friction items → ship or defer with broker-visible note |

**Exit criteria:** At least one "worked" line per scenario type in `results/trial_logs/chen_kui_*.md`.

---

## Week 3 — Workbench ROI

**Goal:** Measurable time savings on one workflow.

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Mon | Cancellation path | Queue filter 需今天处理; sticky 下一步 on case detail |
| Tue | Follow-up path | Promote 更新客户新消息; test reopen + append on real case |
| Wed | Draft quality | Review top 2 draft complaints from observation log; tune client pack |
| Thu | Inline practice | Minimal 练习场景 panel (3 scenarios) for product-only UI |
| Fri | Mid-trial review | Broker answers 3 value questions early (TRIAL_ONE_PATH Q1–Q3) |

**Exit criteria:** Broker names Monday-morning scenario; draft copied with edits ≥2 times.

---

## Week 4 — Payment decision

**Goal:** Yes/no on $99/month with evidence.

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Mon–Tue | Day 7 validation | 5 value questions (TRIAL_ONE_PATH) |
| Wed | FIX_NOW_QUEUE | Post-trial template → `results/trial_logs/` |
| Thu | Commercial | If yes: $99 invoice + 1-page pilot terms; if no: ranked blockers doc |
| Fri | Retrospective | Update trial scores; plan second broker OR next workbench sprint |

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
| Time-to-first-value (unguided, post Week 1 fixes) | <10 min |

---

## Explicitly out of scope (30 days)

- Stripe / billing portal  
- WeChat/email inbox sync  
- OCR / screenshot reading  
- Multi-tenant auth  
- Repo cleanup / archive / lab isolation  
- Qdrant / RAG lab / `/demo` investment  
- New verticals  
- $199 tier  

---

*End of 30-day execution plan*
