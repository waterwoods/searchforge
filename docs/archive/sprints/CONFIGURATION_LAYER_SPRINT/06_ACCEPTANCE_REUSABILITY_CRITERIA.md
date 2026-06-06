# Acceptance / Reusability Criteria

**Sprint:** Configuration Layer / Reusable Template Foundation  
**Created:** 2026-03-18

---

## 1. Clearer Boundaries

- [ ] Base vs industry vs client is documented and reflected in config layout
- [ ] At least one common config file exists (workflow_defaults.json)
- [ ] broker_next_step and client_prep are loaded from industry config when present

---

## 2. Reduced Hardcoding

- [ ] _get_category_templates no longer contains 12+ hardcoded broker_next_step strings
- [ ] Generic fallbacks come from config, not triage.py literals

---

## 3. Easier Client Reuse

- [ ] New broker = new folder under configs/clients/ with handoff_phrases + optional reply_overrides
- [ ] Config extraction guide is updated with new files

---

## 4. Easier Future Migration to A/B/C Clients

- [ ] Structure supports: configs/clients/broker_b/, configs/clients/broker_c/
- [ ] No runtime switch required; path selection is future work

---

## 5. Acceptable to Defer

- Runtime client/industry switch
- Full UI config (all copy from config)
- Handoff thresholds in config
- VALID_CATEGORIES, VALID_URGENCIES in config

---

## 6. Guardrail and Build

- [ ] `bash scripts/guardrail_inbox_triage.sh` → PASS
- [ ] `cd ui && npm run build` → success (if UI touched)

---

*See also: 07_FOUNDER_INSPECTION_NOTES.md*
