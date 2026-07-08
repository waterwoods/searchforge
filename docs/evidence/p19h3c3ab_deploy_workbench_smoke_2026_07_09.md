# P19H-3c-3AB — Deploy + Workbench Smoke (Claim Evidence Checklist)

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Scope:** Deploy 3A backend + 3B frontend; smoke only — no new features, no schema change

---

## 1. Goal

Deploy P19H-3c-3A (`claim_evidence_summary` backend) and P19H-3c-3B (Workbench Evidence Checklist UI) to production/stable QA, then verify health, QA gate, API shape, and Workbench reachability.

---

## 2. Commits deployed

| Layer | Commit | Message |
|-------|--------|---------|
| Backend + image | `ad2d0a3` (`ad2d0a3db`) | feat: show Claim evidence checklist in Workbench |
| Includes 3A | `d2cd71f` | feat: add Claim evidence summary for Workbench |
| Frontend bundle | `ad2d0a3` | Same HEAD — checklist UI |

---

## 3. Backend deploy

| Field | Value |
|-------|-------|
| Service | `fiqa-api` |
| Project | `optimal-disk-472305-e2` |
| Region | `us-west1` |
| **Revision** | **`fiqa-api-00172-4hw`** |
| **URL** | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| **GIT_SHA** | `ad2d0a3db` (`GET /version`) |
| Script | `bash scripts/deploy_paid_pilot.sh` |
| Deploy time (UTC) | ~2026-07-08 19:35 UTC |

---

## 4. Frontend deploy

| Field | Value |
|-------|-------|
| Command | `vercel deploy --prod --yes` (from `ui/`) |
| Build env | `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL`, `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` |
| **Deployment URL** | `https://ui-1yuaetu0s-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| Vercel build | PASS (~52s) |
| Deploy time (UTC) | ~2026-07-08 19:37 UTC |
| Bundle check | `理赔照片`, `Evidence Checklist`, `下一步建议`, `claim_evidence_summary` present in `index-DskUhlzW.js` |

---

## 5. Pre-deploy tests

| Check | Result |
|-------|--------|
| `test_p19h3c3a_claim_evidence_summary_backend.py` | PASS (8/8) |
| `test_p19h3a_claim_workbench_visibility.py` | PASS (8/8) |
| `test_p19h3c1_claim_h5_evidence_foundation.py` | PASS (12/12) |
| `test_p19h3c2_claim_c1_h5_button.py` | PASS (8/8) |
| `pytest -k h5` | PASS |
| `claimWorkbenchDisplay.test.ts` (tsx) | PASS |
| `npm run build` (local) | PASS (~21s) |
| Pre-deploy QA gate (`--cloud-api`) | PASS |

Note: `ui/package.json` has no `npm test` script; utility test run via `npx tsx ui/src/features/intake/utils/claimWorkbenchDisplay.test.ts`.

---

## 6. Backend health

| Endpoint | Result |
|----------|--------|
| `GET /health/live` | **200** |
| `GET /readyz` | **200** |
| `GET /version` | `{"commit":"ad2d0a3db",...}` |

---

## 7. Post-deploy QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**Result: PASS** — QA UI + Cloud Run `fiqa-api-00172-4hw` + Cloud SQL aligned.

---

## 8. Workbench API smoke

**Endpoint:** `GET /api/inbox/cases?limit=50` (with `X-Unified-Intake-Api-Key`)

| Check | Result |
|-------|--------|
| Returns cases | YES (25 total) |
| Claim guided cases (`service_lane=claim`) | **1** (`case_b8d15b3ca59a`) |
| `claim_evidence_summary` on list | **YES** |
| Slots length | **3** |
| Slot keys | `customer_damage_photo`, `other_party_vehicle_photo`, `scene_photo` |
| Per-slot fields | `label`, `required_level`, `status`, `attachment_count` present |
| `broker_next_action` | YES |
| `summary_text` | YES |
| `claim_summary` | YES (on list) |

**Production claim case snapshot (`case_b8d15b3ca59a`):**

- `completion_level`: `complete`
- `broker_next_action`: 资料已基本齐全，请陈总人工确认后决定下一步。
- All 3 slots `received` via `h5_task`, 1 attachment each

### Known gap — GET single case

`GET /api/inbox/cases/{case_id}` does **not** call `enrich_cases_for_workbench()`. For `case_b8d15b3ca59a`:

- List: `claim_evidence_summary` **present**
- GET: `claim_evidence_summary` **absent** (also `claim_summary`, `display_status` absent)

**Impact:** `DocumentIntakeInboxPage` opens drawer with list stub (has summary), then `getSavedCase()` replaces detail and **drops** enrichment → drawer shows fallback **理赔照片状态暂未生成** after hydration.

**Recommended hotfix (next sprint, not in scope here):** enrich GET `/cases/{case_id}` same as list (one-line parity; no schema / no new rules).

---

## 9. Frontend Workbench reachability

| URL | Result |
|-----|--------|
| `https://ui-smoky-beta.vercel.app/workbench/document-intake` | **HTTP 200** |
| JS bundle contains checklist strings | **YES** |

