# Flow Lightweight Productization Blueprint

**Product:** SearchForge → Chen Kui Insurance Unified Entry (Unified Intake / Inbox Triage)  
**Sprint:** Flow Lightweight Productization Sprint  
**Mode:** Document-driven, incremental, test-backed — **not** a rewrite.

## Purpose

The flow already works in production and demos. This sprint makes the **architecture legible** to founders, brokers, and future engineers by:

- Naming five clear layers (Common Engine, Industry Pack, Client Pack, Lexicon/Rule Maps, Regression Battery).
- Mapping **today’s code and config** to those layers without moving fragile orchestration.
- Applying **1–3 low-risk fixes** that improve portability (client-aware config, externalized route copy, schema alignment).

## Non-goals

- LangGraph / new orchestration framework  
- OCR, carrier APIs, auth, multi-tenant product build-out  
- Large UI redesign  
- Splitting `triage.py` without exhaustive regression

## Success criteria

- [x] Sprint folder docs exist and are founder-readable.  
- [x] Five-layer map reflects reality (honest about concentration in `triage.py`).  
- [x] Safe implementations merged: client-scoped reply overrides, soft-route copy in config, `ask_driver_only` loaded/saved consistently.  
- [x] `bash scripts/guardrail_inbox_triage.sh` passes.

## Related paths (quick navigation)

| Area | Path |
|------|------|
| Orchestration + rules | `services/fiqa_api/inbox_triage/triage.py` |
| Config load order | `services/fiqa_api/inbox_triage/config_loader.py` |
| HTTP surface | `services/fiqa_api/routes/inbox_triage.py` |
| Persistence | `services/fiqa_api/inbox_triage/case_store.py` |
| Industry JSON | `configs/industries/insurance/` |
| Client JSON | `configs/clients/<client_id>/` |
| Common defaults | `configs/common/` |
| Guardrail | `scripts/guardrail_inbox_triage.sh` |
