# DOUBLE BRAIN + CONTRACT AUTHORITY — Convergence Sprint

**Control note (single source of truth for this sprint).**  
**Date:** 2026-05-07  
**Theme:** Reduce duplicated truth and ambiguous ownership without rewriting triage, resolver, or workbench.

---

## 1. Objective

- Make **one authoritative story** visible for vehicle identity, lifecycle/progress axes, and contract docs.
- **Converge** frontend/backend assumptions where they drifted in **documentation** and **inline contracts** (minimal runtime change).
- Keep regressions green; preserve demo behavior.

## 2. Non-goals

- No rewrite of `triage.py`, `workbench`, or routing “resolver” stacks.
- No speculative performance work.
- No wiring `resolve_add_car_active_vehicle` into triage in this pass (behavior-changing; needs dedicated sprint with scenario parity).
- No deletion of `active_vehicle_resolver.py` without the above.

## 3. Current system map (concise)

| Layer | Role |
|-------|------|
| `services/fiqa_api/routes/inbox_triage.py` | HTTP orchestration; `_finalize_response_with_pg_truth`; `_attach_case_lifecycle`; stable API finalization |
| `services/fiqa_api/inbox_triage/triage.py` | Core triage (large); handoff/readiness; add-car heuristics; uses `routing_guard` for append scope |
| `services/fiqa_api/inbox_triage/routing_guard.py` | Pure **append** vehicle conflict / scope ambiguity helpers (`detect_vehicle_conflict`, phrase detectors) |
| `services/fiqa_api/inbox_triage/active_vehicle_resolver.py` | **Tested** segment-based vehicle resolution; **not imported by triage** on mainline (2026-05-07) |
| `services/fiqa_api/inbox_triage/case_lifecycle.py` | `_derive_case_lifecycle` — additive `case_lifecycle` axis |
| `services/fiqa_api/inbox_triage/entity_repository.py` | Postgres vehicle entity read/write |
| `ui/src/api/inboxTriage.ts` | Wire `TriageResult` type |
| `ui/src/api/triageResultContract.ts` | **Core vs optional** field picking; contract documentation |
| `ui/src/components/intake/caseLifecycleDisplay.ts` | Server-first `case_lifecycle`; legacy fallback derivation |
| `ui/src/features/intake/utils/intakePure.ts` | Office/customer copy, queue readiness, **mirror heuristics** (focus inference, human_confirmation fallback) |

## 4. Existing discoveries (pre-sprint + verified this sprint)

1. **Doc vs code drift:** `docs/DEPRECATED_PATHS.md`, `UNIFIED_INTAKE_MASTER_BLUEPRINT.md`, `SYSTEM_ONE_PAGE_MAP.md`, and `PLUGIN_ARCHITECTURE_MAP.md` stated that `triage.py` **calls** `resolve_add_car_active_vehicle` / `_compute_add_car_identity_bundle`. **Grep:** `_compute_add_car_identity_bundle` **does not exist**; `resolve_add_car_active_vehicle` is **only** referenced from `active_vehicle_resolver.py` and `tests/test_active_vehicle_resolver.py`.
2. **True production vehicle authority:** Triage builds fields with heuristics + `routing_guard` + entity paths; **HTTP** overwrites from Postgres when `_finalize_response_with_pg_truth` applies — still one **display** convergence point.
3. **Lifecycle double representation:** Server `case_lifecycle` (derived + persisted overlay) vs client `lifecycle_status`, `collection_stage`, `quote_ready_status`, `handoff_ready`. Frontend correctly **prefers** `case_lifecycle` then mirrors `_derive_case_lifecycle` for legacy.
4. **Frontend “second brain”** (intentional compatibility): `inferCaseFocusFromText`, `needsHumanConfirmation` fallbacks when backend omits flags — product-safe but duplicates **category** intelligence shallowly.

## 5. DOUBLE_BRAIN_MATRIX

