# P16-U Phase 4 — Safe Fix Execution

**Date:** 2026-06-01  
**Scope:** Safe Auto Fixes only — no SSO toggle, no Production promote, no new capabilities

---

## Execution log

| # | Fix | FP | File(s) | Result |
|---|-----|-----|---------|--------|
| 1 | Pilot posture sync to `.env.cloudrun` | FP-011 | `.env.cloudrun` | ✅ Applied |
| 2 | Bundle verification (Preview) | FP-005 guard | evidence only | ✅ Confirmed |
| 3 | P16-U documentation artifact set | FP-015 | `docs/product_constitution/P16U_*.md` | ✅ Created |
| 4 | CORS / Preview deploy | FP-002 | — | ⏭ Skipped (already PASS) |
| 5 | Preview SSO disable | FP-004 | — | ❌ Not safe — founder only |
| 6 | Production promote | FP-013 | — | ❌ Not safe — gated on FP-004 |

---

## Fix 1 — `.env.cloudrun` pilot posture sync

**Problem:** Local env file had `UNIFIED_INTAKE_PG_DUAL_WRITE=1` and missing product-only / DB-primary flags → 8 validate errors → runner WARN.

**Change applied:**

```diff
- UNIFIED_INTAKE_PG_DUAL_WRITE=1
+ ENV=prod
+ UNIFIED_INTAKE_PRODUCT_ONLY=1
+ UNIFIED_INTAKE_DB_PRIMARY_READS=1
+ UNIFIED_INTAKE_DB_PRIMARY_WRITES=1
+ UNIFIED_INTAKE_JSON_CASE_WRITES=0
+ UNIFIED_INTAKE_JSON_READ_FALLBACK=0
+ UNIFIED_INTAKE_PG_DUAL_WRITE=0
+ UNIFIED_INTAKE_INTAKE_CORE_READINESS=1
```

**Validation after fix:**
```
FAIL pilot deploy env (.env.cloudrun):
  - UNIFIED_INTAKE_INTAKE_API_KEY must be set (24+ char random)
  - UNIFIED_INTAKE_SUPPORT_API_KEY must be set (24+ char random)
```

Errors reduced **8 → 2**. Remaining gap is Secret Manager keys — not auto-fixable without infra access.

**Deployed impact:** None (local file only; Cloud Run already healthy). **Prevents** accidental wrong posture on next backend deploy.

---

## Fix 2 — Bundle verification

**Command:** `vercel curl` against deployment `ui-iwnyo9ufa`

| Marker | Preview bundle |
|--------|----------------|
| `请把您的需求发给我们` | ✅ |
| `原样粘贴微信/通知文字，不用整理` | ✅ |
| `快速体验（可选）` | ✅ |
| Bundle hash | `index-CKPYkrkL.js` |

**Production (`index-ctrXdUgj.js`):** P16-O markers **absent** — documented, not auto-fixed.

---

## Fix 3 — Documentation sync

Created P16-U phases 1–10 artifacts (this file set). No Constitution rewrite.

---

## Skipped fixes (with reason)

| Fix | Why skipped |
|-----|-------------|
| Disable Vercel Deployment Protection | Founder Approval — Vercel dashboard |
| `vercel deploy --prod` | Founder Approval — P16-R production gate |
| Add API keys to `.env.cloudrun` | Infrastructure — keys in Secret Manager |
| Andy 15-min E2E log | Human Judgment — blocked by SSO |
| Health-check script changes | Out of scope — no new capabilities |

---

## Git state after fixes

| Item | State |
|------|-------|
| Code changes | `.env.cloudrun` only (gitignored) |
| Committable docs | `docs/product_constitution/P16U_*.md` (10 files) |
| Branch | `sprint-a/broker-front-door` @ `d05e94d` |

---

## Phase 4 verdict

**1 safe env fix applied.** **0 runner FAILs cleared** — FP-004 remains the sole automated blocker. System correctly identified that the high-leverage fixes require founder action, not agent deploy.

---

*End of P16-U Phase 4 — Safe Fix Execution*
