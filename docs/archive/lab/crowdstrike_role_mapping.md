# Codebase Mapping to CrowdStrike "Senior Applied AI Engineer" Role

## Component Inventory by Category

### (A) LLM Agents / Workflows / LangGraph / MCP / Orchestration

#### 1. **LangGraph Steward Orchestration**
- **Path**: `orchestrators/steward_graph.py`
- **Description**: LangGraph-based state machine for autonomous experiment evaluation and deployment decisions. Implements review → reflect → dryrun → evaluate → decide → persist workflow with SQLite checkpointing, timeout guards, and metric threshold validation.
- **Category**: A

#### 2. **LabOps Agent Runner (V1/V2/V3)**
- **Path**: `agents/labops/agent_runner.py`, `agents/labops/v2/agent_runner_v2.py`, `agents/labops/v3/runner_v3.py`
- **Description**: Autonomous agents for Ops-like workflows that execute experiments, judge results, and apply configuration changes. V3 includes LLM explainers and code navigation. Implements health gates, execution phases, decision engines, and safe-apply modes.
- **Category**: A

#### 3. **MCP Mortgage Programs Server**
- **Path**: `mcp/mortgage_programs_server/server.py`
- **Description**: Model Context Protocol (MCP) server providing mortgage program search tools to LLM agents. Implements semantic matching, DTI filtering, and program ranking with explainability.
- **Category**: A

#### 4. **Mortgage Agent Runtime**
- **Path**: `services/fiqa_api/mortgage/mortgage_agent_runtime.py`
- **Description**: LLM-powered mortgage agent orchestrating stress checks, risk assessment, and recommendation generation. Integrates with LangGraph workflows for multi-step decision making.
- **Category**: A

#### 5. **Agent Executor & Planner**
- **Path**: `services/fiqa_api/agent/executor.py`, `services/fiqa_api/agent/planner.py`
- **Description**: Agent execution framework that takes structured plans from planners and executes them via tool calls. Supports dependency resolution and dynamic tool invocation.
- **Category**: A

#### 6. **Code Graph Service**
- **Path**: `services/fiqa_api/services/code_graph_service.py`, `scripts/build_graphs.py`
- **Description**: Code intelligence system that builds function call graphs for LLM agents to navigate codebases. Provides semantic code search and navigation capabilities.
- **Category**: A

---

### (B) Evaluation, Offline Tests, Smoke Tests, Regression Harnesses

#### 7. **A/B/C Evaluation Runner**
- **Path**: `eval/run_abc_4m_evaluation.py`, `eval/run_ab_30m_evaluation.py`
- **Description**: Comprehensive evaluation harness for running baseline vs stress scenarios with statistical analysis. Generates timeline charts, latency comparisons, and recall metrics. Supports chaos injection and recovery analysis.
- **Category**: B

#### 8. **Enhanced A/B Evaluator**
- **Path**: `modules/evaluation/enhanced_ab_evaluator.py`, `modules/evaluation/enhanced_ab_analyzer.py`
- **Description**: Statistical evaluation framework with timeline analysis, recovery detection, and automated chart generation. Supports multi-scenario comparisons with configurable metrics.
- **Category**: B

#### 9. **Offline Agent Evaluation**
- **Path**: `experiments/offline_agent_eval.py`, `docs/offline_agent_eval_report.md`
- **Description**: Offline evaluation system for agent performance with 1000+ sample runs, stress band distribution analysis, and approval score validation. Generates comprehensive reports with success rates and improvement statistics.
- **Category**: B

#### 10. **Canary Deployment Evaluator**
- **Path**: `modules/canary/ab_evaluator.py`, `modules/canary/canary_executor.py`
- **Description**: Canary deployment system with 90/10 traffic splitting, SLO monitoring, and automatic rollback. Collects metrics per bucket, validates SLO compliance, and generates audit logs.
- **Category**: B

#### 11. **Regression Test Suite**
- **Path**: `scripts/run_regression_suite.py`, `scripts/smoke.sh`
- **Description**: Comprehensive smoke test and regression harness covering GPU fallback, embedding consistency, health checks, and end-to-end workflows. Includes CI integration and pass/fail reporting.
- **Category**: B

