# Optional: Simple Flow Diagram + “What Lives Where” Table

---

## ASCII flow (request path)

```
Customer / Broker UI
        |
        v
POST /api/inbox/triage  (routes/inbox_triage.py)
        |
        +-- soft_route / client_id normalization
        |
        v
triage_conversation()  (triage.py)
        |
        +-- merge turns -> [客户]/[系统] text
        +-- talk-to-agent fast exit
        +-- rule OR LLM base classification
        +-- handoff vs next_ask (add-car: _get_next_ask_for_add_car)
        +-- handoff phrase selection (handoff_phrases.json + fallbacks)
        +-- patches (doc Q, coverage Q, materials sent, correction, ...)
        +-- structured fields (collected / still_needed / quote_ready_status)
        |
        v
JSON TriageResult  -->  UI + optional case_store save
```

---

## Table: what lives where

| Asset / behavior | Code | Config | UI | Tests |
|------------------|------|--------|-----|-------|
| Issue category + urgency | Yes | markers help | Display | Scenarios |
| Broker next step / client prep | Yes | category_templates | Display | Scenarios |
| Add-car slot detection | Yes | — | — | Add-car batteries |
| Add-car ask **text** | Fallback | add_car_rules.json | — | Scenarios |
| Handoff customer reply | Fallback | handoff_phrases.json | — | Client handoff test |
| Transaction ribbon / closure copy | — | ui_copy.json | Renders + defaults | — |
| Soft-route starter / reroute | Yes | — | Button labels | — |
| Append same vs new issue | Yes | — | Surfaces case_boundary | run_case_boundary_battery |
| Case JSON schema | case_store.py | — | — | verify_inbox_case_persistence |
