"""
Main FastAPI Server for FIQA API Agent

This module provides a web API that orchestrates the complete Agent pipeline:
Router -> Planner -> Executor -> Judge, exposing it through a single endpoint.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, AsyncGenerator
import uvicorn
import json
import asyncio
from pathlib import Path
import os

from agent.router import Router
from agent.planner import Planner
from agent.executor import Executor
from agent.judge import Judge
from agent.explainer import Explainer
from services.code_intelligence.ai_analyzer import get_node_intelligence
from tools.codegraph import CodeGraph
from engines.networkx_engine import NetworkXEngine
try:
    # Preferred import path when package structure allows
    from services.code_intelligence.golden_path import extract_golden_path  # type: ignore
except Exception:
    # Fallback: import module directly from services/code_intelligence
    import sys as _sys
    from pathlib import Path as _Path
    _gp_dir = _Path(__file__).parent.parent / "code_intelligence"
    if str(_gp_dir) not in _sys.path:
        _sys.path.insert(0, str(_gp_dir))
    from golden_path import extract_golden_path  # type: ignore
from services.code_intelligence.graph_ranker import layer2_graph_ranking


def calculate_llm_cost(usage, model_name: str = "gpt-4o-mini") -> float:
    """
    Calculate the cost in USD for LLM usage based on token counts.
    
    Args:
        usage: OpenAI usage object containing prompt_tokens, completion_tokens, total_tokens
        model_name: Name of the model used (default: gpt-4o-mini)
        
    Returns:
        Cost in USD as a float
    """
    if not usage:
        return 0.0
    
    # Pricing for gpt-4o-mini (as of 2024)
    # Input: $0.15 per 1M tokens
    # Output: $0.60 per 1M tokens
    input_cost_per_token = 0.15 / 1_000_000
    output_cost_per_token = 0.60 / 1_000_000
    
    prompt_tokens = getattr(usage, 'prompt_tokens', 0)
    completion_tokens = getattr(usage, 'completion_tokens', 0)
    
    total_cost = (prompt_tokens * input_cost_per_token) + (completion_tokens * output_cost_per_token)
    return round(total_cost, 6)  # Round to 6 decimal places for precision


# Pydantic models for request/response validation
class QueryRequest(BaseModel):
    """Request model for the query endpoint."""
    query: str


class QueryResponse(BaseModel):
    """Response model for successful queries."""
    success: bool
    data: Any  # Changed from Dict[str, Any] to Any to handle both dict and list
    explanation: str = ""  # Markdown explanation from Explainer
    trace: Dict[str, Any] = {}  # Execution trace including plan and verdict
    message: str = "Query executed successfully"


class ErrorResponse(BaseModel):
    """Response model for failed queries."""
    success: bool = False
    error: str
    issues: list = []


# Initialize FastAPI app
app = FastAPI(
    title="FIQA API Agent",
    description="A code analysis agent that provides insights about repository structure and function relationships",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global variables for component instances (initialized on startup)
codegraph: CodeGraph = None
router: Router = None
planner: Planner = None
executor: Executor = None
judge: Judge = None
explainer: Explainer = None
graph_engine: NetworkXEngine = None
redis_client = None

# Instantiate NetworkXEngine at module import with explicit graph path
try:
    _current_dir = Path(__file__).parent
    _graph_path = _current_dir.parent.parent / "codegraph.v1.json"
    graph_engine = NetworkXEngine(str(_graph_path))
except Exception:
    graph_engine = None


@app.on_event("startup")
async def startup_event():
    """Initialize all Agent components on server startup."""
    global codegraph, router, planner, executor, judge, explainer
    global graph_engine, redis_client
    
    try:
        # Get the path to codegraph.v1.json relative to this file
        current_dir = Path(__file__).parent
        codegraph_path = current_dir.parent.parent / "codegraph.v1.json"
        
        if not codegraph_path.exists():
            raise FileNotFoundError(f"CodeGraph file not found at {codegraph_path}")
        
        print(f"🚀 Initializing Agent components...")
        
        # Initialize CodeGraph tool
        codegraph = CodeGraph(str(codegraph_path))
        print(f"✅ CodeGraph loaded: {codegraph.get_graph_stats()['total_nodes']} nodes")
        
        # Initialize Agent components
        router = Router()
        planner = Planner()
        executor = Executor(codegraph)
        judge = Judge()
        explainer = Explainer()
        
        # Initialize Redis client (optional caching)
        try:
            from redis.asyncio import Redis  # type: ignore
        except Exception:
            Redis = None  # type: ignore

        redis_client = None
        if 'Redis' in locals() and Redis is not None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            try:
                redis_client = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
                await redis_client.ping()
                print(f"✅ Redis connected at {redis_url}")
            except Exception as re:
                redis_client = None
                print(f"⚠️ Redis unavailable ({re}); proceeding without caching")

        print(f"✅ Agent components initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize Agent components: {e}")
        raise


@app.get("/api/v1/graph/golden-path")
async def api_golden_path(entry: str = Query(..., description="Entry node id")):
    """Return the Golden Path from the given entry node.

    Uses AI labels (if available) to target the nearest Core node. Falls back to
    a shortest path to the PageRank top-1 node. Ensures 5-9 nodes in the result
    where possible.
    """
    try:
        if graph_engine is None or getattr(graph_engine, "graph", None) is None:
            raise HTTPException(status_code=503, detail="Graph engine not initialized")

        graph = graph_engine.graph

        # Build a best-effort AI labels mapping from node attributes if present
        ai_labels = {}
        try:
            for node_id, attrs in graph.nodes(data=True):
                label = attrs.get("ai_label") or attrs.get("layer3_label")
                tags = attrs.get("ai_tags") or attrs.get("tags")
                if label is not None:
                    ai_labels[str(node_id)] = label
                elif isinstance(tags, (list, tuple)) and ("Core" in tags):
                    ai_labels[str(node_id)] = "Core"
        except Exception:
            ai_labels = {}

        path = extract_golden_path(entry_node_id=str(entry), graph=graph, ai_labels=ai_labels)
        return {"path": path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute golden path: {e}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "FIQA API Agent",
        "version": "1.0.0",
        "endpoints": {
            "POST /v1/query": "Execute a code analysis query",
            "GET /v1/stream": "Stream query execution with real-time events",
            "GET /health": "Health check endpoint"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check if all components are initialized
        if not all([codegraph, router, planner, executor, judge, explainer]):
            raise HTTPException(status_code=503, detail="Agent components not initialized")
        
        # Test CodeGraph connectivity
        stats = codegraph.get_graph_stats()
        
        return {
            "status": "healthy",
            "components": {
                "codegraph": "ready",
                "router": "ready", 
                "planner": "ready",
                "executor": "ready",
                "judge": "ready",
                "explainer": "ready"
            },
            "codegraph_stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.post("/v1/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Execute a code analysis query through the complete Agent pipeline.
    
    This endpoint orchestrates the Router -> Planner -> Executor -> Judge pipeline
    to process user queries and return validated results.
    """
    try:
        # Validate that all components are initialized
        if not all([codegraph, router, planner, executor, judge, explainer]):
            raise HTTPException(
                status_code=503, 
                detail="Agent components not initialized"
            )
        
        # Step 1: Router processes the query
        print(f"🔍 Processing query: '{request.query}'")
        structured_query = router.route_query(request.query)
        print(f"📋 Router output: {structured_query}")
        
        # Step 2: Planner creates action plan
        plan = planner.create_plan(structured_query)
        print(f"📝 Planner goal: {plan['goal']}")
        print(f"📝 Planner steps: {len(plan['steps'])} step(s)")
        
        # Step 3: Executor executes the plan
        execution_result = executor.execute_plan(plan)
        print(f"⚙️ Executor success: {execution_result['success']}")
        
        if not execution_result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"Execution failed: {execution_result['error']}"
            )
        
        # Step 4: Judge reviews the result
        review = judge.review_execution_result(execution_result)
        print(f"⚖️ Judge verdict: {review['verdict']}")
        
        # Handle Judge verdict
        if review['verdict'] == 'pass':
            # Step 5: Explainer generates explanation
            explainer_result = explainer.generate_explanation(execution_result['result'])
            explanation = explainer_result['explanation']
            print(f"📝 Explainer generated explanation: {len(explanation)} characters")
            
            # Build trace information
            trace = {
                "plan": plan,
                "verdict": review['verdict']
            }
            
            # Return successful result with explanation and trace
            return QueryResponse(
                success=True,
                data=execution_result['result'],
                explanation=explanation,
                trace=trace,
                message="Query executed successfully"
            )
        
        elif review['verdict'] == 'revise':
            # Return validation issues
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Query result failed validation",
                    "issues": review['issues']
                }
            )
        
        else:
            # Unexpected verdict
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected Judge verdict: {review['verdict']}"
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    
    except Exception as e:
        # Handle unexpected errors
        print(f"❌ Unexpected error in query execution: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/v1/supported-queries")
