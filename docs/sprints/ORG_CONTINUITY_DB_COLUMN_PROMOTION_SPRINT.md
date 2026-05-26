# ORG CONTINUITY + DB COLUMN PROMOTION SPRINT — SINGLE SOURCE OF TRUTH

**Branch:** `sprint/org-continuity-db-column-promotion`  
**Schema epoch:** `2026-05-09_org_continuity_office_owner_column_v1` (`deployment_profile.INTAKE_SCHEMA_EPOCH`)  
**Mission:** Make office ownership **more durable, continuous, queryable, operationally trustworthy, and support-survivable**—without fake enterprise tenancy.

---

## PHASE 0 — GIT + INVENTORY

### Branch

```text
sprint/org-continuity-db-column-promotion
```

### Modified files (working tree during sprint; primary code ownership)

| Area | Files |
|------|--------|
| Postgres persistence | `services/fiqa_api/db/service_record_repository.py`, `services/fiqa_api/db/schema/stage1_service_record.sql`, `services/fiqa_api/db/schema/migrations/001_service_records_office_owner_org_id.sql` |
| Read facade / list | `services/fiqa_api/inbox_triage/case_truth_repository.py` |
| Routes | `services/fiqa_api/routes/inbox_triage.py` |
| Office semantics / manifest | `services/fiqa_api/security/case_office_access.py` |
| Operator epoch | `services/fiqa_api/deployment_profile.py` |
| Tests | `tests/test_case_office_access.py` |

### Flow inventory (existing system)

| Flow | Mechanism |
|------|-----------|
| **Intake perimeter** | Intake API gate + product-only wiring (`security/intake_api_gate.py`, `deployment_profile`) |
| **Support perimeter** | `UNIFIED_INTAKE_SUPPORT_API_KEY` on `/api/inbox/support/*` (`support_export_gate.py`) |
| **Office ownership hint** | Client `X-Org-Id` → `request.state.client_asserted_org_id` (`IntakeClientAssertionMiddleware`, `request_identity.py`) |
| **Optional enforcement** | `UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP`, strict list `UNIFIED_INTAKE_OFFICE_LIST_STRICT_NO_LEGACY` (`case_office_access.py`) |
| **Session bind** | `session_store` / `session_repository`: `active_case_id`, `asserted_org_id` in session JSON payload |
| **Case persistence** | `case_store.save_case` / updates → `persist_new_case` / `persist_case_append` when DB-primary |
| **JSON persistence** | `data/unified_intake_cases.json` (env path); field `asserted_org_id` on case document |
| **Postgres persistence** | `service_records.extra` JSONB historically held `asserted_org_id`; **now also** `office_owner_org_id` column |
| **Support manifest** | `GET /api/inbox/support/deployment-manifest`, `replay_lineage.office_ownership` |
| **Analytics ownership** | `org_id` optional on `track_event` / route analytics (`triage_inbox` paths); best-effort metadata only |
| **Request lineage** | `http_request_lineage` → `request_trace_id` (no org authority) |

### Where `asserted_org_id` can disappear (pre/post sprint honesty)

1. **Normalization:** `case_store._normalize_case` drops empty `asserted_org_id` keys.
2. **Creates without header:** formal persist paths that omit `org_id` never stamp the case.
3. **Append / partial case dicts:** mutate flows that rebuild `extra` without carrying `asserted_org_id` rely on **COALESCE patch** on column + legacy `extra` bag; empty patch preserves stored ownership.
4. **Session rows:** if client stops sending `X-Org-Id`, session still **preserves** prior `asserted_org_id` when omitted on save (`session_store.save_in_progress_session`).
5. **Read fallback:** JSON-only pilots may diverge from Postgres if dual-write / flags disagree—documented operational risk, not cryptographic tenancy.

### Where ownership was only in memory

- Request-scoped `client_asserted_org_id` (by design, not persistence).
- In-process session store when `UNIFIED_INTAKE_ALLOW_INMEMORY_SESSIONS_FOR_TESTS` (tests only).

