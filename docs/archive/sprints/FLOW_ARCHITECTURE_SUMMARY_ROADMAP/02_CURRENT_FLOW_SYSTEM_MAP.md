# Current Flow System Map — Unified Intake

Founder-readable map of **where behavior lives** and **how layers connect**.

---

## 1. Layered map

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser — Unified Intake UI (customer + broker workbench tabs)   │
│  • conversation_turns, soft_route, persist flags                  │
│  • transaction ribbon / progress / post-handoff panels          │
│  • copy from GET /api/inbox/client-config + local TS fallbacks   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTPS JSON
┌───────────────────────────────▼─────────────────────────────────┐
│  FastAPI — routes/inbox_triage.py                                │
│  • Validates body; merges/normalizes text                        │
│  • soft_route vs text conflict → reroute_message (hardcoded)     │
│  • Calls triage_conversation / triage_for_append                 │
│  • Optional case save, attachments, rules preview/publish        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│  Flow brain — inbox_triage/triage.py                             │
│  • _build_conversation_text_for_triage → [客户]/[系统] thread     │
│  • LLM vs _rule_based_triage (fast path when LLM on)             │
│  • handoff_ready vs _get_next_ask_draft (multi-turn collection)  │
│  • Handoff reply selection + many post-classification patches    │
│  • Structured fields per flow (add-car, missing doc, cancel, …)  │
│  • Append: triage_for_append + case_boundary classification      │
└───────────────────────────────┬─────────────────────────────────┘
          reads                 │                 reads
┌─────────▼──────────┐  ┌───────▼────────┐  ┌─────▼──────────────────┐
│ config_loader.py   │  │ notice_retrieval│  │ (hardcoded fallbacks   │
│ industry + client  │  │ (RAG augment)   │  │  in triage.py)         │
└────────────────────┘  └─────────────────┘  └────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│  Persistence — case_store.py (JSON file + attachments dir)       │
│  • case_messages, workflow-ish fields, status, customer contact    │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  Regression layer — scripts/*.py + guardrail_inbox_triage.sh      │
│  • Locks behavior without starting the full product redesign       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Responsibility table (“what each layer owns”)

| Layer | Owns | Does *not* own |
|-------|------|----------------|
| **triage.py** | Turn merge, classification path, add-car slot extraction & gating, handoff vs next question, follow_up_type, lifecycle/collection hints, append boundary rules, broker_next_step tailoring for several flows | Persistent case schema evolution beyond what routes/store already support; long-term CMS for all strings |
| **config_loader.py** | Load order, path resolution, ui_copy key allowlist, add_car_rules save/publish guard | Business logic branches |
| **routes/inbox_triage.py** | HTTP contract, soft-route starter/re-route strings, case CRUD orchestration | Core triage semantics |
| **case_store.py** | Durable case record, validation limits, message parsing helpers | Reply generation |
| **UI** | Presentation, when to show progress vs closure, inferring “looks like add-car” for chrome, toasts | Server-side truth for category/slots |
| **Configs (JSON)** | Markers, templates, handoff lines, add-car ask strings, portal copy | Execution order of asks (still mostly code) |

---

## 3. Data contract (mental model)

The **canonical runtime object** is the triage result dict (typed in UI as `TriageResult`): category, drafts, `handoff_ready`, `collected_fields` / `still_needed_fields`, add-car `quote_ready_status`, `follow_up_type`, `lifecycle_status`, `next_best_question`, optional `case_boundary`, etc.

The UI treats this blob as **source of truth** for “what stage are we in,” then adds **presentation** (ribbons, tags, post-handoff panels).

---

## 4. Connection summary

1. **UI → API:** sends `conversation_turns`, optional `soft_route`, `client_id`, `persist_case`.
2. **API → triage:** `triage_conversation` returns enriched result.
3. **API → store:** optional `save_case` / append endpoints update JSON.
4. **Configs → triage:** markers, templates, handoff phrases, `add_car_rules` influence text and detection; large `if handoff and is_add_car` blocks still live in code.
5. **Scripts → repo:** guardrail fails CI/local checks if scenarios drift.

This map is the answer to “how do pieces connect without reading 3k lines first.”
