# PILOT SAAS SURVIVABILITY + OFFICE TRUST HARDENING SPRINT

**SSOT authority:** runtime posture, deployment truth, support/replay handoff semantics, office continuity, rollback notes.  
**Not claimed:** enterprise IAM, RLS, SSO, WORM/compliance, billing.  
**Branch:** `sprint/pilot-saas-survivability-office-trust-hardening`  
**Schema / contract label:** `INTAKE_SCHEMA_EPOCH` in `services/fiqa_api/deployment_profile.py` (surfaced on `/health` and `/api/inbox/support/deployment-manifest`).

---

## PHASE 0 — GIT INVENTORY (snapshot)

| Item | Value |
|------|--------|
| Branch | `sprint/pilot-saas-survivability-office-trust-hardening` |
| Snapshot date | **2026-05-10** |
| Working tree | **Dirty** — tracked edits across intake routes, session/case repos, UI contracts, `configs/demo.env.example`, `trial_readiness_check.sh`, plus **many untracked** docs/scripts under `docs/sprints/`, `results/`, `services/fiqa_api/security/`, etc. **Treat as pre-existing WIP**; this sprint’s **authority** is this SSOT + explicit survivability commits called out in Phase 4. |
| Stashes | Multiple historical stashes (`git stash list`) — do not pop blindly |

Operators must not assume a clean tree without checking `git status`.

---

## 1. CURRENT_RUNTIME_TRUTH

- **Entry:** `services/fiqa_api/app_main.py` — loads dotenv (`.env.cloudrun` then `.env`), builds FastAPI app, CORS from `ALLOWED_ORIGINS` or legacy permissive defaults, mounts inbox + analytics always; lab/search routers conditional on **not** `UNIFIED_INTAKE_PRODUCT_ONLY`.
- **Unified Intake HTTP:** `services/fiqa_api/routes/inbox_triage.py` — triage, cases, sessions, WeChat binding, support export routes.
- **Perimeter:** `IntakeApiPerimeterMiddleware` gates `/api/inbox/*` except `/api/inbox/support/*` and WeChat callback when `UNIFIED_INTAKE_INTAKE_API_KEY` is set (`security/intake_api_gate.py`).
- **Support export gate:** `UNIFIED_INTAKE_SUPPORT_API_KEY` optional; when set, support routes require header or Bearer (`security/support_export_gate.py`).
- **Tenant header:** `X-Org-Id` captured as **client assertion** only (`security/request_identity.py`); no server-issued tenant authority.
- **Persistence:** Cases/sessions may be JSON files, Postgres, or mixed per `service_record_settings.py` flags; production-like mode disables JSON case reads as fallback when rules apply.
- **Health:** `GET /health` returns phase, `unified_intake_case_persistence` report, `deployment_profile` (product-only flag, schema epoch, auth posture, intake perimeter, **office ownership posture**, tenant truth, operator hints including **deployment_identity** labels).
- **Readiness:** `/health/ready`, `/ready` tie to artifacts + route probes + embed/Qdrant where applicable.
- **Analytics:** best-effort events (`minimal_events`, funnel helpers); not a billing or audit system.

---

## 2. CURRENT_DEPLOYMENT_TRUTH

- **Primary deploy narrative:** Cloud Run + optional Secret Manager + Vercel frontend; `configs/demo.env.example` documents anti-drift: full deploy replaces env bundle — manual `gcloud` patches lost if not mirrored in committed env template.
- **Ports:** Local demo scripts target **8001** per `AGENTS.md`; Docker sample may use 8000 — operators must verify which process answers `/health`.
- **Product-only:** `UNIFIED_INTAKE_PRODUCT_ONLY=1` shrinks mounted routers; inline platform routes documented as not registered in that profile (`deployment_profile.py`).
- **CORS:** Wrong `ALLOWED_ORIGINS` → browser “network error” with no obvious API 500 — deployment truth lives in Cloud Run env + Vercel build-time `VITE_API_BASE_URL`.
- **Node/Vite:** UI `package.json` requires **Node ≥20.19 or ≥22.12** (Vite 7). Default PATH Node **20.18.x fails** build — use e.g. `PATH=$HOME/.nvm/versions/node/v22.22.0/bin:$PATH` before `npm run build`.
- **Operator hints:** `operator_runtime_hints()` exposes raw `ENV`/`DEMO_MODE` labels, in-memory session test flag, **`operator_warnings`** codes for contradictory posture, and **`deployment_identity`** — best-effort `K_SERVICE` / `K_REVISION` / `K_CONFIGURATION` (Cloud Run) plus optional `GIT_SHA`/`COMMIT_SHA`/`SOURCE_VERSION`/`VERCEL_GIT_COMMIT_SHA` (**not tamper-evident provenance**; semantics string on payload).
- **`GET /health` office block:** `deployment_profile.office_ownership` duplicates `office_ownership_posture_dict()` so operators need not hit support routes for enforcement semantics.

