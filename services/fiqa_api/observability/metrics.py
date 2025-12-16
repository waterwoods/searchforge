"""
metrics.py - LLM Call Metrics Collection

Unified structure for tracking LLM usage (tokens) and latency.
Minimal instrumentation for cost and performance monitoring.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LLMCallMetric(BaseModel):
    """
    Single LLM call metric record.
    
    Captures usage (tokens) and latency for one LLM API call.
    """
    component: str = Field(..., description="Which component made this call, e.g. 'response_generator', 'nl_to_intent', 'llm_judge'")
    model: str = Field(..., description="Model name used for this call")
    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)
    latency_ms: float = Field(..., ge=0.0, description="Total call latency in milliseconds")
    success: bool = Field(..., description="Whether the call succeeded")
    error_message: Optional[str] = Field(None, description="Error message if any")


class LLMRunMetrics(BaseModel):
    """
    Aggregated metrics for a single agent run.
    
    Collects all LLM call metrics from one agent execution.
    """
    calls: List[LLMCallMetric] = Field(default_factory=list, description="List of LLM call metrics")


def extract_llm_usage(response: Any) -> Dict[str, int]:
    """
    Extract token usage from OpenAI response object.
    
    Args:
        response: OpenAI ChatCompletion response object
    
    Returns:
        Dict with prompt_tokens, completion_tokens, total_tokens
        All values default to 0 if usage is not available
    """
    if hasattr(response, 'usage') and response.usage:
        return {
            "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0) or 0,
            "completion_tokens": getattr(response.usage, 'completion_tokens', 0) or 0,
            "total_tokens": getattr(response.usage, 'total_tokens', 0) or 0,
        }
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
