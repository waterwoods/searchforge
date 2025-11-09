#!/usr/bin/env python3
"""
Summarize Run Tool - Generate RUN_SUMMARY.md from winners.json and events.jsonl.

Extracts key information about an experiment run and generates a markdown summary.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def find_latest_run_id(reports_dir: Path) -> Optional[str]:
    """Find the latest run_id from reports directory."""
    if not reports_dir.exists():
        return None
    
    run_dirs = [d for d in reports_dir.iterdir() if d.is_dir() and d.name.startswith("orch-")]
    if not run_dirs:
        return None
    
    # Sort by modification time, newest first
    run_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return run_dirs[0].name


def load_winners_json(run_dir: Path) -> Dict[str, Any]:
    """Load winners.json from run directory."""
    winners_path = run_dir / "winners.json"
    if not winners_path.exists():
        raise FileNotFoundError(f"winners.json not found in {run_dir}")
    
    with open(winners_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_events_jsonl(events_dir: Path, run_id: str) -> List[Dict[str, Any]]:
    """Load events.jsonl for a run."""
    events_path = events_dir / f"{run_id}.jsonl"
    if not events_path.exists():
        return []
    
    events = []
    with open(events_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events


def extract_run_info(winners: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract key information from winners.json and events."""
    info = {
        "run_id": winners.get("run_id", "unknown"),
        "dataset": winners.get("dataset", "unknown"),
        "queries_path": winners.get("queries_path", "unknown"),
        "qrels_path": winners.get("qrels_path", "unknown"),
        "id_normalization": winners.get("id_normalization", "unknown"),
        "sample_size": None,
        "top_k": None,
        "index_config": {},
        "metrics": {},
        "sla_verdict": "unknown",
        "ab_results": {},
        "artifacts": [],
    }
    
    # Extract from RUN_STARTED event
    for event in events:
        if event.get("event_type") == "RUN_STARTED":
            payload = event.get("payload", {})
            info["dataset"] = payload.get("dataset", info["dataset"])
            info["queries_path"] = payload.get("queries_path", info["queries_path"])
            info["qrels_path"] = payload.get("qrels_path", info["qrels_path"])
            info["id_normalization"] = payload.get("id_normalization", info["id_normalization"])
            info["sample_size"] = payload.get("sample_size", info["sample_size"])
            break
    
    # Extract from winner
    winner = winners.get("winner", {})
    if winner:
        metrics = winner.get("metrics", {})
        info["metrics"] = {
            "recall_at_10": metrics.get("recall_at_10", 0.0),
            "p95_ms": metrics.get("p95_ms", 0.0),
            "cost_usd": metrics.get("cost_usd", 0.0),
            "qps": metrics.get("qps", 0.0),
        }
        
        config = winner.get("config", {})
        info["top_k"] = config.get("top_k", None)
        info["index_config"] = {
            "ef_search": config.get("ef_search"),
            "mmr": config.get("mmr", False),
            "mmr_lambda": config.get("mmr_lambda"),
            "use_hybrid": config.get("use_hybrid", False),
            "rerank": config.get("rerank", False),
        }
    
    # Extract SLA verdict
    info["sla_verdict"] = winners.get("sla_verdict", "unknown")
    
    # Extract AB results if available
    if "ab_diff" in winners:
        info["ab_results"] = winners.get("ab_diff", {})
    
    # List artifacts
    run_dir = Path(winners.get("run_id", "unknown"))
    reports_dir = Path("reports")
    full_run_dir = reports_dir / run_dir if (reports_dir / run_dir).exists() else Path(run_dir)
    
    artifact_files = [
        "winners.json",
        "winners.md",
        "pareto.png",
        "ab_diff.png",
        "failTopN.csv",
    ]
    
    for artifact in artifact_files:
        if (full_run_dir / artifact).exists():
            info["artifacts"].append(artifact)
    
    events_file = reports_dir / "events" / f"{info['run_id']}.jsonl"
    if events_file.exists():
        info["artifacts"].append(f"events/{info['run_id']}.jsonl")
    
    return info


