# AutoTuner Demo Pack System

A comprehensive orchestration system for running and packaging AutoTuner demonstrations with scenario-based A/B testing, guardrails validation, and professional HTML reporting.

## Overview

The Demo Pack system converts the SLA AutoTuner into a demo-ready product by providing:

- **Scenario Presets**: Pre-configured A/B/C scenarios with different initial parameters
- **Orchestration CLI**: Command-line interface for running experiments
- **Packaging & Indexing**: Automated generation of HTML+JSON+CSV bundles
- **Guardrails**: PASS/FAIL validation with detailed criteria
- **Professional Reports**: Modern, responsive HTML reports with interactive tabs

## Quick Start

### Run a Quick Demo (10 minutes)

```bash
# Run all scenarios in simulation mode
python scripts/run_demo_pack.py --mode sim --scenario ALL --duration-sec 600 --bucket-sec 10 --qps 12 --pack-out demo_pack/$(date +%Y%m%d_%H%M)

# Run a specific scenario
python scripts/run_demo_pack.py --mode sim --scenario A --duration-sec 600 --bucket-sec 10 --qps 12 --pack-out demo_pack/$(date +%Y%m%d_%H%M) --notes "Demo for stakeholders"
```

### View Results

```bash
# Open the generated report in browser
open demo_pack/20251006_0935/index.html
```

### Run a Comprehensive Demo (1-2 hours)

```bash
# Long-running demo with all scenarios
python scripts/run_demo_pack.py --mode sim --scenario ALL --duration-sec 3600 --bucket-sec 10 --qps 12 --pack-out demo_pack/$(date +%Y%m%d_%H%M)

# For live experiments on ANYWARE box
python scripts/run_demo_pack.py --mode live --scenario ALL --duration-sec 7200 --bucket-sec 10 --qps 12 --pack-out demo_pack/$(date +%Y%m%d_%H%M)
```

## Components

### 1. Orchestrator (`scripts/run_demo_pack.py`)

Main CLI tool for running demo experiments.

**Key Features:**
- Mode selection: `--mode {sim,live}`
- Scenario selection: `--scenario {A,B,C,ALL}`
- Timing control: `--duration-sec`, `--bucket-sec`, `--qps`
- Output control: `--pack-out`, `--csv-out`
- Reproducibility: `--seed`, `--perm-trials`

**Example Usage:**
```bash
python scripts/run_demo_pack.py \
  --mode sim \
  --scenario ALL \
  --duration-sec 1200 \
  --bucket-sec 10 \
  --qps 12 \
  --pack-out demo_pack/20241201_1430 \
  --notes "Quarterly review demo"
```

### 2. Scenario Presets (`configs/demo_pack_scenarios.yaml`)

Pre-configured scenarios for different demonstration purposes:

**Scenario A: High-Latency, Low-Recall**
- Initial params: `ef_search=256, candidate_k=2000, rerank_k=100, threshold_T=0.8`
- Best for: Showing latency optimization capabilities
- Expected: Significant latency reduction with multi-knob tuning

**Scenario B: High-Recall, High-Latency**
- Initial params: `ef_search=512, candidate_k=3000, rerank_k=150, threshold_T=0.3`
- Best for: Multi-objective optimization demonstrations
- Expected: Balanced improvements in both metrics

**Scenario C: Low-Latency, Low-Recall**
- Initial params: `ef_search=64, candidate_k=500, rerank_k=20, threshold_T=0.9`
- Best for: Recall improvement demonstrations
- Expected: Significant recall improvement with acceptable latency trade-off

### 3. Guardrails System (`modules/demo_pack/guardrails.py`)

Comprehensive validation system with PASS/FAIL criteria:

**Pass Criteria:**
- `ΔP95 > 0`: Multi-knob tuning improves latency
- `p < 0.05`: Results are statistically significant
- `ΔRecall ≥ -0.01`: Recall doesn't drop too much
- `Safety ≥ 0.99`: Safety mechanisms working properly
- `Apply Rate ≥ 0.95`: Tuning actions are being applied

**Warning Conditions:**
- Duration < 300s: Too short for reliable results
- Buckets < 10: Insufficient statistical power
- Low QPS: May not show responsive tuning behavior

### 4. Enhanced Aggregator (`scripts/aggregate_observed.py`)

Extended with demo pack functionality:

