# Single Home Mortgage Agent - Architecture Analysis

## 1. Core Entrypoints

### HTTP/API Endpoint
- **File**: `services/fiqa_api/routes/mortgage_agent.py`
- **Function**: `single_home_agent_endpoint()` (line 356)
- **Path**: `POST /api/mortgage-agent/single-home-agent`
- **Description**: FastAPI route handler that accepts `SingleHomeAgentRequest` (borrower profile + home details), validates input, calls the runtime function, and returns `SingleHomeAgentResponse` with stress check results, LLM narrative, and safety upgrade suggestions.

### Main Runtime Function
- **File**: `services/fiqa_api/mortgage/mortgage_agent_runtime.py`
- **Function**: `run_single_home_agent()` (line 2739)
- **Description**: Orchestrates the single-home workflow. Controlled by `USE_LANGGRAPH_SINGLE_HOME` feature flag - if enabled, delegates to LangGraph version (`run_single_home_graph`), otherwise runs legacy sequential flow: `run_stress_check()` → `run_safety_upgrade_flow()` → `run_strategy_lab()` → `_generate_single_home_narrative()`.

### LangGraph Definition
- **File**: `services/fiqa_api/mortgage/graphs/single_home_graph.py`
- **Function**: `run_single_home_graph()` (line 430) and `_build_single_home_graph()` (line 389)
- **Description**: Defines the LangGraph state machine with nodes for stress check, safety upgrade, mortgage programs lookup, strategy lab, and LLM explanation. Entry point is `run_single_home_graph()` which compiles and invokes the graph.

---

## 2. Minimal End-to-End Call Flow

1. **HTTP Request** → FastAPI receives `POST /api/mortgage-agent/single-home-agent` with `SingleHomeAgentRequest` payload (contains `stress_request: StressCheckRequest` + optional `user_message: str`).

2. **Route Handler** → `single_home_agent_endpoint()` in `routes/mortgage_agent.py` extracts request, generates `request_id`, and calls `run_single_home_agent(payload, request_id=request_id)`.

3. **Runtime Dispatch** → `run_single_home_agent()` checks `USE_LANGGRAPH_SINGLE_HOME` flag. If `True`, calls `run_single_home_graph(req)`; otherwise runs legacy sequential flow.

4. **LangGraph Execution** → `run_single_home_graph()` builds initial state from `SingleHomeAgentRequest`, compiles graph via `_build_single_home_graph()`, and invokes `graph.invoke(initial_state)`.

5. **Graph Nodes Execution** → Graph executes nodes in order: `stress_check` → router → (`safety_upgrade` + `mortgage_programs` if tight/high_risk, else skip) → `strategy_lab` → `llm_explanation` → END.

6. **State Aggregation** → Final state contains `stress_result`, `safety_upgrade`, `mortgage_programs_preview`, `strategy_lab`, `borrower_narrative`, `recommended_actions`, `llm_usage`.

7. **Response Construction** → `run_single_home_graph()` converts final state to `SingleHomeAgentResponse` (merges `agent_steps` from graph nodes into `stress_result.agent_steps`).

8. **HTTP Response** → Route handler returns `SingleHomeAgentResponse` as JSON (FastAPI auto-serializes Pydantic model).

---

## 3. LangGraph "SingleHomeGraph" Decomposition

### 3.1 State Schema

**File**: `services/fiqa_api/mortgage/graphs/single_home_graph.py` (line 33)

**Class**: `SingleHomeGraphState` (TypedDict)

| Field | Type | Category | Description |
|-------|------|-----------|-------------|
| `request` | `SingleHomeAgentRequest` | Input | Original API request with `stress_request` and optional `user_message` |
| `stress_request` | `StressCheckRequest` | Input | Extracted stress check parameters (income, debts, home price, etc.) |
| `user_text` | `Optional[str]` | Input | Natural language question (for NLU path, currently unused) |
| `partial_request` | `Optional[PartialStressRequest]` | Intermediate | Partially extracted request from NLU (unused in current flow) |
| `missing_required_fields` | `Optional[List[str]]` | Intermediate | Fields missing from NLU extraction (unused) |
| `nl_intent_type` | `Optional[str]` | Intermediate | NLU intent classification (unused) |
| `stress_result` | `Optional[StressCheckResponse]` | Intermediate | Core stress check output (DTI, stress band, approval score, risk assessment) |
| `safety_upgrade` | `Optional[SafetyUpgradeResult]` | Intermediate | Safer homes search results and upgrade suggestions |
| `mortgage_programs` | `Optional[List[Dict[str, Any]]]` | Intermediate | Full mortgage assistance programs from MCP server |
| `mortgage_programs_preview` | `Optional[List[MortgageProgramPreview]]` | Intermediate | Lightweight preview (top 2-3 programs) for response |
| `strategy_lab` | `Optional[StrategyLabResult]` | Intermediate | What-if scenario analysis (alternative plans) |
| `borrower_narrative` | `Optional[str]` | Final Output | LLM-generated explanation for borrower |
| `recommended_actions` | `Optional[List[str]]` | Final Output | LLM-generated next steps (1-3 bullets) |
| `llm_usage` | `Optional[Dict[str, Any]]` | Final Output | Token usage metadata |
| `agent_steps` | `List[AgentStep]` | Intermediate | Step-by-step execution log (merged from all nodes) |
| `errors` | `List[str]` | Intermediate | Error messages (currently unused) |

