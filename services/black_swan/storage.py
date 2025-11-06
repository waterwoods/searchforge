"""
Black Swan Async - Redis Storage

Handles Redis I/O for Black Swan state, reports, and QA feed.
Provides graceful degradation to memory-only mode when Redis is unavailable.

Redis Keys:
- bs:run:status -> Current run state JSON
- bs:run:report -> Final report JSON
- bs:qa:feed -> List of recent query/answer samples (max 200)

Memory Fallback:
- When Redis unavailable, uses in-memory ring buffer (max 200 items)
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from collections import deque
import redis

logger = logging.getLogger(__name__)


class RedisStorage:
    """
    Redis storage manager with graceful degradation.
    
    If Redis is unavailable, operations silently degrade to memory-only mode
    with in-memory ring buffer for QA feed.
    """
    
    def __init__(self, redis_url: Optional[str] = None, enabled: bool = True):
        """
        Initialize Redis storage.
        
        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
            enabled: Enable Redis storage (if False, uses memory-only mode)
        """
        self.enabled = enabled
        self.client: Optional[redis.Redis] = None
        self.available = False
        
        # Memory fallback: ring buffer for QA feed (max 200 items)
        self._qa_feed_buffer: deque = deque(maxlen=200)
        
        if not enabled:
            logger.info("[BS:STORAGE] Redis disabled, using memory-only mode")
            return
        
        # Get Redis URL from parameter or environment
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        try:
            # Connect to Redis with timeout and retry settings
            from redis import ConnectionPool
            
            pool = ConnectionPool.from_url(
                redis_url,
                socket_connect_timeout=2,    # 2s connection timeout
                socket_timeout=5,            # 5s operation timeout
                retry_on_timeout=True,       # Retry on timeout
                max_connections=10,          # Connection pool size
                decode_responses=True
            )
            
            self.client = redis.Redis(connection_pool=pool)
            
            # Test connection with timeout
            self.client.ping()
            self.available = True
            logger.info(f"[BS:STORAGE] Connected to Redis: {redis_url} (timeouts: connect=2s, op=5s)")
            
        except Exception as e:
            logger.warning(f"[BS:STORAGE] Redis unavailable: {e} (degrading to memory-only)")
            self.client = None
            self.available = False
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self.available and self.client is not None
    
    def save_status(self, state: Dict[str, Any]) -> bool:
        """
        Save current run status to Redis.
        
        Args:
            state: Run state dictionary
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            key = "bs:run:status"
            value = json.dumps(state)
            self.client.set(key, value)
            return True
            
        except Exception as e:
            logger.error(f"[BS:STORAGE] Failed to save status: {e}")
            return False
    
    def load_status(self) -> Optional[Dict[str, Any]]:
        """
        Load current run status from Redis.
        
        Returns:
            State dictionary if available, None otherwise
        """
        if not self.is_available():
            return None
        
        try:
            key = "bs:run:status"
            value = self.client.get(key)
            
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"[BS:STORAGE] Failed to load status: {e}")
            return None
    
    def save_report(self, report: Dict[str, Any]) -> bool:
        """
        Save final report to Redis.
        
        Args:
            report: Report dictionary
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            key = "bs:run:report"
            value = json.dumps(report)
            self.client.set(key, value)
            return True
            
        except Exception as e:
            logger.error(f"[BS:STORAGE] Failed to save report: {e}")
            return False
    
    def load_report(self) -> Optional[Dict[str, Any]]:
        """
        Load final report from Redis.
        
        Returns:
            Report dictionary if available, None otherwise
        """
        if not self.is_available():
            return None
        
        try:
            key = "bs:run:report"
            value = self.client.get(key)
            
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"[BS:STORAGE] Failed to load report: {e}")
            return None
    
    def append_qa_feed(self, item: Dict[str, Any], max_items: int = 200) -> bool:
        """
        Append item to QA feed (with sampling).
        
        Writes to Redis if available, otherwise writes to memory buffer.
        Always succeeds in memory mode to ensure data visibility.
        
        Args:
            item: QA feed item (query, answer, latency, etc.)
            max_items: Maximum items to keep (default 200)
            
        Returns:
            True if appended successfully
        """
        # Always write to memory buffer (fallback)
        try:
            self._qa_feed_buffer.append(item)
        except Exception as e:
            logger.error(f"[BS:STORAGE] Failed to append to memory buffer: {e}")
        
        # Also write to Redis if available
        if self.is_available():
            try:
                key = "bs:qa:feed"
                
                # Append to list
                value = json.dumps(item)
                self.client.rpush(key, value)
                
                # Trim to max items (keep newest)
                self.client.ltrim(key, -max_items, -1)
                
                return True
                
            except Exception as e:
                logger.warning(f"[BS:STORAGE] Failed to append QA feed to Redis: {e} (memory fallback active)")
        
        # Memory buffer write always succeeds
        return True
    
    def get_qa_feed(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent QA feed items (newest first).
        
        Reads from Redis if available, otherwise reads from memory buffer.
        
        Args:
            limit: Maximum items to return
            
        Returns:
            List of QA feed items (newest first)
        """
        # Try Redis first
        if self.is_available():
            try:
                key = "bs:qa:feed"
                
                # Get last N items
                values = self.client.lrange(key, -limit, -1)
                
                # Parse JSON and reverse (newest first)
                items = [json.loads(v) for v in values]
                items.reverse()
                
                return items
                
            except Exception as e:
                logger.warning(f"[BS:STORAGE] Failed to get QA feed from Redis: {e} (falling back to memory)")
        
        # Fallback to memory buffer (newest first)
        try:
            items = list(self._qa_feed_buffer)
            items.reverse()  # Reverse to get newest first
            return items[-limit:] if len(items) > limit else items
        except Exception as e:
            logger.error(f"[BS:STORAGE] Failed to get QA feed from memory: {e}")
            return []
    
    def clear_all(self) -> bool:
        """
        Clear all Black Swan keys from Redis.
        
        Returns:
            True if cleared successfully, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            keys = ["bs:run:status", "bs:run:report", "bs:qa:feed"]
            for key in keys:
                self.client.delete(key)
            logger.info("[BS:STORAGE] Cleared all Black Swan keys")
            return True
            
        except Exception as e:
            logger.error(f"[BS:STORAGE] Failed to clear keys: {e}")
            return False


# Global storage instance (initialized lazily)
_storage: Optional[RedisStorage] = None


def get_storage(redis_url: Optional[str] = None, enabled: Optional[bool] = None) -> RedisStorage:
    """
    Get or create global storage instance.
    
    Args:
        redis_url: Redis connection URL (optional)
        enabled: Enable Redis (if None, checks REDIS_ENABLED env var)
        
    Returns:
        RedisStorage instance
    """
    global _storage
    
    if _storage is None:
        # Check if Redis is enabled via environment
        if enabled is None:
            enabled = os.getenv("REDIS_ENABLED", "true").lower() == "true"
        
        _storage = RedisStorage(redis_url=redis_url, enabled=enabled)
    
    return _storage

