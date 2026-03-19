# Customer Entry Issue-Progression Sprint Report

**Sprint:** Customer Entry Issue-Progression Sprint  
**Date:** 2026-03-11  
**Status:** Complete

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|------|
| Stage 1 — Define what "issue progression" should feel like | ✅ | Target defined below |
| Stage 2 — First-pass issue-progression simulation | ✅ | Simulated 5 flows; identified hit-and-run, 有办法, missing-doc progress gaps |
| Stage 3 — Classify issue-progression weaknesses | ✅ | Hit-and-run generic; renewal "有办法吗" no reassurance; missing-doc no progress phrase |
| Stage 4 — Prioritize highest-value fixes | ✅ | Claim hit-and-run, renewal reassurance, missing-doc progress phrase |
| Stage 5 — Improvement loop 1 | ✅ | Hit-and-run template; premium_review_reassurance |
| Stage 6 — Improvement loop 2 | ✅ | Missing-document "核对好后就能往下推" |
| Stage 7 — Optional loop 3 | ⏭️ | Skipped — loop 2 sufficient |
| Stage 8 — Front-end product proof | ✅ | 5 flow walkthroughs below |
| Stage 9 — Regression + safety protection | ✅ | Guardrail PASS; CUSTOMER_ENTRY_REPLY_STRATEGY updated |
| Stage 10 — Audit | ✅ | Accept |

---

## 2. Issue-progression target

**What "good" issue progression means:**

| Dimension | Weak (before) | Strong (target) |
|-----------|---------------|-----------------|
| **User feels issue moved forward** | Generic reply; no visible next step | "你把这个发我，我这边就能往下推" / "核对好后就能往下推" |
| **Next question feels useful** | Checklist without purpose | Ask explains why (e.g. "邮编确认好就能出报价") |
| **Explanation feels useful** | Static info dump | Explanation + clear action (e.g. "先把这些发我，我帮你确认下一步怎么报案") |
| **Handoff feels like progress** | "办公室会尽快处理" (abrupt) | "您说的报价资料已整理好了，办公室会尽快出价" (reflects what was achieved) |
| **Specific situation acknowledged** | Hit-and-run gets generic claim reply | "对方跑了的话，最关键的是车牌号、现场照片和事故经过" |
| **Reassurance when asked** | "有办法吗" → generic ask | "一般有办法的。" + ask |

**Why it matters:** A good business front desk does not just reply politely—it helps the customer make progress. Users should feel: the system is helping me move this issue forward; I know what the next useful step is; I am not just being stalled.

---

## 3. Product / logic / wording changes made

| File | Change |
|------|--------|
| `configs/industries/insurance/reply_templates.json` | Added `claim_intake_hit_and_run` (zh/en); `premium_review_reassurance` (zh/en); `missing_document` zh_with_item + "核对好后就能往下推"; en_with_item + "once verified we can move forward" |
| `services/fiqa_api/inbox_triage/triage.py` | Claim: when "对方跑了"/"hit and run" in text, use hit-and-run template; Premium: when "有办法"/"有办法吗" in text, use reassurance template |
| `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` | Added hit-and-run variant, premium "有办法" reassurance, missing-doc progress phrase; added Claim intake per-category section |

---

## 4. Simulation and improvement loops

### First pass (baseline)
- Claim hit-and-run "刚撞了，对方跑了": generic first-step guidance, no tailoring to "对方跑了"
- Renewal "续保涨了好多 有办法吗": no explicit "有办法" reassurance
- Missing document: "我这边帮你核对" without "what happens after"

### Fixes (loop 1)
1. Claim hit-and-run: new template emphasizing 车牌号、现场照片、事故经过
2. Premium "有办法": new template with "一般有办法的" / "There are usually options"

### Loop 2
3. Missing document: add "核对好后就能往下推" / "once verified we can move forward"

### After rerun
- Inbox scenarios: pass
- Multi-turn: 29/29 strong
- Adversarial: 27/27 strong
- Complex: 22 strong, 1 acceptable (LC-AC3)
- Guardrail: PASS

---

## 5. Product proof strength

| Flow | Before | After |
|------|--------|-------|
| Add car / quote | Strong (prior sprint) | Unchanged |
| Renewal / premium | Good | "有办法吗" → "一般有办法的。" + ask |
| Claim first response | Good | Hit-and-run → "对方跑了的话，最关键的是车牌号、现场照片和事故经过" |
| Notice / payment | Good | Unchanged |
| Missing document | Good | "核对好后就能往下推" added |

The front-end now feels more progress-oriented: hit-and-run gets tailored guidance; renewal "有办法吗" gets reassurance; missing-doc clarifies what happens after they send.

---

## 6. Validation summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | Pass |
| `run_multi_turn_simulations.py` | 29/29 strong |
| `run_adversarial_simulation.py` | 27/27 strong |
| `run_complex_adversarial_simulation.py` | 22 strong, 1 acceptable |
| `guardrail_inbox_triage.sh` | PASS |
| `npm run build` (ui/) | Success |

---

## 7. Business / platform value

- **User trust:** Hit-and-run users feel the system understands their specific situation; renewal "有办法吗" users get reassurance; missing-doc users see a concrete next step.
- **Office workload:** Customers arrive with clearer context; fewer "what happens next?" questions.
- **Platform story:** Front-end carries more operational load; feels more like a front desk that helps the issue advance.

---

## 8. Remaining blocker(s)

