"""
Minimal FIQA API - FastAPI Application
Self-contained with inlined pipeline manager
"""

import time
import csv
import sys
import random
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, field_validator
import settings

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from logs.metrics_logger import MetricsLogger


class PipelineManager:
    """Minimal pipeline manager with simulated RAG calls"""
    
    def __init__(self):
        self.ready = True
    
    def search(self, query: str, top_k: int = 10) -> dict:
        """
        Simulate RAG pipeline search.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            dict with answers, latency_ms, and cache_hit
        """
        # Simulate processing time
        t0 = time.time()
        time.sleep(random.uniform(0.05, 0.15))
        
        # Generate mock answers
        answers = [f"Answer {i+1} for '{query[:30]}...'" for i in range(top_k)]
        
        # Simulate cache hit
        cache_hit = random.choice([True, False])
        
        latency_ms = (time.time() - t0) * 1000
        
        return {
            "answers": answers,
            "latency_ms": latency_ms,
            "cache_hit": cache_hit
        }


app = FastAPI(title=settings.API_TITLE)
manager = PipelineManager()
metrics_logger = MetricsLogger()

# Track service start time
SERVICE_START_TIME = time.time()

# Simple in-memory rate limiter: {ip: [(timestamp, timestamp, ...)]}
rate_limit_window = defaultdict(list)

# Legacy CSV log path (kept for backward compatibility)
LOG_PATH = Path(__file__).parent / "reports" / "fiqa_api_live.csv"
LOG_PATH.parent.mkdir(exist_ok=True)

# Initialize CSV with header if not exists
if not LOG_PATH.exists():
    with open(LOG_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'query', 'latency_ms', 'cache_hit', 'num_results'])


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('query must be non-empty string')
        return v
    
    @field_validator('top_k')
    @classmethod
    def validate_top_k(cls, v):
        if not 1 <= v <= 20:
            raise ValueError('top_k must be between 1 and 20')
        return v


class SearchResponse(BaseModel):
    answers: list[str]
    latency_ms: float
    cache_hit: bool


def error_response(code: int, msg: str, hint: str = "") -> JSONResponse:
    """Unified error response format"""
    return JSONResponse(
        status_code=code,
        content={
            "code": code,
            "msg": msg,
            "hint": hint,
            "ts": datetime.now(timezone.utc).isoformat()
        }
    )


def check_rate_limit(client_ip: str) -> bool:
    """Check if request is within rate limit. Returns True if allowed."""
    now = time.time()
    
    # Clean old timestamps
    rate_limit_window[client_ip] = [
        ts for ts in rate_limit_window[client_ip] 
        if now - ts < settings.RATE_LIMIT_WINDOW
    ]
    
    # Check limit
    if len(rate_limit_window[client_ip]) >= settings.RATE_LIMIT_MAX:
        return False
    
    # Record this request
    rate_limit_window[client_ip].append(now)
    return True


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with unified format"""
    errors = exc.errors()
    msg = errors[0].get('msg', 'Validation error') if errors else 'Validation error'
    return error_response(422, msg, "Check request body format and field constraints")


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest, request: Request):
    """Search endpoint with validation, rate limiting, and latency tracking"""
    # Rate limit check
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        return error_response(
            429, 
            "Rate limit exceeded", 
            f"Max {settings.RATE_LIMIT_MAX} requests per {settings.RATE_LIMIT_WINDOW}s per IP"
        )
    
    start_time = time.time()
    
    # Call pipeline
    result = manager.search(query=req.query, top_k=req.top_k)
    
    # Calculate total latency
    total_latency_ms = (time.time() - start_time) * 1000
    
    # Estimate tokens (simple heuristic: ~0.75 tokens per word)
    tokens_in = int(len(req.query.split()) * 0.75)
    tokens_out = int(sum(len(ans.split()) * 0.75 for ans in result['answers']))
    # Simple cost estimation: $0.01 per 1K tokens input, $0.03 per 1K tokens output
    est_cost = (tokens_in * 0.01 + tokens_out * 0.03) / 1000.0
    
    # Log to legacy CSV (for backward compatibility)
    with open(LOG_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            time.time(),
            req.query[:50],  # Truncate long queries
            f"{total_latency_ms:.2f}",
            result['cache_hit'],
            len(result['answers'])
        ])
    
    # Log to new metrics logger
    metrics_logger.log(
        p95_ms=total_latency_ms,
        recall_at10=0.85,  # Mock value - would be real in production
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        est_cost=est_cost,
        success=True
    )
    
    return SearchResponse(
        answers=result['answers'],
        latency_ms=total_latency_ms,
        cache_hit=result['cache_hit']
    )


@app.get("/metrics")
def get_metrics():
    """Get rolling average metrics with extended system info"""
    base_metrics = metrics_logger.compute_rolling_averages(window=100)
    
    # Add extended fields
    base_metrics.update({
        "window_sec": settings.METRICS_WINDOW,
        "uptime_sec": int(time.time() - SERVICE_START_TIME),
        "version": settings.API_VERSION
    })
    
    return base_metrics


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
