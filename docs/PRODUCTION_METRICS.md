# Production metrics — Unified Intake triage / Add-Car

Single place to define correctness, latency, and behavior signals used by dashboards and `scripts/run_full_regression.py`.

See also: `services/fiqa_api/inbox_triage/structured_turn_obs.py` (stderr JSON lines `triage_turn_obs`, `pg_truth_turn` when `INBOX_STRUCTURED_TURN_OBS=1`), and chaos output `scripts/llm_chaos_live_triage_check.py` (`summary` block).

---

## Correctness (must converge to zero)

| Metric | Meaning | Target |
|--------|---------|--------|
| `wrong_vehicle_rate` | Disagreement between Postgres active-vehicle identity and API `vehicle_key` / leaks from inactive entities | **0** |
| `pg_truth_mismatch_rate` | Turns with `pg_truth_match: false` in chaos/live harness (`pg_truth_mismatch_turns / pg_truth_checks`) | **0** |
| `clarify_missed_rate` | Ambiguous multi-vehicle scenarios where clarification should trigger but did not (requires ambiguity oracle beyond PG↔API) | **0** (product QA / future harness) |

---

## Performance

| Metric | Meaning | Target |
|--------|---------|--------|
| `http_p50`, `http_p95` | ASGI chaos client wall time per `/api/inbox/triage` turn (`latency_ms`) | **p95 \< 6s** regression gate (`run_full_regression.py`) · product target \< 5s where documented |
| `triage_p50`, `triage_p95` | `triage_turn_metrics.latency_ms` breakdown when `TRIAGE_RETURN_PERF_METRICS=1` | Track for hotspots |

---

## Behavior

| Metric | Meaning |
|--------|---------|
| `clarify_rate` | `clarify_turns_total / turn_count` in chaos summary (`active_vehicle_clarify_prompt`) |
| `switch_rate` | Derived from resolver + DB state (track via scenario logs); not duplicated here |
| `create_rate` | New entity rows vs turns (same) |

Roll-up files: `results/FULL_REGRESSION.json`, `results/LATEST_SYSTEM_STATUS.md` after a full regression run.
