"""
Small helper for LangSmith / LangGraph tracing configuration.

We do NOT hardcode API keys here.
We only read environment variables and optionally log what project/name is used.
"""

from __future__ import annotations

import os
from typing import Dict, Any

LANGSMITH_ENV_VARS = [
    "LANGSMITH_API_KEY",
    "LANGSMITH_ENDPOINT",
    "LANGSMITH_TRACING",
    "LANGSMITH_PROJECT",
    # Back-compat with older LangChain env vars:
    "LANGCHAIN_TRACING_V2",
    "LANGCHAIN_ENDPOINT",
    "LANGCHAIN_API_KEY",
    "LANGCHAIN_PROJECT",
]


def is_langsmith_enabled() -> bool:
    """
    Return True if tracing appears to be enabled via env vars.
    
    Priority order:
    1. LANGCHAIN_API_KEY + LANGCHAIN_TRACING_V2 (preferred, matches .env format)
    2. LANGSMITH_API_KEY + LANGSMITH_TRACING (backward compatibility)
    
    Tracing is enabled if:
    - API key is present (LANGCHAIN_API_KEY or LANGSMITH_API_KEY)
    - Tracing flag is set to "true", "1", "yes", or "on" (case-insensitive)
    """
    # Priority: LANGCHAIN_* first, then LANGSMITH_*
    api_key = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
    
    # Check tracing flag - LANGCHAIN_TRACING_V2 takes priority
    tracing_flag = os.getenv("LANGCHAIN_TRACING_V2")
    if tracing_flag:
        tracing_enabled = tracing_flag.lower() in ("true", "1", "yes", "on")
    else:
        # Fallback to LANGSMITH_TRACING
        tracing_flag = os.getenv("LANGSMITH_TRACING")
        if tracing_flag:
            tracing_enabled = tracing_flag.lower() in ("true", "1", "yes", "on")
        else:
            tracing_enabled = False
    
    return bool(api_key) and tracing_enabled


def default_langsmith_run_config(flow_name: str) -> Dict[str, Any]:
    """
    Default config dict that we can pass into LangGraph .invoke() calls.
    
    This sets a nice run_name so traces are readable in LangSmith.
    
    The project name is read from environment variables:
    - Priority: LANGCHAIN_PROJECT (matches .env format)
    - Fallback: LANGSMITH_PROJECT
    - Default: "jobhunter-local" if neither is set
    
    Args:
        flow_name: Name of the flow (e.g., "jobhunter_jd_analysis")
    
    Returns:
        Config dict with run_name and tags for LangGraph
    """
    # Get project name - priority: LANGCHAIN_PROJECT > LANGSMITH_PROJECT > default
    project_name = (
        os.getenv("LANGCHAIN_PROJECT") 
        or os.getenv("LANGSMITH_PROJECT") 
        or "jobhunter-local"
    )
    
    return {
        "run_name": flow_name,
        # You can add thread_id or other configurable fields later if needed.
        "tags": ["jobhunter", flow_name],
        # Set project name for LangSmith (LangGraph reads LANGCHAIN_PROJECT from env)
        # We set it here via config, but LangGraph also respects LANGCHAIN_PROJECT env var
    }

