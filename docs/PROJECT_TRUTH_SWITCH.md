# PROJECT_TRUTH_SWITCH

## 0. CHAT STARTER SWITCH
1. Product truth: Add-Car-first intake and handoff assistant for auto-insurance brokers; service record is the primary object. **Conceptual backbone:** Identity (who) → Session (this intake) → Service record (durable case); formal submit promotes session-shaped intake to office-visible record—see §6B and master outline §2A.
2. Not the product: full autonomous insurance AI, full CRM, full agency OS, carrier-side execution platform.
3. Strongest current flow: Add-Car / add vehicle quote intake.
4. Strategy: narrow and stable > broad and vague; chat is input surface, not product core.
5. Value center: front-door intake speed, messy-info cleanup, missing-info guidance, handoff-ready service record.
6. Human-in-loop: office confirmation remains required before final external action.
7. Core path: `ui/src/pages/UnifiedIntakePage.tsx` -> `POST /api/inbox/triage` -> `services/fiqa_api/routes/inbox_triage.py` -> `services/fiqa_api/inbox_triage/triage.py`.
8. Persistence truth: lightweight JSON pilot persistence in `case_store.py` + `session_store.py`, default under `data/`. Optional Postgres dual-write for Stage 1 service records when `SERVICE_RECORD_DATABASE_URL` or `DATABASE_URL` is set and `UNIFIED_INTAKE_PG_DUAL_WRITE` is truthy; schema at `services/fiqa_api/db/schema/stage1_service_record.sql`. **DB-primary reads (opt-in):** when the same DB URL is set and `UNIFIED_INTAKE_DB_PRIMARY_READS` is truthy, API case reads go through `case_truth_repository.py` and prefer Postgres, with JSON fallback by default (`UNIFIED_INTAKE_JSON_READ_FALLBACK`). **Workbench flags:** JSON overlay on top of PG-hydrated reads runs only when both JSON case writes and JSON read fallback are enabled; when either is off (strict DB-only pilot), Postgres `extra.workbench_*` is authoritative. **DB-primary writes (opt-in):** when the DB URL is set and `UNIFIED_INTAKE_DB_PRIMARY_WRITES` is truthy, formal case create/append and related case mutations persist to Postgres first (`persist_new_case` / `persist_case_append`); set `UNIFIED_INTAKE_JSON_CASE_WRITES=0|false` to disable writing `unified_intake_cases.json` in pilot (requires DB-primary writes). Rollback: turn off `UNIFIED_INTAKE_DB_PRIMARY_WRITES` and re-enable JSON case writes (unset or `1`). **Add-Car lane:** `POST /api/inbox/triage` with `persist_case` creates an office-visible case only when `formal_submit` is true (or broker/workbench sends `formal_submit: true` on direct paste); see `docs/sprints/PERSIST_FORMAL_SUBMIT_ALIGNMENT_SPRINT/`. **Lane marker:** formally persisted Add-Car cases set `service_lane` to `add_car` on JSON and mirror it in Postgres `structured_payload` when dual-write runs; JSON↔PG consistency: `scripts/check_add_car_service_record_consistency.py` (also wired into `scripts/guardrail_inbox_triage.sh` as warn-only). **Observability:** persisted cases expose `formal_submitted_at` (immutable first office-visible write) vs `updated_at` (last activity); see `docs/sprints/SUBMITTED_AT_ACTIVITY_EVENT_ROLE_C_LIVE_BATTERY_SPRINT/`. **PG `case_activity`:** when reading from Postgres, `case_activity` is reconstructed from `state_history` (coarse events), not from JSON.
9. Client-pack truth: runtime `CLIENT_ID` selects `configs/clients/<client_id>/...`; shared industry pack in `configs/industries/insurance/...`.
10. Safe-first edits: client/industry config JSON and localized UI changes; avoid core engine edits unless justified.
11. High-risk files: `triage.py`, `case_store.py`, `config_loader.py`, `app_main.py`.
12. Validation gate: `bash scripts/guardrail_inbox_triage.sh` before claiming acceptance.
13. Health contract: liveness `/health/live`, readiness `/readyz`, alias `/api/healthz`; Cloud Run may mislead on `/healthz`.
14. Runtime/deploy truth: likely Vercel frontend + Cloud Run backend; local demo/dev uses repo scripts and/or Docker Compose. **`scripts/deploy_rag_demo.sh`** defaults Cloud Run to **memory 1Gi**, **concurrency 30** (live `fiqa-api` parity); forwards optional `SERVICE_RECORD_DATABASE_URL` and Unified Intake flags from `.env.cloudrun` when set; **`bash scripts/guardrail_cloudrun_runtime.sh`** is the read-only drift check. If DB URL is unset, Cloud Run intake stays JSON-only for cases (PG mirror checks remain local/pilot until wired).
15. Current priority: make Add-Car intake/handoff more trustworthy, faster, clearer, and easier to charge for.

