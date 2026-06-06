# SCOPED BROKER IDENTITY + OFFICE-SCOPED OPERATIONAL SAFETY SPRINT

**SSOT status:** Sprint authority for scoped broker identity hints, office continuity honesty, support/replay lineage, deployment posture, analytics scope, and rollback narratives.  
**Branch:** `sprint/scoped-broker-identity-office-operational-safety`  
**Schema epoch (code):** see `deployment_profile.INTAKE_SCHEMA_EPOCH`  
**Non-goals:** SSO, RBAC UI, billing, tenant admin portal, enterprise IAM theater, event-bus rewrite.

---

## PHASE 0 — GIT + INVENTORY (recorded)

| Item | Value |
|------|--------|
| Branch | `sprint/scoped-broker-identity-office-operational-safety` |
| Pre-existing WIP | **Yes** — multiple tracked modifications and untracked `services/fiqa_api/security/*`, tests, migrations from prior work **not** absorbed into this sprint’s narrative beyond honesty that they coexist on branch |
| Stashes | `stash@{0..15}` present (see `git stash list`) |
| Untracked highlights | `security/request_identity.py`, `intake_api_gate.py`, `support_export_gate.py`, `case_office_access.py`, `tests/test_case_office_access.py`, `scripts/run_full_regression.py`, many `docs/sprints/*` drafts |

**Rule:** This document is authority for **intent and operational truth**; merge conflicts must be reconciled against code before claiming production parity.

---

## PHASE 1 — SYSTEM REALITY MAP (files inspected)

| Area | Path |
|------|------|
| App composition, middleware order, `/health` | `services/fiqa_api/app_main.py` |
| Client org assertion | `services/fiqa_api/security/request_identity.py` |
| Intake shared secret | `services/fiqa_api/security/intake_api_gate.py` |
| Support export secret | `services/fiqa_api/security/support_export_gate.py` |
| Office enforcement | `services/fiqa_api/security/case_office_access.py` |
| HTTP routes + manifest + case-head | `services/fiqa_api/routes/inbox_triage.py` |
| Session persistence | `services/fiqa_api/inbox_triage/session_store.py`, `session_repository.py` |
| Case JSON + normalization | `services/fiqa_api/inbox_triage/case_store.py` |
| Read facade PG/JSON | `services/fiqa_api/inbox_triage/case_truth_repository.py` |
| Postgres service records | `services/fiqa_api/db/service_record_repository.py`, `db/schema/stage1_service_record.sql` |
| Deployment honesty | `services/fiqa_api/deployment_profile.py` |
| Audit scaffold | `services/fiqa_api/inbox_triage/audit_export.py` |
| Analytics buffer | `services/fiqa_api/analytics/funnel_events.py`, `triage_funnel.py`, `routes/analytics_dashboard.py` |
| Env template | `configs/demo.env.example` |
| Guardrail | `scripts/guardrail_inbox_triage.sh` |
| Regression | `scripts/run_full_regression.py` |

---

## 1. CURRENT_BROKER_IDENTITY_TRUTH

There is **no** cryptographically authoritative broker principal in the HTTP layer today. Runtime posture:

- **`IntakeTenantTruth`** (`request_identity.py`): `tenant_id_authoritative` is always `None`; `client_asserted_org_id` comes only from `X-Org-Id` captured by middleware — semantics string explicitly denies IAM (`client_asserted_org_id_not_tenant_authority_v1`).
- **Optional shared secrets:** `UNIFIED_INTAKE_INTAKE_API_KEY` gates `/api/inbox/*` except `/support/*` and WeChat OAuth callback; `UNIFIED_INTAKE_SUPPORT_API_KEY` gates `/api/inbox/support/*`. These are **deployment perimeters**, not identities (same key may be shared by many humans).
- **Light identity** fields (`person_link_*`, `identity_binding_state`) are optional CRM hints, not verified auth.

**Implication:** “Who is calling” for audit purposes is **best-effort**: network path + optional shared secret possession + client-asserted org string + logging context (`request_trace_id`).

---

## 2. CURRENT_OFFICE_CONTINUITY_TRUTH

