#!/usr/bin/env python3
"""
KPI Dashboard Generator - Compact comparison of AutoTuner OFF vs ON

This script generates a compact dashboard (PNG + HTML) comparing AutoTuner performance
from two experiment runs, with Qdrant collection size information.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict

# Try to import qdrant-client, but don't fail if not available
try:
    from qdrant_client import QdrantClient
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

def load_trace_log(trace_file: str) -> List[Dict[str, Any]]:
    """Load and parse trace log file."""
    events = []
    
    if not os.path.exists(trace_file):
        print(f"Warning: Trace log file not found: {trace_file}")
        return events
    
    with open(trace_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON on line {line_num}: {e}")
                continue
    
    print(f"Loaded {len(events)} events from {trace_file}")
    return events

def get_qdrant_collection_size(collection_name: str) -> str:
    """Get collection size from Qdrant. Return 'N/A' if unavailable."""
    if not QDRANT_AVAILABLE:
        return "N/A"
    
    try:
        client = QdrantClient("localhost", port=6333)
        info = client.get_collection(collection_name)
        return str(info.points_count)
    except Exception as e:
        print(f"Warning: Could not connect to Qdrant: {e}")
        return "N/A"

def extract_config_from_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract configuration from RUN_INFO events."""
    config = {
        "tuner_enabled": False,
        "force_ce_on": False,
        "ce_cache_size": 0
    }
    
    for event in events:
        if event.get("event") == "RUN_INFO":
            params = event.get("params", {})
            config["tuner_enabled"] = params.get("TUNER_ENABLED", False)
            config["force_ce_on"] = params.get("FORCE_CE_ON", False)
            config["ce_cache_size"] = params.get("CE_CACHE_SIZE", 0)
            break
    
    return config

def timestamp_to_seconds(ts_str: str) -> float:
    """Convert timestamp string to seconds since epoch."""
    if ts_str is None:
        return 0
    try:
        import re
        from datetime import datetime
        if ts_str.endswith('Z'):
            ts_str = ts_str[:-1]
            # Fix truncated seconds format
            ts_str = re.sub(r'(\d{2}:\d{2}):(\d)Z?$', r'\1:0\2', ts_str)
            ts_str += '+00:00'
        if '.' not in ts_str:
            ts_str = ts_str.replace('+', '.000+')
        dt = datetime.fromisoformat(ts_str)
        return dt.timestamp()
    except Exception as e:
        print(f"Warning: Could not parse timestamp {ts_str}: {e}")
        return 0

