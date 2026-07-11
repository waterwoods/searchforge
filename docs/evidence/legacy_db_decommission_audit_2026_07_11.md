# Legacy DB Decommission Audit — 2026-07-11

**Branch:** `sprint/p16-trust-layer`  
**Auditor:** Cursor agent (automated + manual verification)  
**Executive status:** **READY TO ISOLATE** (conditional on backup before delete)

---

## 1. Executive status

| Gate | Result |
|------|--------|
| Cloud SQL is runtime SSOT | **PASS** — production Cloud Run binds `fiqa-service-record-database-url-cloudsql-private` |
| Neon removed from default paths | **PASS** — changes in this audit |
| Legacy access explicit + read-only | **PASS** — `apply_legacy_neon_readonly_env()` + audit script |
| Data completeness vs Neon | **PASS** — Cloud SQL `updated_at_max` newer; zero ID overlap = migration fork |
| Safe to delete Neon now | **NO** — export stale fork backup first (289 historical rows) |

**Recommendation:** **Safe to isolate; not safe to delete yet.** Revoke Neon app credentials only after verified backup.

---

## 2. Legacy reference inventory

| Location | Classification | Notes |
|----------|----------------|-------|
| `.env.cloudrun` `SERVICE_RECORD_DATABASE_URL` | **STALE / DANGEROUS** | Still points at Neon host `*.neon.tech` — now stripped on normal startup |
| `scripts/demo_db_resolve.py` `LEGACY_NEON_SECRET` | **EXPLICIT LEGACY PATH** | Secret `fiqa-service-record-database-url`; `legacy-neon` target + `apply_legacy_neon_readonly_env()` |
| `services/fiqa_api/app_main.py` `load_dotenv(.env.cloudrun)` | **ACTIVE DEFAULT PATH** → **FIXED** | Strips Neon DB URLs after dotenv load |
| `scripts/run_demo_local.sh` | **ACTIVE DEFAULT PATH** → **FIXED** | Overrides with Cloud SQL; hard-fails if unavailable (unless `RUN_DEMO_LOCAL_DB=json`) |
| `scripts/p19m1_mint_prototype_token.py` | **ACTIVE DEFAULT PATH** → **FIXED** | Requires `--cloud-sql` or `--json-local`; no default Neon |
| `scripts/p19m1a_devtools_e2e_smoke.py` | **ACTIVE DEFAULT PATH** → **FIXED** | HTTP mode requires `--cloud-sql` or `--json-local` |
| `scripts/seed_chen_kui_demo.py --target legacy-neon` | **EXPLICIT LEGACY PATH** → **BLOCKED** | Writes disabled; exits 2 |
| `scripts/reset_chen_kui_demo.sh --legacy-neon` | **EXPLICIT LEGACY PATH** → **BLOCKED** | Exits 2 |
| `scripts/legacy_db_metadata_audit.py` | **READ-ONLY ROLLBACK** | Break-glass metadata compare |
| `scripts/deploy_cloud_run_core.sh` | **ACTIVE DEFAULT PATH** | Rejects Neon secret name; default Cloud SQL private |
| Production Cloud Run `fiqa-api` | **ACTIVE DEFAULT PATH** | `SERVICE_RECORD_DATABASE_URL` ← `fiqa-service-record-database-url-cloudsql-private` |
| `docs/evidence/p19m2a_*` `--cloudrun-parity` | **STALE / DANGEROUS** | Documentation only; flag removed from scripts |
| `tests/test_*.py` isolated JSON | **TEST ONLY** | Explicit `pop SERVICE_RECORD_DATABASE_URL` |
| `configs/demo.env.example` | **DOCUMENTATION ONLY** | Warns against Neon in `.env.cloudrun` |
| `miniapp/README.md` `--shared-local-store` | **DOCUMENTATION ONLY** | Stale; JSON dev path only |
| GCP Secret `fiqa-service-record-database-url` | **READ-ONLY ROLLBACK** | Neon URL versions preserved for break-glass |
| GCP Secret `fiqa-service-record-database-url-cloudsql-private` | **ACTIVE DEFAULT PATH** | QA + production SSOT |

