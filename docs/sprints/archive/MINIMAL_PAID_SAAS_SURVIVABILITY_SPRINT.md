# MINIMAL PAID SAAS SURVIVABILITY SPRINT — SSOT

**Authority:** This document is the single source of truth for discoveries, simulations, rollback notes, and convergence for this sprint.  
**Branch:** `sprint/minimal-paid-saas-survivability-20260509`  
**Date:** 2026-05-09  
**Scope:** Minimal broker/auth boundary + org ownership persistence foundation only.

---

## PHASE 0 — Repo inventory

### Git state (at sprint start)

- **Prior branch:** `auto-evolution/tenant-auth-rls-support-replay-foundation-20260507-0247`
- **Dirty tracked files (sample):** `app_main.py`, `routes/inbox_triage.py`, `case_store.py`, `session_store.py`, `session_repository.py`, `service_record_repository.py`, `case_truth_repository.py`, UI intake API/types, `configs/demo.env.example`, `scripts/trial_readiness_check.sh`, tests.
- **Untracked (sample):** Many `docs/sprints/*`, `results/*`, `scripts/run_full_regression.py`, `deployment_profile.py`, `audit_export.py`, `tests/test_support_export_gate.py`, `services/fiqa_api/security/`, etc.

### Existing auth-related logic (identified)

| Area | Location | Semantics |
|------|----------|-----------|
| Client org assertion | `security/request_identity.py` | `X-Org-Id` → `request.state.client_asserted_org_id`; **not** IAM |
| Support export gate | `security/support_export_gate.py` | Optional `UNIFIED_INTAKE_SUPPORT_API_KEY` on `/api/inbox/support/*` |
| Intake perimeter (this sprint) | `security/intake_api_gate.py` | Optional `UNIFIED_INTAKE_INTAKE_API_KEY` on `/api/inbox/*` except `/support/*` + WeChat callback |
| CORS / credentials | `app_main.py` | Often `ALLOW_ALL_CORS`; production should narrow origins |
| Analytics | `routes/analytics_dashboard.py` | **No auth** — in-memory funnel (`/api/analytics/dashboard`) |

### Org / client persistence paths (identified)

| Path | Mechanism |
|------|-----------|
| Broker pack / lane config | `client_id` string from config / request (`config_loader.get_active_client_id`) |
| Case document | JSON file and/or Postgres `service_records` + `extra` JSONB |
| Session document | Postgres `intake_sessions.payload` or in-memory (tests) |
| Tenant authority | **None** — `tenant_id_authoritative` always `None` in `IntakeTenantTruth` |

---

## PHASE 2 — SYSTEM DISCOVERY OUTPUTS

### 1. REAL_AUTH_BOUNDARY_MAP

- **Real:** TLS termination at edge (Cloud Run / proxy); optional shared secrets for support export and (now) inbox HTTP surface when env vars are set.
- **Real:** Explicit honesty strings: `client_asserted_org_id_not_tenant_authority_v1`, support replay semantics `support_replay_handoff_metadata_v1_not_legal_hold`.
- **Not real:** Per-broker cryptographic identity, JWT/session cookies, OAuth for brokers, row-level security tied to authenticated subjects.

### 2. FAKE_AUTH_PATTERNS

- Treating `X-Org-Id` as tenant isolation.
- Assuming Cloud Run URL secrecy equals access control.
- Calling analytics “internal” without network/auth separation.
- Implying Postgres presence equals multi-tenant enforcement.

### 3. REAL_ORG_OWNERSHIP_MAP

- **`client_id`:** Config/pack identifier for copy and behavior — **not** cryptographically bound to HTTP caller.
- **`asserted_org_id` (new):** Persisted hint from `X-Org-Id` at session save and case create — **explicitly client-asserted**, stored for operational lineage.

### 4. CASE_OWNERSHIP_TRUTH_MAP

- No field represents “authenticated broker user owns this case.”
- `current_owner` in Postgres insert path is explicitly `None` in `persist_new_case`.
- Binding/reopen logic uses `case_id`, session linkage, and triage stubs — not IAM-proven office identity.

### 5. SUPPORT_SURFACE_MAP

| Endpoint | Gate |
|----------|------|
| `GET /api/inbox/support/deployment-manifest` | `assert_support_export_authorized` |
| `GET /api/inbox/support/case-head/{case_id}` | Same |
| Manifest payload | `replay_lineage`, `tenant_truth`, `auth_posture`, `intake_perimeter` (post-sprint), `request_lineage.request_trace_id` |

