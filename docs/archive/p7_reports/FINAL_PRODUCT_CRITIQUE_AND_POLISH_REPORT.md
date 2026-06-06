# Final Product Critique + Polish Report

**Sprint:** Final Product Critique + Polish Sprint  
**Date:** 2026-03-13  
**Execution:** Deep critique → Identify 1–3 polish targets → Implement → Retest → Founder summary

---

## 1. Deep product critique

### Speed

**What is genuinely good now:**
- Turn 2+ simple follow-ups (already_sent, clarification, add-car field, correction, handoff confirmation) use the fast path when `LLM_GENERATION_ENABLED=1`. No LLM call for "我发了截图在微信", "garaging proof 是什么意思", "2024年的，zip 90210，下周提车", "这些够了吗", "我其实已经付了".
- Speed routing is correctly integrated: turn 1 → LLM, turn 2+ simple patterns → fast.

**What still feels slow:**
- Turn 1 always goes to LLM (cold start, retrieval latency). By design; no change.
- No visible loading indicator that distinguishes "fast path" vs "LLM path" — user doesn't know if delay is expected.

**What still harms first impression:**
- First reply latency is unchanged. A prospect pasting a message may wait several seconds before seeing a response.

---

### Realism

**What now feels convincingly real:**
- Real customer pack (R1–R8): "都发过了怎么还要", "宝马x5，多少钱", "刚撞了对方跑了", "payment failed 怎么办，另外dec page我上周发过了" — all pass. Messy, short, mixed-language inputs produce correct triage and handoff.
- Add-car, renewal, claim, missing-doc flows feel office-natural. Collected/Still needed chips reflect real extraction.

**What still felt scripted or demo-like (before polish):**
- Recommended trial scenarios (SIM1, SIM2, SIM5, SIM6) used "客户问：…" / "客户说…" — broker-forwarded voice, not direct customer. A prospect watching the trial would think "this is broker dictation, not real client."
- CUSTOMER_ENTRY_EXAMPLES and FOUNDER_DEMO_QUEUE in the UI also use "客户问" / "客户发来" — broker dictation style.

**After polish:** SIM1, SIM2, SIM5, SIM6, SIM8, SIM9, SIM10 now use direct customer voice. Trial demo feels more like real client messages.

---

### Handoff / office usefulness

**What now feels office-like:**
- Unified Case handoff block: case focus → status → one-liner → Your next move → Human confirmation (when needed) → Collected → Still needed. One compact block instead of scattered cards.
- Customer Entry handoff moment shows case focus + one-liner before "查看工作台".
- Simulation Assistant mirrors Workbench structure. Same logic across surfaces.
- Queue triage: Work now / Waiting or parked; Ready to act / Needs more info / Verify receipt badges.
- "Resume here" and "What changed recently" make reopened cases actionable.

**What still feels scattered:**
- "Where this case stands now" remains a separate card below the main handoff block. Could be folded into handoff for reopened cases. Deferred.
- "Keep this case moving" is separate from the handoff block.

**What still feels too debug-like:**
- None critical. The handoff structure is coherent and broker-actionable.

---

### Trust / confidence

**What makes the system feel trustworthy now:**
- Human confirmation recommended badge (gold) when AI collected payment status, customer_says_sent, VIN, or primary driver.
- "Verify before acting: …" with specific field names when `human_confirmation_fields` is populated.
- Collected (green) and Still needed (orange) chips show what the AI extracted.
- Draft card states "The broker still reviews and sends manually."

**What still weakened trust (before polish):**
- When `human_confirmation_fields` was empty, the fallback said "Verify AI-collected info before acting." — too generic; broker didn't know what to verify.
- No explicit "不自动发送" (not auto-sent) near the draft — Chen Kui's pilot offer emphasizes this; the UI didn't reinforce it.

**After polish:** (1) Fallback now says "Verify before acting: payment status, customer_says_sent, or add-car VIN/driver." — more actionable. (2) Draft card adds "不自动发送。" — trust reinforcement.

---

### Demo / pilot value

**What would most impress a small-client prospect:**
- Messy message → structured case with case focus, next move, collected/still needed, draft reply — in one glance.
- "You confirm before sending; nothing is auto-sent."
- Real customer pack (R1–R8) proves the system handles messy, short, mixed-language input.
- Speed routing: turn 2+ simple follow-ups feel fast.

**What would still confuse them:**
- First-time cold start (turn 1) latency.
- "Where this case stands" vs "Case handoff" — two cards; minor.
- If they paste a very ambiguous message, they may get a generic ask — acceptable.

