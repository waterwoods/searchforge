# Handoff Timing Regression Blueprint

**Sprint:** Handoff Timing Regression + Redeploy Sprint  
**Created:** 2026-03-19  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Why This Regression Sprint Matters Now

The prior handoff-timing audit (BROKER_TRIAL_HANDOFF_TIMING_AUDIT) fixed HT8 — add-car + doc clarification in same turn. HT3, HT9, HT10 were classified acceptable-for-trial with fix-next:

- **Premium:** T2 handoff when bill_sent; T3 "其中一辆去掉会便宜吗" would append
- **Payment:** T2 handoff when paid; T3 "截图发你微信了" would append

This sprint systematically tests whether more "handoff too early / one more useful question" cases remain, applies only small high-value fixes justified by evidence, and redeploys so the founder can test on Vercel.

---

## 2. Why This Is the Right Move After the Prior Audit

- HT8 fix is deployed; handoff timing pack passes
- Premium/payment flows may still hand off slightly early when user adds another useful detail one turn later
- Real trial risk: user feels cut off; broker gets under-filled case; append does too much recovery
- Next highest-value move: test this class more systematically, fix 1–2 clear high-value cases if justified, redeploy

---

## 3. What This Sprint Will Strengthen

- Regression pack for handoff-too-early problems
- Clear evaluation of whether more such cases remain
- 0–2 small, justified fixes (only if evidence supports)
- Backend redeployed if code changed
- Clean founder test checklist for Vercel

---

## 4. What This Sprint Intentionally Will NOT Do

- Redesign the workflow engine
- Fix everything
- Make handoff perfect
- Expand into broad new platform work
- Overcorrect (make handoff too slow everywhere)

---

## 5. Core Principle

**Not too early. Not too late. Enough information. Still natural.**

---

*End of Blueprint*
