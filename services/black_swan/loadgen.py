"""
Black Swan Async - Load Generator

Async load generator using httpx and asyncio.
Supports QPS control, burst patterns, concurrency limits, and query diversity.
"""

import asyncio
import time
import random
import logging
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)


class QueryBank:
    """
    Query bank manager for diverse query selection.
    
    Supports round-robin (unique) or random selection from FIQA queries.
    """
    
    def __init__(self, query_file: Optional[str] = None, unique: bool = True):
        """
        Initialize query bank.
        
        Args:
            query_file: Path to query file (one query per line)
            unique: Use round-robin (True) or random (False) selection
        """
        self.queries: List[str] = []
        self.unique = unique
        self.index = 0
        
        # Default query file path
        if query_file is None:
            project_root = Path(__file__).parent.parent.parent
            query_file = str(project_root / "datasets" / "fiqa" / "queries_test.txt")
        
        # Load queries
        try:
            with open(query_file, 'r', encoding='utf-8') as f:
                self.queries = [line.strip() for line in f if line.strip()]
            
            if not self.queries:
                # Fallback to dummy queries
                self.queries = [f"test query {i}" for i in range(100)]
                logger.warning("[BS:LOADGEN] Query file empty, using dummy queries")
            else:
                logger.info(f"[BS:LOADGEN] Loaded {len(self.queries)} queries from {query_file}")
        
        except Exception as e:
            # Fallback to dummy queries
            self.queries = [f"test query {i}" for i in range(100)]
            logger.warning(f"[BS:LOADGEN] Failed to load queries: {e}, using dummy queries")
    
    def set_ground_truth_queries(self, queries_dict: Dict[str, str]):
        """Set queries from ground truth data."""
        self.queries = list(queries_dict.values())
        logger.info(f"[BS:LOADGEN] Set {len(self.queries)} ground truth queries")
    
    def next(self) -> str:
        """Get next query."""
        if self.unique:
            # Round-robin
            query = self.queries[self.index % len(self.queries)]
            self.index += 1
            return query
        else:
            # Random
            return random.choice(self.queries)


