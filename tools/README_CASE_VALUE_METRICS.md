# Case Value Metrics V1

Read-only export of journey timings from existing case fields and Timeline / Slice1 events.

## Usage

```bash
# From live Cloud QA (loads .env.cloudrun.qa)
PYTHONPATH=. python3 tools/export_case_value_metrics.py case_4e5adf36c637

# Multiple cases
PYTHONPATH=. python3 tools/export_case_value_metrics.py case_a case_b --out-dir /tmp/metrics

# Offline fixture
PYTHONPATH=. python3 tools/export_case_value_metrics.py \
  --from-json docs/evidence/qa-fast-lane/20260803T190949Z-final-phone/case-final.json
```

Outputs: `{stem}.json` and `{stem}.csv` under `--out-dir` (default `artifacts/case_value_metrics/`).

## Supported metrics

| Metric | Source |
|--------|--------|
| customer start | `created_at` |
| formal submit | `formal_submitted_at` |
| broker-ready (initial) | `formal_submitted_at` (product shape) |
| Request More loops | count of `broker_request_more_created` |
| supplement turnaround | first Request More → `supplement_submitted` |
| broker supplement review | `broker_supplement_reviewed` |
| office accept | `office_materials_accepted_at` |

## Explicitly unsupported (not fabricated)

- Broker first-open time (no event / `broker_confirmed_at` usually null)
- AI accept / edit / reject rates (no events yet)

Missing timestamps appear as empty CSV cells; reasons go in `data_quality_notes`.

## Tests

```bash
pytest tests/test_export_case_value_metrics.py -q
```
