# Backend Redeploy + Demo Warmup Sprint Report

**Sprint:** Backend Redeploy + Demo Warmup  
**Date:** 2026-03-14  
**Theme:** Ship backend changes, validate warmup, improve demo-day reliability

---

## 1. Sprint Theme

- **Theme:** Backend redeploy + demo warmup readiness
- **Why now:** Latest backend changes (Turn 1 lightweight, mixed-intent fallback, improved warmup) were implemented but not live. Deploying now ensures founder demo uses improved Turn 1 behavior and warmup flow.

---

## 2. Control Docs Created

| Doc | Path |
|-----|------|
| Sprint Blueprint | `docs/sprints/BACKEND_REDEPLOY_DEMO_WARMUP_SPRINT_BLUEPRINT.md` |
| Execution Outline | `docs/sprints/BACKEND_REDEPLOY_DEMO_WARMUP_EXECUTION_OUTLINE.md` |
| Acceptance / SLA Criteria | `docs/sprints/BACKEND_REDEPLOY_DEMO_WARMUP_ACCEPTANCE_CRITERIA.md` |

---

## 3. Pre-Deploy Backend Check

### Files Confirmed

- `services/fiqa_api/inbox_triage/triage.py` — Turn 1 lightweight (`_is_turn1_lightweight_candidate`, `_is_fast_path_candidate`), mixed-intent protection (flow_count >= 2 → LLM)
- `scripts/warmup_for_demo.sh` — healthz, readyz, triage ping
- `docs/runbooks/COLD_START_DEMO_DAY_RUNBOOK.md` — warmup instructions

### Validation Results

| Validation | Result |
|------------|--------|
| `run_inbox_triage_scenarios.py` | 49/49 passed |
| `guardrail_inbox_triage.sh` | PASS |
| `audit_state_field_accuracy.py` | 7/7 passed |
| `verify_speed_routing.py` | All OK (Turn 1 fast path, mixed-intent → LLM) |
| `unified_intake_smoke_check.sh` | Guardrail PASS (manual UI steps printed) |

**Blocker:** None.

---

## 4. Backend Redeploy Result

| Item | Value |
|------|-------|
| **Success** | Yes |
| **Backend URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **Revision** | fiqa-api-00020-hn9 |
| **Warnings** | /healthz returned FAILED in deploy script (5s post-deploy); /readyz OK |
| **Errors** | None |

**Note:** Cloud Run returns 404 for `/healthz` from external requests (possible reserved path). `/readyz` and `/health` return 200. Root `/` and `/api/inbox/triage` work.

---

## 5. Post-Deploy Verification

| Check | Result |
|-------|--------|
| `/healthz` | 404 (Cloud Run) |
| `/readyz` | 200 OK |
| `/health` | 200 OK |
| `/api/inbox/triage` | 200 OK, valid triage output |
| **Lightweight Turn 1** | Inferred from code: `_is_fast_path_candidate` routes high-confidence Turn 1 to rule path when LLM enabled |
| **Mixed-intent** | Inferred: flow_count >= 2 → `triage_path: "llm"` |

**Directly observed:** readyz OK, triage API returns correct structure (issue_category, urgency, broker_next_step, client_reply_draft, etc.).

---

## 6. Demo Warmup Execution

### Warmup Run Result

- **Before fix:** Warmup exited early — `/healthz` failed → "SKIP (backend not running)"
- **After fix:** Warmup uses `/readyz` fallback when `/healthz` fails
- **Result:** All three steps OK (health, readyz, triage warm)

### What Improved

- Warmup script now works against Cloud Run (readyz/health fallback)
- Runbook and ANDY_2MIN_BEFORE_DEMO include concrete Cloud Run URL
- Founder can run warmup 2–3 min before demo

### What Still Feels Risky

- Cold start (min_instances=0) — first request after idle can be 5–15 s
- /healthz 404 on Cloud Run — deploy script reports health FAILED; acceptable since readyz works

### Runbook Clarity