### Where ownership was not query-efficient (mitigations this sprint)

- **Before:** Under enforcement, `GET /api/inbox/cases` loaded **all** cases via `list_all_cases_for_read()` then filtered in Python (bounded by `_MAX_LIST_ALL` on PG path but still heavy).
- **After (Postgres + DB-primary reads):** Indexed/filtered SQL + stub hydration via `list_cases_for_office_enforcement_read`.

---

## PHASE 2 — SYSTEM DISCOVERY OUTPUTS

### 1. ORG_CONTINUITY_FLOW_MAP

```text
Browser/App → X-Org-Id header
    → IntakeClientAssertionMiddleware → request.state.client_asserted_org_id
        → triage_inbox(..., org_id) → save_case(... asserted_org_id=org_id)
            → case document asserted_org_id
            → Postgres: office_owner_org_id column + extra.asserted_org_id (legacy bag)
        → save_in_progress_session(... asserted_org_id=org_id)
            → intake_sessions.payload JSON (asserted_org_id)
Enforcement routes → client_asserted_office_id(request) vs case.asserted_org_id
Support export → deployment-manifest / case-head → asserted_org_id echo + posture dict
```

### 2. CASE_OWNERSHIP_PERSISTENCE_MAP

| Layer | Field | Notes |
|-------|-------|------|
| Case JSON | `asserted_org_id` | Primary API/workflow field |
| Postgres column | `office_owner_org_id` | Promoted, nullable, indexed `(office_owner_org_id, updated_at DESC)` |
| Postgres JSONB | `extra.asserted_org_id` | Legacy / dual-write compatibility; hydrated with column **preferred** on read |

### 3. SESSION_BIND_TRUTH_MAP

| Store | Location | Continuity |
|-------|----------|------------|
| Postgres | `intake_sessions.payload` | `asserted_org_id` preserved when new saves omit org if row had prior stamp |
| Memory | tests only | Same merge semantics in `session_store` |

### 4. POSTGRES_OWNERSHIP_GAP_MAP (remaining)

| Gap | Severity |
|-----|----------|
| **Binding list** still uses global recent stubs—not office-filtered | Medium confusion under multi-office pilots |
| **Partial index** only on column; rows with ownership **only** in `extra` until backfill rely on SQL `COALESCE(column, extra→>'asserted_org_id')` | Low after auto-backfill on DDL ensure |
| **No RLS** | By design (honest); headers are not IAM |

### 5. JSON_STORE_OWNERSHIP_GAP_MAP

| Gap | Notes |
|-----|-------|
| File has no DB index | Office list uses linear scan + filter when `db_primary_reads` off |
| Max 200 cases | Bounded; different scale story than Postgres |

### 6. SUPPORT_REPLAY_OWNERSHIP_MAP

| Artifact | Ownership signal |
|----------|------------------|
| `replay_lineage.office_ownership` | Enforcement flags + column semantics |
| `support_case_head` | `case.asserted_org_id` echoed |
| `tenant_truth` | Client assertion only |

### 7. TOP_30_OWNERSHIP_FAILURES (representative)

1. Missing `X-Org-Id` on formal create → unstamped case.  
2. Typo / rotated office string → silent mismatch under enforcement.  
3. Legacy unstamped rows visible cross-office when strict mode off.  
4. Strict mode hides unstamped → “case vanished” support confusion.  
5. Dual-write PG/JSON drift on ownership.  
6. Append payload missing ownership fields → relied on preserve semantics (now column COALESCE).  
7. Normalization stripping empty org.  
8. Binding resolves against **global** recent cases → wrong-office attachment.  
9. Analytics `org_id` optional → funnel incomplete for audits.  
10. Session org not propagated to case if formal persist never sends header.  
11. Export shows assertion, not legal tenant proof—misread by buyers.  
12. Founder assumes header = IAM.  
13. Proxy strips headers.  
14. Multi-tab different org headers on same browser profile.  
15. Cached FE bundle pointed at wrong office config.  
16. Partial outage on PG → JSON fallback lists differ.  
17. Manual SQL edits to `extra` without column → transient drift until read hydrate (column wins).  
18. Manual column edits without `extra` → tools reading only JSONB bag see stale (column still wins in API hydrate).  
19. Copy/paste case_id across offices → 403 under enforcement (good) but opaque to user.  
20. Empty string header treated as missing.  
21. Unicode trim edge cases in office ids.  
22. Large org string truncation at 256 chars.  
23. Demo env enforcement accidentally on.  
24. Prod enforcement off → cross-office data mingling in lists.  
25. Session eviction loses pre-formal context (org in session gone).  
26. Support replay omits message bodies—cannot reconstruct header context per turn.  
27. Third-party integration forgetting header on **append** only routes.  
28. Mobile wrapper not forwarding header.  
29. Browser privacy tools blocking custom headers.  
30. Future SSO assumed—would bypass current hint model without explicit mapping layer.