## 1. CURRENT PRODUCT POSITIONING
- Product is currently positioned as an **Add-Car-first** intake + case organization + office handoff workflow for broker teams.
- Product is not currently positioned as a fully autonomous insurance AI, complete CRM, complete agency OS, or carrier execution platform.
- Strongest current commercial and operational line is Add-Car intake and quote preparation.
- Current commercial framing is practical operator value: faster front-door intake, clearer messy input capture, clearer case state, faster office handoff, safer follow-up.
- Human-loop truth remains explicit: customers still work with broker teams for final handling and judgment.

## 2. IN-SCOPE / OUT-OF-SCOPE
- In scope now:
  - Add-Car intake flow quality and stability.
  - Case clarity, structured data capture, handoff readiness.
  - Client-pack and industry-pack configuration portability and isolation.
  - Guardrail-driven regression and pilot-safe operations.
- Out of scope now:
  - Expanding into full CRM/agency OS scope.
  - Autonomous end-to-end execution without office confirmation.
  - Broad platform expansion unrelated to insurance intake value.
  - Stripe-first billing platform buildout.

## 2A. COMMERCIAL DIRECTION LOCK (ADD-CAR FIRST)
- First chargeable wedge: **Add-Car intake and handoff assistant**.
- Current sellable outcome: convert messy customer messages/materials into a **handoff-ready service record** that reduces repeated broker follow-up and moves faster toward quote/processing.
- **Paid-wedge value anchors (explicit top 3):** **(1) 正式提交后可追踪** — after formal submit, durable office-visible record + dependable status/history/continuation (not ambiguous chat). **(2) 办公室一眼摘要** — thread becomes scannable record/state for operators (what / gaps / next) without manual reconstruction. **(3) 防漏项检查** — explicit still-needed / gap surfacing before handoff to cut rework. Master outline: §3.0.
- **Image/photo upload and extraction:** useful **secondary** convenience when shipped; **not** the primary paid story unless a named pilot blocks without it—do not outrank the three anchors in positioning.
- Working evaluation standard for new work: **does this make Add-Car intake/handoff more trustworthy, faster, clearer, and easier to charge for?**
- If a change does not improve this wedge directly (or its proof surface), it is not current-priority work.

## 3. CANONICAL PRODUCT / ENGINEERING PATH
- Frontend entry: `ui/src/pages/UnifiedIntakePage.tsx`.
- Backend intake route: `POST /api/inbox/triage` in `services/fiqa_api/routes/inbox_triage.py`.
- Triage engine: `services/fiqa_api/inbox_triage/triage.py`.
- Case persistence: `services/fiqa_api/inbox_triage/case_store.py`.
- Session persistence: `services/fiqa_api/inbox_triage/session_store.py`.
- Config and client-pack loading: `services/fiqa_api/inbox_triage/config_loader.py`.
- Client and industry config roots: `configs/clients/<client_id>/`, `configs/industries/insurance/`, `configs/common/`.
- Primary validation gate: `bash scripts/guardrail_inbox_triage.sh`.

