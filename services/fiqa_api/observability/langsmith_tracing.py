"""
langsmith_tracing.py - Non-intrusive LangSmith tracing helper

Provides a safe, opt-in decorator for LangSmith tracing that:
1. Only traces if langsmith is installed and environment variables are set
2. Completely no-op if tracing is disabled (no performance impact)
3. Exception-safe (never breaks execution if langsmith import fails)

Supports both:
- LANGSMITH_API_KEY / LANGSMITH_PROJECT (preferred)
- LANGCHAIN_API_KEY / LANGCHAIN_TRACING_V2 (backward compatibility)

Usage:
    from services.fiqa_api.observability.langsmith_tracing import maybe_traceable

    @maybe_traceable(name="my_function_run")
    def my_function(...):
        ...
"""

import os
import logging
from functools import wraps
from typing import Callable, TypeVar, ParamSpec, Optional

logger = logging.getLogger(__name__)

# Try to import langsmith's traceable decorator and Client
_LANGSMITH_AVAILABLE = False
traceable = None
Client = None

try:
    from langsmith.run_helpers import traceable
    from langsmith import Client
    _LANGSMITH_AVAILABLE = True
except Exception:
    # langsmith not installed or import failed - safe to continue
    traceable = None
    Client = None
    _LANGSMITH_AVAILABLE = False

# Type variables for decorator typing
P = ParamSpec('P')
T = TypeVar('T')

# Global client instance (initialized once)
_langsmith_client: Optional[Client] = None
_langsmith_client_initialized = False


def _get_langsmith_client() -> Optional[Client]:
    """
    Get or initialize LangSmith client with project configuration.
    
    Returns:
        Client instance if available and configured, None otherwise
    """
    global _langsmith_client, _langsmith_client_initialized
    
    if not _LANGSMITH_AVAILABLE:
        return None
    
    if _langsmith_client_initialized:
        return _langsmith_client
    
    # Check for API key (prefer LANGSMITH_API_KEY, fallback to LANGCHAIN_API_KEY)
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        _langsmith_client_initialized = True
        return None
    
    # Check for project name (prefer LANGSMITH_PROJECT, fallback to LANGCHAIN_PROJECT)
    project_name = os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT")
    
    try:
        # Set project via environment variable (LangSmith reads LANGCHAIN_PROJECT)
        if project_name:
            os.environ["LANGCHAIN_PROJECT"] = project_name
            logger.info(f"[LANGSMITH_TRACING] Set project via LANGCHAIN_PROJECT: {project_name}")
        
        # Initialize client
        _langsmith_client = Client(api_key=api_key)
        
        if not project_name:
            logger.info("[LANGSMITH_TRACING] Initialized without project (using default)")
        
        _langsmith_client_initialized = True
        return _langsmith_client
    except Exception as e:
        logger.warning(f"[LANGSMITH_TRACING] Failed to initialize client: {e}")
        _langsmith_client_initialized = True
        return None


def maybe_traceable(name: str):
    """
    Decorator that optionally wraps a function with LangSmith tracing.
    
    Behavior:
    - If langsmith is not installed → returns original function (no-op)
    - If API key is not set → returns original function (no-op)
    - Otherwise → wraps function with @traceable(name=name)
    
    Supports both:
    - LANGSMITH_API_KEY / LANGSMITH_PROJECT (preferred)
    - LANGCHAIN_API_KEY / LANGCHAIN_TRACING_V2 (backward compatibility)
    
    Args:
        name: Name of the trace run (shown in LangSmith UI)
    
    Returns:
        Decorator function that optionally traces the wrapped function
    
    Example:
        @maybe_traceable(name="ecommerce_after_sales_agent")
        def run_ecommerce_agent(request: EcommerceAgentRequest) -> EcommerceAgentState:
            ...
    """
    def decorator(fn: Callable[P, T]) -> Callable[P, T]:
        # If langsmith is not available, return original function
        if not _LANGSMITH_AVAILABLE:
            return fn
        
        # Check for API key (prefer LANGSMITH_API_KEY, fallback to LANGCHAIN_API_KEY)
        api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
        
        # For backward compatibility, also check LANGCHAIN_TRACING_V2
        if not api_key:
            tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() in ("true", "1", "yes", "on")
            api_key = os.getenv("LANGCHAIN_API_KEY") if tracing_enabled else None
        
        if not api_key:
            # API key not set - return original function (silent no-op)
            return fn
        
        # Initialize client (sets project if LANGSMITH_PROJECT is set)
        _get_langsmith_client()
        
        # Tracing is enabled - wrap with traceable
        try:
            wrapped = traceable(name=name)(fn)
            
            @wraps(fn)
            def inner(*args: P.args, **kwargs: P.kwargs) -> T:
                """Inner wrapper that preserves function metadata."""
                return wrapped(*args, **kwargs)
            
            return inner
        except Exception as e:
            # If wrapping fails, log warning and return original function
            logger.warning(
                f"[LANGSMITH_TRACING] Failed to wrap function '{fn.__name__}' with traceable: {e}. "
                f"Continuing without tracing."
            )
            return fn
    
    return decorator


__all__ = ["maybe_traceable"]

