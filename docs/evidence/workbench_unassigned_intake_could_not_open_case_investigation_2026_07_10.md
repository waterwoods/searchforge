# Workbench — intermittent "Could not open case" on unassigned intake drawer

**Date:** 2026-07-10  
**Branch:** `sprint/p16-trust-layer`  
**Scope:** Root-cause investigation + small frontend fix (no deploy)

---

## 1. Symptom

On the Document Intake / Workbench office queue, clicking a **待确认材料** row (`service_lane: wecom_media_intake`, formerly WeCom Photo / UNASSIGNED):

- The right-hand drawer **opens correctly** and shows customer + attachments from list data.
- A red top toast **"Could not open case"** sometimes appears at the same time.
- Reproduction is **intermittent** — same page may not show the toast on a later visit.

This hurts demo trust: the UI looks broken even though the drawer content is fine.

---

## 2. Screenshot / UX context

Observed flow (2026-07-09):

1. Queue lists `待确认材料` row with attachment count.
2. User clicks **Open** or the row action.
3. Drawer renders WeCom holding content (`Customer`, `Source: WeCom`, `CaseAttachmentsPanel`).
4. Red toast: **Could not open case** (spurious when drawer already has data).

---

## 3. Root cause

`DocumentIntakeInboxPage.openCase` used a **single path for all queue rows**:

```text
setDetail(listRowStub)          // drawer opens immediately from list payload
await getSavedCase(caseId)      // formal GET /api/inbox/cases/{id}
catch → toast("Could not open case")
```

For `wecom_media_intake` / 待确认材料:

- The drawer does **not** need the formal case detail response — `BrokerCaseDetail` renders from list stub (`case_attachments`, `customer_name`, lane tags).
- The background `getSavedCase` call can **fail intermittently** (404, PG/JSON read mismatch, stale id, office-access edge) while the stub is already on screen.
- The catch block always showed the **formal case** error string, even when the holding drawer was already usable.

**Anti-pattern confirmed:** optimistic open from list + unconditional formal detail fetch + formal-case error toast on any failure.

---

## 4. Why intermittent

Likely race / dual-read sources:

| Factor | Effect |
|--------|--------|
| List endpoint returns row from enriched workbench list | Stub present → drawer opens |
| Detail `GET /cases/{id}` hits `get_case_for_read` (PG-primary + JSON fallback) | Occasional miss or lag vs list |
| User clicks quickly after ingest | Row visible in list before detail read is stable |
| No stub path for formal lanes | Claim/Add Car correctly depend on detail hydration |

Because failure is on the **secondary** fetch and the UI already committed stub state, the bug is timing-dependent — not a stable data corruption.

---

## 5. Fix (smallest safe change — Option A)

New helper module: `ui/src/features/intake/utils/workbenchCaseOpen.ts`

| Lane | Behavior |
|------|----------|
| `wecom_media_intake` (待确认材料) | Open drawer from list stub only; **skip** `getSavedCase`; **no** "Could not open case" toast |
| Formal lanes (`claim`, `add_car`, P16 document cases) | Unchanged: fetch detail, show **Could not open case** on failure |

Copy rules:

- Formal case failure: `Could not open case`
- If a holding row ever needed an error without list fallback: `Could not open intake item` (helper ready; not shown when stub exists)

No backend or schema changes.

---

## 6. What changed

| File | Change |
|------|--------|
| `ui/src/features/intake/utils/workbenchCaseOpen.ts` | Lane-aware open-path helpers |
| `ui/src/features/intake/utils/workbenchCaseOpen.test.ts` | Unit tests for fetch/toast policy |
| `ui/src/pages/DocumentIntakeInboxPage.tsx` | `openCase` uses helpers; WeCom holding skips detail fetch |

---

## 7. Tests / build

```bash
npx tsx ui/src/features/intake/utils/workbenchCaseOpen.test.ts
npx tsx ui/src/features/intake/utils/attachmentDisplay.test.ts
npx tsx ui/src/features/intake/utils/claimWorkbenchDisplay.test.ts
cd ui && npm run build
```

Backend: **not touched** — no Python regressions required.

---

## 8. Constraints honored

| Constraint | Status |
|------------|--------|
| No schema change | ✅ |
| No deploy | ✅ |
| No claim boundary / workflow change | ✅ |
| No OCR/ASR / True End Card / highlights | ✅ |
| Small frontend fix only | ✅ |
| Do not hide real errors on formal lanes | ✅ |

---

## 9. Known limitations

- WeCom holding drawer no longer background-hydrates from `GET /cases/{id}`. List payload is the source of truth for holding rows (matches prior visible behavior when fetch failed).
- If list stub is missing and detail fetch fails for a holding row, user would see empty drawer — rare (click always from listed row).
- Root intermittent detail failures for formal Claim/Add Car lanes are unchanged; those still toast correctly.

---

## 10. Next recommended step

- Optional: add lightweight `GET /cases/{id}` parity test for `wecom_media_intake` in backend smoke if detail hydration is desired later.
- Monitor demo queue for any holding row missing attachments in list payload (would be a list-enrichment issue, not this toast fix).

---

**GO** — safe for demo; removes false-negative trust signal on 待确认材料 opens.
