# Trial Reality Audit — P11

**Sources:** BROKER_TRIAL_PLAYBOOK, TRIAL_ONE_PATH, FOUNDER_ONE_PATH, P10 trial readiness score.  
**Question:** Can Chen Kui finish Day 1 and Day 7 **without founder help?**

---

## Day 1 — Learn + first real message (without founder)

**Playbook expects:**

1. Open `/workbench/unified-intake`
2. Click **Load founder demo queue** (UI: 加载演示队列)
3. Open **Simulation Assistant** — run Cancellation, Missing doc, Add-car (3 turns each)
4. Watch Case focus, Your next move, Collected, Still needed
5. Paste one real message
6. Edit draft → copy to WeChat

**Reality without founder:**

| Step | Can broker alone? | Blocker |
|------|-------------------|---------|
| Open URL | Yes | — |
| Find correct tab | **No** | Defaults to 客户报送, not 办公室工作台 |
| Load demo queue | Partial | 15–30s load; no progress — may think broken |
| Simulation Assistant | **No** | Hidden in product-only UI; playbook requires it |
| Understand Case focus / chips | Partial | Labels mixed EN/ZH; no tooltips |
| Paste real message | Partial | First request ~30s; 503 possible |
| Copy draft | Yes | If they reached case detail |

**Day 1 score: 28 / 100**

**Interpretation:** Day 1 playbook **fails unsupervised**. Broker likely lands wrong tab, can't find Simulation, may abandon before cancellation value.

**With 30-min founder kickoff (P10 recommendation): Day 1 score: 72 / 100**

---

## Day 7 — Value validation + decision (without founder)

**Playbook expects:**

1. 2–3 real cases pasted (Day 3 habit)
2. Reopen + follow-up on at least one case
3. Answer 5 value questions
4. Decide on paid pilot

**Reality without founder:**

| Requirement | Can broker alone? | Blocker |
|-------------|-------------------|---------|
| Sustained use Days 2–6 | Unlikely if Day 1 failed | No habit formed |
| Real case logging | Possible if Day 1 worked | No self-serve friction log in UI |
| Follow-up paste workflow | Partial | 更新客户新消息 not prominent |
| 5 value questions | Yes | In playbook — self-assessment |
| Know price / terms | **No** | Not on one-pager today |
| Pay / invoice | **No** | Requires founder |
| Support when stuck | **No** | Founder WeChat only |

**Day 7 score: 35 / 100** (unsupervised from cold start)

**Day 7 score: 68 / 100** (if Day 0 kickoff + async founder Days 1–6 + prod deploy stable)

---

## Combined trial path scores

| Scenario | Day 1 | Day 7 | Overall trial |
|----------|-------|-------|---------------|
| URL only, no founder, local/staging | 28 | 35 | **32 / 100** |
| URL + one-pager + playbook, no founder | 35 | 40 | **38 / 100** |
| 30-min kickoff + prod URL + UI fixes (P10 Week 1) | 72 | 68 | **70 / 100** |
| Full P10 30-day plan executed | 78 | 82 | **80 / 100** |

---

## Can broker finish without founder help?

| Milestone | Without founder? | Notes |
|-----------|------------------|-------|
| **Day 1 complete** | **No** (today) | Wrong tab + missing Simulation + engineer chrome |
| **Day 7 complete** | **No** (today) | Payment, terms, sustained support need founder |
| **Day 1 after UI fixes** | **Marginal yes** | If broker tab default + inline practice + loading states |
| **Day 7 after UI fixes** | **Partial** | Value assessment yes; payment still founder-led |

---

## What trial docs assume vs what broker gets

| Docs assume | UI reality (P10) |
|-------------|------------------|
| Broker Workbench first | Customer Entry default |
| Load founder demo queue | 加载演示队列 (label drift) |
| Simulation Assistant Day 1 | Tab hidden in product-only |
| Cancellation opens first | Manual unless auto-open shipped |
| Production Postgres | Local may be JSON-only |
| Founder "available, not hovering" Day 1 | Required for tab redirect today |

---

## Minimum bar to reach 75 unsupervised

1. Broker tab default on trial URL  
2. Hide engineer chrome (PG, API URL, debug tags)  
3. Inline 练习场景 replacing Simulation dependency  
4. Playbook updated to match UI labels  
5. Production deploy validated; `/readyz` intake_path_ready  
6. $99/mo + 1-page terms on one-pager  
7. Loading/progress on demo queue + first paste  

---

*End of trial reality audit*
