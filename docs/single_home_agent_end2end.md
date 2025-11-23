# Single Home Mortgage Agent · End-to-End Demo Guide

## Overview

The Single Home Mortgage Agent is a Zillow-style AI assistant that evaluates whether a specific home is affordable for a borrower, suggests safer alternatives when needed, and explains its reasoning in plain language. It combines rule-based underwriting logic, a distilled ML model for approval scoring, and a LangGraph workflow that orchestrates stress checks, risk assessment, safety upgrades, mortgage program searches, and what-if scenario analysis.

**Key Capabilities:**

- **Natural-language entry**: Start with "I make $150k/year and want a $750k home in 90803 with 20% down."
- **Rules + ML ApprovalScore**: Combines classic underwriting-style rules with a distilled ML model (logistic regression) for smoother probability estimates.
- **LangGraph workflow**: Orchestrates stress check, risk assessment, safer homes, programs, and strategy lab with conditional routing based on risk level.
- **LLM explanation**: Turns all structured outputs into borrower-friendly narrative and actionable recommendations.

---

## End-to-End Flow (from user to Mortgage Agent)

### 1. User Interaction

Users can interact with the agent in two ways:

- **Natural language conversation**: Type a description into "Talk to the agent (English only)" on the right-hand panel.
- **Form-based entry**: Use Demo Presets or fill the form directly on the left-hand side.

The left-hand form is always the source of truth for the current plan. The NL assistant can populate the form, but the form values are what get sent to the agent.

### 2. NLU + Multi-turn Assistant (Optional Path)

**Module**: `nl_to_stress_request.py` + `/api/mortgage-agent/nl-to-stress-request`

When a user types natural language:

1. **LLM extraction**: Uses OpenAI `gpt-4o-mini` to extract mortgage fields (income, home price, ZIP, down payment, etc.) from free text.
2. **Unit conversion**: Python code handles numeric conversions (k/million, annual vs monthly, percent) automatically.
3. **Partial request**: Returns a `partial_request` merged into the form, plus `missing_required_fields`.
4. **Multi-turn chat**: The NL assistant runs as a multi-turn conversation:
   - It asks follow-up questions if required fields are missing.
   - Once it has enough info, it enables "Run Mortgage Agent on this plan".

**Required fields**: `income_monthly`, `list_price` (minimum to run a stress check).

### 3. Full Mortgage Agent Run

When the user clicks **"Run Mortgage Agent on this plan"** (or the secondary stress-only button):

- The current form state is sent as a `StressCheckRequest`.
- The backend runs the LangGraph workflow (see Section 4).

**Core components executed:**

- **Rule-based stress check**: Computes DTI, payment breakdown, `stress_band` (loose/ok/tight/high_risk).
- **ML ApprovalScore**: Logistic regression model distilled from rules (optional, enabled via `USE_ML_APPROVAL_SCORE`).
- **RiskAssessment guardrails**: Risk flags, `hard_block`/`soft_warning` based on payment-to-income ratios and cash flow.
- **Safety Upgrade**: Searches for safer homes in the same ZIP if the current plan is tight/high_risk.
- **Mortgage Programs (MCP)**: External programs that can help (e.g., first-time buyer, VA, high DTI) via MCP server.
- **Strategy Lab**: What-if scenarios (lower price, higher down payment, different risk preference).

### 4. LangGraph Workflow

**File**: `graphs/single_home_graph.py`

The workflow orchestrates the steps with conditional routing:

**Nodes:**
- `stress_check`: Core stress check tool (always runs first).
- `safety_upgrade`: Searches for safer homes (only if tight/high_risk).
- `mortgage_programs`: Calls MCP server for assistance programs (only if tight/high_risk).
- `strategy_lab`: What-if scenario analysis (always runs).
- `llm_explanation`: Generates borrower narrative and actions (always runs last).

**Conditional routing:**

- **Loose/OK path**: `stress_check` → `strategy_lab` → `llm_explanation` → END
- **Tight/high_risk path**: `stress_check` → `safety_upgrade` → `mortgage_programs` → `strategy_lab` → `llm_explanation` → END

**State tracking**: The workflow state includes `stress_result`, `safety_upgrade`, `mortgage_programs`, `strategy_lab`, `borrower_narrative`, `risk_assessment`, `errors`, and `agent_steps`.

**Frontend visualization**: The "Stage Timeline · LangGraph Workflow" component shows each stage as completed / skipped / not_run.

### 5. LLM Explanation Layer

