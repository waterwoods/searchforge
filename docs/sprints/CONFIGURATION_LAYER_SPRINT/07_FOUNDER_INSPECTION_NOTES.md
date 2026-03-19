# Founder Inspection Notes

**Sprint:** Configuration Layer / Reusable Template Foundation  
**Created:** 2026-03-18

---

## 1. What Founder Should Inspect After This Sprint

1. **Config layout** — `configs/common/`, `configs/industries/insurance/`, `configs/clients/chen_kui/`
2. **New files** — `category_templates.json`, `workflow_defaults.json` (and optionally `ui_copy.json`)
3. **CONFIG_EXTRACTION_GUIDE.md** — Updated with new config files and load order
4. **Demo behavior** — Same as before; no visible change to customer or broker flow

---

## 2. What Should Now Feel More Reusable

- **"We have a template"** — broker_next_step and client_prep are in config, not code
- **"Another broker = new folder"** — configs/clients/new_broker/ with handoff_phrases
- **"Industry swap = new industry folder"** — configs/industries/other_industry/ with markers, templates, category_templates

---

## 3. What Should Now Be Easier to Explain as Product vs Custom Project

- **Before:** "We built this for Chen Kui; it's custom."
- **After:** "We have a configurable broker assistant. Chen Kui is our first client. His wording and handoff phrases are in his config folder. The insurance logic (markers, reply templates, broker guidance) is in the industry folder. Adding another broker is adding a new config folder."

---

## 4. Quick Verification

```bash
# Guardrail
bash scripts/guardrail_inbox_triage.sh

# Scenario pass
LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py
```

---

*End of Founder Inspection Notes*
