# Portable Client / Industry Pack Concept Spec

**Question answered:** If a new customer arrives, what swaps quickly vs. what still needs engineering?

---

## 1. Same industry (auto insurance), different broker office

### Could swap quickly (target: hours, not weeks)

| Asset | Action |
|-------|--------|
| `configs/clients/<new_id>/handoff_phrases.json` | Write new ZH/EN phrases. |
| `configs/clients/<new_id>/ui_copy.json` | All UI strings + quick-start buttons. |
| `configs/clients/<new_id>/reply_overrides.json` | Shallow merge over industry templates (**today:** code must be fixed to not hardcode `chen_kui`). |
| Environment | `CLIENT_ID=new_id`. |

### Would still need review (days)

| Work | Why |
|------|-----|
| **Scenario pass** | Language and tone shifts can break implicit expectations; rerun guardrail + add-car batteries. |
| **Legal/compliance copy** | SLA wording in UI (timing) may need attorney/broker review — keep in client pack. |
| **Route copy** | Until externalized, reroute/starter strings may still say “wrong office.” |

### What the architecture already makes easy

- **Client pack** files exist and are loaded for handoff + UI.
- **Industry pack** stays stable — second broker shares insurance markers and templates.

---

## 2. Different industry (e.g. retail, food, services)

### Hard (weeks+)

| Area | Reason |
|------|--------|
| **`triage.py` intent and extraction** | Heavily insurance-shaped (VIN, DMV, SR-22, add-car, claim). |
| **Scenario batteries** | All packs assume broker inbox semantics. |
| **UI flows** | Unified Intake UX is tuned to insurance quick starts. |

### Reusable without rewrite

| Area | Reason |
|------|--------|
| **Case store pattern** | Generic “case + messages + attachments” — domain-agnostic shell. |
| **Config loader pattern** | industry → client merge order. |
| **Guardrail idea** | “Scenario runner + API smoke” transfers to any vertical. |

**Verdict:** Cross-industry is a **new product fork** of the engine, not a config swap. The **pack concept** still helps: you would create `configs/industries/<new_vertical>/` and strip/replace `triage.py` logic iteratively.

---

## 3. Hot-plug structure table

| Component | Same-industry new broker | New industry |
|-----------|--------------------------|--------------|
| `markers.json` | Reuse or lightly extend | Replace |
| `category_templates.json` | Reuse | Replace |
| `reply_templates.json` | Reuse | Replace |
| `add_car_rules.json` | Reuse | N/A or replace with new flow file |
| `handoff_phrases.json` | **Replace** | Replace |
| `ui_copy.json` | **Replace** | Replace |
| `triage.py` | Rare edits | Major rewrite |
| `case_store.py` | Reuse | Mostly reuse |
| Scenario packs | Extend | Rebuild |

---

## 4. What makes future customer migration easier

1. **No hardcoded client paths** in loaders (`reply_overrides`).
2. **Single home** for customer-visible strings (no duplicate route + UI + triage).
3. **Documented** scenario list so CS can say “we tested X, Y, Z.”
4. **`CLIENT_ID`** in all environments (local, Cloud Run) — already the pattern for UI; finish for templates.

---

## 5. What makes customer review / reporting easier

- **Client pack JSON** can be exported as a “wording appendix” for broker approval.
- **Industry pack** can be “product defaults” in sales materials.
- **Regression battery logs** become the **evidence** slide for “what we guarantee.”

---

## 6. Absolutely do not over-engineer yet

- Multi-tenant runtime switching without a paying second customer.
- Pluggable Python modules per intent **before** a second industry is funded.
- JSON-driven state machines for append boundaries.
