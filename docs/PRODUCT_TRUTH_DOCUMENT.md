# Product Truth Document (PTD)

**Single source of truth** for the California auto insurance **Unified Intake** product: minimal user input → auto-generated usable case → one confirmation → immediate broker handoff → broker completes remaining fields.

**Status:** Living document. Last aligned with repo implementation: 2026-04-20 (Field Strategy behavior + Default Engine + Broker Completion + Learning V1).

---

## 1. Vision

### Zero-effort case completion system

End users (insured customers via broker-facing channels) should feel:

> *"I barely did anything, and it's already done."*

The system **prefers shipping a good-enough structured case** over perfect data collection. The broker office is the **completion layer** for precision, compliance, and binding.

---

## 2. Core Principles

| Principle | Meaning |
|-----------|---------|
| **Do not ask if you can infer** | Use rules, OCR, thread context, and safe defaults before prompting. |
| **Do not block if you can defer** | Missing non–Tier-1 fields must not stop handoff when policy allows. |
| **Confirmation > questioning** | One confirmation block beats a multi-step interview. |
| **Default > empty** | Prefer labeled inferred defaults over blank placeholders. |
| **Completion > perfection** | Structural usability for the office beats 100% field confidence. |
| **Minimize user effort at all times** | Fewer turns, less typing, image-first where it reduces typing. |
| **Explain every machine decision** | Defaults, tiers, and sources must be traceable (field strategy + draft bundle). |

---

## 3. System Architecture

Modular responsibilities (names align with code where applicable):

| # | Module | Role |
|---|--------|------|
| 1 | **Intent Capture Layer** | Classify service lane (e.g. add-car, claim, triage) from minimal text + context (`triage.py`, intent helpers). |
| 2 | **OCR Input Layer** | Image → text → structured field candidates (`image_input_pipeline.py`, `parse_ocr_text_to_fields.py`, attachment sidecar & optional inline image on triage). |
| 3 | **Case Draft Engine** | Package known / inferred / missing / confidence for UI and routing (`case_draft_engine.py`). |
| 4 | **Field Strategy System** | **Behavior-controlling** declarative spec: tiers, blocking, deferral, defaults, inference sources (`configs/common/add_car_field_strategy.json`, `field_strategy.py`). Drives missing-field partitioning, confirm priority, and user-flow prompts (§9). |
| 5 | **Auto-Fill / Default Engine** | Config-first defaults (`auto_fill_defaults`, strategy hooks); each applied value carries value / source / confidence / reason (§10). |
| 6 | **Confidence & Field Priority Engine** | Tiers, handoff completeness, confirm priority (`case_draft_engine.py`, fusion with OCR); **product Tier 1/2/3 declared in field strategy** and mirrored in handoff math. |
| 7 | **Confirmation Layer** | Single-block confirmation copy (`build_v6_unified_confirmation_preview`, V4 confirmation replies). |
| 8 | **Immediate Handoff Engine** | `case_usable` / `handoff_ready` gating without blocking on deferrable fields (V5 policy in `case_draft_engine.py` + `triage.py`). |
| 9 | **Broker Completion Layer** | Incomplete-but-usable handoff; `deferred_to_broker_fields` + office/workbench completion (§11). |
| 10 | **Feedback Learning Loop** | User/broker signals → JSONL + analytics (`learning_signals.py`); config promotion manual in pilot (§12). |
| 11 | **Analytics Consistency Layer** | Funnel + field/broker/learning signals (`triage_funnel.py`, `funnel_events.py`, `append_session_analytics_event`) (§13). |

---

## 4. Field Strategy (summary)

**Scope:** Add-car lane (primary pilot). Other lanes follow the same *tier philosophy* with lane-specific contracts.

### Tier 1 — Required for structural handoff (`case_usable`)

Vehicle identity signals (year / make_model / ZIP / delivery / primary_driver as implemented by `add_car_tier1_vehicle_ok` and V5 completeness). **VIN and contact identity do not block `case_usable`** per current product policy (broker completes).

### Tier 2 — Optional, auto-filled

Usage guess, garaging area hints from ZIP prefix or area code, inferred labels from OCR/heuristics. Shown in confirmation when medium+ confidence; always labeled as inferred.

### Tier 3 — Deferred to broker

High-risk or compliance-sensitive fields completed in office: exact binding details, verified VIN, legal name/phone confirmation where required, carrier-specific nuances.

**Per-field table (conceptual):**