async def get_supported_queries():
    """Get information about supported query types and examples."""
    try:
        if not router:
            raise HTTPException(status_code=503, detail="Router not initialized")
        
        return {
            "supported_intents": router.get_supported_intents(),
            "examples": {
                "overview": [
                    "#overview",
                    "what is the repository",
                    "show me an overview"
                ],
                "file_analysis": [
                    "#file src/api/routes.py",
                    "analyze the file at services/main.py",
                    "examine the code at src/utils.py"
                ],
                "function_analysis": [
                    "#func my_app.utils.clean_data",
                    "analyze the function process_data",
                    "examine the method validate_input"
                ]
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get supported queries: {str(e)}"
        )


async def run_agent_streaming(goal: str) -> AsyncGenerator[str, None]:
    """
    Async generator that orchestrates the Router -> Planner -> Executor -> Judge -> Explainer pipeline
    and yields standardized events at each critical step.
    
    Args:
        goal: The user's query string
        
    Yields:
        JSON strings following the standardized event schema
    """
    try:
        # Validate that all components are initialized
        if not all([codegraph, router, planner, executor, judge, explainer]):
            yield json.dumps({
                "event": "error",
                "step": "S0",
                "goal": goal,
                "error": "Agent components not initialized"
            })
            return
        
        # Step 1: Router processes the query
        yield json.dumps({
            "event": "plan",
            "step": "S1",
            "goal": goal,
            "tool": "router.route_query",
            "args_redacted": {},
            "observation_summary": "Processing query with router",
            "evidence": [],
            "model": None,
            "tokens": {"in": 0, "out": 0, "cost_usd": 0.0},
            "cache_hit": False,
            "cost": {"ms": 0, "tokens": 0},
            "final_data": None
        })
        
        # Add small delay for async behavior
        await asyncio.sleep(0.01)
        
        structured_query = router.route_query(goal)
        
        yield json.dumps({
            "event": "tool_result",
            "step": "S1",
            "goal": goal,
            "tool": "router.route_query",
            "args_redacted": {},
            "observation_summary": f"Router classified query as: {structured_query.get('type', 'unknown')}",
            "evidence": [],
            "model": None,
            "tokens": {"in": 0, "out": 0, "cost_usd": 0.0},
            "cache_hit": False,
            "cost": {"ms": 0, "tokens": 0},
            "final_data": None
        })
        
        # Step 2: Planner creates action plan
        yield json.dumps({
            "event": "plan",
            "step": "S2",
            "goal": goal,
            "tool": "planner.create_plan",
            "args_redacted": {},
            "observation_summary": "Creating action plan",
            "evidence": [],
            "model": None,
            "tokens": {"in": 0, "out": 0, "cost_usd": 0.0},
            "cache_hit": False,
            "cost": {"ms": 0, "tokens": 0},
            "final_data": None
        })
        
        # Add small delay for async behavior
        await asyncio.sleep(0.01)
        
        plan = planner.create_plan(structured_query)
        
        yield json.dumps({
            "event": "tool_result",
            "step": "S2",
            "goal": goal,
            "tool": "planner.create_plan",
            "args_redacted": {},
            "observation_summary": f"Plan created with {len(plan.get('steps', []))} steps",
            "evidence": [],
            "model": None,
            "tokens": {"in": 0, "out": 0, "cost_usd": 0.0},
            "cache_hit": False,
            "cost": {"ms": 0, "tokens": 0},
            "final_data": None
        })
        
        # Step 3: Executor executes the plan
        step_count = 0
        for i, step in enumerate(plan.get('steps', [])):
            step_count += 1
            step_id = f"S{2 + step_count}"
            
            # Tool start event
            yield json.dumps({
                "event": "tool_start",
                "step": step_id,
                "goal": goal,
                "tool": step.get('tool', 'unknown'),
                "args_redacted": step.get('args', {}),
                "observation_summary": f"Starting execution of step {i+1}",
                "evidence": [],
                "model": None,
                "tokens": {"in": 0, "out": 0, "cost_usd": 0.0},
                "cache_hit": False,
                "cost": {"ms": 0, "tokens": 0},
                "final_data": None
            })
            
            # Execute the step
            result = executor._execute_step(step, [])
            
            # Add small delay for async behavior
            await asyncio.sleep(0.01)
            
            # Tool result event
            yield json.dumps({
                "event": "tool_result",
                "step": step_id,
                "goal": goal,
                "tool": step.get('tool', 'unknown'),
                "args_redacted": step.get('args', {}),
                "observation_summary": f"Step {i+1} completed successfully" if not isinstance(result, dict) or not result.get('error') else f"Step {i+1} failed: {result.get('error', 'Unknown error')}",
                "evidence": [],
                "model": None,
                "tokens": {"in": 0, "out": 0, "cost_usd": 0.0},
                "cache_hit": False,
                "cost": {"ms": 0, "tokens": 0},
                "final_data": None
            })
            
            # If step failed, break execution
            if isinstance(result, dict) and result.get('error'):
                yield json.dumps({
                    "event": "error",
                    "step": step_id,
                    "goal": goal,
                    "error": f"Execution failed at step {i+1}: {result['error']}"
                })
                return
        
        # Get final execution result
        execution_result = executor.execute_plan(plan)
        
        if not execution_result['success']:
            yield json.dumps({
                "event": "error",
                "step": "S3",
                "goal": goal,
                "error": f"Execution failed: {execution_result['error']}"
            })
            return
        
        # Step 4: Judge reviews the result
        yield json.dumps({
            "event": "judge",
            "step": "S4",
            "goal": goal,
            "tool": "judge.review_execution_result",
            "args_redacted": {},
            "observation_summary": "Reviewing execution result for evidence completeness",
            "evidence": [],
            "model": None,
            "tokens": {"in": 0, "out": 0, "cost_usd": 0.0},
            "cache_hit": False,
            "cost": {"ms": 0, "tokens": 0},
            "final_data": None
        })
        
        review = judge.review_execution_result(execution_result)
        print(f"🔍 Judge verdict: {review['verdict']}, issues: {review.get('issues', [])}")
        
        yield json.dumps({
            "event": "judge",
            "step": "S4",
            "goal": goal,
            "tool": "judge.review_execution_result",
            "args_redacted": {},
            "observation_summary": f"Judge verdict: {review['verdict']}",
            "evidence": [],
            "model": None,
            "tokens": {"in": 0, "out": 0, "cost_usd": 0.0},
            "cache_hit": False,
            "cost": {"ms": 0, "tokens": 0},
            "final_data": None
        })
        
        # Handle Judge verdict
        if review['verdict'] == 'pass':
            # Step 5: Explainer generates explanation
            yield json.dumps({
                "event": "llm_result",
                "step": "S5",
                "goal": goal,
                "tool": "explainer.generate_explanation",
                "args_redacted": {},
                "observation_summary": "Generating explanation using LLM",
                "evidence": [],
                "model": explainer.model_name,
                "tokens": {"in": 0, "out": 0, "cost_usd": 0.0},
                "cache_hit": False,
                "cost": {"ms": 0, "tokens": 0},
                "final_data": None
            })
            
            # Call explainer and get both explanation and usage data
            explainer_result = explainer.generate_explanation(execution_result['result'])
            explanation = explainer_result['explanation']
            usage = explainer_result['usage']
            
            # Calculate cost and extract token counts
            cost_usd = calculate_llm_cost(usage, explainer.model_name)
            prompt_tokens = getattr(usage, 'prompt_tokens', 0) if usage else 0
            completion_tokens = getattr(usage, 'completion_tokens', 0) if usage else 0
            total_tokens = getattr(usage, 'total_tokens', 0) if usage else 0
            
            yield json.dumps({
                "event": "llm_result",
                "step": "S5",
                "goal": goal,
                "tool": "explainer.generate_explanation",
                "args_redacted": {},
                "observation_summary": f"Generated explanation: {len(explanation)} characters",
                "evidence": [],
                "model": explainer.model_name,
                "tokens": {"in": prompt_tokens, "out": completion_tokens, "cost_usd": cost_usd},
                "cache_hit": False,
                "cost": {"ms": 0, "tokens": total_tokens},
                "final_data": None
            })
            
            # Extract the root node ID from the execution result
            # The result may be nested; unwrap it robustly
            def _unwrap_result(data):
                current = data
                depth = 0
                # Unwrap up to a reasonable depth to avoid infinite loops
                while isinstance(current, dict) and 'result' in current and depth < 10:
                    current = current['result']
                    depth += 1
                return current

            result_data = _unwrap_result(execution_result.get('result'))
            root_node_id = None
            all_node_ids = []
            file_path = None
            
            # Check if this is a file query by examining the plan
            is_file_query = False
            if plan and 'steps' in plan and len(plan['steps']) > 0:
                first_step = plan['steps'][0]
                if first_step.get('tool') == 'codegraph.get_nodes_by_file':
                    is_file_query = True
                    file_path = first_step.get('args', {}).get('file_path')
            
            # Try to extract nodes from various possible structures
            nodes = []
            if isinstance(result_data, dict):
                nodes = (
                    result_data.get('nodes') or
                    result_data.get('matches') or
                    result_data.get('items') or
                    []
                )
            elif isinstance(result_data, list):
                # Some tools may return a plain list of nodes
                nodes = result_data
            
            # Collect all node IDs (with robust field fallback)
            def _get_node_id(node: dict):
                if not isinstance(node, dict):
                    return None
                return (
                    node.get('id') or
                    node.get('node_id') or
                    node.get('fid') or
                    node.get('uid') or
                    node.get('name')
                )

            if nodes and len(nodes) > 0:
                all_node_ids = [nid for nid in (_get_node_id(node) for node in nodes) if nid]
                root_node_id = all_node_ids[0] if all_node_ids else None
            
            print(f"🔍 Extracted root_node_id: {root_node_id}, total nodes: {len(all_node_ids)}, is_file_query: {is_file_query}")
            
            # Determine if this should be a multi-result response
            # Multi-result conditions:
            # 1. Not a file query (file queries return all nodes in the file, which is expected)
            # 2. Multiple nodes found (more than 1) – use either collected IDs or the raw list length
            # 3. Query doesn't explicitly target a specific function (doesn't start with #func)
            nodes_count = len(nodes) if isinstance(nodes, list) else 0
            is_ambiguous_query = (
                not is_file_query
                and (len(all_node_ids) > 1 or nodes_count > 1)
                and not goal.strip().startswith('#func')
            )
            
            # Build final data payload based on result type
            if is_ambiguous_query:
                # MULTI-RESULT FORMAT: Return list of results for user selection
                print(f"🔍 Ambiguous query detected: {len(all_node_ids)} potential results")
                results_list = []
                for node in nodes[:10]:  # Limit to top 10 results
                    if not isinstance(node, dict):
                        continue
                    node_id = _get_node_id(node)
                    # Try multiple possible field names for fully qualified name
                    fq_name = (
                        node.get('fqName') or
                        node.get('fqname') or
                        node.get('qualified_name') or
                        node.get('name') or
                        node_id or
                        ''
                    )
                    # Try multiple possible field names for kind/type
                    kind = node.get('kind') or node.get('type') or node.get('node_type') or 'unknown'
                    # Try multiple possible field names for code snippet
                    evidence = node.get('evidence')
                    evidence_snippet = evidence.get('snippet', '') if isinstance(evidence, dict) else ''
                    snippet = (
                        node.get('snippet') or
                        node.get('code') or
                        node.get('codeSnippet') or
                        node.get('code_snippet') or
                        node.get('text') or
                        evidence_snippet
                    )

                    results_list.append({
                        'id': node_id or '',
                        'fqName': fq_name,
                        'kind': kind,
                        'snippet': (snippet or '')[:200]  # Limit snippet length
                    })
                
                final_data_payload = {
                    "success": True,
                    "results": results_list,
                    "explanation": f"I found {len(results_list)} potential matches for your query. Please select the one you're looking for.",
                    "trace": {
                        "plan": plan,
                        "verdict": review['verdict']
                    },
                    "message": f"Multiple results found: {len(results_list)} matches"
                }
            elif (not is_file_query) and (not goal.strip().startswith('#func')):
                # FALLBACK: If we didn't get nodes from the executed plan (e.g., unknown query -> graph_stats),
                # perform a lightweight fuzzy search locally across the in-memory codegraph for symbol-like queries.
                query_term = goal.strip()
                results_list = []
                if query_term and len(query_term) >= 2 and codegraph and hasattr(codegraph, 'nodes'):
                    term_lower = query_term.lower()
                    # find up to 20 nodes whose fqName or trailing name contains the query term
                    for node in codegraph.nodes:
                        if not isinstance(node, dict):
                            continue
                        fq_name = node.get('fqName') or node.get('fqname') or node.get('name') or ''
                        fq_lower = str(fq_name).lower()
                        tail = fq_lower.split('.')[-1]
                        if term_lower in fq_lower or term_lower in tail:
                            node_id = node.get('id') or node.get('node_id') or node.get('fid') or node.get('uid') or node.get('name')
                            kind = node.get('kind') or node.get('type') or node.get('node_type') or 'unknown'
                            evidence = node.get('evidence')
                            evidence_snippet = evidence.get('snippet', '') if isinstance(evidence, dict) else ''
                            snippet = (
                                node.get('snippet') or node.get('code') or node.get('codeSnippet') or node.get('code_snippet') or node.get('text') or evidence_snippet
                            )
                            results_list.append({
                                'id': node_id or '',
                                'fqName': fq_name,
                                'kind': kind,
                                'snippet': (snippet or '')[:200]
                            })
                            if len(results_list) >= 20:
                                break
                if results_list:
                    final_data_payload = {
                        "success": True,
                        "results": results_list,
                        "explanation": f"I found {len(results_list)} potential matches for '{query_term}'.",
                        "trace": {
                            "plan": plan,
                            "verdict": review['verdict']
                        },
                        "message": f"Multiple results found via fuzzy search: {len(results_list)} matches"
                    }
                else:
                    # SINGLE-RESULT FORMAT: Return single rootNodeId (existing behavior)
                    final_data_payload = {
                        "success": True,
                        "rootNodeId": root_node_id,
                        "explanation": explanation,
                        "trace": {
                            "plan": plan,
                            "verdict": review['verdict']
                        },
                        "message": "Query executed successfully"
                    }
                    
                    # For file queries, include file path instead of all node IDs
                    if is_file_query and file_path:
                        final_data_payload["filePath"] = file_path
                        final_data_payload["nodeCount"] = len(all_node_ids)
                    # For non-file queries with multiple nodes, include all node IDs
                    elif len(all_node_ids) > 1:
                        final_data_payload["allNodeIds"] = all_node_ids
            else:
                # SINGLE-RESULT FORMAT: Return single rootNodeId (existing behavior)
                final_data_payload = {
                    "success": True,
                    "rootNodeId": root_node_id,
                    "explanation": explanation,
                    "trace": {
                        "plan": plan,
                        "verdict": review['verdict']
                    },
                    "message": "Query executed successfully"
                }
                
                # For file queries, include file path instead of all node IDs
                if is_file_query and file_path:
                    final_data_payload["filePath"] = file_path
                    final_data_payload["nodeCount"] = len(all_node_ids)
                # For non-file queries with multiple nodes, include all node IDs
                elif len(all_node_ids) > 1:
                    final_data_payload["allNodeIds"] = all_node_ids
            
            yield json.dumps({
                "event": "final",
                "step": "S6",
                "goal": goal,
                "tool": None,
                "args_redacted": {},
                "observation_summary": "Query execution completed successfully",
                "evidence": [],
                "model": explainer.model_name,
                "tokens": {"in": prompt_tokens, "out": completion_tokens, "cost_usd": cost_usd},
                "cache_hit": False,
                "cost": {"ms": 0, "tokens": total_tokens},
                "final_data": final_data_payload
            })
        
        elif review['verdict'] == 'revise':
            yield json.dumps({
                "event": "final",
                "step": "S6",
                "goal": goal,
                "tool": None,
                "args_redacted": {},
                "observation_summary": "Query result failed validation",
                "evidence": [],
                "model": None,
                "tokens": {"in": 0, "out": 0, "cost_usd": 0.0},
                "cache_hit": False,
                "cost": {"ms": 0, "tokens": 0},
                "final_data": {
                    "success": False,
                    "error": "Query result failed validation",
                    "issues": review['issues']
                }
            })
        
        else:
            yield json.dumps({
                "event": "error",
                "step": "S6",
                "goal": goal,
                "error": f"Unexpected Judge verdict: {review['verdict']}"
            })
    
    except Exception as e:
        yield json.dumps({
            "event": "error",
            "step": "S0",
            "goal": goal,
            "error": f"Unexpected error: {str(e)}"
        })


@app.get("/api/v1/graph/neighborhood/{node_id}")
async def get_neighborhood_subgraph(
    node_id: str,
    depth: int = Query(2, description="Number of hops to traverse from the node", ge=0, le=5)
):
    """
    Get a neighborhood subgraph centered around a specific node.

    This endpoint provides on-demand subgraph loading, returning only the nodes
    and edges within the specified depth from the given node. This enables
    efficient, context-aware graph visualization.

    Args:
        node_id: The ID of the central node
        depth: Number of hops to traverse (default: 2, min: 0, max: 5)

    Returns:
        JSON response with nodes and edges in the neighborhood
    """
    try:
        # Validate that graph engine is initialized
        if not graph_engine:
            raise HTTPException(
                status_code=503,
                detail="Graph engine not initialized"
            )

        # Redis cache get
        cache_key = f"graph:neighborhood:{node_id}:{depth}"
        cached_payload = None
        if redis_client is not None:
            try:
                cached_payload = await redis_client.get(cache_key)  # type: ignore
            except Exception:
                cached_payload = None

        if cached_payload:
            try:
                return json.loads(cached_payload)
            except Exception:
                pass

        # Compute via engine
        result = graph_engine.get_neighborhood(node_id, depth)

        if not result.get('nodes'):
            raise HTTPException(
                status_code=404,
                detail=f"Node with ID '{node_id}' not found in the graph"
            )

        # Cache for 5 minutes
        if redis_client is not None:
            try:
                await redis_client.setex(cache_key, 300, json.dumps(result))  # type: ignore
            except Exception:
                pass

        return result

    except HTTPException:
        raise

    except Exception as e:
        print(f"❌ Error fetching neighborhood: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch neighborhood: {str(e)}"
        )


@app.get("/api/v1/graph/file/{file_path:path}")
async def get_file_subgraph(file_path: str):
    """
    Get all nodes and internal edges from a specific file.
    
    This endpoint returns only the nodes defined in the specified file and
    the edges between those nodes (internal file connections), without
    loading external dependencies or callers.
    
    Args:
        file_path: Relative path to the file
        
    Returns:
        JSON response with nodes and edges internal to the file
    """
    try:
        # Validate that codegraph is initialized
        if not codegraph:
            raise HTTPException(
                status_code=503,
                detail="CodeGraph not initialized"
            )
        
        # Get the file subgraph
        result = codegraph.get_nodes_by_file(file_path)
        
        # Check if any nodes were found
        if not result.get('nodes'):
            raise HTTPException(
                status_code=404,
                detail=f"No nodes found for file '{file_path}'"
            )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    
    except Exception as e:
        # Handle unexpected errors
        print(f"❌ Error fetching file subgraph: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch file subgraph: {str(e)}"
        )


@app.get("/api/v1/graph/stats")
async def get_graph_stats():
    """
    Get global graph analytics and summary statistics.

    Returns:
        - total_nodes: Count of nodes
        - total_edges: Count of edges
        - pagerank_top: Top 20 nodes by PageRank
        - betweenness_top: Top 20 nodes by betweenness centrality
    """
    try:
        if not graph_engine:
            raise HTTPException(status_code=503, detail="Graph engine not initialized")

        pagerank = graph_engine.calculate_pagerank()
        betweenness = graph_engine.calculate_betweenness_centrality()

        try:
            total_nodes = graph_engine.graph.number_of_nodes()  # type: ignore
            total_edges = graph_engine.graph.number_of_edges()  # type: ignore
        except Exception:
            total_nodes = len(pagerank)
            total_edges = None

        def top_k_items(metric_map: Dict[str, float], k: int = 20):
            return [
                {"id": node_id, "score": float(score)}
                for node_id, score in sorted(metric_map.items(), key=lambda x: x[1], reverse=True)[:k]
            ]

        # Build Layer 2 composite ranking using Top-200 PageRank as candidates
        try:
            top200_candidates = [
                node_id for node_id, _ in sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:200]
            ]
        except Exception:
            top200_candidates = list(pagerank.keys())[:200]

        layer2_top80 = []
        layer2_top10 = []
        try:
            # Safety: ensure graph is available on engine
            nx_graph = getattr(graph_engine, "graph", None)
            if nx_graph is not None:
                layer2_top80 = layer2_graph_ranking(top200_candidates, nx_graph)
                layer2_top10 = layer2_top80[:10]
        except Exception:
            layer2_top10 = []

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "pagerank_top": top_k_items(pagerank, 20),
            "betweenness_top": top_k_items(betweenness, 20),
            "layer2_top10": layer2_top10,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute graph stats: {str(e)}")


