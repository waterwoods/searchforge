# P19H-3i — Two-Hour Product Readiness Evaluation

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Starting commit (eval begin):** `5ad2125` — docs: record Claim supplement routing deploy evidence  
**HEAD at eval end:** `7ac5362` — feat: add Claim task dashboard and always-return H5 entry  
**Live backend (last deploy evidence):** `fdba4b7` — Claim supplement routing (revision `fiqa-api-00198-5sj`)  
**Evaluator constraint:** Read-only eval; no deploy, no schema migration, no code changes during eval window

---

## 1. Executive summary

The Claim workflow has crossed from “demo-capable” to **pilot-capable on the happy path**, but **production silkiness is still partial**. The core loop — WeCom start → H5 wizard → submit → broker queue → WeCom supplement — is implemented, tested, and partially live. The largest gap between **local code** and **live production** is the P19H-3i H5 task dashboard + always-return H5 links (`7ac5362`), which is committed but **not yet deployed**.

| Surface | Verdict | Notes |
|---------|---------|-------|
| Customer Claim flow (happy path) | **PARTIAL GO** | Live: wizard works; dashboard/recover links weaker until 3i deploy |
| Broker Workbench | **PARTIAL GO** | Chen can skim a case in ~10s; provenance UI thin; demo clutter |
| WeChat identity | **Acceptable for pilot** | `external_userid` stable; nickname when API allows |
| Broker login | **Must add simple perimeter** | Shared API key exists; must be enforced before real customers |
| Mini-program | **Not needed now** | H5 + WeCom links sufficient for pilot |

**Recommendation:** **GO** for next implementation sprint — deploy P19H-3i dashboard bundle, then pilot-readiness polish. **HOLD** on identity system rewrite, mini-program, and Add Car H5.

---

## 2. Current system map

```text
Customer (WeCom)
  │ 我要理赔 / 进度 / 补资料 / text+photo supplement
  ▼
WeCom adapter (intent, claim_basics, reply cards, media_intake)
  │ mint H5 token link
  ▼
H5 Claim Intake (/task/claim/:token)
  │ PATCH steps → known_facts (source: h5_form)
  │ submit → claim_phase intake_ready_for_broker
  ▼
Broker Workbench (DocumentIntakeInboxPage → BrokerWorkbenchTab)
  │ brief, timeline, attachments, broker_done
  ▼
WeCom End Card (broker_done only — not H5 submit ack)
```

**Channel roles (as designed):**

| Channel | Role |
|---------|------|
| WeCom | Entry, notify, supplement, status commands |
| H5 | Structured source of truth for wizard fields |
| Workbench | Broker review, done, risk visibility |

**Live vs local delta:**

| Capability | Live (`fdba4b7`) | Local (`7ac5362`) |
|------------|------------------|-------------------|
| H5 wizard + submit | ✅ | ✅ |
| Supplement → Claim not Add Car | ✅ | ✅ |
| H5 dashboard panel | ❌ | ✅ |
| Status/supplement ack inline H5 URL | Partial (status card) | ✅ broader command coverage |
| Workbench provenance suffix | ✅ backend | ✅ |

---

## 3. Customer flow reconstruction

| Step | Current behavior | Smooth | Rough | Production risk | Next improvement |
|------|------------------|--------|-------|-----------------|------------------|
| A. Fresh start |「我要理赔」→ Start Card → H5 link → wizard | Clear ceremony; H5 opens in browser | WeChat in-app browser friction; link expiry anxiety | Low | Dashboard CTA on return (3i) |
| B. H5 intake | 6-step wizard: injury → time/location → story → vehicle → evidence → review | Disabled buttons, step progress, PATCH per step | Evidence step optional but unclear; no autosave indicator beyond PATCH | Medium | Dashboard shows received/missing at top (3i) |
| C. After submit | H5 Done screen + WeCom submit confirmation (not broker_done) | Distinct from broker done; disclaimer present | Customer may not realize supplement still OK | Medium | Submitted-state dashboard + supplement CTA (3i) |
| D. Supplements | WeCom text → append + provenance; photo → bound to Claim | Text ack + timeline; routing fix prevents Add Car steal | Photo ack says「进度/链接」not inline URL | Medium | Inline H5 URL in photo ack (small backend patch) |
| E. Broker | Office Review Queue, drawer, brief, timeline, broker_done | 10-second skim possible; injury/photo/missing visible | Demo duplicates; provenance not prominent in UI; source tags subtle | Medium | Workbench polish + demo cleanup (Group B/C) |