## 4. EDIT RISK MAP
- Safe-first zones:
  - `configs/clients/<client_id>/*.json`
  - `configs/industries/insurance/*.json`
  - `configs/common/*.json`
  - Localized UI copy/presentation updates in `ui/src/*` with minimal behavioral impact
- Medium-risk zones:
  - `services/fiqa_api/routes/inbox_triage.py`
  - `ui/src/pages/UnifiedIntakePage.tsx` (large surface, mixed responsibilities)
  - Validation orchestration scripts (especially guardrail wrappers)
- High-risk zones:
  - `services/fiqa_api/inbox_triage/triage.py`
  - `services/fiqa_api/inbox_triage/case_store.py`
  - `services/fiqa_api/inbox_triage/config_loader.py`
  - `services/fiqa_api/app_main.py`

## 5. RUNTIME / HEALTH / DEPLOY TRUTH
- Likely local run truth:
  - Demo path commonly uses `bash scripts/run_demo_local.sh` (8001 path in current runbooks).
  - Additional local/dev paths exist (e.g. 8000 Docker-style); treat runtime as mixed and verify before assumptions.
- Health contract truth:
  - Canonical liveness: `/health/live`
  - Canonical readiness: `/readyz`
  - Canonical alias: `/api/healthz`
  - Warning: `/healthz` may be misleading on Cloud Run edge behavior.
- Hosting/deploy truth:
  - Likely frontend target: Vercel.
  - Likely backend target: Cloud Run.
  - Docker Compose remains active for local/service-level workflows.
- Operational warning:
  - Repo contains legacy and multi-service paths; do not assume non-Unified-Intake services are pilot-critical unless explicitly verified.

## 5A. CANONICAL COMMANDS
- Recon-safe precheck: `bash scripts/demo_pre_checklist.sh`
- Canonical local demo run: `bash scripts/run_demo_local.sh`
- Canonical validation gate: `bash scripts/guardrail_inbox_triage.sh`
- After Cloud Run deploy (before broker/customer demo): automated slice `bash scripts/unified_intake_release_gate.sh '<Cloud Run URL>' '<exact frontend origin>'`; full discipline: `docs/runbooks/RELEASE_CHECKLIST.md` (local guardrail → deploy → runtime checks → browser green bar).
- Deploy caution: do not run deploy commands casually (`scripts/deploy_rag_demo.sh`, `scripts/deploy_and_verify_cloud_run.sh`).

## 6. PERSISTENCE / BILLING / SECURITY TRUTH
- Persistence truth:
  - Current intake persistence is lightweight JSON-based and pilot-usable; Postgres schema + opt-in dual-write (`services/fiqa_api/db/`) exist as the Stage 1 foundation, not a full cutover.
- Billing truth:
  - Stripe is not currently integrated for Unified Intake commercial flow.
- Security truth:
  - Partial controls exist (e.g., CORS/config/runtime controls), but no unified intake-user auth model and no formalized strong PII security layer yet.

## 6A. STRUCTURED TRUTH VS REPLY GENERATION (INDUSTRIAL CONTRACT)

