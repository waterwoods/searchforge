# Founder / Broker Trial Execution Report

**Sprint:** Founder / Broker Trial Execution Sprint  
**Date:** 2026-03-20  
**Execution mode:** Document-driven, multi-loop, automated trial simulation + code inspection

---

## 1. Sprint theme

- **Chosen theme:** Real founder/broker-style trial of Unified Intake — validate four backbones together (Page, Flow, State, Handoff) and fix only the highest-ROI trust/validation gaps.
- **Why now:** The stack has strong modular bones; the risk is **integrated believability** and **operator trust** (including “does our own CI lie to us when the API is up?”).

---

## 2. Document set created

| # | Path |
|---|------|
| 1 | `docs/sprints/FOUNDER_BROKER_TRIAL_EXECUTION_SPRINT/FOUNDER_BROKER_TRIAL_EXECUTION_BLUEPRINT.md` |
| 2 | `docs/sprints/FOUNDER_BROKER_TRIAL_EXECUTION_SPRINT/TRIAL_SCENARIO_PACK_SPEC.md` |
| 3 | `docs/sprints/FOUNDER_BROKER_TRIAL_EXECUTION_SPRINT/TRIAL_OBSERVATION_FRICTION_CLASSIFICATION_SPEC.md` |
| 4 | `docs/sprints/FOUNDER_BROKER_TRIAL_EXECUTION_SPRINT/FIX_NOW_DECISION_SPEC.md` |
| 5 | `docs/sprints/FOUNDER_BROKER_TRIAL_EXECUTION_SPRINT/EXECUTION_OUTLINE.md` |
| 6 | `docs/sprints/FOUNDER_BROKER_TRIAL_EXECUTION_SPRINT/ACCEPTANCE_TRIAL_EXECUTION_CRITERIA.md` |
| 7 | `docs/sprints/FOUNDER_BROKER_TRIAL_EXECUTION_SPRINT/FOUNDER_TRIAL_NOTES.md` |
| 8 | `docs/sprints/FOUNDER_BROKER_TRIAL_EXECUTION_SPRINT/TRIAL_EXECUTION_18_POINT_BREAKDOWN.md` |
| 9 | `docs/sprints/FOUNDER_BROKER_TRIAL_EXECUTION_SPRINT/README.md` |
| 10 | `docs/sprints/FOUNDER_BROKER_TRIAL_EXECUTION_SPRINT/FOUNDER_BROKER_TRIAL_EXECUTION_REPORT.md` (this file) |

**Index link:** `docs/trial/INDEX.md` updated to point at this sprint folder.

---

## 3. Baseline trial audit

| Lens | Assessment |
|------|------------|
| **Biggest current strength** | Rule-backed simulation coverage is deep and aligned with broker language: 51 multi-turn, 27 adversarial, 24 mixed/long-context, 27 Simulation Assistant, 13 broker stress, 13 handoff timing — all **strong** in this run. Add-Car path (quote-ready, materials sent, correction, identity/contact) is a credible flagship. |
| **Biggest trust-breaking risk** | **Operator trust in validation:** when `8001` is live, `test_inbox_triage_api.py` previously failed the append case while the rest passed — a “green except one red” pattern that trains the team to ignore API results. **Mitigated in this sprint** (see Loop 2). |
| **Biggest office-usability risk** | Under **LLM variance**, field extraction and `broker_next_step` could diverge from rule expectations; workbench still depends on founder spot-checking live behavior, not only offline rules. |
| **Biggest commercial-feel risk** | **Expectation management:** anything that implies auto-quote or carrier certainty without office confirmation — mitigated by copy in triage/UI but must stay consistent in demos. |

**Scenario strength snapshot**

| Area | Rating | Note |
|------|--------|------|
| Add-car + materials / correction | Strong | BS11–12, MT43–51, HT12–13 |
| Missing doc + already_sent | Strong | SIM2, SIM10, MT29 |
| Cancellation / payment | Strong | SIM1, SIM7, MT25–26 |
| Premium + remove vehicle | Strong | BS13, MT21 |
| Talk-to-agent | Strong | BS3–5, HT4 |
| Mixed-intent | Strong | MI-* packs |

---

## 4. 10–20 point breakdown

See `TRIAL_EXECUTION_18_POINT_BREAKDOWN.md` for the full numbered list (items 1–18). Summary themes: real usage first, four backbones together, honest friction buckets, fix-now discipline, broker trust vs commercial believability vs rework reduction.

---

## 5. Iteration loop 1

- **Scenarios tested (automated, serious pass):** Inbox triage scenario pack (64), multi-turn (51), adversarial (27), complex (24), Simulation Assistant (27), broker stress (13), handoff timing (13), state/workflow backbone, persistence, client-aware handoff, identity append — via `bash scripts/guardrail_inbox_triage.sh`.
- **What worked:** End-to-end **rule-backed** trial paths are consistent; handoff timing guardrails pass; materials-sent and contact-lite scenarios pass.
- **What felt believable (inferred from outputs + code):** Structured `collected_fields` / `still_needed_fields`, quote-ready status, correction and mixed-intent handling — matches “office can act” bar.
- **What felt weak:** With API server up, **Test 13 append** failed: single-turn partial Add-Car + `persist_case` does not yield `case_id` (by design — `handoff_ready` gate). The test assumed persistence without completing handoff.
- **Worth it?** **Yes** — exposed a real validation honesty issue.

---

## 6. Iteration loop 2

