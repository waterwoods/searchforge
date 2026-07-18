# P26G-R — QA Deploy & Founder Flow Validation

**Date:** 2026-07-18  
**Mode:** Release / validation only — no new features  
**Branch:** `sprint/p16-trust-layer`  
**Commit:** `884aa91b16b34caa2eb0b411c292232db4e93c0a` (`884aa91`)  
**Verdict:** **CONDITIONAL GO** — deploy + automated gates PASS; Founder device A–E still required

---

## 1. Release scope (included)

Exact files in commit `884aa91`:

| File | Role |
|------|------|
| `services/fiqa_api/inbox_triage/default_intake_plan.py` | Default intake SSOT |
| `services/fiqa_api/inbox_triage/constitution_projection.py` | Default task merge + `task_source` |
| `services/fiqa_api/inbox_triage/p20_case_intake_command_service.py` | Customer collecting phase |
| `services/fiqa_api/inbox_triage/p20_customer_start_claim.py` | Resume token issuance |
| `services/fiqa_api/inbox_triage/h5_task_upload.py` | system_default insurance slot |
| `services/fiqa_api/inbox_triage/p20_missing_information.py` | Insurance MVP sendable (follow-up) |
| `miniapp/pages/start-claim/start-claim.ts` | Persist resume → Entry |
| `miniapp/services/startClaimApi.ts` | Resume token client type |
| `miniapp/utils/startClaimEntry.ts` | Home / return-later routing |
| `miniapp/pages/receipt/receipt.ts` | Home vs Start New Claim |
| `miniapp/pages/request-item/*` | system_default insurance path + upload UX |
| `miniapp/types/task.ts` | `task_source` typing |
| `miniapp/utils/resolveCustomerConstitution.ts` | task_source typing |
| `miniapp/utils/resolveCustomerTaskCards.ts` | Card mapping deps |
| `miniapp/tests/startClaimPage.test.ts` | Resume navigation tests |
| `miniapp/tests/startClaimEntry.test.ts` | Entry/Home routing tests |
| `miniapp/tests/resolveCustomerTaskCards.test.ts` | Card tests |
| `tests/test_p26g_default_intake_and_resume.py` | Three flow gates |
| `tests/test_constitution_projection_customer_tasks.py` | Constitution regressions |
| `tests/test_p20_customer_start_claim.py` | Start Claim API |
| `tests/test_p20_send_request_command_service.py` | Broker follow-up send |
| `tests/test_p20_mvp_request_gating.py` | MVP sendable |
| `tests/test_p20_slice1_command_service.py` | Slice1 regressions |
| `tests/test_p20_slice1_e2e.py` | Slice1 e2e |
| `docs/product/p20_product_north_star.md` | §J2 gates |
| `docs/product/p20_production_loop_template.md` | Gate checklist |
| `docs/product/decision_log.md` | D-009 |
| `docs/product/p26g_user_journey_contract_template.md` | Journey contract |
| `docs/evidence/p26g_default_intake_persistent_resume_2026_07_18.md` | Impl evidence |

**Excluded from release:** `broker-workbench/`, `miniapp/pages/dev/*`, prototypes, UI Workbench WIP, unrelated product docs, `AGENTS.md` / founder checklist golden notes, `task-home.wxss` polish.

Worktree after push: **dirty** (excluded WIP remains local; not in commit).

---

## 2. Commit / push

| Field | Value |
|-------|--------|
| Full hash | `884aa91b16b34caa2eb0b411c292232db4e93c0a` |
| Short hash | `884aa91` |
| Branch | `sprint/p16-trust-layer` |
| Remote | `origin/sprint/p16-trust-layer` (pushed) |
| Worktree | Dirty (unrelated local WIP only) |

---

## 3. Deployment

| Surface | Identifier / URL | Status |
|---------|------------------|--------|
| QA API | https://fiqa-api-g7zatxrycq-uw.a.run.app | **PASS** |
| Revision | `fiqa-api-00225-ckv` @ **100%** | **PASS** |
| `/health/live` | `{"ok":true}` | **PASS** |
| `/readyz` | `intake_path_ready: true`, `readiness_mode: intake_core` | **PASS** |
| Start Claim | `POST /api/h5/customer/start-claim` → 201 + resume | **PASS** |
| Intake / Constitution | `GET /api/h5/tasks/{token}/intake` | **PASS** |
| QA Workbench | https://ui-smoky-beta.vercel.app/workbench/unified-intake | Not redeployed (not required for P26G code); existing surface for Gate D |
| Mini Program | Preview @ `884aa91` | `build:gate` + `preview:preflight` + component gates **PASS** |

