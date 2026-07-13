# P20 Track C — QA Reset and Tenant Boundary Evidence

| Field | Value |
|-------|-------|
| **Date** | 2026-07-12 |
| **Branch** | `sprint/p16-trust-layer` |
| **Scope** | Controlled QA Case-domain reset + server-derived `client_id` enforcement |
| **Cloud SQL** | `caseiq` on `caseiq-pilot-pg` (GCP) |
| **Commit** | `feat: complete P20 Track C pilot security foundation` (see git log) |

---

## 1. Pre-reset row counts

| Table / category | Count |
|------------------|------:|
| `service_records` (Cases) | **246** |
| `record_messages` | 317 |
| `structured_record_data` | 246 |
| `state_history` (timeline) | 2080 |
| `office_actions` | 0 |
| `intake_sessions` | 2 |
| `wecom_inbox_events` | 1 |
| `wecom_message_processed` | 186 |
| `wecom_reply_outbox` | 1 |
| `wecom_sync_cursors` | 1 |

**Label distribution (service_records only):**

| Label | Count |
|-------|------:|
| `workbench_test=true` | 159 |
| `demo_name` present | 93 |
| `client_id` present | 17 |

Rollback metadata (no customer content): `~/.searchforge_rollback/p20_track_c_qa_reset_qa_pre_20260713T044417Z.json`

Founder confirmed: all rows were QA / demo / smoke / synthetic. No real customer data.

---

## 2. Data categories cleared

- Case / service records and CASCADE children (`record_messages`, `structured_record_data`, `state_history`, `office_actions`)
- Intake session rows (`intake_sessions`)
- WeCom inbox pipeline derived rows (`wecom_inbox_events`, `wecom_message_processed`, `wecom_reply_outbox`, `wecom_sync_cursors`)

**Not touched:** database instance, schema/migrations, application configuration, auth identities, secrets, non-Case platform tables.

---

## 3. Post-reset row counts

| Table | Count |
|-------|------:|
| `service_records` | **0** |
| `record_messages` | 0 |
| `structured_record_data` | 0 |
| `state_history` | 0 |
| `intake_sessions` | 0 |
| WeCom pipeline tables | 0 |

Second reset run (idempotency): all purge counts **0**. Post snapshot: `~/.searchforge_rollback/p20_track_c_qa_reset_qa_post_20260713T044559Z.json`

---

## 4. Schema and config preserved

| Check | Result |
|-------|--------|
| Cloud SQL instance / database | **Preserved** |
| Case-domain tables (`service_records`, children, `intake_sessions`) | **6/6 present** |
| Schema migration applied | **No new migration** |
| Application / deploy configuration | **Unchanged** |

---

## 5. Client ownership rule

| Rule | Implementation |
|------|----------------|
| New Case `client_id` | Always `resolve_server_client_id()` → `CLIENT_ID` env or default `chen_kui` |
| Request body `client_id` | Ignored for ownership at persist (`case_store.save_case`) |
| `X-Org-Id` | Office hint only; **not** tenant authority |
| Workbench list scope | When `UNIFIED_INTAKE_ENFORCE_CASE_CLIENT_OWNERSHIP=1`, list uses server-resolved client |
| Workbench detail | `assert_case_client_access_allowed` → 403 `case_client_mismatch_v1` for foreign `client_id` |

**Cloud SQL proof (single synthetic case, then deleted):**

- Created `case_77445a287957` with spoof body `client_id=spoof_tenant`
- Persisted `client_id=chen_kui` (server-derived)
- Deleted immediately; `service_records` count returned to 0

---

## 6. Spoof protection

| Vector | Blocked |
|--------|---------|
| Spoofed request body `client_id` at create | **YES** — stored value is server `chen_kui` |
| Spoofed `X-Org-Id` changing list tenant scope | **YES** — list uses `resolve_server_client_id()`, not header |
| Foreign `client_id` on workbench GET | **YES** — 403 when enforcement enabled |

---

## 7. Tests and results

| Suite | Result |
|-------|--------|
| `tests/test_p20_track_c_qa_reset_and_tenant_boundary.py` (10 tests) | **PASS** |
| `tests/test_p20_track_b_backend_foundation.py` (5 tests, incl. provenance) | **PASS** |
| Reset idempotency on live Cloud SQL | **PASS** (second run deleted 0 rows) |

Run separately to avoid `app_main` import order side effects:

```bash
PYTHONPATH=. python3 -m pytest tests/test_p20_track_c_qa_reset_and_tenant_boundary.py -q
PYTHONPATH=. python3 -m pytest tests/test_p20_track_b_backend_foundation.py -q
```

---

## 8. Files changed

| File | Change |
|------|--------|
| `scripts/reset_p20_qa_case_domain.py` | **NEW** — QA case-domain reset + rollback snapshots |
| `services/fiqa_api/security/case_client_access.py` | **NEW** — server client resolution + enforcement helpers |
| `services/fiqa_api/db/service_record_repository.py` | `purge_case_domain_data`, client-scoped list/count |
| `services/fiqa_api/inbox_triage/case_store.py` | Server-derived `client_id` on create/backfill |
| `services/fiqa_api/inbox_triage/case_truth_repository.py` | `list_cases_for_client_scoped_read` |
| `services/fiqa_api/routes/inbox_triage.py` | Client-scoped workbench list/detail + manifest posture |
| `tests/test_p20_track_c_qa_reset_and_tenant_boundary.py` | **NEW** — Track C regressions |
| In-process E2E (`scripts/p19h3h_claim_h5_intake_smoke.py --in-process`) | **PASS** |

**Note:** Run Track C and Track B pytest modules in separate invocations to avoid `app_main` import-order side effects from `.env.cloudrun`.

---

## 9. Schema migration required

**NO** — uses existing `service_records.client_id` column and indexed filters.

---

## 10. Remaining Track C / production work (deferred)

### Track C follow-ups (this phase boundary)

1. Enable `UNIFIED_INTAKE_ENFORCE_CASE_CLIENT_OWNERSHIP=1` on Cloud Run after deploy review (currently opt-in).
2. Wire signed-broker token to authoritative `tenant_id_authoritative` (reserved in `IntakeTenantTruth`).
3. Reseed Chen Kui demo when ready: `bash scripts/reset_chen_kui_demo.sh --qa --reseed` (not run in this track).
4. Second-broker onboarding: tenant admin UI still deferred per P20 Constitution §11.

### Broader production blockers (explicitly out of scope for Track C Phase 1)

| Blocker | Status |
|---------|--------|
| Permanent broker identity (cryptographic IAM, not header hints) | **DEFERRED** |
| Connection pool for Postgres | **DEFERRED** |
| Optimistic concurrency / version column | **DEFERRED** |
| Transactional submit (single-transaction H5 submit) | **DEFERRED** |
| Broader multi-tenant (second broker, RLS, tenant admin) | **DEFERRED** |
| Production deployment (Cloud Run env flip + demo reseed) | **DEFERRED** — no deploy in this track |

---

## 11. Operator commands

```bash
# Inspect counts (dry-run)
PYTHONPATH=. python3 scripts/reset_p20_qa_case_domain.py --qa --dry-run

# Reset QA case domain
PYTHONPATH=. python3 scripts/reset_p20_qa_case_domain.py --qa

# Enable client boundary on workbench (after deploy review)
export UNIFIED_INTAKE_ENFORCE_CASE_CLIENT_OWNERSHIP=1
```