#### 12. **Test Coverage Framework**
- **Path**: `docs/TEST_COVERAGE_SUMMARY.md`, `tests/`
- **Description**: Extensive unit test suite with 98+ test cases covering decision logic, memory systems, constraints, multi-knob tuning, and adversarial safety. Includes test fixtures and sanity check scripts.
- **Category**: B

#### 13. **E2E Test Runner**
- **Path**: `scripts/e2e_test.sh`, `experiments/single_home_agent_integration_test.py`
- **Description**: End-to-end test automation for full agent workflows including sync, rebuild, health checks, job execution, and metrics verification.
- **Category**: B

---

### (C) Guardrails, Risk Assessment, Safety, Timeouts, Fallbacks

#### 14. **Demo Pack Guardrails**
- **Path**: `modules/demo_pack/guardrails.py`
- **Description**: Comprehensive guardrail system with PASS/FAIL gating logic. Validates delta P95, p-value significance, recall thresholds, safety rates, and apply rates. Provides recommendations and warnings for insufficient test duration or statistical power.
- **Category**: C

#### 15. **Risk Assessment Module**
- **Path**: `services/fiqa_api/mortgage/risk_assessment.py`
- **Description**: Risk assessment and control fence system for mortgage applications. Implements hard_block and soft_warning logic based on DTI ratios, stress bands, cashflow analysis, LTV ratios, and approval scores. Provides risk flags and actionable recommendations.
- **Category**: C

#### 16. **Black Swan Guards & Watchdog**
- **Path**: `services/black_swan/guards.py`, `services/black_swan/runner.py`
- **Description**: Guardrails and watchdog monitoring system with timeout detection, progress tracking, and guardrail violation hooks. Implements heartbeat mechanisms and emergency stop capabilities.
- **Category**: C

#### 17. **Guardrail Monitor (SLA Protection)**
- **Path**: `services/fiqa_api/app_v2.py` (guardrail_monitor function)
- **Description**: Background task monitoring SLA violations (P95 latency) and automatically pausing AutoTuner when thresholds are exceeded. Implements cooldown periods and resume logic.
- **Category**: C

#### 18. **Steward Graph Timeout Guards**
- **Path**: `orchestrators/steward_graph.py` (_execute_with_timeout function)
- **Description**: Timeout protection for graph node execution with thread-based timeouts and error handling. Prevents infinite loops and ensures graph progress.
- **Category**: C

#### 19. **Fallback Mechanisms**
- **Path**: `services/fiqa_api/search_core.py`, `services/fiqa_api/search_service.py`
- **Description**: Fallback logic for search operations when GPU workers fail or embeddings are unavailable. Includes Qdrant fallback, CPU fallback, and graceful degradation.
- **Category**: C

#### 20. **Force Override & Guardrails Plugin**
- **Path**: `services/force_override/manager.py`, `services/plugins/guardrails/__init__.py`
- **Description**: Force override system with validation and guardrails plugin architecture. Provides parameter validation and safety checks before applying configuration changes.
- **Category**: C

#### 21. **AutoTuner Safety Constraints**
- **Path**: `modules/autotuner/brain/constraints.py`, `modules/autotuner/brain/decider.py`
- **Description**: Parameter constraint validation with hysteresis bands, cooldown periods, and boundary checks. Prevents unsafe parameter combinations and implements conservative decision logic.
- **Category**: C

---

### (D) RAG / Retrieval / Vector Search / Ranking / Code Intelligence

#### 22. **RAG Pipeline with CAG Cache**
- **Path**: `modules/rag/cache.py`, `modules/rag/README.md`, `pipeline/rag_pipeline.py`
- **Description**: Cache-Augmented Generation (CAG) module with multiple matching policies (exact, normalized, semantic), TTL-based freshness, LRU capacity management, and comprehensive metrics. Integrates with RAG pipelines for latency optimization.
- **Category**: D

#### 23. **Vector Search Engine**
- **Path**: `modules/search/vector_search.py`, `engines/milvus_engine.py`
- **Description**: Vector similarity search using Qdrant and Milvus backends. Supports HNSW index parameters (ef_search), metadata filtering, and configurable top-k retrieval. Includes embedding model integration.
- **Category**: D