---

## 4. Spark Driver / TurboTax UX scorecard

Scale 1–5. Honest assessment against **live production** (`fdba4b7`), with local 3i noted where different.

### Spark Driver criteria

| # | Criterion | Score | One-line rationale |
|---|-----------|-------|-------------------|
| 1 | One current task | 4 | Single active Claim per lane works; multi-open rare edge handled with warning |
| 2 | One obvious next action | 3 | Status card has next step; H5 wizard has CTA but no dashboard on live |
| 3 | Status always visible | 3 |「进度」works; not push-visible without customer pull |
| 4 | Resume later | 3 | H5 token link on status card; expired link recovery via「进度」 |
| 5 | Evidence tied to task | 4 | Photos attach to Claim; unassigned tier for ambiguous cases |
| 6 | Clear completion | 4 | H5 Done + WeCom submit ack distinct from broker_done |
| 7 | Exceptions don't hijack | 4 | Collision confirm rare; supplement routing fix deployed |
| 8 | Customer never manages case complexity | 4 | Append-first; no multi-case picker |

### TurboTax criteria

| # | Criterion | Score | One-line rationale |
|---|-----------|-------|-------------------|
| 1 | Dashboard / progress | 2 live / 4 local | Live: wizard only; local 3i adds dashboard panel |
| 2 | Missing items checklist | 3 | Status card + workbench show missing; H5 review step basic |
| 3 | Save and return later | 4 | PATCH persists; token link recoverable |
| 4 | Guided stepper | 4 | H5 wizard is clear linear stepper |
| 5 | Review before submit | 4 | Review step with summary + disclaimer |
| 6 | Submission receipt | 4 | Done screen + WeCom confirmation |
| 7 | Documents stored and visible | 3 | Workbench attachments; H5/WeCom source distinction thin in UI |
| 8 | Clear disclaimers | 5 | Consistent「不代表正式报案」copy |

**Composite:** ~3.4/5 live · ~3.9/5 with 3i deployed

### Top 5 friction points

1. **No persistent task dashboard on live H5** — customer re-opening link sees wizard step, not「我的事故资料」summary (Group A deploy).
2. **Photo supplement ack lacks inline H5 URL** — customer must remember「进度」command (small WeCom reply patch).
3. **WeCom is pull-based for status** — no proactive push when broker views or missing items change (defer; acceptable for pilot).
4. **Workbench provenance not visually scannable** —「客户文字补充」suffix exists in brief but not in drawer hero (Group B).
5. **Identity display inconsistency** — nickname when profile API works; otherwise「微信客户 · {suffix}」(Group D later).

---

## 5. H5 Dashboard / always-return entry

### Inspection summary

| # | Question | Answer |
|---|----------|--------|
| 1 | Task dashboard or wizard only? | **Local:** dashboard + wizard. **Live:** wizard only |
| 2 | Status immediately visible? | Local yes (dashboard panel); live only after scrolling or on done step |
| 3 | Already received visible? | Local yes (`dashboard.received`); live partial via review/done |
| 4 | Missing visible? | Local yes; live via status card in WeCom, not H5 |
| 5 | Next best action? | Local yes (`next_action`, `primary_cta`); live wizard footer only |
| 6 | Post-submit supplement easy? | Local CTA「继续补充资料」; live WeCom ack works, H5 weaker |
| 7 | WeCom replies include H5 link? | Status card yes (live); supplement ack yes (local); photo ack indirect |
| 8 | 进度/补资料/链接/事故资料/继续填写 same link? | Local yes (`intent.py` + `ingest_claim_status_request`); live status commands yes |
| 9 | Supplement ack includes H5? | Local yes (`build_claim_supplement_received_reply`); live if mint succeeds |
| 10 | Photo ack includes H5? | **No inline URL** — text says reply「进度」or「链接」 |

### Assessment

