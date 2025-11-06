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
_embedder = None  # Pluggable embedder singleton
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

# Embedding readiness flag (for cold-start warmup)
EMBED_READY = False
EMBED_READY_LOCK = threading.Lock()

# ========================================
# Configuration Constants (from env)
# ========================================

# Embedding configuration
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
ENCODER_MODEL = os.getenv("ENCODER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "FASTEMBED").upper()

# Qdrant
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_GRPC_PORT = int(os.getenv("QDRANT_GRPC_PORT", "6334"))
QDRANT_URL = os.getenv("QDRANT_URL", f"http://{QDRANT_HOST}:{QDRANT_PORT}")
QDRANT_TIMEOUT = int(os.getenv("QDRANT_TIMEOUT", "10"))  # 10s default for gRPC

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

class EmbeddingUnreadyError(RuntimeError):
    """Raised when embedding model is not ready (cold-start warmup)."""
    pass


def get_embedder():
    """
    Get pluggable embedder singleton based on EMBEDDING_BACKEND.
    Returns provider with encode(list[str]) -> np.ndarray.
    
    Raises:
        EmbeddingUnreadyError: If embedding model is not ready (cold-start warmup in progress)
    """
    global _embedder, EMBED_READY

    # Check readiness first (fast path)
    if not EMBED_READY:
        raise EmbeddingUnreadyError("Embedding model is warming up. Please retry after a few seconds.")

    if _embedder is None:
        with _lock:
            if _embedder is None:
                try:
                    from services.fiqa_api.embeddings.providers import get_embedder as _factory
                    _embedder = _factory()
                    logger.info(f"[CLIENTS] Embedder initialized (backend={EMBEDDING_BACKEND})")
                except Exception as e:
                    logger.warning(f"[CLIENTS] Embedder initialization failed: {e}")
                    _embedder = None
                    raise EmbeddingUnreadyError(f"Embedder initialization failed: {e}")
    return _embedder


def get_embedding_model():
    """
    Get singleton embedding model (SentenceTransformer).
    Lazy initialization with graceful error handling.
    
    Returns:
        SentenceTransformer instance or None if unavailable (CPU-only mode)
        
    Note:
        In CPU-only deployments, sentence-transformers is not installed.
        This function returns None and callers should handle gracefully.
    """
    global _embedding_model
    
    if _embedding_model is None:
        with _lock:
            # Double-check pattern
            if _embedding_model is None:
                try:
                    # Prefer pluggable embedder; legacy ST fallback for backward compat
                    embedder = get_embedder()
                    if embedder is not None:
                        _embedding_model = embedder  # Expose same var for compatibility
                        return _embedding_model
                    # Legacy path (kept to avoid crashing older code paths)
                    from sentence_transformers import SentenceTransformer
                    logger.info(f"[CLIENTS] Loading embedding model (legacy SBERT): {EMBEDDING_MODEL_NAME}")
                    _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
                    logger.info("[CLIENTS] Legacy SBERT embedding model loaded")
                except ImportError as e:
                    logger.warning(
                        f"[CLIENTS] sentence-transformers not available (CPU-only mode): {e}. "
                        "Embedding features disabled unless provider is available."
                    )
                    _embedding_model = None
                    return None
                except Exception as e:
                    logger.error(f"[CLIENTS] Failed to initialize any embedder: {e}")
                    _embedding_model = None
                    return None
    
    return _embedding_model


def get_encoder_model():
    """
    Get singleton encoder model (for search endpoint).
    Uses ENCODER_MODEL env var (may differ from EMBEDDING_MODEL_NAME).
    Lazy initialization with graceful error handling.
    
    Returns:
        SentenceTransformer instance or None if unavailable (CPU-only mode)
        
    Note:
        In CPU-only deployments, sentence-transformers is not installed.
        This function returns None and callers should handle gracefully.
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
                except ImportError as e:
                    # CPU-only mode: sentence-transformers not installed
                    logger.warning(
                        f"[CLIENTS] sentence-transformers not available (CPU-only mode): {e}. "
                        "Encoder features will be disabled. Install sentence-transformers for encoder support."
                    )
                    globals()['_encoder_model'] = None
                    return None
                except Exception as e:
                    logger.error(f"[CLIENTS] Failed to load encoder model: {e}")
                    globals()['_encoder_model'] = None
                    return None
    
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
                    logger.info(f"[CLIENTS] Initializing Qdrant client at {QDRANT_HOST}:{QDRANT_PORT} (gRPC:{QDRANT_GRPC_PORT})")
                    _qdrant_client = QdrantClient(
                        host=QDRANT_HOST,
                        port=QDRANT_PORT,
                        grpc_port=QDRANT_GRPC_PORT,
                        prefer_grpc=True,
                        timeout=QDRANT_TIMEOUT
                    )
                    logger.info(f"[CLIENTS] Qdrant client initialized successfully with gRPC")
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
    
    # Debug logging for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[DEBUG] OPENAI_API_KEY not loaded from environment")
        logger.warning("[DEBUG] OPENAI_API_KEY not loaded from environment")
    else:
        print(f"[DEBUG] OPENAI_API_KEY loaded: {api_key[:6]}...")
        logger.info(f"[DEBUG] OPENAI_API_KEY loaded: {api_key[:6]}...")
    
    if not OPENAI_API_KEY:
        return None
    
    if _openai_client is None:
        with _lock:
            if _openai_client is None:
                try:
                    from openai import OpenAI
                    print("[DEBUG] OpenAI client initialized successfully")
                    logger.info(f"[CLIENTS] Initializing OpenAI client")
                    logger.info(f"[CLIENTS] OpenAI API Key loaded: {bool(OPENAI_API_KEY)}")
                    _openai_client = OpenAI(
                        api_key=OPENAI_API_KEY,
                        timeout=OPENAI_TIMEOUT
                    )
                    logger.info(f"[CLIENTS] OpenAI client initialized successfully")
                except Exception as e:
                    print(f"[DEBUG] Failed to init OpenAI client: {e}")
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
    
    # OpenAI health check
    try:
        import openai
        print(f"[DEBUG] openai version: {openai.__version__}")
        logger.info(f"[DEBUG] openai version: {openai.__version__}")
    except Exception as e:
        print(f"[DEBUG] openai import failed: {e}")
        logger.warning(f"[DEBUG] openai import failed: {e}")
    
    status = {
        "embedding_model": False,
        "qdrant": False,
        "redis": False,
        "openai": False
    }
    
    # Initialize Embedding Model
    try:
        model = get_embedding_model()
        status["embedding_model"] = model is not None
    except Exception as e:
        logger.error(f"[CLIENTS] Embedding model initialization failed: {e}")
        status["embedding_model"] = False
    
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
        logger.warning(f"[CLIENTS] Redis initialization failed (non-critical): {e}")
        status["redis"] = False
    
    # Initialize OpenAI (optional)
    if not skip_openai:
        try:
            client = get_openai_client()
            status["openai"] = client is not None
        except Exception as e:
            logger.warning(f"[CLIENTS] OpenAI initialization failed (non-critical): {e}")
    
    _clients_initialized = all([
        status["embedding_model"],
        status["qdrant"]
        # Redis is optional, don't block initialization
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


def _warmup_embedding_background():
    """
    Background thread function to warm up FastEmbed model.
    Sets EMBED_READY flag when complete.
    """
    global EMBED_READY, _embedder
    
    try:
        model_name = os.getenv("FASTEMBED_MODEL", "BAAI/bge-small-en-v1.5")
        logger.info(f"[CLIENTS] Starting background embedding warmup (model={model_name})...")
        
        from fastembed import TextEmbedding
        # This will download and initialize the model
        warmup_model = TextEmbedding(model_name=model_name)
        
        # Also initialize the embedder through the provider for consistency
        from services.fiqa_api.embeddings.providers import get_embedder as _factory
        _embedder = _factory()
        
        # Mark as ready
        with EMBED_READY_LOCK:
            EMBED_READY = True
        
        logger.info(f"[CLIENTS] Embedding warmup complete (model={model_name})")
    except Exception as e:
        logger.error(f"[CLIENTS] Embedding warmup failed: {e}")
        # Don't set EMBED_READY, so queries will return 503


def start_embedding_warmup():
    """
    Start background thread to warm up FastEmbed model.
    Non-blocking - returns immediately.
    """
    warmup_thread = threading.Thread(
        target=_warmup_embedding_background,
        daemon=True,
        name="embedding-warmup"
    )
    warmup_thread.start()
    logger.info("[CLIENTS] Background embedding warmup thread started")


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


def check_embedding_ready() -> bool:
    """
    Check if embedding encoder can be initialized (lightweight probe).
    Does not actually initialize the model, just checks if it would succeed.
    
    Returns:
        True if embedding backend is ready, False otherwise
    """
    global _embedding_model

    if _embedding_model is not None:
        return True

    # Try constructing provider (FASTEMBED by default)
    try:
        emb = get_embedder()
        return emb is not None
    except Exception:
        return False

