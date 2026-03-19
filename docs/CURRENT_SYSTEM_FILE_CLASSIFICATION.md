# Current System File Classification

**Purpose:** Map the repo into the Knowledge Architecture layers.  
**Created:** 2026-03-09 — Knowledge Architecture + Config Layer Sprint

---

## 1. Core Logic Files

| File | Purpose | Target Layer | Status |
|------|---------|---------------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | Intent detection, handoff logic, category templates, client draft builder | Rules + Client-specific (mixed) | **Good place.** Consider extracting markers to config later. |
| `services/fiqa_api/inbox_triage/case_store.py` | Case CRUD, persistence | State | **Good place.** |
| `services/fiqa_api/routes/inbox_triage.py` | API route for triage, cases | Rules (orchestration) | **Good place.** |
| `services/fiqa_api/services/search_core.py` | RAG search, Qdrant routing | Rules (routing) + RAG | **Good place.** |
| `services/fiqa_api/utils/qdrant_adapter.py` | Qdrant API compatibility | RAG | **Good place.** |
| `services/fiqa_api/clients.py` | Embedding, Qdrant client init | RAG | **Good place.** |

---

## 2. Config Files (Unified Intake / Broker)

| File | Purpose | Target Layer | Status |
|------|---------|---------------|--------|
| `configs/inbox_triage_scenarios.json` | Triage regression (category, urgency) | Tests | **Good place.** Consider `configs/tests/` later. |
| `configs/chen_kui_proxy_calibration_cases.json` | Chen Kui draft style regression | Tests + Client-specific | **Good place.** Consider `configs/clients/chen_kui/` later. |
| `configs/customer_entry_multi_turn_simulations.json` | Multi-turn handoff regression | Tests | **Good place.** Consider `configs/tests/` later. |
| `configs/expression_robustness_cases.json` | Phrasing robustness regression | Tests | **Good place.** Consider `configs/tests/` later. |
| `configs/broker_demo_urls.json` | Curated URLs for auto_insurance_demo_core | RAG (corpus) | **Good place.** |
| `configs/broker_sr22_validation.json` | SR-22 validation cases | Tests | **Good place.** |
| `configs/broker_longtail_questions.json` | Longtail Q&A | Tests / RAG eval | **Good place.** |
| `configs/broker_demo_urls.txt` | Plain URL list | RAG | **Good place.** |

---

## 3. Config Files (RAG / Demo / Other)

| File | Purpose | Target Layer | Status |
|------|---------|---------------|--------|
| `configs/demo.env.example` | Demo env template | Config | **Good place.** |
| `configs/presets_v10.json` | Search presets | RAG | **Good place.** |
| `configs/fiqa_suite.yaml` | FiQA eval | RAG / Tests | **Good place.** |
| `configs/control.yaml` | Experiment control | RAG | **Good place.** |
| `configs/demo_*.yaml` | Demo configs | RAG | **Good place.** |
| `configs/autotuner_*.yaml` | Autotuner | RAG | **Good place.** |
| `configs/slo_strategies/*.json` | SLO configs | RAG | **Good place.** |
| `configs/presets/*.yaml` | Search presets | RAG | **Good place.** |
| `configs/inbox_triage_scenarios.json` | Triage regression | Tests | **Good place.** |

---

## 4. State / Persistence Files

| File | Purpose | Target Layer | Status |
|------|---------|---------------|--------|
| `data/unified_intake_cases.json` | Saved broker cases | State | **Good place.** |
| `services/fiqa_api/jobhunter/jobhunter_cache.sqlite3` | JobHunter cache | State (out of scope) | **Out of scope.** |

---

## 5. RAG / Qdrant Assets

| Asset | Purpose | Target Layer | Status |
|-------|---------|---------------|--------|
| `auto_insurance_demo_core` (Qdrant collection) | Auto insurance corpus | Common domain knowledge | **Good place.** |
| `auto_insurance_v2_clean` (Qdrant collection) | Larger corpus | Common domain knowledge | **Good place.** |
| `scripts/build_demo_core_collection.py` | Build demo corpus | RAG | **Good place.** |
| `scripts/discover_auto_insurance_sources.py` | Discovery | RAG | **Good place.** |
| `results/auto_insurance/` | Eval reports | Tests | **Good place.** |

