# Ops Copilot Overview

## What is the Ops Copilot skeleton?

The Ops Copilot is a **parallel to the Single Home Mortgage Agent**, but in the **Ops/Infra domain**. It provides a minimal but coherent skeleton for system health monitoring, safety upgrades, and strategy lab scenarios.

### Input/Output

- **Input**: `SystemSnapshot` - captures current system metrics (CPU, memory, latency, error rate, QPS, disk usage, etc.)
- **Output**: 
  - `SystemHealthCheckResult` - health band classification, score, risk flags, and per-metric assessments
  - `SaferConfigSuggestion` - structured suggestions for config changes to improve health
  - `SystemStrategyLabResult` - what-if scenario analysis comparing baseline vs alternative configurations

### Key Features

1. **Rule-based health check** - explainable thresholds and risk flagging
2. **Strategy Lab** - what-if analysis for config changes (e.g., reduce QPS, add replicas)
3. **Safety upgrade behavior** - hard_block/soft_warning guardrails similar to mortgage agent
4. **Offline evaluation** - synthetic system snapshot generation and batch evaluation

## Architecture

### Core Components

1. **`schemas.py`** - Pydantic models for:
   - `SystemSnapshot` - system metrics snapshot
   - `SystemHealthCheckResult` - health check output with band, score, risk flags
   - `SaferConfigSuggestion` - safety upgrade suggestions
   - `SystemStrategyScenario` - individual strategy lab scenario
   - `SystemStrategyLabResult` - strategy lab output

2. **`ops_runtime.py`** - Rule-based runtime logic:
   - `run_system_health_check()` - computes health band and score based on thresholds
   - `run_safety_upgrade_for_system()` - generates config suggestions for unhealthy systems
   - `run_system_strategy_lab()` - generates alternative scenarios and compares health results

### Health Check Rules

Simple threshold-based rules:

- **CPU**: WARN ≥ 70%, CRITICAL ≥ 90%
- **Memory**: WARN ≥ 75%, CRITICAL ≥ 90%
- **Latency**: WARN ≥ 300ms, CRITICAL ≥ 800ms
- **Error Rate**: WARN ≥ 1%, CRITICAL ≥ 5%
- **Disk**: WARN ≥ 75%, CRITICAL ≥ 90%

Health band classification:
- `healthy` - no warnings
- `warning` - 1 warning
- `degraded` - 2+ warnings
- `critical` - any critical threshold exceeded

Health score (0-100):
- Starts at 85
- Subtracts points for each risk (e.g., high CPU -10, critical error rate -40)
- Clamped to 0-100

### Safety Upgrade Suggestions

When system is not healthy, generates 2-3 rule-based suggestions:

1. **Reduce QPS by 20% and add 1 replica** - helps with CPU, memory, latency
2. **Switch to conservative timeout and reduce max QPS** - helps with latency and error rate
3. **Add replicas and scale horizontally** - helps with CPU and memory

Each suggestion includes:
- Estimated health result after applying the change
- Structured config changes (e.g., `{"qps_limit": 0.8, "replicas": "+1"}`)

### Strategy Lab Scenarios

Generates 2-3 alternative scenarios:

1. **Lower QPS by 20%** - reduces load, improves CPU/memory/latency
2. **Add 1 replica** - distributes load, reduces per-instance CPU/memory
3. **Reduce error rate (assuming fix)** - assumes error rate drops by 50%

For each scenario:
- Builds hypothetical `SystemSnapshot` after change
- Runs health check on the new snapshot
- Compares band and score vs baseline

## How it maps to CrowdStrike JD

### LLM Agent Skeleton Ready

The current implementation is **rule-based only**, but the architecture is designed to be extended with:

- **LLM integration** - plug in LLM for natural language explanations and suggestions
- **RAG runbooks** - connect to knowledge base of runbooks and best practices
- **Log/metrics integration** - connect to real-time monitoring systems (Prometheus, Datadog, etc.)

### Guardrails

- **Risk flags** - machine-readable identifiers (e.g., `"high_cpu"`, `"high_error_rate"`)
- **Hard block** - prevents deployment when critical issues detected
- **Soft warning** - alerts for degraded/warning states

### Offline Evaluation Harness

- **Synthetic data generation** - realistic system snapshot distributions
- **Batch evaluation** - process hundreds of snapshots
- **Statistics** - health band distribution, strategy lab improvement rates

This provides a **safe rollout path** - test on synthetic data before connecting to production systems.

## Key Functions

### `run_system_health_check(snapshot: SystemSnapshot) -> SystemHealthCheckResult`

Computes health band, score, risk flags, and per-metric assessments based on rule-based thresholds.

### `run_safety_upgrade_for_system(snapshot: SystemSnapshot) -> List[SaferConfigSuggestion]`

If system is healthy, returns empty list. Otherwise, generates 2-3 config suggestions with estimated health improvements.

### `run_system_strategy_lab(snapshot: SystemSnapshot) -> SystemStrategyLabResult`

Generates alternative scenarios (e.g., lower QPS, add replica, reduce error rate) and compares health results vs baseline.

## Usage Examples

### Health Check

```python
from services.fiqa_api.ops_copilot import run_system_health_check, SystemSnapshot
from datetime import datetime

snapshot = SystemSnapshot(
    service_name="api-gateway",
    environment="prod",
    cpu_pct=85.0,
    mem_pct=70.0,
    p95_latency_ms=500.0,
    error_rate=0.02,
    qps=2000.0,
    disk_pct=60.0,
    timestamp=datetime.utcnow(),
)

health = run_system_health_check(snapshot)
print(f"Band: {health.band}, Score: {health.score}")
print(f"Risk Flags: {health.risk_flags}")
```

### Strategy Lab

