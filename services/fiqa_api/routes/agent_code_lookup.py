"""
agent_code_lookup.py - Code Lookup Route Handler
================================================
Handles /api/agent/code_lookup endpoint with parameter validation.
Core logic delegated to services/code_lookup_service.py.
"""

import logging
import os
import time
import uuid
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.fiqa_api.services.code_lookup_service import do_code_lookup

logger = logging.getLogger(__name__)

# ========================================
# Router Setup
# ========================================

router = APIRouter()


# ========================================
# Request/Response Models
# ========================================

class CodeLookupRequest(BaseModel):
    """Request model for code lookup."""
    message: str


class NeighborSnippet(BaseModel):
    """Neighbor code snippet (one-hop relation)."""
    path: str
    snippet: str
    relation: str
    name: str
    start_line: int
    end_line: int


class CodeFile(BaseModel):
    """Individual code file result."""
    path: str
    language: str
    start_line: int
    end_line: int
    snippet: str
    why_relevant: str
    neighbors: List[NeighborSnippet] = []  # Optional list of related code snippets


class EdgeData(BaseModel):
    """Edge data for call graph visualization."""
    src: str
    dst: str
    type: str


class CodeLookupResponse(BaseModel):
    """Response model for code lookup."""
    rid: str  # Request ID for tracking
    agent: str
    intent: str
    query: str
    summary_md: str
    files: List[CodeFile]
    edges_json: List[EdgeData] = []  # New field for call graph visualization


class DirectGraphRequest(BaseModel):
    """Request model for direct graph generation."""
    query: str


class DirectGraphResponse(BaseModel):
    """Response model for direct graph generation."""
    mermaidText: str
    nodeDetails: dict


# ========================================
# Route Handler
# ========================================