### 8. TOP_30_SUPPORT_CONFUSION_PATTERNS

1. “Tenant ID” language vs assertion semantics.  
2. Strict vs legacy list visibility.  
3. 403 vs 404 leakage debates.  
4. Case exists but not in list (office filter).  
5. Manifest says “disabled enforcement” but pilot expects isolation.  
6. Replay lineage mistaken for WORM export.  
7. `request_trace_id` vs case lineage.  
8. Dual persistence modes (JSON vs PG).  
9. `product_only` router reduction surprises.  
10. Support key vs intake key confusion.  
11. Environment drift (`DEMO_MODE`, `ENV`).  
12. Schema epoch changes interpreted as data migrations.  
13. Git SHA on manifest vs deployed container image.  
14. Customer PII expectations on support endpoints (denied by design).  
15. Attachments not in case-head export.  
16. Session vs case ID interchange conflation.  
17. Talk-to-agent shortcut persistence quirks.  
18. Workbench test flags vs formal cases.  
19. Archived cases still readable by ID paths.  
20. Founder unavailable—no runbook for header-less legacy.  
21. PG connectivity errors masquerading as empty queues.  
22. Partial hydration warnings in logs ignored.  
23. English vs Chinese labels in activity timelines confusing L1.  
24. Multiple offices sharing one deployment—logical separation anxiety.  
25. Analytics gaps vs “missing telemetry bug.”  
26. Org rename without data migration plan.  
27. Mapping office codes to CRM IDs undocumented.  
28. Third-party webhook without org context.  
29. Manual DB fixes without updating JSON mirror.  
30. Escalation to “RLS” requests—requires scope decline response.

### 9. TOP_30_FAKE_TENANCY_PATTERNS_V3 (anti-patterns to avoid)

1. Calling `X-Org-Id` “authentication.”  
2. Implying RLS exists.  
3. Implying SSO readiness.  
4. Billing-per-office without contracts.  
5. Tenant-branding as security boundary.  
6. Export labeled “legal hold.”  
7. Correlation IDs marketed as audit tamper evidence.  
8. Header signing absent—pretending integrity.  
9. Role models without IAM substrate.  
10. Policy-as-code theater without enforcement.  
11. Multi-tenant data model before second office pays.  
12. Complex ORM tenant scopes premature.  
13. Kubernetes namespace as “tenant.”  
14. Feature flags described as compliance controls.  
15. Customer-managed keys narrative at pilot stage.  
16. Log retention claims without DPA.  
17. EU residency promises on single-region demo DB.  
18. Automatic data residency routing fake.  
19. Per-tenant encryption keys without KMS ops.  
20. Implying Postgres JSONB `extra` is cryptographically sealed.  
21. Marketing “zero trust” with header trust.  
22. Treating `client_id` as cryptographic identity.  
23. Treating WeChat binding as legal identity proof.  
24. Confusing demo intake with regulated PHI flows.  
25. “Enterprise RBAC ready” boilerplate in decks.  
26. Selling SOC2 based on manifest JSON.  
27. Calling schema epoch a certified migration ID.  
28. Claiming append-only history when updates exist.  
29. Presenting support manifest as customer-facing SLA.  
30. Describing this sprint as “tenant platform Phase 1.”

