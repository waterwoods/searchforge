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


def tracing_enabled() -> bool:
    """True when LangSmith client can send runs (API key present + package installed)."""
    if not _LANGSMITH_AVAILABLE:
        return False
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if api_key:
        return True
    tracing_flag = os.getenv("LANGCHAIN_TRACING_V2", "").lower() in ("true", "1", "yes", "on")
    return tracing_flag and bool(os.getenv("LANGCHAIN_API_KEY"))


def maybe_traceable(
    name: str,
    *,
    process_inputs: Optional[Callable[[dict], dict]] = None,
    process_outputs: Optional[Callable[[object], object]] = None,
    metadata: Optional[dict] = None,
):
    """
    Decorator that optionally wraps a function with LangSmith tracing.
    
    Behavior:
    - If langsmith is not installed → returns original function (no-op)
    - If API key is not set → returns original function (no-op)
    - Otherwise → wraps function with @traceable(name=name, ...)
    
    Supports both:
    - LANGSMITH_API_KEY / LANGSMITH_PROJECT (preferred)
    - LANGCHAIN_API_KEY / LANGCHAIN_TRACING_V2 (backward compatibility)
    
    Args:
        name: Name of the trace run (shown in LangSmith UI)
        process_inputs: Optional redaction hook for traced inputs
        process_outputs: Optional redaction hook for traced outputs
        metadata: Optional static metadata merged into the run
    
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
        
        if not tracing_enabled():
            # API key not set - return original function (silent no-op)
            return fn
        
        # Initialize client (sets project if LANGSMITH_PROJECT is set)
        _get_langsmith_client()
        
        # Tracing is enabled - wrap with traceable
        try:
            kwargs: dict = {"name": name}
            if process_inputs is not None:
                kwargs["process_inputs"] = process_inputs
            if process_outputs is not None:
                kwargs["process_outputs"] = process_outputs
            if metadata:
                kwargs["metadata"] = dict(metadata)
            wrapped = traceable(**kwargs)(fn)
            
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


__all__ = ["maybe_traceable", "tracing_enabled"]

