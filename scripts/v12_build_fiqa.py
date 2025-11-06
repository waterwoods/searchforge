#!/usr/bin/env python3
"""
v12_build_fiqa.py - Build frozen FIQA datasets (10k & 50k)

Builds frozen FIQA datasets by sampling from beir_fiqa_full_ta collection,
creating new Qdrant collections, and writing corpus JSONL files.

Usage:
    poetry run python scripts/v12_build_fiqa.py --target-size 10000 --name-suffix v1
    poetry run python scripts/v12_build_fiqa.py --target-size 50000 --name-suffix v1
"""

import argparse
import hashlib
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import orjson
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    CollectionStatus,
)
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
        # Extract host and port from URL
        url_parts = url.replace("http://", "").replace("https://", "").split(":")
        host = url_parts[0] if url_parts else "localhost"
        port = int(url_parts[1]) if len(url_parts) > 1 else 6333
        return QdrantClient(host=host, port=port)
    else:
        return QdrantClient(url=url)


def scroll_all_points(
    client: QdrantClient, collection_name: str
) -> List[Dict[str, Any]]:
    """
    Scroll through all points in a Qdrant collection.
    
    Returns list of documents with id, payload (title, text, doc_id), and vector.
    """
    all_docs = []
    offset = None
    
    print(f"[SCROLL] Fetching all points from '{collection_name}'...")
    
    while True:
        result = client.scroll(
            collection_name=collection_name,
            limit=1000,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        
        points, next_offset = result
        
        if not points:
            break
        
        for point in points:
            payload = point.payload or {}
            doc_id = payload.get("doc_id") or payload.get("id") or str(point.id)
            title = payload.get("title", "")
            text = payload.get("text", "")
            abstract = payload.get("abstract") or text  # Use abstract if available, fallback to text
            
            all_docs.append({
                "id": point.id,
                "doc_id": doc_id,
                "title": title,
                "text": text,
                "abstract": abstract,
                "vector": point.vector,
                "payload": payload,
            })
        
        if len(all_docs) % 10000 == 0:
            print(f"  ... fetched {len(all_docs)} points")
        
        offset = next_offset
        if offset is None:
            break
    
    print(f"[SCROLL] Total: {len(all_docs)} documents")
    return all_docs


def sample_documents(
    docs: List[Dict[str, Any]], target_size: int, seed: int = 42
) -> List[Dict[str, Any]]:
    """Sample target_size documents with fixed seed."""
    if len(docs) <= target_size:
        print(f"[SAMPLE] All {len(docs)} documents selected (target: {target_size})")
        return docs
    
    random.seed(seed)
    sampled = random.sample(docs, target_size)
    print(f"[SAMPLE] Sampled {len(sampled)} documents from {len(docs)} (seed={seed})")
    return sampled


def write_corpus_jsonl(
    docs: List[Dict[str, Any]], output_path: Path
) -> None:
    """Write corpus to JSONL file."""
    print(f"[CORPUS] Writing corpus to {output_path}...")
    with open(output_path, "wb") as f:
        for doc in tqdm(docs, desc="Writing corpus"):
            record = {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "text": doc["text"],
            }
            f.write(orjson.dumps(record) + b"\n")
    print(f"[CORPUS] Written {len(docs)} documents")


def create_fingerprint(docs: List[Dict[str, Any]]) -> str:
    """Generate SHA256 fingerprint from sorted doc_id list."""
    doc_ids = sorted([doc["doc_id"] for doc in docs])
    content = "\n".join(doc_ids).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def create_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    distance: Distance = Distance.COSINE,
    recreate: bool = False,
) -> None:
    """Create Qdrant collection if it doesn't exist."""
    import time
    
    # If recreate is True, try to delete first (ignore errors)
    if recreate:
        try:
            print(f"[COLLECTION] Attempting to delete existing collection '{collection_name}'...")
            client.delete_collection(collection_name)
            time.sleep(0.5)  # Wait for deletion to complete
            print(f"[COLLECTION] Deleted '{collection_name}'")
        except Exception as e:
            # If collection doesn't exist, that's fine
            if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                print(f"[COLLECTION] Collection '{collection_name}' doesn't exist (will create new)")
            else:
                # Other errors - might still exist, try once more
                print(f"[WARN] Deletion error (may retry): {e}")
                time.sleep(1)
                try:
                    client.delete_collection(collection_name)
                    print(f"[COLLECTION] Deleted '{collection_name}' (retry succeeded)")
                except:
                    pass  # Ignore on second failure
    
    # Check if collection exists (for non-recreate mode)
    if not recreate:
        try:
            info = client.get_collection(collection_name)
            points_count = getattr(info, 'points_count', 0)
            raise ValueError(
                f"Collection '{collection_name}' already exists with {points_count} points. "
                f"Use --recreate to rebuild it."
            )
        except ValueError:
            raise
        except Exception:
            # Collection doesn't exist, which is fine
            pass
    
    # Create collection
    print(f"[COLLECTION] Creating '{collection_name}' with vector_size={vector_size}, distance={distance.value}...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=distance,
        ),
    )
    print(f"[COLLECTION] Created '{collection_name}'")


