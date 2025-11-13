#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

import requests


def env_bool(key: str) -> bool:
    raw = os.getenv(key)
    if not raw:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def delete_collection(session: requests.Session, detail_url: str) -> None:
    resp = session.delete(detail_url, timeout=5)
    if resp.status_code in (404,):
        return
    if resp.status_code >= 400:
        resp.raise_for_status()


def ensure_collection(
    session: requests.Session,
    base_url: str,
    collection: str,
    vector_dim: int,
    distance: str,
    force: bool,
) -> bool:
    detail_url = f"{base_url}/collections/{collection}"
    if force:
        delete_collection(session, detail_url)

    resp = session.get(detail_url, timeout=5)
    if resp.status_code == 200:
        payload = resp.json().get("result") or {}
        config = payload.get("config", {}).get("params", {}).get("vectors", {})
        size_matches = int(config.get("size", vector_dim)) == vector_dim
        distance_matches = str(config.get("distance", distance)).lower() == distance.lower()
        if size_matches and distance_matches and not force:
            return False
        delete_collection(session, detail_url)
        resp = session.get(detail_url, timeout=5)
    if resp.status_code not in (200, 404):
        resp.raise_for_status()

    payload = {
        "vectors": {
            "size": vector_dim,
            "distance": distance,
        }
    }
    create_resp = session.put(detail_url, json=payload, timeout=10)
    create_resp.raise_for_status()
    return True


def build_demo_points(vector_dim: int, total: int) -> List[Dict[str, Any]]:
    points: List[Dict[str, Any]] = []
    for idx in range(1, total + 1):
        vector = [0.0] * vector_dim
        vector[idx % vector_dim] = 1.0
        points.append(
            {
                "id": idx,
                "vector": vector,
                "payload": {
                    "title": f"Demo Document {idx}",
                    "text": f"Seeded vector for quick smoke test #{idx}",
                    "category": "demo" if idx % 2 else "tutorial",
                    "tags": ["seed", "demo"],
                },
            }
        )
    return points


def seed_points(session: requests.Session, base_url: str, collection: str, vector_dim: int) -> int:
    points = build_demo_points(vector_dim, total=16)
    resp = session.put(
        f"{base_url}/collections/{collection}/points?wait=true",
        json={"points": points},
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json().get("result") or {}
    return len(result.get("operation_id") and points or points)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed demo data into Qdrant collection")
    parser.add_argument("--force", action="store_true", help="Drop and recreate the collection before seeding")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    base_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection = os.getenv("COLLECTION", "fiqa_50k_v1")
    vector_dim = env_int("VECTOR_DIM", env_int("QDRANT_VECTOR_DIM", 384))
    distance = os.getenv("DISTANCE", "Cosine")
    force = args.force or env_bool("FORCE")

    session = requests.Session()
    created = ensure_collection(session, base_url, collection, vector_dim, distance, force)
    upserts = seed_points(session, base_url, collection, vector_dim)

    summary = {
        "created": created,
        "collection": collection,
        "upserts": upserts,
        "vector_dim": vector_dim,
        "distance": distance,
        "forced": force,
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - CLI helper
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        raise SystemExit(1)

