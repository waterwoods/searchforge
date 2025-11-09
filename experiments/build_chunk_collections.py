#!/usr/bin/env python3
"""
Build Chunking Collections - Build three Qdrant collections with different chunking strategies

This script builds three collections from the same FiQA corpus:
1. fiqa_para_50k - Paragraph-based chunking
2. fiqa_sent_50k - Sentence-based chunking  
3. fiqa_win256_o64_50k - Sliding window (256 chars, 64 overlap)

All collections use the same embedding model: all-MiniLM-L6-v2 (384 dimensions)

Usage:
    python experiments/build_chunk_collections.py --corpus-path data/fiqa_v1/corpus_50k_v1.jsonl
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

# Third-party imports
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Local imports
from chunking_strategies import chunk_document, ChunkResult


def find_repo_root() -> Path:
    """Find repository root directory."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_corpus(corpus_path: Path) -> List[Dict[str, Any]]:
    """
    Load corpus from JSONL file.
    
    Args:
        corpus_path: Path to corpus JSONL file
        
    Returns:
        List of document dictionaries
    """
    docs = []
    print(f"Loading corpus from {corpus_path}...")
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                doc = json.loads(line)
                docs.append(doc)
    
    print(f"Loaded {len(docs)} documents")
    return docs


def get_qdrant_client(host: str = "localhost", port: int = 6333) -> QdrantClient:
    """Create Qdrant client."""
    return QdrantClient(host=host, port=port)


def create_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    distance: Distance = Distance.COSINE,
    recreate: bool = False
) -> None:
    """Create Qdrant collection if it doesn't exist."""
    # Check if collection exists
    try:
        info = client.get_collection(collection_name)
        points_count = getattr(info, 'points_count', 0)
        
        if recreate:
            print(f"Deleting existing collection '{collection_name}' ({points_count} points)...")
            client.delete_collection(collection_name)
            time.sleep(0.5)
        else:
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
    print(f"Creating collection '{collection_name}' with vector_size={vector_size}...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=distance,
        ),
    )
    print(f"✅ Created collection '{collection_name}'")


