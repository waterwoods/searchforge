# P16-S Phase 1 — Failure Discovery

**Date:** 2026-06-01  
**Sprint:** P16-S Failure Pattern Library + Post Sprint Health Check  
**Sources:** P16-A through P16-R, Constitution, Capability Contracts, Sprint Reviews, Reality Validation  
**Method:** Extract every documented failure; group by category; record recurrence and cost

---

## Summary

| Category | Failures | Recurring (3+ sprints) | Still open at P16-R |
|----------|----------|------------------------|---------------------|
| Deploy | 13 | 8 | 6 |
| Environment | 7 | 2 | 1 |
| Runtime | 8 | 4 | 3 |
| UI | 14 | 9 | 5 |
| Reality | 6 | 4 | 4 |
| Commercial | 6 | 5 | 4 |
| Process | 7 | 4 | 3 |
| **Total** | **61** | **36** | **26** |

**Meta-pattern (P16-Q):** Engine failures are not the top failure mode. Guardrail PASS, API PASS, local loop PASS. **Distribution and deploy failures dominate.**

---

## DEPLOY (13 failures)

### F-D01 — Vercel Deployment Protection (Preview 401 SSO)

| Field | Detail |
|-------|--------|
| **Description** | Cold `curl`/browser hits Preview or `ui-waterwoods` alias → **401** + `_vercel_sso_nonce`; product never loads without Vercel login or `vercel curl` bypass. |
| **Impact** | Trial-killing: Chen Kui, Role C, assistants cannot open documented Preview URL unsupervised. Broker cold score **12/100** (P16-Q). |
| **Frequency** | **Critical/recurring** — cited in every verdict from P16-J through P16-R (8+ sprints). |
| **Cost** | Blocks entire URL-based Day 0; forces screen-share only. ~20+ hours across sprints re-diagnosing same blocker. |
| **First occurrence** | P16-E (`P16E_GO_NO_GO.md`, `P16E_PREVIEW_SMOKE_TEST.md`) |
| **Latest occurrence** | P16-R (`P16R_FINAL_VERDICT.md`, `P16R_PREVIEW_FIX_PLAN.md` — SSO still ❌ post Phase 8) |

### F-D02 — Production frozen on pre–Sprint A bundle (~41 days)

| Field | Detail |
|-------|--------|
| **Description** | `ui-smoky-beta` serves `index-ctrXdUgj.js` from ~2026-04-21; no P16-I/O, no `product_only`. |
| **Impact** | Stable public URL shows wrong product: 4 tabs, customer default, Add-Car chrome. Production score **52/100**. |
| **Frequency** | **Critical/recurring** — P16-C through P16-R (10+ docs). |
| **Cost** | ~6 weeks UI drift; every broker who opens Production URL sees wrong product. ~15 hrs re-validation across sprints. |
| **First occurrence** | P16-C (`P16C_PREVIEW_DEPLOYMENT_TRUTH.md`) |
| **Latest occurrence** | P16-R (`P16R_DEPLOYMENT_PARITY_AUDIT.md`, `P16R_FINAL_VERDICT.md`) |

### F-D03 — Cloud Run CORS — Preview origin missing from `ALLOWED_ORIGINS`

| Field | Detail |
|-------|--------|
| **Description** | OPTIONS returns **400** `Disallowed CORS origin`; browser shows Network Error on `GET /api/inbox/cases`. |
| **Impact** | Paste → triage → draft loop fails on Preview despite healthy API. |
| **Frequency** | **High** — P16-C, P16-E, P16-F, P16-F.5 (blocked); fixed P16-G; recurs on new hash URLs. |
| **Cost** | P16-G: **~78 fake E2E points** recovered by one env patch; diagnosed over **weeks** (P16-F through P16-G). ~25 hrs total debug. |
| **First occurrence** | P16-C (`P16C_PREVIEW_DEPLOYMENT_TRUTH.md`, `P16F_CORS_DIAGNOSIS.md`) |
| **Latest occurrence** | P16-R (`P16R_ENVIRONMENT_AUDIT.md` — patched for `ui-iwnyo9ufa`; whack-a-mole remains) |

### F-D04 — CORS hash-URL whack-a-mole on each Preview redeploy

| Field | Detail |
|-------|--------|
| **Description** | Each `vercel deploy` creates new origin; must manually patch Cloud Run + `.env.cloudrun`. |
| **Impact** | Repeat Preview breakage after every deploy. |
| **Frequency** | **Medium** — P16-G exit review, P16-Q #18, P16-R. |
| **Cost** | 2–4 hrs per redeploy cycle (P16-L pre-flight estimate). ~12 hrs across 3+ redeploys. |
| **First occurrence** | P16-G (`P16G_EXIT_REVIEW.md`) |
| **Latest occurrence** | P16-R (`P16R_PREVIEW_FIX_PLAN.md` — C5 checklist) |

### F-D05 — `.env.cloudrun` CORS revert risk on full backend deploy

