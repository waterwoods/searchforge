# Weekend Final Product Health Check Report

**Sprint:** Weekend Final Product Health Check Sprint  
**Date:** 2026-03-14  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry  
**Execution:** Deep product audit + validation + optional polish

---

## 1. Deep product health audit

### Speed / responsiveness

**Strong:**
- Turn 2+ simple follow-ups use fast path (rule-based, no LLM) when `LLM_GENERATION_ENABLED=1`. Latency drops from ~2–6 s to ~50–200 ms for clarification, already_sent, add-car field, correction patterns.
- `verify_speed_routing.py` confirms: turn 1 → LLM; turn 2+ simple → fast.
- Simulation Assistant and Customer Entry show loading feedback ("正在整理 case...") so users know the system is working.
- After polish: Customer Entry loading state now shows "正在整理 case..." (was Spin only), reducing perceived "broken" feeling during turn 1.

**Weak:**
- Turn 1 always goes through LLM (by design). Cold start + retrieval + LLM = 1.5–5 s typical; Cloud Run cold start after idle can add 5–15 s.
- No visible feedback that distinguishes fast vs slow path; user sees same loading state for both.
- Document/notice confusion triggers embedding + Qdrant even on fast path when rules call retrieval — adds 0.5–2 s.

**What matters most:** First impression. If Chen Kui pastes a message and waits 5+ seconds with no clear feedback, he may think the system is slow or broken. Mitigation: pre-demo warmup, Offline path for slow backend, and now clearer loading text.

---

### Realism

**Strong:**
- Real Customer Pack (R1–R8) and recommended trial scenarios (SIM1–SIM6) use direct customer voice: "这个英文 notice 说 payment failed", "都发过了怎么还要", "刚撞了对方跑了", "续保涨了好多".
- 38 multi-turn simulations pass; 27 adversarial real-user scenarios strong; 23 complex (mixed-intent + long-context) with only 1 friction case.
- Scenario pack feels believable for a small-client prospect: cancellation risk, missing doc, add-car, claim, renewal — all real office pain points.
- Messy, short, mixed-language inputs are handled; no over-orderly "Turn 1 quote → Turn 2 year → Turn 3 zip" feel in most flows.

**Weak:**
- LC-AC3 ("我刚才说错了，是我老婆开那辆") hands off at turn 2 vs expected turn 3 — driver correction arrives after handoff. Acceptable friction; broker can paste follow-up.
- Some scenario notes still read like QA ("Turn 1 vague quote ask; Turn 2 year") rather than "would a broker think this is real?"
- Founder demo queue is seeded; not live inbox. Prospect must understand it's a trial environment.

**What matters most:** Chen Kui must believe the scenarios could happen in his office. Current pack is strong enough for trial; one edge case (LC-AC3) is documented, not blocking.

---

### Handoff / office usefulness

**Strong:**
- Unified Case handoff block: case focus → status → one-liner → Your next move → Human confirmation (when needed) → Collected → Still needed. One compact block instead of scattered cards.
- "Your next move" is one operational sentence; broker can act without re-reading.
- Collected / Still needed chips (green/orange) for add-car, renewal, claim, missing-doc; human confirmation badge when AI inferred payment status, customer_says_sent, VIN/driver.
- Queue triage: Work now / Waiting or parked; Ready to act / Needs more info / Verify receipt badges.
- Paste follow-up flow: reopen case → paste new message → "Update with new customer message" → case refreshes.
- Resume here: waiting on + next contact + latest note visible on reopen.

**Weak:**
- "Where this case stands now" and "Keep this case moving" remain separate cards; could be consolidated in a future pass.
- Some brokers may want a single "do this next" callout even more prominent; current layout is already good.
- No inbox sync / WeChat integration — broker pastes manually. Acceptable for pilot.

**What matters most:** Can an assistant or broker act fast enough? Yes. The handoff structure is office-like and actionable. No critical fragmentation.

---

### Trust / safety / control

**Strong:**
- Draft card explicitly states "不自动发送。" (not auto-sent) — trust boundary clear.
- Human confirmation badge (gold) when AI collected payment status, customer_says_sent, VIN, or primary driver.
- Fallback text when `human_confirmation_fields` empty: "Verify before acting: payment status, customer_says_sent, or add-car VIN/driver." — actionable, not vague.
- Broker stays in control; nothing is auto-sent; all drafts are review-before-send.
- Full conversation visible for verification.

