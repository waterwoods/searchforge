#!/usr/bin/env python3
"""
Smoke test script for orchestrator endpoints
"""
import json
import time
import requests
import sys

BASE_URL = "http://localhost:8000"

def check_health():
    """Check health endpoints"""
    print("=" * 60)
    print("1. Health Checks")
    print("=" * 60)
    
    # Check /ready
    try:
        resp = requests.get(f"{BASE_URL}/ready", timeout=5)
        ready_ok = resp.status_code == 200 and resp.json().get("ok") is True
        print(f"  /ready: {'✅ OK' if ready_ok else '❌ FAIL'}")
        if not ready_ok:
            print(f"    Response: {resp.text}")
    except Exception as e:
        print(f"  /ready: ❌ ERROR - {e}")
        ready_ok = False
    
    # Check /api/health/embeddings
    try:
        resp = requests.get(f"{BASE_URL}/api/health/embeddings", timeout=5)
        embed_ok = resp.status_code == 200 and resp.json().get("ok") is True
        print(f"  /api/health/embeddings: {'✅ OK' if embed_ok else '❌ FAIL'}")
        if not embed_ok:
            print(f"    Response: {resp.text}")
    except Exception as e:
        print(f"  /api/health/embeddings: ❌ ERROR - {e}")
        embed_ok = False
    
    return {"ready": ready_ok, "embeddings": embed_ok}


def dry_run():
    """Run dry-run plan"""
    print("\n" + "=" * 60)
    print("2. Dry-run Plan")
    print("=" * 60)
    
    payload = {
        "preset": "smoke",
        "collection": "fiqa_para_50k",
        "overrides": {
            "sample": 40,
            "top_k": 10,
            "concurrency": 2
        }
    }
    
    try:
        resp = requests.post(
            f"{BASE_URL}/orchestrate/run?commit=false",
            json=payload,
            headers={"content-type": "application/json"},
            timeout=30
        )
        if resp.status_code == 200:
            result = resp.json()
            print(f"  ✅ Plan created")
            print(f"    Run ID: {result.get('run_id', 'N/A')}")
            print(f"    Dry run: {result.get('dry_run', 'N/A')}")
            return result
        else:
            print(f"  ❌ Failed: {resp.status_code}")
            print(f"    Response: {resp.text}")
            return None
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return None


def commit_run():
    """Commit and run experiment"""
    print("\n" + "=" * 60)
    print("3. Commit Run")
    print("=" * 60)
    
    payload = {
        "preset": "smoke",
        "collection": "fiqa_para_50k",
        "overrides": {
            "sample": 40,
            "top_k": 10,
            "concurrency": 2
        }
    }
    
    try:
        resp = requests.post(
            f"{BASE_URL}/orchestrate/run?commit=true",
            json=payload,
            headers={"content-type": "application/json"},
            timeout=30
        )
        if resp.status_code == 200:
            result = resp.json()
            run_id = result.get("run_id")
            print(f"  ✅ Run started")
            print(f"    Run ID: {run_id}")
            return run_id
        else:
            print(f"  ❌ Failed: {resp.status_code}")
            print(f"    Response: {resp.text}")
            return None
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return None


def poll_status(run_id, max_wait=600):
    """Poll run status until completed or failed"""
    print("\n" + "=" * 60)
    print(f"4. Polling Status (max {max_wait}s)")
    print("=" * 60)
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            resp = requests.get(
                f"{BASE_URL}/orchestrate/status?run_id={run_id}",
                timeout=10
            )
            if resp.status_code == 200:
                status = resp.json()
                stage = status.get("stage", "UNKNOWN")
                status_val = status.get("status", "unknown")
                queue_pos = status.get("queue_pos", 0)
                started_at = status.get("started_at", "N/A")
                finished_at = status.get("finished_at")
                
                print(f"  [{int(time.time() - start_time)}s] Stage: {stage}, Status: {status_val}, Queue: {queue_pos}")
                
                if status_val in ["completed", "failed"]:
                    print(f"  ✅ Final status: {status_val}")
                    return status
            else:
                print(f"  ⚠️  Status check failed: {resp.status_code}")
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
        
        time.sleep(5)
    
    print(f"  ⚠️  Timeout after {max_wait}s")
    return None