---

## 3. CURRENT_SUPPORT_TRUTH

- **Manifest:** `GET /api/inbox/support/deployment-manifest` — git SHA, `case_persistence` snapshot, auth/intake perimeter posture, `replay_lineage`, `tenant_truth`, `operator_runtime_hints`, `office_ownership` (`routes/inbox_triage.py`).
- **Case head:** `GET /api/inbox/support/case-head/{case_id}` — minimal metadata for replay tickets; still **not** legal hold.
- **Secrets:** Support key is shared secret, not per-office IAM; leakage = full manifest access until rotation.
- **Anonymous surface:** With no support key, manifest is world-readable on any host that can reach the API — `production_support_export_risk` flags prod-like env without key (`support_export_gate.py`).
- **Smoke:** `scripts/support_deployment_manifest_smoke.py` checks `/health` and manifest; requires running server unless skipped; asserts `operator_warnings` is a **list**.

---

## 4. CURRENT_REPLAY_TRUTH

- **`_support_replay_lineage_dict`:** `support_export_manifest_version`, `intake_schema_epoch`, wire contract label, explicit semantics string **`support_replay_handoff_metadata_v1_not_legal_hold`**, office ownership posture.
- **`audit_export.record_intake_case_mutation`:** forwards to `track_event` — explicitly **not** compliance/WORM (`audit_export.py`).
- **Disputes:** Replay truth depends on persisted case + session rows + which store was authoritative (JSON vs PG); dual-write and fallback modes create interpretation risk documented in `case_truth_repository` logging signals (`UNIFIED_INTAKE_DB_OBS`).

---

## 5. CURRENT_OFFICE_CONTINUITY_TRUTH

- **Office hint:** `asserted_org_id` on cases from `X-Org-Id` at creation — not cryptographic (`case_office_access.py`).
- **Enforcement:** `UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP` — mismatched or missing org on stamped cases → 403; unstamped legacy rows remain visible depending on list strictness (`UNIFIED_INTAKE_OFFICE_LIST_STRICT_NO_LEGACY`).
- **Postgres mirror:** `office_owner_org_id` column promoted from JSON extra for indexed office queries (`service_record_repository.py`); hydration prefers column then falls back to `extra.asserted_org_id`.
- **Sessions:** `session_store` persists `asserted_org_id` when provided — continuity across trims/bind paths documented in posture dict.
- **Wrong office:** Browser/workspace sending wrong `X-Org-Id` binding remains a **product/process** failure mode; server only matches strings when enforcement is on.

---

## 6. CURRENT_AUTH_BOUNDARY_TRUTH

- **No authoritative tenant ID:** `tenant_id_authoritative` always `None`; semantics fixed string in `IntakeTenantTruth`.
- **API keys:** Coarse deployment perimeter (intake) and support export gate — not broker RBAC.
- **WeChat OAuth:** Callback exempt from intake API key middleware by design.

---

## 7. CURRENT_FOUNDER_DEPENDENCY_MAP

- Cloud Run + Vercel env parity and CORS lists.
- Secret Manager vs plaintext deploy script discipline.
- Qdrant/OpenAI availability for “full quality” demos.
- Interpretation of PG vs JSON flags during pilot transitions.
- Manual office onboarding (`X-Org-Id` convention, enforcement rollout).
- Incident triage when logs reference `UNIFIED_INTAKE_DB_OBS` signals.

