# Case Builder Database Recovery Runbook

**Audience:** Founder + operator  
**Instance:** `caseiq-pilot-pg` (project `optimal-disk-472305-e2`, region `us-west1`)  
**Production SoR database:** `caseiq`  
**Cloud QA database (same instance):** `caseiq-qa`  
**Do not** restore over the live instance. Always recover into a **new** instance, verify, then cut over.

Related audit: [`docs/founder/PRE_PILOT_DATA_SAFETY_DR_AUDIT_2026-08-16.md`](../founder/PRE_PILOT_DATA_SAFETY_DR_AUDIT_2026-08-16.md)

---

## What “recover” means here

| Scenario | Preferred method | Expected data loss |
|----------|------------------|--------------------|
| Accidental **instance delete** blocked | Deletion protection (already ON) — stop and do not disable it | None |
| **Corrupt / DROP / bad write** inside the PITR window | Point-in-time **clone** to a new instance | Seconds–minutes (choose timestamp just before the bad event) |
| Corrupt data **outside** PITR window, or PITR window not ready yet | Restore a **daily backup** into a **new** instance | Up to ~24h (since last successful automated backup @ 03:00 UTC) |
| Need only QA data | Restore/clone then use database `caseiq-qa` only — never point Production at QA | N/A |

---

## 0. Stop the bleeding (first 5 minutes)

1. Do **not** run `gcloud sql backups restore` against `caseiq-pilot-pg`.
2. Do **not** disable `--deletion-protection` unless Google Support explicitly requires it for a controlled rebuild.
3. Optionally pause writes: scale Cloud Run `fiqa-api` to 0 / block traffic, or remove DB secret binding only if you know how to reverse it. Prefer traffic pause over secret surgery.
4. Note the approximate **UTC time** of the incident (`date -u`).

Check posture (read-only):

```bash
gcloud sql instances describe caseiq-pilot-pg --project=optimal-disk-472305-e2 \
  --format='yaml(state,settings.deletionProtectionEnabled,settings.retainBackupsOnDelete,settings.backupConfiguration)'

gcloud sql instances get-latest-recovery-time caseiq-pilot-pg \
  --project=optimal-disk-472305-e2

gcloud sql backups list --instance=caseiq-pilot-pg --project=optimal-disk-472305-e2 \
  --limit=10
```

If `get-latest-recovery-time` returns a window → use **Path A (PITR clone)**.  
If it errors with no valid window → use **Path B (backup → new instance)**.

---

## Path A — Point-in-time clone (preferred when window exists)

Creates a **new** independent instance. Does not overwrite Production.

```bash
# TARGET timestamp = just BEFORE corruption (RFC3339 UTC)
export RECOVERY_TS='2026-08-16T18:00:00.000Z'
export NEW_INSTANCE="caseiq-pilot-pg-recover-$(date -u +%Y%m%d%H%M)"

gcloud sql instances clone caseiq-pilot-pg "$NEW_INSTANCE" \
  --project=optimal-disk-472305-e2 \
  --point-in-time="$RECOVERY_TS"
```

Then:

1. Wait until `$NEW_INSTANCE` is `RUNNABLE`.
2. Confirm databases `caseiq` (and `caseiq-qa` if present) look correct via Cloud SQL Studio / authorized `psql` (counts, recent case ids).
3. Create a **new** Secret Manager secret version pointing at the recovery instance private IP / DB `caseiq` (do not destroy the old secret version until cutover is proven).
4. Point **only** `fiqa-api` at the new secret (Cloud Run update). Leave `fiqa-api-qa` alone until QA is deliberately rebuilt.
5. Hit `/health/live` and `/readyz` (`intake_path_ready: true`).
6. Spot-check 2–3 known cases in Workbench.
7. Keep the old instance (deletion-protected) as forensic evidence until Founder signs off; then schedule decommission.

---

## Path B — Daily backup into a new instance

Use when PITR window is missing or the needed time is older than log retention.

```bash
# Pick a SUCCESSFUL AUTOMATED (or ON_DEMAND) backup id
gcloud sql backups list --instance=caseiq-pilot-pg --project=optimal-disk-472305-e2 --limit=10

export BACKUP_ID='REPLACE_WITH_BACKUP_ID'
export NEW_INSTANCE="caseiq-pilot-pg-restore-$(date -u +%Y%m%d%H%M)"

# Restore into a NEW instance name — never the live name
gcloud sql backups restore "$BACKUP_ID" \
  --backup-instance=caseiq-pilot-pg \
  --restore-instance="$NEW_INSTANCE" \
  --project=optimal-disk-472305-e2 \
  --enable-point-in-time-recovery \
  --deletion-protection
```

If the CLI requires creating the target instance first, create an empty sibling instance with the same tier/region/network, then restore into it — still **never** restore onto `caseiq-pilot-pg` while it holds the only copy of pilot data.

Cut over with the same secret + Cloud Run steps as Path A.

---

## Path C — Instance was deleted (should be blocked)

Deletion protection is ON. If someone disabled it and deleted:

1. List backups still retained (`retainBackupsOnDelete` is ON).
2. Restore the newest good backup into a **new** instance (Path B).
3. If PITR logs survived deletion, clone with `--source-instance-deletion-time` (see `gcloud sql instances clone --help`).

---

## What a normal deploy cannot and can do

| Action | Wipes Production `caseiq`? |
|--------|----------------------------|
| `bash scripts/deploy_paid_pilot.sh` / `deploy_cloud_qa.sh` | **No** — deploys container + env; does not DROP databases |
| Cloud QA deploy with isolation PASS | **No** — binds `fiqa-service-record-database-url-qa` → `caseiq-qa` |
| Mistaken QA→Prod secret binding | **Blocked** by `p36_deploy_safety_check.py` |
| Prod with fixture / Golden QA flags still ON | **Does not drop the DB**, but authenticated support/intake callers can seed/reset **cases** — treat as operational risk, not backup failure |

---

## Post-recovery checklist

- [ ] New instance `RUNNABLE`, deletion protection ON, backups + PITR ON  
- [ ] Production secret points at `caseiq` on the recovery instance  
- [ ] `fiqa-api` `/readyz` → `intake_path_ready: true`  
- [ ] Workbench shows expected pilot cases  
- [ ] Founder records incident time, recovery path (A/B), and estimated data loss  
- [ ] Old instance retained ≥7 days before any delete  

---

## Commands that are forbidden during an incident

- `gcloud sql instances delete caseiq-pilot-pg`
- `gcloud sql backups restore … --restore-instance=caseiq-pilot-pg` (overwrite live)
- Disabling deletion protection “to make restore easier”
- Pointing Production at `caseiq-qa` or the QA DB secret

---

## Artifact Registry cleanup (images, not customer data)

Policy file in-repo: [`configs/gcr_cleanup_policies.json`](../../configs/gcr_cleanup_policies.json)  
Applied to `gcr.io` (`us`) in **dry-run** on 2026-08-16 (untagged >30d delete + keep 20 versions).  
Does not affect Cloud SQL recovery.
