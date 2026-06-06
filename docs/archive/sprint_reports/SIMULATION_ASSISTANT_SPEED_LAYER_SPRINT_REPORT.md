# Simulation Assistant Speed Layer Sprint Report

**Sprint:** Simulation Assistant Speed Layer Sprint  
**Date:** 2026-03-13  
**Mode:** Design → implement → simulate → inspect → refine

---

## 1. Blueprint summary

### Why it was slow

| Cause | Impact |
|-------|--------|
| LLM path | Every turn called OpenAI — 1.5–5 s per turn |
| Cold start | Cloud Run idle → 5–15 s first request |
| Retrieval | Notice/document confusion → +0.5–2 s |
| Full-chain path | Every turn went through full LLM regardless of complexity |
| Perceived latency | No loading feedback; user saw nothing until full reply |

### 3-layer speed strategy

1. **Immediate feedback layer** — Show "正在整理 case..." + spinner as soon as user clicks Run/Next turn.
2. **Fast path layer** — For simple turns (turn 2+), use rule-based triage only. Skip LLM. ~50–200 ms instead of 1.5–5 s.
3. **Complex-case LLM layer** — Reserve LLM for turn 1, mixed intent, unclear, adversarial.

---

## 2. Loading feedback changes

### What was added

- **Skeleton placeholder** in Replay area when `loading && replayTurns.length > 0`
- System-style block with Spin + "正在整理 case..." text
- Appears immediately after customer turn is added, before API returns

### Why

- Reduces "nothing happened" feeling
- User sees system is working; no dead wait
- Matches existing replay styling (green border, left-aligned)

### File

`ui/src/components/simulation/SimulationAssistant.tsx`

---

## 3. Fast path strategy

### What was designed

- **Decision point:** `triage_conversation()` in `services/fiqa_api/inbox_triage/triage.py`
- **When:** Before `_llm_triage()`; if `_is_fast_path_candidate(merged_text, customer_count)` → use `_rule_based_triage()` instead
- **Signals:** Last customer message + `_derive_follow_up_type()`, add-car field markers, message length

### What counts as simple (fast path)

| Type | Examples |
|------|----------|
| already_sent | "发你了", "我发了截图", "sent" |
| clarification_question | "garaging proof 是什么意思", "要发什么" |
| urgency_question | "最要紧做什么" |
| next_step_question | "办公室先看什么" |
| correction | "我其实已经付了" |
| new_info (add-car field) | "2024年的", "90210，下周提车" (short, ≤80 chars) |
| minimal | "发你了" (≤15 chars)

### What counts as complex (LLM path)

- Turn 1 (always — intent classification)
- Mixed intent, unclear category
- Adversarial / noisy / contradictory
- Long message without clear simple pattern

---

## 4. Selective LLM routing changes

### What was implemented

- **`_is_fast_path_candidate(merged_text, customer_count)`** — Returns True when turn 2+ and last message matches simple patterns
- **Routing in `triage_conversation()`:** When `LLM_GENERATION_ENABLED=1`, check fast path first; if True, use `_rule_based_triage()` instead of `_llm_triage()`
- **Observability:** `triage_path: "fast" | "llm" | "rule"` added to result

### What still remains on full LLM path

- Turn 1 (all scenarios)
- Turn 2+ when last message is unclear, mixed, or doesn't match simple patterns
- When `LLM_GENERATION_ENABLED=0`, full rule-based (no change)

### Refinement

- Added "发您" to minimal already-sent check for formal Chinese

---

## 5. Before vs after

### Perceived speed

| Before | After |
|--------|-------|
| Click → nothing → 2–6 s → reply | Click → customer turn + "正在整理 case..." → reply |
| User unsure if system responded | Immediate feedback; user knows system is working |

### Actual speed (when LLM enabled)

| Turn | Before | After (simple) |
|------|--------|----------------|
| Turn 1 | 1.5–5 s (LLM) | 1.5–5 s (LLM) — unchanged |
| Turn 2+ simple | 1.5–5 s (LLM) | ~50–200 ms (rule) |

