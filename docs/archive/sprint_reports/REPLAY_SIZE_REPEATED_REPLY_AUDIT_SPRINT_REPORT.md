# Replay Size + Repeated Reply Audit Sprint Report

**Sprint:** Chen Kui Insurance Unified Entry — Replay Size + Repeated Reply Audit  
**Date:** 2026-03-12

---

## 1. Replay audit

### Is it too small?

**Before:** Replay area had `maxHeight: 240px`, drawer `width: 420px`, message padding 8px. For 3–4 turn conversations (6–8 bubbles), the viewport was cramped. Users reported the replay window felt too small to clearly inspect multi-turn differences.

**Classification:** Too small — clearly hurting usefulness for trial/demo inspection.

### What was changed?

| Change | File | Before | After |
|--------|------|--------|-------|
| Replay max height | `SimulationAssistant.tsx` | 240px | 360px |
| Replay min height | `SimulationAssistant.tsx` | — | 200px |
| Drawer width | `SimulationAssistant.tsx` | 420px | 480px |
| Message padding | `SimulationAssistant.tsx` | 8px | 10px |
| Message spacing | `SimulationAssistant.tsx` | — | marginBottom: 6px |

---

## 2. Repeated-reply audit

### Which top scenarios showed the issue?

| Scenario | Turn 2 system reply | Turn 3 system reply (before) | Issue |
|----------|---------------------|------------------------------|-------|
| **SIM1** Cancellation risk | 好的，收到了。办公室会尽快处理 | 好的，明白了。办公室会尽快处理 | Nearly identical; turn 3 says "already paid" + "what matters most" |
| **SIM2** Missing document | 好的，收到了。办公室会尽快处理 | 好的，收到了。办公室会尽快处理 | **Identical**; turn 3 asks "what is garaging proof?" |
| **SIM5** Claim intake | 您说的情况已整理好了... | 您说的情况已整理好了... | **Identical**; turn 3 asks "what matters most?" |
| **SIM6** Premium review | 好的，收到了... | 您说的情况已整理好了... | Slightly different but both generic |
| SIM3, SIM15 | — | — | Add-car flow already differentiated ✓ |

### Root cause

1. **Overly broad sent marker:** Bare `"发"` in `sent_markers` matched `"要发什么"` (what to send) as if the customer said "I sent" — causing SIM2 turn 3 to wrongly use `other_received` ("好的，收到了").

2. **No clarification handling:** When the customer asked follow-up questions after handoff (e.g. "已经付了" / "最要紧做什么" / "什么意思" / "要发什么"), the triage always used the same generic handoff template (`other_received`, `other_corrected`, or `other`). No distinct reply for clarification questions.

3. **Template selection order:** `sent_markers` and `correction_markers` were checked before any clarification logic, so clarification questions fell through to generic handoff.

---

## 3. Fixes made

### Exact files changed

| File | Change |
|------|--------|
| `ui/src/components/simulation/SimulationAssistant.tsx` | Replay maxHeight 240→360, minHeight 200, drawer width 420→480, padding 8→10, marginBottom 6 |
| `configs/clients/chen_kui/handoff_phrases.json` | Added `other_clarification`: "您说的已收到，办公室会优先核实，有结果会联系您。" |
| `services/fiqa_api/inbox_triage/triage.py` | Refined `sent_markers` (removed bare "发"); added `clarification_markers` and `other_clarification` branch before sent/correction |

### Why

- **Replay:** Larger viewport and spacing make 3–4 turn conversations easier to read and compare.
- **Sent markers:** Dropping bare `"发"` avoids matching "要发什么" and similar question phrases.
- **Clarification handoff:** When the customer asks "已经付了", "最要紧", "什么意思", "要发什么", "先看什么", use `other_clarification` so turn 3 gets a distinct reply instead of repeating the generic handoff.

---

## 4. Before vs after

### What improved

| Scenario | Before (Turn 2 vs Turn 3) | After |
|----------|---------------------------|-------|
| SIM1 | 好的，收到了 vs 好的，明白了 (nearly same) | 好的，收到了 vs **您说的已收到，办公室会优先核实，有结果会联系您。** |
| SIM2 | 好的，收到了 vs 好的，收到了 (identical) | 好的，收到了 vs **您说的已收到，办公室会优先核实，有结果会联系您。** |
| SIM5 | 您说的情况已整理好了 vs 您说的情况已整理好了 (identical) | 您说的情况已整理好了 vs **您说的已收到，办公室会优先核实，有结果会联系您。** |
| SIM6 | 好的，收到了 vs 您说的情况已整理好了 | 好的，收到了 vs **您说的已收到，办公室会优先核实，有结果会联系您。** (with "先看什么" marker) |

Replay: 360px height, 480px width, clearer spacing between turns.

### What still remains weak

- `other_clarification` is still a generic handoff; it does not explain "garaging proof" or "what matters most" in detail. Broker receives the case and can clarify.
- No change to handoff timing; handoff still occurs at turn 2 for SIM1/SIM2/SIM5/SIM6.
- Add-car flows (SIM3, SIM15) were already differentiated; no change.

---

## 5. Validation summary

| Check | Result |
|-------|--------|
| `npm run build` (ui/) | ✓ Built successfully |
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `run_multi_turn_simulations.py` | 38/38 strong |
| `guardrail_inbox_triage.sh` | PASS |
| `unified_intake_smoke_check.sh` | Guardrail PASS (manual UI steps printed) |
| Simulation Assistant scenarios | 15/15 Normal |

---

## 6. Redeploy readiness

| Component | Redeploy? | Notes |
|-----------|-----------|-------|
| **Frontend** | Yes | `SimulationAssistant.tsx` — Replay sizing, drawer width |
| **Backend** | Yes | `triage.py` — handoff phrase selection; `handoff_phrases.json` — new phrase |

**What to verify online after redeploy:**

1. Open Simulation Assistant → run SIM1 (Cancellation risk) through all 3 turns.
2. Confirm Replay panel is taller and easier to read.
3. Confirm Turn 3 reply is "您说的已收到，办公室会优先核实，有结果会联系您。" (not "好的，收到了" or "好的，明白了").
4. Run SIM2, SIM5, SIM6 and confirm turn 3 replies are differentiated from turn 2.

---

## 7. 中文总结

- **Replay 窗口是不是太小？** 是。之前 240px 高、420px 宽，3–4 轮对话很难看清。已改为 360px 高、480px 宽，气泡间距加大。
- **重复回复是不是确实有问题？** 是。SIM1/SIM2/SIM5 的 Turn 2 和 Turn 3 系统回复几乎或完全一样，客户明明说了不同内容（如「已经付了」「最要紧做什么」「garaging proof 什么意思」）。
- **这次修了什么？** ① Replay 区域变大、更易读；② 去掉过于宽泛的「发」标记，避免把「要发什么」当成「我发了」；③ 新增「澄清类」回复：当客户问「已经付了」「最要紧」「什么意思」「要发什么」「先看什么」时，用「您说的已收到，办公室会优先核实，有结果会联系您。」，不再重复通用 handoff。
- **修完以后最该再看哪几个场景？** SIM1（取消风险）、SIM2（缺材料）、SIM5（理赔）、SIM6（保费审核）— 重点看 Turn 3 是否与 Turn 2 明显不同，以及 Replay 是否足够大、易读。
