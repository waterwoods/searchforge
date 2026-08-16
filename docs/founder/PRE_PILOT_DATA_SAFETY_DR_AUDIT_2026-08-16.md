# Pre-Pilot Data Safety + Disaster Recovery Audit

**Date:** 2026-08-16  
**Scope:** Case Builder / Unified Intake paid-pilot SoR on GCP  
**Method:** Live read-only `gcloud` inspection first; then only safe, reversible config patches  
**Production app deploy:** not performed (not authorized)

---

## Verdict (one line)

Durability controls on Cloud SQL are now **pilot-adequate** (deletion protection + automated backups + PITR **configured**). **HOLD** before storing 5–20 real cases on Production until Founder turns off Production QA-fixture flags and confirms the PITR recovery window is live.

---

## A. Current data-safety grade: **3.5 / 5**

| Before this audit | After config fixes |
|-------------------|--------------------|
| ~2 / 5 (backups only; no deletion protection; PITR off) | **3.5 / 5** |

Not 5/5: shared Prod/QA instance, Cloud Run default SA still has `roles/editor`, several secrets still plaintext env on Cloud Run, Production still carries QA fixture surfaces, PITR continuous window not yet visible to the API.

---

## B. Current system of record (SoR)

| Item | Value |
|------|--------|
| Authoritative store | **Cloud SQL Postgres 15** database **`caseiq`** |
| Instance | `caseiq-pilot-pg` (`db-f1-micro`, zonal, `us-west1-b`, 10 GB SSD) |
| App path | Cloud Run `fiqa-api` → Secret `fiqa-service-record-database-url-cloudsql-private` → private IP `10.73.0.3` → DB `caseiq` |
| Not SoR | JSON files, Qdrant, Vercel, Mini Program local storage |

Verified secret target (credentials redacted): host `10.73.0.3`, database **`caseiq`**.

---

## C. Backup status

| Check | Evidence |
|-------|----------|
| Automated backups | **ON**, daily start `03:00` UTC |
| Retention | **7** backups (`retainedBackups: 7`) |
| Recent success | Multiple `SUCCESSFUL` `AUTOMATED` runs through 2026-08-16; extra automated snapshot created during PITR enable (~16:54 UTC) |
| On-demand | `pre-chen-demo-known-customer-20260729` present |
| Retain backups on delete | **ON** (patched this audit) |

“Backup enabled” alone was **not** accepted as recovery proof — list + describe + successful `BACKUP_VOLUME` operations were verified.

---

## D. PITR status and recovery window

| Check | Status |
|-------|--------|
| `pointInTimeRecoveryEnabled` | **True** (patched this audit; was unset/false) |
| `transactionLogRetentionDays` | **7** |
| Log storage | **`CLOUD_STORAGE`** after enable |
| Continuous window API | **`get-latest-recovery-time` → no valid window yet** (checked ~10–15 min after enable) |

**Interpretation:** PITR is **configured correctly**, but the **continuous second-level window is still warming**. Until `gcloud sql instances get-latest-recovery-time caseiq-pilot-pg` returns a window:

- Recover with **daily backups** (Path B in the runbook).
- Maximum loss vs last backup ≈ **up to ~24 hours** of writes.

After the window appears (usually once WAL archival is healthy; often within hours):

- Recover to any second in the last **≤7 days** of logs (Path A).
- Practical RPO inside the window: **seconds–minutes** (ops delay), not “last night’s backup.”

Founder check (no engineering required beyond running one command or asking an agent):

```bash
gcloud sql instances get-latest-recovery-time caseiq-pilot-pg --project=optimal-disk-472305-e2
```

---

## E. Deletion protection status

| Setting | Before | After |
|---------|--------|-------|
| `settings.deletionProtectionEnabled` | **false** | **true** |
| `retainBackupsOnDelete` | unset | **true** |

A console / CLI instance delete of `caseiq-pilot-pg` is now blocked until protection is explicitly disabled.

---

## F. Production / QA isolation

