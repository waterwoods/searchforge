# Same-Industry Migration Checklist (Second Broker)

**Scope:** Another **California auto insurance** broker — same engine, new **client pack**, same validation discipline.

---

## Prerequisites

- [ ] Agree **`client_id`** (lowercase, folder-safe, e.g. `socal_precision`).
- [ ] Copy an existing pack as template: `configs/clients/chen_kui/` → `configs/clients/<new_id>/`.

---

## Step-by-step

1. **Choose / create client id**  
   - [ ] Folder exists: `configs/clients/<client_id>/`

2. **Copy / create client pack**  
   - [ ] `handoff_phrases.json` — replace office name, tone, stitched block if used  
   - [ ] `reply_overrides.json` — start empty `{}` or minimal overrides  
   - [ ] `ui_copy.json` — titles, welcome, quick-start buttons, handoff card strings  
   - [ ] `README.md` — who this is for

3. **Define UI copy**  
   - [ ] All required user-visible strings present (no accidental empty → wrong defaults)  
   - [ ] Quick-start `starterMessage` aligns with soft-route intents

4. **Define handoff phrases**  
   - [ ] `handoff.add_car` / `handoff.other` (zh/en as needed)  
   - [ ] Optional `stitched` keys if broker needs distinct boundary/caveat wording

5. **Define reply overrides**  
   - [ ] Only keys that must differ from industry; avoid duplicating entire file

6. **Client-specific markers (usually skip)**  
   - [ ] Prefer industry `markers.json`; only add client-specific logic in engine if truly unavoidable (avoid in normal migration)

7. **Verify A/B isolation**  
   - [ ] `CLIENT_ID=<new> LLM_GENERATION_ENABLED=0 PYTHONPATH=. python3 scripts/run_cross_client_ab_scenarios.py`  
   - [ ] `run_append_boundary_ab_scenarios.py`  
   - [ ] `run_residual_copy_ab_scenarios.py`

8. **Run guardrail / scenario batteries**  
   - [ ] `bash scripts/guardrail_inbox_triage.sh`

9. **Optional browser inspection**  
   - [ ] Start demo stack; open Unified Intake; confirm titles/buttons/handoff  
   - [ ] Toggle `CLIENT_ID` (or deploy env) and repeat smoke

10. **Define “migration successful”**  
   - [ ] Guardrail **PASS**  
   - [ ] Cross-client A/B scripts **PASS**  
   - [ ] `GET /api/inbox/client-config?client=<id>` returns expected `ui_copy`  
   - [ ] Spot triage: same input under two `CLIENT_ID`s shows **different** broker-specific strings where intended  
   - [ ] No unintended fallback to `chen_kui` phrasing (watch missing JSON keys)

---

## What to change first (order of operations)

1. `ui_copy.json` + `handoff_phrases.json` (founder-visible)  
2. `reply_overrides.json` (draft tone)  
3. Industry files **only** if the new broker needs **shared** lexicon updates  
4. Engine code **last** and only if config cannot express the requirement

---

## Anti-patterns

- Editing `triage.py` first for “wording” — use config.  
- Relying on cross-client fallback — isolation tests exist to prevent this.  
- Skipping `LLM_GENERATION_ENABLED=0` for regression — keeps runs deterministic.

---

*Validation detail: [VALIDATION_REGRESSION_CHECKLIST.md](./VALIDATION_REGRESSION_CHECKLIST.md)*