---

## 8. CURRENT_SUPPORT_ESCALATION_MAP

1. `/health` + `deployment_profile` + persistence mode.
2. `/api/inbox/support/deployment-manifest` (+ support key if configured).
3. `support/case-head/{case_id}` for stamped metadata.
4. Git SHA from manifest vs expected release.
5. `operator_warnings` / `production_support_export_risk` / short-key warnings.
6. Application logs with case_id / request_trace_id (PII risk — operational honesty).
7. Founder for DB contents, env mismatch, office binding disputes.

---

## 9. CURRENT_DEPLOYMENT_DRIFT_MAP

| Drift | Symptom | Detection |
|-------|---------|-----------|
| Manual Cloud Run env not in `demo.env.example` | Mystery flags after redeploy | Diff describe vs template |
| `ENV=prod` + `DEMO_MODE` truthy | Confusing metrics / operator narrative | **`operator_warnings`** `env_prod_with_demo_mode_truthy_v1` |
| Prod-like without DB URL | Cases/sessions unusable or wrong store | **`production_like_missing_service_record_database_url_v1`** |
| Office enforcement + prod-like + no DB URL | Office rules imply shared persistent truth but runtime has no Postgres — multi-instance / continuity hazard | **`office_enforcement_on_without_service_record_database_url_multi_instance_unsafe_v1`** |
| In-memory session flag + DB URL | Accidental test posture in shared env | `inmemory_sessions_flag_on_while_db_url_configured_v1` |
| Vercel API URL ≠ Cloud Run URL | Silent frontend failures | `/health/live` compare |
| Missing support key in prod-like | Open reconnaissance on support routes | `production_support_export_risk` |
| Dual-write / JSON fallback confusion | “Case disappeared” / wrong workbench | persistence report + logs |

---

## 10. CURRENT_OFFICE_CONFUSION_MAP

- Legacy cases without `asserted_org_id` visible to all offices when enforcement off or list not strict — **cross-office data bleed** in demo posture.
- Brokers clipboarding `case_id` into wrong office context — enforcement reduces impact only when stamped + enforced.
- Multiple browser tabs / cached `session_id` + changed org header — stale binding narrative.
- “Org” naming vs carrier vs franchise — string equality only.
- Analytics/funnels may not align to office if frontend omits org propagation — verify events per route.

---

## TOP_30_OPERATIONAL_FAILURES

1. Assuming `X-Org-Id` is authentication.  
2. Deploying prod-like runtime without Postgres URL.  
3. Running demo CORS (`*`) on internet-facing pilot.  
4. Losing manual Cloud Run env on full redeploy.  
5. Wrong frontend API base URL baked at Vercel build.  
6. Mixing JSON-authoritative and PG-authoritative reads mid-pilot.  
7. Ignoring `UNIFIED_INTAKE_DB_OBS` log signals.  
8. Cold starts vs min-instances surprise during trial.  
9. Embedding pilot keys in client-side bundles.  
10. Treating support manifest as compliance export.  
11. Rotating OpenAI/Qdrant keys without updating Secret Manager bindings.  
12. Using `/healthz` on Cloud Run where frontend strips path (use `/health/live` or `/api/healthz`).  
13. Product-only vs full platform route confusion during debugging.  
14. Assuming sessions durable without DB URL + correct flags.  
15. Enabling enforcement without stamping legacy data → visibility cliff.  
16. Clipboard leak of support shared secret.  
17. Interpreting `tenant_truth` as IAM decision.  
18. Omitting `X-Org-Id` on enforced list routes → empty or 403 surprises.  
19. Dual-write disabled but expecting PG mirror completeness.  
20. Local smoke on wrong port (8000 vs 8001).  
21. Trusting JSON workbench overlay when PG-primary strict.  
22. WeChat callback failure mistaken for intake API key bug.  
23. Schema epoch mismatch between branches during replay comparison.  
24. Fat fingering `UNIFIED_INTAKE_DB_PRIMARY_READS` override in prod debug.  
25. Assuming guardrail PASS implies live Cloud Run health.  
26. Over-loading `/ready` semantics when Qdrant wedged.  
27. Missing ALLOWED_ORIGINS entry for new Vercel preview hostname.  
28. Operating without `replay_lineage.semantics` in tickets → false audit claims.  
29. Case ID reuse across environments without manifest SHA check.  
30. Founder-only access to DB/psql for disputes — bus factor.

