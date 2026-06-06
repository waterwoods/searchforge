# Client-Pack Operating Manual — Blueprint

**Purpose:** Single-page **blueprint** for how “Unified Intake” is packaged: what a **client pack** is, how it plugs in, and what operations repeat for every broker.

---

## 1. Product shape (today)

Unified Intake is a **single-tenant-style** deployment: one running instance uses one **active client** via `CLIENT_ID` (default `chen_kui`). All broker-specific surface area is meant to live under **`configs/clients/<client_id>/`** plus optional shared tuning under **`configs/industries/insurance/`** and **`configs/common/`**.

---

## 2. Client pack definition

A **client pack** is the smallest set of files that makes the **same engine** sound and look like **that broker’s office**:

| File | Responsibility |
|------|------------------|
| `ui_copy.json` | App title, office labels, welcome copy, quick-start button labels/messages, add-car / handoff UI strings |
| `handoff_phrases.json` | `handoff` phrases (e.g. add_car / other, zh/en); optional `stitched` block (append boundaries, caveats, tails) |
| `reply_overrides.json` | Shallow merge overrides on top of industry `reply_templates.json` |
| `README.md` | Human note: who this pack is for (optional but recommended) |

**Not in client pack (usually):** Python triage logic, FastAPI routes, React structure.

---

## 3. Load order (authoritative mental model)

Implemented in `config_loader.py`:

1. **Industry** base: markers, category templates, reply templates, add-car rules.
2. **Client** overlays: handoff + stitched phrases; reply overrides merged per template key; `ui_copy` loaded per request/client.
3. **Common** overlays: `soft_route_inbox.json`, `workflow_defaults.json` — shared across clients unless you fork behavior in code.

**No cross-client fallback** for several client-only structures (by design — avoids Broker A’s wording leaking to Broker B).

---

## 4. Operating loops (repeatable)

| Loop | When | Actions |
|------|------|---------|
| **Copy refresh** | Marketing / compliance / tone | Edit JSON in client pack → run guardrail → spot-check UI |
| **New intent tuning (industry)** | New notice types / phrases | Edit `markers.json` or templates → run scenario + adversarial packs |
| **New broker (same industry)** | Second CA auto broker | New `configs/clients/<id>/` → set `CLIENT_ID` → cross-client A/B → guardrail |
| **Release gate** | Any merge to triage path | `guardrail_inbox_triage.sh` green |

---

## 5. Success criteria (operating manual view)

A client pack is **operable** when:

1. `CLIENT_ID=<id>` serves correct `GET /api/inbox/client-config`.
2. Triage outputs use **that broker’s** handoff / stitched strings (not another client).
3. `run_cross_client_ab_scenarios.py` (and related append/residual A/B runners) pass.
4. `guardrail_inbox_triage.sh` passes.

---

## 6. Boundaries (what this manual is not)

- Not a substitute for **API contract** docs (see route source for request/response fields).
- Not **multi-tenant auth** or per-user client selection in production (out of current scope).
- Not **carrier API** or **OCR** roadmap.

---

*Companion: [SAME_INDUSTRY_MIGRATION_CHECKLIST.md](./SAME_INDUSTRY_MIGRATION_CHECKLIST.md), [VALIDATION_REGRESSION_CHECKLIST.md](./VALIDATION_REGRESSION_CHECKLIST.md).*