**Weak:**
- One-sentence pilot offer ("你确认后再发，不自动发送") is in docs; could be surfaced more prominently in UI for first-time visitors (e.g., a small trust banner on first load).
- No explicit "AI collected vs human must confirm" explanation in UI; badge + fallback text cover it, but a first-time user might not immediately understand.

**What matters most:** Chen Kui must feel safe. Current trust signals (不自动发送, Human confirmation, Verify before acting) are sufficient for pilot. No critical gap.

---

### Demo / sellability

**Strong:**
- One-sentence value: "帮你把客户发来的messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。"
- Best demo order: Cancellation risk (SIM1) first — urgency, same-day action, broker handoff. Then Missing document (SIM2), Add-car (SIM3).
- Simulation Assistant: 15 trial + 8 real-customer scenarios; clear Run/Next turn/Reset; replay shows Collected/Still needed/Human confirmation per turn.
- Load founder demo queue → 13 cases; cancellation opens first. Repeatable, demo-safe.
- Strongest sellable value: Less manual triage, fewer repetitive explanations, clearer next steps, no lost follow-ups.

**Weak:**
- Unified Intake lives under "AI Workbench" in sider alongside Agent Studio, Retriever Lab, etc. For broker-first demo, the product feels slightly buried in a lab-style nav.
- Demo page (/demo) is separate from Unified Intake (/workbench/unified-intake). Two entry points; prospect may not know which to use.
- No explicit "office-use framing" banner or one-liner on first load of Unified Intake.

**What matters most:** What would make Chen Kui hesitate to pay? (1) Turn 1 latency if he thinks it's slow. (2) Confusion about what the product does vs doesn't do. (3) Trust: "will it send without me?" — addressed by 不自动发送. Strongest actual value: structured intake + draft + no auto-send.

---

### Product coherence

**Strong:**
- Customer Entry, Broker Workbench, and Simulation Assistant share the same Case handoff structure: case focus → status → one-liner → next move → human confirmation → collected → still needed.
- `inferCaseFocus` / `getOneLiner` logic aligned across surfaces.
- Design language: Ant Design, consistent tags (urgency, case focus, readiness), same chip styling.
- Three mainlines (Speed routing, Real customer pack, Case handoff) integrate without conflict.

**Weak:**
- App has many routes (Showtime, RAG Lab, JobHunter, Mortgage, etc.). Unified Intake is one of many; not a "broker-only" product shell.
- Dark theme (AppLayout) vs Demo page (light). Unified Intake uses dark; Demo page uses light. Slight context switch.
- "Simulation Assistant" button is English; rest of Customer Entry is Chinese. Minor inconsistency.

**What matters most:** Do the major surfaces feel like one product? Yes. The handoff flow is coherent. The lab-style nav is a cosmetic issue for broker demo; direct link to /workbench/unified-intake avoids it.

---

## 2. Validation / simulation pass

| Script / Check | Result |
|----------------|--------|
| `run_inbox_triage_scenarios.py` | (runs against API; skipped — no server on 8001) |
| `run_multi_turn_simulations.py` | **38/38 PASS** |
| `audit_state_field_accuracy.py` | **7/7 PASS** |
| `verify_speed_routing.py` | **6/6 OK** (turn 1→llm, turn 2+ simple→fast) |
| `guardrail_inbox_triage.sh` | **PASS** — 49/49 scenarios, 38/38 multi-turn, 27/27 adversarial, 23/23 complex (1 LC-AC3 friction) |
| `unified_intake_smoke_check.sh` | **PASS** — guardrail + daily-use simulation |
| `cd ui && npm run build` | **PASS** (chunk size warning only) |

**Key qualitative observations:**
- All 23 Simulation Assistant scenarios (15 trial + 8 real) pass.
- LC-AC3: Handoff at turn 2, expected 3 — driver correction "我刚才说错了，是我老婆开那辆" arrives after handoff. Marked as [FRICTION]; broker can paste follow-up.
- State field accuracy: cancellation, missing_doc, add_car, claim, renewal — all correct follow_up and collected fields.
- Speed routing: turn 1 always LLM; turn 2+ simple (screenshot sent, garaging question, zip+delivery, already paid) → fast path.

