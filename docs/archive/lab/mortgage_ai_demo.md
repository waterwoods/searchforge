# Single Home Stress Check Demo - Interview Guide

## Problem We Solve

Traditional affordability calculators only provide a binary yes/no or high-risk judgment. They don't tell users "what's next" when a home is unaffordable, leading to user drop-off. Our Single Home Stress Check combines structured financial calculations with an AI agent that explains results and suggests actionable next steps.

## High-Level Workflow

The complete flow:

1. **User picks a home** → `stress_check` tool computes monthly payment, DTI ratio, and stress band (loose/ok/tight/high_risk)

2. **If Tight/High Risk** → `safety_upgrade_flow` automatically runs:
   - (a) Searches for safer homes in the same ZIP code
   - (b) Computes DTI deltas for each candidate, or explains why the ZIP is pricey
   - (c) Builds structured upgrade suggestions

3. **SingleHomeAgent LLM** turns structured outputs into:
   - Short borrower narrative (2-3 paragraphs)
   - 1-3 actionable next steps (each under 120 characters)
   - Optional safety ∫upgrade explanati∫on

## Tools & Data We Use

### Core Tools

- **`run_stress_check`**: Computes monthly payment (P&I + tax/insurance/HOA), DTI ratio, and stress band classification
  - Input: Monthly income, debts, home price, down payment %, ZIP/state, HOA, risk preference
  - Output: `StressCheckResponse` with payment breakdown, DTI, stress_band, wallet/home snapshots

- **`search_listings_for_zip`**: Searches mock local property listings by ZIP code
  - Input: ZIP code, optional filters (price range, beds, etc.)
  - Output: List of `LocalListingSummary` objects

- **`search_safer_homes_for_case`**: Finds safer homes given a stress-check context
  - Input: Borrower profile, ZIP code, baseline stress band/DTI, target list price
  - Output: `SaferHomesResult` with candidates that improve stress band or DTI

- **`local_cost_factors`**: Estimates location-specific tax and insurance rates
  - Input: ZIP code, state
  - Output: Tax rate estimate, insurance ratio estimate, data source (ZIP override / state default / global default)

### Agent Workflow

- **`run_single_home_agent`**: Orchestrates the full workflow
  1. Calls `run_stress_check` to get baseline metrics
  2. If tight/high_risk, calls `run_safety_upgrade_flow` to search safer homes
  3. Calls LLM to generate borrower narrative and recommended actions
  4. Returns `SingleHomeAgentResponse` with stress_result, borrower_narrative, recommended_actions, and safety_upgrade

## How to Run the Demo Locally

### Backend Tests

```bash
# Stress check regression tests
python3 experiments/stress_check_regression.py

# Safer homes smoke test
python3 experiments/safer_homes_smoke.py

# Safety upgrade smoke test
python3 experiments/safety_upgrade_smoke.py

# Single-home-agent smoke test (full workflow)
python3 experiments/single_home_agent_smoke.py
```

### Frontend

```bash
cd ui
npm install
npm run dev    # then open http://localhost:3000/workbench/single-home-stress
```

### Demo Scenarios

The frontend includes preset scenarios:
- **SoCal High Price (Feels Tight)**: $12k/month income, $950k home → typically "tight" band
- **Texas Starter Home (OK)**: $6.5k/month income, $320k home → typically "ok" band
- **Borderline High Risk**: $5.5k/month income, $750k home → typically "tight" or "high_risk"

## How This Maps to the Zillow JD

This demo showcases several key capabilities mentioned in the Zillow job description:

- **Agentic workflows, planning, tool integration**: The `run_single_home_agent` orchestrates multiple tools (stress_check, safer_homes search, local_cost_factors) and uses LLM reasoning to explain results

- **Combine generative reasoning with classical ML / scoring tools**: We combine:
  - Classical calculations (DTI ratios, payment formulas, stress band thresholds)
  - LLM-based explanation and recommendation generation
  - Structured data extraction and validation

- **Use proprietary local data for decisioning**: 
  - `local_cost_factors` uses ZIP-level tax/insurance estimates (currently mock data, designed for real API integration)
  - `search_listings_for_zip` searches location-specific property listings
  - Safety upgrade suggestions are ZIP-aware

- **Structured output with validation**: All responses use Pydantic models (`StressCheckResponse`, `SingleHomeAgentResponse`, `SafetyUpgradeResult`) ensuring type safety and API contract compliance

- **End-to-end user experience**: Frontend integrates stress check, AI explanation, safety upgrade suggestions, and what-if scenarios in a single cohesive workflow

## Key Design Decisions

1. **Separation of concerns**: Financial calculations are pure Python (no LLM), explanations are LLM-generated
2. **Structured + natural language**: We return both structured metrics (DTI, stress_band) and natural language explanations
3. **Progressive enhancement**: Safety upgrade only runs when stress is tight/high_risk, reducing unnecessary computation
4. **Interview-friendly output**: Borrower narrative is constrained to 2-3 short paragraphs, actions are limited to 3 bullets under 120 characters each

