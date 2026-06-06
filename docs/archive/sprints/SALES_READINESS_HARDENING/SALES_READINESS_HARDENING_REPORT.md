# Sales Readiness Hardening Report

**Sprint:** Sales Readiness Hardening Sprint  
**Created:** 2026-03-17  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

- **What was chosen:** Strengthen Talk to Agent, 2–3 high-value edge cases, and handoff/office readiness so the product feels more trustworthy and trial-ready.
- **Why now:** The standard scenario package clarified the offer, but Talk to Agent still felt lightweight and a few edge cases felt unfinished. The next move is sales-readiness hardening, not broad expansion.

---

## 2. Document Set Created

| Doc | Path |
|-----|------|
| Product / Sales Readiness Blueprint | `01_PRODUCT_SALES_READINESS_BLUEPRINT.md` |
| Talk to Agent Deepening Spec | `02_TALK_TO_AGENT_DEEPENING_SPEC.md` |
| Edge Case Selection Spec | `03_EDGE_CASE_SELECTION_SPEC.md` |
| Handoff / Office Readiness Spec | `04_HANDOFF_OFFICE_READINESS_SPEC.md` |
| Execution Outline | `05_EXECUTION_OUTLINE.md` |
| Acceptance / Sellability Criteria | `06_ACCEPTANCE_SELLABILITY_CRITERIA.md` |
| Founder Demo / Trial Notes | `07_FOUNDER_DEMO_TRIAL_NOTES.md` |
| 10–20 Point Breakdown | `08_10_20_POINT_BREAKDOWN.md` |
| Baseline Audit | `09_BASELINE_AUDIT.md` |

---

## 3. Baseline Audit

| Area | Status |
|------|--------|
| **Talk to Agent (button)** | Acceptable |
| **Talk to Agent (free-text)** | Weak — not implemented |
| **Office display** | Acceptable |
| **Billing "我发你了"** | Acceptable (MT40 exists) |
| **Late correction** | Acceptable (badge exists) |

**Biggest trust weakness:** Talk to Agent only worked via button; typing "联系人工" was ignored.

**Biggest office handoff weakness:** No explicit customer_requested_human badge.

**Biggest edge-case risk:** Billing "我发你了" — needed verification.

---

## 4. 10–20 Point Breakdown (Implemented)

| # | Point | Status |
|---|-------|--------|
| 1 | Talk to Agent trigger: button + free-text markers | ✓ |
| 2 | Customer-facing wording: "好的，已帮您转给陈奎办公室，他们会尽快联系您。" | ✓ |
| 3 | Reassurance copy; no "Are you sure?" | ✓ |
| 4 | Handoff payload: issue_category, broker_next_step, collected_fields | ✓ |
| 5 | Office sees: Case focus "联系人工", broker_next_step | ✓ |
| 6 | Next office action shown | ✓ |
| 7 | Edge cases: Billing "我发你了", Talk to Agent mid-flow, Late correction | ✓ |
| 8 | Billing "我发你了" → already_sent handoff | ✓ (MT40) |
| 9 | Late correction survives handoff | ✓ (append persists follow_up_type) |
| 10 | customer_requested_human badge in workbench | ✓ |
| 11 | handoff_phrases for customer_requested_human | ✓ |
| 12 | Welcome text: "或直接说「联系人工」" | ✓ |
| 13 | MT41 Talk to Agent mid-flow simulation | ✓ |
| 14 | R3b inbox triage scenario for "联系人工" | ✓ |

---

## 5. Iteration Loop 1 — Talk to Agent Strengthening

**What was fixed:**
- Free-text detection: "联系人工", "联系陈奎", "联系办公室", "我要找人工", "我想直接跟人说", etc.
- handoff_phrases for customer_requested_human in config
- customer_requested_human badge in workbench (green)
- inferCaseFocusFromText for Talk to Agent patterns
- Early return in triage_conversation when last customer message requests human
- _classify_with_guardrails early check for talk_to_agent
- VALID_CATEGORIES and RULE_GUIDANCE_CATEGORIES updated

**Why these fixes:** Talk to Agent felt like an escape hatch because it only worked via button. Free-text detection makes it a real service capability.

**What became more trustworthy:** Customer can type "联系人工" at any turn and get immediate handoff. Office sees "客户要求联系人工" badge.

**What became more useful:** Broker gets clear case focus and next move for human-request cases.

**What remained weak:** Mixed-intent + human ("加车报价，但我想跟人说") deferred.

**Worth it:** Yes. Single highest-value trust improvement.