def get_report(run_id):
    """Get run report"""
    print("\n" + "=" * 60)
    print("5. Get Report")
    print("=" * 60)
    
    try:
        resp = requests.get(
            f"{BASE_URL}/orchestrate/report?run_id={run_id}",
            timeout=10
        )
        if resp.status_code == 200:
            report = resp.json()
            print(f"  ✅ Report retrieved")
            return report
        else:
            print(f"  ❌ Failed: {resp.status_code}")
            print(f"    Response: {resp.text}")
            return None
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return None


def check_artifacts(run_id, report):
    """Check if artifacts exist"""
    print("\n" + "=" * 60)
    print("6. Check Artifacts")
    print("=" * 60)
    
    from pathlib import Path
    
    artifacts = report.get("artifacts", {})
    files_exist = {}
    
    for key, path in artifacts.items():
        full_path = Path(path)
        exists = full_path.exists()
        files_exist[key] = exists
        status = "✅" if exists else "❌"
        print(f"  {status} {key}: {path}")
    
    return files_exist


def test_idempotency():
    """Test idempotency by running same request twice"""
    print("\n" + "=" * 60)
    print("7. Idempotency Check")
    print("=" * 60)
    
    payload = {
        "preset": "smoke",
        "collection": "fiqa_para_50k",
        "overrides": {
            "sample": 40,
            "top_k": 10,
            "concurrency": 2
        }
    }
    
    try:
        # First run
        resp1 = requests.post(
            f"{BASE_URL}/orchestrate/run?commit=true",
            json=payload,
            headers={"content-type": "application/json"},
            timeout=30
        )
        run_id1 = resp1.json().get("run_id") if resp1.status_code == 200 else None
        
        # Second run (should return same run_id)
        resp2 = requests.post(
            f"{BASE_URL}/orchestrate/run?commit=true",
            json=payload,
            headers={"content-type": "application/json"},
            timeout=30
        )
        run_id2 = resp2.json().get("run_id") if resp2.status_code == 200 else None
        
        is_idempotent = run_id1 == run_id2 and run_id1 is not None
        print(f"  Run 1 ID: {run_id1}")
        print(f"  Run 2 ID: {run_id2}")
        print(f"  {'✅ Idempotent' if is_idempotent else '❌ Not idempotent'}")
        
        return is_idempotent
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False


def main():
    """Main test flow"""
    print("\n" + "=" * 60)
    print("ORCHESTRATOR SMOKE TEST")
    print("=" * 60 + "\n")
    
    # Health checks
    health = check_health()
    if not health["ready"] or not health["embeddings"]:
        print("\n❌ Health checks failed. Please ensure service is running.")
        sys.exit(1)
    
    # Dry run
    plan_result = dry_run()
    if not plan_result:
        print("\n❌ Dry-run failed.")
        sys.exit(1)
    
    # Commit run
    run_id = commit_run()
    if not run_id:
        print("\n❌ Commit run failed.")
        sys.exit(1)
    
    # Poll status
    status = poll_status(run_id)
    if not status:
        print("\n⚠️  Status polling incomplete, but continuing...")
        status = {"stage": "UNKNOWN", "status": "unknown"}
    
    # Get report
    report = get_report(run_id)
    if not report:
        print("\n⚠️  Report not available, using empty report")
        report = {"artifacts": {}, "sla_verdict": "unknown"}
    
    # Check artifacts
    files_exist = check_artifacts(run_id, report)
    
    # Test idempotency
    is_idempotent = test_idempotency()
    
    # Generate final report
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    
    final_report = {
        "health": health,
        "run": {
            "run_id": run_id,
            "stage": status.get("stage", "UNKNOWN"),
            "status": status.get("status", "unknown"),
            "queue_pos": status.get("queue_pos", 0),
            "started_at": status.get("started_at", "N/A"),
            "finished_at": status.get("finished_at", "N/A")
        },
        "report": {
            "sla_verdict": report.get("sla_verdict", "unknown"),
            "artifacts": report.get("artifacts", {}),
            "files_exist": files_exist
        },
        "idempotent_check": "true" if is_idempotent else "false",
        "notes": ""
    }
    
    print(json.dumps(final_report, indent=2))
    
    # Save to file
    with open("/tmp/smoke_test_result.json", "w") as f:
        json.dump(final_report, f, indent=2)
    
    print(f"\n✅ Report saved to /tmp/smoke_test_result.json")


if __name__ == "__main__":
    main()