| Field | Detail |
|-------|--------|
| **Description** | Next `deploy_cloud_run_core.sh` can overwrite `ALLOWED_ORIGINS` if file not synced. |
| **Impact** | CORS fix undone; Preview breaks again. |
| **Frequency** | **Medium** — P16-F.5, P16-G, P16-R. |
| **Cost** | Unknown repeat-debug time; latent risk ~4 hrs if triggered. |
| **First occurrence** | P16-F.5 (`P16F5_FINAL_VERDICT.md` #9 blocker) |
| **Latest occurrence** | P16-R (`P16R_ENVIRONMENT_AUDIT.md`) |

### F-D06 — `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` not persisted in Vercel dashboard

| Field | Detail |
|-------|--------|
| **Description** | Build-time flag only via CLI `-b`; not in Preview env; Production added P16-R but **not redeployed**. |
| **Impact** | Redeploy without flags → full dev UI (Simulation, 我的办理, wrong default). |
| **Frequency** | **Critical/recurring** — P16-C, P16-E, P16-F.5, P16-J, P16-Q, P16-R. |
| **Cost** | Entire Sprint A benefit invisible on Vercel without manual flags. ~10 hrs across sprints. |
| **First occurrence** | P16-C (`P16C_PREVIEW_DEPLOYMENT_TRUTH.md`) |
| **Latest occurrence** | P16-R (`P16R_ENVIRONMENT_AUDIT.md` — Preview FAIL; Production PARTIAL) |

### F-D07 — `VITE_API_BASE_URL` missing on Vercel Preview

| Field | Detail |
|-------|--------|
| **Description** | Production-only in dashboard; Preview builds need CLI injection. |
| **Impact** | Preview builds fail or point wrong without manual deploy args. |
| **Frequency** | **High** — P16-C, P16-R. |
| **Cost** | ~3 hrs discovery + fix attempts. |
| **First occurrence** | P16-C (`P16C_PREVIEW_DEPLOYMENT_TRUTH.md`) |
| **Latest occurrence** | P16-R (`P16R_ENVIRONMENT_AUDIT.md`) |

### F-D08 — No Vercel Preview for Sprint A branch / Git not connected

| Field | Detail |
|-------|--------|
| **Description** | Push to `sprint-a/broker-front-door` did not trigger build; latest Preview **26 days** pre-Sprint A at discovery. |
| **Impact** | Sprint A code invisible remotely despite local PASS. |
| **Frequency** | **High** — P16-C surprise #1; P16-R confirms CLI-only deploy model. |
| **Cost** | ~26 days stale Preview at P16-C discovery; ~8 hrs investigation. |
| **First occurrence** | P16-C (`P16C_PREVIEW_DEPLOYMENT_TRUTH.md`) |
| **Latest occurrence** | P16-R (`P16R_ENVIRONMENT_AUDIT.md`) |

### F-D09 — P16-O customer UX committed locally but not deployed (deploy drift)

| Field | Detail |
|-------|--------|
| **Description** | P16-O improved customer entry locally; Preview lacked `请把您的需求发给我们` until P16-R. |
| **Impact** | Paper score 78 (P16-O) vs reality 64 (P16-Q); **−41** on deployed customer score. |
| **Frequency** | **Medium** — P16-Q central finding; **fixed** P16-R. |
| **Cost** | Full P16-O sprint value unrealized until P16-R commit `d05e94d`. ~16 hrs sprint + re-validation. |
| **First occurrence** | P16-Q (`P16Q_PREVIEW_VERIFICATION.md`, `P16Q_FAILURE_ANALYSIS.md` #3) |
| **Latest occurrence** | P16-R (`P16R_P16O_PARITY_CHECK.md` — bundle PASS; cold access still blocked) |

### F-D10 — Production promotion not executed

| Field | Detail |
|-------|--------|
| **Description** | Explicit mission constraint: no `vercel deploy --prod` despite Preview fixes. |
| **Impact** | No broker-stable long-term URL with correct UI. |
| **Frequency** | **Critical/recurring** — P16-E through P16-R. |
| **Cost** | P16-Q top fix #5: "Week 0 day 2"; P16-L: 2–4 hrs when ready. Deferred ~41 days. |
| **First occurrence** | P16-C (`P16C_GO_NO_GO.md` — Production NO-GO) |
| **Latest occurrence** | P16-R (`P16R_PRODUCTION_GATE.md`, `P16R_FINAL_VERDICT.md`) |

### F-D11 — Uncommitted `ui/` files in Preview deploy artifact

| Field | Detail |
|-------|--------|
| **Description** | P16-E deploy included 5 dirty `ui/` paths vs git SHA. |
| **Impact** | Unknown delta between deployed bundle and committed code. |
| **Cost** | ~2 hrs audit. |
| **First occurrence** | P16-E (`P16E_GO_NO_GO.md`) |
| **Latest occurrence** | P16-F.5 (`P16F5_PREVIEW_ENV_REPORT.md`) |

### F-D12 — Customer tab hidden on `product_only` deploy — no customer URL path

| Field | Detail |
|-------|--------|
| **Description** | P16-I hides 客户报送 in product_only; external customer path blocked on trial URL. |
| **Impact** | Cannot share customer P16-O UX without full-dev or dedicated route. |
| **Frequency** | **Medium** — P16-R gap list, P16-Q verdict #4. |
| **Cost** | ~4 hrs design discussion; unresolved. |
| **First occurrence** | P16-I (`P16I_FOUNDER_REVIEW.md` — intentional hide) |
| **Latest occurrence** | P16-R (`P16R_FINAL_VERDICT.md` #5 remaining gap) |

### F-D13 — Production ignores `?tab=broker` query param

| Field | Detail |
|-------|--------|
| **Description** | Production stays on 客户报送 even with `?tab=broker`. |
| **Impact** | Workaround links fail; broker lands wrong tab. |
| **Cost** | ~1 hr discovery. |
| **First occurrence** | P16-Q (`P16Q_PREVIEW_VERIFICATION.md`, `P16Q_FAILURE_ANALYSIS.md` #18) |
| **Latest occurrence** | P16-Q (Production bundle frozen — not retested post-R) |

---

## ENVIRONMENT (7 failures)

### F-E01 — Node 20 default breaks `run_demo_local.sh` frontend

| Field | Detail |
|-------|--------|
| **Description** | WSL Node 20.18 < Vite 7 requirement (≥20.19 / repo policy ≥22.22); `npm run dev` fails while backend PASS. |
| **Impact** | "Backend healthy, blank UI" — blocks every local validation without manual `source with_node22_path.sh`. |
| **Frequency** | **Medium** — P16-C regression #8, P16-D root cause. **Fixed** P16-D. |
| **Cost** | Blocks **every local session** before fix; ~10 hrs cumulative pre-fix. |
| **First occurrence** | P16-C (`P16C_FINAL_REVIEW.md` #42), P16-D (`P16D_ROOT_CAUSE.md`) |
| **Latest occurrence** | P16-D (`P16D_DEV_EXPERIENCE_AUDIT.md` — ✅ resolved) |

### F-E02 — Localhost preview origin not in `ALLOWED_ORIGINS`

| Field | Detail |
|-------|--------|
| **Description** | `http://127.0.0.1:4173/4174` blocked from Cloud Run API. |
| **Impact** | Local production-build preview cannot E2E demo queue. |
| **Cost** | ~3 hrs. |
| **First occurrence** | P16-C (`P16C_PREVIEW_DEPLOYMENT_TRUTH.md`) |
| **Latest occurrence** | P16-F.5 (`P16F5_PREVIEW_ENV_REPORT.md`) |

### F-E03 — Embedding warming / backend 503 after start

| Field | Detail |
|-------|--------|
| **Description** | Workbench appears broken until `restore_8001_readiness.sh`. |
| **Impact** | False "product broken" on cold start. |
| **Cost** | ~2 hrs per false alarm; ~6 hrs cumulative. |
| **First occurrence** | P16-D (`P16D_DEV_EXPERIENCE_AUDIT.md` friction #6) |
| **Latest occurrence** | P16-D (documented; ongoing latent risk) |

### F-E04 — Two runtime paths (8001 vs 8000) confusion

| Field | Detail |
|-------|--------|
| **Description** | Local demo vs Docker port mismatch documented but still confuses new engineers. |
| **Impact** | Wrong port → failed validation. |
| **Cost** | ~2 hrs per new engineer. |
| **First occurrence** | P16-D (`P16D_DEV_EXPERIENCE_AUDIT.md` #8) |
| **Latest occurrence** | P16-D |

### F-E05 — Clean laptop / first-time setup friction

| Field | Detail |
|-------|--------|
| **Description** | Requires nvm Node 22, `npm install`, optional `.env`; no zero-to-workbench script. |
| **Impact** | New engineer/agent cannot validate without setup doc. |
| **Cost** | ~4 hrs first-time setup. |
| **First occurrence** | P16-D (`P16D_DEV_EXPERIENCE_AUDIT.md`) |
| **Latest occurrence** | P16-D |

### F-E06 — `npm install` not checked in `run_demo_local.sh`

| Field | Detail |
|-------|--------|
| **Description** | Fresh clone fails at UI step if `node_modules` missing. |
| **Impact** | Silent or cryptic Vite failure. |
| **Cost** | ~1 hr per fresh clone. |
| **First occurrence** | P16-D (`P16D_DEV_EXPERIENCE_AUDIT.md` #5) |
| **Latest occurrence** | P16-D |

### F-E07 — No UI port health probe in demo script

| Field | Detail |
|-------|--------|
| **Description** | Script prints "ready" before Vite actually listens. |
| **Impact** | Race-condition false ready signal. |
| **Cost** | ~30 min per false ready. |
| **First occurrence** | P16-D (`P16D_DEV_EXPERIENCE_AUDIT.md` #10) |
| **Latest occurrence** | P16-D |

---

## RUNTIME (8 failures)

### F-R01 — OpenAI 429 quota → rules-only triage fallback

| Field | Detail |
|-------|--------|
| **Description** | Guardrail passes 64/64 on rules; LLM drafts degraded when quota hit. |
| **Impact** | Lower draft quality; trust break on edge cases. |
| **Frequency** | **Medium** — P16-J, P16-Q, guardrail runs across sprints. |
| **Cost** | ~4 hrs investigation; ongoing latent risk. |
| **First occurrence** | P16-J (`P16J_PREVIEW_BASELINE.md`) |
| **Latest occurrence** | P16-Q (`P16Q_FAILURE_ANALYSIS.md`, `P16Q_TOP20_REALITY_FIXES.md` #19) |

### F-R02 — API cold start / ~30s first triage

| Field | Detail |
|-------|--------|
| **Description** | First analysis ~30s without warming; loading copy helps but patience risk. |
| **Impact** | Abandonment at ~2–3 min if broker thinks hung. |
| **Cost** | Risk factor; ~2 hrs analysis. |
| **First occurrence** | P16-C (`P16C_SIMULATION_REPORT.md`) |
| **Latest occurrence** | P16-L (`P16L_TOP20_TRIAL_RISKS.md` #13) |

### F-R03 — Network Error misattributed to product bug (CORS)

| Field | Detail |
|-------|--------|
| **Description** | UI CORS hint exists but reads as "product broken" to brokers. |
| **Impact** | Instant trust break. |
| **Frequency** | **High** during CORS outage (P16-F through pre-P16-G). |
| **Cost** | ~8 hrs misdiagnosis as product bug. |
| **First occurrence** | P16-F (`P16F_BROWSER_REPRO.md`) |
| **Latest occurrence** | P16-C (`P16C_FINAL_REVIEW.md` — perceived regression) |

### F-R04 — Demo queue E2E fails when API/CORS misconfigured

| Field | Detail |
|-------|--------|
| **Description** | `加载演示队列` → Network Error; progress copy shows `0/12` mixed signal. |
| **Impact** | Day 0 value moment lost; 5-min simulation drops to **58** (P16-C). |
| **Frequency** | **High** — P16-C, P16-E, P16-F.5, P16-G (pre-fix). |
| **Cost** | ~12 hrs across CORS outage period. |
| **First occurrence** | P16-C (`P16C_SIMULATION_REPORT.md`, `P16C_FINAL_REVIEW.md` #38) |
| **Latest occurrence** | P16-G (pre-CORS fix) |

### F-R05 — English draft on Chinese WeChat paste

| Field | Detail |
|-------|--------|
| **Description** | Triage returns English drafts for Chinese office threads; broker must 大改 every time. |
| **Impact** | Usage stop Day 3–4; "AI doesn't understand my office." |
| **Frequency** | **High** — P16-H, P16-J #8, P16-L #11, P16-M, P16-Q. |
| **Cost** | ~6 hrs prompt/analysis; unresolved. |
| **First occurrence** | P16-H (`P16H_FINAL_VERDICT.md`) |
| **Latest occurrence** | P16-Q (`P16Q_FAILURE_ANALYSIS.md`, `P16Q_TOP20_REALITY_FIXES.md` #11) |

### F-R06 — Stateless triage POST vs UI persist timing gap

| Field | Detail |
|-------|--------|
| **Description** | API triage works; full case persist/reopen flow not fully proven at API layer. |
| **Impact** | Case/reopen scores capped ~75–85 in P16-G E2E. |
| **Cost** | ~3 hrs E2E gap analysis. |
| **First occurrence** | P16-G (`P16G_E2E_REPORT.md`) |
| **Latest occurrence** | P16-G |

### F-R07 — Trust-breaking wrong urgency on cancellation

| Field | Detail |
|-------|--------|
| **Description** | Wrong triage on real cancellation → one-strike trial kill. |
| **Impact** | Critical payment blocker if occurs. |
| **Cost** | Risk factor (not yet observed in trial). |
| **First occurrence** | P16-L (`P16L_TOP20_TRIAL_RISKS.md` #10) |
| **Latest occurrence** | P16-L |

### F-R08 — Wrong workflow expectation (sync/OCR/auto-send)

| Field | Detail |
|-------|--------|
| **Description** | Broker expects WeChat sync or auto-reply; product is paste-only manual send. |
| **Impact** | Fit mismatch; hard no on payment. |
| **Cost** | ~4 hrs simulation analysis. |
| **First occurrence** | P16-L (`P16L_TOP20_TRIAL_RISKS.md` #8) |
| **Latest occurrence** | P16-Q (`P16Q_ASSISTANT_SIMULATION.md`) |

---

## UI (14 failures)

### F-U01 — Wrong default tab — Customer Entry (客户报送) first

| Field | Detail |
|-------|--------|
| **Description** | Production/full dev opens Add-Car customer portal, not broker workbench. |
| **Impact** | #1 trial killer; unsupervised Day 1 ~28/100 (constitution C-P0-2). |
| **Frequency** | **Critical/recurring** — P16-C, constitution, P16-Q Production snapshot. |
| **Cost** | P16-C: default tab fix alone **+37 pts** orientation ROI; ~8 hrs Sprint A work. |
| **First occurrence** | P16-A (`CONSTITUTION_CONFLICT_REPORT.md` C-P0-2), P16-C |
| **Latest occurrence** | P16-Q (`P16Q_PREVIEW_VERIFICATION.md` — Production browser) |

### F-U02 — 客户报送 tab still visible in product_only

| Field | Detail |
|-------|--------|
| **Description** | Sprint A fixed default tab, not tab removal; wrong-tab exploration persists. |
| **Impact** | Broker wanders to Add-Car portal; trust break. **Fixed** P16-I locally. |
| **Frequency** | **High** — P16-F.5, P16-G revalidations, P16-H #1 action. |
| **Cost** | ~6 hrs P16-I implementation. |
| **First occurrence** | P16-F.5 (`P16F5_PREVIEW_ENV_REPORT.md` #4) |
| **Latest occurrence** | P16-G (`P16G_CHEN_KUI_REVALIDATION.md` — residual until P16-I deploy) |

### F-U03 — Add-Car copy dominates cancellation-first trial

| Field | Detail |
|-------|--------|
| **Description** | Header/tagline/tab suffixes say 加车报价 despite cancellation wedge GTM. |
| **Impact** | Cognitive dissonance; Chen Kui: "Is this for quotes or messages?" |
| **Frequency** | **High** — P16-C #16, P16-H, constitution C-P0-1, P16-F.5 #7. |
| **Cost** | ~10 hrs across UI sprints; partially fixed. |
| **First occurrence** | P16-A (`CONSTITUTION_CONFLICT_REPORT.md`) |
| **Latest occurrence** | P16-H (`P16H_FINAL_VERDICT.md`) |

### F-U04 — Customer landing — category-before-message overload

| Field | Detail |
|-------|--------|
| **Description** | Empty state: 3 buttons, ①②③ instructions, flow track before first keystroke. |
| **Impact** | 5-second test **33/100**; not shippable to end customers (P16-N). **Fixed** P16-O locally. |
| **Frequency** | **Medium** — P16-N, P16-M customer 10s **50/100**. |
| **Cost** | ~16 hrs P16-N + P16-O sprints. |
| **First occurrence** | P16-N (`P16N_FINAL_VERDICT.md`) |
| **Latest occurrence** | P16-N (`P16N_FIVE_SECOND_TEST.md` — eval); deployed gap until P16-R |

### F-U05 — Demo card (快速体验) competes with paste on Day 0

| Field | Detail |
|-------|--------|
| **Description** | Equal-weight demo panel vs 开始整理; Chen Kui Day-0 #1 wrong-first-click. |
| **Impact** | Lost users click demo instead of real paste. |
| **Frequency** | **High** — P16-M, P16-J #7, P16-L #12, P16-Q dual onboarding #7. |
| **Cost** | ~8 hrs analysis across sprints; unresolved. |
| **First occurrence** | P16-M (`P16M_FINAL_VERDICT.md`) |
| **Latest occurrence** | P16-Q (`P16Q_FAILURE_ANALYSIS.md` #7) |

### F-U06 — Empty broker queue on first open

| Field | Detail |
|-------|--------|
| **Description** | 「暂无服务记录」 with no guidance to paste. |
| **Impact** | "Nothing works" — lost users. |
| **Frequency** | **Medium** — P16-Q, P16-C simulation B, P16-M. |
| **Cost** | ~4 hrs P16-O empty state work. |
| **First occurrence** | P16-C (`P16C_SIMULATION_REPORT.md`) |
| **Latest occurrence** | P16-Q (`P16Q_FAILURE_ANALYSIS.md` #6) |

### F-U07 — Dual onboarding — demo queue vs paste

| Field | Detail |
|-------|--------|
| **Description** | Two entry paths without clear hierarchy. |
| **Impact** | Founder/Chen Kui confusion on Day 0. |
| **Cost** | ~3 hrs simulation. |
| **First occurrence** | P16-Q (`P16Q_FAILURE_ANALYSIS.md` #7) |
| **Latest occurrence** | P16-Q |

### F-U08 — Contact-only handoff — two-step submit

| Field | Detail |
|-------|--------|
| **Description** | Phone in chat + separate confirm button. |
| **Impact** | "Submit once or twice?" — lost moment. |
| **Cost** | ~6 hrs P16-O partial fix. |
| **First occurrence** | P16-N (`P16N_FINAL_VERDICT.md` #8) |
| **Latest occurrence** | P16-Q (`P16Q_FAILURE_ANALYSIS.md` #10) |

### F-U09 — Follow-up / append buried below fold

| Field | Detail |
|-------|--------|
| **Description** | 追加客户补充 not prominent; follow-up plan below fold. |
| **Impact** | Usage stop for assistants; one-shot tool only. |
| **Cost** | ~4 hrs analysis. |
| **First occurrence** | P16-Q (`P16Q_ASSISTANT_SIMULATION.md`, `P16Q_FAILURE_ANALYSIS.md` #11) |
| **Latest occurrence** | P16-Q |

### F-U10 — Dark app header vs white product island

| Field | Detail |
|-------|--------|
| **Description** | Dark wrapper around white cards reads internal/engineering. |
| **Impact** | "Unfinished tool" signal; trust break. |
| **Cost** | ~3 hrs UI review. |
| **First occurrence** | P16-J (`P16J_TOP20_REMAINING_ISSUES.md` #6) |
| **Latest occurrence** | P16-Q (`P16Q_FAILURE_ANALYSIS.md` #17) |

### F-U11 — Engineer chrome visible (PG镜像, API URL, monospace IDs)

| Field | Detail |
|-------|--------|
| **Description** | Production workbench shows PG tags, English leaks, monospace case IDs. |
| **Impact** | "Beta/lab" signal; Role C trust break. |
| **Frequency** | **High** — P16-C #2/#12, P16-M Stripe list #20, P16-Q #16. |
| **Cost** | ~6 hrs across UI audits. |
| **First occurrence** | P16-C (`P16C_FINAL_REVIEW.md`) |
| **Latest occurrence** | P16-Q (`P16Q_FAILURE_ANALYSIS.md` #16–17) |

### F-U12 — 场景仿真 tab visible on full dev / Production

| Field | Detail |
|-------|--------|
| **Description** | Simulation tab exposed on non-product_only URLs. |
| **Impact** | "I'm in a test lab" — trust break #3 (P16-Q). |
| **Cost** | ~4 hrs; fixed locally P16-I, not on Production. |
| **First occurrence** | P16-Q, P16-N, constitution C-P0-4 |
| **Latest occurrence** | P16-Q (`P16Q_FAILURE_ANALYSIS.md`) |

### F-U13 — 开始整理 → 已打开 without explanation

| Field | Detail |
|-------|--------|
| **Description** | Button state change confuses first-time users. |
| **Impact** | Feels broken on first click. |
| **Cost** | ~2 hrs. |
| **First occurrence** | P16-J (`P16J_TOP20_REMAINING_ISSUES.md` #13) |
| **Latest occurrence** | P16-M (Day-0 fix item) |

### F-U14 — UI density / duplicate trust copy

| Field | Detail |
|-------|--------|
| **Description** | 「不自动发送」 repeated 3×; nested cards; wayfinding + trust duplication. |
| **Impact** | Amateur signal; 10-second test −7 pts (P16-M). |
| **Cost** | ~8 hrs P16-H/M simplification sprints. |
| **First occurrence** | P16-H, P16-M, P16-J #11 |
| **Latest occurrence** | P16-M (`P16M_FINAL_VERDICT.md`) |

---

## REALITY (6 failures)

### F-RL01 — Local PASS falsely implies Production/Preview updated

| Field | Detail |
|-------|--------|
| **Description** | Guardrail PASS + local product_only success while remote URLs stale. |
| **Impact** | Founder Control **−4** (P16-F.5); false confidence risk. |
| **Frequency** | **Critical/recurring** — P16-C, P16-F.5, P16-Q scorecard thesis. |
| **Cost** | ~30+ hrs building on false premise across sprints. |
| **First occurrence** | P16-C (`P16C_FINAL_REVIEW.md` regression #5) |
| **Latest occurrence** | P16-Q (`P16Q_REALITY_SCORECARD.md` — "P16-O lied by omission") |

### F-RL02 — Paper scores vs deployed reality gap

| Field | Detail |
|-------|--------|
| **Description** | P16-O **78** local vs P16-Q **64** reality (−14); P16-J **74** ignored deploy. |
| **Impact** | Wrong GO decisions; building UI without deploy closes wrong gap. |
| **Frequency** | **High** — P16-Q, P16-R revalidation. |
| **Cost** | ~20 hrs P16-O + P16-Q revalidation. |
| **First occurrence** | P16-Q (`P16Q_REALITY_SCORECARD.md`) |
| **Latest occurrence** | P16-R (`P16R_REVALIDATION.md` — 68 post-R, still not parity) |

### F-RL03 — Distribution failure masks engine quality

| Field | Detail |
|-------|--------|
| **Description** | Engine ~85–90; users never reach it on documented URLs. |
| **Impact** | #1 P16-Q risk: "Andy's side project broke" not "paste needs polish." |
| **Frequency** | **High** — P16-Q verdict, P16-Q failure analysis key insight. |
| **Cost** | Entire trial blocked despite engine readiness. |
| **First occurrence** | P16-Q (`P16Q_FINAL_VERDICT.md`, `P16Q_FAILURE_ANALYSIS.md`) |
| **Latest occurrence** | P16-R |

### F-RL04 — No mobile validation

| Field | Detail |
|-------|--------|
| **Description** | Chen Kui phone usage never browser-tested on trial URLs. |
| **Impact** | Usage stop; paste may not be first on phone. |
| **Cost** | ~2 hrs gap identified; not tested. |
| **First occurrence** | P16-Q (`P16Q_FAILURE_ANALYSIS.md` #15) |
| **Latest occurrence** | P16-Q |

### F-RL05 — Zero paying brokers / no social proof

| Field | Detail |
|-------|--------|
| **Description** | No peer customers, testimonials, or reference brokers. |
| **Impact** | "Am I the guinea pig?" — trust break. |
| **Cost** | Commercial blocker; no hours fixable by code. |
| **First occurrence** | P16-Q (`P16Q_FAILURE_ANALYSIS.md`, `P16Q_SKEPTICAL_BROKER.md`) |
| **Latest occurrence** | P16-Q |

### F-RL06 — No WeChat integration story

| Field | Detail |
|-------|--------|
| **Description** | Paste-only model; no sync with WeChat inbox. |
| **Impact** | Skeptical broker usage stop (accepted v1 scope). |
| **Cost** | ~2 hrs simulation; accepted deferral. |
| **First occurrence** | P16-Q (`P16Q_FAILURE_ANALYSIS.md` #19) |
| **Latest occurrence** | P16-Q |

---

## COMMERCIAL (6 failures)

### F-C01 — No commercial pack ($49/$99, terms, invoice)

| Field | Detail |
|-------|--------|
| **Description** | Before P16-K: no pricing, pilot terms, or invoice on one-pager. |
| **Impact** | Cannot answer "how much?" or Day 7 payment conversation. **Closed** P16-K (docs only). |
| **Frequency** | **High** — P16-F.5 #8, P16-G, P16-J P0 #1. |
| **Cost** | ~12 hrs P16-K sprint. |
| **First occurrence** | P16-F.5, `CONSTITUTION_GAP_ANALYSIS.md` |
| **Latest occurrence** | P16-K (`P16K_FINAL_VERDICT.md` — closed; payment proof still open) |

### F-C02 — Invoice payment IDs empty (Zelle/Venmo/WeChat)

| Field | Detail |
|-------|--------|
| **Description** | Templates exist; `[Andy Zelle/Venmo/WeChat]` placeholders unfilled. |
| **Impact** | Cannot send payable invoice Day 7. |
| **Frequency** | **High** — P16-K, P16-L, P16-Q, P16-R. |
| **Cost** | **10 min** Andy task — repeatedly deferred across 4 sprints. |
| **First occurrence** | P16-K (`P16K_PAYMENT_READINESS_AUDIT.md`) |
| **Latest occurrence** | P16-R (`P16R_FINAL_VERDICT.md`, `P16L_FINAL_VERDICT.md`) |

### F-C03 — Zero 7-day trial with observation log

| Field | Detail |
|-------|--------|
| **Description** | No completed Chen Kui trial; log v2/v3 unused with real cases. |
| **Impact** | Payment proof impossible; $49 probability **12%** today. |
| **Frequency** | **Critical/recurring** — P16-K through P16-R. |
| **Cost** | Entire commercial validation blocked. |
| **First occurrence** | P16-G (`P16G_FINAL_VERDICT.md`) |
| **Latest occurrence** | P16-Q (`P16Q_FINAL_VERDICT.md` — 0 days completed) |

### F-C04 — Zero minutes-saved on real cases

| Field | Detail |
|-------|--------|
| **Description** | No logged "worked" line with timed savings on broker's WeChat threads. |
| **Impact** | $49/$99 ask indefensible. |
| **Frequency** | **High** — P16-K, P16-L, P16-Q payment stopper table. |
| **Cost** | Commercial blocker. |
| **First occurrence** | P16-K (`P16K_PAYMENT_READINESS_AUDIT.md`) |
| **Latest occurrence** | P16-Q (`P16Q_FINAL_VERDICT.md`) |

### F-C05 — No pricing visible on product surface

| Field | Detail |
|-------|--------|
| **Description** | UI lacks "$49/mo pilot" reinforcement. |
| **Impact** | "Why pay?" not answered in-product. |
| **Cost** | ~3 hrs analysis. |
| **First occurrence** | P16-J (`P16J_TOP20_REMAINING_ISSUES.md` #20) |
| **Latest occurrence** | P16-Q (`P16Q_FAILURE_ANALYSIS.md` #13) |

### F-C06 — Payment blocked at every gate simultaneously

| Field | Detail |
|-------|--------|
| **Description** | Cannot open alone + no proof + no log + empty invoice + wrong URL + no peers. |
| **Impact** | "$49 ask today would damage relationship" (P16-Q). |
| **Cost** | Compound commercial failure. |
| **First occurrence** | P16-Q (`P16Q_FINAL_VERDICT.md` §4) |
| **Latest occurrence** | P16-Q |

---

## PROCESS (7 failures)

### F-P01 — No Andy authenticated Preview E2E log

| Field | Detail |
|-------|--------|
| **Description** | 15-min walkthrough (paste ×3, demo, copy, append) never published across **3+ sprints**. |
| **Impact** | Founder cannot certify deploy = local; blocks broker URL send. |
| **Frequency** | **Critical/recurring** — P16-C #4 action → P16-R still open. |
| **Cost** | **15 min** repeatedly cited, never done; ~5 hrs cumulative re-asking. |
| **First occurrence** | P16-C (`P16C_FINAL_REVIEW.md` #4 Andy dry-run) |
| **Latest occurrence** | P16-R (`P16R_FINAL_VERDICT.md`, `P16R_PREVIEW_FIX_PLAN.md` D1–D2 unchecked) |

### F-P02 — Founder over-helping invalidates trial

| Field | Detail |
|-------|--------|
| **Description** | Andy clicks, rewrites drafts, defends triage during Days 1–6. |
| **Impact** | Evidence invalid; payment probability collapse. |
| **Cost** | Risk factor for future trial. |
| **First occurrence** | P16-L (`P16L_TOP20_TRIAL_RISKS.md` #4) |
| **Latest occurrence** | P16-Q (`P16Q_FINAL_VERDICT.md`) |

### F-P03 — Constitution / goal doc conflicts (Add-Car vs cancellation, RAG vs workbench)

| Field | Detail |
|-------|--------|
| **Description** | 6 P0 conflicts: GTM wedge, default tab, RAG demo vs workbench, Simulation required vs hidden, etc. |
| **Impact** | Agents/build wrong thing; broker sees wrong story. |
| **Cost** | ~8 hrs P16-A constitution work; partially addressed. |
| **First occurrence** | P16-A (`CONSTITUTION_CONFLICT_REPORT.md`, `CONSTITUTION_GAP_ANALYSIS.md`) |
| **Latest occurrence** | P16-N (`P16N_FINAL_VERDICT.md` — Constitution copy conflict note) |

### F-P04 — Stale RAG-era goal docs mislead agents

| Field | Detail |
|-------|--------|
| **Description** | `insurance_paid_pilot_goal.md`, `insurance_broker_pilot_rules.md` describe RAG demo not workbench. |
| **Impact** | Wrong validation scripts, wrong product expectations. |
| **Cost** | ~4 hrs agent confusion. |
| **First occurrence** | P16-A (`CONSTITUTION_GAP_ANALYSIS.md`, `CONSTITUTION_CONFLICT_REPORT.md` C-P0-3) |
| **Latest occurrence** | P16-A |

### F-P05 — Constitution not git-frozen / remote not pushed (P16-A)

| Field | Detail |
|-------|--------|
| **Description** | Constitution on disk but no `constitution-v1` tag/push at gate time. |
| **Impact** | No rollback point; high local-only risk. |
| **Cost** | ~2 hrs P16-A gate review. |
| **First occurrence** | P16-A (`P16_GO_NO_GO.md`) |
| **Latest occurrence** | P16-A |

### F-P06 — Feature building during trial (scope creep)

| Field | Detail |
|-------|--------|
| **Description** | Temptation to fix UI/prompts mid-trial confounds evidence. |
| **Impact** | Invalidates 7-day validation. |
| **Cost** | ~4 hrs P16-L feature freeze analysis. |
| **First occurrence** | P16-L (`P16L_FEATURE_FREEZE_REPORT.md`) |
| **Latest occurrence** | P16-Q (`P16Q_FINAL_VERDICT.md` — "do not start P17") |

### F-P07 — Manual deploy discipline / no Git-linked Vercel

| Field | Detail |
|-------|--------|
| **Description** | CLI-only deploys; engineers must remember commit → push → deploy → CORS patch checklist. |
| **Impact** | Repeat deploy drift; P16-O uncommitted gap exemplar. |
| **Frequency** | **High** — P16-C, P16-R execution log. |
| **Cost** | ~10 hrs across deploy cycles. |
| **First occurrence** | P16-C (`P16C_PREVIEW_DEPLOYMENT_TRUTH.md`) |
| **Latest occurrence** | P16-R (`P16R_EXECUTION_LOG.md`) |

---

## Grouping index

| Group | Failure IDs |
|-------|-------------|
| **Deploy parity cluster** | F-D01, F-D02, F-D09, F-D10, F-RL01, F-RL02, F-RL03 |
| **CORS cluster** | F-D03, F-D04, F-D05, F-R03, F-R04 |
| **Feature flag / env drift** | F-D06, F-D07, F-E01, F-E02 |
| **UI complexity creep** | F-U04, F-U05, F-U07, F-U08, F-U14 |
| **Commercial gap** | F-C01–F-C06 |
| **Missing evidence** | F-P01, F-C03, F-C04, F-P02 |
| **Founder assumption** | F-RL01, F-P01, F-P02 |

---

*End of P16-S Phase 1 — Failure Discovery*