| Item | Value |
|------|-------|
| **H5 Dashboard readiness** | **PARTIAL** — code complete at `7ac5362`; **MISSING on production** |
| Minimal plan | Deploy backend + frontend 3i bundle; manual WeCom checklist; optional photo ack inline URL |
| Files | `h5_task_intake.py`, `H5ClaimIntakePage.tsx`, `h5ClaimIntake.ts`, `claim_basics.py`, `reply.py`, `intent.py` |
| Tests | `test_p19h3i_claim_task_dashboard_always_return_h5.py`, `test_h5_claim_intake_form.py` |
| Deploy | **Both** frontend and backend |

---

## 6. WeCom text and photo supplement policy

### Text supplements

| # | Question | Status |
|---|----------|--------|
| 1 | After submitted Claim? | ✅ `claim_supplement_appended` |
| 2 | Yields to Claim over Add Car Phase 2? | ✅ Deployed `fdba4b7` |
| 3 | Ack includes H5 link? | ✅ When `is_h5_task_dashboard_available` |
| 4 | Labeled customer supplement? | ✅ `known_fact_provenance`: `wecom_customer_text` / `customer_supplement` |
| 5 | Distinguishable from H5? | ✅ Workbench brief suffix「（客户文字补充）」vs「（客户已确认）」 |
| 6 | Overwrite H5 confirmed facts? | ⚠️ WeCom patch can update same key — provenance tracks source but no hard block |

### Photo supplements

| # | Question | Status |
|---|----------|--------|
| 6 | Accepted after submit? | ✅ Bound to active Claim (tier A) |
| 7 | Shown in Workbench? | ✅ `case_attachments` + evidence summary |
| 8 | Unassigned float risk? | ⚠️ Tier B/C for ambiguous binding; `unassigned_wecom_photos` counted |
| 9 | H5 vs WeCom photo distinction? | Partial — attachment `source` field exists; UI not prominent |
| 10 | Overwrite H5 facts? | N/A for photos; text overwrite risk remains |

### Policy verdict

| Item | Recommendation |
|------|----------------|
| Current state | **Acceptable for pilot** with documented provenance rules |
| Production risk | WeCom text can update H5-filled plate/insurance keys — broker must confirm |
| Minimal fix | (1) Deploy 3i; (2) inline H5 URL in photo ack; (3) optional: block WeCom overwrite of `h5_form` provenance keys |
| Defer | Full provenance UI, auto-merge rules, broker confirm workflow |

---

## 7. WeChat identity / nickname

### Current model

| Field | Storage | Purpose |
|-------|---------|---------|
| `wecom_external_userid` | Case root | **Stable system key** |
| `customer_name` | Case root | Display label (nickname or fallback) |
| `extra.customer_identity` | JSON bag | `wecom_nickname`, profile fetch metadata |
| `customer_phone` | Case root | Display fallback; from text extraction |

### Display logic (`identity.py`, `case_store.bind_case_channel_identity`)

Priority: broker_manual (future) → wecom_remark (future) → wecom_nickname → meaningful customer_name → `微信客户 · {last6 of external_userid}` → `企业微信客户`

### Why waterwoods vs 微信客户 · 194919

- **waterwoods** — WeCom KF customer profile API returned nickname; stored in `customer_identity.wecom_nickname`
- **微信客户 · 194919** — Profile fetch skipped/failed/generic; fallback uses external_userid suffix

### Pilot assessment

| Item | Verdict |
|------|---------|
| True WeChat personal ID | **Not available** — only external_userid + profile fields |
| Stable key | `wecom_external_userid` ✅ |
| Nickname change | Display may drift; case key stable |
| Cross-channel same person | **Gap** — no unionid merge in pilot scope |
| Pilot blocker? | **No** — acceptable with suffix fallback |
| Must fix now | None |
| Later | Broker manual rename, phone-as-secondary-key, unionid if mini-program added |

---

## 8. Broker Workbench production readiness

### Chen 10-second checklist