**Key Fields**:
- **Inputs**: `request`, `stress_request`
- **Intermediate**: `stress_result`, `safety_upgrade`, `mortgage_programs`, `strategy_lab`
- **Final Outputs**: `borrower_narrative`, `recommended_actions`, `llm_usage`

### 3.2 Nodes and Routing

**Graph Structure** (defined in `_build_single_home_graph()`, line 389):

```
Entry → stress_check → [router] → 
  ├─ need_upgrade → safety_upgrade → mortgage_programs → strategy_lab → llm_explanation → END
  └─ skip_upgrade → strategy_lab → llm_explanation → END
```

#### Node: `stress_check`
- **File**: `services/fiqa_api/mortgage/graphs/single_home_graph.py`
- **Function**: `_stress_check_node()` (line 101)
- **Inputs from state**: `stress_request: StressCheckRequest`
- **Outputs to state**: `stress_result: StressCheckResponse`, `agent_steps: List[AgentStep]`
- **Business logic**: Calls `run_stress_check()` which computes monthly payment, DTI ratio, stress band (loose/ok/tight/high_risk), approval score (rule-based + optional ML adjustment), and risk assessment (hard_block/soft_warning flags). Pure Python - no LLM calls.

#### Router: `_need_safety_upgrade_router`
- **File**: `services/fiqa_api/mortgage/graphs/single_home_graph.py`
- **Function**: `_need_safety_upgrade_router()` (line 120)
- **Condition**: Checks `stress_result.stress_band` - if `"tight"` or `"high_risk"`, returns `"need_upgrade"`; otherwise `"skip_upgrade"`.
- **Routing logic**: Tight/high_risk path triggers safety upgrade flow (search safer homes + mortgage programs). Loose/ok path skips upgrade and goes directly to strategy lab.

#### Node: `safety_upgrade`
- **File**: `services/fiqa_api/mortgage/graphs/single_home_graph.py`
- **Function**: `_safety_upgrade_node()` (line 133)
- **Inputs from state**: `stress_request: StressCheckRequest`
- **Outputs to state**: `safety_upgrade: SafetyUpgradeResult`
- **Business logic**: Calls `run_safety_upgrade_flow()` which: (1) runs baseline stress check (already done, but re-runs for consistency), (2) searches for safer homes in same ZIP code via `search_safer_homes_for_case()`, (3) re-runs stress checks on candidate homes, (4) builds structured suggestions. Only executes if router returned `"need_upgrade"`.

#### Node: `mortgage_programs`
- **File**: `services/fiqa_api/mortgage/graphs/single_home_graph.py`
- **Function**: `_mortgage_programs_node()` (line 159)
- **Inputs from state**: `stress_result: StressCheckResponse`, `stress_request: StressCheckRequest`
- **Outputs to state**: `mortgage_programs: List[Dict[str, Any]]`, `mortgage_programs_preview: List[MortgageProgramPreview]`, `agent_steps: List[AgentStep]`
- **Business logic**: Calls MCP server (`mcp/mortgage_programs_server/server.py`) via `search_mortgage_programs()` to find mortgage assistance programs matching borrower's ZIP code, state, and DTI. Only executes if `stress_band` is `"tight"` or `"high_risk"`. Returns top 3 programs as preview.

#### Node: `strategy_lab`
- **File**: `services/fiqa_api/mortgage/graphs/single_home_graph.py`
- **Function**: `_strategy_lab_node()` (line 331)
- **Inputs from state**: `stress_request: StressCheckRequest`
- **Outputs to state**: `strategy_lab: StrategyLabResult`
- **Business logic**: Calls `run_strategy_lab()` which generates 3 alternative scenarios: (1) lower price by 10%, (2) increase down payment by 5%, (3) more conservative risk preference. Each scenario re-runs `run_stress_check()` and compares results. Returns baseline metrics + scenario comparisons.