### 10. TOP_20_HIGH_ROI_MOVES

1. **Promoted ownership column + index** (done).  
2. **SQL-scoped list path** (done for PG primary reads).  
3. Office-filtered **binding candidate list** (not done—high leverage next).  
4. Startup warning when enforcement on but `%` cases unstamped (not done).  
5. Structured operator metric: unstamped count by env (not done).  
6. Append routes assert preserve ownership regression tests with PG (partially covered indirectly).  
7. Unified anomaly log line when column vs extra diverge (not done).  
8. Documented office-code rename runbook (partially external).  
9. Support bundle includes office enforcement snapshot (manifest exists).  
10. FE devtools banner showing asserted org in dev (not done).  
11. Contract tests for list filters vs stub hydration ordering (not done).  
12. Pilot playbook: required headers per route family (docs).  
13. Kill linear JSON scan for enforcement in prod via mandatory PG (ops).  
14. Bench query plans at 100k rows for office filter (ops).  
15. Optional partial index including expression on COALESCE (future).  
16. Rate-limit anonymous case probes if enforcement off (security backlog).  
17. Session bind includes asserted org match guard when enforcement on (future).  
18. Dual-write checker includes ownership column (mirror scripts).  
19. Explicit “unstamped case” UI badge for brokers (product).  
20. Map future SSO group → `office_owner_org_id` explicitly when IAM arrives.

### 11. WHAT_BREAKS_AT_30_OFFICES

- Operational entropy in **office codes** and CRM mappings without runbooks.  
- Support confusion from **legacy unstamped** rows if strict mode toggled late.  
- **Binding** cross-office mistakes remain likely without filtered binding lists.

### 12. WHAT_BREAKS_AT_100_OFFICES

- **Human process** scaling (rename, churn, disputes) exceeds tooling.  
- Analytics without authoritative IAM still **non-attributable** forensically.  
- Postgres maintenance windows + enforcement semantics need SRE clarity.

### 13. WHAT_BREAKS_AT_ENTERPRISE

- Procurement expects **SSO, audit, RLS, DPAs**—explicitly out of scope here.  
- Legal discovery workflows—not represented in replay exports.  
- Per-tenant isolation guarantees contradict honest header assertion model.

---

## PHASE 3 — ARCHITECTURE CONVERGENCE (SMALLEST SAFE PATH)

**Chosen path:** Promote ownership to **`office_owner_org_id`** on `service_records`, **keep** `asserted_org_id` as the API/workflow field, **prefer column on read**, **preserve on append** via `COALESCE` patch, **auto DDL + backfill** on first PG mutation/read that runs ensure (rollback-friendly: column nullable). Replace brute-force “load all cases then filter” with **SQL + stub hydration** when Postgres primary reads are enabled.

**Explicit non-goals:** IAM, SSO, RBAC, RLS, billing, enterprise tenancy theater.

---

## PHASE 4 — IMPLEMENTATION SUMMARY

### Shipped

- `office_owner_org_id` nullable column + index `idx_service_records_office_owner_updated`.  
- `_ensure_office_owner_org_schema` on PG writes/reads that need the column (additive DDL + one-time backfill from `extra`).  
- `persist_new_case` / `persist_case_append` write column; append preserves prior stamp when incoming empty.  
- Hydration: `_hydrate_case_asserted_org_id` prefers column over `extra`.  
- `count_service_records_office_scoped` + `list_record_ids_office_scoped` using visibility rule aligned with `case_visible_in_office_list`.  
- `list_cases_for_office_enforcement_read` + route wiring for `GET /api/inbox/cases`.  
- `office_ownership_posture_dict` extended with persistence column semantics.  
- `stage1_service_record.sql` + `migrations/001_service_records_office_owner_org_id.sql` for explicit ops apply.  
- `INTAKE_SCHEMA_EPOCH` bumped.

### Rollback

