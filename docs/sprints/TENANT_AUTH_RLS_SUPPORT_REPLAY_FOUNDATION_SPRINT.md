# TENANT / AUTH / RLS + SUPPORT REPLAY FOUNDATION SPRINT

**Control note · tenancy authority · replay authority · auth boundary authority · support export authority · operator access authority · validation journal · self critique · final report**

---

## Sprint meta

| Field | Value |
|--------|--------|
| **Branch** | `auto-evolution/tenant-auth-rls-support-replay-foundation-20260507-0247` |
| **Parent lineage** | `auto-evolution/product-only-wire-closure-support-export-20260507-0222` (Unified Intake pilot wire + support export WIP) |
| **Created (UTC wall)** | 2026-05-07 |
| **SSOT** | *This file* — superseding fragmentary notes for **tenancy, replay, support export, audit honesty** for Unified Intake. |
| **Related prior SSOT** | `docs/sprints/STRICT_PRODUCT_ONLY_WIRE_CLOSURE_SUPPORT_EXPORT_SPRINT.md` (wire closure + manifest v1) |
| **AGENTS.md tension** | Declares auth + multi-tenant **out of scope**; **this sprint explicitly models the gap** between pilot docs and SaaS runtime honesty. |

---

## PHASE 0 — GIT + SSOT (authoritative snapshot)

### 0.1 Deployment topology discovery (critical)

| Reality | Implication |
|---------|-------------|
| **`origin/main` (31572ca)** does **not** contain Unified Intake (`services/fiqa_api/inbox_triage/*`, `routes/inbox_triage.py`, UI intake APIs). Only trivial `triage.sh` overlap. | **“Main” is not the SaaS runtime for Unified Intake.** Pilot/evolution branches carry the product. Any “merge to main = production” assumption is **false** until intake lands on main. |
| This sprint branch is cut from **pilot intake line**, not from bare main. | Discovery and contracts below describe **pilot codebase**, not empty main. |

### 0.2 Git status at sprint open (after branch + stash replay)

**Tracked modifies (inherited WIP from prior wire-closure sprint — review before commit):**

- `configs/demo.env.example`
- `scripts/trial_readiness_check.sh`
- `services/fiqa_api/app_main.py`
- `services/fiqa_api/db/service_record_repository.py`
- `services/fiqa_api/inbox_triage/active_vehicle_resolver.py`
- `services/fiqa_api/inbox_triage/case_lifecycle.py`
- `services/fiqa_api/inbox_triage/case_truth_repository.py`
- `services/fiqa_api/inbox_triage/session_repository.py`
- `services/fiqa_api/inbox_triage/session_store.py`
- `services/fiqa_api/routes/inbox_triage.py`
- `tests/test_case_truth_repository.py`
- `tests/test_intake_session_persistence.py`
- `ui/src/api/inboxTriage.ts`
- `ui/src/api/triageResultContract.ts`
- `ui/src/components/intake/caseLifecycleDisplay.ts`
- `ui/src/features/intake/utils/intakePure.ts`

**Untracked (local workspace; not auto-owned by this sprint):**

- Large `docs/sprints/*`, `docs/*.md` drafts, `results/*`, `scripts/run_full_regression.py`, `ci_smoke.sh`, `services/fiqa_api/deployment_profile.py`, `inbox_triage/audit_export.py`, `pack_validation.py`, `structured_turn_obs.py`, `platform_inline_routes.py`, `json_safe_utils.py`, `tests/test_deployment_profile.py`, `tests/test_pack_validation.py`, `.vercel/`, `tmp/`, etc.

**Unrelated WIP policy:** Do not commit unrelated sprint artifacts. Prefer **tracked intake changes** + this SSOT; add untracked scaffolding only when Phase 5 explicitly justifies it.

### 0.3 Stash / branch mechanics

- Stash `pre-tenant-auth-rls-foundation: product-only-wire tracked WIP` was applied when creating this branch so **tracked modifications** are preserved on the foundation branch.

---

## PHASE 1 — TENANCY REALITY DISCOVERY

### TENANCY_REALITY_MAP

