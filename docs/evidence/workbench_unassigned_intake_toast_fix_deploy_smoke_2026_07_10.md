# Workbench — unassigned intake toast fix deploy + smoke

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Fix commit:** `2377fbc`  
**Verdict:** **GO**

---

## 1. Goal

Deploy frontend fix for intermittent **"Could not open case"** toast when opening **待确认材料** (`wecom_media_intake`) rows, and verify formal Claim / Add Car behavior is unchanged.

---

## 2. Deployed frontend URL / alias

| Field | Value |
|-------|-------|
| Command | `cd ui && npm run build && vercel --prod --yes` |
| Deployment URL | `https://ui-45rurpt7n-andys-projects-1f411b73.vercel.app` |
| **Stable alias** | **`https://ui-smoky-beta.vercel.app`** |
| Bundle | `assets/index-Do42hJJS.js` |
| Bundle markers | `Could not open intake item`, `wecom_media_intake`, `待确认材料` present |

### Route checks

| Route | HTTP |
|-------|------|
| `/workbench/document-intake` | **200** |
| `/workbench/unified-intake` | **200** |
| `/add-car` | **200** |

---

## 3. Backend deploy

| Field | Value |
|-------|-------|
| Backend redeployed? | **No** (frontend-only change) |
| Cloud Run URL | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| `GET /version` GIT_SHA | **`62c4b35d8`** (unchanged) |

---

## 4. Root cause recap

`DocumentIntakeInboxPage.openCase` used one path for all rows: open drawer from list stub, then unconditionally `getSavedCase` (`GET /api/inbox/cases/{id}`). For `wecom_media_intake`, the drawer already renders from list data; when detail fetch failed intermittently, catch still showed **"Could not open case"**.

---

## 5. Fix recap

| Lane | Open behavior |
|------|----------------|
| `wecom_media_intake` / 待确认材料 | Drawer from list stub only; **skip** formal detail fetch; **no** false case toast |
| Formal lanes (`claim`, `add_car`, P16) | Unchanged: detail fetch + real error toast on failure |

Helper: `ui/src/features/intake/utils/workbenchCaseOpen.ts`

---

## 6. Smoke A — unassigned intake / 待确认材料

**URL:** https://ui-smoky-beta.vercel.app/workbench/document-intake

| Check | Result |
|-------|--------|
| Click 待确认材料 row (top of queue) | **PASS** |
| Drawer opens | **PASS** — title `企业微信客户 · 待确认材料` |
| Customer section | **PASS** — Name + Source: WeCom |
| Attachment panel | **PASS** — Unknown document card visible |
| Next Step banner | **PASS** — WeCom media received guidance |
| Red toast "Could not open case" | **PASS (absent)** |
| Treated as Claim | **PASS (no)** — lane tags 待确认材料 only |
| Close + reopen same row | **PASS** — no toast |
| Rapid switch while drawer open | **PASS** — no false toast observed |

---

## 7. Smoke B — formal Claim row

**Row:** UI index 6 (first Claim after 5 WeCom holding rows)

| Check | Result |
|-------|--------|
| Drawer opens | **PASS** |
| Lane label | **PASS** — `Claim · 记录中` |
| Claim Case Brief / 事故摘要 | **PASS** |
| Highlights / 重点速览 | **PASS** — injury + photo highlights visible |
| Accident basics + evidence checklist | **PASS** |
| Detail hydration | **PASS** — formal detail path still active |
| Error toast | **PASS (none)** — detail fetch succeeded |

---

## 8. Smoke C — Add Car row

**Row:** UI index 5 (first Add Car after WeCom block)

| Check | Result |
|-------|--------|
| Drawer opens | **PASS** |
| Lane label | **PASS** — `Add Car` |
| Next Step | **PASS** — quote |
| Attachments panel | **PASS** |
| Error toast | **PASS (none)** |
| Regression vs prior deploy | **PASS** |

---

## 9. Smoke D — product boundary

| Item | Observed |
|------|----------|
| 待确认材料 | Holding lane; not formal case; WeCom source only |
| Claim row | `Claim · 记录中`; brief + highlights; no Start Card confusion in drawer |
| Add Car row | `Add Car`; broker review flow |
| Unassigned media | No Claim Case Brief / Start Card ceremony language |

---

## 10. Tests / build

```bash
npx tsx ui/src/features/intake/utils/workbenchCaseOpen.test.ts      # PASS
npx tsx ui/src/features/intake/utils/attachmentDisplay.test.ts      # PASS
npx tsx ui/src/features/intake/utils/claimWorkbenchDisplay.test.ts  # PASS (after label fix)
cd ui && npm run build                                              # PASS
```

---

## 11. Test cleanup performed

**Yes** — `claimWorkbenchDisplay.test.ts` expectation updated:

- Old: `claimLaneLabel()` → `'Claim'`
- New: `claimLaneLabel()` → `'Claim · 记录中'` (matches production since P19H-3f)

Production label behavior unchanged.

---

## 12. Constraints

| Constraint | Status |
|------------|--------|
| No schema change | ✅ |
| No workflow change | ✅ |
| No case boundary change | ✅ |
| No hiding formal case errors | ✅ |
| Frontend-only deploy | ✅ |

---

## 13. Known limitations

- WeCom holding drawer no longer background-hydrates from `GET /cases/{id}`; list payload is source of truth (same visible content as before when fetch failed).
- Attachment preview may still show "预览加载失败" for some WeCom objects — separate from toast fix.
- Backend remains at `62c4b35d8`; no API changes required.

---

## 14. GO / HOLD

**GO** — fix deployed to `ui-smoky-beta`; unassigned intake opens without false case toast; Claim and Add Car formal paths verified on QA.
