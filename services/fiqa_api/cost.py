"""
cost.py - Cost Estimation
===========================
V11: Cost estimation utilities for experiments.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional


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


def load_pricing(model: Optional[str] = None) -> Tuple[float, float, bool, Optional[str]]:
    """
    Unified pricing parser that loads MODEL_PRICING_JSON from environment or .env.current.
    
    Supports two formats:
    - Format A: {"model_name": {"prompt": <price>, "completion": <price>}}
    - Format B: {"model_name": {"in": <price>, "out": <price>}}
    
    If only in/out is provided, maps to prompt/completion.
    Missing fields default to 0.0.
    
    Args:
        model: Model name to lookup. If None, uses first model in pricing JSON.
        
    Returns:
        Tuple of (prompt_price, completion_price, cost_enabled, matched_key)
        - prompt_price: Price per 1k input tokens
        - completion_price: Price per 1k output tokens
        - cost_enabled: True if at least one price > 0
        - matched_key: Model key that matched, or None
    """
    # Try to get from environment
    raw = os.getenv("MODEL_PRICING_JSON", "")
    
    # Fallback to .env.current file
    if not raw:
        env_path = Path(".env.current")
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("MODEL_PRICING_JSON="):
                    raw = line.split("=", 1)[1].strip()
                    break
    
    if not raw:
        return 0.0, 0.0, False, None
    
    # Strip quotes if present
    raw = raw.strip()
    if raw and raw[0] in {"'", '"'} and raw[-1] == raw[0]:
        raw = raw[1:-1]
    
    # Parse JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return 0.0, 0.0, False, None
    
    # If model is not specified, try to get first entry
    if model is None:
        if isinstance(data, dict) and data:
            # Use first key
            model = next(iter(data.keys()))
        elif isinstance(data, list) and data:
            # Use first item's model field
            first_item = data[0]
            if isinstance(first_item, dict):
                model = first_item.get("model")
    
    if not model:
        return 0.0, 0.0, False, None
    
    # Try to find matching entry
    candidates = [
        model,
        model.lower(),
        model.replace(":", "-"),
        model.replace(":", ""),
    ]
    
    entry: Any = None
    matched_key: Optional[str] = None
    
    if isinstance(data, dict):
        for key in candidates:
            if key in data:
                entry = data[key]
                matched_key = key
                break
    
    if entry is None and isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("model") in candidates:
                entry = item
                matched_key = item.get("model")
                break
    
    if entry is None:
        return 0.0, 0.0, False, None
    
    # Extract prices from entry
    def _extract_price(value: Any) -> Optional[float]:
        """Extract numeric price from various formats."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        if isinstance(value, dict):
            for nested_key in (
                "usd_per_1k",
                "price",
                "value",
                "usd",
                "price_per_1k",
                "usd_per_thousand",
            ):
                if nested_key in value:
                    nested_value = _extract_price(value[nested_key])
                    if nested_value is not None:
                        return nested_value
        return None
    
    def _lookup(entry_dict: Dict[str, Any], keys: tuple) -> float:
        """Lookup price by trying multiple key names."""
        for key in keys:
            if key in entry_dict:
                result = _extract_price(entry_dict[key])
                if result is not None:
                    return result
        # Try case-insensitive match
        for key, value in entry_dict.items():
            if key.lower() in [k.lower() for k in keys] and isinstance(value, (int, float, str, dict)):
                result = _extract_price(value)
                if result is not None:
                    return result
        return 0.0
    
    if not isinstance(entry, dict):
        return 0.0, 0.0, False, matched_key
    
    # Try prompt/completion first (Format A)
    prompt_price = _lookup(
        entry,
        ("prompt", "prompt_in", "usd_in", "usd_input", "input")
    )
    completion_price = _lookup(
        entry,
        ("completion", "usd_out", "usd_output", "output")
    )
    
    # If not found, try in/out (Format B) and map to prompt/completion
    if prompt_price == 0.0:
        prompt_price = _lookup(entry, ("in",))
    if completion_price == 0.0:
        completion_price = _lookup(entry, ("out",))
    
    # Determine if cost is enabled (at least one price > 0)
    cost_enabled = prompt_price > 0.0 or completion_price > 0.0
    
    return float(prompt_price), float(completion_price), cost_enabled, matched_key

