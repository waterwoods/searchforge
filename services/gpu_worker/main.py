"""
GPU Worker Service - FastAPI service for GPU-accelerated embeddings and reranking.

Endpoints:
- GET /healthz: Health check (process alive)
- GET /meta: Metadata (model names, git SHA, device)
- GET /ready: Readiness check (models loaded + warmup done)
- POST /embed: Embed texts with optional normalization
- POST /rerank: Rerank documents with query
"""

import os
import time
import asyncio
import logging
from typing import List, Optional, Dict, Any
from collections import deque
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import numpy as np


def get_git_sha() -> tuple[str, str]:
    """Get git SHA, with fallback if gitinfo module not available."""
    try:
        from services.fiqa_api.utils.gitinfo import get_git_sha as _get_git_sha
        return _get_git_sha()
    except (ImportError, AttributeError):
        # Fallback: try to get from environment or git directly
        git_sha = os.getenv("GIT_SHA", "unknown")
        if git_sha == "unknown":
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    git_sha = result.stdout.strip()
            except Exception:
                pass
        return git_sha, "env_or_git"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Environment variables
MODEL_EMBED = os.getenv("MODEL_EMBED", "sentence-transformers/all-MiniLM-L6-v2")
MODEL_RERANK = os.getenv("MODEL_RERANK", "cross-encoder/ms-marco-MiniLM-L-12-v2")
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "2"))
QUEUE_LIMIT = int(os.getenv("QUEUE_LIMIT", "128"))
BATCH_WINDOW_MS = int(os.getenv("BATCH_WINDOW_MS", "20"))
PORT = int(os.getenv("PORT", "8090"))

# Global state
_embed_model = None
_rerank_model = None
_device = None
_ready = False
_git_sha = None

# Concurrency control
_semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
_request_queue = deque(maxlen=QUEUE_LIMIT)

# Micro-batching state for /embed
_embed_batch_queue = []
_embed_batch_event = asyncio.Event()
_embed_batch_lock = asyncio.Lock()


def get_device():
    """Get device (cuda if available, else cpu)."""
    global _device
    if _device is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"[DEVICE] Using device: {_device}")
        if _device == "cuda":
            logger.info(f"[DEVICE] CUDA device: {torch.cuda.get_device_name(0)}")
    return _device