| Field / signal | Default | Inference | Confidence | Blocking |
|----------------|---------|-----------|------------|----------|
| Vehicle line | — | Extraction + OCR fusion | medium–high | Tier-1 gate |
| ZIP | — | Regex + OCR | medium | Tier-1 gate |
| Delivery / driver | — | Extraction + keywords | medium | Tier-1 gate |
| Usage | `daily_commute` (weak) | Keywords / default | low–medium | No |
| Area hint | ZIP3 / area code map | Heuristic | low | No |
| VIN | — | OCR / text | medium+ if extracted | No (handoff) |
| Name / phone | — | Extraction | varies | No (handoff) |

---

## 5. Input Strategy

| Mode | Behavior |
|------|----------|
| **Text** | Minimal utterances; thread merge with `[客户]` / `[系统]` labels for extraction. |
| **Image** | OCR via Google Vision when configured; optional **inline base64** on `POST /api/inbox/triage` merges into `v6_ocr_signals`; attachments on case trigger sidecar OCR on save. |
| **Multi-source fusion** | `fuse_ocr_into_inferred` + `merge_v6_ocr_signals` prefer higher-confidence structured fields. |

---

## 6. UX Flow

1. User provides **text and/or image** (minimal).
2. System generates **`case_draft` bundle** (known + inferred + gaps).
3. System **auto-fills** safe defaults and OCR-backed fields.
4. System shows **one confirmation block** (variants B/C; A is baseline).
5. User confirms (e.g. "OK").
6. **Immediate handoff** to broker (`handoff_ready` / persist when enabled); broker completes remainder.

---

## 7. Success Metrics

| Metric | Target / direction |
|--------|-------------------|
| Median turns to handoff | ≤ 2 (product goal) |
| Handoff rate | High for eligible add-car sessions |
| User typing | Low vs baseline (proxy: character count + penalties for no-image paths) |
| Image / OCR usage | High where it reduces typing (measured via simulation + analytics) |
| Correction rate | Acceptable (too high → trust erosion; tune fusion and confirmation) |
| Funnel integrity | `handoff_started` correlates with structural or explicit handoff state (§13) |

---

## 8. Evolution Strategy

1. Run **A/B/C** variants (`v6_auto_input_variant` via client UI config / server default).
2. Run **simulated sessions** (e.g. `scripts/run_v6_auto_input_simulation.py`) with OCR noise and personas.
3. Compare **effort**, **handoff**, **`case_usable`** across variants.
4. **Promote** the best-balanced variant; iterate 2–3 cycles per release train.
5. Record outcomes in **Appendix B** (below).

---

## 9. Field Strategy System (CRITICAL)

Field Strategy is **not** metadata-only documentation. It is an **executable contract** that **must drive** missing-field logic, auto-fill eligibility, confirmation candidate ordering, user-flow prompting, and broker deferral.

**Executable spec:** `configs/common/add_car_field_strategy.json`  
**Runtime:** `services/fiqa_api/inbox_triage/field_strategy.py` — partitions `still_needed` into user-flow vs broker-deferred, sorts confirm priority, and gates next-ask behavior (e.g. skip VIN prompt when `defer_to_broker`).

**Mandatory statement:** **Field Strategy must drive missing-fields logic, auto-fill, confirmation, and handoff behavior.**

### Per-field schema (authoritative)

For each `field_id` in the strategy file:

| Key | Meaning |
|-----|---------|
| `field_id` | Canonical id (JSON key under `fields`). |
| `purpose` | One-line product intent for the slot. |
| `priority_tier` | **Tier 1** = structural path / highest user-prompt priority; **Tier 2** = quality / inferred; **Tier 3** = weak hints — **never** blocks handoff or user-flow nags. |
| `blocking` | If `true`, missing value counts toward Tier-1 structural concern and user-flow “still needed” (subject to V5 `case_usable` math). If `false`, missing does **not** force user-flow blocking prompts (may still appear in full `still_needed_fields` for broker truth). |
| `default_value` | Safe machine default when inference absent (nullable = never fabricate). |
| `inference_sources` | Ordered intent: `text`, `OCR`, `history` (engine routing + docs). |
| `confidence_policy` | e.g. `truth_required`, `prefer_inference`, `weak_hint`, `default_low` — guides labeling and confirm surfacing. |
| `confirmation_required_when` | When to include in single-block confirmation (e.g. `medium_confidence_inferred`, `never_for_tier3`). |
| `defer_to_broker` | If `true`, the chat layer **must not** treat the gap as a prerequisite for continuing; broker/workbench completes later. |
| `override_rules` | Named policies (`user_explicit_wins`, `never_fabricate`, …). |

**Tier semantics (runtime):**

- **Tier 1** — Highest priority for extraction, OCR fusion, and user prompts; drives `tier1_blocking_missing` when `blocking` is true and value is missing.
- **Tier 2** — Improves case quality; may confirm when confidence policy allows; **does not** block handoff when `blocking` is false.
- **Tier 3** — Never blocks handoff; excluded from confirmation priority; not used to extend user interview.