```python
from services.fiqa_api.ops_copilot import run_system_strategy_lab

strategy_lab = run_system_strategy_lab(snapshot)
print(f"Baseline: {strategy_lab.baseline_health.band}")

for scenario in strategy_lab.scenarios:
    print(f"Scenario: {scenario.title}")
    print(f"  Band: {scenario.health_result.band}, Score: {scenario.health_result.score}")
```

## Observability & Logging

### Structured Logging

The Ops Copilot emits structured logs for each request and node execution. All logs use the `ops_copilot` logger name and include a `request_id` for tracing.

#### Per-Node Logging

Each node in the LangGraph workflow logs completion events with the following structure:

```
event=ops_node_complete node=<node_name> request_id=<request_id> latency_ms=<ms> band=<band> score=<score> ...
```

**Node Events:**
- `health_check`: Logs band, score, risk_flags
- `safety_upgrade`: Logs band, score, safety_upgrade_ran=true, suggestions_count
- `strategy_lab`: Logs band, score, strategy_improved=<count>, scenarios_count
- `llm_explanation`: Logs band, score, llm_fallback_used=<bool>, model=<model_name>

**Example log line:**
```
event=ops_node_complete node=health_check request_id=req_abc123 latency_ms=12.5 band=degraded score=45.2 risk_flags=high_cpu,high_latency
```

#### LLM Explanation Logging

The LLM explanation node logs separate events for LLM attempts:

```
event=ops_llm_explanation request_id=<request_id> model=<model> success=<bool> fallback_used=<bool> latency_ms=<ms> ...
```

**Example log lines:**
```
event=ops_llm_explanation request_id=req_abc123 model=gpt-4o-mini success=true fallback_used=false latency_ms=1250.3 tokens=245 cost_usd_est=0.000123
event=ops_llm_explanation request_id=req_xyz789 model=none success=false fallback_used=true latency_ms=0.0 reason=llm_disabled
```

#### Log Fields

- **request_id**: Unique identifier for each request (flows through all nodes)
- **latency_ms**: Node execution time in milliseconds
- **band**: Health band (healthy/warning/degraded/critical)
- **score**: Health score (0-100)
- **risk_flags**: Comma-separated list of risk identifiers
- **safety_upgrade_ran**: Boolean indicating if safety upgrade node executed
- **strategy_improved**: Count of improved scenarios (for strategy_lab node)
- **llm_fallback_used**: Boolean indicating if fallback narrative was used
- **model**: LLM model name (or "none" if LLM disabled)

**Note**: Logs do not include raw prompts or full narratives to keep them compact and safe for production.

## Evaluation

### Demo Script – How to Show Ops Copilot in 3 Minutes

This section provides a speaking script you can use during interviews to demonstrate the Ops Copilot effectively.

**Quick demo with 3 fixed scenarios** (2-3 minutes):
```bash
# Run all scenarios (default)
python experiments/ops_copilot_demo.py

# Run a single scenario (recommended for interviews)
python experiments/ops_copilot_demo.py --scenario healthy
python experiments/ops_copilot_demo.py --scenario degraded
python experiments/ops_copilot_demo.py --scenario critical

# HTTP call to local server (if backend is running)
python experiments/ops_copilot_demo.py --use-http --base-url http://localhost:8001

# Enable verbose debug output
python experiments/ops_copilot_demo.py --verbose
```

The demo script runs 3 scenarios:
1. **Healthy Service**: Low CPU/memory, low latency, low errors → shows `band=healthy`
2. **Degraded Service**: High CPU/memory/latency but not catastrophic → shows `band=degraded` with safety suggestions
3. **Critical Service**: Very high CPU + high error_rate + disk_near_full → shows `band=critical` with hard_block

Each scenario produces a structured mini-report with:
- Health band and score
- Key metrics (CPU, memory, latency, error rate) in human-friendly format
- Risk flags (or "(none)" if healthy)
- Hard block and soft warning status
- Safety suggestions (if applicable)
- Best Strategy Lab scenario with improvement delta
- LLM summary (2-3 sentences)
- Recommended actions (1-3 items)

**Note**: The demo script automatically disables LLM if `LLM_GENERATION_ENABLED` is not set, ensuring consistent fallback narratives for demo purposes.

---

#### Step 1 – Healthy Service

**Command:**
```bash
python experiments/ops_copilot_demo.py --scenario healthy
```

**What to say:**
1. "This is a normal production service: CPU at 32%, memory at 48%, p95 latency at 120ms, error rate at 0.02%."
2. "The agent classifies it as **healthy** with a high score (typically 85+), no hard_block or soft_warning."
3. "Strategy Lab still finds a slightly safer autoscaling configuration that could improve the score by a few points, but it's optional."
4. "Notice the clean output format – this is what I'd show an SRE or manager during an incident review."

**What to point at on screen:**
- The health band (`healthy`) and score (e.g., `85.0`)
- The absence of risk flags: `Risk flags: (none)`
- The absence of safety suggestions: `(none, system is already healthy)`
- The best strategy scenario and the score improvement (e.g., `+3.0`)
- The LLM summary (if enabled) or fallback narrative

---

#### Step 2 – Degraded Service

**Command:**
```bash
python experiments/ops_copilot_demo.py --scenario degraded
```

**What to say:**
1. "Here we simulate a degraded service with high CPU at 78%, high memory at 82%, and p95 latency at 450ms."
2. "The agent marks it as **degraded** (not yet critical), sets `soft_warning = True`, and identifies multiple risk flags: high_cpu, high_mem, high_latency, high_error_rate, high_disk."
3. "The banner says: 'System is degraded but still serving traffic; prioritize mitigation.'"
4. "Safety suggestions include things like 'Reduce QPS by 20% and add 1 replica' or 'Switch to conservative timeout'."
5. "Strategy Lab proposes 1-2 changes that statistically improve the score – for example, adding a replica might bump the score from 45 to 55."

**What to point at:**
- The `degraded` health band and lower score (e.g., `45.0`)
- The risk flags list: `high_cpu, high_mem, high_latency, high_error_rate, high_disk`
- The safety suggestions (2-3 concrete config changes)
- The Strategy Lab best scenario with the score delta (e.g., `+10.0`)
- The recommended actions list (1-3 items)

