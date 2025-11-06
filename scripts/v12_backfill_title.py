#!/usr/bin/env python3
import argparse
from typing import Dict, Any, List, Tuple

from qdrant_client import QdrantClient


def _unpack_scroll(scroll_res):
    if isinstance(scroll_res, tuple):
        if len(scroll_res) == 2:
            return scroll_res[0], scroll_res[1], None
        if len(scroll_res) == 3:
            return scroll_res[0], scroll_res[1], scroll_res[2]
    return [], None, None


def backfill_titles(collection: str, host: str, port: int, batch: int) -> None:
    client = QdrantClient(host=host, port=port)

    total_scanned = 0
    total_updated = 0
    page_offset = None

    while True:
        scroll_res = client.scroll(
            collection_name=collection,
            with_payload=True,
            limit=batch,
            offset=page_offset,
        )
        points, page_offset, _ = _unpack_scroll(scroll_res)
        if not points:
            break

        for p in points:
            payload: Dict[str, Any] = p.payload or {}
            title = (payload.get("title") or "").strip()
            abstract = (payload.get("abstract") or "").strip()
            text = (payload.get("text") or "").strip()

            if not title:
                if abstract:
                    new_title = " ".join(abstract.split()[:16])
                elif text:
                    new_title = " ".join(text.split()[:16])
                else:
                    new_title = ""

                if new_title:
                    client.set_payload(
                        collection_name=collection,
                        payload={"title": new_title},
                        points=[p.id],
                    )
                    total_updated += 1

        total_scanned += len(points)

        if page_offset is None:
            break

    rate = (total_updated / max(1, total_scanned)) * 100.0
    print(f"[BACKFILL] scanned={total_scanned} updated={total_updated} rate={rate:.2f}%")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", default="fiqa_10k_v1")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=6333)
    parser.add_argument("--batch", type=int, default=1000)
    args = parser.parse_args()

    backfill_titles(args.collection, args.host, args.port, args.batch)


if __name__ == "__main__":
    main()
