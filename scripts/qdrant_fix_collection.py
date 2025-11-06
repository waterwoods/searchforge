#!/usr/bin/env python3
"""
Qdrant Collection Resolver - Read-only discovery and auto-resolution
Safely finds the best existing collection and persists it to runtime_settings.json
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


def get_qdrant_url():
    """Get Qdrant URL from env or default"""
    return os.environ.get("QDRANT_URL", "http://localhost:6333")


def list_collections(url):
    """
    Read-only: List all collections from Qdrant
    Returns: [{name, points_count, vector_size, distance}, ...]
    """
    try:
        req = urllib.request.Request(f"{url}/collections", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            collections = []
            
            for coll in data.get("result", {}).get("collections", []):
                name = coll.get("name")
                if not name:
                    continue
                
                # Get collection details for points_count
                try:
                    detail_req = urllib.request.Request(f"{url}/collections/{name}", method="GET")
                    with urllib.request.urlopen(detail_req, timeout=3) as detail_resp:
                        detail_data = json.loads(detail_resp.read().decode('utf-8'))
                        result = detail_data.get("result", {})
                        
                        points_count = result.get("points_count", 0)
                        vectors_config = result.get("config", {}).get("params", {}).get("vectors", {})
                        
                        # Handle both dict and simple config
                        if isinstance(vectors_config, dict):
                            if "size" in vectors_config:
                                vector_size = vectors_config.get("size", 0)
                                distance = vectors_config.get("distance", "Unknown")
                            else:
                                # Multiple vectors, take first one
                                first_vec = next(iter(vectors_config.values()), {})
                                vector_size = first_vec.get("size", 0)
                                distance = first_vec.get("distance", "Unknown")
                        else:
                            vector_size = 0
                            distance = "Unknown"
                        
                        collections.append({
                            "name": name,
                            "points_count": points_count,
                            "vector_size": vector_size,
                            "distance": distance
                        })
                except Exception as e:
                    print(f"[WARN] Failed to get details for {name}: {e}", file=sys.stderr)
                    collections.append({
                        "name": name,
                        "points_count": 0,
                        "vector_size": 0,
                        "distance": "Unknown"
                    })
            
            return collections
            
    except urllib.error.URLError as e:
        print(f"[ERROR] Cannot connect to Qdrant at {url}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[ERROR] Failed to list collections: {e}", file=sys.stderr)
        return []


def resolve_best(collections):
    """
    Resolve best collection based on:
    1. Max points_count (exclude 0)
    2. Tie-break by name priority: ["fiqa", "beir", "qa", "search"]
    
    Returns: collection name or None
    """
    if not collections:
        return None
    
    # Filter out empty collections
    candidates = [c for c in collections if c["points_count"] > 0]
    
    if not candidates:
        print("[WARN] All collections have 0 points", file=sys.stderr)
        return None
    
    # Priority keywords (case-insensitive)
    priorities = ["fiqa", "beir", "qa", "search"]
    
    def score(coll):
        """
        Score function: (points_count, priority_index)
        Higher points_count is better, lower priority_index is better
        """
        name_lower = coll["name"].lower()
        priority_idx = 999  # Default low priority
        
        for i, keyword in enumerate(priorities):
            if keyword in name_lower:
                priority_idx = i
                break
        
        return (coll["points_count"], -priority_idx)
    
    # Sort by score descending
    candidates.sort(key=score, reverse=True)
    
    return candidates[0]["name"]


def print_table(collections):
    """Print collections as a formatted table"""
    if not collections:
        print("No collections found.")
        return
    
    print("\n┌─────────────────────────────────┬────────────┬────────────┬──────────┐")
    print("│ Collection Name                 │ Points     │ Vector Dim │ Distance │")
    print("├─────────────────────────────────┼────────────┼────────────┼──────────┤")
    
    for c in collections:
        name = c["name"][:31]  # Truncate long names
        points = f"{c['points_count']:,}"
        vec_size = str(c["vector_size"]) if c["vector_size"] > 0 else "—"
        distance = c["distance"][:10]
        
        print(f"│ {name:<31} │ {points:>10} │ {vec_size:>10} │ {distance:<8} │")
    
    print("└─────────────────────────────────┴────────────┴────────────┴──────────┘\n")


def save_runtime_settings(collection_name, repo_root):
    """Save resolved collection to runtime_settings.json"""
    settings = {
        "qdrant_collection": collection_name,
        "resolved_at": datetime.now(timezone.utc).isoformat()
    }
    
    settings_path = repo_root / "runtime_settings.json"
    
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)
    
    return settings_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Qdrant Collection Resolver - Read-only discovery"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only list collections, don't apply"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Resolve and save to runtime_settings.json"
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        parser.error("Must specify either --dry-run or --apply")
    
    # Get repo root (script is in scripts/, root is parent)
    repo_root = Path(__file__).parent.parent
    
    # Get Qdrant URL
    url = get_qdrant_url()
    print(f"[QDRANT] url={url}")
    
    # List collections (read-only)
    print("[DISCOVER] Fetching collections...")
    collections = list_collections(url)
    
    if not collections:
        print("[ERROR] No collections found or cannot connect to Qdrant", file=sys.stderr)
        sys.exit(1)
    
    # Sort by points_count descending for display
    collections.sort(key=lambda c: c["points_count"], reverse=True)
    
    if args.dry_run:
        print_table(collections)
        
        # Show what would be selected
        best = resolve_best(collections)
        if best:
            print(f"[DRY-RUN] Would select: {best}")
        else:
            print("[DRY-RUN] No valid collection (all have 0 points)")
        
        sys.exit(0)
    
    if args.apply:
        print_table(collections)
        
        best = resolve_best(collections)
        
        if not best:
            print("[ERROR] Cannot resolve collection: all have 0 points", file=sys.stderr)
            sys.exit(1)
        
        # Save to runtime_settings.json
        settings_path = save_runtime_settings(best, repo_root)
        
        # Get selected collection details for summary
        selected = next((c for c in collections if c["name"] == best), None)
        points = selected["points_count"] if selected else 0
        
        print(f"[FIX] resolved collection: {best} | points={points:,} | saved to {settings_path}")
        
        sys.exit(0)


if __name__ == "__main__":
    main()

