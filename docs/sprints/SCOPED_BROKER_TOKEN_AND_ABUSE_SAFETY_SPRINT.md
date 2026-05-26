# Scoped Broker Token + Minimal Abuse Safety Sprint

**Authority:** This document is the **single source of truth** for this sprint.  
**Date:** 2026-05-11  
**Philosophy:** Paid pilot survivability with **fewer lies** — not enterprise IAM theater.

---

## Phase 0 — Git + inventory + truth

### Git snapshot (recorded at sprint execution)

| Item | Value |
|------|--------|
| **Branch** | `sprint/scoped-broker-identity-office-operational-safety` |
| **Dirty tree** | Yes — extensive modified tracked files + many untracked docs/results + new security/tests from convergent work |
| **Stashes** | Multiple (`stash@{0}` … `stash@{15}+`) — pre-merge WIP from other lines of work |
| **WIP coexistence risks** | Same branch mixes office-enforcement, persistence, analytics, UI contract edits; merging without re-reading `deployment_profile.INTAKE_SCHEMA_EPOCH` and guardrails risks silent drift; duplicate sprint markdown filenames elsewhere — **this file** supersedes narrative for *this* sprint scope |

### Inventory — what actually exists (no exaggeration)

| Topic | Truth |
|-------|--------|
| **Intake API key** | Optional env `UNIFIED_INTAKE_INTAKE_API_KEY`. When set, `IntakeApiPerimeterMiddleware` requires `X-Unified-Intake-Api-Key` or `Authorization: Bearer` on `/api/inbox/*` except `/api/inbox/support/*` and WeChat OAuth callback GET. When unset, inbox is **anonymous_ok** (demo default). Not per-broker identity — one shared secret for the deployment. |
| **Support API key** | Optional `UNIFIED_INTAKE_SUPPORT_API_KEY`; gates `/api/inbox/support/*` only. Same honesty model: possession ≠ tenancy. |
| **`X-Org-Id` semantics** | Copied to `request.state.client_asserted_org_id` by `IntakeClientAssertionMiddleware`. Documented as **client assertion**, not IAM (`request_identity.py`, `support_export_gate`, tenant truth). Spoofable by any caller who can hit the URL. |
| **Office ownership enforcement** | Opt-in `UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP`: stamped cases require matching `X-Org-Id` on scoped routes; list route behavior documented in `case_office_access.py`. Still not cryptography — compares asserted header to persisted hint. |
| **Analytics scope** | Funnel / minimal events attach org as **hint** when present; wrong header poisons attribution, not isolation. |
| **Request lineage** | `http_request_lineage` → `request_trace_id` from request-id middleware; surfaced on manifest/case-head — correlation only. |
| **Deployment manifest** | `GET /api/inbox/support/deployment-manifest` (+ `/health` deployment_profile): persistence snapshot, auth posture, replay lineage, schema epoch — **no PII by design**. |
| **Health posture** | `/health` exposes persistence mode, product-only flags, operator warnings, tenant truth shell. |
| **Abuse surfaces** | Anonymous triage when keys unset; LLM cost per POST; shared intake key rotatable only by redeploy; no per-user quotas unless enabled; IP spoofing on `X-Forwarded-For` if proxies misconfigured. |
| **Replay truth** | `replay_lineage` + `support_export_manifest_version` — **handoff metadata**, not legal hold or byte-identical replay guarantees. |

---

## Phase 1 — Deep discovery (TOP lists)

### TOP_30_AUTH_ILLUSIONS

