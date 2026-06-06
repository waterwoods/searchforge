# Failure Pattern Library

**Version:** V1 (P16-S)  
**Date:** 2026-06-01  
**Status:** Operational — mandatory reference for post-sprint health checks  
**Rule:** Every new failure must map to an existing FP or spawn FP-021+ with owner and detection method.

**Sources:** P16-A through P16-R failure discovery (`P16S_FAILURE_DISCOVERY.md`)

---

## How to use

1. **Before sprint close:** Scan symptoms against this library.
2. **During incident:** Match symptom → FP → run Detection → apply Fix → add Prevention to sprint checklist.
3. **After sprint:** Update Frequency and Examples if pattern recurred.

**Severity scale:** P0 = trial-killing · P1 = trust break / usage stop · P2 = polish · P3 = defer

---

## FP-001 — Deployment Parity Failure

**Name:** Local/Preview/Production Divergence

**Symptoms**
- Local score 75+; Preview or Production score 50–65
- Guardrail PASS locally; broker sees wrong UI remotely
- Sprint verdict says "shippable" but URL test fails
- Bundle hash on Production ≠ Preview ≠ git HEAD

**Root Cause**
- No mandatory three-environment parity check before sprint close
- CLI-only deploy model without Git-linked Vercel
- Production promotion deferred as "later" across multiple sprints

**Detection**
- Compare bundle hashes: `curl -s URL | grep -o 'index-[A-Za-z0-9]*\.js'`
- Run `P16R_DEPLOYMENT_PARITY_AUDIT.md` checklist
- Score Local vs Preview vs Production in reality test matrix

**Fix**
- Commit → push → `vercel deploy` with explicit `-b` flags → CORS patch → verify cold URL
- Promote to Production only after Preview gates pass

**Prevention**
- Mandatory POST_SPRINT_HEALTH_CHECK § Deploy before any GO verdict
- Block sprint close if parity delta > 10 points

**Related Sprints:** P16-C, P16-Q, P16-R

**Frequency:** Critical/recurring (10+ sprints)

**Severity:** P0

**Owner:** Founder + deploy engineer

**Examples**
- P16-O local 78 → deployed 64 until P16-R (`P16Q_REALITY_SCORECARD.md`)
- Production frozen 41 days on `index-ctrXdUgj.js` (`P16R_DEPLOYMENT_PARITY_AUDIT.md`)

---

## FP-002 — CORS Origin Block

**Name:** Cloud Run ALLOWED_ORIGINS Missing Preview Origin

**Symptoms**
- Browser Network Error on `GET /api/inbox/cases`
- OPTIONS returns 400 `Disallowed CORS origin`
- API healthy via `curl`; UI broken in browser
- Demo queue shows `0/12` with Network Error

**Root Cause**
- Vercel Preview URL changes on every deploy (hash subdomain)
- `ALLOWED_ORIGINS` on Cloud Run not updated automatically
- `.env.cloudrun` can revert on full backend deploy

**Detection**
- `curl -I -X OPTIONS -H "Origin: PREVIEW_URL" API/api/inbox/cases`
- Browser DevTools → failed preflight
- `validate_pilot_deploy_env.py` (backend posture, not origin list)

**Fix**
- Add new Preview origin to Cloud Run env + `.env.cloudrun`
- Redeploy backend if needed; verify OPTIONS 200

**Prevention**
- Wildcard subdomain pattern or post-deploy CORS hook
- C5 checklist in `P16R_PREVIEW_FIX_PLAN.md` after every Preview deploy

**Related Sprints:** P16-C, P16-F, P16-F.5, P16-G, P16-R

**Frequency:** High (6+ occurrences)

**Severity:** P0

**Owner:** Backend deploy engineer

**Examples**
- Weeks of misdiagnosis P16-F through P16-G; ~78 E2E points fake-failing (`P16G_FINAL_VERDICT.md`)
- `ui-iwnyo9ufa` patched P16-R (`P16R_ENVIRONMENT_AUDIT.md`)

---

## FP-003 — Feature Flag Drift

