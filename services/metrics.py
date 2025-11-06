"""
Metrics Router
==============
Read-only endpoints for metrics, Qdrant, and QA feed.

These endpoints proxy or reuse existing logic from app_v2 without modification.
"""

import sys
import time
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

# Add project root to path for core.metrics import
# Use absolute path to ensure correctness
project_root = Path(__file__).parent.parent.parent.resolve()
project_root_str = str(project_root)

# Remove old path if present and insert at front
if project_root_str in sys.path:
    sys.path.remove(project_root_str)
sys.path.insert(0, project_root_str)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ops", tags=["metrics"])


# Import core metrics if available
try:
    from core.metrics import metrics_sink, METRICS_BACKEND
    CORE_AVAILABLE = True
except Exception as e:
    logger.warning(f"[METRICS] core.metrics not available: {e}")
    CORE_AVAILABLE = False
    metrics_sink = None
    METRICS_BACKEND = "unavailable"

# Import settings for recall configuration
try:
    from services.core.settings import RECALL_ENABLED, RECALL_SAMPLE_RATE
except Exception as e:
    logger.warning(f"[METRICS] settings import failed: {e}, using defaults")
    RECALL_ENABLED = False
    RECALL_SAMPLE_RATE = 0.0


@router.get("/summary")
async def ops_summary():
    """
    Unified ops summary: health + window60s + timeline + series60s(meta) + auto status.
    
    This is a read-only proxy that returns system health and metrics.
    Returns timeline array for P95 and Recall@10 charts.
    """
    try:
        now_ms = int(time.time() * 1000)
        result = {
            "ok": True,
            "source": "app_main",
            "backend": METRICS_BACKEND,
            "window_sec": 60,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "degraded": {"redis": False}  # Track degradation state
        }
        
        # 1. Health check (with graceful degradation)
        try:
            if not CORE_AVAILABLE or metrics_sink is None:
                result["health"] = {"ok": False, "error": "core.metrics not available"}
                result["degraded"]["redis"] = True
            else:
                samples = metrics_sink.snapshot_last_60s(now_ms)
                redis_connected = False
                if hasattr(metrics_sink, 'client'):  # RedisMetrics
                    try:
                        metrics_sink.client.ping()
                        redis_connected = True
                    except:
                        result["degraded"]["redis"] = True
                else:
                    result["degraded"]["redis"] = True
                
                result["health"] = {
                    "ok": True,
                    "core_metrics_backend": METRICS_BACKEND,
                    "redis_connected": redis_connected,
                    "rows_60s": len(samples)
                }
        except Exception as e:
            result["health"] = {"ok": False, "error": str(e)}
            result["degraded"]["redis"] = True
        
        # 2. Window60s aggregated metrics
        try:
            if CORE_AVAILABLE and metrics_sink:
                window_data = metrics_sink.window60s(now_ms)
                result["window60s"] = {
                    "p95_ms": window_data.get("p95_ms"),
                    "tps": window_data.get("tps"),
                    "recall_at_10": window_data.get("recall_at_10"),
                    "samples": window_data.get("samples", 0)
                }
            else:
                result["window60s"] = {
                    "p95_ms": None,
                    "tps": 0.0,
                    "recall_at_10": None,
                    "samples": 0
                }
        except Exception as e:
            logger.error(f"[METRICS] window60s error: {e}")
            result["window60s"] = {
                "p95_ms": None,
                "tps": 0.0,
                "recall_at_10": None,
                "samples": 0,
                "error": str(e)
            }
        
        # 3. Timeline - 5s buckets for charts (NEW)
        try:
            timeline = []
            if CORE_AVAILABLE and metrics_sink:
                bucket_ms = 5000  # 5s buckets
                aligned_now_ms = (now_ms // bucket_ms) * bucket_ms
                aligned_cutoff_ms = aligned_now_ms - 60000  # Last 60s
                samples = metrics_sink.snapshot_last_60s(now_ms)
                
                # Group samples by 5s bucket
                buckets = {}
                for s in samples:
                    ts = s.get("ts", 0)
                    if ts >= aligned_cutoff_ms and ts <= aligned_now_ms:
                        bucket_ts = (ts // bucket_ms) * bucket_ms
                        if bucket_ts not in buckets:
                            buckets[bucket_ts] = []
                        buckets[bucket_ts].append(s)
                
                # Compute p95 and recall for each bucket
                for bucket_ts in sorted(buckets.keys()):
                    bucket_samples = buckets[bucket_ts]
                    
                    # Compute P95
                    latencies = [s.get("latency_ms") for s in bucket_samples if s.get("latency_ms") is not None]
                    p95_ms = None
                    if len(latencies) >= 3:
                        sorted_latencies = sorted(latencies)
                        idx = int(len(sorted_latencies) * 0.95)
                        p95_ms = round(sorted_latencies[idx], 2)
                    elif latencies:
                        p95_ms = round(max(latencies), 2)  # Fallback to max if < 3 samples
                    
                    # Compute Recall@10 (only if enabled)
                    recall_at_10 = None
                    if RECALL_ENABLED:
                        recalls = [s.get("recall_at10") for s in bucket_samples if s.get("recall_at10") is not None]
                        if recalls:
                            recall_at_10 = round(sum(recalls) / len(recalls), 4)
                    
                    # Check experiment phase for this bucket
                    experiment_phase = None
                    experiment_valid = True
                    try:
                        from services.routers.quiet_experiment import _experiment, _state_lock
                        import asyncio
                        # Check if this bucket falls within an experiment window
                        if _experiment.running or _experiment.windows:
                            for window in _experiment.windows:
                                # Check if bucket_ts is within this window (±5s tolerance)
                                if abs(window.timestamp - bucket_ts) < 5000:
                                    experiment_phase = window.phase
                                    experiment_valid = window.valid
                                    break
                    except:
                        pass
                    
                    # Add to timeline (ISO timestamp)
                    timeline_item = {
                        "t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(bucket_ts / 1000)),
                        "p95_ms": p95_ms,
                        "recall_at_10": recall_at_10  # Will be None if disabled
                    }
                    
                    # Add experiment metadata if available
                    if experiment_phase:
                        timeline_item["experiment_phase"] = experiment_phase
                        timeline_item["experiment_valid"] = experiment_valid
                    
                    timeline.append(timeline_item)
            
            result["timeline"] = timeline
        except Exception as e:
            logger.error(f"[METRICS] timeline error: {e}")
            result["timeline"] = []
        
        # 4. Series60s metadata (buckets count + non-empty buckets)
        try:
            if CORE_AVAILABLE and metrics_sink:
                bucket_ms = 5000
                aligned_now_ms = (now_ms // bucket_ms) * bucket_ms
                aligned_cutoff_ms = aligned_now_ms - 60000
                samples = metrics_sink.snapshot_last_60s(now_ms)
                
                # Count non-empty buckets
                buckets_set = set()
                for s in samples:
                    ts = s.get("ts", 0)
                    if ts >= (aligned_cutoff_ms - 1000) and ts <= (aligned_now_ms + 1000):
                        bucket_ts = (ts // bucket_ms) * bucket_ms
                        buckets_set.add(bucket_ts)
                
                # Calculate total expected buckets (12 or 13)
                total_buckets = 0
                current_ts = aligned_cutoff_ms
                while current_ts <= aligned_now_ms:
                    total_buckets += 1
                    current_ts += bucket_ms
                
                result["series60s"] = {
                    "buckets": total_buckets,
                    "non_empty": len(buckets_set),
                    "step_sec": 5
                }
            else:
                result["series60s"] = {"ok": False, "error": "core.metrics not available"}
        except Exception as e:
            result["series60s"] = {"ok": False, "error": str(e)}
        
        # 5. Auto status (placeholder for now)
        result["auto"] = {
            "ok": False,
            "error": "AutoTuner not integrated in app_main yet"
        }
        
        # 6. Data sources status (for frontend compatibility)
        redis_status = {"ok": False, "message": "Redis unavailable"}
        try:
            if CORE_AVAILABLE and metrics_sink and hasattr(metrics_sink, 'client'):
                metrics_sink.client.ping()
                redis_status = {
                    "ok": True,
                    "backend": "redis",
                    "connected": True
                }
        except Exception as e:
            redis_status = {
                "ok": False,
                "error": "redis_unreachable",
                "message": "Core metrics module not available - using memory mode"
            }
        
        qdrant_status = {"ok": False, "message": "Qdrant status unknown"}
        try:
            from qdrant_client import QdrantClient
            import os
            qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
            qdrant_port = int(os.environ.get("QDRANT_PORT", "6333"))
            client = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=1)
            collections = client.get_collections()
            qdrant_status = {
                "ok": True,
                "host": qdrant_host,
                "port": qdrant_port,
                "collections": len(collections.collections)
            }
        except Exception as e:
            qdrant_status = {
                "ok": False,
                "error": "qdrant_unreachable",
                "message": str(e)[:100]
            }
        
        result["data_sources"] = {
            "redis": redis_status,
            "qdrant": qdrant_status
        }
        
        return result
        
    except Exception as e:
        # Never return 5xx - always return 200 with ok:false
        logger.error(f"[METRICS] ops_summary error: {e}")
        return {
            "ok": False,
            "error": "internal_error",
            "message": str(e),
            "source": "app_main",
            "backend": METRICS_BACKEND,
            "window_sec": 60,
            "timeline": [],  # Empty timeline on error
            "degraded": {"redis": True},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }


@router.get("/qdrant/ping")
async def qdrant_ping():
    """Check if Qdrant is reachable and return collection info."""
    try:
        from qdrant_client import QdrantClient
        import os
        
        qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
        qdrant_port = int(os.environ.get("QDRANT_PORT", "6333"))
        
        start_ms = time.time() * 1000
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        
        # Get collections
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        latency_ms = time.time() * 1000 - start_ms
        
        logger.info(
            f"[QDRANT] Ping successful: {qdrant_host}:{qdrant_port} "
            f"({latency_ms:.2f}ms) - collections: {collection_names}"
        )
        
        return {
            "ok": True,
            "host": qdrant_host,
            "port": qdrant_port,
            "latency_ms": round(latency_ms, 2),
            "collections": collection_names,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    except Exception as e:
        # Never return 5xx - always return 200 with ok:false
        logger.error(f"[QDRANT] Ping failed: {e}")
        return {
            "ok": False,
            "error": "qdrant_unreachable",
            "message": f"Qdrant connection failed: {str(e)}",
            "host": os.environ.get("QDRANT_HOST", "localhost"),
            "port": int(os.environ.get("QDRANT_PORT", "6333")),
            "latency_ms": None,
            "collections": [],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }


@router.get("/qdrant/config")
async def qdrant_config():
    """Get Qdrant configuration (concurrency, batch_size, override state)."""
    import os
    
    try:
        # Read override settings from environment
        override = os.environ.get("BS_QDRANT_OVERRIDE", "0").lower() in ("1", "true")
        max_concurrency = int(os.environ.get("BS_QDRANT_MAX_CONCURRENCY", "32"))
        batch_size = int(os.environ.get("BS_QDRANT_BATCH_SIZE", "1"))
        
        # Defaults (when override is off)
        default_concurrency = 32
        default_batch_size = 1
        
        # Effective values
        effective_concurrency = max_concurrency if override else default_concurrency
        effective_batch_size = batch_size if override else default_batch_size
        source = "override" if override else "default"
        
        return {
            "ok": True,
            "override": override,
            "concurrency": effective_concurrency,
            "batch_size": effective_batch_size,
            "source": source,
            "defaults": {
                "concurrency": default_concurrency,
                "batch_size": default_batch_size
            }
        }
    except Exception as e:
        # Never 5xx - return safe defaults
        return {
            "ok": True,
            "override": False,
            "concurrency": 32,
            "batch_size": 1,
            "source": "default",
            "defaults": {
                "concurrency": 32,
                "batch_size": 1
            },
            "error": str(e)
        }


@router.get("/qdrant/stats")
async def qdrant_stats():
    """
    Get Qdrant hit statistics from Redis (direct connection with graceful degradation).
    
    Reads from Redis key 'qa:qdrant:stats:60s' or returns empty stats if unavailable.
    No proxy to app_v2 - always returns 200 with ok:true/false.
    """
    import os
    
    try:
        # Try to get stats from Redis
        if CORE_AVAILABLE and metrics_sink and hasattr(metrics_sink, 'client'):
            try:
                redis_client = metrics_sink.client
                redis_client.ping()  # Check connection
                
                # Try to read stats from Redis hash
                stats_key = "qa:qdrant:stats:60s"
                stats_data = redis_client.hgetall(stats_key)
                
                if stats_data:
                    # Parse Redis hash data
                    return {
                        "ok": True,
                        "hits_60s": int(stats_data.get(b"hits_60s", b"0")),
                        "avg_query_ms_60s": float(stats_data.get(b"avg_query_ms_60s", b"0")) if stats_data.get(b"avg_query_ms_60s") else None,
                        "p95_query_ms_60s": float(stats_data.get(b"p95_query_ms_60s", b"0")) if stats_data.get(b"p95_query_ms_60s") else None,
                        "remote_pct_60s": float(stats_data.get(b"remote_pct_60s", b"0")),
                        "cache_pct_60s": float(stats_data.get(b"cache_pct_60s", b"0")),
                        "window_sec": 60
                    }
                else:
                    # Key doesn't exist - graceful degradation
                    return {
                        "ok": False,
                        "error": "no_data",
                        "message": "Qdrant stats not available in Redis",
                        "hits_60s": 0,
                        "avg_query_ms_60s": None,
                        "p95_query_ms_60s": None,
                        "remote_pct_60s": 0,
                        "cache_pct_60s": 0,
                        "window_sec": 60
                    }
            except Exception as redis_err:
                # Redis connection failed
                logger.warning(f"[METRICS] Redis error in qdrant_stats: {redis_err}")
                return {
                    "ok": False,
                    "error": "redis_unreachable",
                    "message": f"Cannot connect to Redis: {str(redis_err)}",
                    "hits_60s": 0,
                    "avg_query_ms_60s": None,
                    "p95_query_ms_60s": None,
                    "remote_pct_60s": 0,
                    "cache_pct_60s": 0,
                    "window_sec": 60
                }
        else:
            # Core metrics not available
            return {
                "ok": False,
                "error": "redis_unreachable",
                "message": "Core metrics backend not available",
                "hits_60s": 0,
                "avg_query_ms_60s": None,
                "p95_query_ms_60s": None,
                "remote_pct_60s": 0,
                "cache_pct_60s": 0,
                "window_sec": 60
            }
    except Exception as e:
        # Catch-all error handler
        logger.error(f"[METRICS] Unexpected error in qdrant_stats: {e}")
        return {
            "ok": False,
            "error": "internal_error",
            "message": str(e),
            "hits_60s": 0,
            "avg_query_ms_60s": None,
            "p95_query_ms_60s": None,
            "remote_pct_60s": 0,
            "cache_pct_60s": 0,
            "window_sec": 60
        }


@router.get("/qa/feed")
async def qa_feed(limit: int = Query(default=20, le=50)):
    """
    Get recent QA events from Black Swan storage (Redis or memory fallback).
    
    Reads from Black Swan storage which automatically handles Redis/memory fallback.
    Always returns 200 with ok:true/false.
    """
    try:
        # Use Black Swan storage (with automatic Redis/memory fallback)
        from services.black_swan.storage import get_storage
        
        storage = get_storage()
        items = storage.get_qa_feed(limit=limit)
        
        if items:
            return {
                "ok": True,
                "items": items,
                "circuit_open": False,
                "sample_rate": 0.05,  # 5% sampling
                "sample_rate_effective": 0.05,
                "source": "redis" if storage.is_available() else "memory"
            }
        else:
            # Feed empty - this is OK, just no data yet
            return {
                "ok": True,  # Changed from False - empty feed is valid state
                "error": "no_data",
                "message": "No QA events yet — run Black Swan to generate traffic",
                "items": [],
                "circuit_open": False,
                "sample_rate": 0.05,
                "sample_rate_effective": 0.05,
                "source": "redis" if storage.is_available() else "memory"
            }
    except Exception as e:
        # Catch-all error handler
        logger.error(f"[METRICS] Unexpected error in qa_feed: {e}")
        return {
            "ok": True,  # Still return ok:true to not break UI
            "error": "internal_error",
            "message": str(e),
            "items": [],
            "circuit_open": False,
            "sample_rate": 0,
            "sample_rate_effective": 0,
            "source": "error"
        }


@router.get("/query_bank/status")
async def query_bank_status():
    """
    Get query bank loading status from environment configuration.
    
    Reads configuration from environment variables - no external dependencies.
    Always returns 200 with ok:true.
    """
    import os
    from pathlib import Path
    
    try:
        # Read from environment (mimics settings.py in app_v2)
        use_real_queries = os.getenv("USE_REAL_QUERIES", "false").lower() == "true"
        query_bank_path = os.getenv("FIQA_QUERY_BANK", "data/fiqa_query_bank.txt")
        bs_unique_queries = os.getenv("BS_UNIQUE_QUERIES", "true").lower() == "true"
        bs_bypass_cache = os.getenv("BS_BYPASS_CACHE", "true").lower() == "true"
        
        # Try to count queries if file exists
        queries_loaded = 0
        sample_queries = []
        
        if use_real_queries:
            try:
                project_root = Path(__file__).parent.parent.parent
                query_file = project_root / query_bank_path
                
                if query_file.exists():
                    with open(query_file, 'r', encoding='utf-8') as f:
                        queries = [line.strip() for line in f if line.strip()]
                        queries_loaded = len(queries)
                        sample_queries = queries[:3]
            except Exception as file_err:
                logger.warning(f"[METRICS] Could not read query bank file: {file_err}")
        
        return {
            "ok": True,
            "use_real_queries": use_real_queries,
            "query_bank_path": query_bank_path,
            "queries_loaded": queries_loaded,
            "bs_unique_queries": bs_unique_queries,
            "bs_bypass_cache": bs_bypass_cache,
            "sample_queries": sample_queries
        }
    except Exception as e:
        # Even on error, return ok:true with safe defaults
        logger.error(f"[METRICS] Error in query_bank_status: {e}")
        return {
            "ok": True,
            "error": str(e),
            "use_real_queries": False,
            "query_bank_path": "",
            "queries_loaded": 0,
            "bs_unique_queries": False,
            "bs_bypass_cache": False,
            "sample_queries": []
        }


@router.get("/black_swan/status")
async def black_swan_status():
    """
    Get Black Swan test status from Redis (direct connection with graceful degradation).
    
    Reads from Redis hash 'bs:run:status' or returns idle state if unavailable.
    No proxy to app_v2 - always returns 200 with proper structure.
    """
    try:
        # Try to get status from Redis
        if CORE_AVAILABLE and metrics_sink and hasattr(metrics_sink, 'client'):
            try:
                redis_client = metrics_sink.client
                redis_client.ping()  # Check connection
                
                # Try to read status from Redis hash
                status_key = "bs:run:status"
                status_data = redis_client.hgetall(status_key)
                
                if status_data:
                    # Parse Redis hash data
                    return {
                        "phase": status_data.get(b"phase", b"idle").decode('utf-8'),
                        "progress": int(status_data.get(b"progress", b"0")),
                        "run_id": status_data.get(b"run_id", b"").decode('utf-8') or None,
                        "message": status_data.get(b"message", b"").decode('utf-8'),
                        "running": status_data.get(b"running", b"false").decode('utf-8').lower() == "true",
                        "started_at": int(status_data.get(b"started_at", b"0")) if status_data.get(b"started_at") else None,
                        "ended_at": int(status_data.get(b"ended_at", b"0")) if status_data.get(b"ended_at") else None,
                        "mode": status_data.get(b"mode", b"").decode('utf-8') or None
                    }
                else:
                    # No active run - return idle state
                    return {
                        "phase": "idle",
                        "progress": 0,
                        "run_id": None,
                        "message": "No Black Swan test running",
                        "running": False
                    }
            except Exception as redis_err:
                # Redis connection failed
                logger.warning(f"[METRICS] Redis error in black_swan_status: {redis_err}")
                return {
                    "phase": "idle",
                    "progress": 0,
                    "run_id": None,
                    "message": f"Redis unavailable: {str(redis_err)}",
                    "running": False,
                    "error": {
                        "code": "redis_unreachable",
                        "message": str(redis_err)
                    }
                }
        else:
            # Core metrics not available
            return {
                "phase": "idle",
                "progress": 0,
                "run_id": None,
                "message": "Core metrics backend not available",
                "running": False,
                "error": {
                    "code": "redis_unreachable",
                    "message": "Core metrics not initialized"
                }
            }
    except Exception as e:
        # Catch-all error handler
        logger.error(f"[METRICS] Unexpected error in black_swan_status: {e}")
        return {
            "phase": "idle",
            "progress": 0,
            "run_id": None,
            "message": f"Error: {str(e)}",
            "running": False,
            "error": {
                "code": "internal_error",
                "message": str(e)
            }
        }


@router.get("/black_swan/config")
async def black_swan_config():
    """
    Get Black Swan configuration from environment variables.
    
    Reads configuration from .env - no external dependencies.
    Always returns 200 with ok:true.
    """
    import os
    
    try:
        return {
            "ok": True,
            "use_real": os.getenv("BLACK_SWAN_USE_REAL", "true").lower() == "true",
            "nocache": os.getenv("BLACK_SWAN_NOCACHE", "true").lower() == "true",
            "fiqa_search_url": os.getenv("FIQA_SEARCH_URL", "http://localhost:8011/search"),
            "qdrant_collection": os.getenv("QDRANT_COLLECTION", "beir_fiqa_full_ta"),
            "heavy_topk": int(os.getenv("HEAVY_TOPK", "100")),
            "rerank_topk": int(os.getenv("RERANK_TOPK", "200")),
            "mode_c_delay_ms": int(os.getenv("MODE_C_DELAY_MS", "250")),
            "demo_tuner_pause": os.getenv("DEMO_TUNER_PAUSE", "true").lower() == "true",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    except Exception as e:
        # Even on error, return ok:true with safe defaults
        logger.error(f"[METRICS] Error in black_swan_config: {e}")
        return {
            "ok": True,
            "error": str(e),
            "use_real": True,
            "nocache": True,
            "fiqa_search_url": "http://localhost:8011/search",
            "qdrant_collection": "beir_fiqa_full_ta",
            "heavy_topk": 100,
            "rerank_topk": 200,
            "mode_c_delay_ms": 250,
            "demo_tuner_pause": True
        }

