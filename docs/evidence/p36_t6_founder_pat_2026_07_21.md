# P36 T6 — Founder PAT on Isolated Cloud QA

**Date/time:** 2026-07-21 ~18:33–18:37 UTC  
**Tester:** Cursor agent (ainew6380 / operator environment)  
**Final verdict:** see § Final Verdict  

**Synthetic PAT marker:** `P36-T6-FOUNDER-PAT-20260721`  
**No real customer PII used.**

---

## Clients / targets

| Item | Value |
|------|-------|
| Preferred client | Mini Program QA (`apiProfile=qa`) — **API-contract path** (same `/api/h5/customer/start-claim` the Mini Program calls). WeChat DevTools GUI compile was **not** executable in this agent environment. |
| Inspection client | Founder QA Console API (`/api/internal/founder-qa/*`) against Cloud QA |
| QA API URL | `https://fiqa-api-qa-g7zatxrycq-uw.a.run.app` |
| QA DB | `caseiq-qa` on `caseiq-pilot-pg` |
| Production API | `https://fiqa-api-g7zatxrycq-uw.a.run.app` (unchanged) |
| Production DB | `caseiq` (read-only verification only) |
| Session id (synthetic) | `wx_p36_t6_pat_20260721_synth` |
| Case id | `case_693dd3924952` |
| Resume token | masked `h5t1.eyJjYXN…0c56d8` (expires `2026-07-28T18:36:15Z`) |

---

## Preconditions

| # | Check | Result |
|---|-------|--------|
| 1 | Vercel Preview env from `ui/env.preview.example` | **PASS** — Preview previously pointed at Production (`fiqa-api-1013093472160…`). Set Preview-only via Vercel API: `VITE_API_BASE_URL=https://fiqa-api-qa-g7zatxrycq-uw.a.run.app`, QA intake key, `VITE_ENABLE_QA_TOOLS=1`. Production env rows left intact. **Preview redeploy still required** for UI bundle bake-in. |
| 2 | WeChat request合法域名 `fiqa-api-qa-g7zatxrycq-uw.a.run.app` | **BLOCKED / operator** — cannot verify WeChat MP admin from this environment. |
| 3 | DevTools clear-cache full compile + `apiProfile=qa` | **PARTIAL** — repo `apiProfile=qa` + Cloud QA URL confirmed; Build Gate **PASS** after fixing local gitignored `project.private.config.json` compile condition[0] → `pages/start-claim/start-claim`. **DevTools GUI clean-cache compile not run** (no WeChat DevTools here). |
| 4 | Isolation verifier | **PASS** — exit 0 (before and after PAT) |
| 5 | QA `/health/live` + `/readyz`; Production revision | **PASS** — live/readyz 200 after cold start; Production still `fiqa-api-00233-scz` / gen `233` |

**Three WeChat Release Gates (code-level):**

1. Component completeness (start-claim + task-cta quaternary files) — **PASS**  
2. `usingComponents` paths/casing — **PASS** (`/components/task-cta/index`)  
3. DevTools clean-cache full compile — **NOT PERFORMED** (environment); Build Gate evaluate on disk — **PASS**

No Production Mini Program upload. No Experience upload performed.

---

## PAT flow (step results)

| Step | Action | Result |
|------|--------|--------|
| 1 | Open QA client (API health) | **PASS** — `/health/live` 200 |
| 2–3 | Start claim via Mini Program contract `POST /api/h5/customer/start-claim` with PAT marker in description | **PASS** — HTTP 201 `outcome=accepted`, resume token issued |
| 4 | Capture case/session ids | **PASS** — `case_693dd3924952` via Founder QA identity/status |
| 5 | Follow-up write | **PASS** (after schema correction) — `append-message` (`new_message`) + case `notes` (`note`) both 200 |
| 6–7 | Leave / reopen same case | **PASS** — Founder status still bound to same `case_id` |
| 8 | Prior data present | **PASS** — marker + Camry present in H5 intake + case JSON |
| 9 | Founder Console inspect | **PASS** — `environment=qa`, `enabled=true`, case visible. **Note:** `production_like=true` on QA (see defects) |
| 10 | Rows in `caseiq-qa` | **PASS** — see DB proof |
| 11 | Zero rows in `caseiq` | **PASS** — see DB proof |

---

## Database proof (redacted)

### caseiq-qa (expected hits)

| Field | Value |
|-------|-------|
| `current_database()` | `caseiq-qa` |
| `service_records` match count | **1** |
| `record_id` | `case_693dd3924952` |
| `created_at` | `2026-07-21 18:36:15+00` |
| `updated_at` | `2026-07-21 18:36:49+00` |
| `record_messages` for case | **2** |
| `mp_customer_active_case` matches | **1** |
| extra preview (redacted) | contains PAT marker note bodies (no secrets) |