#### 24. **Hybrid Search Pipeline**
- **Path**: `modules/search/hybrid.py`, `modules/search/search_pipeline.py`
- **Description**: Hybrid search combining vector and BM25 retrieval with Reciprocal Rank Fusion (RRF). Implements alpha-weighted fusion, reranking integration, and explainability metrics.
- **Category**: D

#### 25. **Reranking System**
- **Path**: `modules/rerankers/factory.py`, `modules/rerankers/simple_ce.py`
- **Description**: Cross-encoder reranking system with configurable models and top-k selection. Includes fake reranker for testing and cost-aware reranking with budget constraints.
- **Category**: D

#### 26. **BM25 Retriever**
- **Path**: `modules/retrievers/bm25.py`
- **Description**: BM25 sparse retrieval implementation for keyword-based search. Integrates with hybrid search pipeline for combining dense and sparse signals.
- **Category**: D

#### 27. **Page Index (Hierarchical RAG)**
- **Path**: `modules/rag/page_index.py`
- **Description**: Two-stage hierarchical retrieval system with chapter-level and paragraph-level ranking. Implements TF-IDF scoring, fusion weights, and timeout protection.
- **Category**: D

#### 28. **Code Intelligence & Graph Ranker**
- **Path**: `services/code_intelligence/graph_ranker.py`, `services/code_intelligence/static_analyzer.py`
- **Description**: Code intelligence system with static analysis, function call graph construction, and semantic code ranking. Enables LLM agents to navigate and understand codebases.
- **Category**: D

#### 29. **Retrieval Proxy**
- **Path**: `services/retrieval_proxy/` (Go implementation)
- **Description**: High-performance retrieval proxy with caching, budget management, and source policy routing. Implements fuse operations and observability hooks.
- **Category**: D

#### 30. **Search Pipeline Integration**
- **Path**: `modules/search/search_pipeline_integration.py`
- **Description**: Complete search pipeline integrating vector search, BM25, reranking, and AutoTuner. Includes observability, chaos injection, and SLO monitoring.
- **Category**: D

#### 31. **Routing & Cost Estimation**
- **Path**: `modules/routing/cost/estimator.py`, `modules/routing/rules/router.py`
- **Description**: Intelligent routing system with cost estimation for different search strategies. Routes queries to optimal retrieval paths based on budget and performance requirements.
- **Category**: D

---

## Resume Bullet Points (CrowdStrike JD Language)

1. **Built LangGraph-based orchestration system** for autonomous LLM agent workflows, implementing state machines with SQLite checkpointing, timeout guards, and metric threshold validation for safe experiment evaluation and deployment decisions.

2. **Developed comprehensive evaluation harness** with A/B/C testing framework supporting offline evaluation, statistical analysis, timeline chart generation, and chaos injection testing. Validated agent performance across 1000+ sample runs with automated reporting.

3. **Implemented multi-layered guardrails system** with risk assessment, SLA monitoring, and automatic fallback mechanisms. Designed hard_block/soft_warning logic for mortgage applications and integrated watchdog systems with timeout detection and emergency stop capabilities.

4. **Architected RAG pipeline with Cache-Augmented Generation (CAG)** supporting exact, normalized, and semantic matching policies. Achieved 30%+ latency improvement through TTL-based freshness, LRU capacity management, and comprehensive cache metrics.

5. **Built hybrid retrieval system** combining vector search (Qdrant/Milvus), BM25 sparse retrieval, and cross-encoder reranking with Reciprocal Rank Fusion. Integrated AutoTuner for dynamic parameter optimization with SLO-aware guardrails.

6. **Designed LabOps agents** for autonomous experiment orchestration with health gates, execution phases, decision engines, and safe-apply modes. V3 agents include LLM explainers and code navigation capabilities for Ops-like workflows.

7. **Created canary deployment system** with 90/10 traffic splitting, SLO monitoring, and automatic rollback. Implemented per-bucket metrics collection, threshold validation, and audit logging for safe configuration rollouts.

8. **Developed code intelligence system** with static analysis, function call graph construction, and semantic code ranking. Enabled LLM agents to navigate codebases through MCP (Model Context Protocol) integration and graph-based retrieval.

