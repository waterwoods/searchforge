# Append / Boundary Customer-Visible Strings Externalization Report

## 1. Sprint theme

- **Reviewed / improved:** Customer-visible copy for **append** flows when the engine marks **`new_issue`** or **`borderline`**, previously hardcoded in `_apply_append_case_boundary` and shared across all clients.
- **Why now:** Add-Car **stitched** phrases already switched by client pack, but **boundary** replies still leaked **Chen-style「办公室」** for Client B—undermining same-industry hot-plug credibility on the **continuation / pivot** path.

## 2. Document set created

| Document |
|----------|
| `APPEND_BOUNDARY_STRINGS_EXTERNALIZATION_BLUEPRINT.md` |
| `BOUNDARY_COPY_LEAK_AUDIT_SPEC.md` |
| `AB_BOUNDARY_SCENARIO_PACK_SPEC.md` |
| `EXTERNALIZATION_DESIGN_SPEC.md` |
| `EXECUTION_OUTLINE.md` |
| `ACCEPTANCE_CRITERIA.md` |
| `FOUNDER_INSPECTION_NOTES.md` |
| `BEFORE_AFTER_LEAK_CHECKLIST.md` (optional) |
| `append_boundary_ab_scenario_battery.json` |
| `FINAL_REPORT.md` (this file) |

## 3. Boundary copy leak audit

- **What still leaked (pre-sprint):** All **ZH/EN** continuity lines, new-issue tails, add-car split hints, and borderline paragraphs inside `_apply_append_case_boundary`—**one engine voice** for every `client_id`.
- **Highest priority:** **ZH new_issue** after **add-car** handoff (documented as **`ab_10`**).
- **Safe to externalize:** Wording only; **not** domain/pivot rules or broker `Case boundary:` prefixes.

## 4. Externalization design

- **Strategy:** `handoff_phrases.json` → `stitched.append_boundary`, merged over **`_APPEND_BOUNDARY_DEFAULTS`** in `triage.py`; **no cross-client fallback** for this block.
- **Why:** Same operational pattern as `add_car_materials_sent` / `prospective_send`; minimal new surfaces.
- **Fallback:** Omitted keys → engine defaults (legacy Chen-path strings).
- **Risk level:** **Low**—classification untouched; defaults preserve prior A behavior.

## 5. Implementation changes

| Change | Why | Portability | Risk |
|--------|-----|-------------|------|
| `_APPEND_BOUNDARY_DEFAULTS` + `_merged_append_boundary_copy` + `client_id` on `_apply_append_case_boundary` | Per-client customer copy | Same-industry clients can diverge on **append boundary** voice | Low |
| `socal_precision` `stitched.append_boundary` | Remove forced **办公室** on B | High ROI for second-broker demo | Low |
| `_str_override` uses `rstrip("\r\n")` only | Preserve EN trailing spaces for stitching | Correct spacing for EN packs | Low |
| `config_loader` docstring for `append_boundary` | Discoverability | — | Low |
| `cross_client_ab_scenario_battery.json` **`ab_10`** updated | Assert B isolation | Locks regression | Low |
| `run_append_boundary_ab_scenarios.py` + battery + guardrail **`[12b]`** | Continuous validation | — | Low |

## 6. A/B boundary scenario pack

- **Count:** **12** scenarios in `append_boundary_ab_scenario_battery.json`.
- **What they test:** `same_case`, `new_issue` (ZH/EN, billing, premium pivot, claim leak path), `borderline` A vs B, **`demo_broker`** default fallback.
- **Why they matter:** Prove **logic stable** while **wording** differs by client and **no Chen tokens** on B where forbidden.

## 7. Validation summary

| Check | Result |
|-------|--------|
| `scripts/run_append_boundary_ab_scenarios.py` | **12/12** |
| `scripts/run_cross_client_ab_scenarios.py` | **12/12** |
| `scripts/run_case_boundary_battery.py` | **23/23** |
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** (includes `[12b]`) |
| `cd ui && npm run build` | **Not run** (no UI changes) |

