# Minimal Real SaaS Foundation Sprint — SSOT

**Document role:** Single source of truth for moving Unified Intake / SearchForge from an honest pilot monolith toward a **minimal real SaaS foundation** without fake enterprise surface area.

**Last updated:** 2026-05-08

---

## Objective

Create the **smallest set of real foundations** needed before:

- ~30 paying broker offices,
- path to ~100-office operational load,
- support/operator scaling without heroic founder intervention,
- **trust** grounded in operational honesty (not compliance theater).

Success is **convergence and honesty**, not feature count.

---

## Non-goals (explicit)

- More AI cleverness, new verticals, enterprise SSO, Stripe billing.
- Fake multi-tenant dashboards, premature RBAC UI, giant IAM.
- Rewriting triage core logic in this sprint.
- Claiming RLS, SOC2, HIPAA, or immutable legal replay where not implemented.

---

## Current architecture truth

| Layer | Truth |
|-------|--------|
| **Runtime** | FastAPI monolith (`services/fiqa_api/app_main.py`): middleware stack (CORS outermost → RequestID → `IntakeClientAssertionMiddleware` → logging → ops deprecation → error handler → routes). |
| **Unified Intake API** | Router `services/fiqa_api/routes/inbox_triage.py` under `/api/inbox/*` (triage, sessions, cases, WeChat binding hooks, Role C replay helpers, **support manifest + case-head**). |
| **Product-only profile** | `UNIFIED_INTAKE_PRODUCT_ONLY=1` gates **included routers** to inbox + analytics + health/Qdrant probes; platform/lab routers omitted; `register_platform_inline_routes` not called (`deployment_profile.py`). |
| **Persistence** | Cases: JSON files by default; Postgres **optional** behind `SERVICE_RECORD_DATABASE_URL` / `DATABASE_URL` and flags (`service_record_settings.py`). Sessions: Postgres preferred; in-memory only if `UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS` (explicit). |
| **Vectors / readiness** | `/health` and `/ready` tie phase to embedding + Qdrant (`EMBED_READY`, `ensure_qdrant_connection`). |
| **Analytics** | `GET /api/analytics/dashboard` reads **in-memory** funnel buffer (`routes/analytics_dashboard.py`) — process-local, not multi-tenant BI. |

---

## Fake SaaS patterns (call them what they are)

1. **`X-Org-Id` as “tenant”** — Client assertion only; no server-issued tenant authority (`request_identity.py`).
2. **Anonymous `/api/inbox/support/*` by default** — Unless `UNIFIED_INTAKE_SUPPORT_API_KEY` is set (`support_export_gate.py`).
3. **Analytics dashboard** — Ephemeral buffer; not durable cross-instance metrics.
4. **`audit_export.record_intake_case_mutation`** — Forwards to `track_event` only; docstring says not for compliance claims (`audit_export.py`).
5. **CORS `*` / `ALLOW_ALL_CORS` defaults** — Convenient for demo; not tenant isolation.
6. **“Production mode” via `ENV=prod`** — Gates JSON case paths; still requires correct DB URL configuration separately.
7. **Role C “replay”** — Simulation/replay for testing flows; not court-grade reconstruction.
8. **Git SHA on manifest** — Build provenance, not tamper-evident signing.

---

## Current tenant truth

| Mechanism | Authoritative? | Notes |
|-----------|------------------|-------|
| `tenant_id_authoritative` | **Always `None`** today | Reserved for future JWT/API-key scope. |
| `client_asserted_org_id` | **Untrusted label** | From `X-Org-Id` via middleware; semantics fixed string in `IntakeTenantTruth`. |
| Case/session binding | **Application logic** | `client_id` from client pack / request body; not cryptographic office proof. |

---

## Current auth truth

| Surface | Mechanism |
|---------|-----------|
| Public triage | No end-user auth in scope (pilot). |
| Support export | Optional shared secret: header `X-Unified-Intake-Support-Key` or `Authorization: Bearer`. |
| Ops/platform routes | Product-only profile removes most; full profile exposes broad API (founder/demo hazard). |

---

## Current support truth