1. Treating `X-Org-Id` as tenant proof.  
2. Treating `client_id` as authentication.  
3. Treating intake API key as “broker login.”  
4. Treating support key as RBAC.  
5. Assuming HTTPS implies honest org headers.  
6. Assuming Cloud Run URL secrecy equals auth.  
7. Assuming case IDs are unguessable.  
8. Assuming Postgres URL implies RLS.  
9. Assuming “product only” mode deletes all attack paths.  
10. Assuming CORS blocks scripted abuse (server-side callers ignore CORS).  
11. Assuming Bearer header proves human broker.  
12. Assuming rotation story exists beyond redeploy + client updates.  
13. Assuming demo env vars cannot ship to prod.  
14. Assuming `tenant_id_authoritative` non-null today (it is **always** null until real issuance exists).  
15. Assuming session persistence implies secure sessions.  
16. Assuming WeChat binding state secret defaults are safe (dev fallbacks exist — see code paths).  
17. Assuming analytics partitions are authoritative billing facts.  
18. Assuming “office enforcement” stops cross-office attacker with shared DB + guessed IDs.  
19. Assuming attachment paths cannot collide across offices on shared disk.  
20. Assuming append routes cannot be abused without intake key when key unset.  
21. Assuming multi-instance JSON authority is safe.  
22. Assuming `deployment-manifest` proves compliance.  
23. Assuming git SHA on manifest proves running code (env labels are best-effort).  
24. Assuming founders manually verify every pilot URL pair (Vercel ↔ Cloud Run).  
25. Assuming LLM off removes abuse (CPU/rule paths still callable).  
26. Assuming rate limits without keys stop determined attackers (new IPs, botnets).  
27. Assuming office list filtering scales (bounded slices — not OLTP tenancy).  
28. Assuming “anonymous_ok” is acceptable on public internet without conscious choice.  
29. Assuming stakeholders read runbooks before trials.  
30. Assuming this sprint “solves identity.”

### TOP_30_ABUSE_PATHS

1. Drive-by `POST /api/inbox/triage` when intake key unset.  
2. Scraping `GET /api/inbox/cases` when open.  
3. Spamming triage to burn OpenAI budget.  
4. Parallel pilots on one DB without physical isolation.  
5. Shared intake key leaked in Slack → entire perimeter gone.  
6. Replay of captured Bearer token until rotate.  
7. Guessing sequential case identifiers where entropy weak.  
8. Upload / OCR paths invoked repeatedly if exposed without throttle.  
9. Confusing support operators into pasting support URLs publicly.  
10. Manifest reconnaissance when support key unset.  
11. Spoofed `X-Org-Id` → polluted analytics + operator confusion.  
12. Wrong office browser profile → wrong binding unless enforcement on + FE discipline.  
13. Reverse proxy stripping org header → silent mismatch.  
14. Customer forwarding triage link with embedded secrets (if ever introduced in FE).  
15. Founder laptop `.env` copied to demo → prod parity lies.  
16. Dual-write JSON/PG inconsistencies misleading replay.  
17. In-memory sessions flag in prod-like mode → surprise data loss.  
18. Autotuner / lab routes in platform-full deployments.  
19. Job board / ecommerce routers surfacing in non-product profiles by mis-config.  
20. Rate limit bypass via IPv6 rotation (if enabled naïvely).  
21. Rate limit friend-fire on NATted offices (single IP many brokers).  
22. Append endpoint abuse on open deployments.  
23. CRM export future hooks trusting headers alone.  
24. Attachment download guessing without signed URLs.  
25. LLM prompt stuffing via long customer text.  
26. Concurrent edits from two tabs erasing workflow state (logical abuse).  
27. Operator scripts without `X-Org-Id` creating unstamped legacy rows.  
28. Migration rows missing `asserted_org_id` hidden or exposed depending on strict list flags.  
29. Third-party scanners hammering `/health` and warm paths.  
30. Insider forwarding deployment-manifest to competitor.

### TOP_30_OPERATIONAL_FAILURES

1. ENV=prod with DEMO_MODE on.  
2. Missing `ALLOWED_ORIGINS` → blank UI “Network Error.”  
3. Qdrant/embed warmup causing false 503 narratives.  
4. Secret Manager deploy mismatch wiping GSM-bound vars.  
5. Node version drift breaking UI build pipelines.  
6. Founder-dependent manual URL verification.  
7. Support tickets without manifest snapshot.  
8. Assuming JSON case files are backup authority during PG-primary.  
9. Rotating only Qdrant key but not redeploying FE env.  
10. Partial office enforcement rollout (FE forgets header).  
11. Multi-instance without DB for sessions.  
12. Logging PII in verbose modes shipped accidentally.  
13. Trial checklist skipped under time pressure.  
14. Mixing Chen vs SoCal packs in marketing vs runtime `CLIENT_ID`.  
15. Manual `gcloud` patches overwritten by next deploy script.  
16. Min instances cost shock vs cold-start complaints.  
17. Langfuse keys omitted → blind observability assumed anyway.  
18. Attachment disk fills → intake failures.  
19. Postgres disk auto-grow surprises.  
20. Time zone inconsistencies in case timestamps in tickets.  
21. Duplicate alarms on embedding warming vs real outages.  
22. On-call playbook references deprecated `/ops/*`.  
23. Case-head interpreted as full replay when only head fields returned.  
24. Operators confuse intake vs support keys.  
25. Operators use same secret for both keys.  
26. WeChat redirect URI typo discovered Friday 5pm PT.  
27. Customer sends multi-MB images → latency SLA breach perceived as “AI down.”  
28. Partial locale strings shipped → trust erosion.  
29. Benchmark regressions discovered mid-trial.  
30. No named owner for secret rotation calendar.

