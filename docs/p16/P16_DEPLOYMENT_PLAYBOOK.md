# P16 Deployment Playbook

**Date:** 2026-06-20  
**Status:** Frozen — paid pilot phase  
**Authority:** `docs/p16/P16_DECISION_FREEZE_V1.md`

---

## North Star

One stable QA URL. Always.

Pilot users, brokers, screenshots, demo scripts, onboarding docs, and QA reports  
reference **only** the stable QA URL. Preview URLs are engineering-internal only.

---

## Stable QA URL

```
https://ui-smoky-beta.vercel.app/add-car
```

**Backend:**

```
https://fiqa-api-1013093472160.us-west1.run.app
```

**Rules:**

| Rule | Required |
|------|----------|
| All QA validation runs against the stable URL | Yes |
| All pilot/broker/demo links use the stable URL | Yes |
| Stable URL must be aliased after every frontend deploy | Yes |
| Preview URLs go in release reports | No |
| Preview URLs go in documentation | No |
| Preview URLs go to pilot users | No |

---

## Deployment Flow

### Frontend Deploy

```bash
# 1. Deploy to Vercel
cd ui && vercel --prod --yes

# 2. Capture the preview URL from the output (engineering-internal only)
#    e.g. https://ui-xxxx-andys-projects-1f411b73.vercel.app

# 3. IMMEDIATELY alias to stable QA URL
vercel alias https://ui-xxxx-andys-projects-1f411b73.vercel.app ui-smoky-beta.vercel.app

# 4. Verify alias
curl -s -o /dev/null -w "%{http_code}" https://ui-smoky-beta.vercel.app/add-car
# Expected: 200
```

**Why alias first:** Every Vercel deploy creates a new unique preview domain. That domain  
is NOT in `ALLOWED_ORIGINS` on Cloud Run. Testing from it will fail with CORS errors.  
The stable alias (`ui-smoky-beta.vercel.app`) is already whitelisted — always test from there.

### Backend Deploy (when backend changed)

```bash
# Deploy paid pilot posture
bash scripts/deploy_paid_pilot.sh

# Verify health
curl -s https://fiqa-api-1013093472160.us-west1.run.app/health/live
# Expected: {"ok": true}
```

### CORS Validation

```bash
curl -s -X OPTIONS https://fiqa-api-1013093472160.us-west1.run.app/api/intake/add-car/extract \
  -H "Origin: https://ui-smoky-beta.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -i | grep -E "HTTP/|access-control-allow-origin"
# Expected: HTTP/2 200 + access-control-allow-origin: https://ui-smoky-beta.vercel.app
```

If CORS fails: `ui-smoky-beta.vercel.app` must be in `ALLOWED_ORIGINS` on Cloud Run.  
Check: `gcloud run services describe fiqa-api --region us-west1 --project optimal-disk-472305-e2 --format='value(spec.template.spec.containers[0].env)'`

### Functional Validation

```bash
# Extraction smoke test
curl -s -X POST https://fiqa-api-1013093472160.us-west1.run.app/api/intake/add-car/extract \
  -H "Origin: https://ui-smoky-beta.vercel.app" \
  -F "customer_name=Test User" \
  -F "phone=6265550000" \
  -F "garaging_zip=91101" | python3 -c "import sys,json; r=json.load(sys.stdin); print('OK' if r.get('packet') else 'FAIL')"
# Expected: OK
```

Manual validation (< 3 min): open `https://ui-smoky-beta.vercel.app/add-car` →  
complete intent → info → upload → extract → verify packet → copy packet.

---

## DEPLOY_CHECKLIST

```
□ Frontend deployed (vercel --prod --yes)
□ Stable alias updated (vercel alias [preview] ui-smoky-beta.vercel.app)
□ Stable alias verified (HTTP 200 from ui-smoky-beta.vercel.app/add-car)
□ Backend deployed (if backend changed)
□ Backend health verified ({"ok": true})
□ CORS verified (preflight HTTP 200 + correct allow-origin header)
□ Extraction endpoint verified (packet returned)
□ Manual QA flow verified (intent → upload → packet → copy)
```

---

## Required Release Report Format

Every deployment must end with this block. No preview URLs.

```
DEPLOY_STATUS

Frontend:   [deployed / skipped]
Backend:    [revision name / skipped]
Alias:      ui-smoky-beta.vercel.app → [preview URL it now points to]
CORS:       [pass / fail]
QA Validation: [pass / fail]

QA URL:
https://ui-smoky-beta.vercel.app/add-car
```

---

## Preview URL Policy

| Use | Allowed |
|-----|---------|
| Internal debugging | Yes |
| Temporary deploy verification before aliasing | Yes |
| Demo | No |
| Pilot / broker testing | No |
| Documentation | No |
| Screenshots | No |
| Release reports | No |

---

## CORS Maintenance Rule

`ui-smoky-beta.vercel.app` is permanently whitelisted in `ALLOWED_ORIGINS` on Cloud Run.  
Do not add preview URLs to `ALLOWED_ORIGINS`. If a preview URL needs CORS access,  
that is a signal the stable alias step was skipped — fix the process, not the whitelist.

Current `ALLOWED_ORIGINS` includes `ui-smoky-beta.vercel.app`.  
Cloud Run service: `fiqa-api`, region: `us-west1`, project: `optimal-disk-472305-e2`.

---

## A/B Testing Rule

Current state: single stable QA URL only.

Multiple public QA URLs are not allowed until:

- 20+ real pilot cases logged (CK-001 through CK-020)
- Measurable conversion metrics established
- Explicit decision recorded in `P16_DECISION_FREEZE_V1.md`

---

*Related: `docs/CURRENT_PRODUCT_SHAPE.md` · `docs/p16/P16_DECISION_FREEZE_V1.md` · `scripts/deploy_paid_pilot.sh`*