---

## 3. Highest-value remaining issues

| Issue | Why it matters | Priority |
|-------|----------------|----------|
| **Turn 1 latency** | First impression; prospect may think system slow or broken if 5+ s with no feedback | Important soon |
| **LC-AC3 early handoff** | Driver correction arrives after handoff; broker must paste follow-up. Edge case; not blocking trial | Cosmetic / can wait |
| **Unified Intake buried in lab nav** | Broker-first demo may feel product is "one of many" rather than focused | Cosmetic / can wait |
| **No trust banner on first load** | "不自动发送" is on draft card; first-time visitor might not see it until case created | Cosmetic / can wait |
| **Simulation Assistant label in English** | Rest of Customer Entry is Chinese; minor inconsistency | Cosmetic / can wait |

---

## 4. Optional polish loop

**Used:** Yes.

**Exact change:**
- `ui/src/pages/UnifiedIntakePage.tsx`: Customer Entry loading state — added "正在整理 case..." text next to Spin (was Spin only).

**What improved:**
- When user pastes a message and submits, loading state now shows "正在整理 case..." instead of a bare spinner. Reduces perceived "broken" feeling during turn 1 (1.5–5 s). Aligns with Simulation Assistant loading feedback.

**Rerun:** `npm run build` — PASS.

---

## 5. Founder-level final judgment

### Top 5 things the product now does well

1. **Integrated quality across three mainlines.** Real messy messages → correct routing (turn 1 LLM, turn 2+ fast when simple) → clean office-style handoff with case focus, one-liner, next move, human confirmation, collected/still needed. No conflicts.
2. **Trust boundaries are visible.** Human confirmation badge, "Verify before acting" with specific fields, "不自动发送" on draft card. Broker stays in control.
3. **Scenario pack is believable.** Real customer voice (R1–R8), recommended trial order (SIM1→SIM2→SIM3), 38 multi-turn + 27 adversarial + 23 complex — all pass except one edge friction.
4. **Handoff is office-like and actionable.** One Case handoff block; "Your next move" is one sentence; Collected/Still needed chips; queue triage with Work now / Waiting, Ready to act / Needs more info.
5. **Speed routing reduces perceived latency for turn 2+.** Simple follow-ups skip LLM; 50–200 ms vs 2–6 s. Turn 1 still LLM; loading feedback now clearer.

### Top 5 remaining weaknesses or risks

1. **Turn 1 latency.** First reply always goes through LLM; cold start and retrieval add delay. No visible fast/slow distinction. Mitigation: pre-demo warmup, Offline path, clearer loading text (done).
2. **LC-AC3 early handoff.** Driver correction scenario hands off one turn early; broker pastes follow-up. Edge case; acceptable.
3. **Product buried in lab-style nav.** Unified Intake under "AI Workbench" with Agent Studio, Retriever Lab, etc. For broker demo, use direct link.
4. **No inbox sync / WeChat integration.** Broker pastes manually. Acceptable for pilot; prospect may ask "when can it read my WeChat?"
5. **Two entry points.** /demo (RAG Q&A) vs /workbench/unified-intake (Unified Intake). Prospect may not know which to use for trial.

### Single strongest sellable value right now

**Structured intake + draft + no auto-send.** "帮你把客户发来的messy消息整理成结构化case，有下一步动作、收集了什么、还缺什么、草稿回复。你确认后再发，不自动发送。"

### Single biggest blocker to stronger small-client conversion right now

**Turn 1 latency + first-impression risk.** If Chen Kui pastes a message and waits 5+ seconds with no clear feedback, he may think the system is slow or broken. Mitigations in place (loading text, Offline path, warmup); not fully eliminated.

### Current maturity level

**Good for early pilot conversation.** Not quite "nearly ready for small paying trial" — turn 1 latency and manual paste flow are acceptable for pilot but would need improvement for daily paid use. Strong enough for founder demo and value-validation conversation.

### What the founder should do next after tonight