| Endpoint | Purpose | Auth |
|----------|---------|------|
| `GET /api/inbox/support/deployment-manifest` | Build SHA, persistence posture, schema epoch, auth posture, replay lineage tuple | Optional API key |
| `GET /api/inbox/support/case-head/{case_id}` | Minimal case metadata (no message bodies) | Optional API key |
| `GET /health` | Includes `deployment_profile` + persistence snapshot + auth posture + tenant truth | None |

**Gap:** No ticketing integration, no L1 runbook in-product, no signed export bundles (`audit_export.future_export_bundle_keys` is a checklist only).

---

## Replay truth

| Kind | What exists | What does not |
|------|-------------|----------------|
| Support handoff | Manifest version `support_export_v2`, `intake_schema_epoch`, triage wire label, **`replay_lineage`** object on manifest + case-head (2026-05-08) | Full turn replay export, WORM storage, legal chain-of-custody |
| Engineering | Scenario runners, guardrail scripts, chaos regression | Customer-facing “replay UI” as evidentiary system |

---

## Deployment truth

| Topic | Fact |
|-------|------|
| **Ports** | `PORT` / `MAIN_PORT`; demo docs emphasize **8001** local (`AGENTS.md`). |
| **Cloud Run** | `/healthz` may not reach app; `/api/healthz` and `/health/live` documented (`app_main.py`). |
| **Static frontend** | `frontend/dist` mounted when present; separate `ui/` Vite app for broker UI (`ui/package.json`, engines Node `>=20.19.0`; Vite 7 often needs **Node 22** on PATH per prior sprint notes). |
| **Env loading** | `.env.cloudrun` then `.env` at process start (`app_main.py`). |

---

## Operational truth

| Control | Location |
|---------|----------|
| Schema / contract label | `INTAKE_SCHEMA_EPOCH` in `deployment_profile.py`; surfaced on `/health` + manifest. |
| Persistence mode | `unified_intake_case_persistence_report()` — modes like `STRICT_PG_ONLY`, `PG_FIRST_BUT_NOT_STRICT`, `MIXED_STATE`, `UNKNOWN`. |
| Production-like risk visibility | `auth_posture.production_support_export_risk` when `ENV=prod` (or DB-primary flags path in `is_production_mode`) and support key unset; startup warning in `app_main.py` (2026-05-08). |

---

## Scaling truth

| Dimension | ~30 offices | ~100 offices |
|-----------|-------------|--------------|
| **Data plane** | JSON or mixed PG/JSON risks confusion; dual-write + multi-instance needs **DB-primary reads** or lost read-your-writes. | Postgres authority + connection pooling + backups becomes mandatory. |
| **Analytics** | In-memory funnel per instance — misleading if aggregated naively. | Requires external metrics store. |
| **Support** | Founder-led acceptable short-term. | Requires runbooks + keyed support surface + clear persistence truth. |

---

## Founder dependency map

1. Correct env matrix for each deployment (PG URL, dual-write, JSON fallback flags).
2. Interpreting `GET /health` persistence block when brokers report “lost case”.
3. Client pack / `client_id` correctness per office.
4. Qdrant / embedding outages (`/ready` 503 narrative).
5. Product-only vs full profile exposure decisions.
6. WeChat OAuth credentials and simulate flags.
7. Git SHA / manifest paste into tickets when debugging.
8. Chaos/regression interpretation (`run_full_regression.py`).
9. Escalation when PG vs JSON mismatch suspected (`check_add_car_service_record_consistency.py` guardrail path).
10. Manual cross-office confusion triage (no authoritative tenant).

---

## Support escalation map

| Tier | Can do today | Cannot do yet |
|------|----------------|----------------|
| **L1** | Read `/health`, manifest; verify support key posture; collect `X-Request-ID` | Cryptographically prove office identity |
| **L2** | `case-head` metadata; schema epoch for replay disputes | Full message-level signed export |
| **Engineering** | DB queries, JSON files on disk, logs | Automatic tenant-scoped log discovery without grep discipline |

---

## Risk matrix (abbrev.)

