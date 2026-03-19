# Lightweight State Machine + Field Progress + Multi-Turn Strategy Sprint Report

**Sprint:** Lightweight State Machine + Field Progress + Multi-Turn Strategy  
**Date:** 2026-03-12  
**Budget:** 20–40 minutes focused work  
**Status:** Complete

---

## 1. Blueprint summary

A lightweight conversation-state framework was designed and partially implemented. The system now derives **follow_up_type** (new_info, correction, already_sent, clarification_question, urgency_question, next_step_question) and **collection_stage** (collecting | enough_for_handoff) from the conversation. These signals drive reply strategy: clarification questions get answered first; already_sent gets warmer handoff phrasing; corrections get "好的，明白了". This is **not** a heavy workflow engine—it is a thin layer that improves multi-turn reply quality without redesigning the app.

---

## 2. Lightweight state machine design

| Dimension | Meaning | Implemented? |
|-----------|---------|--------------|
| **issue_category / flow** | Which of the 5 flows | ✓ (existing) |
| **collection_stage** | collecting \| enough_for_handoff | ✓ (new) |
| **collected_fields** | What we've extracted | ✓ (existing) |
| **still_needed_fields** | What would improve the case | ✓ (existing) |
| **follow_up_type** | Type of later-turn message | ✓ (new) |
| **ready_for_handoff** | handoff_ready | ✓ (existing) |
| **human_confirmation_required** | needsHumanConfirmation badge | ✓ (existing) |

**What state helps decide:** Ask one more vs hand off; explain vs collect; warmer vs generic handoff; which reply template fits.

---

## 3. Field progress model

Per-flow field progress tables were defined in `docs/LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md`:

| Flow | Critical fields | Enough for handoff |
|------|-----------------|--------------------|
| Add-car | year, model, zip, VIN | (year+model OR VIN) + (zip OR delivery OR driver) |
| Missing doc | requested_item, sent_status | Item identified + sent status clear |
| Cancellation / payment | notice, screenshot, paid_claimed | Notice or screenshot or "I sent it" |
| Claim | accident_reported, photos, other_driver | 1–2 turns with accident details |
| Renewal | premium_concern, policy_bill_sent | Policy or bill mentioned |

---

## 4. Follow-up type strategy

| follow_up_type | Detection | Reply action |
|----------------|-----------|--------------|
| **new_info** | New field values | Acknowledge + ask next OR hand off |
| **correction** | "不是", "说错了" | other_corrected phrase |
| **already_sent** | "发了", "sent", "截图" | other_received ("好的，收到了") |
| **clarification_question** | "什么意思", "要发什么", "garaging 是什么意思" | **Answer first** + handoff suffix (SIM2 fix) |
| **urgency_question** | "最要紧", "是不是今天" | Answer + handoff |
| **next_step_question** | "先看什么", "what matters most" | Answer + handoff |

---

## 5. Human confirmation boundaries

Defined in blueprint:

- **Human-confirm required:** VIN, primary_driver, policy_number, due_date/payment_status, customer_says_sent_*, quote implications
- **Mark "Human confirmation recommended":** customer_says_sent_*, vin, primary_driver, payment/cancellation category
- **Avoid overcommitting:** Do not state premium as final; do not promise carrier received when customer said sent

---

## 6. Implementation changes made

| Change | File | Purpose |
|--------|------|---------|
| Blueprint doc | `docs/LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md` | Full design: state machine, field progress, follow-up strategy, trust |
| `_derive_follow_up_type()` | `triage.py` | Derive follow-up type from last customer message |
| `_derive_collection_stage()` | `triage.py` | Derive collecting \| enough_for_handoff |
| Handoff phrase selection | `triage.py` | Use follow_up_type instead of inline marker checks |
| Expose follow_up_type, collection_stage | `triage.py` | Add to triage_conversation result |
| Doc map update | `docs/PROJECT_DOC_SYSTEM_MAP.md` | Link to blueprint |

