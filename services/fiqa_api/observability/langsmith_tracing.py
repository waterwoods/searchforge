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
    """True when LangSmith client can send runs (API key present + package installed).

    Accident-story kill switch: ACCIDENT_STORY_LANGSMITH_TRACING=0 disables tracing
    even when a key is present. Missing key → False (intake continues).
    """
    if not _LANGSMITH_AVAILABLE:
        return False
    story_flag = (os.getenv("ACCIDENT_STORY_LANGSMITH_TRACING") or "1").strip().lower()
    if story_flag in ("0", "false", "no", "off"):
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

    Behavior (evaluated at **call** time so kill switches work without reimport):
    - If langsmith is not installed → no-op
    - If tracing_enabled() is False → no-op
    - Otherwise → @traceable with optional process_inputs / process_outputs

    Supports both:
    - LANGSMITH_API_KEY / LANGSMITH_PROJECT (preferred)
    - LANGCHAIN_API_KEY / LANGCHAIN_TRACING_V2 (backward compatibility)
    """
    def decorator(fn: Callable[P, T]) -> Callable[P, T]:
        if not _LANGSMITH_AVAILABLE or traceable is None:
            return fn

        wrapped_fn: Optional[Callable[P, T]] = None

        @wraps(fn)
        def inner(*args: P.args, **kwargs: P.kwargs) -> T:
            nonlocal wrapped_fn
            if not tracing_enabled():
                return fn(*args, **kwargs)
            try:
                _get_langsmith_client()
                if wrapped_fn is None:
                    tkwargs: dict = {"name": name}
                    if process_inputs is not None:
                        tkwargs["process_inputs"] = process_inputs
                    if process_outputs is not None:
                        tkwargs["process_outputs"] = process_outputs
                    if metadata:
                        tkwargs["metadata"] = dict(metadata)
                    wrapped_fn = traceable(**tkwargs)(fn)  # type: ignore[misc]
                return wrapped_fn(*args, **kwargs)  # type: ignore[misc]
            except Exception as e:
                logger.warning(
                    f"[LANGSMITH_TRACING] Trace wrap/call failed for '{fn.__name__}': {e}. "
                    f"Continuing without tracing."
                )
                return fn(*args, **kwargs)

        return inner

    return decorator


__all__ = ["maybe_traceable", "tracing_enabled"]