@router.post("/api/agent/code_lookup", response_model=CodeLookupResponse)
async def code_lookup(request: CodeLookupRequest):
    """
    Search codebase using Qdrant vector search with LLM summarization.
    
    This endpoint provides semantic code search powered by Qdrant vector database.
    It embeds the user's query, searches for similar code snippets, and uses
    GPT-4o mini to generate a concise summary and select the most relevant files.
    
    Args:
        request: CodeLookupRequest with message field
        
    Returns:
        CodeLookupResponse with LLM-generated summary and top files
        
    Environment:
        OPENAI_API_KEY: Required for LLM summarization (optional, falls back to raw results)
        CODE_LOOKUP_LLM_MODEL: LLM model (default: gpt-4o-mini)
        CODE_LOOKUP_LLM_TIMEOUT_MS: Timeout in ms (default: 3000)
        
    Example:
        POST /api/agent/code_lookup
        {
            "message": "embedding code"
        }
    """
    # Performance tracking
    start = time.perf_counter()
    
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())
    
    # Check if clients are ready
    from services.fiqa_api.clients import are_clients_ready
    
    if not are_clients_ready():
        raise HTTPException(
            status_code=503,
            detail="Code lookup service unavailable. Clients not initialized."
        )
    
    try:
        # Call service layer
        result = do_code_lookup(message=request.message)
        
        # Convert files to Pydantic models
        files = [
            CodeFile(
                path=f["path"],
                language=f["language"],
                start_line=f["start_line"],
                end_line=f["end_line"],
                snippet=f["snippet"],
                why_relevant=f["why_relevant"],
                neighbors=[
                    NeighborSnippet(
                        path=n["path"],
                        snippet=n["snippet"],
                        relation=n["relation"],
                        name=n["name"],
                        start_line=n["start_line"],
                        end_line=n["end_line"]
                    )
                    for n in f.get("neighbors", [])
                ]
            )
            for f in result["files"]
        ]
        
        # Extract real edges from service result files
        all_edges = []
        if result and result.get("files"):
            # Get Qdrant client to fetch file-level edge data
            from services.fiqa_api.clients import get_qdrant_client
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            import json
            
            qdrant_client = get_qdrant_client()
            collection_name = os.getenv("QDRANT_COLLECTION_NAME", os.getenv("COLLECTION_NAME", "searchforge_codebase"))
            
            # Extract edges from each file in the result
            for file_data in result["files"]:
                file_path = file_data.get("path")
                if not file_path:
                    continue
                
                try:
                    # Find the file-level point in Qdrant to get edges_json
                    file_filter = Filter(
                        must=[
                            FieldCondition(key="file_path", match=MatchValue(value=file_path)),
                            FieldCondition(key="kind", match=MatchValue(value="file"))
                        ]
                    )
                    
                    file_results = qdrant_client.scroll(
                        collection_name=collection_name,
                        scroll_filter=file_filter,
                        limit=1
                    )
                    
                    if file_results and file_results[0]:
                        file_point = file_results[0][0]
                        file_payload = file_point.payload
                        
                        # Parse edges_json from file payload
                        edges_json_str = file_payload.get('edges_json', '[]')
                        if edges_json_str and edges_json_str != '[]':
                            try:
                                file_edges = json.loads(edges_json_str)
                                if isinstance(file_edges, list):
                                    # Convert edges to EdgeData objects, handling etype vs type mapping
                                    for edge in file_edges:
                                        if isinstance(edge, dict) and 'src' in edge and 'dst' in edge:
                                            # Map etype to type field
                                            edge_type = edge.get('type', edge.get('etype', 'unknown'))
                                            all_edges.append(EdgeData(
                                                src=edge['src'],
                                                dst=edge['dst'],
                                                type=edge_type
                                            ))
                            except json.JSONDecodeError as e:
                                logger.warning(f"[EDGE_EXTRACT] Failed to parse edges_json for {file_path}: {e}")
                                continue
                
                except Exception as e:
                    logger.warning(f"[EDGE_EXTRACT] Failed to fetch edges for {file_path}: {e}")
                    continue
            
            # Deduplicate edges to keep the graph clean
            unique_edges = {}
            for edge in all_edges:
                edge_key = f"{edge.src}->{edge.dst}"
                if edge_key not in unique_edges:
                    unique_edges[edge_key] = edge
            
            final_edges = list(unique_edges.values())
        else:
            final_edges = []
        
        response_obj = CodeLookupResponse(
            rid=request_id,
            agent=result["agent"],
            intent=result["intent"],
            query=result["query"],
            summary_md=result["summary_md"],
            files=files,
            edges_json=final_edges
        )
        
        # Debug logging - log the final_edges data being sent to frontend
        logger.info(f"Returning {len(final_edges)} edges to frontend: {final_edges}")
        
        # Debug logging
        logger.info(f"[DEBUG] req_id_in = {request_id}, rid_out = {response_obj.rid}, edges_json length = {len(response_obj.edges_json)}, total hits = {len(response_obj.files)}")
        
        # Log performance
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"[Perf] /api/agent/code_lookup took {elapsed:.1f} ms")
        
        return response_obj
        
    except RuntimeError as e:
        # Service layer errors (client issues)
        logger.error(f"[CODE_LOOKUP] Service error: {e}")
        
        # Log performance even on error
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"[Perf] /api/agent/code_lookup took {elapsed:.1f} ms (error)")
        
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected errors
        logger.error(f"[CODE_LOOKUP] Unexpected error: {e}")
        
        # Log performance even on error
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"[Perf] /api/agent/code_lookup took {elapsed:.1f} ms (error)")
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during code lookup: {str(e)}"
        )