def build_and_index_collection(
    client: QdrantClient,
    collection_name: str,
    corpus: List[Dict[str, Any]],
    embedding_model: SentenceTransformer,
    chunking_strategy: str,
    chunking_params: Dict[str, Any],
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Build and index a collection with specified chunking strategy.
    
    Args:
        client: Qdrant client
        collection_name: Name of collection to create
        corpus: List of documents
        embedding_model: SentenceTransformer model
        chunking_strategy: Chunking strategy name
        chunking_params: Parameters for chunking
        batch_size: Batch size for indexing
        
    Returns:
        Dictionary with build metrics
    """
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"Building collection: {collection_name}")
    print(f"  Strategy: {chunking_strategy}")
    print(f"  Params: {chunking_params}")
    print(f"  Corpus size: {len(corpus)} documents")
    print(f"{'='*60}\n")
    
    # Step 1: Chunk all documents
    print("Step 1: Chunking documents...")
    all_chunks = []
    for doc in tqdm(corpus, desc="Chunking"):
        chunks = chunk_document(doc, chunking_strategy, **chunking_params)
        all_chunks.extend(chunks)
    
    print(f"✅ Created {len(all_chunks)} chunks from {len(corpus)} documents")
    print(f"   Average chunks per document: {len(all_chunks) / len(corpus):.2f}")
    
    # Step 2: Generate embeddings
    print("\nStep 2: Generating embeddings...")
    texts = [chunk.text for chunk in all_chunks]
    
    # Batch encode for efficiency
    embeddings = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
        batch_texts = texts[i:i + batch_size]
        batch_embeddings = embedding_model.encode(
            batch_texts,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        embeddings.extend(batch_embeddings)
    
    print(f"✅ Generated {len(embeddings)} embeddings")
    
    # Step 3: Index into Qdrant
    print("\nStep 3: Indexing into Qdrant...")
    points = []
    for i, (chunk, embedding) in enumerate(zip(all_chunks, embeddings)):
        point = PointStruct(
            id=i,  # Use sequential IDs
            vector=embedding.tolist(),
            payload={
                'doc_id': chunk.doc_id,
                'chunk_id': chunk.chunk_id,
                'text': chunk.text,
                'chunk_index': chunk.chunk_index,
                'chunking_strategy': chunking_strategy,
                **chunk.metadata
            }
        )
        points.append(point)
    
    # Batch upsert
    for i in tqdm(range(0, len(points), batch_size), desc="Indexing"):
        batch = points[i:i + batch_size]
        client.upsert(
            collection_name=collection_name,
            points=batch,
            wait=True
        )
    
    # Verify
    info = client.get_collection(collection_name)
    indexed_count = getattr(info, 'points_count', len(points))
    print(f"✅ Indexed {indexed_count} points")
    
    # Calculate metrics
    build_time = time.time() - start_time
    
    # Get collection size (approximate)
    try:
        # Try to get collection info including disk usage
        collection_info = client.get_collection(collection_name)
        # Estimate: vectors + payload (rough estimate)
        vector_size_bytes = indexed_count * 384 * 4  # 384 dim * 4 bytes per float
        payload_size_bytes = sum(len(json.dumps(p.payload)) for p in points[:100]) * indexed_count / 100
        total_size_mb = (vector_size_bytes + payload_size_bytes) / (1024 * 1024)
    except Exception:
        total_size_mb = 0
    
    metrics = {
        'collection_name': collection_name,
        'chunking_strategy': chunking_strategy,
        'chunking_params': chunking_params,
        'num_documents': len(corpus),
        'num_chunks': len(all_chunks),
        'chunks_per_doc': len(all_chunks) / len(corpus),
        'build_time_sec': build_time,
        'index_size_mb': total_size_mb,
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    print(f"\n✅ Collection built successfully!")
    print(f"   Build time: {build_time:.2f}s")
    print(f"   Index size: {total_size_mb:.2f} MB")
    
    return metrics


def write_collection_metadata(
    collection_name: str,
    embed_model: str,
    dim: int,
    chunking_strategy: str,
    chunking_params: Dict[str, Any],
    metrics: Dict[str, Any],
    config_dir: Path
) -> None:
    """
    Write collection metadata to configs/collection_tags/<collection_name>.json
    
    Args:
        collection_name: Name of collection
        embed_model: Embedding model name
        dim: Vector dimension
        chunking_strategy: Chunking strategy name
        chunking_params: Chunking parameters
        metrics: Build metrics
        config_dir: Config directory path
    """
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / f"{collection_name}.json"
    
    metadata = {
        'collection_name': collection_name,
        'embed_model': embed_model,
        'dim': dim,
        'chunking_strategy': chunking_strategy,
        'chunking_params': chunking_params,
        'num_documents': metrics['num_documents'],
        'num_chunks': metrics['num_chunks'],
        'chunks_per_doc': metrics['chunks_per_doc'],
        'build_time_sec': metrics['build_time_sec'],
        'index_size_mb': metrics['index_size_mb'],
        'created_at': metrics['created_at']
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Wrote metadata to {config_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Build three chunking collections"
    )
    parser.add_argument(
        '--corpus-path',
        type=str,
        default='data/fiqa_v1/corpus_50k_v1.jsonl',
        help='Path to corpus JSONL file'
    )
    parser.add_argument(
        '--qdrant-host',
        type=str,
        default='localhost',
        help='Qdrant host (default: localhost)'
    )
    parser.add_argument(
        '--qdrant-port',
        type=int,
        default=6333,
        help='Qdrant port (default: 6333)'
    )
    parser.add_argument(
        '--embed-model',
        type=str,
        default='all-MiniLM-L6-v2',
        help='Embedding model name (default: all-MiniLM-L6-v2)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for indexing (default: 100)'
    )
    parser.add_argument(
        '--recreate',
        action='store_true',
        help='Recreate collections if they exist'
    )
    parser.add_argument(
        '--strategies',
        nargs='+',
        choices=['paragraph', 'sentence', 'sliding_window', 'all'],
        default=['all'],
        help='Chunking strategies to build (default: all)'
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    repo_root = find_repo_root()
    corpus_path = Path(args.corpus_path)
    if not corpus_path.is_absolute():
        corpus_path = repo_root / corpus_path
    
    config_dir = repo_root / 'configs' / 'collection_tags'
    
    # Load corpus
    corpus = load_corpus(corpus_path)
    
    # Initialize embedding model
    print(f"\nLoading embedding model: {args.embed_model}...")
    embedding_model = SentenceTransformer(args.embed_model)
    vector_dim = embedding_model.get_sentence_embedding_dimension()
    print(f"✅ Model loaded, dimension: {vector_dim}")
    
    # Connect to Qdrant
    client = get_qdrant_client(args.qdrant_host, args.qdrant_port)
    
    # Define collections to build
    collections = []
    
    if 'all' in args.strategies or 'paragraph' in args.strategies:
        collections.append({
            'name': 'fiqa_para_50k',
            'strategy': 'paragraph',
            'params': {}
        })
    
    if 'all' in args.strategies or 'sentence' in args.strategies:
        collections.append({
            'name': 'fiqa_sent_50k',
            'strategy': 'sentence',
            'params': {}
        })
    
    if 'all' in args.strategies or 'sliding_window' in args.strategies:
        collections.append({
            'name': 'fiqa_win256_o64_50k',
            'strategy': 'sliding_window',
            'params': {'window_size': 256, 'overlap': 64}
        })
    
    # Build all collections
    all_metrics = []
    
    for col_config in collections:
        collection_name = col_config['name']
        strategy = col_config['strategy']
        params = col_config['params']
        
        try:
            # Create collection
            create_collection(
                client,
                collection_name,
                vector_dim,
                recreate=args.recreate
            )
            
            # Build and index
            metrics = build_and_index_collection(
                client,
                collection_name,
                corpus,
                embedding_model,
                strategy,
                params,
                batch_size=args.batch_size
            )
            
            # Write metadata
            write_collection_metadata(
                collection_name,
                args.embed_model,
                vector_dim,
                strategy,
                params,
                metrics,
                config_dir
            )
            
            all_metrics.append(metrics)
            
        except Exception as e:
            print(f"❌ Error building collection {collection_name}: {e}")
            continue
    
    # Summary
    print(f"\n{'='*60}")
    print(f"BUILD SUMMARY")
    print(f"{'='*60}")
    print(f"Successfully built {len(all_metrics)} collections:")
    for metrics in all_metrics:
        print(f"\n  {metrics['collection_name']}:")
        print(f"    - Strategy: {metrics['chunking_strategy']}")
        print(f"    - Chunks: {metrics['num_chunks']}")
        print(f"    - Chunks/doc: {metrics['chunks_per_doc']:.2f}")
        print(f"    - Build time: {metrics['build_time_sec']:.2f}s")
        print(f"    - Index size: {metrics['index_size_mb']:.2f} MB")
    
    print(f"\n✅ All collections built successfully!")
    print(f"\nNext steps:")
    print(f"  1. Run health checks: python experiments/run_chunk_health_checks.py")
    print(f"  2. Run experiments: python experiments/run_chunk_experiments.py")


if __name__ == '__main__':
    main()