### 6. REPLAY_TRUTH_MAP

- **Engineering-grade:** `request_trace_id`, git SHA, schema epoch, manifest version, case-head metadata.
- **Not compliance-grade:** No WORM, no immutable audit chain, no signed export bundles (`audit_export.py` explicitly deferred).

### 7. TOP_30_OPERATIONAL_FAILURES (representative)

1. Public inbox URL without `UNIFIED_INTAKE_INTAKE_API_KEY` → drive-by reads/writes.  
2. Public URL without support key → deployment reconnaissance.  
3. `ENV=prod` but missing DB URL → case/session persistence degraded (warnings exist).  
4. Dual-write off + multi-instance → session stickiness false confidence.  
5. JSON read fallback mis-set during migration → wrong source of truth.  
6. CORS `*` + credentials false → accidental coupling with random frontends.  
7. Founder-only knowledge of which env bundle is live → wrong incident assumptions.  
8. Analytics buffer process-local → false funnel truth under scale.  
9. Qdrant/embed warmup → 503 “mystery” if ops only hits `/healthz`.  
10. WeChat callback exempt from intake key → must rely on state/nonce correctness (OAuth threat surface).  
11. Large case list GET without rate limits → noisy neighbor.  
12. Attachment paths wrong on disk → 404 support churn.  
13. Clock skew → confusing `updated_at` ordering in support tickets.  
14. Partial Postgres DDL → runtime create-if-not-exists hides migration discipline drift.  
15. `FAST_STARTUP` deferrals → “ready” versus “actually usable” confusion.  
16. Mixed English/Chinese logs → L1 triage slows.  
17. Missing `UNIFIED_INTAKE_SUPPORT_API_KEY` in prod-like mode → silent anonymous support export.  
18. Missing intake key in prod-like mode → silent anonymous inbox (pre-sprint); **now warned + optional enforced**.  
19. Wrong `SERVICE_RECORD_DATABASE_URL` rotation → cases appear “lost.”  
20. Demo cases path writable in prod-like → accidental data poisoning.  
21. Client pack mismatch between FE and BE deploy → wrong handoff copy while “system up.”  
22. Stale `INTAKE_SCHEMA_EPOCH` documentation → wrong replay assumptions.  
23. Operator runs manifest smoke against wrong region URL → false green.  
24. Embedding model change without epoch bump discipline → retrieval regressions “feel random.”  
25. Session eviction cap (`_MAX_SESSION_ROWS`) → unexplained continuity loss under load tests.  
26. Support ticket lacks `request_trace_id` correlation from FE → cannot match logs.  
27. Multiple brokers share one deployment without header discipline → `asserted_org_id` collisions in reporting (hint-only).  
28. Cloud Run min instances = 0 → cold start during broker demo.  
29. LLM dependency outage → triage path unclear fallback messaging to brokers.  
30. No formal on-call runbook link from manifest → founder paging for every anomaly.

### 8. TOP_30_SUPPORT_FAILURES (representative)

1. Cannot prove which deployment answered a case.  
2. Cannot distinguish client assertion vs authoritative tenant.  
3. Case-head lacks ownership fields historically → “whose office?” loops.  
4. Anonymous support export in prod-like env → ticket severity fights.  
5. No stable partition key per broker beyond hints.  
6. FE omits `X-Org-Id` → org lineage missing (mitigated by honesty + persistence hint).  
7. Replay bundle not signed → disputes inconclusive.  
8. Logs lack request id in customer-facing errors → duplicate reports.  
9. Attachments redacted inconsistently → privacy anxiety.  
10. Session vs case ID confusion in tickets.  
11. English/Chinese mixed transcripts without labeling policy.  
12. “Workbench test” cases mixed with production pilots.  
13. Support assumes single-region routing; DNS cutover invalidates notes.  
14. Manifest stale vs running container → false compatibility claims.  
15. PG mirror lag (if introduced later) → head-scratching 404s.  
16. Multiple git SHAs during rolling deploy → ambiguous replay.  
17. Operator fat-fingers support key rotation without FE update → total outage perception.  
18. No L1 script for “503 embedding_warming” → founder escalations.  
19. Case append boundary disputes → engineering-only interpretation docs.  
20. OCR paths vendor-specific → reproduction difficulty.  
21. Third-party email forwarding breaks session continuity → “duplicate cases.”  
22. Vendor webhook retries → duplicate messages interpreted as new intent.  
23. Lack of explicit “data residency” statement → enterprise blocker (expected).  
24. Customer PII in URLs (if ever introduced) → audit panic (not current).  
25. Internal analytics mistaken for customer KPIs → wrong commitments.  
26. Support cannot access FE console → cannot repro header issues.  
27. Language mismatch between broker staff and logs → slow RCA.  
28. Incomplete case deletion semantics → “delete” expectations violated.  
29. Rate limiting absent → abusive replay scripts flood triage.  
30. Training gap: “headers are not security” → sales overpromises multi-tenant isolation.