| # | Question | Answer |
|---|----------|--------|
| 1 | Which cases need attention? | ✅ Queue filters, urgency, lifecycle tags |
| 2 | Which customer? | ✅ Name with fallback suffix |
| 3 | What happened? | ✅ Brief summary + description |
| 4 | When/where? | ✅ key_facts in brief |
| 5 | Injury? | ✅ injury_status in brief |
| 6 | Photos? | ✅ photo_count + attachments panel |
| 7 | Other party plate/insurance? | ✅ With provenance suffix |
| 8 | Missing items? | ✅ missing_info in brief |
| 9 | Recommended next message? | Partial — `next_best_question` in backend, not always surfaced in UI |
| 10 | Mark done? | ✅ `confirmCaseByBroker` → broker_done + End Card |
| 11 | Source of facts? | Partial — backend suffix; UI not highlighted |
| 12 | Supplements after submit? | ✅ Timeline + follow-up messages |
| 13 | Demo duplicates? | ⚠️ Yes — delete_test_case exists but clutter remains |
| 14 | Login/auth? | Optional `UNIFIED_INTAKE_INTAKE_API_KEY` perimeter |
| 15 | No-login for pilot? | **Internal demo only** |
| 16 | Public URL risk? | Case list + PII if key unset |
| 17 | Minimum before real use? | **Shared secret API key** on Cloud Run + Vercel env |

### Scores and recommendation

| Item | Value |
|------|-------|
| Readiness score | **3.5 / 5** |
| Top blockers | (1) API key not enforced on prod, (2) provenance UI, (3) demo queue noise |
| Pilot auth | **B — must add simple password/shared secret before pilot** |
| Future login | Google SSO or office allowlist post-pilot |

---

## 9. Add Car lane risk

| # | Question | Answer |
|---|----------|--------|
| 1 | Stable enough to leave alone? | Yes for Claim-primary pilot |
| 2 | Can steal Claim supplements? | **Fixed** at `fdba4b7` — tests pass |
| 3 | Explicit「我要加车」works? | ✅ Lane switch confirm |
| 4 | H5 or WeCom only? | H5 photos + WeCom Phase 2 text — no Add Car task dashboard |
| 5 | Hide during Claim pilot? | **Recommend soft-hide** — don't advertise; keep explicit path |
| 6 | Next H5 task? | Yes — Group E after Claim pilot stable |
| 7 | Dangerous inputs? | Passive accident words during Add Car → lane switch prompt |
| 8 | Test coverage? | Strong — `test_p19e1_phase2_routing_fix`, `test_p19h3f5`, append-first suite |

| Item | Value |
|------|-------|
| Risk level | **Medium-Low** (post routing fix) |
| Recommendation | **Keep, don't promote** during Claim pilot |
| Future | Group E — Add Car H5 task dashboard |

---

## 10. Four group tasks roadmap

### Recommended order (next 1–2 days)

#### Group Task A — Claim Task Dashboard / Always-return H5 (P19H-3i)

| Field | Value |
|-------|-------|
| Problem | Customer loses task context; live H5 is wizard-only |
| Commercial | #1 silkiness gap; reduces「我填到哪了」support burden |
| Scope | Deploy `7ac5362`; manual WeCom checklist; photo ack inline URL optional |
| Out of scope | Mini-program, new wizard steps |
| Files | `h5_task_intake.py`, `H5ClaimIntakePage.tsx`, `claim_basics.py`, `reply.py` |
| Tests | `test_p19h3i_*`, `test_h5_claim_intake_form.py`, smoke scripts |
| Deploy | Backend + frontend |
| Risk | Low |
| Time | 2–4 hours |
| **GO/HOLD** | **GO — first** |
| Acceptance | Live H5 shows dashboard; 进度/补资料/链接 return same URL; supplement ack has URL; manual checklist pass |

#### Group Task C — Pilot Readiness / Demo Package / QA

| Field | Value |
|-------|-------|
| Problem | Chen pilot needs clean queue, reset script, one-page runbook |
| Commercial | Can't sell messy demo state |
| Scope | Demo case cleanup, `founder_pre_trial_checklist` alignment, manual QA script |
| Out of scope | New features |
| Files | `scripts/cleanup_p16_demo_queue.py`, trial docs, evidence templates |
| Tests | Existing smoke + manual |
| Deploy | Ops only |
| Risk | Low |
| Time | 3–5 hours |
| **GO/HOLD** | **GO — second** |
| Acceptance | Empty/demo-free queue; one-command pre-trial check passes |

#### Group Task B — Broker Workbench Production Polish

