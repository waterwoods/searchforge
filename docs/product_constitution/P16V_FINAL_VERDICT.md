# P16-V Phase 10 — Final Verdict

**Date:** 2026-06-01  
**Sprint:** P16-V Reality Closure  
**Mission:** Move `post_sprint_check.sh` from 8/10 FAIL → 10/10 PASS

---

## Sprint outcome

**NOT SUCCESSFUL** — Preview URL does not open normally; runner unchanged at 8/10.

P16-V correctly identified the blocker, confirmed the fix is safe, and documented why it could not be applied autonomously. **No false success claimed.**

---

## 1. Initial score

**8 / 10 (80%) — FAIL**

Blockers: HTTP 401, SSO/401 (FP-004)

---

## 2. Final score

**8 / 10 (80%) — FAIL**

No change. Phase 4 fix not applied.

---

## 3. Which failures closed

| Failure | Closed? |
|---------|---------|
| `preview_url_reachable` (401) | ❌ |
| `preview_protection_absent` (FP-004) | ❌ |
| FP-001 parity note | ❌ (informational; not runner FAIL) |
| pilot_env_posture WARN | ❌ (local only) |

**Failures closed: 0**

---

## 4. Which failures remain

| # | Failure | Pattern | Owner |
|---|---------|---------|-------|
| 1 | Preview cold 401 | FP-004 | Andy — Vercel dashboard |
| 2 | Preview SSO wall | FP-004 | Andy — Vercel dashboard |
| 3 | Preview ≠ Production bundle | FP-001 / FP-013 | Andy — post Preview gate |
| 4 | Production stale UI | FP-013 / FP-016 | Andy — prod promote |
| 5 | No Andy E2E log | FP-010 / FP-015 | Andy — post SSO |

**Runner-native blockers: 2 (both FP-004)**

---

## 5. Runner result

```
Before P16-V:  8/10 FAIL
After P16-V:   8/10 FAIL
Target:       10/10 PASS (requires SSO toggle only)
```

Command: `bash scripts/post_sprint_check.sh`

---

## 6. Preview status

| Dimension | Status |
|-----------|--------|
| Deploy exists | ✅ `ui-iwnyo9ufa` @ Ready |
| Alias | ✅ `ui-waterwoods` |
| Bundle content | ✅ P16-O + product_only (`index-CKPYkrkL.js`) |
| Cold access | ❌ **401 SSO** |
| Shareable for trial | ❌ |

**Preview has the right build; wrong access model.**

---

## 7. Production status

| Dimension | Status |
|-----------|--------|
| Cold access | ✅ HTTP 200 |
| Bundle | ❌ Stale (`index-ctrXdUgj.js`, ~41 days) |
| P16-O markers | ❌ absent |
| product_only | ❌ not deployed |
| Default UX | Customer portal (wrong for broker trial) |

**Production is publicly reachable but serves outdated UI.**

---

## 8. Trial readiness

**NOT READY**

| Requirement | Met? |
|-------------|------|
| Shareable broker URL | ❌ |
| Cold 200 Preview | ❌ |
| Deployed E2E proof | ❌ |
| API engine | ✅ |
| CORS | ✅ |

---

## 9. Commercial readiness

**NOT READY** (unchanged from P16-K/Q/U)

Invoice, pricing confirmation, observation log — out of P16-V scope but still open for Day 7.

---

## 10. Exact next action for Andy

**One action unlocks 10/10 runner and unblocks trial distribution:**

### Disable Preview Deployment Protection (~5 min)

1. Open: https://vercel.com/andys-projects-1f411b73/ui/settings/deployment-protection
2. Turn **OFF** Deployment Protection for **Preview** only
3. Leave Production protection **unchanged**
4. Verify:

```bash
curl -sI https://ui-waterwoods-andys-projects-1f411b73.vercel.app | head -1
# Expected: HTTP/2 200

bash scripts/post_sprint_check.sh
# Expected: 10/10 PASS
```

5. Open Preview in incognito → confirm broker paste UI (not Vercel login)
6. Run 15-min paste E2E → publish log
7. Then consider `vercel deploy --prod` with product_only flags (separate gate)

---

## P16-V artifact index

| Phase | Document |
|-------|----------|
| 1 | `P16V_BASELINE.md` |
| 2 | `P16V_PREVIEW_PROTECTION_AUDIT.md` |
| 3 | `P16V_PREVIEW_PROTECTION_PLAN.md` |
| 4 | `P16V_PREVIEW_PROTECTION_CHANGE.md` (NOT APPLIED) |
| 5 | `P16V_PREVIEW_REVALIDATION.md` |
| 6 | `P16V_PARITY_REPORT.md` |
| 7 | `P16V_PRODUCTION_READINESS.md` |
| 8 | `P16V_RUNNER_DELTA.md` |
| 9 | `P16V_REALITY_GATE.md` |
| 10 | `P16V_FINAL_VERDICT.md` |

---

## Success criteria check

| Criterion | Met? |
|-----------|------|
| Preview URL opens normally | ❌ |
| Runner improves | ❌ |
| Reality Gate improves | ❌ |
| Blocker documented if not fixable | ✅ |
| No false success | ✅ |

**P16-V closes with honest FAIL and a 5-minute founder path to PASS.**

---

*End of P16-V Phase 10 — Final Verdict*
