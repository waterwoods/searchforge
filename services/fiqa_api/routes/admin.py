"""
admin.py - Admin API Routes
============================
Admin endpoints for warmup, cache management, system tuning, and policy management.
"""

import logging
import time
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ========================================
# Policy Management State
# ========================================

_CURRENT_POLICY: Dict[str, Any] = {
    "name": "baseline_v1",
    "applied_at": None,
    "source": "default",
    "params": {},
    "sha": None
}

_POLICY_FILE = Path(__file__).parent.parent.parent.parent / "configs" / "policies.json"
_SLA_BREACH_COUNT = 0
_SLA_HISTORY = []  # List of {timestamp, p95_ms, error_rate, breach}

def _load_policies() -> Dict[str, Any]:
    """Load policies from configs/policies.json."""
    if not _POLICY_FILE.exists():
        raise HTTPException(status_code=500, detail=f"Policy file not found: {_POLICY_FILE}")
    try:
        with open(_POLICY_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load policies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load policies: {e}")

def _get_policy_params(policy_name: str) -> Dict[str, Any]:
    """Get policy parameters by name."""
    policies_data = _load_policies()
    policies = policies_data.get("policies", {})
    if policy_name not in policies:
        raise HTTPException(status_code=404, detail=f"Policy not found: {policy_name}")
    return policies[policy_name]


class WarmupRequest(BaseModel):
    """Request model for warmup endpoint."""
    limit: int = Field(default=100, ge=1, le=1000, description="Number of warmup queries to run")
    timeout_sec: int = Field(default=300, ge=10, le=600, description="Total timeout in seconds")


class WarmupResponse(BaseModel):
    """Response model for warmup endpoint."""
    ok: bool
    queries_run: int
    duration_ms: float
    avg_latency_ms: float
    p95_latency_ms: float
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0


@router.post("/warmup", response_model=WarmupResponse)
async def warmup(request: WarmupRequest) -> WarmupResponse:
    """
    Prewarm system by running sample queries to populate caches.
    
    This endpoint:
    1. Runs `limit` warmup queries using sample questions
    2. Populates embedding cache, BM25 cache, and connection pools
    3. Returns latency metrics and cache hit rates
    
    Args:
        request: Warmup configuration (limit, timeout_sec)
        
    Returns:
        Warmup statistics including latency metrics and cache hit rates
    """
    start_time = time.perf_counter()
    
    try:
        from services.fiqa_api.clients import get_encoder_model, get_qdrant_client, get_redis_client, ensure_qdrant_connection
        from services.fiqa_api.services.search_core import perform_search
        
        # Ensure connections are healthy
        if not ensure_qdrant_connection():
            raise HTTPException(status_code=503, detail="Qdrant connection unhealthy")
        
        # Sample warmup queries (diverse set to warm up caches)
        warmup_queries = [
            "financial advisor",
            "investment strategy",
            "retirement planning",
            "stock market analysis",
            "mutual funds",
            "portfolio diversification",
            "asset allocation",
            "risk management",
            "tax planning",
            "estate planning",
            "401k retirement",
            "dividend investing",
            "bond yields",
            "real estate investment",
            "cryptocurrency trading",
            "hedge fund strategies",
            "index fund comparison",
            "ETF selection",
            "market volatility",
            "economic indicators"
        ]
        
        queries_run = 0
        latencies = []
        cache_hits = 0
        cache_misses = 0
        
        logger.info(f"[WARMUP] Starting warmup with {request.limit} queries (timeout={request.timeout_sec}s)")
        
        # Run warmup queries
        for i in range(request.limit):
            # Check timeout
            elapsed = time.perf_counter() - start_time
            if elapsed > request.timeout_sec:
                logger.warning(f"[WARMUP] Timeout reached after {queries_run} queries")
                break
            
            # Select query (cycle through sample queries)
            query = warmup_queries[i % len(warmup_queries)]
            
            try:
                # Run search (no need to check result, just warm up caches)
                query_start = time.perf_counter()
                result = perform_search(
                    query=query,
                    top_k=10,
                    collection="fiqa_10k_v1",
                    use_hybrid=True,
                    rerank=False
                )
                query_latency = (time.perf_counter() - query_start) * 1000
                
                latencies.append(query_latency)
                queries_run += 1
                
                # Track cache hits (if available in observability_metrics)
                obs = result.get("observability_metrics", {})
                if "cache_hit" in obs:
                    if obs["cache_hit"]:
                        cache_hits += 1
                    else:
                        cache_misses += 1
                
            except Exception as e:
                logger.warning(f"[WARMUP] Query {i+1} failed: {e}")
                continue
        
        # Calculate statistics
        total_duration_ms = (time.perf_counter() - start_time) * 1000
        avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0
        p95_latency_ms = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        
        total_cache_queries = cache_hits + cache_misses
        cache_hit_rate = (cache_hits / total_cache_queries) if total_cache_queries > 0 else 0.0
        
        logger.info(f"[WARMUP] Completed: {queries_run} queries in {total_duration_ms:.0f}ms, "
                   f"avg={avg_latency_ms:.1f}ms, p95={p95_latency_ms:.1f}ms, "
                   f"cache_hit_rate={cache_hit_rate:.1%}")
        
        return WarmupResponse(
            ok=True,
            queries_run=queries_run,
            duration_ms=round(total_duration_ms, 2),
            avg_latency_ms=round(avg_latency_ms, 2),
            p95_latency_ms=round(p95_latency_ms, 2),
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            cache_hit_rate=round(cache_hit_rate, 4)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WARMUP] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Warmup failed: {str(e)}")


# ========================================
# Policy Management Endpoints
# ========================================

class PolicyApplyResponse(BaseModel):
    """Response model for policy apply endpoint."""
    ok: bool
    policy_name: str
    applied_at: str
    params: Dict[str, Any]
    previous_policy: str


class PolicyCurrentResponse(BaseModel):
    """Response model for current policy endpoint."""
    policy_name: str
    applied_at: Optional[str]
    params: Dict[str, Any]
    source: str
    sla_breach_count: int
    sla_history_size: int


@router.post("/policy/apply", response_model=PolicyApplyResponse)
async def apply_policy(name: str = Query(..., description="Policy name to apply")) -> PolicyApplyResponse:
    """
    Apply a named policy from configs/policies.json.
    
    This atomically switches the current policy and logs the change.
    All subsequent searches will use this policy unless explicitly overridden.
    
    Args:
        name: Policy name (e.g., 'balanced_v1', 'fast_v1', 'quality_v1', 'baseline_v1')
        
    Returns:
        Applied policy details and previous policy name
    """
    global _CURRENT_POLICY, _SLA_BREACH_COUNT
    
    try:
        # Validate policy exists
        params = _get_policy_params(name)
        
        # Get SHA from git (if available)
        sha = None
        try:
            from services.fiqa_api.utils.gitinfo import get_git_sha
            sha = get_git_sha()
        except Exception:
            pass
        
        # Record previous policy
        previous_policy = _CURRENT_POLICY.get("name", "unknown")
        
        # Apply new policy atomically
        applied_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _CURRENT_POLICY = {
            "name": name,
            "applied_at": applied_at,
            "source": "winners.final",
            "params": params,
            "sha": sha
        }
        
        # Reset SLA breach counter on policy change
        _SLA_BREACH_COUNT = 0
        
        logger.info(f"[POLICY_APPLY] name={name} params={json.dumps(params)} ts={applied_at} sha={sha}")
        
        return PolicyApplyResponse(
            ok=True,
            policy_name=name,
            applied_at=applied_at,
            params=params,
            previous_policy=previous_policy
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[POLICY_APPLY] Failed to apply policy {name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to apply policy: {str(e)}")


@router.get("/policy/current", response_model=PolicyCurrentResponse)
async def get_current_policy() -> PolicyCurrentResponse:
    """
    Get the currently active policy.
    
    Returns the policy name, parameters, and SLA monitoring state.
    """
    global _CURRENT_POLICY, _SLA_BREACH_COUNT, _SLA_HISTORY
    
    # Ensure policy is initialized
    if not _CURRENT_POLICY.get("params"):
        try:
            params = _get_policy_params(_CURRENT_POLICY.get("name", "baseline_v1"))
            _CURRENT_POLICY["params"] = params
        except Exception as e:
            logger.warning(f"Failed to load default policy: {e}")
    
    return PolicyCurrentResponse(
        policy_name=_CURRENT_POLICY.get("name", "baseline_v1"),
        applied_at=_CURRENT_POLICY.get("applied_at"),
        params=_CURRENT_POLICY.get("params", {}),
        source=_CURRENT_POLICY.get("source", "default"),
        sla_breach_count=_SLA_BREACH_COUNT,
        sla_history_size=len(_SLA_HISTORY)
    )


@router.get("/policy/list")
async def list_policies() -> Dict[str, Any]:
    """
    List all available policies.
    
    Returns all policies defined in configs/policies.json.
    """
    try:
        policies_data = _load_policies()
        return {
            "ok": True,
            "policies": policies_data.get("policies", {}),
            "default_policy": policies_data.get("default_policy", "balanced_v1"),
            "sla_thresholds": policies_data.get("sla_thresholds", {})
        }
    except Exception as e:
        logger.error(f"[POLICY_LIST] Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list policies: {str(e)}")


def get_current_policy_params() -> Dict[str, Any]:
    """
    Helper function to get current policy params (used by other modules).
    """
    global _CURRENT_POLICY
    if not _CURRENT_POLICY.get("params"):
        try:
            params = _get_policy_params(_CURRENT_POLICY.get("name", "baseline_v1"))
            _CURRENT_POLICY["params"] = params
        except Exception as e:
            logger.warning(f"Failed to load default policy: {e}")
            return {}
    return _CURRENT_POLICY.get("params", {})


def record_sla_check(p95_ms: float, error_rate: float) -> bool:
    """
    Record SLA check and return True if auto-rollback should be triggered.
    
    Args:
        p95_ms: P95 latency in milliseconds
        error_rate: Error rate (0.0 to 1.0)
        
    Returns:
        True if rollback should be triggered, False otherwise
    """
    global _SLA_BREACH_COUNT, _SLA_HISTORY, _CURRENT_POLICY
    
    # Load SLA thresholds
    try:
        policies_data = _load_policies()
        thresholds = policies_data.get("sla_thresholds", {})
        p95_budget = thresholds.get("p95_budget_ms", 1500)
        err_budget = thresholds.get("error_budget_rate", 0.01)
        breach_streak = thresholds.get("breach_streak", 2)
        rollback_target = thresholds.get("rollback_target", "baseline_v1")
    except Exception as e:
        logger.error(f"Failed to load SLA thresholds: {e}")
        return False
    
    # Check for breach
    breach = (p95_ms > p95_budget) or (error_rate > err_budget)
    
    # Record in history
    _SLA_HISTORY.append({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "p95_ms": p95_ms,
        "error_rate": error_rate,
        "breach": breach,
        "p95_budget": p95_budget,
        "err_budget": err_budget
    })
    
    # Keep only last 100 checks
    if len(_SLA_HISTORY) > 100:
        _SLA_HISTORY = _SLA_HISTORY[-100:]
    
    # Update breach counter
    if breach:
        _SLA_BREACH_COUNT += 1
        logger.warning(f"[SLA_BREACH] p95={p95_ms:.1f}ms (budget={p95_budget}ms), "
                      f"error_rate={error_rate:.4f} (budget={err_budget}), "
                      f"streak={_SLA_BREACH_COUNT}/{breach_streak}")
        
        # Check if we should rollback
        if _SLA_BREACH_COUNT >= breach_streak:
            current_policy = _CURRENT_POLICY.get("name", "unknown")
            if current_policy != rollback_target:
                logger.error(f"[AUTO_ROLLBACK] from={current_policy} to={rollback_target} "
                           f"reason=breach_streak={_SLA_BREACH_COUNT}")
                
                # Trigger rollback
                try:
                    params = _get_policy_params(rollback_target)
                    applied_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    _CURRENT_POLICY = {
                        "name": rollback_target,
                        "applied_at": applied_at,
                        "source": "auto_rollback",
                        "params": params,
                        "sha": _CURRENT_POLICY.get("sha")
                    }
                    _SLA_BREACH_COUNT = 0
                    logger.info(f"[AUTO_ROLLBACK] Successfully rolled back to {rollback_target}")
                    return True
                except Exception as e:
                    logger.error(f"[AUTO_ROLLBACK] Failed to rollback: {e}")
            else:
                logger.warning(f"[AUTO_ROLLBACK] Already on rollback target {rollback_target}, resetting counter")
                _SLA_BREACH_COUNT = 0
    else:
        # Reset counter on successful check
        _SLA_BREACH_COUNT = 0
    
    return False