- **Issues found:** API integration test “append follow-up” used a **partial** add-car message with `persist_case=True`, so no case was saved (`MULTI_TURN_CONTINUITY` / handoff gate).
- **Classification:** **Fix-now** for validation trust (not a product UX bug — product behavior was correct; the test was wrong).
- **Fix-now implemented:** `scripts/test_inbox_triage_api.py` — Test 13 now uses one **handoff-eligible** add-car message (vehicle + zip + delivery + driver + name/phone) so `persist_case` returns `case_id`, then append runs as intended.
- **Intentionally not fixed:** LLM vs rule divergence (defer to ongoing monitoring); full browser walkthrough in this session (time-box; simulations substituted).
- **What improved:** With server on `8001`, **all** API tests pass; guardrail step [3] is **OK** instead of WARN.
- **Worth it?** **Yes** — low risk, high trust ROI for anyone running guardrail with a live server.

---

## 7. Iteration loop 3

- **Retested:** Full `bash scripts/guardrail_inbox_triage.sh` after the API test change.
- **What improved:** API test block fully green when `healthz` returns 200.
- **What still remained weak:** Production **live LLM** behavior not re-benchmarked in this session; founder should still run a **5-minute manual** pass before external broker exposure.
- **Stronger for broker review?** **Yes** on the **validation / regression** axis; product behavior was already strong in simulation.
- **Worth it?** **Yes.**

---

## 8. Optional loop 4

- **Used?** **No.**
- **Reason:** No second trust-breaking item met fix-now criteria without scope creep; stopping avoids churn.

---

## 9. Validation summary

| Check | Result |
|-------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** (including API tests with server on 8001) |
| `PYTHONPATH=. python3 scripts/test_inbox_triage_api.py --url http://localhost:8001` | **PASS** (after Test 13 fix) |
| `cd ui && npm run build` | **Not run** (no UI changes in this sprint) |

**Limitations:** No full Cursor browser session against production URL; no OCR/carrier APIs tested (out of scope).

---

## 10. Deployment / release judgment

| Layer | Changed? | Redeploy? |
|-------|----------|-----------|
| Backend app code | **No** | **No** |
| Scripts (`test_inbox_triage_api.py`) | **Yes** | **No** — affects **dev/CI validation**, not production runtime |
| Frontend | **No** | **No** |

**Performed deploy:** **Not executed in this session** (no production deploy credentials / target invoked). If you rely on CI running API tests against a staging URL, pick up this script change on the next normal push.

---

## 11. Founder manual inspection list

1. **Customer tab → Add-car quick start:** Send a **partial** message; confirm the system **asks** for zip/driver/contact — not instant fake “done.”
2. **Customer tab → full add-car:** Confirm quote-ready / handoff copy and that it does **not** promise a bound premium.
3. **Workbench queue:** Sort/scan — pick cancellation vs add-car without reading every line.
4. **Open Add-car case:** Read `broker_next_step` — must mention concrete office actions (verify materials, confirm contact, run quote).
5. **Missing-doc already_sent:** Confirm verify-with-carrier / receipt tone, not re-requesting blindly.
6. **Append message on saved case:** Paste a follow-up; confirm `case_activity` and updated fields.

---

## 12. Final judgment

| Question | Answer |
|----------|--------|
| **Biggest gain** | **Honest API validation** when the server is running — guardrail no longer trains the team to tolerate a failing append test. |
| **Biggest remaining weakness** | **LLM live variance** vs offline rules — still needs periodic human spot-check before high-stakes demos. |
| **Ready for more serious broker review?** | **Yes**, with the caveat: run the **6 manual checks** above on the **same environment** you will show (local or deployed). |
| **Best next step** | 10-minute **live** founder pass on deployed stack; capture 3 friction bullets in `docs/trial/TRIAL_OBSERVATION_LOG_TEMPLATE.md` if anything feels off. |

---

## 13. 中文宏观总结

- **为什么现在做这一轮：** 功能模块已经齐，关键问题是“连在一起像不像真生意 + 办公室敢不敢信”。
- **主要验证/修了什么：** 跑完全套 guardrail 与场景模拟；修复 **API 集成测试** 在「未 handoff 却想 persist」上的错误假设，使「服务启动时」的测试结果与产品设计一致。
- **最大提升：** **验证可信度** — 不再出现“前面全绿、append 红”的误导信号。
- **还差什么：** **线上 LLM 路径** 仍需真人短测；未做完整浏览器生产环境走查。
- **下一步最该做什么：** 在真实要给经纪人看的环境里做 **5–10 分钟** 手动走查（上表 6 条）。

---

## 14. COPY/PASTE FOUNDER BLOCK

```
【本轮最大发现】API 在 8001 启动时，append 测试曾误报失败：部分加车不会落库是刻意设计（需 handoff_ready），不是产品坏了。
【最大 fix-now】修正 test_inbox_triage_api.py：用可 handoff 的完整加车消息测 append，guardrail 全绿。
【最大残留弱点】线上 LLM 与离线规则可能不一致 — 对外演示前请真人短测一轮。
【要不要 redeploy】本轮未改运行时前后端；仅改测试脚本 → 生产不必为此次单独发布。
【能否进入更认真经纪人审阅】可以 — 但请先在目标环境完成 6 条手动检查。
```

---

## 15. REQUIRED SHORT OVERVIEW

### 为什么做这件事

验证四条骨干（页面/流程/状态/交接）在真实使用视角下是否可信，并修掉最伤信任的环节。

### 主要用了什么方法/技术

文档化 sprint 包 + `guardrail_inbox_triage.sh` 全量模拟与 API 测试 + 对失败用例的根因分析（persist 与 handoff 语义）。

### 这轮最大的提升

**当 API 在线时测试结果与产品语义一致**，避免团队对集成测试脱敏。

### 现在还差什么

**生产环境 + LLM 下的短手动走查**；未执行实际生产 deploy。

---

*End of Report*