#### Node: `llm_explanation`
- **File**: `services/fiqa_api/mortgage/graphs/single_home_graph.py`
- **Function**: `_llm_explanation_node()` (line 358)
- **Inputs from state**: `stress_result: StressCheckResponse`, `request: SingleHomeAgentRequest`, `safety_upgrade: SafetyUpgradeResult`, `mortgage_programs: List[Dict]`
- **Outputs to state**: `borrower_narrative: str`, `recommended_actions: List[str]`, `llm_usage: Dict[str, Any]`
- **Business logic**: Calls `_generate_single_home_narrative()` which constructs LLM prompt with stress result, safety upgrade suggestions, mortgage programs, approval score, and risk assessment. LLM generates friendly explanation and 1-3 recommended actions. Only executes if `LLM_GENERATION_ENABLED` is true.

---

### 3.3 "Best Features" of This Graph

#### Feature 1: Hybrid Approval Score (Rules + ML Logistic Regression)
- **Location**: `services/fiqa_api/mortgage/mortgage_agent_runtime.py` (line 1900-2078)
- **Integration**: `run_stress_check()` computes rule-based approval score first, then applies ML adjustment if `USE_ML_APPROVAL_SCORE` is enabled. ML model (`predict_ml_approval_prob()`) predicts approval probability, then `combine_rule_and_ml()` merges scores.
- **State field**: `stress_result.approval_score: ApprovalScore` (score 0-100, bucket: likely/borderline/unlikely, reasons list)
- **Why it matters**: Production systems need explainable scores (rules) with ML refinement for edge cases. Demonstrates hybrid AI architecture.

#### Feature 2: Safety Upgrade Flow with Safer Homes Search
- **Location**: `services/fiqa_api/mortgage/mortgage_agent_runtime.py` (line 3070-3280)
- **Integration**: `_safety_upgrade_node()` calls `run_safety_upgrade_flow()` which searches local listings, filters to "safer" homes (better stress band or lower DTI), re-runs stress checks on candidates, and builds structured suggestions.
- **State fields**: `safety_upgrade: SafetyUpgradeResult` (baseline metrics, safer homes list, primary/alternative suggestions)
- **Why it matters**: Proactive agent behavior - doesn't just report problems, searches for solutions. Shows tool-using agent pattern (search + re-evaluation).

#### Feature 3: Strategy Lab Auto-Generates What-If Scenarios
- **Location**: `services/fiqa_api/mortgage/mortgage_agent_runtime.py` (line 2086-2276)
- **Integration**: `_strategy_lab_node()` calls `run_strategy_lab()` which generates 3 scenarios (lower price, more down payment, conservative risk), re-runs stress checks, and compares results.
- **State field**: `strategy_lab: StrategyLabResult` (baseline + scenario comparisons)
- **Why it matters**: Demonstrates reflection/planning step - agent explores alternatives before finalizing recommendation. Useful for "what-if" UX.

#### Feature 4: Risk Assessment and Guardrails (hard_block/soft_warning)
- **Location**: `services/fiqa_api/mortgage/mortgage_agent_runtime.py` (line 1915-1949)
- **Integration**: `run_stress_check()` calls `assess_risk()` which computes `RiskAssessment` with `risk_flags` (e.g., `["high_dti", "negative_cashflow"]`), `hard_block: bool`, `soft_warning: bool`. This influences LLM tone in `_generate_single_home_narrative()`.
- **State field**: `stress_result.risk_assessment: RiskAssessment`
- **Why it matters**: Safety guardrails prevent LLM from recommending dangerous loans. `hard_block=True` triggers stronger warnings. Shows how structured risk signals control LLM behavior.

#### Feature 5: MCP Integration for External Mortgage Programs
- **Location**: `services/fiqa_api/mortgage/graphs/single_home_graph.py` (line 159-328)
- **Integration**: `_mortgage_programs_node()` dynamically loads MCP server module (`mcp/mortgage_programs_server/server.py`) and calls `search_mortgage_programs()` with ZIP code, state, DTI. Returns JSON list of programs.
- **State fields**: `mortgage_programs: List[Dict]`, `mortgage_programs_preview: List[MortgageProgramPreview]`
- **Why it matters**: Demonstrates external tool integration (MCP = Model Context Protocol). Shows how agents can call external APIs/services for real-time data.

---

## 4. CrowdStrike-Style Interview Talking Points