1. Unset `UNIFIED_INTAKE_ENFORCE_CASE_OFFICE_OWNERSHIP` (behavioral).  
2. Leave column in place (harmless); or drop manually only if **no** consumers rely on it (not required).  
3. Revert code deploy to prior artifact if necessary—column remains backward compatible.

---

## PHASE 5 — MULTI-LOOP VALIDATION OUTPUTS

### LOOP A — Commands

| Command | Result |
|---------|--------|
| `python3 -m compileall -q services/fiqa_api tests` | **PASS** (exit 0) |
| `PYTHONPATH=. pytest tests/` | **PASS** (exit 0; 1 skipped; DeprecationWarning from SWIG unrelated) |
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** (`Guardrail: PASS`) |
| `PYTHONPATH=. python3 scripts/run_full_regression.py` | **PASS** (`assertions.passed: true`) |

### LOOP B–D (documentary)

- Session bind continuity: unchanged semantics; column promotion does not alter session JSON.  
- Wrong-office access: still HTTP 403 on single-case routes when enforcement on + stamped mismatch.  
- Unstamped legacy: SQL visibility matches Python `case_visible_in_office_list`.  
- Replay / export: `replay_lineage` includes expanded posture; no message-body expansion (by design).

### UI build + madge

| Command | Result |
|---------|--------|
| `cd ui && npm run build` | **FAIL** — Node **20.18.2** installed; **Vite requires Node 20.19+ or 22.12+**. Follow-on error: `ERR_REQUIRE_ESM` loading Vite from `vite.config.ts` (config load path incompatible with current Node/tooling combo). **Remediation:** upgrade Node to ≥20.19 (or 22.12+) per Vite engine requirement, then rerun `npm run build`. |
| `cd ui && npx --yes madge --circular --extensions ts,tsx src` | **PASS** (`No circular dependency found`) |

### Support manifest smoke

- `scripts/support_deployment_manifest_smoke.py`: **not run against live server** in this sprint execution (no server on 8001 in guardrail). Use when API is up.

---

## PHASE 6 — SELF_CRITIQUE_REPORT_V6

| Persona | Critique |
|---------|----------|
| **Skeptical broker** | You still trust a header I can forge unless enforcement is on—tell me plainly on every screen. |
| **Angry office manager** | Another office’s case appeared in binding suggestions—WHY is binding not office-scoped? |
| **Support escalation lead** | Manifest is honest, but L1 still conflates “tenant truth” with real IAM—needs wording discipline. |
| **Exhausted founder** | Auto-DDL on prod startup can surprise locked-down DB roles—monitor permissions. |
| **Enterprise reviewer** | No RLS/SSO; header assertion ≠ tenant isolation—acceptable only with written scope. |
| **Operations engineer** | Backfill + index creation can contend on huge tables—watch locks on first deploy. |
| **Deployment engineer** | Schema epoch bumped—ensure tickets mention **behavioral** vs **DDL** changes separately. |

**Verdict:** Increment is honest and rollback-friendly; remaining highest-risk gap is **office-blind binding list**, not this sprint’s column work.

---

## PHASE 7 — CONVERGENCE ANSWERS

1. **What became REAL?** Indexed Postgres ownership stamp + query-aligned office list path under DB-primary reads; explicit persistence semantics in operator posture JSON.  
2. **What is still fake SaaS?** No billing, no IAM-backed tenant authority, no per-tenant SLAs implied by code.  
3. **What is still fake tenancy?** Header assertion without cryptographic binding to identity provider.  
4. **What ownership continuity is now reliable?** Once stamped, Postgres append preserves ownership via column COALESCE; reads prefer durable column.  
5. **What ownership continuity still breaks?** Unstamped creates; wrong-office **binding** suggestions; non-PG JSON pilots at scale.  
6. **What is now operationally survivable?** Office-scoped lists without loading full case history for every row on PG path.  
7. **What is now support-survivable?** Clearer manifest vocabulary connecting API field ↔ DB column.  
8. **What is now deployment-honest?** Schema epoch reflects ownership persistence promotion; explicit migration SQL exists.  
9. **What is now replay-honest?** Same disclaimer: replay metadata is **not** WORM/legal hold; ownership posture is declared, not proven.  
10. **Next smallest 10x move?** **Office-filter `list_recent_cases_for_binding` / resolve path** when enforcement is enabled.

