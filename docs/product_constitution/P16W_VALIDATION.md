# P16-W Phase 7 — Validation

**Date:** 2026-06-01  
**Fix commit:** `b0d6073`  
**Preview bundle:** `index-OFXnRnil.js`

---

## guardrail_inbox_triage.sh

```
Guardrail: PASS
```

All inbox triage scenarios, client A/B batteries, and append boundary checks passed (2026-06-01 run).

---

## npm build

| Environment | Result |
|-------------|--------|
| Local (`ui/`, Node 22.22.0) | ✅ PASS — `vite build` in 22s |
| Vercel Preview deploy | ✅ PASS — built in 46s |

Note: Default shell Node 20.18.2 fails Vite 7 engine check; use `ui/.nvmrc` (22.22.0).

---

## Preview deploy verification

| Check | Pre-fix (`CKPYkrkL`) | Post-fix (`OFXnRnil`) |
|-------|----------------------|------------------------|
| Cold HTTP | 200 | 200 |
| 加载演示队列 | ReferenceError | ✅ 12/12 loaded |
| Runtime error boundary | Yes | No |
| Bundle in HTML | `index-CKPYkrkL.js` | `index-OFXnRnil.js` |

---

## post_sprint_check.sh (after deploy)

```
Checks passed: 10 / 10 (100%)
OVERALL ...................... PASS
```

Includes: preview reachable, protection absent, product_only markers, CORS, Cloud Run health.

---

## Runtime error check

| Test | Result |
|------|--------|
| Open Preview | ✅ No crash |
| Demo queue | ✅ No ReferenceError |
| Paste → triage | ✅ Draft panel renders |

---

*End of P16-W Phase 7*