def generate_summary_markdown(info: Dict[str, Any]) -> str:
    """Generate markdown summary from extracted info."""
    lines = [
        f"# Run Summary: {info['run_id']}",
        "",
        "## Dataset & Data Files",
        "",
        f"- **Dataset**: `{info['dataset']}`",
        f"- **Queries**: `{info['queries_path']}`",
        f"- **Qrels**: `{info['qrels_path']}`",
        f"- **ID Normalization**: `{info['id_normalization']}`",
        "",
        "## Experiment Parameters",
        "",
    ]
    
    if info["sample_size"]:
        lines.append(f"- **Sample Size**: {info['sample_size']}")
    if info["top_k"]:
        lines.append(f"- **Top-K**: {info['top_k']}")
    
    lines.extend([
        "",
        "## Index Configuration",
        "",
    ])
    
    idx_cfg = info["index_config"]
    if idx_cfg.get("ef_search"):
        lines.append(f"- **ef_search**: {idx_cfg['ef_search']}")
    lines.append(f"- **MMR**: {idx_cfg.get('mmr', False)}")
    if idx_cfg.get("mmr_lambda") is not None:
        lines.append(f"- **MMR Lambda**: {idx_cfg['mmr_lambda']}")
    lines.append(f"- **Hybrid Search**: {idx_cfg.get('use_hybrid', False)}")
    lines.append(f"- **Rerank**: {idx_cfg.get('rerank', False)}")
    
    lines.extend([
        "",
        "## Metrics",
        "",
    ])
    
    metrics = info["metrics"]
    if metrics:
        lines.append(f"- **Recall@10**: {metrics.get('recall_at_10', 0.0):.3f}")
        lines.append(f"- **P95 Latency (ms)**: {metrics.get('p95_ms', 0.0):.2f}")
        lines.append(f"- **Cost (USD)**: {metrics.get('cost_usd', 0.0):.4f}")
        lines.append(f"- **QPS**: {metrics.get('qps', 0.0):.2f}")
    
    lines.extend([
        "",
        "## SLA Verdict",
        "",
        f"- **Status**: `{info['sla_verdict']}`",
        "",
    ])
    
    if info["ab_results"]:
        lines.extend([
            "## A/B Test Results",
            "",
        ])
        ab = info["ab_results"]
        if isinstance(ab, dict):
            for key, value in ab.items():
                lines.append(f"- **{key}**: {value}")
        lines.append("")
    
    lines.extend([
        "## Artifacts",
        "",
    ])
    
    for artifact in info["artifacts"]:
        lines.append(f"- `{artifact}`")
    
    lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate RUN_SUMMARY.md from winners.json and events.jsonl")
    parser.add_argument("--run-id", type=str, default=None, help="Run ID (default: latest)")
    parser.add_argument("--reports-dir", type=str, default="reports", help="Reports directory (default: reports)")
    
    args = parser.parse_args()
    
    reports_dir = Path(args.reports_dir)
    events_dir = reports_dir / "events"
    
    # Determine run_id
    run_id = args.run_id
    if not run_id:
        run_id = find_latest_run_id(reports_dir)
        if not run_id:
            print("ERROR: No run_id provided and no runs found in reports directory", file=sys.stderr)
            sys.exit(1)
        print(f"Using latest run_id: {run_id}", file=sys.stderr)
    
    run_dir = reports_dir / run_id
    if not run_dir.exists():
        print(f"ERROR: Run directory not found: {run_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Load data
    try:
        winners = load_winners_json(run_dir)
        events = load_events_jsonl(events_dir, run_id)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Extract info and generate summary
    info = extract_run_info(winners, events)
    summary_md = generate_summary_markdown(info)
    
    # Write summary
    summary_path = run_dir / "RUN_SUMMARY.md"
    # Ensure directory exists and is writable
    run_dir.mkdir(parents=True, exist_ok=True)
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_md)
    
    print(f"✅ Generated: {summary_path}")
    print()
    print(summary_md)


if __name__ == "__main__":
    main()