---

## PHASE 8 — FINAL OUTPUT (PRINTED SUMMARY)

### 1. Branch

`sprint/org-continuity-db-column-promotion`

### 2. Sprint-owned files

`services/fiqa_api/db/service_record_repository.py`, `services/fiqa_api/inbox_triage/case_truth_repository.py`, `services/fiqa_api/routes/inbox_triage.py`, `services/fiqa_api/security/case_office_access.py`, `services/fiqa_api/deployment_profile.py`, `services/fiqa_api/db/schema/stage1_service_record.sql`, `services/fiqa_api/db/schema/migrations/001_service_records_office_owner_org_id.sql`, `tests/test_case_office_access.py`, **this document**.

### 3. What was implemented

Promoted Postgres ownership storage (`office_owner_org_id`), automatic schema ensure + backfill, read hydration preferring the column, append preservation, indexed office-scoped counting/listing aligned with list visibility rules, route integration for enforcement lists, manifest posture extensions, schema epoch bump, migration SQL for explicit ops.

### 4. What became more real

Durable, query-efficient office stamping on Postgres; enforcement list behavior grounded in SQL + stubs instead of full-table Python filtering on PG-primary paths.

### 5. What is still fake

Header-based “org” as IAM; no RLS; no SSO mapping; analytics org metadata still best-effort.

### 6. Biggest ownership truths

**Stamped ownership lives in Postgres column + mirrors to API `asserted_org_id`; unstamped legacy is a product/policy choice, not a security boundary.**

### 7. Biggest support truths

Enforcement + strict legacy toggles change **visibility**—not cryptographic tenant proof.

### 8. Biggest deployment truths

First PG touch may **ALTER + backfill**—needs DB permissions; epoch label documents contract generation, not legal certification.

### 9. Biggest replay truths

Support exports remain **non-repudiation-free** handoff aids; they describe posture and IDs, not full evidentiary replay.

### 10. Biggest continuity truths

Append paths preserve prior stamp when incoming payload omits org; sessions preserve prior org across saves.

### 11. Biggest remaining risks

Office-blind binding; DB role denial on auto-DDL; JSON-primary deployments still scan flat files for enforcement lists.

### 12. Biggest founder dependencies

Correct env toggles for enforcement/strict mode; operational clarity that headers are hints, not IAM.

### 13. What breaks at 30 offices

Process/runbook debt; binding confusion without filtered candidates.

### 14. What breaks at 100 offices

Operational/heavy human workflows; forensic attribution limits without IAM.

### 15. What breaks at enterprise sales

Expectations of SSO/RLS/compliance artifacts beyond honest assertion model.

### 16. Best next 10x leverage

Office-scoped binding candidate retrieval under enforcement.

### 17. Best next sprint

**Binding + session continuity hardening per office** (minimal SQL/filter extensions + tests).

### 18. Best next 3-month roadmap

IAM-aligned server-issued org mapping (when ready), DR drills for PG ownership backfills, operator dashboards for unstamped rates, attachment governance—not fake compliance theater.

### 19. What should NOT be built yet

Full RLS, SSO, RBAC platform, billing-per-tenant, “legal hold” exports, enterprise tenancy abstraction layer.

### 20. FINAL_ONE_LINE

**We promoted honest office hints into indexed Postgres reality and killed the worst list-query lies—without pretending headers are IAM.**

---

## OPERATOR NOTES

- Apply migration explicitly if auto-DDL is undesirable: `services/fiqa_api/db/schema/migrations/001_service_records_office_owner_org_id.sql`.  
- After deploy, verify `GET /api/inbox/support/deployment-manifest` shows updated `intake_schema_epoch` and expanded `office_ownership`.  
- If UI CI fails: upgrade Node per Vite engine constraint (see Phase 5).
