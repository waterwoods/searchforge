# Cross-Client Compatibility / Isolation + Stitched Copy Externalization Report

## 1. Sprint theme

- **Reviewed / improved:** Per-client isolation for **high-frequency stitched customer-visible copy** on Add-Car-adjacent paths (materials-sent, prospective-send, “why still chasing”), plus a 12-scenario **chen_kui vs socal_precision** battery and guardrail hook.
- **Why now:** Second-broker drill showed packs change tone, but core **stitched** lines could still sound like Client A; that undermines trust in same-industry switching.

## 2. Document set created

| Doc |
|-----|
| `CROSS_CLIENT_COMPATIBILITY_BLUEPRINT.md` |
| `CLIENT_ISOLATION_AUDIT_SPEC.md` |
| `AB_SCENARIO_PACK_SPEC.md` |
| `STITCHED_COPY_EXTERNALIZATION_PRIORITY_SPEC.md` |
| `EXECUTION_OUTLINE.md` |
| `ACCEPTANCE_CRITERIA.md` |
| `FOUNDER_INSPECTION_NOTES.md` |
| `FINAL_REPORT.md` (this file) |
| `AB_COMPARISON_TABLE.md` |
| `LEAK_CHECKLIST_BEFORE_AFTER.md` |
| `EXTERNALIZE_OR_KEEP_TABLE.md` |
| `cross_client_ab_scenario_battery.json` |

## 3. Client isolation audit

- **Switches correctly today:** `handoff_phrases.json` handoff keys, `reply_overrides.json`, `ui_copy.json`, API `client_id` threading for triage.
- **Still leaks (known):** Chinese **append-case boundary** copy in `_apply_append_case_boundary` (scenario `ab_10` documents identical 办公室 wording for B). Additional leaks: coverage handoff suffix, `get_handoff_phrases` Chen **file** fallback for incomplete packs, UI `DEFAULT_UI_COPY` in `clientConfig.ts` when API returns empty.
- **Highest priority fixed this sprint:** Materials-sent, prospective-send bundle, why-still-chasing — highest traffic and most visibly “wrong office” for B.

## 4. A/B scenario pack

- **Count:** 12 scenarios (`cross_client_ab_scenario_battery.json`).
- **Coverage:** Add-car clean, materials-sent, ask-to-send, correction, append new-issue (leak callout), talk-to-agent — mirrored A/B.
- **Why it matters:** Proves **stitched** lines diverge on B without breaking A; append case proves where isolation is **not** done yet.

## 5. Externalization decisions

- **Now:** `stitched` object on `handoff_phrases.json` loaded via `get_stitched_handoff_phrases()` (no cross-client fallback).
- **Deferred:** Append boundary Chinese blocks; coverage overlay; broader engine phrases.
- **Stays in code:** Markers, extraction, LLM routing, workflow state, business rules.

## 6. Implementation changes

| Change | Why | Risk | Portability value |
|--------|-----|------|-------------------|
| `config_loader.get_stitched_handoff_phrases` | Single load path for optional stitched map | Low | Client-owned copy |
| `triage.py` uses `stitched` for 3 paths + `client_id` through next-ask / prospective lead | Remove hardcoded 办公室 on those paths for B | Low — A strings match old defaults | Same-industry switch more honest |
| `chen_kui` / `socal_precision` `stitched` JSON | A parity with legacy text; B distinct tone | Low | Pack-level control |
| `scripts/run_cross_client_ab_scenarios.py` + guardrail `[12]` | Regression signal for A/B | Low | CI confidence |

## 7. Validation summary

| Check | Result |
|-------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** |
| `scripts/run_cross_client_ab_scenarios.py` | **12/12** |
| `scripts/test_client_aware_handoff.py --direct` | **PASS** (via guardrail) |
| `ui` build | **Not run** (no UI changes) |

**Regressions:** None observed; 64 scenario pack, 69 multi-turn sims, broker stress, handoff timing, case boundary battery all green.

## 8. Portability / isolation judgment

### A. What now isolates correctly between clients?

- UI copy (when served from API).
- Config handoff one-liners.
- **Selected stitched paths:** materials-sent handoff, prospective-send leads, why-still-chasing reassurance.

### B. What still leaks from the common engine?

- **Append-case** Chinese continuity and broker-facing boundary prefixes (shared).
- **Coverage** add-car overlay and other small 办公室 phrases in collecting/handoff overlays.
- **Default client** and **handoff file** fallback to Chen when configs missing.

### C. Is same-industry client switching credible?

- **Demo:** **Stronger** for Add-Car-adjacent reassurance.
- **Controlled pilot:** **Stronger**, provided B’s JSON is complete and `client_id` is set end-to-end.
- **General “hot-plug” claim:** **Not yet** — append + a few overlays still need config hooks or copy pass.

## 9. Risk analysis

- **Risk introduced:** More JSON surface area; typos in `stitched` keys fall back to engine defaults (could surprise ops if they expect custom copy).
- **Risk reduced:** Wrong-office wording on **three** high-visibility Add-Car paths.
- **Why guardrails matter:** Full guardrail run catches triage regressions; new A/B step catches cross-client copy regressions on those paths.
- **Avoid next:** Big template DSL, moving rules into JSON blobs, or rewriting append logic without a scoped copy strategy.

## 10. Final judgment

- **Biggest gain:** B can run flagship Add-Car flows without **materials-sent / prospective-send / chase** lines forcing Chen-style 办公室 language.
- **Biggest remaining gap:** **Append-case** Chinese boundary copy still shared; **coverage** suffix still office-generic.
- **Best next move:** Externalize `_apply_append_case_boundary` zh strings (and optionally en) with the same `stitched` or sibling map, then re-run A/B with `ab_10` expectations flipped for B.

## 11. 中文宏观总结

- **A/B 会不会更容易串台？** 在「加车材料已发、要不要先发材料、材料发了怎么还在追」这几条高频话术上，**更不容易串台**——因为已经放进各客户自己的 `handoff_phrases.json` 的 `stitched` 里，而且 **stitched 不会做跨客户回退到 Chen Kui**。
- **哪些高频话术能切换？** 材料已发安抚、先发材料许可（含微信/截图/打包）、以及「怎么还在追」类安抚。
- **哪些还在主脑里？** 典型例子：同一条对话里追加「新问题」时的中文边界说明，仍大量共用带「办公室」的引擎原文；加车保额相关的拼接安抚也还在代码里。
- **是不是更接近真正可切换？** **更接近**，尤其在加车主路径上；但要说「随便切换客户都不会露馅」，还要把追加会话边界那类句子也配置化。
- **下一步最值的动作？** 把 `_apply_append_case_boundary` 的中英文客户可见句做成可配置（小步、与本次 `stitched` 同一风格），并更新 `ab_10` 的断言，让 B 侧不再被迫出现 Chen 式「办公室」叙事。
