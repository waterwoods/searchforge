# P19M Phase 1 — Final E2E Acceptance and Closeout

**Date:** 2026-07-11  
**Branch:** `sprint/p16-trust-layer`  
**HEAD (pre-commit):** `fd6e3aa` — chore: finalize legacy Neon deletion

---

## 1. Environment Status (Phase 0–1)

| Check | Result |
|-------|--------|
| Branch | `sprint/p16-trust-layer` |
| API port 8001 | ✅ Exactly **one** healthy process (`python3` pid 480261) |
| Docker uvicorn on 8000 | Present (separate stack — **not** duplicate on 8001) |
| `/readyz` | ✅ `ok: true`, `intake_path_ready: true` |
| `/health` persistence | ✅ `STRICT_PG_ONLY`, `postgres_case_persistence_primary: true`, `json_case_writes: false` |
| Script DB bootstrap | ✅ `provider=gcp-cloud-sql`, `is_neon=False` (Neon legacy deleted) |
| Mini Program pages | ✅ 8/8 resolve (`p19m1a_verify_miniapp_pages.py`) |
| Founder GUI token | ✅ Resolves — masked `h5t1.eyJ…af8a15` |
| Founder GUI case ID | `case_a1cf5dfea5c6` (QA label `P19M1A-DEVTOOLS-E2E-founder-gui`) |
| Token in tracked files | ✅ None committed (`config.local.ts` gitignored) |

**Preserved:** All unrelated working-tree changes (UI polish wxml/wxss, `project.config.json`, untracked evidence JSON) left unstaged.

---

## 2. Runtime Fixes (Phase 2)

| # | Issue | Fix | Files |
|---|-------|-----|-------|
| 1 | `devLog.ts` module failed to resolve in DevTools bundle | Colocate `devLog()` in `config.ts`; no separate module | `miniapp/utils/config.ts` |
| 2 | `require("./config.local")` not bundled — `devTaskToken` silently empty | Static `import` from `config.local.ts` | `miniapp/utils/config.ts` |
| 3 | Entry `redirectTo` left loading spinner on navigation failure | `wx.reLaunch` + `fail` handler sets error state | `miniapp/pages/entry/entry.ts` |
| 4 | API hang risk on bad network | `timeout: 30000` on `wx.request` | `miniapp/utils/request.ts` |
| 5 | Token source opaque during DevTools debugging | `inspectLaunchTokenSources()` + gated `devLog` | `miniapp/services/taskLaunchContext.ts` |

**Runtime audit confirmations:**

| Item | Status |
|------|--------|
| No `devLog.ts` file / `require("./devLog")` | ✅ PASS |
| No circular dependency (devLog in config, imported by launch context) | ✅ PASS |
| Entry stable navigation to task-home / receipt | ✅ PASS (`reLaunch`) |
| Navigation failure → error UI (not infinite loading) | ✅ PASS |
| Request timeout | ✅ PASS (30s) |
| Duplicate-tap guard (task-home `navigating`, review `submitting`, story `saving`) | ✅ PASS |
| Resume storage (`persistLaunchToken` / `loadResumeToken`) | ✅ PASS |
| Submit-once (`X-Submit-Intent-Id` + `already_submitted`) | ✅ PASS (backend + in-process E2E) |

**Uncommitted (not in this commit):** P19M-2 UI polish (wxml/wxss), `project.config.json`, copy tweaks in `taskMapping.ts` / `receipt.ts`.

---

## 3. Tests (Phase 2)

```bash
PYTHONPATH=. python3 -m pytest \
  tests/test_p19m1_mini_program_logic.py \
  tests/test_h5_claim_intake_form.py \
  tests/test_h5_task_token.py \
  tests/test_h5_task_link.py \
  tests/test_h5_single_slot_upload.py \
  tests/test_p19h3h_append_first_split_later.py \
  tests/test_p19h3i_claim_task_dashboard_always_return_h5.py \
  tests/test_p19h3i_claim_photo_ack_h5_link.py \
  tests/test_p19h3e1_claim_timeline_case_brief.py \
  tests/test_p19h3e1b_claim_case_brief_highlights.py \
  tests/test_p19h3a_claim_workbench_visibility.py \
  tests/test_p19h3c3c_h5_claim_slot_persistence.py \
  tests/test_p19h3c1_claim_h5_evidence_foundation.py \
  tests/test_p19h3c3a_claim_evidence_summary_backend.py \
  tests/test_p19h3f2_true_end_card_on_broker_done.py \
  tests/test_p19i2c_claim_state_kernel_parity.py \
  --maxfail=0 -q
```

