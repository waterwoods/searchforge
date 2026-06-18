# P16 Preview Phone Lookup — Live Certification

**Sprint:** P16-PREVIEW-ACTIVE-CASE-API-KEY-RECOVERY  
**Date:** 2026-06-07  
**Preview URL:** https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer  
**Deployment:** `dpl_BKUCFQnAst7QVoYiZmAscPcaZzjB` · Bundle `index-Bb0VZ9fA.js`

---

## Test matrix

| # | Scenario | Input | Expected | Result |
|---|----------|-------|----------|--------|
| 1 | Valid phone lookup | `2039935973` + Continue | No `无法验证手机号`; API success | **PASS** — shows **Active Add-Car Request** card (seeded case exists for this phone in Postgres) |
| 2 | Known test active phone | `6265551002` + Continue | Active case status card if seeded | **PASS** — Active Add-Car Request + Continue Request / Contact Broker |
| 3 | Invalid phone format | `123` + Continue | Client-side validation, no API auth error | **PASS** — stays on entry; shows 10-digit validation message (not auth error) |
| 4 | Customer tab | default | Loads entry screen | **PASS** |
| 5 | Office tab | click 办公室工作台 | Queue / workbench loads | **PASS** |
| 6 | Simulation tab | click 场景仿真 | Simulation controls load | **PASS** |
| 7 | Runtime stability | all tabs | No blank page / red screen | **PASS** |
| 8 | active-case via UI | phones above | HTTP 200 through browser | **PASS** (no auth error UI) |

---

## Scenario 1 detail — phone `2039935973`

Backend (with key): `has_active_case: true` for this phone from prior test session (`case_31f7fb7de023`). UI correctly shows **active case path**, not "Start New Add-Car Request."

For a phone with **no** active case (e.g. `5555551234`), backend returns `has_active_case: false` / HTTP 200 — UI would show Start New path (verified via API; not re-run in browser this sprint).

---

## Scenario 2 detail — phone `6265551002`

Backend: `has_active_case: true`, `case_id: case_23e113d4b686`.  
UI: Active Add-Car Request heading, missing-fields list, action buttons.

---

## Scenario 3 detail — phone `123`

No network call to `active-case` (client validation in `CustomerFirstEntryScreen.handleContinue`).  
Page text includes 10-digit requirement; **no** `无法验证手机号`.

---

## Pre-fix vs post-fix

| | Pre-fix (`index-CMdMnAqV.js`) | Post-fix (`index-Bb0VZ9fA.js`) |
|---|-------------------------------|--------------------------------|
| active-case status | 401 | 200 |
| UI after Continue | 无法验证手机号 | Active case or start-new flow |

---

## Certification verdict

**PASS** — Preview phone lookup restored. Customer First Continue flow works through Cloud Run with intake API key in bundle.

---

*End of P16 Preview Phone Lookup Live Certification*