- **Persisted hint:** `asserted_org_id` on cases (JSON and PG `extra`, mirrored to `office_owner_org_id` column when PG repo runs).
- **Optional enforcement:** `UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP` → `assert_case_office_access_allowed` returns 403 on mismatch or missing header when case stamped (`case_office_access.py`).
- **List scoping:** Under enforcement, `GET /api/inbox/cases` requires `X-Org-Id` and filters (with optional strict legacy exclusion via `UNIFIED_INTAKE_OFFICE_LIST_STRICT_NO_LEGACY`).
- **Session continuity:** Session rows carry `asserted_org_id`; route logic clears sticky case binding when office assertion shifts mid-flight (honest multi-office UX).

**Implication:** Office continuity is **policy + data stamping**, not database-enforced tenancy.

---

## 3. CURRENT_SUPPORT_TRUTH

- **`GET /api/inbox/support/deployment-manifest`** and **`GET /api/inbox/support/case-head/{case_id}`** require support secret when configured; otherwise anonymously reachable (explicit in env docs).
- Responses include **`replay_lineage`** (`support_export_manifest_version`, `intake_schema_epoch`, office posture dict), **`tenant_truth`**, **`operator_runtime_hints`**, **`request_lineage`** (`request_trace_id`).
- **case-head** exposes minimal non-PII case metadata for replay handoff; **not** a legal hold export.

---

## 4. CURRENT_REPLAY_TRUTH

Replay integrity is **documentary**, not cryptographic:

- Manifest + schema epoch + git SHA (best-effort) + wire contract label.
- PG vs JSON hydration fallbacks can produce different snapshots if misconfigured (`case_truth_repository` observability prefixes `UNIFIED_INTAKE_DB_OBS`).
- Support operator must align headers (`X-Org-Id`) with broker narrative; mismatch now surfaces as optional **`support_office_hint_check`** on case-head (this sprint).

---

## 5. CURRENT_DEPLOYMENT_TRUTH

- **`UNIFIED_INTAKE_PRODUCT_ONLY`** reduces mounted routers; inline platform routes gated elsewhere (`deployment_profile.py` docstring).
- **`deployment_identity_truth`**: Cloud Run `K_*` labels + optional commit env vars — explicitly **not tamper-evident**.
- **`deployment_operator_warnings`**: ENV/DEMO contradictions, PG URL missing in prod-like mode, in-memory sessions risks, office enforcement without DB (multi-instance unsafe), **duplicate intake/support API keys** (added this sprint).

---

## 6. CURRENT_ANALYTICS_TRUTH

- Funnel events live in an **in-process deque** (`funnel_events.py`) — single-instance semantics only.
- Events are **not** a billing or compliance ledger.
- **This sprint:** canonical funnel metadata includes optional **`client_asserted_org_id`**; **`GET /api/analytics/dashboard`** accepts **`X-Org-Id`** and filters buffered events, returning **`dashboard_scope`** counts (honest partial coverage when historical events lack org metadata).

---

## 7. CURRENT_SUPPORT_ESCALATION_TRUTH

Escalation chains depend on **human procedures** (founder docs under `docs/trial/`), not automated routing. Tooling provides manifest/case-head/trace id labels — not ticket system integration.

---

## 8. CURRENT_FOUNDER_DEPENDENCY_TRUTH

Founder remains load-bearing for: Cloud Run + Vercel env alignment, Secret Manager discipline, DATABASE_URL provisioning, interpreting JSON/PG drift logs, manual broker onboarding for headers/secrets, and deciding when enforcement flags flip.

---

## 9. CURRENT_DRIFT_TRUTH

Primary drift vectors: **partial deploy** (FE/API epoch skew), **manual gcloud env patches** lost on next scripted deploy, **DEMO_MODE vs ENV prod**, **PG schema not migrated**, **JSON fallback** masking PG truth, **two offices sharing demo credentials**.

---

## 10. CURRENT_ABUSE_SURFACE_TRUTH

Largest surfaces when secrets unset: **public triage POST**, **public support manifest**, **org spoofing** when enforcement off, **LLM cost amplification**, **attachment upload size**, **Enumeration of case ids** if IDs leak. Shared-secret perimeter reduces drive-by abuse but **does not** identify humans.

---

## TOP_50_SUPPORT_FAILURES

