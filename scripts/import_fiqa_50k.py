#!/usr/bin/env python3
"""
Import full FiQA 50k dataset into Qdrant collections.

Supports:
- fiqa_50k_v1: Main collection (from corpus_50k_v1.jsonl)
- fiqa_para_50k, fiqa_sent_50k, fiqa_win256_o64_50k: Chunked collections (if data exists)

Usage:
    python scripts/import_fiqa_50k.py --collection fiqa_50k_v1
    python scripts/import_fiqa_50k.py --all
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

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


def load_corpus(path: Path) -> List[Dict[str, Any]]:
    """Load corpus from JSONL file."""
    docs = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            doc_id = str(obj.get('doc_id', ''))
            title = str(obj.get('title', '') or '')
            text = str(obj.get('text') or obj.get('abstract') or '')
            docs.append({'doc_id': doc_id, 'title': title, 'text': text})
    return docs


def ensure_collection(client: QdrantClient, name: str, dim: int, recreate: bool) -> None:
    """Create collection if it doesn't exist or recreate if requested."""
    try:
        collection_info = client.get_collection(name)
        if recreate:
            print(f"[INFO] Deleting existing collection: {name}")
            client.delete_collection(name)
            client.recreate_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
            )
            print(f"[INFO] Recreated collection: {name}")
        else:
            print(f"[INFO] Collection {name} already exists (points: {collection_info.points_count})")
    except Exception:
        # Collection doesn't exist, create it
        print(f"[INFO] Creating collection: {name}")
        client.recreate_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
        )


def embed_documents(model: SentenceTransformer, docs: List[Dict[str, Any]], fields: str = 'title+text') -> List[List[float]]:
    """Generate embeddings for documents."""
    contents = []
    for d in docs:
        if fields == 'title+text':
            contents.append((d['title'] + ' ' + d['text']).strip())
        elif fields == 'text':
            contents.append(d['text'])
        elif fields == 'title':
            contents.append(d['title'])
        else:
            contents.append((d['title'] + ' ' + d['text']).strip())
    
    print(f"[INFO] Generating embeddings for {len(contents)} documents...")
    vectors = model.encode(
        contents,
        show_progress_bar=True,
        batch_size=512,
        normalize_embeddings=False
    )
    return vectors.tolist()


def upsert_points(client: QdrantClient, collection: str, docs: List[Dict[str, Any]], vectors: List[List[float]], batch_size: int = 512, docid_length: int = 6) -> None:
    """Upsert points to Qdrant collection."""
    points: List[PointStruct] = []
    for i, (d, v) in enumerate(zip(docs, vectors)):
        # Use doc_id as point ID, or fallback to sequential ID
        try:
            pid = int(d['doc_id'])
        except (ValueError, KeyError):
            pid = i + 1
        
        # Normalize doc_id to zero-padded string format
        raw_doc_id = d.get('doc_id', '')
        if isinstance(raw_doc_id, int):
            doc_id_str = f"{raw_doc_id:0{docid_length}d}"
        elif isinstance(raw_doc_id, str) and raw_doc_id.isdigit():
            doc_id_str = raw_doc_id.zfill(docid_length)
        else:
            # Fallback: use point ID if doc_id is missing or invalid
            doc_id_str = f"{pid:0{docid_length}d}"
        
        points.append(PointStruct(
            id=pid,
            vector=v,
            payload={
                'doc_id': doc_id_str,
                'title': d['title'],
                'text': d['text']
            }
        ))
    
    print(f"[INFO] Upserting {len(points)} points to collection {collection}...")
    for i in tqdm(range(0, len(points), batch_size), desc='Upserting'):
        client.upsert(
            collection_name=collection,
            points=points[i:i+batch_size],
            wait=True
        )


def get_collection_info(client: QdrantClient, collection: str) -> Optional[Dict[str, Any]]:
    """Get collection information."""
    try:
        info = client.get_collection(collection)
        return {
            'name': collection,
            'points_count': info.points_count,
            'status': str(info.status),
            'vector_size': info.config.params.vectors.size if hasattr(info.config.params, 'vectors') else None
        }
    except Exception as e:
        return None


