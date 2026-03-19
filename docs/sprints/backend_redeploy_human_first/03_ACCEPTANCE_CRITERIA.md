# Backend Redeploy for Human-First Entry Flow — Acceptance / Operational Criteria

**Sprint:** Backend Redeploy for Human-First Entry Flow

---

## 1. Successful Redeploy

- `bash scripts/deploy_rag_demo.sh` exits 0
- Script outputs Service URL
- No fatal errors in deploy output

---

## 2. Successful Production Verification

| Criterion | Pass |
|-----------|------|
| `/healthz` returns 200 | ✓ |
| `/readyz` returns 200 or JSON with `ok` | ✓ |
| Triage API responds (no 500) | ✓ |
| Payment case ("付款有问题") returns payment-specific reply | ✓ |
| Quote case returns quote intent + next missing info | ✓ |
| Missing-doc / already-sent case acknowledges first | ✓ |

---

## 3. Acceptable Risk

- `/readyz` may be `false` if Qdrant not ready; triage path works without Qdrant.
- One-off transient 503 during cold start is acceptable.
- Minor wording differences between local and production are acceptable if intent is correct.

---

## 4. What Would Block Founder Inspection

- Backend deploy fails
- `/healthz` fails after deploy
- Triage API returns 500 for standard cases
- Payment case still returns generic "内容不够完整" in production

---

## 5. Non-Negotiable Rule

Do NOT stop at "deploy succeeded". Verify production truth by checking triage behavior for key human-first cases.