@app.get("/v1/stream")
async def stream_query_execution(goal: str = Query(..., description="The user's query string")):
    """
    Stream the execution of a code analysis query through the complete Agent pipeline.
    
    This endpoint provides real-time streaming of the Agent's execution trace using
    Server-Sent Events (SSE), allowing the frontend to display progress and results
    as they become available.
    
    Args:
        goal: The user's query string to process
        
    Returns:
        StreamingResponse with text/event-stream content type
    """
    async def event_generator():
        """Generate SSE events from the agent streaming function."""
        try:
            async for event_data in run_agent_streaming(goal):
                # Format as SSE event
                yield f"data: {event_data}\n\n"
                
                # Add a small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
            
            # Send end-of-stream marker
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            # Send error event
            error_event = json.dumps({
                "event": "error",
                "step": "S0",
                "goal": goal,
                "error": f"Streaming error: {str(e)}"
            })
            yield f"data: {error_event}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.get("/api/v1/intelligence/summary/{node_id}")
async def get_intelligence_summary(node_id: str):
    """
    Return Layer-3 AI analysis summary and tags for a given node.

    Response keys: aiSummary, aiTags
    """
    try:
        data = get_node_intelligence(node_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"No intelligence found for node '{node_id}'")

        return {
            "nodeId": node_id,
            "aiSummary": data.get("aiSummary", ""),
            "aiTags": data.get("aiTags", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch intelligence: {str(e)}")


@app.get("/api/v1/analyze-node/{node_id}")
async def analyze_node(node_id: str):
    """
    Stream a focused AI analysis for a specific node using contextual metrics.

    This endpoint builds a targeted prompt from the node's code and metrics and
    streams the LLM's response via SSE for an interactive frontend experience.
    """
    async def event_generator():
        try:
            # Validate components
            if not all([codegraph, explainer]):
                yield "data: Agent components not initialized.\n\n"
                yield "data: [DONE]\n\n"
                return

            # Fetch node data
            node = getattr(codegraph, "_nodes_by_id", {}).get(node_id)
            if not node:
                yield f"data: Node '{node_id}' not found.\n\n"
                yield "data: [DONE]\n\n"
                return

            # Extract fields with robust fallbacks
            fq_name = (
                node.get("fqName")
                or node.get("fqname")
                or node.get("qualified_name")
                or node.get("name")
                or node.get("id")
                or "unknown"
            )

            evidence = node.get("evidence") if isinstance(node.get("evidence"), dict) else {}
            snippet = (
                node.get("snippet")
                or node.get("code")
                or node.get("codeSnippet")
                or node.get("code_snippet")
                or node.get("text")
                or (evidence.get("snippet") if isinstance(evidence, dict) else None)
                or ""
            )

            metrics = node.get("metrics", {}) if isinstance(node.get("metrics"), dict) else {}
            data_bag = node.get("data", {}) if isinstance(node.get("data"), dict) else {}

            complexity = metrics.get("complexity") or node.get("complexity") or "unknown"
            risk_index = data_bag.get("risk_index") or node.get("risk_index") or "unknown"
            hotness_score = (
                node.get("hotness_score")
                or data_bag.get("hotness_score")
                or 0
            )
            p95_latency = data_bag.get("p95_latency") or node.get("p95_latency") or "unknown"

            # Build focused prompt
            prompt_template = """
You are an expert Staff Software Engineer, acting as a code consultant.
A developer has asked for your analysis on the following function.

Function Name: {fqName}
Code Snippet:
```python
{snippet}
```

Contextual Metrics:
  - Code Complexity: {complexity}
  - Risk Index: {risk_index}
  - Call Frequency (Hotness): {hotness_score}
  - P95 Latency: {p95_latency}ms

Based on the code AND its contextual metrics, please provide a concise analysis in Markdown format covering:

1. **Core Responsibility**: In one sentence, what is the primary purpose of this function?
2. **Metric-Driven Analysis**: Explain WHY this function has the given metrics. For example, if the risk is high, point to the specific code constructs causing it. If the latency is high, suggest potential reasons based on the code's logic (e.g., "This high latency is likely due to the blocking network call inside the for-loop.").
3. **Actionable Recommendations**: Provide 1-2 concrete, actionable suggestions for refactoring or improvement, directly addressing the findings from your analysis.
"""

            prompt = prompt_template.format(
                fqName=fq_name,
                snippet=snippet,
                complexity=complexity,
                risk_index=risk_index,
                hotness_score=hotness_score,
                p95_latency=str(p95_latency).replace("ms", "") if isinstance(p95_latency, str) else p95_latency,
            )

            # Stream LLM response
            try:
                stream = explainer.client.chat.completions.create(
                    model=explainer.model_name,
                    messages=[
                        {"role": "system", "content": "You are an expert Staff Software Engineer, acting as a code consultant."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    stream=True,
                )

                async def iterate_stream():
                    # Wrap sync iterator in async for compatibility
                    for chunk in stream:
                        delta = None
                        try:
                            delta = chunk.choices[0].delta.content
                        except Exception:
                            delta = None
                        if delta:
                            yield f"data: {delta}\n\n"
                        await asyncio.sleep(0)  # cooperative yield

                async for sse_chunk in iterate_stream():
                    yield sse_chunk

                # End of stream marker
                yield "data: [DONE]\n\n"
            except Exception as e:
                # Surface LLM errors to client and end stream
                yield f"data: Error generating analysis: {str(e)}\n\n"
                yield "data: [DONE]\n\n"
        except Exception as outer_e:
            yield f"data: Unexpected error: {str(outer_e)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
