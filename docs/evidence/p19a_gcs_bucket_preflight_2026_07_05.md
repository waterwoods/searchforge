# P19A-0 — GCS Bucket + IAM + Storage Preflight Evidence

**Date:** 2026-07-05  
**Branch:** `sprint/p16-trust-layer` @ `83ee7ff`  
**GCP project:** `optimal-disk-472305-e2`  
**Final verdict:** **PASS**

---

## 1. Pre-check

| Check | Result |
|-------|--------|
| Branch | `sprint/p16-trust-layer` |
| Working tree | clean |
| QA gate (`check_chen_kui_demo_environment.sh --cloud-api`) | **PASS** |
| Cloud Run reads Cloud SQL | `provider=gcp-cloud-sql host=10.73.0.3 db=caseiq` |
| Neon | legacy only — **not QA truth** |
| Cloud Run revision | `fiqa-api-00148-mk2` (us-west1) |

---

## 2. Cloud Run service account

| Item | Value |
|------|-------|
| Service | `fiqa-api` |
| Service account | `1013093472160-compute@developer.gserviceaccount.com` |
| Project roles (storage-relevant) | `roles/editor`, `roles/cloudsql.client` |
| Editor role present | **yes** — not removed this round |
| Least-privilege target (future) | Bucket-level `roles/storage.objectUser` only; remove project `roles/editor` in a separate IAM tightening pass |

**Note:** This round adds bucket-level permission only. No project-level storage admin added. No existing roles deleted.

---

## 3. GCS bucket

| Item | Value |
|------|-------|
| Bucket name | `caseiq-wecom-media-qa` |
| URI | `gs://caseiq-wecom-media-qa/` |
| Status | **created** (did not exist before this run) |
| Location | `US-WEST1` (region) |
| Uniform bucket-level access | **enabled** (`uniform_bucket_level_access: true`) |
| Public access prevention | **enforced** (`public_access_prevention: enforced`) |
| Default storage class | `STANDARD` |

**Constraints honored:**

- Not using legacy `smartsearchx-bucket`
- Not public
- Co-located with Cloud Run (`us-west1`)

---

## 4. Bucket-level IAM

| Member | Role | Scope |
|--------|------|-------|
| `serviceAccount:1013093472160-compute@developer.gserviceaccount.com` | `roles/storage.objectUser` | `gs://caseiq-wecom-media-qa` only |

**Not changed:** other buckets, project-level storage admin, service account identity, existing project roles.

---

## 5. Storage preflight (upload / read / delete)

Test file: `/tmp/p19a_wecom_media_preflight.txt` (synthetic text — **no real customer data**)

| Step | Path | Result |
|------|------|--------|
| Upload | `gs://caseiq-wecom-media-qa/wecom/preflight/2026/07/p19a_wecom_media_preflight.txt` | **PASS** |
| List | `gs://caseiq-wecom-media-qa/wecom/preflight/` | **PASS** |
| Read (cat) | same object | **PASS** — content matched |
| Delete | same object | **PASS** — object removed |

---

## 6. Object path pattern (P19 spec alignment)

Production path (from P19 spec §8):

```
gs://caseiq-wecom-media-qa/wecom/<external_userid>/<yyyy>/<mm>/<msg_id>.<ext>
```

Preflight used:

```
gs://caseiq-wecom-media-qa/wecom/preflight/<yyyy>/<mm>/p19a_wecom_media_preflight.txt
```

---

## 7. Private access / Workbench preview note

| Check | Finding |
|-------|---------|
| Bucket publicly accessible | **No** — public access prevention enforced |
| Direct public URL | **Not available** — by design |
| Future Workbench preview | Backend proxy or signed URL required; P19 spec §8 recommends signed URL or backend proxy |
| P19A metadata approach | Store `storage_uri` in Postgres metadata only; no binary in DB; no public URL exposure in MVP |

No signed URL code implemented this round. Workbench unchanged.

---

## 8. Scope guardrails (this round)

| Item | Changed? |
|------|----------|
| WeCom media detection/download code | **No** |
| `sync_msg.py` / `slice.py` | **No** |
| DB schema | **No** |
| Cloud SQL / VPC / NAT / Secret | **No** |
| WeCom callback | **No** |
| Cloud Run deploy | **No** |
| Vercel deploy | **No** |
| Neon used | **No** |
| `smartsearchx-bucket` used | **No** |
| Real customer images uploaded | **No** |

---

## 9. Next step

**P19A Loop 1 — WeCom Media Intake Foundation**

Prerequisites met: dedicated private bucket, bucket-level IAM for Cloud Run SA, upload/read/delete preflight verified.
