# Offline Ops Copilot Agent Evaluation

## Run Information

- **Date/Time**: 2025-11-24 17:39:50 UTC
- **Samples**: 1000
- **Random Seed**: 42
- **Mode**: full_agent
- **LLM Generation**: Disabled (rule-based health check + strategy lab only)

## Overall Statistics

- **Total Samples**: 1000
- **Success Count**: 1000
- **Error Count**: 0 (0.0%)
- **Runtime**: 0.10 seconds

## Health Band Distribution

| Band | Count | Percentage |
|------|-------|------------|
| healthy | 67 | 6.7% |
| warning | 200 | 20.0% |
| degraded | 323 | 32.3% |
| critical | 410 | 41.0% |

## Guardrail Statistics

- **Hard Blocks**: 769 (76.9% of successful samples)
- **Soft Warnings**: 523 (52.3% of successful samples)
- **Neither**: 67 (6.7%)

## Strategy Lab Improvement

- **Total Cases with Strategy Lab**: 1000
- **Cases with At Least One Improved Scenario**: 813 (81.3%)
- **Average Change in Score for Improved Scenarios**: 21.02 points

### Improvement Rate by Baseline Band

| Baseline Band | Improved Cases | Total Cases | Improvement Rate |
|---------------|----------------|-------------|------------------|
| healthy | 0 | 67 | 0.0% |
| warning | 121 | 200 | 60.5% |
| degraded | 303 | 323 | 93.8% |
| critical | 389 | 410 | 94.9% |

## Interpretation

- Most synthetic snapshots are deliberately skewed towards degraded/critical states to stress-test guardrails and strategy lab improvements.
- Hard blocks trigger correctly when critical thresholds are exceeded (e.g., error rate ≥ 5%, disk usage ≥ 90%, CPU ≥ 90%).
- Strategy Lab produces at least one better configuration scenario for a significant percentage of degraded/critical cases.
- This offline evaluation focuses on rule-based logic only (no LLM calls), ensuring deterministic and reproducible results.
- The evaluation demonstrates the core health check and strategy lab functionality before integrating LLM-based explanations.