| Field | Value |
|-------|-------|
| Problem | Provenance not scannable; next action buried; attachment sources unclear |
| Commercial | Broker trust = product trust |
| Scope | Hero provenance badges, photo source tags, hide demo cases filter default |
| Out of scope | Full CRM, auth system |
| Files | `BrokerWorkbenchTab.tsx`, `WorkbenchSummary.tsx`, `claim_workbench_display.py` |
| Tests | `claimWorkbenchDisplay.test.ts` |
| Deploy | Frontend + maybe backend enrichment |
| Risk | Low-Medium |
| Time | 4–6 hours |
| **GO/HOLD** | **GO — third** |
| Acceptance | Chen identifies H5 vs WeCom facts in <5s; recommended reply visible |

#### Group Task D — Identity + Access Control

| Field | Value |
|-------|-------|
| Problem | Public workbench URL; inconsistent customer labels |
| Commercial | PII exposure risk; broker confusion |
| Scope | Enforce `UNIFIED_INTAKE_INTAKE_API_KEY` on prod; Vercel key; display name polish |
| Out of scope | Full login, unionid, mini-program identity |
| Files | Cloud Run env, `ui/src/api/request.ts`, `identity.py` |
| Tests | `test_case_confirm_route.py` |
| Deploy | Config + frontend |
| Risk | Medium (lockout if misconfigured) |
| Time | 2–3 hours |
| **GO/HOLD** | **GO — fourth** (before first real customer) |

#### Group Task E — Add Car H5 (deferred)

| Field | Value |
|-------|-------|
| **GO/HOLD** | **HOLD** until Claim pilot completes |

---

## 11. Health tests

| Command | Result |
|---------|--------|
| `pytest tests/test_p19h3h_append_first_split_later.py -q` | **PASS** |
| `pytest tests/test_h5_claim_intake_form.py -q` | **PASS** |
| `pytest tests/test_p19h3f4_unified_status_card.py -q` | **PASS** |
| `pytest tests/test_p19e1_phase2_routing_fix.py -q` | **PASS** |
| `pytest tests/test_p19h3i_claim_task_dashboard_always_return_h5.py -q` | **PASS** |
| Combined (69 tests) | **PASS** |
| `cd ui && npm run build` | **PASS** (23s) |

---

## 12. GO/HOLD summary

| Area | Verdict |
|------|---------|
| Next implementation | **GO** — deploy P19H-3i first |
| Customer Claim pilot (live today) | **PARTIAL GO** — usable with hand-holding until 3i deploy |
| Broker Workbench pilot | **PARTIAL GO** — after API key enforced |
| Identity | **GO for pilot** as-is |
| Mini-program | **HOLD** |
| Add Car promotion | **HOLD** — keep lane, don't market |

---

## 13. Exact next prompt recommendation

**Title:** `P19H-3i Deploy — Claim Task Dashboard + Always-return H5 Entry`

**Scope bullets:**

1. Deploy backend `7ac5362` (or current HEAD) to Cloud Run via `deploy_paid_pilot.sh`
2. Deploy frontend with H5 dashboard UI to Vercel/production static host
3. Pre-deploy: run full pytest suite listed in §11 + H5 live smoke
4. Post-deploy: `GET /version` confirms new SHA
5. Manual WeCom checklist: 进度, 补资料, 链接, 事故资料, 继续填写 → same H5 URL
6. Manual: submitted Claim → text supplement → ack has inline URL
7. Manual: H5 page shows dashboard panel (已收到 / 还缺 / 下一步)
8. Optional small patch: photo ack inline H5 URL (not just「进度」)
9. Record deploy evidence markdown
10. Do NOT schema migrate; do NOT change auth; do NOT start mini-program
11. Rollback tag before deploy
12. Human sign-off: Andy or Chen on one real WeCom test account

---

## 14. Human manual checks when back

1. Open live H5 link after「我要理赔」— confirm dashboard vs wizard (expect wizard until deploy)
2. Send「进度」on submitted Claim — confirm H5 link in footer
3. Send photo supplement — note whether inline URL or command-only ack
4. Open Workbench — scan one Claim in 10 seconds; note customer name display
5. Verify `UNIFIED_INTAKE_INTAKE_API_KEY` posture on live (`/readyz` or deployment manifest)
6. Run supplement routing manual checklist if not done since `fdba4b7` deploy

---

*Eval complete. No deploy performed. No schema migration. Tracked working tree clean at doc creation.*