| ID | Risk | Severity | Mitigation state |
|----|------|----------|------------------|
| R1 | Anonymous support export on internet | High | Env secret optional; **prod warning + auth_posture flag** (2026-05-08) |
| R2 | `X-Org-Id` spoofing | Med | Documented as untrusted; no IAM |
| R3 | PG/JSON skew | High | Flags + guardrail scripts + persistence report |
| R4 | Per-instance analytics | Med | Document as non-durable |
| R5 | Full profile route leak | High | Product-only profile + discipline |
| R6 | Founder-only interpretation | Med | Manifest + epoch + replay_lineage tuple |

---

## Rollback strategy

- **Support posture:** Unset `UNIFIED_INTAKE_SUPPORT_API_KEY` restores anonymous pilot behavior (not recommended on public internet).
- **Code changes (2026-05-08):** Revert `replay_lineage` keys and `production_support_export_risk` / startup warning commit — behavior is additive JSON + logging.
- **Persistence:** Follow env rollback comments in `service_record_settings.py` (disable DB-primary, re-enable JSON).

---

## Validation gates

Required before declaring sprint round complete:

1. `python3 -m compileall -q services/fiqa_api tests`
2. `pytest tests/`
3. `bash scripts/guardrail_inbox_triage.sh`
4. `PYTHONPATH=. python3 scripts/run_full_regression.py`
5. `cd ui && npm run build` (Node: see `ui/package.json` engines `>=20.19.0`; use Node 22 if Vite fails)
6. `cd ui && npx --yes madge --circular --extensions ts,tsx src`
7. Support smoke: `GET /api/inbox/support/deployment-manifest` (with key if set)
8. `GET /health` — deployment_profile block
9. `UNIFIED_INTAKE_PRODUCT_ONLY=1` — confirm expected router reduction (manual or staging)

### Validation run — 2026-05-08 (this sprint)

| Gate | Result |
|------|--------|
| `compileall` `services/fiqa_api` + `tests` | PASS |
| `PYTHONPATH=. pytest tests/` | PASS (~220s) |
| `scripts/guardrail_inbox_triage.sh` | PASS |
| `scripts/run_full_regression.py` | PASS (`http_p95_ms` ~4614 &lt; 6000) |
| `cd ui && npx --yes madge --circular --extensions ts,tsx src` | PASS (no cycles) |
| `cd ui && npm run build` | **FAIL on workspace Node 20.18.2** — Vite 7 requires **Node ≥20.19** or **≥22.12** per CLI message; `ui/package.json` declares `"node": ">=20.19.0"`. Use Node 22.x on PATH (see prior sprint notes). |
| Support manifest / health (TestClient) | PASS (`replay_lineage` present; `auth_posture.support_export_surface` readable) |

---

## Convergence criteria

- Operators can answer **where truth lives** (PG vs JSON) from `/health` without reading code.
- Support manifest carries **explicit replay lineage tuple** for ticket paste.
- Production-like env without support secret is **visible** in logs + `auth_posture`, not silent.
- No new fake IAM or tenancy claims introduced.

---

## Self critique

**What this sprint document optimizes for:** Honest labeling of gaps so founders do not mis-sell.

**What it does not fix:** Multi-tenant isolation, billing, durable analytics, legal-grade replay.

**Bias risk:** Over-weighting manifest/json observability vs database migration ops — both matter at 30+ offices.

---

## Final decision

Ship **small honesty layers** (support replay lineage object, production support-export risk visibility, startup warning) and keep scope bounded. Defer IAM, RLS, and signed exports until there is a paying trigger and compliance requirement written down.

---

## FINAL_ONE_LINE

**Sell operational honesty and optional Postgres authority — not tenant IAM — until support keys, persistence flags, and replay lineage are standard in every deployment.**

---

# Phase 1 — Discovery artifacts

## 1. REAL_SAAS_FOUNDATION_MAP