**Name:** VITE Build Flags Not Persisted in Vercel Dashboard

**Symptoms**
- Redeploy shows full dev UI (Simulation tab, 我的办理, wrong default)
- `product_only` works locally but not on Vercel
- Sprint A improvements invisible on remote URLs
- CLI `-b` flags required every manual deploy

**Root Cause**
- `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` and `VITE_API_BASE_URL` are build-time only
- Not saved in Vercel project environment settings
- Engineers forget `-b` on redeploy

**Detection**
- Inspect deployed bundle for Simulation strings or Add-Car default tab
- Compare Vercel dashboard env vs `.env.production` / deploy script args
- `validate_pilot_deploy_env.py` for backend; frontend needs bundle grep

**Fix**
- Add vars to Vercel dashboard (Preview + Production scopes)
- Redeploy with correct flags; verify bundle

**Prevention**
- Link Git repo to Vercel OR document flags in deploy script as single entry point
- POST_SPRINT_HEALTH_CHECK § Environment — feature flags row

**Related Sprints:** P16-C, P16-E, P16-F.5, P16-J, P16-R

**Frequency:** Critical/recurring (8+ sprints)

**Severity:** P0

**Owner:** Frontend deploy engineer

**Examples**
- Entire Sprint A benefit invisible without manual flags (`P16C_PREVIEW_DEPLOYMENT_TRUTH.md`)
- Production var added P16-R but not redeployed (`P16R_ENVIRONMENT_AUDIT.md`)

---

## FP-004 — Preview Protection (SSO Wall)

**Name:** Vercel Deployment Protection Returns 401

**Symptoms**
- Cold `curl` to Preview URL returns 401 + `_vercel_sso_nonce`
- Broker sees Vercel login, not product
- Chen Kui cold score 12/100
- "Link is broken" — #1 lost moment (P16-Q)

**Root Cause**
- Vercel Deployment Protection enabled on Preview
- Trial URLs documented as shareable but require Vercel account or `vercel curl`

**Detection**
- `curl -sI PREVIEW_URL` → 401
- Unauthenticated browser test (incognito)

**Fix**
- Disable Deployment Protection for Preview OR publish bypass/protection-disabled deployment
- Document authenticated vs cold-access URLs separately

**Prevention**
- POST_SPRINT_HEALTH_CHECK § Deploy — Preview cold access must PASS
- Never document Preview URL as broker-facing until cold curl returns 200 HTML

**Related Sprints:** P16-E, P16-F.5, P16-G, P16-J, P16-Q, P16-R

**Frequency:** Critical/recurring (every verdict P16-J onward)

**Severity:** P0

**Owner:** Founder (Vercel project settings)

**Examples**
- Blocks entire URL-based Day 0 across 8+ sprints (`P16R_FINAL_VERDICT.md`)
- Still ❌ post P16-R Phase 8 (`P16R_PREVIEW_FIX_PLAN.md`)

---

## FP-005 — Not Deployed (Commit Without Deploy)

**Name:** Local Sprint Work Never Reaches Remote URL

**Symptoms**
- Sprint verdict PASS locally; Preview/Production unchanged
- Git commit exists but no `vercel deploy` after merge
- Paper score rises; reality score flat or falls
- "P16-O lied by omission" (P16-Q)

**Root Cause**
- Sprint scope = code only, deploy = separate step
- No deploy gate in sprint definition of done
- P16-O improved customer UX locally; Preview lacked strings until P16-R

**Detection**
- Grep deployed bundle for sprint-specific strings (e.g. `请把您的需求发给我们`)
- Compare git HEAD date vs bundle mtime/hash
- P16-O parity check pattern (`P16R_P16O_PARITY_CHECK.md`)

**Fix**
- Explicit deploy step in sprint close checklist
- Verify bundle on Preview before sprint verdict

**Prevention**
- POST_SPRINT_HEALTH_CHECK § Deploy — all three environments
- Constitution Enforcement: "Would a user notice?" requires deployed URL test

**Related Sprints:** P16-O, P16-Q, P16-R