| area | source A | source B | risk | user-visible? | authority unclear? |
|------|----------|----------|------|---------------|--------------------|
| Add-car vehicle line | `triage.py` heuristics + entity | `active_vehicle_resolver.py` (unwired) | Medium — two mental models in codebase | Yes (summary lines) | **Was** unclear in docs; code path is triage+PG |
| Append vehicle scope | `routing_guard.detect_vehicle_conflict` | Triage sets `vehicle_key` / boundary fields | Medium if diverged | Yes (append / new case) | Low — guard is pure |
| API vehicle display | Triage-computed fields | `_finalize_response_with_pg_truth` | Low when PG on | Yes | Low — route wins |
| Progress axis | `case_lifecycle` (`_derive_case_lifecycle`) | `lifecycle_status`, `collection_stage` | Low if UI prefers `case_lifecycle` | Yes | Medium for new engineers |
| Formal submit CTA | `resolveCaseLifecycle` + `isAddCarReadyForFormalSubmit` | `lifecycle_status === handoff_pending` | Low — legacy compat | Yes | Documented in TS |
| Human confirmation | `human_confirmation_required` | `needsHumanConfirmation` heuristics | Low — fallback only | Yes (badges) | Low |
| Add-car detection | `quote_ready_status` / structured fields | `inferCaseFocusFromText` regex | Medium under edge chats | Yes (UI lane) | Medium |
| Contract docs | `DEPRECATED_PATHS` / blueprint | Actual imports in `triage.py` | **High** for onboarding | No | **Fixed this sprint** |

## 5a. CONVERGENCE_TARGET_SELECTION

| Target | Rationale | Done this sprint? |
|--------|-----------|-------------------|
| Align canonical docs with **grep-verified** `triage.py` | Zero runtime risk; removes false “resolver wired” narrative | **Yes** |
| Cross-link `case_lifecycle` authority (`_attach_case_lifecycle`, `_derive_case_lifecycle`, TS fallback) | Single documented chain | **Yes** |
| `active_vehicle_resolver` module header: unwired + PG finalizer pointer | Clarifies test vs production call graph | **Yes** |
| Wire `resolve_add_car_active_vehicle` into triage | High leverage; behavior-changing | **No** (defer) |
| Strip frontend queue / focus heuristics | Needs broker UX + tests | **No** (defer) |

## 6. AUTHORITY_MAP

| concept | current authority | fallback authority | frontend assumptions | backend assumptions | stale paths |
|---------|-------------------|--------------------|----------------------|---------------------|-------------|
| lifecycle (UX axis) | `case_lifecycle` after `_attach_case_lifecycle` | `_derive_case_lifecycle` on client | Prefer API field; mirror for legacy | Overlay `formal_submitted_at` from persisted case | Old servers without `case_lifecycle` |
| vehicle / identity | Postgres active row **on response** | Triage in-memory before finalize | Trust finalized API fields | `routing_guard` on append; heuristics in triage | Unwired `active_vehicle_resolver` |
| active case | `case_id` + case store / truth repo | session id | Local session storage | Route loads stub/full per flow | JSON read fallback (dev) |
| workflow state | `case_status` (office) | — | `CASE_STATUS_OPTIONS` | `case_store` | — |
| route status | `triage_path`, assist (optional) | — | Debug only per contract | Set in triage/route | — |
| action readiness | `action_ready`, `case_usable`, gates in triage | — | Display | `case_draft_engine`, policies | — |
| quote readiness | `quote_ready_status` | `still_needed_fields` | Strips + queue labels | `triage_add_car_policy` | — |
| binding | `identity_binding_state`, link keys | — | Stage-1 UI | Request models in route | — |
| collected fields | Triage + case persistence | — | Lists in UI | `case_store`, append | — |

## 7. Risks

- **Future engineer wires `resolve_add_car_active_vehicle` twice** or conflicts with triage if docs drift again → mitigated by corrected canonical docs + module docstring.
- **Queue readiness** (`getQueueReadinessLabel`) vs server gates — partial duplication; changing one without the other could confuse brokers.
- **Full regression runtime** (chaos + ASGI) may be environment-sensitive.

## 8. Validation gates