**Function**: `_generate_single_home_narrative()` in `mortgage_agent_runtime.py`

Takes all structured outputs and produces:

- **Borrower Narrative**: 2–3 short paragraphs explaining the affordability assessment, risk factors, and context.
- **Recommended Actions**: Up to 3 concise suggestions (e.g., "Consider a lower-priced home", "Explore first-time buyer programs", "Increase down payment to 25%").

This powers the "AI Explanation / Next steps" panel in the UI.

### 6. Frontend Dashboard

**File**: `ui/src/pages/SingleHomeStressPage.tsx`

The Single Home Stress page displays:

- **Left column (30-35% width)**: Input form + presets + NL assistant card.
- **Right column (65-70% width)**: Results dashboard:
  - **Wallet vs Target home**: Side-by-side comparison cards.
  - **Stress band bar**: Horizontal 3-segment bar (Loose/OK/Tight) with DTI ratio.
  - **ApprovalScore**: Score (0-100) and bucket (likely/borderline/unlikely) with reasons.
  - **Risk flags**: List of risk indicators (e.g., `tight_band`, `payment_above_safe_range`, `high_dti`).
  - **Strategy Lab scenarios**: Alternative plans with improved DTI.
  - **Mortgage assistance programs**: Top 2-3 programs from MCP server.
  - **LangGraph Stage Timeline**: Visual workflow execution status.
  - **Agent Steps**: Collapsible section showing AI reasoning steps with timestamps.
  - **AI Explanation**: Borrower narrative and recommended actions.

**Badge indicator**: A small badge shows "Started from conversation" or "Started from form" to indicate how the last run was triggered.

---

## Demo Scenarios (for interviews)

### Scenario 1 – SoCal High Price (Feels Tight)

**Story:** High income ($180k/year) but very expensive home ($1.1M) in coastal SoCal. Payment exceeds safe range by >20%, so classified as `high_risk` even though DTI is in tight range. Should trigger safety upgrade, mortgage programs, and strategy lab.

**How to run:**

1. Use the "SoCal High Price, Feels Tight" preset (or type similar numbers into the form).
2. Optionally start from a conversation:
   - "We make about $15k per month and are looking at a $1.1M home in 92648 with 20% down."
3. Click **Run Mortgage Agent on this plan**.

**What to highlight:**

- **Stress band**: Typically `high_risk` (payment exceeds safe_band by >20%).
- **ApprovalScore**: Mid-range (40-60), with reasons like `high_dti`, `expensive_home`, `payment_above_safe_range`.
- **Risk flags**: Show `tight_band`, `payment_above_safe_range`, `hard_block=true`.
- **Safety Upgrade**: 2–3 cheaper homes in the same ZIP (92648) with better DTI (e.g., $900k-$950k range).
- **Mortgage Programs**: High-DTI / assistance programs that appear because the case is borderline (e.g., "California First-Time Homebuyer Assistance").
- **Strategy Lab**: Scenarios where lowering price to $950k or increasing down payment to 25% improves DTI to `ok` band.
- **Stage Timeline**: All stages run, including Safety Upgrade and Programs.

### Scenario 2 – Texas Starter Home (Comfortable)

**Story:** Moderate income ($108k/year), modest home ($380k) in Texas. DTI below 36% threshold, classified as `loose`. Strong ApprovalScore, minimal risk flags.

**How to run:**

1. Use the "Texas Starter Home, Comfortable" preset.
2. Click **Run Mortgage Agent on this plan**.

**What to highlight:**

- **Stress band**: `loose` (DTI ~32.5%, below 36% threshold).
- **ApprovalScore**: High (70-85), bucket `likely`, reasons like `low_dti`, `reasonable_payment`.
- **Risk flags**: Minimal or none (no `hard_block`, no `soft_warning`).
- **Safety Upgrade**: Skipped (not needed for loose/ok cases).
- **Mortgage Programs**: Skipped (no assistance needed).
- **Strategy Lab**: Runs as "confirmation" rather than rescue—shows scenarios are already comfortable.
- **Stage Timeline**: Only `stress_check`, `strategy_lab`, and `llm_explanation` run (safety_upgrade and mortgage_programs are skipped).

### Scenario 3 – Extreme High Risk (Hard Block)

**Story:** Very low income ($54k/year) vs very high price ($850k), almost no down payment (5%). DTI >80%, triggers `hard_block=true`.

**How to run:**