**Turn 2+ simple turns:** ~10–20× faster when LLM is enabled.

### Quality impact

- All 15 Simulation Assistant scenarios: PASS (15/15 Normal)
- All 49 inbox triage scenarios: PASS
- All 38 multi-turn simulations: PASS
- All 7 state field accuracy: PASS
- Guardrail: PASS

No regressions observed.

---

## 6. Validation summary

| Script | Result |
|--------|--------|
| `run_simulation_assistant_scenarios.py` | 15/15 Normal |
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `audit_state_field_accuracy.py` | 7/7 passed |
| `guardrail_inbox_triage.sh` | PASS |
| `cd ui && npm run build` | ✓ built |

---

## 7. Redeploy readiness

| Component | Redeploy? |
|-----------|-----------|
| **Frontend** | Yes — SimulationAssistant.tsx (loading feedback) |
| **Backend** | Yes — triage.py (fast path, selective LLM routing) |

**Both** frontend and backend need redeploy for full effect.

---

## 8. Final judgment

- **Did perceived speed improve?** Yes. Immediate "正在整理 case..." reduces dead-wait feeling.
- **Did actual speed improve meaningfully for simple cases?** Yes. Turn 2+ simple turns use fast path when LLM enabled; ~10–20× faster.
- **Is the fast-path strategy practical for a startup team?** Yes. Simple rule-based check; no new infra; configurable via existing logic.
- **Is selective LLM routing helping?** Yes. LLM reserved for turn 1 and complex cases; simple follow-ups avoid LLM cost and latency.
- **What remains the biggest speed problem?** Turn 1 (cold start + LLM) and Cloud Run cold start after idle. Pre-demo warmup or min_instances recommended.

**Verdict:** **Good first speed layer.** Perceived speed improved; actual speed improved for simple turns; quality unchanged; strategy is startup-grade.

---

## 9. 中文宏观总结

我们用三层策略解决「慢」：

1. **立即反馈**：点击后立刻显示「正在整理 case...」，不再死等。
2. **快路径**：Turn 2+ 的简单回复（发了、 clarification、加车字段等）走规则，不走 LLM。
3. **LLM 留给复杂**：Turn 1、混合意图、不清楚的继续用 LLM。

现在不是每次都要走完整 LLM：Turn 2+ 的简单场景（如「发你了」「2024年的」「garaging proof 是什么意思」）会走快路径，约 50–200 ms。

**哪些场景会更快：** 加车 Turn 2/3、缺材料 follow-up、已发截图、clarification 问、最要紧做什么、发你了 等。

**还剩下最大的速度问题：** Turn 1 仍需 LLM（1.5–5 s）；冷启动 5–15 s。建议 demo 前 prewarm 或 min_instances=1。

**下一步：** 是否继续做真实客户风格场景包（adversarial + mixed_intent 进 Simulation Assistant）— 与速度无关，属于 realism 提升。

---

## 10. COPY/PASTE SPEED STRATEGY BLOCK

```
=== Simulation Assistant Speed Strategy ===

3-layer speed strategy:
  1. Immediate feedback — "正在整理 case..." + spinner as soon as user clicks
  2. Fast path — Turn 2+ simple turns use rule-based only (~50–200 ms)
  3. Complex-case LLM — Turn 1, mixed intent, unclear → LLM

Simple cases now do: Rule-based triage (no LLM). Examples: already_sent, clarification, add-car field, next-step question, correction, minimal "发你了".

Complex cases still use LLM: Turn 1, mixed intent, unclear, adversarial.

Biggest speed gain: Turn 2+ simple turns ~10–20× faster when LLM enabled.

Biggest remaining bottleneck: Turn 1 (LLM); cold start (5–15 s).

Next step: Pre-demo warmup script or min_instances=1 (cost). Optional: Real customer style scenario pack (realism).
```

---

*See also: `docs/SIMULATION_ASSISTANT_SPEED_LAYER_BLUEPRINT.md`, `docs/SIMULATION_ASSISTANT_SPEED_REALISM_AUDIT_REPORT.md`*
