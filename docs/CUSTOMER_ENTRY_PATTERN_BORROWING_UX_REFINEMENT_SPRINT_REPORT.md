# Customer Entry Pattern Borrowing + UX Refinement Sprint Report

**Sprint:** Customer Entry Pattern Borrowing + UX Refinement Sprint  
**Date:** 2026-03-10  
**Scope:** Unified Intake Customer Entry UX — 5 flows only

---

## 1. Reusable patterns borrowed

From Intercom Fin, Zendesk AI Copilot, and mature CX systems:

| Pattern | What it means | How it applies to this product | Flows that benefit most |
|---------|---------------|--------------------------------|-------------------------|
| **Acknowledge first, then ask** | Mirror the customer's question or key detail before requesting more | "好的，宝马X5。先把年份和地址邮编发我" — already in add-car; reinforces office-natural flow | Add-car, remove-car |
| **Ask 1–2 highest-value items, not six** | One or two focused asks per turn | Progressive ask: year+model → zip → delivery+driver. "先发其中一个也行" for multi-item | Add-car, missing-document, premium-review |
| **Explain why the next step matters** | Link action to outcome | "发过来我就能帮你确认" / "核对好后就能往下推" — causal link | Claim, missing-document |
| **Pair explanation with action** | Brief context, then concrete ask | "英文通知有些术语看不懂很正常。把完整通知发我，我先帮你看一下" | Notice confusion |
| **Handoff only after visible progress** | Don't hand off until enough info collected | Thresholds per MATURE_INTAKE_SKELETON; add-car needs year+model+zip | All 5 flows |
| **Make human follow-through explicit but not abrupt** | "We've got it; office will handle" | "您说的情况已整理好了，办公室会尽快处理" — progress feel, not cold receipt | All handoffs |
| **Keep answers concise and purpose-driven** | No generic empathy, no long FAQs | Chen Kui proxy style: conclusion first, next step second | All 5 flows |
| **Present assistant as moving the issue forward** | "I can confirm" / "I will check" | "我就能帮你确认下一步" — causal "send X → I can do Y" | Claim, add-car |

---

## 2. First-pass UX simulation findings

**Multi-turn simulations:** 29/29 PASS (all strong or acceptable).

| Flow | Strongest cases | Weakest / notes |
|------|-----------------|-----------------|
| **Add car** | MT1, MT2, MT15, MT16 — acknowledgement + progressive ask | MT18 ultra-short: delivery in T1, year/model in T2 — works |
| **Renewal** | MT4, MT20, MT21 — "有办法吗" reassurance, "先发其中一个也行" | — |
| **Claim** | MT17, MT22, MT23 — empathy + first-step guidance, hit-and-run tailored | — |
| **Notice** | MT7, MT8, MT24 — "英文通知看不懂很正常" + ask for full notice | — |
| **Missing doc** | MT9, MT10, MT27, MT28, MT29 — "核对好后就能往下推", multi-item "先发其中一个" | — |
| **Payment** | MT5, MT6, MT12, MT25, MT26 — "现在最关键的是", other_received handoff | — |

**Repeated weak patterns (pre-fix):**
- Generic handoff "您说的情况已收到" could feel passive vs "已整理好了"
- Claim flow "我帮你确认" — causal "我就能" stronger
- English claim "I will help you" — "I can confirm" more action-oriented

---

## 3. Prioritized fixes

| Priority | Fix | Rationale |
|----------|-----|-----------|
| 1 | Handoff "other": 已收到 → 已整理好了 | Mirrors add-car/remove-car; user feels info was organized, not just received |
| 2 | Claim templates: 我帮你确认 → 我就能帮你确认 | Causal link: send X → I can confirm next step |
| 3 | English claim: "I will help" → "I can confirm" | More action-oriented, less generic |
| 4 | Handoff fallback in triage.py | Align hardcoded fallback with config for consistency |

---

## 4. Improvement loop 1 results

**Changes made:**

1. **configs/clients/chen_kui/handoff_phrases.json**
   - `other.zh`: "您说的情况已收到" → "您说的情况已整理好了"
   - `other.en`: "Got it. Our office will review..." → "Got it. We've noted your info—our office will review and follow up with you."

2. **configs/industries/insurance/reply_templates.json**
   - `claim_intake.zh`: "我帮你确认下一步怎么报案" → "我就能帮你确认下一步怎么报案"
   - `claim_intake.en`: "I will help you with the next steps" → "I can confirm the next steps to report the claim"
   - `claim_intake_hit_and_run.zh`: "我帮你确认" → "我就能帮你确认"
   - `claim_intake_hit_and_run.en`: "I will help you" → "I can confirm the next steps"

3. **services/fiqa_api/inbox_triage/triage.py**
   - Handoff fallback for `other`: same wording as config for consistency when config empty

**Before vs after (claim flow):**
- Before: "先把事故经过、对方信息和照片发我，我帮你确认下一步怎么报案"
- After: "先把事故经过、对方信息和照片发我，我就能帮你确认下一步怎么报案"

**Before vs after (handoff other):**
- Before: "您说的情况已收到，办公室会尽快处理"
- After: "您说的情况已整理好了，办公室会尽快处理"

---

## 5. Improvement loop 2 results

Skipped — loop 1 fixes sufficient; no clear additional gains from a second pass.

---

## 6. Optional loop 3 results

Skipped — validations pass; no remaining weak patterns warranting another pass.

---

## 7. Product proof walkthroughs