| Dimension | Current truth (pilot) | Authority / gap |
|-----------|------------------------|-----------------|
| **Org / tenant record** | No `org_id` column in `service_records` or `intake_sessions`. | **No row-level tenant key in DB.** |
| **Client pack vs tenant** | `client_id` on cases + `CLIENT_ID` env (`config_loader.get_active_client_id`) selects `configs/clients/<id>/`. | **Deployment-time client**, not authenticated broker identity. Two “offices” cannot safely share one deployment without cross-visibility. |
| **Caller-supplied org** | `X-Org-Id` header on `POST /api/inbox/triage` → passed into analytics (`track_event`, funnel metadata) only. | **Unauthenticated, spoofable** org tag — analytics dimension, **not** enforcement. |
| **Case listing** | `GET /api/inbox/cases` lists **global** queue (`list_recent_cases_for_read`) with no tenant filter. | **Any holder of API can enumerate all cases** (network-trust model). |
| **Sessions** | `intake_sessions` table: `(session_id, payload JSONB, timestamps)` — **no org column**. | Session binding is global. |
| **Delete** | `DELETE /api/inbox/cases/{id}` only for `workbench_test` cases. | No customer GDPR delete path; no org-scoped delete. |
| **Attachments** | Files on disk + metadata in case JSON/DB — no tenant path prefix in schema review. | Cross-tenant path confusion risk when multi-tenant FS layout is introduced. |

### CURRENT_ORG_BOUNDARY_MAP

| Surface | Org boundary behavior |
|---------|----------------------|
| Postgres `service_records.client_id` | **Soft label** from triage/config; not tied to IAM. |
| `X-Org-Id` | **Optional metadata** on triage POST. |
| Workbench / UI | Assumes single deployment + single CLIENT_ID unless manually changed. |
| WeChat binding | `session_id` + `client_id` query params — **no org isolation**. |

### CURRENT_REPLAY_BOUNDARY_MAP

| Capability | What exists | Trust limit |
|------------|-------------|-------------|
| **Persisted case replay** | `GET /api/inbox/cases/{case_id}` returns full case (messages when stored). | No versioning of triage contract; no snapshot of prompts/retrieval. |
| **In-progress replay** | `GET /api/inbox/session/{session_id}` returns turns + `workflow_state`. | Same global access pattern. |
| **Role C simulation** | Request models carry `conversation_turns` for bounded LLM customer replay. | Lab/simulation semantics; not audit replay. |
| **Support case head** | `GET /api/inbox/support/case-head/{case_id}` — minimal metadata, **no message bodies**. | Good for L2 handoff; insufficient for “why did AI say X?” without full case + model/retrieval lineage. |
| **Deployment manifest** | `GET /api/inbox/support/deployment-manifest` — git SHA, persistence report, `support_export_manifest_version`. | Does not prove staging ≡ prod parity without CI enforcement. |

### CURRENT_SUPPORT_BOUNDARY_MAP

| Route / artifact | Purpose | Access control today |
|------------------|---------|----------------------|
| `/api/inbox/support/deployment-manifest` | Operator provenance | **None** (same as inbox API surface). |
| `/api/inbox/support/case-head/{case_id}` | L2 metadata | **None**; knowing `case_id` = read metadata. |
| Full case GET | Support debugging | **Full PII exposure** if URL leaks. |
| `audit_export.record_intake_case_mutation` | Future WORM hook | **Stub** → `track_event` only; not durable audit. |

### CURRENT_AUTH_ASSUMPTION_MAP

| Assumption | Evidence | Honesty label |
|------------|----------|----------------|
| API trust = LAN/VPN/trusted UI | No Bearer tokens / sessions on inbox routes in reviewed code | **Network trust / pilot** |
| Headers are honest | `X-Org-Id` accepted from client | **Spoofable** |
| Broker identity | `CLIENT_ID` env | **Singleton deployment** |
| Admin vs customer | No role model on intake HTTP | **Missing** |

### CURRENT_FOUNDER_DEPENDENCY_MAP

| Dependency | Why |
|------------|-----|
| DB direct access | No RLS; support cannot self-serve safe SQL with tenant guards. |
| Git / env interpretation | `deployment_profile`, `UNIFIED_INTAKE_PRODUCT_ONLY`, persistence flags require runtime knowledge. |
| Log correlation | `track_event` / funnel buffer — not a customer-facing audit trail. |
| Main vs pilot branch confusion | Intake not on `origin/main` — **merge hygiene** is founder-shaped. |

### CURRENT_DATA_VISIBILITY_MAP