---

#### Step 3 – Critical Service

**Command:**
```bash
python experiments/ops_copilot_demo.py --scenario critical
```

**What to say:**
1. "This is a simulated outage: CPU pegged at 94%, memory at 91%, errors spiking to 6.5%, disk nearly full at 93%."
2. "The agent marks it as **critical** with `hard_block = True`, meaning we'd block deployments until the issue is resolved."
3. "Notice the CRITICAL banner at the top: '!!! CRITICAL: Immediate attention required (hard_block = True)'."
4. "Safety suggestions are more aggressive – for example, 'Reduce QPS by 20% and add 1 replica' or 'Add replicas and scale horizontally'."
5. "Strategy Lab still runs what-if analysis to show which mitigation would have the biggest impact on health score."
6. "The recommended actions are concrete next steps an SRE can take immediately."

**What to point at:**
- The **CRITICAL** banner and `hard_block = True`
- The `critical` health band and very low score (e.g., `15.0`)
- The extensive risk flags list
- The best improvement scenario (e.g., adding replicas might bump score from 15 to 40)
- The narrative tone (more urgent, action-oriented)
- The first recommended action (highest priority)

---

#### Summary for Interviews

**Key talking points:**
1. "This demo shows how the Ops Copilot combines **rule-based health checks** with **what-if strategy analysis** to help SREs make informed decisions."
2. "The output is designed to be **interview-friendly** – clean, structured, and easy to explain to non-technical stakeholders."
3. "The system uses **guardrails** (hard_block, soft_warning) similar to production safety systems I've worked on."
4. "The Strategy Lab is like A/B testing for infrastructure – we simulate changes before applying them."
5. "I built this with **offline evaluation** in mind – we can test on hundreds of synthetic scenarios before connecting to real systems."

**If asked about LLM integration:**
- "The LLM layer (gpt-4o-mini) generates SRE-friendly narratives and recommended actions based on the health check results and semantic context (logs, runbooks, incidents)."
- "The system gracefully degrades if the LLM is disabled or fails – we fall back to deterministic narratives."
- "I've designed it so the core logic (health checks, strategy lab) is rule-based and testable, with LLM as an optional enhancement layer."

### Smoke Test

**Basic smoke test** (rule-based only):
```bash
python experiments/ops_copilot_smoke.py
```

**System health agent smoke test** (LangGraph + LLM):
```bash
python experiments/system_health_agent_smoke.py
```

Tests 3 hard-coded cases:
1. Healthy prod service - asserts `band="healthy"`, `hard_block=False`
2. Degraded service - asserts `band in ("degraded", "warning")`, at least one strategy scenario improves
3. Critical service - asserts `band="critical"`, `hard_block=True`, at least one strategy scenario improves

### Offline Evaluation

```bash
python experiments/offline_ops_agent_eval.py --n-samples 500 --random-seed 42 --output-report docs/offline_ops_agent_eval_report.md
```

Generates 500 synthetic system snapshots, runs health checks and strategy lab, and prints statistics:
- Health band distribution
- Scenario type distribution (healthy_like, cpu_bound, latency_spike, error_spike, disk_pressure)
- Health score statistics by band (p50, p95, mean)
- Safety upgrade statistics (percentage of degraded/critical cases with suggestions)
- Strategy lab improvement rates
- Improvement rates by baseline band
- Operational patterns (e.g., "X% of CPU-bound incidents were classified degraded/critical")

**Offline Evaluation Report**: See [offline_ops_agent_eval_report.md](./offline_ops_agent_eval_report.md) for a comprehensive evaluation report with 300+ samples.

The offline evaluation measures:
- **Health band distribution**: Distribution of healthy/warning/degraded/critical states across synthetic snapshots
- **Scenario type distribution**: Breakdown by scenario type (healthy_like, cpu_bound, etc.)
- **Guardrail behavior**: Hard block vs soft warning vs neither (rule-based guardrails)
- **Safety upgrade effectiveness**: Percentage of degraded/critical cases that receive suggestions
- **Strategy Lab improvement rate**: Percentage of cases where at least one scenario improves health
- **Operational patterns**: Insights like "X% of CPU-bound incidents were classified degraded/critical"

**Note**: LLM generation is disabled for offline evaluation. Only rule-based health checks and graph logic are tested, ensuring deterministic and reproducible results.

### RAG Evaluation

```bash
python experiments/offline_ops_rag_eval.py [--top-k 5] [--verbose]
```

Evaluates RAG retrieval quality by testing fixed test cases (service_name + symptom combinations) and checking if retrieved snippets match expected source files (runbooks, configs, incidents, lessons_learned).

**RAG Evaluation Report**: See [ops_rag_eval_report.md](./ops_rag_eval_report.md) for retrieval quality metrics including hit@k rates and top1 hit rates by source type.

## LangGraph & API Wiring

### LangGraph Workflow