- **Entry:** `app_main.py` composes middleware, `/health`, `/healthz`, product-only router gating, static mounts.
- **Intake routes:** `routes/inbox_triage.py` — triage POST, append, sessions, case CRUD patterns, WeChat, analytics hooks, support endpoints.
- **Deployment profile:** `deployment_profile.py` — `UNIFIED_INTAKE_PRODUCT_ONLY`, `INTAKE_SCHEMA_EPOCH`, inline route leak tuple (empty).
- **Identity:** `security/request_identity.py` — `X-Org-Id` → state; `intake_tenant_truth`; `HttpRequestLineage` uses `request.state.request_id`.
- **Support gate:** `security/support_export_gate.py` — optional shared secret; `support_export_auth_posture_dict`.
- **Persistence truth:** `db/service_record_settings.py` + `inbox_triage/case_truth_repository.py` — PG vs JSON facade.
- **Audit scaffolding:** `inbox_triage/audit_export.py` — `track_event` only.
- **Analytics:** `routes/analytics_dashboard.py` — reads funnel buffer only.
- **Guardrails:** `scripts/guardrail_inbox_triage.sh` — scenarios, persistence verify, state backbone, multi-turn sims, optional API check on 8001.

## 2. TENANT_TRUTH_MATRIX

| Concept | Source | Trusted? |
|---------|--------|----------|
| Office/org | `X-Org-Id` | No |
| Authoritative tenant | None | N/A |
| Case isolation | `case_id` + app logic | Weak cross-customer boundary if URLs leak |

## 3. AUTH_BOUNDARY_MATRIX

| Boundary | Status |
|----------|--------|
| End-user broker login | Out of scope |
| Support export | Optional shared secret |
| Platform APIs | Wide in `platform_full`; reduced in product-only |

## 4. SUPPORT_BOUNDARY_MATRIX

| Asset | Exposed via |
|-------|-------------|
| Deployment posture | `/health`, manifest |
| Case metadata shell | `case-head` |
| Message bodies | Not via support routes |

## 5. REPLAY_LINEAGE_MATRIX

| Artifact | Version carrier |
|----------|-----------------|
| Support manifest | `support_export_manifest_version`, `intake_schema_epoch`, `replay_lineage` |
| HTTP triage contract | `triage_wire_contract_label` |

## 6. OPERATOR_DEPENDENCY_MAP

Env matrix correctness; Qdrant readiness; DB URL; product-only flag; support secret for public deploys; client pack paths.

## 7. TOP_30_REAL_SAAS_RISKS

1. No authoritative tenant  
2. Support routes anonymous by default  
3. CORS open defaults  
4. PG/JSON confusion  
5. Dual-write read-your-writes  
6. In-memory sessions if misconfigured  
7. Per-pod analytics  
8. `case_id` guessability / URL sharing  
9. Full profile exposed by mistake  
10. Embedding cold start 503  
11. Missing DB in `ENV=prod`  
12. WeChat simulate flags in prod  
13. Log PII discipline undefined  
14. No centralized error tracking contract  
15. Attachment storage backup story  
16. Single-region deployment  
17. No SLO definitions  
18. Founder-only on-call  
19. Support tooling outside codebase  
20. Schema epoch drift between replicas (rolling deploy)  
21. Guardrail skipped in CI  
22. `.env` divergence across offices  
23. Manual client_id typos  
24. Role C vs production conflation  
25. `/ops` 410 confusion for legacy scripts  
26. Reports static mount accidental exposure  
27. Dual Cloud Run URL vs custom domain  
28. Rate limiting absent on triage  
29. LLM cost spikes  
30. Third-party API key rotation

## 8. TOP_20_SUPPORT_FAILURES

Wrong persistence assumption; missing support key docs; `case-head` without messages; cross-office ID confusion; analytics buffer empty; cannot prove build; Qdrant false “healthy”; timeline mismatch PG/JSON;附件 issues; session lost (in-memory); client pack mismatch; “replay” expectation vs Role C; unclear schema epoch; founder unreachable; ticket lacks `X-Request-ID`; ENV typo; prod demo CORS; duplicate cases; language/expectation; SLA not defined; escalation to eng without manifest.

## 9. TOP_20_OPERATOR_FAILURES

