# Broker Pilot Core Report

**Phase**: Broker Pilot Core  
**Date**: 2026-03-06

---

## 1. What was improved

| Change | Files | Why it matters |
|--------|-------|----------------|
| **Answer structure** | `DemoPage.tsx` | Added 简短结论 at top, 官方依据 inline, 下一步建议; scenario tag for workflow feel |
| **Copy-to-client format** | `demoCopy.ts` | Softer tone: 【可直接转发给客户】, "建议您：" for steps, "官方参考：" for links; less robotic |
| **Scenario tags** | `DemoPage.tsx` | Tags: 新车投保、注册恢复、合规查询、省钱/折扣、理赔流程 — broker workflow feel |
| **Snapshot script** | `snapshot_demo_answers.py` | Now snapshots all 5 questions (was 3) for full offline coverage |
| **Pilot package doc** | `docs/BROKER_PILOT_PACKAGE.md` | Scope, onboarding, pricing placeholder, file paths |
| **Future extraction note** | `docs/FUTURE_EXTRACTION_POINTS.md` | Common base vs region-specific; where config pack could go |
| **Operator runbook** | `BROKER_DEMO_OPERATOR_RUNBOOK.md` | Updated to 5 recommended questions |

---

## 2. Broker usefulness improvements

### Answer structure

- **Before**: "建议结论（给客户的版本）" → bullets → steps → copy
- **After**: Scenario tag → **简短结论** (quick answer) → bullets 2–3 → **官方/权威依据** (inline domains) → **下一步建议** → 复制给客户

Matches target: 简短结论 / 官方依据 / 下一步建议 / 可直接转发给客户.

### Copy-to-client usefulness

- **Before**: 【问题】【3点结论】【下一步】【权威链接】 — formal, robotic
- **After**: 【可直接转发给客户】 + quick answer + "建议您：" + steps + "官方参考：" + URLs — client-friendly, WeChat-ready

### Workflow feel

- Scenario tags on answers (新车投保, 注册恢复, etc.)
- Clearer section labels (下一步建议 vs 下一步怎么做)
- Inline 官方依据 so broker sees sources at a glance

---

## 3. Pilot package

| Item | Location |
|------|----------|
| **Pilot scope** | `docs/BROKER_PILOT_PACKAGE.md` |
| **Onboarding** | 3 steps: access, try, ask |
| **Proposal wording** | Placeholder in BROKER_PILOT_PACKAGE.md (§4) |
| **Included v1** | 5 questions, answer structure, copy-to-client, offline, scenario tags |
| **Excluded v1** | Stripe, multi-tenant, LLM generation, China/Europe |

---

## 4. Future extensibility note

| Category | Location | Notes |
|----------|----------|-------|
| **Common base** | `search_core.py`, `query.py`, `demoCopy.ts` | Collection/mode-agnostic |
| **Region config pack** | `DemoPage.tsx` SAMPLE_QUESTIONS, SCENARIOS, fallbacks, detectScenario | Extract to `configs/regions/ca_auto_insurance.json` when expanding |
| **Doc** | `docs/FUTURE_EXTRACTION_POINTS.md` | Full list |

---

## 5. Simulated broker-use test

| Question | Scenario tag | Quick answer | Copy format | Pilot-worthy? |
|----------|--------------|--------------|-------------|--------------|
| 新车最低保险？ | 新车投保 | 加州最低责任险：15,000/30,000... | ✅ 可直接转发 | Yes |
| 注册暂停恢复？ | 注册恢复 | 注册暂停通常因保险失效... | ✅ 建议您：... | Yes |
| 合规查询？ | 合规查询 | insurance.ca.gov 可查... | ✅ 官方参考：... | Yes |
| 省钱/折扣？ | 省钱/折扣 | 保费受驾驶记录... | ✅ | Yes |
| 理赔流程？ | 理赔流程 | 确保安全 → 报警... | ✅ | Yes |

**Remaining weak points**:
- LLM generation off by default — answers come from retrieval + heuristic extraction; fallbacks fill gaps
- demo_fallback.json has 3 items; snapshot now produces 5; offline for Q4/Q5 uses DEFAULT_FALLBACK_ITEMS
- Copy format improved but could be A/B tested with real broker feedback

---

## 6. Work split

| Who | Responsibility |
|-----|----------------|
| **Cursor** | Product edits, docs, scripts; answer structure, copy format, pilot package |
| **OpenClaw** | Repetitive ingest, snapshot, validation; `snapshot_demo_answers.py`, `demo_quick_validate.sh` |
| **Andy** | Business layer: broker outreach, pricing, terms, demo scheduling; run `demo_prep_one_command.sh` before demo |

---

## 7. Next 12 actions (ordered by priority)

1. **Run snapshot** — `python3 scripts/snapshot_demo_answers.py` (backend on 8001) to refresh demo_fallback.json with 5 questions
2. **Demo to broker** — Use updated UI; show 复制给客户 with new format
3. **Capture feedback** — "What would make this most useful?"; note questions that failed
4. **Set pilot price** — Replace $XX in BROKER_PILOT_PACKAGE.md with actual amount
5. **One-pager terms** — Create for email when broker agrees to pilot
6. **Optional: enable LLM** — Set `LLM_GENERATION_ENABLED=true` for richer answers (adds cost)
7. **Optional: broker-specific header** — Add broker name to header if pilot closes
8. **Refresh offline pack** — Re-run snapshot after any collection/answer changes
9. **Add 1–2 broker questions** — If broker asks new question types, add to SCENARIOS
10. **Deploy for pilot** — Use `deploy_rag_demo.sh` or ngrok when broker ready
11. **Track usage manually** — Log questions asked, copy usage
12. **Document extraction** — When expanding to China/Europe, follow FUTURE_EXTRACTION_POINTS.md

---

*End of report*