class LoadGenerator:
    """
    Async load generator with QPS control and metrics collection.
    
    Features:
    - Precise QPS control via asyncio timing
    - Concurrency limiting
    - Query diversity (round-robin or random)
    - Cache bypass (nocache parameter)
    - Real-time metrics aggregation
    """
    
    def __init__(
        self,
        target_url: str,
        qps: int,
        duration: int,
        concurrency: int = 16,
        unique_queries: bool = True,
        bypass_cache: bool = True,
        candidate_k: Optional[int] = None,
        rerank_top_k: Optional[int] = None,
        query_bank: Optional[QueryBank] = None,
        phase: str = "unknown"
    ):
        """
        Initialize load generator.
        
        Args:
            target_url: Target endpoint URL
            qps: Target queries per second
            duration: Test duration in seconds
            concurrency: Max concurrent requests
            unique_queries: Use unique queries (round-robin)
            bypass_cache: Add nocache parameters
            candidate_k: Candidate K for retrieval (optional)
            rerank_top_k: Rerank top K (optional)
            query_bank: Query bank instance (optional, will create if None)
            phase: Current test phase (for QA feed logging)
        """
        self.target_url = target_url
        self.qps = qps
        self.duration = duration
        self.concurrency = concurrency
        self.unique_queries = unique_queries
        self.bypass_cache = bypass_cache
        self.candidate_k = candidate_k
        self.rerank_top_k = rerank_top_k
        self.phase = phase
        
        # Query bank
        self.query_bank = query_bank or QueryBank(unique=unique_queries)
        
        # Ground truth cache for Recall@10 calculation
        self._qrels_cache = None
        self._queries_cache = None
        self._valid_query_ids = None  # Cache query IDs that have ground truth
        
        # Metrics tracking
        self.metrics = {
            "count": 0,
            "errors": 0,
            "latencies": [],
            "start_time": 0,
            "end_time": 0,
            "consecutive_errors": 0,
            "circuit_open": False,
            "circuit_opened_at": 0
        }
        
        # Control flags
        self.running = False
        self.stopped = False
        
        # Circuit breaker thresholds
        self.circuit_error_threshold = 10  # 10 consecutive errors
        self.circuit_cooldown_sec = 10     # 10s cooldown
        
        # Semaphore for concurrency control
        self.semaphore = asyncio.Semaphore(concurrency)
        
        # QA feed sampling (5% of requests)
        self.qa_feed_sample_rate = 0.05
    
    async def _make_request(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """
        Make a single HTTP request.
        
        Returns:
            Result dict with success, latency_ms, query, answer, and optional error
        """
        start = time.time()
        
        try:
            # Build request payload
            query = self.query_bank.next()
            
            payload = {
                "query": query,
                "top_k": 10
            }
            
            # Add heavy params if specified
            if self.candidate_k is not None:
                payload["candidate_k"] = self.candidate_k
            
            if self.rerank_top_k is not None:
                payload["rerank_top_k"] = self.rerank_top_k
            
            # Add cache bypass params
            params = {}
            if self.bypass_cache:
                params["nocache"] = int(time.time() * 1000)
                params["rand"] = random.randint(1000, 9999)
            
            # Make request
            response = await client.post(
                self.target_url,
                json=payload,
                params=params,
                timeout=30.0
            )
            
            latency_ms = (time.time() - start) * 1000
            
            # Parse response to extract answer and doc_ids for recall calculation
            answer = ""
            hit_from = "qdrant"
            doc_ids = []
            recall_at_10 = None
            
            try:
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        # Extract answer from first result
                        answers = data.get("answers", [])
                        if answers and len(answers) > 0:
                            answer = str(answers[0])[:200]  # Truncate to 200 chars
                        
                        # Extract document IDs from doc_ids field (already provided by search endpoint)
                        doc_ids_raw = data.get("doc_ids", [])
                        if doc_ids_raw:
                            doc_ids = [str(doc_id) for doc_id in doc_ids_raw]
                        
                        # Check if mock mode
                        if data.get("mock_mode"):
                            hit_from = "mock"
                        
                        # Calculate real recall if we have doc_ids
                        if doc_ids:
                            recall_at_10 = self._calculate_recall_at_10(query, doc_ids)
            except Exception as parse_err:
                # Log parse error but don't fail the request
                import logging
                logging.debug(f"Response parse error: {parse_err}")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "latency_ms": latency_ms,
                    "query": query,
                    "answer": answer,
                    "hit_from": hit_from,
                    "topk": payload.get("top_k", 10),
                    "candidate_k": self.candidate_k,
                    "rerank_top_k": self.rerank_top_k,
                    "recall_at_10": recall_at_10
                }
            else:
                return {
                    "success": False,
                    "latency_ms": latency_ms,
                    "query": query,
                    "answer": "",
                    "hit_from": hit_from,
                    "topk": payload.get("top_k", 10),
                    "candidate_k": self.candidate_k,
                    "rerank_top_k": self.rerank_top_k,
                    "error": f"HTTP {response.status_code}",
                    "recall_at_10": None
                }
        
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            return {
                "success": False,
                "latency_ms": latency_ms,
                "query": query if 'query' in locals() else "unknown",
                "answer": "",
                "hit_from": "error",
                "topk": 10,
                "candidate_k": self.candidate_k,
                "rerank_top_k": self.rerank_top_k,
                "error": str(e),
                "recall_at_10": None
            }
    
    async def _worker(self, client: httpx.AsyncClient) -> None:
        """Worker task that makes requests."""
        while self.running and not self.stopped:
            # Check circuit breaker
            if self._check_circuit_breaker():
                await asyncio.sleep(0.5)  # Wait if circuit is open
                continue
            
            async with self.semaphore:
                if not self.running or self.stopped:
                    break
                
                # Make request
                result = await self._make_request(client)
                
                # Track metrics
                self.metrics["count"] += 1
                self.metrics["latencies"].append(result["latency_ms"])
                
                if not result["success"]:
                    self.metrics["errors"] += 1
                    self.metrics["consecutive_errors"] += 1
                    
                    # Check if circuit breaker should trip
                    if self.metrics["consecutive_errors"] >= self.circuit_error_threshold:
                        self._trip_circuit_breaker()
                else:
                    # Reset consecutive errors on success
                    self.metrics["consecutive_errors"] = 0
                
                # Push to core metrics sink (for P95/Recall charts)
                try:
                    from core.metrics import metrics_sink
                    if metrics_sink and result["success"]:
                        metrics_sink.push({
                            "ts": int(time.time() * 1000),  # Timestamp in ms
                            "latency_ms": result["latency_ms"],
                            "recall_at10": result.get("recall_at_10"),  # Real recall from ground truth
                            "mode": self.phase,
                            "candidate_k": self.candidate_k,
                            "rerank_hit": 1 if result.get("rerank_top_k", 0) > 0 else 0,
                            "cache_hit": 1 if result.get("hit_from") == "cache" else 0,
                        })
                except Exception as e:
                    # Silent failure - don't break the test
                    logger.debug(f"[BS:LOADGEN] Metrics push failed: {e}")
                
                # Log to QA feed (sampled)
                if random.random() < self.qa_feed_sample_rate and result["success"]:
                    await self._log_qa_feed(result)
    
    def _calculate_recall_at_10(self, query: str, doc_ids: List[str]) -> Optional[float]:
        """
        Calculate real Recall@10 using ground truth data.
        
        Args:
            query: Search query text
            doc_ids: List of retrieved document IDs
            
        Returns:
            Recall@10 value (0.0-1.0) or None if not calculable
        """
        try:
            # Load ground truth data (cache it for performance)
            if self._qrels_cache is None:
                self._load_ground_truth()
            
            if not self._qrels_cache or not self._queries_cache:
                return None
            
            # Find query_id for this query text
            query_id = None
            for q_id, q_text in self._queries_cache.items():
                if q_text.lower().strip() == query.lower().strip():
                    query_id = q_id
                    break
            
            if not query_id or query_id not in self._qrels_cache:
                return None
            
            # Get relevant documents for this query
            relevant_docs = self._qrels_cache[query_id]
            if not relevant_docs:
                return None
            
            # Normalize doc IDs for comparison
            normalized_retrieved = {str(doc_id).strip() for doc_id in doc_ids[:10]}
            normalized_relevant = {str(doc_id).strip() for doc_id in relevant_docs}
            
            # Calculate hits
            hits = len(normalized_retrieved & normalized_relevant)
            
            # Recall@10 = hits / min(10, |relevant|)
            return hits / min(10, len(relevant_docs))
            
        except Exception as e:
            # Log error for debugging
            import logging
            logging.warning(f"[BS:LOADGEN] Recall calculation failed for query '{query}' with doc_ids {doc_ids}: {e}")
            return None
    
    def _load_ground_truth(self):
        """Load ground truth data (qrels and queries)."""
        try:
            # Try to load from data directory
            data_dir = Path(__file__).parent.parent.parent / "data" / "fiqa"
            
            # Load qrels first to get valid query IDs
            qrels_file = data_dir / "qrels" / "test.tsv"
            valid_query_ids = set()
            if qrels_file.exists():
                self._qrels_cache = {}
                with open(qrels_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("query-id"):  # Skip header
                            continue
                        parts = line.strip().split('\t')
                        if len(parts) >= 3:
                            query_id, doc_id, score = parts[0], parts[1], parts[2]
                            if score == "1":  # Only relevant docs (score=1)
                                valid_query_ids.add(query_id)
                                if query_id not in self._qrels_cache:
                                    self._qrels_cache[query_id] = []
                                self._qrels_cache[query_id].append(doc_id)
            
            # Load only queries that have ground truth
            queries_file = data_dir / "queries.jsonl"
            if queries_file.exists():
                self._queries_cache = {}
                with open(queries_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        data = json.loads(line.strip())
                        query_id = data.get("_id")
                        if query_id in valid_query_ids:  # Only load queries with ground truth
                            self._queries_cache[query_id] = data.get("text", "")
                
                self._valid_query_ids = list(valid_query_ids)
            
            import logging
            logging.info(f"[BS:LOADGEN] Loaded {len(self._queries_cache or {})} queries and {len(self._qrels_cache or {})} query-doc mappings")
            logging.info(f"[BS:LOADGEN] Sample queries: {list(self._queries_cache.keys())[:5] if self._queries_cache else []}")
            logging.info(f"[BS:LOADGEN] Sample qrels: {list(self._qrels_cache.keys())[:5] if self._qrels_cache else []}")
            
            # Update query bank with ground truth queries
            if self._queries_cache and hasattr(self, 'query_bank'):
                self.query_bank.set_ground_truth_queries(self._queries_cache)
            
        except Exception as e:
            import logging
            logging.warning(f"[BS:LOADGEN] Failed to load ground truth: {e}")
            self._qrels_cache = {}
            self._queries_cache = {}

    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker is open."""
        if not self.metrics["circuit_open"]:
            return False
        
        # Check if cooldown period has passed
        elapsed = time.time() - self.metrics["circuit_opened_at"]
        if elapsed >= self.circuit_cooldown_sec:
            self._close_circuit_breaker()
            return False
        
        return True
    
    def _trip_circuit_breaker(self) -> None:
        """Trip the circuit breaker."""
        if not self.metrics["circuit_open"]:
            self.metrics["circuit_open"] = True
            self.metrics["circuit_opened_at"] = time.time()
            logger.warning(
                f"[BS:LOADGEN] Circuit breaker OPEN: {self.metrics['consecutive_errors']} "
                f"consecutive errors (cooldown={self.circuit_cooldown_sec}s)"
            )
    
    def _close_circuit_breaker(self) -> None:
        """Close the circuit breaker."""
        if self.metrics["circuit_open"]:
            self.metrics["circuit_open"] = False
            self.metrics["consecutive_errors"] = 0
            logger.info("[BS:LOADGEN] Circuit breaker CLOSED: resuming requests")
    
    async def _log_qa_feed(self, result: Dict[str, Any]) -> None:
        """
        Log request to QA feed (async, non-blocking).
        
        Args:
            result: Request result with query, answer, latency, etc.
        """
        try:
            from .storage import get_storage
            
            storage = get_storage()
            
            # Build QA feed item
            item = {
                "ts": int(time.time()),
                "mode": self.phase,
                "latency_ms": round(result.get("latency_ms", 0), 2),
                "hit_from": result.get("hit_from", "unknown"),
                "topk": result.get("topk", 10),
                "rerank_k": result.get("rerank_top_k", 0) or 0,
                "query": result.get("query", "")[:100],  # Truncate
                "answer": result.get("answer", "")[:200],  # Truncate
            }
            
            # Append to storage (non-blocking)
            storage.append_qa_feed(item)
            
        except Exception as e:
            # Silent failure - don't let QA logging break the test
            logger.debug(f"[BS:LOADGEN] QA feed log failed: {e}")
    
    async def run(self) -> Dict[str, Any]:
        """
        Run load generator for specified duration.
        
        Returns:
            Final metrics dictionary
        """
        self.running = True
        self.stopped = False
        self.metrics["start_time"] = time.time()
        
        logger.info(f"[BS:LOADGEN] Starting: {self.qps} QPS for {self.duration}s (concurrency={self.concurrency})")
        
        # Create HTTP client
        async with httpx.AsyncClient() as client:
            # Calculate inter-request interval
            interval = 1.0 / self.qps if self.qps > 0 else 0.1
            
            # Calculate number of workers (at least QPS/10, up to concurrency)
            num_workers = min(self.concurrency, max(1, self.qps // 10))
            
            # Start workers
            workers = [asyncio.create_task(self._worker(client)) for _ in range(num_workers)]
            
            # Run for specified duration
            end_time = time.time() + self.duration
            
            while time.time() < end_time and not self.stopped:
                await asyncio.sleep(min(interval, 0.1))
            
            # Stop workers
            self.running = False
            
            # Wait for workers to finish
            await asyncio.gather(*workers, return_exceptions=True)
        
        self.metrics["end_time"] = time.time()
        
        # Calculate final metrics
        return self.get_metrics()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics.
        
        Returns:
            Metrics dictionary with count, errors, p50, p95, etc.
        """
        count = self.metrics["count"]
        errors = self.metrics["errors"]
        latencies = self.metrics["latencies"]
        
        if not latencies:
            return {
                "count": 0,
                "errors": 0,
                "error_rate": 0.0,
                "qps": 0.0,
                "p50_ms": None,
                "p95_ms": None,
                "p99_ms": None,
                "max_ms": None
            }
        
        # Calculate percentiles
        sorted_latencies = sorted(latencies)
        p50_ms = sorted_latencies[int(len(sorted_latencies) * 0.50)]
        p95_ms = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99_ms = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        max_ms = max(latencies)
        
        # Calculate QPS
        elapsed = self.metrics["end_time"] - self.metrics["start_time"]
        qps = count / elapsed if elapsed > 0 else 0.0
        
        # Calculate error rate
        error_rate = errors / count if count > 0 else 0.0
        
        return {
            "count": count,
            "errors": errors,
            "error_rate": round(error_rate, 4),
            "qps": round(qps, 2),
            "p50_ms": round(p50_ms, 2),
            "p95_ms": round(p95_ms, 2),
            "p99_ms": round(p99_ms, 2),
            "max_ms": round(max_ms, 2),
            "circuit_open": self.metrics.get("circuit_open", False),
            "consecutive_errors": self.metrics.get("consecutive_errors", 0)
        }
    
    async def stop(self) -> None:
        """Stop load generator gracefully."""
        logger.info("[BS:LOADGEN] Stopping...")
        self.stopped = True
        self.running = False