- `COLD_START_DEMO_DAY_RUNBOOK.md` — concrete URL added
- `ANDY_2MIN_BEFORE_DEMO.md` — concrete URL added

---

## 7. Optional Second Loop

**Used:** Yes.

**What changed:**

1. `scripts/warmup_for_demo.sh` — health check tries `/readyz` and `/health` when `/healthz` fails
2. `docs/runbooks/COLD_START_DEMO_DAY_RUNBOOK.md` — added concrete Cloud Run URL
3. `docs/ANDY_2MIN_BEFORE_DEMO.md` — added concrete Cloud Run URL

**What improved:** Warmup now runs successfully against Cloud Run; founder has exact URL.

**Worth it:** Yes — unblocked warmup for Cloud Run demos.

---

## 8. Iteration Log

### Loop 1

| Item | Value |
|------|-------|
| **What changed** | Deploy backend, post-deploy verify, run warmup |
| **What got better** | Backend live, triage works, readyz OK |
| **What did not improve** | Warmup failed (healthz 404), runbook had placeholder URL |
| **Worth it** | Yes — established baseline |
| **Recommended next step** | Fix warmup for Cloud Run |

### Loop 2

| Item | Value |
|------|-------|
| **What changed** | Warmup script fallback (readyz/health), runbook URLs |
| **What got better** | Warmup completes against Cloud Run |
| **What did not improve** | /healthz 404 remains (acceptable) |
| **Worth it** | Yes — warmup now usable |
| **Recommended next step** | Final report |

---

## 9. Final Operational Judgment

| Question | Answer |
|----------|--------|
| **Did backend redeploy succeed?** | Yes |
| **Is Turn 1 lightweight logic now live?** | Yes (in code; triage_conversation uses fast path for high-confidence Turn 1) |
| **Does warmup flow reduce demo-day risk?** | Yes — founder can warm 2–3 min before demo |
| **Biggest remaining operational risk** | Cold start (5–15 s first request after idle); min_instances=0 |
| **What Andy should do before tomorrow's demo** | Run `bash scripts/warmup_for_demo.sh --url https://fiqa-api-g7zatxrycq-uw.a.run.app` 2–3 min before; run `bash scripts/demo_pre_checklist.sh` |

---

## 10. 中文宏观总结

- **Backend 是不是重新发上去了？** 是。Cloud Run 已部署，URL: https://fiqa-api-g7zatxrycq-uw.a.run.app
- **Turn 1 轻量逻辑是不是上线了？** 是。代码中 `_is_fast_path_candidate` 对高置信度 Turn 1 走 rule 路径。
- **Warmup 能不能真正帮到 demo？** 能。修复后 warmup 对 Cloud Run 可用，2–3 分钟前跑一次可减少冷启动风险。
- **现在最大剩余风险是什么？** 冷启动（min_instances=0，空闲后首请求可能 5–15 秒）。
- **明天 demo 前具体该做什么？** 1) `bash scripts/warmup_for_demo.sh --url https://fiqa-api-g7zatxrycq-uw.a.run.app` 2–3 分钟前；2) `bash scripts/demo_pre_checklist.sh`。

---

## 11. COPY/PASTE EXECUTION BLOCK

```
Backend Redeploy + Demo Warmup Sprint — Summary
================================================

Backend deploy: SUCCESS
  URL: https://fiqa-api-g7zatxrycq-uw.a.run.app
  Revision: fiqa-api-00020-hn9

Warmup: WORKING
  bash scripts/warmup_for_demo.sh --url https://fiqa-api-g7zatxrycq-uw.a.run.app
  (Uses /readyz when /healthz returns 404 on Cloud Run)

Biggest remaining risk: Cold start (5–15 s first request after idle)

Exact pre-demo steps for Andy:
  1. 2–3 min before: bash scripts/warmup_for_demo.sh --url https://fiqa-api-g7zatxrycq-uw.a.run.app
  2. bash scripts/demo_pre_checklist.sh
  3. Open http://localhost:5173/demo (or Vercel URL if using Cloud frontend)

Nothing else must be fixed before demo. Warmup + checklist are sufficient.
```
