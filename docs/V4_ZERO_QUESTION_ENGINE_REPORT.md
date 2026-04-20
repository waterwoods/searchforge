# V4 Zero-Question Intake Engine — Report

This document consolidates **Phase 1–11** deliverables: gap analysis, engine design, shipped code touchpoints, simulation outputs, and success criteria.

---

## V4_GAP_ANALYSIS (Phase 1)

### Why the system still needs multi-turn (pre–V4 / variant A)

1. **Pilot truth bar**: Add-car `quote_ready` requires **VIN + ZIP + primary driver + delivery/effective date** (`_add_car_quote_ready_status` in `triage.py`). Slots are **truth-gated**; the engine does not invent VIN or contact.
2. **Sequential collection**: `_get_next_ask_for_add_car` walks **vehicle → VIN/year/model → ZIP → driver → dates** when gaps exist — a **question ladder**, not a single confirmation.
3. **Conversion Flow V3**: After quote-ready, **name/phone** completion uses a **multi-line “steps” ladder** in `conversion_layer.py` (even if presented as one bubble).
4. **Intake engine**: `intake_engine.py` computes **slot-by-slot** `intake_next_best_ask`, and triage may **override** `client_reply_draft` when 1–2 slots remain (variant A).
5. **Handoff gating**: `handoff_ready` for add-car is **blocked** unless truth fields satisfy quote-ready (`_add_car_is_quote_ready`), so **incomplete threads** keep cycling.

### Fields that block a true “zero-question” flow

| Blocker | Reason |
|--------|--------|
| **VIN** | Required for `quote_ready`; no safe auto-fabrication |
| **ZIP** | Garaging / rating; extraction required or broker verify |
| **primary_driver** | Rating + UW relevance |
| **delivery_date / effective** | Calendar truth for quote/bind |
| **name / phone** | Conversion V3 contact completion (channel logistics) |

### Safe to infer vs must confirm

| Class | Examples | Policy |
|--------|-----------|--------|
| **Infer + often auto** | Year/make from text, thread vehicle summary | Still **confirm** under variant C for vehicle; B/C use **one confirmation block** |
| **Infer + always confirm (MEDIUM)** | Usage keywords (commute/rideshare), ZIP→broad area label | Shown in V4 confirmation |
| **Infer + LOW / defer** | Industry default usage when no keyword | Labeled `industry_default`; broker may override |
| **Never auto-fill as truth** | VIN, legal name, phone | Extraction or user-provided only |

### Current avg-turn bottleneck (observed pattern)

- **Structured path**: Multiple **customer turns** until all pilot slots + contact are present; **median** in Monte Carlo **often lands in ~7–10 turns** before quote-ready + conversion (see `VARIANT_COMPARISON_TABLE` / `run_conversion_v3_monte_carlo` in `scripts/run_analytics_north_star_simulation.py`).
- **Dominant friction**: **Slot collection order** + **post–quote-ready contact** + **persona** (messy / silent / distrust).

---

## V4 engine shape (Phases 2–3)

Shipped in `case_draft_engine.py`:

- **`build_v4_case_draft_bundle`**: Produces  
  `known_fields`, `inferred_fields`, `missing_fields`, `confidence_map`, **`confirm_priority_fields`**, **`v4_completeness_score`**, **`v4_partial_handoff_eligible`**, **`v4_flow`**, **`confidence_tier_policy`**.
- **`auto_fill_defaults`**: Safe heuristics only (ZIP prefix → area hint, usage keywords / industry default).
- **Tiers**: HIGH / MEDIUM / LOW via `confidence_tier_policy` and per-field `tier` where applicable.
- **`estimate_v4_error_risk_score`**: Heuristic **0–1** wrong-inference risk for analytics.

---

## Confirmation-first UX (Phases 4–5) — variants B / C

Shipped in `triage.py`:

- **Turn 1**: For **`intake_evolution_variant` in `B` | `C`**, **no instant handoff** even if quote-ready; **one confirmation block** via `build_v4_confirmation_client_reply_from_bundle`.
- **Collecting turns**: **No** slot-by-slot override from `intake_next_best_ask` focus path for B/C (single confirmation style preserved).
- **Partial handoff (Phase 6)**: From **customer turn ≥ 2**, if **`v4_completeness_score ≥ 0.70`** and pilot quote-ready is **not** met, **`v4_partial_ok`** allows **`handoff_ready`** so the office can broker-complete.

Configure via client **`ui_copy.intake_evolution_variant`** (`config_loader.get_intake_evolution_variant`).

---

## Variants (Phase 7)

