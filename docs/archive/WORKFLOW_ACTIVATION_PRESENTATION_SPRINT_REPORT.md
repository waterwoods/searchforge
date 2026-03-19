# Workflow Activation + Presentation Sprint Report

**Sprint:** Workflow Activation + Presentation  
**Date:** 2026-03-06  
**Focus:** California Auto Insurance Broker Assistant

---

## 1. Activation status

**Workflow-helper logic is active** in the running system when using the Docker backend (port 8000).

| Check | Result |
|-------|--------|
| `_apply_broker_demo_answer_fixes` in `query.py` | ✅ Present and correct |
| Unit test (direct call) | ✅ Passes |
| Live regression Q1–Q5 | ✅ All show 客户可准备 + 经纪人可进一步询问 |

**Exact commands run:**

```bash
# Restart backend (Docker stack)
docker compose --env-file .env.current -p searchforge up -d qdrant rag-api

# Run broker regression (port 8000 = Docker rag-api)
python3 scripts/broker_regression_all5.py --port 8000 --report /tmp/broker_report.md
```

**Port note:** `run_demo_local.sh` starts backend on 8001; Docker rag-api uses 8000. For validation with Docker: `bash scripts/demo_quick_validate.sh --port 8000`.

**Q1–Q5 workflow hints now present:**

- **Q1 (new car):** 客户可准备：车辆信息、驾照、VIN（如有）。经纪人可进一步询问：车型、用途、预算、是否贷款、是否需加保碰撞/综合险。
- **Q2 (suspension):** 客户可准备：保险证明、驾照、DMV 通知函。经纪人可进一步询问：暂停原因（保险失效/费用）、是否已续保、当前保单号。
- **Q3 (license):** 客户可准备：公司/经纪人名称或执照号。经纪人可进一步询问：客户要查的是公司还是个人、是否有执照号，可引导至 insurance.ca.gov 查执照。
- **Q4 (discounts):** Already had broker hint; continues to show 客户可准备 + 经纪人可进一步询问.
- **Q5 (claims):** 客户可准备：保单号、驾照、事故说明、现场照片、对方信息。经纪人可进一步询问：事故时间、人员伤亡、是否已报警、保单号，指导在线或电话报案。

---

## 2. Presentation quality

**What looked good:**

- Workflow blocks (客户可准备, 经纪人可进一步询问) appear at the end of answers.
- Q4 discount scenario already had clear structure.

**What was weak:**

- Broker workflow block blended into main answer with no visual separation.
- "复制给客户" could include 经纪人可进一步询问 (broker-only) in bullets/steps, which is not client-facing.

**Changes made:**

1. **Broker workflow block separation** (`DemoPage.tsx` + `DemoPage.css`):
   - When answer contains `**客户可准备**`, split and render the broker block under a "经纪人工作流" label.
   - Added subtle border-top and label styling (purple accent) so brokers see it as a distinct section.

2. **Copy-to-client cleanup** (`demoCopy.ts`):
   - Filter out bullets/steps containing "经纪人可进一步询问" when building client-ready copy.
   - 客户可准备 remains in client copy (useful for clients); 经纪人可进一步询问 is broker-only.

**Why it helps:** Brokers get clear next-step guidance; client-facing copy stays focused; the product feels more like a workflow helper than a chatbot.

---

## 3. Re-test results

| Test | Before | After |
|------|--------|-------|
| Q1 workflow | ❌ | ✅ |
| Q2 workflow | ❌ | ✅ |
| Q3 workflow | ❌ | ✅ |
| Q4 workflow | ✅ | ✅ |
| Q5 workflow | ❌ | ✅ |
| Regression exit code | 1 (FAIL) | 0 (PASS) |

**Before:** Regression against port 8001 showed workflow=CHECK (Q1–Q5 missing hints). Backend on 8001 was running pre-change code or different path.

**After:** Regression against Docker rag-api (port 8000) shows workflow=OK for all Q1–Q5. Presentation changes: broker block visually separated; copy-to-client excludes broker-only content.

---

## 4. Broker/business impact

- **Workflow usefulness:** Brokers see what to ask next and what the client should prepare for every core scenario.
- **Copy-to-client:** "复制给客户（可直接发微信）" output stays client-focused; 经纪人可进一步询问 is excluded.
- **Helper vs chatbot:** Answers now follow 简短结论 → 权威依据 → 下一步建议 → 客户可准备 → 经纪人可进一步询问.

---

## 5. Manual-work reduction

| Task | Before | After |
|------|--------|-------|
| Manually check Q1–Q5 for workflow hints | Andy | `broker_regression_all5.py` |
| Validate workflow activation | Manual | `demo_quick_validate.sh --port 8000` |
| Copy-to-client quality | Manual review | Filter in `buildCopyTextClientReady` |

**Cursor can now:** Re-run `broker_regression_all5.py` to validate workflow hints; use `--port 8000` for Docker, `--port 8001` for run_demo_local.

**OpenClaw can now:** Use the same regression script for automated validation.

**Reusable asset:** `demo_quick_validate.sh` comment updated for port 8000 (Docker).

---

## 6. Remaining blocker(s)

- **Port mismatch:** Demo UI proxy targets 8001; Docker rag-api uses 8000. For demo with workflow hints via Docker: set `VITE_API_PROXY_TARGET=http://127.0.0.1:8000` when running UI, or use `run_demo_local.sh` with a backend that has the latest code and working Qdrant.

---

## 7. Recommended next sprint

**Target:** Ensure demo_quick_validate + snapshot_demo_answers run successfully against the backend used for demos (8001 or 8000), and that the offline pack (`demo_fallback.json`) includes workflow hints for Q1–Q5.

**Why:** Offline mode is the demo fallback. If the offline pack lacks workflow hints, brokers clicking the 5 questions in Offline mode won't see the new behavior. Run `snapshot_demo_answers.py` after a successful regression to refresh the pack.

---

## Future-readiness note (Step 5)

Without heavy refactoring, this sprint suggests:

- **Workflow pack:** The broker hint pattern (客户可准备 + 经纪人可进一步询问) is consistent; could become a `workflow_pack` or `scenario_pack` with per-scenario templates.
- **Broker output template:** Structured sections (简短结论 → 权威依据 → 下一步建议 → 客户可准备 → 经纪人可进一步询问) could be formalized as a template.
- **Client-copy template:** `buildCopyTextClientReady` already filters broker-only content; could be extended with explicit client vs broker sections.
- **Region-specific workflow config:** Keywords, DMV references, $14 fee are California-specific; a future `region_config` could parameterize these.

Documentation only. No architecture changes this sprint.

---

## Files changed this sprint

| File | Change |
|------|--------|
| `ui/src/utils/demoCopy.ts` | Filter 经纪人可进一步询问 from client-ready copy |
| `ui/src/pages/DemoPage.tsx` | Split answer; render broker workflow block with label |
| `ui/src/pages/DemoPage.css` | Styles for `.answer-broker-workflow` |
| `scripts/demo_quick_validate.sh` | Port comment: 8000 for Docker |
| `docs/WORKFLOW_ACTIVATION_PRESENTATION_SPRINT_REPORT.md` | This report |