1. **LC-AC3:** Handoff at turn 2 when driver correction in turn 3 (known edge case).
2. **Premium/renewal:** No acknowledgement on follow-up turns (lower priority).
3. **Notice/payment:** Could add "确认好以后告诉你下一步" (low priority).

---

## 9. Recommended next step

**One clear next step:** Add 1–2 issue-progression examples to the founder demo queue (e.g. hit-and-run claim, renewal "有办法吗", missing-doc with progress phrase) so Chen Kui can see the improved flow live.

---

## 10. 中文或中英混合宏观总结

**前端「推进事情」的感觉这次具体变好了什么：**
- 事故对方跑了：不再给通用指引，改为「对方跑了的话，最关键的是车牌号、现场照片和事故经过。先把这些发我，我帮你确认下一步怎么报案和报保险」
- 续保「有办法吗」：增加「一般有办法的。」再问保单，让用户感到有希望
- 缺材料：增加「核对好后就能往下推」，让用户知道发完以后会怎样

**哪几条主线最像在帮用户办事：**
- 加车（已有确认语、渐进问）
- 事故（含对方跑了特例）
- 缺材料（有进度语）
- 续保（有办法时加 reassurance）

**哪几条还不够强：**
- 续保多轮暂无确认语
- LC-AC3 司机纠正边缘情况

**修了哪些最值钱的问题：**
- 对方跑了专属回复
- 有办法吗 reassurance
- 缺材料进度语

**对用户和陈奎办公室有什么帮助：**
- 用户感觉系统在推进事情，不只是礼貌回复
- 办公室收到的案件更有针对性，客户更易配合

---

## 11. Practical issue-progression cheat sheet

| Flow | Stronger "next step" | Stronger "issue progression" | Still weaker |
|------|----------------------|------------------------------|--------------|
| Add car | "把地址邮编发我，我先帮你算报价" | Acknowledgement + 1–2 asks | — |
| Renewal | "把保单和账单发我，我先帮你核对" | "一般有办法的" when 有办法 | Follow-up no ack |
| Claim | "把事故经过、对方信息和照片发我" | Hit-and-run: 车牌号、照片、经过 | — |
| Notice | "把通知发我，我先帮你确认" | Urgency + today | — |
| Missing doc | "请再发我一次；发过也跟我说，我帮你核对" | "核对好后就能往下推" | — |

---

## 12. Issue-progression problem summary

| Category | Strong | Acceptable | Weak | Fixes |
|----------|--------|------------|------|-------|
| Add car | Progressive ask; ack | — | — | (prior sprint) |
| Renewal | Policy/bill ask; 有办法 reassurance | — | — | premium_review_reassurance |
| Claim | Empathy + guidance; hit-and-run variant | — | — | claim_intake_hit_and_run |
| Notice | Urgency + ask | — | — | — |
| Missing doc | Item naming + progress phrase | — | — | 核对好后就能往下推 |
| Handoff | Warmer phrasing | — | — | (prior sprint) |

**Repeated patterns addressed:** Hit-and-run generic reply, renewal "有办法吗" no reassurance, missing-doc no progress signal.

---

## 13. Front-end proof walkthroughs

### 1. Add car / quote
- **Customer T1:** 我买了台宝马X5，想问下保费多少钱
- **System T1:** 好的，宝马X5。可以把年份和地址邮编发我，我先帮你算报价。
- **Customer T2:** 2024年的，zip 90210，下周提车
- **System T2:** 您说的报价资料已整理好了，办公室会尽快出价，有结果会联系您。
- **Progress:** User gave year+zip+delivery → handoff; user sees "报价资料已整理" = concrete progress.
- **Result:** Strong

### 2. Renewal / premium (有办法吗)
- **Customer T1:** 续保涨了好多 有办法吗
- **System T1:** 一般有办法的。我先帮你看这次保费为什么变高，再看看有没有能调整的地方。把现在保单和最新账单发我，我先帮你核对。
- **Progress:** User asked "有办法吗" → got "一般有办法的" + clear ask.
- **Result:** Strong

### 3. Claim hit-and-run
- **Customer T1:** 刚撞了，对方跑了，我现在先干嘛
- **System T1:** 刚出事故一定很着急，先别慌。对方跑了的话，最关键的是车牌号、现场照片和事故经过。先把这些发我，我帮你确认下一步怎么报案和报保险。
- **Progress:** User said "对方跑了" → got tailored reply (plate, photos, what happened).
- **Result:** Strong

### 4. Notice confusion
- **Customer T1:** 客户问：这个英文 notice 说 payment failed，我现在怎么办？
- **System T1:** 这看起来是付款出了问题。请把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。
- **Progress:** Conclusion first; urgency; next step.
- **Result:** Strong

### 5. Missing document follow-up
- **Customer T1:** UW follow up - need dec page + garaging proof. 客户说上周发过了
- **System T1:** 现在文件里还缺 declaration page（保单首页） 和 garaging proof（车辆停放地址证明）。请再发我一次；如果你之前已经发过，也跟我说一声，我这边帮你核对，核对好后就能往下推。
- **Progress:** Names items; "核对好后就能往下推" = user knows what happens after.
- **Result:** Strong

### Graceful limitation
- **Case:** LC-AC3 — driver correction in turn 3.
- **Behavior:** Handoff at turn 2; expected turn 3.
- **Result:** Acceptable — known edge case.

---

*End of sprint report*
