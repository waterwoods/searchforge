#!/usr/bin/env python3
"""
Import FiQA collection from manifest and corpus file.

Reads JSONL corpus file, preserves doc_id EXACTLY as in source (no padding/transformation),
and imports to Qdrant collection.

Usage:
    python scripts/import_fiqa_manifest.py --manifest data/fiqa_v1/manifest_50k_v1.json --collection fiqa_para_50k --recreate
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


def find_repo_root() -> Path:
    """Find repository root directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load manifest JSON file."""
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def infer_corpus_path(manifest_path: Path, manifest: Dict[str, Any]) -> Path:
    """Infer corpus file path from manifest location."""
    # Try common locations relative to manifest
    manifest_dir = manifest_path.parent
    
    # Try fiqa_50k_v1/corpus.jsonl first (organized structure)
    corpus_path = manifest_dir / "fiqa_50k_v1" / "corpus.jsonl"
    if corpus_path.exists():
        return corpus_path
    
    # Fallback to corpus_50k_v1.jsonl
    corpus_path = manifest_dir / "corpus_50k_v1.jsonl"
    if corpus_path.exists():
        return corpus_path
    
    # Last resort: check if dataset_name gives us a hint
    dataset_name = manifest.get("dataset_name", "")
    if dataset_name:
        corpus_path = manifest_dir / f"{dataset_name}" / "corpus.jsonl"
        if corpus_path.exists():
            return corpus_path
    
    raise FileNotFoundError(
        f"Could not find corpus file. Tried:\n"
        f"  - {manifest_dir / 'fiqa_50k_v1' / 'corpus.jsonl'}\n"
        f"  - {manifest_dir / 'corpus_50k_v1.jsonl'}\n"
        f"  - {manifest_dir / dataset_name / 'corpus.jsonl'}"
    )


def load_corpus(corpus_path: Path) -> List[Dict[str, Any]]:
    """Load corpus from JSONL file, preserving doc_id exactly as-is."""
    docs = []
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                doc_id = obj.get("doc_id")
                if doc_id is None:
                    print(f"[WARN] Line {line_num}: missing doc_id, skipping")
                    continue
                
                # Preserve doc_id EXACTLY as-is (convert to string but no padding/trimming)
                doc_id = str(doc_id)
                
                # Validate doc_id is digits only (as per requirements)
                if not doc_id.isdigit():
                    print(f"[WARN] Line {line_num}: doc_id '{doc_id}' is not digits-only, skipping")
                    continue
                
                text = obj.get("text", "")
                title = obj.get("title", "")
                
                # Use placeholder if text is empty (to preserve all 50k documents)
                if not text or not text.strip():
                    if title and title.strip():
                        text = title  # Use title as fallback
                    else:
                        text = "[empty]"  # Minimal placeholder for embedding
                    print(f"[WARN] Line {line_num}: doc_id '{doc_id}' has empty text, using placeholder")
                
                docs.append({
                    "doc_id": doc_id,  # EXACT as-is, no transformation
                    "title": str(title) if title else "",
                    "text": str(text)
                })
            except json.JSONDecodeError as e:
                print(f"[ERROR] Line {line_num}: JSON decode error: {e}")
                continue
            except Exception as e:
                print(f"[ERROR] Line {line_num}: Unexpected error: {e}")
                continue
    
    return docs


def ensure_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    recreate: bool
) -> None:
    """Create or recreate collection with proper configuration."""
    try:
        collection_info = client.get_collection(collection_name)
        if recreate:
            print(f"[INFO] Deleting existing collection: {collection_name}")
            client.delete_collection(collection_name)
            print(f"[INFO] Collection deleted")
        else:
            print(f"[INFO] Collection {collection_name} already exists (points: {collection_info.points_count})")
            return
    except Exception:
        # Collection doesn't exist, will create below
        pass
    
    print(f"[INFO] Creating collection: {collection_name}")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )
    print(f"[INFO] Collection created with vector_size={vector_size}, distance=Cosine")


def embed_documents(
    model: SentenceTransformer,
    docs: List[Dict[str, Any]],
    batch_size: int = 512
) -> List[List[float]]:
    """Generate embeddings for documents."""
    # Use text field for embedding (title+text if title exists, otherwise just text)
    contents = []
    for doc in docs:
        text = doc["text"]
        title = doc.get("title", "")
        if title and title.strip():
            content = f"{title} {text}".strip()
        else:
            content = text.strip()
        contents.append(content)
    
    print(f"[INFO] Generating embeddings for {len(contents)} documents...")
    vectors = model.encode(
        contents,
        show_progress_bar=True,
        batch_size=batch_size,
        normalize_embeddings=False
    )
    return vectors.tolist()


def upsert_points(
    client: QdrantClient,
    collection_name: str,
    docs: List[Dict[str, Any]],
    vectors: List[List[float]],
    batch_size: int = 512
) -> None:
    """Upsert points to Qdrant, using doc_id as point ID (converted to int if possible)."""
    total = len(docs)
    print(f"[INFO] Upserting {total} points in batches of {batch_size}...")
    
    for batch_start in tqdm(range(0, total, batch_size), desc="Upserting batches"):
        batch_end = min(batch_start + batch_size, total)
        batch_docs = docs[batch_start:batch_end]
        batch_vectors = vectors[batch_start:batch_end]
        
        points = []
        for doc, vector in zip(batch_docs, batch_vectors):
            doc_id = doc["doc_id"]
            
            # Use doc_id as point ID (Qdrant requires int or UUID)
            # Since doc_id is digits-only, convert to int
            try:
                point_id = int(doc_id)
            except (ValueError, TypeError):
                # Fallback: use hash if somehow not an int (shouldn't happen per validation)
                point_id = hash(doc_id) & 0x7FFFFFFF  # Positive int
            
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "doc_id": doc_id,  # EXACT as-is in payload
                    "title": doc["title"],
                    "text": doc["text"]
                }
            )
            points.append(point)
        
        # Upsert batch
        client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True
        )
    
    print(f"[INFO] Upserted {total} points")


def main():
    parser = argparse.ArgumentParser(
        description="Import FiQA collection from manifest and corpus",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to manifest JSON file (e.g., data/fiqa_v1/manifest_50k_v1.json)"
    )
    parser.add_argument(
        "--collection",
        type=str,
        required=True,
        help="Qdrant collection name (e.g., fiqa_para_50k)"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate collection if it exists"
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=512,
        help="Batch size for upserting (default: 512)"
    )
    parser.add_argument(
        "--qdrant-url",
        type=str,
        default="http://andy-wsl:6333",
        help="Qdrant URL (default: http://andy-wsl:6333)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model name (default: sentence-transformers/all-MiniLM-L6-v2)"
    )
    parser.add_argument(
        "--corpus",
        type=str,
        default=None,
        help="Explicit corpus JSONL path (default: auto-infer from manifest)"
    )
    
    args = parser.parse_args()
    
    # Find repo root
    repo_root = find_repo_root()
    
    # Resolve paths
    manifest_path = (repo_root / args.manifest).resolve()
    if not manifest_path.exists():
        print(f"[ERROR] Manifest file not found: {manifest_path}")
        sys.exit(1)
    
    # Load manifest
    print(f"[INFO] Loading manifest: {manifest_path}")
    manifest = load_manifest(manifest_path)
    print(f"[INFO] Manifest: dataset_name={manifest.get('dataset_name')}, size={manifest.get('size')}")
    
    # Determine corpus path
    if args.corpus:
        corpus_path = (repo_root / args.corpus).resolve()
    else:
        corpus_path = infer_corpus_path(manifest_path, manifest)
    
    if not corpus_path.exists():
        print(f"[ERROR] Corpus file not found: {corpus_path}")
        sys.exit(1)
    
    print(f"[INFO] Using corpus: {corpus_path}")
    
    # Load corpus
    print(f"[INFO] Loading corpus...")
    docs = load_corpus(corpus_path)
    print(f"[INFO] Loaded {len(docs)} documents from corpus")
    
    if len(docs) == 0:
        print("[ERROR] No documents loaded from corpus")
        sys.exit(1)
    
    # Initialize Qdrant client
    print(f"[INFO] Connecting to Qdrant: {args.qdrant_url}")
    client = QdrantClient(url=args.qdrant_url)
    
    # Initialize embedding model
    print(f"[INFO] Loading embedding model: {args.model}")
    model = SentenceTransformer(args.model)
    vector_size = model.get_sentence_embedding_dimension()
    print(f"[INFO] Model loaded: {vector_size}D embeddings")
    
    # Ensure collection exists
    ensure_collection(client, args.collection, vector_size, args.recreate)
    
    # Generate embeddings
    vectors = embed_documents(model, docs, batch_size=args.batch)
    
    # Upsert points
    upsert_points(client, args.collection, docs, vectors, batch_size=args.batch)
    
    # Verify final count
    collection_info = client.get_collection(args.collection)
    points_count = collection_info.points_count
    
    print(f"\n{'='*60}")
    print(f"✅ Import complete!")
    print(f"   Collection: {args.collection}")
    print(f"   Points count: {points_count}")
    print(f"   Expected: {len(docs)}")
    print(f"{'='*60}")
    
    if points_count != len(docs):
        print(f"[WARN] Points count mismatch: expected {len(docs)}, got {points_count}")
        sys.exit(1)


if __name__ == "__main__":
    main()

