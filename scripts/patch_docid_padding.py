#!/usr/bin/env python3
import os, sys, re, json, argparse

from typing import Optional, List

from qdrant_client import QdrantClient


def iter_points(client: QdrantClient, coll: str, limit: int = 512):
    offset = None
    while True:
        points, offset = client.scroll(
            coll,
            with_payload=True,
            with_vectors=False,
            limit=limit,
            offset=offset,
        )
        if not points:
            break
        yield points
        if offset is None:
            break


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--collection", required=True)
    p.add_argument("--length", type=int, default=6)
    p.add_argument("--assert-only", action="store_true")
    p.add_argument("--batch", type=int, default=512)
    p.add_argument("--url", default=os.getenv("QDRANT_URL", os.getenv("QDRANT_BASE_URL", "http://qdrant:6333")))
    args = p.parse_args()

    client = QdrantClient(url=args.url, prefer_grpc=False)
    want = re.compile(rf"^\d{{{args.length}}}$")

    seen = patched = bad = 0
    # 修补 / 断言
    for chunk in iter_points(client, args.collection, limit=args.batch):
        for pt in chunk:
            seen += 1
            raw = pt.payload.get("doc_id")
            new_val = None
            if isinstance(raw, int):
                new_val = f"{raw:0{args.length}d}"
            elif isinstance(raw, str):
                if raw.isdigit():
                    if not want.match(raw):
                        new_val = raw.zfill(args.length)
                else:
                    bad += 1
            else:
                # 缺失时用 point id（若是 int）
                if isinstance(pt.id, int):
                    new_val = f"{pt.id:0{args.length}d}"
                else:
                    bad += 1

            if args.assert_only:
                # 断言模式遇到第一条不合规即失败退出
                check_val = str(raw) if raw is not None else ""
                if new_val is not None or (check_val and not want.match(check_val)):
                    print(json.dumps({"ok": False, "sample_id": pt.id, "doc_id": raw, "expected_format": f"^\\d{{{args.length}}}$"}, ensure_ascii=False))
                    sys.exit(2)
                continue

            if new_val is not None:
                client.set_payload(args.collection, payload={"doc_id": new_val}, points=[pt.id])
                patched += 1

    # 最终抽检最多 1000 条
    checked = 0
    ok = True
    for chunk in iter_points(client, args.collection, limit=args.batch):
        for pt in chunk:
            val = pt.payload.get("doc_id")
            if not isinstance(val, str) or not want.match(val):
                ok = False
                break
            checked += 1
            if checked >= 1000:
                break
        if checked >= 1000 or not ok:
            break

    print(json.dumps({
        "collection": args.collection,
        "seen": seen,
        "patched": patched,
        "bad_samples": bad,
        "ok": ok
    }, ensure_ascii=False))
    sys.exit(0 if ok or args.assert_only else 1)


if __name__ == "__main__":
    main()