### 9. TOP_30_FOUNDER_DEPENDENCIES (representative)

1. Which env vars actually set on the live Cloud Run service.  
2. Whether DB primary writes are truly on for this pilot.  
3. Interpreting `deployment_profile` banner logs.  
4. Knowing the correct health URL (`/health/live` vs `/healthz` pitfalls).  
5. Rotating support vs intake keys without downtime discipline.  
6. Mapping `client_id` packs to real broker brands.  
7. Deciding when to bump `INTAKE_SCHEMA_EPOCH`.  
8. Interpreting PG vs JSON drift warnings.  
9. Handling WeChat OAuth app registration + redirect URI drift.  
10. Knowing which scripts are authoritative (`guardrail_inbox_triage.sh`).  
11. Qdrant collection naming per demo vs prod.  
12. Embedding warmup patience versus user-facing SLA.  
13. Whether analytics buffer reset is acceptable during incident.  
14. Coordinating Vercel env with Cloud Run CORS.  
15. Git SHA correlation across UI vs API builds.  
16. Whether product-only mode is enabled for paid pilot.  
17. Deciding incident severity when intake is open anonymously.  
18. Vendor relationship for OCR/LLM outages.  
19. Legal wording around replay exports (`audit_export` honesty).  
20. Disk paths for attachments on Cloud Run (ephemeral).  
21. Capacity planning for concurrent broker offices on one instance.  
22. Migration sequencing when enabling intake key globally.  
23. Explaining “asserted org” semantics to brokers without sounding weak.  
24. Choosing pilot kill-switch (disable triage vs disable reads).  
25. Manual cleanup of poisoned demo JSON cases.  
26. Understanding case boundary policy exceptions.  
27. Running full regression locally before declaring green.  
28. Managing multiple pilot brokers on one deployment (hint-only partitioning).  
29. Setting realistic CFO-facing uptime definitions.  
30. Saying “no” to enterprise SSO theater pre-revenue.

### 10. TOP_30_FAKE_SAAS_PATTERNS (representative)

1. Calling header org a “tenant.”  
2. Postgres row without IAM labeled “multi-tenant.”  
3. Dashboard charts presented as customer billing metrics.  
4. Marketing “enterprise-ready” with optional secrets off.  
5. RBAC language without roles implementation.  
6. “Audit trail” via mutable JSON logs.  
7. “Encrypted at rest” claims without key management story.  
8. Implying RLS exists when it does not.  
9. Treating demo guardrails as contractual SLAs.  
10. Single shared API key as “per-broker auth.”  
11. Analytics as observability substitute.  
12. Manual founder deploy checks called “GitOps.”  
13. Case IDs as security boundaries.  
14. Session IDs embedded in URLs without TLS discipline framed as “secure.”  
15. Hard-coded schema epoch as migration governance.  
16. Dual-write toggles described as “active-active.”  
17. Feature flags without audit who flipped them.  
18. Spreadsheets as customer source of truth alongside DB.  
19. Treating LLM output as regulated advice.  
20. “SOC2-ready” narrative on hobby infra.  
21. Calling JSON files “legacy only” while still readable in some modes.  
22. Implying Cloud Run IAM replaces broker auth.  
23. Using “prod” env label without DB discipline.  
24. Presenting founder analytics as broker-facing product surface.  
25. Shipping open CORS as “flexible integration.”  
26. Describing optional gates as on-by-default security.  
27. Paper integrations (“Stripe soon”) in pilot contracts.  
28. Treating triage semantics versioning as legal evidence versioning.  
29. Hidden admin endpoints in non-product-only profiles marketed away.  
30. Branding “Unified Intake” as full AMS replacement.

### 11. TOP_20_HIGH_ROI_MOVES