### TOP_30_PILOT_SURVIVABILITY_RISKS

1. Selling multi-tenant isolation today.  
2. Promising SOC2 / HIPAA alignment from headers.  
3. Billing without durable metering keyed to honest tenant IDs.  
4. Pilot thinks office list is legally confidential partition.  
5. Founder-only deploy knowledge.  
6. Single shared intake key across unrelated brokers.  
7. Accidental anonymous support manifest exposure.  
8. Customer-visible errors leaking stack traces.  
9. Assist layer variance breaking scripted demos.  
10. OCR costs unpredictable.  
11. Cross-office case accidentally opened at front desk.  
12. Mobile Safari quirks on workbench.  
13. Language mismatch eroding “Unified” promise.  
14. Attachment malware scanning absent — buyer assumes antivirus.  
15. Data residency promises vs default OpenAI routing.  
16. Lack of explicit incident comms template.  
17. Pilot compares to Salesforce parity mentally.  
18. Hidden platform routes erode “product-only” trust if discovered.  
19. Slow chaos regressions skipped before investor demo.  
20. Trial users hit cold starts during live meeting.  
21. Founder interprets analytics as ground truth revenue attribution.  
22. Broker staff training absent on org header discipline.  
23. Export / audit expectations beyond code capability.  
24. Pilot expects SSO “next week.”  
25. Concurrent editing collisions blamed on “AI bugs.”  
26. Vendor lock-in fears without honest portability notes.  
27. Pricing tied to per-seat assumptions — product is per-deployment secret + usage.  
28. Lack of named security contact in contract vs reality (founder cell).  
29. Undocumented rollback turns incidents into improvisational theater.  
30. Narrative drift between sales deck and `/health` JSON.

### TOP_30_FAKE_SAAS_PATTERNS

1. Calling optional header “tenant.”  
2. Calling shared secret “broker identity.”  
3. Calling manifest “compliance pack.”  
4. Calling git SHA “tamper evident.”  
5. Calling office filter “RLS.”  
6. Calling analytics “billing ledger.”  
7. Calling demo mode “staging parity.”  
8. Calling JSON dual-write “HA.”  
9. Calling LLM guardrails “deterministic compliance.”  
10. Calling product-only flag “certified perimeter.”  
11. Calling case ID “customer PII boundary.”  
12. Calling UI pack switch “multi-tenant provisioning.”  
13. Calling manual deploy checklist “GitOps.”  
14. Calling founder manual replay “audit trail.”  
15. Calling attachment folder “WORM storage.”  
16. Calling rate limit “DDoS protection.”  
17. Calling office expectation list “authorization.”  
18. CallingBearer header “session.”  
19. Calling schema epoch “migration id.”  
20. Calling support export “data portability API.”  
21. Calling triage output “underwriting decision.”  
22. Calling workbench “CRM replacement.”  
23. Calling inbox triage “sentiment analysis SKU.”  
24. Calling Cloud Run “private VPC magic.”  
25. Calling minimal events “product analytics suite.”  
26. Calling guardrail scripts “continuous verification.”  
27. Calling chaos regression “load testing.”  
28. Calling operational warnings “SOC alarms.”  
29. Calling office mismatch hint “403 enforcement.”  
30. Calling this sprint “IAM phase 1.”

### TOP_30_SUPPORT_FAILURES

