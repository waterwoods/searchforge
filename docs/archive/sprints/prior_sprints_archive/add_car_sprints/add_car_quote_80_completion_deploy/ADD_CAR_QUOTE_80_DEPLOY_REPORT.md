# Add-Car Quote 80% Completion Deploy Report

**Sprint:** Add-Car Quote 80% Completion Deploy Sprint  
**Date:** 2025-03-16  
**Execution:** Cursor Composer multi-agent operational sprint

---

## 1. Sprint Theme

- **What was deployed:** Add-Car Quote 80% Completion backend logic (handoff requires zip + delivery/driver; richer extraction; flow continues after ZIP)
- **Why now:** Founder needs to inspect the stronger add-car flow on live Vercel. The improved flow is only valuable if it is actually in production.

---

## 2. Control Docs Created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/add_car_quote_80_completion_deploy/SPRINT_BLUEPRINT.md` |
| Execution Outline | `docs/sprints/add_car_quote_80_completion_deploy/EXECUTION_OUTLINE.md` |
| Acceptance / Operational Criteria | `docs/sprints/add_car_quote_80_completion_deploy/ACCEPTANCE_CRITERIA.md` |

---

## 3. Pre-Deploy Validation

### Files Inspected

- `services/fiqa_api/inbox_triage/triage.py` — `_add_car_enough_for_handoff` requires vehicle + zip + (delivery or driver); `_get_next_ask_for_add_car` asks delivery/driver when zip-only
- `configs/customer_entry_multi_turn_simulations.json` — add-car scenarios aligned with 80% completion
- `configs/simulation_assistant_scenarios.json` — add-car scenarios present
- `ui/src/config/simulation_assistant_scenarios.json` — in sync with backend config

### Expected Logic Found

- `_add_car_enough_for_handoff`: vehicle_ok + has_zip + has_delivery_or_driver ✓
- `_get_next_ask_for_add_car`: asks year/model → zip → delivery/driver in order ✓
- Richer extraction: insurance_status, additional_drivers ✓

### Validation Results

| Script | Result |
|--------|--------|
| `run_inbox_triage_scenarios.py` | 53/53 passed |
| `run_multi_turn_simulations.py` | 38/38 passed |
| `audit_state_field_accuracy.py` | 6/7 passed (M1 missing_document — not Add-Car, scoped out) |
| `verify_speed_routing.py` | 9/9 OK |
| `guardrail_inbox_triage.sh` | PASS |
| `unified_intake_smoke_check.sh` | PASS |

### Blocker

None. All Add-Car validations passed.

---

## 4. Backend Redeploy Result

| Field | Value |
|-------|-------|
| **Success** | Yes |
| **Backend URL** | https://fiqa-api-1013093472160.us-west1.run.app (from gcloud) |
| **Alternate URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app (per DEMO_CHECKLIST) |
| **Revision** | fiqa-api-00024-sxp |
| **Warnings** | /healthz returned 404 during deploy script health check |
| **Notes** | /readyz OK; /api/inbox/triage OK; intake_path_ready=true |

---

## 5. Frontend Deploy Result

| Field | Value |
|-------|-------|
| **Success** | Yes |
| **Production URL** | https://ui-smoky-beta.vercel.app |
| **Deployment URL** | https://ui-8csj0cr5o-andys-projects-1f411b73.vercel.app |
| **Alias Updated** | Yes — ui-smoky-beta.vercel.app |
| **Warnings** | Chunk size warning (non-blocking) |

**Judgment:** Frontend redeploy was performed to reduce ambiguity for the founder. Add-car logic is backend-driven; frontend bundles scenario config. Redeploy ensures latest config and alignment with new backend.

---

## 6. Post-Deploy Verification

### Health / Readyz

- **/readyz:** OK — `{"ok":true,"status":"ready","intake_path_ready":true}`
- **/healthz:** 404 (deploy script; may be load balancer config). Root `/` and `/api/inbox/triage` work.

### Add-Car First Turn

