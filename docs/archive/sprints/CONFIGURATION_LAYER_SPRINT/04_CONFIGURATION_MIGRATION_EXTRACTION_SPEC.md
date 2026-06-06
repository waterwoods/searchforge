# Configuration Migration / Extraction Spec

**Sprint:** Configuration Layer / Reusable Template Foundation  
**Created:** 2026-03-18

---

## 1. Extraction 1: broker_next_step + client_prep → category_templates.json

| Field | Current location | Target | Migration |
|-------|------------------|--------|-----------|
| broker_next_step (per category) | triage.py _get_category_templates | configs/industries/insurance/category_templates.json | New file; config_loader; triage reads from loader |
| client_prep (per category) | triage.py _get_category_templates | Same | Same |

**Structure:**
```json
{
  "version": "1",
  "description": "Per-category broker_next_step and client_prep. Used when config present; falls back to triage hardcoded.",
  "categories": {
    "cancellation_warning": {
      "broker_next_step": "Confirm whether the cancellation is still active...",
      "client_prep": "The cancellation notice, any payment confirmation..."
    },
    "payment_lapse_expiration": { ... },
    "missing_document": { "broker_next_step": "...", "client_prep": "dynamic" },
    ...
  }
}
```

**Note:** missing_document and customer_question have dynamic client_prep (built from text). For those, we keep a static broker_next_step in config and leave dynamic logic in code.

**Verification:** Run guardrail_inbox_triage.sh; compare triage output before/after.

---

## 2. Extraction 2: Common Workflow Defaults

| Field | Current location | Target | Migration |
|-------|------------------|--------|-----------|
| Generic broker_next_step fallback | triage.py | configs/common/workflow_defaults.json | New file; config_loader; triage uses when category missing |
| Generic client_prep fallback | triage.py | Same | Same |
| Generic client_reply_draft fallback | triage.py | Same | Same |

**Structure:**
```json
{
  "version": "1",
  "description": "Common workflow fallbacks when category-specific config missing",
  "fallbacks": {
    "broker_next_step": "Review and act on {category}.",
    "client_prep": "Please have any relevant documents or information ready.",
    "client_reply_draft": "Thank you for reaching out. We are reviewing your message..."
  }
}
```

**Verification:** Guardrail; triage unclear category still returns sensible output.

---

## 3. Extraction 3: Client UI Copy (Optional / Loop 2)

| Field | Current location | Target | Migration |
|-------|------------------|--------|-----------|
| "办公室", "陈奎", "联系人工" | UnifiedIntakePage.tsx | configs/clients/chen_kui/ui_copy.json | New file; UI fetches or imports |
| "保险经纪人智能助手" | AppLayout.tsx | Same | Same |
| Quick-start labels | QUICK_START_BUTTONS | Same or separate | Evaluate effort |

**Approach:** Create ui_copy.json; add API or static import for UI to read. Defer full UI config if time-constrained.

---

## 4. Testing / Verification Approach

| Check | Command |
|-------|---------|
| Scenario pack | `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` |
| Multi-turn | `LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` |
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` |
| Frontend build | `cd ui && npm run build` |

---

*See also: 05_EXECUTION_OUTLINE.md*