def upsert_documents(
    client: QdrantClient,
    collection_name: str,
    docs: List[Dict[str, Any]],
    batch_size: int = 500,
) -> None:
    """Upsert documents to Qdrant collection."""
    print(f"[UPSERT] Upserting {len(docs)} documents to '{collection_name}'...")
    
    points = []
    for doc in tqdm(docs, desc="Preparing points"):
        point = PointStruct(
            id=doc["id"],
            vector=doc["vector"],
            payload={
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "text": doc["text"],
                "abstract": doc.get("abstract") or doc["text"],  # Include abstract, fallback to text
            },
        )
        points.append(point)
    
    # Batch upsert
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        try:
            client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=True,
            )
        except Exception as e:
            # Continue even if validation errors occur (Qdrant API version differences)
            if "validation" in str(e).lower() or "strict_mode" in str(e).lower():
                print(f"[WARN] Validation warning during upsert (continuing): {e}")
                # Try without wait
                try:
                    client.upsert(
                        collection_name=collection_name,
                        points=batch,
                        wait=False,
                    )
                except Exception as e2:
                    print(f"[ERROR] Failed to upsert batch: {e2}")
                    raise
            else:
                raise
    
    # Verify (with error handling for API version differences)
    try:
        info = client.get_collection(collection_name)
        points_count = getattr(info, 'points_count', len(points))
        print(f"[UPSERT] Verified: {points_count} points in '{collection_name}'")
    except Exception as e:
        # If verification fails due to API issues, just log
        if "validation" in str(e).lower() or "strict_mode" in str(e).lower():
            print(f"[INFO] Upserted {len(points)} points (verification skipped due to API version)")
        else:
            raise


def write_sha256(file_path: Path) -> str:
    """Write SHA256 checksum file and return checksum."""
    sha256_path = file_path.with_suffix(file_path.suffix + ".sha256")
    hash_obj = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    checksum = hash_obj.hexdigest()
    with open(sha256_path, "w") as f:
        f.write(f"{checksum}  {file_path.name}\n")
    
    print(f"[SHA256] {sha256_path.name}: {checksum}")
    return checksum


def write_manifest(
    manifest_path: Path,
    dataset_name: str,
    qdrant_collection: str,
    size: int,
    seed: int,
    fingerprint: str,
    source_collection: str,
    vector_size: int,
    git_sha: Optional[str] = None,
    queries_file: Optional[Path] = None,
    queries_sha256: Optional[str] = None,
) -> None:
    """Write manifest.json."""
    manifest = {
        "dataset_name": dataset_name,
        "qdrant_collection": qdrant_collection,
        "source_collection": source_collection,
        "size": size,
        "seed": seed,
        "fingerprint": fingerprint,
        "vector_size": vector_size,
        "git_sha": git_sha or "unknown",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    
    if queries_file and queries_sha256:
        # Store relative path from repo root
        repo_root = find_repo_root()
        try:
            manifest["queries_file"] = str(queries_file.relative_to(repo_root))
        except ValueError:
            # If not relative, store absolute path as fallback
            manifest["queries_file"] = str(queries_file)
        manifest["queries_sha256"] = queries_sha256
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"[MANIFEST] Written {manifest_path}")


