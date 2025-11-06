#!/usr/bin/env python3
"""
embed_doctor.py - Embedding Model Consistency Checker
=====================================================
Validates embedding model consistency between API and collection metadata.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)


def get_api_embed_info(api_url: str) -> dict:
    """Get embedding info from API health endpoint."""
    try:
        response = requests.get(f"{api_url}/api/health/embeddings", timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "ok": data.get("ok", False),
            "model": data.get("model", "unknown"),
            "dim": data.get("dim"),
            "backend": data.get("backend", "unknown")
        }
    except requests.exceptions.RequestException as e:
        return {
            "ok": False,
            "error": str(e)
        }


def get_collection_embed_info(
    qdrant_host: str,
    qdrant_port: int,
    collection: str,
    config_dir: str = "configs/collection_tags"
) -> dict:
    """Get embedding info from collection metadata or config file."""
    # Try to get from config file first
    config_path = Path(config_dir) / f"{collection}.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {
                    "model": config.get("embed_model"),
                    "dim": config.get("dim"),
                    "source": "config_file"
                }
        except Exception as e:
            print(f"WARNING: Failed to read config file: {e}", file=sys.stderr)
    
    # Try to get from Qdrant collection info
    base_url = f"http://{qdrant_host}:{qdrant_port}"
    try:
        response = requests.get(f"{base_url}/collections/{collection}", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract vector size (dimension)
        config = data.get("result", {}).get("config", {})
        params = config.get("params", {})
        vectors = params.get("vectors", {})
        
        dim = None
        if isinstance(vectors, dict):
            dim = vectors.get("size")
        elif hasattr(vectors, 'size'):
            dim = vectors.size
        
        # Try to get model info from collection metadata
        # (This is custom - collections may not have this)
        metadata = data.get("result", {}).get("config", {}).get("metadata", {})
        model = metadata.get("embed_model")
        
        return {
            "model": model,
            "dim": dim,
            "source": "qdrant_collection"
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "source": "qdrant_error"
        }


def main():
    parser = argparse.ArgumentParser(description="Check embedding model consistency")
    parser.add_argument("--collection", help="Collection name")
    parser.add_argument("--dataset-name", help="Dataset name (will resolve collection if not provided)")
    parser.add_argument("--api-url", default=None, help="API base URL (default: read from env or docker-compose.yml)")
    parser.add_argument("--api", help="Short alias for --api-url")
    parser.add_argument("--qdrant-host", default="qdrant", help="Qdrant host")
    parser.add_argument("--qdrant-port", type=int, default=6333, help="Qdrant port")
    parser.add_argument("--config-dir", default="configs/collection_tags", help="Config directory for collection tags")
    parser.add_argument("--create-config", action="store_true", help="Create config file if missing")
    parser.add_argument("--out", default="reports/embed_consistency.json", help="Output JSON report path")
    
    args = parser.parse_args()
    
    # Resolve collection from dataset if provided
    collection = args.collection
    if args.dataset_name and not collection:
        # Try to resolve from presets
        try:
            presets_path = Path("configs/presets_v10.json")
            if presets_path.exists():
                with open(presets_path, 'r') as f:
                    presets = json.load(f)
                    for preset in presets.get("presets", []):
                        if preset.get("dataset_name") == args.dataset_name:
                            collection = preset.get("collection") or args.dataset_name
                            break
        except Exception:
            pass
        if not collection:
            collection = args.dataset_name  # Default: dataset name matches collection
    
    if not collection:
        print("ERROR: Must provide --collection or --dataset-name", file=sys.stderr)
        print("  Example: --collection fiqa_50k_v1", file=sys.stderr)
        print("  Or: --dataset-name fiqa_50k_v1 (will use dataset name as collection)", file=sys.stderr)
        sys.exit(1)
    
    # Resolve API URL: args.api > args.api_url > env var > default
    api_url = args.api or args.api_url
    if not api_url:
        api_url = os.getenv("API_BASE") or os.getenv("RAG_API_BASE")
        if not api_url:
            # Try to read from docker-compose.yml (simple string parsing)
            try:
                compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
                if compose_path.exists():
                    with open(compose_path, 'r') as f:
                        content = f.read()
                        # Look for port mapping like "100.67.88.114:8000:8000" or just ":8000:8000"
                        import re
                        match = re.search(r':(\d+):8000', content)
                        if match:
                            port = match.group(1)
                            api_url = f"http://andy-wsl:{port}"
            except Exception:
                pass
        if not api_url:
            api_url = "http://andy-wsl:8000"  # Default from user's prompt
    
    # Get API embedding info
    print(f"Fetching embedding info from API: {api_url}...")
    api_info = get_api_embed_info(api_url)
    
    if not api_info.get("ok"):
        print(f"ERROR: API health check failed: {api_info.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)
    
    print(f"API: model={api_info['model']}, dim={api_info['dim']}, backend={api_info['backend']}")
    
    # Get collection embedding info
    print(f"Fetching collection info from Qdrant: {collection}...")
    coll_info = get_collection_embed_info(
        args.qdrant_host,
        args.qdrant_port,
        collection,
        config_dir=args.config_dir
    )
    
    if "error" in coll_info:
        print(f"ERROR: Failed to get collection info: {coll_info['error']}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Collection: model={coll_info.get('model', 'N/A')}, dim={coll_info.get('dim', 'N/A')}, source={coll_info.get('source')}")
    
    # Compare
    model_match = api_info["model"] == coll_info.get("model") or (
        coll_info.get("model") is None and args.create_config
    )
    dim_match = api_info["dim"] == coll_info.get("dim")
    
    status = "PASS" if (model_match and dim_match) else "FAIL"
    
    report = {
        "collection": collection,
        "api": api_info,
        "collection": coll_info,
        "comparison": {
            "model_match": model_match,
            "dim_match": dim_match,
            "status": status
        }
    }
    
    # If model info missing and create_config is set, create config file
    if not coll_info.get("model") and args.create_config:
        config_path = Path(args.config_dir) / f"{args.collection}.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_data = {
            "embed_model": api_info["model"],
            "dim": api_info["dim"],
            "backend": api_info["backend"]
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        print(f"Created config file: {config_path}")
        report["config_created"] = str(config_path)
    
    # Write report
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Model match: {model_match}")
    print(f"Dimension match: {dim_match}")
    print(f"Status: {status}")
    print(f"Report written to: {out_path}")
    print(f"{'='*60}")
    
    if status != "PASS":
        print(f"ERROR: Embedding model inconsistency detected", file=sys.stderr)
        print(f"  API: model={api_info.get('model')}, dim={api_info.get('dim')}", file=sys.stderr)
        print(f"  Collection: model={coll_info.get('model')}, dim={coll_info.get('dim')}", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()