1. Ticket lacks manifest JSON.  
2. Wrong key pasted into curl templates.  
3. Interpreting replay lineage as full transcript export.  
4. Assuming case-head includes messages.  
5. Missing `X-Org-Id` context when enforcement on.  
6. Confusion between intake vs support endpoints.  
7. Expecting timestamp parity JSON vs PG without checking mode.  
8. Assuming FE build SHA equals BE SHA.  
9. Over-trusting customer-provided org names vs asserted slug.  
10. Escalating without `/health` persistence snapshot.  
11. Assuming 503 always means outage not warmup.  
12. Assuming demo scripts work against prod keys.  
13. Sharing support key in Zoom chat.  
14. Rotating intake key without coordinating FE embed locations.  
15. Language barrier triage labeled “model regression.”  
16. Assuming OCR stub vs Vision parity across envs.  
17. Assuming guardrail PASS implies prod telemetry green.  
18. Assuming attachment IDs are opaque UUIDs always.  
19. Assuming List pagination equals SQL OFFSET stability under churn.  
20. Assuming schema epoch bump implies auto DB migrate.  
21. Mis-reading `tenant_id_authoritative=null` as bug.  
22. Expecting SOC2 answers from FastAPI JSON.  
23. Assuming rate-limit 429 means “ban” not throttle.  
24. Assuming office expectation header blocks mismatched traffic.  
25. Assuming founder inbox is ticketing system.  
26. Assuming Linear/Jira integration exists because startup norm.  
27. Assuming PII scrubbing in logs by default.  
28. Assuming SLA clock starts without written measurement method.  
29. Assuming customer success owns rotation calendar (nobody owns).  
30. Assuming “PASS trial readiness” equals legal readiness.

### TOP_30_FOUNDER_DEPENDENCIES

1. Manual Cloud Run ↔ Vercel URL pairing.  
2. Secret placement discipline (GSM vs plaintext env).  
3. Interpretation of operator_warnings lists.  
4. Decision to enable intake/support keys per pilot.  
5. Decision to enable office enforcement per pilot.  
6. Escalation bridge when analytics lies vs reality.  
7. Narrative control when buyer asks for SSO timeline honesty.  
8. Hands-on replay of weird cases.  
9. Chooses NODE version for CI/local parity.  
10. Runs or delegates `run_full_regression.py` before big moments.  
11. Chooses DEMO_MODE posture vs prod honesty.  
12. Maintains client pack truth (`configs/clients`).  
13. Owns WeChat credential lifecycle.  
14. Owns Qdrant collection naming discipline.  
15. Owns DB backup verification story (if any).  
16. Approves marketing claims vs `/health` facts.  
17. Personal laptop still has canonical `.env` fragments.  
18. Answers security questionnaires from first principles.  
19. Decides when to eat LLM cost spike vs throttle UX hit.  
20. Bridges broker IT pushing IP allowlists (product gap).  
21. Performs incident comms when manifest exposes uncomfortable truths.  
22. Validates trial checklist items others rubber-stamp.  
23. Manual deletion / GDPR handling processes absent automation.  
24. Broker onboarding copy still founder-authored.  
25. Pricing disputes fallback to founder calendar.  
26. Chooses to postpone true tenant issuance honestly vs sales pressure.  
27. Sleep debt → mis-deploy risk windows.  
28. Investor demo narrative vs engineering blunt JSON coexistence.  
29. Founder intuition on “good enough” perimeter per pilot tier.  
30. Final say when engineering wants “just one more fake RBAC screen.”

---

## Phase 2 — Design convergence (minimal real improvements)

**Goals delivered in code + docs (rollback-safe):**

1. **Broker-scoped token truth** — Explicit JSON: intake/support surfaces remain **shared secrets**, not identities; `pilot_token_scope_registry` names env-driven labels only.  
2. **Office-scoped token hints** — Optional `UNIFIED_INTAKE_EXPECTED_OFFICE_SLUGS` drives honest telemetry header on triage responses + manifest visibility — **not** enforcement.  
3. **Minimal token registry shape** — `token_scope_registry_dict()` with `registry_version`, semantics string, sorted slug list, deploy broker label.  
4. **Minimal abuse protection** — Optional `UNIFIED_INTAKE_TRIAGE_POST_MAX_PER_MINUTE_PER_IP` sliding window on **POST** `/api/inbox/triage` only; explicit `429` body semantics.  
5. **Minimal rotation story** — Unchanged mechanically (rotate env secrets + redeploy + redistribute FE embeds); documented as such — **no** vault UI.  
6. **Minimal replay lineage** — `replay_lineage.token_scope_registry` + manifest top-level keys; `support_export_v3` version bump.  
7. **Minimal support posture** — `support_deployment_manifest_smoke.py` asserts `token_scope_registry` presence on `/health` + manifest.  
8. **Minimal deployment honesty** — `INTAKE_SCHEMA_EPOCH` bumped; operator warning when expectation list set without intake key in prod-like mode.

**Explicitly NOT built:** OAuth, SAML, Cognito, Auth0, RBAC UI, user tables, large migrations, row-level security.

---

## Phase 3 — Implementation summary