---

## TOP_30_SUPPORT_FAILURES

1. Opening manifest without support key when team thinks it is protected.  
2. No git SHA captured on ticket.  
3. Explaining replay without `intake_schema_epoch`.  
4. Treating case-head as full message export.  
5. Pasting manifest JSON containing internal URLs into customer email.  
6. Missing `request_trace_id` correlation.  
7. Assuming anonymous_ok is acceptable on public internet pilot.  
8. Short support key without reading `support_operator_warnings`.  
9. Conflating intake perimeter key with support key.  
10. Ignoring `production_support_export_risk`.  
11. Wrong interpretation of `tenant_truth.client_asserted_org_id`.  
12. Not checking `case_persistence_mode` before “where is my case”.  
13. Escalating to engineering without deployment-manifest snapshot.  
14. Expecting RLS guarantees from Postgres URL presence alone.  
15. Using stale chaos/regression JSON from `results/` as live truth.  
16. Failure to rotate support key after contractor offboarding.  
17. Assuming funnel analytics = case truth.  
18. Not documenting office enforcement on/off in ticket.  
19. Blind trust in broker-provided org names vs IDs.  
20. Skipping `office_ownership` block when debugging wrong-office reports.  
21. Misreading LEGACY visibility rules under enforcement.  
22. Expecting WORM from `audit_export` naming.  
23. No checklist when `operator_warnings` non-empty.  
24. Support smoke script failure interpreted as code regression vs server down.  
25. Bearer vs header confusion for support key.  
26. Ignoring semantics string on replay lineage.  
27. Assuming TestClient behavior matches Cloud Run cookies/CORS.  
28. Missing DB observability when hydration gaps logged.  
29. Attribution disputes without comparing stub vs PG row timestamps.  
30. Ticket closed without persistence posture recorded.

---

## TOP_30_DEPLOYMENT_FAILURES

1. Node 20.18 PATH causing Vite 7 build failure.  
2. `npm run build` never run before claiming UI green.  
3. Secret Manager mismatch during `deploy_rag_demo.sh`.  
4. Omitting `ALLOWED_ORIGINS` from deploy bundle.  
5. Manual prod patch overwritten next deploy.  
6. `DEMO_MODE` left true in prod-adjacent env.  
7. Product-only unintentionally enabled hiding debug routers.  
8. Wrong region/project in gcloud describe.  
9. Min instances cost shock vs latency shock tradeoff mishandled.  
10. Embedding dev API URL in production Vercel project.  
11. Logging OPENAI prefix at startup — key hygiene (operational).  
12. Parallel experiments on same Cloud Run service without revision pinning.  
13. Container memory too low for embed warmup spikes.  
14. Assuming Docker compose ports match demo scripts.  
15. Failure to document rollback revision ID.  
16. ENV typos (`prod ` with space).  
17. Missing `SERVICE_RECORD_DATABASE_URL` in secret binding.  
18. Running migrations only locally, not in pilot DB.  
19. Trusting default FAST_STARTUP without measuring cold path.  
20. Full regression skipped before release candidate.  
21. Guardrail skipped due to “small change”.  
22. Madge cycles ignored — UI import regression risk.  
23. Partial env copy from teammate laptop.  
24. Using wildcard CORS for pilot “speed” then forgetting to tighten.  
25. Stale `INTAKE_SCHEMA_EPOCH` documentation vs code.  
26. Branch deployed not matching manifest git SHA expectation.  
27. Multi-office rollout without staged enforcement flag plan.  
28. Alerts wired to `/health` phase without embed context.  
29. Assuming Cloud Run always routes `/healthz`.  
30. No written deploy-owner handoff when founder travels.