| Data class | Who can see (today) | Blast radius |
|------------|---------------------|--------------|
| Case PII | Anyone with API reach + `case_id` | **Whole fleet** |
| Session turns | Same | Pre-case + in-flight intent |
| Analytics payload | In-process buffer + downstream if wired | May duplicate **PII** in events if payloads include text (verify before enterprise claims). |
| Support manifest | Anyone | Low (non-PII by design). |

---

## PHASE 2 — SUPPORT / REPLAY WALKTHROUGHS (simulated)

*Method: mental simulation against current code + operator runbooks (AGENTS.md). Each scenario lists **failure mode** if founder/DB not available.*

### Scenario outcomes → gap backlog

| # | Scenario | Top failure |
|---|----------|-------------|
| 1 | L1 replays wrong vehicle | No guaranteed **vehicle resolution snapshot** in export; resolver state may not match message timeline. |
| 2 | L2 missing append | Append path depends on case + session binding logs — **no append-specific audit chain** beyond analytics events. |
| 3 | “Why did AI say this?” | No **prompt + model + retrieval snapshot** tied to turn; LLM non-determinism unbounded. |
| 4 | Customer export | No **signed support bundle**; `future_export_bundle_keys` is documentation only. |
| 5 | Customer deletion | Only test-case delete; **no production delete / retention workflow**. |
| 6 | Customer audit trail | No WORM; `audit_intake_mutation` not durable. |
| 7 | Office admin reviews replay | Full case GET exposes PII without **role-based redaction**. |
| 8 | Support compares deployments | `deployment-manifest` helps; **no automatic diff** vs ticket timestamps. |
| 9 | Rollback investigation | Git SHA in manifest; **no migration version / schema epoch** in API response. |
| 10 | Replay mismatch | **No triage_result version** pinned per turn in persisted messages consistently. |
| 11 | Staging vs prod mismatch | Environment parity **not proven** by manifest alone. |
| 12 | “Who accessed this case?” | **No access log** per case/session. |
| 13 | Support without DB | Blocked on **PII-heavy** JSON inspection unless API suffices. |
| 14 | Founder unavailable | Escalation stalls on **persistence + branch + env** questions. |
| 15 | Enterprise security review | Declares multi-tenant out of scope in AGENTS while product behaves like shared SaaS API — **honesty gap**. |

### TOP_50_SUPPORT_REPLAY_FAILURES (rolling ledger — first 25 written; extend during sprint)

1. Global case list without tenant filter.  
2. Global case GET without auth.  
3. Session GET without auth.  
4. `case_id` as sole secret (URL leak = data leak).  
5. No per-field redaction for L1.  
6. No export manifest signature.  
7. No export time + exporter identity.  
8. No model ID per response in persisted record.  
9. No retrieval trace ID per response.  
10. Append blocked without durable reason code in customer-auditable store.  
11. Wrong-vehicle diagnosis needs entity timeline — incomplete.  
12. Role C replay conflated with production replay in mental model risk.  
13. Attachment download URL not time-scoped.  
14. WeChat binding state in session — sensitive, globally readable.  
15. `X-Org-Id` spoof → wrong analytics attribution.  
16. **No org in DB** → impossible honest RLS later without migration.  
17. Support engineer cannot prove **which deployment** answered a ticket without manual SHA check.  
18. No **break-glass** workflow documented in product.  
19. Founder DB access bypasses all app-level future controls — **dual world**.  
20. In-memory analytics loss on crash — replay of funnel incomplete.  
21. JSON file fallback path (if enabled) — file permission model = host trust.  
22. `workbench_test` flag misuse could mark real cases deletable — policy gap.  
23. No rate limit per org/office.  
24. Staging datasets in shared DB — unrealistic isolation story.  
25. Customer-facing “AI said” with no lawyer-safe bundle.  
26–50. *Reserved:* expand with CI findings, OpenAPI review, attachment paths, cross-link to `TOP_30_AUDIT_FAILURES`, ticket simulations.

### TOP_30_AUDIT_FAILURES (representative sample)

1. No WORM / immutable log.  
2. Audit scaffold → `track_event` only.  
3. No actor identity on mutations.  
4. No before/after diff for case updates.  
5. No signed export artifact.  
6. No retention TTL enforcement.  
7. No legal hold flag.  
8. Session create/update not audited durably.  
9. Attachment access not logged per actor.  
10. Support manifest not logged when fetched.  
… (20 more: chain of custody, clock sync, PII in logs, model versioning, etc. — extend in journal.)

