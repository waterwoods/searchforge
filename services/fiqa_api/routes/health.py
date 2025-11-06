"""
health.py - Qdrant Health Check Endpoint
========================================
Detailed health check endpoint for Qdrant HTTP and gRPC connectivity.

Provides:
- GET /api/health/qdrant - Detailed Qdrant connectivity check
"""

import os
import time
import asyncio
import logging
import requests
from fastapi import APIRouter
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

# ========================================
# Router Setup
# ========================================

router = APIRouter()

# ========================================
# Configuration
# ========================================

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_HTTP_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_GRPC_PORT = int(os.getenv("QDRANT_GRPC_PORT", "6334"))


# ========================================
# Helper Functions
# ========================================

def _check_http() -> Tuple[bool, Optional[str]]:
    """
    Check HTTP connectivity to Qdrant (port 6333).
    Uses short timeout (0.5s) for fast health checks.
    
    Returns:
        (success: bool, error_message: str | None)
    """
    try:
        http_url = f"http://{QDRANT_HOST}:{QDRANT_HTTP_PORT}/"
        response = requests.get(http_url, timeout=0.5)
        if response.status_code == 200:
            return True, None
        else:
            return False, f"HTTP returned status code {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "HTTP request timed out after 0.5 seconds"
    except requests.exceptions.ConnectionError as e:
        return False, f"HTTP connection error: {str(e)}"
    except Exception as e:
        return False, f"HTTP check failed: {str(e)}"


def _check_grpc() -> Tuple[bool, Optional[str]]:
    """
    Check gRPC connectivity to Qdrant (port 6334).
    Uses short timeout (0.5s) for fast health checks.
    
    Returns:
        (success: bool, error_message: str | None)
    """
    try:
        from qdrant_client import QdrantClient
        import grpc
        
        # Create a temporary client for health check with very short timeout
        client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_HTTP_PORT,  # HTTP port for connection setup
            grpc_port=QDRANT_GRPC_PORT,
            prefer_grpc=True,
            timeout=0.5  # Very short timeout for fast health check
        )
        
        # Try to get collections to verify gRPC connectivity
        # The timeout is enforced by QdrantClient itself
        client.get_collections()
        return True, None
    except grpc.RpcError as e:
        # Specifically catch gRPC errors
        return False, f"gRPC error: {str(e)}"
    except Exception as e:
        error_str = str(e)
        if "timeout" in error_str.lower() or "deadline" in error_str.lower():
            return False, "gRPC request timed out after 0.5 seconds"
        return False, str(e)


# ========================================
# Health Check Endpoints
# ========================================

@router.get("/api/health/qdrant")
async def qdrant_health_check() -> Dict[str, Any]:
    """
    Detailed Qdrant health check endpoint.
    
    Checks both HTTP (port 6333) and gRPC (port 6334) connectivity.
    Returns detailed error information for debugging.
    
    Returns:
        {
            "http_ok": bool,
            "grpc_ok": bool,
            "error_http": str | None,
            "error_grpc": str | None,
            "host": str,
            "port": int,
            "grpc_port": int,
            "ts": str
        }
    """
    # Check if in production mode (hide detailed errors)
    is_production = os.getenv("ENV", "").lower() == "prod"
    
    # Run both checks concurrently for better performance
    http_ok, error_http = await asyncio.to_thread(_check_http)
    grpc_ok, error_grpc = await asyncio.to_thread(_check_grpc)
    
    # Prepare response
    response: Dict[str, Any] = {
        "http_ok": http_ok,
        "grpc_ok": grpc_ok,
        "host": QDRANT_HOST,
        "port": QDRANT_HTTP_PORT,
        "grpc_port": QDRANT_GRPC_PORT,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    # Add error details only if not in production
    if not is_production:
        response["error_http"] = error_http
        response["error_grpc"] = error_grpc
    else:
        # In production, only include status codes or minimal info
        if not http_ok:
            response["error_http"] = "HTTP connection failed"
        if not grpc_ok:
            response["error_grpc"] = "gRPC connection failed"
    
    return response


@router.get("/api/health/embeddings")
async def embeddings_health_check() -> Dict[str, Any]:
    """
    Embedding model readiness check endpoint.
    
    Returns:
        {
            "ok": bool,
            "model": str,
            "dim": int | None,
            "backend": str,
            "ts": str
        }
    """
    try:
        from services.fiqa_api.clients import EMBED_READY, get_embedder
    except Exception:
        EMBED_READY = False
    
    model_name = "unknown"
    dim = None
    backend = os.getenv("EMBEDDING_BACKEND", "UNKNOWN")
    
    if EMBED_READY:
        try:
            embedder = get_embedder()
            model_name = getattr(embedder, "model_name", os.getenv("SBERT_MODEL", "unknown"))
            dim = getattr(embedder, "dim", None)
        except Exception as e:
            logger.warning(f"[HEALTH] Failed to get embedder info: {e}")
    
    return {
        "ok": EMBED_READY,
        "model": model_name,
        "dim": dim,
        "backend": backend,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