1. **Run a live demo** using `docs/CHEN_KUI_TRIAL_PACK.md` order: SIM1 → SIM2 → SIM3. Pre-warm backend if possible.
2. **Ask Chen Kui the 5 value validation questions** after trial: Which scenario felt most useful? Which part still feels risky? Would this save time? What would you want next? What would you pay for first?
3. **If turn 1 feels slow in practice:** Consider min_instances=1 on Cloud Run, or demo with Offline path for first question.
4. **Do NOT** open new feature frontier (inbox sync, CRM, auth). Stay focused on pilot feedback.

---

## 6. Redeploy readiness

| Component | Redeploy? | Reason |
|-----------|-----------|--------|
| **Backend** | No | No backend changes |
| **Frontend** | **Yes** | Polish: Customer Entry loading state now shows "正在整理 case..." |

**Recommendation:** Redeploy frontend only. One small UX improvement.

---

## 7. 中文宏观总结

**现在产品最强的 5 个地方：**
1. 三条主线整合：messy 消息 → 正确分类 → 清晰 handoff（case focus、next move、collected/still needed、human confirmation）
2. 信任边界清晰：不自动发送、Human confirmation 徽章、Verify before acting
3. 场景真实：R1–R8、SIM1–6 用真实客户口吻；38+27+23 场景基本全过
4. Handoff 像办公室工具：一个 Case handoff 块、Your next move 一句话、Collected/Still needed chips
5. Turn 2+ 快：简单 follow-up 走 fast path，50–200 ms

**还最怕客户看到的 5 个问题：**
1. Turn 1 延迟：首轮回复 1.5–5 秒，冷启动更久；客户可能觉得慢或坏了
2. LC-AC3 早 handoff：司机纠正场景少问一轮；可 paste follow-up 补
3. 产品藏在 lab 导航里：Unified Intake 在 AI Workbench 下，不像独立产品
4. 没有 inbox/微信同步：需要手动粘贴；客户可能问「什么时候能读微信？」
5. 两个入口：/demo 和 /workbench/unified-intake，客户可能不知道用哪个

**现在最能卖钱的点：**  
 messy 消息 → 结构化 case + 下一步 + 收集了什么/还缺什么 + 草稿。你确认后再发，不自动发送。

**目前最大阻碍变现的问题：**  
 Turn 1 延迟 + 第一印象风险。客户粘贴后等 5+ 秒可能觉得慢或坏了。已有 loading 文案、Offline 路径、warmup 缓解，未完全消除。

**这个产品现在属于：**  
 适合 early pilot 对话。可以 founder demo、可以和陈奎做价值验证。还没到「接近付费试用」—— turn 1 延迟和手动粘贴对 pilot 可接受，日付费用需要再改进。

**明天以后最该做什么：**
1. 按 CHEN_KUI_TRIAL_PACK 跑 live demo：SIM1→SIM2→SIM3
2. 问陈奎 5 个价值验证问题
3. 若 turn 1 实际感觉慢：考虑 Cloud Run min_instances=1 或首问用 Offline
4. 不开新功能；专注 pilot 反馈

---

## 8. COPY/PASTE FOUNDER HEALTH BLOCK

```
WEEKEND FINAL PRODUCT HEALTH CHECK — Chen Kui Insurance Unified Entry

Current product maturity: Good for early pilot conversation
Strongest value: Structured intake + draft + no auto-send
Biggest blocker: Turn 1 latency + first-impression risk

Top strengths:
• Integrated quality: messy → routing → clean handoff
• Trust boundaries visible: 不自动发送, Human confirmation
• Believable scenario pack (38+27+23 pass)
• Office-like handoff: one block, next move, collected/still needed
• Turn 2+ fast (50–200 ms for simple follow-ups)

Top risks:
• Turn 1 latency (1.5–5 s; cold start worse)
• LC-AC3 edge case (early handoff)
• Product in lab nav; two entry points
• No inbox sync; manual paste

Redeploy needed: Frontend only (loading text polish)

What to do next:
1. Run live demo: SIM1→SIM2→SIM3
2. Ask Chen Kui 5 value validation questions
3. Pre-warm backend; use Offline if turn 1 slow
4. Do NOT open new features
```

---

*End of report*
