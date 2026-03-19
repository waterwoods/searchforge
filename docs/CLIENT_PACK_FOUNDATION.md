# Client Pack Foundation

**Purpose:** Define the practical package model the platform uses: common base → industry pack → client pack.

**Scope:** Unified Intake / Broker Workbench mainline. Chen Kui insurance is the first client.

---

## 1. Package Model (What Each Layer Means)

### Common Platform Base

**What it is:** Shared workflow conventions, defaults, and structure that apply to all clients and industries.

| Item | Status | Location |
|------|--------|----------|
| Intake skeleton (detect → ask → enough? → hand off) | **Implemented** | `triage.py`, `docs/MATURE_INTAKE_SKELETON.md` |
| Shared workflow conventions | **Implemented** | `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` |
| Shared persistence expectations | **Implemented** | `case_store.py`, `data/unified_intake_cases.json` |
| Shared test framework | **Implemented** | `scripts/run_inbox_triage_scenarios.py`, etc. |
| Generic fallback wording | **Partial** | Hardcoded in `triage.py`; future: `configs/common/` |
| Max turns before handoff | **Hardcoded** | `triage.py` (2–3 turns) |

**Reusable:** Yes. **Replaceable:** No (core platform).

---

### Insurance Industry Pack

**What it is:** Insurance-specific markers, reply templates, and notice-handling patterns. Reusable across insurance brokers.

| Item | Status | Location |
|------|--------|----------|
| Intent markers (add_vehicle, payment, cancellation, dmv_help, etc.) | **Config** | `configs/industries/insurance/markers.json` |
| Document item labels (dec page, garaging proof, SR-22, etc.) | **Config** | `configs/industries/insurance/markers.json` |
| Reply templates (add_car, payment_lapse, missing_document, etc.) | **Config** | `configs/industries/insurance/reply_templates.json` |
| Handoff thresholds (add-car enough when year+model+zip) | **Hardcoded** | `triage.py` |
| Category set (cancellation_warning, missing_document, etc.) | **Hardcoded** | `triage.py` |

**Reusable:** Across insurance brokers. **Replaceable:** Yes (swap for another industry).

---

### Chen Kui Client Pack

**What it is:** Chen Kui office phrasing, tone preferences, and optional overrides for industry templates.

| Item | Status | Location |
|------|--------|----------|
| Handoff phrases (add_car / other, zh / en) | **Config** | `configs/clients/chen_kui/handoff_phrases.json` |
| Reply template overrides | **Config** | `configs/clients/chen_kui/reply_overrides.json` |
| Proxy calibration cases | **Config** | `configs/chen_kui_proxy_calibration_cases.json` |
| Office tone (conclusion first, next step second) | **Documented** | `docs/CHEN_KUI_REPLY_STYLE_PROXY.md` |

**Reusable:** No (per client). **Replaceable:** Yes (swap for another broker).

---

## 2. Load / Override Order

**Order:** common → industry → client

| Step | What loads | Override behavior |
|------|------------|-------------------|
| 1 | Common base | Defaults for workflow, labels, fallbacks |
| 2 | Industry pack | Markers, reply templates, document items |
| 3 | Client pack | Handoff phrases, reply_overrides merged into industry templates |

**Reply templates specifically:**
1. Load `configs/industries/insurance/reply_templates.json` (base)
2. Load `configs/clients/chen_kui/reply_overrides.json`
3. For each key in overrides: `templates[key] = {**templates[key], **override}` (shallow merge)

**Handoff phrases:** Client-only. No industry default; Chen Kui pack is the source.

**Markers:** Industry-only. No client override today.

---

## 3. What Is Still Hardcoded (and Why)

| Area | Why |
|------|-----|
| broker_next_step, client_prep | Complex per-category logic; future extraction candidate |
| Handoff thresholds (add-car enough when year+model+zip) | Rules; could move to config later |
| VALID_CATEGORIES, VALID_URGENCIES | Schema; low value to extract |
| FORMAL_DRAFT_MARKERS, UNSENDABLE_DRAFT_MARKERS | Draft quality; could move to common later |
| Classification logic | Core rules; stays in code |
| Some category reply templates (missing_signature, underwriting, renewal, etc.) | Next extraction candidates |

---

## 4. How to Add a New Client

1. Create `configs/clients/<client_id>/`
2. Add `handoff_phrases.json` with `add_car` and `other` keys, each with `zh` and `en` strings
3. Optionally add `reply_overrides.json` with `overrides` key
4. (Future) Add env or runtime switch to select client; today triage loads `chen_kui` by default

---

## 5. How to Add a New Industry

1. Create `configs/industries/<industry>/markers.json`
2. Create `configs/industries/<industry>/reply_templates.json`
3. Adapt `config_loader.py` to accept industry parameter; today it loads `insurance` only

---

## 6. Demo Honesty

| Claim | Reality |
|-------|---------|
| Package layering is real | **Yes** — markers, reply templates, handoff phrases load from config; merge order is implemented |
| Hot-swap engine exists | **No** — no runtime client/industry switch; paths are fixed |
| Common base has config | **Partial** — workflow is in code; no `configs/common/` files yet |
| Future portability | **Structure ready** — new client = new folder + handoff_phrases; new industry = new folder + markers + templates |

---

*See also: `docs/CONFIG_EXTRACTION_GUIDE.md`, `docs/KNOWLEDGE_ARCHITECTURE_AND_CONFIG_LAYER.md`*
