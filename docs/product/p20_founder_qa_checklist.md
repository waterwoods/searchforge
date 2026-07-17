# P20 Founder QA Checklist

**Governing SSOT:** `docs/product/p20_product_north_star.md`  
**Do not duplicate gate rules here.** This checklist only defines order.

## Mandatory order

1. **Mini Program Build Gate** — North Star §K  
   `cd miniapp && npm run build:gate` must **PASS**.  
   If it fails: **STOP**. Do not open Form QA, Navigation QA, or physical Preview.

2. **DevTools rebuild** (only after Build Gate PASS)  
   - 清缓存 → 全部清除  
   - 重新编译  
   - Generate a **new** Preview QR  
   - Remote Debug connects  
   - Start Claim renders — **not** `wx://not-found`

3. **Founder Form Gate** — North Star §I  
   (including State-to-Payload sub-gate)

4. **Founder Entry and Navigation Gate** — North Star §J

5. **Physical-device QA** — record evidence before Capability Done

## Worksheet

Use `docs/product/p20_production_loop_template.md` for scorecard and hard-gate
checkboxes. Gate definitions live only in the North Star.
