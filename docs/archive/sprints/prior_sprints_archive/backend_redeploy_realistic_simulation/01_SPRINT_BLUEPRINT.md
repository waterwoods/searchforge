# Backend Redeploy for Realistic Simulation Fixes — Sprint Blueprint

**Sprint:** Backend Redeploy for Realistic Simulation Fixes  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry  
**Mode:** Focused deployment + production verification  
**Budget:** 15–35 minutes

---

## 1. Mission

Deploy the latest backend fixes from the Realistic Conversation Simulation + Fix-Now Sprint to production, then verify that the key newly-fixed scenarios are truly live.

## 2. What Was Fixed (Pre-Sprint)

| Fix | Before | After |
|-----|--------|-------|
| "找陈奎" | unclear, generic fallback | customer_requested_human, handoff-ready |
| "急死了 保单要停了" | unclear, medium | cancellation_warning, critical |

## 3. Scope Guardrail

- **In scope:** Deploy backend, verify production API behavior for fixed scenarios
- **Out of scope:** New features, unrelated product changes, frontend changes

## 4. Success Criteria

1. Backend deploys to Cloud Run successfully
2. Scenario A ("找陈奎") → customer_requested_human on production
3. Scenario B ("急死了 保单要停了") → cancellation_warning, critical on production
4. Scenario C ("联系人工") still works
5. Founder can test on live frontend with confidence

## 5. Non-Negotiable

Do NOT stop at "deploy succeeded". Must verify exact production behavior.
