# Safe vs Risky Changes — Quick Reference

| Area | Risk | Guidance |
|------|------|------------|
| `configs/clients/<id>/ui_copy.json` | **Low** | Prefer for branding / visible copy |
| `configs/clients/<id>/handoff_phrases.json` | **Low** | Handoff + stitched; run A/B + guardrail |
| `configs/clients/<id>/reply_overrides.json` | **Low–medium** | Shallow merge; watch missing keys |
| `configs/industries/insurance/reply_templates.json` | **Medium** | Affects all brokers |
| `configs/industries/insurance/markers.json` | **Medium–high** | False positives / category drift |
| `configs/industries/insurance/add_car_rules.json` | **Medium** | Add-car UX for everyone |
| `configs/common/soft_route_inbox.json` | **Medium** | Global soft-route text |
| `services/fiqa_api/inbox_triage/triage.py` | **High** | Engine; broad blast radius |
| `services/fiqa_api/inbox_triage/config_loader.py` | **High** | Wrong merge = cross-client bugs |
| `services/fiqa_api/routes/inbox_triage.py` | **High** | API + persistence wiring |
| `services/fiqa_api/inbox_triage/case_store.py` | **High** | Data shape |
| `ui/src/pages/UnifiedIntakePage.tsx` | **Medium** | UX logic; test manually |
| `ui/src/api/clientConfig.ts` | **Medium** | Defaults skew one broker |
| `scripts/guardrail_inbox_triage.sh` | **Medium** | Don’t weaken gates without replacement tests |

**Rule of thumb:** If the change is **words**, stay in **JSON**. If the change is **when** something happens, expect **engine** work + full regression.

---

*Detail: [FILE_FOLDER_RESPONSIBILITY_MAP.md](./FILE_FOLDER_RESPONSIBILITY_MAP.md)*