### TOP_30_ACCESS_CONTROL_FAILURES (representative)

1. No authentication on inbox routes.  
2. No authorization roles.  
3. No tenant scoping.  
4. Spoofable org header.  
5. Enumerate-all cases.  
6. Predictable/guessable IDs risk — review ID generation separately.  
7. Attachment direct file response — link lifetime.  
8. Delete restricted to test — but **read not restricted**.  
9. WeChat simulate endpoint in wrong env — identity spoof.  
10. Founder DB superuser — breaks enterprise story.  
… (extend).

### TOP_20_TENANCY_FAILURES

1. No `org_id` / `tenant_id` in schema.  
2. `client_id` ≠ tenant isolation.  
3. Single-DB shared visibility.  
4. `X-Org-Id` not verified.  
5. Sessions not scoped.  
6. Analytics mixing tenants if header spoofed.  
7. Future RLS migration — **no placeholder column** today.  
8. Attachment FS paths not tenant-prefixed.  
9. Case binding race — cross-session confusion under load (operational, not RLS).  
10. MAIN branch missing intake — **release isolation** broken.  
11–20. *Reserved.*

### REPLAY_TRUST_MATRIX

| Dimension | Present? | Notes |
|-----------|----------|-------|
| Message timeline | Partial | DB + JSON paths |
| Triage result per turn | Partial | Embedded in turn payloads when saved |
| Model identifier | Weak | Not a first-class persisted field in all paths |
| Prompt snapshot | No | |
| Retrieval snapshot | No | |
| Determinism | No | LLM + live config |
| Contract version | Partial | `support_export_manifest_version`, `triage_wire_contract_label` in manifest |

### SUPPORT_ESCALATION_MATRIX

| Level | Can solve today? | Blocker |
|-------|------------------|---------|
| L1 | Operational scripts + UI | No safe read-only tenant view |
| L2 | API case + session | No auth; PII handling policy |
| L3 | Founder + DB | Founder dependency |

---

## PHASE 3 — AUTH / TENANCY / RLS MODELING (design only)

### TENANT_BOUNDARY_AUTHORITY

- **Future authority:** `tenant_id` (or `org_id`) **issued by auth**, not client headers — stored on **session, case, and audit events**.
- **Transitional:** `client_id` remains **config lane**; must not be conflated with **security boundary**.

### AUTHZ_MODEL_V1 (target sketch)

- **Subjects:** `end_customer`, `broker_user`, `office_admin`, `support_l1`, `support_l2`, `operator`, `system_worker`.
- **Resources:** `session`, `case`, `attachment`, `export_bundle`, `deployment_manifest`.
- **Actions:** `read_redacted`, `read_full`, `append`, `export`, `delete`, `impersonate (break-glass)`.

### OPERATOR_ROLE_MATRIX

| Role | deployment-manifest | case-head | full case | export |
|------|---------------------|-----------|-----------|--------|
| L1 | ✓ | redacted? TBD | ✗ | ✗ |
| L2 | ✓ | ✓ metadata | ✓ policy | ✓ signed bundle |
| Founder break-glass | ✓ | ✓ | ✓ | ✓ (audited) |

*(✓ = target state; today all open if API reachable.)*

### REPLAY_VISIBILITY_MODEL

- **Internal replay package:** messages + `triageResult` blobs + **engine version** + **config hash**.
- **Customer-facing narrative:** redacted + stable ordering + **non-repudiation** optional Phase 2.

### SUPPORT_EXPORT_AUTHORITY

- **Current label:** `support_export_v1` (+ `future_export_bundle_keys` in `audit_export.py`).
- **Target:** signed manifest + **exporter principal** + **purpose** + **retention class**.

### AUDIT_LINEAGE_MODEL

- **Mutation events:** case create/update/append/delete/export/access.
- **Lineage chain:** `(tenant, actor, action, resource, prior_hash, new_hash, timestamp_utc, deployment_id)`.

### FUTURE_RLS_MODELING

- Postgres: `tenant_id` on `service_records`, `intake_sessions`, `record_messages` (denormalized for policy), attachment metadata.
- Policy: `tenant_id = current_setting('app.tenant_id')::uuid` (pattern only — **not implemented** this sprint unless Phase 5 approves migration).

### SUPPORT_BUNDLE_MODEL

- JSON + detached signature + manifest version + git SHA + schema version of `triage_result`.

---

