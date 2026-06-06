# File / Folder Responsibility Map

For each category: **why it matters**, **safe to change?**, **typical change types**.

---

## 1. Common engine (core product code)

| Path | Why it matters | Safe? | Typical changes |
|------|----------------|-------|-----------------|
| `services/fiqa_api/inbox_triage/triage.py` | All triage behavior, workflow, add-car, append | **Risky** | Bug fixes, new flows (high review) |
| `services/fiqa_api/inbox_triage/config_loader.py` | Merge order, CLIENT_ID, JSON paths | **Risky** | New config keys, allowlist for UI |
| `services/fiqa_api/routes/inbox_triage.py` | API contract, persistence wiring | **Risky** | New endpoints, request fields |
| `services/fiqa_api/inbox_triage/case_store.py` | Case JSON schema, validation | **Risky** | New case fields (coordinate UI) |
| `services/fiqa_api/inbox_triage/session_store.py` | In-progress session continuity | **Medium** | Session field additions |
| `services/fiqa_api/inbox_triage/notice_retrieval.py` (if present) | RAG/retrieval augment for notices | **Medium** | Retrieval tuning |
| `services/fiqa_api/app_main.py` | Router mount | **Low touch** | Rare |

**Change posture:** Engine changes affect **every** client and all tests. Prefer **config** for wording.

---

## 2. Industry pack (same vertical, shared)

**Path:** `configs/industries/insurance/`

| File | Why it matters | Safe? | Typical changes |
|------|----------------|-------|-----------------|
| `markers.json` | Intent detection lexicon | **Medium** | Add phrases; watch false positives |
| `reply_templates.json` | Default replies | **Safer** | Industry-wide tone |
| `category_templates.json` | Per-category broker/client guidance | **Safer** | Template text |
| `add_car_rules.json` | Add-car next prompts | **Safer** | Wording, order handled in engine |
| `README.md` | Doc | **Safe** | Documentation |

**Change posture:** Shared across brokers — good for **California auto** defaults; use **client overrides** when tone diverges.

---

## 3. Client pack (per broker)

**Path:** `configs/clients/<client_id>/`

| File | Why it matters | Safe? | Typical changes |
|------|----------------|-------|-----------------|
| `ui_copy.json` | Branding, buttons, handoff UI text | **Safest** | Copy, quick-start labels |
| `handoff_phrases.json` | Customer-visible handoff + stitched | **Safest** | Phrases, boundaries |
| `reply_overrides.json` | Overrides industry templates | **Safe** | Per-template zh/en |
| `README.md` | Operator notes | **Safe** | Notes |

**Change posture:** **First stop** for new broker onboarding.

---

## 4. Common config (cross-client defaults)

**Path:** `configs/common/`

| File | Why it matters | Safe? | Typical changes |
|------|----------------|-------|-----------------|
| `soft_route_inbox.json` | Soft-route reroute + starter replies | **Safe / Medium** | Affects all clients if not overridden per client later |
| `workflow_defaults.json` | Fallback broker/client/draft lines | **Safe / Medium** | Shared fallbacks |

**Change posture:** Treat as **global** — if one broker needs different soft-route behavior long-term, consider per-client extension (today: mostly common + engine defaults).

---

## 5. Rule / lexicon layer (scenario + markers)

| Path | Why it matters | Safe? | Typical changes |
|------|----------------|-------|-----------------|
| `configs/inbox_triage_scenarios.json` | Core regression scenarios | **Medium** | Add scenarios when new behavior |
| `docs/sprints/**/scenario_battery.json` | Sprint-specific batteries | **Safe** | Documented experiments |
| Industry `markers.json` | Lexicon | **Medium** | Synonyms, new intents |

---

## 6. UI semantics

| Path | Why it matters | Safe? | Typical changes |
|------|----------------|-------|-----------------|
| `ui/src/pages/UnifiedIntakePage.tsx` | Layout, flows, demo seeds | **Medium** | UX; avoid hardcoding broker names |
| `ui/src/api/clientConfig.ts` | Types + **DEFAULT_UI_COPY** | **Medium** | New keys; defaults skew “Chen” if not careful |
| `ui/src/api/inboxTriage.ts` (if used) | API client | **Medium** | Field parity with backend |

---

## 7. Regression / validation scripts

**Path:** `scripts/` (subset)

| Script | Role |
|--------|------|
| `guardrail_inbox_triage.sh` | Umbrella gate |
| `run_inbox_triage_scenarios.py` | Main JSON scenario pack |
| `run_multi_turn_simulations.py`, `run_adversarial_simulation.py`, `run_complex_adversarial_simulation.py` | Stress / realism |
| `run_case_boundary_battery.py` | Append / new-issue boundaries |
| `test_client_aware_handoff.py`, `test_client_identity_append.py` | Client stickiness |
| `run_cross_client_ab_scenarios.py`, `run_append_boundary_ab_scenarios.py`, `run_residual_copy_ab_scenarios.py` | **A/B isolation** |
| `run_add_car_*` family | Add-car specific |
| `test_inbox_triage_api.py` | Live API smoke |

**Change posture:** Adding scenarios is **safe** and encouraged; **skipping** guardrail steps is **not**.

---

## 8. Infra / deploy (when relevant)

| Path | Notes |
|------|------|
| `docker-compose*.yml`, Cloud Run configs | Set `CLIENT_ID` in environment for target broker |
| `scripts/run_demo_local.sh` | Local demo; confirm which `CLIENT_ID` |

---

## 9. Taxonomy: what belongs where?

| Concern | Engine | Industry | Client | Common |
|---------|--------|----------|--------|--------|
| “Is this cancellation?” | logic + markers | markers.json | — | — |
| “What do we ask next for add-car?” | triage flow | add_car_rules.json | overrides rare | — |
| “Office handoff wording” | when to handoff | templates | handoff_phrases.json | — |
| “Button labels on UI” | — | — | ui_copy.json | — |
| “Soft route starter text” | route uses copy | — | — | soft_route_inbox.json |

---

*See [SAFE_VS_RISKY_CHANGES.md](./SAFE_VS_RISKY_CHANGES.md) for a shorter matrix.*
