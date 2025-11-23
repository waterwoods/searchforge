"""
kv_experiment_service.py - KV/Streaming Experiment Service

Core experiment logic for running KV-cache and streaming performance comparisons.
This module provides reusable functions that can be used by both CLI scripts and HTTP API endpoints.
"""

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Mode configurations
MODES = {
    "baseline": dict(use_kv_cache=False, stream=False),
    "kv_only": dict(use_kv_cache=True, stream=False),
    "stream_only": dict(use_kv_cache=False, stream=True),
    "kv_and_stream": dict(use_kv_cache=True, stream=True),
}


@dataclass
class KvExperimentSample:
    """Single experiment sample data."""
    mode: str
    latency_ms: float
    first_token_ms: float
    total_tokens: int
    cost_usd_est: float
    kv_enabled: bool
    kv_hit: bool
    stream_enabled: bool
    error: Optional[str] = None


def _percentile(values: List[float], q: float) -> float:
    """Calculate nearest-rank percentile with simple guards."""
    if not values:
        return 0.0
    q = max(0.0, min(1.0, float(q)))
    vals = sorted(float(v) for v in values)
    if q <= 0.0:
        return vals[0]
    if q >= 1.0:
        return vals[-1]
    idx = int((len(vals) * q + 0.999999)) - 1
    idx = max(0, min(idx, len(vals) - 1))
    return vals[idx]


