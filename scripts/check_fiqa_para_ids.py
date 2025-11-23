#!/usr/bin/env python3
"""
Verify doc_id values in Qdrant match manifest exactly.

Checks:
1. Points count matches expected (50000)
2. Sample doc_ids from manifest can be retrieved from Qdrant with exact match
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue


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


def load_sample_doc_ids(corpus_path: Path, count: int = 5) -> List[str]:
    """Load first N doc_ids from corpus file."""
    doc_ids = []
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            if len(doc_ids) >= count:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                doc_id = obj.get("doc_id")
                if doc_id:
                    doc_ids.append(str(doc_id))
            except json.JSONDecodeError:
                continue
    return doc_ids


def infer_corpus_path(manifest_path: Path, manifest: Dict[str, Any]) -> Path:
    """Infer corpus file path from manifest location."""
    manifest_dir = manifest_path.parent
    
    # Try fiqa_50k_v1/corpus.jsonl first
    corpus_path = manifest_dir / "fiqa_50k_v1" / "corpus.jsonl"
    if corpus_path.exists():
        return corpus_path
    
    # Fallback to corpus_50k_v1.jsonl
    corpus_path = manifest_dir / "corpus_50k_v1.jsonl"
    if corpus_path.exists():
        return corpus_path
    
    raise FileNotFoundError(f"Could not find corpus file")


def check_collection(
    client: QdrantClient,
    collection_name: str,
    expected_count: int,
    sample_doc_ids: List[str]
) -> bool:
    """Check collection points count and verify sample doc_ids."""
    print(f"[INFO] Checking collection: {collection_name}")
    
    # Get collection info
    try:
        collection_info = client.get_collection(collection_name)
        points_count = collection_info.points_count
        print(f"[INFO] Points count: {points_count} (expected: {expected_count})")
        
        if points_count != expected_count:
            print(f"[ERROR] Points count mismatch: expected {expected_count}, got {points_count}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to get collection info: {e}")
        return False
    
    # Verify sample doc_ids
    print(f"[INFO] Verifying {len(sample_doc_ids)} sample doc_ids...")
    all_match = True
    
    for doc_id in sample_doc_ids:
        # Query by doc_id filter
        try:
            results, _ = client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="doc_id",
                            match=MatchValue(value=doc_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
                with_vectors=False
            )
            
            if not results:
                print(f"[ERROR] doc_id '{doc_id}' not found in collection")
                all_match = False
                continue
            
            # Check that the doc_id in payload matches exactly
            found_doc_id = results[0].payload.get("doc_id")
            if found_doc_id != doc_id:
                print(f"[ERROR] doc_id mismatch: expected '{doc_id}', got '{found_doc_id}'")
                all_match = False
            else:
                print(f"[OK] doc_id '{doc_id}' verified (exact match)")
        
        except Exception as e:
            print(f"[ERROR] Failed to query doc_id '{doc_id}': {e}")
            all_match = False
    
    return all_match


def main():
    parser = argparse.ArgumentParser(
        description="Verify fiqa_para_50k collection doc_ids match manifest"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="fiqa_para_50k",
        help="Collection name (default: fiqa_para_50k)"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/fiqa_v1/manifest_50k_v1.json",
        help="Path to manifest file (default: data/fiqa_v1/manifest_50k_v1.json)"
    )
    parser.add_argument(
        "--qdrant-url",
        type=str,
        default="http://andy-wsl:6333",
        help="Qdrant URL (default: http://andy-wsl:6333)"
    )
    parser.add_argument(
        "--sample-count",
        type=int,
        default=5,
        help="Number of sample doc_ids to verify (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Find repo root
    repo_root = find_repo_root()
    
    # Load manifest
    manifest_path = (repo_root / args.manifest).resolve()
    if not manifest_path.exists():
        print(f"[ERROR] Manifest file not found: {manifest_path}")
        sys.exit(1)
    
    print(f"[INFO] Loading manifest: {manifest_path}")
    manifest = load_manifest(manifest_path)
    expected_count = manifest.get("size", 50000)
    print(f"[INFO] Expected points count: {expected_count}")
    
    # Get sample doc_ids from corpus
    corpus_path = infer_corpus_path(manifest_path, manifest)
    print(f"[INFO] Loading sample doc_ids from: {corpus_path}")
    sample_doc_ids = load_sample_doc_ids(corpus_path, count=args.sample_count)
    print(f"[INFO] Sample doc_ids: {sample_doc_ids}")
    
    if len(sample_doc_ids) < args.sample_count:
        print(f"[WARN] Only found {len(sample_doc_ids)} doc_ids, expected {args.sample_count}")
    
    # Connect to Qdrant
    print(f"[INFO] Connecting to Qdrant: {args.qdrant_url}")
    client = QdrantClient(url=args.qdrant_url)
    
    # Check collection
    success = check_collection(
        client,
        args.collection,
        expected_count,
        sample_doc_ids
    )
    
    if success:
        print(f"\n{'='*60}")
        print("✅ All checks passed!")
        print(f"   Collection: {args.collection}")
        print(f"   Points count: {expected_count} ✓")
        print(f"   Sample doc_ids verified: {len(sample_doc_ids)} ✓")
        print(f"{'='*60}")
        sys.exit(0)
    else:
        print(f"\n{'='*60}")
        print("❌ Verification failed!")
        print(f"{'='*60}")
        sys.exit(1)


if __name__ == "__main__":
    main()