async def load_models():
    """Load embedding and reranking models."""
    global _embed_model, _rerank_model, _ready, _git_sha
    
    device = get_device()
    _git_sha, _ = get_git_sha()
    
    logger.info(f"[MODELS] Loading embedding model: {MODEL_EMBED} on {device}")
    try:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer(MODEL_EMBED, device=device)
        logger.info(f"[MODELS] Embedding model loaded: {MODEL_EMBED}")
    except Exception as e:
        logger.error(f"[MODELS] Failed to load embedding model: {e}")
        raise
    
    logger.info(f"[MODELS] Loading rerank model: {MODEL_RERANK} on {device}")
    try:
        from sentence_transformers import CrossEncoder
        _rerank_model = CrossEncoder(MODEL_RERANK, device=device, max_length=512)
        logger.info(f"[MODELS] Rerank model loaded: {MODEL_RERANK}")
    except Exception as e:
        logger.error(f"[MODELS] Failed to load rerank model: {e}")
        raise
    
    # Warmup: run one forward pass for each model
    logger.info("[WARMUP] Running warmup forward passes...")
    warmup_start = time.time()
    
    try:
        # Embedding warmup
        test_texts = ["warmup test"]
        _ = _embed_model.encode(test_texts, normalize_embeddings=False)
        embed_warmup_ms = (time.time() - warmup_start) * 1000
        
        # Rerank warmup
        rerank_start = time.time()
        test_pairs = [["warmup query", "warmup document"]]
        _ = _rerank_model.predict(test_pairs)
        rerank_warmup_ms = (time.time() - rerank_start) * 1000
        
        total_warmup_ms = (time.time() - warmup_start) * 1000
        logger.info(
            f"[WARMUP] Complete - embed: {embed_warmup_ms:.1f}ms, "
            f"rerank: {rerank_warmup_ms:.1f}ms, total: {total_warmup_ms:.1f}ms"
        )
        
        _ready = True
        logger.info(f"[READY] GPU worker ready (device={device}, git_sha={_git_sha})")
    except Exception as e:
        logger.error(f"[WARMUP] Warmup failed: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("=" * 60)
    logger.info("GPU Worker Service - Starting Up")
    logger.info("=" * 60)
    
    try:
        await load_models()
    except Exception as e:
        logger.error(f"[STARTUP] Failed to load models: {e}")
        raise
    
    # Start micro-batching background task
    asyncio.create_task(_embed_batch_processor())
    
    yield
    
    # Shutdown
    logger.info("GPU Worker Service - Shutting Down")


app = FastAPI(
    title="GPU Worker",
    description="GPU-accelerated embeddings and reranking service",
    version="1.0.0",
    lifespan=lifespan
)


# Request models
class EmbedRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to embed")
    normalize: bool = Field(default=False, description="Normalize embeddings to unit length")


class RerankRequest(BaseModel):
    query: str = Field(..., description="Query text")
    docs: List[str] = Field(..., description="List of document texts to rerank")
    top_n: Optional[int] = Field(default=None, description="Number of top results to return")


# Response models
class EmbedResponse(BaseModel):
    vectors: List[List[float]] = Field(..., description="List of embedding vectors")


class RerankResponse(BaseModel):
    indices: List[int] = Field(..., description="Indices of top documents (original order)")
    scores: List[float] = Field(..., description="Relevance scores for top documents")


# Endpoints
@app.get("/healthz")
async def healthz():
    """Health check: returns 200 if process is alive."""
    return {"ok": True}


@app.get("/meta")
async def meta():
    """Get metadata: model names, git SHA, device."""
    return {
        "model_embed": MODEL_EMBED,
        "model_rerank": MODEL_RERANK,
        "git_sha": _git_sha or "unknown",
        "device": get_device()
    }


@app.get("/ready")
async def ready():
    """Readiness check: returns 200 only after models loaded + warmup done."""
    if not _ready:
        raise HTTPException(status_code=503, detail="Models not ready")
    return {"ok": True, "ready": True}


async def _embed_batch_processor():
    """Background task to process batched embedding requests."""
    while True:
        try:
            # Wait for batch window or event
            await asyncio.sleep(BATCH_WINDOW_MS / 1000.0)
            
            async with _embed_batch_lock:
                if not _embed_batch_queue:
                    continue
                
                # Collect all pending requests
                batch = list(_embed_batch_queue)
                _embed_batch_queue.clear()
            
            if not batch:
                continue
            
            # Process batch
            all_texts = []
            all_futures = []
            all_normalize = []
            
            for req_texts, normalize, future in batch:
                all_texts.extend(req_texts)
                all_futures.append((future, len(req_texts)))
                all_normalize.append(normalize)
            
            # Use most common normalize setting (or first if mixed)
            normalize = all_normalize[0] if all_normalize else False
            
            try:
                # Encode batch
                vectors = _embed_model.encode(all_texts, normalize_embeddings=normalize)
                
                # Split results back to original requests
                idx = 0
                for (future, count), normalize_req in zip(all_futures, all_normalize):
                    batch_vectors = vectors[idx:idx + count]
                    # Re-normalize if needed (if batch used different setting)
                    if normalize_req != normalize:
                        # Re-normalize this subset
                        batch_vectors = batch_vectors / np.linalg.norm(batch_vectors, axis=1, keepdims=True)
                    future.set_result(batch_vectors.tolist())
                    idx += count
            except Exception as e:
                logger.error(f"[BATCH] Batch processing failed: {e}")
                # Set exception on all futures
                for future, _ in all_futures:
                    if not future.done():
                        try:
                            future.set_exception(e)
                        except Exception:
                            pass  # Future may have been cancelled
        except Exception as e:
            logger.error(f"[BATCH] Batch processor error: {e}")
            await asyncio.sleep(0.1)


@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    """Embed texts with optional normalization. Supports micro-batching."""
    # Check concurrency limit
    if len(_request_queue) >= QUEUE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Queue limit reached ({QUEUE_LIMIT})"
        )
    
    # Acquire semaphore (non-blocking check)
    if _semaphore.locked() and len(_request_queue) >= MAX_CONCURRENCY:
        raise HTTPException(
            status_code=429,
            detail=f"Concurrency limit reached ({MAX_CONCURRENCY})"
        )
    
    async with _semaphore:
        _request_queue.append(time.time())
        
        try:
            # Add to batch queue
            future = asyncio.Future()
            async with _embed_batch_lock:
                _embed_batch_queue.append((request.texts, request.normalize, future))
            
            # Wait for batch processing (with timeout)
            try:
                vectors = await asyncio.wait_for(future, timeout=5.0)
                return EmbedResponse(vectors=vectors)
            except asyncio.TimeoutError:
                # Fallback: process immediately (remove from batch queue)
                async with _embed_batch_lock:
                    try:
                        _embed_batch_queue.remove((request.texts, request.normalize, future))
                    except ValueError:
                        pass  # Already removed
                logger.warning(f"[EMBED] Batch timeout, processing immediately (n={len(request.texts)})")
                vectors = _embed_model.encode(
                    request.texts,
                    normalize_embeddings=request.normalize
                )
                return EmbedResponse(vectors=vectors.tolist())
        except Exception as e:
            logger.error(f"[EMBED] Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            # Remove from queue
            if _request_queue:
                _request_queue.popleft()


@app.post("/rerank", response_model=RerankResponse)
async def rerank(request: RerankRequest):
    """Rerank documents with query. Returns top_n indices and scores."""
    # Check concurrency limit
    if len(_request_queue) >= QUEUE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Queue limit reached ({QUEUE_LIMIT})"
        )
    
    async with _semaphore:
        _request_queue.append(time.time())
        
        try:
            if not request.docs:
                return RerankResponse(indices=[], scores=[])
            
            # Prepare pairs: [[query, doc1], [query, doc2], ...]
            pairs = [[request.query, doc] for doc in request.docs]
            
            # Predict scores
            with torch.no_grad():
                scores = _rerank_model.predict(pairs, batch_size=32, show_progress_bar=False)
            
            # Convert to numpy for easier sorting
            scores = np.array(scores)
            
            # Get top_n indices (sorted by score descending)
            top_n = request.top_n or len(request.docs)
            top_n = min(top_n, len(request.docs))
            
            # Get indices sorted by score
            top_indices = np.argsort(scores)[::-1][:top_n]
            top_scores = scores[top_indices]
            
            return RerankResponse(
                indices=top_indices.tolist(),
                scores=top_scores.tolist()
            )
        except Exception as e:
            logger.error(f"[RERANK] Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            # Remove from queue
            if _request_queue:
                _request_queue.popleft()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

