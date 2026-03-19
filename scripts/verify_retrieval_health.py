#!/usr/bin/env python3
"""
Verify Retrieval Health — Runtime check for notice explanation retrieval.
==============================================================
Checks that retrieval dependencies (embedder + Qdrant) are ready and that
notice_interpretation / dmv_sr22 knowledge chunks are retrievable.

Usage:
  PYTHONPATH=. python3 scripts/verify_retrieval_health.py
  PYTHONPATH=. python3 scripts/verify_retrieval_health.py --live  # against running API on 8001

Use after: scripts/ingest_insurance_knowledge.py (ensure knowledge is ingested)
Use when: diagnosing retrieval-active vs fallback mode for english_notice_confusion

See: docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv()
    p = REPO_ROOT / ".env.cloudrun"
    if p.exists():
        load_dotenv(p, override=True)
except ImportError:
    pass


def check_live_api(port: int = 8001) -> dict:
    """Check retrieval readiness via live API health/ready endpoints."""
    import urllib.request
    base = f"http://127.0.0.1:{port}"
    result = {"ok": False, "ready": False, "retrieval_ready": False, "error": None}
    try:
        with urllib.request.urlopen(f"{base}/ready", timeout=5) as r:
            data = json.loads(r.read().decode())
            result["ready"] = data.get("ok", False)
            clients = data.get("clients", {})
            result["embedding_model"] = clients.get("embedding_model", False)
            result["qdrant_connected"] = clients.get("qdrant_connected", False)
            result["retrieval_ready"] = result["embedding_model"] and result["qdrant_connected"]
            result["ok"] = result["ready"]
    except Exception as e:
        result["error"] = str(e)
    return result


def check_standalone() -> dict:
    """
    Check retrieval path in standalone mode (no app warmup).
    Validates: embedder + Qdrant + notice_interpretation chunks are retrievable.
    """
    result = {"ok": False, "embedder_ok": False, "qdrant_ok": False, "probe_ok": False, "error": None}
    try:
        # First try via notice_retrieval (works if run inside app after warmup)
        from services.fiqa_api.inbox_triage.notice_retrieval import retrieve_notice_explanation
        snippet = retrieve_notice_explanation("What does payment failed mean?")
        if snippet and len(snippet) > 20:
            result["probe_ok"] = True
            result["embedder_ok"] = True
            result["qdrant_ok"] = True
            result["ok"] = True
            return result

        # Fallback: run test_knowledge_retrieval as subprocess (standalone path)
        # Check both notice path and document path
        import subprocess
        both_ok = True
        for query in ["What does payment failed mean?", "What is declaration page?"]:
            proc = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "test_knowledge_retrieval.py"),
                 "--query", query],
                cwd=str(REPO_ROOT),
                env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
                capture_output=True,
                timeout=60,
            )
            if proc.returncode != 0:
                both_ok = False
                if proc.stderr:
                    result["error"] = proc.stderr.decode()[:200]
                break
        result["probe_ok"] = both_ok
        result["embedder_ok"] = result["probe_ok"]
        result["qdrant_ok"] = result["probe_ok"]
        result["ok"] = result["probe_ok"]
        if proc.returncode != 0 and proc.stderr:
            result["error"] = (proc.stderr.decode()[:200] if proc.stderr else "query failed")
    except subprocess.TimeoutExpired:
        result["error"] = "test_knowledge_retrieval timed out"
    except Exception as e:
        result["error"] = str(e)
    return result


def main():
    parser = argparse.ArgumentParser(description="Verify retrieval health for notice explanation")
    parser.add_argument("--live", action="store_true", help="Check against live API on 8001")
    parser.add_argument("--port", type=int, default=8001, help="Port when using --live")
    args = parser.parse_args()

    print("=" * 60)
    print("Retrieval Health Verification")
    print("=" * 60)

    if args.live:
        print("Mode: live API")
        r = check_live_api(args.port)
        if r.get("error"):
            print(f"  ERROR: {r['error']}")
            sys.exit(1)
        print(f"  ready: {r.get('ready', False)}")
        print(f"  embedding_model: {r.get('embedding_model', False)}")
        print(f"  qdrant_connected: {r.get('qdrant_connected', False)}")
        print(f"  retrieval_ready: {r.get('retrieval_ready', False)}")
        ok = r.get("retrieval_ready", False)
    else:
        print("Mode: standalone (same process as triage)")
        r = check_standalone()
        if r.get("error"):
            print(f"  ERROR: {r['error']}")
            sys.exit(1)
        print(f"  retrieval_ready: {r.get('retrieval_ready', False)}")
        print(f"  probe_ok (payment failed query): {r.get('probe_ok', False)}")
        ok = r.get("ok", False)

    print("=" * 60)
    if ok:
        print("PASS: Retrieval is healthy. Notice explanation will use retrieval when available.")
    else:
        print("FAIL: Retrieval not ready. Notice explanation will use template-only fallback.")
        print("  Fix: Ensure embedder warmup completed and Qdrant is reachable.")
        print("  See: docs/RETRIEVAL_KNOWLEDGE_LAYER_FOUNDATION.md, scripts/restore_8001_readiness.sh")
    print("=" * 60)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