### Add car
- **Customer T1:** 我买了台宝马X5，想问下保费多少钱
- **System T1:** 好的，宝马X5。先把年份和地址邮编发我，我就能帮你算报价。
- **Customer T2:** 2024年的，zip 90210，下周提车
- **System T2 (handoff):** 您说的报价资料已整理好了，办公室会尽快出价，有结果会联系您。
- **Pattern:** Acknowledge first; progressive ask; handoff mirrors add-car phrasing
- **Result:** Strong

### Renewal
- **Customer T1:** 保费太高了，能不能便宜一点
- **System T1:** 一般有办法的。我先帮你看这次保费为什么变高，再看看有没有能调整的地方。把现在保单和最新账单发我（先发其中一个也行），我先帮你核对。
- **Customer T2:** 续保通知和账单我发你微信了
- **System T2 (handoff):** 好的，收到了。办公室会尽快处理，有结果会联系您。
- **Pattern:** Reassurance ("有办法"); "先发其中一个也行"; other_received handoff
- **Result:** Strong

### Claim
- **Customer T1:** 刚出事故了，要收集什么？
- **System T1:** 刚出事故一定很着急，先别慌。先确保人没事，再拍现场照片、记下对方车牌和保险信息。先把事故经过、对方信息和照片发我，我就能帮你确认下一步怎么报案。
- **Customer T2:** 拍了照片，对方保险也记了，发你微信
- **System T2 (handoff):** 好的，收到了。办公室会尽快处理，有结果会联系您。
- **Pattern:** Empathy + first-step guidance; causal "我就能帮你确认"
- **Result:** Strong

### Notice
- **Customer T1:** 这个英文 notice 什么意思？
- **System T1:** 英文通知有些术语看不懂很正常。把完整通知或更清楚的照片发我，我先帮你看一下，再告诉你重点和下一步怎么处理。
- **Customer T2:** 通知我发你了，你看下
- **System T2 (handoff):** 好的，收到了。办公室会尽快处理，有结果会联系您。
- **Pattern:** Reassurance; pair explanation with action; other_received handoff
- **Result:** Strong

### Missing document
- **Customer T1:** 他们要我补 declaration page 和 garaging proof
- **System T1:** 现在文件里还缺 declaration page（保单首页） 和 garaging proof（车辆停放地址证明）。请再发我一次（先发其中一个也行）；如果你之前已经发过，也跟我说一声，我这边帮你核对，核对好后就能往下推。
- **Customer T2:** declaration page 发你了，garaging 还没弄
- **System T2 (handoff):** 您说的情况已整理好了，办公室会尽快处理，有结果会联系您。
- **Pattern:** Name items; "先发其中一个也行"; "核对好后就能往下推"; handoff other
- **Result:** Strong

---

## 8. Validation summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `run_multi_turn_simulations.py` | 29/29 PASS |
| `run_expression_robustness.py` | 41/41 strong |
| `npm run build` (ui/) | ✓ built |
| `guardrail_inbox_triage.sh` | (includes scenarios + multi-turn; scenarios pass) |
| `test_inbox_triage_api.py` | (requires server on 8001; skipped when no server) |

---

## 9. Remaining weaknesses

- **Unclear category:** "这段内容还不够完整" — when intent is partially clear (e.g. "新车" only), could add "新车报价的话" before ask; low impact.
- **Retrieval-augmented replies:** When notice/document retrieval returns a snippet, insertion order and length can occasionally feel slightly awkward; no change in this sprint.
- **Handoff "other" vs "other_received":** When customer did not explicitly say "发你了", we use "您说的情况已整理好了" — good. When they did say "发你了", we use "好的，收到了" — good. No remaining gap.

---

## 10. Recommended next step

1. **Run full guardrail:** `bash scripts/guardrail_inbox_triage.sh` (includes adversarial and complex adversarial packs).
2. **Manual smoke:** `bash scripts/unified_intake_smoke_check.sh` with demo running.
3. **Broker feedback:** Have Chen Kui try 2–3 real conversations; capture where it still feels robotic or vague.
4. **Optional:** Add "新车报价的话" prefix for unclear-but-partial-add-car cases.

---

## 11. 中文宏观总结

**抄到了哪些“模式”：**
- 先确认再问（acknowledge first, then ask）
- 每次只问 1–2 个最有用的信息
- 解释“发过来我就能帮你做什么”的因果链
- 交接时用“已整理好了”而不是“已收到”，让用户感觉有进展
- 事故理赔用“我就能帮你确认下一步”，强化行动导向

**改了哪些地方：**
- 通用交接语：从“您说的情况已收到”改为“您说的情况已整理好了”
- 事故理赔：从“我帮你确认”改为“我就能帮你确认下一步怎么报案”
- 英文：从“I will help you”改为“I can confirm the next steps”

**前端统一入口现在更像什么：**
- 更像一个真实办公室前台：先确认你说了什么，再要最关键的下一步信息，然后说“发过来我就能帮你处理”，交接时用“已整理好了”而不是冷冰冰的“收到了”。

**还差什么：**
- 完全模糊的“这段内容还不够完整”可以再细分（如“新车报价的话”前缀）
- 检索增强的插入语有时略长，可后续微调

**下一步最值得做什么：**
- 跑完整 guardrail 和 manual smoke
- 让陈奎试几条真实对话，收集反馈
- 若发现某类场景仍偏冷或偏模板，再做针对性微调

---

*End of sprint report*