## PHASE 4 — SYSTEM CONVERGENCE (single authorities)

### REPLAY_CONTRACT_V2 (draft)

- **Minimum replay unit:** ordered turns + per-turn `triageResult` + **`triage_contract_version`** + **server `git_commit`** at write time.
- **Excluded from “trusted replay”:** responses without persisted `triageResult` linkage.

### SUPPORT_EXPORT_CONTRACT_V2 (draft)

- Includes: `support_export_manifest_version`, `git_sha`, `case_id`, **`export_actor`** (future), **`redaction_profile`**, **`bundle_created_at`**, hashes of included sections.

### DEPLOYMENT_IDENTITY_CONTRACT

- **Authoritative tuple:** `(git_commit, UNIFIED_INTAKE_PRODUCT_ONLY flag, persistence mode, intake_schema_epoch)`
- **Today:** manifest exposes commit + persistence report; **schema epoch missing** (add in Phase 5 if low-risk).

### TENANT_VISIBILITY_CONTRACT

- **Invariant (target):** no API response lists rows outside authenticated tenant.
- **Today:** **no invariant** — document as **pilot**.

### OPERATOR_SUPPORT_WORKFLOW

1. Ticket → verify `deployment-manifest`.  
2. Fetch `case-head` → decision to escalate.  
3. If allowed → full case / export bundle (future).  
4. Log access (future).

### REPLAY_LINEAGE_CONTRACT

- Each persisted mutation appends **structured** event: `{case_id, session_id, mutation_type, contract_versions, config_digest}` — target storage TBD (WORM).

---

## PHASE 5 — IMPLEMENTATION GATE (not executed in Phase 0–4 doc pass)

**Allowed when gated:** metadata fields, manifest builders, OpenAPI tags, non-breaking route annotations, `org_id` propagation **as opaque future key** (nullable column discussion), schema epoch in manifest, audit scaffolding behind feature flag.

**Forbidden without design review:** full IAM, RLS enablement in prod, triage semantic changes, resolver changes.

**Candidate backlog from Phase 4 gaps:**

- Add `intake_schema_epoch` (constants file) + surface in `deployment-manifest`.
- Migration sketch: nullable `tenant_id` column — **requires explicit approval** (behavior + rollout).

---

## PHASE 6 — VALIDATION LOOPS (journal)

| Iteration | compileall | pytest | npm build | madge | guardrail | full regression | Notes |
|-----------|------------|--------|-----------|-------|-----------|-----------------|-------|
| 0 | *pending* | *pending* | *pending* | *pending* | *pending* | *pending* | Branch + SSOT only at open. |

*Update after each batch.*

---

## PHASE 7 — ENTERPRISE / OPERATOR REVIEWS (rolling)

### ENTERPRISE_READINESS_REVIEW (summary)

- **Could support operate safely?** Partially on **one-tenant pilot**; fails multi-tenant review.  
- **Could replay be trusted?** Partial — no prompt/retrieval chain.  
- **Exports auditable?** No signed bundle.  
- **Orgs isolated?** No.  
- **Pilot tells?** Open HTTP case/session reads; AGENTS “out of scope” vs deployed API **signals SMB pilot** not managed SaaS.

### SUPPORT_SCALING_REVIEW_V2

- Needs **authenticated read replicas** + **redacted views** before L1 scale.

### TENANT_ISOLATION_REVIEW

- **Current:** none. **Data bleed:** any API client with network access.

### REPLAY_TRUST_REVIEW

- Good: case-head minimizes PII for handoff.  
- Bad: **“why AI”** narrative unsupported for compliance.

### AUTH_HONESTY_REVIEW

- **Auth is absent** on inbox — must be stated externally to customers.

### SELF_CRITIQUE_REPORT_V5

- This document over-claims nothing: stubs stay labeled stubs.  
- Risk: teams confuse `X-Org-Id` with real tenancy — **call out loudly** (done above).

---

## PHASE 8 — FINAL REPORT (stub)

`TENANT_AUTH_RLS_SUPPORT_REPLAY_FOUNDATION_FINAL_REPORT` will be appended when sprint closes. Sections 1–11 as required by charter.

---

## Change log

| Date | Author | Change |
|------|--------|--------|
| 2026-05-07 | Sprint agent | Initial SSOT: Phase 0 inventory, Phase 1–4 authority drafts, Phase 2 matrices, mainline discovery. |