1. Support assumes SSO reality; logs show only shared-secret or open surface.
2. Ticket cites wrong Cloud Run revision because K_REVISION missing locally.
3. Manifest git SHA from filesystem disagrees with deployed container SOURCE_VERSION.
4. Operator pastes support key into customer-facing chat.
5. Replay bundle lacks schema epoch; interpretation invents fields.
6. L2 asks for case-head without office hint; wrong-office dispute escalates.
7. support_export anonymous_ok on public URL; crawler indexed manifest.
8. Two founders rotate keys; second forgot to update smoke script env.
9. JSON read fallback on in prod-like env masks PG outage.
10. case-head shows asserted_org_id null; broker insists office stamped.
11. Session binding cleared silently; support cannot reproduce thread.
12. WeChat callback exempt from intake key; confused with perimeter bypass.
13. Health DEMO_MODE true while ENV prod; ignored until outage.
14. In-memory sessions flag on with DB URL; split-brain sessions.
15. Dual-write off but analyst reads JSON file on disk.
16. Attachment path leakage through copied absolute paths in ticket.
17. Rate limit absent; abusive replay spam fills logs.
18. Langfuse keys in env screenshot attached to Slack.
19. Founder runs migration on wrong project Postgres.
20. service_records office_owner column NULL; list filter hides case.
21. Support disputes triage_contract_version vs FE bundle.
22. Clipboard case ID from staging pasted into prod manifest curl.
23. 404 case-head interpreted as permission when row purged.
24. Mixed timezone timestamps in export confuse litigation narrative.
25. Redaction policy verbal only; logs contain phone numbers.
26. Escalation loses request_trace_id chain.
27. Partial deploy: new FE old API schema epoch mismatch.
28. Rollback revision lacks office enforcement flag clarity.
29. Operator mistakes product-only for platform-full missing routes.
30. Qdrant down marks degraded; intake still works; support blames vectors.
31. OPENAI missing; silent degradation to rules-only not communicated.
32. Append blocked requires_new_case; broker tries force-append API.
33. Identity binding stub mistaken for verified customer auth.
34. Person_link_key treated as unique human globally.
35. Multi-tab session race; two active_case_id stories.
36. Cached triage stub stale within single request misunderstood.
37. PG connection timeout logged once; retries invisible.
38. Neon sleeping DB cold start blamed on application.
39. Secret Manager binding dropped on partial gcloud update.
40. CORS error masked as API 500 in browser.
41. Vercel preview URL not in ALLOWED_ORIGINS during demo.
42. Browser blocks third-party cookies irrelevant but blamed.
43. Support runs curl without X-Org-Id under enforcement; 403 misread.
44. Legacy unstamped cases visible; broker thinks leak.
45. Strict legacy hide surprises ops counting totals.
46. Export gate 401; operator assumes DDOS.
47. Weak support key brute-force not monitored.
48. Duplicate intake/support key halves blast radius story.
49. Office mismatch hint on case-head ignored.
50. Analytics filtered wrong; founder thinks funnel died.

---

## TOP_50_OFFICE_CONFUSION_FAILURES

1. Broker toggles office in UI; stale active_case_id from prior org.
2. Shared demo URL across franchises; cases merge perceptually.
3. X-Org-Id typo office_a vs office-a invisible until audit.
4. Enforcement off in prod-like env; surprise cross-office reads.
5. Enforcement on without consistent FE header wiring.
6. List endpoint returns empty; broker forgot header.
7. Legacy rows excluded; broker thinks data loss.
8. Legacy rows included; wrong-office confusion in queue.
9. PG office_owner column drift from JSON extra.asserted_org_id.
10. Migration backfill skipped; column empty.
11. Browser profile mixes cookies for two demo tenants.
12. Manual curl omits header; triage creates unstamped case.
13. Clipboard session_id reused across offices.
14. Workbench bookmark omits client pack param.
15. Two brokers share client_id string collision.
16. Vehicle key collision across offices assumed impossible.
17. Add-car lane stamp timing vs session save ordering.
18. Talk-to-agent path persist without org when header dropped.
19. Append successful under wrong header if enforcement off.
20. Office migration rename without row updates.
21. Broker A inherits Broker B DNS before TTL flush.
22. Training uses staging org id in prod bookmark.
23. PDF export manual includes wrong logo franchise.
24. Timezone in SLAs crosses midnight office boundaries.
25. Multi-office dashboard aggregate bleeds before filter.
26. Strict list hides escalations tied to unstamped historic cases.
27. Binding candidates filtered; broker cannot reopen old case.
28. Session office assertion shift clears binding mid-demo.
29. Staff copies case link; recipient office differs.
30. Mobile browser strips custom headers myth persists.
31. Reverse proxy strips X-Org-Id misconfiguration.
32. CDN caches GET cases response without Vary header hypothetical.
33. Docker local without enforcement trains wrong mental model.
34. Cloud Run multiple regions imaginary; actually single.
35. Postgres read replica lag hypothetical confusion.
36. JSON file path shared NFS hallucinated twin writes.
37. Operator runs psql update asserted_org_id wrong WHERE.
38. Broker thinks RLS exists because Postgres.
39. Excel pivot on exported CSV mixes offices.
40. Call center script asks wrong franchise disclosure.
41. IVR sends SMS deep link without org context.
42. Email forwarding strips metadata.
43. Screenshot redacts org id needed for support.
44. Zendesk macro inserts wrong office disclaimer.
45. Slack thread fork loses case-id message.
46. Notion runbook outdated enforcement flag.
47. GitOps drift between branches for header injection.
48. Feature flag office strictness inconsistent FE vs BE.