async def _call_query_internal(
    question: str,
    collection: str,
    profile_name: Optional[str],
    filters: Optional[Dict[str, Any]],
    use_kv_cache: bool,
    session_id: Optional[str],
    stream: bool,
) -> Tuple[Optional[Dict[str, Any]], KvExperimentSample]:
    """
    Internal function to execute query by calling core search and LLM logic directly.
    
    This function bypasses HTTP layer and directly calls the core search and LLM functions.
    This approach is cleaner and doesn't require mocking Request/Response objects.
    
    Args:
        question: User's question
        collection: Collection name
        profile_name: Optional profile name
        filters: Optional filter dict (price_max, min_bedrooms, neighbourhood, room_type)
        use_kv_cache: Whether to use KV-cache
        session_id: Session ID for KV-cache
        stream: Whether to stream response (currently not fully supported, will use non-streaming)
    
    Returns:
        Tuple of (response_dict_or_none, KvExperimentSample)
    """
    import asyncio
    from services.fiqa_api.services.search_core import perform_search
    from services.fiqa_api.services.search_profiles import get_search_profile
    from services.fiqa_api.utils.llm_client import generate_answer_for_query, is_llm_generation_enabled
    from services.fiqa_api.clients import get_openai_client
    from services.fiqa_api.app_main import app
    
    start_time = time.perf_counter()
    first_token_time: Optional[float] = None
    error: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    
    try:
        # Check LLM generation is enabled
        if not is_llm_generation_enabled():
            raise ValueError("LLM generation is disabled (LLM_GENERATION_ENABLED=false)")
        
        # Get app state
        try:
            routing_flags = app.state.routing_flags
            faiss_engine = app.state.faiss_engine
            faiss_ready = app.state.faiss_ready
            faiss_enabled = app.state.faiss_enabled
        except Exception:
            routing_flags = {"enabled": True, "mode": "rules"}
            faiss_engine = None
            faiss_ready = False
            faiss_enabled = False
        
        # Get search profile
        profile = get_search_profile(profile_name)
        
        # Build effective parameters (similar to query.py)
        effective_params = {}
        effective_params["collection"] = collection or (profile.collection if profile else None) or "fiqa"
        profile_filters = profile.default_filters if profile else {}
        effective_params["price_max"] = filters.get("price_max") if filters else profile_filters.get("price_max")
        effective_params["min_bedrooms"] = filters.get("min_bedrooms") if filters else profile_filters.get("min_bedrooms")
        effective_params["neighbourhood"] = filters.get("neighbourhood") if filters else profile_filters.get("neighbourhood")
        effective_params["room_type"] = filters.get("room_type") if filters else profile_filters.get("room_type")
        
        collection_name = effective_params["collection"]
        
        # Perform search
        search_result = await asyncio.to_thread(
            perform_search,
            query=question,
            top_k=10,
            collection=collection_name,
            routing_flags=routing_flags,
            faiss_engine=faiss_engine,
            faiss_ready=faiss_ready,
            faiss_enabled=faiss_enabled,
            lab_headers=None,
            use_hybrid=False,
            rrf_k=60,
            rerank=False,
            rerank_top_k=20,
            rerank_if_margin_below=None,
            max_rerank_trigger_rate=0.25,
            rerank_budget_ms=25,
            obs_ctx={"trace_id": str(uuid.uuid4()), "job_id": str(uuid.uuid4())},
            price_max=effective_params.get("price_max"),
            min_bedrooms=effective_params.get("min_bedrooms"),
            neighbourhood=effective_params.get("neighbourhood"),
            room_type=effective_params.get("room_type"),
            profile_name=profile_name,
        )
        
        # Extract sources
        sources = []
        for result in search_result.get("results", []):
            source = {
                "doc_id": result.get("id", "unknown"),
                "title": result.get("title", ""),
                "text": result.get("text", ""),
                "score": result.get("score", 0.0)
            }
            # Add Airbnb fields if present
            if collection_name == "airbnb_la_demo":
                if "price" in result:
                    source["price"] = result.get("price")
                if "bedrooms" in result:
                    source["bedrooms"] = result.get("bedrooms")
                if "neighbourhood" in result:
                    source["neighbourhood"] = result.get("neighbourhood")
                if "room_type" in result:
                    source["room_type"] = result.get("room_type")
            sources.append(source)
        
        # Generate answer using LLM
        answer = ""
        llm_usage = None
        kv_enabled = use_kv_cache
        kv_hit = False
        first_token_latency_ms: Optional[float] = None
        
        if sources:
            try:
                # Build context from sources
                context = []
                for source in sources[:10]:
                    context_item = {
                        "title": source.get("title", source.get("doc_id", "")),
                        "text": source.get("text", source.get("content", "")),
                    }
                    # Include Airbnb fields if present
                    if collection_name == "airbnb_la_demo":
                        if "price" in source:
                            context_item["price"] = source.get("price")
                        if "bedrooms" in source:
                            context_item["bedrooms"] = source.get("bedrooms")
                        if "neighbourhood" in source:
                            context_item["neighbourhood"] = source.get("neighbourhood")
                        if "room_type" in source:
                            context_item["room_type"] = source.get("room_type")
                    context.append(context_item)
                
                # Generate answer (streaming or non-streaming based on stream parameter)
                if stream:
                    from services.fiqa_api.utils.llm_client import stream_answer_for_query
                    # Use streaming version
                    answer, llm_usage, kv_enabled, kv_hit, first_token_latency_ms = await stream_answer_for_query(
                        question=question,
                        context=context,
                        use_kv_cache=use_kv_cache,
                        session_id=session_id,
                    )
                else:
                    # Use non-streaming version
                    answer, llm_usage, kv_enabled, kv_hit = generate_answer_for_query(
                        question=question,
                        context=context,
                        use_kv_cache=use_kv_cache,
                        session_id=session_id,
                    )
                    # For non-streaming, first token latency equals total latency
                    first_token_latency_ms = None  # Will be set to total latency below
            except Exception as e:
                logger.warning(f"LLM generation failed: {e}", exc_info=True)
                kv_enabled = use_kv_cache
                kv_hit = False
        
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Set first_token_ms: use measured value for streaming, or total latency for non-streaming
        if first_token_latency_ms is not None:
            first_token_ms = first_token_latency_ms
        else:
            # For non-streaming, first token arrives at the same time as the complete response
            first_token_ms = latency_ms
        
        # Build response data
        response_data = {
            "ok": True,
            "question": question,
            "answer": answer,
            "sources": sources,
            "metrics": {
                "llm_usage": llm_usage,
                "llm_enabled": llm_usage is not None,
                "kv_enabled": kv_enabled,
                "kv_hit": kv_hit,
            } if llm_usage else {
                "llm_enabled": False,
                "kv_enabled": False,
                "kv_hit": False,
            },
        }
        
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        error = str(e)
        logger.warning(f"Query call failed: {e}", exc_info=True)
    
    # Extract metrics from response
    total_tokens = 0
    cost_usd_est = 0.0
    kv_enabled_actual = use_kv_cache
    kv_hit = False
    
    if response_data:
        metrics_data = response_data.get("metrics", {})
        llm_usage = metrics_data.get("llm_usage", {})
        
        total_tokens = llm_usage.get("total_tokens", 0) if llm_usage else 0
        cost_usd_est = llm_usage.get("cost_usd_est", 0.0) if llm_usage else 0.0
        if cost_usd_est is None:
            cost_usd_est = 0.0
        
        kv_enabled_actual = metrics_data.get("kv_enabled", use_kv_cache)
        kv_hit = metrics_data.get("kv_hit", False)
    
    # Ensure stream_enabled matches the actual stream parameter (not the modified value)
    # This ensures that even if streaming fails and falls back, we record the intended mode
    stream_enabled_actual = stream  # Use the original stream parameter
    
    sample = KvExperimentSample(
        mode="",  # Will be set by caller
        latency_ms=latency_ms,
        first_token_ms=first_token_ms,
        total_tokens=total_tokens,
        cost_usd_est=cost_usd_est,
        kv_enabled=kv_enabled_actual,
        kv_hit=kv_hit,
        stream_enabled=stream_enabled_actual,  # Use actual stream parameter
        error=error,
    )
    
    return response_data, sample


