# PROJECT_TRUTH_SWITCH

## 0. CHAT STARTER SWITCH
1. Product truth: Auto insurance customer unified intake + case organization + office handoff tool.
2. Not the product: full autonomous insurance AI, full CRM, full agency OS, carrier-side execution platform.
3. Strongest current flow: Add-Car / add vehicle quote intake.
4. Strategy: narrow and stable > broad and vague; chat is input surface, not product core.
5. Value center: case clarity, structured intake, missing-info guidance, office handoff.
6. Human-in-loop: office confirmation remains required before final external action.
7. Core path: `ui/src/pages/UnifiedIntakePage.tsx` -> `POST /api/inbox/triage` -> `services/fiqa_api/routes/inbox_triage.py` -> `services/fiqa_api/inbox_triage/triage.py`.
8. Persistence truth: lightweight JSON pilot persistence in `case_store.py` + `session_store.py`, default under `data/`. Optional Postgres dual-write for Stage 1 service records when `SERVICE_RECORD_DATABASE_URL` or `DATABASE_URL` is set and `UNIFIED_INTAKE_PG_DUAL_WRITE` is truthy; schema at `services/fiqa_api/db/schema/stage1_service_record.sql` (JSON remains authoritative until reads cut over). **Add-Car lane:** `POST /api/inbox/triage` with `persist_case` creates an office-visible case only when `formal_submit` is true (or broker/workbench sends `formal_submit: true` on direct paste); see `docs/sprints/PERSIST_FORMAL_SUBMIT_ALIGNMENT_SPRINT/`. **Observability:** persisted cases expose `formal_submitted_at` (immutable first office-visible write) vs `updated_at` (last activity); see `docs/sprints/SUBMITTED_AT_ACTIVITY_EVENT_ROLE_C_LIVE_BATTERY_SPRINT/`.
9. Client-pack truth: runtime `CLIENT_ID` selects `configs/clients/<client_id>/...`; shared industry pack in `configs/industries/insurance/...`.
10. Safe-first edits: client/industry config JSON and localized UI changes; avoid core engine edits unless justified.
11. High-risk files: `triage.py`, `case_store.py`, `config_loader.py`, `app_main.py`.
12. Validation gate: `bash scripts/guardrail_inbox_triage.sh` before claiming acceptance.
13. Health contract: liveness `/health/live`, readiness `/readyz`, alias `/api/healthz`; Cloud Run may mislead on `/healthz`.
14. Runtime/deploy truth: likely Vercel frontend + Cloud Run backend; local demo/dev uses repo scripts and/or Docker Compose.
15. Current priority: reduce engineering confusion, improve portal/result clarity, and prepare pilot-safe operations.

## 1. CURRENT PRODUCT POSITIONING
- Product is currently positioned as an auto insurance unified intake + case organization + office handoff workflow.
- Product is not currently positioned as a fully autonomous insurance AI, complete CRM, complete agency OS, or carrier execution platform.
- Strongest current commercial and operational line is Add-Car intake and quote preparation.
- Current commercial framing is practical operator value: clearer intake, clearer case state, faster office handoff, safer follow-up.

## 2. IN-SCOPE / OUT-OF-SCOPE
- In scope now:
  - Unified Intake flow quality and stability.
  - Case clarity, structured data capture, handoff readiness.
  - Client-pack and industry-pack configuration portability and isolation.
  - Guardrail-driven regression and pilot-safe operations.
- Out of scope now:
  - Expanding into full CRM/agency OS scope.
  - Autonomous end-to-end execution without office confirmation.
  - Broad platform expansion unrelated to insurance intake value.
  - Stripe-first billing platform buildout.

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

## 7. CURRENT TOP PRIORITIES
- **Add-Car efficiency loop optimization** (faster start, faster/clearer collection, faster/safer office takeover) as the active near-term north star — bounded loop hardening, not feature sprawl.
- Reduce engineering confusion by enforcing one operational truth map for runtime, health, and deploy paths.
- Improve portal/result clarity and handoff readability in the Unified Intake user journey.
- Keep pilot-safe reliability high through guardrail-first regression and acceptance discipline.
- Preserve strict client-pack isolation and avoid copy/behavior bleed across clients.
- Prevent scope drift: prioritize narrow intake workflow quality over broad platform expansion.

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
