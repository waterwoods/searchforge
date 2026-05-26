"""Platform / lab / graph / tuner inline routes for SearchForge Main API.

Registered only when ``UNIFIED_INTAKE_PRODUCT_ONLY`` is **not** set. Extracted from
``app_main`` so product-only deployments do not expose these paths at the wire.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from services.fiqa_api import obs
from services.code_intelligence.ai_analyzer import get_node_intelligence
from services.code_intelligence.graph_ranker import layer2_graph_ranking
from services.fiqa_api.json_safe_utils import json_safe

try:
    from services.code_intelligence.golden_path import extract_golden_path  # type: ignore
except Exception:  # pragma: no cover - optional path layout
    import sys as _sys
    from pathlib import Path as _Path

    _gp_dir = _Path(__file__).parent.parent / "code_intelligence"
    if str(_gp_dir) not in _sys.path:
        _sys.path.insert(0, str(_gp_dir))
    from golden_path import extract_golden_path  # type: ignore

logger = logging.getLogger(__name__)

_tuner_enabled = False


def register_platform_inline_routes(app: FastAPI, *, graph_engine: Any) -> None:
    """Mount lab/graph/embeddings/tuner/demo routes (platform-full only)."""

    @app.get("/obs/ping")
    def obs_ping():
        """Emit a noop Langfuse trace for connectivity validation."""
        trace_id = f"ping-{uuid.uuid4().hex[:8]}"
        trace = obs.trace_start(trace_id, name="obs.ping", input={"ts": time.time()})
        ctx = {"trace": trace, "root": trace, "trace_id": trace_id, "job_id": trace_id}
        obs.finalize_root(ctx)
        obs.trace_end(trace, output={"ok": True})
        return {"ok": True, "trace_id": trace_id}

    @app.get("/api/lab/report")
    async def get_lab_report_api(mini: Optional[int] = 0, exp_id: Optional[str] = None):
        """
        Get lab experiment report (unified /api endpoint).

        Query params:
        - mini: If 1, return mini metrics (default: 0)
        - exp_id: Experiment ID (default: latest)

        Returns:
            Report data with metrics
        """
        try:
            from backend_core.lab_combo_reporter import generate_mini, get_latest_experiment_id

            # Determine experiment ID
            experiment_id = exp_id or get_latest_experiment_id()

            if not experiment_id:
                return {
                    "ok": False,
                    "message": "No experiment data found",
                    "delta_p95_pct": 0.0,
                    "delta_qps_pct": 0.0,
                    "error_rate_pct": 0.0,
                    "faiss_share_pct": 0.0,
                    "milvus_share_pct": 0.0,
                    "qdrant_share_pct": 0.0,
                    "generated_at": time.time()
                }

            # Generate report
            text_report, json_metrics = generate_mini(experiment_id)

            if mini == 1:
                # Return mini JSON metrics
                return json_metrics
            else:
                # Return full text report
                return {
                    "ok": json_metrics.get('ok', False),
                    "report": text_report,
                    "metrics": json_metrics
                }

        except Exception as e:
            logger.error(f"[LAB_REPORT] Failed to generate report: {e}")
            return {
                "ok": False,
                "message": f"Report generation failed: {str(e)}",
                "delta_p95_pct": 0.0,
                "delta_qps_pct": 0.0,
                "error_rate_pct": 0.0,
                "faiss_share_pct": 0.0,
                "milvus_share_pct": 0.0,
                "qdrant_share_pct": 0.0,
                "generated_at": time.time()
            }


    @app.get("/api/metrics/mini")
    async def get_mini_metrics(exp_id: str, window_sec: int = 120):
        """
        Get mini metrics for an experiment from Redis.

        Query params:
        - exp_id: Experiment ID
        - window_sec: Time window in seconds (default: 120)

        Returns:
            JSON with p95, qps, err_pct, route_share, samples
        """
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            raw_key = f"lab:exp:{exp_id}:raw"

            # Read raw data
            raw_data = r.lrange(raw_key, 0, -1)
            if not raw_data:
                return {
                    "ok": False,
                    "error": "no_data",
                    "p95": 0, "qps": 0, "err_pct": 0,
                    "route_share": {"milvus": 0, "faiss": 0, "qdrant": 0},
                    "samples": 0
                }

            # Parse and filter by window
            metrics = [json.loads(m) for m in raw_data]
            now = time.time()
            windowed = [m for m in metrics if now - m["ts"] <= window_sec]

            if not windowed:
                return {"ok": False, "error": "no_data_in_window"}

            # Compute metrics
            import numpy as np
            from collections import defaultdict

            latencies = [m["latency_ms"] for m in windowed if m.get("ok")]
            p95 = float(np.percentile(latencies, 95)) if latencies else 0

            errors = sum(1 for m in windowed if not m.get("ok", True))
            err_pct = (errors / len(windowed) * 100) if windowed else 0

            duration = max(m["ts"] for m in windowed) - min(m["ts"] for m in windowed)
            qps = len(windowed) / duration if duration > 0 else 0

            routes = defaultdict(int)
            for m in windowed:
                routes[m.get("route", "unknown")] += 1

            route_total = sum(routes.values())
            route_share = {
                "milvus": routes["milvus"] / route_total * 100 if route_total > 0 else 0,
                "faiss": routes["faiss"] / route_total * 100 if route_total > 0 else 0,
                "qdrant": routes["qdrant"] / route_total * 100 if route_total > 0 else 0
            }

            return {
                "ok": True,
                "p95": round(p95, 2),
                "qps": round(qps, 2),
                "err_pct": round(err_pct, 2),
                "route_share": {k: round(v, 1) for k, v in route_share.items()},
                "samples": len(windowed)
            }

        except Exception as e:
            logger.error(f"[MINI_METRICS] Error: {e}")
            return {"ok": False, "error": str(e)}


    @app.post("/api/lab/snapshot")
    async def create_snapshot(request: Request):
        """
        Create a snapshot of current system state.

        Saves:
        - Selected environment variables
        - Git SHA (if available)
        - Timestamp

        Returns:
            Snapshot path
        """
        try:
            import subprocess

            # Get git SHA
            git_sha = "unknown"
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    git_sha = result.stdout.strip()[:8]
            except:
                pass

            # Request body (optional metadata)
            body = {}
            try:
                body = await request.json()
            except:
                pass

            # Selected safe environment variables
            safe_env = {
                "MAIN_PORT": os.getenv("MAIN_PORT", "8000"),
                "QDRANT_HOST": os.getenv("QDRANT_HOST", "localhost"),
                "QDRANT_PORT": os.getenv("QDRANT_PORT", "6333"),
                "LAB_REDIS_TTL": os.getenv("LAB_REDIS_TTL", "86400"),
                "DISABLE_FAISS": os.getenv("DISABLE_FAISS", "false"),
                "VECTOR_BACKEND": os.getenv("VECTOR_BACKEND", "faiss")
            }

            # Build snapshot
            ts = int(time.time())
            snapshot = {
                "timestamp": ts,
                "timestamp_human": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ts)),
                "git_sha": git_sha,
                "env": safe_env,
                "flags": app.state.routing_flags,
                "trigger": body.get("trigger", "manual"),
                "exp_id": body.get("exp_id", "unknown")
            }

            # Write to reports/_snapshots/
            project_root = Path(__file__).parent.parent.parent
            snapshots_dir = project_root / "reports" / "_snapshots"
            snapshots_dir.mkdir(parents=True, exist_ok=True)

            snapshot_file = snapshots_dir / f"{ts}_snapshot.json"
            with open(snapshot_file, "w") as f:
                json.dump(snapshot, f, indent=2)

            logger.info(f"[SNAPSHOT] Created: {snapshot_file}")

            return {
                "ok": True,
                "path": str(snapshot_file),
                "timestamp": ts
            }

        except Exception as e:
            logger.error(f"[SNAPSHOT] Error: {e}")
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": str(e)}
            )


    # ========================================
    # Routing Flags Endpoint
    # ========================================

    @app.post("/api/routing/flags")
    async def set_routing_flags(flags: dict):
        """
        Set routing configuration flags.

        Flags:
        - enabled: bool - Enable/disable smart routing
        - mode: str - Routing mode ("rules" or "cost")
        - manual_backend: str - Force backend ("qdrant", "faiss", "milvus")
        - faiss_enabled: bool - Enable/disable FAISS backend (runtime control)

        Returns:
            Status dict
        """
        try:
            # Update routing flags
            if "enabled" in flags:
                app.state.routing_flags["enabled"] = bool(flags["enabled"])
            if "mode" in flags:
                app.state.routing_flags["mode"] = str(flags["mode"])
            if "policy" in flags:
                # Accept "policy" as alias for "mode"
                app.state.routing_flags["mode"] = str(flags["policy"])
            if "manual_backend" in flags:
                if flags["manual_backend"] is None:
                    # Clear manual override
                    app.state.routing_flags.pop("manual_backend", None)
                else:
                    app.state.routing_flags["manual_backend"] = str(flags["manual_backend"])

            # ✅ Runtime FAISS enable/disable control
            if "faiss_enabled" in flags:
                app.state.faiss_enabled = bool(flags["faiss_enabled"])
                logger.info(f"[FAISS] Runtime control: enabled={app.state.faiss_enabled}")

            logger.info(f"[ROUTING] Flags updated: {app.state.routing_flags}")

            return {
                "ok": True,
                "flags": app.state.routing_flags,
                "faiss_enabled": app.state.faiss_enabled
            }
        except Exception as e:
            logger.error(f"[ROUTING] Failed to set flags: {e}")
            return {
                "ok": False,
                "error": str(e)
            }


    @app.get("/api/routing/status")
    async def get_routing_status():
        """
        Get routing status.

        Returns:
            Routing status with FAISS and config info
        """
        return {
            "ok": True,
            "flags": app.state.routing_flags,
            "faiss": {
                "enabled": app.state.faiss_enabled,
                "ready": app.state.faiss_ready,
                "engine": app.state.faiss_engine.get_status() if app.state.faiss_engine else None
            }
        }



    # ========================================
    # Graph Mermaid API
    # ========================================

    @app.get("/api/graph/mermaid")
    async def get_mermaid_graph(rid: str = Query(..., description="Request ID to retrieve graph data")):
        """
        Transform raw graph data into a ready-to-render Mermaid.js string.

        This endpoint retrieves stored graph data (edges_json and files) for a given requestId
        and transforms it into a Mermaid.js graph syntax string with node details.

        Args:
            requestId: Request ID to retrieve stored graph data

        Returns:
            JSON response with mermaidText and nodeDetails

        Raises:
            HTTPException: 404 if requestId is invalid or data not found
            HTTPException: 422 if requestId is missing or empty
        """
        # Input validation
        if not rid or not rid.strip():
            raise HTTPException(
                status_code=422,
                detail="Request ID is invalid or has expired."
            )

        # Check cache first (optional Redis caching)
        cache_key = f"mermaid_graph:{rid}"
        cached_result = None

        try:
            # Try to get from Redis cache if available
            import redis
            redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            cached_data = redis_client.get(cache_key)
            if cached_data:
                import json
                cached_result = json.loads(cached_data)
                logger.info(f"[MERMAID_GRAPH] Cache hit for requestId {rid}")
                return cached_result
        except Exception as e:
            logger.warning(f"[MERMAID_GRAPH] Cache check failed: {e}")
            # Continue without cache

        try:
            # MASTER ERROR HANDLER: Wrap all data processing in bulletproof try-catch
            try:
                # Try to retrieve actual cached search results first
                import redis
                import json
                redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

                # Try different cache key patterns for the search results
                possible_cache_keys = [
                    f"search_result:{rid}",
                    f"code_lookup:{rid}",
                    f"agent_result:{rid}",
                    f"search:{rid}",
                    rid  # Sometimes the rid itself is the key
                ]

                cached_search_result = None
                for cache_key in possible_cache_keys:
                    try:
                        cached_data = redis_client.get(cache_key)
                        if cached_data:
                            cached_search_result = json.loads(cached_data)
                            logger.info(f"[MERMAID_GRAPH] Found cached search result for requestId {rid} using key {cache_key}")
                            break
                    except Exception as e:
                        logger.debug(f"[MERMAID_GRAPH] Cache key {cache_key} not found or invalid: {e}")
                        continue

                # If we found cached search results, use them
                if cached_search_result:
                    # Extract edges_json and files from the cached result
                    # Handle different possible data structures
                    if isinstance(cached_search_result, dict):
                        edges_json = cached_search_result.get('edges_json', [])
                        files = cached_search_result.get('files', [])
                    elif hasattr(cached_search_result, 'edges_json'):
                        # Handle Pydantic model objects
                        edges_json = getattr(cached_search_result, 'edges_json', [])
                        files = getattr(cached_search_result, 'files', [])
                    else:
                        # Fallback: assume it's a list or handle as unknown structure
                        logger.warning(f"[MERMAID_GRAPH] Unknown cached data structure for requestId {rid}: {type(cached_search_result)}")
                        edges_json = []
                        files = []

                    # Add diagnostic logging
                    logger.info(f"[MERMAID_GRAPH] Retrieved edges_json for rid {rid}: {edges_json}")
                    logger.info(f"[MERMAID_GRAPH] Retrieved files for rid {rid}: {len(files)} files")

                    # Handle empty or invalid edge data gracefully
                    if not edges_json or edges_json == [] or edges_json is None:
                        logger.warning(f"[MERMAID_GRAPH] No edges found for rid {rid}. Returning an empty graph.")
                        return {
                            "mermaidText": "graph LR\n    A[\"No code relationships found to visualize\"]",
                            "nodeDetails": {
                                "A": {
                                    "code": "No code relationships found to visualize",
                                    "filePath": "No data available"
                                }
                            }
                        }
                else:
                    # Fallback to mock data if no cached results found
                    logger.warning(f"[MERMAID_GRAPH] No cached search results found for requestId {rid}. Using mock data.")

                    # Mock data for demonstration
                    mock_edges_json = [
                        {"src": "main.py::start", "dst": "controller.py::init", "type": "calls"},
                        {"src": "controller.py::init", "dst": "config.py::load_settings", "type": "calls"},
                        {"src": "controller.py::init", "dst": "database.py::connect", "type": "calls"},
                        {"src": "config.py::load_settings", "dst": "settings.py::get_config", "type": "calls"},
                        {"src": "database.py::connect", "dst": "models.py::User", "type": "imports"},
                        {"src": "models.py::User", "dst": "auth.py::authenticate", "type": "calls"},
                        {"src": "auth.py::authenticate", "dst": "utils.py::hash_password", "type": "calls"},
                        {"src": "utils.py::hash_password", "dst": "crypto.py::sha256", "type": "calls"},
                    ]

                    mock_files = [
                        {
                            "path": "main.py",
                            "snippet": "def start():\n    controller.init()\n    print('Application started')",
                            "language": "python"
                        },
                        {
                            "path": "controller.py", 
                            "snippet": "def init():\n    config.load_settings()\n    database.connect()",
                            "language": "python"
                        },
                        {
                            "path": "config.py",
                            "snippet": "def load_settings():\n    settings.get_config()\n    return True",
                            "language": "python"
                        }
                    ]

                    edges_json = mock_edges_json
                    files = mock_files

                # Transform the data using the helper function
                result = convert_edges_to_mermaid_data(edges_json, files)

                # Store result in cache (optional Redis caching)
                try:
                    import redis
                    import json
                    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
                    # Cache for 15 minutes (900 seconds)
                    redis_client.setex(cache_key, 900, json.dumps(result))
                    logger.info(f"[MERMAID_GRAPH] Cached result for requestId {rid}")
                except Exception as e:
                    logger.warning(f"[MERMAID_GRAPH] Cache storage failed: {e}")
                    # Continue without caching

                return result

            except Exception as processing_error:
                # BULLETPROOF ERROR HANDLER: Catch any processing error and return graceful response
                logger.error(f"[MERMAID_GRAPH] Failed to process graph for rid {rid} due to an unexpected error: {processing_error}", exc_info=True)

                # Return the same user-friendly "empty graph" response
                # This ensures users NEVER see a 422 error again
                return {
                    "mermaidText": "graph LR\n    A[\"Unable to process graph data\"]",
                    "nodeDetails": {
                        "A": {
                            "code": "Unable to process graph data - please try again",
                            "filePath": "Error occurred during data processing"
                        }
                    }
                }

        except Exception as e:
            # This outer catch is for any remaining unhandled errors
            logger.error(f"[MERMAID_GRAPH] Critical error processing requestId {rid}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}"
            )


    def convert_edges_to_mermaid_data(edges_json: list, files: list) -> dict:
        """
        Convert edges_json and files data into Mermaid.js graph format.

        Args:
            edges_json: List of edge data with src, dst, type keys
            files: List of file data with path, snippet, language keys

        Returns:
            Dict with mermaidText and nodeDetails keys
        """
        # Security limits to prevent DoS
        MAX_NODES = 200
        MAX_EDGES = 500

        # Handle empty or invalid edge data gracefully
        if not edges_json or edges_json == [] or edges_json is None:
            logger.warning("[MERMAID_CONVERT] No edges provided. Returning empty graph.")
            return {
                "mermaidText": "graph LR\n    A[\"No code relationships found to visualize\"]",
                "nodeDetails": {
                    "A": {
                        "code": "No code relationships found to visualize",
                        "filePath": "No data available"
                    }
                }
            }

        # Validate input limits
        if len(edges_json) > MAX_EDGES:
            raise ValueError(f"Too many edges: {len(edges_json)} > {MAX_EDGES}")

        # Extract all unique nodes from edges
        nodes = set()
        for edge in edges_json:
            if isinstance(edge, dict) and 'src' in edge and 'dst' in edge:
                nodes.add(edge['src'])
                nodes.add(edge['dst'])

        # Handle case where no valid nodes are found
        if not nodes:
            logger.warning("[MERMAID_CONVERT] No valid nodes found in edges. Returning empty graph.")
            return {
                "mermaidText": "graph LR\n    A[\"No valid code relationships found\"]",
                "nodeDetails": {
                    "A": {
                        "code": "No valid code relationships found",
                        "filePath": "No data available"
                    }
                }
            }

        if len(nodes) > MAX_NODES:
            raise ValueError(f"Too many nodes: {len(nodes)} > {MAX_NODES}")

        # Build Mermaid.js graph syntax
        mermaid_lines = ["graph LR"]

        # Add nodes with proper escaping
        for node in sorted(nodes):
            # Escape special characters for Mermaid
            escaped_node = _escape_mermaid_identifier(node)
            # Create a short label for display
            label = _create_node_label(node)
            mermaid_lines.append(f'    {escaped_node}["{label}"]')

        # Add edges with proper escaping
        for edge in edges_json:
            if isinstance(edge, dict) and 'src' in edge and 'dst' in edge:
                src = _escape_mermaid_identifier(edge['src'])
                dst = _escape_mermaid_identifier(edge['dst'])
                edge_type = edge.get('type', 'calls')

                # Choose arrow style based on edge type
                if edge_type == 'calls':
                    arrow = "-->"
                elif edge_type == 'imports':
                    arrow = "-.->"
                else:
                    arrow = "-->"

                mermaid_lines.append(f'    {src} {arrow} {dst}')

        # Add click callbacks for each node
        click_lines = []
        for node in sorted(nodes):
            escaped_node = _escape_mermaid_identifier(node)
            # Escape the node ID for JavaScript
            js_safe_node_id = node.replace('"', '\\"').replace("'", "\\'")
            click_lines.append(f'    click {escaped_node} call handleNodeClick("{js_safe_node_id}")')

        # Combine all lines
        all_lines = mermaid_lines + click_lines
        mermaid_text = ";\n".join(all_lines) + ";"

        # Build node details map
        node_details = {}
        for node in nodes:
            # Find corresponding file data
            file_data = _find_file_for_node(node, files)

            node_details[node] = {
                "code": _escape_html(file_data.get('snippet', '')) if file_data else '',
                "filePath": _escape_html(file_data.get('path', '')) if file_data else ''
            }

        return {
            "mermaidText": mermaid_text,
            "nodeDetails": node_details
        }


    def _escape_mermaid_identifier(identifier: str) -> str:
        """Escape special characters in Mermaid identifiers."""
        # Replace problematic characters with underscores
        escaped = identifier.replace('::', '_').replace(':', '_').replace('.', '_')
        escaped = escaped.replace(' ', '_').replace('-', '_')
        # Remove any remaining special characters
        import re
        escaped = re.sub(r'[^a-zA-Z0-9_]', '_', escaped)
        return escaped


    def _create_node_label(node: str) -> str:
        """Create a short, readable label for a node."""
        # Extract the function/class name from the node
        if '::' in node:
            return node.split('::')[-1]
        elif '.' in node:
            return node.split('.')[-1]
        else:
            return node.split('/')[-1] if '/' in node else node


    def _find_file_for_node(node: str, files: list) -> dict:
        """Find the file data that corresponds to a node."""
        for file_data in files:
            file_path = file_data.get('path', '')
            if file_path in node or node in file_path:
                return file_data
        return {}


    def _escape_html(text: str) -> str:
        """Escape HTML/JavaScript characters to prevent XSS."""
        if not text:
            return ''

        # Replace HTML/JS special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#x27;')
        text = text.replace('/', '&#x2F;')

        return text


    # ========================================
    # Chat API Models
    # ========================================

    class ChatRequest(BaseModel):
        """Request model for conversational chat endpoint."""
        node_id: str
        message: str
        conversation_history: Optional[List[Dict[str, str]]] = None  # List of {role, content} messages


    # ========================================
    # Embeddings API
    # ========================================

    class EmbeddingRequest(BaseModel):
        """Embedding request model."""
        chunks: List[Dict[str, Any]]
        batch_size: int = 64
        max_tokens: int = 512
        normalize: bool = True
        backend: Optional[str] = None  # Force backend: milvus, qdrant, or none


    @app.post("/api/embeddings/encode")
    async def encode_embeddings(request: EmbeddingRequest, response: Response):
        """
        Encode chunks to embeddings and optionally store in vector database.

        Request body:
            chunks: List of dicts with doc_id, chunk_id, text
            batch_size: Batch size for encoding (default: 64)
            max_tokens: Max tokens per text (default: 512)
            normalize: Normalize vectors (default: true)
            backend: Force backend (milvus, qdrant, none) or use VECTOR_BACKEND env

        Response:
            ok: bool
            count: int (number of chunks processed)
            dim: int (vector dimension)
            model: str (model name used)
            backend: str (backend used: milvus, qdrant, or none)

        Headers:
            X-Embed-Model: Model name used
            X-Embed-Dim: Vector dimension
        """
        start_time = time.time()

        try:
            from modules.embedding import embed_chunks
            from modules.embedding.sinks import auto_upsert

            # Validate input
            if not request.chunks:
                return JSONResponse(
                    status_code=400,
                    content={
                        "ok": False,
                        "error": "empty_chunks",
                        "message": "No chunks provided"
                    }
                )

            # Validate chunk schema
            for i, chunk in enumerate(request.chunks):
                if not all(key in chunk for key in ["doc_id", "chunk_id", "text"]):
                    return JSONResponse(
                        status_code=400,
                        content={
                            "ok": False,
                            "error": "invalid_chunk",
                            "message": f"Chunk {i} missing required fields (doc_id, chunk_id, text)"
                        }
                    )

            # Embed chunks
            logger.info(f"[EMBEDDINGS] Processing {len(request.chunks)} chunks")
            embedded_items = embed_chunks(
                request.chunks,
                batch_size=request.batch_size,
                max_tokens=request.max_tokens,
                normalize=request.normalize
            )

            # Get model and dimension info
            model = embedded_items[0]["model"] if embedded_items else "unknown"
            dim = embedded_items[0]["dim"] if embedded_items else 0

            # Upsert to vector database (if configured)
            upsert_result = auto_upsert(
                embedded_items,
                collection="sf_chunks",
                backend=request.backend
            )

            latency_ms = (time.time() - start_time) * 1000

            # Set response headers
            response.headers["X-Embed-Model"] = model
            response.headers["X-Embed-Dim"] = str(dim)

            logger.info(
                f"[EMBEDDINGS] Encoded {len(embedded_items)} chunks in {latency_ms:.2f}ms, "
                f"backend: {upsert_result['backend']}"
            )

            return {
                "ok": True,
                "count": len(embedded_items),
                "dim": dim,
                "model": model,
                "backend": upsert_result["backend"],
                "latency_ms": latency_ms
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"[EMBEDDINGS] Error: {e}")

            return JSONResponse(
                status_code=500,
                content={
                    "ok": False,
                    "error": str(e),
                    "latency_ms": latency_ms
                }
            )



    # ========================================
    # Tuner Endpoints (Stub Implementation)
    # ========================================

    # In-memory tuner state (stub)
    _tuner_enabled = False

    @app.get("/tuner/enabled")
    async def get_tuner_enabled():
        """
        Get tuner enabled status (stub implementation).

        Returns:
            Tuner enabled status with stub data
        """
        global _tuner_enabled
        return {
            "ok": True,
            "enabled": _tuner_enabled,
            "mode": "stub",
            "message": "Tuner stub implementation"
        }


    @app.post("/tuner/toggle")
    async def toggle_tuner():
        """
        Toggle tuner status (stub implementation).

        Returns:
            Toggle result with updated status
        """
        global _tuner_enabled
        _tuner_enabled = not _tuner_enabled
        return {
            "ok": True,
            "enabled": _tuner_enabled,
            "message": f"Tuner {'enabled' if _tuner_enabled else 'disabled'} (stub)"
        }

    # ========================================
    # Startup Event
    # ========================================

    @app.post("/api/demo/generate-traffic")
    async def generate_demo_traffic(high_qps: bool = False, duration: int = 60):
        """
        Generate demo traffic for monitoring and testing.

        Args:
            high_qps: If True, use high QPS mode (20 QPS vs 10 QPS)
            duration: Duration in seconds (default: 60)

        This endpoint triggers the demo_monitor.sh script to generate test traffic.
        """
        try:
            import subprocess
            import asyncio

            logger.info(f"[DEMO] Starting traffic generation (high_qps={high_qps})...")

            # Choose script based on QPS mode
            script_path = "/Users/nanxinli/Documents/dev/searchforge/scripts/demo_monitor_configurable.sh"

            if high_qps:
                mode = f"高QPS模式 (20 QPS, {duration}秒)"
                # Pass duration and QPS as arguments to the script
                process = await asyncio.create_subprocess_exec(
                    "bash", script_path, str(duration), "20",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                mode = f"标准模式 (10 QPS, {duration}秒)"
                # Pass duration and QPS as arguments to the script
                process = await asyncio.create_subprocess_exec(
                    "bash", script_path, str(duration), "10",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

            # Don't wait for completion, let it run in background
            logger.info(f"[DEMO] Traffic generation started in background ({mode})")

            return {
                "status": "started",
                "message": f"Demo traffic generation started ({mode})",
                "mode": mode,
                "pid": process.pid
            }

        except Exception as e:
            logger.error(f"[DEMO] Failed to start traffic generation: {e}")
            return {
                "status": "error", 
                "message": f"Failed to start traffic generation: {str(e)}"
            }

    @app.post("/api/lab/prewarm")
    async def prewarm_faiss():
        """
        Prewarm FAISS engine with hot vectors from Qdrant.

        Loads a subset of vectors into FAISS for fast in-memory search.
        """
        try:
            logger.info("[FAISS] Starting prewarm...")

            # Import FAISS engine
            from services.search.faiss_engine import FaissEngine
            import numpy as np
            from qdrant_client import QdrantClient

            # Connect to Qdrant
            qdrant_host = os.getenv("QDRANT_HOST", "localhost")
            qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
            collection_name = os.getenv("COLLECTION_NAME", "fiqa")

            client = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=10)

            # Get collection info
            collection_info = client.get_collection(collection_name)
            vector_size = collection_info.config.params.vectors.size
            total_points = collection_info.points_count

            # Fetch a subset of vectors (50k max for speed)
            fetch_limit = min(50000, total_points)
            logger.info(f"[FAISS] Fetching {fetch_limit} vectors from Qdrant (total: {total_points})")

            # Scroll through points
            points, _ = client.scroll(
                collection_name=collection_name,
                limit=fetch_limit,
                with_vectors=True
            )

            if not points:
                return {
                    "ok": False,
                    "error": "no_points_found",
                    "message": "No points found in Qdrant collection"
                }

            # Extract vectors and IDs
            embeddings = []
            ids = []
            for point in points:
                embeddings.append(point.vector)
                # Extract doc_id from payload or use point id
                doc_id = point.payload.get("doc_id", str(point.id)) if point.payload else str(point.id)
                ids.append(doc_id)

            embeddings = np.array(embeddings, dtype='float32')
            ids = np.array(ids)

            # Initialize and load FAISS
            engine = FaissEngine(dim=vector_size)
            engine.load(embeddings, ids)

            # Store in app state
            app.state.faiss_engine = engine
            app.state.faiss_ready = True

            logger.info(f"[FAISS] Prewarm complete: {len(ids)} vectors loaded")

            return {
                "ok": True,
                "vectors_loaded": len(ids),
                "dimension": vector_size,
                "status": engine.get_status()
            }

        except Exception as e:
            logger.error(f"[FAISS] Prewarm failed: {e}")
            return {
                "ok": False,
                "error": str(e)
            }


    # ========================================
    # Graph Golden Path API Endpoint
    # ========================================

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
            return path
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[GOLDEN_PATH] Failed to compute golden path: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to compute golden path: {e}")


    # ========================================
    # Graph Statistics API Endpoint
    # ========================================

    @app.get("/api/v1/graph/stats")
    async def get_graph_stats_endpoint():
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
            logger.error(f"[GRAPH_STATS] Failed to compute graph stats: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to compute graph stats: {str(e)}")


    # ========================================
    # Graph Search Streaming (SSE) Endpoint
    # ========================================

    @app.get("/api/v1/graph/stream-search")
    async def stream_search(q: str = Query(..., description="Search query for graph exploration")):
        """
        Server-Sent Events endpoint that streams progress updates and a final
        graph search result for the provided query.

        Behavior:
          - Accepts queries such as:
            • '#func <node_id>'
            • '#file <file_path>'
            • '#overview'
          - Returns final payload with full graph data: { nodes: [...], edges: [...] }
        """
        if graph_engine is None or getattr(graph_engine, "graph", None) is None:
            raise HTTPException(status_code=503, detail="Graph engine not initialized")

        def _serialize_nodes_edges_from_subgraph(node_ids: List[str]) -> Dict[str, Any]:
            g = graph_engine.graph
            valid_ids = [nid for nid in node_ids if nid in g]
            subg = g.subgraph(valid_ids).copy()

            nodes_out: List[Dict[str, Any]] = []
            for nid in subg.nodes:
                attrs = dict(subg.nodes[nid]) if hasattr(subg, "nodes") else {}
                fq_name = attrs.get("fqName") or attrs.get("name") or nid
                nodes_out.append({
                    "id": str(nid),
                    "fqName": fq_name,
                    "data": json_safe(attrs)
                })

            edges_out: List[Dict[str, str]] = [{"from": str(u), "to": str(v)} for u, v in subg.edges]
            return {"nodes": nodes_out, "edges": edges_out}

        def _neighborhood(node_id: str, depth: int = 2) -> Dict[str, Any]:
            hood = graph_engine.get_neighborhood(node_id=node_id, depth=depth)
            nodes_map: Dict[str, Dict[str, Any]] = hood.get("nodes", {}) if isinstance(hood.get("nodes"), dict) else {}
            edges_list: List[Dict[str, str]] = hood.get("edges", []) or []

            nodes_arr: List[Dict[str, Any]] = []
            for nid, attrs in nodes_map.items():
                fq_name = (attrs or {}).get("fqName") or (attrs or {}).get("name") or nid
                nodes_arr.append({
                    "id": str(nid),
                    "fqName": fq_name,
                    "data": json_safe(attrs or {})
                })
            edges_arr = [{"from": str(e.get("from")), "to": str(e.get("to"))} for e in edges_list if isinstance(e, dict)]
            return {"nodes": nodes_arr, "edges": edges_arr}

        def _file_subgraph(file_path: str) -> Dict[str, Any]:
            g = graph_engine.graph
            # Normalize input path once
            try:
                from pathlib import Path as _Path
                q_path = str(_Path(file_path))
            except Exception:
                q_path = file_path

            def _matches(node_attrs: Dict[str, Any]) -> bool:
                ev = (node_attrs or {}).get("evidence", {})
                f = ev.get("file") or node_attrs.get("file") or ""
                if not isinstance(f, str) or not f:
                    return False
                # Match if equal, endswith, or contains normalized query path
                if f == q_path:
                    return True
                if f.endswith(q_path):
                    return True
                return q_path in f

            file_nodes = [nid for nid in g.nodes if _matches(g.nodes[nid])]
            return _serialize_nodes_edges_from_subgraph(file_nodes)

        async def event_generator():
            try:
                yield f"event: message\ndata: {json.dumps({'event': 'processing', 'query': q})}\n\n"

                query = (q or "").strip()
                final_graph: Dict[str, Any] = {"nodes": [], "edges": []}

                if query.startswith("#func "):
                    node_id = query[len("#func "):].strip()
                    final_graph = _neighborhood(node_id=node_id, depth=2)
                elif query.startswith("#file "):
                    file_path = query[len("#file "):].strip()
                    final_graph = _file_subgraph(file_path=file_path)
                elif query.startswith("#overview") or query == "#":
                    try:
                        pr = graph_engine.calculate_pagerank()
                        if pr:
                            top_node = max(pr.items(), key=lambda kv: kv[1])[0]
                            final_graph = _neighborhood(node_id=top_node, depth=2)
                    except Exception:
                        final_graph = {"nodes": [], "edges": []}
                else:
                    if query in graph_engine.graph:
                        final_graph = _neighborhood(node_id=query, depth=2)
                    else:
                        final_graph = {"nodes": [], "edges": []}

                final_graph = json_safe(final_graph)
                yield f"event: message\ndata: {json.dumps({'event': 'final', 'final_data': final_graph})}\n\n"
                yield "event: message\ndata: [DONE]\n\n"
            except Exception as e:
                err = {"event": "error", "message": str(e)}
                yield f"event: message\ndata: {json.dumps(err)}\n\n"
                yield "event: message\ndata: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )

    # ========================================
    # Intelligence Summary API Endpoint
    # ========================================

    @app.get("/api/v1/intelligence/summary/{node_id}")
    async def get_intelligence_summary(node_id: str):
        """
        Return Layer-3 AI analysis summary and tags for a given node.

        First checks in-memory NODE_INTELLIGENCE_STORE cache.
        If not found, returns empty response instead of 404 to prevent frontend errors.

        Response keys: aiSummary, aiTags
        """
        try:
            # Try to get from in-memory cache first
            data = get_node_intelligence(node_id)

            if data:
                return {
                    "nodeId": node_id,
                    "aiSummary": data.get("aiSummary", ""),
                    "aiTags": data.get("aiTags", []),
                    "aiImportance": data.get("aiImportance", None),
                }

            # If not in cache, return empty response (don't fail with 404)
            # This happens when nodes haven't been analyzed yet via layer3_ai_analysis
            logger.debug(f"[INTELLIGENCE] No cached intelligence for node {node_id}, returning empty response")
            return {
                "nodeId": node_id,
                "aiSummary": "",
                "aiTags": [],
                "aiImportance": None,
            }

        except Exception as e:
            logger.error(f"[INTELLIGENCE] Failed to fetch intelligence for node {node_id}: {e}")
            # Return empty response instead of 500 error
            return {
                "nodeId": node_id,
                "aiSummary": "",
                "aiTags": [],
                "aiImportance": None,
            }


    # ========================================
    # AI Analysis (Streaming) API Endpoint
    # ========================================

    @app.get("/api/v1/analyze-node/{node_id}")
    async def analyze_node(node_id: str):
        """
        Stream a deep AI analysis for a given graph node via Server-Sent Events.

        - Fetches node attributes from the in-memory NetworkX graph
        - Builds a rich prompt with code snippet and metadata
        - Streams analysis tokens from the LLM to the client
        """
        async def event_generator():
            try:
                # Ensure LLM client is available
                from services.fiqa_api.clients import get_openai_client
                openai_client = get_openai_client()
                if openai_client is None:
                    yield "data: LLM client not initialized. Please set OPENAI_API_KEY.\n\n"
                    yield "data: [DONE]\n\n"
                    return

                # Pull node data from NetworkX engine
                try:
                    if graph_engine is None or getattr(graph_engine, "graph", None) is None:
                        yield "data: Graph engine not initialized.\n\n"
                        yield "data: [DONE]\n\n"
                        return

                    g = graph_engine.graph
                    if node_id not in g:
                        yield f"data: Node '{node_id}' not found in graph.\n\n"
                        yield "data: [DONE]\n\n"
                        return

                    attrs = dict(g.nodes[node_id])
                except Exception as e:
                    yield f"data: Error fetching node from graph: {str(e)}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                # Extract useful fields with fallbacks
                fq_name = attrs.get("fqName") or attrs.get("name") or node_id
                kind = attrs.get("kind") or attrs.get("type") or "unknown"
                evidence = attrs.get("evidence", {}) if isinstance(attrs.get("evidence"), dict) else {}
                file_path = evidence.get("file") or attrs.get("file") or attrs.get("file_path", "")
                snippet = evidence.get("snippet") or attrs.get("text") or attrs.get("code_snippet") or ""
                doc = attrs.get("doc") or attrs.get("documentation") or ""

                # Optional intelligence signal
                try:
                    ai_info = get_node_intelligence(node_id) or {}
                    ai_summary = ai_info.get("aiSummary", "")
                    ai_tags = ai_info.get("aiTags", [])
                except Exception:
                    ai_summary = ""
                    ai_tags = []

                # Build analysis prompt
                prompt = (
                    "You are an expert code reviewer. Provide a deep, actionable analysis for the given function.\n"
                    "Include: what it does, potential risks/edge cases, performance concerns, test ideas, and concrete refactor suggestions.\n\n"
                    f"Function: {fq_name}\n"
                    f"Kind: {kind}\n"
                    f"File: {file_path}\n"
                    f"Docstring: {doc}\n"
                    f"Prior AI Summary: {ai_summary}\n"
                    f"Tags: {', '.join(map(str, ai_tags)) if isinstance(ai_tags, (list, tuple)) else ai_tags}\n\n"
                    "Code:\n"
                    "```\n"
                    f"{snippet}\n"
                    "```\n\n"
                    "Answer in concise bullet points where appropriate."
                )

                # Stream from OpenAI
                try:
                    stream = openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a senior code assistant performing targeted function analysis."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.2,
                        stream=True,
                    )

                    async def iterate_stream():
                        for chunk in stream:
                            delta = None
                            try:
                                delta = chunk.choices[0].delta.content
                            except Exception:
                                delta = None
                            if delta:
                                yield f"data: {delta}\n\n"
                            await asyncio.sleep(0)

                    async for sse_chunk in iterate_stream():
                        yield sse_chunk

                    yield "data: [DONE]\n\n"
                except Exception as e:
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

    # ========================================
    # Chat API Endpoint
    # ========================================

    @app.post("/api/v1/agent/chat")
    async def agent_chat(request: ChatRequest):
        """
        Streaming chat endpoint that builds rich context for a given node and
        streams the assistant's response with multi-turn conversation support.

        Request body:
          - node_id: graph node identifier
          - message: the user's current message
          - conversation_history: optional list of previous messages [{role: "user"/"assistant", content: "..."}]

        Returns:
          Server-Sent Events stream with assistant's response
        """
        async def event_generator():
            try:
                from services.fiqa_api.clients import get_openai_client, get_qdrant_client

                # Get OpenAI client (optional)
                openai_client = get_openai_client()
                if openai_client is None:
                    yield "data: LLM client not initialized. Please set OPENAI_API_KEY.\n\n"
                    yield "data: [DONE]\n\n"
                    return

                node_id = request.node_id
                user_message = request.message or ""
                conversation_history = request.conversation_history or []

                # Fetch node data from Qdrant directly
                try:
                    qdrant_client = get_qdrant_client()

                    # Search for the node in code_graph collection by ID
                    results, _ = qdrant_client.scroll(
                        collection_name="code_graph",
                        scroll_filter={
                            "must": [
                                {"key": "id", "match": {"value": node_id}}
                            ]
                        },
                        limit=1,
                        with_payload=True,
                        with_vectors=False
                    )

                    if not results or len(results) == 0:
                        # Fallback: try to get from NetworkX graph if available
                        if graph_engine and getattr(graph_engine, "graph", None) and node_id in graph_engine.graph:
                            g = graph_engine.graph
                            attrs = dict(g.nodes[node_id])
                            node_data = {
                                "name": attrs.get("fqName") or attrs.get("name") or node_id,
                                "type": attrs.get("kind") or attrs.get("type") or "unknown",
                                "file_path": attrs.get("evidence", {}).get("file") if isinstance(attrs.get("evidence"), dict) else attrs.get("file", ""),
                                "code_snippet": attrs.get("evidence", {}).get("snippet") if isinstance(attrs.get("evidence"), dict) else attrs.get("text") or attrs.get("code_snippet") or "",
                            }
                            logger.info(f"[AGENT_CHAT] Found node {node_id} in NetworkX graph as fallback")
                        else:
                            yield f"data: Node '{node_id}' not found in Qdrant or NetworkX graph.\n\n"
                            yield "data: [DONE]\n\n"
                            return
                    else:
                        # Extract node data from Qdrant payload
                        point = results[0]
                        node_data = point.payload if point.payload else {}

                except Exception as e:
                    logger.error(f"[AGENT_CHAT] Error fetching node data: {e}")
                    # Try NetworkX fallback
                    try:
                        if graph_engine and getattr(graph_engine, "graph", None) and node_id in graph_engine.graph:
                            g = graph_engine.graph
                            attrs = dict(g.nodes[node_id])
                            node_data = {
                                "name": attrs.get("fqName") or attrs.get("name") or node_id,
                                "type": attrs.get("kind") or attrs.get("type") or "unknown",
                                "file_path": attrs.get("evidence", {}).get("file") if isinstance(attrs.get("evidence"), dict) else attrs.get("file", ""),
                                "code_snippet": attrs.get("evidence", {}).get("snippet") if isinstance(attrs.get("evidence"), dict) else attrs.get("text") or attrs.get("code_snippet") or "",
                            }
                            logger.info(f"[AGENT_CHAT] Using NetworkX fallback for node {node_id}")
                        else:
                            yield f"data: Error fetching node data: {str(e)}\n\n"
                            yield "data: [DONE]\n\n"
                            return
                    except Exception as fallback_error:
                        yield f"data: Error fetching node data from both Qdrant and NetworkX: {str(e)}, fallback: {str(fallback_error)}\n\n"
                        yield "data: [DONE]\n\n"
                        return

                # Extract node information with fallbacks
                fq_name = node_data.get("name", node_id)
                kind = node_data.get("kind", node_data.get("type", "unknown"))
                file_path = node_data.get("file_path", "")
                snippet = node_data.get("text", node_data.get("code_snippet", ""))

                # Get AI intelligence if available (optional)
                try:
                    from services.code_intelligence.ai_analyzer import get_node_intelligence
                    ai_info = get_node_intelligence(node_id) or {}
                    ai_summary = ai_info.get("aiSummary", "")
                    ai_tags = ai_info.get("aiTags", [])
                except Exception:
                    ai_summary = ""
                    ai_tags = []

                # Build the assistant-facing prompt with rich context
                prompt_template = (
                    "You are a senior code assistant helping with a specific graph node.\n"
                    "Use ONLY the provided context to answer concisely and accurately.\n\n"
                    f"Node: {fq_name}\n"
                    f"Kind: {kind}\n"
                    f"File: {file_path}\n"
                    f"AI Summary: {ai_summary}\n"
                    f"AI Tags: {', '.join(map(str, ai_tags)) if isinstance(ai_tags, (list, tuple)) else ai_tags}\n\n"
                    "Relevant Code:\n"
                    "```\n"
                    f"{snippet}\n"
                    "```\n\n"
                    "Now answer the user's message. If uncertain, say so and suggest next steps."
                )

                # Build messages array with conversation history
                messages = [
                    {"role": "system", "content": "You are a senior code assistant for a code graph."},
                    {"role": "user", "content": prompt_template},
                ]

                # Add conversation history (only assistant and user messages, skip system messages)
                for msg in conversation_history:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        role = msg["role"]
                        if role in ["user", "assistant"]:
                            messages.append({"role": role, "content": msg["content"]})

                # Add current user message
                messages.append({"role": "user", "content": user_message})

                # Stream from OpenAI
                try:
                    stream = openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=0.2,
                        stream=True,
                    )

                    async def iterate_stream():
                        for chunk in stream:
                            delta = None
                            try:
                                delta = chunk.choices[0].delta.content
                            except Exception:
                                delta = None
                            if delta:
                                yield f"data: {delta}\n\n"
                            await asyncio.sleep(0)

                    async for sse_chunk in iterate_stream():
                        yield sse_chunk

                    yield "data: [DONE]\n\n"
                except Exception as e:
                    yield f"data: Error generating response: {str(e)}\n\n"
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
