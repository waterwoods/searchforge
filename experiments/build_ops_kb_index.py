#!/usr/bin/env python3
"""
build_ops_kb_index.py - CLI script to build Ops knowledge base vector index

Usage:
    python experiments/build_ops_kb_index.py [--recreate] [--collection-name OPS_KB]
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.ops_copilot.ops_rag_index import build_ops_kb_index

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    parser = argparse.ArgumentParser(
        description="Build vector index for Ops knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete existing collection before creating new one",
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default="ops_kb",
        help="Qdrant collection name (default: ops_kb)",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model name (default: sentence-transformers/all-MiniLM-L6-v2)",
    )
    
    args = parser.parse_args()
    
    try:
        build_ops_kb_index(
            collection_name=args.collection_name,
            recreate=args.recreate,
            embedding_model_name=args.embedding_model,
        )
        print(f"\n✅ Successfully built index: {args.collection_name}")
        return 0
    except Exception as e:
        print(f"\n❌ Failed to build index: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