---

## 4. Fresh QA case (API contract proof)

**Not** Camry Golden / Request More seed. Created via customer Start Claim only.

| Field | Value |
|-------|--------|
| case_id | `case_247cde95a5e9` |
| customer | Founder P26G-R (anonymous session) |
| vehicle | (none yet — default intake) |
| initial claim phase | `accident_basics_in_progress` (collecting) |
| broker request count | **0** |
| default task count | **3** (`accident_story`, `accident_photos`, `insurance_card`) |
| task_source | all `system_default` |
| Today | `上传保险卡` (not「先不用操作」) |
| stage | `customer_action_needed` |
| resume token issued | **yes** (preview only in probe JSON) |

Probe artifact: `docs/evidence/p26g_r_fresh_case_api_probe.json`  
Private device handoff (not committed): `/tmp/p26g_r_founder_handoff.json`

**Note:** Founder Gate A should **Start Claim on device** (creates their own case). The API case proves the server contract; do not inject a broker QR for first entry.

---

## 5. Preview prep gates

| Gate | Result |
|------|--------|
| 1. Changed components have index.ts/json/wxml/wxss (`task-photo` etc.) | **PASS** |
| 2. `usingComponents` path/case/existence (`npm run test:component-gates`) | **PASS** |
| 3. Clear cache → full compile before Preview | **Founder action** (agent cannot operate DevTools) |

**Do not use** `bash scripts/launch_golden_qa.sh --qa` for this loop — it reseeds Camry + Request More and would invalidate First-Time Customer Gate.

**Founder Preview steps:**

1. WeChat DevTools → 清缓存 → 全部清除  
2. Compile mode: **Start Claim (customer entry)** — empty query (no token)  
3. Full compile  
4. Generate Preview QR **once**  
5. On phone: clear mini program storage / reinstall if needed before Gate A  

---

## 6. Three permanent gates + A–E checklist

| Gate | Automated / API | Founder device |
|------|-----------------|----------------|
| First-Time Customer | **PASS** (fresh case, 0 broker, default tasks actionable) | ☐ PENDING |
| Return-Later | Prep ready (resume issued + Entry routing shipped) | ☐ PENDING |
| Exceptional Follow-Up | Prep ready (Slice1 send + Constitution merge tested) | ☐ PENDING |

| Step | Result |
|------|--------|
| A. First-Time Customer Gate | **BLOCKED** — awaiting Founder device |
| B. Default Task Completion | **BLOCKED** — awaiting Founder device |
| C. Return-Later Gate | **BLOCKED** — awaiting Founder device |
| D. Exceptional Follow-Up Gate | **BLOCKED** — awaiting Founder device |
| E. Broker Truth | **BLOCKED** — awaiting Founder device |

---

## 7. Automated test table

| Suite | Result |
|-------|--------|
| `tests/test_p26g_default_intake_and_resume.py` | **PASS** |
| `tests/test_constitution_projection_customer_tasks.py` | **PASS** |
| `tests/test_constitution_projection_api.py` | **PASS** |
| `tests/test_p20_customer_start_claim.py` | **PASS** |
| `tests/test_p20_send_request_command_service.py` | **PASS** |
| `tests/test_p20_mvp_request_gating.py` | **PASS** |
| `tests/test_p20_slice1_e2e.py` | **PASS** |
| miniapp startClaim / Entry / task cards / photos (75) | **PASS** |
| `npm run build:gate` | **PASS** |
| `npm run preview:preflight` | **PASS** |
| `npm run test:component-gates` | **PASS** |
| Fresh QA simulation (zero broker) | **PASS** → `case_247cde95a5e9` |

---

## 8. Evidence locations

- Impl: `docs/evidence/p26g_default_intake_persistent_resume_2026_07_18.md`
- This release: `docs/evidence/p26g_r_qa_deploy_founder_validation_2026_07_18.md`
- API probe: `docs/evidence/p26g_r_fresh_case_api_probe.json`
- North Star §J2 / D-009 / journey template (in commit)

---

## 9. Remaining defects

None observed in automated / API prep.

**Open:** Founder device A–E not yet executed → cannot mark FOUNDER FLOW COMPLETE.

---

## 10. Final verdict

**CONDITIONAL GO**

Deploy and automated regressions are healthy. Founder must complete device gates A–E on a real phone before **FOUNDER FLOW COMPLETE**.

**STOP** — do not begin P26B / P26C / account landing / case history.