---

## TOP_30_OFFICE_CONFUSION_FAILURES

1. Legacy unstamped cases mixing with stamped lists.  
2. Strict list hides legacy → “where did cases go”.  
3. Tab A office-alpha, Tab B office-beta same browser.  
4. Wrong `X-Org-Id` string casing mismatch (if ever introduced) — today trimmed equality.  
5. Broker thinks carrier ID == org ID.  
6. Enforcement off → perceived “data leak” between franchises.  
7. Enforcement on → perceived “lost history”.  
8. Session reuse after office switch without new session.  
9. Clipboard `case_id` pasted into another office’s UI path.  
10. Training uses demo org string; prod uses different string.  
11. Analytics counts interpreted as office-authoritative without header propagation audit.  
12. Binding candidates filtered — broker thinks system “lost” cases.  
13. Migration backfill of `office_owner_org_id` incomplete mid-window.  
14. PG column vs JSON extra divergence during incident edits.  
15. Founder manually edits DB row — breaks narrative of client assertion.  
16. Multi-office SSO expectation — **not implemented** (honesty).  
17. Sub-broker accounts — no distinct auth primitive.  
18. Office rename request without ID stability discipline.  
19. Printed PDFs with case IDs crossing office boundaries.  
20. Support reads case without org context on ticket.  
21. Customer WhatsApp thread spans offices — product ambiguity.  
22. Test fixtures left in shared pilot DB.  
23. Clock skew misunderstands `updated_at` ordering.  
24. Duplicate humans answering same case — operational, not technical fix.  
25. Language mix causing wrong intent classification blamed on office routing.  
26. Vehicle key collisions across offices misunderstood.  
27. Expecting automatic org inference from phone number — not guaranteed.  
28. WeChat binding perceived as office proof — still assertion layer issues remain.  
29. Dashboard filters omit org → misleading workload stats.  
30. Pilot contract silent on org ID issuance → chaos at 30 offices.

---

## TOP_30_FAKE_SAAS_PATTERNS

1. Calling header org “tenant authority”.  
2. Implying Postgres URL alone delivers multi-tenant isolation.  
3. Selling manifest JSON as audit-grade export.  
4. Claiming `audit_export` is compliance logging.  
5. Presenting support shared secret as enterprise SSO.  
6. Stating product-only mode is “zero attack surface”.  
7. Assuming sessions cannot leak across users without DB.  
8. Implying guardrails replace monitoring/alerting.  
9. Marketing funnel analytics as broker SLA metrics.  
10. Calling intake API key “broker authentication”.  
11. Suggesting `office_owner_org_id` is tamper-proof.  
12. Claiming dual-write is seamless without reconciliation story.  
13. Assuming Cloud Run HTTPS solves office binding.  
14. Presenting chaos regression as contractual perf SLA.  
15. Implying automatic RLS from future sprint without shipping it.  
16. Treating demo.env.example as legally binding runbook for brokers.  
17. Stating WeChat OAuth proves customer identity for regulated purposes.  
18. Claiming JSON fallback never loses data.  
19. Suggesting founders can scale to 100 offices without support tooling beyond manifest.  
20. Calling `tenant_truth` object “tenant resolution”.  
21. Implying case-head export satisfies carrier evidence requests.  
22. Presenting engine graph loads as customer feature when platform-only.  
23. Suggesting `/ready` green means LLM quality acceptable.  
24. Claiming embedding warmup phases are fraud-proof readiness.  
25. Marketing “Unified Intake” as full AMS replacement.  
26. Implying clipboard hygiene is enforced by software.  
27. Stating replay semantics string is a lawyer-approved disclaimer — it is engineering honesty only.  
28. Suggesting Vercel preview URLs are safe for PHI — operational boundary unset.  
29. Calling operator_warnings “SOC2 controls”.  
30. Promising enterprise IAM roadmap dates without builds.

---

## TOP_30_SURVIVABILITY_GAPS