No Playwright Workbench smoke script in repo (only unrelated e2e). **Visual drawer smoke: HUMAN-PENDING** (blocked by GET enrichment gap above).

---

## 10. Log check

Revision `fiqa-api-00172-4hw` (~250 lines):

| Finding | Status |
|---------|--------|
| `claim_evidence_summary` / `enrich_claim` errors | **None** |
| Workbench `/api/inbox/cases` 500 | **None** |
| Postgres read facade errors | **None** |
| Qdrant unreachable (6334) | Expected optional |
| Redis optional (6379) | Expected optional |
| Embedding warmup deferred | Expected optional |
| langgraph steward import disabled | Expected optional |

Vercel runtime logs: not inspected (CLI inspect available; build succeeded).

---

## 11. Manual smoke checklist for Andy

### Smoke A — Workbench visual

**Status: HUMAN-PENDING** (GET enrichment gap — expect fallback text until hotfix)

Open: https://ui-smoky-beta.vercel.app/workbench/document-intake

Open Claim case `case_b8d15b3ca59a` (or any `service_lane=claim`).

Expected after hotfix:

- Accident Basics card visible
- **理赔照片 / Evidence Checklist** section
- 3 slots with status icons
- **下一步建议** subsection

### Smoke B — End-to-end claim + H5 + Workbench

**Status: HUMAN-PENDING**

| Step | Input | Expected |
|------|-------|----------|
| 1 | WeCom: `我要理赔` | Claim lane |
| 2 | `开始理赔` | Accident basics prompt |
| 3 | `今天上午10点，在 Irvine Blvd 和 Culver 附近，对方变道刮到我左前门` | Step 1 complete + H5 button |
| 4 | Click **上传事故照片** | H5 damage photo slot |
| 5 | Upload test damage photo | Received |
| 6 | Workbench → Claim drawer | ✅ 自己车损照片 received; ○ other party missing; optional scene |

---

## 12. Constraints honored

| Constraint | Status |
|------------|--------|
| No schema change | ✅ |
| No new feature code in this sprint | ✅ |
| No OCR | ✅ |
| No WeCom direct image binding | ✅ |
| No identity resolver | ✅ |
| No H5 skip persistence | ✅ |
| No business rule changes | ✅ |

---

## 13. GO / HOLD

| Area | Verdict |
|------|---------|
| Backend deploy + health + list API | **GO** |
| Frontend deploy + bundle + reachability | **GO** |
| QA gate | **GO** |
| List API `claim_evidence_summary` | **GO** |
| Drawer visual / GET hydration | **HOLD** — needs GET enrichment parity hotfix |
| End-to-end WeCom/H5 smoke | **HUMAN-PENDING** |

**Overall: HOLD** on full Workbench drawer acceptance until GET `/cases/{id}` enrichment hotfix + Andy visual smoke.

---

## 14. Next recommended sprint

1. **Hotfix:** `GET /api/inbox/cases/{case_id}` → `enrich_cases_for_workbench` (parity with list; ~3 lines)
2. **Human Workbench smoke** — open Claim drawer, confirm checklist
3. **P19H-3c-3C** — H5 Slot Persistence / Skip Reason
4. **P19H-3c-R3** — Claim Identity Resolver Foundation

**STOP**
