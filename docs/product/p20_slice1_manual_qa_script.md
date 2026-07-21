# P20 Slice 1 Manual QA Script (≈10–15 min)

**Purpose:** Prove Broker Request More → Customer Continue on Workbench + WeChat DevTools / iPhone Preview.  
**Date:** 2026-07-15  
**Env:** Founder/QA shared pilot (classification **B**) — not a separate non-prod stack

## Deployed identifiers (fill before each run)

| Layer | Value |
|-------|-------|
| Git branch | `sprint/p16-trust-layer` |
| Slice 1 commits | `80f5fe04e` (package) + `d3cd7ecfa` (jsonb cast hotfix) |
| Backend service | Cloud Run `fiqa-api` / `optimal-disk-472305-e2` / `us-west1` |
| Backend revision | `fiqa-api-00205-pjf` (`GIT_SHA=d3cd7ecfa`) |
| Backend URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Feature flag | `P20_SLICE1_REQUEST_MORE` **unset** (case-level only) |
| Workbench alias | `https://ui-smoky-beta.vercel.app` |
| Workbench deployment | `dpl_CNi9ccf1MMFjwzpgDxk1U21c5Ch2` / `https://ui-a06fl4kak-andys-projects-1f411b73.vercel.app` |
| Document Intake | `https://ui-smoky-beta.vercel.app/workbench/document-intake` |
| QA claim | `case_874d750b5d5f` (`微信客户 · _retry`, `workbench_test=true`) |
| DB | Cloud SQL `caseiq-pilot-pg` / database `caseiq` |
| Migration | `002_p20_slice1_request_more.sql` applied |
| Mini Program API | `apiProfile: "qa"` → `https://fiqa-api-g7zatxrycq-uw.a.run.app` |

### Automated smoke already completed (do not re-create unless rolled back)

- Structured Request More panel visible on QA claim
- One VIN Request More accepted (`aggregate_version=1`, event `broker_request_more_created`)
- Idempotent replay returned `replayed`
- Second create rejected while open group exists
- Customer next action: exactly one `provide_fact` (VIN)

If that open request still exists, **start at step B** (customer continue). To re-run A, use product recovery or enable a different test claim — do not SQL-delete companion rows to hide state.

## Preconditions

- [ ] QA API reachable; Mini Program `apiProfile: "qa"`
- [ ] `npm run preview:preflight` PASS from `miniapp/`
- [ ] Slice 1 enabled on QA claim (`slice1_capability_version: 1`)
- [ ] Workbench office access to `case_874d750b5d5f`
- [ ] Valid customer Mini Program task token for the same case
- [ ] WeChat DevTools: **清缓存 → 全部清除 → 重新编译** (Gate 3)

Capture for each step: screenshot of customer UI, Workbench panel, and Timeline/request progress.

---

## DevTools Three Gates (before customer steps)

1. **Gate 1 — AppID / profile:** Experience/Preview AppID matches office package; `apiProfile: "qa"`; no localhost API base.
2. **Gate 2 — Legal domain:** request合法域名 includes `fiqa-api-qa-g7zatxrycq-uw.a.run.app` for Cloud QA / Experience builds (P36 T5). Production host `fiqa-api-g7zatxrycq-uw.a.run.app` remains for Production Mini Program releases only.
3. **Gate 3 — Clear cache full compile:** 清缓存 → 全部清除 → 重新编译; then open task token.

---

## A. Broker opens QA claim and creates structured Request More

| | |
|---|---|
| **Action** | Open Document Intake → **Open** on `微信客户 · _retry` (`case_874d750b5d5f`) → Structured Request More → VIN → **Send request** once |
| **Expected UI** | Panel shows `Slice 1 enabled`; after success: Request open, Progress 0/1, active VIN; Create disabled while open |
| **Expected API** | `POST /api/inbox/cases/case_874d750b5d5f/request-more` → `outcome=accepted` (or `replayed` on retry with same command identity) |
| **Expected timeline** | One `broker_request_more_created` |
| **Aggregate version** | `0 → 1` on first accept |
| **Retry** | Duplicate click with same `command_id`/`idempotency_key` → `replayed`, same `event_ids` |
| **Recovery** | Conflict / open-group rejection → refresh case; do not SQL-edit companion tables |
| **Evidence** | Screenshot: panel Progress 0/1 + VIN active |

Pass / Fail: ____

## B. Customer sees exactly one server-owned next action

