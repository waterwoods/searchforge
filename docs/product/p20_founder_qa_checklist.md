# P20 Founder QA Checklist

**Governing SSOT:** `docs/product/p20_product_north_star.md`  
**Do not duplicate gate rules here.** This checklist only defines order.

## Mandatory order

1. **Mini Program Build Gate** — North Star §K  
   `cd miniapp && npm run build:gate` must **PASS**.  
   If it fails: **STOP**. Do not open Form QA, Navigation QA, or physical Preview.

1b. **Unified claim release gate (P26H)** — before Preview / Founder device  
   Before QA deploy: `bash scripts/run_claim_release_gate.sh --local` → **READY FOR QA DEPLOY**  
   After QA deploy: `bash scripts/run_claim_release_gate.sh --qa` → **READY FOR FOUNDER QA**  
   (Requires `P26H_QA_BASE_URL` + `UNIFIED_INTAKE_SUPPORT_API_KEY` and QA flags  
   `ENABLE_P26H_FIXTURE_RUNNER=1` + `UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1`.)  
   If either gate fails or prints **STOP**: do not hand Founder a Preview.

2. **DevTools rebuild** (only after local + QA gates PASS)  
   - 清缓存 → 全部清除  
   - 重新编译  
   - Generate a **new** Preview QR  
   - Remote Debug connects  
   - Start Claim renders — **not** `wx://not-found`

3. **Founder Form Gate** — North Star §I (including State-to-Payload)  
4. **Founder Entry and Navigation Gate** — North Star §J  

5. **Founder device confirmation (~5 minutes)** — visual only  
   1. Open a fresh claim  
   2. Tap insurance / photos / story once  
   3. Confirm visual quality  
   4. Exit and reopen  
   5. Confirm Broker follow-up UX  

   Founder is **not** responsible for discovering: wrong route, missing parameter,
   blank page, stale case state, false completion, broken resume, or Projection mismatch.

6. **Golden Production QA** (release / Founder demo / customer pilot)  
   Single production acceptance standard:  
   `docs/product/p24f_golden_production_qa_flow.md`  
   One token → one Camry Case → full customer + broker journey → GO / NO-GO.  
   Do **not** substitute `pages/dev/*` prototypes or mock `broker-workbench/`.

## Worksheet

Use `docs/product/p20_production_loop_template.md` for scorecard and hard-gate
checkboxes. Gate definitions live only in the North Star.

For release readiness after gates 1–5, run the Golden Production QA script in
`docs/product/p24f_golden_production_qa_flow.md`.
