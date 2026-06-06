# Sprint Blueprint: Frontend + Backend Deploy for Client Identity Persistence

**Sprint name:** Client Identity Persistence Deploy  
**Target budget:** 15–35 minutes  
**Mode:** Focused deployment + production verification

## What We're Deploying

- **Backend:** Client identity persistence in case lifecycle
  - `client_id` stored on cases (case_store)
  - Append/follow-up uses `case.client_id` for handoff phrases
  - Reopened/reviewed workbench cases remain client-aware
- **Frontend:** Append flow passes `currentCase.client_id ?? clientId` to API

## Scope Guardrail

- **In scope:** Deploy existing changes, verify production
- **Out of scope:** New features, unrelated product changes

## Success Criteria

1. Backend deployed to Cloud Run
2. Frontend deployed to Vercel
3. Scenario A: Client-aware entry copy (default vs demo_broker)
4. Scenario B: Client-aware handoff wording (我想联系客服)
5. Scenario C: Lifecycle persistence across append (chen_kui case + demo_broker URL → append uses chen_kui)

---

## Sprint Report Summary (completed)

- **Backend:** Deployed fiqa-api-00031-vzr to https://fiqa-api-1013093472160.us-west1.run.app
- **Frontend:** Deployed to https://ui-smoky-beta.vercel.app
- **Pre-deploy:** Guardrail PASS, npm build PASS (fixed BrokerWorkbenchTab clientId shadow)
- **Verification:** Scenarios A/B/C inferred from code; manual Founder Verification Checklist recommended
- **Andy:** Can test on Vercel now — run 4 checks in CLIENT_IDENTITY_PERSISTENCE_FOUNDER_VERIFICATION_CHECKLIST.md first
