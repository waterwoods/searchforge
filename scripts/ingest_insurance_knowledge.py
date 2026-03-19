#!/usr/bin/env python3
"""
Ingest Insurance Knowledge — First Live Retrieval Slice
=======================================================
Reads knowledge/industries/insurance/*.md, chunks by section, embeds, and upserts
to Qdrant (auto_insurance_demo_core) with knowledge_pack metadata.

First slice: dmv_sr22_explanations.md

Usage:
  PYTHONPATH=. python3 scripts/ingest_insurance_knowledge.py
  PYTHONPATH=. python3 scripts/ingest_insurance_knowledge.py --dry-run
  PYTHONPATH=. python3 scripts/ingest_insurance_knowledge.py --source knowledge/industries/insurance/dmv_sr22_explanations.md

See: docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md
"""

import argparse
import hashlib
import logging
import os
import sys
from pathlib import Path

# Load env from .env / .env.cloudrun
try:
    from dotenv import load_dotenv
    load_dotenv()
    p = Path(".env.cloudrun")
    if p.exists():
        load_dotenv(p, override=True)
except ImportError:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_INSURANCE = REPO_ROOT / "knowledge" / "industries" / "insurance"
COLLECTION_NAME = "auto_insurance_demo_core"
EMBEDDING_DIM = 384

# Embedding model — must match demo corpus (build_demo_core_collection, fiqa_api)
FASTEMBED_MODEL = os.getenv("FASTEMBED_MODEL", "BAAI/bge-small-en-v1.5")
SBERT_MODEL = os.getenv("SBERT_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_embedder():
    """Get embedder: fastembed first, else SentenceTransformer. Same as build_demo_core_collection."""
    try:
        from fastembed import TextEmbedding
        model = TextEmbedding(model_name=FASTEMBED_MODEL)
        logger.info(f"Using fastembed: {FASTEMBED_MODEL}")
        return model, "fastembed"
    except Exception as e:
        logger.warning(f"fastembed failed: {e}")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(SBERT_MODEL)
        logger.info(f"Using sentence_transformers: {SBERT_MODEL}")
        return model, "sbert"
    except Exception as e:
        logger.warning(f"sentence_transformers failed: {e}")
    raise RuntimeError("No embedding backend. Install fastembed or sentence-transformers.")


def infer_topic(source_path: str) -> str:
    """Infer topic from filename, e.g. dmv_sr22_explanations.md -> dmv_sr22."""
    name = Path(source_path).stem
    if "dmv" in name.lower() or "sr22" in name.lower() or "sr_22" in name.lower():
        return "dmv_sr22"
    if "notice" in name.lower() and "interpret" in name.lower():
        return "notice_interpretation"
    if "declaration" in name.lower() or "garaging" in name.lower():
        return "declaration_page_garaging"
    return name.replace(" ", "_").lower()[:32]


def chunk_by_section(md_path: Path) -> list[dict]:
    """
    Chunk markdown by ## headings. Each chunk gets title + content.
    Returns list of {"title": str, "content": str, "source_path": str}.
    """
    text = md_path.read_text(encoding="utf-8")
    chunks = []
    current_title = "Overview"
    current_content: list[str] = []
    source_path = str(md_path.relative_to(REPO_ROOT))

    for line in text.split("\n"):
        if line.startswith("## "):
            # Flush previous chunk
            content = "\n".join(current_content).strip()
            if content:
                chunks.append({
                    "title": current_title,
                    "content": content,
                    "source_path": source_path,
                })
            current_title = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)

    content = "\n".join(current_content).strip()
    if content:
        chunks.append({
            "title": current_title,
            "content": content,
            "source_path": source_path,
        })

    return chunks


def make_point_id(source_path: str, chunk_index: int, content_preview: str) -> str:
    """Deterministic ID for upsert idempotency."""
    raw = f"knowledge:{source_path}:{chunk_index}:{content_preview[:80]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def get_qdrant_client():
    """Initialize Qdrant client. Same env logic as build_demo_core_collection."""
    from qdrant_client import QdrantClient

    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_url = None if os.getenv("USE_LOCAL_QDRANT") == "1" else os.getenv("QDRANT_URL")
    qdrant_api_key = None if os.getenv("USE_LOCAL_QDRANT") == "1" else os.getenv("QDRANT_API_KEY")

    kwargs = {"check_compatibility": False}  # Avoid client/server version mismatch warning
    if qdrant_url and (qdrant_url.startswith("http://") or qdrant_url.startswith("https://")):
        logger.info(f"Connecting to Qdrant at {qdrant_url}")
        kwargs["url"] = qdrant_url
        if qdrant_api_key:
            kwargs["api_key"] = qdrant_api_key
        return QdrantClient(**kwargs)
    logger.info(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}")
    kwargs["host"] = qdrant_host
    kwargs["port"] = qdrant_port
    return QdrantClient(**kwargs)


