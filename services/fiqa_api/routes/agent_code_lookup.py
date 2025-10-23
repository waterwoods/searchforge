"""
agent_code_lookup.py - Code Lookup Route Handler
================================================
Handles /api/agent/code_lookup endpoint with parameter validation.
Core logic delegated to services/code_lookup_service.py.
"""

import logging
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
        
        # Generate mock edges_json for call graph visualization
        mock_edges = [
            EdgeData(src="main.py::start", dst="controller.py::init", type="calls"),
            EdgeData(src="controller.py::init", dst="config.py::load_settings", type="calls"),
            EdgeData(src="controller.py::init", dst="database.py::connect", type="calls"),
            EdgeData(src="config.py::load_settings", dst="settings.py::get_config", type="calls"),
            EdgeData(src="database.py::connect", dst="models.py::User", type="imports"),
            EdgeData(src="models.py::User", dst="auth.py::authenticate", type="calls"),
            EdgeData(src="auth.py::authenticate", dst="utils.py::hash_password", type="calls"),
            EdgeData(src="utils.py::hash_password", dst="crypto.py::sha256", type="calls"),
        ]
        
        response_obj = CodeLookupResponse(
            rid=request_id,
            agent=result["agent"],
            intent=result["intent"],
            query=result["query"],
            summary_md=result["summary_md"],
            files=files,
            edges_json=mock_edges
        )
        
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