- **Structured truth layer** is authoritative for: `collected_fields`, `still_needed_fields`, lifecycle/handoff readiness, **formal submit** vs pre-submit record identity, office-visible persistence, and time semantics (`formal_submitted_at` vs `updated_at`). Add-Car gates and right-rail explanations must be derivable from this layer.
- **Reply generation layer** (`client_reply_draft`, handoff phrase families, stitched reassurance lines) **must not outrank** that truth: wording may explain and reassure **within** what the truth layer already allows; it must not claim office receipt, completeness, verification, quote readiness, or audit detail that structured state does not support.
- **Intent layer (middle contract):** Between truth and reply, the product must resolve **what the current customer turn is doing** (e.g. supplement vs correct vs process question vs “did office get it?”)—using latest text + thread context, **with truth as a hard constraint**—so late turns do not collapse into one generic template family. Truth constrains intent; intent constrains reply; reply still cannot outrun truth. Normative three-layer rules, forbidden collapse modes, and checklist: `docs/sprints/TRUTH_INTENT_REPLY_THREE_LAYER_STANDARD_SPRINT/02_THREE_LAYER_STANDARD_SPEC.md`.
- **Known failure mode to guard:** `handoff_ready` / friendly templates implying “已到办公室” or “资料齐了” while **formal submit** has not happened, required fields remain in `still_needed_fields`, or only customer-claimed materials exist—see `docs/sprints/TRUTH_LAYER_REPLY_LAYER_INDUSTRIAL_STANDARD_SPRINT/02_TWO_LAYER_STANDARD_SPEC.md` for explicit non-overreach rules and a review checklist. **Additional gap:** truth-safe but **intent-wrong** replies (repeated post-submit blocks, weak latest-turn specificity, long-thread generic closure)—see three-layer spec.
- **Contact-gap reminders (name/phone):** Structured truth and office summary stay honest when contact is missing; **customer-facing** replies use **strong** nudges when intake/handoff is the point, **light** one-line nudges when the turn is timeline / quote detail / receipt / materials / supplement, and **suppress repeating the same tail** across consecutive assistant turns so the gap does not drown the latest intent. Normative product framing: master outline **§4.10**.

## 6B. IDENTITY / SESSION / SERVICE RECORD (STAGE 1 TRUTH MAP)

Normative product framing for this backbone: `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` §2A. This file states **what may be treated as true** at each layer for operators and implementers.

### Identity truth (who is speaking)

- **May be treated as identity truth (Stage 1, lightweight):** stable **same-intake linkage** (session/case/thread id), **broker-supplied** reference when present, **collected or pasted** name/phone/email when the product defines them as captured fields—not as verified government ID.
- **Remain careful / bounded:** “same person” across **sessions** without an explicit key or broker merge is **uncertain**; do not imply CRM-grade identity resolution.
- **Explicitly not required now:** login/account platform, SSO, multi-tenant customer master, KYC/verification as a gate—unless a future roadmap item promotes them.
- **Future-facing (optional) identity/binding layer:** roadmap may later introduce an **optional lightweight external handle/binding** (e.g. WeChat, email-link, or equivalent) to stabilize repeat-user identity for specific markets, without changing the current rules for anonymous start, minimal handoff identity, or formal submit.

### Session-only truth (this conversation)

- **Session/thread** is the **process container**: messages, latest-turn intent, in-flight draft structured state **before** formal submit gates are satisfied.
- **Session-only** means: fine for UX and extraction, **not** automatically **office-visible persisted record** or **immutable submit** semantics—until formal submit (or equivalent) under product rules.

### Service-record truth (durable case object)

- **Service record** is the **durable Add-Car case** the portal/workbench and broker rely on: structured fields, lifecycle, record id, **office-visible** persistence when dual-write/submit rules say so.
- **Trust bar:** broker-facing copy and customer replies must align with **structured truth** (§6A); the **chat** is supporting evidence, not the authoritative definition of “what the office has.”

### What formal submit changes

- **Before formal submit:** conversational and draft; readiness and handoff language must not claim **office receipt** or **immutable office record** beyond what structured truth allows.
- **After formal submit:** the **service record** is the promoted, **office-visible** artifact (`formal_submitted_at` and related semantics)—subsequent activity updates **that** record; it is not “unsent chat.”

### How to judge new work

Ask: **Does this strengthen identity clarity, session clarity, or service-record trust for Add-Car—without building a heavyweight CRM or identity platform?** If it does not, it is not current-priority unless it is clearly enabling infrastructure.

### What the product is still not

- Not a **full identity/account platform**, **full CRM**, **customer 360**, **agency workflow engine**, or **enterprise multi-tenant profile system** in Stage 1—see master outline §2A.

## 6C. FRONTEND SIMPLIFICATION + LIGHT IDENTITY + RECORD OPENING TRUTH (STAGE 1)

