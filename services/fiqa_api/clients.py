"""
clients.py - Singleton Client Manager
======================================
Thread-safe singleton clients for heavy resources.
Initialize once at startup, reuse across requests.

Provides:
- get_embedding_model() -> SentenceTransformer
- get_qdrant_client() -> QdrantClient  
- get_redis_client() -> redis.Redis
- get_openai_client() -> OpenAI (optional)
"""

import os
import time
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# ========================================
# Global Singleton State (Thread-Safe)
# ========================================

_lock = threading.Lock()
_embedding_model = None
_qdrant_client = None
_redis_client = None
_openai_client = None
_clients_initialized = False

# Reconnection state tracking
_qdrant_last_reconnect_attempt = 0.0
_redis_last_reconnect_attempt = 0.0
_qdrant_connection_ok = True
_redis_connection_ok = True

# Reconnection cooldown (seconds)
RECONNECT_COOLDOWN = float(os.getenv("CLIENT_RECONNECT_COOLDOWN", "5.0"))

# ========================================
# Configuration Constants (from env)
# ========================================

# Embedding model
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
ENCODER_MODEL = os.getenv("ENCODER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Qdrant
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_URL = os.getenv("QDRANT_URL", f"http://{QDRANT_HOST}:{QDRANT_PORT}")
QDRANT_TIMEOUT = int(os.getenv("QDRANT_TIMEOUT", "3"))  # 3s default

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT", "3"))  # 3s default

# OpenAI (optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_TIMEOUT = int(os.getenv("CODE_LOOKUP_LLM_TIMEOUT_MS", "3000")) / 1000.0  # 3s default


# ========================================
# Singleton Getters (Thread-Safe)
# ========================================

def get_embedding_model():
    """
    Get singleton embedding model (SentenceTransformer).
    
    Returns:
        SentenceTransformer instance
        
    Raises:
        RuntimeError: If model failed to initialize
    """
    global _embedding_model
    
    if _embedding_model is None:
        with _lock:
            # Double-check pattern
            if _embedding_model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    logger.info(f"[CLIENTS] Loading embedding model: {EMBEDDING_MODEL_NAME}")
                    _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
                    logger.info(f"[CLIENTS] Embedding model loaded successfully")
                except Exception as e:
                    logger.error(f"[CLIENTS] Failed to load embedding model: {e}")
                    raise RuntimeError(f"Embedding model initialization failed: {e}")
    
    return _embedding_model


def get_encoder_model():
    """
    Get singleton encoder model (for search endpoint).
    Uses ENCODER_MODEL env var (may differ from EMBEDDING_MODEL_NAME).
    
    Returns:
        SentenceTransformer instance
    """
    # For search endpoint, use the same singleton if models match
    if ENCODER_MODEL == f"sentence-transformers/{EMBEDDING_MODEL_NAME}":
        return get_embedding_model()
    
    # Otherwise, use a separate singleton (rare case)
    global _encoder_model
    if '_encoder_model' not in globals():
        globals()['_encoder_model'] = None
    
    _encoder = globals().get('_encoder_model')
    if _encoder is None:
        with _lock:
            _encoder = globals().get('_encoder_model')
            if _encoder is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    logger.info(f"[CLIENTS] Loading encoder model: {ENCODER_MODEL}")
                    _encoder = SentenceTransformer(ENCODER_MODEL)
                    globals()['_encoder_model'] = _encoder
                    logger.info(f"[CLIENTS] Encoder model loaded successfully")
                except Exception as e:
                    logger.error(f"[CLIENTS] Failed to load encoder model: {e}")
                    raise RuntimeError(f"Encoder model initialization failed: {e}")
    
    return _encoder


def get_qdrant_client():
    """
    Get singleton Qdrant client.
    
    Returns:
        QdrantClient instance
        
    Raises:
        RuntimeError: If client failed to initialize
    """
    global _qdrant_client
    
    if _qdrant_client is None:
        with _lock:
            if _qdrant_client is None:
                try:
                    from qdrant_client import QdrantClient
                    logger.info(f"[CLIENTS] Initializing Qdrant client at {QDRANT_URL}")
                    _qdrant_client = QdrantClient(url=QDRANT_URL, timeout=QDRANT_TIMEOUT)
                    logger.info(f"[CLIENTS] Qdrant client initialized successfully")
                except Exception as e:
                    logger.error(f"[CLIENTS] Failed to initialize Qdrant client: {e}")
                    raise RuntimeError(f"Qdrant client initialization failed: {e}")
    
    return _qdrant_client


def ensure_qdrant_connection() -> bool:
    """
    Ensure Qdrant connection is alive, reconnect if necessary.
    
    Uses cooldown mechanism to prevent reconnection storms.
    
    Returns:
        True if connection is healthy, False otherwise
    """
    global _qdrant_client, _qdrant_last_reconnect_attempt, _qdrant_connection_ok
    
    if _qdrant_client is None:
        logger.warning("[QDRANT] Client not initialized yet")
        return False
    
    # Quick health check
    try:
        # Lightweight check: get collections (should be fast)
        _qdrant_client.get_collections()
        
        # Mark connection as OK if it was previously failed
        if not _qdrant_connection_ok:
            logger.info("[QDRANT] Connection restored successfully")
            _qdrant_connection_ok = True
        
        return True
        
    except Exception as e:
        # Connection failed
        if _qdrant_connection_ok:
            logger.error(f"[QDRANT] Connection lost: {e}")
            _qdrant_connection_ok = False
        
        # Check cooldown before attempting reconnect
        now = time.monotonic()
        time_since_last_attempt = now - _qdrant_last_reconnect_attempt
        
        if time_since_last_attempt < RECONNECT_COOLDOWN:
            logger.debug(f"[QDRANT] Reconnection on cooldown ({time_since_last_attempt:.1f}s < {RECONNECT_COOLDOWN}s)")
            return False
        
        # Attempt reconnection
        logger.info("[QDRANT] Attempting to reconnect...")
        _qdrant_last_reconnect_attempt = now
        
        with _lock:
            try:
                from qdrant_client import QdrantClient
                _qdrant_client = QdrantClient(url=QDRANT_URL, timeout=QDRANT_TIMEOUT)
                
                # Test new connection
                _qdrant_client.get_collections()
                
                logger.info("[QDRANT] Reconnection successful")
                _qdrant_connection_ok = True
                return True
                
            except Exception as reconnect_error:
                logger.error(f"[QDRANT] Reconnection failed: {reconnect_error}")
                return False


def get_redis_client():
    """
    Get singleton Redis client (with connection pooling).
    
    Returns:
        redis.Redis instance
        
    Raises:
        RuntimeError: If client failed to initialize
    """
    global _redis_client
    
    if _redis_client is None:
        with _lock:
            if _redis_client is None:
                try:
                    import redis
                    logger.info(f"[CLIENTS] Initializing Redis client at {REDIS_HOST}:{REDIS_PORT}")
                    _redis_client = redis.Redis(
                        host=REDIS_HOST,
                        port=REDIS_PORT,
                        decode_responses=True,
                        socket_timeout=REDIS_SOCKET_TIMEOUT,
                        socket_connect_timeout=REDIS_SOCKET_TIMEOUT,
                        # Connection pool settings
                        max_connections=50,
                        health_check_interval=30
                    )
                    # Test connection
                    _redis_client.ping()
                    logger.info(f"[CLIENTS] Redis client initialized successfully")
                except Exception as e:
                    logger.error(f"[CLIENTS] Failed to initialize Redis client: {e}")
                    raise RuntimeError(f"Redis client initialization failed: {e}")
    
    return _redis_client


def ensure_redis_connection() -> bool:
    """
    Ensure Redis connection is alive, reconnect if necessary.
    
    Uses cooldown mechanism to prevent reconnection storms.
    
    Returns:
        True if connection is healthy, False otherwise
    """
    global _redis_client, _redis_last_reconnect_attempt, _redis_connection_ok
    
    if _redis_client is None:
        logger.warning("[REDIS] Client not initialized yet")
        return False
    
    # Quick health check
    try:
        # Lightweight check: ping
        _redis_client.ping()
        
        # Mark connection as OK if it was previously failed
        if not _redis_connection_ok:
            logger.info("[REDIS] Connection restored successfully")
            _redis_connection_ok = True
        
        return True
        
    except Exception as e:
        # Connection failed
        if _redis_connection_ok:
            logger.error(f"[REDIS] Connection lost: {e}")
            _redis_connection_ok = False
        
        # Check cooldown before attempting reconnect
        now = time.monotonic()
        time_since_last_attempt = now - _redis_last_reconnect_attempt
        
        if time_since_last_attempt < RECONNECT_COOLDOWN:
            logger.debug(f"[REDIS] Reconnection on cooldown ({time_since_last_attempt:.1f}s < {RECONNECT_COOLDOWN}s)")
            return False
        
        # Attempt reconnection
        logger.info("[REDIS] Attempting to reconnect...")
        _redis_last_reconnect_attempt = now
        
        with _lock:
            try:
                import redis
                _redis_client = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    decode_responses=True,
                    socket_timeout=REDIS_SOCKET_TIMEOUT,
                    socket_connect_timeout=REDIS_SOCKET_TIMEOUT,
                    max_connections=50,
                    health_check_interval=30
                )
                
                # Test new connection
                _redis_client.ping()
                
                logger.info("[REDIS] Reconnection successful")
                _redis_connection_ok = True
                return True
                
            except Exception as reconnect_error:
                logger.error(f"[REDIS] Reconnection failed: {reconnect_error}")
                return False