| Area | Change |
|------|--------|
| **New** | `services/fiqa_api/security/token_scope_posture.py` — registry + operator warnings hook |
| **New** | `services/fiqa_api/security/pilot_intake_middleware.py` — office expectation header + triage rate limit |
| **Updated** | `app_main.py` — middleware ordering; CORS expose header; `/health` token registry |
| **Updated** | `intake_api_gate.py` — nested `pilot_token_scope_registry` |
| **Updated** | `deployment_profile.py` — schema epoch; merged token-scope warnings |
| **Updated** | `routes/inbox_triage.py` — manifest + replay lineage fields; `support_export_v3` |
| **Updated** | `configs/demo.env.example` — documented new env vars |
| **Updated** | `scripts/support_deployment_manifest_smoke.py` — asserts registry dict |
| **Tests** | `tests/test_token_scope_and_rate_limit.py`, extensions to deployment + intake gate tests |

---

## Phase 4 — Tabletop simulations + outcomes

| Scenario | What happens | More real / still fake |
|----------|----------------|------------------------|
| **Leaked broker key** | Attacker passes perimeter until rotate; org hints irrelevant | Real: single secret blast radius; Fake: “broker scoped” identity |
| **Wrong office key** | N/A — keys aren’t office-scoped; enforcement uses `X-Org-Id` vs persisted hint when flag on | Still fake office-bound crypto keys |
| **No org header** | Analytics/marked absent; enforcement routes may 403 when required; expectation header `absent_v1` if list configured | Real: explicit absent signal |
| **Spoofed org header** | Accepted as client assertion; may poison analytics; enforcement compares to stamp when enabled — **not** crypto proof | Still fake tenancy |
| **Support confusion** | Wrong key → 401 on support routes when gated | Real separation of surfaces |
| **Replay confusion** | Manifest shows epoch + lineage; not full transcripts | Real metadata; fake legal-grade replay |
| **Multiple brokers sharing key** | Indistinguishable at HTTP layer | Real honest limitation |
| **One broker attacking another office** | Without enforcement: possible cross-read depending on routes; with enforcement: reduces casual mistakes, not APT | Partial real boundary |
| **Deployment misconfiguration** | `/health` operator_warnings surface contradictions | Real drift signals |
| **Noisy pilot customer** | Optional IP throttle may 429; NAT risk | Real coarse cushion; fake fairness guarantee |

### Automated validations (this sprint run)

| Check | Result |
|-------|--------|
| `python3 -m compileall` (targeted) | PASS |
| `pytest` (full suite) | PASS (`~180s`, 1 skipped) |
| `scripts/guardrail_inbox_triage.sh` | PASS |
| `scripts/run_full_regression.py` | PASS (`http_p95_ms` ≈ 4587 &lt; 6000) |
| `scripts/trial_readiness_check.sh` | PASS |
| `cd ui && npx madge --circular --extensions ts,tsx src` | PASS (no cycles) |
| `cd ui && npm run build` (direct shell Node **20.18.2**) | **FAIL** — Vite requires Node **20.19+** or **22.12+**; `ERR_REQUIRE_ESM` loading vite config |
| **Note** | `trial_readiness_check.sh` reported UI build OK — likely **different PATH / Node** than bare agent shell; treat Node parity as **operational dependency**, not assumed |

---

## Phase 5 — `SELF_CRITIQUE_REPORT_V10`

1. **Illusions smuggled** — Registry naming could be misread as “auth registry”; semantics strings fight marketing gloss only if operators read them.  
2. **Half-measures** — IP rate limit is per-process memory — useless cross-replica without Redis; acceptable only as honest coarse default.  
3. **Unsafe assumptions** — Trusting `X-Forwarded-For` first hop — misconfigured LB breaks fairness or enables spoofing.  
4. **Hidden scaling cliffs** — 30–100 offices on one deployment without composite DB keys + real IAM → attribution debt and support chaos.  
5. **Operational lies** — “PASS trial readiness” can coexist with Node 20.18 local build failure — environment truth fragmentation.  
6. **Support pain** — Another manifest field → good/bad: richer tickets vs parsing drift (`support_export_v3`).  
7. **Replay weaknesses** — Still no signed export chain; customer narrative can diverge from persisted stub.  
8. **Abuse gaps** — GET flood on non-triage routes; LLM token economics not capped by this throttle alone.  
9. **Token weaknesses** — Shared secrets rot as blobs — no audience claims, no binding to office slug.  
10. **Founder dependencies** — All scary paths still route through human discipline on env + explanation discipline on sales calls.