- **UI discipline is product truth, not styling preference:** default intake/workbench surfaces should stay focused on four operator-critical questions: who this is now (identity confidence), what matter is being handled, what step/status the case is in, and the next required action/owner. Anything outside this scope should be folded or secondary by default.
- **Identity entry remains progressive and lightweight:** Stage 1 allows anonymous start, optional lightweight binding for continuity, and minimum business identity completion at formal submit. This is an intake discipline, not an auth-platform roadmap.
- **WeChat framing (market-specific, optional):** WeChat can be used as a strong optional light-binding candidate for North American Chinese users, but it must remain optional and coexist with non-WeChat paths (e.g. phone/email continuity and broker-assisted capture).
- **Record opening principle:** do not apply one-person-one-record as a hard rule. A person can have multiple service records when matters differ.
- **Append/new-case decision rule (tightened):**
  - append is allowed only when same-matter evidence is jointly strong: identity linkage + same service type/lane + same vehicle unit + close timing + strong content continuity.
  - open new case when there is clear matter separation: different vehicle, different request type, explicit topic pivot, or lifecycle/handling context showing separate office work.
  - when append triage marks `case_boundary=new_issue`, product truth is "do not silently treat as normal append"; next implementation must enforce explicit split policy (recommended default: hard-confirm split/new-case).
- **Formal-submit boundary remains authoritative:** office-visible durable case truth is promoted at formal submit under current Add-Car gates; pre-submit/session signals are process-state and must not be overstated as office-received truth.
- **Dual-state boundary (must not be mixed):**
  - `lifecycle_status` = process/lifecycle truth for intake/handoff progression; primary axis for customer/workbench state semantics.
  - `case_status` = operator workflow label for queue handling.
  - Rule: do not let `case_status` drive handoff/submit semantics; do not use `lifecycle_status` to replace queue labels.
- **Lightweight person-link extension point (documented, not implemented as auth):**
  - optional `person_link_key` (nullable, client-scoped stable link key),
  - optional `person_link_source` (binding handle type),
  - optional `person_link_confidence` (`low`/`medium`/`high`).
  - This is continuity metadata only; not login, not mandatory gate, not CRM identity graph.
- **Runtime alignment:** Add-Car-first wedge remains the Stage 1 contract. **Formal service records** may run **strict Postgres-primary** (Neon/Postgres as durable truth: DB-primary reads/writes on, JSON case file writes off, JSON read fallback off) while **sessions** and **attachment bytes** stay on local JSON/files by default. Optional PG dual-write remains for transitional parity when not in strict write mode.

## 7. CURRENT TOP PRIORITIES
- **Add-Car efficiency loop optimization** (faster start, faster/clearer collection, faster/safer office takeover) as the active near-term north star — bounded loop hardening, not feature sprawl.
- Reduce engineering confusion by enforcing one operational truth map for runtime, health, and deploy paths.
- Improve portal/result clarity and handoff readability in the Unified Intake user journey.
- Keep pilot-safe reliability high through guardrail-first regression and acceptance discipline.
- Preserve strict client-pack isolation and avoid copy/behavior bleed across clients.
- Prevent scope drift: prioritize narrow intake workflow quality over broad platform expansion.
- Keep simulation (Role C / Role C Plus / replay) as demo-and-validation instrumentation for this wedge, not as a standalone product direction.

## 8. UPDATE RULES
- Update this file immediately when any of the following changes:
  - Runtime path defaults, startup scripts, or port conventions.
  - Health/readiness endpoint contract or operational health guidance.
  - Deploy topology truth (Vercel/Cloud Run/Docker assumptions).
  - Env contract for intake-critical behavior (especially `CLIENT_ID`, readiness, persistence paths, and optional `SERVICE_RECORD_DATABASE_URL` / `UNIFIED_INTAKE_PG_DUAL_WRITE`).
  - Persistence architecture for case/session storage.
  - High-risk vs safe-first edit map.
  - Product boundaries (in-scope/out-of-scope) or core positioning.
- If a change contradicts this file, update this file first (or in the same PR) before declaring work complete.
- Update **§6B** when identity/session/service-record boundaries or formal-submit semantics change in a way that affects what operators may trust.
