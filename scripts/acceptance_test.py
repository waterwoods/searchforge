#!/usr/bin/env python3
"""
一键验收脚本：plan → commit → status → report
"""

import json
import time
import requests
from pathlib import Path

ORCH_BASE = "http://127.0.0.1:8001"
REPORTS_DIR = Path("reports")

def load_config():
    import yaml
    with open("agents/orchestrator/config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)

def generate_payload(cfg):
    collections = cfg.get("collections") or ["fiqa_para_50k"]
    dataset = collections[0]
    smoke = cfg.get("smoke", {})
    grid = cfg.get("grid", {})
    return {
        "dataset": dataset,
        "sample_size": smoke.get("sample", 50),
        "search_space": {
            "top_k": grid.get("top_k"),
            "mmr": grid.get("mmr"),
            "ef_search": grid.get("ef_search"),
        },
        "budget": cfg.get("budget", {}),
        "concurrency": smoke.get("concurrency"),
        "baseline_id": cfg.get("baseline_policy"),
    }

def main():
    cfg = load_config()
    payload = generate_payload(cfg)
    
    result = {
        "plan": {},
        "run": {},
        "report": {},
    }
    
    # 1. Plan (dry-run)
    print("📋 Step 1: Generating plan (dry-run)...")
    resp = requests.post(f"{ORCH_BASE}/orchestrate/run?commit=false", json=payload, timeout=30)
    plan_resp = resp.json()
    print(f"Plan response: {json.dumps(plan_resp, indent=2)}")
    
    plan_run_id = plan_resp.get("run_id")
    if not plan_run_id:
        print("❌ Failed to get plan run_id")
        return result
    
    # Extract plan info from events
    events_file = REPORTS_DIR / "events" / f"{plan_run_id}.jsonl"
    if events_file.exists():
        with open(events_file, encoding="utf-8") as f:
            for line in f:
                event = json.loads(line.strip())
                if event.get("event_type") == "DRY_RUN_PLAN":
                    payload_data = event.get("payload", {})
                    plan_data = payload_data.get("plan", {})
                    fingerprints = payload_data.get("fingerprints", {})
                    result["plan"] = {
                        "preset": "grid",  # Default preset
                        "fingerprints": fingerprints,
                        "estimate": {
                            "batches": plan_data.get("batches", 0),
                            "eta_min": plan_data.get("estimated_duration_s", 0) / 60.0,
                            "budget_usd": 0.0,  # Placeholder
                        },
                    }
                    break
    
    # If no DRY_RUN_PLAN found, try to get from response
    if not result["plan"] and "plan" in plan_resp:
        plan_data = plan_resp.get("plan", {})
        fingerprints = plan_resp.get("fingerprints", {})
        result["plan"] = {
            "preset": "grid",
            "fingerprints": fingerprints,
            "estimate": {
                "batches": plan_data.get("batches", 0),
                "eta_min": plan_data.get("estimated_duration_s", 0) / 60.0,
                "budget_usd": 0.0,
            },
        }
    
    # 2. Commit (execute)
    print("\n🚀 Step 2: Committing and executing...")
    resp = requests.post(f"{ORCH_BASE}/orchestrate/run?commit=true", json=payload, timeout=30)
    commit_resp = resp.json()
    print(f"Commit response: {json.dumps(commit_resp, indent=2)}")
    
    run_id = commit_resp.get("run_id")
    if not run_id:
        print("❌ Failed to get run_id")
        return result
    
    result["run"] = {
        "run_id": run_id,
        "queue_pos": commit_resp.get("queue_pos"),
        "started_at": None,
        "finished_at": None,
        "stage": "PENDING",
        "status": "running",
    }
    
    # 3. Poll status
    print("\n⏳ Step 3: Polling status...")
    max_polls = 120  # 10 minutes max
    poll_count = 0
    while poll_count < max_polls:
        resp = requests.get(f"{ORCH_BASE}/orchestrate/status?run_id={run_id}", timeout=10)
        if resp.status_code != 200:
            print(f"Status check failed: {resp.status_code}")
            break
        
        status_data = resp.json()
        result["run"].update({
            "stage": status_data.get("stage", "PENDING"),
            "status": status_data.get("status", "running"),
            "started_at": status_data.get("started_at"),
            "finished_at": status_data.get("finished_at"),
            "queue_pos": status_data.get("queue_pos"),
        })
        
        print(f"  [{poll_count+1}/{max_polls}] Stage: {result['run']['stage']}, Status: {result['run']['status']}")
        
        if status_data.get("status") in ["completed", "failed"]:
            break
        
        time.sleep(5)
        poll_count += 1
    
    # 4. Get report
    print("\n📊 Step 4: Fetching report...")
    resp = requests.get(f"{ORCH_BASE}/orchestrate/report?run_id={run_id}", timeout=10)
    if resp.status_code == 200:
        report_data = resp.json()
        artifacts = report_data.get("artifacts", {})
        
        # Check file existence
        files_exist = {}
        for key, rel_path in artifacts.items():
            full_path = REPORTS_DIR / rel_path if not str(rel_path).startswith("/") else Path(rel_path)
            files_exist[key] = full_path.exists()
        
        result["report"] = {
            "sla_verdict": report_data.get("sla_verdict", "unknown"),
            "sla_checks": report_data.get("sla_checks", []),
            "artifacts": artifacts,
            "files_exist": files_exist,
        }
        
        # Get winners_final tail
        winners_final_path = REPORTS_DIR / "winners.final.json"
        if winners_final_path.exists():
            with open(winners_final_path, encoding="utf-8") as f:
                winners_data = json.load(f)
                if isinstance(winners_data, list) and winners_data:
                    result["report"]["winners_final_tail"] = json.dumps(winners_data[-1], indent=2)
                elif isinstance(winners_data, dict) and winners_data.get("entries"):
                    entries = winners_data["entries"]
                    if entries:
                        result["report"]["winners_final_tail"] = json.dumps(entries[-1], indent=2)
    
    # Output final result
    print("\n" + "="*60)
    print("FINAL RESULT:")
    print("="*60)
    print(json.dumps(result, indent=2))
    
    # Validation
    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    
    if result["run"]["status"] != "completed":
        print(f"❌ Status is not completed: {result['run']['status']}")
        # Get recent events
        events_file = REPORTS_DIR / "events" / f"{run_id}.jsonl"
        if events_file.exists():
            print("\nRecent events:")
            with open(events_file, encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-5:]:
                    event = json.loads(line.strip())
                    print(f"  {event.get('event_type')}: {event.get('payload', {}).get('error', {}).get('msg', 'N/A')}")
    else:
        print("✅ Status: completed")
    
    missing_files = [k for k, v in result["report"].get("files_exist", {}).items() if not v]
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
    else:
        print("✅ All artifacts exist")
    
    if result["report"].get("sla_verdict") not in ["pass", "warn", "fail"]:
        print(f"⚠️  SLA verdict missing or invalid: {result['report'].get('sla_verdict')}")
    else:
        print(f"✅ SLA verdict: {result['report'].get('sla_verdict')}")
    
    return result

if __name__ == "__main__":
    main()

