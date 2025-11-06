#!/usr/bin/env python3
import os
import sys
import time
import json
import requests

BASE = os.getenv("FIQA_API_BASE", "http://localhost:8011")
JOB_ID = os.getenv("JOB_ID")

PAYLOAD = {
    "overrides": {"fast_mode": False, "top_k": 80, "rerank": True, "rerank_top_k": 55}
}

def pick_latest_job():
    try:
        r = requests.get(f"{BASE}/api/experiment/jobs", timeout=5)
        r.raise_for_status()
        data = r.json()
        jobs = data.get("jobs", [])
        for j in jobs:
            if j.get("status") in ("SUCCEEDED", "FAILED"):
                return j.get("job_id")
    except Exception as e:
        print(f"Failed to pick latest job: {e}")
    return None


def main():
    global JOB_ID
    if not JOB_ID:
        JOB_ID = pick_latest_job()
    if not JOB_ID:
        print("Please set JOB_ID env to an existing completed job id.")
        return 1

    url = f"{BASE}/api/experiment/rerun/{JOB_ID}"
    print(f"POST {url} payload={json.dumps(PAYLOAD)}")
    resp = requests.post(url, json=PAYLOAD, timeout=10)
    print(f"status={resp.status_code} body={resp.text}")

    if resp.ok:
        data = resp.json()
        new_job_id = data.get("job_id")
        print(f"New job: {new_job_id}")
        # Poll logs for audit lines
        for _ in range(30):
            try:
                tail = requests.get(f"{BASE}/api/experiment/logs/{new_job_id}", params={"tail": 200}, timeout=5)
                if tail.ok:
                    lines = tail.json().get("tail", [])
                    for line in lines[-50:]:
                        if "[OVR-AUDIT]" in line:
                            print(line)
                time.sleep(1)
            except Exception:
                time.sleep(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
