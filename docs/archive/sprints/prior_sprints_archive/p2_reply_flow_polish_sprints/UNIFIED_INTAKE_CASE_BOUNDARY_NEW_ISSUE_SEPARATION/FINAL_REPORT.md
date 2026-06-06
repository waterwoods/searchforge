# Unified Intake Case Boundary + New-Issue Separation Report

## 1. Sprint theme

- **Evaluated / fixed:** Append-flow behavior when an existing Unified Intake case receives a new customer message—especially **same-case continuation** vs **new operational issue** vs **borderline pivots**.
- **Why now:** The product was strong on single-intake flows but could still feel like “one endless chat” after handoff; brokers lacked a **lightweight boundary signal**, and customers sometimes saw **off-topic drafts** (e.g. add-car asks) when they had pivoted to claim/billing.

## 2. Document set created

| Doc | Path |
|-----|------|
| Blueprint | `docs/sprints/UNIFIED_INTAKE_CASE_BOUNDARY_NEW_ISSUE_SEPARATION/BLUEPRINT.md` |
| Detection spec | `DETECTION_SPEC.md` (same folder) |
| Customer UX spec | `CUSTOMER_BOUNDARY_UX_SPEC.md` |
| Broker workbench spec | `BROKER_WORKBENCH_BOUNDARY_SPEC.md` |
| Scenario pack notes | `BOUNDARY_SCENARIO_PACK.md` |
| Execution outline | `EXECUTION_OUTLINE.md` |
| Acceptance criteria | `ACCEPTANCE_CRITERIA.md` |
| Founder inspection | `FOUNDER_INSPECTION_NOTES.md` |
| Scenario data | `configs/case_boundary_append_scenarios.json` |
| Runner | `scripts/run_case_boundary_battery.py` |
| Guardrail hook | `scripts/guardrail_inbox_triage.sh` step `[7c]` |

## 3. Baseline audit

| Risk | Finding |
|------|---------|
| **Biggest boundary weakness** | `triage_for_append` always forced handoff but did not classify **thread pivots**; customer draft followed **merged-text triage** and could mismatch the customer’s latest intent. |
| **Biggest broker cleanliness risk** | Single case record absorbing **multiple operational issues** without a visible **split-risk** hint. |
| **Biggest customer confusion risk** | After add-car context, a **claim/billing** message could still get a **quote-collection** style reply. |
| **Safest high-value fix** | Rule-based **append-only** boundary layer + broker prefixes + short continuity copy (no new ticketing stack). |

## 4. Scenario battery overview

- **18** append scenarios across: same-case materials/correction/zip/extra vehicle; **new_issue** claim/billing/remove/premium↔add-car; **borderline** vague pivot + office hours + ambiguous “另一个保险问题”.
- **Use:** Regression for append semantics and founder-facing proof that the portal distinguishes threads **without** extra chat turns.

## 5. Scenario-by-scenario results

All **18/18 PASS** under `LLM_GENERATION_ENABLED=0` (`scripts/run_case_boundary_battery.py`).

| ID | Expected | Observed | Judgment |
|----|----------|----------|----------|
| CB-01 | same_case | same_case | Strong |
| CB-02 | new_issue | new_issue | Strong |
| CB-03 | same_case | same_case | Strong |
| CB-04 | new_issue | new_issue | Strong |
| CB-05 | borderline | borderline | Acceptable (human confirm) |
| CB-06 | borderline | borderline | Acceptable |
| CB-07 | new_issue | new_issue | Strong |
| CB-08 | new_issue | new_issue | Strong |
| CB-09 | borderline | borderline | Acceptable |
| CB-10 | new_issue | new_issue | Strong |
| CB-11 | new_issue | new_issue | Strong |
| CB-12 | same_case | same_case | Strong |
| CB-13 | same_case | same_case | Strong |
| CB-14 | new_issue | new_issue | Strong |
| CB-15 | new_issue | new_issue | Strong |
| CB-16 | new_issue | new_issue | Strong |
| CB-17 | borderline | borderline | Acceptable |
| CB-18 | same_case | same_case | Strong |

