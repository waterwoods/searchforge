# P26G-Q1-R — QA Deploy & Founder Validation

**Date:** 2026-07-18  
**Mode:** Release only — no new features  
**Branch:** `sprint/p16-trust-layer`  
**Commit:** `0e6339edbde905017413f286541741018e3c5b38` (`0e6339e`)  
**Verdict:** **STOP** — deploy + API contract PASS; Founder device QA / screenshots not executed

---

## 1. Release scope (included)

Exact files in commit `0e6339e`:

| File | Role |
|------|------|
| `services/fiqa_api/inbox_triage/constitution_projection.py` | `insurance` vs `request_item` routes; no fake photo/story completion; honest Why; `action` payload |
| `miniapp/pages/request-item/request-item.ts` | Allow system_default insurance without Slice1 gate |
| `miniapp/utils/resolveCustomerTaskCards.ts` | Map `insurance` → upload page |
| `miniapp/types/task.ts` | `action` typing |
| `miniapp/tests/resolveCustomerTaskCards.test.ts` | Insurance / photos / story route mapping |
| `tests/test_p26g_q1_route_and_isolation.py` | Route / Zero-Broker / Isolation / New-vs-Resume gates |
| `tests/test_p26g_default_intake_and_resume.py` | Gate updates for `insurance` route + blocked photos |
| `tests/test_constitution_projection_customer_tasks.py` | Empty-slot One Truth honesty |

**Excluded:** `broker-workbench/`, `miniapp/pages/dev/*`, UI Workbench WIP, `task-home.wxss`, `AGENTS.md`, unrelated product docs / golden QA artifacts.

---

## 2. Commit / push

| Field | Value |
|-------|--------|
| Full hash | `0e6339edbde905017413f286541741018e3c5b38` |
| Short hash | `0e6339e` |
| Branch | `sprint/p16-trust-layer` |
| Remote | `origin/sprint/p16-trust-layer` (pushed) |
| Worktree | Dirty (unrelated local WIP only) |

---

## 3. Deployment

| Surface | Identifier / URL | Status |
|---------|------------------|--------|
| QA API | https://fiqa-api-g7zatxrycq-uw.a.run.app | **PASS** |
| Revision | `fiqa-api-00226-vnv` @ **100%** | **PASS** |
| `/health/live` | `{"ok":true}` | **PASS** |
| `/readyz` | `intake_path_ready: true`, `readiness_mode: intake_core` | **PASS** |
| Start Claim | `POST /api/h5/customer/start-claim` → 201 + resume | **PASS** |
| Intake / Constitution | `GET /api/h5/tasks/{token}/intake` | **PASS** |
| Mini Program | Preview @ `0e6339e` | `build:gate` + `preview:preflight` + component gates **PASS** |
| QA Workbench | https://ui-smoky-beta.vercel.app/workbench/unified-intake | Not redeployed (not required for Q1 client/API fix) |

---

## 4. Fresh QA case (API contract proof)

**Not** Camry Golden / Request More seed. Created via customer Start Claim only.

| Field | Value |
|-------|--------|
| case_id | `case_8a1754937290` |
| broker request count | **0** |
| Today | `上传保险卡` |
| Why | `事故经过已收到，请继续上传保险卡。` (no fake「现场照片已经完成」) |
| Story state | `completed` (description saved on Start Claim) |
| Photos state | `blocked`, progress `0/1` (**not** completed) |
| Insurance route | `insurance` (`system_default`, no `request_item_id`) |
| Insurance actionable | **true** |
| resume token | **yes** (preview only in probe JSON) |

Probe: `docs/evidence/p26g_q1_r_fresh_case_api_probe.json`  
Private handoff (not committed): `/tmp/p26g_q1_r_founder_handoff.json`

**Do not use** `bash scripts/launch_golden_qa.sh` for this loop.

---

## 5. Founder device QA

| Step | Result |
|------|--------|
| Clear mini-program storage | **PENDING** — Founder / DevTools |
| Start **New Claim** (not Resume) | **PENDING** |
| Basics only → Story completed / Photos not completed | **API PASS** · device **PENDING** |
| Tap Insurance → upload page (no「当前任务无需此步骤」) | **API route PASS** · device **PENDING** |
| Upload insurance → Task Home updates / re-entry | **PENDING** |
| Broker insurance follow-up → `request_item` still works | **Unit PASS** · device **PENDING** |
| Screenshots | **NONE** — agent cannot operate WeChat DevTools / phone |

**Founder Preview steps:**

1. WeChat DevTools → 清缓存 → 全部清除  
2. Compile mode: **Start Claim (customer entry)** — empty query (no token)  
3. Full compile → Preview QR once  
4. On phone: clear mini program storage before Start New Claim  

---

## 6. Automated tests

| Suite | Result |
|-------|--------|
| `tests/test_p26g_q1_route_and_isolation.py` | **PASS** |
| `tests/test_p26g_default_intake_and_resume.py` | **PASS** |
| `tests/test_constitution_projection_customer_tasks.py` | **PASS** |
| `npm run build:gate` | **PASS** |
| `npm run preview:preflight` | **PASS** |
| `npm run test:component-gates` | **PASS** |
| Fresh QA simulation (zero broker + Q1 asserts) | **PASS** → `case_8a1754937290` |

---

## 7. Remaining issues

1. Founder physical device QA not executed — no screenshots.  
2. Live insurance upload + Task Home refresh not exercised on device.  
3. Live broker follow-up insurance request not exercised on device (covered by unit gates).

---

## 8. Final verdict

**STOP**

Deploy and live API Q1 contracts are healthy. Do **not** mark Founder flow complete until device checklist + screenshots are recorded.

**STOP** — do not begin P26B / P26C / account landing / case history.