| | |
|---|---|
| **Action** | Mini Program Preview → open same-case task |
| **Expected UI** | Task Home: one primary CTA for VIN; no competing primary CTAs |
| **Expected API** | Task projection `customer_next_action.action_type=provide_fact`, `ordering.total=1` |
| **Expected timeline** | No new events from view-only |
| **Aggregate version** | Unchanged |
| **Retry / recovery** | Pull-to-refresh uses server SSOT; local drafts only |
| **Evidence** | Screenshot: single primary VIN CTA |

Pass / Fail: ____

## C. Customer submits requested VIN

| | |
|---|---|
| **Action** | Primary CTA → enter valid 17-char VIN → submit |
| **Expected UI** | Submitting state; then waiting-for-broker copy (single-item complete) |
| **Expected API** | `POST .../request-items/{item_id}/submit` → accepted; page vs upload loading separate |
| **Expected timeline** | `customer_continue_started` → `field_saved` → `customer_request_item_satisfied` → `supplement_submitted` (once each) |
| **Aggregate version** | Advances (e.g. `1 → N`) |
| **Retry** | Same command identity on **重试提交**; no duplicate satisfaction |
| **Recovery** | Stale responses ignored; destroyed page does not `setData` |
| **Evidence** | Workbench Progress 1/1; customer waiting |

Pass / Fail: ____

## D. Next request item activates in order (multi-item — optional if A used single VIN only)

| | |
|---|---|
| **Action** | On a **new/enabled** test claim in `broker_review`, create ordered items: 1 VIN, 2 insurance card, 3 damage photos; complete one-by-one |
| **Expected UI** | Only active item is primary; queued not tappable as primary |
| **Expected API** | One create; per-item submit advances active item |
| **Expected timeline** | One create event; per-item receipt + satisfied; final `supplement_submitted` once |
| **Aggregate version** | Increases per accepted command |
| **Evidence** | Positions 1→2→3 screenshots |

Pass / Fail: ____ / N/A ____

## E. Final submission returns case to broker review

| | |
|---|---|
| **Action** | Complete last item |
| **Expected UI** | Customer waiting / no submit CTA; broker panel review-ready |
| **Expected API** | Projection `workflow_state=broker_review_ready` (or equivalent review action) |
| **Expected timeline** | Final `supplement_submitted`; group completed |
| **Aggregate version** | Final shared version on broker + customer projections |
| **Evidence** | Broker + customer projections same version |

Pass / Fail: ____

## F. Broker and customer projections + timeline remain consistent

| | |
|---|---|
| **Action** | Refresh Workbench drawer + Mini Program task |
| **Expected UI** | Same progress, same active/completed items, same next actions |
| **Expected API** | GET case / task projection parity |
| **Expected timeline** | Append-only; no rewritten history |
| **Evidence** | Side-by-side notes or screenshots |

Pass / Fail: ____

## G. Safe refresh / resume / duplicate protection

| | |
|---|---|
| **Action** | Mid-flow: background app, reopen; double-tap submit once |
| **Expected UI** | Server next action wins; draft restore only if matching item |
| **Expected API** | Idempotent replay; no second open group |
| **Expected timeline** | No duplicate event set for same command identity |
| **Evidence** | Network panel or outcome `replayed` |

Pass / Fail: ____

---

## Rollback steps

| Layer | Action |
|-------|--------|
| Claim capability | See `/tmp/p20_slice1_deploy/qa_claim_rollback.sql` (restore `claim_phase=intake_ready_for_broker`, remove `slice1_capability_version`) |
| Open Request More | Do **not** DROP companion rows after accepted commands; use product completion/cancel path or leave for audit |
| Backend | `gcloud run services update-traffic fiqa-api --to-revisions fiqa-api-00203-mfm=100 --region us-west1 --project optimal-disk-472305-e2` |
| UI | `cd ui && vercel rollback` (prior production deployment) |
| Feature flag | Keep `P20_SLICE1_REQUEST_MORE` unset |
| DB migration | Do not DROP tables if outcomes exist; PITR/backups retained 7 days on `caseiq-pilot-pg` |

---

## Slice 1 Capability Done (definition — do **not** mark yet)

All must be true:

1. DevTools clear-cache full compile PASS  
2. Preview/experience build PASS  
3. iPhone A–G manual acceptance PASS  
4. No unresolved P0/P1 defect  
5. Rollback evidence retained  

**Slice 1 Capability Done: NO** until the user reports the five items above.

---

## Sign-off

| Check | Result |
|---|---|
| No duplicate request groups / items from double-submit | |
| Legacy (non-Slice-1) claim still uses old Task Home | |
| No white screen / endless spinner | |
| Preview AppID + QA domain correct | |
| Recoverable projection error UI (if forced) | |

Tester: ________  Date: ________  Device: DevTools / iPhone ________