1. No hosted operator dashboard for org posture across offices.  
2. No automated nightly manifest diff between envs.  
3. No secret rotation runbook executable by non-founder.  
4. Limited case dispute merge UI — relies on founder DB skill.  
5. Support tooling lacks redaction helper for exports.  
6. No per-office rate visibility — noisy neighbor ambiguous.  
7. PG hydration gap signals exist but no paging integration.  
8. Clipboard + support key social engineering risk unmanaged.  
9. Multi-office onboarding checklist not enforced in software.  
10. Session fixation education gaps for brokers.  
11. Weak story for broker offboarding data deletion.  
12. Analytics vs case truth reconciliation absent.  
13. No structured “wrong office” incident type in ticketing template.  
14. Enforcement rollout playbook software-enforced only via env — easy to typo.  
15. Dual-track JSON/PG migration remains cognitively heavy.  
16. Cloud Run revision rollback practiced rarely — muscle memory low.  
17. No synthetic probe for support manifest auth regression.  
18. Trial docs proliferation — risk of contradictory SSOT (mitigated by THIS file for sprint scope only).  
19. Founder dependency on Vercel project settings.  
20. Lack of per-office config versioning in client packs surfaced to support.  
21. Minimal automation for ALLOWED_ORIGINS discovery from Vercel CLI.  
22. Stress testing mostly chaos script — not full multi-tenant load model.  
23. Operational honesty relies on reading comments — could regress if docs diverge.  
24. No kill switch for triage globally besides perimeter keys.  
25. Attachment paths — secondary risk surface not central here.  
26. OCR paths — third-party key hygiene.  
27. LLM outage degradation story not customer-facing standardized.  
28. Bus factor on deploy scripts (`deploy_rag_demo.sh`).  
29. Incomplete typing of env flags — runtime stringly typed.  
30. Psychological: selling “pilot” while env says “prod” — **`operator_warnings`** now surfaces contradiction.

---

## PHASE 3 — TABLETOPS

### WHAT_BREAKS_AT_30_OFFICES

- **Org ID issuance chaos:** duplicate strings, typos, stale spreadsheets — support tickets spike; enforcement amplifies pain if rolled out suddenly.  
- **Legacy unstamped rows:** perceived data leaks or missing cases depending on strict list flags.  
- **Support queue:** manifest interpretation errors; founders become bottleneck on DB queries.  
- **Clipboard case_id leakage:** human error crosses offices faster than tooling prevents.  
- **Analytics confusion:** dashboards without strict org correlation mislead managers.

### WHAT_BREAKS_AT_100_OFFICES

- Everything at 30, plus: **key rotation logistics**, **CORS origin explosion**, **cost visibility** (Qdrant/OpenAI/Cloud Run), **incident deduplication** without structured codes, **on-call** unsustainable on founder-only escalation.

### WHAT_BREAKS_AT_ENTERPRISE

- **Honest answer:** current architecture is **not** enterprise-sales-safe as sold — no broker IAM, no row-level security story, no SSO, no formal compliance exports, no multi-region DR narrative in code. Enterprise procurement expectations exceed shipped honesty layer.

---

## PHASE 4 — IMPLEMENTATION LOG (this sprint)

| Change | Rollback | Purpose |
|--------|----------|---------|
| `deployment_operator_warnings()` + extended `operator_runtime_hints()` | revert `deployment_profile.py` | Surface ENV/DEMO contradictions, prod-like missing DB URL, in-memory session flag hazards — deployment truth & drift detection |
| `deployment_identity_truth()` nested under `operator_runtime_hints["deployment_identity"]` | revert `deployment_profile.py` | Faster “which revision?” answers on tickets (Cloud Run / optional CI env vars); explicit non-provenance semantics |
| `office_enforcement_on_without_service_record_database_url_multi_instance_unsafe_v1` warning | revert `deployment_profile.py` | Continuity honesty when enforcement expects durable shared case store |
| `GET /health` → `deployment_profile.office_ownership` | revert `app_main.py` | Support-survivable glance at enforcement posture without authenticated manifest |
| `configs/demo.env.example` pointer to this SSOT under office section | revert line | Single doc anchor for operators |
| `tests/test_deployment_profile.py` | revert | Lock hints, warnings, deployment_identity, office_ownership on `/health` |
| `tests/test_support_export_gate.py` — assert `operator_warnings` list on manifest | revert | Manifest contract smoke via pytest |
| `scripts/support_deployment_manifest_smoke.py` — require `operator_warnings`, `deployment_identity`, `/health` `office_ownership` | revert | Operator script parity |

