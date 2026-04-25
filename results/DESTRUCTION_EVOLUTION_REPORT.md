# Add-Car Destruction Evolution — Final Report

## 1. Time spent

| Item | Value |
|------|--------|
| **Total (approx.)** | ~95 minutes |
| **Evolution loops completed** | 3 (wave-1 fix + loop2 library + loop3 library) |

## 2. Scenario stats

| Metric | Value |
|--------|--------|
| **Total scenarios (wave 1)** | 150 |
| **Baseline pass rate (wave 1, first run)** | 134 / 150 (**89.3%**) — 16 failures |
| **Final pass rate (wave 1, after triage + library fix)** | 150 / 150 (**100%**) |
| **Loop 2 scenarios** | 36 (all pass) |
| **Loop 3 scenarios** | 20 (all pass) |
| **Combined stress files** | `add_car_destruction_scenarios.py`, `add_car_destruction_loop2_scenarios.py`, `add_car_destruction_loop3_scenarios.py` |

## 3. Top 5 failure types (from initial wave-1 baseline)

1. **summary_or_substring_mismatch** — `primary_vehicle_summary` missing make (year-only), wrong make (Tesla vs Camry, CR-V vs Camry), or missing `WRX` token.
2. **Identity collapse** — last-wins model extraction latched onto Tesla/CR-V after user had reverted to “first car / earlier” language.
3. **ZH pad thread** — Chinese template used `定的是{年}。` without embedding model name; Model Y/3 pads degraded to a bare `Y` token in Chinese.
4. **Multi-entity** — CR-V mentioned in late bubbles overrode Camry when both appeared in-thread.
5. **Cross-thread “correction signal” noise** — (secondary) year-only extraction when model lived only in early bubbles under ZH formatting.

## 4. What broke the system hardest

- **Primary vehicle line (`primary_vehicle_summary`)** is the single highest-leverage brittle surface: it is derived from stacked heuristics over many bubbles. Under contradiction, “last non-empty model win” fights product truth when the user explicitly re-anchors to the **first** mention or **drops** a sibling vehicle (CR-V) for the bind.
- **Padding with Chinese templates** that omitted make strings produced year-only summaries and false “failures” that were library bugs, not triage bugs.

## 5. What fixes worked

| Fix | Where | Effect |
|-----|--------|--------|
| **First-mention re-anchor** | `triage.py` — `_add_car_revert_to_first_mentioned_scope` + early return in `_extract_primary_add_car_vehicle_concrete` | Restores Camry / first-line truth when user says “first line / car I said earlier / 第一台…”. |
| **Sibling drop (Camry vs CR-V)** | `triage.py` — `_add_car_prefer_model_when_sibling_ignored` | Prefer Camry when thread explicitly ignores/drops CR-V or “not the CR-V”. |
| **WRX token** | `triage.py` — `_extract_make_model_from_lower` | `Subaru WRX` appears in summary for WRX threads. |
| **ZH pad model text** | `add_car_destruction_scenarios.py` — `_make_thread` | Embeds model in `定的是…` and handles **Model Y / Model 3** in Chinese lines. |

All changes stayed in **triage.py** (plus the scenario library file for data quality). No DB / UI / Postgres changes.

## 6. What is still broken (honest)

- **Full `pytest -q`** does not pass green in this repo state: `tests/test_append_truth_alignment.py` imports a missing symbol (`_resolve_add_car_handoff_phrase_key`); `test_first_quote_ready_moment_compact_no_all_complete_wording` and `test_already_sent_add_car_reply_acknowledges_materials_and_can_ask_zip` fail on draft copy expectations (documented elsewhere; not introduced by this destruction pass).
- **HTTP live test** on `:8001` was not executed (no server listening); parity was validated via `triage_conversation` scenario runners (LLM off) and **guardrail** script.
- **Long-horizon semantic memory** beyond rule extraction (true “summary of summary” drift across sessions) is **not** solved—only in-thread, regex-bounded vehicle resolution improved.

## 7. Product judgment

**Choice: INTERNAL_DEMO_READY**

Rule-based + deterministic replay now holds on **150** adversarial 8–15 turn scenarios plus **56** follow-on loop scenarios, but full pytest green and live HTTP validation are not confirmed in this run. For a paying customer pilot, add CI-green tests and a short live burn-in on `/api/inbox/triage` with the API server up.

## 8. Meta — what fundamentally weakens this system?

**The weakness is not “wrong regex once”—it is that office-facing truth is compressed from a linear chat into a few scalar fields with shallow, last-message bias.** Humans resolve pronouns, sibling vehicles, and “revert to first” using global intent; the engine mostly stacks bubbles and prunes with keywords. Under adversarial or emotional threads, **any single field (`primary_vehicle_summary`, `service_type`, `follow_up_type`) that is heuristically fused will eventually disagree with a motivated user** unless you add heavier structured state (explicit slot ledger with turn indices) or an LLM with strict JSON schema and verification—both outside the “≤20 line triage fix” scope here.

## 9. Artifacts

| Artifact | Path |
|----------|------|
| Baseline (first run, 16 fails) | Overwritten; metrics captured in this report (134/150) |
| After fix (wave 1) | `results/DESTRUCTION_AFTER_FIX_1.json` (150/150) |
| Loop 2 | `results/DESTRUCTION_LOOP2.json` |
| Loop 3 | `results/DESTRUCTION_LOOP3.json` |
| Git branch | `auto-evolution/add-car-destruction-` |

## 10. Commands run

```bash
PYTHONPATH=. LLM_GENERATION_ENABLED=0 python3 scripts/run_add_car_cplus_scenario_library.py \
  --library-path tests/scenario_libraries/add_car_destruction_scenarios.py \
  --output results/DESTRUCTION_AFTER_FIX_1.json

bash scripts/guardrail_inbox_triage.sh
```

(Loop 2/3: same script with `add_car_destruction_loop2_scenarios.py` / `add_car_destruction_loop3_scenarios.py`.)