**Dual vocabulary note:** `CONF_HIGH` / `CONF_MEDIUM` / `CONF_LOW` on inferred objects describe *display* confidence; **`priority_tier` + `blocking` + V5 math** are authoritative for gating.

**Draft attachment:** `build_v4_case_draft_bundle` adds `field_strategy`, `still_needed_user_flow`, `deferred_to_broker_fields`, and `broker_completion` to the draft.

---

## 10. Default Engine (SYSTEM LEVEL)

All defaults and inferred values must be **config-driven whenever possible**. Python heuristics remain only where a rule is not yet externalized.

Each applied default or inferred value **must** carry explainable metadata:

| Dimension | Meaning |
|-----------|---------|
| **Value** | The literal applied value or hint. |
| **Default source** | Strategy key (`field_strategy_id`), rule id, or heuristic name (e.g. `keyword_heuristic`, `zip_prefix_heuristic`). |
| **Fallback order** | Declared in strategy `default_engine` / field-level docs — e.g. keyword → industry default → omit. |
| **Confidence label** | Numeric `confidence` + `confidence_policy` + tier. |
| **When to surface to user** | Single-block confirmation when `confirmation_required_when` matches (e.g. medium+ inferred). |
| **When to silently apply** | Low-risk Tier-2/Tier-3 hints applied into `inferred_fields` without extra turns. |

**Code:** `auto_fill_defaults()` in `case_draft_engine.py`; usage industry fallback via `usage_default_from_strategy()`; ZIP / area-code hints tagged with `default_engine` trace fields where configured.

**Non-goal:** Multi-turn interrogation to satisfy defaults.

---

## 11. Broker Completion Layer

**Broker-usable case:** Runtime `case_usable` from `evaluate_v5_case_usable` (Tier-1 vehicle gate + V5 completeness threshold). Handoff may proceed when `case_usable` is true even if quote-perfect completeness is not.

**Deferred fields:** Fields with `defer_to_broker` or Tier-3 / non-blocking Tier-2 gaps appear in `deferred_to_broker_fields` and **must not** block the user chat path. Full gaps remain in `still_needed_fields` / `missing_fields` for the service record and broker UI.

**Surfacing:** Case draft exposes `broker_completion` with `broker_usable_case`, `deferred_fields`, and human-readable `office_completes_summary` for workbench copy.

**Tracking:** Broker completion is implied by persistence on the service record; optional `broker_field_edit` / completion signals feed the learning loop (§12).

**Hard rule:** Do not block handoff for VIN, identity, or Tier-3 hints when `case_usable` is satisfied and strategy marks deferral.

---

## 12. Learning Loop (LIGHTWEIGHT V1)

**Signals (inputs):**

- **User corrections** — After confirmation or inline edits; thread deltas vs prior draft truth. Recorded via `learning_signals.record_user_correction_signal` + optional `append_session_analytics_event("user_correction_signal", …)`.
- **Broker edits** — Workbench / service-record updates; `record_broker_field_edit_signal` for field-level completion (V1 stub path for future aggregation).

**Outputs:**

- **Feedback memory** — Append-only JSONL under configurable path (`LEARNING_SIGNALS_PATH`); suitable for weekly review and future default promotion (no silent auto-promotion in pilot).

**Future:** Automated promotion of stable ZIP→garaging or usage priors into config behind review.

---

## 13. Analytics Consistency Layer

**Canonical funnel order:** `session_started` → `first_meaningful_input` → `case_created` → `quote_ready_reached` → `handoff_started` → `handoff_confirmed` → `broker_followup_started` (`funnel_events.CANONICAL_FUNNEL_EVENTS`).

**`handoff_started`:** Emitted when **`handoff_ready` OR (`case_usable` AND `quote_ready_status == "quote_ready"`)**.

**PTD mapping (measurable):**

| Product behavior | Analytics / metadata |
|-------------------|----------------------|
| Field strategy partitions | `case_snapshot.still_needed_fields`, `deferred_to_broker_fields`, `case_draft.field_strategy` |
| Handoff / gating | `handoff_ready`, `case_usable`, `quote_ready_status`, funnel `handoff_started` metadata |
| Broker completion | `broker_completion` on draft; optional `broker_field_edit` learning rows |
| Learning loop | `user_correction_signal`, JSONL `learning_signals` |

**Baseline events:** `field_progress`, `append_blocked`, and other `append_session_analytics_event` rows for drill-down.

---

## 14. Inline Image UX Completion

**Target loop:** file picker → preview → upload → OCR → merge into `v6_ocr_signals` → triage draft → confirmation.