@router.post("/api/graph/direct_from_query", response_model=DirectGraphResponse)
async def direct_graph_from_query(request: DirectGraphRequest):
    """
    Generate graph data directly from a search query without relying on cache.
    
    This endpoint bypasses the Redis cache and directly executes a code lookup
    to generate fresh graph data. It's designed to replace the cache-dependent
    graph generation for better reliability.
    
    Args:
        request: DirectGraphRequest with query field
        
    Returns:
        DirectGraphResponse with mermaidText and nodeDetails
        
    Environment:
        OPENAI_API_KEY: Required for LLM summarization (optional, falls back to raw results)
        CODE_LOOKUP_LLM_MODEL: LLM model (default: gpt-4o-mini)
        CODE_LOOKUP_LLM_TIMEOUT_MS: Timeout in ms (default: 3000)
    """
    # Performance tracking
    start = time.perf_counter()
    
    # Check if clients are ready
    from services.fiqa_api.clients import are_clients_ready
    
    if not are_clients_ready():
        raise HTTPException(
            status_code=503,
            detail="Code lookup service unavailable. Clients not initialized."
        )
    
    try:
        # Call service layer directly
        result = do_code_lookup(message=request.query)
        
        # Extract real edges from service result files
        all_edges = []
        if result and result.get("files"):
            # Get Qdrant client to fetch file-level edge data
            from services.fiqa_api.clients import get_qdrant_client
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            import json
            import os
            
            qdrant_client = get_qdrant_client()
            collection_name = os.getenv("QDRANT_COLLECTION_NAME", os.getenv("COLLECTION_NAME", "searchforge_codebase"))
            
            # Extract edges from each file in the result
            for file_data in result["files"]:
                file_path = file_data.get("path")
                if not file_path:
                    continue
                
                try:
                    # Find the file-level point in Qdrant to get edges_json
                    file_filter = Filter(
                        must=[
                            FieldCondition(key="file_path", match=MatchValue(value=file_path)),
                            FieldCondition(key="kind", match=MatchValue(value="file"))
                        ]
                    )
                    
                    file_results = qdrant_client.scroll(
                        collection_name=collection_name,
                        scroll_filter=file_filter,
                        limit=1
                    )
                    
                    if file_results and file_results[0]:
                        file_point = file_results[0][0]
                        file_payload = file_point.payload
                        
                        # Parse edges_json from file payload
                        edges_json_str = file_payload.get('edges_json', '[]')
                        if edges_json_str and edges_json_str != '[]':
                            try:
                                file_edges = json.loads(edges_json_str)
                                if isinstance(file_edges, list):
                                    # Convert edges to EdgeData objects, handling etype vs type mapping
                                    for edge in file_edges:
                                        if isinstance(edge, dict) and 'src' in edge and 'dst' in edge:
                                            # Map etype to type field
                                            edge_type = edge.get('type', edge.get('etype', 'unknown'))
                                            all_edges.append(EdgeData(
                                                src=edge['src'],
                                                dst=edge['dst'],
                                                type=edge_type
                                            ))
                            except json.JSONDecodeError as e:
                                logger.warning(f"[DIRECT_GRAPH] Failed to parse edges_json for {file_path}: {e}")
                                continue
                
                except Exception as e:
                    logger.warning(f"[DIRECT_GRAPH] Failed to fetch edges for {file_path}: {e}")
                    continue
            
            # Deduplicate edges to keep the graph clean
            unique_edges = {}
            for edge in all_edges:
                edge_key = f"{edge.src}->{edge.dst}"
                if edge_key not in unique_edges:
                    unique_edges[edge_key] = edge
            
            final_edges = list(unique_edges.values())
        else:
            final_edges = []
        
        # Convert edges to Mermaid format using the existing helper function
        # Import the helper function from app_main
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app_main import convert_edges_to_mermaid_data
        
        # Convert files to the format expected by the helper function
        files_for_conversion = [
            {
                "path": f["path"],
                "snippet": f["snippet"],
                "language": f["language"]
            }
            for f in result["files"]
        ]
        
        # Convert edges to the format expected by the helper function
        edges_for_conversion = [
            {
                "src": edge.src,
                "dst": edge.dst,
                "type": edge.type
            }
            for edge in final_edges
        ]
        
        # Generate Mermaid data
        mermaid_data = convert_edges_to_mermaid_data(edges_for_conversion, files_for_conversion)
        
        # Add diagnostic logging to track mermaid_data generation
        logger.info(f"Generated Mermaid Data before return: {mermaid_data}")
        
        # Bulletproof check: ensure we always return valid, renderable Mermaid syntax
        mermaid_text = mermaid_data.get("mermaidText", "")
        
        if not mermaid_text or not mermaid_text.strip():
            logger.warning("Generated mermaid text was empty. Returning a default 'no relationships' graph.")
            # This is the standard, valid Mermaid syntax for our empty message
            mermaid_data["mermaidText"] = "graph TD\n    A[\"No code relationships found to visualize\"]"
            # Also ensure nodeDetails is populated for consistency
            mermaid_data["nodeDetails"] = {
                "A": {
                    "code": "No code relationships found to visualize",
                    "filePath": "No data available"
                }
            }
        
        # Log performance
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"[Perf] /api/graph/direct_from_query took {elapsed:.1f} ms")
        
        return DirectGraphResponse(
            mermaidText=mermaid_data["mermaidText"],
            nodeDetails=mermaid_data["nodeDetails"]
        )
        
    except RuntimeError as e:
        # Service layer errors (client issues)
        logger.error(f"[DIRECT_GRAPH] Service error: {e}")
        
        # Log performance even on error
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"[Perf] /api/graph/direct_from_query took {elapsed:.1f} ms (error)")
        
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected errors
        logger.error(f"[DIRECT_GRAPH] Unexpected error: {e}")
        
        # Log performance even on error
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"[Perf] /api/graph/direct_from_query took {elapsed:.1f} ms (error)")
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during direct graph generation: {str(e)}"
        )

