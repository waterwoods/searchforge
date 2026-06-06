# P16-X Phase 2 — Chen Kui Simulation

**Date:** 2026-06-01  
**Persona:** Chen Kui — busy California auto broker; 2 minutes available; 50 unread WeChat messages  
**Method:** Timed walkthrough on deployed Preview + P16-W founder E2E evidence  
**URL:** https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake

---

## Context

| Constraint | Effect |
|------------|--------|
| 2 minutes total | ~30s consumed by first triage alone |
| 50 unread WeChat | Opportunity cost: every click must beat「直接回微信」 |
| No Andy on call | Must self-serve from URL |
| Cancellation wedge | Primary trial scenario |

---

## 1. Would he continue after first draft?

**Maybe — one message only.**

| Signal | Continue | Stop |
|--------|----------|------|
| Draft quality (cancellation) | Chinese draft usable with 小改 |「办公室主行动」in English breaks trust |
| Time | 30s acceptable **once** if draft saves 5+ min | Second message in same session unclear |
| Habit | Copy → WeChat is natural | Returning to web for follow-up is **not** natural |
| Queue | Loaded demo shows cases exist | English previews; duplicate rows look like bugs |

**Verdict:** **60% chance** he sends the first draft to a real client **today** if Andy pre-warned about wait time. **15% chance** he opens the URL again **tomorrow** without a reminder.

**Continue-after-first-draft score:** **52 / 100**

---

## 2. Would he know what to do next?

**No — not without training.**

After copying draft, the product offers:

- Paste area still open (suggests new message, not follow-up)
- Queue below (requires scroll + click to reopen)
- **No** visible「追加客户补充」on fresh triage (only after queue reopen)
- **No**「已发送给客户」or「等客户回复」state
- Status change buried under「状态」kebab

**What Chen Kui would actually do:** Paste draft into WeChat → mark mentally done → never reopen case unless Andy shows queue.

**Next-step clarity score:** **38 / 100**

---

## 3. What would he expect?

| Expectation (professional broker SaaS) | Deployed reality | Gap |
|--------------------------------------|------------------|-----|
| Paste → draft in &lt;15s on urgent | ~30s first triage | Medium |
| Clear「发这条给客户」moment | Copy button only | Medium |
| Same case updates when client replies | Must find case in queue → reopen → append | **Large** |
| Today's urgent items at top | Queue exists; no「需今天处理」filter in product_only | Medium |
| Chinese throughout | Mixed EN/ZH in glance and queue cards | **Large** |
| Works on phone between WeChat threads | Desktop-first; not validated | Unknown |
| Day 7: proof of time saved | No in-app counter or log | **Large** |

**Expectation match:** **45 / 100**

---

## 2-minute timeline (simulated)

```
0:00  Open URL — brand + paste visible                    ✅
0:05  Paste cancellation WeChat text                      ✅
0:08  Click 开始整理 — wait begins                         ⚠️
0:38  Draft appears — scroll to find it                   ⚠️
0:45  Copy draft — mentally done                          ✅
0:50  Sees queue / demo noise — ignores                   ❌
1:00  Second urgent ping in WeChat — leaves tab           ❌
2:00  Session ends — no second case, no follow-up setup   ❌
```

**Cases processed in 2 min:** 1 (if lucky). **WeChat messages cleared:** 0–1. **Product stickiness:** Low.

---

## Payment intent (Day 0, not Day 7)

| Question | Answer |
|----------|--------|
| Would pay $49 today? | No |
| Would try free for a week if Andy sets up? | Yes — supervised |
| Killer objection |「用完一次就回微信，为什么要开网页？」 |

---

## Chen Kui composite

| Dimension | Score |
|-----------|-------|
| First draft value | 68 |
| Continue after first draft | 52 |
| Next-step clarity | 38 |
| 2-minute throughput | 40 |
| Unsupervised Day 1 | 35 |
| **Overall Chen Kui (deployed)** | **47 / 100** |

**Delta vs P16-G (54) and P16-L (54 supervised):** Cold Preview is **reachable** now (+8 vs P16-Q), but **post-submit continuation** regressed vs founder expectations.

---

*End of P16-X Phase 2 — Chen Kui Simulation*
