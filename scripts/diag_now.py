#!/usr/bin/env python3
"""
diag_now.py - Zero-Risk Diagnostics Script
===========================================
Read-only diagnostics that hits the running API to check:
1. Version alignment (server commit vs local git)
2. Readiness status (clients_ready, redis_connected, embedding_loaded)
3. Minimal usable query (POST /api/query)
4. Policy interface availability (GET /api/autotuner/status)

Output: Terminal summary + .runs/diag.json
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError

# Add project root to path to enable imports
_SCRIPT_DIR = Path(__file__).parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Try to import from _http_util
try:
    from scripts._http_util import fetch_json, wait_ready
except ImportError as e:
    print(f"ERROR: Could not import from scripts._http_util: {e}", file=sys.stderr)
    print(f"Project root: {_PROJECT_ROOT}", file=sys.stderr)
    print(f"Script dir: {_SCRIPT_DIR}", file=sys.stderr)
    sys.exit(1)


def get_local_git_commit() -> Optional[str]:
    """Get local git commit SHA (short)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=Path(__file__).parent.parent
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def check_version(base: str) -> Dict[str, Any]:
    """Check version endpoint and compare with local git commit."""
    result = {
        "version_ok": "unknown",
        "server_commit": None,
        "local_commit": None,
    }
    
    # Get local commit
    local_commit = get_local_git_commit()
    result["local_commit"] = local_commit
    
    # Check server version
    try:
        version_url = f"{base.rstrip('/')}/version"
        response = fetch_json(version_url, timeout=5.0, max_retry=2)
        server_commit = response.get("commit")
        result["server_commit"] = server_commit
        
        if server_commit and local_commit:
            # Compare commits (allow partial match for short SHA)
            if server_commit.startswith(local_commit) or local_commit.startswith(server_commit):
                result["version_ok"] = True
            else:
                result["version_ok"] = False
        elif server_commit or local_commit:
            # One is missing, can't compare
            result["version_ok"] = "unknown"
        else:
            result["version_ok"] = False
            
    except HTTPError as e:
        if e.code == 404:
            # Version endpoint not found - not fatal
            result["version_ok"] = "unknown"
            result["server_commit"] = None
        else:
            result["version_ok"] = False
            result["server_commit"] = None
    except Exception as e:
        result["version_ok"] = False
        result["server_commit"] = None
    
    return result


def check_readiness(base: str, timeout: int = 300, consecutive: int = 3, wait: bool = True) -> Dict[str, Any]:
    """Check readiness endpoint and extract key signals.
    
    Args:
        base: Base URL
        timeout: Maximum time to wait in seconds (if wait=True)
        consecutive: Number of consecutive successful checks required (if wait=True)
        wait: If True, wait for readiness; if False, just check current status
    """
    result = {
        "ready": False,
        "ready_reasons": {
            "clients_ready": False,
            "redis_connected": False,
            "qdrant_connected": False,
            "embedding_loaded": False,
        }
    }
    
    readyz_url = f"{base.rstrip('/')}/readyz"
    healthz_url = f"{base.rstrip('/')}/healthz"
    
    try:
        # For diagnostics, we want to check current status quickly
        # Only wait if explicitly requested
        if wait and timeout > 0:
            # Use wait_ready to ensure consecutive successful checks
            is_ready = wait_ready(base, timeout=timeout, consecutive=consecutive)
            # Fetch readiness response to get detailed reasons
            response = fetch_json(readyz_url, timeout=5.0, max_retry=1)
        else:
            # Just check current status without waiting
            try:
                response = fetch_json(readyz_url, timeout=5.0, max_retry=1)
                is_ready = response.get("clients_ready", False)
            except Exception:
                # If we can't fetch, return False with error details
                result["ready"] = False
                result["ready_error"] = "Could not fetch /readyz endpoint"
                return result
        
        result["ready"] = is_ready
        result["ready_reasons"]["clients_ready"] = response.get("clients_ready", False)
        
        # Extract client status details - check both clients dict and top-level fields
        clients = response.get("clients", {})
        
        # Check top-level fields first (added in ready.py lines 78-79)
        if "qdrant_connected" in response:
            result["ready_reasons"]["qdrant_connected"] = response["qdrant_connected"]
        elif "qdrant_connected" in clients:
            result["ready_reasons"]["qdrant_connected"] = clients["qdrant_connected"]
        else:
            result["ready_reasons"]["qdrant_connected"] = False
            
        if "redis_connected" in response:
            result["ready_reasons"]["redis_connected"] = response["redis_connected"]
        elif "redis_connected" in clients:
            result["ready_reasons"]["redis_connected"] = clients["redis_connected"]
        else:
            result["ready_reasons"]["redis_connected"] = False
        
        # Check embedding status - may be in clients dict or need to check /healthz
        if "embedding_ready" in clients:
            result["ready_reasons"]["embedding_loaded"] = clients["embedding_ready"]
        else:
            # Try to get from /healthz endpoint
            try:
                health_response = fetch_json(healthz_url, timeout=2.0, max_retry=1)
                result["ready_reasons"]["embedding_loaded"] = health_response.get("embedding_ready", False)
            except Exception:
                result["ready_reasons"]["embedding_loaded"] = False
                
    except Exception as e:
        result["ready"] = False
        result["ready_error"] = str(e)
    
    return result


