# READ THIS FIRST — Client-Pack & Unified Intake Productization

**Audience:** Founder / operator (non-engineer welcome; engineers use the same map).

**What this sprint folder is:** A compact **operator’s map** for SearchForge **Unified Intake** (broker inbox triage + demo UI). It explains layers, where configs live, what is safe to change, and how to validate after changes.

**Read in this order (about 25–40 minutes total):**

| Order | Doc | Purpose |
|------|-----|---------|
| 1 | [PRODUCTIZATION_INDEX.md](./PRODUCTIZATION_INDEX.md) | Layers, file groups, reading order, validation pointers |
| 2 | [MODULE_ARCHITECTURE_GUIDE.md](./MODULE_ARCHITECTURE_GUIDE.md) | Plain-language: what each major module does |
| 3 | [FILE_FOLDER_RESPONSIBILITY_MAP.md](./FILE_FOLDER_RESPONSIBILITY_MAP.md) | Engine vs industry vs client vs common vs UI vs batteries |
| 4 | [SAME_INDUSTRY_MIGRATION_CHECKLIST.md](./SAME_INDUSTRY_MIGRATION_CHECKLIST.md) | Step-by-step second same-industry broker |
| 5 | [VALIDATION_REGRESSION_CHECKLIST.md](./VALIDATION_REGRESSION_CHECKLIST.md) | What to run after any change; what blocks release |
| 6 | [IMPORTANT_VS_NOT_IMPORTANT.md](./IMPORTANT_VS_NOT_IMPORTANT.md) | Priorities to avoid thrash |
| 7 | [SAFE_VS_RISKY_CHANGES.md](./SAFE_VS_RISKY_CHANGES.md) | Change posture at a glance |

**Quick anchors:**

- **Runtime switch for “which broker”:** environment variable `CLIENT_ID` (default `chen_kui`). Backend loads `configs/clients/<CLIENT_ID>/`.
- **Core brain (logic):** `services/fiqa_api/inbox_triage/triage.py` — high impact; don’t edit casually for “copy” changes.
- **Copy / tone hot-plug:** `configs/clients/<id>/` (handoff, reply overrides, UI strings) + `configs/industries/insurance/` (shared auto-insurance lexicon).
- **Must-run regression umbrella:** `bash scripts/guardrail_inbox_triage.sh` (when developing triage).

**Glossary:** [GLOSSARY.md](./GLOSSARY.md)

**Sprint meta:** [EXECUTION_OUTLINE.md](./EXECUTION_OUTLINE.md), [FOUNDER_INSPECTION_NOTES.md](./FOUNDER_INSPECTION_NOTES.md), [FINAL_REPORT.md](./FINAL_REPORT.md)

---

*Sprint: Client-Pack Operating Manual / Productization Index — March 2025*
