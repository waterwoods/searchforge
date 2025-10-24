# SurgeForge Retrieval MVP — Study Map
# 
# Legend: ★ SLA-critical   ★ CACHE   ★ RPS/Concurrency   ★ FASTPATH   ★ RETRY   ★ EVAL
# 
# Control Flow:
# FakeEmbedAPI → TokenBucket → AsyncBatchEmbedder → _batcher → _dispatch → retry loop
#     ↓              ↓              ↓                ↓          ↓           ↓
#  error rates    rate limit    batch queue    deadline    semaphore   backoff
#
# batch_embedder.py
"""
Async batch embedder with micro-batching, concurrency & RPS limits, retries, and
in-order fulfillment. Includes a deterministic FakeEmbedAPI for reproducible tests.

Usage (quick smoke):
    python batch_embedder.py
"""

import asyncio
import contextlib
import hashlib
import random
import statistics
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

# --------------------------
# Errors (simulated service)
# --------------------------
class RateLimitError(Exception): ...
class TransientError(Exception): ...
class ServerError(Exception): ...

# --------------------------
# Deterministic vector helper
# --------------------------
def _deterministic_vector(text: str, dim: int) -> List[float]:  # ★ EVAL: stable vectors for tests
    """
    Produce a deterministic pseudo-random vector in [0,1) per input string.
    Stable across runs for the same text & dim.
    """
    out: List[float] = []
    need = dim
    counter = 0
    while need > 0:
        h = hashlib.sha256(f"{text}::{counter}".encode()).digest()
        # turn bytes into floats
        for i in range(0, len(h), 4):
            if need == 0:
                break
            chunk = h[i : i + 4]
            val = int.from_bytes(chunk, "big") / 2**32  # [0,1)
            out.append(float(val))
            need -= 1
        counter += 1
    return out

# --------------------------
# Fake API (batch endpoint)
# --------------------------
class FakeEmbedAPI:
    """
    Simulated embedding service:
      - latency = base_ms + per_item_ms * batch + jitter
      - per-second RPS limit
      - transient & server errors
      - deterministic vectors (for stable tests)
    """
    def __init__(
        self,
        dim: int = 64,  # ★ SLA: vector dimension
        base_ms: int = 35,  # ★ SLA: base latency
        per_item_ms: int = 4,  # ★ SLA: per-item latency
        jitter_ms: int = 12,  # ★ SLA: random jitter
        rps_limit: int = 8,  # ★ RPS: requests per second
        transient_err_rate: float = 0.04,  # ★ RETRY: transient error rate
        server_err_rate: float = 0.01,  # ★ RETRY: server error rate
    ):
        self.dim = dim
        self.base_ms = base_ms
        self.per_item_ms = per_item_ms
        self.jitter_ms = jitter_ms
        self._rps_limit = rps_limit
        self._window_start = time.time()
        self._calls_in_window = 0
        self._window_sec = 1.0
        self.transient_err_rate = transient_err_rate
        self.server_err_rate = server_err_rate

    async def embed(self, batch: List[str]) -> List[List[float]]:
        # RPS window
        now = time.time()
        if now - self._window_start >= self._window_sec:  # ★ RPS: window reset
            self._window_start = now
            self._calls_in_window = 0
        self._calls_in_window += 1
        if self._calls_in_window > self._rps_limit:  # ★ RPS: rate limit check
            raise RateLimitError("rps exceeded")

        # random errors
        r = random.random()
        if r < self.server_err_rate:  # ★ RETRY: server error injection
            raise ServerError("5xx")
        if r < self.server_err_rate + self.transient_err_rate:  # ★ RETRY: transient error injection
            raise TransientError("transport/429")

        # latency model
        delay = (
            self.base_ms + self.per_item_ms * max(1, len(batch)) + random.randint(0, self.jitter_ms)  # ★ SLA: latency model
        ) / 1000
        await asyncio.sleep(delay)  # ★ SLA: simulated latency

        # deterministic vectors
        return [_deterministic_vector(x, self.dim) for x in batch]

# --------------------------
# Token bucket (RPS limit)
# --------------------------
class TokenBucket:
    def __init__(self, rate_per_sec: int, capacity: Optional[int] = None):
        self.rate = float(rate_per_sec)
        self.capacity = float(capacity or rate_per_sec)
        self.tokens = self.capacity
        self.ts = time.time()
        self._lock = asyncio.Lock()

    async def take(self, n: int = 1) -> None:
        async with self._lock:
            while True:
                now = time.time()
                elapsed = now - self.ts
                self.ts = now
                # refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)  # ★ RPS: token refill logic
                if self.tokens >= n:
                    self.tokens -= n
                    return
                # wait for enough tokens
                missing = n - self.tokens
                sleep_s = max(missing / self.rate, 0.001)  # ★ RPS: sleep calculation
                await asyncio.sleep(sleep_s)

# --------------------------
# Async Batch Embedder
# --------------------------
@dataclass
class EmbedRequest:
    text: str
    fut: asyncio.Future
    t0: float

