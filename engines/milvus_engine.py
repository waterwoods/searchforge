#!/usr/bin/env python3
"""
Milvus Vector Engine - Second Lane Implementation

Provides high-performance vector search using Milvus with HNSW index.
Features:
- HNSW indexing (M=16, ef=64)
- Search/Upsert/Prewarm/Health operations
- Compatible with existing vector search interface
- Fallback to Qdrant on errors
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Delay import of SentenceTransformer until actually needed
# This allows the API to start without sentence-transformers installed
# Embedding should be done via GPU/CPU worker service instead

try:
    from pymilvus import (
        connections,
        Collection,
        CollectionSchema,
        FieldSchema,
        DataType,
        utility
    )
    MILVUS_AVAILABLE = True
except ImportError:
    logger.warning("pymilvus not installed. Milvus engine unavailable.")
    MILVUS_AVAILABLE = False


class MilvusEngine:
    """
    Milvus vector search engine with HNSW indexing.
    
    Configuration:
    - MILVUS_HOST: Milvus server host (default: localhost)
    - MILVUS_PORT: Milvus server port (default: 19530)
    - MILVUS_COLLECTION: Collection name (default: fiqa)
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        collection_name: str = "fiqa",
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        dim: int = 384
    ):
        """
        Initialize Milvus engine.
        
        Args:
            host: Milvus server host
            port: Milvus server port
            collection_name: Name of the collection
            embedding_model_name: SentenceTransformer model name
            dim: Vector dimension (384 for all-MiniLM-L6-v2)
        """
        if not MILVUS_AVAILABLE:
            raise ImportError("pymilvus is required for MilvusEngine")
        
        import os
        self.host = host or os.getenv("MILVUS_HOST", "localhost")
        self.port = port or int(os.getenv("MILVUS_PORT", "19530"))
        self.collection_name = collection_name
        self.dim = dim
        self.embedding_model_name = embedding_model_name
        
        # Initialize embedding model (lazy import to avoid heavy dependencies in API)
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer(embedding_model_name)
        except ImportError:
            logger.warning("sentence-transformers not available. MilvusEngine requires embedding via external service.")
            raise ImportError("sentence-transformers is required for MilvusEngine. Use GPU worker service for embeddings.")
        
        # Connection state
        self._connected = False
        self._collection = None
        
        # HNSW parameters
        self.hnsw_m = 16  # Number of bi-directional links
        self.hnsw_ef_construction = 64  # Construction time ef
        self.hnsw_ef_search = 64  # Search time ef (default)
        
        logger.info(f"MilvusEngine initialized: {self.host}:{self.port}/{collection_name}")
    
    def connect(self) -> bool:
        """
        Connect to Milvus server.
        
        Returns:
            True if connection successful
        """
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            self._connected = True
            logger.info(f"Connected to Milvus: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            self._connected = False
            return False
    
    def health(self) -> Dict[str, Any]:
        """
        Check Milvus health status.
        
        Returns:
            Health status dict with ok, latency_ms, collections, etc.
        """
        start_time = time.perf_counter()
        
        try:
            if not self._connected:
                self.connect()
            
            # List collections as health check
            collections = utility.list_collections()
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            return {
                "ok": True,
                "backend": "milvus",
                "host": self.host,
                "port": self.port,
                "latency_ms": round(latency_ms, 2),
                "collections": collections,
                "collection_exists": self.collection_name in collections
            }
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Milvus health check failed: {e}")
            return {
                "ok": False,
                "backend": "milvus",
                "error": str(e),
                "latency_ms": round(latency_ms, 2)
            }
    
    def _create_collection(self) -> bool:
        """
        Create collection with schema if not exists.
        
        Schema:
        - id: int64 (primary key, auto_id)
        - vec: float_vector[dim]
        - text: varchar (optional, max 65535)
        - metadata: varchar (optional, max 65535, JSON string)
        
        Returns:
            True if collection created or already exists
        """
        try:
            if utility.has_collection(self.collection_name):
                logger.info(f"Collection '{self.collection_name}' already exists")
                self._collection = Collection(self.collection_name)
                return True
            
            # Define schema
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="vec", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535)
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description=f"Vector collection for {self.collection_name}"
            )
            
            # Create collection
            self._collection = Collection(
                name=self.collection_name,
                schema=schema
            )
            
            logger.info(f"Created collection '{self.collection_name}'")
            
            # Create HNSW index
            index_params = {
                "metric_type": "L2",  # or "IP" for inner product
                "index_type": "HNSW",
                "params": {
                    "M": self.hnsw_m,
                    "efConstruction": self.hnsw_ef_construction
                }
            }
            
            self._collection.create_index(
                field_name="vec",
                index_params=index_params
            )
            
            logger.info(f"Created HNSW index: M={self.hnsw_m}, ef={self.hnsw_ef_construction}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False
    
    def upsert(
        self,
        vectors: List[List[float]],
        texts: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Insert or update vectors in collection.
        
        Args:
            vectors: List of embedding vectors
            texts: Optional list of text content
            metadatas: Optional list of metadata dicts
        
        Returns:
            Result dict with insert_count, time_ms
        """
        start_time = time.perf_counter()
        
        try:
            if not self._connected:
                self.connect()
            
            if self._collection is None:
                self._create_collection()
            
            # Prepare data
            n = len(vectors)
            data = [
                vectors,  # vec field
                texts or [""] * n,  # text field
                [str(m or {}) for m in (metadatas or [{}] * n)]  # metadata as JSON string
            ]
            
            # Insert data
            result = self._collection.insert(data)
            
            # Flush to persist
            self._collection.flush()
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            logger.info(f"Upserted {n} vectors in {elapsed_ms:.2f}ms")
            
            return {
                "ok": True,
                "insert_count": n,
                "time_ms": round(elapsed_ms, 2)
            }
            
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Upsert failed: {e}")
            return {
                "ok": False,
                "error": str(e),
                "time_ms": round(elapsed_ms, 2)
            }
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        ef_search: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            ef_search: HNSW search parameter (higher = more accurate, slower)
            metadata_filter: Optional metadata filter (not fully supported yet)
            collection_name: Optional collection name override
        
        Returns:
            Tuple of (results, debug_info)
            - results: List of dicts with id, text, metadata, score, distance
            - debug_info: Search metadata (latency, params, etc.)
        """
        start_time = time.perf_counter()
        
        # Use provided collection_name or fall back to default
        target_collection = collection_name or self.collection_name
        
        try:
            if not self._connected:
                self.connect()
            
            # Get or create collection
            if self._collection is None or self._collection.name != target_collection:
                if utility.has_collection(target_collection):
                    self._collection = Collection(target_collection)
                    logger.info(f"Using existing collection: {target_collection}")
                else:
                    # Collection doesn't exist, try default behavior
                    self._create_collection()
            
            # Load collection to memory if not loaded
            if not self._collection.has_index():
                raise ValueError(f"Collection '{target_collection}' has no index")
            
            self._collection.load()
            
            # Generate query embedding
            query_vector = self.embedding_model.encode(query).tolist()
            
            # Set search parameters
            search_params = {
                "metric_type": "L2",
                "params": {
                    "ef": ef_search or self.hnsw_ef_search
                }
            }
            
            # Execute search (request only fields that exist in schema)
            search_results = self._collection.search(
                data=[query_vector],
                anns_field="vec",
                param=search_params,
                limit=top_k,
                output_fields=["text", "doc_id"]  # ✅ Use doc_id instead of metadata
            )
            
            # Parse results
            results = []
            for hits in search_results:
                for hit in hits:
                    results.append({
                        "id": hit.entity.get("doc_id", str(hit.id)),  # Use doc_id from entity
                        "text": hit.entity.get("text", ""),
                        "metadata": {},  # Empty metadata for now
                        "score": float(1.0 / (1.0 + hit.distance)),  # Convert L2 distance to similarity score
                        "distance": float(hit.distance)
                    })
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            debug_info = {
                "latency_ms": round(elapsed_ms, 2),
                "backend": "milvus",
                "collection": self.collection_name,
                "top_k": top_k,
                "ef_search": ef_search or self.hnsw_ef_search,
                "result_count": len(results)
            }
            
            logger.debug(f"Search completed: {len(results)} results in {elapsed_ms:.2f}ms")
            
            return results, debug_info
            
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Search failed: {e}")
            
            debug_info = {
                "latency_ms": round(elapsed_ms, 2),
                "backend": "milvus",
                "error": str(e),
                "result_count": 0
            }
            
            return [], debug_info
    
    def prewarm(self, num_queries: int = 100, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Prewarm the collection by loading it into memory and running sample queries.
        
        Args:
            num_queries: Number of warmup queries to run
            collection_name: Collection to prewarm (uses default if None)
        
        Returns:
            Prewarm result with avg_latency_ms, queries_run, etc.
        """
        start_time = time.perf_counter()
        
        try:
            if not self._connected:
                self.connect()
            
            if self._collection is None:
                self._create_collection()
            
            # Load collection
            self._collection.load()
            
            logger.info(f"Prewarming collection '{self.collection_name}' with {num_queries} queries...")
            
            # Run sample queries
            latencies = []
            sample_queries = [
                "financial advisor",
                "investment strategy",
                "retirement planning",
                "stock market",
                "mutual funds"
            ]
            
            for i in range(num_queries):
                query = sample_queries[i % len(sample_queries)]
                _, debug = self.search(query, top_k=10)
                latencies.append(debug.get("latency_ms", 0))
            
            avg_latency = np.mean(latencies) if latencies else 0
            p95_latency = np.percentile(latencies, 95) if latencies else 0
            
            total_time_ms = (time.perf_counter() - start_time) * 1000
            
            logger.info(f"Prewarm complete: avg={avg_latency:.2f}ms, p95={p95_latency:.2f}ms")
            
            return {
                "ok": True,
                "queries_run": num_queries,
                "avg_latency_ms": round(avg_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "total_time_ms": round(total_time_ms, 2)
            }
            
        except Exception as e:
            total_time_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Prewarm failed: {e}")
            return {
                "ok": False,
                "error": str(e),
                "total_time_ms": round(total_time_ms, 2)
            }
    
    def close(self):
        """Disconnect from Milvus."""
        if self._connected:
            connections.disconnect(alias="default")
            self._connected = False
            logger.info("Disconnected from Milvus")