**Explicitly NOT shipped:** RBAC/SSO/RLS/billing/event bus/microservices.

---

## PHASE 5 — VALIDATION RECORD

Last automated pass (**2026-05-10**, branch `sprint/pilot-saas-survivability-office-trust-hardening`).

| Check | Result |
|-------|--------|
| `python3 -m compileall -q services/fiqa_api tests` | **PASS** |
| Targeted pytest (`deployment_profile`, `support_export_gate`, `case_office_access`, `intake_api_gate`) | **PASS** (24 tests) |
| Full `pytest` | **PASS** (1 skipped; SWIG `DeprecationWarning` noise) |
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** |
| `PYTHONPATH=. python3 scripts/run_full_regression.py` | **PASS** (`http_p95_ms` ≈ **4214** &lt; 6000; `wrong_vehicle_related` **0**; `pg_mismatch_turns` **0**) |
| Support/export smoke | `scripts/support_deployment_manifest_smoke.py` — requires running API (+ optional support key); asserts `deployment_identity` + `office_ownership` on `/health` |
| Office continuity / wrong-office | `tests/test_case_office_access.py` **PASS** (via full pytest) |
| Replay lineage | `tests/test_support_export_gate.py` **PASS** |
| Deployment manifest | pytest **PASS** |
| Health endpoint | `tests/test_deployment_profile.py` **PASS** |
| Madge `cd ui && npx --yes madge --circular --extensions ts,tsx src` | **PASS** (no cycles) |
| `npm run build` | **FAIL** with default PATH Node **v20.18.2** (below `engines` / Vite 7); **PASS** with `PATH=/home/andy/.nvm/versions/node/v22.22.0/bin:$PATH` → **v22.22.0** |

---

## SELF_CRITIQUE_REPORT_V8

1. **Fake safety:** Optional API keys are **not** broker identity — calling them “security” externally is dishonest; they reduce drive-by scraping only.  
2. **Fake tenancy:** `X-Org-Id` + `asserted_org_id` are continuity hints, not isolation proofs.  
3. **Fake replay:** Manifest + case-head are engineering aids; semantics string explicitly denies legal hold — repeating that in sales is mandatory.  
4. **Fake support narrative:** “Run guardrail = production safe” is false — only reduces regression drift.  
5. **Deployment assumptions:** Clean git tree is assumed by some runbooks; reality is often WIP-heavy — operators must read status.  
6. **Operational blind spots:** No automated prod manifest polling; drift detected only when someone looks at `/health`.  
7. **Support illusions:** Pytest proves shape, not Cloud Run wiring — smoke script still needs live URL + key discipline.  
8. **Founder dependency:** DB + Vercel + GCP triple remains concentrated; warnings don’t delegate authority.  
9. **Env complexity:** Persistence matrix (`service_record_settings`) still requires senior engineer to explain — hints help, don’t eliminate training debt.  
10. **Scaling illusions:** `operator_warnings` does not increase capacity — it increases honesty at the margin only.
11. **deployment_identity theater:** If CI/CD never injects `K_*` or commit SHA env vars, the block is honestly empty — **do not** pretend it replaces release auditing or binary provenance.

---

## CONVERGENCE — LABELS

| Label | Meaning |
|-------|---------|
| **REAL** | Postgres-backed pilot paths, optional enforcement, support/manifest honesty strings, persistence report, operator warnings codes |
| **FAKE** | Enterprise IAM/RLS/SSO/compliance/WORM claims; header-as-tenant boundary |
| **READY** | Paid pilot with founder-operated deploy + explicit env checklist + keys rotated deliberately |
| **NOT READY** | Enterprise procurement “secure multi-tenant SaaS” without major new systems |
| **PILOT SAFE** | Small office count, founder on-call, enforcement staged, secrets set, DB URL present |
| **ENTERPRISE UNSAFE** | Large self-serve tenant base, unclear org issuance, no SOC2 story aligned to code |
| **OPERATIONALLY HONEST** | This sprint’s direction: manifest + warnings + explicit non-IAM docs |
| **STILL DANGEROUS** | Anonymous support surface on public URL; weak keys; wrong-office human error; JSON/PG migration windows |