| Layer | Status |
|-------|--------|
| Cloud Run services | `fiqa-api` (prod) vs `fiqa-api-qa` |
| Databases | `caseiq` vs `caseiq-qa` on **same** instance |
| DB secrets | Distinct SM secrets; live bindings verified |
| Deploy guards | `p36_verify_cloud_qa_isolation.py` + `p36_deploy_safety_check.py` fail-closed |

**Gap (accepted for cost, not fixed here):** one `db-f1-micro` shared compute/connection pool — QA load can still hurt Production availability. Logical data isolation is real; blast-radius isolation is not.

---

## G. Secret Manager status

| Secret | Used by live pilot? |
|--------|---------------------|
| `fiqa-service-record-database-url-cloudsql-private` | Yes — Production DB URL |
| `fiqa-service-record-database-url-qa` | Yes — Cloud QA DB URL |
| `fiqa-openai-api-key` / `fiqa-qdrant-api-key` / `fiqa-h5-task-token-secret` | Yes — both services |
| `fiqa-wechat-mp-app-secret` | Exists in SM; **QA still has plaintext `WECHAT_MP_APP_SECRET` env** |
| Legacy `fiqa-service-record-database-url` | Versions **disabled** (good) |
| `fiqa-service-record-database-url-cloudsql` | Still has enabled versions (public-IP era); **not** bound on live `fiqa-api` |

**Still plaintext on Cloud Run env (describe, values not printed):**  
`UNIFIED_INTAKE_INTAKE_API_KEY`, `UNIFIED_INTAKE_SUPPORT_API_KEY`, WeCom token/AES/agent secret (prod + QA), WeChat MP app secret (QA).

Moving those into Secret Manager requires a **Cloud Run revision update** → left as Founder-authorized deploy work.

**IAM note:** Cloud Run uses the default compute SA, which has **`roles/editor`** on the project (over-privileged for pilot). Accessor bindings on the fiqa secrets are present. Narrowing Editor is reversible but not “small” without a break-glass test — **not changed**.

---

## H. Maximum plausible data loss after the fixes

| Failure mode | Max plausible loss |
|--------------|--------------------|
| Instance delete misclick | **Blocked** (deletion protection) |
| DB corrupt / bad SQL / app wipe of rows — **PITR window live** | **Seconds–minutes** of work after chosen recovery timestamp (≤7 day log window) |
| Same — **PITR window not yet live** (current API state) | **Up to ~24h** to last successful automated backup |
| Outside 7-day backup retention | **Unrecoverable** for that age of data (not expected for a 5–20 case pilot) |
| Authenticated fixture/reset on Production | Case-level damage **without** needing backups to fail — see §L |

Honest answer to the Founder scenario *“If tomorrow we accidentally delete or corrupt the Case Builder database…”*:

1. **Delete the instance** → GCP should refuse; if protection were removed and delete succeeded, restore from retained backups into a **new** instance (runbook Path B/C).  
2. **Corrupt the data** → clone/restore to a **new** instance; cut Secret Manager + Cloud Run over after verification. **Never restore onto the live name while it is the only copy.**  
3. **How much loss** → today, plan for **≤24h** until you personally see a non-empty PITR window; after that window exists, plan for **minutes**, not a business day.

Exact steps: [`docs/runbooks/CASE_BUILDER_DATABASE_RECOVERY.md`](../runbooks/CASE_BUILDER_DATABASE_RECOVERY.md).

---

## I. Exact recovery procedure

See runbook (Paths A/B/C). Summary:

1. Freeze writes / pause traffic.  
2. Prefer **PITR clone** to a new instance when `get-latest-recovery-time` works.  
3. Else **backup restore** to a new instance.  
4. Verify row counts / known cases.  
5. New secret version → point `fiqa-api` only.  
6. Keep old instance for forensics.

---

## J. Changes actually made (this audit)