**Frequency:** High (3+ major instances)

**Severity:** P0

**Owner:** Sprint owner + deploy engineer

**Examples**
- P16-O 78 local → 64 reality (`P16Q_REALITY_SCORECARD.md`)
- Fixed P16-R commit `d05e94d` (`P16R_FINAL_VERDICT.md`)

---

## FP-006 — Runtime Error (Misattributed Network Failure)

**Name:** CORS/API Failure Reads as Product Bug

**Symptoms**
- "Network Error" in UI; broker thinks product broken
- Guardrail PASS; engine healthy
- Demo queue fails; paste may work intermittently
- Console shows CORS blocked, not application error

**Root Cause**
- Infrastructure failure (CORS, SSO, API down) surfaces as generic Network Error
- UI hint exists but not broker-readable
- Local PASS creates false confidence product code is wrong

**Detection**
- Browser DevTools → Network tab → failed preflight
- Distinguish 401 (SSO) vs 400 CORS vs 503 API vs 200 app error

**Fix**
- Fix infrastructure layer first (FP-002, FP-004)
- Improve error copy only after infra confirmed healthy

**Prevention**
- Runtime section of health check: classify error type before UI sprint
- Never start UI bug sprint on remote URL without cold-access PASS

**Related Sprints:** P16-C, P16-F, P16-G

**Frequency:** High during deploy outages

**Severity:** P1

**Owner:** Full-stack engineer

**Examples**
- P16-F weeks diagnosing "product bug" that was CORS (`P16F_CORS_DIAGNOSIS.md`)
- 5-min simulation 58/100 during CORS outage (`P16C_SIMULATION_REPORT.md`)

---

## FP-007 — UI Complexity Creep

**Name:** Feature Accumulation Without Deletion Discipline

**Symptoms**
- 10-second / 5-second test scores below 60
- Dual onboarding (demo vs paste); duplicate trust copy 3×
- Category-before-message on customer landing
- TOP100 deletion lists grow faster than implementation

**Root Cause**
- Sprints add improvements without removing competing elements
- Constitution says "simplicity" but sprint goals add surfaces
- No mandatory deletion quota per sprint

**Detection**
- 10-second test, 5-second test, primary action audit
- Count visible actions above fold on Day 0
- Compare to Stripe/Typeform benchmarks (P16-M, P16-N)

**Fix**
- Execute TOP50/TOP100 deletion lists before new features
- Progressive disclosure: one primary action per screen

**Prevention**
- Constitution Enforcement: "Would Chen Kui care?" + deletion budget
- Contract Simplicity Amendments gate (`CONTRACT_SIMPLICITY_AMENDMENTS.md`)

**Related Sprints:** P16-H, P16-M, P16-N, P16-O

**Frequency:** High (every UI sprint)

**Severity:** P1

**Owner:** Product / UI sprint owner

**Examples**
- Customer 5-second test 33/100 pre-P16-O (`P16N_FIVE_SECOND_TEST.md`)
- Demo card competes with paste (`P16M_FINAL_VERDICT.md`)

---

## FP-008 — Reality Gap (Paper Score ≠ Deployed Score)

**Name:** Local Verdict Overstates External Readiness

**Symptoms**
- Sprint FINAL_VERDICT 74–78; reality validation 64–68
- Founder confidence rises; broker URL still wrong
- "Shippable" in sprint doc; "not trial ready" in Q/R
- Engine score ~85; distribution score ~12

**Root Cause**
- Sprint close criteria = local guardrail + localhost UI
- No mandatory cold-URL reality validation before verdict
- P16-O pattern: optimize locally while deploy drifts

**Detection**
- Run P16-Q style reality scorecard on deployed URLs
- Delta: local score − min(preview, production) > 10 → FAIL

**Fix**
- Re-run verdict after deploy parity fixed
- Separate "code complete" from "trial ready"

**Prevention**
- REALITY_VALIDATION_CHECKLIST mandatory before sprint close
- POST_SPRINT_HEALTH_CHECK § Reality — all roles

