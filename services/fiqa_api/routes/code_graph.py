"""
code_graph.py - Code Graph Route Handler
=======================================
Handles code graph endpoints for fetching and visualizing code relationships.
Core logic delegated to services/code_graph_service.py.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.fiqa_api.services.code_graph_service import get_full_graph, get_graph_stats, get_summary_graph, get_local_graph

logger = logging.getLogger(__name__)

# ========================================
# Router Setup
# ========================================

router = APIRouter(prefix="/api")


# ========================================
# Response Models
# ========================================

class GraphNode(BaseModel):
    """Graph node model."""
    id: str
    file_path: str
    name: str
    kind: str
    start_line: int
    end_line: int
    text: str
    language: str


class GraphEdge(BaseModel):
    """Graph edge model."""
    src: str
    dst: str
    type: str
    file_path: str


class GraphResponse(BaseModel):
    """Full graph response model."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class GraphStatsResponse(BaseModel):
    """Graph statistics response model."""
    ok: bool
    collection_name: str
    points_count: int
    vector_size: int
    status: str
    error: str = None


# ========================================
# Route Handlers
# ========================================

@router.get("/codemap/full_graph", response_model=GraphResponse)
async def get_full_code_graph():
    """
    Get the complete code graph with all nodes and edges.
    
    Returns:
        Complete graph data with nodes and edges from the code_graph collection
        
    Raises:
        HTTPException: 500 if graph fetch fails
    """
    try:
        logger.info("[CODE_GRAPH_ROUTE] Fetching full code graph")
        
        # Call service layer
        graph_data = await get_full_graph()
        
        logger.info(f"[CODE_GRAPH_ROUTE] Retrieved graph with {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")
        
        return graph_data
        
    except Exception as e:
        logger.error(f"[CODE_GRAPH_ROUTE] Error fetching code graph: {e}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "ok": False,
                "error": str(e),
                "message": "Failed to fetch code graph"
            }
        )


@router.get("/codemap/summary_graph", response_model=GraphResponse)
async def get_summary_code_graph():
    """
    Get a summary view of the code graph with only entry points and their direct neighbors.
    
    This endpoint returns a smaller, digestible graph that focuses on:
    - Entry points (routes, APIs, controllers)
    - Their direct neighbors (1-hop connections)
    
    This is ideal for initial page loads to avoid "Maximum text size exceeded" errors.
    
    Returns:
        Summary graph data with nodes and edges from entry points and their neighbors
        
    Raises:
        HTTPException: 500 if graph fetch fails
    """
    try:
        logger.info("[CODE_GRAPH_ROUTE] Fetching summary code graph")
        
        # Call service layer
        graph_data = await get_summary_graph()
        
        logger.info(f"[CODE_GRAPH_ROUTE] Retrieved summary graph with {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")
        
        return graph_data
        
    except Exception as e:
        logger.error(f"[CODE_GRAPH_ROUTE] Error fetching summary code graph: {e}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "ok": False,
                "error": str(e),
                "message": "Failed to fetch summary code graph"
            }
        )


@router.get("/codemap/stats", response_model=GraphStatsResponse)
async def get_code_graph_stats():
    """
    Get statistics about the code graph collection.
    
    Returns:
        Collection statistics including point count and status
    """
    try:
        logger.info("[CODE_GRAPH_ROUTE] Fetching code graph statistics")
        
        # Call service layer
        stats = get_graph_stats()
        
        if not stats.get("ok", False):
            raise HTTPException(
                status_code=500,
                detail={
                    "ok": False,
                    "error": stats.get("error", "Unknown error"),
                    "message": "Failed to get graph statistics"
                }
            )
        
        logger.info(f"[CODE_GRAPH_ROUTE] Retrieved stats: {stats['points_count']} points")
        
        return stats
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"[CODE_GRAPH_ROUTE] Error fetching graph stats: {e}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "ok": False,
                "error": str(e),
                "message": "Failed to fetch graph statistics"
            }
        )


@router.get("/codemap/local_graph", response_model=GraphResponse)
async def get_local_code_graph(query: str):
    """
    Get a localized graph centered around a specific node found by flexible search.
    
    This endpoint returns a small, focused graph that shows:
    - The center node (found by flexible search matching ID or name)
    - All direct neighbors (1-hop connections)
    - Only the edges connecting these nodes
    
    This is ideal for on-demand rendering to avoid performance issues.
    
    Args:
        query: The search term to find the center node (matches against ID or name)
        
    Returns:
        Local graph data with nodes and edges from the center node and its neighbors
        
    Raises:
        HTTPException: 500 if graph fetch fails or center node not found
    """
    try:
        logger.info(f"[CODE_GRAPH_ROUTE] Fetching local code graph for search term: {query}")
        
        # Call service layer
        graph_data = await get_local_graph(search_term=query)
        
        logger.info(f"[CODE_GRAPH_ROUTE] Retrieved local graph with {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")
        
        return graph_data
        
    except Exception as e:
        logger.error(f"[CODE_GRAPH_ROUTE] Error fetching local code graph: {e}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "ok": False,
                "error": str(e),
                "message": "Failed to fetch local code graph"
            }
        )
