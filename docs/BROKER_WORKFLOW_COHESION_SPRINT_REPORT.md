# Broker Workflow Cohesion Sprint Report

**Sprint:** Broker Workflow Cohesion Sprint  
**Date:** 2026-03-10  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry — Broker Workbench cohesion across 4 structured flows

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|------|
| **Stage 1 — Define unified broker workflow language** | ✅ Completed | Section 0 added to BROKER_HANDOFF_CLARITY_GUIDE.md; Case focus → Your next move → Collected → Still needed → Full conversation |
| **Stage 2 — Improve cross-flow consistency** | ✅ Completed | Section ordering, label consistency; smoke check step 15 added |
| **Stage 3 — Strengthen "Your next move"** | ✅ Completed | All 4 flows: more operational, action-oriented wording |
| **Stage 4 — Broker-centered simulation** | ✅ Completed | Guardrail PASS; multi-turn 19/19; CLI verification for 4 flows |
| **Stage 5 — Identify high-value cohesion issues** | ✅ Completed | Next-move wording was primary; addressed in Stage 3 |
| **Stage 6 — Improvement loop 1** | Skipped | First pass sufficient; no repeated usability issues |
| **Stage 7 — Optional improvement loop 2** | Skipped | Not needed |
| **Stage 8 — Founder demo proof** | ✅ Completed | 5 proof walkthroughs below |
| **Stage 9 — Regression + safety** | ✅ Completed | Runbook, smoke check updated |
| **Stage 10 — Audit + judgment** | ✅ Completed | Verdict: Accept |

---

## 2. Unified broker workflow language

| Order | Section | What broker sees | Why |
|-------|---------|------------------|-----|
| 1 | **Case focus** | Add car quote · Premium review · Claim intake · Missing document | Triage at a glance |
| 2 | **Your next move** | One operational sentence | Action clarity |
| 3 | **Collected** | Green chips | Avoid re-asking |
| 4 | **Still needed** | Orange chips | Next ask clarity |
| 5 | **Full conversation** | Raw text | Verification |

**Per-flow next move (after sprint):**

| Flow | Your next move |
|------|----------------|
| Add car | Confirm any missing driver, ZIP, or VIN if needed; then quote or add same day. |
| Renewal | Review renewal notice and current premium; confirm remove-vehicle or coverage-adjust intent, then send 1–2 realistic options. |
| Claim | Guide client to collect evidence and start claim reporting; confirm photos and other-driver info received. |
| Missing document | Verify whether customer-resubmitted items were received; request any still-missing items. |

**Intentionally kept flexible:** Field labels vary by flow (Year/Make/Model vs Requested: Declaration page). Same mental model, not perfect sameness.

---

## 3. UI / backend / product changes made

| File | Change | Purpose |
|------|--------|---------|
| `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` | Added Section 0: Unified Broker Workflow Language | Single source of truth for cross-flow structure |
| `services/fiqa_api/inbox_triage/triage.py` | broker_next_step for add-car | "Confirm any missing driver, ZIP, or VIN if needed; then quote or add same day." |
| `services/fiqa_api/inbox_triage/triage.py` | broker_next_step for renewal | "Review renewal notice and current premium; confirm remove-vehicle or coverage-adjust intent, then send 1–2 realistic options." |
| `services/fiqa_api/inbox_triage/triage.py` | broker_next_step for claim | "Guide client to collect evidence and start claim reporting; confirm photos and other-driver info received." |
| `services/fiqa_api/inbox_triage/triage.py` | broker_next_step for missing_document | "Verify whether customer-resubmitted items were received; request any still-missing items." |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | Broker handoff note | Unified workflow language reference |
| `scripts/unified_intake_smoke_check.sh` | Step 15 | Verify 4 flows show consistent Collected/Still needed layout |

---

## 4. Validation and improvement loops

| Check | Result | Notes |
|-------|--------|-------|
| `bash scripts/guardrail_inbox_triage.sh` | PASS | 49/49 scenarios, multi-turn, adversarial, complex |
| `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` | 19/19 strong | All flows pass |
| `cd ui && npm run build` | PASS | UI compiles |
| CLI add-car | PASS | New broker_next_step |
| CLI renewal | PASS | New broker_next_step |
| CLI claim | PASS | New broker_next_step |
| CLI missing-doc | PASS | New broker_next_step |

**Issues found:** None blocking. LC-AC3 (driver correction) remains acceptable friction from prior sprint.

**Fixes made:** broker_next_step wording for all 4 flows; unified workflow language doc.

---

## 5. Product proof strength

| Question | Answer |
|----------|--------|
| Do the 4 flows feel like one family? | Yes. Same section order, same Collected/Still needed layout, consistent next-move style. |
| Is "Your next move" meaningfully better? | Yes. More operational, action verbs, office-focused. |
| Is broker scanning easier? | Yes. Next move tells broker what to do faster. |
| Is this more convincing in a founder demo? | Yes. Cohesive workbench language supports the story. |

---

## 6. Validation summary

| Check | Result | Protects |
|-------|--------|----------|
| `bash scripts/guardrail_inbox_triage.sh` | PASS | Scenario pack, multi-turn, adversarial, complex |
| `cd ui && npm run build` | PASS | UI compile |
| `scripts/unified_intake_smoke_check.sh` | PASS | Guardrail + manual UI steps including 4-flow consistency |

---

## 7. Business / platform value

