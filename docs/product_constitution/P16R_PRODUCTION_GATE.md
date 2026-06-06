# P16-R Phase 6 — Production Readiness Gate

**Date:** 2026-06-01  
**Rule:** **DO NOT DEPLOY TO PRODUCTION YET** (mission constraint)  
**Question:** If promoted today, what breaks?

---

## If `vercel deploy --prod` ran today (hypothetical)

| Area | What happens | Severity |
|------|--------------|----------|
| **Build** | Would use new dashboard `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` + existing `VITE_API_BASE_URL` | ✅ Likely builds |
| **UI surface** | Broker product_only; customer tab hidden on workbench URL | ⚠️ Chen Kui can't use customer P16-O on `/workbench` without separate customer route |
| **Customer P16-O** | In bundle but **not default tab** on product_only | ⚠️ Trial needs customer URL strategy |
| **Alias cutover** | `ui-smoky-beta` moves to new bundle | 🔶 Irreversible perception shift |
| **Rollback** | Old prod `ui-cupempwva` exists but alias swap is ops-sensitive | Med |
| **CORS** | smoky-beta already allowlisted | ✅ |
| **Backend** | No code deploy in P16-R | ✅ |
| **Commercial** | Invoice IDs still empty | ❌ payment blocked |
| **Andy proof** | No Preview E2E log yet | ❌ process gate |

---

## What is missing before Production promote

| # | Missing item | Blocks |
|---|--------------|--------|
| 1 | Preview cold URL works (SSO off) | Broker trial link |
| 2 | Andy 15-min Preview E2E log | Founder sign-off |
| 3 | Preview = Local sign-off | Parity proof |
| 4 | Customer-only URL decision (or full dev customer tab policy) | Role C / end customer |
| 5 | Persisted Preview env (no `-b` drift) | Redeploy safety |
| 6 | `.env.cloudrun` ALLOWED_ORIGINS includes all aliases | Backend redeploy safety |
| 7 | Supervised Chen Kui Day 0 | Payment narrative |
| 8 | Fill payment IDs in commercial pack | $49 ask |

---

## What must be true first

```
Preview cold 200
    → Andy E2E log (paste → queue → draft → copy → follow-up)
        → Preview bundle = Local bundle (grep + screenshot)
            → Customer URL strategy documented
                → vercel deploy --prod
                    → Production smoke (same grep + Role C browser)
                        → Chen Kui supervised Day 0
```

---

## Production-specific break scenarios

| Scenario | Break |
|----------|-------|
| Promote without product_only flag | Full dev UI on public URL — **worse than today for brokers** |
| Promote without P16-O | Customer still sees 加车 grid — **fails P16-O parity** |
| Promote while Preview SSO on | Andy tests wrong environment — false confidence |
| Share `ui-smoky-beta` before promote | Users stay on 41d-old UI — **current reality** |

---

## Gate verdict

| Promote today? | **NO** |
|----------------|--------|
| Ready for promote after Preview gates? | **Conditional** — 1–2 days ops if SSO + E2E complete |
| Production safer than Preview for brokers today? | **Yes** (200, no SSO) — but **wrong UI** |

---

*End of P16-R Phase 6 — Production Gate*
