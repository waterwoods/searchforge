# P16 Commit and QA Smoke Certification

**Date:** 2026-06-07  
**Sprint:** P16-FINAL-QA-CERTIFICATION  
**Audience:** Founder — Chen Kui / Wu Xiaojie internal pilot readiness

---

## 1. Was the white-screen fix committed?

**Yes.** Commit `366a7d6` — `fix(ui): restore customer first preview rendering`  
Restores missing `ADD_CAR_FIELD_LABELS` import in `customerFirstEntry.ts`.

---

## 2. Is the git tree clean or mostly clean?

**Mostly clean for pilot scope.** The fix commit is isolated (3 files). Unrelated local edits remain unstaged (backend routes, App.tsx, BrokerWorkbenchTab, configs, 150+ untracked P16 docs). **No secrets in commit.**

---

## 3. Is the QA alias usable?

**Yes.**

- URL: https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer
- Deployment: `dpl_7LuRLamWCHoEo5xVNie1TvFmtk7Q` · Ready
- Bundle: `index-Bs99AAgT.js` (fixed)
- Cloud Run API: healthy · intake key present in bundle

See `P16_QA_ALIAS_VERIFICATION.md`.

---

## 4. Did all three realistic cases pass?

| Case | Phone | Verdict |
|------|-------|---------|
| A — Tesla Model Y | `7145559104` | **PASS** |
| B — Honda Accord | `7145559102` | **PASS** |
| C — BMW X5 | `7145559103` | **PASS** |

See `P16_REALISTIC_CASE_SMOKE_TEST_REPORT.md`.

---

## 5. Did phone return restore case memory?

**Yes.** For all three phones:

Phone Return Key → Active Case Lookup → GET `/api/inbox/cases/{id}` → same messages + status on re-lookup.

**CASE MEMORY: PASS**

---

## 6. Did the four-state model behave correctly?

| API state | Customer label | Verified on |
|-----------|----------------|-------------|
| `awaiting_customer` | 等客户补资料 | B, C |
| `submitted_to_office` | 已提交办公室 | A (post-formal) |
| `office_processing` | 办公室处理中 | Prior cert `7145559101` (browser session) |
| `closed` | 已关闭 | Mapping documented; not exercised this run |

No customer-visible contradiction. Incomplete cases (B, C) never show false 已提交办公室.

**FOUR-STATE MODEL: PASS**

---

## 7. Safe for Andy to show Wu Xiaojie and Chen Kui?

**Yes — internal supervised pilot on `ui-waterwoods` alias.**

Customer First entry, phone return, case memory, and status truth are certified on Cloud Run + fixed Preview bundle. Use alias only; do not share raw hash URLs.

---

## Risks remaining

1. **Formal submit creates a new case record** — UI patches `customer_phone` onto the new id; API-only callers must mirror this (documented in Case A flow).
2. **Chinese year parsing** — standalone `2023` in Case B did not clear `year` from still_needed; gaps stay visible, no false submit (acceptable for pilot).
3. **Direct Postgres not queried from agent env** — persistence verified via Cloud Run case API (messages + formal timestamps present).

---

## Related docs

| Doc | Purpose |
|-----|---------|
| `P16_COMMIT_PRECHECK.md` | Pre-commit file classification |
| `P16_PRE_COMMIT_VERIFICATION.md` | Build verification |
| `P16_COMMIT_REPORT.md` | Commit SHA + dirty tree |
| `P16_QA_ALIAS_VERIFICATION.md` | Alias + bundle |
| `P16_REALISTIC_CASE_SMOKE_TEST_REPORT.md` | Cases A–C detail |

---

## Final verdict

**GO** — Customer First + Phone Return Key + Case Memory + Status Truth are ready for Chen Kui / Wu Xiaojie internal pilot on the certified QA alias.

---

*End of P16 Commit and QA Smoke Certification*