class AsyncBatchEmbedder:
    """
    Features:
      - micro-batching (max_batch_size, max_batch_latency_ms)
      - concurrency limit (max_concurrency)
      - RPS limit (token bucket)
      - retries with exponential backoff + jitter (for 429/5xx/transient)
      - preserves output order
    """

    def __init__(
        self,
        api: FakeEmbedAPI,
        max_batch_size: int = 16,  # ★ SLA: batch size limit
        max_batch_latency_ms: int = 25,  # ★ SLA: batch timeout
        max_concurrency: int = 4,  # ★ RPS: concurrency limit
        rps_limit: int = 8,  # ★ RPS: rate limit
        max_retries: int = 5,  # ★ RETRY: max retry attempts
        retry_base_ms: int = 40,  # ★ RETRY: base backoff time
    ):
        self.api = api
        self.max_batch_size = max_batch_size
        self.max_batch_latency_ms = max_batch_latency_ms
        self._sem = asyncio.Semaphore(max_concurrency)  # ★ RPS: concurrency control
        self._bucket = TokenBucket(rps_limit, rps_limit)  # ★ RPS: rate limiting
        self.max_retries = max_retries
        self.retry_base_ms = retry_base_ms

        self._q: "asyncio.Queue[EmbedRequest]" = asyncio.Queue()  # ★ RPS: request queue
        self._bg = asyncio.create_task(self._batcher())  # ★ RPS: background batcher

    # Public API
    async def embed_one(self, text: str) -> List[float]:
        fut = asyncio.get_running_loop().create_future()
        await self._q.put(EmbedRequest(text=text, fut=fut, t0=time.time()))
        return await fut

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        futs = [asyncio.get_running_loop().create_future() for _ in texts]
        for t, f in zip(texts, futs):
            await self._q.put(EmbedRequest(text=t, fut=f, t0=time.time()))
        return await asyncio.gather(*futs)

    async def close(self):
        self._bg.cancel()
        with contextlib.suppress(Exception):
            await self._bg

    # Internals
    async def _batcher(self):
        batch: List[EmbedRequest] = []
        deadline: Optional[float] = None

        while True:
            try:
                timeout = None
                if batch and deadline is not None:
                    timeout = max(deadline - time.time(), 0)  # ★ SLA: deadline logic
                req: EmbedRequest = await asyncio.wait_for(self._q.get(), timeout=timeout)
                batch.append(req)
                if len(batch) == 1:
                    deadline = time.time() + self.max_batch_latency_ms / 1000
                if len(batch) >= self.max_batch_size:  # ★ SLA: batch flush on size
                    await self._dispatch(batch)
                    batch, deadline = [], None
            except asyncio.TimeoutError:
                if batch:
                    await self._dispatch(batch)  # ★ SLA: batch flush on timeout
                    batch, deadline = [], None

    async def _dispatch(self, batch: List[EmbedRequest]) -> None:
        await self._sem.acquire()  # ★ RPS: semaphore acquire
        await self._bucket.take(1)  # ★ RPS: token bucket take
        try:
            attempt = 0
            while True:
                attempt += 1
                try:
                    texts = [r.text for r in batch]
                    vecs = await self.api.embed(texts)
                    # fulfill in order
                    for r, v in zip(batch, vecs):  # ★ SLA: in-order fulfillment
                        if not r.fut.done():
                            r.fut.set_result(v)
                    return
                except (RateLimitError, TransientError, ServerError) as e:
                    if attempt <= self.max_retries:  # ★ RETRY: retry loop
                        backoff = (self.retry_base_ms * (2 ** (attempt - 1)) + random.randint(0, 20)) / 1000  # ★ RETRY: exp backoff + jitter
                        await asyncio.sleep(backoff)
                        continue
                    # exhaust retries: fail all remaining
                    for r in batch:
                        if not r.fut.done():
                            r.fut.set_exception(e)
                    return
                except Exception as e:
                    for r in batch:
                        if not r.fut.done():
                            r.fut.set_exception(e)
                    return
        finally:
            self._sem.release()  # ★ RPS: semaphore release

# --------------------------
# Quick benchmark (optional)
# --------------------------
async def _bench(n: int = 200):
    api = FakeEmbedAPI(rps_limit=8, base_ms=35, per_item_ms=4, jitter_ms=8)
    be = AsyncBatchEmbedder(
        api,
        max_batch_size=16,
        max_batch_latency_ms=25,
        max_concurrency=4,
        rps_limit=8,
    )

    texts = [f"doc-{i}" for i in range(n)]
    lat = [0.0] * n

    async def one(i: int) -> Tuple[int, float]:
        s = time.time()
        v = await be.embed_one(texts[i])
        assert len(v) == api.dim
        return i, time.time() - s

    async def record(i):
        _, l = await one(i)
        lat[i] = l

    t0 = time.time()
    await asyncio.gather(*(record(i) for i in range(n)))
    t1 = time.time()

    p50 = statistics.median(lat)
    p95 = statistics.quantiles(lat, n=100)[94]
    print(
        f"n={n} total={t1-t0:.3f}s p50={p50*1000:.1f}ms p95={p95*1000:.1f}ms "
        f"max={max(lat)*1000:.1f}ms"
    )

    # SLA gate (aligns with earlier spec)
    assert p95 * 1000 < 200, "p95 must be < 200ms"  # ★ EVAL: p95<200ms assertion

if __name__ == "__main__":
    asyncio.run(_bench(200))

# Study Checklist
# Numbers to remember:
#   batch: max_batch_size=16, max_batch_latency_ms=25, max_concurrency=4
#   limits: rps_limit=8, max_retries=5, retry_base_ms=40
#   eval gates: p95<200ms (embedder)
# 3 trade-offs (one line each):
#   HNSW vs PQ: HNSW faster search, PQ smaller memory
#   BM25 vs vector: BM25 exact matches, vector semantic similarity
#   ONNX vs Torch: ONNX faster inference, Torch more flexible
# Grep cheats:
#   grep -n "★" -n
#   grep -n "\[FASTPATH\]\|\[RPS\]\|\[CACHE\]"