# P16 Freeze Commit Summary

**Date:** 2026-06-17  
**Branch:** `sprint/p16-trust-layer`  
**Commit message:** P16 Decision Freeze V1 — freeze architecture decisions, freeze product scope, establish trusted packet north star, complete bakeoff reviews, prepare trust layer sprint

---

## Decisions Frozen

### Product

| Decision | Value |
|----------|-------|
| North star flow | Customer Docs → Trusted Packet → Broker |
| Time goal | ~10 min → ~2–3 min per add-car intake |
| Deliverable | Trusted Packet with Copy Fields + Source Attribution |
| Customer confirmation | **Deferred** — broker reviews packet |
| WeChat integration | **Out of scope** |
| Trade-in automation | **Out of scope** |

### Scope (Included)

- Customer intake: Name, Phone, Garaging ZIP
- Upload: PDF, JPG, PNG, HEIC
- Gemini Flash 2.5 extraction
- VIN validation + warnings
- Basic packet review + mobile support

### Scope (Excluded)

CRM, policy management, claims, renewals, Document AI, PDF generation, customer accounts, auth system, multi-broker platform, WeChat native, complex trade-in, customer confirmation workflow, screenshot crop attribution

---

## Architecture Frozen

| Layer | Stack |
|-------|-------|
| Frontend | React 18, Ant Design 5, Zod, Zustand |
| Backend | FastAPI, Postgres, Cloud Run, GCS |
| Extraction | Gemini Flash 2.5 |
| Deploy | Vercel (UI) + Cloud Run (API) |

**Rejected:** shadcn/ui migration, Document AI, UploadThing, workflow engines

---

## Scope Frozen — Trust Layer Sprint

Only six capabilities:

1. Upload  
2. Extraction  
3. Packet  
4. Copy Fields  
5. VIN Validation  
6. Source Attribution  

Nothing else until V0 acceptance criteria pass.

---

## Acceptance Criteria (V0)

- [ ] Upload works  
- [ ] Extraction works  
- [ ] Packet generated  
- [ ] Copy Fields works  
- [ ] Source file shown  
- [ ] VIN warning shown  

---

## Revenue Milestone

```
Chen Kui Pilot → 10 Real Cases → Average ≥4 min saved → First $49 payment
```

---

## Documents Created

| File | Purpose |
|------|---------|
| `docs/p16/P16_DECISION_FREEZE_V1.md` | SSOT for P16 scope + architecture |
| `docs/p16/P16_REPO_CLEANUP_RECOMMENDATIONS.md` | KEEP / ARCHIVE / REVIEW audit |
| `P16_FREEZE_COMMIT_SUMMARY.md` | This commit summary |

---

## Prerequisite Reviews (Complete)

1. Architecture Bakeoff  
2. Customer Input Reality Review  
3. Workflow Failure Review  
4. Commercial Validation Review  
5. Zip2 Simplicity Review  

---

## Next Sprint

**Trust Layer Sprint** — implement the six frozen capabilities only.

**Do not start:** CRM, confirmation UI, WeChat, PDF, Document AI, trade-in automation.

---

## Push Command (manual)

```bash
git push -u origin sprint/p16-trust-layer
```

---

*End of P16 Freeze Commit Summary*