**What part feels strongest as a sellable value proposition:**
- **"Messy client messages → one structured case with next move, collected/still needed, draft reply. You confirm before sending. No auto-send."** — this is the one-sentence pilot offer and it matches what the product delivers.

---

## 2. Chosen polish targets

| # | Target | Why |
|---|--------|-----|
| 1 | **Recommended trial direct voice** | SIM1, SIM2, SIM5, SIM6 (and SIM8, SIM9, SIM10) used "客户问"/"客户说" — broker dictation. Trial demo felt scripted. Direct customer voice improves realism for Chen Kui trial. |
| 2 | **Trust reinforcement near draft** | Pilot offer says "不自动发送" — UI didn't. Adding "不自动发送。" to the Draft card reinforces trust. |
| 3 | **Human confirmation generic fallback** | When `human_confirmation_fields` empty, "Verify AI-collected info before acting." was too vague. Replaced with "Verify before acting: payment status, customer_says_sent, or add-car VIN/driver." — more actionable. |

---

## 3. Implementation changes made

| File | Change |
|------|--------|
| `configs/simulation_assistant_scenarios.json` | SIM1: "客户问：…" → "这个英文 notice 说 payment failed，我现在怎么办？"; "客户说其实已经付了…" → "其实已经付了…". SIM2: "客户说上周发过了" → "上周发过了"; "客户问现在要发什么" → removed. SIM5: "客户问现在最要紧做什么？" → "现在最要紧做什么？". SIM6: "客户问能不能少一辆车…" → "能不能少一辆车…". SIM8, SIM9, SIM10: same direct-voice edits. |
| `ui/src/config/simulation_assistant_scenarios.json` | Synced from configs/ (copy). |
| `ui/src/pages/UnifiedIntakePage.tsx` | Draft card: added "不自动发送。" after "The broker still reviews and sends manually." Human confirmation fallback: "Verify AI-collected info before acting." → "Verify before acting: payment status, customer_says_sent, or add-car VIN/driver." |
| `ui/src/components/simulation/SimulationAssistant.tsx` | Same human confirmation fallback text. |

**What improved:**
- Trial scenarios (SIM1–SIM6) now use direct customer voice — demo feels more real.
- Draft card explicitly states "不自动发送" — trust boundary clearer.
- Human confirmation fallback is more actionable when fields list is empty.

---

## 4. Retest results

| Script / Check | Result |
|----------------|--------|
| `run_inbox_triage_scenarios.py` | **49/49 passed** |
| `run_multi_turn_simulations.py` | **38/38 Strong** |
| `audit_state_field_accuracy.py` | **7/7 passed** |
| `verify_speed_routing.py` (LLM=1) | **6/6 OK** |
| `guardrail_inbox_triage.sh` | **PASS** |
| `unified_intake_smoke_check.sh` | **PASS** |
| `cd ui && npm run build` | **✓ built** |

**Targeted observations:**
- Simulation Assistant: 23/23 Normal (15 trial + 8 real-customer). Direct-voice changes did not break any scenario.
- LC-AC3 remains the single acceptable friction (handoff 1 turn early).
- No regressions.

---

## 5. Founder-level final summary

### Top 3 strengths

1. **Integrated quality across three mainlines.** Real messy messages → correct routing (turn 1 LLM, turn 2+ fast when simple) → clean office-style handoff with case focus, one-liner, next move, human confirmation, collected/still needed. No conflicts.
2. **Real customer pack (R1–R8) proves robustness.** "都发过了怎么还要", "宝马x5，多少钱", "刚撞了对方跑了", mixed payment+dec page — all pass. Small-client prospect sees the system handles real office input.
3. **Trust boundaries are visible.** Human confirmation badge, "Verify before acting" with specific fields, "不自动发送" on draft card. Broker stays in control.

### Top 3 weaknesses still remaining

1. **Turn 1 latency.** First reply always goes through LLM; cold start and retrieval add delay. No visible feedback that distinguishes fast vs slow path.
2. **"Where this case stands" separate card.** Minor UX; could be folded into handoff block for reopened cases. Deferred.
3. **LC-AC3 handoff timing.** One long-context correction case ("我刚才说错了，是我老婆开那辆") hands off 1 turn early. Low impact; acceptable.

### Single strongest sellable value for a small client

