# Simulation Assistant Speed Layer Blueprint

**Sprint:** Simulation Assistant Speed Layer Sprint  
**Date:** 2026-03-13  
**Purpose:** Define the 3-layer speed strategy before implementation.

---

## A. Why Simulation Assistant Feels Slow Today

| Cause | Impact |
|-------|--------|
| **LLM path** | Every turn calls `client.chat.completions.create()` — 1.5–5 s per turn |
| **Cold start** | Cloud Run idle → 5–15 s first request |
| **Retrieval** | Notice/document confusion triggers embedding + Qdrant — +0.5–2 s |
| **Full-chain path** | Every turn goes through full LLM regardless of complexity |
| **Perceived latency** | No loading feedback; user sees nothing until full reply arrives |

**Net:** Warm path ~2–6 s per turn, dominated by LLM. User waits with no feedback.

---

## B. The 3-Layer Speed Strategy

1. **Immediate feedback layer** — Show "Thinking..." / skeleton as soon as user clicks Run/Next turn. Reduces "nothing happened" feeling.
2. **Fast path layer** — For simple turns, use rule-based triage only. Skip LLM. ~50–200 ms instead of 1.5–5 s.
3. **Complex-case LLM layer** — Reserve LLM for turns that actually need it: mixed intent, unclear, first-turn ambiguity, adversarial.

---

## C. What Counts as "Simple" (Fast Path)

| Type | Examples | Why safe for rules |
|------|----------|-------------------|
| **already_sent** | "发你了", "我发了截图", "sent" | Clear pattern; rule handoff phrase works |
| **clarification** | "garaging proof 是什么意思", "要发什么" | Document explanation in rules |
| **missing-doc common** | "declaration page 他又发了一次" | Structured extraction in rules |
| **add-car field** | "2024年的", "90210，下周提车" | Field extraction in rules |
| **next-step question** | "最要紧做什么", "办公室先看什么" | Template-based answer |
| **correction** | "我其实已经付了" | Acknowledge + handoff |
| **minimal follow-up** | "发你了" (2 chars) | Obvious already_sent |

**Decision:** Turn 2+ with last message matching these patterns → fast path.

---

## D. What Counts as "Complex" (LLM Path)

| Type | Examples | Why LLM helps |
|------|----------|---------------|
| **Mixed intent** | "加车，顺便 garaging proof 是什么？" | Two intents; LLM disambiguates |
| **Correction + new info** | "不是那个，是另一辆，2024宝马" | Multiple signals |
| **Unclear category** | Vague first message | Intent classification |
| **Adversarial / noisy** | "都发过了怎么还要" | Emotion + correction |
| **First turn** | Any turn 1 | Often needs intent classification |

**Decision:** Turn 1, or last message has mixed markers / unclear → LLM.

---

## E. Startup-Grade Target

- **Not perfect** — Some edge cases may use LLM when rules could work.
- **Just faster** — Simple turns noticeably faster; complex turns unchanged.
- **Good enough for pilot** — Quality stays acceptable; no regressions.
- **Observable** — Add `triage_path: "fast" | "llm"` for debugging.

---

## Implementation Notes

- **Where:** `triage_conversation()` in `services/fiqa_api/inbox_triage/triage.py`
- **When:** Before `_llm_triage()`; if `_is_fast_path_candidate(merged_text, customer_count)` → use `_rule_based_triage()` instead
- **Loading feedback:** `SimulationAssistant.tsx` — show skeleton when `loading && replayTurns.length > 0`

---

*See also: `docs/SIMULATION_ASSISTANT_SPEED_REALISM_AUDIT_REPORT.md`, `docs/LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md`*
