# Speed Routing Mainline Blueprint

**Sprint:** Speed Routing Mainline Sprint  
**Date:** 2026-03-13  
**Purpose:** Practical blueprint for the 3-layer speed routing layer.

---

## A. Current Speed Problem

| Cause | Impact |
|-------|--------|
| **LLM path** | Every turn calls `client.chat.completions.create()` — 1.5–5 s per turn |
| **Cold start** | Cloud Run idle → 5–15 s first request |
| **Retrieval** | Document/notice confusion triggers embedding + Qdrant — +0.5–2 s |
| **Full-chain path** | Turn 2+ simple follow-ups still go through LLM when they don't need it |
| **Perceived latency** | User sees nothing until full reply arrives (loading feedback exists but can feel slow) |

**Net:** Warm path ~2–6 s per turn when LLM is used. Turn 1 needs LLM for intent; turn 2+ simple cases (already_sent, clarification, add-car field) do not.

**Why turn 1 vs turn 2+ differ:** Turn 1 is open-ended—user intent is ambiguous. Turn 2+ has context; simple patterns (sent screenshot, year+zip, clarification question) are rule-handlable.

---

## B. Desired 3-Layer Speed-Routing Structure

1. **Immediate feedback layer** — Show "正在整理 case..." + spinner as soon as user clicks Run/Next turn. Reduces "nothing happened" feeling.
2. **Fast path layer** — For simple turn 2+ messages, use `_rule_based_triage()` only. Skip LLM. ~50–200 ms instead of 1.5–5 s.
3. **LLM path layer** — Reserve LLM for turn 1, mixed intent, unclear category, adversarial input.

---

## C. What Counts as "Simple" (Fast Path)

| Type | Examples | Why safe for rules |
|------|----------|-------------------|
| **already_sent** | "发你了", "我发了截图", "sent" | Clear pattern; rule handoff phrase works |
| **clarification** | "garaging proof 是什么意思", "要发什么", "需要再发什么给你吗" | Document explanation in rules |
| **correction** | "不是那个", "我其实已经付了" | Acknowledge + handoff |
| **add-car field** | "2024年的", "90210，下周提车", "我老公开" | Field extraction in rules |
| **next-step question** | "最要紧做什么", "办公室先看什么" | Template-based answer |
| **handoff confirmation** | "可以了", "就这样吧", "好了", "ok" | Short confirmation; hand off |
| **minimal follow-up** | "发你了" (≤15 chars) | Obvious already_sent |

**Decision:** Turn 2+ with last message matching these patterns → fast path.

---

## D. What Counts as "Complex" (LLM Path)

| Type | Examples | Why LLM helps |
|------|----------|---------------|
| **Turn 1** | Any first message | Intent classification needed |
| **Mixed intent** | "加车，顺便 garaging proof 是什么？" | Two intents; LLM disambiguates |
| **Unclear category** | Vague first message | Intent classification |
| **Adversarial / noisy** | "都发过了怎么还要" | Emotion + correction |
| **Correction + new info** | "不是那个，是另一辆，2024宝马" (long, mixed) | Multiple signals; rules can handle short form |

**Decision:** Turn 1, or last message has mixed markers / unclear / long → LLM.

---

## E. Startup-Grade Target

- **Faster enough** — Simple turn 2+ noticeably faster; complex turns unchanged.
- **Not perfect** — Some edge cases may use LLM when rules could work.
- **Good enough for pilot** — Quality stays acceptable; no regressions.
- **Observable** — `triage_path: "fast" | "llm" | "rule"` in response for debugging.

---

## Implementation Location

- **Routing:** `triage_conversation()` in `services/fiqa_api/inbox_triage/triage.py`
- **Fast-path check:** `_is_fast_path_candidate(merged_text, customer_count)`
- **Loading feedback:** `SimulationAssistant.tsx` — "正在整理 case..." + Spin when loading

---

*See also: `docs/SIMULATION_ASSISTANT_SPEED_LAYER_BLUEPRINT.md`, `docs/LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md`*