**Backlog classification:** Most rows **rule-based good enough**; borderline rows **human confirmation better**; long messy narratives **candidate for future LLM assist** (not required for this sprint).

## 6. What was changed

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | Prior/last domain detection, `_classify_append_case_boundary`, `_apply_append_case_boundary`, `triage_for_append` wiring |
| `services/fiqa_api/inbox_triage/case_store.py` | Persist optional `case_boundary` on append |
| `ui/src/api/inboxTriage.ts` | Optional `case_boundary` on types |
| `ui/src/pages/UnifiedIntakePage.tsx` | Workbench tags when boundary set |
| `configs/case_boundary_append_scenarios.json` | New scenario pack |
| `scripts/run_case_boundary_battery.py` | New runner |
| `scripts/guardrail_inbox_triage.sh` | Added `[7c]` battery |

**Product behavior:** On append, possible **new_issue** or **borderline** states now adjust **customer reply**, **broker_next_step**, **conversation_summary**, and (borderline) **human_confirmation**; workbench shows **boundary tags**.

## 7. Overall pattern analysis

| Topic | Assessment |
|-------|-------------|
| **Stronger now** | Append pivots (add-car → claim/billing/remove), broker-visible split risk, customer continuity copy. |
| **Still weak** | Prior domain = **coarse**; threads without clear markers stay `generic`; secondary-intent note still **last-bubble biased**. |
| **Rule-based enough** | Short pivots with clear domain markers; factual same-case follow-ups. |
| **Human confirmation** | Borderline pivots + office-hours-on-quote-thread. |
| **LLM assist later** | Long ambiguous “story” messages with weak markers; nuanced “related but different policy” cases. |

## 8. Fix-now / Fix-next / Human-confirm / LLM-assist

| Bucket | Items |
|--------|--------|
| **Fix-now** | Shipped in this sprint (append boundary layer + tests + UI tags). |
| **Fix-next** | Enrich prior domain using **case metadata** (e.g. stored `issue_category`) when thread text is thin; optional `same_case` explicit value for analytics. |
| **Human-confirm** | All `borderline` rows; any append where broker disagrees with triage category vs boundary tag. |
| **LLM-assist** | Soft pivots with no domain hits; multi-paragraph mixed stories. |

## 9. Final broker-confidence judgment

- **More portal-like?** Yes for **append**, where split-risk is now visible and customer copy respects **continuity**.
- **Biggest strength:** Low-risk, **deterministic** behavior under `LLM_GENERATION_ENABLED=0` with full guardrail green.
- **Biggest remaining weakness:** **Generic** prior threads and **non-append** flows do not yet carry the same boundary semantics.
- **Best next step:** Optionally pass **stored case `issue_category`** into append triage to tighten `prior` when customer text is minimal.

## 10. 中文宏观总结

这轮 sprint 针对 **“已有 case 里再来一条客户消息”** 的场景，补上 **case 边界**：系统会判断更像 **继续原 case**、**明显换了一个业务事项**，还是 **边界不清需要人工确认**。实现上主要在 `triage_for_append` 增加规则层，给客户更清楚的 **“前一件事办公室继续 / 新问题也转办公室”** 表述，给经纪人 `broker_next_step` 和 summary 加 **可扫读的边界提示**，并在工作台用标签标出 **可能新事项** 或 **建议确认**。加车 → 理赔/账单/删车等 **跨域** 组合已用 18 条自动化用例锁住；**模糊转折**（例如“还有一个问题”、营业时间）走 **borderline + 人工确认**。整体更像成熟入口的 **工单意识**，但仍不是完整 ticketing；**泛化 prior** 与 **非 append** 会话仍可后续增强。
