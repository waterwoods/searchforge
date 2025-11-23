"""
GPU Worker Client - Pool management for GPU worker instances.

Features:
- Round-robin load balancing
- Health state tracking
- /meta cache and validation
- Retry/backoff on 429/5xx
- Graceful degradation (fallback to CPU)
"""

import os
import time
import logging
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from collections import deque
from dataclasses import dataclass

import logging
logger = logging.getLogger(__name__)

try:
    import aiohttp
    import numpy as np
    _GPU_CLIENT_AVAILABLE = True
except ImportError as e:
    _GPU_CLIENT_AVAILABLE = False
    aiohttp = None
    np = None
    logger.warning(f"[GPU_CLIENT] Optional dependencies not available: {e}. GPU worker client disabled.")


@dataclass
class WorkerInstance:
    """Represents a GPU worker instance."""
    url: str
    healthy: bool = True
    meta_cache: Optional[Dict[str, Any]] = None
    last_check: float = 0.0
    consecutive_failures: int = 0


class GPUWorkerPool:
    """Pool of GPU worker instances with round-robin and health tracking."""
    
    def __init__(self, urls: List[str], timeout: float = 5.0, max_retries: int = 3):
        """
        Initialize GPU worker pool.
        
        Args:
            urls: List of worker URLs (e.g., ["http://gpu-worker:8090"])
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        if not _GPU_CLIENT_AVAILABLE:
            raise RuntimeError("GPU worker client requires aiohttp and numpy. Install: pip install aiohttp numpy")
        self.instances = [WorkerInstance(url=url) for url in urls]
        self.timeout = timeout
        self.max_retries = max_retries
        self._round_robin_idx = 0
        self._session: Optional[Any] = None  # aiohttp.ClientSession when available
        self._degraded = False  # Global degrade flag
        
        logger.info(f"[GPU_POOL] Initialized with {len(urls)} instances: {urls}")
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """Close HTTP session."""
        if self._session is not None and hasattr(self._session, 'closed') and not self._session.closed:
            await self._session.close()
    
    def _get_next_instance(self) -> Optional[WorkerInstance]:
        """Get next healthy instance via round-robin."""
        if not self.instances:
            return None
        
        # Try to find a healthy instance
        for _ in range(len(self.instances)):
            instance = self.instances[self._round_robin_idx]
            self._round_robin_idx = (self._round_robin_idx + 1) % len(self.instances)
            
            if instance.healthy:
                return instance
        
        # No healthy instances
        return None
    
    async def _check_health(self, instance: WorkerInstance) -> bool:
        """Check instance health and update meta cache."""
        try:
            session = await self._get_session()
            async with session.get(f"{instance.url}/meta", timeout=self.timeout) as resp:
                if resp.status == 200:
                    meta = await resp.json()
                    instance.meta_cache = meta
                    instance.healthy = True
                    instance.consecutive_failures = 0
                    instance.last_check = time.time()
                    return True
                else:
                    instance.healthy = False
                    instance.consecutive_failures += 1
                    return False
        except Exception as e:
            logger.debug(f"[GPU_POOL] Health check failed for {instance.url}: {e}")
            instance.healthy = False
            instance.consecutive_failures += 1
            return False
    
    async def wait_ready(
        self,
        timeout: float = 300.0,
        consecutive: int = 3,
        check_interval: float = 2.0
    ) -> bool:
        """
        Wait for at least one instance to be ready.
        
        Args:
            timeout: Maximum time to wait in seconds
            consecutive: Number of consecutive successful /ready checks required
            check_interval: Interval between checks in seconds
        
        Returns:
            True if ready, False if timeout
        """
        start_time = time.time()
        success_count = 0
        
        logger.info(f"[GPU_POOL] Waiting for GPU workers to be ready (timeout={timeout}s)...")
        
        while time.time() - start_time < timeout:
            for instance in self.instances:
                try:
                    session = await self._get_session()
                    async with session.get(f"{instance.url}/ready", timeout=5.0) as resp:
                        if resp.status == 200:
                            success_count += 1
                            if success_count >= consecutive:
                                # Validate meta matches
                                await self._check_health(instance)
                                logger.info(f"[GPU_POOL] GPU worker ready: {instance.url}")
                                self._degraded = False
                                return True
                        else:
                            success_count = 0
                except Exception as e:
                    logger.debug(f"[GPU_POOL] Ready check failed for {instance.url}: {e}")
                    success_count = 0
            
            await asyncio.sleep(check_interval)
        
        logger.warning(f"[GPU_POOL] Timeout waiting for GPU workers (degraded mode)")
        self._degraded = True
        return False
    
    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        instance: Optional[WorkerInstance] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[int]]:
        """
        Make request with retry and backoff.
        
        Returns:
            (response_json, status_code) or (None, status_code) on failure
        """
        if instance is None:
            instance = self._get_next_instance()
        
        if instance is None:
            return None, 503
        
        session = await self._get_session()
        
        for attempt in range(self.max_retries):
            try:
                url = f"{instance.url}{endpoint}"
                async with session.request(
                    method,
                    url,
                    json=json_data,
                    timeout=self.timeout
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        instance.healthy = True
                        instance.consecutive_failures = 0
                        return data, 200
                    elif resp.status == 429:
                        # Rate limited - backoff
                        backoff = min(2 ** attempt, 5.0)
                        logger.warning(
                            f"[GPU_POOL] 429 from {instance.url}, backing off {backoff}s"
                        )
                        await asyncio.sleep(backoff)
                        continue
                    elif resp.status >= 500:
                        # Server error - retry with backoff
                        backoff = min(2 ** attempt, 5.0)
                        logger.warning(
                            f"[GPU_POOL] {resp.status} from {instance.url}, retrying in {backoff}s"
                        )
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        # Client error - don't retry
                        return None, resp.status
            except asyncio.TimeoutError:
                logger.warning(f"[GPU_POOL] Timeout from {instance.url} (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(min(2 ** attempt, 5.0))
                continue
            except Exception as e:
                logger.error(f"[GPU_POOL] Request error: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(min(2 ** attempt, 5.0))
                continue
        
        # All retries failed
        instance.healthy = False
        instance.consecutive_failures += 1
        return None, 500
    
    async def embed(
        self,
        texts: List[str],
        normalize: bool = False
    ) -> Optional[Any]:  # np.ndarray when available
        """
        Embed texts using GPU worker.
        
        Returns:
            numpy array of embeddings or None if degraded/unavailable
        """
        if self._degraded or not self.instances:
            return None
        
        data, status = await self._request_with_retry(
            "POST",
            "/embed",
            json_data={"texts": texts, "normalize": normalize}
        )
        
        if data and "vectors" in data:
            if np is None:
                raise RuntimeError("numpy not available")
            return np.array(data["vectors"], dtype=np.float32)
        else:
            logger.debug(f"[GPU_POOL] Embed failed (status={status}), degrading")
            return None
    
    async def rerank(
        self,
        query: str,
        docs: List[str],
        top_n: Optional[int] = None
    ) -> Optional[Tuple[List[int], List[float]]]:
        """
        Rerank documents using GPU worker.
        
        Returns:
            (indices, scores) tuple or None if degraded/unavailable
        """
        if self._degraded or not self.instances:
            return None
        
        data, status = await self._request_with_retry(
            "POST",
            "/rerank",
            json_data={"query": query, "docs": docs, "top_n": top_n}
        )
        
        if data and "indices" in data and "scores" in data:
            return (data["indices"], data["scores"])
        else:
            logger.debug(f"[GPU_POOL] Rerank failed (status={status}), degrading")
            return None


# Global pool instance
_gpu_pool: Optional[GPUWorkerPool] = None


def get_gpu_pool() -> Optional[GPUWorkerPool]:
    """Get global GPU worker pool."""
    return _gpu_pool


def initialize_gpu_pool(urls: Optional[List[str]] = None) -> Optional[GPUWorkerPool]:
    """
    Initialize global GPU worker pool.
    
    Args:
        urls: List of worker URLs (defaults to WORKER_URLS env var)
    
    Returns:
        GPUWorkerPool instance or None if no URLs provided
    """
    global _gpu_pool
    
    if urls is None:
        worker_urls = os.getenv("WORKER_URLS", "")
        if not worker_urls:
            logger.info("[GPU_POOL] WORKER_URLS not set, GPU worker disabled")
            return None
        urls = [url.strip() for url in worker_urls.split(",") if url.strip()]
    
    if not urls:
        logger.info("[GPU_POOL] No worker URLs provided, GPU worker disabled")
        return None
    
    _gpu_pool = GPUWorkerPool(urls)
    return _gpu_pool