---

## Phase 6 — Convergence

| Question | Answer |
|----------|--------|
| **What became more real** | Named pilot token registry JSON; optional triage throttle; explicit expectation header semantics; manifest/smoke checks; prod-like warning when expectations exist without intake perimeter |
| **What is still fake** | Per-broker cryptographic identity, SSO, tenant isolation, durable global rate limit, tamper-evident replay |
| **Breaks @ 30 offices** | Operational support volume; analytics attribution mess; NAT throttle collisions; manual secret distribution |
| **Breaks @ 100 offices** | Single-deploy mental model; list endpoints; lack of provisioning API; cost unpredictability |
| **Breaks @ enterprise sales** | IAM/SCIM/SOC2 expectations vs actual shared-secret model |
| **Best next 10x leverage** | Server-issued office-bound tokens **or** signed embed cookies — still minimal JWT/HMAC, not full IAM |
| **Best next sprint** | **Durable rate limit + usage metering** (Redis or edge) tied to deployment id + honest headers |
| **Best 3-month roadmap** | (1) Real tenant issuance pointer in DB nullable column lifecycle (2) Composite case keys (3) Structured audit export with signatures — each as explicit honesty sprint |
| **Do NOT build yet** | RBAC UI, SAML, multi-tenant billing plumbing, customer-facing IAM screens |

---

## Phase 7 — Validation log (commands)

```bash
python3 -m compileall -q services/fiqa_api/security ...
PYTHONPATH=. pytest -q
bash scripts/guardrail_inbox_triage.sh
PYTHONPATH=. python3 scripts/run_full_regression.py
bash scripts/trial_readiness_check.sh
cd ui && npx --yes madge --circular --extensions ts,tsx src
cd ui && npm run build   # fails on Node 20.18.2 in this environment — upgrade PATH
```

---

## Phase 8 — Final output (verbatim summary)

1. **Branch:** `sprint/scoped-broker-identity-office-operational-safety`  
2. **Sprint-owned files:** This doc; `token_scope_posture.py`; `pilot_intake_middleware.py`; `tests/test_token_scope_and_rate_limit.py`; touched `app_main.py`, `intake_api_gate.py`, `deployment_profile.py`, `inbox_triage.py`, `demo.env.example`, `support_deployment_manifest_smoke.py`, `test_deployment_profile.py`, `test_intake_api_gate.py`  
3. **Implemented:** Pilot token scope registry; optional office-expectation response header on triage POST; optional per-IP triage POST rate limit; manifest/replay/health wiring; operator warnings; `support_export_v3` + schema epoch bump; smoke script asserts  
4. **More real:** Explicit honesty JSON for token semantics; coarse abuse throttle hook; expectation telemetry; warnings when operators configure expectations without perimeter  
5. **Still fake:** Broker-grade identity, cryptographic org binding, multi-tenant isolation, cross replica rate limits  
6. **Biggest auth truths:** Shared secrets gate surfaces; headers are assertions; `tenant_id_authoritative` is null by design today  
7. **Biggest abuse truths:** Open deployments + LLM = cost attack; IP throttle is optional and process-local  
8. **Biggest support truths:** Manifest version bumped — parsers must tolerate `support_export_v3`; keys must stay separated  
9. **Biggest deployment truths:** Node major affects UI build; `/health` warnings beat silent drift  
10. **Biggest replay truths:** Metadata-only lineage; not chain-of-custody  
11. **Biggest remaining risks:** Shared keys, spoofed org, founder-dependent env discipline, NAT + throttle  
12. **Biggest founder dependencies:** Choosing when keys/enforcement/throttle toggle per pilot + explaining limits honestly  
13. **30-office breaker:** Support load + header discipline + secret distribution  
14. **100-office breaker:** Architecture still single logical tenant without data-plane partitioning story  
15. **Enterprise sales breaker:** IAM/compliance expectations vs actual model  
16. **Best next 10x leverage:** Signed office-scoped secondary token for browser embeds (minimal crypto)  
17. **Best next sprint:** Durable metering + rate limiting behind proxy trust boundaries  
18. **3-month roadmap:** Tenant issuance pointer → composite keys → signed exports (explicit honesty milestones)  
19. **Should NOT build yet:** SAML/OAuth/RBAC theater  
20. **FINAL_ONE_LINE:** **We tightened the pilot perimeter with honest labels, optional throttles, and manifest truth — not with fake enterprise IAM.**