**Related Sprints:** P16-Q, P16-O, P16-J, P16-R

**Frequency:** Critical/recurring

**Severity:** P0

**Owner:** Founder

**Examples**
- P16-O 78 → 64 (`P16Q_REALITY_SCORECARD.md`)
- Distribution failure masks engine (`P16Q_FAILURE_ANALYSIS.md` key insight)

---

## FP-009 — Commercial Gap

**Name:** Payment Path Incomplete Despite Product Progress

**Symptoms**
- Invoice templates exist; payment IDs empty
- No 7-day trial log; zero minutes-saved evidence
- No pricing on product surface
- $49 ask would "damage relationship" (P16-Q)

**Root Cause**
- Commercial sprints (P16-K) closed docs but not Andy action items
- Product sprints prioritized UI over payment proof
- Trial blocked by deploy failures → no commercial evidence generated

**Detection**
- P16-K payment readiness audit checklist
- Invoice placeholder grep: `[Andy Zelle`
- Observation log v3 empty rows

**Fix**
- Fill payment IDs (10 min Andy task)
- Run supervised Day 0 → 7 with observation log
- Add pricing line to product footer (doc or UI)

**Prevention**
- POST_SPRINT_HEALTH_CHECK § Commercial — all three rows must PASS for paid sprint
- Constitution Enforcement: "Would a payer notice?"

**Related Sprints:** P16-K, P16-L, P16-Q

**Frequency:** High (5+ sprints)

**Severity:** P1 (P0 at Day 7)

**Owner:** Founder

**Examples**
- Invoice IDs empty across P16-K, L, Q, R (`P16K_PAYMENT_READINESS_AUDIT.md`)
- $49 probability 12% (`P16L_FINAL_VERDICT.md`)

---

## FP-010 — Founder Assumption

**Name:** "Local Works = Ready to Send URL"

**Symptoms**
- Andy screen-share works; Chen Kui cold open fails
- 15-min Preview E2E log never published (3+ sprints)
- Founder over-helping during trial (invalidates evidence)
- Preview URL sent before SSO check

**Root Cause**
- Founder daily driver is localhost; deploy path not in muscle memory
- E2E log treated as optional 15-min task
- Empathy gap: founder session ≠ broker unsupervised session

**Detection**
- Checklist item: Andy cold-open Preview in incognito (no Vercel login)
- Observation log: who clicked? (founder vs broker)

**Fix**
- Andy 15-min authenticated Preview E2E log (`P16R_PREVIEW_FIX_PLAN.md` D1–D2)
- Hand-holding protocol: founder observes, broker clicks

**Prevention**
- REALITY_VALIDATION_CHECKLIST: "Can Andy use it?" on deployed URL, not localhost
- POST_SPRINT_HEALTH_CHECK § Reality — Founder row

**Related Sprints:** P16-C, P16-L, P16-Q, P16-R

**Frequency:** Critical/recurring

**Severity:** P0

**Owner:** Founder

