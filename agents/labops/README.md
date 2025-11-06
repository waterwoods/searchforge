# LabOps Agent V1
**Autonomous COMBO Experiment Orchestration**

## Overview
V1 LabOps Agent runs one COMBO (flow control + routing) experiment end-to-end, evaluates results using deterministic rules, and makes deployment decisions automatically.

**No UI. No LLM. Pure rule-based automation.**

## Features
✅ **Plan → Execute → Judge → Apply → Report** lifecycle  
✅ **Health gate**: Block on unhealthy dependencies  
✅ **Decision rules**: Pass if ΔP95 ≤ -10% AND error < 1%  
✅ **Flag management**: Auto-apply on PASS; rollback hint on FAIL  
✅ **≤60-line summary**: Concise, actionable reports  
✅ **Append-only history**: Immutable audit trail (JSONL)  
✅ **AB balance check**: Warn when sample imbalance > 5%  
✅ **Time budget enforcement**: Respect execution limits  

## Quick Start

### 1. Run Agent (Default Config)
```bash
./scripts/run_labops_agent.sh
```

### 2. Dry Run (No Execution)
```bash
./scripts/run_labops_agent.sh --dry-run
```

### 3. Custom Config
```bash
./scripts/run_labops_agent.sh --config my_plan.yaml
```

### 4. View Results
```bash
# View summary
cat reports/LABOPS_AGENT_SUMMARY.txt

# View history
tail agents/labops/state/history.jsonl

# View latest lab report
cat reports/LAB_COMBO_REPORT_MINI.txt
```

## Configuration
Default config: `agents/labops/plan/plan_combo.yaml`

```yaml
experiment:
  qps: 10.0
  window_sec: 120  # 2 minutes
  rounds: 2        # ABAB cycles
  flow_policy: "aimd"
  target_p95: 1200
  routing_mode: "rules"
  topk_threshold: 32

thresholds:
  pass_delta_p95_max: -10.0  # Pass if ≥10% improvement
  edge_delta_p95_max: -5.0   # Edge if 5-10% improvement
  max_error_rate: 1.0        # <1% errors required
```

## Decision Logic

| Verdict | Condition | Action |
|---------|-----------|--------|
| **PASS** | ΔP95 ≤ -10% AND error < 1% | Apply flags |
| **EDGE** | ΔP95 in (-10%, -5%] AND error < 1% | Manual review |
| **FAIL** | ΔP95 > -5% OR error ≥ 1% | No action, provide rollback |

## File Structure
```
agents/labops/
├── agent_runner.py          # Main orchestrator (Plan→Execute→Judge→Apply→Report)
├── tools/
│   ├── ops_client.py        # /ops/* API client + script runner
│   └── report_parser.py     # Parse mini reports & extract metrics
├── policies/
│   └── decision.py          # Pass/Edge/Fail rules
├── plan/
│   └── plan_combo.yaml      # Default experiment config
├── prompts/
│   └── system.md            # LLM template (future use)
├── state/
│   └── history.jsonl        # Append-only run history
└── tests/
    └── test_smoke.py        # Smoke tests (3 numbers + length check)
```

## API Endpoints Used
- `GET /api/lab/config` - Health check (Redis, Qdrant)
- `GET /api/lab/report?mini=1` - Fetch metrics (ΔP95, ΔQPS, Err%)
- `POST /api/flags` - Apply control/routing flags
- Script: `./scripts/run_lab_headless.sh combo --with-load ...`

## Output Format
**reports/LABOPS_AGENT_SUMMARY.txt** (≤60 lines):
```
==============================
LABOPS AGENT V1 - EXECUTION SUMMARY
==============================

INPUTS
- QPS: 10.0, Window: 120s, Rounds: 2
- Flow: aimd, Target P95: 1200ms
- Routing: rules, TopK Threshold: 32

RESULTS
- ΔP95: -12.5%
- ΔQPS: -5.2%
- Error Rate: 0.50%
- AB Imbalance: 4.5%

VERDICT
- Decision: PASS
- Reason: P95 improved by 12.5% (≥10%)
- Flags Applied: YES

NEXT STEP
- Monitor metrics for 24h

ROLLBACK
curl -X POST http://localhost:8011/ops/flags \
  -H 'Content-Type: application/json' \
  -d '{"control": {...}, "routing": {...}}'
```

## Testing
```bash
# Run smoke tests
python3 agents/labops/tests/test_smoke.py

# Tests verify:
# ✓ Three key numbers exist (ΔP95, ΔQPS, Err%)
# ✓ Summary length ≤ 60 lines
# ✓ Decision logic (pass/edge/fail)
```

## Dependencies
- **Required**: Python 3.7+, PyYAML
- **Optional**: requests (falls back to urllib)
- **System**: bash, curl, jq (for scripts)

Install:
```bash
pip install PyYAML requests
```

## Constraints
- **No heavy deps**: Pure Python stdlib + requests/httpx
- **Deterministic seed**: Reproducible experiments
- **Code limit**: ~300 LOC total
- **AB balance**: Warn when imbalance > 5%
- **Budget enforcement**: Respect time limits

## Safety Features
1. **Health gate**: Block on unhealthy deps
2. **Dry-run mode**: Test without execution
3. **Rollback ready**: Always provide undo command
4. **Append-only history**: Audit trail preserved
5. **Early stop signals**: Surface in summary

## Future Extensions (Out of Scope for V1)
- Multi-combo grid search
- Bayesian optimization
- LLM-based analysis
- Web UI integration
- Resume from checkpoint

## Troubleshooting

### Agent fails at health gate
```bash
# Check dependencies
curl http://localhost:8011/api/lab/config

# Expected: {"ok": true, "health": {"redis": {"ok": true}, "qdrant": {"ok": true}}}
```

### No report generated
```bash
# Check if experiment ran
ls -lh reports/LAB_COMBO_REPORT_MINI.txt

# Manually fetch report
curl http://localhost:8011/ops/lab/report?mini=1
```

### Script timeout
```bash
# Increase time budget in config
time_budget: 600  # 10 minutes
```

## Contributing
- Add new decision policies in `policies/`
- Extend report parsers in `tools/report_parser.py`
- Add tests in `tests/test_*.py`

---

**Version**: 1.0.0  
**Author**: LabOps Team  
**Last Updated**: 2025-10-18

