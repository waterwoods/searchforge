# Backend Redeploy for Lightweight Case Record — Report

**Sprint**: Backend Redeploy for Lightweight Case Record  
**Date**: 2026-03-16

---

## 1. Sprint Theme

- **What was redeployed:** Backend (fiqa-api) to Cloud Run with Lightweight Production Case Record changes
- **Why now:** Case-record improvements (case_messages, workflow state, customer linkage) were implemented but not yet live in production

---

## 2. Control Docs Created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `01_SPRINT_BLUEPRINT.md` |
| Execution Outline | `02_EXECUTION_OUTLINE.md` |
| Acceptance / Operational Criteria | `03_ACCEPTANCE_OPERATIONAL_CRITERIA.md` |

---

## 3. Pre-Deploy Validation

| Check | Result |
|-------|--------|
| verify_inbox_case_persistence.py | PASS |
| run_inbox_triage_scenarios.py | 53/53 (via guardrail) |
| run_multi_turn_simulations.py | 38/38 PASS |
| audit_state_field_accuracy.py | 6/7 (M1 pre-existing) |
| verify_speed_routing.py | OK |
| guardrail_inbox_triage.sh | PASS |

**Files inspected:** case_store.py, routes/inbox_triage.py, triage.py  
**Expected logic found:** case_messages, update_case_customer, handoff_ready, workflow state, customer fields  
**Blocker:** None

---

## 4. Backend Redeploy Result

| Item | Value |
|------|-------|
| **Success** | Yes (exit 0) |
| **Backend URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **Revision** | fiqa-api-00022-fnm |
| **Project** | optimal-disk-472305-e2 |
| **Region** | us-west1 |
| **Warnings** | /healthz failed in deploy script (5s post-deploy); /readyz OK |
| **Notes** | Build ~4.5 min; deploy completed |

---

## 5. Post-Deploy Verification

| Check | Result |
|-------|--------|
| /healthz | 404 (script check); /readyz 200 OK |
| /readyz | 200, ok:true, intake_path_ready:true |
| Case creation (persist_case=true) | case_id, case_messages (1), handoff_ready ✓ |
| GET /api/inbox/cases | case_messages present ✓ |
| POST append-message | case_messages grew 1→3 ✓ |
| PATCH /customer | customer_name, phone, policy_number stored ✓ |

**Directly confirmed in production:**
- Case creation returns case_messages
- Append adds messages (no overwrite)
- Customer linkage PATCH works
- Workflow state (handoff_ready) present

---

## 6. Optional Second Loop

**Not used.** No issues requiring a second deploy.

---

## 7. Final Operational Judgment

1. **Did backend redeploy succeed?** Yes.
2. **Are the lightweight case-record changes now live?** Yes. case_messages, workflow state, customer linkage verified in production.
3. **Can the founder now go to Vercel and more honestly/demo-confidently show the system?** Yes. Backend serves the new case-record model.
4. **Biggest remaining risk:** Case storage is ephemeral (Cloud Run container filesystem). Cases lost on scale-to-zero or new instance. Acceptable for demo.
5. **What Andy should inspect next on frontend/workbench:** (a) Create case from Customer Entry, confirm case appears in Workbench with case_messages. (b) Append follow-up, confirm new messages visible. (c) PATCH customer via API or future UI, confirm customer info displays.

---

## 8. 中文宏观总结

- **backend 是否重新部署成功：** 是
- **轻量正式 case record 有没有上线：** 有。case_messages、workflow state、customer linkage 已在生产验证
- **现在是不是可以去 Vercel 更完整地展示了：** 是
- **最大剩余风险：** 案件存储是临时的（Cloud Run 容器内），实例重启后丢失。演示可接受
- **我下一步具体该测什么：** 在 Vercel 打开 workbench，创建案件、追加消息、确认 case_messages 和客户信息显示

---

## 9. COPY/PASTE EXECUTION BLOCK

**Backend deploy status:** Success. fiqa-api live at https://fiqa-api-g7zatxrycq-uw.a.run.app

**Lightweight case record live?** Yes. case_messages, workflow state, customer linkage verified in production.

**Should Andy show/test Vercel now?** Yes.

**Biggest remaining risk:** Case storage ephemeral (Cloud Run). Acceptable for demo.

**Exact next tests:** (1) Open Vercel workbench, create case, append follow-up. (2) Confirm case_messages and customer fields in case detail. (3) If UI does not yet show messages/customer, consider adding.
