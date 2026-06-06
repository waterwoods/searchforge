# P16-F Phase 8 — Final Review

**Date:** 2026-05-31  
**Sprint:** P16-F Preview Network Debug + Role-C Simulation Test

---

## Validation run

| Check | Result |
|-------|--------|
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** (13/13 HT + batteries) |
| `source scripts/with_node22_path.sh && cd ui && npm run build` | **PASS** (with Preview env flags) |

---

## Answers

### 1. Is Preview usable right now?

**Partially.** UI shell loads after Vercel login, but **API workflow is broken** (queue load + triage) due to CORS. Not usable for end-to-end broker demo without env patch.

### 2. Is Network Error caused by CORS, API URL, auth, backend down, or other?

**CORS** — confirmed. Not API URL (bundle correct), not auth (anonymous endpoint), not backend down (health 200).

### 3. Can Andy review the UI despite Network Error?

**YES for visual/front-door review** (tabs, wayfinding, paste copy, practice scenarios) after Vercel login.  
**NO for functional review** (demo queue, paste triage, draft output) until CORS fixed.

### 4. Can Chen Kui test this Preview?

**NO-GO** until CORS fixed and Andy completes supervised 5-minute walkthrough with working API.

### 5. Should we fix Preview CORS now?

**YES** — Option B env patch is low-risk and unblocks the exact URL already shared. **Await Andy approval** before running `gcloud` command.

### 6. Should we use Production alias instead?

**NO** for Sprint A validation — `ui-smoky-beta` is old code and wrong default experience. Production alias is only a CORS workaround, not a product workaround.

### 7. Should we still proceed to P17?

**NO** — fix Preview CORS + Andy functional sign-off first. P17 blocked on working Preview E2E.

### 8. What is the exact next action?

Andy approves → run `gcloud run services update` from `P16F_FIX_PLAN.md` → verify OPTIONS 200 → Andy hard-refreshes Preview → paste cancellation test message → confirm triage + queue.

Secondary: add Preview env vars to Vercel dashboard; update `.env.cloudrun` before next backend deploy.

---

## Go / No-Go

| Gate | Verdict |
|------|---------|
| **Andy UI shell review** | **GO** (with Vercel login) |
| **Andy functional E2E** | **NO-GO** until CORS patch |
| **Chen Kui Preview** | **NO-GO** |
| **P17** | **NO-GO** |
| **Production deploy** | **NO-GO** (explicitly out of scope) |

---

*End of P16-F Phase 8*