async def run_single_query_mode(
    mode: str,
    question: str,
    collection: str,
    profile_name: Optional[str],
    filters: Optional[Dict[str, Any]],
    session_id: Optional[str] = None,
) -> KvExperimentSample:
    """
    Run a single query in a specific mode.
    
    Args:
        mode: One of "baseline", "kv_only", "stream_only", "kv_and_stream"
        question: User's question
        collection: Collection name
        profile_name: Optional profile name
        filters: Optional filter dict
        session_id: Optional session ID (for KV-cache modes, should be fixed across runs)
    
    Returns:
        KvExperimentSample with metrics
    """
    if mode not in MODES:
        raise ValueError(f"Invalid mode: {mode}. Must be one of {list(MODES.keys())}")
    
    config = MODES[mode]
    use_kv_cache = config["use_kv_cache"]
    stream = config["stream"]
    
    # For KV modes, generate a fixed session_id if not provided
    if use_kv_cache and not session_id:
        session_id = f"kv-lab-{mode}-{uuid.uuid4().hex[:8]}"
    
    _, sample = await _call_query_internal(
        question=question,
        collection=collection,
        profile_name=profile_name,
        filters=filters,
        use_kv_cache=use_kv_cache,
        session_id=session_id,
        stream=stream,
    )
    
    sample.mode = mode
    return sample


def _aggregate_mode_metrics(samples: List[KvExperimentSample]) -> Dict[str, Any]:
    """
    Aggregate metrics for a single mode from multiple samples.
    
    Args:
        samples: List of KvExperimentSample for the same mode
    
    Returns:
        Dict with aggregated metrics
    """
    if not samples:
        return {
            "num_runs": 0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "p50_first_token_ms": 0.0,
            "p95_first_token_ms": 0.0,
            "avg_total_tokens": 0.0,
            "avg_cost_usd": 0.0,
            "stream_enabled": False,
            "kv_enabled": False,
            "kv_hit_rate": 0.0,
            "stream_error_rate": 0.0,
        }
    
    # Filter out error samples for latency calculations
    valid_samples = [s for s in samples if s.error is None]
    
    latencies = [s.latency_ms for s in valid_samples] if valid_samples else [0.0]
    first_token_times = [s.first_token_ms for s in valid_samples] if valid_samples else [0.0]
    total_tokens = [s.total_tokens for s in valid_samples] if valid_samples else [0]
    costs = [s.cost_usd_est for s in valid_samples] if valid_samples else [0.0]
    
    # Calculate stream error rate
    stream_requests = [s for s in samples if s.stream_enabled]
    stream_errors = sum(1 for s in stream_requests if s.error is not None)
    stream_error_rate = (stream_errors / len(stream_requests)) if stream_requests else 0.0
    
    # Calculate KV hit rate
    kv_enabled_requests = [s for s in samples if s.kv_enabled]
    kv_hits = sum(1 for s in kv_enabled_requests if s.kv_hit)
    kv_hit_rate = (kv_hits / len(kv_enabled_requests)) if kv_enabled_requests else 0.0
    
    # Get mode flags from first sample
    first_sample = samples[0]
    stream_enabled = first_sample.stream_enabled
    kv_enabled = first_sample.kv_enabled
    
    return {
        "num_runs": len(samples),
        "p50_ms": _percentile(latencies, 0.5),
        "p95_ms": _percentile(latencies, 0.95),
        "p50_first_token_ms": _percentile(first_token_times, 0.5),
        "p95_first_token_ms": _percentile(first_token_times, 0.95),
        "avg_total_tokens": sum(total_tokens) / len(total_tokens) if total_tokens else 0.0,
        "avg_cost_usd": sum(costs) / len(costs) if costs else 0.0,
        "stream_enabled": stream_enabled,
        "kv_enabled": kv_enabled,
        "kv_hit_rate": kv_hit_rate,
        "stream_error_rate": stream_error_rate,
    }