---

## 6. Iteration Loop 2 — Edge Cases

**What was fixed:**
- MT41: Talk to Agent mid-flow (add-car T1 → "算了，我想直接跟人说" T2) → immediate handoff
- MT40 billing "我发你了" verified (already passing)
- Late correction: append_follow_up_message persists follow_up_type; badge shows

**Why these fixes:** Talk to Agent mid-flow is trust-critical; billing already_sent was already working.

**What improved vs Loop 1:** MT41 proves Talk to Agent works mid-conversation.

**What remained weak:** None for in-scope edge cases.

**Worth it:** Yes.

---

## 7. Iteration Loop 3 — Trust / Handoff Hardening

**What was fixed:**
- Welcome text: "或直接说「联系人工」" — makes typing discoverable
- customer_requested_human badge (green) in workbench Case handoff block

**Why these fixes:** Reduces "still feels MVP" moment; improves discoverability.

**What improved vs Loop 2:** Clearer guidance; office sees badge immediately.

**What remained weak:** None for in-scope items.

**Worth it:** Yes.

---

## 8. Optional Loop 4

**Not used.** No clearly valuable, low-risk refinement remained. Stopping is correct.

---

## 9. Validation Summary

| Test | Result |
|------|--------|
| run_inbox_triage_scenarios.py | 64/64 passed |
| run_multi_turn_simulations.py | 41/41 passed |
| guardrail_inbox_triage.sh | PASS |
| unified_intake_smoke_check.sh | PASS |
| audit_state_field_accuracy.py | 7/7 passed |
| UI build | ✓ |

**Limitations:** test_inbox_triage_api.py requires server on 8001 (skipped in smoke when no server).

---

## 10. Deployment / Release Judgment

- **Backend changed:** Yes (triage.py, inbox_triage.py, configs)
- **Frontend changed:** Yes (UnifiedIntakePage.tsx)
- **Backend redeploy needed:** Yes, if using Cloud Run
- **Frontend redeploy needed:** Yes, if using Vercel
- **Founder can inspect:** After redeploy; or locally via `bash scripts/run_demo_local.sh`

---

## 11. Founder Showcase

### Example 1: Talk to Agent (button)
- **Scenario:** Customer clicks "联系人工"
- **What customer experiences:** Immediate handoff; "好的，已帮您转给陈奎办公室，他们会尽快联系您。"
- **What office gets:** Case focus "联系人工"; broker_next_step "Customer requested human contact. Call or message back promptly."; "客户要求联系人工" badge
- **Why better:** Same as before; now reinforced by free-text path
- **Trial readiness:** Formal upgrade path; not escape hatch

### Example 2: Talk to Agent (typed)
- **Scenario:** Customer types "联系人工" or "我想直接跟人说" (any turn)
- **What customer experiences:** Immediate handoff; same reassuring reply
- **What office gets:** Same as Example 1; prior context in conversation_summary when multi-turn
- **Why better:** Previously ignored; now works
- **Trial readiness:** Customer can reach human without finding button

### Example 3: Talk to Agent mid-flow (MT41)
- **Scenario:** Add-car T1 "我买了台宝马X5..."; T2 "算了，我想直接跟人说"
- **What customer experiences:** Handoff at T2 with prior context preserved
- **What office gets:** Case focus "联系人工"; prior add-car context in summary
- **Why better:** Mid-flow human request now honored
- **Trial readiness:** No feeling of being trapped in triage

### Example 4: Billing "我发你了" (MT40)
- **Scenario:** T1 "账单什么意思"; T2 "账单我发你微信了"
- **What customer experiences:** already_sent handoff; no re-ask
- **What office gets:** broker_next_step verify receipt; "Client says already sent" badge when follow_up_type=already_sent
- **Why better:** Verified; no robotic re-ask
- **Trial readiness:** High-frequency flow handled correctly

---

## 12. Final Judgment

- **Biggest gain:** Talk to Agent feels like a real service capability (free-text + mid-flow)
- **Biggest remaining weakness:** Mixed-intent + human escalation deferred
- **Meaningfully strengthens sales-readiness:** Yes
- **Best next step:** Founder trial feedback; consider mixed-intent + human in next sprint if requested

---

## 13. Iteration Log