---

## 6. Test / Validation Scripts

| Script | Purpose | Protects | Status |
|--------|---------|----------|--------|
| `scripts/run_inbox_triage_scenarios.py` | Triage regression | Category, urgency | **Good place.** |
| `scripts/run_chen_kui_proxy_calibration.py` | Draft style | Chen Kui proxy | **Good place.** |
| `scripts/run_multi_turn_simulations.py` | Multi-turn handoff | Handoff flow | **Good place.** |
| `scripts/run_expression_robustness.py` | Phrasing robustness | Expression variants | **Good place.** |
| `scripts/test_inbox_triage_api.py` | API test | API contract | **Good place.** |
| `scripts/guardrail_inbox_triage.sh` | Guardrail | Pre-demo quality | **Good place.** |
| `scripts/unified_intake_smoke_check.sh` | Smoke + guardrail | Smoke flow | **Good place.** |

---

## 7. Key Documentation

| Doc | Purpose | Status |
|-----|---------|--------|
| `docs/MATURE_INTAKE_SKELETON.md` | Shared flow shape | Rules (design) |
| `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` | Per-category strategy | Rules (design) |
| `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` | Broker handoff format | Rules (design) |
| `docs/CHEN_KUI_REPLY_STYLE_PROXY.md` | Chen Kui tone | Client-specific |
| `docs/CONTINUOUS_CUSTOMER_INTAKE_MVP.md` | Intake design | Rules (design) |
| `docs/business_rules/insurance_broker_pilot_rules.md` | RAG/broker rules | Rules | Mixed RAG + broker demo |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | How to run | Runbook |
| `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | Demo readiness | Runbook |

---

## 8. What Is Mixed or Unclear

| Area | Issue | Recommendation |
|------|-------|----------------|
| **Markers in triage.py** | ADD_VEHICLE_MARKERS, PAYMENT_MARKERS, etc. are hardcoded | Future: move to `configs/industries/insurance/markers.json` if tunable |
| **Templates in triage.py** | `_build_client_reply_draft` has Chinese/English strings | Future: move to `configs/clients/chen_kui/templates.json` for hot-swap |
| **Doc vs code** | Rules live in docs (MATURE_INTAKE_SKELETON) and code (triage.py) | Keep both; docs = design, code = implementation |
| **Config flat** | All configs in `configs/` root | Propose `configs/tests/`, `configs/clients/chen_kui/` (Stage 5) |

---

## 9. What Should Move Later (Optional)

| Current | Target | When |
|---------|--------|------|
| `configs/inbox_triage_scenarios.json` | `configs/tests/inbox_triage_scenarios.json` | When adding more test packs |
| `configs/chen_kui_proxy_calibration_cases.json` | `configs/clients/chen_kui/proxy_calibration_cases.json` | When adding second client |
| `configs/customer_entry_multi_turn_simulations.json` | `configs/tests/multi_turn_simulations.json` | When adding more test packs |
| `configs/expression_robustness_cases.json` | `configs/tests/expression_robustness_cases.json` | When adding more test packs |
| Markers in triage.py | `configs/industries/insurance/markers.json` | When adding second industry |

**Do NOT move now.** This stage is classification only. Physical moves only when clearly useful.

---

## 10. Summary

| Layer | Count | Clarity |
|-------|-------|---------|
| Rules | triage.py, docs | **Clear** |
| Common domain | Qdrant collections, RAG | **Clear** |
| Client-specific | triage.py, CHEN_KUI_REPLY_STYLE_PROXY.md | **Mixed** (in code) |
| State | case_store.py, data/*.json | **Clear** |
| Tests | configs/*.json, scripts/run_*.py | **Clear** |

**Verdict:** The system is mostly well-placed. The main improvement is clearer config organization (configs/tests/, configs/clients/) and future extraction of markers/templates from code when hot-swap is needed.

---

*End of classification*