def get_openai_client() -> Optional[object]:
    """
    Get singleton OpenAI client (optional).
    
    Returns:
        OpenAI instance or None if API key not available
    """
    global _openai_client
    
    if not OPENAI_API_KEY:
        return None
    
    if _openai_client is None:
        with _lock:
            if _openai_client is None:
                try:
                    from openai import OpenAI
                    logger.info(f"[CLIENTS] Initializing OpenAI client")
                    _openai_client = OpenAI(
                        api_key=OPENAI_API_KEY,
                        timeout=OPENAI_TIMEOUT
                    )
                    logger.info(f"[CLIENTS] OpenAI client initialized successfully")
                except Exception as e:
                    logger.warning(f"[CLIENTS] Failed to initialize OpenAI client: {e}")
                    return None
    
    return _openai_client


# ========================================
# Initialization & Health Check
# ========================================

def initialize_clients(skip_openai: bool = False) -> dict:
    """
    Initialize all singleton clients at startup.
    
    Args:
        skip_openai: If True, skip OpenAI client initialization
        
    Returns:
        Dict with initialization status for each client
    """
    global _clients_initialized
    
    status = {
        "embedding_model": False,
        "qdrant": False,
        "redis": False,
        "openai": False
    }
    
    # Initialize Embedding Model
    try:
        get_embedding_model()
        status["embedding_model"] = True
    except Exception as e:
        logger.error(f"[CLIENTS] Embedding model initialization failed: {e}")
    
    # Initialize Qdrant
    try:
        get_qdrant_client()
        status["qdrant"] = True
    except Exception as e:
        logger.error(f"[CLIENTS] Qdrant initialization failed: {e}")
    
    # Initialize Redis
    try:
        get_redis_client()
        status["redis"] = True
    except Exception as e:
        logger.error(f"[CLIENTS] Redis initialization failed: {e}")
    
    # Initialize OpenAI (optional)
    if not skip_openai:
        try:
            client = get_openai_client()
            status["openai"] = client is not None
        except Exception as e:
            logger.warning(f"[CLIENTS] OpenAI initialization failed (non-critical): {e}")
    
    _clients_initialized = all([
        status["embedding_model"],
        status["qdrant"],
        status["redis"]
    ])
    
    logger.info(f"[CLIENTS] Initialization complete: {status}")
    return status


def are_clients_ready() -> bool:
    """
    Check if core clients are initialized and ready.
    
    Returns:
        True if all core clients (embedding, qdrant, redis) are ready
    """
    return _clients_initialized


def get_clients_status() -> dict:
    """
    Get detailed status of all clients.
    
    Returns:
        Dict with status of each client
    """
    return {
        "embedding_model": _embedding_model is not None,
        "qdrant": _qdrant_client is not None,
        "redis": _redis_client is not None,
        "openai": _openai_client is not None,
        "ready": are_clients_ready()
    }