| Loop | What changed | What got better | What did not improve | Worth it | Next step |
|------|--------------|-----------------|----------------------|----------|-----------|
| 1 | Free-text Talk to Agent; handoff payload; badge | Trust; office clarity | Mixed-intent deferred | Yes | Loop 2 |
| 2 | MT41; verify MT40; correction | Mid-flow proof; edge-case coverage | — | Yes | Loop 3 |
| 3 | Welcome "或直接说"; badge | Discoverability; office visibility | — | Yes | Stop |
| 4 | — | — | — | N/A | — |

---

## 14. 中文宏观总结

**为什么现在做这轮：** 标准场景包已定义清晰，但 Talk to Agent 仍显薄弱，部分 edge case 未完全覆盖。下一步应做销售就绪强化，而非扩大范围。

**主要用了什么方法/技术：** (1) 在 triage 中增加 talk_to_agent 文本检测；(2) 在 triage_conversation 开头做 early return；(3) handoff_phrases 配置 customer_requested_human；(4) 工作台增加「客户要求联系人工」badge；(5) MT41 多轮模拟验证 mid-flow。

**这轮最大的提升：** Talk to Agent 从「只能点按钮」变为「可输入文字、可 mid-flow」，成为正式升级路径，而非弱逃生口。

**还差什么：** 混合意图 + 人工（如「加车报价，但我想跟人说」）暂未处理；inbox 集成、client pack 定制为后续工作。

**下一步最该做什么：** 创始人试用反馈；视情况在下一轮处理 mixed-intent + human。

---

## 15. COPY/PASTE FOUNDER BLOCK

**Biggest sales-readiness improvement:** Talk to Agent now works when the customer types "联系人工" or "我想直接跟人说" at any turn, not only when they click the button. It feels like a real service capability.

**Biggest remaining weakness:** Mixed-intent + human (e.g. "加车报价，但我想跟人说") is deferred.

**Makes the product more sellable/reusable:** Yes. Office sees "客户要求联系人工" badge; broker gets clear next move.

**Redeploy needed:** Yes (backend + frontend if using Cloud Run + Vercel).

**What Andy should inspect next:** (1) Click "联系人工" → handoff; (2) Type "联系人工" in new conversation → handoff; (3) Add-car T1, then "算了，联系人工" T2 → handoff; (4) Open Talk-to-Agent case in workbench → see badge and case focus.

---

## 16. REQUIRED CROSS-WINDOW BLOCK

**Current product/package maturity:** Strong. 7 scenarios; multi-turn; workbench; handoff. Talk to Agent now a real capability.

**Biggest improvements:** (1) Talk to Agent free-text + mid-flow; (2) customer_requested_human badge; (3) MT41 proof; (4) Welcome "或直接说「联系人工」".

**Biggest remaining weaknesses:** Mixed-intent + human deferred; inbox integration deferred.

**Direction correct:** Yes. Sales-readiness hardening was the right move.

**Best next recommendation:** Founder trial; collect feedback; consider mixed-intent + human if requested.

**Current IT technical backbone:** Python/FastAPI backend; React/TypeScript/Vite frontend; triage engine (rule + optional LLM); configs (markers, handoff_phrases); local JSON case store; Cloud Run + Vercel deploy.

---

## 17. REQUIRED SHORT OVERVIEW

### 为什么做这件事
标准场景包已清晰，但 Talk to Agent 仍显薄弱，部分 edge case 未完全覆盖。下一步应做销售就绪强化。

### 主要用了什么方法/技术
triage 增加 talk_to_agent 文本检测；triage_conversation early return；handoff_phrases 配置；工作台 badge；MT41 多轮模拟。

### 这轮最大的提升
Talk to Agent 从「只能点按钮」变为「可输入、可 mid-flow」，成为正式升级路径。

### 现在还差什么
混合意图 + 人工暂未处理；inbox 集成、client pack 定制为后续工作。

---

## 18. REQUIRED TIME / EFFORT SUMMARY

### 主要做了哪些工作
- 7 份控制文档
- Talk to Agent 自由文本检测与 mid-flow 支持
- customer_requested_human handoff 配置与 badge
- MT41、R3b 场景
- Welcome 文案更新

### 哪些地方比原系统提高了
- Talk to Agent 支持输入与 mid-flow
- 办公室可见「客户要求联系人工」badge
- 欢迎文案提示「或直接说」

### 每一轮大概花了哪些时间 / 精力
- Loop 1: 主要实现（triage、config、UI badge）
- Loop 2: MT41、验证 MT40
- Loop 3: Welcome 文案、badge 完善

### 还有哪些值得下一轮继续做
- 混合意图 + 人工
- inbox 集成
- client pack 定制

---

*End of Sales Readiness Hardening Report*
