#!/usr/bin/env python3
"""
v12_make_silver_qrels.py - Generate silver qrels for FIQA datasets

Generates silver qrels using BM25 + vector retrieval with thresholding.

Usage:
    poetry run python scripts/v12_make_silver_qrels.py --dataset fiqa_10k_v1
    poetry run python scripts/v12_make_silver_qrels.py --dataset fiqa_50k_v1
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

import orjson
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


def find_repo_root() -> Path:
    """Find repository root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def get_qdrant_client(url: str) -> QdrantClient:
    """Create Qdrant client."""
    if url.startswith("http://") or url.startswith("https://"):
        url_parts = url.replace("http://", "").replace("https://", "").split(":")
        host = url_parts[0] if url_parts else "localhost"
        port = int(url_parts[1]) if len(url_parts) > 1 else 6333
        return QdrantClient(host=host, port=port)
    else:
        return QdrantClient(url=url)


def tokenize(text: str) -> List[str]:
    """Consistent tokenization for BM25."""
    if not text:
        return []
    text_lower = text.lower()
    tokens = re.findall(r'\b\w+\b', text_lower)
    return tokens


def load_corpus_for_bm25(corpus_path: Path) -> Tuple[List[Dict[str, str]], BM25Okapi, Dict[str, int]]:
    """
    Load corpus for BM25 indexing.
    
    Returns:
        (docs, bm25_index, doc_id_to_idx)
    """
    print(f"[BM25] Loading corpus from {corpus_path}...")
    docs = []
    doc_id_to_idx = {}
    
    with open(corpus_path, "rb") as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            data = orjson.loads(line)
            doc_id = data.get("doc_id", "")
            title = data.get("title", "")
            text = data.get("text", "")
            
            if doc_id:
                combined_text = f"{title} {text}".strip()
                docs.append({
                    "doc_id": doc_id,
                    "text": combined_text,
                })
                doc_id_to_idx[doc_id] = idx
    
    print(f"[BM25] Loaded {len(docs)} documents")
    
    # Build BM25 index
    print(f"[BM25] Building BM25 index...")
    tokenized_corpus = [tokenize(doc["text"]) for doc in docs]
    bm25_index = BM25Okapi(tokenized_corpus)
    print(f"[BM25] BM25 index ready")
    
    return docs, bm25_index, doc_id_to_idx


