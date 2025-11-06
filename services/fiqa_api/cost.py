"""
cost.py - Cost Estimation
===========================
V11: Cost estimation utilities for experiments.
"""

from typing import Dict, Any


# Price table (per 1k tokens/requests)
PRICE_TABLE = {
    "embed_per_1k": 0.0001,  # $0.0001 per 1k embedding requests
    "rerank_per_1k": 0.002,  # $0.002 per 1k rerank requests
    "gen_per_1k": 0.002,  # $0.002 per 1k generated tokens (input+output)
}


def estimate_cost(metrics: Dict[str, Any], config: Dict[str, Any]) -> float:
    """
    Estimate cost per query based on metrics and config.
    
    Args:
        metrics: Metrics dict with request counts, token counts, etc.
        config: Config dict with experiment parameters
        
    Returns:
        Estimated cost per query in USD
    """
    if not metrics or not config:
        return 0.0
    
    # Extract counts from metrics
    total_queries = metrics.get("total_queries", 0) or metrics.get("queries", 0) or 1
    embed_requests = metrics.get("embed_requests", 0) or metrics.get("embed_calls", 0) or total_queries
    rerank_requests = metrics.get("rerank_requests", 0) or metrics.get("rerank_calls", 0) or 0
    tokens_in = metrics.get("tokens_in", 0) or metrics.get("total_tokens_in", 0) or 0
    tokens_out = metrics.get("tokens_out", 0) or metrics.get("total_tokens_out", 0) or 0
    total_tokens = tokens_in + tokens_out
    
    # Calculate costs
    embed_cost = (embed_requests / 1000.0) * PRICE_TABLE["embed_per_1k"]
    rerank_cost = (rerank_requests / 1000.0) * PRICE_TABLE["rerank_per_1k"]
    gen_cost = (total_tokens / 1000.0) * PRICE_TABLE["gen_per_1k"]
    
    total_cost = embed_cost + rerank_cost + gen_cost
    
    # Return cost per query
    if total_queries > 0:
        return total_cost / total_queries
    return total_cost