Wrong env file; forgot `UNIFIED_INTAKE_PRODUCT_ONLY`; DB migrate skipped; JSON fallback left on unintentionally; secret not rotated; scaled to N replicas without PG reads; disk full on JSON path; log volume; no backup restore tested; health check wrong URL; Cloud Run timeout too low; dependency version drift; Node version wrong for UI build; missed guardrail; chaos regression ignored; dual-write disabled mid-flight; attached wrong client pack; **production deploy without support key**; feature flags undocumented; manual SQL on prod.

## 10. TOP_20_FOUNDER_DEPENDENCIES

Persistence interpretation; env matrix; client onboarding; profile mode; Qdrant triage; incident comms; prioritization; vendor relationships; legal wording for replay; pricing; hiring support; DB restore; security exceptions; roadmap; key custody; demo vs prod; metrics narrative; integration contracts; chaos triage; strategic “say no”.

---

# Phase 2 — Highest ROI foundations (minimal real)

**Selected (implemented or reinforced this round):**

1. **Production-visible support export risk** — logs + `auth_posture` field when prod-like without key.
2. **Replay lineage tuple** on manifest + case-head — ticket paste clarity without claiming legal hold.

**Rejected here:** RBAC, RLS, signed bundles, multi-tenant analytics store.

---

# Phase 3 — Implementation notes (2026-05-08)

- `support_export_gate.support_export_auth_posture_dict`: optional `production_support_export_risk`.
- `app_main`: startup warning when production-like and support key unset.
- `routes/inbox_triage.py`: `_support_replay_lineage_dict()` + `replay_lineage` on manifest and case-head.
- Tests: `tests/test_support_export_gate.py` extended.

---

# Phase 5 — Operator / support tabletop (summary)

| Scenario | Breaks first | Survivable | Founder still needed |
|----------|--------------|------------|----------------------|
| Angry broker | Trust erosion faster than tech | If persistence truth clear | Messaging / policy |
| Wrong office read | No IAM boundary | Partially via client pack discipline | Definitive routing rules |
| Leaked `case_id` | Anyone may hit triage append paths if they have URL/session context | Rate limits absent — fragile | Incident response |
| Onboarding failure | Wrong `client_id`/pack | Checklist + validation scripts | Pack authoring |
| Replay dispute | No message-level export | Epoch + lineage tuple helps scope “what build” | Legal interpretation |
| Founder unavailable | Escalation stalls | Health/manifest self-serve reduces noise | Strategic calls |
| PG/JSON mismatch | Wrong screen vs DB | Persistence report + guardrails | Data reconciliation |

---

# Phase 6 — Self critique lists

## TOP_20_FAKE_SAAS_PATTERNS

Header-as-tenant; dashboard without warehouse; audit event == compliance; demo CORS as policy; manual org spreadsheet; “enterprise-ready” without IAM; implying RLS; single git SHA as audit; treating Role C as production replay; in-memory analytics aggregation; PDF exports as truth; checkbox security; shared demo API key per office; verbal SLA; founder grep as observability; JSON file as SoT in prod misconfig; feature flags in chat only; mock tenancy in UI; billing portal pretend; support heroics as system.

## TOP_20_STILL_MISSING_FOUNDATIONS

Authoritative tenant; durable metrics; signed exports; backup/restore runbook automation; rate limits; per-office key rotation; structured audit store; incident commander rotation; SLO/error budget; data residency choice; secrets manager integration; staging/prod parity checks; automated PG migration gate; customer-facing status page; log redaction standard; abuse detection; attachment virus scan policy; dependency SBOM gate; cost caps alerts; formal DPA path.

## TOP_20_THINGS_NOT_TO_BUILD_YET

Full RBAC UI; SSO; per-row RLS across all tables; billing engine; multi-tenant admin suite; custom IAM product; compliance certifications as marketing; heavy workflow builder; arbitrary plugin marketplace; multi-region active-active; ML observability platform.

## TOP_20_SUPPORT_TRUTHS

