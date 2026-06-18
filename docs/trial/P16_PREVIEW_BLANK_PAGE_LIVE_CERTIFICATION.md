# P16 Preview Blank Page — Live Certification

**Sprint:** P16-PREVIEW-BLANK-PAGE-RECOVERY  
**Date:** 2026-06-07  
**Certified URL:** https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer  
**Deployment:** `dpl_7LuRLamWCHoEo5xVNie1TvFmtk7Q` · Bundle `index-Bs99AAgT.js`

**Note:** Use the **`ui-waterwoods` alias** for QA. Per-deployment URLs (e.g. `ui-r4si9tqyh-…`) are not on Cloud Run CORS whitelist and will fail phone lookup with `无法验证手机号`.

---

## Certification matrix

| # | Check | Result |
|---|-------|--------|
| 1 | Page not blank | **PASS** — header, tabs, Customer First card render |
| 2 | Header renders | **PASS** — 金盾·陈魁团队 · 客户统一受理 |
| 3 | Customer tab renders | **PASS** |
| 4 | Phone entry renders | **PASS** — phone + name inputs, Continue button |
| 5 | Office tab renders | **PASS** — queue, filters, paste area |
| 6 | Simulation tab renders | **PASS** — scenario controls, combobox |
| 7 | Phone lookup `6265559101` | **PASS** — HTTP 200 → **Start New Add-Car Request** (no active case) |
| 8 | BMW X5 no false green submit | **PASS** — simulation battery `D — BMW X5 full lifecycle` 7/7 sub-checks against Cloud Run API |
| 9 | Return by phone | **PASS** — `2039935973` → Active Add-Car Request, conversation restorable via Continue |
| 10 | Simplified status states | **PASS** — return phone shows **等客户补资料** (one of four states) |

---

## Scenario details

### Fresh phone — 6265559101

- Continue → spinner → **Start New Add-Car Request**
- No auth error on `ui-waterwoods` origin

### Return phone — 2039935973

- Active case card with vehicle hint
- Status: **等客户补资料** / Awaiting Your Information
- Still Needed: Year, Make & Model, ZIP, Effective Date, Driver License, VIN
- Continue Request / Contact Broker buttons present

### BMW X5 lifecycle (API simulation)

Script: `scripts/run_p16_customer_status_simplification_simulations.py`  
BASE=`https://fiqa-api-g7zatxrycq-uw.a.run.app`

- 宝马X5 → `awaiting_customer` (等客户补资料), no false submitted card
- Full lifecycle through formal submit → office processing → closed: **PASS**

---

## Broken URL confirmation

https://ui-6hc7cfoxk-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer  
Still **blank** (old bundle `index-BxgUOLwB.js`) — expected; do not use.

---

## Verdict

**PASS** — Preview page load restored. Customer First + phone lookup + status truth certified on `ui-waterwoods` alias.

---

*End of P16 Preview Blank Page Live Certification*