---

## SPRINT-OWNED FILES

- `docs/sprints/PILOT_SAAS_SURVIVABILITY_OFFICE_TRUST_HARDENING_SPRINT.md` (this SSOT)  
- `services/fiqa_api/deployment_profile.py`  
- `services/fiqa_api/app_main.py` (`/health` office posture)  
- `configs/demo.env.example` (SSOT pointer)  
- `tests/test_deployment_profile.py`  
- `tests/test_support_export_gate.py`  
- `scripts/support_deployment_manifest_smoke.py`

---

## PHASE 8 — FINAL REQUIRED OUTPUT (operator digest)

1. **Branch:** `sprint/pilot-saas-survivability-office-trust-hardening`
2. **Sprint-owned files:** Listed above (plus validation transcripts in shell history / CI).
3. **Implemented (this iteration):** Deployment identity truth on `operator_runtime_hints`; prod office-enforcement-without-DB warning; `/health` exposes `office_ownership`; smoke script hardened; demo.env SSOT pointer; tests extended.
4. **More real:** `/health` and manifest-adjacent paths expose enforcement + deploy labels with explicit non-IAM / non-provenance semantics.
5. **Still fake:** Enterprise IAM, RLS, SSO, WORM/compliance, header-as-tenant-authority, “manifest = audit export”.
6. **Biggest support truths:** Shared-secret gates are optional; replay lineage string denies legal hold; `tenant_truth` is client assertion; persistence mode drives “where is my case”.
7. **Biggest deployment truths:** Full redeploy replaces Cloud Run env bundle from template; CORS + Vite API URL are drift magnets; Node version gates UI build.
8. **Biggest replay truths:** Schema epoch + manifest version matter; PG/JSON authority periods invalidate naive replay diff.
9. **Biggest office continuity truths:** Enforcement is string match on `asserted_org_id`; legacy unstamped rows are a product hazard; sessions need Postgres for durable multi-instance continuity.
10. **Biggest auth truths:** No `tenant_id_authoritative`; intake vs support keys are separate coarse perimeters.
11. **Biggest operational truths:** `operator_warnings` codes are diagnostic, not controls; founder still owns GCP/Vercel/DB interpretation.
12. **Biggest remaining risks:** Anonymous support surface if key unset; wrong-office human error; secret leakage; dual-track persistence confusion during migration.
13. **Biggest founder dependencies:** Env parity, Secret Manager discipline, dispute queries, office ID issuance convention.
14. **30 offices:** Org ID chaos, legacy row visibility cliffs, support manifest misreads, clipboard leakage.
15. **100 offices:** + key rotation, CORS/origin sprawl, cost opacity, on-call unsustainable without delegation.
16. **Enterprise sales:** Current honesty layer ≠ procurement security claims — ship narrative discipline or decline scope.
17. **Best next 10× leverage:** Automated manifest diff between staging/prod + synthetic probe for support-route auth regression.
18. **Best next sprint:** Structured support ticket template (persistence snapshot + warnings + case-head) wired into Notion/Linear.
19. **Best 3-month roadmap:** Real broker IAM **or** stop selling multi-tenant isolation; either way, reconciliation tooling for PG vs operational expectations.
20. **What NOT to build yet:** SSO platform, billing, tenant admin UI, event bus rewrite, “RLS” theater without Postgres policies + app identity model.
21. **FINAL_ONE_LINE:** Honest pilot survivability means smaller lies in `/health`, not a bigger platform fantasy.

---

## FINAL_ONE_LINE (internal)

**Honest pilot survivability means smaller lies in `/health`, not a bigger platform fantasy.**