- **Input:** "我想加一台X5"
- **Result:** handoff_ready=False; draft asks "先把年份和地址邮编发我"
- **Confirmed:** ✓

### Add-Car Second Turn (zip only)

- **Input:** "想加一台2024宝马X5" + "90210"
- **Result:** handoff_ready=False; draft asks "提车日期和主要驾驶人发我一下"
- **Confirmed:** ✓ — zip alone is NOT enough for handoff

### Add-Car Third Turn (delivery)

- **Input:** + "下周提车"
- **Result:** handoff_ready=True; handoff reply "报价资料已整理好了，办公室会尽快出价"
- **Confirmed:** ✓

### Stronger Flow Directly Confirmed in Production

Yes. Production add-car flow matches the 80% completion spec: handoff requires zip + (delivery or driver); flow continues when only zip given.

---

## 7. Optional Second Loop

- **Used:** No
- **Reason:** No deployment mismatch revealed. All validations passed; production behavior matches expected.

---

## 8. Final Operational Judgment

| Question | Answer |
|----------|--------|
| Did backend deploy succeed? | Yes |
| Did frontend deploy succeed? | Yes |
| Is Add-Car Quote 80% Completion now live? | Yes |
| Can the founder now go to Vercel and inspect the new flow? | Yes |
| Biggest remaining risk? | /healthz 404 — cosmetic; readyz and API work. M1 (missing_document) state audit friction — not Add-Car. |
| Exact next tests for Andy? | See Section 10. |

---

## 9. 中文宏观总结

- **为什么现在要部署：** Add-Car 80% 流程已改好（zip 不够就 handoff、要 delivery/driver），但只有上线才有价值；创始人需要在 Vercel 上验收。
- **主要用了什么方法：** 先建控制文档 → 跑全量验证 → 部署后端 → 部署前端 → 生产验证 add-car 三回合。
- **现在是不是已经上线：** 是。后端和前端都已部署。
- **现在可不可以去 Vercel 看：** 可以。打开 https://ui-smoky-beta.vercel.app，进 Simulation Assistant 或 Broker Workbench 测 add-car。
- **最大剩余风险：** /healthz 404（不影响功能）；M1 missing_document 为既有问题，非 Add-Car。
- **我下一步具体该测什么：** 见下方 COPY/PASTE 块。

---

## 10. COPY/PASTE EXECUTION BLOCK

```
Add-Car Quote 80% Completion Deploy — Founder Summary
=====================================================

Backend deploy:     SUCCESS (revision fiqa-api-00024-sxp)
Frontend deploy:    SUCCESS (ui-smoky-beta.vercel.app)
Add-Car 80% live:   YES
Inspect Vercel now: YES

Backend URL:  https://fiqa-api-g7zatxrycq-uw.a.run.app
Frontend URL:  https://ui-smoky-beta.vercel.app

Biggest remaining risk: /healthz 404 (cosmetic); M1 missing_document friction (not Add-Car).

Exact next tests:
1. Open https://ui-smoky-beta.vercel.app/workbench/unified-intake
2. Simulation Assistant → Run SIM3 (Add-car quote Chinese), SIM15 (Add-car 3-turn)
3. Manual: Type "想加一台X5" → "90210" → verify system asks delivery/driver, NOT handoff
4. Manual: Add "下周提车" → verify handoff
5. Broker Workbench → Load founder demo queue → Add-car case → verify Collected: year, model, zip, delivery
```

---

## 11. REQUIRED SHORT OVERVIEW

### 为什么做这件事

Add-Car 80% 流程已改好，但只有上线才能让创始人在 Vercel 上验收。

### 主要用了什么方法/技术

控制文档 → 全量验证 → 后端部署 (deploy_rag_demo.sh) → 前端部署 (vercel --prod) → 生产 API 验证 add-car 三回合。

### 这轮最大的提升

Add-Car Quote 80% Completion 已上线；zip  alone 不再触发 handoff；流程会继续问 delivery/driver。

### 现在还差什么

/healthz 404（不影响功能）；M1 missing_document 为既有问题；创始人需在 Vercel 上做一次人工验收。
