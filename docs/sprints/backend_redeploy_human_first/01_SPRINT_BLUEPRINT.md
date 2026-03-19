# Backend Redeploy for Human-First Entry Flow — Sprint Blueprint

**Sprint:** Backend Redeploy for Human-First Entry Flow  
**Date:** 2025-03-15  
**Budget:** 15–30 minutes

---

## 1. Why This Redeploy Is Needed Now

- **Production frontend** is already deployed to Vercel with the latest Human-First Entry Flow UI.
- **Production backend** (Cloud Run) has not been redeployed since the Human-First logic changes.
- Without redeploy: payment markers, soft_route fallback, and answer-first behavior may not be live in production.
- **Goal:** Make production backend match the latest intended behavior so the founder can test the full flow on Vercel.

---

## 2. What Must Be Live

| Item | Location | Purpose |
|------|----------|---------|
| **Payment markers** | `configs/industries/insurance/markers.json` | 付款, 付款问题, 付款失败 → payment_lapse_expiration |
| **Soft_route fallback** | `services/fiqa_api/routes/inbox_triage.py` | When triage returns unclear + soft_route set → intent-specific first reply |
| **Human-first reply logic** | `services/fiqa_api/inbox_triage/triage.py` | Answer-first, reassure-first, already_sent lead, clarification_question |
| **SOFT_ROUTE_STARTER_REPLIES** | `routes/inbox_triage.py` | add_car, remove_car, claim_intake, cancellation_warning, missing_document |

---

## 3. What Counts as Success

- Backend deploy completes (exit 0).
- Production `/healthz` and `/readyz` return 200.
- Production triage API returns intent-specific replies for:
  - Payment: "付款有问题" → payment-specific, not generic "内容不够完整"
  - Quote: "我才买了一个2026年的丰田花冠，大约半年的保费是多少？" → quote intent, next missing info
  - Missing-doc / already-sent: "我上周已经发过了，怎么还在追材料？" → acknowledge first, not dismissive

---

## 4. Out of Scope

- No new features.
- No unrelated cleanup.
- This sprint is about safely shipping backend logic already implemented.

---

## 5. Sprint Report (2025-03-15)

**Deploy:** SUCCESS. URL: https://fiqa-api-g7zatxrycq-uw.a.run.app  
**Latest logic live:** Yes (payment markers, soft_route fallback, human-first reply).  
**Founder can test on Vercel:** Yes. Ensure API base URL points to Cloud Run.  
**Biggest risk:** CORS, cold start.  
**Next tests:** Payment, quote, missing-doc cases; run test_inbox_triage_api.py --url https://fiqa-api-g7zatxrycq-uw.a.run.app
