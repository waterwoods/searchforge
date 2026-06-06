# P16-C Phase 6 & 7 — Final Review

**Date:** 2026-05-31  
**Sprint validated:** Sprint A — Broker Front Door (`c2e3dff`)  
**Sprint type:** Validation only — no feature changes made in P16-C  

---

## PHASE 6 — Top Findings

### TOP_20_DISCOVERIES

1. Default tab fix alone likely moves unsupervised Day 1 from ~28 to ~65+ (biggest ROI)  
2. Engineer chrome purge (PG 镜像, API URL) removes primary "beta" signal on production workbench  
3. Inline 3 practice scenarios fully replace hidden Simulation tab for Day 0 playbook  
4. `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` is **build-time** — merge without env = zero Sprint A benefit on Vercel  
5. Production alias still defaults to 客户报送 with 4 tabs — **Sprint A invisible to brokers today**  
6. No Vercel Preview exists for `sprint-a/broker-front-door` despite push  
7. Wayfinding banner locates paste in <10s without tab switching  
8. 「取消/付款风险」 practice loads realistic cancellation text into paste — click-to-try works  
9. Guardrail 13/13 PASS — Sprint A did not regress triage engine  
10. Cloud Run `/readyz` intake_path_ready=true — backend trial-ready independent of UI deploy  
11. Local preview CORS error reproduces exactly what brokers would see if Preview origin not allowlisted  
12. Production workbench (when found) still shows PG tags and English next-step leaks  
13. Pilot intro collapsed by default reduces Day 0 overwhelm  
14. Tab count 4→2 removes 我的办理 and 场景仿真 confusion  
15. Empty queue hides simplified filters — first-time broker sees less lifecycle tooling than designed  
16. Header card Add-Car tagline contradicts cancellation-first constitution on every load  
17. Chen Kui team branding (金盾·陈魁团队) builds immediate trust for named pilot  
18. Simulation average first-30s **73** vs pre-Sprint ~15 — orientation problem largely solved  
19. Payment willingness unchanged at Day 7 — UI sprint cannot create ROI proof  
20. Founder Control score **decreased** (−2) because code/deploy divergence creates false confidence risk  

### TOP_10_SURPRISES

1. **Vercel never auto-built** the Sprint A branch — 26-day-old Preview is latest  
2. Production **has** `VITE_API_BASE_URL` but **not** product_only — worst combo (API works, wrong UI)  
3. Demo queue shows progress copy (`0/12 条示例已就绪`) even when network fails — mixed signal  
4. Practice scenarios work without any API call — stronger than expected for offline demo  
5. Sidebar lab routes fully hidden in product_only — cleaner than scorecard assumed  
6. Node 20 default in WSL breaks `npm run dev` — Node 22 required for validation  
7. Production workbench tab **does** load real cases with PG labels — engineer chrome worse than empty-state review suggested  
8. 5-minute simulation score **drops** to 58 for new broker if demo queue fails — deploy is UX  
9. Cap 4 Intake score rises (+6) from Cap 1 default tab alone — surface alignment has downstream effect  
10. Sprint A success is **deploy-blocked**, not code-blocked  

### TOP_10_REGRESSIONS

1. **None in triage engine** — guardrail PASS  
2. **None in contracts/constitution** — validation-only sprint  
3. **Perceived regression:** Network Error banner on misconfigured Preview — looks like product bug  
4. **Copy regression risk:** Tab still says 加车旗舰路径 after cancellation-first intro — cognitive dissonance  
5. **False progress risk:** Local PASS may imply Production updated — it is not  
6. **Founder Control −2:** Deploy drift is new operational regression  
7. **Filter visibility:** Empty queue hides broker filters — regression vs populated-queue design intent  
8. **Dev UX:** `npm run dev` fails on Node 20 — local founder path friction (not broker-facing)  
9. **客户报送 tab still visible:** Unsupervised brokers can still wander to Add-Car portal  
10. **No E2E proof** of auto-open cancellation — code present, behavior not observed this session  

### TOP_10_NEXT_ACTIONS (Constitution scope only)

| # | Action | Capability | Sprint |
|---|--------|------------|--------|
| 1 | Deploy Vercel Preview with product_only + API URL build args | 1, 7 | Deploy gate |
| 2 | Persist `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` on Vercel Preview + Production | 1, 7 | Deploy gate |
| 3 | Add Preview origin to Cloud Run `ALLOWED_ORIGINS` | 1, 7 | Deploy gate |
| 4 | Andy 5-minute dry-run on Preview URL (playbook Day 0) | 1, 7 | Founder gate |
| 5 | Fix tab suffix / header tagline to cancellation-first (ui_copy) | 1 | Sprint A tail or B |
| 6 | Sprint B — pricing + pilot terms + invoice on one-pager | 6 | Sprint B |
| 7 | Supervised Chen Kui 7-day trial with observation log | 6 | Trial execution |
| 8 | Prod Postgres + `/readyz` validation on pilot URL | 7, 3 | Parallel O2–O3 |
| 9 | Prominent 「更新客户新消息」 for follow-up paste | 5 | Sprint C |
| 10 | Fix-now draft quality from real-message trial log (max 3) | 3 | Post-trial only |

**Explicitly out of scope:** Stripe, CRM, WeChat sync, platform work, repo cleanup.

---

## PHASE 7 — Final Verdict

### 1. Is Sprint A successful?

**Yes — conditionally.** Code delivers the contracted Front Door improvements (default tab, chrome purge, wayfinding, inline practice, tab reduction). Success is **incomplete** until Vercel Preview E2E PASS and Andy dry-run.

### 2. Is Broker Front Door materially improved?

**Yes.** Score **35 → 68 (+33)**. Unsupervised orientation ~**28 → 71** (Chen Kui simulation). The primary P10/P11 Day-1 failure mode (wrong tab + engineer chrome) is addressed in product_only builds.

### 3. Is Preview deployment justified?

**Yes.** Code quality acceptable (guardrail PASS, build PASS). Preview is the minimum step to prove demo queue + shareable URL before merge or broker access. **Production deploy is not justified.**

### 4. Is Chen Kui closer to paying?

**Closer to trialing, not paying.** Trust and orientation improved — he would likely complete a **supervised** kickoff. Payment still requires 7-day ROI proof, pricing, and terms (unchanged). Willingness to pay at Day 7: **~45/100** (same commercial gap).

### 5. What is the next sprint?

| Priority | Sprint | Scope |
|----------|--------|-------|
| **Immediate** | **Deploy gate** (not a feature sprint) | Vercel Preview + env + CORS + Andy dry-run |
| **Next feature sprint** | **Sprint B — Trial Conversion** | Pricing, pilot terms (Chinese), invoice template, one-pager |
| **Parallel** | **Founder Control O2–O3** | Prod Postgres, `/readyz`, persistence validation |
| **Then** | **Sprint C — Case Lifecycle** | Follow-up paste prominence, queue wayfinding polish |

---

## One-Line Verdict

**The broker front door is now orientation-ready on product_only builds, but not yet broker-proven until Andy ships a Vercel Preview with the correct env and completes a 5-minute dry-run.**

---

## Summary Table

| Question | Answer |
|----------|--------|
| Sprint A successful? | **Yes (conditional on Preview)** |
| Cap 1 materially improved? | **Yes — 35 → 68** |
| Overall product score | **60 → 67** |
| Create Vercel Preview? | **YES** |
| Chen Kui paying? | **Not yet — trial + proof required** |
| Next sprint | **Deploy gate → Sprint B (Trial Conversion)** |

---

*End of P16-C Phase 6 & 7 — Final Review*
