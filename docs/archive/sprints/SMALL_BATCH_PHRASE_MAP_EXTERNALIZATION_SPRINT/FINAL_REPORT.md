# Small-Batch Phrase Map Externalization Report

## 1. Sprint theme
- Reviewed remaining customer-visible residual handoff overlays in core triage paths.
- Externalized a small, high-ROI wording batch into client-overridable stitched phrase map keys.
- Goal now: reduce voice leakage while preserving existing working logic and guardrails.

## 2. Document set created
- `docs/sprints/SMALL_BATCH_PHRASE_MAP_EXTERNALIZATION_SPRINT/BLUEPRINT.md`
- `docs/sprints/SMALL_BATCH_PHRASE_MAP_EXTERNALIZATION_SPRINT/RESIDUAL_COPY_AUDIT_SPEC.md`
- `docs/sprints/SMALL_BATCH_PHRASE_MAP_EXTERNALIZATION_SPRINT/PHRASE_MAP_EXTERNALIZATION_SPEC.md`
- `docs/sprints/SMALL_BATCH_PHRASE_MAP_EXTERNALIZATION_SPRINT/AB_SCENARIO_PACK_SPEC.md`
- `docs/sprints/SMALL_BATCH_PHRASE_MAP_EXTERNALIZATION_SPRINT/EXECUTION_OUTLINE.md`
- `docs/sprints/SMALL_BATCH_PHRASE_MAP_EXTERNALIZATION_SPRINT/ACCEPTANCE_CRITERIA.md`
- `docs/sprints/SMALL_BATCH_PHRASE_MAP_EXTERNALIZATION_SPRINT/FOUNDER_INSPECTION_NOTES.md`
- `docs/sprints/SMALL_BATCH_PHRASE_MAP_EXTERNALIZATION_SPRINT/FINAL_REPORT.md`

## 3. Residual copy audit
- Remaining leak-prone customer-visible lines were concentrated in handoff overlay paths inside `triage.py`.
- Selected this batch (3 families):
  1. handoff doc-clarification suffix (add-car / non-add-car)
  2. add-car coverage side-question handoff overlay (answer + suffix)
  3. payment correction+urgency handoff reassurance line
- Chosen because they are high-visibility and medium/high-frequency in real follow-up turns.
- Deferred:
  - lower-frequency generic one-liners (`unclear`, `informational`, `policy_delay_pending`)
- Keep-in-code:
  - intent markers, routing logic, state transitions, slot extraction.

## 4. Externalization plan
- Reused existing `stitched` phrase-map pattern in client `handoff_phrases.json`.
- Added keys:
  - `handoff_doc_clarification_suffix_add_car`
  - `handoff_doc_clarification_suffix_other`
  - `handoff_add_car_coverage_answer`
  - `handoff_add_car_coverage_suffix`
  - `handoff_payment_correction_urgency`
- Fallback behavior: if a key is missing, engine uses the current hardcoded default.
- Risk level: low (wording only; no control-flow migration).

## 5. Implementation changes
- Updated `services/fiqa_api/inbox_triage/triage.py` to read selected handoff overlays via `_stitched_customer_visible_line(...)`.
- Added client-specific overrides in:
  - `configs/clients/chen_kui/handoff_phrases.json` (baseline office wording retained)
  - `configs/clients/socal_precision/handoff_phrases.json` (desk/business-day wording)
- Updated `services/fiqa_api/inbox_triage/config_loader.py` docstring to document new stitched keys.
- Updated guardrail to include new battery step.
- Logic changes: none intended; wording selection only.

## 6. A/B scenario pack
- Added battery: `small_batch_ab_scenario_battery.json` with 9 scenarios.
- Added runner: `scripts/run_small_batch_phrase_map_ab_scenarios.py`.
- Coverage includes:
  - A/B pair scenarios per new phrase family
  - negative substring leak check for client B
  - omitted-key fallback check via `demo_broker`
  - flagship add-car handoff regression check

## 7. Validation summary
- `python3 scripts/run_small_batch_phrase_map_ab_scenarios.py` → pass (9/9)
- `python3 scripts/run_residual_copy_ab_scenarios.py` → pass (15/15)
- `python3 scripts/run_cross_client_ab_scenarios.py` → pass (12/12)
- `python3 scripts/run_append_boundary_ab_scenarios.py` → pass (12/12)
- `python3 scripts/run_add_car_driver_zip_materials_stress_battery.py` → pass (22 scenarios)
- `bash scripts/guardrail_inbox_triage.sh` → PASS (all checks green, API check skipped because no local server)
- Regression observed: none in tested paths.

## 8. Portability / isolation judgment
### A. What now isolates correctly
- Newly externalized handoff overlay phrase families (3 groups above).
- Prior stitched families remain isolated (materials-sent, why-still-chasing, prospective-send, append boundary, residual-copy families).
- Client B no longer needs to inherit shared office wording in these selected handoff overlays.

### B. What still remains in engine
- Some lower-frequency category one-liners and generic fallback responses.
- Handoff assembly glue and control-flow-specific text coupling.
- Logic-tied text in correction/state-machine decisions.

### C. Same-industry hot-plug credibility
- Demo: improved (more visible A/B tone separation).
- Controlled pilot: improved (less obvious cross-client voice bleed on key handoff turns).
- Productization claim: stronger, but still not fully copy-externalized.

## 9. Risk analysis
- Risk created:
  - Added config key surface area (possible typo/omission risk).
- Risk reduced:
  - Reduced hardcoded shared-voice leakage on customer-visible high-traffic handoff paths.
- Why platform safety remains high:
  - engine defaults preserved
  - no routing/decision logic moved to config
  - guardrail and stress batteries remain green
- What to avoid next:
  - broad text migration that drags logic branches into JSON
  - rewriting `triage.py` under productization scope

## 10. Final judgment
- Biggest gain: client-separable wording now covers another high-visibility handoff overlay layer.
- Biggest remaining gap: long tail of lower-frequency category text still in engine.
- Best next move: one more small batch focused on highest-frequency non-handoff generic replies, still wording-only and battery-driven.

## 11. 中文宏观总结
- 这次清出来的是 3 组高频客户可见话术：  
  1) 文档释义后接的转办公室/转本所收口句；  
  2) 加车里“coverage 能不能调”的答复+收口句；  
  3) “其实已经付了，现在最要紧做什么”这类纠正场景收口句。  
- A/B 串台风险更低了：`chen_kui` 和 `socal_precision` 在这些路径上已能稳定用各自风格，不再硬吃同一套办公室口吻。  
- 仍留在主脑里的主要是长尾低频分类一句话、以及和状态机/意图判断强耦合的话术。  
- 离“同业可切换”又近了一步：关键客户可见路径的可覆写率提升，而且回归全绿，可信度上升。  
- 下一步最值动作：继续做一小批“高频但非核心逻辑”的通用回复外置，并保持每批都配 A/B + fallback + guardrail 验证。
