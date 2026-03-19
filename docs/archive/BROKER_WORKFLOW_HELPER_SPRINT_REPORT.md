# Broker Workflow Helper Sprint Report

## 1. Issue targeted

**Workflow gap:** Q1 (new car), Q2 (suspension), Q3 (license), Q5 (claims) lacked structured broker workflow hints—**客户可准备** (what client should prepare) and **经纪人可进一步询问** (what broker should ask next). Only Q4 (discounts) and SR-22/LT03 had these.

**Why it mattered most:** Brokers need to know what to tell the client, what to ask next, and what the client should prepare. Without these blocks, the product behaves like a Q&A tool instead of a workflow helper. The highest-value gap was the missing "what to ask next" and "what client should prepare" for the majority of core scenarios.

## 2. Changes made

| File | Change |
|------|--------|
| `services/fiqa_api/routes/query.py` | Extended `_apply_broker_demo_answer_fixes` to append scenario-specific broker hints for Q1, Q2, Q3, Q5 when the answer lacks them. Added `_BROKER_NEWCAR_KEYWORDS` and `_BROKER_LICENSE_KEYWORDS`. Each scenario now gets: **客户可准备** + **经纪人可进一步询问** blocks. |
| `scripts/broker_regression_all5.py` | Added `has_broker_workflow` check for Q1–Q5; updated report and `all_pass` to include workflow validation. |

**Hints added:**

- **Q1 (new car):** 客户可准备：车辆信息、驾照、VIN（如有）。经纪人可进一步询问：车型、用途、预算、是否贷款、是否需加保碰撞/综合险。
- **Q2 (suspension):** 客户可准备：保险证明、驾照、DMV 通知函。经纪人可进一步询问：暂停原因（保险失效/费用）、是否已续保、当前保单号。
- **Q3 (license):** 客户可准备：公司/经纪人名称或执照号。经纪人可进一步询问：客户要查的是公司还是个人、是否有执照号，可引导至 insurance.ca.gov 查执照。
- **Q5 (claims):** 客户可准备：保单号、驾照、事故说明、现场照片、对方信息。经纪人可进一步询问：事故时间、人员伤亡、是否已报警、保单号，指导在线或电话报案。

**Why it helps:** Every core broker scenario now surfaces actionable workflow blocks. Brokers see what to ask and what the client should prepare, reducing mental load and manual lookup.

## 3. Re-test / simulation results

**Unit test (direct call):** All Q1–Q5 broker hints added correctly when `_apply_broker_demo_answer_fixes` is called with mock answers.

**Live API:** Regression run against backend at port 8001. Workflow hints did not appear—backend was running pre-change code. **Restart backend** to pick up changes, then re-run:

```bash
# Restart backend (e.g. make restart-backend or your usual command)
python3 scripts/broker_regression_all5.py --port 8001 --report /tmp/broker_report.md
```

Quick unit test (no backend needed):

```bash
python3 -c "
from services.fiqa_api.routes.query import _apply_broker_demo_answer_fixes
q = '我刚买了辆新车（加州），最低需要买哪些保险？'
out = _apply_broker_demo_answer_fixes('加州最低责任险...', q, q, [], 'demo')
print('OK' if '经纪人可进一步询问' in out and '客户可准备' in out else 'FAIL')
"
```

**Before:** Q1, Q2, Q3, Q5 answers had no 客户可准备 or 经纪人可进一步询问 blocks.  
**After (with restarted backend):** All five scenarios should include these blocks.

## 4. Broker/business impact

- **Workflow usefulness:** Answers now guide brokers on what to ask next and what the client should prepare, not just what to say.
- **Repetitive explanation:** Brokers no longer need to remember or look up these follow-up questions; they appear in the answer.
- **Helper vs chatbot:** The product moves from Q&A-style answers to structured workflow guidance (简短结论 → 权威依据 → 下一步建议 → 客户可准备 → 经纪人可进一步询问).

## 5. Manual-work reduction

- **Andy no longer needs to:** Manually explain or document "what to ask next" and "what client should prepare" for Q1–Q5; the system now appends these.
- **Cursor can now:** Re-run `broker_regression_all5.py` to validate workflow hints; the script checks `has_broker_workflow` for Q1–Q5.
- **OpenClaw can now:** Use the same regression script for automated validation.
- **Reusable asset:** `broker_regression_all5.py` now validates broker workflow hints; use `--report PATH` for pre-demo validation.

## 6. Future extraction note

- **Reusable:** The broker hint pattern (客户可准备 + 经纪人可进一步询问) is consistent across scenarios; could become a `workflow_pack` or `scenario_pack` with per-scenario templates.
- **California-specific:** Keywords, DMV references, insurance.ca.gov, and fee amounts ($14) are California-specific; a future `region_config` could parameterize these.

## 7. Remaining blocker(s)

- **Backend restart required:** Restart the fiqa_api backend for changes to take effect. After restart, run `broker_regression_all5.py` to confirm workflow hints.

## 8. Recommended next sprint

**Target:** Improve copy-to-client so broker workflow blocks (客户可准备, 经纪人可进一步询问) are clearly separated for broker use, while the client-ready copy stays client-focused.

**Why:** The full answer now includes both client-facing content and broker-only workflow hints. A small UI or copy enhancement could surface "经纪人工作流" as a collapsible section, keeping the copy-to-client button output clean for client sharing.