| Change | Result |
|--------|--------|
| Cloud SQL `--deletion-protection` | **ON** |
| Cloud SQL `--enable-point-in-time-recovery` + `--retained-transaction-log-days=7` | **ON** (logs → Cloud Storage) |
| Cloud SQL `--retain-backups-on-delete` | **ON** |
| Artifact Registry `gcr.io` cleanup policy | **Applied in dry-run**: delete untagged >30d + keep minimum 20 versions |
| Application deploy / secret value changes / restore tests | **Not done** |

Post-change verification:

- Instance `RUNNABLE`
- `fiqa-api` and `fiqa-api-qa` `/health/live` → 200  
- Both `/readyz` → `intake_path_ready: true`

---

## K. Cost impact per month

| Item | Estimate |
|------|----------|
| Deletion protection / retain-backups-on-delete | **$0** |
| PITR WAL in Cloud Storage (Enterprise) | **~$0–2** at current tiny DB size (GCP documents Cloud Storage PITR logs as no extra per-instance fee; disk duplicates remain small) |
| Existing 7 daily backups | Unchanged (~**$1–2** already in baseline) |
| Artifact Registry dry-run policy | **$0** until dry-run is disabled; then storage should **fall** from ~77 GB over time |
| **Net new monthly** | **≈ $0–3** |

No second backup product was added.

---

## L. Anything still requiring Founder action

1. **Confirm PITR window** (one command above) before treating RPO as “minutes.”  
2. **Production QA surfaces (HOLD driver):** live `fiqa-api` still has `ENABLE_P26H_FIXTURE_RUNNER=1`, `UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1`, `ENABLE_GOLDEN_QA_LAUNCH=1`. Fixing requires a Founder-authorized Production env/revision update (deploy scripts already refuse shipping those flags).  
3. **Optional:** flip Artifact Registry cleanup from dry-run to live after reviewing dry-run logs (~1 day):  
   `gcloud artifacts repositories update gcr.io --location=us --no-remote-dry-run` (confirm current flag name in CLI help before running).  
4. **Optional later:** move WeCom / intake / support keys into Secret Manager; replace default compute `roles/editor` with least privilege.  
5. **Optional later:** separate Cloud SQL instance for QA when revenue justifies ~2× DB floor cost.

---

## M. GO / HOLD for storing 5–20 real pilot cases

### **HOLD** on Production SoR — until item L.2 is done and L.1 shows a PITR window.

**Why not GO yet:** durability is mostly fixed, but Production still exposes authenticated case seed/reset tooling, and continuous PITR is configured but not yet proven by the recovery-time API.

**When it becomes GO:**

1. PITR `get-latest-recovery-time` returns a real window, **and**  
2. Production fixture / Golden QA flags are off on `fiqa-api`, **and**  
3. Real customer traffic uses Production (`fiqa-api` + `caseiq`), not QA simulate login.

Durability alone after this audit is **good enough for a 5–20 case pilot**; the HOLD is operational foot-guns, not missing backups.

---

## Teaching review (10 lines) — BACKUP vs PITR vs DELETION PROTECTION vs SECRET MANAGER

1. A **backup** is a saved photo of the whole database at one moment (here: about once a day at 03:00 UTC, keeping the last 7 photos).  
2. If you only have backups, and you mess up at 8pm, you rewind to last night and **lose the whole day’s new cases**.  
3. **PITR** keeps a continuous diary of every change (WAL logs) so you can rewind to **8:00:00pm**, not just “yesterday’s photo.”  
4. PITR needs backups underneath — the diary replays from the nearest photo forward.  
5. **Deletion protection** is a safety lock on the database *machine* so one wrong “delete instance” click cannot vaporize the server.  
6. Deletion protection does **not** stop bad SQL or a buggy app from deleting rows inside the database.  
7. **Secret Manager** is a locked vault for passwords and API keys so they are not pasted into deploy files or visible as ordinary env text.  
8. Putting the DB URL in Secret Manager does not back up customer cases — it only protects **credentials**.  
9. For pilot data: backups = daily seatbelt, PITR = time machine, deletion protection = “don’t crush the car,” Secret Manager = “don’t leave the keys on the dashboard.”  
10. Recover by cloning/restoring into a **new** instance first — never overwrite the only living copy while you still need it.