1. Use the "Extreme High Risk, Hard Block" preset.
2. Click **Run Mortgage Agent on this plan**.

**What to highlight:**

- **Stress band**: `high_risk`.
- **ApprovalScore**: Very low (0-30), bucket `unlikely`, reasons like `very_high_dti`, `low_down_payment`, `payment_way_above_safe_range`.
- **Risk flags**: `hard_block=true`, `very_high_dti`, `low_down_payment`, `payment_way_above_safe_range`.
- **Safety Upgrade**: 2–3 much cheaper homes ($400k-$500k range) that bring DTI down to `tight` or `ok`.
- **Mortgage Programs**: Multiple assistance programs (first-time buyer, low-income, high-DTI accommodation).
- **Strategy Lab**: Scenarios show dramatic improvements needed (e.g., price down to $400k, down payment up to 20%).
- **LLM Explanation**: Strong warning tone in narrative, emphasizes high risk and potential inability to get approval.
- **Stage Timeline**: All stages run.

### Scenario 4 – Borderline with Aid / Multi-turn NL Demo (Optional)

**Story:** Borderline DTI/LTV, moderate income. Use NL assistant to incrementally fill the form, then run the full agent.

**How to run:**

1. Start with an incomplete query in the NL assistant:
   - "I'm looking at a $550k home in 92705 with 15% down."
2. The assistant will ask: "What's your monthly income?"
3. Reply: "About $8k per month."
4. The assistant will ask: "Any other monthly debts?"
5. Reply: "Around $500 for car and credit cards."
6. Once the form is populated, click **Run Mortgage Agent on this plan**.

**What to highlight:**

- **Multi-turn NLU**: Conversation history is maintained, assistant asks follow-up questions.
- **Form population**: Watch the left-hand form populate as fields are extracted.
- **Conversation-origin badge**: Badge shows "Started from conversation".
- **Stress band**: Typically `high_risk` (payment exceeds safe_band by >20%).
- **Mortgage Programs**: Should find at least one program (e.g., "California First-Time Homebuyer Assistance" for ZIP 92705).
- **Stage Timeline**: All stages run.

---

## Architecture & Components

### Stress Check & Local Costs

**Files:**
- `mortgage_agent_runtime.py`: `run_stress_check()` function
- `local_cost_factors.py`: Location-based cost factors (property tax, insurance, HOA estimates)
- `mortgage_math.py`: Core mortgage calculations (DTI, monthly payment, affordability)

**What it does:**
- Computes DTI ratio, monthly payment breakdown (principal + interest + taxes + insurance + HOA), cash flow.
- Determines `stress_band` based on DTI thresholds: `<36%` = loose, `36-43%` = ok, `43-80%` = tight, `>80%` = high_risk.
- Uses local cost factors to estimate property tax and insurance based on ZIP code and state.

**Smoke tests:**
- `experiments/stress_check_smoke.py`
- `experiments/single_home_agent_smoke.py`

### ApprovalScore: From Rules to ML

**Files:**
- `approval/hybrid_score.py`: `combine_rule_and_ml()` function
- `approval/ml_approval_score.py`: ML model loader and predictor
- `experiments/train_approval_score_ml.py`: Training script
- `experiments/eval_approval_score_ml.py`: Evaluation script
- `docs/approval_score_ml.md`: Full documentation

**Rule-based component:**
- `compute_rule_based_approval_score()` in `mortgage_agent_runtime.py`
- Computes score (0-100) and bucket (likely/borderline/unlikely) based on DTI, LTV, payment-to-income, cash flow.

**ML component:**
- Logistic regression model distilled from rules (trained on synthetic data).
- Model file: `ml_models/approval_score_logreg_v1.joblib`
- Performance: AUC ≈ 0.967 vs teacher, accuracy ≈ 89.8%, monotonicity violation rate ≈ 0%.

**Hybrid logic:**
- Rules as primary (70% weight for likely/unlikely, 50% for borderline).
- ML adjusts scores and buckets, adds `ml_adjusted` reason if bucket changes.
- Fallback: If ML unavailable, uses pure rule-based score.

**Offline training & eval:**
- `experiments/gen_approval_distillation_data.py`: Synthetic data generation
- `experiments/train_approval_score_ml.py`: Model training
- `experiments/eval_approval_score_ml.py`: Performance evaluation

### RiskAssessment Guardrails

**File**: `risk_assessment.py`

