# Product / System Blueprint — Minimal Production Backbone

**Sprint:** Minimal Production Backbone Master Sprint  
**Created:** 2026-03-17  
**Scope:** Chen Kui Insurance Unified Entry — backend foundation

---

## 1. Why Minimal Production Backbone Matters Now

The product has evolved from an AI demo into:

- A **customer entry system** (paste → triage → collect → hand off)
- A **stateful intake system** (multi-turn, workflow_state, lifecycle)
- A **case creation and handoff system** (broker workbench)
- A **broker workbench system** (queue, reopen, follow-up, append message)

The biggest next challenge: **make the backend backbone more formal, more durable, and more coherent.**

Without this, scaling to many merchants will be fragile:

- Messages and state may diverge
- Case progression may become inconsistent
- Storage may stay too prototype-like
- Frontend/backend/workbench contracts may drift
- Demo/prod boundaries may stay weak

---

## 2. Current Limitations

| Area | Limitation |
|------|------------|
| **Message + state + case** | Relationship is implicit; session_id and case_id are not formally linked when case created |
| **Persistence** | JSON files with atomic write; no schema validation; no transactional guarantees |
| **workflow_state** | Extracted from triage; lifecycle_status in case derived from case_status, may not match triage |
| **Frontend/backend** | Contract exists but not formally documented; lifecycle_status values may drift |
| **Demo/prod** | Same storage; env vars for paths; no explicit demo-only behavior flag |
| **Source of truth** | case_messages vs source_text; some fields derived, some stored; no single contract |

---

## 3. What This Sprint Will Strengthen

1. **Message + state + case relationship** — clearer and more formal
2. **Persistence strategy** — more coherent, less prototype-like
3. **Frontend/backend/workbench contract** — tighter
4. **Demo/prod boundary** — clearer
5. **Backbone reusability** — more merchant scenarios
6. **Paid pilot foundation** — closer to production-ready

---

## 4. What This Sprint Intentionally Will NOT Do

- Full enterprise architecture
- Migration to SQLite or other DB (unless clearly justified)
- Multi-tenant or auth
- Stripe or billing
- New product features or scenario expansion
- Giant rewrite

---

*See also: `02_MINIMAL_PRODUCTION_BACKBONE_ARCHITECTURE_SPEC.md`, `03_PERSISTENCE_STORAGE_STRATEGY_SPEC.md`*
