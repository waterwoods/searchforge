# Broker Workflow Depth Sprint Report

**Sprint:** Broker Workflow Depth Sprint  
**Date:** 2026-03-07  
**Duration:** ~25 min closed loop

---

## 1. Issue targeted

**Workflow-depth gap:** The product had **客户可准备** (what client should prepare) and **经纪人可进一步询问** (what broker should ask next), but lacked an explicit **经纪人下一步** (what the broker should do next). Brokers could see what to ask and what the client should bring, but not a clear, actionable "do this next" step.

**Why it mattered most:** Real broker workflow requires knowing not only what to ask and what the client prepares, but also what action to take immediately. Without 经纪人下一步, the output felt more like answer text than a usable workflow helper. The highest-value gap was the missing "what to do next" for broker action.

---

## 2. Changes made

| File | Change |
|------|--------|
| `services/fiqa_api/routes/query.py` | Added **经纪人下一步** block to all broker workflow hints: Q1, Q2, Q3, Q4, Q5, SR-22. Each scenario now has a concrete next action for the broker. |
| `ui/src/utils/demoCopy.ts` | Added `经纪人下一步` to `BROKER_ONLY_MARKERS` so it is excluded from client-ready copy. |
| `scripts/verify_copy_to_client_guardrail.py` | Added `经纪人下一步` to `BROKER_ONLY_MARKERS`; added test case for filtering. |
| `ui/src/assets/demo_fallback.json` | Appended 经纪人下一步 block to all 5 Q1–Q5 answers. |
| `ui/src/pages/DemoPage.tsx` | Updated `DEFAULT_FALLBACK_ITEMS` with 经纪人下一步 for all 5 scenarios. |
| `docs/BROKER_DEMO_QUALITY_STANDARD.md` | Documented 经纪人下一步 in workflow-helper expectations and copy-to-client exclusion. |

**Hints added (examples):**

- **Q1 (new car):** 经纪人下一步：确认客户车辆/驾照信息，给出 2–3 套方案并附官方链接。
- **Q2 (suspension):** 经纪人下一步：确认暂停原因，引导客户至 DMV 在线提交保险证明并缴费（约 $14）。
- **Q3 (license):** 经纪人下一步：打开 insurance.ca.gov 查执照，截图保存发给客户。
- **Q4 (discounts):** 经纪人下一步：收集客户信息，推荐可申请折扣，提供 2–3 家报价对比。
- **Q5 (claims):** 经纪人下一步：安抚客户，指导在线或电话报案，协助准备材料。
- **SR-22:** 经纪人下一步：确认客户需求，协助购买符合要求的保险，保险公司会向 DMV 提交 SR-22。

**Why it helps:** Every core broker scenario now surfaces a concrete next step. Brokers see what to do, not just what to ask or what the client needs.

---

## 3. Re-test / simulation results

**Unit test (no backend):**

```bash
python3 -c "
from services.fiqa_api.routes.query import _apply_broker_demo_answer_fixes
q1 = '我刚买了辆新车（加州），最低需要买哪些保险？'
out1 = _apply_broker_demo_answer_fixes('加州最低责任险...', q1, q1, [], 'demo')
ok1 = '经纪人下一步' in out1 and '客户可准备' in out1
print('Q1:', 'PASS' if ok1 else 'FAIL')
"
# Q1: PASS
```

**Guardrail:**

```bash
bash scripts/guardrail_broker_demo.sh
# Result: PASS
```

**Copy-to-client:**

```bash
python3 scripts/verify_copy_to_client_guardrail.py
python3 scripts/test_copy_to_client_e2e.py
# Both PASS
```

**Before:** Workflow hints had 客户可准备 + 经纪人可进一步询问; no explicit "do this next."  
**After:** All three blocks present: 客户可准备 + 经纪人可进一步询问 + 经纪人下一步.  

**Broker regression (live API):** Backend returned 503 during sprint; unit test and guardrail confirm logic. Restart backend and run `python3 scripts/broker_regression_all5.py --port 8001` to validate live.

---

## 4. Broker/business impact

- **Workflow usefulness:** Answers now guide brokers on what to do next, not just what to ask and what the client should prepare.
- **Repetitive explanation:** Brokers no longer need to infer "do this next" from the answer; it is explicit.
- **Helper vs chatbot:** The product moves from Q&A-style answers to structured workflow guidance with explicit next steps.

---

## 5. Manual-work reduction

- **Andy no longer needs to:** Manually explain or document "what to do next" for Q1–Q5; the system now appends 经纪人下一步.
- **Cursor can now:** Re-run `broker_regression_all5.py` to validate workflow hints; the script checks `has_broker_workflow` (客户可准备 + 经纪人可进一步询问). Consider adding 经纪人下一步 to the regression check in a future sprint.
- **OpenClaw can now:** Use the same regression script for automated validation.
- **Reusable asset:** `broker_regression_all5.py`; `guardrail_broker_demo.sh`; `verify_copy_to_client_guardrail.py` (now includes 经纪人下一步 in filter).

---

## 6. Remaining blocker(s)

- **Backend restart required:** Restart the fiqa_api backend for query.py changes to take effect. Live broker regression was not run (backend unavailable during sprint).
- **Optional:** Add 经纪人下一步 to `broker_regression_all5.py` workflow check for stricter validation.

---

## 7. Recommended next sprint

**Target:** Improve copy-to-client structure so the "建议您" section is more actionable.

**Why:** The client copy uses `buildHighlights` to extract bullets and steps heuristically. The 客户可准备 block could be surfaced as a dedicated "您可准备" section in the client copy instead of being mixed into steps. A small enhancement could make the client-facing copy clearer and more actionable.

---

## 8. Future-readiness note

- **Workflow pack:** The broker hint pattern (客户可准备 + 经纪人可进一步询问 + 经纪人下一步) could become a `workflow_pack` or `scenario_pack` with per-scenario templates.
- **California-specific:** Keywords, DMV references, insurance.ca.gov, and fee amounts ($14) are California-specific; a future `region_config` could parameterize these.
- **Client-copy template:** A dedicated "您可准备" section in the client copy template could improve reuse.