def check_direct_query(base: str) -> Dict[str, Any]:
    """Check minimal query endpoint (POST /api/query)."""
    result = {
        "direct_query_ok": False,
        "direct_query_error": None,
        "latency_ms": None,
    }
    
    query_url = f"{base.rstrip('/')}/api/query"
    
    try:
        import time
        start_time = time.perf_counter()
        
        response = fetch_json(
            query_url,
            method="POST",
            json={"question": "ping", "budget_ms": 200},
            timeout=30.0,
            max_retry=1
        )
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        result["latency_ms"] = round(elapsed_ms, 2)
        
        # Check if response is successful and has sources
        if response.get("ok") and isinstance(response.get("sources"), list):
            sources = response["sources"]
            if len(sources) >= 1:
                result["direct_query_ok"] = True
            else:
                result["direct_query_ok"] = False
                result["direct_query_error"] = "empty_items"
        elif isinstance(response.get("sources"), list):
            # API responded correctly but query failed (e.g., missing dataset)
            # This is still valuable - API is working, just missing data
            ret_code = response.get("ret_code", "unknown")
            message = response.get("message", "")
            result["direct_query_ok"] = False
            result["direct_query_error"] = f"query_failed: {ret_code}"
            result["direct_query_message"] = message
            result["direct_query_ret_code"] = ret_code
        else:
            result["direct_query_ok"] = False
            result["direct_query_error"] = f"invalid_response: ok={response.get('ok')}"
            
    except HTTPError as e:
        result["direct_query_ok"] = False
        result["direct_query_error"] = f"HTTP_{e.code}"
        if hasattr(e, 'read'):
            try:
                error_body = e.read().decode('utf-8')
                result["direct_query_error_detail"] = error_body[:200]
            except:
                pass
    except URLError as e:
        result["direct_query_ok"] = False
        result["direct_query_error"] = f"connection_error: {str(e)[:100]}"
    except Exception as e:
        result["direct_query_ok"] = False
        result["direct_query_error"] = f"error: {str(e)[:100]}"
    
    return result


def check_autotuner_api(base: str) -> Dict[str, Any]:
    """Check autotuner status endpoint."""
    result = {
        "autotuner_api": "error",
    }
    
    autotuner_url = f"{base.rstrip('/')}/api/autotuner/status"
    
    try:
        response = fetch_json(autotuner_url, timeout=5.0, max_retry=1)
        
        # Check if response has policy field
        if "policy" in response:
            result["autotuner_api"] = "online"
            result["policy"] = response.get("policy")
        else:
            result["autotuner_api"] = "online"  # Still online, but no policy field
            result["policy"] = None
            
    except HTTPError as e:
        if e.code == 404:
            result["autotuner_api"] = "404"
        else:
            result["autotuner_api"] = f"HTTP_{e.code}"
    except Exception as e:
        result["autotuner_api"] = "error"
        result["autotuner_error"] = str(e)[:100]
    
    return result


