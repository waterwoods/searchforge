# ANALYTICS_SYSTEM_REPORT

## 1. Score system (North Star, 0–10)

Deterministic composite of **five dimensions**, **0–2 points each**:

| Dimension | Meaning |
|-----------|---------|
| **start_ease** | First meaningful customer input by turn 1 (2), turn 2 (1), else 0. |
| **continuity** | No append/boundary blocks or reroute (2); one break (1); multiple blocks (0). |
| **guidance** | Reached `quote_ready`, or used `next_best_question`, else inferred from draft vs missing fields. |
| **efficiency** | Turns to `quote_ready` (tight band = 2, mid = 1, slow = 0); stalls after `quote_ready` without `handoff_started` cap at 1; non–quote-ready paths use turn depth heuristics. |
| **trust** | Penalizes “complete” phrasing in `client_reply_draft` when `still_needed_fields` non-empty; inconsistent `quote_ready` + still-needed → 0. |

Implementation: `services/fiqa_api/analytics/north_star_score.py` (`compute_north_star_score`). Output includes `explain` for auditability.

## 2. Funnel definition

Canonical events (ordered): `session_started` → `first_meaningful_input` → `case_created` → `quote_ready_reached` → `handoff_started` → `handoff_confirmed` → optional `broker_followup_started`.

- **Deduped** per session/case so **append** does not double-count `quote_ready_reached`.
- **Anonymous** requests (no `session_id` and no `case_id`) skip dedupe to avoid cross-user collision in the in-memory buffer.

## 3. Implementation

| Piece | Location |
|-------|----------|
| Event buffer + `emit_funnel_event` | `services/fiqa_api/analytics/funnel_events.py` |
| Triage wiring + snapshots | `services/fiqa_api/analytics/triage_funnel.py`, `services/fiqa_api/routes/inbox_triage.py` |
| Funnel math + drop-off | `services/fiqa_api/analytics/funnel_metrics.py` |
| Dashboard API | `GET /api/analytics/dashboard` in `services/fiqa_api/routes/analytics_dashboard.py` |
| Legacy structured logs | `track_event` retained where useful; funnel milestones go through the standard payload + buffer |

## 4. Simulation results

Run: `python3 scripts/run_analytics_north_star_simulation.py` — output block **`ANALYTICS_SIMULATION_RESULTS`**.

Observed spread (example): happy path **10.0**, slow user **7.0**, messy user **5.0**, quote-ready without handoff **9.0** (efficiency capped when `handoff_started` never fires).

## 5. Test results

- `tests/test_north_star_and_funnel.py` — perfect vs broken scores, funnel counts, dedupe.
- `tests/test_minimal_analytics.py` — field_progress logging; funnel rows for quote-ready / handoff_confirmed.

## 6. Insights

- Largest product signal is **quote_ready → handoff** (conversion stall); scoring now penalizes **quote_ready without `handoff_started`**.
- **Session id** should always be set client-side so milestones dedupe correctly and cohorts stay clean.

## 7. What to improve next

- Persist events to Postgres or BigQuery when pilot volume exceeds in-memory buffer.
- Tie `broker_followup_started` to office/workbench actions.
- Add language-specific trust patterns per client pack.