def ensure_collection(client, collection_name: str, vector_size: int):
    """Create collection if it does not exist."""
    from qdrant_client.models import Distance, VectorParams

    collections = client.get_collections()
    if any(c.name == collection_name for c in collections.collections):
        logger.info(f"Collection {collection_name} exists, skipping creation")
        return
    logger.info(f"Creating collection {collection_name} (vector_size={vector_size})")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    logger.info(f"Collection {collection_name} created")


def main():
    parser = argparse.ArgumentParser(description="Ingest insurance knowledge into Qdrant")
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Single .md file or directory. Default: knowledge/industries/insurance/",
    )
    parser.add_argument("--collection", type=str, default=COLLECTION_NAME)
    parser.add_argument("--dry-run", action="store_true", help="Chunk and embed only, no upsert")
    args = parser.parse_args()

    # Resolve source paths
    if args.source:
        src = Path(args.source)
        if src.is_file():
            paths = [src] if src.suffix == ".md" else []
        else:
            paths = sorted(src.glob("*.md"))
    else:
        paths = sorted(KNOWLEDGE_INSURANCE.glob("*.md")) if KNOWLEDGE_INSURANCE.exists() else []

    # Exclude README
    paths = [p for p in paths if p.name != "README.md"]
    if not paths:
        logger.error("No .md files found. Use --source or ensure knowledge/industries/insurance/*.md exists.")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Ingest Insurance Knowledge")
    logger.info("=" * 60)
    logger.info(f"Sources: {[str(p.relative_to(REPO_ROOT)) for p in paths]}")
    logger.info(f"Collection: {args.collection}")
    logger.info("")

    # Chunk
    all_chunks = []
    for p in paths:
        chunks = chunk_by_section(p)
        all_chunks.extend(chunks)
        logger.info(f"  {p.name}: {len(chunks)} chunks")

    if not all_chunks:
        logger.error("No chunks produced")
        sys.exit(1)

    # Embed
    logger.info("")
    logger.info("Initializing embedder...")
    model, backend = get_embedder()
    texts = [f"{c['title']}\n{c['content']}" for c in all_chunks]

    import numpy as np
    if backend == "fastembed":
        embeddings = np.array(list(model.embed(texts)))
    else:
        embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    if embeddings.shape[1] != EMBEDDING_DIM:
        logger.warning(f"Embedding dim {embeddings.shape[1]} may not match collection ({EMBEDDING_DIM})")

    if args.dry_run:
        logger.info("DRY RUN: Skipping Qdrant upsert")
        for i, c in enumerate(all_chunks):
            logger.info(f"  Chunk {i+1}: {c['title'][:50]}... ({len(c['content'])} chars)")
        return

    # Upsert
    client = get_qdrant_client()
    ensure_collection(client, args.collection, embeddings.shape[1])

    from qdrant_client.models import PointStruct

    points = []
    for i, (chunk, emb) in enumerate(zip(all_chunks, embeddings)):
        point_id = make_point_id(chunk["source_path"], i, chunk["content"])
        points.append(
            PointStruct(
                id=point_id,
                vector=emb.tolist(),
                payload={
                    "doc_id": point_id,
                    "title": chunk["title"],
                    "text": chunk["content"],
                    "source_path": chunk["source_path"],
                    "knowledge_pack": "insurance",
                    "client_pack": None,
                    "topic": infer_topic(chunk["source_path"]),
                    "chunk_title": chunk["title"],
                    "content_type": "knowledge",
                },
            )
        )

    batch_size = 50
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=args.collection, points=batch)
        logger.info(f"  Upserted batch {i // batch_size + 1}/{(len(points) - 1) // batch_size + 1} ({len(batch)} points)")

    info = client.get_collection(args.collection)
    logger.info("")
    logger.info("=" * 60)
    logger.info("Ingest Complete")
    logger.info("=" * 60)
    logger.info(f"Chunks: {len(all_chunks)} | Points in collection: {info.points_count}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
