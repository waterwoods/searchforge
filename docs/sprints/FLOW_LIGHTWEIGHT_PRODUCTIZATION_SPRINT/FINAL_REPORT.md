# Flow Lightweight Productization Sprint Report

**Sprint:** Flow Lightweight Productization Sprint (Common Engine + Industry Pack + Client Pack + Rule Maps + Regression Battery)  
**Date:** 2026-03-22  
**Branch context:** Chen Kui / Unified Intake

---

## 1. Sprint theme

- **Reviewed:** Unified Intake layering (code + config), concentration in `triage.py`, client vs industry config boundaries, regression coverage.
- **Improved:** Client-scoped reply template loading, externalized soft-route copy, aligned add-car JSON schema with loader/publish behavior.
- **Why now:** The flow is commercially usable; the founder needs **clearer ownership**, **safer multi-client growth**, and **editable common copy** without touching orchestration.

---

## 2. Document set created

| Doc |
|-----|
| `FLOW_LIGHTWEIGHT_PRODUCTIZATION_BLUEPRINT.md` |
| `FIVE_LAYER_ARCHITECTURE_SPEC.md` |
| `CURRENT_OWNERSHIP_RESPONSIBILITY_MAP.md` |
| `EXTERNALIZATION_PRIORITY_SPEC.md` |
| `SAFE_REFACTOR_RISK_GUARD_SPEC.md` |
| `HOT_PLUG_PATH_SPEC.md` |
| `EXECUTION_OUTLINE.md` |
| `FOUNDER_INSPECTION_NOTES.md` |
| `REGRESSION_BATTERIES_INDEX.md` |
| `FINAL_REPORT.md` (this file) |

---

## 3. Current architecture audit

**What already fits the 5-layer model**

- Industry JSON under `configs/industries/insurance/` (markers, templates, category templates, add-car rules).
- Client JSON under `configs/clients/<client_id>/` (handoff, UI copy, reply overrides).
- Common JSON under `configs/common/` (workflow fallbacks; now soft-route copy).
- Persistence and API separation (`case_store.py`, `routes/inbox_triage.py`).
- Strong regression battery via `guardrail_inbox_triage.sh`.

**What is too concentrated**

- Conversational and handoff policy largely lives in `triage.py` (large single module). This is the main complexity hotspot.

**What is too scattered**

- Marker fallbacks duplicated in code (`_FALLBACK_MARKERS`) and JSON — acceptable as safety net but should be documented when changing behavior.

**What is fragile**

- Changes to handoff timing, `WORKFLOW_STATE_KEYS`, or persist_case gating — high blast radius; must stay test-backed.

**Safe to move now (done)**

- Client path for reply overrides; soft-route strings to config; `ask_driver_only` in loader/save.

**Should stay in code for now**

- Orchestration order, append boundary logic, mixed-intent resolution, LLM guardrail merge.

---

## 4. Five-layer architecture map

See `FIVE_LAYER_ARCHITECTURE_SPEC.md` for full detail. Summary:

| Layer | Belongs now | Move next | Do not move yet |
|-------|-------------|-----------|-----------------|
| **Common Engine** | `triage.py`, `case_store.py`, session store, route orchestration | Thin helpers only with tests | Core state machine split |
| **Industry Pack** | Insurance configs + add-car rules | Pack manifest docs | Policy-only JSON for complex branches |
| **Client Pack** | Per-client handoff, UI, overrides | Fill `reply_overrides` for ops | Client-specific Python forks |
| **Lexicon / Rule maps** | `markers.json` + code fallbacks | More markers in JSON w/ tests | “All rules in JSON” |
| **Regression battery** | Guardrail + listed scripts | CI wiring (optional) | Replace runners blindly |

---

## 5. Productization plan

**Move now (executed)**

- Client-scoped `reply_overrides` merge path + per-client template cache.
- `configs/common/soft_route_inbox.json` for reroute + starter replies.
- `ask_driver_only` fully in `get_add_car_rules` / preserved in `save_add_car_rules`.

**Move later**

- Per-client soft-route overrides if needed.
- Further marker externalization from `triage.py` with scenario coverage.
- Optional package split of `triage.py` in a dedicated refactor sprint.

**Keep in code for now**

- Handoff gating, add-car quote-ready logic, append/new-issue boundary, LLM routing.

---

## 6. Implementation changes