---

## 3. Current DB routing matrix

| Path | Database | Evidence |
|------|----------|----------|
| Production Cloud Run `fiqa-api` | **GCP Cloud SQL** `caseiq` @ `caseiq-pilot-pg` | `gcloud run services describe` → secret `fiqa-service-record-database-url-cloudsql-private` |
| `run_demo_local.sh` (default) | **GCP Cloud SQL** | `shell_export_qa_postgres_env()` after stripping Neon |
| `run_demo_local.sh` `RUN_DEMO_LOCAL_DB=json` | **Isolated JSON** | Explicit flag |
| `p19m1_mint --cloud-sql` | **GCP Cloud SQL** | `bootstrap_prototype_cloud_sql_env()` |
| `p19m1a E2E --cloud-sql` | **GCP Cloud SQL** | Same bootstrap |
| `p19m1a E2E --inprocess` / `--json-local` | **Isolated JSON** | Temp file / explicit flag |
| `seed_chen_kui_demo.py --target qa` | **GCP Cloud SQL** | `apply_qa_postgres_env()` |
| `seed_chen_kui_demo.py --target local` | **JSON** | `data/unified_intake_cases.json` |
| Deploy smokes `p19h3*` | **GCP Cloud SQL** | `load_cloudrun_env_skip_db()` + `apply_qa_postgres_env()` |
| Direct `uvicorn app_main` | **No Neon** | Neon URL stripped; Postgres only if set elsewhere |
| `legacy_db_metadata_audit.py` | **Neon + Cloud SQL read-only** | Explicit audit tool |
| `apply_legacy_neon_readonly_env()` | **Neon read-only** | Break-glass; `LEGACY_NEON_READONLY=1` |

---

## 4. Neon vs Cloud SQL metadata comparison

**Audit artifact:** `docs/evidence/legacy_db_metadata_audit_2026_07_11.json`  
**Command:** `PYTHONPATH=. python3 scripts/legacy_db_metadata_audit.py`

| Metric | Legacy Neon | GCP Cloud SQL |
|--------|-------------|---------------|
| `service_records` rows | 289 | 239 |
| `created_at` range | 2026-03-31 → 2026-07-11 | 2026-07-05 → 2026-07-11 |
| `updated_at_max` | **2026-07-11T18:51:12Z** | **2026-07-11T21:36:05Z** |
| `chen_kui_p18` demo rows | 5 | 5 |
| `workbench_test=true` | 19 | 151 |
| Record ID overlap | **0** | **0** |

Interpretation: complete migration fork (new IDs on Cloud SQL since ~2026-07-05). Cloud SQL receives all current writes; Neon stopped updating ~2h before audit.

---

## 5. Unique / newer record findings

- **Neon-only IDs:** 289 (entire Neon dataset — stale fork)
- **Cloud SQL-only IDs:** 239 (current SSOT)
- **Neon newer than Cloud SQL:** **NO** (`neon_newer_than_cloud_sql: false`)
- **Stop gate:** **CLEAR** for isolation (not for deletion without backup)

Neon may contain pre-migration history not copied with same `record_id`s. Export backup recommended before credential revocation; not a blocker for isolating runtime paths.

---

## 6. Changes made

| File | Change |
|------|--------|
| `scripts/demo_db_resolve.py` | `is_neon_database_url`, `strip_neon_database_urls_from_env`, `apply_legacy_neon_readonly_env` |
| `scripts/legacy_db_metadata_audit.py` | **NEW** read-only Neon vs Cloud SQL compare |
| `services/fiqa_api/app_main.py` | Strip Neon DB URLs after `.env.cloudrun` load |
| `scripts/run_demo_local.sh` | Hard-fail without Cloud SQL (unless explicit JSON) |
| `scripts/restore_8001_readiness.sh` | Strip Neon + Cloud SQL override |
| `scripts/seed_chen_kui_demo.py` | Block `--target legacy-neon` writes |
| `scripts/reset_chen_kui_demo.sh` | Block `--legacy-neon` |
| `services/fiqa_api/db/service_record_repository.py` | Read-only session when `LEGACY_NEON_READONLY=1` |
| `scripts/p19h3*_smoke.py` (10 files) | `load_cloudrun_env_skip_db()` instead of full `.env.cloudrun` |
| `scripts/p19h3h_claim_h5_intake_smoke.py`, `p19h3i_claim_task_dashboard_smoke.py` | Same |
| `tests/test_demo_db_resolve.py` | **NEW** isolation guardrail tests |
| `configs/demo.env.example` | Warn against Neon in `.env.cloudrun` |