1. Require **both** intake + support keys on any internet-exposed paid pilot (operators configure).  
2. Persist **`asserted_org_id`** on case + session (done this sprint).  
3. Surface **`intake_perimeter`** + **`auth_posture`** together on manifest + `/health`.  
4. FE sends **`X-Request-ID`** correlation (already middleware) — ensure UI surfaces on error toast.  
5. Narrow **CORS** to known FE origins in pilot.  
6. Run **`trial_launch_check.sh`** before every broker kickoff.  
7. Document **kill-switch**: unset intake key only in break-glass (rollback path exists).  
8. Add **rate limiting** at edge (future; smallest is Cloud Armor or proxy).  
9. Split **analytics** onto authenticated founder route or IP allowlist (future).  
10. **Bump epoch** whenever FE/BE contract changes — tie to release checklist.  
11. **Backup Postgres** snapshot discipline for pilot data.  
12. **Attachment storage** off local ephemeral disk for real retention (future).  
13. **Per-broker API keys** when revenue justifies (true IAM-lite).  
14. **Synthetic monitors** on `/ready` + one triage smoke with secrets in vault.  
15. **On-call sheet**: manifest URL + required headers.  
16. **L1 script** mapping HTTP codes → operator actions.  
17. **Separate pilot projects** per tier when chaos dominates (cheap isolation).  
18. **Webhook signatures** if email ingress added (future).  
19. **Delete semantics** documented for brokers (avoid GDPR surprises).  
20. **Cost caps** on LLM per pilot day (financial survivability).

### 12. WHAT_BREAKS_AT_30_OFFICES

- Hint-only `asserted_org_id` collisions and mis-attribution in reporting without per-office keys.  
- Shared intake secret rotation coordination pain.  
- Founder bottleneck on interpreting logs without L1 tooling.  
- Analytics buffer meaningless across offices; false prioritization.  
- Support ticket volume overwhelms manifest-based RCA unless templated.

### 13. WHAT_BREAKS_AT_100_OFFICES

- Single-column broker identifiers (`client_id`, asserted org string) without registry discipline.  
- Operational drift: multiple deployments without infra-as-code parity.  
- Case search/list latency and noisy-neighbor effects without DB indexing investment.  
- Compliance questions on data segregation unanswered by architecture.

### 14. WHAT_BREAKS_AT_ENTERPRISE

- No SSO/SAML, no SCIM, no formal RBAC, no DPAs mapped to components.  
- Replay/export non-compliance-grade artifacts rejected by legal.  
- Lack of regional residency and key management story.  
- Shared secrets model rejected by infosec (rotate per env minimally acceptable).

### 15. WHAT_NOT_TO_BUILD_YET

- SSO, RBAC UI, Stripe, self-serve signup, full RLS, workflow builders, billing, CRM replacement, marketing redesigns, signed legal hold exports.

---

## PHASE 3 — ARCHITECTURE CONVERGENCE

**Smallest real foundation chosen:**

1. **Optional intake shared-secret perimeter** — same operational pattern as support gate; rollback = unset env var; exempt only `/api/inbox/support/*` and `GET /api/inbox/wechat/binding/callback`.  
2. **Persist client-asserted org hint** as `asserted_org_id` on cases (JSON + Postgres `extra`) and intake sessions — honesty preserved (`tenant_truth` unchanged).  
3. **Manifest + support case-head + `/health`** expose **`intake_perimeter`** alongside **`auth_posture`** for deployment truth.

---

## PHASE 4 — IMPLEMENTATION LOG (this sprint)

| Change | Rollback |
|--------|----------|
| `services/fiqa_api/security/intake_api_gate.py` | Remove middleware registration + unset `UNIFIED_INTAKE_INTAKE_API_KEY` |
| `app_main.py`: `IntakeApiPerimeterMiddleware`, prod-like warning, `/health` `intake_perimeter` | Revert middleware + health dict key |
| `case_store.save_case(..., asserted_org_id=)` | Stop passing kwarg; strip field from new cases if undesired |
| `service_record_repository._build_extra` + PG hydrate | Remove key from tuple + hydrate blocks |
| `session_store` / `in_progress_session_view` | Remove `asserted_org_id` handling |
| `routes/inbox_triage.py`: wire org → save_case + session; manifest/case-head fields | Revert wiring |
| `configs/demo.env.example` | Remove commented `UNIFIED_INTAKE_INTAKE_API_KEY` block |
| `tests/test_intake_api_gate.py` | Delete tests |

---

## PHASE 5 — VALIDATION LOOPS

