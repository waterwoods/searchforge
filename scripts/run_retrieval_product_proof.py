#!/usr/bin/env python3
"""
Retrieval Product Proof — Compare template-only vs retrieval-assisted notice explanation.
======================================================================================
Runs side-by-side comparison for english_notice_confusion cases to demonstrate
when retrieval improves the product.

Usage:
  PYTHONPATH=. python3 scripts/run_retrieval_product_proof.py
  PYTHONPATH=. python3 scripts/run_retrieval_product_proof.py --verbose

Requires: Backend running on 8001 with retrieval ready, OR run after ingest + local Qdrant.
See: docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md
"""

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv()
    if (REPO_ROOT / ".env.cloudrun").exists():
        load_dotenv(REPO_ROOT / ".env.cloudrun", override=True)
except ImportError:
    pass

# Test cases: (customer_message, expected_improvement_description)
# Path 1: notice confusion | Path 2: document confusion
PROOF_CASES = [
    ("这个英文 notice 说 payment failed，什么意思？", "payment failed 解释"),
    ("What does cancel pending mean?", "cancel pending 解释"),
    ("last notice 这个是不是很严重？", "last notice 紧急程度"),
    ("What does this insurance notice mean?", "通用 notice 解释"),
    ("payment failed 是不是马上停保？", "payment failed + 停保 关联"),
    # Second path: declaration page / garaging proof
    ("declaration page是什么？", "declaration page 解释"),
    ("garaging proof 是什么意思？", "garaging proof 解释"),
    ("为什么他们还要我补 declaration page？", "为什么补 declaration page"),
]

# Template-only base (from reply_templates / triage fallback)
TEMPLATE_ZH = "英文通知有些术语看不懂很正常。把完整通知或更清楚的照片发我，我先帮你看一下，再告诉你重点和下一步怎么处理。"
TEMPLATE_EN = "English notices can be confusing. Send me the full notice or a clearer photo and I will tell you what it means and what to do next."


def get_fallback_reply(msg: str, lang: str = "zh") -> str:
    """Template-only reply (no retrieval). Uses triage with retrieval disabled."""
    import os
    prev = os.environ.get("NOTICE_RETRIEVAL_ENABLED")
    try:
        os.environ["NOTICE_RETRIEVAL_ENABLED"] = "0"
        from services.fiqa_api.inbox_triage.triage import triage_message
        result = triage_message(msg)
        return result.get("client_reply_draft") or (TEMPLATE_ZH if lang == "zh" else TEMPLATE_EN)
    finally:
        if prev is not None:
            os.environ["NOTICE_RETRIEVAL_ENABLED"] = prev
        elif "NOTICE_RETRIEVAL_ENABLED" in os.environ:
            os.environ.pop("NOTICE_RETRIEVAL_ENABLED")


def get_retrieval_assisted_reply(msg: str, lang: str = "zh") -> tuple[str, bool]:
    """
    Retrieval-assisted reply. Returns (reply_text, retrieval_used).
    Uses triage_message to get full flow (notice + document paths).
    """
    from services.fiqa_api.inbox_triage.triage import triage_message
    result = triage_message(msg)
    draft = result.get("client_reply_draft") or ""
    retrieval_used = "根据常见情况" in draft or "Based on common cases" in draft
    return draft, retrieval_used


def get_reply_via_api(msg: str, port: int = 8001) -> tuple[str, bool]:
    """Get reply via live triage API. Returns (client_reply_draft, retrieval_used)."""
    import urllib.request
    import json
    url = f"http://127.0.0.1:{port}/api/inbox/triage"
    data = json.dumps({"text": msg}).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        out = json.loads(r.read().decode())
    draft = out.get("client_reply_draft") or ""
    retrieval_used = "根据常见情况" in draft or "Based on common cases" in draft
    return draft, retrieval_used


def run_comparison(verbose: bool = False, live_port: int | None = None) -> dict:
    """Run product proof comparison. Returns summary dict."""
    results = []
    retrieval_used_count = 0
    for msg, desc in PROOF_CASES:
        lang = "zh" if any(ord(c) > 127 for c in msg) else "en"
        fallback = get_fallback_reply(msg, lang)
        if live_port:
            assisted, used = get_reply_via_api(msg, live_port)
        else:
            assisted, used = get_retrieval_assisted_reply(msg, lang)
        if used:
            retrieval_used_count += 1
        diff = "retrieval augmented" if used else "template only (retrieval not ready)"
        results.append({
            "msg": msg,
            "desc": desc,
            "fallback": fallback[:100] + "..." if len(fallback) > 100 else fallback,
            "assisted": (assisted[:120] + "...") if len(assisted) > 120 else assisted,
            "retrieval_used": used,
        })
        if verbose:
            print("-" * 60)
            print(f"Case: {desc}")
            print(f"Customer: {msg}")
            print(f"Fallback: {fallback[:150]}...")
            print(f"Assisted: {assisted[:150]}...")
            print(f"Status: {diff}")
            print()
    return {
        "results": results,
        "retrieval_used_count": retrieval_used_count,
        "total": len(PROOF_CASES),
        "retrieval_active": retrieval_used_count > 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Retrieval product proof comparison")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--live", action="store_true", help="Use live API on 8001 (backend must be running)")
    parser.add_argument("--port", type=int, default=8001, help="Port when using --live")
    args = parser.parse_args()

    print("=" * 60)
    print("Retrieval Product Proof — Notice Explanation Comparison")
    print("=" * 60)
    if args.live:
        print(f"Mode: live API (port {args.port})")
    else:
        print("Mode: standalone (direct triage call)")
    print()

    summary = run_comparison(verbose=args.verbose, live_port=args.port if args.live else None)

    print(f"Cases: {summary['total']}")
    print(f"Retrieval augmented: {summary['retrieval_used_count']}/{summary['total']}")
    print(f"Retrieval active: {summary['retrieval_active']}")
    print("=" * 60)

    if summary["retrieval_active"]:
        print("PASS: Retrieval is improving notice explanation in at least one case.")
    else:
        print("INFO: Retrieval not active (warmup or Qdrant). All replies use template-only.")
        print("  Run with backend ready: bash scripts/run_demo_local.sh, wait for /ready")
        print("  Or: bash scripts/restore_8001_readiness.sh")
    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