**"Messy client messages → one structured case with next move, collected/still needed, draft reply. You confirm before sending. No auto-send."** — matches the product. Reduces triage time, clarifies next steps, keeps broker in control.

### Single biggest risk if we showed this to a prospect tomorrow

**First-reply latency.** If the prospect pastes a message and waits 5–10 seconds with no clear feedback, they may think the system is slow or broken. Mitigation: use Offline path for demo if backend is slow; or add a brief "Analyzing…" state.

### What did this polish sprint improve?

1. **Trial realism:** Recommended scenarios (SIM1–SIM6) now use direct customer voice instead of "客户问"/"客户说". Demo feels less scripted.
2. **Trust reinforcement:** Draft card adds "不自动发送"; human confirmation fallback is more specific when fields list is empty.
3. **No regressions:** All guardrails and scripts pass.

### Is the product now in a better place for demo/pilot use?

**Yes.** Trial scenarios feel more real; trust boundaries are clearer. The product is ready for Chen Kui trial with the improved trial pack and trust signals.

---

## 6. Redeploy readiness

| Component | Redeploy? | Reason |
|-----------|-----------|--------|
| **Backend** | No | No backend changes. |
| **Frontend** | **Yes** | Simulation config (direct voice), Draft card ("不自动发送"), Human confirmation fallback. |

---

## 7. 中文宏观总结

**现在产品最强的三个地方是什么**
1. 三条主线整合质量高：真实 messy 消息 → 正确路由 → 清晰的 office-style handoff。
2. 真实客户 pack (R1–R8) 证明鲁棒性：都发过了怎么还要、宝马x5多少钱、刚撞了对方跑了等都能正确处理。
3. 信任边界清晰：Human confirmation 徽章、Verify before acting、不自动发送。

**还最需要补的三个地方是什么**
1. Turn 1 延迟：首轮回复必经 LLM，冷启动和检索有延迟；没有快/慢路径的可见反馈。
2. "Where this case stands" 仍是独立卡片：可并入 handoff block，暂缓。
3. LC-AC3 长上下文纠正场景 handoff 早一 turn：影响小，可接受。

**最能卖钱的点是什么**
 messy 客户消息 → 一个结构化 case，有下一步、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。

**现在拿去给小客户看，最怕出什么问题**
 首轮回复延迟。客户粘贴消息后等 5–10 秒没反馈，可能觉得系统慢或坏了。对策：演示时可用 Offline 路径，或加「分析中…」状态。

**这轮 polish 有什么提升**
1. 推荐 trial 场景改用直接客户原话，去掉「客户问」「客户说」，演示更真实。
2. 草稿卡片加「不自动发送」；Human confirmation 无字段时的 fallback 更具体。
3. 无回归，所有 guardrail 通过。

**下一步最该做什么**
1. 部署 frontend（polish 改动）。
2. 用 R1、R2、R3 和 SIM1、SIM2、SIM3 跑一次 live demo。
3. 可选：为首轮回复加「分析中…」或类似 loading 反馈。

---

## 8. COPY/PASTE FOUNDER BLOCK

```
FINAL PRODUCT CRITIQUE + POLISH — Sprint Summary
==================================================

Top 3 strengths
  1. Integrated quality: messy → correct routing → clean handoff (case focus, next move, human confirmation, collected/still needed).
  2. Real customer pack (R1–R8) proves robustness: 都发过了怎么还要, 宝马x5多少钱, 刚撞了对方跑了 — all pass.
  3. Trust boundaries visible: Human confirmation badge, Verify before acting, 不自动发送 on draft card.

Top 3 weaknesses
  1. Turn 1 latency — first reply always LLM; no fast/slow feedback.
  2. "Where this case stands" still separate card — minor; deferred.
  3. LC-AC3 handoff 1 turn early — acceptable.

Strongest sellable value
  "Messy client messages → one structured case with next move, collected/still needed, draft reply. You confirm before sending. No auto-send."

Biggest remaining risk
  First-reply latency. Prospect may think system is slow if they wait 5–10 sec with no feedback.

What polish improved
  1. Trial scenarios (SIM1–SIM6) now direct customer voice — less scripted.
  2. Draft card adds 不自动发送; human confirmation fallback more specific.
  3. No regressions.

Redeploy needed?
  Frontend only (simulation config, draft card, human confirmation text).

Next step
  1. Deploy frontend
  2. Run live demo with R1–R3 and SIM1–SIM3
  3. Optional: add "Analyzing…" or loading feedback for turn 1
```

---

*End of report*