**What it does:**
- Assesses risk flags: `tight_band`, `payment_above_safe_range`, `high_dti`, `low_down_payment`, `very_high_dti`, etc.
- Determines `hard_block` (true if payment exceeds safe range by >20% or DTI >80%).
- Determines `soft_warning` (true if payment exceeds safe range by 10-20% or DTI in tight range).
- Used across the pipeline to trigger safety upgrades and program searches.

### Safety Upgrade & Safer Homes

**Files:**
- `mortgage_agent_runtime.py`: `run_safety_upgrade_flow()`, `search_safer_homes_for_case()`
- `tools/property_tool.py`: `search_listings_for_zip()`

**What it does:**
- Searches for cheaper homes in the same ZIP code (mocked listings per ZIP).
- Re-runs stress checks for each candidate home.
- Returns top 2-3 safer homes with improved DTI and stress bands.
- Only runs if `stress_band` is `tight` or `high_risk`.

**Smoke tests:**
- `experiments/safety_upgrade_smoke.py`
- `experiments/safer_homes_smoke.py`

### Mortgage Programs (MCP Server)

**Files:**
- `mcp/mortgage_programs_server/server.py`: FastMCP server with `search_mortgage_programs` tool
- `mcp/mortgage_programs_server/mortgage_programs.json`: Sample programs database
- `graphs/single_home_graph.py`: `_mortgage_programs_node()` integrates MCP tool

**What it does:**
- FastMCP server exposes `search_mortgage_programs` tool (ZIP code, state, profile tags, current DTI).
- Returns up to 5 matching programs (first-time buyer, VA, low-income, high-DTI, senior programs).
- Integrated into LangGraph as an external tool node.
- Only runs if `stress_band` is `tight` or `high_risk`.

**Smoke test:**
- `mcp/mortgage_programs_server/smoke_test.py`

### Strategy Lab

**File**: `mortgage_agent_runtime.py`: `run_strategy_lab()`

**What it does:**
- Constructs what-if strategies:
  - Lower price (-10%, -20%)
  - Higher down payment (+5%, +10%)
  - More conservative risk preference
- Re-runs stress checks for each scenario.
- Results visualized as alternative scenarios with improved DTI and stress bands.
- Always runs (on both loose/ok and tight/high_risk paths).

**Smoke test:**
- `experiments/single_home_graph_scenarios_smoke.py`

### LangGraph Workflow

**File**: `graphs/single_home_graph.py`

**State schema**: `SingleHomeGraphState` includes:
- Input: `request`, `stress_request`, `user_text`, `partial_request`
- Intermediate: `stress_result`, `safety_upgrade`, `mortgage_programs`, `strategy_lab`
- Output: `borrower_narrative`, `recommended_actions`, `llm_usage`
- Metadata: `agent_steps`, `errors`

**Nodes:**
- `stress_check`: Entry point, always runs first.
- `safety_upgrade`: Conditional (only if tight/high_risk).
- `mortgage_programs`: Conditional (only if tight/high_risk, after safety_upgrade).
- `strategy_lab`: Always runs (on both paths).
- `llm_explanation`: Always runs last.

**Routing:**
- `_need_safety_upgrade_router()`: Routes to `need_upgrade` if `stress_band` is `tight` or `high_risk`, else `skip_upgrade`.

**Public API:**
- `run_single_home_graph(request: SingleHomeAgentRequest) -> SingleHomeAgentResponse`

**Smoke tests:**
- `experiments/single_home_graph_smoke.py`
- `experiments/single_home_graph_scenarios_smoke.py`

### NLU / Natural-Language Assistant

**Files:**
- `nl_to_stress_request.py`: Core NLU extraction and unit conversion
- `graphs/nl_entry_graph.py`: Multi-turn conversation graph (if exists)
- `/api/mortgage-agent/nl-to-stress-request`: API endpoint

**What it does:**
- Uses OpenAI `gpt-4o-mini` to extract fields from free text (JSON response format).
- Python code handles unit conversions (k/million, annual/monthly, percent).
- Detects missing required fields and returns them for follow-up questions.
- Multi-turn chat with conversation history (last 6 messages, 3 turns).

**Smoke tests:**
- `experiments/nl_to_stress_request_smoke.py`
- `experiments/nl_entry_graph_smoke.py`

### Frontend UI

**File**: `ui/src/pages/SingleHomeStressPage.tsx`

**Layout:**
- Left column (30-35%): Form + presets + NL assistant card.
- Right column (65-70%): Results dashboard with all components listed in Section 2.6.