---

## TOP_50_IDENTITY_FAILURES

1. X-Org-Id trusted as cryptographic tenant boundary.
2. Bearer intake token assumed unique per broker human.
3. No authoritative tenant_id; dashboards invent tenant.
4. client_id treated as authenticated principal.
5. person_link_key confused with government ID.
6. WeChat openid assumed immutable forever.
7. Phone number normalization inconsistent hash collisions.
8. Email optional; identity merge ambiguous.
9. Session id entropy assumed unguessable.
10. API keys in browser localStorage hypothetical exposure.
11. JWT mentioned in sales deck; code has none.
12. mTLS promised; edge TLS only.
13. Rate limits documented but not implemented universally.
14. IP allowlist discussed; never shipped.
15. Geo fencing assumed from zip alone.
16. Device fingerprinting imagined.
17. OAuth state secret rotation undocumented.
18. Binding simulate flag left on in prod nightmare.
19. Anonymous intake surface confused with public marketing site.
20. Intake key rotation breaks embedded devices myth.
21. Support key reuse across environments.
22. Same machine prod and demo keys in bash history.
23. Environment variable injection via Procfile confusion.
24. Kubernetes service account identity hallucination.
25. Cloud Run service agent confused with user identity.
26. Audit log claims non-repudiation; only stdout logs.
27. Broker staff accounts table missing entirely.
28. Role admin/editor/viewer imagined.
29. Per-case ACL imagined.
30. Object-level encryption promised.
31. Customer consent ledger absent.
32. GDPR erasure workflow absent.
33. SOC2 checklist referenced verbally.
34. Pen test PDF from unrelated product attached.
35. Vendor SOC relied upon for app boundary.
36. API gateway policy fiction.
37. WAF rule assumed.
38. Bot detection absent.
39. Captcha absent.
40. HMAC request signing absent.
41. Nonce replay protection absent except funnel dedupe.
42. Clock skew attacks ignored.
43. Multi-instance sticky sessions absent.
44. Session fixation hypothetical.
45. CSRF on JSON POST underestimated risk.
46. CORS wildcard in demo copied to prod.
47. Subdomain takeover risk on stale Vercel.
48. TLS cert expiry monitoring external only.
49. Secrets in docker image layers hypothetical.

---

## TOP_50_DEPLOYMENT_FAILURES

1. ENV prod + DEMO_MODE true simultaneously.
2. UNIFIED_INTAKE_PRODUCT_ONLY unset; lab routes exposed accidentally.
3. platform_inline_route_leak_count non-zero regression.
4. Cloud Run min instances zero during trial peak.
5. Wrong REGION deploy script.
6. Secret literal replaces Secret Manager binding.
7. DATABASE_URL typo silent until triage write.
8. PG SSL mode mismatch.
9. Schema migration not applied; insert fails partially.
10. office_owner column migration skipped.
11. JSON writes off but disk path still read by script.
12. Health ready requires Qdrant when DEMO_MODE false surprise.
13. Embedding warming 503 playbook not run.
14. Revision traffic split 90/10 accidental.
15. Traffic tag wrong revision.
16. Custom domain mapping stale.
17. Vercel env not redeployed after API URL change.
18. API base URL http vs https mixed content.
19. CORS list truncated over CLI length limits.
20. gcloud auth application-default expired.
21. Workload identity not configured for Secret Manager.
22. Docker compose port 8000 vs local script 8001 confusion.
23. Python version drift local vs container.
24. Dependency lock not updated; poetry vs pip chaos.
25. Test fixture data shipped in image accidental.
26. DEBUG logging volume sinks Cloud Logging budget.
27. Log sampling obscures errors.
28. Trace exporter misconfigured OTEL.
29. Feature flag env typo OFF vs 0.
30. FAST_STARTUP false lengthens cold start unexpectedly.
31. MAIN_PORT vs PORT precedence misunderstood.
32. Health check path wrong on load balancer.
33. Graceful shutdown kills inflight triage.
34. INSTANCE_ID env assumed stable.
35. Git SHA build-arg missing in CI.
36. Multi-stage build caches stale layer.
37. Base image CVE panic unnecessary.
38. Roll forward instead of rollback under pressure.
39. Rollback removes migration incompatible.
40. Blue-green not supported; manual cutover human error.
41. Staging data refresh overwrites prod clone accident.
42. Backup restore untested.
43. Point-in-time recovery confusion.
44. Read replica endpoint never wired.
45. Connection pool size default too low spike.
46. Statement timeout too aggressive.
47. VACUUM manual forgotten.