**Regressions:** None observed in the above.

**Isolation:** **Stronger** on append **new_issue** / **borderline** customer drafts for Client B.

## 8. Portability / isolation judgment

### A. What now isolates correctly?

- **Append `new_issue`** customer continuity + tails + add-car split hint (ZH/EN) when `stitched.append_boundary` is set.
- **Append `borderline`** customer draft (ZH/EN).
- **Post-handoff boundary semantics** as experienced by the **customer** in chat draft (broker tags still English in code).

### B. What still leaks from the common engine?

- **Broker-facing** strings: `Case boundary: possible new issue…`, `Case boundary unclear…`, summary tags.
- **Prior-thread inference markers** (e.g. `_SYSTEM_ADD_CAR_HANDOFF_MARKERS`)—policy, not shown as a single customer block.
- **Other paths** called out in earlier audits (e.g. add-car **coverage** handoff suffix in main triage) remain **out of scope** for this sprint.

### C. Is same-industry hot-plug more credible?

- **Demo:** **Yes** for append pivots—B no longer forced to **办公室** on boundary copy.
- **Controlled pilot:** **Yes**, with the caveat that broker UI tags are still shared English.
- **Strongest portability claim:** **Main path + append boundary customer wording** can both track client pack; not “every string in the repo.”

## 9. Risk analysis

| Risks of doing this | Risks of not doing this |
|---------------------|-------------------------|
| Mis-edited JSON could produce awkward copy for one client | B continues to **sound like Chen** on append pivots—trust hit |
| Guardrail drift if battery not run | Harder to sell **second broker** |

**Why it should not break the platform if guardrails stay green:** Defaults match pre-sprint strings; only explicit `append_boundary` overrides change voice; classification batteries unchanged.

**What to avoid next:** Moving **classification** into JSON; rewriting broker `Case boundary:` lines without a product decision; giant monolithic “all strings” files.

## 10. Final judgment

- **Biggest gain:** **Append-path** customer boundary copy is **client-overridable** with **A/B + guardrail** coverage; **`ab_10`** now enforces B isolation.
- **Biggest remaining gap:** Broker-facing boundary **English** prefixes; other **non-append** hardcoded customer phrases (see prior cross-client audit).
- **Best next move:** Externalize remaining **high-frequency** customer-only hardcodes called out in product priority (e.g. coverage handoff suffix) using the same **stitched** discipline, or localize broker tags if the workbench ships in Chinese.

## 11. 中文宏观总结

- **追加消息 / 新问题边界的话术能不能切换？** 能。`new_issue` 和 `borderline` 下给客户看的整段说明，现在可以通过各 client 的 `handoff_phrases.json` → `stitched.append_boundary` 覆盖；不写这一段则仍用引擎默认（与原先 Chen 路径一致）。
- **A/B 会不会更不容易串台？** 会明显改善：**Client B** 在「加车后续 → 账单/理赔/模糊转折」等 append 边界场景下，不再被硬编码成统一的「办公室」叙事；`ab_10` 与新的 **12 条 append 边界电池** 把这一点锁在回归里。
- **哪些边界文案已能按 client pack 变化？** 同案延续句、按事项拼接的转接尾句、加车场景下的「另开新问题」提示、边界不清时的安抚说明（中英可选覆盖）。
- **哪些还在主脑（代码）里？** 边界**判定规则**（算不算 new issue / borderline）、经纪人侧的 `Case boundary:` 英文提示、summary 里的 `Boundary:` 标签等。
- **下一步最值的动作？** 按产品优先级继续把**仍为硬编码、客户高频可见**的句子（例如主路径里加车 coverage 相关 handoff 缀句）纳入同一套 **stitched / 小表** 管理；或若工作台要中文版，再单独做经纪人侧文案外置。