**Key components:**
- Form inputs: Monthly income, other debts, home price, down payment %, ZIP, state, HOA, risk preference.
- Demo presets: 4 scenarios (SoCal tight, Texas comfortable, extreme high risk, borderline with aid).
- NL assistant: Chat interface with conversation history.
- Results dashboard: Wallet vs home, stress band, ApprovalScore, risk flags, Strategy Lab, Programs, AI explanation, Stage Timeline, Agent Steps.

**API integration:**
- `/api/mortgage-agent/nl-to-stress-request`: NLU extraction
- `/api/mortgage-agent/single-home`: Full agent run

---

## Offline Evaluation & Metrics

### ApprovalScore Distillation

**Data generation:**
- `experiments/gen_approval_distillation_data.py`: Generates synthetic borrower/home combinations.
- ~50% focused around threshold regions (DTI 35–55%, LTV 70–100%).
- ~50% across broader range for generalization.
- Calls `run_stress_check` to get rule-based teacher labels.

**Model training:**
- `experiments/train_approval_score_ml.py`: Trains logistic regression model.
- Output: `ml_models/approval_score_logreg_v1.joblib` (includes model, scaler, encoders, feature names).

**Performance metrics:**
- **AUC vs teacher**: ≈ 0.967 (meets ≥ 0.85 target).
- **Accuracy vs teacher**: ≈ 89.8%.
- **Monotonicity checks**: Violation rate ≈ 0% for DTI & LTV (higher DTI/LTV never increases approval probability).

**Evaluation script:**
- `experiments/eval_approval_score_ml.py`: Evaluates model vs teacher, checks monotonicity, generates confusion matrices.

### Strategy Lab / Agent Evaluation

**Smoke tests:**
- `experiments/single_home_graph_scenarios_smoke.py`: Runs 4 demo scenarios, validates node execution, checks stress bands and risk flags.

**Metrics measured:**
- Distribution of stress bands (loose/ok/tight/high_risk) across scenarios.
- ApprovalScore distribution by band.
- Fraction of cases where Strategy Lab finds a safer scenario.
- Node execution paths (which nodes ran vs expected).

**Purpose:**
- Keep Agent behavior stable across refactors.
- Compare strategy/ML variants (rule-only vs hybrid vs pure-ML).
- Regression testing for interview demos.

---

## Running the Demo Locally

### Backend

**Start the API server:**

```bash
# Option 1: Using start-agent.sh (recommended)
./scripts/start-agent.sh

# Option 2: Manual start
cd services/fiqa_api
python -m uvicorn app_main:app --host 0.0.0.0 --port 8001 --reload
```

**Environment variables required:**
- `OPENAI_API_KEY`: For LLM generation (NLU and explanations)
- `USE_ML_APPROVAL_SCORE`: Set to `true` to enable ML-based ApprovalScore (default: `false`)
- `LLM_GENERATION_ENABLED`: Set to `true` to enable LLM explanations (default: `false`)

**Smoke tests:**

```bash
# Single home graph scenarios (4 demo scenarios)
python experiments/single_home_graph_scenarios_smoke.py

# NLU extraction
python experiments/nl_to_stress_request_smoke.py

# Full agent smoke test
python experiments/single_home_agent_smoke.py
```

### Frontend

**Start the dev server:**

```bash
# Option 1: Using start-agent.sh (starts both backend and frontend)
./scripts/start-agent.sh

# Option 2: Manual start
cd ui
npm install  # First time only
npm run dev  # Starts on http://localhost:5173
```

**Open the demo:**
- URL: `http://localhost:5173/workbench/single-home-stress`
- Or navigate from the main app to "Single Home Stress" page.

**Recommended presets to click:**
1. **"SoCal High Price, Feels Tight"**: Shows full workflow with safety upgrade and programs.
2. **"Texas Starter Home, Comfortable"**: Shows comfortable path (skips safety upgrade).
3. **"Extreme High Risk, Hard Block"**: Shows hard block and all rescue paths.

### Notes

- **MCP Server**: The mortgage programs MCP server is integrated directly into the LangGraph workflow (no separate server process needed in current implementation).
- **Mock data**: Property listings and mortgage programs use mocked data (not real APIs).
- **LLM costs**: Each agent run uses ~1-2 LLM calls (NLU extraction + explanation generation). Costs are logged in `llm_usage` field.

---

## Deploying the Backend to GCP Cloud Run

This section explains how to deploy the backend API to GCP Cloud Run for production use. The frontend can then be deployed separately (e.g., to Vercel/Netlify) and configured to call the Cloud Run API.

