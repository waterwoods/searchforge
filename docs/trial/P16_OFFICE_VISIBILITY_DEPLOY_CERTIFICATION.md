# P16 Office Visibility Deploy Certification

**Sprint:** P16-VERIFY-AND-DEPLOY-OFFICE-VISIBILITY-SPRINT  
**Date:** 2026-06-06  
**Phase:** 4 — Browser Certification  
**URL tested:** `https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake`  
**Deployment:** `dpl_2S7zGtHDyHX2WW4fZdKtuQ9CwJHL` · `index-DMOKMAa_.js`

---

## Method

Automated browser verification (Cursor IDE browser) after hard navigation + **刷新列表** with intake-key-enabled bundle.

---

## Office queue card checklist — `case_ea74d66fa3ba`

| Requirement | Observed | Pass? |
|-------------|----------|-------|
| **Vehicle summary** | `2024 Tesla Model Y` | ✅ |
| **Case ID** | `服务记录编号：case_ea7…` (short + copyable) | ✅ |
| **Submitted indicator** | `已正式送达办公室` · `已送达·待补缺口` | ✅ |
| **Missing fields** | `待补问：提车日期` | ✅ |
| **Office next step** | `办公室侧下一步：联系客户补齐提车日期，然后出报价` | ✅ |

---

## Ranking verification

| Check | Result |
|-------|--------|
| Tesla case visible in workbench | ✅ |
| Position in queue | **#1** — first case card after queue header (index 1 in flat product-only list) |
| Demo queue loaded | 11/12 seeds present (does not block Tesla visibility) |
| API error banner | ❌ None (`intake_api_unauthorized` cleared after API-key redeploy) |

---

## Card presentation vs pre-fix Preview

| Signal | Pre-fix (`index-CJ0tCunS.js`) | Post-fix (`index-DMOKMAa_.js`) |
|--------|-------------------------------|--------------------------------|
| Vehicle on card | ❌ | ✅ |
| Case ID on card | ❌ | ✅ |
| Submitted tag | ❌ | ✅ |
| Missing fields | ❌ | ✅ |
| Office next step (Chinese) | ❌ | ✅ |
| Tesla near top | ❌ (#50 UI score) | ✅ (#1 in browser) |

---

## Certification result

**PASS** — Office Visibility fix certified on Preview alias.

All success-criteria UI signals present; certified Tesla case ranks at top of visible queue.

---

## Operator note

Always open the **`ui-waterwoods` alias**, not raw hash deployment URLs. Hash URLs may fail CORS if not in Cloud Run `ALLOWED_ORIGINS`.

Hard refresh (Ctrl+Shift+R) after deploy to avoid stale bundle cache.