---

## TOP_50_ABUSE_PATTERNS

1. Anonymous triage POST flood.
2. Manifest scraping for git SHA reconnaissance.
3. case-id enumeration when support open.
4. Intake key stolen from browser devtools if ever embedded.
5. Reflective XSS via client_reply_draft hypothetical.
6. Prompt injection via customer text into LLM.
7. LLM cost amplification large threads.
8. Image upload size DoS.
9. Attachment zip bomb hypothetical.
10. Webhook replay if added future.
11. Session id brute force low entropy fear.
12. Org id spoofing cross-office writes enforcement off.
13. Org id spoofing read others cases enforcement off.
14. Shared demo API key on GitHub gist.
15. Public Grafana dashboard hypothetical.
16. Log injection via newline in customer text.
17. Unicode homograph org ids.
18. HTTP parameter pollution duplicate headers.
19. Slowloris generic.
20. ZIP dns rebinding irrelevant.
21. CSRF triage from malicious site if CORS loose.
22. Clickjacking iframe hypothetical.
23. Prototype pollution JSON parse hypothetical.
24. YAML deserialization none.
25. Pickle remote none.
26. SQL injection parameterized safety but dynamic ORDER BY future risk.
27. Path traversal attachment filename.
28. Symlink attack attachment store hypothetical.
29. chmod 0777 attachment dir mistake.
30. World-readable bucket hypothetical.
31. Public Postgres port exposed.
32. Redis exposed hypothetical.
33. SSH password auth on VM.
34. Supply chain npm typo squatting.
35. Typosquat pypi internal.
36. Malicious model checkpoint unrealistic.
37. Fork bomb in OCR unrealistic.
38. Regex catastrophic backtracking triage regexes.
39. ReDoS in email validation.
40. Email header injection.
41. SMS pumping not applicable.
42. International toll fraud not applicable.
43. Crypto miner on compromised Cloud Run unrealistic short-lived.
44. Cryptojacking browser extension customer side.
45. Clipboard malware stealing case ids.
46. Support engineer stalking customer via logs policy gap.

---

## TOP_50_FAKE_SAAS_PATTERNS

1. We have multi-tenant isolation.
2. RLS secures all reads.
3. Every action audit trails to SOC.
4. Enterprise SSO ready.
5. RBAC shipped.
6. Per-tenant encryption keys.
7. Zero trust architecture checkbox.
8. SOC2 Type II in progress slide implies certified.
9. HIPAA compliant without BAA.
10. PCI scope avoided verbally incorrect.
11. 99.99% SLA on single-region hobby DB.
12. Automatic horizontal scale to 1000 offices today.
13. Self-service tenant provisioning portal.
14. Billing metered per seat live.
15. Usage analytics tamper-evident.
16. Legal hold WORM export shipped.
17. eDiscovery integration.
18. Data residency choice EU/US.
19. Air-gapped deployment one-click.
20. FedRAMP roadmap slide mistaken for status.
21. ISO27001 certified boilerplate.
22. Penetration tested annually claim.
23. Bug bounty program active.
24. CVE disclosure SLA.
25. Customer-managed keys KMS.
26. PrivateLink networking configured.
27. VPC peering mandatory narrative.
28. Dedicated instances per tenant default.
29. Noisy neighbor eliminated practically.
30. Fair queuing per tenant.
31. Quota enforcement strict.
32. Graceful degradation per tier.
33. Feature flags per tenant enterprise.
34. White-label mobile apps.
35. Offline-first guaranteed.
36. Real-time collaboration cursors.
37. Workflow builder for brokers.
38. AI agents autonomous binding coverage.
39. Auto-underwriting decisions.
40. Carrier API live integrations implied all.
41. DMV instant verification nationwide.
42. Credit pull embedded.
43. Identity verification KYC Level 3.
44. Biometric auth.
45. Hardware security module referenced.
46. Blockchain audit trail joke taken seriously.
47. NFT policy binder sarcasm.
48. Quantum-safe crypto readiness.
49. AI ethics board oversight.
50. Automated fairness certification.