```bash
# Generate simulator A/B report
python scripts/aggregate_observed.py --simulator-ab single_dir multi_dir

# Generate demo pack index
python scripts/aggregate_observed.py --demo-pack demo_pack/20241201_1430
```

### 5. Professional Assets (`assets/demo/`)

Modern CSS and SVG icons for professional presentation:
- `demo-pack.css`: Responsive design with modern styling
- `icons.svg`: Comprehensive icon set for metrics and actions
- Print-friendly styles and mobile optimization

## Output Structure

Each demo pack generates a structured output directory:

```
demo_pack/20251006_0935/
├── index.html                 # Main dashboard with tabs A/B/C
├── metadata.json              # Run metadata, summary, and reproducibility info
├── scenario_A/
│   ├── one_pager.html         # Detailed A/B report
│   ├── one_pager.json         # JSON data with metrics
│   └── one_pager.csv          # Per-bucket CSV data
├── scenario_B/                # Same structure as A
└── scenario_C/                # Same structure as A
```

## Testing

Comprehensive test suite with fast simulation tests:

```bash
# Run fast unit tests (< 1s)
python tests/test_demo_pack.py --fast

# Run integration tests (≤ 20s with simulation)
python tests/test_demo_pack.py --integration

# Run all tests
python tests/test_demo_pack.py --all
```

**Test Coverage:**
- Scenario preset validation
- Guardrails logic verification
- Fast simulation pack generation
- HTML template generation
- Pass/Fail criteria evaluation

## Usage Examples

### 1. Stakeholder Demo (Quick)

```bash
python scripts/run_demo_pack.py \
  --mode sim \
  --scenario A \
  --duration-sec 600 \
  --notes "Q4 stakeholder review"
```

**Result:** 10-minute demo showing latency optimization with clear PASS/FAIL results.

### 2. Technical Deep Dive

```bash
python scripts/run_demo_pack.py \
  --mode sim \
  --scenario ALL \
  --duration-sec 3600 \
  --bucket-sec 5 \
  --qps 15 \
  --notes "Engineering team deep dive"
```

**Result:** Comprehensive 1-hour analysis across all scenarios with detailed metrics.

### 3. Custom Configuration

```bash
# Custom guardrails
python scripts/run_demo_pack.py \
  --mode sim \
  --scenario B \
  --duration-sec 1800 \
  --notes "Custom SLO validation"
```

## Integration with Existing System

The demo pack system integrates seamlessly with existing AutoTuner components:

- **Reuses**: `run_brain_ab_experiment.py` for A/B experiments
- **Extends**: `aggregate_observed.py` for report generation
- **Preserves**: All existing tuner logic without modification
- **Adds**: Demo-specific orchestration and packaging

## Performance Characteristics

- **Fast Simulation**: 3×A/B runs of 120s complete in < 20s total
- **Live Experiments**: Scale to 1-2h runs on ANYWARE box
- **Memory Efficient**: Streaming data processing
- **Reproducible**: Git SHA, seed, and parameter tracking

## Troubleshooting

### Common Issues

1. **Simulation Too Slow**
   - Reduce `--duration-sec` for testing
   - Use `--mode sim` instead of `--mode live`

2. **Guardrails Failing**
   - Check warning messages for recommendations
   - Increase experiment duration or QPS
   - Review scenario preset parameters

3. **Missing Assets**
   - Ensure `assets/demo/` directory exists
   - Check CSS and icon file paths in HTML

### Debug Mode

```bash
# Verbose output
python scripts/run_demo_pack.py --mode sim --scenario A --duration-sec 120 -v

# Check generated files
ls -la demo_pack/*/
```

## Future Enhancements

- **Live Mode Integration**: Complete integration with real AutoTuner experiments
- **Advanced Scenarios**: More scenario presets for different use cases
- **Export Options**: PDF generation, PowerPoint integration
- **Real-time Monitoring**: Live experiment progress tracking
- **Custom Metrics**: User-defined guardrail criteria

## Contributing

When extending the demo pack system:

1. **Add Tests**: Include fast simulation tests for new features
2. **Update Documentation**: Keep this README current
3. **Follow Patterns**: Use existing guardrails and scenario patterns
4. **Maintain Performance**: Keep fast tests under 20s total execution

## License

Part of the SearchForge AutoTuner system. See main project license for details.
