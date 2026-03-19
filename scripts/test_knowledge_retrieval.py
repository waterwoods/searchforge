#!/usr/bin/env python3
"""
Test Knowledge Retrieval — First Live Retrieval Validation
==========================================================
Validates that ingested insurance knowledge (dmv_sr22_explanations) can be
retrieved from Qdrant with targeted queries.

Usage:
  PYTHONPATH=. python3 scripts/test_knowledge_retrieval.py
  PYTHONPATH=. python3 scripts/test_knowledge_retrieval.py --query "What is SR-22?"
  PYTHONPATH=. python3 scripts/test_knowledge_retrieval.py --collection auto_insurance_demo_core

See: docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
    p = Path(".env.cloudrun")
    if p.exists():
        load_dotenv(p, override=True)
except ImportError:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
COLLECTION_NAME = "auto_insurance_demo_core"

# Default validation queries (DMV/SR-22 + notice_interpretation + declaration_page_garaging)
DEFAULT_QUERIES = [
    "What is SR-22?",
    "What do I need to take to DMV for SR-22?",
    "How do I clear suspension with insurance proof?",
    "What does DMV need after lapse or suspension?",
    # Second slice: notice_interpretation
    "What does payment failed mean?",
    "What does cancel pending mean?",
    "What does last notice mean?",
    "Is this insurance notice urgent?",
    "What should I send if I got a cancellation notice?",
    # Third slice: declaration_page_garaging
    "What is declaration page?",
    "What is garaging proof?",
    "Why do they need garaging proof?",
]


def get_embedder():
    """Same embedding logic as ingest script."""
    FASTEMBED_MODEL = os.getenv("FASTEMBED_MODEL", "BAAI/bge-small-en-v1.5")
    SBERT_MODEL = os.getenv("SBERT_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    try:
        from fastembed import TextEmbedding
        model = TextEmbedding(model_name=FASTEMBED_MODEL)
        return model, "fastembed"
    except Exception:
        pass
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(SBERT_MODEL)
        return model, "sbert"
    except Exception:
        pass
    return None, None


def get_qdrant_client():
    """Same as ingest script. Use check_compatibility=False for server 1.8.x."""
    from qdrant_client import QdrantClient

    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_url = None if os.getenv("USE_LOCAL_QDRANT") == "1" else os.getenv("QDRANT_URL")
    qdrant_api_key = None if os.getenv("USE_LOCAL_QDRANT") == "1" else os.getenv("QDRANT_API_KEY")

    kwargs = {"check_compatibility": False}  # Avoid client 1.15 vs server 1.8 warning
    if qdrant_url and (qdrant_url.startswith("http://") or qdrant_url.startswith("https://")):
        kwargs["url"] = qdrant_url
        if qdrant_api_key:
            kwargs["api_key"] = qdrant_api_key
        return QdrantClient(**kwargs)
    kwargs["host"] = qdrant_host
    kwargs["port"] = qdrant_port
    return QdrantClient(**kwargs)


def search(client, collection: str, query: str, embedder, backend: str, limit: int = 5):
    """Vector search. Uses client.search() for compatibility with Qdrant server 1.8.x."""
    texts = [query]
    if backend == "fastembed":
        vecs = list(embedder.embed(texts))
        vec = vecs[0] if vecs else []
    else:
        vec = embedder.encode(texts)[0]
    if hasattr(vec, "tolist"):
        vec = vec.tolist()

    # Prefer search() for server 1.8 compatibility; fallback to qdrant_adapter
    if hasattr(client, "search"):
        try:
            results = client.search(
                collection_name=collection,
                query_vector=vec,
                limit=limit,
            )
            out = []
            for r in results:
                score = getattr(r, "score", None) or 0.0
                payload = getattr(r, "payload", None) or {}
                out.append((float(score), payload))
            return out
        except Exception:
            pass
    from services.fiqa_api.utils.qdrant_adapter import qdrant_search
    results = qdrant_search(
        client=client,
        collection_name=collection,
        query_vector=vec,
        limit=limit,
        with_payload=True,
    )
    out = []
    for r in results:
        score = getattr(r, "score", None) or r.get("score", 0.0)
        payload = getattr(r, "payload", None) or r.get("payload") or {}
        out.append((float(score), payload))
    return out


def main():
    parser = argparse.ArgumentParser(description="Test knowledge retrieval from Qdrant")
    parser.add_argument("--query", type=str, help="Single query (otherwise runs default validation set)")
    parser.add_argument("--collection", type=str, default=COLLECTION_NAME)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    queries = [args.query] if args.query else DEFAULT_QUERIES

    print("=" * 60)
    print("Test Knowledge Retrieval")
    print("=" * 60)
    print(f"Collection: {args.collection}")
    print(f"Queries: {len(queries)}")
    print()

    embedder, backend = get_embedder()
    if not embedder:
        print("ERROR: No embedding backend. Install fastembed or sentence-transformers.")
        sys.exit(1)

    try:
        client = get_qdrant_client()
        info = client.get_collection(args.collection)
        print(f"Collection points: {info.points_count}")
        print()
    except Exception as e:
        print(f"ERROR: Cannot connect to Qdrant: {e}")
        sys.exit(1)

    passed = 0
    failed = 0
    for q in queries:
        print("-" * 50)
        print(f"Query: {q}")
        print("-" * 50)
        try:
            results = search(client, args.collection, q, embedder, backend, limit=args.limit)
            if not results:
                print("  (no results)")
                failed += 1
                continue
            for i, (score, payload) in enumerate(results, 1):
                title = payload.get("chunk_title") or payload.get("title") or "—"
                kp = payload.get("knowledge_pack", "—")
                topic = payload.get("topic", "—")
                ct = payload.get("content_type", "—")
                text_preview = (payload.get("text") or "")[:120] + "..." if payload.get("text") else "—"
                print(f"  [{i}] score={score:.4f} | pack={kp} | topic={topic} | type={ct}")
                print(f"      title: {title}")
                print(f"      text:  {text_preview}")
            # Consider pass if we got at least one result with knowledge_pack or reasonable score
            has_knowledge = any(
                (p.get("knowledge_pack") == "insurance" or p.get("content_type") == "knowledge")
                for _, p in results
            )
            has_good_score = results[0][0] > 0.3
            if results and (has_knowledge or has_good_score):
                passed += 1
                print("  ✓ retrieval OK")
            else:
                failed += 1
                print("  ? check if knowledge chunks are ingested")
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Summary: {passed} passed, {failed} failed")
    print("=" * 60)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