**Examples**
- E2E log open since P16-C (`P16C_FINAL_REVIEW.md` #4)
- Founder Control −4 from local-only validation (`P16F5_FINAL_VERDICT.md`)

---

## FP-011 — Environment Drift

**Name:** Dev Machine / Cloud / Vercel Config Mismatch

**Symptoms**
- Node 20 breaks Vite locally; backend PASS, blank UI
- `127.0.0.1:4173` blocked by CORS
- Embedding 503 on cold start
- Two ports (8001 vs 8000) confusion

**Root Cause**
- No single source of truth for environment requirements
- WSL default Node ≠ repo policy
- Cloud Run env not synced with local `.env.cloudrun`

**Detection**
- `run_demo_local.sh` + `demo_pre_checklist.sh`
- `validate_pilot_deploy_env.py`
- `P16D_DEV_EXPERIENCE_AUDIT.md` pattern

**Fix**
- `with_node22_path.sh` in demo script (P16-D fix)
- Document port standard in RUNTIME_PATH_STANDARD

**Prevention**
- POST_SPRINT_HEALTH_CHECK § Environment
- Pre-demo checklist mandatory

**Related Sprints:** P16-D, P16-C, P16-R

**Frequency:** Medium (local); High (remote env)

**Severity:** P1

**Owner:** Dev experience / infra

**Examples**
- Node 20 blocked every local session pre-P16-D (`P16D_ROOT_CAUSE.md`)
- Preview env not in dashboard (`P16R_ENVIRONMENT_AUDIT.md`)

---

## FP-012 — Capability Regression

**Name:** Sprint Fix Breaks Adjacent Capability Contract

**Symptoms**
- Hiding customer tab breaks customer URL path (Cap 4)
- `product_only` fixes Cap 1 but regresses Cap 4 share link
- Capability score up locally; contract evidence missing on deploy
- Guardrail PASS but capability 6 (trial conversion) unchanged

**Root Cause**
- Single-capability sprint without cross-contract impact review
- P16-I hid 客户报送 → no external customer path on trial URL

**Detection**
- Rescore all 7 capabilities after sprint (`P16I_CAPABILITY_RESCORING.md` pattern)
- Map every change to exactly one contract (`CAPABILITY_MAP_V1.md` rule)

**Fix**
- Document tradeoff in contract amendment
- Add dedicated customer route if tab hidden

**Prevention**
- Constitution Enforcement: "Which capability? Which contract? What score changes?"
- POST_SPRINT_HEALTH_CHECK § Capability — regression detection

**Related Sprints:** P16-I, P16-G, P16-I rescoring

**Frequency:** Medium

**Severity:** P1

**Owner:** Sprint owner

**Examples**
- Customer tab hidden on product_only (`P16R_FINAL_VERDICT.md` #5)
- Cap 1 improved locally; Cap 4 share path blocked

---

## FP-013 — Preview/Production Divergence

**Name:** Production Frozen While Preview Moves

**Symptoms**
- Preview has P16-O strings; Production has 41-day-old bundle
- Production default tab = customer; Preview = broker (with flags)
- `?tab=broker` ignored on Production
- Public URL misleading for trial

**Root Cause**
- Intentional "no prod deploy" mission constraint
- No scheduled Production promotion gate
- Brokers may receive Production link from old docs

**Detection**
- Side-by-side bundle hash + string grep
- `P16R_PRODUCTION_GATE.md` checklist

**Fix**
- `vercel deploy --prod` with product_only + P16-O after Preview gates
- Update all broker-facing links to correct URL

**Prevention**
- POST_SPRINT_HEALTH_CHECK § Deploy — Production row
- Never mark sprint complete if Production > 7 days behind Preview

**Related Sprints:** P16-C through P16-R

**Frequency:** Critical/recurring

**Severity:** P0

**Owner:** Founder

**Examples**
- Production 52/100 vs Preview 68/100 (`P16R_FINAL_VERDICT.md`)
- `index-ctrXdUgj.js` frozen since ~2026-04-21

---

## FP-014 — Broken Trial Flow

**Name:** Day 0–7 Journey Fails at Documented Entry Point

**Symptoms**
- Day 0: cannot load URL (SSO)
- Day 1: wrong tab / empty queue
- Day 3: English drafts on Chinese paste
- Day 7: empty invoice / no proof

**Root Cause**
- Compound of FP-001, FP-004, FP-009, FP-010
- Trial plan written before deploy parity achieved

**Detection**
- P16-L role simulation + P16-Q founder journey
- TRIAL_ONE_PATH dry run on deployed URL

**Fix**
- Fix P0 deploy blockers first (SSO, CORS, prod promote)
- Then UI Day 0 fixes (empty state, demo demotion)

**Prevention**
- POST_SPRINT_HEALTH_CHECK full pass before trial launch
- `trial_launch_check.sh` on Preview URL

**Related Sprints:** P16-L, P16-Q

**Frequency:** High

**Severity:** P0

**Owner:** Founder

**Examples**
- Chen Kui journey stops at link open (`P16Q_FOUNDER_JOURNEY.md`)
- Payment blocked at every gate (`P16Q_FINAL_VERDICT.md` §4)

---

## FP-015 — Missing Evidence

**Name:** No Artifact Proves Sprint Claim

**Symptoms**
- "Trial ready" with zero observation log entries
- "Preview verified" with no Andy E2E log
- Capability score increased with no deployed proof
- Guardrail PASS but no broker screenshot/timestamp

**Root Cause**
- Evidence treated as optional appendix
- Sprint velocity prioritized over proof artifacts

**Detection**
- Evidence grep: observation log, E2E log, screenshot, curl transcript
- Constitution Enforcement: "What evidence exists?"

**Fix**
- Publish 15-min E2E log; fill observation log row 1
- Attach bundle hash + curl output to sprint verdict

**Prevention**
- REALITY_VALIDATION_CHECKLIST — "Can it be demonstrated?"
- No GO without linked evidence file

**Related Sprints:** P16-C, P16-G, P16-L, P16-R

**Frequency:** Critical/recurring

**Severity:** P1

**Owner:** Sprint owner + Founder

**Examples**
- Andy E2E log unchecked since P16-C (`P16R_PREVIEW_FIX_PLAN.md`)
- Zero minutes-saved (`P16K_PAYMENT_READINESS_AUDIT.md`)

---

## FP-016 — Wrong Default Tab / GTM Story Mismatch

**Name:** Customer Portal First on Broker Trial URL

**Symptoms**
- Opens to 客户报送 / Add-Car portal
- Header says 加车报价; trial wedge is cancellation triage
- Unsupervised Day 1 score 28/100
- Chen Kui: "Is this for quotes or messages?"

**Root Cause**
- Legacy Add-Car GTM in UI copy and default route
- Constitution C-P0-1, C-P0-2 conflicts partially fixed Sprint A

**Detection**
- Cold open Production/Preview without login
- Constitution conflict report check

**Fix**
- `product_only` + broker default tab (P16-I)
- Deploy to Production (FP-013)

**Prevention**
- Cap 1 contract acceptance test on deployed URL

**Related Sprints:** P16-A, P16-C, P16-I, P16-Q

**Frequency:** Critical/recurring

**Severity:** P0

**Owner:** Frontend

**Examples**
- #1 trial killer in constitution (`CONSTITUTION_CONFLICT_REPORT.md`)
- Production still wrong default (`P16Q_PREVIEW_VERIFICATION.md`)

---

## FP-017 — Engineer Chrome Visible

**Name:** Internal/Dev Signals on Broker-Facing Surface

**Symptoms**
- PG镜像 tags, API URL display, monospace case IDs
- 场景仿真 tab on Production
- Dark lab header wrapper
- "Beta tool" trust break

**Root Cause**
- `product_only` flag not deployed or incomplete hiding logic
- Dev ergonomics left enabled on pilot URLs

**Detection**
- Stripe benchmark audit (`P16M_STRIPE_BENCHMARK.md`)
- Skeptical broker simulation

**Fix**
- P16-I product_only deploy to all broker URLs
- Remove PG tags from production build

**Prevention**
- TOP50 UI deletions enforced before new chrome added

**Related Sprints:** P16-C, P16-M, P16-I, P16-Q

**Frequency:** High

**Severity:** P2

**Owner:** Frontend

**Examples**
- Role C trust break (`P16Q_ROLE_C_SIMULATION.md`)
- Simulation tab = "test lab" (#3 trust break P16-Q)

---

## FP-018 — Draft Language Mismatch

**Name:** English Output on Chinese Office Input

**Symptoms**
- WeChat paste in Chinese → English `client_reply_draft`
- Broker 大改 every draft; usage stop Day 3–4
- "AI doesn't understand my office"

**Root Cause**
- Prompt/locale not tuned for Chinese office threads
- Rules fallback when OpenAI 429 may worsen language

**Detection**
- Paste Chinese cancellation thread; inspect draft language
- P16-Q assistant simulation

**Fix**
- Prompt engineering for Chinese output
- Restore OpenAI quota or document rules-only limits

**Prevention**
- Guardrail scenario with Chinese input in acceptance suite

**Related Sprints:** P16-H, P16-J, P16-Q

**Frequency:** High

**Severity:** P2

**Owner:** Backend / prompt

**Examples**
- P16-Q failure #8 (`P16Q_FAILURE_ANALYSIS.md`)
- Assistant usage stop (`P16Q_ASSISTANT_SIMULATION.md`)

---

## FP-019 — Git/Vercel Disconnect

**Name:** Push Does Not Trigger Preview Build

**Symptoms**
- Branch pushed; Preview unchanged for weeks
- Sprint A invisible remotely 26 days
- Engineers assume CI deploys; it does not

**Root Cause**
- Vercel project not linked to GitHub repo/branch
- CLI-only deploy workflow undocumented until failure

**Detection**
- Compare last git push time vs Vercel deployment log
- `P16C_PREVIEW_DEPLOYMENT_TRUTH.md` audit pattern

**Fix**
- Link Git OR document CLI deploy as only path
- Run explicit `vercel deploy` after every sprint merge

**Prevention**
- POST_SPRINT_HEALTH_CHECK § Deploy — verify deployment timestamp > last commit

**Related Sprints:** P16-C, P16-R

**Frequency:** Medium

**Severity:** P1

**Owner:** Infra / Founder

**Examples**
- 26-day stale Preview at P16-C (`P16C_PREVIEW_DEPLOYMENT_TRUTH.md`)
- CLI-only model confirmed P16-R (`P16R_EXECUTION_LOG.md`)

---

## FP-020 — Scope Creep During Trial Window

**Name:** Feature Work Invalidates Trial Evidence

**Symptoms**
- UI/prompt changes mid 7-day trial
- P17 temptation during P16-L freeze
- Observation log confounded by deploy change Day 3

**Root Cause**
- No feature freeze enforcement
- Anxiety-driven "one more fix" before broker trial

**Detection**
- Git log during trial dates
- P16-L feature freeze report checklist

**Fix**
- Honor freeze; defer to post-trial sprint
- If deploy required, restart trial clock

**Prevention**
- Constitution Enforcement: "Why are we building it?" during trial
- P16-L freeze as mandatory for any paid pilot week

**Related Sprints:** P16-L, P16-Q

**Frequency:** Medium

**Severity:** P1

**Owner:** Founder

**Examples**
- P16-L feature freeze report (`P16L_FEATURE_FREEZE_REPORT.md`)
- "Do not start P17" (`P16Q_FINAL_VERDICT.md`)

---

## Pattern index

| ID | Name | Severity | Still open P16-R |
|----|------|----------|------------------|
| FP-001 | Deployment Parity | P0 | Partial |
| FP-002 | CORS | P0 | Latent |
| FP-003 | Feature Flag Drift | P0 | Partial |
| FP-004 | Preview Protection | P0 | **Yes** |
| FP-005 | Not Deployed | P0 | Reduced |
| FP-006 | Runtime Error | P1 | Latent |
| FP-007 | UI Complexity Creep | P1 | Partial |
| FP-008 | Reality Gap | P0 | **Yes** |
| FP-009 | Commercial Gap | P1 | **Yes** |
| FP-010 | Founder Assumption | P0 | **Yes** |
| FP-011 | Environment Drift | P1 | Partial |
| FP-012 | Capability Regression | P1 | **Yes** |
| FP-013 | Preview/Production Divergence | P0 | **Yes** |
| FP-014 | Broken Trial Flow | P0 | **Yes** |
| FP-015 | Missing Evidence | P1 | **Yes** |
| FP-016 | Wrong Default Tab | P0 | Production |
| FP-017 | Engineer Chrome | P2 | Production |
| FP-018 | Draft Language | P2 | **Yes** |
| FP-019 | Git/Vercel Disconnect | P1 | Process |
| FP-020 | Scope Creep | P1 | Process |

---

*End of Failure Pattern Library V1 — P16-S*