Manifest is best-effort provenance; case-head is not full replay; support key is not IAM; org header is asserted; logs may lack tenant index; analytics buffer is ephemeral; English-only runbooks unless built; attachments may be large; browser timezone affects timestamps display; mobile clients vary; WebSocket story undefined here; SLA not contractual unless written; escalation needs epoch + SHA; dual-write periods need explicit notices; founders may override flags; demo profiles differ; Cloud Run cold starts happen; error messages may leak internals if verbose; third-party LLM latency noisy; customer anger often precedes log capture.

## TOP_20_OPERATOR_TRUTHS

Health endpoint is contract for ops; readiness may flap with embeddings; prod without DB URL is broken for cases; JSON files don’t replicate across pods; guardrail is CI-quality gate not security scan; Node major matters for UI; env vars beat docs when they disagree; rolling deploys span two schema epochs briefly; logs without trace ID are useless; disk paths matter for JSON mode; support secret rotation requires coordination; feature envs compound; least privilege not enforced in pilot; backups untested == none; staging should hurt less than prod; metrics from one replica lie; manual SQL is debt; runbooks rot; incident timelines need UTC; communication beats dashboards.

## TOP_20_DEPLOYMENT_TRUTHS

Product-only reduces attack surface; `/api/healthz` exists for Cloud Run; static SPA mount excludes some paths; PORT env wins; `.env.cloudrun` layering can surprise; multiple health URLs confuse probes; graph optional import may warn; frontend dist path `frontend/dist` not `ui/dist`; UI built separately; reports dir may expose files; CORS reflects demo-first defaults; region pinning manual; secrets in env not Vault by default; horizontal scaling changes session affinity if in-memory; blue/green not built-in; schema epoch is label not migration lock; git SHA may be unknown in bad builds; container image tags need discipline; dependency caches stale in CI; rollback is redeploy + env revert.

## TOP_20_ENTERPRISE_ILLUSIONS

“We have tenants”; “dashboard is BI”; “audit events are SOC2”; “headers enforce isolation”; “replay API is legal discovery”; “single region is OK forever”; “JSON is fine at scale”; “LLM outputs are deterministic”; “demo profile is safe on internet”; “founder on-call scales”; “Git equals SBOM”; “encryption at rest solves everything”; “email auth is enough”; “we can promise uptime”; “RBAC later is free”; “multi-tenant is a flag”; “contracts don’t need lawyers”; “support can grep prod”; “pen test optional”; “no abuse risk in insurance”; “we’re HIPAA-ready”.

## TOP_20_REAL_ADVANTAGES

Explicit honesty in code comments; persistence report in `/health`; optional PG path; product-only profile; support manifest for tickets; guardrail scenario discipline; chaos regression script; schema epoch labeling; replay lineage tuple; operational sprint SSOT culture; FastAPI stack simplicity; JSON fallback for local dev speed; dual-write transition path; founder analytics funnel for iteration; case lifecycle vocabulary; attachment pipeline hooks; WeChat optional module; test coverage around gates; documented Cloud Run health quirks; small blast-radius decisions.

---

# Phase 7 — Architecture convergence

| Question | Answer |
|----------|--------|
| Truly ready | Pilot Unified Intake with honest docs + health/manifest + optional PG + guardrails. |
| Still fake | Tenant IAM, durable analytics, legal replay, enterprise SSO. |
| Safe to sell | Assisted intake workflow **with clear pilot boundaries**. |
| Never promise yet | Cross-office cryptographic isolation; immutable compliance exports; multi-tenant SLO. |
| Blocks 30 offices | Operational env discipline + PG authority + support key on public deploys. |
| Blocks 100 | External metrics, backups, rate limits, staffing model, cost controls. |
| Blocks enterprise sales | IAM, audit story, DPAs, SOC path, support org — **not** features in this repo today. |
| Real moat | Workflow + insurance domain packaging + iteration speed — **if** ops foundation holds. |
| Real wedge | Fast broker intake path vs generic chatbots — **not** fake tenancy. |
| Dangerous illusion | Calling header org IDs “multi-tenant security”. |

---

# Phase 8 — Required final output (inline summary)

See chat response **Phase 8 — Sprint output** for numbered answers 1–17 mirroring this sprint.