| Result | Count |
|--------|-------|
| **Passed** | **181** |
| Failed | 0 |

---

## 4. Automated E2E Support (Phase 3)

**Founder GUI case (`case_a1cf5dfea5c6`) — read-only Cloud SQL inspection (2026-07-12, not overwritten):**

| Field | Value |
|-------|-------|
| DB | `provider=gcp-cloud-sql` (Neon deleted) |
| Phase | `other_party_complete` |
| Submitted | `false` |
| `broker_done` | `false` |
| Story | **Saved** (`accident_description` present) |
| Basics | **Partial** — datetime `7/8`, location `irvine`, injury `yes`; `vehicle_details` empty |
| Photos | **2** (`attachment_count=2`) |
| Current step | `review` |
| Submit events | 0 |
| `workbench_visible` | `false` (expected until submit) |
| `updated_at` | `2026-07-12T06:11:15Z` |

**Decision:** Did **not** auto-complete submit on this case — preserves Founder GUI path for Review → Receipt → Resume → Workbench.

**API contract proof (isolated in-process smoke — fresh case, does not touch Founder case):**

```bash
PYTHONPATH=. python3 scripts/p19m1a_devtools_e2e_smoke.py --inprocess
```

| Step | Result |
|------|--------|
| Load Task Home | ✅ |
| Save Story | ✅ |
| Save Basics | ✅ |
| Upload Photo 1 + 2 | ✅ |
| Refresh / Review | ✅ |
| Submit once | ✅ |
| Duplicate submit idempotent | ✅ |
| Resume submitted case | ✅ |
| Workbench readback | ✅ (`submit_event_count: 1`, `broker_done_false`) |

Evidence: `docs/evidence/p19m1a_devtools_e2e_smoke_20260712_0514.json`

---

## 5. Broker Workbench Readback (Phase 4)

**Founder GUI case (`case_a1cf5dfea5c6`) — backend vs GUI verification:**

| Item | BACKEND VERIFIED | FOUNDER GUI VERIFIED |
|------|------------------|----------------------|
| QA/test label | ✅ `P19M1A-DEVTOOLS-E2E-founder-gui` | — |
| Launch / token resolve | ✅ | ✅ Task Home reached |
| Accident story | ✅ saved | ✅ (DevTools save reflected in Cloud SQL) |
| Accident date/time, location, injury | ✅ partial (vehicle empty) | ✅ partial |
| Two photos/evidence | ✅ count **2** | ✅ (uploads in Cloud SQL) |
| Current H5 step | ✅ `review` | ⏳ Review page not yet signed off |
| Submitted / broker-review state | ❌ `submitted=false` | ⏳ |
| Timeline submit event | ❌ 0 events | ⏳ |
| `broker_done=false` | ✅ | — |
| Workbench visible + enrichment | ❌ pre-submit | ⏳ visual check after submit |
| Chen Kui 10-second comprehension | — | ⏳ after Workbench open |

**Automated E2E case (post-submit reference):** All workbench checks PASS in smoke JSON (`p19m1a_devtools_e2e_smoke_20260712_0514.json`).

---

## 6. Founder GUI Checklist (Phase 5)

Prerequisites: API on 8001 (`bash scripts/run_demo_local.sh`), open `miniapp/` in WeChat DevTools, compile.

| # | Step | PASS means (visual only) |
|---|------|---------------------------|
| 1 | **Task Home** | Title「我的事故资料」; status「资料收集中」;「还需补充」lists story/basics/photos; case feels like one task (no error page) |
| 2 | **Story** | Tap story row → enter ≥10 chars (e.g. Irvine 追尾) →「保存并返回」→ toast「已保存」→ back to Task Home with story in「已收到」 |
| 3 | **Basics** | Enter time, location, injury chip, vehicle → save → back; injury/location rows move toward received |
| 4 | **Photos** | Upload **two** test images via native picker →「上传成功」×2 →「完成，返回」 |
| 5 | **Review** | Story + basics summary visible; 2 photos counted;「提交给陈总审核」enabled |
| 6 | **Submit** | Tap submit **once** → lands on Receipt (no double-submit toast) |
| 7 | **Receipt** | Success copy; status shows submitted;「返回我的资料」works |
| 8 | **Resume** | Close/reopen mini program → same case; submitted state persists (not a new empty case) |
| 9 | **Workbench** | Browser Workbench shows same case: story, basics, 2 photos, timeline submit event, brief summary |