### caseiq Production (expected zero)

| Field | Value |
|-------|-------|
| `current_database()` | `caseiq` |
| match count for `record_id` **or** marker in `extra` | **0** |
| queried `case_id` | `case_693dd3924952` |
| queried marker | `P36-T6-FOUNDER-PAT-20260721` |

Production was queried **read-only**. No DDL/DML on `caseiq`.

---

## Product acceptance matrix

| Check | Classification | Notes |
|-------|----------------|-------|
| Founder can clearly start QA intake | **PASS** | Start-claim API accepted; resume token returned |
| Next action obvious | **PASS** (API) / **NOT APPLICABLE** (GUI) | API returns resume; GUI not exercised |
| Submission provides clear feedback | **PASS** | HTTP 201 + `outcome=accepted` |
| Same case can be resumed | **PASS** | Same `case_id` after re-status; resume token issued |
| State durable across reopen | **PASS** | Marker + vehicle text persist in intake/case |
| Founder can locate case afterward | **PASS** | Founder QA status/active_case + broker case GET |
| Errors understandable | **PASS WITH FRICTION** | Initial follow-up failed with schema 422/400 until correct field names used |
| No accidental Production branding/URL/data | **FAIL (P2)** | Founder status returned `production_like=true` while `environment=qa`; Vercel Preview was Production-backed until fixed mid-PAT |

---

## Defects found

| ID | Severity | Summary | Reproduction | Disposition |
|----|----------|---------|--------------|-------------|
| D1 | **P2** | Vercel Preview `VITE_API_BASE_URL` still pointed at Production before T6 | `vercel env pull --environment=preview` showed `fiqa-api-1013093472160…` | Fixed Preview-only env via API this task; **Preview redeploy still needed** |
| D2 | **P2** | Founder QA status on Cloud QA reports `production_like=true` | `GET /api/internal/founder-qa/status` on `fiqa-api-qa` | Recorded; no broad repair in T6 |
| D3 | **P3** | Follow-up write schemas not discoverable (`notes` needs `note`; append needs `new_message`) | Wrong body keys → 422/400 | Narrow retry succeeded; no product change |
| D4 | **P1 (process)** | WeChat DevTools GUI PAT + legal-domain verification not completed in agent environment | N/A | Operator follow-up before phone Experience PAT |
| D5 | **P3** | Local gitignored compile condition had `service-home` first (Build Gate fail) | `project.private.config.json` | Fixed locally (not committed); Build Gate PASS |

No **P0** isolation breach. Production DB zero-match proven.

---

## Production non-mutation proof

| Check | Result |
|-------|--------|
| Production Cloud Run revision | `fiqa-api-00233-scz` / gen `233` (unchanged before & after) |
| Production Vercel env rows | Still present (`VITE_API_BASE_URL` Production 6d ago, etc.) — not deleted |
| Production DB `caseiq` PAT rows | **0** |
| Production Mini Program release | **None** |
| Secrets / PII committed | **None** |

---

## Post-PAT verification

| Check | Result |
|-------|--------|
| Isolation verifier | PASS exit 0 |
| QA `/health/live` | 200 |
| QA `/readyz` | ready / `intake_path_ready=true` |
| Production revision | unchanged |
| Production marker rows | 0 |
| Secrets committed | no |

---

## Operator follow-ups (not done in T6)

1. Redeploy **Vercel Preview only** (`cd ui && vercel --yes` — never `--prod`) so Preview UI bakes Cloud QA URL.  
2. Confirm WeChat admin request合法域名 includes `fiqa-api-qa-g7zatxrycq-uw.a.run.app`.  
3. In WeChat DevTools: clear cache → full compile → smoke Start Claim on phone/Experience if desired.  
4. Investigate why Founder QA reports `production_like=true` on `fiqa-api-qa`.

---

## Final Verdict

**P36 PASS WITH FOLLOW-UP DEFECTS**

A synthetic Founder PAT case was created through the Mini Program start-claim API against `fiqa-api-qa`, resumed/inspected via Founder QA APIs, persisted in `caseiq-qa` (`case_693dd3924952`, marker present, messages/notes durable), and proven **absent** from Production `caseiq`. Isolation and Production non-mutation hold.

Follow-up defects remain for Preview redeploy, WeChat GUI/legal-domain operator steps, and the `production_like=true` signal on QA — none are P0 isolation breaches.