---

## 7. Simulation findings

| Pack | Result |
|------|--------|
| Multi-turn (MT1–MT25+) | PASS |
| Simulation Assistant (SIM1–SIM15) | 15/15 Normal |
| Guardrail inbox triage | PASS |
| Unified intake smoke check | PASS |
| UI build | ✓ |

**Key scenarios verified:** SIM1 (Cancellation risk), SIM2 (Missing document / garaging clarification), SIM3 (Add-car 3-turn), SIM5 (Claim), SIM6 (Premium review), SIM15 (Add-car 3-turn strongest proof).

---

## 8. Improvement loop results

No regression. The refactor to use `_derive_follow_up_type()` centralizes follow-up detection and makes reply routing more maintainable. SIM2 document clarification (garaging proof 是什么意思) continues to work: answer first, then handoff suffix.

---

## 9. Validation summary

| Check | Result |
|-------|--------|
| `cd ui && npm run build` | ✓ |
| `run_inbox_triage_scenarios.py` | (run with backend) |
| `run_multi_turn_simulations.py` | PASS (38 scenarios) |
| `guardrail_inbox_triage.sh` | PASS |
| `unified_intake_smoke_check.sh` | PASS |

---

## 10. Redeploy readiness

- **Backend:** No breaking changes. New fields `follow_up_type`, `collection_stage` are additive. Redeploy when convenient.
- **Frontend:** No changes. Build passes.

---

## 11. Recommended next step

1. **Use follow_up_type in broker UI** (optional): Show "Clarification" or "Already sent" badge on case cards when useful.
2. **Expand clarification detection:** Add more markers for "what to send" / "what office reviews first" if scenarios surface gaps.
3. **Run SIM1–SIM6, SIM15** before Chen Kui trial as quick sanity check.

---

## 12. 中文宏观总结

本次 sprint 设计了轻量级对话状态框架，并实现了最小可用层：系统现在会推导 **follow_up_type**（新信息、更正、已发送、澄清问题、紧急问题、下一步问题）和 **collection_stage**（收集中 | 可交接）。这些信号驱动回复策略：澄清问题先回答再交接；已发送用更暖的「好的，收到了」；更正用「好的，明白了」。这不是重型工作流引擎，而是一层薄逻辑，提升多轮对话质量。SIM1–SIM15 全部通过，无回归。

---

## 13. COPY/PASTE SUMMARY BLOCK

```
# Lightweight State Machine Sprint — Summary

**One-paragraph summary:** A lightweight conversation-state layer was designed and implemented. The system derives follow_up_type (new_info, correction, already_sent, clarification_question, etc.) and collection_stage (collecting | enough_for_handoff) from the last customer message. These drive reply strategy: clarification → answer first; already_sent → warmer handoff; correction → "好的，明白了". Not a workflow engine—a thin layer for better multi-turn behavior.

**3 most important concepts:**
1. follow_up_type — what kind of later-turn message (clarification vs already_sent vs correction)
2. collection_stage — collecting vs enough_for_handoff
3. Reply strategy by type — answer clarification before handoff; warmer phrasing for already_sent

**Minimum per-flow field progress:** Add-car: year+model+zip; Missing doc: item+sent status; Cancellation: notice/screenshot; Claim: accident+photos; Renewal: policy/bill.

**Code changes:** Added _derive_follow_up_type(), _derive_collection_stage(); handoff phrase selection now uses follow_up_type; triage result exposes follow_up_type and collection_stage.

**What improved:** Centralized follow-up detection; more maintainable reply routing; explicit state signals for future UI/analytics.

**What remains weak:** follow_up_type detection is keyword-based; some edge cases (e.g. "要发什么" vs "发你了") may need tuning; no UI display of follow_up_type yet.

**Next step:** Use follow_up_type in broker UI (optional badge); run SIM1–SIM6, SIM15 before trial.
```
