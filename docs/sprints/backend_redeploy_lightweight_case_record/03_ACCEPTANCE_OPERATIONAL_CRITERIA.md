# Backend Redeploy for Lightweight Case Record — Acceptance / Operational Criteria

**Sprint**: Backend Redeploy for Lightweight Case Record  
**Created**: 2026-03-15

---

## 1. Successful Redeploy

| Criterion | Pass |
|-----------|------|
| deploy_rag_demo.sh exits 0 | Yes |
| Service URL printed | Yes |
| /healthz returns 200 | Yes |
| /readyz returns (ok:true or ok:false) | Yes |

---

## 2. Successful Production Verification

| Criterion | Pass |
|-----------|------|
| Case creation returns case_messages | Yes |
| Append adds messages to case_messages | Yes |
| Customer PATCH stores fields | Yes |
| Workflow state present in case | Yes |
| Lifecycle values accepted | Yes |

---

## 3. Acceptable Risk

| Item | Acceptable |
|------|------------|
| /readyz ok:false when Qdrant cold | Yes (triage path works without Qdrant) |
| Case storage ephemeral (Cloud Run) | Yes (demo design) |
| One pre-existing audit failure (M1) | Yes |

---

## 4. Would Block Founder Inspection

| Blocker | Action |
|---------|--------|
| /healthz fails | Do not claim success; fix and redeploy |
| CORS errors from Vercel | Check ALLOWED_ORIGINS |
| Case creation 500 | Check logs; configs; OpenAI key |
| case_messages missing in response | Backend not reflecting new code; redeploy |
