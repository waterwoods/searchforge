# Execution Outline — This Sprint

**Sprint name:** Client-Pack Operating Manual / Productization Index  
**Mode:** Document-driven audit → organize → index → checklists → summarize → refine  
**Target time:** 45–90 minutes  

---

## Phases executed

1. **Audit (read-only)**  
   - `triage.py` (structure, config integration, workflow keys)  
   - `config_loader.py` (load order, `CLIENT_ID`, merge rules)  
   - `routes/inbox_triage.py` (API surface, soft_route)  
   - `case_store.py` (persistence role)  
   - `configs/industries/insurance/*`, `configs/clients/chen_kui/*`, `configs/clients/socal_precision/*`, `configs/common/*`  
   - `UnifiedIntakePage.tsx` (head), `clientConfig.ts`  
   - `guardrail_inbox_triage.sh` (full step list)  
   - Script inventory: cross-client A/B, append boundary, residual copy, add-car batteries  

2. **Organize**  
   - Layer diagram: UI → API → engine → loader → configs  
   - Taxonomy: engine / industry / client / common / batteries  

3. **Index**  
   - `PRODUCTIZATION_INDEX.md` — navigation + tables  

4. **Operating manual**  
   - `CLIENT_PACK_OPERATING_MANUAL_BLUEPRINT.md`  
   - `MODULE_ARCHITECTURE_GUIDE.md`  
   - `FILE_FOLDER_RESPONSIBILITY_MAP.md`  

5. **Checklists**  
   - `SAME_INDUSTRY_MIGRATION_CHECKLIST.md`  
   - `VALIDATION_REGRESSION_CHECKLIST.md`  

6. **Founder aids**  
   - `READ_THIS_FIRST.md`, `GLOSSARY.md`, `IMPORTANT_VS_NOT_IMPORTANT.md`, `SAFE_VS_RISKY_CHANGES.md`  
   - `FOUNDER_INSPECTION_NOTES.md`, `FINAL_REPORT.md` (judgment + 中文总结)  

---

## Explicit question coverage (where answered)

| # | Question | Primary doc |
|---|----------|-------------|
| 1 | Major layers | PRODUCTIZATION_INDEX, MODULE_ARCHITECTURE_GUIDE |
| 2 | Modules / files | MODULE_ARCHITECTURE_GUIDE, FILE_FOLDER_RESPONSIBILITY_MAP |
| 3 | Engine / industry / client / lexicon / battery | FILE_FOLDER_RESPONSIBILITY_MAP, PRODUCTIZATION_INDEX |
| 4 | Migration-important files | SAME_INDUSTRY_MIGRATION_CHECKLIST, FILE_FOLDER_RESPONSIBILITY_MAP |
| 5–6 | Safe vs risky | SAFE_VS_RISKY_CHANGES, FILE_FOLDER_RESPONSIBILITY_MAP |
| 7 | Validation | VALIDATION_REGRESSION_CHECKLIST |
| 8 | Smallest onboarding process | SAME_INDUSTRY_MIGRATION_CHECKLIST |
| 9 | Founder first vs later | IMPORTANT_VS_NOT_IMPORTANT |
| 10 | Strengths / risks | FINAL_REPORT, FOUNDER_INSPECTION_NOTES |

---

## Out of scope (per sprint charter)

Large features, framework replacement, OCR, carrier API, multi-tenant auth, broad UI redesign, heavy engine refactors.

---

*Deliverables live only under this folder unless linked from repo docs later.*