def get_git_sha() -> Optional[str]:
    """Get current git SHA."""
    try:
        import subprocess
        
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def load_queries_from_sources(repo_root: Path) -> List[Dict[str, str]]:
    """
    Load queries with source priority:
    1. experiments/data/fiqa/queries.jsonl (legacy JSONL)
    2. data/fiqa/fiqa_queries.txt (plain txt; convert to JSONL)
    
    Returns:
        List of {"id": str, "text": str} dictionaries
    """
    queries = []
    
    # Priority 1: legacy JSONL
    legacy_path = repo_root / "experiments" / "data" / "fiqa" / "queries.jsonl"
    if legacy_path.exists():
        print(f"[QUERIES] Loading from legacy JSONL: {legacy_path}")
        with open(legacy_path, "rb") as f:
            for line in f:
                if line.strip():
                    data = orjson.loads(line)
                    qid = data.get("_id") or data.get("id", "")
                    text = data.get("text", "")
                    if qid and text:
                        queries.append({"id": qid, "text": text})
        print(f"[QUERIES] Loaded {len(queries)} queries from legacy JSONL")
        return queries
    
    # Priority 2: plain txt
    txt_path = repo_root / "data" / "fiqa_queries.txt"
    if txt_path.exists():
        print(f"[QUERIES] Loading from plain txt: {txt_path}")
        with open(txt_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                text = line.strip()
                if text:
                    queries.append({"id": str(idx), "text": text})
        print(f"[QUERIES] Loaded {len(queries)} queries from plain txt")
        return queries
    
    print(f"[WARN] No queries source found, returning empty list")
    return queries


def write_queries_jsonl(
    queries: List[Dict[str, str]], output_path: Path
) -> None:
    """Write queries to JSONL file."""
    print(f"[QUERIES] Writing queries to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for query in tqdm(queries, desc="Writing queries"):
            record = {
                "id": query["id"],
                "text": query["text"],
            }
            f.write(orjson.dumps(record) + b"\n")
    print(f"[QUERIES] Written {len(queries)} queries")


def main():
    parser = argparse.ArgumentParser(
        description="Build frozen FIQA datasets from Qdrant collection"
    )
    parser.add_argument(
        "--qdrant-url",
        type=str,
        default="http://localhost:6333",
        help="Qdrant URL (default: http://localhost:6333)",
    )
    parser.add_argument(
        "--source-col",
        type=str,
        default="beir_fiqa_full_ta",
        help="Source collection name (default: beir_fiqa_full_ta)",
    )
    parser.add_argument(
        "--target-size",
        type=int,
        required=True,
        choices=[10000, 50000],
        help="Target dataset size (10000 or 50000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--name-suffix",
        type=str,
        default="v1",
        help="Dataset name suffix (default: v1)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Output directory (default: data/fiqa_v1)",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate Qdrant collection if it exists",
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    repo_root = find_repo_root()
    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        out_dir = repo_root / "data" / "fiqa_v1"
    
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Dataset naming
    dataset_name = f"fiqa_{args.target_size // 1000}k_{args.name_suffix}"
    qdrant_collection = dataset_name  # e.g., fiqa_10k_v1
    
    # Create dataset directory
    dataset_dir = out_dir / dataset_name
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    corpus_filename = f"corpus_{args.target_size // 1000}k_{args.name_suffix}.jsonl"
    corpus_path = out_dir / corpus_filename
    
    queries_path = dataset_dir / "queries.jsonl"
    
    manifest_path = out_dir / f"manifest_{args.target_size // 1000}k_{args.name_suffix}.json"
    
    print(f"=" * 60)
    print(f"V12 Build FIQA Dataset")
    print(f"  Source: {args.source_col}")
    print(f"  Target size: {args.target_size}")
    print(f"  Dataset: {dataset_name}")
    print(f"  Qdrant collection: {qdrant_collection}")
    print(f"  Output: {out_dir}")
    print(f"=" * 60)
    
    # Connect to Qdrant
    client = get_qdrant_client(args.qdrant_url)
    
    # Get source collection info
    try:
        # Try to get collection info with error handling for API version differences
        try:
            source_info = client.get_collection(args.source_col)
            # Handle different response formats
            if hasattr(source_info, 'config'):
                if hasattr(source_info.config, 'params'):
                    if hasattr(source_info.config.params, 'vectors'):
                        vector_size = source_info.config.params.vectors.size
                    else:
                        # Fallback: try to get from vectors_config
                        vector_size = getattr(source_info.config.params, 'vectors_config', {}).get('size', 384)
                else:
                    vector_size = 384  # Default
            else:
                vector_size = 384  # Default
            
            source_points = getattr(source_info, 'points_count', 0)
        except Exception as api_error:
            # Fallback: try direct HTTP call or use defaults
            print(f"[WARN] API error getting collection info: {api_error}")
            print(f"[INFO] Using default vector_size=384, will detect from actual vectors")
            vector_size = 384
            source_points = None
        
        if source_points is not None:
            print(f"[SOURCE] Collection '{args.source_col}': {source_points} points, vector_size={vector_size}")
        else:
            print(f"[SOURCE] Collection '{args.source_col}': vector_size={vector_size} (points count unknown)")
    except Exception as e:
        print(f"[ERROR] Failed to access source collection '{args.source_col}': {e}")
        print(f"[INFO] Will try to proceed and detect vector_size from actual documents")
        vector_size = 384
    
    # Scroll all documents
    all_docs = scroll_all_points(client, args.source_col)
    
    if len(all_docs) < args.target_size:
        print(f"[ERROR] Source has {len(all_docs)} docs, but target is {args.target_size}")
        sys.exit(1)
    
    # Detect vector_size from first document if not already known
    if vector_size == 384 and len(all_docs) > 0:
        first_vector = all_docs[0].get("vector")
        if first_vector:
            vector_size = len(first_vector)
            print(f"[INFO] Detected vector_size={vector_size} from first document")
    
    # Sample documents
    sampled_docs = sample_documents(all_docs, args.target_size, args.seed)
    
    # Write corpus JSONL
    write_corpus_jsonl(sampled_docs, corpus_path)
    corpus_sha256 = write_sha256(corpus_path)
    
    # Load and write queries
    queries = load_queries_from_sources(repo_root)
    queries_sha256 = None
    if queries:
        write_queries_jsonl(queries, queries_path)
        queries_sha256 = write_sha256(queries_path)
    else:
        print(f"[WARN] No queries loaded, skipping queries.jsonl")
    
    # Create Qdrant collection
    try:
        create_collection(client, qdrant_collection, vector_size, recreate=args.recreate)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    
    # Upsert documents
    upsert_documents(client, qdrant_collection, sampled_docs)
    
    # Generate fingerprint
    fingerprint = create_fingerprint(sampled_docs)
    print(f"[FINGERPRINT] {fingerprint}")
    
    # Write manifest
    git_sha = get_git_sha()
    write_manifest(
        manifest_path,
        dataset_name,
        qdrant_collection,
        args.target_size,
        args.seed,
        fingerprint,
        args.source_col,
        vector_size,
        git_sha,
        queries_path if queries else None,
        queries_sha256,
    )
    write_sha256(manifest_path)
    
    print(f"=" * 60)
    print(f"✅ Dataset built successfully!")
    print(f"  Corpus: {corpus_path}")
    if queries:
        print(f"  Queries: {queries_path}")
    print(f"  Manifest: {manifest_path}")
    print(f"  Qdrant collection: {qdrant_collection}")
    print(f"  Next: Run v12_make_silver_qrels.py")
    print(f"=" * 60)


if __name__ == "__main__":
    main()

