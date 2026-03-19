#!/usr/bin/env python3
"""
Snapshot golden demo answers from running backend for offline fallback.
POSTs 5 broker questions to /api/query, saves JSON to ui/src/assets/demo_fallback.json.
Demo path: run_demo_local.sh → port 8001. Docker → --port 8000.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import requests

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "ui" / "src" / "assets" / "demo_fallback.json"

QUESTIONS = [
    "我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？",
    "我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？",
    "客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？",
    "客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？",
    "出险后理赔流程是怎样的？",
]


def main() -> None:
    p = argparse.ArgumentParser(description="Snapshot 5 broker answers for offline fallback")
    p.add_argument("--port", type=int, default=8001, help="Backend port")
    args = p.parse_args()
    backend = f"http://127.0.0.1:{args.port}"

    output_dir = OUTPUT_PATH.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    items = []
    for q in QUESTIONS:
        try:
            r = requests.post(
                f"{backend}/api/query",
                json={
                    "question": q,
                    "mode": "demo",
                    "translation_mode": "auto",
                    "top_k": 5,
                    "generate_answer": True,
                },
                timeout=60,
            )
            r.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            print("ERROR: Backend not reachable.", file=sys.stderr)
            print(f"  {backend} - is the backend running?", file=sys.stderr)
            print("  Start with: bash scripts/run_demo_local.sh", file=sys.stderr)
            print(f"  Detail: {e}", file=sys.stderr)
            sys.exit(1)
        except requests.exceptions.Timeout:
            print("ERROR: Backend request timed out.", file=sys.stderr)
            print(f"  {backend} - backend may be slow or overloaded.", file=sys.stderr)
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            print(f"ERROR: Backend returned HTTP {r.status_code}: {e}", file=sys.stderr)
            sys.exit(1)

        data = r.json()
        sources = data.get("sources") or data.get("results") or []
        sources_out = []
        for s in sources:
            url = s.get("source_url") or s.get("url") or ""
            domain = s.get("domain") or ""
            if not domain and url:
                try:
                    from urllib.parse import urlparse
                    domain = (urlparse(url).hostname or "").lower()
                except Exception:
                    pass
            sources_out.append({
                "domain": domain,
                "url": url,
                "snippet": (s.get("snippet") or s.get("text") or "")[:500],
            })
        items.append({
            "question": q,
            "answer": data.get("answer") or "",
            "sources": sources_out,
        })

    payload = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "backend": backend,
        "items": items,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(items)} items to {OUTPUT_PATH}")
    print(f"  Total sources: {sum(len(i['sources']) for i in items)}")


if __name__ == "__main__":
    main()