**Not changed (operator action later):** `.env.cloudrun` still contains Neon URL locally (gitignored). Remove or comment `SERVICE_RECORD_DATABASE_URL` line on laptop when convenient.

---

## 7. Remaining legacy read-only access path

```bash
# Metadata audit (both sources, read-only)
PYTHONPATH=. python3 scripts/legacy_db_metadata_audit.py

# Programmatic break-glass (read-only session)
PYTHONPATH=. python3 -c "
from scripts.demo_db_resolve import apply_legacy_neon_readonly_env
print(apply_legacy_neon_readonly_env().masked())
"
```

Requirements met: explicit, warned, read-only session, no seed/reset/write, not default, not CI.

---

## 8. Tests and verification

| Test | Result |
|------|--------|
| `pytest tests/test_demo_db_resolve.py` | **7 passed** |
| `p19m1a_devtools_e2e_smoke.py --inprocess` | **PASS** |
| Mint without flag | **FAIL** (requires `--cloud-sql` or `--json-local`) ✓ |
| `bootstrap_prototype_cloud_sql_env()` | **Cloud SQL** (`is_neon=False`) ✓ |
| `legacy_db_metadata_audit.py` | **PASS** (stop_gate=false) |
| Production Cloud Run DB secret | **Unchanged** (Cloud SQL) ✓ |

---

## 9. Credential / secrets audit

| Secret / credential | Status | Later action |
|---------------------|--------|--------------|
| `fiqa-service-record-database-url` (Neon) | Active in Secret Manager | Disable versions after backup |
| `fiqa-service-record-database-url-cloudsql-private` | **Production SSOT** | Keep |
| `.env.cloudrun` `SERVICE_RECORD_DATABASE_URL` | Local Neon (gitignored) | Remove line after isolation verified |
| Tracked repo files | **No full DB URLs committed** | — |
| Cloud Run describe | API keys visible in describe output | Pre-existing; out of scope |

**Do not revoke yet** until Neon export verified.

---

## 10. Final decommission checklist

- [ ] Export full Neon `service_records` backup (`pg_dump` or audit JSON + row export)
- [ ] Verify backup restorable / row count matches (289)
- [ ] Remove `SERVICE_RECORD_DATABASE_URL` from developer `.env.cloudrun` copies
- [ ] Disable Neon secret versions in Secret Manager (`fiqa-service-record-database-url`)
- [ ] Revoke Neon database role / password
- [ ] Remove CI/CD references (none active)
- [ ] Archive connection metadata (host `*.neon.tech`, db `neondb`) in runbook
- [ ] Delete Neon project/database
- [ ] Post-delete smoke: Cloud Run + `check_chen_kui_demo_environment.sh --cloud-api`

---

## 11. Exact recommendation

**Safe to isolate — not safe to delete.**

- Runtime, QA, demo, E2E, and deploy paths now target **GCP Cloud SQL** exclusively.
- Neon is reachable only via explicit read-only audit/break-glass tooling.
- Neon holds a **stale fork** (289 rows, last write before Cloud SQL current max). Export backup before credential revocation and deletion.

**Next action:** Operator removes `SERVICE_RECORD_DATABASE_URL` from local `.env.cloudrun`, runs `check_chen_kui_demo_environment.sh --cloud-api`, then schedules Neon `pg_dump` backup before secret revocation.

---

