# Second Broker / Client-Pack Drill Sprint Report

## 1. Sprint theme

- **Reviewed / tested:** Unified Intake client boundaries (`client_id`), config loader behavior, `triage.py` handoff stitching, UI client-config fetch + triage payload wiring, and a full fictional second broker pack (`socal_precision`).
- **Why now:** Recent architecture (common engine + industry + client pack) needed an **honest** same-industry second-broker drill before claiming hot-plug readiness.

## 2. Document set created

| Document |
|----------|
| `INDEX.md` |
| `SECOND_BROKER_DRILL_BLUEPRINT.md` |
| `SECOND_BROKER_CLIENT_PACK_SPEC.md` |
| `CURRENT_PORTABILITY_AUDIT_SPEC.md` |
| `CLIENT_PACK_DRILL_SCENARIO_PACK.md` |
| `PORTABILITY_GAPS_SPEC.md` |
| `EXECUTION_OUTLINE.md` |
| `ACCEPTANCE_CRITERIA.md` |
| `FOUNDER_INSPECTION_NOTES.md` |
| `FINAL_REPORT.md` (this file) |
| `drill_scenarios.json` |

## 3. Current portability audit

### Client-pack friendly

- Per-client **`ui_copy.json`**, **`handoff_phrases.json`**, **`reply_overrides.json`** with clear loader contracts.
- API **`client_id`** on triage and append; UI passes **`clientId`** from `?client=` context.
- Reply template overrides **do not** cross-fallback between clients (good isolation for overrides).

### Still leaks default / Chen-adjacent assumptions

- Default **`CLIENT_ID` / `chen_kui`** and UI **`DEFAULT_UI_COPY`** (Chen-specific starters).
- **Industry** `talk_to_agent` markers still include **陈奎** (broker name in industry file).
- **`triage.py`** injects many **办公室** sentences on specialized branches regardless of `client_id`.
- **Add-car rules** and **soft-route inbox** copy are shared (industry/common), not per-client.

### Configurable now (shared)

- `add_car_rules.json`, `category_templates.json`, `soft_route_inbox.json`, `workflow_defaults.json`.

### Not really portable yet (without more work)

- Stitched handoff / clarification / materials / coverage strings inside **`triage.py`**.
- Consistent “second broker voice” on **every** path.

### Dangerous to fake as configurable

- **Silent fallback** of missing client handoff file to **Chen Kui** — sounds like wrong office.

## 4. Second broker pack definition

- **Who:** Fictional **南加精算车险服务台** (`socal_precision`) — same CA auto / Chinese-speaking segment, different tone (concise, business-day queue).
- **Differs from Chen Kui:** 本所/事务所 identity, explicit 营业日 timing, different quick-start labels and talk-to-agent starter; handoff lines shorter and more operational.
- **Config surfaces:** `configs/clients/socal_precision/ui_copy.json`, `handoff_phrases.json`, `reply_overrides.json`.

### Comparison (high level)

| Surface | Chen Kui | socal_precision |
|---------|----------|-----------------|
| App title | 保险经纪人智能助手 | 南加车险 · 客户入口 |
| Office label | 办公室 | 本事务所 |
| Add-car CTA | 获取报价 | 加车核价 |
| Talk-to-agent starter | 我想联系陈奎办公室 | 我要转接南加精算事务所人工 |
| Handoff timing copy | 一至两个工作日… | 一至两个**营业日**… |
| Voice | Warmer, “我们” | Shorter, “本所” |

## 5. Implementation changes

| Change | Why | Risk |
|--------|-----|------|
| `configs/clients/socal_precision/*` | Second broker drill pack | Low — isolated folder |
| `docs/sprints/...` + `drill_scenarios.json` | Documentation + repeatable drill | None |
| `scripts/run_second_broker_drill.py` | Automated drill | Low |
| `configs/industries/insurance/markers.json` + `triage.py` fallback: **`转接人工`** | UI used “转接人工”; detection must match | Low — broker-agnostic |

## 6. Drill scenario pack