async def run_kv_experiment_for_all_modes(
    question: str,
    collection: str = "airbnb_la_demo",
    profile_name: Optional[str] = "airbnb_la_location_first",
    runs_per_mode: int = 3,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run KV/Streaming experiment for all 4 modes.
    
    Args:
        question: User's question
        collection: Collection name (default: "airbnb_la_demo")
        profile_name: Profile name (default: "airbnb_la_location_first")
        runs_per_mode: Number of runs per mode (default: 3, max: 10)
        filters: Optional filter dict (price_max, min_bedrooms, neighbourhood, room_type)
    
    Returns:
        Dict with experiment results:
        {
            "ok": bool,
            "question": str,
            "collection": str,
            "profile_name": str,
            "modes": {
                "baseline": {...},
                "kv_only": {...},
                "stream_only": {...},
                "kv_and_stream": {...},
            },
            "raw_samples": List[Dict] (optional, limited to first 3 per mode)
        }
    """
    # Check LLM generation is enabled
    from services.fiqa_api.utils.llm_client import is_llm_generation_enabled
    if not is_llm_generation_enabled():
        return {
            "ok": False,
            "error": "LLM generation is disabled (LLM_GENERATION_ENABLED=false). Please enable LLM generation to run experiments.",
            "question": question,
            "collection": collection,
            "profile_name": profile_name,
            "modes": {},
            "raw_samples": [],
        }
    
    # Limit runs_per_mode
    runs_per_mode = min(max(1, runs_per_mode), 10)
    
    all_samples: Dict[str, List[KvExperimentSample]] = {
        "baseline": [],
        "kv_only": [],
        "stream_only": [],
        "kv_and_stream": [],
    }
    
    # Generate fixed session IDs for KV modes (to allow cache hits on subsequent runs)
    kv_session_ids = {
        "kv_only": f"kv-lab-kv_only-{uuid.uuid4().hex[:8]}",
        "kv_and_stream": f"kv-lab-kv_and_stream-{uuid.uuid4().hex[:8]}",
    }
    
    # Run experiments for each mode
    for mode in MODES.keys():
        logger.info(f"[KV_EXPERIMENT] Running {runs_per_mode} runs for mode: {mode}")
        
        session_id = kv_session_ids.get(mode)  # Only KV modes get a session_id
        
        for run_idx in range(runs_per_mode):
            try:
                sample = await run_single_query_mode(
                    mode=mode,
                    question=question,
                    collection=collection,
                    profile_name=profile_name,
                    filters=filters,
                    session_id=session_id,  # Reuse same session_id for KV modes
                )
                all_samples[mode].append(sample)
                
                if sample.error:
                    logger.warning(f"[KV_EXPERIMENT] Mode {mode} run {run_idx+1} failed: {sample.error}")
                else:
                    logger.info(
                        f"[KV_EXPERIMENT] Mode {mode} run {run_idx+1}: "
                        f"stream={sample.stream_enabled} kv={sample.kv_enabled} "
                        f"total_ms={sample.latency_ms:.1f} first_token_ms={sample.first_token_ms:.1f} "
                        f"tokens={sample.total_tokens} cost=${sample.cost_usd_est:.6f} "
                        f"kv_hit={sample.kv_hit}"
                    )
            except Exception as e:
                logger.error(f"[KV_EXPERIMENT] Mode {mode} run {run_idx+1} exception: {e}", exc_info=True)
                # Create error sample
                error_sample = KvExperimentSample(
                    mode=mode,
                    latency_ms=0.0,
                    first_token_ms=0.0,
                    total_tokens=0,
                    cost_usd_est=0.0,
                    kv_enabled=MODES[mode]["use_kv_cache"],
                    kv_hit=False,
                    stream_enabled=MODES[mode]["stream"],
                    error=str(e),
                )
                all_samples[mode].append(error_sample)
    
    # Aggregate metrics for each mode
    modes_metrics = {}
    for mode, samples in all_samples.items():
        modes_metrics[mode] = _aggregate_mode_metrics(samples)
    
    # Prepare raw samples (limit to first 3 per mode)
    raw_samples = []
    for mode, samples in all_samples.items():
        for sample in samples[:3]:  # Limit to first 3
            raw_samples.append({
                "mode": sample.mode,
                "latency_ms": sample.latency_ms,
                "first_token_ms": sample.first_token_ms,
                "total_tokens": sample.total_tokens,
                "cost_usd_est": sample.cost_usd_est,
                "kv_enabled": sample.kv_enabled,
                "kv_hit": sample.kv_hit,
                "stream_enabled": sample.stream_enabled,
                "error": sample.error,
            })
    
    return {
        "ok": True,
        "question": question,
        "collection": collection,
        "profile_name": profile_name,
        "modes": modes_metrics,
        "raw_samples": raw_samples,
    }