The system health agent is now orchestrated via **LangGraph** (similar to the mortgage agent's `single_home_graph`):

- **Graph file**: `services/fiqa_api/ops_copilot/graphs/system_health_graph.py`
- **State**: `SystemHealthGraphState` with fields for snapshot, health_result, safety_suggestions, strategy_lab, narrative, recommended_actions, agent_steps
- **Nodes**:
  1. `health_check` - runs core health check
  2. `safety_upgrade` - generates safety suggestions (conditional, only if degraded/critical)
  3. `strategy_lab` - runs strategy lab analysis
  4. `llm_explanation` - generates SRE-friendly narrative
- **Flow**: `entry → health_check → router → (need_upgrade → safety_upgrade → strategy_lab → llm_explanation → END | skip_upgrade → strategy_lab → llm_explanation → END)`

### HTTP Endpoint

**Endpoint**: `POST /api/ops-copilot/system-health`

- **Request**: `SystemSnapshot` (JSON body)
- **Response**: `SystemHealthAgentResponse` with all results
- **Route file**: `services/fiqa_api/routes/ops_copilot.py`
- **Wired into**: `services/fiqa_api/app_main.py`

### Usage

**Python (direct)**:
```python
from services.fiqa_api.ops_copilot.graphs.system_health_graph import run_system_health_graph
from services.fiqa_api.ops_copilot.schemas import SystemSnapshot
from datetime import datetime

snapshot = SystemSnapshot(
    service_name="search-api",
    environment="prod",
    cpu_pct=82.0,
    mem_pct=78.0,
    p95_latency_ms=650.0,
    error_rate=0.03,
    qps=1200.0,
    disk_pct=88.0,
    timestamp=datetime.utcnow(),
)

result = run_system_health_graph(snapshot, request_id="req_123")
print(f"Band: {result['health_result'].band}")
print(f"Narrative: {result['narrative']}")
```

**HTTP (curl)**:
```bash
curl -X POST http://localhost:8001/api/ops-copilot/system-health \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "search-api",
    "environment": "prod",
    "cpu_pct": 82.0,
    "mem_pct": 78.0,
    "p95_latency_ms": 650.0,
    "error_rate": 0.03,
    "qps": 1200.0,
    "disk_pct": 88.0,
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

### LLM Explanation Layer

The `llm_explanation` node uses **mini-4o** (gpt-4o-mini) to generate SRE-friendly narratives:

- **Function**: `_generate_system_health_narrative()` in `ops_runtime.py`
- **Model**: `gpt-4o-mini` (hardcoded)
- **Timeout**: 20 seconds
- **Graceful degradation**: Falls back to deterministic narrative if LLM is disabled or fails
- **Output**: JSON with `narrative` (2-3 sentences) and `recommended_actions` (1-3 items)
- **Environment variable**: `LLM_GENERATION_ENABLED` (must be "true"/"1"/"yes"/"on" to enable)

## RAG on Ops Knowledge Base

The Ops Copilot includes a **RAG (Retrieval-Augmented Generation) layer** that provides vector-search-based context from the ops knowledge base. This complements the existing memory layer with semantic search capabilities.

### Overview

The RAG layer:
- Uses **Qdrant vector database** for storing embeddings of knowledge base chunks
- Performs **semantic search** based on service_name + symptom (risk_flag)
- Returns **top-k relevant snippets** (default: 3) with similarity scores
- Integrates seamlessly into the LLM explanation phase
- **Gracefully degrades** if index is unavailable (returns empty results, doesn't break workflow)

### Knowledge Sources

The RAG index is built from the same knowledge base files as the memory layer:
- `knowledge_base/runbooks.md` - Operational runbooks
- `knowledge_base/incidents.md` - Historical incidents
- `knowledge_base/configs.md` - Known risky configurations
- `knowledge_base/lessons_learned.md` - Operational lessons learned

### Technical Stack

- **Vector Search**: Qdrant collection `ops_kb`
- **Embeddings**: SentenceTransformer model (default: `sentence-transformers/all-MiniLM-L6-v2`)
- **Retriever**: `retrieve_ops_knowledge()` in `ops_rag_retriever.py`
- **Integration**: `fetch_rag_context_for_system()` in `ops_runtime.py`

### Integration Point

The RAG layer is integrated into the **system_health_graph** workflow:

1. **Health Check Node**: After computing health_result, calls `fetch_rag_context_for_system()`
   - Constructs query from `service_name` + first `risk_flag` (symptom)
   - Retrieves top 3 snippets from vector search
   - Stores results in `SystemContextSnapshot.rag_snippets`

2. **LLM Explanation Node**: RAG snippets are included in the prompt
   - Added as a separate section: "# RAG knowledge from ops knowledge base"
   - Each snippet formatted as: `[source=filename, score=0.XX] text preview`
   - LLM is instructed to reference source_file when applicable

### Safety Measures

- **Graceful degradation**: If vector search fails or index is unavailable, returns empty list
- **No breaking changes**: RAG is purely additive - existing functionality works without it
- **RAG is "enhancement only"**: RAG provides additional context but doesn't directly make decisions
- **Limited snippet count**: Only top 3 snippets are retrieved to avoid prompt bloat

### Building the Index

To build or rebuild the RAG index:

```bash
python experiments/build_ops_kb_index.py
```

This script:
1. Loads markdown files from `knowledge_base/`
2. Splits into chunks by `##` headers
3. Extracts service/symptom hints from headers
4. Generates embeddings and stores in Qdrant

### Example Usage

```python
from services.fiqa_api.ops_copilot.ops_runtime import fetch_rag_context_for_system
from services.fiqa_api.ops_copilot.schemas import SystemSnapshot, SystemHealthCheckResult

# After health check
rag_snippets = fetch_rag_context_for_system(
    snapshot=snapshot,
    health_result=health_result,
    top_n=3,
)

# Result: List[RagSnippet] with text, source_file, score, etc.
for snippet in rag_snippets:
    print(f"Source: {snippet.source_file}, Score: {snippet.score:.2f}")
    print(snippet.text[:100])
```

### Comparison with Memory Layer

The RAG layer complements the existing memory layer:

| Feature | Memory Layer | RAG Layer |
|---------|-------------|-----------|
| **Matching** | Simple text matching | Semantic vector search |
| **Query** | Service name + env/region | Service name + symptom |
| **Results** | Fixed snippets from files | Top-k relevant chunks |
| **Scoring** | None | Similarity score (0-1) |
| **Use Case** | Historical context | Symptom-specific knowledge |

Both layers are used together in the LLM explanation phase for comprehensive context.

---

## Memory Layer (File-Based Knowledge Base)

The Ops Copilot includes a lightweight **memory layer** that provides historical operational context from past incidents, runbooks, known configuration risks, and lessons learned.

### Overview

The memory layer is a file-based knowledge base stored in `knowledge_base/*.md` markdown files at the repository root. When generating LLM explanations, the Ops Copilot automatically loads relevant snippets based on the service name, environment, and region.

**Key Features**:
- Simple text matching (no complex NLP required)
- Service/environment/region filtering
- Graceful degradation (empty results if no matches)
- Limit 2-3 snippets per category to avoid prompt bloat
- Easy to maintain and update (just edit markdown files)

### Knowledge Base Structure

The knowledge base consists of 4 markdown files:

1. **`incidents.md`** - Historical incidents with:
   - Summary, impact, root cause
   - Mitigations taken
   - Follow-up actions
   - Examples: payment-service latency spike, api-gateway connection pool exhaustion

2. **`runbooks.md`** - Operational runbooks for common symptoms:
   - When to use (symptom detection)
   - Step-by-step remediation actions
   - Verification steps
   - Examples: high-error-rate, high-latency, disk-near-full

3. **`configs.md`** - Known risky configurations and best practices:
   - Retry policies, connection pool settings
   - Timeout configuration, resource limits
   - Trade-offs and recommendations
   - Examples: payment-service retry config, api-gateway connection pool

4. **`lessons_learned.md`** - High-level operational wisdom:
   - Avoid retry storms, prefer horizontal scaling
   - Cache invalidation strategies
   - Observability and proactive monitoring
   - Examples: deployment safety, capacity planning

### Usage

The memory layer is automatically invoked during the LLM explanation phase. It's wired into `_generate_system_health_narrative()` in `ops_runtime.py`:

```python
from services.fiqa_api.ops_copilot.memory import load_system_memory

# Load memory based on service/env/region
memory = load_system_memory(
    service_name="payment-service",
    env="prod",
    region="us-east-1",
    max_snippets_per_category=2,
    max_snippet_length=400,
)

# Result: dict with keys "incidents", "runbooks", "configs", "lessons"
# Each value is a list of relevant snippet strings
```

**Smoke Test**:
```bash
python3 experiments/ops_memory_smoke.py
```

This script demonstrates memory loading for several services (payment-service, api-gateway, search-api) and shows what snippets are retrieved.

### Integration with LLM Explanation

When the LLM generates a narrative, the prompt includes:
- **Recent incidents**: Past failures for this service/env
- **Known runbooks**: Remediation steps for similar symptoms
- **Risky configs**: Configuration pitfalls to be aware of
- **Lessons learned**: Operational best practices

This historical context helps the LLM provide more specific, actionable recommendations grounded in real operational data.

**Example LLM prompt enhancement**:
```
# Historical context (from system memory)

Past incidents:
  1. [payment-service][prod][us-east-1][2024-11-05] Latency spike and error storm
     Payment service experienced sudden latency spike (p95 > 3000ms) followed by 8% error rate...

Known runbooks:
  1. [service=payment-service][symptom=high-error-rate]
     When to use: Payment service error rate > 2% for 5+ minutes
     Step 1: Check external payment gateway status...

Known risky configs:
  1. [payment-service][prod] Retry Configuration
     Aggressive retry without backoff can amplify load on payment gateway...

Lessons learned:
  1. Avoid retry storms against single-region dependencies
     Multiple incidents were caused by aggressive retry logic...
```

### Current Implementation

- **Storage**: Local markdown files in `knowledge_base/`
- **Matching**: Simple text search (case-insensitive, substring matching)
- **Filtering**: By service name (required), environment (optional), region (optional)
- **Limit**: 2 snippets per category, 400 chars per snippet
- **Graceful degradation**: Returns empty lists if no matches found

### Future Extensions

- Replace text matching with vector search (RAG)
- Connect to real incident management systems (PagerDuty, Jira)
- Auto-populate knowledge base from production logs and postmortems
- Add versioning and approval workflow for knowledge base updates

---

## Semantic Ops Tools

The Ops Copilot includes 3 **semantic tools** that provide LLM-grounded operational context:

### 1. Log Query (`query_logs`)

Queries recent logs for a service and returns aggregated statistics with sample entries.

**Interface:**
```python
def query_logs(
    service_name: str,
    window_minutes: int = 15,
    max_samples: int = 5,
) -> LogSummary
```

**Returns:**
- Total log lines in window
- Error count, warning count
- Sample log entries (up to 5)

**Current Implementation:** Mock data with realistic log patterns (errors, warnings, timeouts, etc.)

**Future Implementation:** Connect to Splunk, Elasticsearch, CloudWatch Logs, or other log aggregation systems.

### 2. Runbook Fetch (`get_runbook`)

Fetches runbook guidance for a specific service and symptom (e.g., "high_latency", "high_error_rate").

**Interface:**
```python
def get_runbook(
    service_name: str,
    symptom: str,
) -> RunbookEntry
```

**Returns:**
- Runbook title and summary
- Step-by-step remediation actions
- Additional notes and context

**Current Implementation:** Template-based runbooks for common service/symptom combinations (e.g., "api-gateway + high_latency", "payment-service + high_error_rate"). Falls back to generic runbook if no exact match.

**Future Implementation:** Connect to internal runbook database, Confluence, PagerDuty runbooks, or other knowledge management systems.

### 3. Incident Summarization (`summarize_recent_incidents`)

Summarizes recent incidents for a service over a time window.

**Interface:**
```python
def summarize_recent_incidents(
    service_name: str,
    window_days: int = 30,
    max_items: int = 5,
) -> IncidentSummary
```

**Returns:**
- Total incident count
- Critical/high severity breakdown
- Recent incident records with root cause and resolution time

**Current Implementation:** Template-based incident history with realistic severity distribution and resolution times.

**Future Implementation:** Connect to PagerDuty, Jira, ServiceNow, or internal incident management systems.

### Integration with LLM Explanation

The semantic tools are automatically invoked during the health check phase:

1. **Always queried**: Logs (last 15 minutes) and incidents (last 30 days)
2. **Conditionally queried**: Runbook (only if degraded/critical)

The context is passed to the LLM explanation node, enriching the narrative with:
- Log error patterns ("Logs show 45 errors in last 15 min")
- Runbook guidance (key remediation steps)
- Historical incident context ("3 critical incidents in last 30 days")

**Example LLM prompt enhancement:**
```
Recent Logs (last 15 minutes):
  Total lines: 2345
  Errors: 45, Warnings: 123
  Sample errors/warnings:
    [ERROR] Timeout connecting to downstream service: connection timeout after 5000ms
    [ERROR] Database query failed: connection pool exhausted

Runbook Guidance:
  Title: API Gateway High Latency Remediation
  Summary: High latency in API gateway often caused by downstream service degradation...
  Key steps:
    1. Check downstream service health metrics
    2. Review connection pool settings
```

This semantic context enables the LLM to provide more specific, actionable recommendations grounded in operational data.

## Multi-Agent View

The Ops Copilot is designed with a **multi-agent architecture** that separates concerns into three logical agents, making it easy to explain and extend:

### 1. Health Analyst Agent

**Responsibility**: Analyze system health and gather diagnostic context.

**Functions**:
- Runs core health check (band, score, risk flags) via `run_system_health_check()`
- Loads operational context from semantic tools (logs, runbooks, incidents)
- Generates human-friendly analysis notes (e.g., "CPU and error rate both elevated - may indicate retry storm")

**Maps to**:
- LangGraph node: `health_check`
- Function: `run_health_analyst_agent()` in `ops_runtime.py`
- Output schema: `HealthAnalystOutput` with `health_result`, `context`, and `analysis_notes`

### 2. Remediation Planner Agent

**Responsibility**: Generate remediation strategies and what-if scenarios.

**Functions**:
- Generates safety upgrade suggestions via `run_safety_upgrade_for_system()` (if system is degraded/critical)
- Runs strategy lab analysis via `run_system_strategy_lab()` to explore alternative scenarios
- Provides planning notes about recommended actions (e.g., "Scenario X improves score from 34 → 52, recommend executing it first")

**Maps to**:
- LangGraph nodes: `safety_upgrade` + `strategy_lab`
- Function: `run_remediation_planner_agent()` in `ops_runtime.py`
- Output schema: `RemediationPlannerOutput` with `safety_suggestions`, `strategy_lab`, and `plan_notes`

### 3. Explainer Agent

**Responsibility**: Produce human-friendly explanations and actionable recommendations.

**Functions**:
- Generates SRE-friendly narrative via LLM (or fallback if LLM disabled)
- Extracts actionable recommendations for ops teams (e.g., "Scale horizontally by adding 2 replicas")
- Tracks LLM usage metadata (tokens, cost, model)

**Maps to**:
- LangGraph node: `llm_explanation`
- Function: `run_explainer_agent()` in `ops_runtime.py`
- Output schema: `ExplainerOutput` with `narrative`, `recommended_actions`, and `llm_usage`

### Multi-Agent Demo Script

To demonstrate the multi-agent architecture, use the dedicated demo script:

```bash
# Run all scenarios (default)
python experiments/ops_copilot_multi_agent_demo.py

# Run a single scenario
python experiments/ops_copilot_multi_agent_demo.py --scenario healthy
python experiments/ops_copilot_multi_agent_demo.py --scenario degraded
python experiments/ops_copilot_multi_agent_demo.py --scenario critical

# Disable LLM (skip Explainer agent)
python experiments/ops_copilot_multi_agent_demo.py --no-llm
```

The demo script clearly separates the output from each agent:

```
[HealthAnalyst]
  - band: critical
  - score: 0.0
  - risk_flags: [high_cpu, high_error_rate, disk_near_full]
  - notes:
    * System is critical with score 0.0 - immediate attention required
    * CPU and error rate both elevated - may indicate retry storm

[RemediationPlanner]
  - safety suggestions: 3 generated
    Best: Reduce QPS by 20% and add 1 replica
    Estimated improvement: 0.0 → 0.0
  - strategy lab: best scenario is 'Add 1 replica'
    Score change: 0.0 → 10.0 (+10.0)
  - notes:
    * Scenario 'Add 1 replica' improves score from 0.0 → 10.0, recommend executing it first

[Explainer]
  - narrative: The payment service is currently in a critical state...
  - recommended_actions:
    1) Add replicas to distribute load
    2) Investigate error root cause
```

### Why Multi-Agent?

This design makes it easy to:
1. **Explain in interviews** - clear separation of concerns (analyze → plan → explain)
2. **Extend independently** - each agent can be improved without affecting others
3. **Test in isolation** - unit test each agent's logic separately
4. **Parallelize** - agents can run concurrently when dependencies allow
5. **Swap implementations** - replace rule-based planner with ML-based planner, etc.

The multi-agent view is a **thin layer on top of existing logic** - no breaking changes, just better organization and storytelling.

## ReAct Planner for System Health (Deterministic vs Planner)

The Ops Copilot provides two entry points for system health analysis:

- **`run_system_health_graph()`** - Deterministic pipeline with fixed tool sequence: `health_check → safety_upgrade (if degraded/critical) → strategy_lab → action_planner → llm_explanation`
- **`run_system_health_graph_with_planner()`** - ReAct-style planner where LLM decides tool call sequence dynamically

### How the Planner Works

The ReAct planner (`react_planner.py`) implements a simple ReAct loop (max 3 steps):

1. **Step 1**: Always runs `health_check` if not provided
2. **Steps 2-3**: LLM reads current snapshot + tools menu (`health_check`, `safety_upgrade`, `strategy_lab`) and decides next action:
   - **Thought**: Analyzes current health status and what tools have been called
   - **Act**: Chooses a tool to call (or `finish` if done)
   - **Observe**: Sees tool result and optionally repeats

**Hard limits**: Max N steps (default: 3), only whitelisted tools from `TOOL_REGISTRY`, no direct side effects (all tools are read-only/plan-only).

### Alignment with CrowdStrike-Style Safety

- **LLM is read-only & plan-only**: The planner never executes config changes directly; all actions go through the structured `OpsActionPlan` layer
- **All tools are typed/whitelisted**: Only `health_check`, `safety_upgrade`, `strategy_lab` are available, with guardrails (e.g., `safety_upgrade` blocked for healthy systems)
- **Graceful degradation**: If LLM fails or is disabled, falls back to deterministic tool sequence
- **Dual-path strategy**: We keep the deterministic path for safety & regression testing, and use the planner path as an "intelligent orchestration layer" that can adapt tool order based on context

### Offline Evaluation

We provide an offline evaluation script (`experiments/offline_ops_planner_eval.py`) to compare deterministic vs planner on fixed test scenarios:

```bash
# Run both deterministic and planner versions
python experiments/offline_ops_planner_eval.py

# Run only planner version
python experiments/offline_ops_planner_eval.py --use-planner-only

# Enable verbose output (show agent step details)
python experiments/offline_ops_planner_eval.py --verbose
```

The script runs 5 test cases (healthy, degraded, critical, and variants) and prints comparison metrics:
- Health band & score
- Agent step counts
- Tool call counts
- Action plan sizes
- Planner-specific step traces

This makes it easy to review and explain the differences between deterministic and planner approaches during interviews or internal reviews.

## Future Extensions

1. ~~**LangGraph integration**~~ ✅ - Done
2. ~~**HTTP endpoints**~~ ✅ - Done
3. ~~**LLM explanations**~~ ✅ - Done
4. ~~**Semantic Ops Tools**~~ ✅ - Done (log query, runbook fetch, incident summarization)
5. ~~**Multi-Agent Architecture**~~ ✅ - Done (HealthAnalyst, RemediationPlanner, Explainer)
6. **Real-time metrics** - connect semantic tools to real log platforms (Splunk, Datadog, Elastic)
7. **RAG runbooks** - replace template-based runbooks with vector search over knowledge base
8. **Multi-service analysis** - analyze dependencies and cascading failures

## LangSmith / LangGraph Observability (Optional)

The Ops Copilot supports optional LangSmith tracing for observability of LangGraph workflow execution.

### Setup

Set environment variables to enable LangSmith tracing:

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_langsmith_api_key_here
export LANGCHAIN_PROJECT=searchforge-ops
```

### Usage

Once configured, all existing scripts and API endpoints automatically send traces to LangSmith:

- **Smoke tests**: `python experiments/ops_copilot_smoke.py`
- **System health agent smoke**: `python experiments/system_health_agent_smoke.py`
- **Demo script**: `python experiments/ops_copilot_demo.py --scenario degraded`
- **API calls**: Any request to `/api/ops-copilot/system-health` via frontend or Cloud Run

### What You'll See in LangSmith

In the LangSmith UI, you'll see:

- **Top-level trace**: `system_health_graph_run` - the entire workflow execution
  - Includes request_id, health band, score, and other metadata
  - Shows the full graph execution flow (health_check → safety_upgrade → strategy_lab → llm_explanation)
- **LLM explanation trace**: `ops_llm_explanation` - nested under the graph trace
  - Shows LLM prompts, responses, tokens, and latency

### Non-Intrusive Design

- **Zero impact when disabled**: If environment variables are not set, tracing is completely disabled (no performance impact)
- **Graceful degradation**: If langsmith package is not installed, tracing silently fails without breaking execution
- **No code changes required**: All tracing is handled via decorators, existing code logic remains unchanged

## Security & Guardrails

The Ops Copilot implements a multi-layered security and guardrails system to ensure safe, production-grade operation. These guardrails align with best practices for AI safety, prompt injection defense, and safe rollout strategies.

### Input Validation

**Module**: `services/fiqa_api/ops_copilot/input_validation.py`

Before any processing begins, all system snapshot inputs are validated for hard errors:

- **Range checks**: All percentage fields (CPU, memory, disk) must be in 0-100% range
- **Non-negative checks**: Latency (p95_latency_ms), error rate, and QPS must be non-negative
- **Error rate bounds**: Error rate must be in 0-1 range (0-100%)
- **Environment validation**: Environment must be one of: "prod", "staging", "dev"
- **Service name**: Service name cannot be empty

Invalid inputs are rejected with HTTP 400 status and detailed error messages. All validation failures are logged as security events for audit purposes.

**Security logging**: All input validation failures trigger `input_validation_failed` security events with context (field name, invalid value, service_name, environment).

### Output Guardrails

**Function**: `apply_ops_output_guardrails()` in `ops_runtime.py`

The LLM-generated narrative and recommendations are checked and adjusted to ensure they are sufficiently urgent for critical cases:

- **Critical/hard_block cases**: If `health_result.hard_block = True` or `band = "critical"`, the narrative MUST contain urgent language (e.g., "立即", "CRITICAL", "emergency"). If missing, urgent language is prepended.
- **Emergency actions**: Recommended actions must include emergency actions (e.g., "降流量", "增加副本", "触发应急runbook"). If missing, standard emergency actions are prepended.
- **Degraded cases**: For `band = "degraded"` cases, the narrative should mention priority. If missing, a priority note is appended.

**Security logging**: All narrative adjustments trigger `narrative_guardrail_adjusted` security events with context (reason, band, hard_block status, what was adjusted).

### Tool-level Guardrails

**Structure**: `SENSITIVE_TOOLS` in `ops_runtime.py`, `guard_tool_call()` function

The Ops Copilot includes a foundation for tool-level guardrails to protect against dangerous tool calls:

- **Sensitive tools registry**: Defines which tools require guardrails (e.g., `apply_config_change`, `trigger_emergency_rollback`)
- **Environment restrictions**: Tools can be restricted to specific environments (e.g., only allow `apply_config_change` in staging, not prod)
- **Dry-run mode**: All tools are currently in dry-run mode (suggestions only, no execution)

**Current status**: All tools are read-only (suggestions only). The guardrail structure is in place for future tools that could modify production configurations.

**Security logging**: Tool call attempts (even in dry-run mode) are logged as `tool_call_blocked` security events with context (tool name, environment, reason).

### Security Event Logging

**Module**: `services/fiqa_api/observability/security_events.py`

All security-related events are logged to a dedicated "security" logger:

- **Event types**: `input_validation_failed`, `hard_blocked_request`, `tool_call_blocked`, `narrative_guardrail_adjusted`
- **Structured logging**: All events include `event_type`, `request_id`, `timestamp`, and context
- **Exception-safe**: Logging failures never impact the main request flow
- **Audit trail**: Security events provide a complete audit trail for compliance and incident investigation

**Usage in interviews**: These guardrails demonstrate production-grade safety practices, including:
- **Prompt injection defense**: Input validation prevents malformed requests
- **Safe rollout**: Output guardrails ensure urgent messaging even if LLM misbehaves
- **Tool safety**: Tool-level guardrails prevent dangerous operations in production
- **Audit compliance**: All security events are logged for regulatory compliance

## Plan / Act Separation & OpsActionPlan

The Ops Copilot implements a strict **"think / act separation"** architecture to ensure safety and clarity:

### Core Principle

**LLM is read-only and plan-only** - all "actions" are only output as structured `OpsActionPlan` objects. The LLM never executes any real operations, never calls any external APIs (Kubernetes, Cloud Run, database config changes, etc.).

### OpsActionPlan Structure

All proposed actions are encapsulated in structured `OpsActionPlan` and `OpsAction` models:

- **`OpsActionPlan`**: Contains a list of planned actions for a service, along with metadata (band, hard_block, generated_at, notes, num_actions_blocked, num_actions_require_human)
- **`OpsAction`**: Represents a single planned action with:
  - `action_type`: One of `reduce_qps`, `add_replica`, `reduce_error_rate`, `adjust_timeout`, `tune_retry_policy`
  - `target_service`: Target service name (defaults to snapshot.service_name)
  - `severity`: `info`, `warning`, or `critical` (determined by health_result.band and hard_block)
  - `reason`: Brief explanation combining risk_flags and action rationale (e.g., "high_error_rate + high_latency — reduce QPS to relieve upstream pressure")
  - `summary`: One-sentence description
  - `estimated_before_score` / `estimated_after_score` / `estimated_delta`: Health score estimates and change
  - `require_human_approval`: Boolean flag (set to `True` for critical/high-risk scenarios)
  - `source`: Either `safety_suggestions` or `strategy_lab`

### Action Planning Flow

1. **Health Check** → identifies health issues
2. **Safety Upgrade** → generates safety suggestions (if degraded/critical)
3. **Strategy Lab** → explores what-if scenarios
4. **Action Planner** → converts suggestions/scenarios into structured `OpsActionPlan` (PLAN ONLY, no execution)
5. **LLM Explanation** → reads `OpsActionPlan` and translates it into human-friendly narrative

### Execution Safety

All actions in `OpsActionPlan` are **plan-only suggestions**. If real execution is needed in the future, it must go through:

- A separate `safe_apply` service with GuardRails
- Human approval workflow
- Whitelisted action types only
- Environment restrictions (e.g., staging only)
- Audit logging

### Audit Logging

Every OpsActionPlan is also written to an audit log (`ops_copilot.audit` logger). The audit log captures all proposed actions (type, target service, severity, estimated impact, human-approval flag), so we can replay and review what the agent wanted to do even though it never executes changes directly.

The audit log is only written for `degraded` or `critical` scenarios with at least one action, to avoid log explosion. Audit log failures are handled gracefully and never affect the main request flow.

### LLM Instructions

The LLM explanation layer is explicitly instructed:

```
IMPORTANT: You MUST treat any proposed actions as plan-only suggestions.
You NEVER execute them. You only explain them and, if necessary, prioritize them.
Execution is handled by a separate system with GuardRails and human approval.
Your role is read-only and plan-only.
```

### Guardrail Validation

The `validate_ops_action_plan()` function applies high-risk guardrails to action plans:

- **Critical/high-risk scenarios**: When `health_result.band == "critical"` or `"high_error_rate"` / `"disk_near_full"` in risk_flags:
  - All actions are automatically marked with `require_human_approval=True`
  - Dangerous action types (e.g., `scale_up_traffic`, `shift_traffic_to_single_region`) are blocked
  - Unknown action types are removed and logged in plan.notes
- **Statistics**: The plan tracks `num_actions_blocked` and `num_actions_require_human` for audit/eval purposes
- **Audit trail**: All guardrail decisions are logged in plan.notes for transparency

**Key principle**: In critical / high_error_rate / disk_near_full scenarios, all actions are marked as requiring human approval, and human SREs are the final executors.

### Summary

**"In Ops Copilot, the LLM is read-only and plan-only; all write actions must go through a whitelisted, validated OpsAction layer."**

This separation ensures:
- **Safety**: No accidental production changes
- **Clarity**: Clear distinction between "thinking" (planning) and "acting" (execution)
- **Auditability**: All planned actions are structured and traceable
- **Guardrails**: High-risk scenarios automatically require human approval
- **Interview-ready**: Easy to explain the architecture and safety model

## Notes

- This is a **skeleton** - minimal but coherent implementation
- **No dependencies on mortgage modules** - standalone within the repo
- **Rule-based only** - no LLM calls, designed for offline evaluation
- **Interview-ready** - demonstrates system design, guardrails, and evaluation practices
- **Production-grade security** - multi-layered guardrails with security event logging
- **Plan / Act separation** - all actions are plan-only, execution requires separate safe_apply service

