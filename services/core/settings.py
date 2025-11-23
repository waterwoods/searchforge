"""
Unified Settings Module for SearchForge
========================================
Single source of truth for all environment variables.
Loads from .env at repo root with strict parsing.

Usage:
    from services.core.settings import get_env, get_force_override_config
    
    value = get_env("SOME_VAR", default="default_value")
    config = get_force_override_config()
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env from repository root
_REPO_ROOT = Path(__file__).parent.parent.parent
_ENV_PATH = _REPO_ROOT / '.env'

if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH, override=False)
    logger.info(f"[SETTINGS] Loaded environment from {_ENV_PATH}")
else:
    logger.warning(f"[SETTINGS] .env file not found at {_ENV_PATH}")


def get_env(name: str, default: Optional[str] = None) -> str:
    """
    Get environment variable with optional default.
    
    Args:
        name: Environment variable name
        default: Default value if not set
        
    Returns:
        Environment variable value or default
    """
    return os.getenv(name, default)


def get_env_bool(name: str, default: bool = False) -> bool:
    """
    Get environment variable as boolean.
    
    Args:
        name: Environment variable name
        default: Default value if not set
        
    Returns:
        Boolean value (true/false/yes/no/1/0)
    """
    value = get_env(name, str(default)).lower()
    return value in ('true', 'yes', '1', 'on')


def get_env_int(name: str, default: int = 0) -> int:
    """
    Get environment variable as integer.
    
    Args:
        name: Environment variable name
        default: Default value if not set
        
    Returns:
        Integer value
    """
    try:
        return int(get_env(name, str(default)))
    except ValueError:
        logger.warning(f"[SETTINGS] Invalid integer for {name}, using default {default}")
        return default


def get_env_float(name: str, default: float = 0.0) -> float:
    """
    Get environment variable as float.
    
    Args:
        name: Environment variable name
        default: Default value if not set
        
    Returns:
        Float value
    """
    try:
        return float(get_env(name, str(default)))
    except ValueError:
        logger.warning(f"[SETTINGS] Invalid float for {name}, using default {default}")
        return default


def get_env_json(name: str, default: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Get environment variable as JSON object.
    
    Args:
        name: Environment variable name
        default: Default value if JSON parsing fails
        
    Returns:
        Parsed JSON dictionary or default
    """
    if default is None:
        default = {}
    
    value = get_env(name, '')
    if not value:
        return default
    
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        logger.error(f"[SETTINGS] Failed to parse JSON for {name}: {e}")
        return default


# ========================================
# Force Override Configuration
# ========================================

def get_force_override_enabled() -> bool:
    """Check if force override is enabled."""
    return get_env_bool("FORCE_OVERRIDE", False)


def get_force_override_params() -> Dict[str, Any]:
    """Get forced parameters from environment."""
    return get_env_json("FORCE_PARAMS_JSON", {})


def get_hard_cap_enabled() -> bool:
    """Check if hard cap is enabled."""
    return get_env_bool("HARD_CAP_ENABLED", False)


def get_hard_cap_limits() -> Dict[str, Any]:
    """Get hard cap limits from environment."""
    return get_env_json("HARD_CAP_LIMITS", {})


def get_force_override_config() -> Dict[str, Any]:
    """
    Get complete force override configuration.
    
    Returns:
        Dictionary with force override settings:
        {
            "enabled": bool,
            "params": dict,
            "hard_cap_enabled": bool,
            "hard_cap_limits": dict
        }
    """
    config = {
        "enabled": get_force_override_enabled(),
        "params": get_force_override_params(),
        "hard_cap_enabled": get_hard_cap_enabled(),
        "hard_cap_limits": get_hard_cap_limits()
    }
    
    # Log configuration on first retrieval
    if config["enabled"]:
        logger.info(f"[FORCE_OVERRIDE] Enabled with params: {config['params']}")
        if config["hard_cap_enabled"]:
            logger.info(f"[FORCE_OVERRIDE] Hard cap enabled with limits: {config['hard_cap_limits']}")
    
    return config


# ========================================
# Other Configuration Getters
# ========================================

def get_rate_limit_config() -> Dict[str, Any]:
    """Get rate limiting configuration."""
    return {
        "max": get_env_int("RATE_LIMIT_MAX", 1000),
        "window_sec": get_env_float("RATE_LIMIT_WINDOW_SEC", 1.0)
    }


def get_qdrant_config() -> Dict[str, Any]:
    """Get Qdrant configuration."""
    return {
        "url": get_env("QDRANT_URL", "http://localhost:6333"),
        "collection": get_env("COLLECTION_NAME", "beir_fiqa_full_ta"),
        "enable_page_index": get_env_bool("ENABLE_PAGE_INDEX", True)
    }


def get_reranker_config() -> Dict[str, Any]:
    """Get reranker configuration."""
    return {
        "enabled": get_env_bool("ENABLE_RERANKER", True),
        "model_name": get_env("RERANK_MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
        "top_k": get_env_int("RERANK_TOP_K", 6),
        "candidate_k_max": get_env_int("CANDIDATE_K_MAX", 50),
        "timeout_ms": get_env_int("RERANK_TIMEOUT_MS", 2000),
        "model_cache_dir": get_env("MODEL_CACHE_DIR", "./models")
    }


def get_recall_config() -> Dict[str, Any]:
    """Get Recall@10 calculation configuration."""
    return {
        "enabled": get_env_bool("RECALL_ENABLED", False),
        "sample_rate": get_env_float("RECALL_SAMPLE_RATE", 0.0)
    }


def get_use_ml_approval_score() -> bool:
    """
    Check if ML approval score should be used (hybrid rules + ML).
    
    Returns:
        True if USE_ML_APPROVAL_SCORE env var is set to true, False otherwise
    """
    return get_env_bool("USE_ML_APPROVAL_SCORE", False)


# ========================================
# Module-level constants for quick access
# ========================================

RECALL_ENABLED = get_env_bool("RECALL_ENABLED", False)
RECALL_SAMPLE_RATE = get_env_float("RECALL_SAMPLE_RATE", 0.0)


# Module initialization
logger.info(f"[SETTINGS] Module initialized from {_ENV_PATH}")

