# P16 Remote Preservation — Final Audit

**Date:** 2026-06-06  
**Mission:** P16-PUSH-AND-GOVERNANCE-CLOSEOUT — Phase 3  
**Remote:** `origin` → `git@github.com:waterwoods/searchforge.git`  
**Mode:** Read-only verification via `git ls-remote`

---

## Verification Results

| Ref | Exists on origin? | SHA | Purpose |
|-----|:-----------------:|-----|---------|
| `refs/heads/sprint-a/broker-front-door` | ✅ | `b3c8ec369fa9f9232e3f663be23cd4f093c985d3` | Active P16 line + runtime resolution |
| `refs/heads/release/p16-demo-ready-v1` | ✅ | `517f7281ebdf136fda8e2d6ab884b26ce0e5cf37` | Frozen demo-ready baseline |
| `refs/tags/p16-demo-ready-v1` | ✅ | `5a2ab39df4d0d01256e4a1f8070be4b47f8c0501` | Annotated release tag (points to `517f728`) |
| `refs/heads/archive/production-pre-p16-demo` | ✅ | `85bacc639f174e0680d11d8486aa86b53ffa6986` | Pre-P16 production rollback |

Verification command:

```bash
git ls-remote origin \
  refs/heads/sprint-a/broker-front-door \
  refs/heads/release/p16-demo-ready-v1 \
  refs/tags/p16-demo-ready-v1 \
  refs/heads/archive/production-pre-p16-demo
```

All four refs returned valid SHAs. **No missing refs.**

---

## Recovery Paths

| Scenario | Recovery command |
|----------|------------------|
| Restore demo-ready code | `git checkout release/p16-demo-ready-v1` or `git checkout p16-demo-ready-v1` |
| Restore active sprint line | `git checkout sprint-a/broker-front-door` |
| Roll back to pre-P16 production | `git checkout archive/production-pre-p16-demo` |
| Run local demo from frozen pin | `git checkout p16-demo-ready-v1 && bash scripts/run_demo_local.sh` |

Supporting docs on origin (in sprint history): `P16_RELEASE_BASELINE_REPORT.md`, `P16_ENVIRONMENT_PRESERVATION_REPORT.md`, `docs/ANDY_QUICK_START.md`, operator runbooks.

---

## If Andy's laptop dies tomorrow: Can the demo-ready state be recovered?

### **YES**

**Why:**

1. **Demo pin is on origin.** `release/p16-demo-ready-v1` @ `517f728` and tag `p16-demo-ready-v1` are remotely accessible. Any machine can clone and checkout the frozen baseline.

2. **Rollback exists.** `archive/production-pre-p16-demo` @ `85bacc6` preserves pre-P16 production state for emergency revert.

3. **Active line is preserved.** `sprint-a/broker-front-door` @ `b3c8ec3` includes all hygiene commits, audit reports, and the runtime resolution commit — not just local work.

4. **Preview deploy aligns to demo pin.** Vercel Preview was built from `517f728` (documented in `P16_DEPLOYMENT_PARITY_REPORT.md`). Frontend demo URL remains viable independent of laptop.

5. **What would be lost:** Only uncommitted working-tree diffs (17 UNSURE runtime paths + 15 untracked governance docs from this session). Committed governance and product state are fully recoverable from origin.

---

*Phase 3 complete. Demo-ready state is remotely preserved.*