1. **"Designed a LangGraph-based multi-step agent workflow to orchestrate rule-based risk checks, ML approval scoring, safer-option search, and LLM explanations, with conditional routing based on stress bands (loose/ok vs tight/high_risk)."**

2. **"Implemented guardrails and risk assessment (hard_block/soft_warning flags) to control downstream agent behavior and LLM tone, ensuring safe recommendations for high-risk borrowers and preventing dangerous loan suggestions."**

3. **"Built hybrid approval scoring system combining rule-based heuristics (explainable, deterministic) with ML logistic regression (for edge cases), demonstrating production-ready AI architecture that balances interpretability and accuracy."**

4. **"Architected safety upgrade flow that proactively searches for safer homes in borrower's ZIP code, re-runs stress checks on candidates, and generates structured upgrade suggestions - demonstrating tool-using agent pattern with search + re-evaluation loop."**

5. **"Integrated MCP (Model Context Protocol) server for external mortgage programs lookup, enabling real-time data fetching from external APIs while maintaining graceful degradation if service unavailable."**

6. **"Implemented strategy lab reflection step that auto-generates what-if scenarios (lower price, more down payment, conservative risk), re-runs stress checks, and compares results - enabling exploratory planning before final recommendation."**

7. **"Designed end-to-end workflow from HTTP request → LangGraph state → tool calls (stress check, safer homes search, MCP) → LLM explanation → structured response, with comprehensive agent step logging for observability and debugging."**

---

## 5. Concise "Mental Model" Summary

1. **Minimal Skeleton**: Single Home Mortgage Agent is a LangGraph workflow that takes borrower profile (income, debts) + home details (price, down payment) and returns stress check result + LLM explanation + safety upgrade suggestions.

2. **Key State Fields**: `stress_request` (input), `stress_result` (core output with DTI, stress band, approval score, risk assessment), `safety_upgrade` (safer homes + suggestions), `strategy_lab` (what-if scenarios), `borrower_narrative` (LLM explanation).

3. **Main Nodes**: `stress_check` (computes DTI/stress band) → router (tight/high_risk? → `safety_upgrade` + `mortgage_programs` : skip) → `strategy_lab` (what-if scenarios) → `llm_explanation` (generates narrative).

4. **Most Impressive Features**: (1) Hybrid approval score (rules + ML), (2) Safety upgrade flow (proactive search + re-evaluation), (3) Risk assessment guardrails (hard_block/soft_warning), (4) MCP integration (external tools), (5) Strategy lab (reflection/planning).

5. **Ops/Infra Copilot Adaptation Ideas**:
   - **Infrastructure Risk Assessment**: Replace stress check with infrastructure health check (CPU, memory, latency). Router branches on "healthy" vs "degraded/critical". Safety upgrade searches for safer configurations (lower resource usage, better redundancy). Strategy lab explores what-if scenarios (scale down, add replicas, change instance types).
   - **Incident Response Agent**: Replace stress check with incident severity assessment. Router branches on severity (low/medium vs high/critical). Safety upgrade searches for similar past incidents and their resolutions. Strategy lab explores mitigation strategies (rollback, scale up, traffic shift). LLM explains incident and recommended actions.

---

## File Reference Quick Index

- **API Endpoint**: `services/fiqa_api/routes/mortgage_agent.py:356` (`single_home_agent_endpoint`)
- **Runtime Function**: `services/fiqa_api/mortgage/mortgage_agent_runtime.py:2739` (`run_single_home_agent`)
- **LangGraph Definition**: `services/fiqa_api/mortgage/graphs/single_home_graph.py:389` (`_build_single_home_graph`)
- **Graph Entry Point**: `services/fiqa_api/mortgage/graphs/single_home_graph.py:430` (`run_single_home_graph`)
- **State Schema**: `services/fiqa_api/mortgage/graphs/single_home_graph.py:33` (`SingleHomeGraphState`)
- **Stress Check**: `services/fiqa_api/mortgage/mortgage_agent_runtime.py:1508` (`run_stress_check`)
- **Safety Upgrade**: `services/fiqa_api/mortgage/mortgage_agent_runtime.py:3070` (`run_safety_upgrade_flow`)
- **Strategy Lab**: `services/fiqa_api/mortgage/mortgage_agent_runtime.py:2086` (`run_strategy_lab`)
- **LLM Narrative**: `services/fiqa_api/mortgage/mortgage_agent_runtime.py:2304` (`_generate_single_home_narrative`)
- **Schemas**: `services/fiqa_api/mortgage/schemas.py`

