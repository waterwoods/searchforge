# Long-Tail Generic Customer Reply Externalization Report

## 1. Sprint theme
- Reviewed remaining long-tail generic customer-visible replies still embedded in `inbox_triage` reply generation.
- Improved same-industry A/B voice isolation with a small, low-risk wording-only externalization batch.
- Timing: this follows high-frequency and append/boundary/residual copy sprints; focus shifted to lower-frequency polish lines.

## 2. Document set created
- `01_BLUEPRINT.md`
- `02_LONG_TAIL_REPLY_AUDIT_SPEC.md`
- `03_EXTERNALIZATION_DESIGN_SPEC.md`
- `04_AB_SCENARIO_PACK_SPEC.md`
- `05_EXECUTION_OUTLINE.md`
- `06_ACCEPTANCE_CRITERIA.md`
- `07_FOUNDER_INSPECTION_NOTES.md`
- `08_FINAL_REPORT.md`
- `long_tail_ab_scenario_battery.json`

## 3. Long-tail reply audit
- Residual hardcoded long-tail customer-visible families found in `triage.py`:
  - `missing_signature`
  - `underwriting_followup`
  - `renewal_reminder`
  - `informational`
- Selected for this batch: all four above because they are:
  - noticeable to customers,
  - generic across same-industry brokers,
  - low risk to externalize (wording-only),
  - already naturally compatible with the existing template/override layer.
- Kept in code for now:
  - category detection and handoff control logic,
  - retrieval-dependent dynamic snippets,
  - deep one-off edge wording tightly tied to branching.

## 4. Externalization design
- Strategy:
  - Reused `reply_templates` + `reply_overrides` merge path.
  - Preserved code-level fallback literals.
  - No cross-client override fallback.
- Config locations / key names:
  - Industry base: `configs/industries/insurance/reply_templates.json`
  - Client B overrides: `configs/clients/socal_precision/reply_overrides.json`
  - Keys: `missing_signature`, `underwriting_followup`, `renewal_reminder`, `informational`
- Fallback behavior:
  - missing client key -> industry key
  - missing industry key -> existing code literal
- Risk level: low (no control-flow changes, no policy logic move).

## 5. Implementation changes
- `services/fiqa_api/inbox_triage/triage.py`
  - `_build_client_reply_draft(...)` now reads template keys for four families in zh/en, then falls back to existing literal defaults.
- `configs/industries/insurance/reply_templates.json`
  - Added baseline industry templates for the four families.
- `configs/clients/socal_precision/reply_overrides.json`
  - Added client-specific tone overrides for the same four families.
- `scripts/run_long_tail_generic_reply_ab_scenarios.py`
  - New sprint runner.
  - Supports both conversation-path and explicit rule-path scenarios (`use_rule_based`) to validate wording behavior on low-frequency branches.
- `docs/sprints/LONG_TAIL_GENERIC_REPLY_EXTERNALIZATION_SPRINT/long_tail_ab_scenario_battery.json`
  - New A/B scenario battery with leak/fallback/flagship checks.

Portability value:
- Client packs can now differentiate four more generic customer-visible branches without touching engine logic.

Logic change vs wording change:
- Wording source changed (code literal -> config-backed with fallback).
- Business logic/control flow unchanged.

## 6. A/B scenario pack
- Scenario count: 9.
- Coverage:
  - A/B for each new family.
  - negative leak checks for `socal_precision`.
  - fallback sanity via `chen_kui` (no per-client overrides for these keys).
  - flagship add-car sanity.
- Why it matters:
  - verifies isolation and non-regression while keeping scope small.

## 7. Validation summary
- Ran:
  - `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_long_tail_generic_reply_ab_scenarios.py` -> pass (9/9)
  - `bash scripts/guardrail_inbox_triage.sh` -> PASS
  - `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_small_batch_phrase_map_ab_scenarios.py` -> pass
  - `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_residual_copy_ab_scenarios.py` -> pass
  - `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_append_boundary_ab_scenarios.py` -> pass
- Result:
  - no observed regression in flagship add-car/append/boundary guardrails.
  - A/B isolation strengthened on the new wording families.

## 8. Portability / isolation judgment
- What now isolates correctly:
  - Newly externalized four long-tail generic families.
  - Previously externalized stitched / append-boundary / residual high-frequency families.
- What still remains in engine:
  - deeper low-frequency one-offs in follow-up/handoff edge branches,
  - logic-coupled or retrieval-coupled wording assembly,
  - final generic fallback lines.
- Same-industry hot-plug credibility:
  - improved for demo and controlled pilot.
  - still not full no-code portability because some long-tail customer-visible branches remain code-coupled.

## 9. End-of-sprint founder summary
- This sprint solved:
  - residual long-tail generic reply leakage for four customer-visible families.
- Wording families moved:
  - `missing_signature`, `underwriting_followup`, `renewal_reminder`, `informational`.
- Moved from/to:
  - from hardcoded-only literals in `_build_client_reply_draft` -> industry `reply_templates` + client `reply_overrides` with safe code fallback.
- Files/functions changed:
  - `services/fiqa_api/inbox_triage/triage.py` (`_build_client_reply_draft`)
  - `configs/industries/insurance/reply_templates.json`
  - `configs/clients/socal_precision/reply_overrides.json`
  - `scripts/run_long_tail_generic_reply_ab_scenarios.py`
  - `docs/sprints/LONG_TAIL_GENERIC_REPLY_EXTERNALIZATION_SPRINT/long_tail_ab_scenario_battery.json`
- Logic changed?
  - No. Wording sourcing changed; triage logic unchanged.
- Validation:
  - new sprint A/B battery pass + full guardrail pass + directly affected prior A/B runners pass.
- What remains:
  - additional ultra-low-frequency, control-flow-adjacent customer-visible literals.
- Next best sprint:
  - run another micro-batch targeting 2-3 handoff-adjacent long-tail fallback lines still in `triage.py` that are customer-visible but not yet stitched/template-backed.

## 10. 中文宏观总结
- 这次清出来的长尾通用客户可见回复有四组：`missing_signature`、`underwriting_followup`、`renewal_reminder`、`informational`。
- 处理方式是沿用现有的模板/覆盖模式：行业模板 + 客户覆盖 + 主脑兜底，不动主流程判断逻辑。
- A/B 串台风险进一步下降：`chen_kui` 继续走行业默认语气，`socal_precision` 可以在这四组上使用自己的事务所语气（如 business-day / 本所）。
- 仍留在主脑里的客户可见句子，主要是更深层、分支强耦合、或和检索拼接强相关的低频句子。
- 距离“同业可切换”又前进了一步：演示与受控试点可信度更高，但还没到完全热插拔。
- 下一步最值动作：继续做一个小批次（2-3 组）handoff 边缘长尾可见句子外置，并维持同样的 A/B 防串台验证节奏。