def load_queries(queries_path: Path) -> Dict[str, str]:
    """Load queries from JSON or JSONL file."""
    queries = {}
    
    if not queries_path.exists():
        print(f"[WARN] Queries file not found: {queries_path}")
        return queries
    
    print(f"[QUERIES] Loading queries from {queries_path}...")
    
    try:
        if queries_path.suffix == ".json":
            with open(queries_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        qid = item.get("_id") or item.get("id")
                        text = item.get("text") or item.get("query")
                        if qid and text:
                            queries[str(qid)] = text
                elif isinstance(data, dict):
                    for qid, text in data.items():
                        queries[str(qid)] = text
        else:  # JSONL
            with open(queries_path, "rb") as f:
                for line in f:
                    if not line.strip():
                        continue
                    item = orjson.loads(line)
                    qid = item.get("_id") or item.get("id")
                    text = item.get("text") or item.get("query")
                    if qid and text:
                        queries[str(qid)] = text
        
        print(f"[QUERIES] Loaded {len(queries)} queries")
    except Exception as e:
        print(f"[ERROR] Failed to load queries: {e}")
        sys.exit(1)
    
    return queries


def bm25_search(
    bm25_index: BM25Okapi,
    docs: List[Dict[str, str]],
    query: str,
    top_k: int,
) -> List[Tuple[str, float, int]]:
    """
    BM25 search.
    
    Returns:
        List of (doc_id, score, rank) tuples
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    
    scores = bm25_index.get_scores(query_tokens)
    
    # Create (doc_id, score, idx) tuples
    results = []
    for idx, (doc, score) in enumerate(zip(docs, scores)):
        if score > 0:
            results.append((doc["doc_id"], float(score), idx))
    
    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def vector_search(
    client: QdrantClient,
    collection_name: str,
    query: str,
    top_k: int,
    embedding_model,
) -> List[Tuple[str, float]]:
    """
    Vector search using Qdrant.
    
    Returns:
        List of (doc_id, score) tuples
    """
    try:
        # Encode query using embedding model
        query_vector = embedding_model.encode(query).tolist()
        
        # Search in Qdrant
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
        )
        
        # Extract doc_id and score
        vec_results = []
        for hit in results:
            payload = hit.payload or {}
            doc_id = payload.get("doc_id") or str(hit.id)
            score = float(hit.score)  # Cosine similarity score
            vec_results.append((doc_id, score))
        
        return vec_results
    except Exception as e:
        print(f"[WARN] Vector search failed: {e}")
        return []


def generate_silver_qrels(
    queries: Dict[str, str],
    bm25_index: BM25Okapi,
    docs: List[Dict[str, str]],
    doc_id_to_idx: Dict[str, int],
    client: QdrantClient,
    collection_name: str,
    bm25_topk: int,
    vec_topk: int,
    cos_th: float,
    bm25_k: int,
    embedding_model,
) -> Dict[str, Set[str]]:
    """
    Generate silver qrels for all queries.
    
    Returns:
        Dict mapping query_id to set of relevant doc_ids
    """
    qrels = defaultdict(set)
    
    print(f"[QRELS] Generating silver qrels for {len(queries)} queries...")
    print(f"  BM25 top-k: {bm25_topk}, Vector top-k: {vec_topk}")
    print(f"  Thresholds: cosine >= {cos_th}, BM25 rank <= {bm25_k}")
    
    for qid, query_text in tqdm(queries.items(), desc="Processing queries"):
        # BM25 retrieval
        bm25_results = bm25_search(bm25_index, docs, query_text, bm25_topk)
        
        # Vector retrieval
        if embedding_model is not None:
            vec_results = vector_search(client, collection_name, query_text, vec_topk, embedding_model)
        else:
            vec_results = []
        
        # Apply silver labeling rules
        relevant_docs = set()
        
        # Rule 1: BM25 rank <= bm25_k
        for rank, (doc_id, score, _) in enumerate(bm25_results, 1):
            if rank <= bm25_k:
                relevant_docs.add(doc_id)
        
        # Rule 2: Vector cosine >= cos_th (if implemented)
        for doc_id, score in vec_results:
            if score >= cos_th:
                relevant_docs.add(doc_id)
        
        if relevant_docs:
            qrels[qid] = relevant_docs
    
    # Statistics
    total_relevant = sum(len(docs) for docs in qrels.values())
    avg_per_query = total_relevant / len(qrels) if qrels else 0
    coverage = len(qrels) / len(queries) * 100 if queries else 0
    
    print(f"[QRELS] Generated qrels:")
    print(f"  Queries with qrels: {len(qrels)}/{len(queries)} ({coverage:.1f}%)")
    print(f"  Total relevant pairs: {total_relevant}")
    print(f"  Avg per query: {avg_per_query:.1f}")
    
    return dict(qrels)


def write_trec_qrels(
    qrels: Dict[str, Set[str]], output_path: Path
) -> None:
    """Write qrels in TREC format."""
    print(f"[TREC] Writing TREC qrels to {output_path}...")
    
    with open(output_path, "w") as f:
        for qid in sorted(qrels.keys()):
            for doc_id in sorted(qrels[qid]):
                f.write(f"{qid}\t0\t{doc_id}\t1\n")
    
    print(f"[TREC] Written TREC qrels")


def write_jsonl_qrels(
    qrels: Dict[str, Set[str]], output_path: Path
) -> None:
    """Write qrels in JSONL format."""
    print(f"[JSONL] Writing JSONL qrels to {output_path}...")
    
    with open(output_path, "wb") as f:
        for qid in sorted(qrels.keys()):
            record = {
                "query_id": qid,
                "relevant_doc_ids": sorted(list(qrels[qid])),
            }
            f.write(orjson.dumps(record) + b"\n")
    
    print(f"[JSONL] Written JSONL qrels")


def write_sha256(file_path: Path) -> None:
    """Write SHA256 checksum file."""
    sha256_path = file_path.with_suffix(file_path.suffix + ".sha256")
    hash_obj = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    checksum = hash_obj.hexdigest()
    with open(sha256_path, "w") as f:
        f.write(f"{checksum}  {file_path.name}\n")
    
    print(f"[SHA256] {sha256_path.name}: {checksum}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate silver qrels for FIQA datasets"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Dataset name (e.g., fiqa_10k_v1)",
    )
    parser.add_argument(
        "--qdrant-url",
        type=str,
        default="http://localhost:6333",
        help="Qdrant URL (default: http://localhost:6333)",
    )
    parser.add_argument(
        "--queries-path",
        type=str,
        default=None,
        help="Path to queries file (default: auto-detect from experiments/data/fiqa/queries.json or data/fiqa/queries.jsonl)",
    )
    parser.add_argument(
        "--bm25-topk",
        type=int,
        default=100,
        help="BM25 top-k retrieval (default: 100)",
    )
    parser.add_argument(
        "--vec-topk",
        type=int,
        default=100,
        help="Vector top-k retrieval (default: 100)",
    )
    parser.add_argument(
        "--cos-th",
        type=float,
        default=0.35,
        help="Cosine similarity threshold (default: 0.35)",
    )
    parser.add_argument(
        "--bm25-k",
        type=int,
        default=20,
        help="BM25 rank threshold (default: 20)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Output directory (default: data/fiqa_v1)",
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    repo_root = find_repo_root()
    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        out_dir = repo_root / "data" / "fiqa_v1"
    
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Find corpus file
    corpus_pattern = f"corpus_*_{args.dataset.split('_')[-1]}.jsonl"
    corpus_files = list(out_dir.glob(corpus_pattern))
    if not corpus_files:
        # Try alternative pattern
        size_k = args.dataset.split('_')[1]  # e.g., "10k" -> "10"
        corpus_pattern = f"corpus_{size_k}k_*.jsonl"
        corpus_files = list(out_dir.glob(corpus_pattern))
    
    if not corpus_files:
        print(f"[ERROR] Corpus file not found in {out_dir}")
        print(f"  Looking for pattern: {corpus_pattern}")
        sys.exit(1)
    
    corpus_path = corpus_files[0]
    print(f"[CORPUS] Using corpus: {corpus_path}")
    
    # Find queries file
    if args.queries_path:
        queries_path = Path(args.queries_path)
    else:
        # Try default locations
        candidates = [
            repo_root / "experiments" / "data" / "fiqa" / "queries.json",
            repo_root / "data" / "fiqa" / "queries.jsonl",
            repo_root / "data" / "fiqa" / "queries.json",
        ]
        queries_path = None
        for candidate in candidates:
            if candidate.exists():
                queries_path = candidate
                break
        
        if not queries_path:
            print(f"[ERROR] Queries file not found. Tried: {candidates}")
            sys.exit(1)
    
    # Collection name
    qdrant_collection = args.dataset  # e.g., fiqa_10k_v1
    
    # Output paths - fix filename: extract size number (e.g., "10k" -> "10")
    size_part = args.dataset.split('_')[1]  # e.g., "10k"
    size_num = size_part.replace('k', '')  # Remove 'k' to get "10"
    trec_filename = f"fiqa_qrels_{size_num}k_{args.dataset.split('_')[-1]}.trec"
    trec_path = out_dir / trec_filename
    
    jsonl_filename = f"fiqa_qrels_{size_num}k_{args.dataset.split('_')[-1]}.jsonl"
    jsonl_path = out_dir / jsonl_filename
    
    print(f"=" * 60)
    print(f"V12 Make Silver Qrels")
    print(f"  Dataset: {args.dataset}")
    print(f"  Qdrant collection: {qdrant_collection}")
    print(f"  Corpus: {corpus_path}")
    print(f"  Queries: {queries_path}")
    print(f"  Output: {out_dir}")
    print(f"=" * 60)
    
    # Connect to Qdrant
    client = get_qdrant_client(args.qdrant_url)
    
    # Load corpus for BM25
    docs, bm25_index, doc_id_to_idx = load_corpus_for_bm25(corpus_path)
    
    # Load queries
    queries = load_queries(queries_path)
    
    if not queries:
        print(f"[ERROR] No queries loaded")
        sys.exit(1)
    
    # Load embedding model for vector search
    print(f"[EMBEDDING] Loading embedding model...")
    try:
        embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print(f"[EMBEDDING] Model loaded")
    except Exception as e:
        print(f"[ERROR] Failed to load embedding model: {e}")
        print(f"[WARN] Continuing with BM25 only")
        embedding_model = None
    
    # Generate silver qrels
    qrels = generate_silver_qrels(
        queries,
        bm25_index,
        docs,
        doc_id_to_idx,
        client,
        qdrant_collection,
        args.bm25_topk,
        args.vec_topk,
        args.cos_th,
        args.bm25_k,
        embedding_model,
    )
    
    # Write outputs
    write_trec_qrels(qrels, trec_path)
    write_sha256(trec_path)
    
    write_jsonl_qrels(qrels, jsonl_path)
    write_sha256(jsonl_path)
    
    print(f"=" * 60)
    print(f"✅ Silver qrels generated successfully!")
    print(f"  TREC format: {trec_path}")
    print(f"  JSONL format: {jsonl_path}")
    print(f"=" * 60)


if __name__ == "__main__":
    main()