## 12. Final decommission completion — 2026-07-11 (post-backup)

**Executive status:** **DECOMMISSION IN PROGRESS** — backup verified, credentials revoked; Neon console deletion pending manual step.

### Final Neon backup

| Field | Value |
|-------|-------|
| Backup path | `~/secure_backups/searchforge_legacy_neon_20260711.dump` |
| Metadata path | `~/secure_backups/searchforge_legacy_neon_20260711.meta.json` |
| Dump size | 188,408 bytes |
| SHA-256 | `36f4f1914fcc09200beb93f1efad9497eda94383af5cdbc333fd62fd236c3592` |
| Format | PostgreSQL custom compressed (`pg_dump -Fc`) |
| Pre-delete row count | 289 (`legacy_db_metadata_audit.py`) |
| Verification | `pg_restore --list` OK — 11 `TABLE DATA` entries including `service_records`, `record_messages`, `state_history`, `intake_sessions`, WeCom tables |
| Committed to Git | **NO** (stored outside repo) |

### Local configuration cleanup

- `.env.cloudrun` `SERVICE_RECORD_DATABASE_URL` (Neon) **neutralized** — replaced with comment `LEGACY_NEON_REMOVED 2026-07-11`
- No active `DATABASE_URL` / `SERVICE_RECORD_DATABASE_URL` keys remain in local `.env.cloudrun`
- `bootstrap_prototype_cloud_sql_env()` resolves **GCP Cloud SQL** (`provider=gcp-cloud-sql`, `is_neon=False`)

### Legacy secret revocation

| Secret | Action | Versions |
|--------|--------|----------|
| `fiqa-service-record-database-url` (legacy Neon) | **DISABLED** | v1, v2 |
| `fiqa-service-record-database-url-cloudsql-private` (SSOT) | **UNCHANGED enabled** | v1 |

- Production Cloud Run `fiqa-api` revision `fiqa-api-00200-jxs` binds `fiqa-service-record-database-url-cloudsql-private:latest`
- No deploy script requires legacy Neon secret (`deploy_cloud_run_core.sh` rejects Neon secret name)

### Neon database / project deletion

| Item | Value |
|------|-------|
| Neon endpoint slug | `nameless-bird-akrtm0v2` |
| Neon host (pooler) | `ep-nameless-bird-akrtm0v2-pooler.c-3.us-west-2.aws.neon.tech` |
| Database name | `neondb` |
| Verified backup exists | **YES** |
| Credentials disabled | **YES** |
| Automatic deletion | **NOT POSSIBLE** — no `neonctl` auth on this machine |

**Manual step remaining (Founder):**

1. Open [Neon Console](https://console.neon.tech)
2. Select project containing endpoint `nameless-bird-akrtm0v2` (database `neondb`)
3. Confirm backup checksum `36f4f191…c3592` is stored at `~/secure_backups/`
4. **Settings → Delete project** (or delete branch/database if project has other uses)
5. Confirm deletion — no Cloud Run or local path can reconnect (secret versions disabled)

### Post-revocation verification

| Check | Result |
|-------|--------|
| Cloud SQL bootstrap | **PASS** — `gcp-cloud-sql`, not Neon |
| Cloud Run `/readyz` | **PASS** — HTTP 200 |
| `legacy_db_metadata_audit.py` | **FAIL CLOSED** — cannot access disabled Neon secret ✓ |
| `pytest tests/test_demo_db_resolve.py` | **PASS** — 7/7 |
| `p19m1a_devtools_e2e_smoke.py --inprocess` | **PASS** |
| Cloud SQL `chen_kui_p18` rows | **PASS** — ≥5 rows in QA DB |
| Chen Kui API name visibility | **WARN** — API page pagination (pre-existing; not Neon-related) |

### Updated recommendation

**Legacy Neon credentials revoked. Safe to delete Neon project after Founder completes console step above.** Cloud SQL remains sole SSOT. Do not re-enable secret versions `fiqa-service-record-database-url` v1/v2 unless performing disaster recovery from backup.