---

## TOP_50_SURVIVABILITY_GAPS

1. No per-human broker authentication.
2. No tenant provisioning workflow.
3. No systematic key rotation runbook executed.
4. No anomaly detection on traffic.
5. No synthetic uptime monitors on triage path only vectors.
6. No chaos drills scheduled.
7. No documented RTO/RPO for intake DB.
8. No cross-region failover.
9. No gradual rollout feature flags server-side comprehensive.
10. No customer-facing status page wired.
11. No structured on-call rotation tied to dashboards.
12. No paging policy for embedding warming.
13. No SLO error budget policy.
14. No capacity model for LLM tokens.
15. No cost caps per office.
16. No deletion workflow for cases GDPR.
17. No export portability standard format.
18. No contract testing between FE contract_version and BE.
19. No automated screenshot diff for UI regressions.
20. No load test in CI.
21. No fuzzing customer text.
22. No static analysis gate on PR optional.
23. No dependency update bot merged discipline.
24. No SBOM published.
25. No signed releases.
26. No reproducible builds enforced.
27. No database migration lint.
28. No stale feature branch detector.
29. No codified architecture decision records enforced.
30. No onboarding checklist per office automated.
31. No training environment refresh cadence.
32. No broker acceptance sign-off artifact.
33. No pilot exit criteria numeric.
34. No pricing enforcement in product.
35. No license entitlement check.
36. No seat counting.
37. No org hierarchy parent-child offices.
38. No franchise branding isolation beyond client pack.
39. No comparative analytics between offices trustworthy.
40. No PII classification tags on fields.
41. No retention TTL automation.
42. No log PII scrubber guaranteed.
43. No secure SDLC gates.
44. No third-party subprocessors list maintained in app.
45. No DPAs tracked.
46. No incident response tabletop outcomes recorded.
47. No cyber insurance alignment.
48. No vendor risk reviews quarterly.
49. No accessibility WCAG audit.
50. No localization coverage beyond zh snippets partial.

---

## PHASE 3 — TABLETOP + CHAOS SIMULATIONS (abbreviated outcomes)

| Scenario | Break / symptom | Mitigation posture |
|----------|-----------------|-------------------|
| Wrong-office append | Mutation denied when enforcement on + stamped case; silent wrong data if enforcement off | Keep enforcement aligned with pilot contract |
| Leaked broker key | Anyone with key passes perimeter | Rotate keys; separate intake vs support; monitor logs |
| Stale session binding | Cleared on org shift; else wrong case reopened | Rely on route logs + session asserted org |
| Office migration | Historical rows retain old org unless scripted update | Migration playbook + list strictness choice |
| Replay mismatch | Different schema epoch / FE grouping | Manifest + case-head lineage |
| Support escalation confusion | Missing trace id | Always copy `request_trace_id` + manifest |
| Analytics bleed | Cross-office sessions mixed in buffer | Org filter on dashboard (this sprint); accept historic blind spot |
| Intake/support abuse | Flood / scrape | Rate limits future; secrets today |
| Missing org headers | 403 list under enforcement; unstamped legacy visibility varies | Document broker FE requirement |
| Mixed legacy unstamped rows | Surprise inclusion/exclusion | `UNIFIED_INTAKE_OFFICE_LIST_STRICT_NO_LEGACY` |
| Deployment drift | Health operator_warnings | Fix env contradictions |
| Wrong env deploy | DEMO prod contradiction warnings | trial_readiness + `/health` |
| PG/JSON disagreement | `UNIFIED_INTAKE_DB_OBS` logs | Strict fallback policy |
| Anonymous intake exposure | Default without intake key | Set `UNIFIED_INTAKE_INTAKE_API_KEY` in pilot |
| Weak shared secret | Short key warnings | 24+ chars |
| Support replay disputes | Non-WORM export | Honest semantics strings |
| Angry broker replay review | Emotional + data mismatch | case-head office hint check |
| Support handoff failure | Incomplete manifest | deployment-manifest curl |
| Clipboard case leakage | Human ops issue | Train against |
| Browser multi-office confusion | Cached tabs | Session org shift clearing |
| Rollback under office enforcement | Flag unset restores legacy shared queue | Document rollback |
| Rate-limit absence abuse | Noise | Future throttle |
| Cloud Run revision mismatch | traffic not latest | Use revision labels |
| Manifest mismatch | Cached response | Cache-Control discipline operator-side |
| Schema epoch mismatch | FE/API skew | Align deploy bundles |
| Support operator misunderstanding | Wrong conclusions | Training on tenant_truth semantics |
| Onboarding chaos | Headers missing | Checklist |
| Founder/support overload | Latency + ticket volume | Automation incremental only |