| Area | Improvement |
|------|-------------|
| **Broker mental load** | Next move is shorter and more action-oriented; broker knows what to do faster. |
| **Repeated intake work** | Same mental model across flows reduces mental switching. |
| **Platform story** | Workbench feels more like one operating console, not four separate tools. |

---

## 8. Remaining blocker(s)

1. **LC-AC3 friction:** Driver correction scenario (from prior sprint) still has minor handoff timing friction.
2. **Field values:** Current display shows field names (Year, Make/Model) not extracted values (2025, Honda CR-V).
3. **Non-structured cases:** Payment/cancellation, DMV/SR-22 still use conversation_summary only; no structured chips.

---

## 9. Recommended next step

**Tighten one broker workflow validation step** — e.g. add a compact script that asserts broker_next_step contains action verbs for the 4 structured flows. Keep guardrail as primary protection.

---

## 10. 中文或中英混合宏观总结

**这次 broker workflow cohesion 变好了什么：**
- 4 条主线（加车、续保、理赔、缺材料）现在有统一的 broker workflow language：Case focus → Your next move → Collected → Still needed → Full conversation。
- "Your next move" 全部改成更操作化的句子：broker 一眼能看出下一步该做什么。
- 加车：Confirm any missing driver, ZIP, or VIN if needed; then quote or add same day.
- 续保：Review renewal notice and current premium; confirm remove-vehicle or coverage-adjust intent.
- 理赔：Guide client to collect evidence and start claim reporting.
- 缺材料：Verify whether customer-resubmitted items were received; request any still-missing items.

**现在这 4 条主线是不是更像同一套后台语言：**
- 是。同一套 section 顺序、同一套 Collected/Still needed 布局、同一套 next-move 风格。

**经纪人一眼能不能更快看懂：**
- 能。Next move 更短、更 actionable，broker 不用再读长句就能知道下一步。

**还缺什么：**
- 字段值（如 2025, Honda CR-V）未单独展示；非结构化 case（payment、DMV）仍只有 conversation_summary。

**这次对陈奎和以后别的客户有什么帮助：**
- 工作台更像一个真实办公室工具，减少 mental load，founder demo 更有说服力。

---

## 11. Practical broker-workflow cheat sheet

| Item | What |
|------|------|
| **Case focus** | Add car quote · Premium review · Claim intake · Missing document |
| **Your next move** | One operational sentence: what the office should do next |
| **Collected** | Green chips: what the customer already provided |
| **Still needed** | Orange chips: what broker should ask or verify next |
| **What broker still does manually** | Live quote, carrier underwriting, VIN validation, send reply, verify carrier received |

---

## 12. Broker-value summary

| Category | Strength | Notes |
|----------|----------|-------|
| **Add-car** | Strongest | Structured chips; next move: confirm missing → quote same day |
| **Renewal** | Strong | Structured chips; next move: review notice → confirm intent → options |
| **Claim** | Strong | Structured chips; next move: guide evidence → confirm received |
| **Missing document** | Strong | Structured chips; next move: verify received → request still-missing |
| **Non-structured (control)** | Acceptable | Graceful fallback to conversation_summary |

---

## 13. Live proof walkthroughs

### 1. Add-car

| Step | Content |
|------|---------|
| Customer | 客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价 |
| Broker sees first | Case focus: Add car quote · Your next move: Confirm any missing driver, ZIP, or VIN if needed; then quote or add same day. |
| Structure | Collected: Year, Make/Model, Delivery · Still needed: Primary driver |
| Demo-strong? | **Yes** |

### 2. Renewal

| Step | Content |
|------|---------|
| Customer | 续保保费太高了，其中一辆去掉会便宜吗 |
| Broker sees first | Case focus: Premium review · Your next move: Review renewal notice and current premium; confirm remove-vehicle or coverage-adjust intent, then send 1–2 realistic options. |
| Structure | Collected: Premium too high, Premium review, Remove vehicle interest · Still needed: Renewal notice or bill, Current premium details, Which vehicle to remove |
| Demo-strong? | **Yes** |

### 3. Claim intake

| Step | Content |
|------|---------|
| Customer | 刚出事故了，要收集什么？ |
| Broker sees first | Case focus: Claim intake · Your next move: Guide client to collect evidence and start claim reporting; confirm photos and other-driver info received. |
| Structure | Collected: Accident reported · Still needed: Photos, Other driver insurance/license, Accident time/location, Police report (if applicable) |
| Demo-strong? | **Yes** |

### 4. Missing document

| Step | Content |
|------|---------|
| Customer | UW follow up - need dec page + garaging proof. 客户说上周发过了 |
| Broker sees first | Case focus: Missing document · Your next move: Verify whether customer-resubmitted items were received; request any still-missing items. |
| Structure | Collected: Requested: Declaration page, Requested: Garaging proof, Customer says sent: Declaration page, Customer says sent: Garaging proof, Customer claims already sent, UW follow-up · Still needed: Verify carrier received |
| Demo-strong? | **Yes** |

### 5. Control non-structured case

| Step | Content |
|------|---------|
| Customer | Notice: Policy will be cancelled in 7 days due to non-payment. |
| Broker sees first | Case focus: Cancellation risk · Your next move: Confirm whether the cancellation is still active, verify any payment already made, and call or text the client today with the exact deadline. |
| Structure | No Collected/Still needed chips; conversation_summary as before |
| Demo-strong? | N/A (control) |

---

*End of sprint report*
