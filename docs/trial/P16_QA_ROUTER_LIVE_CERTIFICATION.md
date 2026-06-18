# P16 QA Router Live Certification

**Sprint:** P16-QA-PREVIEW-ROUTER-RUNTIME-RECOVERY  
**Date:** 2026-06-07  
**Preview URL:** https://ui-rj27hhjeh-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer  
**Alias:** https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

---

## Live checks

| # | Check | Result |
|---|-------|--------|
| 1 | Customer tab loads | ✅ PASS |
| 2 | Customer First entry screen | ✅ PASS — Add-Car Request |
| 3 | Phone field | ✅ PASS |
| 4 | Name optional field | ✅ PASS |
| 5 | Continue button | ✅ PASS |
| 6 | No red runtime error | ✅ PASS — router crash gone |
| 7 | No blank page | ✅ PASS |
| 8 | Office tab loads | ✅ PASS — 办公室工作台 |
| 9 | Simulation tab loads | ✅ PASS — 场景仿真 |
| 10 | Phone lookup vs Cloud Run | ⚠️ CONDITIONAL — API returns `401 intake_api_unauthorized` without `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` on Preview build; UI shows validation error, page does not crash |

---

## Phone tests

| Phone | Expected | Observed |
|-------|----------|----------|
| 6265551001 | No active / start new | API 401 from browser → error state on Continue (no crash) |
| 6265551002 | Active case if seeded | Not verified live (same API key gap) |

**Note:** Router recovery is verified. Phone lookup requires Vercel Preview env `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` matching Cloud Run — separate from router fix.

---

## Verdict

**CONDITIONAL GO** — Preview loads all tabs without runtime error. Phone lookup E2E pending intake API key on Vercel Preview env.

---

*End of P16 QA Router Live Certification*