- **8 scenarios** in JSON (including config surface check + intentional **办公室** leak assertion).
- Tests: add-car clean / partial→complete / correction / talk-to-agent / template path / materials branch + **client config** presence.
- **Why they matter:** They separate “logic works” from “**voice** is actually client-owned.”

## 7. Validation summary

| Check | Result |
|-------|--------|
| `python3 scripts/run_second_broker_drill.py` | **PASS** |
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** |
| `cd ui && npm run build` | **PASS** |
| Live `curl` API against 8001 | **Not run** (no server in this session) — inferred OK from code paths |

**Regressions:** None observed in guardrail.

## 8. Portability judgment

### A. What successfully swapped through client pack

- **UI copy** (via `client-config` + merge).
- **Handoff phrases** for standard add-car / talk-to-agent / generic other keys when no special branch overrides.
- **Reply overrides** when the engine actually routes through template merge for that turn.

### B. What still leaked from common engine / hardcoded logic

- **Materials-sent** add-car path and several **stitched** sentences still say **办公室**.
- **Premium caveat** stitching adds an **办公室** line.
- **Industry markers** still encode **陈奎** as talk-to-agent synonyms.
- **Shared** add-car prompts and soft-route starters.

### C. Is same-industry second client feasible?

- **Partially yes for a pilot:** You can demo a distinct office **for the paths that use handoff_phrases + ui_copy + overrides**.
- **Not yet for a commercial “hot plug” claim:** Too many high-traffic branches still **hardcode** office wording.

## 9. Risk analysis

- **Biggest risk:** Believing **client pack = full voice isolation** while **`triage.py`** still authors customer-visible text.
- **Hot-plug ambition:** Fine for **internal / founder demos** with eyes open; premature for **white-label** promises.
- **Fix next:** Externalize the worst stitched strings (materials-sent, premium caveat, coverage side-answers) into config keyed by client or at least common defaults.
- **Do not do yet:** Full multi-tenant platform, per-broker LLM prompts DB, dynamic remote config — not justified before string externalization.

## 10. Final judgment

- **How close to same-industry hot-plug:** **Medium** — architecture points the right way; **execution** still mixes too much copy in code.
- **Biggest gain:** Proved **`client_id` + three JSON files** deliver a **meaningfully different** office for core add-car handoff + UI.
- **Biggest remaining gap:** **Branch-specific** customer text in **`triage.py`**.
- **Best next move:** Small “**handoff stitch**” config map (client overlay) for the top 5–10 user-visible hardcoded strings, then re-run this drill until `drill_materials_sent_note` can assert **本所** instead of **办公室**.

## 11. 中文宏观总结

- **第二个同类 broker 能不能接？** 作为**演示级 / 试点级**可以：用 `client_id` + 客户端三包（`ui_copy`、`handoff_phrases`、`reply_overrides`）已经能让**主路径**听起来像另一家事务所。
- **哪些已经能靠 client pack 换掉？** 页面文案、快捷入口话术、多数标准交接语、以及模板合并能覆盖到的首轮回覆片段。
- **哪些还写死在主脑里？** `triage.py` 里大量拼接句（尤其材料已发、保费追问拼接等）仍常出现**办公室**；行业 `markers` 里还夹着**陈奎**；加车追问与 soft-route 文案仍是行业/公共层。
- **下一步最值得做什么？** 把最高频、客户可见的拼接句抽到可配置层（至少按 client 覆盖），再跑一遍本 drill，直到“材料已发”这类路径也不再强行用 Chen 时代的**办公室**口吻。

---

### Optional checklists

**Swapped successfully (drill-verified)**

- [x] Handoff line for clean add-car (本所 + 营业日)
- [x] Talk-to-agent after **转接人工** detection
- [x] `get_ui_copy` / `get_handoff_phrases` for `socal_precision` load without 陈奎 in those files

**Still leaking from core**

- [x] Materials-sent handoff branch → **办公室** wording
- [x] Premium stitching → **办公室** caveat line
- [ ] Industry talk_to_agent markers → **陈奎** (documented; not removed this sprint)