---

## WHAT_BREAKS_AT_30_OFFICES

Operational coordination (keys, headers, client packs), analytics interpretability (single-process buffer), manual onboarding throughput, increased probability of **org spoofing** if enforcement inconsistent, support templates outdated, DNS/CORS fanout mistakes.

---

## WHAT_BREAKS_AT_100_OFFICES

Linear founder support cost, secret rotation choreography, absence of **real** identity federation noticeable, dashboard/filter mismatch complaints, PG operational limits without pooling tuning, duplicate configuration drift across franchises.

---

## WHAT_BREAKS_AT_ENTERPRISE

Sales expectations for SSO/RBAC/RLS/compliance automation collide with actual perimeter-key + asserted-header model; procurement blocks; field-level security demands; multi-region HA expectations; formal SLA penalties.

---

## PHASE 4 — IMPLEMENTED CHANGES (this sprint)

1. **Funnel lineage:** `client_asserted_org_id` propagated through `emit_session_milestones`, `emit_case_created_milestone`, `emit_funnel_from_triage_result` (`triage_funnel.py` + `inbox_triage.py` call sites; append path uses request org).
2. **Analytics scope:** `/api/analytics/dashboard` filters by `X-Org-Id` / middleware state; returns `dashboard_scope` metadata (`analytics_dashboard.py`). Tests: `tests/test_analytics_dashboard_scope.py`.
3. **Deployment warning:** duplicate intake/support API keys flagged (`deployment_profile.py`). Test extended `tests/test_deployment_profile.py`.
4. **Support honesty:** `support_case_head` adds `support_office_hint_check` when header org differs from case `asserted_org_id` (`inbox_triage.py`).
5. **Env doc pointer:** `configs/demo.env.example` references this SSOT.

---

## PHASE 5 — VALIDATION LOG (this execution)

| Check | Result |
|-------|--------|
| `python -m compileall` (changed modules) | PASS |
| `pytest tests/` | PASS (1 skipped overall suite) |
| `pytest` targeted analytics/deployment/office/gates | PASS |
| `scripts/guardrail_inbox_triage.sh` | PASS |
| `scripts/run_full_regression.py` | PASS (`http_p95_ms` ~3916 < 6000) |
| `scripts/trial_readiness_check.sh` | PASS |
| `scripts/support_deployment_manifest_smoke.py` | **NOT RUN** (no local API on 8001; connection refused) |
| `cd ui && npm run build` | **FAIL** — Node **20.18.2** on PATH; Vite **7** requires **>=20.19**; `ERR_REQUIRE_ESM` loading `vite.config.ts` |
| `npx madge --circular … src` (ui) | PASS |

**Node/Vite honesty:** Upgrade Node (20.19+ or 22.x per `ui/package.json`) **or** prepend PATH with approved Node before `npm run build`, matching other sprint docs.

---

## SELF_CRITIQUE_REPORT_V9

1. **Fake identity:** Tenant authority fields exist structurally but are always null — good honesty; still easy for sales to misread headers as trust.
2. **Fake tenancy:** Postgres rows are not RLS-isolated; enforcement is optional middleware policy.
3. **Fake replay:** Manifest is not signed; git SHA may be absent in container.
4. **Fake support narrative:** “Export” endpoints are minimal JSON snapshots, not forensic bundles.
5. **Fake deployment assumptions:** Health `ok` does not prove correct env vars on **all** instances behind LB.
6. **Fake analytics assumptions:** Dashboard is not census-accurate cross replicas; filtered view hides legacy unscoped events.
7. **Support illusions:** case-head mismatch hint helps but does not prevent deliberate spoofed headers.
8. **Office continuity illusions:** Clearing binding on org shift prevents stale reuse but can surprise brokers during demos.
9. **Founder dependency:** Still central for rotations and env alignment — improved docs/warnings only modestly reduce chaos.
10. **Operational blind spots:** No production-grade rate limits documented as enforced here.
11. **Scaling illusions:** Org-filtered analytics does not imply multi-tenant SaaS billing readiness.
12. **Residual risk:** Same secret for intake+support collapses perimeter story — now warned, not blocked.

