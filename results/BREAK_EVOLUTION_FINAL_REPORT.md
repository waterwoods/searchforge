# Add-Car Break Evolution — Final Report

**Sprint:** Phase 2 (BREAK → FIX → HARDEN)  
**Branch:** `auto-evolution/add-car-break-evolution-20260424`  
**Rule path:** `LLM_GENERATION_ENABLED=0` (deterministic `triage_conversation`)

## 1. Time and loops

| Metric | Value |
|--------|--------|
| Approx. session time | ~30 minutes (automation-assisted) |
| Loops | **3** — (1) build library + baseline, (2) first surgical fixes + replay, (3) wave-2 hardening + follow-up / Highlander + regression |
| `pytest` | Full suite: **1 known failure** on `test_first_quote_ready_moment_compact_no_all_complete_wording` (reproduces **without** this sprint’s triage diff — contact-only draft `请提供姓名` vs expected `整理` / `look right`). **1 import error** in `tests/test_append_truth_alignment.py` (missing `…_resolve_add_car_handoff_phrase_key` symbol). Excluding those, targeted runs and **guardrails pass.** |
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** (after case-boundary fix for CB-05) |

## 2. Scenario stats

| Item | Count |
|------|--------|
| Scenarios in `add_car_break_scenarios.py` | **120** (6–12 user turns each) + **8** wave-2 “harder” cases subsampled into the same 120-total build via reduced padding |
| **Baseline** pass rate (first run, `BREAK_BASELINE.json`) | **116 / 120** (96.7%) |
| **Final** pass rate (`BREAK_WAVE2.json` / `brk_reg` replay) | **120 / 120** (100%) |

**Artifacts (local):** `results/BREAK_BASELINE.json`, `results/BREAK_AFTER_FIX_1.json`, `results/BREAK_WAVE2.json`  
(Can be regenerated: `scripts/run_add_car_cplus_scenario_library.py` with `--library-path tests/scenario_libraries/add_car_break_scenarios.py`.)

## 3. Top failure patterns (from baseline, TOP 3 focused)

1. **summary_or_substring_mismatch / primary line stuck on Tesla** — Last bubble only negated Tesla (“Tesla was a mistake”, “Model 3 noise”) while an earlier turn held the true vehicle (e.g. 2020 Camry). The make extractor latched `tesla` / `Model 3` from the last line.
2. **follow_up_type_mismatch (`already_sent`)** — Thread had “already sent on WeChat” in an earlier turn; the **last** turn was a neutral slot (e.g. primary driver) and did not re-trigger `_message_claims_completed_material_send` on the last message alone.
3. **summary_or_substring (wrong primary model in multi-vehicle noise)** — Last line was “ignore CRV” (negation) and the system briefly preferred CR-V; related to ordering of negation vs. affirmed add target.

(Additional pattern addressed in loop 3: **year-only / missing `Highlander`** when the customer writes “2019 highlander” without the word “Toyota”.)

## 4. Fix summary (surgical, `triage.py` only)

| Change | Why it worked |
|--------|----------------|
| **Thread-aware `follow_up_type`** — `_all_customer_concat_from_merged` + second arg to `_derive_follow_up_type`; after **corrections** are handled, if the last bubble did not already claim a completed send, but the **full customer concat** does, and the last line is not a question / vague meta opener, return `already_sent`. | Sticky “materials already sent” when the customer moves on to driver/zip/confirm, matching product invariant #6. |
| **Exclude “还有一个问题”-style appends** from sticky `already_sent` | Sticky was swallowing `CB-05` (borderline append). Those phrases need **borderline** / human confirmation, not `already_sent`. |
| **Negation-aware Tesla / Model 3** in `_extract_make_model_from_lower` | Skips latching a positive Tesla identity when the bubble is about ignore/mistake/noise; allows **Camry/final** in the same bubble to win. |
| **`if "highlander" in t` → `Toyota Highlander`** (mirrors Camry without requiring “toyota”) | Fixes “2019 highlander” threads where “Toyota” is never typed. |

**No architecture refactors, no UI/PG, no new subsystems** — as requested.

## 5. Remaining weaknesses (honest)

- **Last-line negation** is still pattern-based. Novel phrasing (“kidding about the Audi”) may still wrong-latch a make until we see real traffic.
- **Sticky `already_sent`** uses heuristics (length, `?`, vague Chinese openers). Edge cases: long “rants” with embedded questions, or a later denial of an earlier “sent” claim, may need thread-level *revocation* detection (not in scope for this pass).
- **LLM on path** is not covered by this battery; all numbers here are **rule path only**.
- **Pre-existing `pytest` / import drift** (conversion layer test, append test import) should be triaged on `main` — not introduced by the files changed here.

## 6. Product judgment

**INTERNAL_DEMO_READY**

**Rationale:** Deterministic add-car lane now survives a **120-scenario** chaos pack (including wave-2) with **100%** assertion pass on the runner, and **inbox triage guardrails** are green. Full customer pilot still wants LLM/observability and the outstanding unit-test hygiene above, so **not** `CUSTOMER_DEMO_READY_CANDIDATE` yet.

---

*Generated: 2026-04-24 (repo date context).*