| Variant | Behavior |
|---------|-----------|
| **A** | **V3 baseline**: question ladder + existing conversion V3; legacy `build_add_car_case_draft` |
| **B** | **Aggressive**: shorter / confirmation block + V4 bundle; higher modeled inference risk |
| **C** | **Confirm-heavy**: confirmation block + extra trust copy; more fields prioritized for confirm |

---

## Simulation upgrade (Phases 8–10)

In `scripts/run_analytics_north_star_simulation.py`:

- **`run_v4_intake_monte_carlo`**: 100–500 sessions; personas **messy_user, hesitant_user, silent_user, distrust_user**; metrics: **median turns**, **confirmation success**, **correction rate**, **completeness**, **error risk**.
- **`run_v4_variant_comparison_table`**: prints **`V4_VARIANT_COMPARISON_TABLE`** (joins V4 metrics with **quote_ready→handoff** from existing V3 MC).
- **`run_auto_evolution_loop_v4`**: max **2** cycles; promotes challenger only if **conversion improves** and **mean_error_risk_score ≤ cap** (default **0.42**). Prints **`V4_AUTO_EVOLUTION_LOOP`**.

Run:

```bash
PYTHONPATH=. python3 scripts/run_analytics_north_star_simulation.py --mc-sessions 400 --mc-seed 42
```

---

## V4_VARIANT_COMPARISON_TABLE (Phase 9 — illustrative run)

Values **vary by seed**. Example shape (see script stdout for **`V4_VARIANT_COMPARISON_TABLE`**):

| Metric | A (baseline) | B (aggressive) | C (safe) |
|--------|----------------|----------------|----------|
| Median turns (V4 model) | ~8–10 | ~6–8 | ~7–9 |
| Mean confirmation success | lower | higher | highest |
| Mean correction rate | higher | lower | mid |
| Mean error risk | lowest | highest | mid |
| quote_ready→handoff (V3 MC arm) | baseline | often + | often ++ |

---

## V4_FINAL_SYSTEM_REPORT (Phase 11)

### 1. Turn reduction

- **Product**: B/C replace **multi-step slot asks** on the **first turn** with **one confirmation block**; partial handoff reduces **stall** when **≥70%** weighted completeness.
- **Modeled**: **`run_v4_intake_monte_carlo`** shows **lower median_turns_total** for **B** vs **A** in typical seeds (verify on your run).

### 2. Conversion improvement

- **Post–quote_ready** conversion remains governed by **`conversion_layer`** and **`run_conversion_v3_monte_carlo`**.
- **V4 table** adds **`quote_ready_to_handoff_rate`** per arm for a **combined** view.

### 3. Effort reduction

- **User effort score** proxy: total turns in V4 MC + existing **`user_effort_score`** in conversion MC.

### 4. Error risk tradeoff

- **B** increases **`mean_error_risk_score`** vs **A** in the model; **C** trades some efficiency for **lower risk** than **B**.
- **`run_auto_evolution_loop_v4`** enforces an **error-risk cap** before promoting **B**.

### 5. “Zero-Question Goal” achieved?

- **Strict zero questions** is **not** guaranteed while **VIN/contact** must be real — the shipped design is **zero *ladder*** + **one confirmation surface** + **partial broker-complete**.
- **Median turns ≤ 5**: **Not asserted globally**; tune **B** + production telemetry. Monte Carlo often still **>5** until real traffic proves otherwise.

### Success criteria checklist

| Criterion | Status |
|-----------|--------|
| Median turns ≤ 5 | **Track** (V4 MC + prod); not hard-coded |
| ≥70% cases “auto-generated” (completeness) | **`auto_generated_case_rate_ge_70pct_completeness`** in V4 MC |
| Conversion vs V3 | **Compare** `quote_ready_to_handoff_rate` arms |
| User input reduced | **B** confirmation vs **A** ladder (qualitative + turns) |

---

## Code map

| Area | File |
|------|------|
| V4 draft + auto-fill + confirmation text | `services/fiqa_api/inbox_triage/case_draft_engine.py` |
| B/C routing, partial handoff, skip focused ask | `services/fiqa_api/inbox_triage/triage.py` |
| Conversion V3 (unchanged contract) | `services/fiqa_api/inbox_triage/conversion_layer.py` |
| API | `services/fiqa_api/routes/inbox_triage.py` (no route change required) |
| UI types | `ui/src/api/inboxTriage.ts` (`zero_question_intake`, `v4_error_risk_score`) |
| Simulation | `scripts/run_analytics_north_star_simulation.py` |

---

## Operational note

Set **`intake_evolution_variant`** to **`B`** or **`C`** in the active client pack’s **`ui_copy`** to enable V4 behavior for that tenant. **`A`** remains the **V3** control arm.