| Stage | Status |
|-------|--------|
| API: inline base64 on triage | **Shipped** |
| Backend: OCR merge | **Shipped** |
| UI: file picker + preview | **Partial** — wire in product surfaces as scope allows; broker/workbench paths may dominate |
| Mobile polish | Future |

**Guardrail:** OCR skip / empty text must not hard-fail (synthetic `[image intake]` fallback).

---

## Appendix A — PTD_GAP_ANALYSIS_V2

### Missing modules

- **Full Default Engine (§10)** — rules not yet fully externalized from `auto_fill_defaults`.
- **Automated learning promotion** — correction → config pipeline is manual.
- **End-user mobile image UX** — picker/preview not complete everywhere.

### Partial modules

- **Field Strategy System** — **v1 shipped**: JSON spec + `field_strategy` on draft + usage default hook; heuristics still mostly code-defined.
- **Broker completion** — persistence + workbench exist; async SLA metrics thin.
- **Analytics** — `handoff_started` alignment fixed; dashboards for new metadata (`case_usable` in funnel) optional.

### Inconsistencies (watch)

- **Dual tier vocabulary** — `CONF_HIGH` / `CONF_MEDIUM` / `CONF_LOW` (confidence display) vs `priority_tier` 1/2/3 (product); both may appear on the same inferred object. Document which is authoritative for blocking (**priority_tier + V5 math**).
- **Multi-step questioning** — Soft-route starters may still expose `still_needed_fields` lists; keep add-car on single-confirmation track for pilot.

---

## Appendix B — Simulation & evolution log

**Run:** 2026-04-20 (post field-strategy behavior wiring) — `PYTHONPATH=. python3 scripts/run_v6_auto_input_simulation.py --sessions 320 --cycles 2`

| Cycle | Focus (scripted heuristic) | Variant A handoff | Variant B handoff | Variant C handoff | Median turns (all variants) |
|-------|----------------------------|------------------|------------------|------------------|------------------------------|
| 1 | input_effort_score | 0.331 | 0.381 | 0.275 | 2 |
| 2 | handoff_rate | 0.244 | 0.300 | 0.250 | 2 |

**Notes:** 160 sessions per variant per cycle (Monte Carlo). Compare **completeness** via `case_usable_rate`, **handoff** via `handoff_rate`, **effort** via `input_effort_score` + typing chars. Harness is largely unchanged; strategy affects live triage + draft, not this script’s RNG personas.

**Earlier run (400 × 3 cycles):** retained for historical comparison in git history / prior appendix snapshots.

---

## Appendix C — PRIORITY_TASK_LIST

### Critical

1. **Field Strategy System** — **v1 done**: `add_car_field_strategy.json`, `field_strategy.py`, `case_draft_engine` attachment, usage default integration. **Next:** migrate more `auto_fill_defaults` branches to config rules.
2. **Default Engine refactor** — externalize heuristics into declarative rules (§10); keep single-confirmation UX.
3. **Analytics** — **done**: `handoff_started` aligns with `handoff_ready` ∨ (quote-ready ∧ `case_usable`); validate in dashboards.
4. **Broker completion (basic)** — surface `field_strategy.tier1_blocking_missing` + `missing_fields` in office UI for faster backfill.

### High impact

- Product UI for inline image (§14).
- Attachment + inline OCR fusion verification in pilot.
- Dashboards: median turns, image usage, handoff rate, funnel drop-offs.

### Future

- Second OCR provider or on-device OCR.
- Automated variant promotion behind feature flags + guardrail tests.
- PDF ingestion (currently skipped in OCR pipeline).

---

## Appendix D — Implementation log (PTD execution)

| Change | Path / behavior |
|--------|-----------------|
| Field strategy config | `configs/common/add_car_field_strategy.json` (purpose, `defer_to_broker`, `confidence_policy`, `default_engine`) |
| Runtime partition + prompts | `field_strategy.py` — `partition_still_needed_by_strategy`, confirm ordering; `triage._get_next_ask_for_add_car` respects VIN deferral |
| Draft bundle | `build_v4_case_draft_bundle` — `field_strategy`, `still_needed_user_flow`, `deferred_to_broker_fields`, `broker_completion` |
| Default engine | `auto_fill_defaults` — strategy-tagged metadata for usage, garaging, vehicle hints |
| Learning V1 | `learning_signals.py` — JSONL feedback memory |
| Funnel | `emit_funnel_from_triage_result` + `case_snapshot` extended metadata (§13) |
| Tests | `tests/test_field_strategy.py`, `tests/test_minimal_analytics.py`, `tests/test_field_strategy_behavior.py` |

---

*Full doc map: `docs/PROJECT_DOC_SYSTEM_MAP.md`*
