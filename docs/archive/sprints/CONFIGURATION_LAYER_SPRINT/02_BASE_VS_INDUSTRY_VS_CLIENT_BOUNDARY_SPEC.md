# Base vs Industry vs Client Boundary Spec

**Sprint:** Configuration Layer / Reusable Template Foundation  
**Created:** 2026-03-18

---

## 1. Common Base Layer

**What belongs:** Shared workflow conventions, defaults, and structure that apply to all clients and industries.

| Item | Status | Location |
|------|--------|----------|
| Intake skeleton (detect → ask → enough? → hand off) | Implemented | triage.py, MATURE_INTAKE_SKELETON.md |
| Shared workflow conventions | Implemented | CUSTOMER_ENTRY_REPLY_STRATEGY.md |
| Case store, persistence | Implemented | case_store.py, data/unified_intake_cases.json |
| Generic fallback wording | **Partial** | Hardcoded in triage.py; target: configs/common/ |
| Max turns before handoff | Hardcoded | triage.py |
| Generic broker_next_step fallback | Hardcoded | triage.py: "Review and act on {category}." |
| Generic client_prep fallback | Hardcoded | triage.py: "Please have any relevant documents..." |
| DRAFT_QUALITY_PHRASES, FORMAL_DRAFT_MARKERS | Hardcoded | triage.py |

**Reusable:** Yes. **Replaceable:** No (core platform).

---

## 2. Industry Configuration Layer (Insurance)

**What belongs:** Insurance-specific markers, reply templates, document types, scenario definitions, broker guidance.

| Item | Status | Location |
|------|--------|----------|
| Intent markers (add_vehicle, payment, cancellation, etc.) | **Config** | configs/industries/insurance/markers.json |
| Document item labels | **Config** | markers.json document_items |
| Reply templates (add_car, payment_lapse, missing_document, etc.) | **Config** | configs/industries/insurance/reply_templates.json |
| Add-car next-step prompts | **Config** | configs/industries/insurance/add_car_rules.json |
| broker_next_step per category | **Hardcoded** | triage.py _get_category_templates |
| client_prep per category | **Hardcoded** | triage.py _get_category_templates |
| Handoff thresholds (add-car enough when year+model+zip) | Hardcoded | triage.py |
| VALID_CATEGORIES, VALID_URGENCIES | Hardcoded | triage.py (schema; low value to extract) |

**Reusable:** Across insurance brokers. **Replaceable:** Yes (swap for another industry).

---

## 3. Client Configuration Layer (Chen Kui)

**What belongs:** Chen Kui office phrasing, tone preferences, handoff labels, UI copy.

| Item | Status | Location |
|------|--------|----------|
| Handoff phrases (add_car / other, zh / en) | **Config** | configs/clients/chen_kui/handoff_phrases.json |
| Reply template overrides | **Config** | configs/clients/chen_kui/reply_overrides.json |
| UI: "办公室", "陈奎", "联系人工" | **Hardcoded** | UnifiedIntakePage.tsx |
| UI: "保险经纪人智能助手" | **Hardcoded** | AppLayout.tsx |
| UI: Quick-start button labels | **Hardcoded** | UnifiedIntakePage.tsx QUICK_START_BUTTONS |
| Simulation Assistant scenarios | **Config** | ui/src/config/simulation_assistant_scenarios.json |

**Reusable:** No (per client). **Replaceable:** Yes (swap for another broker).

---

## 4. What Is Currently Mixed and Should Be Separated

| Mixed area | Base | Industry | Client | Action |
|------------|------|----------|--------|--------|
| broker_next_step strings | Generic fallback | Per-category guidance | — | Extract to industry |
| client_prep strings | Generic fallback | Per-category prep | — | Extract to industry |
| "陈奎办公室" in handoff fallback | — | — | Client | Already in handoff_phrases; remove hardcoded fallback |
| "办公室会尽快处理" | — | — | Client | Centralize in client config |
| Quick-start labels | — | Industry (scenario types) | Client (wording) | Split: industry ids, client labels |

---

## 5. Load / Override Order

**Order:** common → industry → client

1. **Common:** workflow defaults, generic fallbacks
2. **Industry:** markers, reply_templates, broker_next_step, client_prep, add_car_rules
3. **Client:** handoff_phrases, reply_overrides, UI copy overrides

---

*See also: 03_REUSABLE_CONFIGURATION_INVENTORY_SPEC.md*