---

## PHASE 7 — CONVERGENCE

| Label | Meaning today |
|-------|----------------|
| **REAL** | Optional shared-secret perimeters; client-asserted org middleware; office stamping `asserted_org_id` / `office_owner_org_id`; PG/JSON settings matrix; deployment-manifest lineage; honest warning codes |
| **FAKE** | Enterprise IAM, RLS tenant isolation, authoritative tenant id, tamper-evident replay |
| **SAFE** | Rollback via unset env flags; small incremental metadata additions; tests passing |
| **UNSAFE** | Public URLs without secrets; prod-like mode without DB; enforcement on multi-instance without shared DB |
| **PILOT READY** | With secrets + DB + headers wired + founder runbooks followed |
| **ENTERPRISE UNSAFE** | SSO/RBAC/compliance expectations unmet |
| **SUPPORT SAFE** | When manifest + trace ids used; understanding limits of exports |
| **DEPLOYMENT SAFE** | Scripted deploy from SSOT env file + Secret Manager discipline |
| **STILL DANGEROUS** | Operator misconfiguration, social engineering key theft, LLM abuse cost |

---

## SPRINT-OWNED FILES (touch list for this sprint authority)

- `docs/sprints/SCOPED_BROKER_IDENTITY_OFFICE_OPERATIONAL_SAFETY_SPRINT.md` (this file)
- `services/fiqa_api/analytics/triage_funnel.py`
- `services/fiqa_api/routes/analytics_dashboard.py`
- `services/fiqa_api/deployment_profile.py`
- `services/fiqa_api/routes/inbox_triage.py` (support hint + funnel wiring)
- `configs/demo.env.example` (SSOT pointer)
- `tests/test_minimal_analytics.py`
- `tests/test_deployment_profile.py`
- `tests/test_analytics_dashboard_scope.py`

---

## PHASE 8 — FINAL OUTPUT (mirror for operators)

1. **Branch:** `sprint/scoped-broker-identity-office-operational-safety`
2. **Sprint-owned files:** listed above (plus pre-existing branch WIP noted in Phase 0)
3. **Implemented:** funnel org metadata; dashboard office filter + scope metadata; duplicate-key warning; support case-head office mismatch hint; demo.env SSOT pointer; tests
4. **More real:** analytics office labeling; deployment contradiction visibility; support replay handoff hints
5. **Still fake:** enterprise identity, RLS, authoritative tenancy, signed replay
6. **Biggest broker identity truths:** shared secrets ≠ users; `X-Org-Id` is assertion not proof
7. **Biggest office truths:** stamping + optional enforcement + session org-shift clearing
8. **Biggest support truths:** manifest/case-head are operational probes not compliance exports
9. **Biggest replay truths:** epoch + manifest version + git best-effort only
10. **Biggest deployment truths:** operator_warnings surface contradictions; identity labels env-injected
11. **Biggest analytics truths:** in-memory buffer; single-instance; filtered view partial historically
12. **Biggest operational truths:** founder still integrates env+CORS+secrets; docs must stay aligned
13. **Biggest remaining risks:** anonymous surfaces if unset keys; org spoof when enforcement off
14. **Biggest founder dependencies:** deploy honesty, rotation, pilot interpretation
15. **30 offices:** onboarding + header drift + analytics noise
16. **100 offices:** linear support + rotation + expectation management
17. **Enterprise sales:** IAM/compliance expectation clash
18. **Best 10x leverage:** real broker-scoped API tokens mapped to office stamp server-side (future small step, not SSO theater)
19. **Best next sprint:** rate limiting + structured audit sink behind feature flag
20. **Best 3-month roadmap:** DB-primary everywhere pilot; minimal rate limits; rotation runbook automation; optional read-only operator UI for manifest
21. **Should NOT build yet:** SSO portal, RBAC UI, billing engine, workflow builder
22. **FINAL_ONE_LINE:** Honest perimeter keys plus client-asserted office stamps and manifest lineage beat fake enterprise tenancy until real broker-scoped tokens arrive.