### Prerequisites

- **gcloud CLI** installed and authenticated:
  ```bash
  gcloud auth login
  gcloud config set project YOUR_PROJECT_ID
  ```
- **Docker** installed and running locally
- **GCP project** with Cloud Run API enabled
- **Billing** enabled on your GCP project

### Quick Deployment Steps

1. **Set your GCP project and region:**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   gcloud config set run/region us-west1  # or your preferred region
   ```

2. **Build and deploy:**
   ```bash
   cd services/fiqa_api  # or repo root where Dockerfile is
   ../../scripts/deploy_cloud_run.sh
   ```

   The script will:
   - Build the Docker image using `Dockerfile.cloudrun`
   - Push it to GCP Container Registry (or Artifact Registry)
   - Deploy to Cloud Run with default settings

3. **Configure environment variables in Cloud Run console:**
   
   Go to the [Cloud Run console](https://console.cloud.google.com/run) and edit your service to set:
   
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `USE_ML_APPROVAL_SCORE=true` - Enable ML-based approval scoring
   - `LLM_GENERATION_ENABLED=true` - Enable LLM explanations
   - `ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app` - Frontend URL(s), comma-separated
   
   Or use gcloud CLI:
   ```bash
   gcloud run services update mortgage-agent-api \
     --region us-west1 \
     --update-env-vars \
       OPENAI_API_KEY=your-key,\
       USE_ML_APPROVAL_SCORE=true,\
       LLM_GENERATION_ENABLED=true,\
       ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
   ```

4. **Get the deployed URL:**
   ```bash
   gcloud run services describe mortgage-agent-api \
     --region us-west1 \
     --format 'value(status.url)'
   ```

5. **Test the endpoint:**
   ```bash
   CLOUD_RUN_URL=$(gcloud run services describe mortgage-agent-api \
     --region us-west1 \
     --format 'value(status.url)')
   
   curl "$CLOUD_RUN_URL/health"
   curl "$CLOUD_RUN_URL/api/mortgage-agent/single-home" \
     -H "Content-Type: application/json" \
     -d '{"income_monthly": 8000, "list_price": 500000, "zip_code": "90210", "down_payment_pct": 20}'
   ```

### Frontend Configuration

After deploying the backend, configure your frontend to use the Cloud Run URL:

```bash
# In your frontend .env or build config
VITE_API_BASE_URL=https://mortgage-agent-api-xxxxx-uw.a.run.app
```

### Customizing the Deployment

The deployment script (`scripts/deploy_cloud_run.sh`) supports environment variables for customization:

```bash
export PROJECT_ID=your-project-id
export SERVICE_NAME=your-service-name
export REGION=us-west1
export IMAGE_NAME=gcr.io/$PROJECT_ID/$SERVICE_NAME

./scripts/deploy_cloud_run.sh
```

### CORS Configuration

The backend supports CORS via the `ALLOWED_ORIGINS` environment variable:

- **Local dev**: `ALLOWED_ORIGINS="*"` (allows all origins)
- **Production**: `ALLOWED_ORIGINS="https://your-frontend.vercel.app"` (specific origins)

Multiple origins can be comma-separated:
```bash
ALLOWED_ORIGINS="https://app1.vercel.app,https://app2.netlify.app"
```

### Notes

- The Dockerfile (`services/fiqa_api/Dockerfile.cloudrun`) is optimized for Cloud Run:
  - Uses port 8080 (Cloud Run default)
  - Stateless container design
  - Minimal dependencies for production
- Local development is unaffected: existing `uvicorn` commands and scripts continue to work.
- The backend automatically respects the `PORT` environment variable set by Cloud Run.

## Deploying the Frontend

See [deploy_frontend_vercel.md](./deploy_frontend_vercel.md) for instructions on deploying the Single Home Stress UI to Vercel and pointing it at the Cloud Run backend.

---

## Summary

The Single Home Mortgage Agent demonstrates a production-ready AI system that combines:

- **Agentic workflows** (LangGraph with conditional routing)
- **Classical ML** (logistic regression for approval scoring)
- **GenAI explanations** (LLM-powered borrower narratives)
- **External tools** (MCP server for mortgage programs)
- **Offline evaluation** (synthetic data generation, model training, regression tests)

The system is designed for interview demos, showing how different borrower/home profiles trigger different workflow paths, and how the agent provides actionable recommendations with clear explanations.