| Change | Why | Portability value | Risk |
|--------|-----|-------------------|------|
| `get_reply_templates(client_id)`; triage `_get_reply_templates` / `_build_client_reply_draft(..., client_id)`; per-client cache | Remove hardcoded `chen_kui` path; correct behavior when multiple clients have different override files | New broker folder can ship `reply_overrides.json` without code edit | **Low** (Chen Kui overrides currently empty; demo_broker uses industry base) |
| `get_soft_route_inbox_copy()` + `configs/common/soft_route_inbox.json`; route uses loaded dicts | Founder/ops can tune button-path copy without editing Python | Deployment-specific wording | **Low** (defaults match previous literals) |
| `get_add_car_rules` / `save_add_car_rules` handle `ask_driver_only` | JSON on disk already had key; engine consumed it via `rules.get` — loader/publish now consistent | Rules Center publish does not drop driver-only prompt | **Low** |

**Files touched:** `config_loader.py`, `triage.py`, `routes/inbox_triage.py`, new `configs/common/soft_route_inbox.json`.

---

## 7. Validation summary

| Check | Result |
|-------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** (all steps including scenarios, multi-turn, adversarial, case boundary, handoff timing, client-aware handoff, client identity append) |
| API test on 8001 | SKIP (no server; optional) |
| `cd ui && npm run build` | Not required (no frontend changes this sprint) |

**Regressions:** None observed in guardrail output.

---

## 8. Hot-plug readiness judgment

**Same-industry new client:** **Moderate readiness.** Client pack files + `client_id` API/env give a clear path for voice and UI. Knowledge paths and hosting still need explicit work for a true second production office.

**Cross-industry:** **Low reuse of conversation logic** without a new industry pack and new triage/LLM assumptions; persistence and test harness reuse is high.

**Reporting / explainability:** **Improved.** Layers and config files map cleanly to founder slides; remaining gap is explaining *internals* of `triage.py` without reading code.

---

## 9. Risk analysis

**Risks of doing this**

- Any config typo in `soft_route_inbox.json` could change customer-visible strings — mitigated by guardrails and quick JSON review.
- Per-client template cache grows with many clients in one long-lived process — negligible at current scale.

**Risks of not doing this**

- Second client would silently get wrong template merge behavior (previously always merged Chen Kui overrides path in code).
- Disk/editor and engine continue to disagree on add-car keys (`ask_driver_only`), confusing operators.

**Avoid in the next 1–3 weeks**

- Large `triage.py` splits without a dedicated test plan.
- Moving conditional logic to JSON without new scenarios.

**Continue safely**

- Small externalizations + immediate `guardrail_inbox_triage.sh` run; prefer additive config with code defaults.

---

## 10. Final judgment

**More productized?** Yes — **incrementally**: clearer client vs common vs industry boundaries and one fewer hardcoded broker path.

**Biggest gain:** **Correct client-scoped reply template loading** + **documented regression index** for the founder.

**Biggest remaining gap:** **Orchestration density** in `triage.py` (understood and documented, not yet modularized).

**Best next move:** Add real content to `configs/clients/chen_kui/reply_overrides.json` when ops wants Chen-specific drafts without forking industry templates; run guardrail after each batch.

---

## 11. 中文宏观总结

这次 sprint **没有重写 flow**，而是在「已经能跑、能卖 demo」的前提下，把结构说清楚，并做了几处 **低风险、可回滚** 的整理。

- **Flow 更像产品了吗？** 更像了：行业包、客户包、公共配置、回归层的分工在文档和代码边界上更一致。
- **哪几层已经比较清楚？** 行业配置（`configs/industries/insurance/`）、客户配置（`configs/clients/<id>/`）、公共文案（`configs/common/`）、回归脚本（`guardrail_inbox_triage.sh`）这几块已经可以用「层」来讲清楚。
- **哪几层还混在一起？** 最大的仍然是 **Common Engine** 里的 `triage.py`：编排、策略、很多边界情况仍集中在一个大文件里——这是刻意的「先别大拆」。
- **热插拔还能往前走吗？** **同一行业新客户**：换 handoff/UI/reply override 已经比较接近「只加配置 + client_id」。**跨行业**仍然要当新项目看，不能指望配置 alone。
- **下一步最值的动作？** 运营上若要对陈奎话术做 A/B，优先填 `reply_overrides.json`（现在结构已按 client 生效），每次改完跑一遍 guardrail；工程上若要继续产品化，应用 **场景驱动** 把稳定 marker 从代码 fallback 挪到 JSON，而不是硬拆 `triage.py`。