| gate | command | Sprint result |
|------|---------|---------------|
| UI build | `cd ui && npm run build` | Run — see Final report |
| Circular imports | `cd ui && npx madge --circular --extensions ts,tsx src` | Run — see Final report |
| Python syntax | `python3 -m compileall` (changed modules) | Run — see Final report |
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` | Run — see Final report |
| Focused tests | `PYTHONPATH=. python3 -m pytest tests/test_case_lifecycle.py tests/test_active_vehicle_resolver.py -q` | Run — see Final report |
| Full regression | `PYTHONPATH=. python3 scripts/run_full_regression.py` | Run when feasible — see Final report |

## 9. Iteration log

| time | action |
|------|--------|
| 2026-05-07 | Created control note; deep grep (`resolve_add_car_active_vehicle`, `_compute_add_car_identity`), read `routing_guard`, `case_lifecycle`, frontend mirrors |
| 2026-05-07 | **Loop 1:** Fixed `DEPRECATED_PATHS.md`, `UNIFIED_INTAKE_MASTER_BLUEPRINT.md`, `SYSTEM_ONE_PAGE_MAP.md`, `PLUGIN_ARCHITECTURE_MAP.md`; docstrings in `case_lifecycle.py`, `active_vehicle_resolver.py`; contract comments in `triageResultContract.ts`, `caseLifecycleDisplay.ts` |
| 2026-05-07 | Validations: pytest OK, madge OK, guardrail PASS, UI build OK (Node 22 on PATH), `run_full_regression` chaos PASS correctness but **http_p95** 6004.6ms &gt; 6000ms cap |

## 10. LOOP_1_SYSTEM_REVIEW

1. **Reduced double brain?** **Yes** in the **documentation / contract** layer — onboarding no longer claims a non-existent `_compute_add_car_identity_bundle` or a triage import that is absent.
2. **Clearer ownership?** **Yes** — vehicle **display** authority explicitly **route PG finalizer**; segment resolver module explicitly **unwired**.
3. **Compatibility worsened?** **No** runtime behavior changed.
4. **Frontend/backend alignment?** Comments now state server-first `case_lifecycle` and `_attach_case_lifecycle` overlay behavior.
5. **Stale fallback removable?** Not yet — `resolveCaseLifecycle` fallback still needed for old payloads.
6. **Contract drift exposed?** **Yes** — several first-class docs were ahead of code.

## 11. Deploy / infra (Step 11)

- **Vite / Node:** `ui/package.json` requires `>=20.19.0`. In this environment the default `node` on PATH was **20.18.2** (Cursor-injected), which breaks `vite build`. **Fix:** prepend nvm Node **22.x** or **20.19+** on PATH in CI and local scripts (document for Vercel/Cloud Build if they pin an older patch).
- **No server on 8001:** Optional guardrail API probe skipped; no CORS or deploy changes made.

## 11a. LOOP_2 (second target)

- **Target:** Same risk band — extend **inline** API contract documentation (`triageResultContract`, `caseLifecycleDisplay`) and **Python** module headers so the authority chain is visible in-repo without opening `results/*.md` time slices.
## 12. PRODUCTIZATION_INSIGHTS

1. **More product-like?** Slightly — fewer contradictory “official” narratives.
2. **Authority clearer?** Yes for vehicle and lifecycle **emission** paths.
3. **Faster onboarding?** Yes if engineers read `DEPRECATED_PATHS` + blueprint.
4. **Less surprise?** Reduces “why doesn’t triage import the resolver?” confusion.
5. **SaaS readiness?** Indirect — accurate contracts reduce wrong refactors.
6. **Pilot safety?** Unchanged runtime — safe.
7. **Regression risk?** Lower for **doc-induced** bugs; technical debt remains until resolver wired or removed.

## 13. CONTRACT_AUTHORITY_REPORT

### TriageResult (grouping)

- **Core (UI headings / identity):** `pickTriageResultCore` — includes `case_lifecycle`, vehicle summary keys, `handoff_ready`, `quote_ready_status`, `lifecycle_status` (legacy axis).
- **Optional signals:** `assist`, `route_perf`, `triage_turn_metrics`, `triage_path` — must not gate primary workflow.
- **Authoritative:** For lifecycle UX axis, prefer **`case_lifecycle`** from API after `_attach_case_lifecycle`.
- **Deprecated / legacy:** Relying on **`lifecycle_status` alone** for formal-submit CTA without `case_lifecycle` — supported via `isAddCarReadyForFormalSubmit` for older backends.
- **Frontend-only compatibility:** `inferCaseFocusFromText`, partial `needsHumanConfirmation` heuristics.

### Small tightening done

- Cross-references between `case_lifecycle.py`, `_attach_case_lifecycle`, and TS `resolveCaseLifecycle` / `triageResultContract.ts`.

## 14. SELF_CRITIQUE_REPORT

1. **Actually reduce double brain?** **Docs + comments yes**; **executable** duplicate (unwired resolver vs triage heuristics) **remains**.
2. **Only move logic around?** **No** — clarified authority without moving Python logic.
3. **Added complexity?** Minimal — a few sentences in docstrings.
4. **Still duplicated?** Triage vehicle heuristics vs `active_vehicle_resolver`; frontend focus inference vs backend categories.
5. **Still dangerous?** Wiring resolver without scenario parity; queue label heuristics vs server gates.
6. **Future sprint unlocked?** **Single decision:** import `resolve_add_car_active_vehicle` in triage **or** delete module and merge tests into triage policy.
7. **What NOT to do next?** Blindly delete resolver; “fix” queue labels without broker UX review.

## 15. DOUBLE_BRAIN_CONVERGENCE_FINAL_REPORT

1. **Authority clarified:** API vehicle mirror = `_finalize_response_with_pg_truth`; lifecycle axis = `_attach_case_lifecycle` + `_derive_case_lifecycle`; segment resolver = **test-only** until wired.
2. **Duplication reduced:** **Narrative** duplication across blueprint / deprecated paths / plugin map / system one-pager.
3. **Contracts improved:** `TriageResult` header comments; Python module docstrings; canonical markdown corrected.
4. **Regressions:** `guardrail_inbox_triage.sh` **PASS**; focused pytest **PASS**; **`run_full_regression` correctness PASS** (`wrong_vehicle_related: 0`, 100% pass rate) but **SLO assertion** failed — HTTP p95 **6004.6 ms** vs **6000** ms cap (~5 ms over; not attributed to this sprint).
5. **Risks remain:** Unwired resolver; frontend queue heuristics; large `triage.py`.
6. **Unlocked work:** Resolver wiring sprint with explicit scenario matrix; optional removal sprint if product chooses heuristics-only.
7. **Performance:** No change.
8. **Productization impact:** Trust in internal docs; fewer wrong refactors.
9. **Remaining double-brain areas:** Executable vehicle policy (triage vs resolver); UI `inferCaseFocus` vs backend category.

## 16. Validation run log (filled by execution)

| Step | Result | Notes |
|------|--------|--------|
| `python3 -m compileall` (changed modules) | **PASS** | |
| `pytest tests/test_case_lifecycle.py tests/test_active_vehicle_resolver.py` | **PASS** | |
| `npm run build` (ui) | **PASS** | Requires Node **≥20.19** on PATH; Cursor default `node` was 20.18.2 — succeeded with `/home/andy/.nvm/versions/node/v22.22.0/bin` prepended |
| `npx madge --circular ... src` (ui) | **PASS** | No cycles |
| `bash scripts/guardrail_inbox_triage.sh` | **PASS** | API spot-check on 8001 **SKIP** (no server); all scripted packs OK |
| `python3 scripts/run_full_regression.py` | **PARTIAL** | Guardrail + ASGI chaos completed; rollup **failed assertion** `http_p95_gt_6000ms` (**6004.64 ms** vs 6000 cap) — **4.6 ms** over threshold; `wrong_vehicle_related: 0`, `pass_rate_pct: 100`. Treat as **environment / SLO noise**, not regressions from this sprint (doc-only + comments). |
| curl / representative HTTP flows | **SKIP** | No `8001` listener in this run |

---

## 17. FINAL DECISION

**C — NEEDS_ANOTHER_CONVERGENCE_PASS**

**Why:** Documentation and inline contracts are aligned with the **current** mainline, but the **executable** duplicate (`active_vehicle_resolver` vs triage heuristics) is **deliberately unchanged** and requires a **follow-up** wiring or removal sprint with scenario parity. Runtime behavior and pilot posture are unchanged — **not** rollback.

---

## 18. Final one line

This sprint made the system more trustworthy not by adding intelligence, but by reducing contradiction and clarifying authority.