def print_summary(diag: Dict[str, Any]) -> None:
    """Print terminal summary with green/red status indicators."""
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSTICS SUMMARY")
    print("=" * 60)
    
    # Version check
    version_ok = diag.get("version_ok")
    if version_ok is True:
        print("✅ version_ok: TRUE (aligned)")
    elif version_ok is False:
        print("❌ version_ok: FALSE (misaligned)")
        print(f"   Server: {diag.get('server_commit', 'N/A')}")
        print(f"   Local:  {diag.get('local_commit', 'N/A')}")
    else:
        print("⚠️  version_ok: UNKNOWN (cannot compare)")
        print(f"   Server: {diag.get('server_commit', 'N/A')}")
        print(f"   Local:  {diag.get('local_commit', 'N/A')}")
    
    # Readiness check
    ready = diag.get("ready", False)
    if ready:
        print("✅ ready: TRUE")
    else:
        print("❌ ready: FALSE")
    
    reasons = diag.get("ready_reasons", {})
    print(f"   clients_ready:    {'✅' if reasons.get('clients_ready') else '❌'}")
    print(f"   redis_connected:  {'✅' if reasons.get('redis_connected') else '❌'}")
    print(f"   qdrant_connected: {'✅' if reasons.get('qdrant_connected') else '❌'}")
    print(f"   embedding_loaded: {'✅' if reasons.get('embedding_loaded') else '❌'}")
    
    # Direct query check
    direct_query_ok = diag.get("direct_query_ok", False)
    if direct_query_ok:
        latency = diag.get("latency_ms")
        print(f"✅ direct_query_ok: TRUE (latency: {latency}ms)")
    else:
        error = diag.get("direct_query_error", "unknown")
        ret_code = diag.get("direct_query_ret_code")
        message = diag.get("direct_query_message", "")
        if ret_code:
            print(f"⚠️  direct_query_ok: FALSE ({error})")
            if message:
                print(f"   Message: {message}")
        else:
            print(f"❌ direct_query_ok: FALSE ({error})")
    
    # Autotuner API check
    autotuner_api = diag.get("autotuner_api", "error")
    if autotuner_api == "online":
        policy = diag.get("policy", "N/A")
        print(f"✅ autotuner_api: ONLINE (policy: {policy})")
    elif autotuner_api == "404":
        print("⚠️  autotuner_api: 404 (endpoint not found)")
    else:
        print(f"❌ autotuner_api: {autotuner_api}")
    
    print("=" * 60)
    print()


def main():
    parser = argparse.ArgumentParser(description="Zero-risk diagnostics for running API")
    parser.add_argument(
        "--base",
        type=str,
        default="http://andy-wsl:8000",
        help="Base URL (default: http://andy-wsl:8000, fallback: http://localhost:8000)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Readiness check timeout in seconds (default: 300)"
    )
    parser.add_argument(
        "--consecutive",
        type=int,
        default=3,
        help="Number of consecutive readiness checks required (default: 3)"
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        default=False,
        help="Wait for readiness (default: False, just check current status)"
    )
    
    args = parser.parse_args()
    
    # Fallback to localhost if andy-wsl fails
    base = args.base
    if base.startswith("http://andy-wsl") or base.startswith("https://andy-wsl"):
        # Try andy-wsl first, but we'll handle connection errors gracefully
        pass
    
    # Initialize diagnosis result
    diag: Dict[str, Any] = {
        "base": base,
        "ts": datetime.utcnow().isoformat() + "Z",
    }
    
    # (a) Version check
    print("[1/4] Checking version alignment...")
    version_result = check_version(base)
    diag.update(version_result)
    
    # (b) Readiness check
    if args.wait:
        print(f"[2/4] Checking readiness (waiting, timeout={args.timeout}s, consecutive={args.consecutive})...")
    else:
        print("[2/4] Checking readiness (current status only)...")
    try:
        readiness_result = check_readiness(
            base, 
            timeout=args.timeout, 
            consecutive=args.consecutive,
            wait=args.wait
        )
        diag.update(readiness_result)
    except Exception as e:
        print(f"⚠️  Readiness check error: {e}")
        diag.update({
            "ready": False,
            "ready_reasons": {
                "clients_ready": False,
                "redis_connected": False,
                "qdrant_connected": False,
                "embedding_loaded": False,
            },
            "ready_error": str(e)
        })
    
    # (c) Direct query check
    print("[3/4] Checking direct query endpoint...")
    query_result = check_direct_query(base)
    diag.update(query_result)
    
    # (d) Autotuner API check
    print("[4/4] Checking autotuner API...")
    autotuner_result = check_autotuner_api(base)
    diag.update(autotuner_result)
    
    # Print summary
    print_summary(diag)
    
    # Write to .runs/diag.json
    runs_dir = Path(__file__).parent.parent / ".runs"
    runs_dir.mkdir(exist_ok=True)
    diag_file = runs_dir / "diag.json"
    
    with open(diag_file, "w") as f:
        json.dump(diag, f, indent=2)
    
    print(f"\n📄 Diagnostics saved to: {diag_file}")
    
    # Exit with non-zero if critical checks failed (for automation)
    # Note: This is a diagnostics script, so we always show the results
    # but exit with non-zero if critical infrastructure is down
    if not diag.get("ready", False) or not diag.get("direct_query_ok", False):
        print("\n⚠️  Critical checks failed - see diagnostics above")
        sys.exit(1)
    
    print("\n✅ All critical checks passed")
    sys.exit(0)


if __name__ == "__main__":
    main()