| Loop | Result |
|------|--------|
| A — `python3 -m compileall -q services/fiqa_api tests` | PASS |
| A — `PYTHONPATH=. pytest tests/` | PASS (warnings only) |
| A — `bash scripts/guardrail_inbox_triage.sh` | PASS |
| A — `PYTHONPATH=. python3 scripts/run_full_regression.py` | PASS (`assertions.passed: true`) |
| B — replay / wrong-org / support-key simulations | Documented in sections above; automated intake/support tests cover gate matrix |
| C — tabletops | Captured in self-critique |
| D — guardrail + regression re-run | PASS after implementation |

### Mandatory validations — UI / Node

- **`cd ui && npm run build`** — **FAILED** in this environment.  
  - **Reason:** `Node.js 20.18.2` installed; Vite requires **20.19+ or 22.12+**. Follow-on error: `ERR_REQUIRE_ESM` loading Vite from `vite.config.ts` under incompatible Node.  
  - **Remediation:** Upgrade Node (e.g. `nvm install 22 && nvm use 22`) and re-run `npm run build`.

- **`cd ui && npx --yes madge --circular --extensions ts,tsx src`** — **PASS** (no circular dependencies).

---

## PHASE 6 — SELF_CRITIQUE_REPORT_V4

**Enterprise buyer:** Shared-secret perimeter is not tenant isolation; acceptable only for early pilot with contractual clarity — otherwise procurement will stall.

**Security reviewer:** Intake key rotation requires coordinated FE/header updates; WeChat callback exemption is necessary but increases reliance on OAuth state integrity; analytics remains unauthenticated.

**Angry broker:** “Why can someone with my URL hit intake?” — Answer: they can unless intake key is set; this must be explicit in onboarding.

**Exhausted founder:** Two secrets (intake + support) plus DB URLs multiply operational burden — document in one operator page.

**L1 support:** Case-head now includes `asserted_org_id` and `client_id` — reduces ambiguity but does not prove office identity.

**Operations engineer:** Middleware returns JSON `401` body — ensure proxies don’t strip bodies needed for L1.

**SaaS CFO:** Revenue-bearing SLA cannot rest on optional env vars without enforcement automation — next step is monitored configuration drift alerts.

---

## PHASE 7 — CONVERGENCE ANSWERS

1. **What became REAL?** Optional intake HTTP perimeter; persisted `asserted_org_id` hints on cases/sessions; manifest/health truth includes `intake_perimeter`.  
2. **What is still fake SaaS?** True multi-tenant IAM, RLS, per-user audit, billing, enterprise SSO.  
3. **What still depends on founder knowledge?** Live env bundles, key rotation choreography, schema epoch governance, Qdrant/LLM vendor posture.  
4. **What still breaks at 30 offices?** Reporting collisions on hints-only partitioning; support volume without L1 scripts; analytics not office-isolated.  
5. **What still breaks at 100 offices?** Architecture needs per-tenant keys or VPC-grade separation — shared secrets do not scale socially or operationally.  
6. **What is now operationally survivable?** Honest deployment manifest + optional coarse HTTP gates + persisted org hints for tickets.  
7. **What is now support-survivable?** Case-head includes org/client hints; manifest distinguishes support vs intake posture.  
8. **What is now deployment-honest?** `/health` exposes support + intake posture fragments side-by-side.  
9. **What is now replay-honest?** Same engineering-grade lineage as before; org hint adds operational context without claiming cryptographic tenant proof.  
10. **Next smallest 10x move?** Per-broker API keys minted from a registry (still no full IAM UI) **or** edge rate limiting + authenticated analytics separation.

---

## PHASE 8 — FINAL OUTPUT (mirrored for chat)

See user-visible summary in the assistant’s final message.

---

## Sprint-owned files (authoritative list)

- `docs/sprints/MINIMAL_PAID_SAAS_SURVIVABILITY_SPRINT.md` (this SSOT)  
- `services/fiqa_api/security/intake_api_gate.py`  
- `services/fiqa_api/app_main.py` (middleware, warnings, `/health` intake perimeter)  
- `services/fiqa_api/routes/inbox_triage.py` (org persistence wiring, manifest/case-head)  
- `services/fiqa_api/inbox_triage/case_store.py`  
- `services/fiqa_api/inbox_triage/session_store.py`  
- `services/fiqa_api/db/service_record_repository.py`  
- `configs/demo.env.example`  
- `tests/test_intake_api_gate.py`