---

## 7. Phase 1 Closeout Decision (Phase 6)

**Verdict: CONDITIONAL GO**

| Area | BACKEND VERIFIED | FOUNDER GUI VERIFIED |
|------|------------------|----------------------|
| Launch / Task Home | ✅ | ✅ |
| Story | ✅ | ✅ |
| Basics | ✅ partial (vehicle empty) | ✅ partial |
| Photos (2) | ✅ | ✅ |
| Review | ✅ (`current_step=review`) | ⏳ |
| Submit once | ⏳ (not submitted) | ⏳ |
| Receipt | ⏳ | ⏳ |
| Resume same case | ⏳ (needs post-submit) | ⏳ |
| Workbench readback | ⏳ (pre-submit) | ⏳ |
| No blocking app errors | ✅ | ✅ through photos |
| Focused tests | ✅ 181/181 | — |

**Not NO-GO:** No state corruption, wrong case, or API contract failure observed.

**Architecture:** No blocker. **GCP Cloud SQL is SSOT; legacy Neon deleted.**

**Remaining Founder GUI path:** **Review → Submit → Receipt → Resume → Workbench visual check** (same case `case_a1cf5dfea5c6` or fresh mint).

---

## 8. Prototype Scorecard (Phase 7)

| Area | Score (0–5) | Notes |
|------|-------------|-------|
| Customer task clarity | 4 | Clear supplement list + CTAs |
| Task Home usability | 4 | Founder reached Task Home |
| Story/Basics entry | 4 | Native forms; GUI unverified end-to-end |
| Photo collection | 4 | Slot model + upload API proven |
| Review/Submit confidence | 4 | Photo gate + idempotent submit |
| Resume reliability | 3 | Storage + API ready; GUI resume TBD |
| Backend/API reliability | 5 | 181 tests + in-process E2E |
| Cloud SQL consistency | 5 | SSOT; Neon deleted |
| Broker Workbench usefulness | 4 | Enrichment works post-submit |
| Demo readiness | 4 | Needs Founder 9-step GUI |
| Production readiness | 1 | Prototype scope only |
| WeChat publication readiness | 1 | Gate 1 not started |

**Largest remaining gap:** Founder GUI sign-off on **Review → Submit → Receipt → Resume → Workbench** (backend data through photos already on Cloud SQL).

### Recommended next sequence

1. Finish Founder GUI E2E (9 steps above)  
2. Close Phase 1 Prototype (flip to GO)  
3. Gate 1 — official WeChat feasibility recon  
4. Real AppID + company 主体 verification  
5. Service-category + compliance verification  
6. Privacy policy, user agreement, data disclosure  
7. HTTPS production domain + request/upload/download domains  
8. Phone preview + real-device testing  
9. WeCom → Mini Program card spike  
10. Small Chen Kui pilot  
11. Measure customer completion time + broker time saved  
12. Production identity / multi-tenant (only after pilot metrics)

| Gate | Required before |
|------|-----------------|
| Founder GUI E2E + Phase 1 sign-off | Internal pilot prep |
| Items 3–8 | WeChat submission |
| Items 9–12 | Real customer production use |

---

## 9. Remaining Blockers

| Blocker | Severity |
|---------|----------|
| Founder GUI: Review → Submit → Receipt → Resume → Workbench visual | Medium — last path only |
| WeChat real-device / publication path unverified | Low (out of Phase 1) |

---

## 10. Commit (Phase 8)

**Message:** `fix: stabilize mini program runtime and entry flow`

**Files committed (runtime only):**

- `miniapp/utils/config.ts`
- `miniapp/utils/request.ts`
- `miniapp/pages/entry/entry.ts`
- `miniapp/services/taskLaunchContext.ts`
- `docs/evidence/p19m_phase1_final_e2e_acceptance_2026_07_11.md`

**Excluded:** `config.local.ts`, tokens, UI polish wxml/wxss, `project.config.json`, unrelated evidence JSON.

**Not pushed** (per mission).

---

*P19M Phase 1 — no architectural blocker; Cloud SQL SSOT; Neon deleted. Awaiting Founder GUI closeout on Review → Submit → Receipt → Resume → Workbench.*