def extract_time_series(events: List[Dict[str, Any]], bucket_size: int = 5) -> Tuple[List[float], List[float], List[float], List[float]]:
    """Extract time series data with 5s bucketing."""
    buckets = defaultdict(lambda: {
        "p95_ms": [],
        "recall_at10": [],
        "ef_search": [],
        "timestamps": []
    })
    
    for event in events:
        if event.get("event") == "RESPONSE":
            ts_str = event.get("ts", "")
            event_time = timestamp_to_seconds(ts_str)
            bucket_key = int(event_time // bucket_size)
            
            # Get latency (cost_ms or p95_ms)
            latency = event.get("cost_ms", 0)
            buckets[bucket_key]["p95_ms"].append(latency)
            buckets[bucket_key]["timestamps"].append(event_time)
            
            # Estimate recall from results count
            total_results = event.get("stats", {}).get("total_results", 0)
            recall = min(1.0, total_results / 10.0)
            buckets[bucket_key]["recall_at10"].append(recall)
            
        elif event.get("event") == "AUTOTUNER_SUGGEST":
            ts_str = event.get("ts", "")
            event_time = timestamp_to_seconds(ts_str)
            bucket_key = int(event_time // bucket_size)
            
            ef_search = event.get("params", {}).get("ef_search", 128)
            buckets[bucket_key]["ef_search"].append(ef_search)
            
        elif event.get("event") == "RETRIEVE_VECTOR":
            ts_str = event.get("ts", "")
            event_time = timestamp_to_seconds(ts_str)
            bucket_key = int(event_time // bucket_size)
            
            ef_search = event.get("params", {}).get("ef_search", 128)
            buckets[bucket_key]["ef_search"].append(ef_search)
    
    # Convert to time series
    times = []
    p95_values = []
    recall_values = []
    ef_values = []
    
    last_ef = 128  # Default ef_search value
    
    for bucket_key in sorted(buckets.keys()):
        bucket = buckets[bucket_key]
        bucket_time = bucket_key * bucket_size
        
        # P95 latency
        if bucket["p95_ms"]:
            p95_values.append(np.percentile(bucket["p95_ms"], 95))
        else:
            p95_values.append(np.nan)
        
        # Mean recall
        if bucket["recall_at10"]:
            recall_values.append(np.mean(bucket["recall_at10"]))
        else:
            recall_values.append(np.nan)
        
        # EF search (use last value in bucket, or carry forward)
        if bucket["ef_search"]:
            last_ef = bucket["ef_search"][-1]
        ef_values.append(last_ef)
        
        times.append(bucket_time)
    
    return times, p95_values, recall_values, ef_values

def calculate_kpis(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate KPIs from events."""
    response_events = [e for e in events if e.get("event") == "RESPONSE"]
    autotuner_events = [e for e in events if e.get("event") == "AUTOTUNER_SUGGEST"]
    
    if not response_events:
        return {
            "p95_overall_ms": np.nan,
            "mean_recall_at10": np.nan,
            "slo_violations": 0,
            "area_over_slo": 0,
            "ef_change_count": 0
        }
    
    # Extract latencies and timestamps
    latencies = []
    timestamps = []
    recalls = []
    
    for event in response_events:
        latency = event.get("cost_ms", 0)
        latencies.append(latency)
        
        ts_str = event.get("ts", "")
        timestamps.append(timestamp_to_seconds(ts_str))
        
        # Estimate recall
        total_results = event.get("stats", {}).get("total_results", 0)
        recall = min(1.0, total_results / 10.0)
        recalls.append(recall)
    
    # Calculate KPIs
    p95_overall = np.percentile(latencies, 95) if latencies else np.nan
    mean_recall = np.mean(recalls) if recalls else np.nan
    
    # SLO violations (bucketed)
    times, p95_series, _, _ = extract_time_series(events)
    slo_violations = sum(1 for p95 in p95_series if not np.isnan(p95) and p95 > 1200)
    
    # Area over SLO
    area_over_slo = 0
    for i, p95 in enumerate(p95_series):
        if not np.isnan(p95) and p95 > 1200:
            duration = 5  # 5s bucket size
            area_over_slo += max(0, p95 - 1200) * duration
    
    ef_change_count = len(autotuner_events)
    
    return {
        "p95_overall_ms": p95_overall,
        "mean_recall_at10": mean_recall,
        "slo_violations": slo_violations,
        "area_over_slo": area_over_slo,
        "ef_change_count": ef_change_count
    }

def create_dashboard(off_events: List[Dict[str, Any]], on_events: List[Dict[str, Any]], 
                    dataset: str, collection: str, collection_size: str, output_dir: str):
    """Create the KPI dashboard."""
    
    # Extract time series data
    off_times, off_p95, off_recall, off_ef = extract_time_series(off_events)
    on_times, on_p95, on_recall, on_ef = extract_time_series(on_events)
    
    # Calculate KPIs
    off_kpis = calculate_kpis(off_events)
    on_kpis = calculate_kpis(on_events)
    
    # Extract configs
    off_config = extract_config_from_events(off_events)
    on_config = extract_config_from_events(on_events)
    
    # Create figure
    fig = plt.figure(figsize=(12, 8))
    
    # Define colors
    color_off = '#ff4444'
    color_on = '#4444ff'
    
    # 1. P95 Latency (top left)
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(off_times, off_p95, color=color_off, linewidth=2, label='AutoTuner OFF', alpha=0.8)
    ax1.plot(on_times, on_p95, color=color_on, linewidth=2, label='AutoTuner ON', alpha=0.8)
    ax1.axhline(y=1200, color='gray', linestyle='--', alpha=0.7, label='SLO (1200ms)')
    ax1.set_title('P95 Latency (ms)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Latency (ms)')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # 2. Recall@10 (top right)
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(off_times, off_recall, color=color_off, linewidth=2, label='AutoTuner OFF', alpha=0.8)
    ax2.plot(on_times, on_recall, color=color_on, linewidth=2, label='AutoTuner ON', alpha=0.8)
    ax2.set_title('Recall@10', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Recall')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 1)
    
    # 3. EF Search (bottom left)
    ax3 = plt.subplot(2, 2, 3)
    ax3.step(off_times, off_ef, color=color_off, linewidth=2, label='AutoTuner OFF', alpha=0.8, where='post')
    ax3.step(on_times, on_ef, color=color_on, linewidth=2, label='AutoTuner ON', alpha=0.8, where='post')
    ax3.set_title('EF Search Parameter', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Time (seconds)')
    ax3.set_ylabel('EF Search')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    
    # 4. P95 vs EF Scatter (bottom right)
    ax4 = plt.subplot(2, 2, 4)
    
    # Filter out NaN values for scatter plot
    off_valid = [(ef, p95) for ef, p95 in zip(off_ef, off_p95) if not np.isnan(p95)]
    on_valid = [(ef, p95) for ef, p95 in zip(on_ef, on_p95) if not np.isnan(p95)]
    
    if off_valid:
        off_ef_vals, off_p95_vals = zip(*off_valid)
        ax4.scatter(off_ef_vals, off_p95_vals, color=color_off, alpha=0.6, s=20, label='AutoTuner OFF')
    
    if on_valid:
        on_ef_vals, on_p95_vals = zip(*on_valid)
        ax4.scatter(on_ef_vals, on_p95_vals, color=color_on, alpha=0.6, s=20, label='AutoTuner ON')
    
    ax4.set_title('P95 vs EF Search', fontsize=12, fontweight='bold')
    ax4.set_xlabel('EF Search')
    ax4.set_ylabel('P95 Latency (ms)')
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    
    # Add SLO line to scatter plot
    ax4.axhline(y=1200, color='gray', linestyle='--', alpha=0.7)
    
    # Add side information panel
    info_text = f"""Dataset: {dataset}
Collection: {collection}
Collection Size: {collection_size}
CE Cache Size: {off_config['ce_cache_size']}
Force CE On: {off_config['force_ce_on']}
AutoTuner OFF: {not off_config['tuner_enabled']}
AutoTuner ON: {on_config['tuner_enabled']}"""
    
    # Position the info panel on the left
    fig.text(0.02, 0.98, info_text, fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.8))
    
    # Add bottom KPI comparison table
    kpi_text = f"""KPI Comparison:
    
P95 Overall (ms):
  OFF: {off_kpis['p95_overall_ms']:.1f}
  ON:  {on_kpis['p95_overall_ms']:.1f}

Mean Recall@10:
  OFF: {off_kpis['mean_recall_at10']:.3f}
  ON:  {on_kpis['mean_recall_at10']:.3f}

EF Changes:
  OFF: {off_kpis['ef_change_count']}
  ON:  {on_kpis['ef_change_count']}"""
    
    fig.text(0.5, 0.02, kpi_text, fontsize=9, horizontalalignment='center',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    plt.subplots_adjust(left=0.15, bottom=0.15)
    
    # Save PNG
    os.makedirs(output_dir, exist_ok=True)
    png_path = os.path.join(output_dir, 'kpi_dash.png')
    plt.savefig(png_path, dpi=150, bbox_inches='tight')
    print(f"Dashboard saved to: {png_path}")
    
    # Create HTML version
    html_path = os.path.join(output_dir, 'kpi_dash.html')
    create_html_dashboard(png_path, off_kpis, on_kpis, dataset, collection, collection_size, html_path)
    
    plt.close()

def create_html_dashboard(png_path: str, off_kpis: Dict[str, Any], on_kpis: Dict[str, Any],
                         dataset: str, collection: str, collection_size: str, html_path: str):
    """Create HTML version of the dashboard."""
    
    # Read PNG as base64
    import base64
    with open(png_path, 'rb') as f:
        img_data = base64.b64encode(f.read()).decode()
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>AutoTuner KPI Dashboard - {dataset}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #333; margin-bottom: 10px; }}
        .header p {{ color: #666; font-size: 14px; }}
        .dashboard {{ text-align: center; margin-bottom: 30px; }}
        .dashboard img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; }}
        .kpi-section {{ display: flex; justify-content: space-around; margin-top: 30px; }}
        .kpi-card {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; min-width: 200px; }}
        .kpi-card h3 {{ margin-top: 0; color: #495057; }}
        .kpi-value {{ font-size: 24px; font-weight: bold; margin: 10px 0; }}
        .kpi-off {{ color: #dc3545; }}
        .kpi-on {{ color: #007bff; }}
        .info-section {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-top: 20px; }}
        .info-section h4 {{ margin-top: 0; color: #495057; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AutoTuner KPI Dashboard</h1>
            <p>Dataset: {dataset} | Collection: {collection} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="dashboard">
            <img src="data:image/png;base64,{img_data}" alt="KPI Dashboard">
        </div>
        
        <div class="kpi-section">
            <div class="kpi-card">
                <h3>P95 Overall (ms)</h3>
                <div class="kpi-value kpi-off">OFF: {off_kpis['p95_overall_ms']:.1f}</div>
                <div class="kpi-value kpi-on">ON: {on_kpis['p95_overall_ms']:.1f}</div>
            </div>
            
            <div class="kpi-card">
                <h3>Mean Recall@10</h3>
                <div class="kpi-value kpi-off">OFF: {off_kpis['mean_recall_at10']:.3f}</div>
                <div class="kpi-value kpi-on">ON: {on_kpis['mean_recall_at10']:.3f}</div>
            </div>
            
            <div class="kpi-card">
                <h3>EF Changes</h3>
                <div class="kpi-value kpi-off">OFF: {off_kpis['ef_change_count']}</div>
                <div class="kpi-value kpi-on">ON: {on_kpis['ef_change_count']}</div>
            </div>
            
            <div class="kpi-card">
                <h3>SLO Violations</h3>
                <div class="kpi-value kpi-off">OFF: {off_kpis['slo_violations']}</div>
                <div class="kpi-value kpi-on">ON: {on_kpis['slo_violations']}</div>
            </div>
        </div>
        
        <div class="info-section">
            <h4>Experiment Configuration</h4>
            <div class="info-grid">
                <div><strong>Dataset:</strong> {dataset}</div>
                <div><strong>Collection:</strong> {collection}</div>
                <div><strong>Collection Size:</strong> {collection_size}</div>
                <div><strong>AutoTuner OFF:</strong> Disabled</div>
                <div><strong>AutoTuner ON:</strong> Enabled</div>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    with open(html_path, 'w') as f:
        f.write(html_content)
    
    print(f"HTML dashboard saved to: {html_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate KPI dashboard comparing AutoTuner OFF vs ON")
    parser.add_argument("--off", required=True, help="Directory containing OFF experiment trace.log")
    parser.add_argument("--on", required=True, help="Directory containing ON experiment trace.log")
    parser.add_argument("--collection", required=True, help="Qdrant collection name")
    parser.add_argument("--dataset", required=True, help="Dataset name")
    parser.add_argument("--out", required=True, help="Output directory")
    
    args = parser.parse_args()
    
    # Load trace logs
    off_trace = os.path.join(args.off, "trace.log")
    on_trace = os.path.join(args.on, "trace.log")
    
    off_events = load_trace_log(off_trace)
    on_events = load_trace_log(on_trace)
    
    if not off_events:
        print(f"Error: No events found in OFF experiment: {off_trace}")
        return
    
    if not on_events:
        print(f"Error: No events found in ON experiment: {on_trace}")
        return
    
    # Get Qdrant collection size
    collection_size = get_qdrant_collection_size(args.collection)
    print(f"Collection {args.collection} size: {collection_size}")
    
    # Create dashboard
    create_dashboard(off_events, on_events, args.dataset, args.collection, collection_size, args.out)
    
    print("Dashboard generation completed!")

if __name__ == "__main__":
    main()