def import_collection(
    client: QdrantClient,
    collection_name: str,
    corpus_path: Path,
    model: SentenceTransformer,
    recreate: bool = False,
    fields: str = 'title+text',
    docid_length: int = 6
) -> Dict[str, Any]:
    """Import a single collection."""
    print(f"\n{'='*60}")
    print(f"Importing collection: {collection_name}")
    print(f"Corpus: {corpus_path}")
    print(f"{'='*60}")
    
    # Load corpus
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")
    
    docs = load_corpus(corpus_path)
    print(f"[INFO] Loaded {len(docs)} documents from {corpus_path}")
    
    # Get embedding dimension
    dim = model.get_sentence_embedding_dimension()
    
    # Ensure collection exists
    ensure_collection(client, collection_name, dim, recreate)
    
    # Generate embeddings
    vectors = embed_documents(model, docs, fields)
    
    # Upsert points
    upsert_points(client, collection_name, docs, vectors, docid_length=docid_length)
    
    # Verify
    info = get_collection_info(client, collection_name)
    
    result = {
        'collection': collection_name,
        'documents_loaded': len(docs),
        'points_upserted': len(docs),
        'vector_dim': dim,
        'status': 'success'
    }
    
    if info:
        result['points_count'] = info['points_count']
        print(f"\n[SUCCESS] Collection {collection_name}: {info['points_count']} points")
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Import FiQA 50k dataset into Qdrant')
    parser.add_argument(
        '--collection',
        type=str,
        choices=['fiqa_50k_v1', 'fiqa_para_50k', 'fiqa_sent_50k', 'fiqa_win256_o64_50k'],
        help='Collection name to import'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Import all available collections'
    )
    parser.add_argument(
        '--corpus',
        type=str,
        default=None,
        help='Path to corpus JSONL file (default: auto-detect)'
    )
    parser.add_argument(
        '--qdrant-url',
        type=str,
        default=os.getenv('QDRANT_URL', 'http://localhost:6333'),
        help='Qdrant URL (default: http://localhost:6333)'
    )
    parser.add_argument(
        '--recreate',
        action='store_true',
        help='Recreate collection if it exists'
    )
    parser.add_argument(
        '--fields',
        type=str,
        default='title+text',
        choices=['title', 'text', 'title+text'],
        help='Fields to use for embedding (default: title+text)'
    )
    
    args = parser.parse_args()
    
    if not args.collection and not args.all:
        parser.error("Must specify either --collection or --all")
    
    # Find repo root
    repo_root = find_repo_root()
    
    # Initialize Qdrant client
    if args.qdrant_url.startswith('http'):
        client = QdrantClient(url=args.qdrant_url)
    else:
        client = QdrantClient(url=args.qdrant_url)
    
    # Initialize model
    print("[INFO] Loading embedding model...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print(f"[INFO] Model loaded: {model.get_sentence_embedding_dimension()}D embeddings")
    
    # Default corpus path for fiqa_50k_v1
    default_corpus = repo_root / 'data' / 'fiqa_v1' / 'corpus_50k_v1.jsonl'
    
    results = []
    
    if args.all:
        # Import all available collections
        collections_to_import = [
            ('fiqa_50k_v1', default_corpus),
        ]
        
        # Check for chunked collection corpus files (if they exist, otherwise use base corpus)
        chunked_base = repo_root / 'data' / 'fiqa_v1'
        para_corpus = chunked_base / 'corpus_para_50k.jsonl'
        sent_corpus = chunked_base / 'corpus_sent_50k.jsonl'
        win256_corpus = chunked_base / 'corpus_win256_o64_50k.jsonl'
        
        # Use base corpus if chunked version doesn't exist (chunking happens at query time or in the app)
        if para_corpus.exists():
            collections_to_import.append(('fiqa_para_50k', para_corpus))
        else:
            print(f"[WARN] corpus_para_50k.jsonl not found, using base corpus for fiqa_para_50k")
            collections_to_import.append(('fiqa_para_50k', default_corpus))
        if sent_corpus.exists():
            collections_to_import.append(('fiqa_sent_50k', sent_corpus))
        else:
            print(f"[WARN] corpus_sent_50k.jsonl not found, using base corpus for fiqa_sent_50k")
            collections_to_import.append(('fiqa_sent_50k', default_corpus))
        if win256_corpus.exists():
            collections_to_import.append(('fiqa_win256_o64_50k', win256_corpus))
        else:
            print(f"[WARN] corpus_win256_o64_50k.jsonl not found, using base corpus for fiqa_win256_o64_50k")
            collections_to_import.append(('fiqa_win256_o64_50k', default_corpus))
        
        for collection_name, corpus_path in collections_to_import:
            try:
                result = import_collection(
                    client=client,
                    collection_name=collection_name,
                    corpus_path=corpus_path,
                    model=model,
                    recreate=args.recreate,
                    fields=args.fields
                )
                results.append(result)
            except Exception as e:
                print(f"[ERROR] Failed to import {collection_name}: {e}")
                results.append({
                    'collection': collection_name,
                    'status': 'error',
                    'error': str(e)
                })
    else:
        # Import single collection
        if args.corpus:
            corpus_path = Path(args.corpus)
        else:
            if args.collection == 'fiqa_50k_v1':
                corpus_path = default_corpus
            else:
                # Try to find chunked collection corpus, fallback to base corpus if not found
                chunked_base = repo_root / 'data' / 'fiqa_v1'
                collection_corpus_map = {
                    'fiqa_para_50k': chunked_base / 'corpus_para_50k.jsonl',
                    'fiqa_sent_50k': chunked_base / 'corpus_sent_50k.jsonl',
                    'fiqa_win256_o64_50k': chunked_base / 'corpus_win256_o64_50k.jsonl',
                }
                chunked_corpus = collection_corpus_map.get(args.collection)
                if chunked_corpus and chunked_corpus.exists():
                    corpus_path = chunked_corpus
                else:
                    print(f"[WARN] Chunked corpus for {args.collection} not found, using base corpus: {default_corpus}")
                    corpus_path = default_corpus
        
        try:
            result = import_collection(
                client=client,
                collection_name=args.collection,
                corpus_path=corpus_path,
                model=model,
                recreate=args.recreate,
                fields=args.fields
            )
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Failed to import {args.collection}: {e}")
            sys.exit(1)
    
    # Summary
    print(f"\n{'='*60}")
    print("Import Summary")
    print(f"{'='*60}")
    for result in results:
        if result['status'] == 'success':
            print(f"✅ {result['collection']}: {result.get('points_count', result['points_upserted'])} points")
        else:
            print(f"❌ {result['collection']}: {result.get('error', 'Failed')}")
    
    # Output JSON summary
    output_file = repo_root / '.runs' / 'import_fiqa_50k.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump({'results': results}, f, indent=2, ensure_ascii=False)
    print(f"\n[INFO] Summary saved to: {output_file}")


if __name__ == '__main__':
    main()

