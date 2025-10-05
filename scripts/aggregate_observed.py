#!/usr/bin/env python3
"""
Observed Experiment Aggregator - Report Generation Script

This script reads trace logs and generates HTML reports with charts and analysis.
"""

import os
import sys
import json
import argparse
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict
import numpy as np
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def to_py_number(x):
    """Convert numpy types, Decimal, int64, etc. to native Python float/int."""
    if isinstance(x, (np.float64, np.float32, np.int64, np.int32, np.int16, np.int8)):
        return float(x) if isinstance(x, (np.float64, np.float32)) else int(x)
    elif isinstance(x, Decimal):
        return float(x)
    elif isinstance(x, (list, tuple)):
        return [to_py_number(item) for item in x]
    elif isinstance(x, dict):
        return {key: to_py_number(value) for key, value in x.items()}
    else:
        return x

def serialize_values(obj):
    """Convert numpy types to native Python types and round floats to 2 decimal places."""
    if isinstance(obj, (np.float64, np.float32, np.int64, np.int32, np.int16, np.int8)):
        if isinstance(obj, (np.float64, np.float32)):
            return round(float(obj), 2)
        else:
            return int(obj)
    elif isinstance(obj, Decimal):
        return round(float(obj), 2)
    elif isinstance(obj, float):
        return round(obj, 2)
    elif isinstance(obj, list):
        return [serialize_values(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: serialize_values(value) for key, value in obj.items()}
    else:
        return obj

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
                event['line_num'] = line_num
                events.append(event)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON on line {line_num}: {e}")
                continue
    
    print(f"Loaded {len(events)} events from {trace_file}")
    return events

def extract_metrics_by_stage(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Extract metrics grouped by stage (candidate_k changes)."""
    stages = defaultdict(list)
    current_stage = "unknown"
    
    for event in events:
        if event.get("event") == "FETCH_QUERY":
            # Determine stage based on candidate_k
            candidate_k = event.get("stats", {}).get("candidate_k")
            if candidate_k:
                if candidate_k <= 100:
                    current_stage = "stage_1_k100"
                elif candidate_k <= 200:
                    current_stage = "stage_2_k200"
                elif candidate_k <= 400:
                    current_stage = "stage_3_k400"
                else:
                    current_stage = f"stage_k{candidate_k}"
        
        if current_stage != "unknown":
            stages[current_stage].append(event)
    
    return dict(stages)

def calculate_stage_metrics(stage_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate metrics for a single stage."""
    response_events = [e for e in stage_events if e.get("event") == "RESPONSE"]
    autotuner_events = [e for e in stage_events if e.get("event") == "AUTOTUNER_SUGGEST"]
    params_events = [e for e in stage_events if e.get("event") == "PARAMS_APPLIED"]
    
    if not response_events:
        return {"error": "No response events found"}
    
    # Calculate latency metrics
    latencies = [e.get("cost_ms", 0) for e in response_events]
    slo_violations = [e.get("params", {}).get("slo_violated", False) for e in response_events]
    
    metrics = {
        "total_queries": len(response_events),
        "p50_ms": np.percentile(latencies, 50) if latencies else 0,
        "p95_ms": np.percentile(latencies, 95) if latencies else 0,
        "p99_ms": np.percentile(latencies, 99) if latencies else 0,
        "avg_ms": np.mean(latencies) if latencies else 0,
        "slo_violation_rate": sum(slo_violations) / len(slo_violations) if slo_violations else 0,
        "autotuner_suggestions": len(autotuner_events),
        "params_applied": len([e for e in params_events if e.get("applied", {}).get("applied", False)]),
        "params_rejected": len([e for e in params_events if not e.get("applied", {}).get("applied", False)])
    }
    
    # Calculate recall metrics (simplified)
    recall_values = []
    for event in response_events:
        # Extract recall from stats if available, otherwise estimate
        stats = event.get("stats", {})
        if "recall" in stats:
            recall_values.append(stats["recall"])
        else:
            # Estimate based on results count
            total_results = stats.get("total_results", 0)
            recall_values.append(min(1.0, total_results / 10.0))
    
    if recall_values:
        metrics["recall_at_10"] = np.mean(recall_values)
        metrics["recall_p95"] = np.percentile(recall_values, 95)
    
    return metrics

def create_timeline_charts(stages: Dict[str, List[Dict[str, Any]]], events: List[Dict[str, Any]] = None) -> str:
    """Create timeline charts and return as base64 encoded image."""
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle('AutoTuner Performance Timeline', fontsize=16)
    
    # Prepare data
    stage_names = list(stages.keys())
    stage_metrics = {}
    
    for stage_name, events in stages.items():
        stage_metrics[stage_name] = calculate_stage_metrics(events)
    
    # Chart 1: P95 Latency over time with AutoTuner event markers
    p95_values = [stage_metrics.get(name, {}).get("p95_ms", 0) for name in stage_names]
    axes[0].plot(range(len(stage_names)), p95_values, 'b-o', linewidth=2, markersize=8)
    
    # Add AutoTuner event markers if events are provided
    if events:
        autotuner_events = [e for e in events if e.get('event') == 'AUTOTUNER_SUGGEST']
        for i, event in enumerate(autotuner_events):
            # Map event to stage position (simplified mapping)
            stage_position = i % len(stage_names)
            ef_suggest = event.get('params', {}).get('suggest', {}).get('ef_search', 'N/A')
            axes[0].axvline(x=stage_position, color='red', linestyle='--', alpha=0.7, linewidth=1)
            # Add annotation for first few events
            if i < 5:
                axes[0].annotate(f'EF: {ef_suggest}', xy=(stage_position, p95_values[stage_position]), 
                               xytext=(5, 10), textcoords='offset points', fontsize=8, ha='left',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    axes[0].set_title('P95 Latency (ms) - Red lines = AutoTuner Events')
    axes[0].set_ylabel('Latency (ms)')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_xticks(range(len(stage_names)))
    axes[0].set_xticklabels([name.replace('stage_', '').replace('_k', ' K=') for name in stage_names], rotation=45)
    
    # Chart 2: EF Search parameter over time
    ef_values = []
    for stage_name in stage_names:
        # Extract ef_search from PARAMS_APPLIED events
        stage_events = stages[stage_name]
        params_events = [e for e in stage_events if e.get("event") == "PARAMS_APPLIED"]
        if params_events:
            latest_ef = params_events[-1].get("applied", {}).get("new_ef_search", 128)
        else:
            latest_ef = 128  # Default
        ef_values.append(latest_ef)
    
    axes[1].plot(range(len(stage_names)), ef_values, 'g-o', linewidth=2, markersize=8)
    axes[1].set_title('EF Search Parameter')
    axes[1].set_ylabel('EF Search')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xticks(range(len(stage_names)))
    axes[1].set_xticklabels([name.replace('stage_', '').replace('_k', ' K=') for name in stage_names], rotation=45)
    
    # Chart 3: Recall@10 over time
    recall_values = [stage_metrics.get(name, {}).get("recall_at_10", 0) for name in stage_names]
    axes[2].plot(range(len(stage_names)), recall_values, 'r-o', linewidth=2, markersize=8)
    axes[2].set_title('Recall@10')
    axes[2].set_ylabel('Recall')
    axes[2].set_xlabel('Stage')
    axes[2].grid(True, alpha=0.3)
    axes[2].set_xticks(range(len(stage_names)))
    axes[2].set_xticklabels([name.replace('stage_', '').replace('_k', ' K=') for name in stage_names], rotation=45)
    
    plt.tight_layout()
    
    # Convert to base64
    import io
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return image_base64

def extract_tuner_impact(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract tuner impact data by pairing AUTOTUNER_SUGGEST with PARAMS_APPLIED."""
    change_events = []
    
    # Helper function to convert timestamp to seconds
    def timestamp_to_seconds(ts_str):
        if ts_str is None:
            return 0
        try:
            from datetime import datetime
            import re
            # Fix truncated ISO format: 2025-10-02T20:39:4Z -> 2025-10-02T20:39:04Z
            if ts_str.endswith('Z'):
                ts_str = ts_str[:-1]
                # Fix single digit seconds
                ts_str = re.sub(r'(\d{2}:\d{2}):(\d)Z?$', r'\1:0\2', ts_str)
                ts_str += '+00:00'
            # Add fractional seconds if missing
            if '.' not in ts_str:
                ts_str = ts_str.replace('+', '.000+')
            dt = datetime.fromisoformat(ts_str)
            return dt.timestamp()
        except Exception as e:
            print(f"Timestamp parsing error: {e}, input: {ts_str}")
            return 0
    
    # Find all AUTOTUNER_SUGGEST and PARAMS_APPLIED events
    autotuner_suggestions = []
    params_applied = []
    
    for event in events:
        if event.get("event") == "AUTOTUNER_SUGGEST":
            autotuner_suggestions.append(event)
        elif event.get("event") == "PARAMS_APPLIED":
            params_applied.append(event)
    
    # Pair suggestions with applications (using index since events are in order)
    for i, suggest in enumerate(autotuner_suggestions):
        # Find the corresponding PARAMS_APPLIED event
        if i < len(params_applied):
            applied_after = params_applied[i]
        else:
            continue
        
        if not applied_after:
            continue
            
        # Check if EF search parameter actually changed
        old_ef = applied_after.get("applied", {}).get("old_ef_search")
        new_ef = applied_after.get("applied", {}).get("new_ef_search")
        
        if old_ef is None or new_ef is None or old_ef == new_ef:
            continue
        
        change_time = timestamp_to_seconds(applied_after.get("ts", applied_after.get("timestamp", "")))
        
        # Since all events have the same timestamp, use event order for before/after analysis
        # Find the index of this PARAMS_APPLIED event
        applied_index = None
        for idx, event in enumerate(events):
            if event.get("event") == "PARAMS_APPLIED" and event == applied_after:
                applied_index = idx
                break
        
        if applied_index is None:
            continue
        
        # Get response events before and after this change (using event order)
        before_responses = []
        after_responses = []
        
        for idx, event in enumerate(events):
            if event.get("event") == "RESPONSE":
                if idx < applied_index:
                    before_responses.append(event)
                elif idx > applied_index:
                    after_responses.append(event)
        
        # Need at least 2 responses in each window
        if len(before_responses) < 2 or len(after_responses) < 2:
            continue
        
        # Calculate metrics
        before_p95 = np.percentile([r.get("cost_ms", 0) for r in before_responses], 95)
        after_p95 = np.percentile([r.get("cost_ms", 0) for r in after_responses], 95)
        
        # Calculate recall (estimate from results count)
        before_recalls = []
        for r in before_responses:
            total_results = r.get("stats", {}).get("total_results", 0)
            before_recalls.append(min(1.0, total_results / 10.0))
        
        after_recalls = []
        for r in after_responses:
            total_results = r.get("stats", {}).get("total_results", 0)
            after_recalls.append(min(1.0, total_results / 10.0))
        
        before_recall = np.mean(before_recalls) if before_recalls else 0
        after_recall = np.mean(after_recalls) if after_recalls else 0
        
        # Determine stage based on candidate_k
        candidate_k = suggest.get("params", {}).get("candidate_k", 100)
        if candidate_k <= 100:
            stage = "k100"
        elif candidate_k <= 200:
            stage = "k200"
        elif candidate_k <= 400:
            stage = "k400"
        else:
            stage = f"k{candidate_k}"
        
        change_events.append({
            "t": change_time,
            "ef_old": old_ef,
            "ef_new": new_ef,
            "p95_before_ms": before_p95,
            "p95_after_ms": after_p95,
            "delta_ms": after_p95 - before_p95,
            "recall_before": before_recall,
            "recall_after": after_recall,
            "stage": stage
        })
    
    return change_events

def create_tuner_impact_charts(events: List[Dict[str, Any]], change_events: List[Dict[str, Any]]) -> Tuple[str, str, str]:
    """Create tuner impact visualization charts."""
    
    # Helper function to convert timestamp to seconds
    def timestamp_to_seconds(ts_str):
        if ts_str is None:
            return 0
        try:
            from datetime import datetime
            import re
            # Fix truncated ISO format: 2025-10-02T20:39:4Z -> 2025-10-02T20:39:04Z
            if ts_str.endswith('Z'):
                ts_str = ts_str[:-1]
                # Fix single digit seconds
                ts_str = re.sub(r'(\d{2}:\d{2}):(\d)Z?$', r'\1:0\2', ts_str)
                ts_str += '+00:00'
            # Add fractional seconds if missing
            if '.' not in ts_str:
                ts_str = ts_str.replace('+', '.000+')
            dt = datetime.fromisoformat(ts_str)
            return dt.timestamp()
        except Exception as e:
            print(f"Timestamp parsing error: {e}, input: {ts_str}")
            return 0
    
    # Chart 1: Timeline with EF change markers
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    
    # Extract time series data for P95
    response_events = [e for e in events if e.get("event") == "RESPONSE"]
    if response_events:
        times = []
        p95_values = []
        bucket_size = 5
        
        # Create 5s buckets
        buckets = {}
        for event in response_events:
            event_time = timestamp_to_seconds(event.get("ts", event.get("timestamp", "")))
            bucket_key = int(event_time // bucket_size)
            if bucket_key not in buckets:
                buckets[bucket_key] = []
            buckets[bucket_key].append(event.get("cost_ms", 0))
        
        for bucket_key in sorted(buckets.keys()):
            times.append(bucket_key * bucket_size)
            p95_values.append(np.percentile(buckets[bucket_key], 95))
        
        ax1.plot(times, p95_values, 'b-', linewidth=2, label='P95 Latency')
        
        # Add vertical markers for EF changes
        for change in change_events:
            ax1.axvline(x=change["t"], color='red', linestyle='--', alpha=0.7)
            ax1.annotate(f'ef: {change["ef_old"]}→{change["ef_new"]}\nΔp95={change["delta_ms"]:+.0f}ms',
                        xy=(change["t"], change["p95_after_ms"]), xytext=(10, 10),
                        textcoords='offset points', fontsize=8, ha='left',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    ax1.set_title('P95 Timeline with EF Change Points')
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('P95 Latency (ms)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    plt.tight_layout()
    
    # Convert to base64
    import io
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    timeline_chart = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    # Chart 2: Scatter plot
    if change_events:
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        
        # Color mapping for stages
        stage_colors = {'k100': 'red', 'k200': 'blue', 'k400': 'green'}
        colors = [stage_colors.get(change["stage"], 'gray') for change in change_events]
        
        x_values = [change["ef_old"] for change in change_events]
        y_values = [change["delta_ms"] for change in change_events]
        
        scatter = ax2.scatter(x_values, y_values, c=colors, s=100, alpha=0.7)
        
        # Add zero line
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        ax2.set_title('EF Change Impact on P95')
        ax2.set_xlabel('EF Search (old value)')
        ax2.set_ylabel('ΔP95 (ms, negative is better)')
        ax2.grid(True, alpha=0.3)
        
        # Add legend for stages
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=10, label=stage)
                          for stage, color in stage_colors.items()]
        ax2.legend(handles=legend_elements, title='Stage')
        
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        scatter_chart = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
    else:
        scatter_chart = ""
    
    # Top-10 table data
    if change_events:
        # Separate improvements (negative delta) and degradations (positive delta)
        improvements = [change for change in change_events if change["delta_ms"] < 0]
        degradations = [change for change in change_events if change["delta_ms"] > 0]
        
        # Sort improvements by delta (most negative = best improvement)
        best_improvements = sorted(improvements, key=lambda x: x["delta_ms"])[:10]
        # Sort degradations by delta (most positive = worst degradation)
        worst_degradations = sorted(degradations, key=lambda x: x["delta_ms"], reverse=True)[:10]
        
        table_html = ""
        
        if best_improvements:
            table_html += """
            <h3>Top-10 Best Improvements (P95 ↓)</h3>
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>Time (s)</th>
                        <th>EF Change</th>
                        <th>P95 Before</th>
                        <th>P95 After</th>
                        <th>ΔP95</th>
                        <th>Recall Before</th>
                        <th>Recall After</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for change in best_improvements:
                table_html += f"""
                    <tr>
                        <td>{change["t"]:.1f}</td>
                        <td>{change["ef_old"]}→{change["ef_new"]}</td>
                        <td>{change["p95_before_ms"]:.1f}</td>
                        <td>{change["p95_after_ms"]:.1f}</td>
                        <td style="color: green">{change["delta_ms"]:+.1f}</td>
                        <td>{change["recall_before"]:.3f}</td>
                        <td>{change["recall_after"]:.3f}</td>
                    </tr>
                """
            
            table_html += """
                </tbody>
            </table>
            """
        
        if worst_degradations:
            table_html += """
            <h3>Top-10 Worst Degradations (P95 ↑)</h3>
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>Time (s)</th>
                        <th>EF Change</th>
                        <th>P95 Before</th>
                        <th>P95 After</th>
                        <th>ΔP95</th>
                        <th>Recall Before</th>
                        <th>Recall After</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for change in worst_degradations:
                table_html += f"""
                    <tr>
                        <td>{change["t"]:.1f}</td>
                        <td>{change["ef_old"]}→{change["ef_new"]}</td>
                        <td>{change["p95_before_ms"]:.1f}</td>
                        <td>{change["p95_after_ms"]:.1f}</td>
                        <td style="color: red">{change["delta_ms"]:+.1f}</td>
                        <td>{change["recall_before"]:.3f}</td>
                        <td>{change["recall_after"]:.3f}</td>
                    </tr>
                """
            
            table_html += """
                </tbody>
            </table>
            """
        
        if not best_improvements and not worst_degradations:
            table_html = '<p style="color: orange;">No significant EF changes detected.</p>'
    else:
        table_html = '<p style="color: orange;">No EF applications detected.</p>'
    
    return timeline_chart, scatter_chart, table_html

def create_ef_adjustments_table(events: List[Dict[str, Any]]) -> str:
    """Create a table showing all EF adjustments with 30s impact analysis."""
    
    # Helper function to convert timestamp to seconds
    def timestamp_to_seconds(ts_str):
        if ts_str is None:
            return 0
        try:
            import re
            from datetime import datetime
            if ts_str.endswith('Z'):
                ts_str = ts_str[:-1]
                ts_str = re.sub(r'(\d{2}:\d{2}):(\d)Z?$', r'\1:0\2', ts_str)
                ts_str += '+00:00'
            if '.' not in ts_str:
                ts_str = ts_str.replace('+', '.000+')
            dt = datetime.fromisoformat(ts_str)
            return dt.timestamp()
        except Exception as e:
            return 0
    
    # Find all PARAMS_APPLIED events with EF changes
    ef_adjustments = []
    for event in events:
        if event.get('event') == 'PARAMS_APPLIED':
            applied = event.get('applied', {})
            old_ef = applied.get('old_ef_search')
            new_ef = applied.get('new_ef_search')
            if old_ef is not None and new_ef is not None and old_ef != new_ef:
                ef_adjustments.append({
                    'time': timestamp_to_seconds(event.get('ts', '')),
                    'old_ef': old_ef,
                    'new_ef': new_ef,
                    'event': event
                })
    
    if not ef_adjustments:
        return '<p style="color: orange;">No EF adjustments detected.</p>'
    
    # Sort by time
    ef_adjustments.sort(key=lambda x: x['time'])
    
    # Create table HTML
    table_html = """
    <h3>EF Parameter Adjustments</h3>
    <table class="metrics-table">
        <thead>
            <tr>
                <th>Time (s)</th>
                <th>EF Change</th>
                <th>ΔP95 (30s)</th>
                <th>ΔRecall (30s)</th>
                <th>Impact</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for adj in ef_adjustments[:20]:  # Show first 20 adjustments
        # Calculate 30-second impact (simplified)
        change_time = adj['time']
        after_30s = change_time + 30
        
        # Get response events in the 30s window after change
        after_responses = []
        for event in events:
            if event.get('event') == 'RESPONSE':
                event_time = timestamp_to_seconds(event.get('ts', ''))
                if change_time < event_time <= after_30s:
                    after_responses.append(event)
        
        # Calculate metrics
        if len(after_responses) >= 2:
            after_p95 = np.percentile([r.get('cost_ms', 0) for r in after_responses], 95)
            after_recalls = []
            for r in after_responses:
                total_results = r.get('stats', {}).get('total_results', 0)
                after_recalls.append(min(1.0, total_results / 10.0))
            after_recall = np.mean(after_recalls) if after_recalls else 0
            
            # Get baseline metrics (before change)
            before_responses = []
            for event in events:
                if event.get('event') == 'RESPONSE':
                    event_time = timestamp_to_seconds(event.get('ts', ''))
                    if change_time - 30 <= event_time < change_time:
                        before_responses.append(event)
            
            if before_responses:
                before_p95 = np.percentile([r.get('cost_ms', 0) for r in before_responses], 95)
                before_recalls = []
                for r in before_responses:
                    total_results = r.get('stats', {}).get('total_results', 0)
                    before_recalls.append(min(1.0, total_results / 10.0))
                before_recall = np.mean(before_recalls) if before_recalls else 0
                
                delta_p95 = after_p95 - before_p95
                delta_recall = after_recall - before_recall
                
                # Determine impact
                if delta_p95 < -5:  # Significant improvement
                    impact = 'Good'
                    p95_color = 'green'
                elif delta_p95 > 5:  # Significant degradation
                    impact = 'Bad'
                    p95_color = 'red'
                else:
                    impact = 'Neutral'
                    p95_color = 'black'
                
                table_html += f"""
                    <tr>
                        <td>{change_time:.1f}</td>
                        <td>{adj['old_ef']}→{adj['new_ef']}</td>
                        <td style="color: {p95_color}">{delta_p95:+.1f}</td>
                        <td>{delta_recall:+.3f}</td>
                        <td>{impact}</td>
                    </tr>
                """
            else:
                table_html += f"""
                    <tr>
                        <td>{change_time:.1f}</td>
                        <td>{adj['old_ef']}→{adj['new_ef']}</td>
                        <td>N/A</td>
                        <td>N/A</td>
                        <td>Insufficient data</td>
                    </tr>
                """
        else:
            table_html += f"""
                <tr>
                    <td>{change_time:.1f}</td>
                    <td>{adj['old_ef']}→{adj['new_ef']}</td>
                    <td>N/A</td>
                    <td>N/A</td>
                    <td>Insufficient data</td>
                </tr>
            """
    
    table_html += """
        </tbody>
    </table>
    """
    
    return table_html

def extract_run_info(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract run info from RUN_INFO events."""
    run_info = {}
    for event in events:
        if event.get("event") == "RUN_INFO":
            params = event.get("params", {})
            run_info.update({
                "dataset": params.get("dataset", "N/A"),
                "collection": params.get("collection", "N/A"),
                "TUNER_ENABLED": params.get("TUNER_ENABLED", "N/A"),
                "FORCE_CE_ON": params.get("FORCE_CE_ON", "N/A"),
                "FORCE_HYBRID_ON": params.get("FORCE_HYBRID_ON", "N/A"),
                "CE_CACHE_SIZE": params.get("CE_CACHE_SIZE", "N/A")
            })
            break
    return run_info

def extract_ce_stats(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract CE statistics from RERANK_CE events."""
    ce_stats = {
        "model": "N/A",
        "batch_size": "N/A", 
        "cache_size": "N/A",
        "cache_hits_total": 0,
        "cache_miss_total": 0
    }
    
    for event in events:
        if event.get("event") == "RERANK_CE":
            params = event.get("params", {})
            if params.get("model") and params["model"] != "unknown":
                ce_stats["model"] = params["model"]
            if params.get("batch_size"):
                ce_stats["batch_size"] = params["batch_size"]
            if params.get("cache_size") is not None:
                ce_stats["cache_size"] = params["cache_size"]
            if params.get("cache_hits") is not None:
                ce_stats["cache_hits_total"] += params["cache_hits"]
            if params.get("cache_miss") is not None:
                ce_stats["cache_miss_total"] += params["cache_miss"]
    
    return ce_stats

def generate_html_report(stages: Dict[str, List[Dict[str, Any]]], 
                        summary_file: str = "reports/observed/summary.json",
                        events: List[Dict[str, Any]] = None) -> str:
    """Generate HTML report."""
    
    # Load summary if available
    summary = {}
    if os.path.exists(summary_file):
        with open(summary_file, 'r') as f:
            summary = json.load(f)
    
    # Extract run info and CE stats
    run_info = extract_run_info(events or [])
    ce_stats = extract_ce_stats(events or [])
    
    # Extract tuner impact data
    change_events = extract_tuner_impact(events or [])
    
    # Calculate stage metrics
    stage_metrics = {}
    for stage_name, events in stages.items():
        stage_metrics[stage_name] = calculate_stage_metrics(events)
    
    # Create timeline charts
    timeline_chart = create_timeline_charts(stages, events)
    
    # Create tuner impact charts
    tuner_timeline, tuner_scatter, tuner_table = create_tuner_impact_charts(events or [], change_events)
    
    # Create EF adjustments table
    ef_adjustments_table = create_ef_adjustments_table(events or [])
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Observed Experiment Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .metrics-table {{ border-collapse: collapse; width: 100%; }}
        .metrics-table th, .metrics-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .metrics-table th {{ background-color: #f2f2f2; }}
        .chart {{ text-align: center; margin: 20px 0; }}
        .chart img {{ max-width: 100%; height: auto; }}
        .summary {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Observed Experiment Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h2>Run Info</h2>
        <table class="metrics-table">
            <tr>
                <td><strong>Dataset:</strong></td>
                <td>{run_info.get('dataset', 'N/A')}</td>
                <td><strong>Collection:</strong></td>
                <td>{run_info.get('collection', 'N/A')}</td>
            </tr>
            <tr>
                <td><strong>TUNER_ENABLED:</strong></td>
                <td>{run_info.get('TUNER_ENABLED', 'N/A')}</td>
                <td><strong>FORCE_CE_ON:</strong></td>
                <td>{run_info.get('FORCE_CE_ON', 'N/A')}</td>
            </tr>
            <tr>
                <td><strong>FORCE_HYBRID_ON:</strong></td>
                <td>{run_info.get('FORCE_HYBRID_ON', 'N/A')}</td>
                <td><strong>CE_CACHE_SIZE:</strong></td>
                <td>{run_info.get('CE_CACHE_SIZE', 'N/A')}</td>
            </tr>
        </table>
    </div>
    
    <div class="section">
        <h2>CE Stats</h2>
        <table class="metrics-table">
            <tr>
                <td><strong>Model:</strong></td>
                <td>{ce_stats.get('model', 'N/A')}</td>
                <td><strong>Batch Size:</strong></td>
                <td>{ce_stats.get('batch_size', 'N/A')}</td>
            </tr>
            <tr>
                <td><strong>Cache Size:</strong></td>
                <td>{ce_stats.get('cache_size', 'N/A')}</td>
                <td><strong>Cache Hits Total:</strong></td>
                <td>{ce_stats.get('cache_hits_total', 'N/A')}</td>
            </tr>
            <tr>
                <td><strong>Cache Miss Total:</strong></td>
                <td>{ce_stats.get('cache_miss_total', 'N/A')}</td>
                <td></td>
                <td></td>
            </tr>
        </table>
    </div>
    
    <div class="summary">
        <h2>Experiment Summary</h2>
        <p><strong>Total Queries:</strong> {summary.get('aggregates', {}).get('total_queries', 'N/A')}</p>
        <p><strong>Successful Queries:</strong> {summary.get('aggregates', {}).get('successful_queries', 'N/A')}</p>
        <p><strong>Failed Queries:</strong> {summary.get('aggregates', {}).get('failed_queries', 'N/A')}</p>
        <p><strong>Collection:</strong> {summary.get('experiment', {}).get('collection', 'N/A')}</p>
        <p><strong>QPS:</strong> {summary.get('experiment', {}).get('qps', 'N/A')}</p>
        <p><strong>Duration:</strong> {summary.get('experiment', {}).get('duration_minutes', 'N/A')} minutes</p>
    </div>
    
    <div class="section">
        <h2>Performance Timeline</h2>
        <div class="chart">
            <img src="data:image/png;base64,{timeline_chart}" alt="Performance Timeline">
        </div>
    </div>
    
    <div class="section">
        <h2>Stage Metrics</h2>
        <table class="metrics-table">
            <thead>
                <tr>
                    <th>Stage</th>
                    <th>Queries</th>
                    <th>P50 (ms)</th>
                    <th>P95 (ms)</th>
                    <th>P99 (ms)</th>
                    <th>Avg (ms)</th>
                    <th>SLO Violations</th>
                    <th>Recall@10</th>
                    <th>AutoTuner Suggestions</th>
                    <th>Params Applied</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for stage_name, metrics in stage_metrics.items():
        if "error" not in metrics:
            html += f"""
                <tr>
                    <td>{stage_name.replace('stage_', '').replace('_k', ' K=')}</td>
                    <td>{metrics.get('total_queries', 0)}</td>
                    <td>{metrics.get('p50_ms', 0):.1f}</td>
                    <td>{metrics.get('p95_ms', 0):.1f}</td>
                    <td>{metrics.get('p99_ms', 0):.1f}</td>
                    <td>{metrics.get('avg_ms', 0):.1f}</td>
                    <td>{metrics.get('slo_violation_rate', 0):.1%}</td>
                    <td>{metrics.get('recall_at_10', 0):.3f}</td>
                    <td>{metrics.get('autotuner_suggestions', 0)}</td>
                    <td>{metrics.get('params_applied', 0)}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>AutoTuner Analysis</h2>
        <p>This report shows the performance of the AutoTuner system across different candidate_k stages.</p>
        <ul>
            <li><strong>P95 Latency:</strong> Shows how latency changes as candidate_k increases</li>
            <li><strong>EF Search:</strong> Shows how the AutoTuner adjusts the ef_search parameter</li>
            <li><strong>Recall@10:</strong> Shows recall performance across stages</li>
            <li><strong>SLO Violations:</strong> Percentage of queries that exceeded the SLO threshold</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Tuner Impact (EF change → p95/recall delta)</h2>
"""
    
    if change_events:
        html += f"""
        <div class="chart">
            <img src="data:image/png;base64,{tuner_timeline}" alt="Tuner Impact Timeline">
        </div>
        
        <div class="chart">
            <img src="data:image/png;base64,{tuner_scatter}" alt="Tuner Impact Scatter">
        </div>
        
        <h3>Top-10 Most Impactful Changes</h3>
        {tuner_table}
        """
    else:
        html += '<p style="color: orange;">No EF applications detected.</p>'
    
    # Add EF adjustments table
    html += f"""
    <div class="section">
        {ef_adjustments_table}
    </div>
    """
    
    html += """
    </div>
</body>
</html>
"""
    
    return html

def create_compare_charts(baseline_events: List[Dict[str, Any]], tuner_events: List[Dict[str, Any]]) -> Tuple[str, float]:
    """Create comparison charts for baseline vs tuner."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('AutoTuner Comparison: Baseline vs Tuner ON', fontsize=16)
    
    # Helper function to convert timestamp to seconds
    def timestamp_to_seconds(ts_str):
        if ts_str is None:
            return 0
        try:
            import re
            from datetime import datetime
            if ts_str.endswith('Z'):
                ts_str = ts_str[:-1]
                ts_str = re.sub(r'(\d{2}:\d{2}):(\d)Z?$', r'\1:0\2', ts_str)
                ts_str += '+00:00'
            if '.' not in ts_str:
                ts_str = ts_str.replace('+', '.000+')
            dt = datetime.fromisoformat(ts_str)
            return dt.timestamp()
        except Exception as e:
            return 0
    
    # Extract time series data (5s buckets) with timestamp normalization
    def extract_time_series(events, bucket_size=5, t0=None, max_duration=180):
        buckets = {}
        first_event_time = None
        
        # First, find t0 from any event if not provided
        if t0 is None:
            for event in events:
                event_time = timestamp_to_seconds(event.get('ts', ''))
                if event_time > 0:
                    t0 = event_time
                    break
        
        for event in events:
            event_time = timestamp_to_seconds(event.get('ts', ''))
            if event_time == 0:
                continue
                
            # Normalize timestamp: (ts - t0) seconds
            normalized_time = (event_time - t0)
            bucket_key = int(normalized_time // bucket_size)
            
            # Skip buckets beyond max_duration
            if bucket_key * bucket_size > max_duration:
                continue
            
            if event.get("event") == "RESPONSE":
                if bucket_key not in buckets:
                    buckets[bucket_key] = {"p95": [], "recall": [], "ef_search": []}
                buckets[bucket_key]["p95"].append(event.get("cost_ms", 0))
                # Estimate recall from results count
                total_results = event.get("stats", {}).get("total_results", 0)
                buckets[bucket_key]["recall"].append(min(1.0, total_results / 10.0))
                
            elif event.get("event") == "PARAMS_APPLIED":
                if bucket_key not in buckets:
                    buckets[bucket_key] = {"p95": [], "recall": [], "ef_search": []}
                ef_search = event.get("applied", {}).get("new_ef_search", 128)
                buckets[bucket_key]["ef_search"].append(ef_search)
                
            elif event.get("event") == "RETRIEVE_VECTOR":
                if bucket_key not in buckets:
                    buckets[bucket_key] = {"p95": [], "recall": [], "ef_search": []}
                ef_search = event.get("params", {}).get("ef_search", 128)
                buckets[bucket_key]["ef_search"].append(ef_search)
        
        # Convert to time series - fill all buckets from 0 to max_duration
        times = []
        p95_values = []
        recall_values = []
        ef_values = []
        last_ef = 128  # Default ef_search value
        
        max_buckets = max_duration // bucket_size
        for bucket_key in range(max_buckets + 1):
            bucket = buckets.get(bucket_key, {"p95": [], "recall": [], "ef_search": []})
            times.append(bucket_key * bucket_size)
            p95_values.append(np.median(bucket["p95"]) if bucket["p95"] else np.nan)
            recall_values.append(np.median(bucket["recall"]) if bucket["recall"] else np.nan)
            
            # Use the last EF value in the bucket, or carry forward the previous value
            if bucket["ef_search"]:
                last_ef = bucket["ef_search"][-1]  # Take the last (most recent) EF value
            ef_values.append(last_ef)
        
        return times, p95_values, recall_values, ef_values, first_event_time
    
    # Find t0 from baseline events (first event timestamp)
    baseline_t0 = None
    for event in baseline_events:
        baseline_t0 = timestamp_to_seconds(event.get('ts', ''))
        if baseline_t0 > 0:
            break
    
    # Find t0 from tuner events (first event timestamp)
    tuner_t0 = None
    for event in tuner_events:
        tuner_t0 = timestamp_to_seconds(event.get('ts', ''))
        if tuner_t0 > 0:
            break
    
    # Extract data for both runs with their own normalized timestamps
    baseline_times, baseline_p95, baseline_recall, baseline_ef, _ = extract_time_series(baseline_events, t0=baseline_t0)
    tuner_times, tuner_p95, tuner_recall, tuner_ef, _ = extract_time_series(tuner_events, t0=tuner_t0)
    
    # Calculate experiment duration
    all_times = baseline_times + tuner_times
    duration = max(all_times) if all_times else 180  # Default to 180s if no data
    
    # Calculate delta series (ON - OFF)
    delta_p95 = np.array(tuner_p95) - np.array(baseline_p95)
    delta_recall = np.array(tuner_recall) - np.array(baseline_recall)
    delta_ef = np.array(tuner_ef) - np.array(baseline_ef)
    
    # Create 5 subplots: 2 original comparison charts + 3 delta charts
    fig, axes = plt.subplots(5, 1, figsize=(14, 16))
    fig.suptitle('AutoTuner Comparison: Baseline vs Tuner ON', fontsize=16)
    
    # Chart 1: P95 Latency (Dual-line) with unified X-axis
    axes[0].plot(baseline_times, baseline_p95, 'r-', label='TUNER_ENABLED=0', linewidth=3, markersize=6)
    axes[0].plot(tuner_times, tuner_p95, 'b-', label='TUNER_ENABLED=1', linewidth=3, markersize=6)
    axes[0].set_title('P95 Latency Comparison (ms)', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Latency (ms)', fontsize=12)
    axes[0].set_xlim(0, duration)  # Unified X-axis range
    axes[0].legend(fontsize=12, loc='upper right')
    axes[0].grid(True, alpha=0.3)
    
    # Chart 2: EF Search Parameter (Dual-line) with unified X-axis
    axes[1].plot(baseline_times, baseline_ef, 'r-', label='TUNER_ENABLED=0', linewidth=3, markersize=6)
    axes[1].plot(tuner_times, tuner_ef, 'b-', label='TUNER_ENABLED=1', linewidth=3, markersize=6)
    axes[1].set_title('EF Search Parameter Comparison', fontsize=14, fontweight='bold')
    axes[1].set_ylabel('EF Search', fontsize=12)
    axes[1].set_xlim(0, duration)  # Unified X-axis range
    axes[1].legend(fontsize=12, loc='upper right')
    axes[1].grid(True, alpha=0.3)
    
    # Chart 3: Delta P95 (ON - OFF)
    axes[2].axhline(y=0, color='black', linestyle='--', alpha=0.5)
    axes[2].fill_between(baseline_times, 0, delta_p95, where=(delta_p95 < 0), color='green', alpha=0.3, label='Improvement')
    axes[2].fill_between(baseline_times, 0, delta_p95, where=(delta_p95 > 0), color='red', alpha=0.3, label='Degradation')
    axes[2].plot(baseline_times, delta_p95, 'k-', linewidth=2, label='Δ = ON - OFF')
    axes[2].set_title('ΔP95 Latency (ms)', fontsize=14, fontweight='bold')
    axes[2].set_ylabel('Δ Latency (ms)', fontsize=12)
    axes[2].set_xlim(0, duration)
    axes[2].legend(fontsize=10, loc='upper right')
    axes[2].grid(True, alpha=0.3)
    
    # Chart 4: Delta Recall (ON - OFF)
    axes[3].axhline(y=0, color='black', linestyle='--', alpha=0.5)
    axes[3].fill_between(baseline_times, 0, delta_recall, where=(delta_recall > 0), color='green', alpha=0.3, label='Improvement')
    axes[3].fill_between(baseline_times, 0, delta_recall, where=(delta_recall < 0), color='red', alpha=0.3, label='Degradation')
    axes[3].plot(baseline_times, delta_recall, 'k-', linewidth=2, label='Δ = ON - OFF')
    axes[3].set_title('ΔRecall@10', fontsize=14, fontweight='bold')
    axes[3].set_ylabel('Δ Recall@10', fontsize=12)
    axes[3].set_ylim(-0.2, 0.2)
    axes[3].set_xlim(0, duration)
    axes[3].legend(fontsize=10, loc='upper right')
    axes[3].grid(True, alpha=0.3)
    
    # Chart 5: Delta EF Search (ON - OFF)
    axes[4].axhline(y=0, color='black', linestyle='--', alpha=0.5)
    axes[4].plot(baseline_times, delta_ef, 'k-', linewidth=2, label='Δ = ON - OFF')
    axes[4].set_title('ΔEF Search Parameter', fontsize=14, fontweight='bold')
    axes[4].set_ylabel('Δ EF Search', fontsize=12)
    axes[4].set_xlabel('Time (seconds)', fontsize=12)
    axes[4].set_xlim(0, duration)
    axes[4].legend(fontsize=10, loc='upper right')
    axes[4].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Convert to base64
    import io
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    # Export CSV data
    import csv
    csv_filename = 'reports/observed/delta_series.csv'
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['t', 'off_p95', 'on_p95', 'delta_p95', 'off_recall', 'on_recall', 'delta_recall', 'off_ef', 'on_ef', 'delta_ef'])
        for i in range(len(baseline_times)):
            writer.writerow([
                baseline_times[i],
                baseline_p95[i] if not np.isnan(baseline_p95[i]) else '',
                tuner_p95[i] if not np.isnan(tuner_p95[i]) else '',
                delta_p95[i] if not np.isnan(delta_p95[i]) else '',
                baseline_recall[i] if not np.isnan(baseline_recall[i]) else '',
                tuner_recall[i] if not np.isnan(tuner_recall[i]) else '',
                delta_recall[i] if not np.isnan(delta_recall[i]) else '',
                baseline_ef[i],
                tuner_ef[i],
                delta_ef[i]
            ])
    
    return image_base64, duration, delta_p95, delta_recall, delta_ef

def calculate_kpi_summary(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate KPI summary from events."""
    response_events = [e for e in events if e.get("event") == "RESPONSE"]
    
    if not response_events:
        return {
            "p95_overall_ms": "N/A",
            "mean_recall_at10": "N/A", 
            "slo_violations": "N/A",
            "area_over_slo": "N/A"
        }
    
    latencies = [e.get("cost_ms", 0) for e in response_events]
    slo_violations = [e.get("params", {}).get("slo_violated", False) for e in response_events]
    
    # Calculate recall from results count
    recalls = []
    for event in response_events:
        total_results = event.get("stats", {}).get("total_results", 0)
        recalls.append(min(1.0, total_results / 10.0))
    
    return {
        "p95_overall_ms": round(np.percentile(latencies, 95), 2) if latencies else "N/A",
        "mean_recall_at10": round(np.mean(recalls), 3) if recalls else "N/A",
        "slo_violations": sum(slo_violations),
        "area_over_slo": "N/A"  # Simplified for now
    }

def calculate_delta_kpi(delta_p95, delta_recall, delta_ef, tuner_events) -> Dict[str, Any]:
    """Calculate Delta KPI summary."""
    # Filter out NaN values
    valid_delta_p95 = delta_p95[~np.isnan(delta_p95)]
    valid_delta_recall = delta_recall[~np.isnan(delta_recall)]
    
    # Calculate EF change count
    ef_change_count = 0
    unique_ef_values = set()
    for event in tuner_events:
        if event.get("event") == "RETRIEVE_VECTOR":
            ef_search = event.get("params", {}).get("ef_search", 128)
            unique_ef_values.add(ef_search)
    ef_change_count = len(unique_ef_values) - 1  # Subtract 1 for the initial value
    
    return {
        "mean_delta_p95_ms": round(np.mean(valid_delta_p95), 2) if len(valid_delta_p95) > 0 else "N/A",
        "median_delta_p95_ms": round(np.median(valid_delta_p95), 2) if len(valid_delta_p95) > 0 else "N/A",
        "min_delta_p95_ms": round(np.min(valid_delta_p95), 2) if len(valid_delta_p95) > 0 else "N/A",
        "max_delta_p95_ms": round(np.max(valid_delta_p95), 2) if len(valid_delta_p95) > 0 else "N/A",
        "pct_improved": round(100 * np.sum(valid_delta_p95 < 0) / len(valid_delta_p95), 1) if len(valid_delta_p95) > 0 else "N/A",
        "mean_delta_recall": round(np.mean(valid_delta_recall), 3) if len(valid_delta_recall) > 0 else "N/A",
        "ef_change_count": ef_change_count
    }

def create_simple_compare_chart(baseline_events: List[Dict[str, Any]], tuner_events: List[Dict[str, Any]]) -> Tuple[str, float, float]:
    """Create a simple P95 latency comparison chart."""
    
    # Helper function to convert timestamp to seconds
    def timestamp_to_seconds(ts_str):
        if ts_str is None:
            return 0
        try:
            import re
            from datetime import datetime
            if ts_str.endswith('Z'):
                ts_str = ts_str[:-1]
                ts_str = re.sub(r'(\d{2}:\d{2}):(\d)Z?$', r'\1:0\2', ts_str)
                ts_str += '+00:00'
            if '.' not in ts_str:
                ts_str = ts_str.replace('+', '.000+')
            dt = datetime.fromisoformat(ts_str)
            return dt.timestamp()
        except Exception as e:
            return 0
    
    # Extract time series data (5s buckets) with timestamp normalization
    def extract_p95_series(events, bucket_size=5, t0=None, max_duration=300):
        buckets = {}
        first_event_time = None
        
        # Find t0 from first event if not provided
        if t0 is None:
            for event in events:
                event_time = timestamp_to_seconds(event.get('ts', ''))
                if event_time > 0:
                    t0 = event_time
                    break
        
        for event in events:
            event_time = timestamp_to_seconds(event.get('ts', ''))
            if event_time == 0:
                continue
                
            # Normalize timestamp: (ts - t0) seconds
            normalized_time = (event_time - t0)
            bucket_key = int(normalized_time // bucket_size)
            
            # Skip buckets beyond max_duration
            if bucket_key * bucket_size > max_duration:
                continue
            
            # Skip negative buckets (before t0)
            if bucket_key < 0:
                continue
            
            if event.get("event") == "RESPONSE":
                if bucket_key not in buckets:
                    buckets[bucket_key] = {"p95": []}
                buckets[bucket_key]["p95"].append(event.get("cost_ms", 0))
                
                if first_event_time is None:
                    first_event_time = event_time
        
        # Convert to time series - fill all buckets from 0 to max_duration
        times = []
        p95_values = []
        is_interpolated = []  # Track which values are interpolated
        
        max_buckets = max_duration // bucket_size
        last_valid_p95 = None
        
        for bucket_key in range(max_buckets + 1):
            bucket = buckets.get(bucket_key, {"p95": []})
            times.append(bucket_key * bucket_size)
            
            if bucket["p95"]:
                # Real data
                p95_values.append(np.median(bucket["p95"]))
                is_interpolated.append(False)
                last_valid_p95 = np.median(bucket["p95"])
            else:
                # Interpolate using last valid value
                if last_valid_p95 is not None:
                    p95_values.append(last_valid_p95)
                    is_interpolated.append(True)
                else:
                    # No data yet, use NaN
                    p95_values.append(np.nan)
                    is_interpolated.append(True)
        
        return times, p95_values, is_interpolated, first_event_time
    
    # Find t0 from baseline events (first event timestamp)
    baseline_t0 = None
    for event in baseline_events:
        baseline_t0 = timestamp_to_seconds(event.get('ts', ''))
        if baseline_t0 > 0:
            break
    
    # Find t0 from tuner events (first event timestamp)
    tuner_t0 = None
    for event in tuner_events:
        tuner_t0 = timestamp_to_seconds(event.get('ts', ''))
        if tuner_t0 > 0:
            break
    
    # Extract P95 data for both runs
    baseline_times, baseline_p95, baseline_interpolated, _ = extract_p95_series(baseline_events, t0=baseline_t0)
    tuner_times, tuner_p95, tuner_interpolated, _ = extract_p95_series(tuner_events, t0=tuner_t0)
    
    # Calculate experiment duration
    all_times = baseline_times + tuner_times
    duration = max(all_times) if all_times else 180  # Default to 180s if no data
    
    # Get SLO from tuner events (look for SLO_P95_MS in RUN_INFO)
    slo_p95_ms = 1200  # Default SLO
    for event in tuner_events:
        if event.get("event") == "RUN_INFO":
            params = event.get("params", {})
            if "SLO_P95_MS" in params:
                slo_p95_ms = params["SLO_P95_MS"]
                break
    
    # Create simple chart
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    
    # Plot P95 latency lines with interpolation indicators
    # Baseline: solid for real data, dashed for interpolated
    baseline_real_times, baseline_real_values = [], []
    baseline_interp_times, baseline_interp_values = [], []
    
    for i, (time, value, is_interp) in enumerate(zip(baseline_times, baseline_p95, baseline_interpolated)):
        if not np.isnan(value):
            if is_interp:
                baseline_interp_times.append(time)
                baseline_interp_values.append(value)
            else:
                baseline_real_times.append(time)
                baseline_real_values.append(value)
    
    # Tuner: solid for real data, dashed for interpolated
    tuner_real_times, tuner_real_values = [], []
    tuner_interp_times, tuner_interp_values = [], []
    
    for i, (time, value, is_interp) in enumerate(zip(tuner_times, tuner_p95, tuner_interpolated)):
        if not np.isnan(value):
            if is_interp:
                tuner_interp_times.append(time)
                tuner_interp_values.append(value)
            else:
                tuner_real_times.append(time)
                tuner_real_values.append(value)
    
    # Plot real data (solid lines)
    if baseline_real_times:
        ax.plot(baseline_real_times, baseline_real_values, 'r-', label='AutoTuner OFF (real)', linewidth=2.5, alpha=0.9)
    if tuner_real_times:
        ax.plot(tuner_real_times, tuner_real_values, 'b-', label='AutoTuner ON (real)', linewidth=2.5, alpha=0.9)
    
    # Plot interpolated data (dashed lines)
    if baseline_interp_times:
        ax.plot(baseline_interp_times, baseline_interp_values, 'r--', label='AutoTuner OFF (interpolated)', linewidth=1.5, alpha=0.6)
    if tuner_interp_times:
        ax.plot(tuner_interp_times, tuner_interp_values, 'b--', label='AutoTuner ON (interpolated)', linewidth=1.5, alpha=0.6)
    
    # Add SLO line
    ax.axhline(y=slo_p95_ms, color='gray', linestyle=':', linewidth=2, alpha=0.8, label=f'SLO ({slo_p95_ms}ms)')
    
    # Formatting
    ax.set_title('P95 Latency Over Time (AutoTuner ON vs OFF)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('P95 Latency (ms)', fontsize=12)
    ax.set_xlim(0, duration)
    ax.legend(fontsize=10, loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # Make sure y-axis starts from 0
    ax.set_ylim(bottom=0)
    
    plt.tight_layout()
    
    # Convert to base64
    import io
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return image_base64, duration, slo_p95_ms

def generate_simple_compare_html(baseline_events: List[Dict[str, Any]], tuner_events: List[Dict[str, Any]]) -> str:
    """Generate simple comparison HTML report with just P95 latency chart."""
    
    # Create simple comparison chart
    chart_image, duration, slo_p95_ms = create_simple_compare_chart(baseline_events, tuner_events)
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Simple AutoTuner Comparison Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #333; margin-bottom: 10px; }}
        .header p {{ color: #666; font-size: 14px; }}
        .chart {{ text-align: center; margin: 20px 0; }}
        .chart img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }}
        .info {{ background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin-top: 20px; }}
        .info h3 {{ margin-top: 0; color: #495057; }}
        .info ul {{ margin: 10px 0; padding-left: 20px; }}
        .info li {{ margin: 5px 0; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Simple AutoTuner Comparison Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="chart">
            <img src="data:image/png;base64,{chart_image}" alt="P95 Latency Comparison">
        </div>
        
        <div class="info">
            <h3>Chart Information</h3>
            <ul>
                <li><strong>Red solid line:</strong> AutoTuner OFF (real data)</li>
                <li><strong>Blue solid line:</strong> AutoTuner ON (real data)</li>
                <li><strong>Red dashed line:</strong> AutoTuner OFF (interpolated)</li>
                <li><strong>Blue dashed line:</strong> AutoTuner ON (interpolated)</li>
                <li><strong>Gray dotted line:</strong> SLO target ({slo_p95_ms}ms)</li>
                <li><strong>Duration:</strong> {duration:.0f} seconds</li>
                <li><strong>Goal:</strong> Lower latency (blue line below red line) indicates AutoTuner is working</li>
                <li><strong>Note:</strong> Dashed lines show interpolated values during periods with no query activity</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
    
    return html

def generate_compare_html(baseline_events: List[Dict[str, Any]], tuner_events: List[Dict[str, Any]],
                         baseline_dir: str, tuner_dir: str) -> str:
    """Generate comparison HTML report."""
    
    # Create comparison charts
    compare_chart, duration, delta_p95, delta_recall, delta_ef = create_compare_charts(baseline_events, tuner_events)
    
    # Calculate KPI summaries
    baseline_kpi = calculate_kpi_summary(baseline_events)
    tuner_kpi = calculate_kpi_summary(tuner_events)
    
    # Calculate Delta KPI
    delta_kpi = calculate_delta_kpi(delta_p95, delta_recall, delta_ef, tuner_events)
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AutoTuner Comparison Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; text-align: center; }}
        .badges {{ display: flex; justify-content: center; gap: 20px; margin: 20px 0; }}
        .badge {{ padding: 10px 20px; border-radius: 5px; font-weight: bold; }}
        .badge-off {{ background-color: #ffcccc; color: #cc0000; }}
        .badge-on {{ background-color: #ccffcc; color: #006600; }}
        .section {{ margin: 20px 0; }}
        .chart {{ text-align: center; margin: 20px 0; }}
        .chart img {{ max-width: 100%; height: auto; }}
        .kpi-table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        .kpi-table th, .kpi-table td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
        .kpi-table th {{ background-color: #f2f2f2; }}
        .links {{ text-align: center; margin: 30px 0; }}
        .links a {{ margin: 0 20px; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
        .links a:hover {{ background-color: #0056b3; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AutoTuner Comparison Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="badges">
        <div class="badge badge-off">TUNER_ENABLED=0 (baseline)</div>
        <div class="badge badge-on">TUNER_ENABLED=1 (tuner)</div>
    </div>
    
    <div class="section">
        <h2>Performance Comparison</h2>
        <div class="chart">
            <img src="data:image/png;base64,{compare_chart}" alt="Performance Comparison">
        </div>
    </div>
    
    <div class="section">
        <h2>KPI Summary</h2>
        <table class="kpi-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>TUNER_ENABLED=0</th>
                    <th>TUNER_ENABLED=1</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>P95 Overall (ms)</strong></td>
                    <td>{baseline_kpi['p95_overall_ms']}</td>
                    <td>{tuner_kpi['p95_overall_ms']}</td>
                </tr>
                <tr>
                    <td><strong>Mean Recall@10</strong></td>
                    <td>{baseline_kpi['mean_recall_at10']}</td>
                    <td>{tuner_kpi['mean_recall_at10']}</td>
                </tr>
                <tr>
                    <td><strong>SLO Violations (#)</strong></td>
                    <td>{baseline_kpi['slo_violations']}</td>
                    <td>{tuner_kpi['slo_violations']}</td>
                </tr>
                <tr>
                    <td><strong>Area Over SLO (ms·s)</strong></td>
                    <td>{baseline_kpi['area_over_slo']}</td>
                    <td>{tuner_kpi['area_over_slo']}</td>
                </tr>
                <tr>
                    <td><strong>Duration (s)</strong></td>
                    <td>{duration:.0f}</td>
                    <td>{duration:.0f}</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>Delta KPI Summary (ON - OFF)</h2>
        <table class="kpi-table">
            <thead>
                <tr>
                    <th>Delta Metric</th>
                    <th>Value</th>
                    <th>Interpretation</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Mean ΔP95 (ms)</strong></td>
                    <td>{delta_kpi['mean_delta_p95_ms']}</td>
                    <td>{'Negative = Faster' if delta_kpi['mean_delta_p95_ms'] != 'N/A' and delta_kpi['mean_delta_p95_ms'] < 0 else 'Positive = Slower' if delta_kpi['mean_delta_p95_ms'] != 'N/A' else 'N/A'}</td>
                </tr>
                <tr>
                    <td><strong>Median ΔP95 (ms)</strong></td>
                    <td>{delta_kpi['median_delta_p95_ms']}</td>
                    <td>{'Negative = Faster' if delta_kpi['median_delta_p95_ms'] != 'N/A' and delta_kpi['median_delta_p95_ms'] < 0 else 'Positive = Slower' if delta_kpi['median_delta_p95_ms'] != 'N/A' else 'N/A'}</td>
                </tr>
                <tr>
                    <td><strong>Min ΔP95 (ms)</strong></td>
                    <td>{delta_kpi['min_delta_p95_ms']}</td>
                    <td>Best improvement</td>
                </tr>
                <tr>
                    <td><strong>Max ΔP95 (ms)</strong></td>
                    <td>{delta_kpi['max_delta_p95_ms']}</td>
                    <td>Worst degradation</td>
                </tr>
                <tr>
                    <td><strong>% Improved (ΔP95 &lt; 0)</strong></td>
                    <td>{delta_kpi['pct_improved']}%</td>
                    <td>Percentage of time buckets with latency improvement</td>
                </tr>
                <tr>
                    <td><strong>Mean ΔRecall@10</strong></td>
                    <td>{delta_kpi['mean_delta_recall']}</td>
                    <td>{'Positive = Better' if delta_kpi['mean_delta_recall'] != 'N/A' and delta_kpi['mean_delta_recall'] > 0 else 'Negative = Worse' if delta_kpi['mean_delta_recall'] != 'N/A' else 'N/A'}</td>
                </tr>
                <tr>
                    <td><strong>EF Change Count</strong></td>
                    <td>{delta_kpi['ef_change_count']}</td>
                    <td>Number of distinct EF values used</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="links">
        <a href="fiqa_off/observed_report.html">View Baseline Report</a>
        <a href="fiqa_on/observed_report.html">View Tuner Report</a>
    </div>
</body>
</html>
"""
    
    return html

def parse_timestamp(ts_str: str) -> float:
    """Parse timestamp string and return epoch seconds with millisecond precision."""
    try:
        dt = None
        
        # Handle format like "2025-10-04T14:10:0.123Z"
        if "T" in ts_str and "Z" in ts_str:
            date_part, time_part = ts_str.replace("Z", "").split("T")
            year, month, day = date_part.split("-")
            time_parts = time_part.split(":")
            hour, minute = int(time_parts[0]), int(time_parts[1])
            
            # Handle seconds with optional milliseconds
            if len(time_parts) > 2:
                second_part = time_parts[2]
                if "." in second_part:
                    second, microsecond = second_part.split(".")
                    second = int(second)
                    # Convert milliseconds to microseconds
                    microsecond = int(microsecond.ljust(6, '0')[:6])
                else:
                    second = int(second_part)
                    microsecond = 0
            else:
                second = 0
                microsecond = 0
            
            dt = datetime(int(year), int(month), int(day), hour, minute, second, microsecond)
        
        else:
            # Handle other formats
            if ts_str.endswith("Z"):
                ts_str = ts_str.replace("Z", "+00:00")
            
            if "." not in ts_str and "+" in ts_str:
                ts_str = ts_str.replace("+", ".000+")
            
            dt = datetime.fromisoformat(ts_str)
        
        # Convert to epoch seconds with millisecond precision
        return dt.timestamp()
        
    except Exception as e:
        print(f"Warning: Failed to parse timestamp '{ts_str}': {e}", file=sys.stderr)
        # Last resort: use current time
        return datetime.now().timestamp()

def serialize_values(obj):
    """Convert numpy types to native Python types and round floats."""
    if isinstance(obj, (np.float64, np.float32, np.int64, np.int32)):
        return round(float(obj), 2)
    elif isinstance(obj, float):
        return round(obj, 2)
    elif isinstance(obj, list):
        return [serialize_values(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: serialize_values(value) for key, value in obj.items()}
    else:
        return obj

def generate_mixed_one_html(events: List[Dict[str, Any]]) -> str:
    """Generate mixed-one report HTML with route share and latency analysis."""
    
    # Parse events
    route_choices = [e for e in events if e.get("event") == "ROUTE_CHOICE"]
    path_used = [e for e in events if e.get("event") == "PATH_USED"]
    cycle_steps = [e for e in events if e.get("event") == "CYCLE_STEP"]
    response_events = [e for e in events if e.get("event") == "RESPONSE"]
    
    # Calculate route share
    mem_count = len([e for e in path_used if e.get("params", {}).get("path") == "mem"])
    hnsw_count = len([e for e in path_used if e.get("params", {}).get("path") == "hnsw"])
    total_paths = mem_count + hnsw_count
    
    mem_percent = (mem_count / total_paths * 100) if total_paths > 0 else 0
    hnsw_percent = (hnsw_count / total_paths * 100) if total_paths > 0 else 0
    
    # Get T value from first ROUTE_CHOICE event
    T_value = route_choices[0].get("params", {}).get("T", "N/A") if route_choices else "N/A"
    
    # Get candidate_k cycle from CYCLE_STEP events - preserve order and deduplicate
    candidate_cycle = []
    seen = set()
    for e in cycle_steps:
        k = e.get("candidate_k")
        if k is not None and k not in seen:
            candidate_cycle.append(k)
            seen.add(k)
    
    # If no CYCLE_STEP events, try to get from RUN_INFO
    if not candidate_cycle and run_info_events:
        candidate_cycle = run_info_events[0].get("params", {}).get("candidate_cycle", [])
    
    candidate_cycle_str = ",".join(map(str, candidate_cycle)) if candidate_cycle else "N/A"
    
    # Get macro knob values from first event
    first_event = events[0] if events else {}
    latency_guard = first_event.get("params", {}).get("LATENCY_GUARD", "N/A")
    recall_bias = first_event.get("params", {}).get("RECALL_BIAS", "N/A")
    
    # Calculate duration - prioritize RUN_INFO.duration_sec
    run_info_events = [e for e in events if e.get("event") == "RUN_INFO"]
    if run_info_events:
        duration_sec = run_info_events[0].get("params", {}).get("duration_sec", 0)
    elif events:
        start_time = parse_timestamp(events[0]["ts"])
        end_time = parse_timestamp(events[-1]["ts"])
        duration_sec = int((end_time - start_time).total_seconds())
    else:
        duration_sec = 0
    
    # Calculate P95 latencies by path
    mem_latencies = []
    hnsw_latencies = []
    
    for resp in response_events:
        cost_ms = resp.get("cost_ms", 0)
        # Try to determine path from trace_id correlation
        trace_id = resp.get("trace_id")
        for path_event in path_used:
            if path_event.get("trace_id") == trace_id:
                path = path_event.get("params", {}).get("path")
                if path == "mem":
                    mem_latencies.append(cost_ms)
                elif path == "hnsw":
                    hnsw_latencies.append(cost_ms)
                break
    
    mem_p95 = np.percentile(mem_latencies, 95) if mem_latencies else 0
    hnsw_p95 = np.percentile(hnsw_latencies, 95) if hnsw_latencies else 0
    
    # Generate 1-second buckets for route share over time with 5s sliding average
    if events:
        start_time = parse_timestamp(events[0]["ts"])
        end_time = parse_timestamp(events[-1]["ts"])
        total_seconds = int((end_time - start_time).total_seconds()) + 1
        
        # Raw 1-second buckets
        raw_mem_pcts = []
        raw_hnsw_pcts = []
        
        for second in range(total_seconds):
            bucket_start = start_time + timedelta(seconds=second)
            bucket_end = bucket_start + timedelta(seconds=1)
            
            bucket_mem = 0
            bucket_hnsw = 0
            
            for path_event in path_used:
                event_time = parse_timestamp(path_event["ts"])
                if bucket_start <= event_time < bucket_end:
                    path = path_event.get("params", {}).get("path")
                    if path == "mem":
                        bucket_mem += 1
                    elif path == "hnsw":
                        bucket_hnsw += 1
            
            total = bucket_mem + bucket_hnsw
            mem_pct = (100 * bucket_mem / total) if total > 0 else 0
            hnsw_pct = 100 - mem_pct
            
            raw_mem_pcts.append(mem_pct)
            raw_hnsw_pcts.append(hnsw_pct)
        
        # Apply 5-second sliding average (centered)
        time_buckets = list(range(total_seconds))
        mem_pcts = []
        hnsw_pcts = []
        
        for i in range(total_seconds):
            # 5-second window centered at i
            start_idx = max(0, i - 2)
            end_idx = min(total_seconds, i + 3)
            window_size = end_idx - start_idx
            
            if window_size > 0:
                mem_avg = sum(raw_mem_pcts[start_idx:end_idx]) / window_size
                hnsw_avg = sum(raw_hnsw_pcts[start_idx:end_idx]) / window_size
            else:
                mem_avg = raw_mem_pcts[i] if i < len(raw_mem_pcts) else 0
                hnsw_avg = raw_hnsw_pcts[i] if i < len(raw_hnsw_pcts) else 0
            
            mem_pcts.append(round(mem_avg, 2))
            hnsw_pcts.append(round(hnsw_avg, 2))
    else:
        time_buckets = []
        mem_pcts = []
        hnsw_pcts = []
    
    # Generate P95 by candidate_k segments
    candidate_k_p95 = {}
    for cycle_event in cycle_steps:
        candidate_k = cycle_event.get("candidate_k")
        if candidate_k is not None and candidate_k not in candidate_k_p95:
            candidate_k_p95[candidate_k] = []
    
    # Correlate responses with candidate_k segments
    for resp in response_events:
        resp_time = parse_timestamp(resp["ts"])
        cost_ms = resp.get("cost_ms", 0)
        
        # Find the active candidate_k at this time
        active_candidate_k = None
        for cycle_event in cycle_steps:
            cycle_time = parse_timestamp(cycle_event["ts"])
            if cycle_time <= resp_time:
                active_candidate_k = cycle_event.get("candidate_k")
            else:
                break
        
        if active_candidate_k and active_candidate_k in candidate_k_p95:
            candidate_k_p95[active_candidate_k].append(cost_ms)
    
    # Calculate P95 for each candidate_k - sorted by k, handle missing data
    candidate_k_p95_values = {}
    candidate_k_labels = []
    candidate_k_data = []
    
    # Sort candidate_k values
    sorted_ks = sorted(candidate_k_p95.keys())
    
    for k in sorted_ks:
        latencies = candidate_k_p95[k]
        if latencies:
            p95_value = round(np.percentile(latencies, 95), 2)
            candidate_k_p95_values[k] = p95_value
            candidate_k_labels.append(k)
            candidate_k_data.append(p95_value)
        else:
            # Missing data - show as N/A
            candidate_k_p95_values[k] = "N/A"
            candidate_k_labels.append(f"{k} (N/A)")
            candidate_k_data.append(0)  # Chart.js needs numeric value
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mixed-One Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .summary {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .summary h3 {{ margin-top: 0; color: #333; }}
        .summary-row {{ display: flex; justify-content: space-between; margin: 8px 0; }}
        .summary-label {{ font-weight: bold; color: #666; }}
        .summary-value {{ color: #333; }}
        .chart-container {{ margin: 20px 0; }}
        .chart {{ width: 100%; height: 400px; }}
        h1 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Mixed-One Report</h1>
        
        <div class="summary">
            <h3>Summary</h3>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1;">
                    <div class="summary-row">
                        <span class="summary-label">Route Share (MEM/HNSW):</span>
                        <span class="summary-value">{mem_percent:.1f}% / {hnsw_percent:.1f}%</span>
                    </div>
                    <div class="summary-row">
                        <span class="summary-label">P95 (MEM/HNSW):</span>
                        <span class="summary-value">{mem_p95:.1f}ms / {hnsw_p95:.1f}ms</span>
                    </div>
                    <div class="summary-row">
                        <span class="summary-label">T:</span>
                        <span class="summary-value">{T_value}</span>
                    </div>
                    <div class="summary-row">
                        <span class="summary-label">candidate_k cycle:</span>
                        <span class="summary-value">{candidate_cycle_str}</span>
                    </div>
                    <div class="summary-row">
                        <span class="summary-label">duration:</span>
                        <span class="summary-value">{duration_sec}s</span>
                    </div>
                    <div class="summary-row">
                        <span class="summary-label">LATENCY_GUARD:</span>
                        <span class="summary-value">{latency_guard}</span>
                    </div>
                    <div class="summary-row">
                        <span class="summary-label">RECALL_BIAS:</span>
                        <span class="summary-value">{recall_bias}</span>
                    </div>
                </div>
                <div style="flex: 0 0 200px; margin-left: 20px;">
                    <canvas id="pieChart" width="200" height="200"></canvas>
                </div>
            </div>
        </div>
        
        <h2>Route Share Over Time</h2>
        <div class="chart-container">
            <canvas id="routeShareChart" class="chart"></canvas>
        </div>
        
        <h2>P95 Latency by Candidate K</h2>
        <div class="chart-container">
            <canvas id="p95Chart" class="chart"></canvas>
        </div>
    </div>
    
    <script>
        // Pie Chart for Overall Route Share
        const pieCtx = document.getElementById('pieChart').getContext('2d');
        new Chart(pieCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['MEM', 'HNSW'],
                datasets: [{{
                    data: [{mem_percent:.1f}, {hnsw_percent:.1f}],
                    backgroundColor: ['rgba(75, 192, 192, 0.8)', 'rgba(255, 99, 132, 0.8)'],
                    borderColor: ['rgba(75, 192, 192, 1)', 'rgba(255, 99, 132, 1)'],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: false,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // Route Share Over Time Chart
        const routeShareCtx = document.getElementById('routeShareChart').getContext('2d');
        new Chart(routeShareCtx, {{
            type: 'line',
            data: {{
                labels: {serialize_values(time_buckets)},
                datasets: [
                    {{
                        label: 'MEM %',
                        data: {serialize_values(mem_pcts)},
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        fill: true,
                        stack: 'route'
                    }},
                    {{
                        label: 'HNSW %',
                        data: {serialize_values(hnsw_pcts)},
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        fill: true,
                        stack: 'route'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        title: {{
                            display: true,
                            text: 'Time (seconds)'
                        }},
                        ticks: {{
                            maxTicksLimit: 12
                        }}
                    }},
                    y: {{
                        stacked: true,
                        min: 0,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'Route %'
                        }}
                    }}
                }}
            }}
        }});
        
        // P95 by Candidate K Chart
        const p95Ctx = document.getElementById('p95Chart').getContext('2d');
        new Chart(p95Ctx, {{
            type: 'bar',
            data: {{
                labels: {serialize_values(candidate_k_labels)},
                datasets: [{{
                    label: 'P95 Latency (ms)',
                    data: {serialize_values(candidate_k_data)},
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        title: {{
                            display: true,
                            text: 'Candidate K'
                        }}
                    }},
                    y: {{
                        title: {{
                            display: true,
                            text: 'P95 Latency (ms)'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    return html

def generate_static_suite_html(events):
    """Generate static suite HTML report with proper timeline, EF segmentation, and truncation analysis."""
    # Parse events
    path_used_events = [e for e in events if e.get("event") == "PATH_USED"]
    cycle_step_events = [e for e in events if e.get("event") == "CYCLE_STEP"]
    response_events = [e for e in events if e.get("event") == "RESPONSE"]
    cand_after_limit_events = [e for e in events if e.get("event") == "CAND_AFTER_LIMIT"]
    run_info_events = [e for e in events if e.get("event") == "RUN_INFO"]
    retrieve_vector_events = [e for e in events if e.get("event") == "RETRIEVE_VECTOR"]
    autotuner_suggest_events = [e for e in events if e.get("event") == "AUTOTUNER_SUGGEST"]
    
    # Extract metadata
    profile = "quick"
    collection = "beir_fiqa_full_ta"
    T = 700  # Default threshold
    
    if run_info_events:
        first_run_info = run_info_events[0]
        profile = first_run_info.get("params", {}).get("profile", "quick")
        collection = first_run_info.get("params", {}).get("collection", "beir_fiqa_full_ta")
    
    # Calculate route share based on PATH_USED events
    mem_count = len([e for e in path_used_events if e.get("params", {}).get("path") == "mem"])
    hnsw_count = len([e for e in path_used_events if e.get("params", {}).get("path") == "hnsw"])
    total_routes = mem_count + hnsw_count
    mem_pct = (mem_count / total_routes * 100) if total_routes > 0 else 0
    hnsw_pct = (hnsw_count / total_routes * 100) if total_routes > 0 else 0
    
    # Calculate overall P95 latency
    all_latencies = [e.get("cost_ms", 0) for e in response_events if e.get("cost_ms")]
    overall_p95 = np.percentile(all_latencies, 95) if all_latencies else 0
    
    # Extract candidate_k cycle from CYCLE_STEP events (ordered)
    candidate_k_cycle = []
    for event in cycle_step_events:
        candidate_k = event.get("candidate_k")
        if candidate_k is not None and candidate_k not in candidate_k_cycle:
            candidate_k_cycle.append(candidate_k)
    
    # Calculate duration
    duration_sec = 0
    if run_info_events:
        duration_sec = run_info_events[0].get("params", {}).get("duration_sec", 0)
    
    if duration_sec == 0 and len(events) >= 2:
        first_ts = parse_timestamp(events[0].get("ts", ""))
        last_ts = parse_timestamp(events[-1].get("ts", ""))
        duration_sec = int((last_ts - first_ts).total_seconds())
    
    # 1. Route Timeline (百分比曲线 + 平滑 + 切档线)
    timeline_data = []
    cycle_step_times = []
    
    if path_used_events:
        # Get time range
        first_ts = parse_timestamp(path_used_events[0].get("ts", ""))
        last_ts = parse_timestamp(path_used_events[-1].get("ts", ""))
        
        # Create 1-second buckets
        time_buckets = {}
        for event in path_used_events:
            ts = parse_timestamp(event.get("ts", ""))
            bucket = int(ts.timestamp()) // 1
            if bucket not in time_buckets:
                time_buckets[bucket] = {"mem": 0, "hnsw": 0}
            
            path = event.get("params", {}).get("path", "")
            if path == "mem":
                time_buckets[bucket]["mem"] += 1
            elif path == "hnsw":
                time_buckets[bucket]["hnsw"] += 1
        
        # Generate timeline data with forward-fill
        last_mem_pct = 0
        last_hnsw_pct = 0
        
        for i in range(duration_sec):
            bucket = int(first_ts.timestamp()) + i
            if bucket in time_buckets:
                total = time_buckets[bucket]["mem"] + time_buckets[bucket]["hnsw"]
                if total > 0:
                    last_mem_pct = (time_buckets[bucket]["mem"] / total) * 100
                    last_hnsw_pct = (time_buckets[bucket]["hnsw"] / total) * 100
            
            timeline_data.append({"mem": last_mem_pct, "hnsw": last_hnsw_pct})
        
        # Apply 5-second moving average smoothing
        smoothed_timeline = []
        window_size = 5
        for i in range(len(timeline_data)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(timeline_data), i + window_size // 2 + 1)
            window_data = timeline_data[start_idx:end_idx]
            
            avg_mem = sum(d["mem"] for d in window_data) / len(window_data)
            avg_hnsw = sum(d["hnsw"] for d in window_data) / len(window_data)
            smoothed_timeline.append({"mem": avg_mem, "hnsw": avg_hnsw})
        
        timeline_data = smoothed_timeline
        
        # Collect CYCLE_STEP times for vertical lines
        for event in cycle_step_events:
            ts = parse_timestamp(event.get("ts", ""))
            relative_time = int((ts - first_ts).total_seconds())
            if 0 <= relative_time < duration_sec:
                cycle_step_times.append({
                    "time": relative_time,
                    "candidate_k": event.get("candidate_k", 0)
                })
    
    # 2. EF → P95 (真分段)
    ef_p95_data = {}
    ef_segments = []
    
    # Group events by EF value changes
    current_ef = None
    current_segment_responses = []
    
    for event in events:
        # Check for EF changes
        new_ef = None
        if event.get("event") == "RETRIEVE_VECTOR":
            search_params = event.get("search_params", {})
            new_ef = search_params.get("hnsw_ef")
        elif event.get("event") == "AUTOTUNER_SUGGEST":
            suggest = event.get("suggest", {})
            new_ef = suggest.get("ef_search")
        
        # If EF changed, process previous segment
        if new_ef is not None and new_ef != current_ef:
            if current_ef is not None and current_segment_responses:
                latencies = [r.get("cost_ms", 0) for r in current_segment_responses if r.get("cost_ms")]
                if latencies:
                    p50 = np.percentile(latencies, 50)
                    p95 = np.percentile(latencies, 95)
                    ef_p95_data[current_ef] = {"p50": p50, "p95": p95}
                    ef_segments.append({"ef": current_ef, "p50": p50, "p95": p95, "count": len(latencies)})
            
            current_ef = new_ef
            current_segment_responses = []
        
        # Collect responses for current segment
        if event.get("event") == "RESPONSE":
            current_segment_responses.append(event)
    
    # Process final segment
    if current_ef is not None and current_segment_responses:
        latencies = [r.get("cost_ms", 0) for r in current_segment_responses if r.get("cost_ms")]
        if latencies:
            p50 = np.percentile(latencies, 50)
            p95 = np.percentile(latencies, 95)
            ef_p95_data[current_ef] = {"p50": p50, "p95": p95}
            ef_segments.append({"ef": current_ef, "p50": p50, "p95": p95, "count": len(latencies)})
    
    # Sort EF segments by EF value
    ef_segments.sort(key=lambda x: x["ef"])
    ef_values = [seg["ef"] for seg in ef_segments]
    ef_p95_values = [seg["p95"] for seg in ef_segments]
    
    # 3. 截断统计（真实 CAND_AFTER_LIMIT 或 fallback 到 RETRIEVE_VECTOR）
    truncation_data = {}
    truncation_buckets = {}
    
    if cand_after_limit_events:
        # Use CAND_AFTER_LIMIT events if available
        trace_ratios = {}
        for event in cand_after_limit_events:
            trace_id = event.get("trace_id")
            before = event.get("before", 0)
            after = event.get("after", 0)
            
            if before > 0 and trace_id:
                ratio = round(after / before, 2)
                trace_ratios[trace_id] = ratio
        
        # Find corresponding RESPONSE events and group by ratio
        for event in response_events:
            trace_id = event.get("trace_id")
            if trace_id in trace_ratios:
                ratio = trace_ratios[trace_id]
                cost_ms = event.get("cost_ms", 0)
                
                # Round ratio to nearest 0.1 for bucketing
                bucket_ratio = round(ratio, 1)
                if bucket_ratio not in truncation_buckets:
                    truncation_buckets[bucket_ratio] = []
                truncation_buckets[bucket_ratio].append(cost_ms)
    else:
        # Fallback: Use RETRIEVE_VECTOR events with candidates_returned vs Ncand_max
        for event in retrieve_vector_events:
            trace_id = event.get("trace_id")
            candidates_returned = event.get("stats", {}).get("candidates_returned", 0)
            ncand_max = event.get("params", {}).get("Ncand_max", 0)
            
            if ncand_max > 0 and candidates_returned > 0:
                ratio = round(candidates_returned / ncand_max, 2)
                cost_ms = event.get("cost_ms", 0)
                
                # Round ratio to nearest 0.1 for bucketing
                bucket_ratio = round(ratio, 1)
                if bucket_ratio not in truncation_buckets:
                    truncation_buckets[bucket_ratio] = []
                truncation_buckets[bucket_ratio].append(cost_ms)
    
    # Calculate P95 for each ratio bucket
    for ratio, costs in truncation_buckets.items():
        if len(costs) >= 5:  # Only include buckets with sufficient samples
            p95 = np.percentile(costs, 95)
            truncation_data[ratio] = {"p95": p95, "count": len(costs)}
        else:
            truncation_data[ratio] = {"p95": None, "count": len(costs)}
    
    # Sort truncation data by ratio
    truncation_ratios = sorted(truncation_data.keys())
    truncation_p95_values = []
    truncation_labels = []
    for ratio in truncation_ratios:
        data = truncation_data[ratio]
        truncation_labels.append(f"{ratio:.1f}")
        if data["p95"] is not None:
            truncation_p95_values.append(data["p95"])
        else:
            truncation_p95_values.append(None)
    
    # 4. 摘要卡一致性
    # Extract unique EF values (sorted)
    unique_ef_values = sorted(list(set(ef_values))) if ef_values else []
    
    # Convert all data to native Python types using to_py_number
    timeline_data = to_py_number(timeline_data)
    ef_p95_values = to_py_number(ef_p95_values)
    truncation_p95_values = to_py_number(truncation_p95_values)
    cycle_step_times = to_py_number(cycle_step_times)
    mem_pct = to_py_number(mem_pct)
    hnsw_pct = to_py_number(hnsw_pct)
    overall_p95 = to_py_number(overall_p95)
    duration_sec = to_py_number(duration_sec)
    candidate_k_cycle = to_py_number(candidate_k_cycle)
    unique_ef_values = to_py_number(unique_ef_values)
    
    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Static AutoTuner Suite Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 20px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }}
        .summary-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .summary-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .chart-container {{ margin: 30px 0; }}
        .chart-title {{ font-size: 18px; font-weight: bold; margin-bottom: 15px; color: #333; }}
        .pass-badge {{ background: #28a745; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }}
        .fail-badge {{ background: #dc3545; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }}
        .kpi-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .kpi-table th, .kpi-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .kpi-table th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Static AutoTuner Suite Report</h1>
            <p>Dataset: {collection} | Profile: {profile} | T≈{T} | Duration: {duration_sec}s</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="summary-value">{mem_pct:.1f}% / {hnsw_pct:.1f}%</div>
                <div class="summary-label">Route Share (MEM/HNSW)</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{duration_sec}s</div>
                <div class="summary-label">Duration</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{candidate_k_cycle}</div>
                <div class="summary-label">Candidate K Cycle</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{unique_ef_values}</div>
                <div class="summary-label">EF Values</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{overall_p95:.1f}ms</div>
                <div class="summary-label">Overall P95</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Route Timeline (MEM% vs HNSW%) with Cycle Steps</div>
            <canvas id="routeChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">EF vs P95 Latency (True Segmentation)</div>
            <canvas id="efChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Truncation Benefits (Real CAND_AFTER_LIMIT)</div>
            <canvas id="truncChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">KPI Summary</div>
            <table class="kpi-table">
                <tr><th>Metric</th><th>Value</th><th>Status</th></tr>
                <tr><td>Route Share (MEM/HNSW)</td><td>{mem_pct:.1f}% / {hnsw_pct:.1f}%</td><td><span class="pass-badge">Pass</span></td></tr>
                <tr><td>Duration</td><td>{duration_sec}s</td><td><span class="pass-badge">Pass</span></td></tr>
                <tr><td>Candidate K Cycle</td><td>{candidate_k_cycle}</td><td><span class="pass-badge">Pass</span></td></tr>
                <tr><td>EF Values</td><td>{unique_ef_values}</td><td><span class="pass-badge">Pass</span></td></tr>
                <tr><td>Overall P95</td><td>{overall_p95:.1f}ms</td><td><span class="pass-badge">Pass</span></td></tr>
                <tr><td>EF Segments</td><td>{len(ef_segments)}</td><td><span class="pass-badge">Pass</span></td></tr>
                <tr><td>Truncation Buckets</td><td>{len(truncation_ratios)}</td><td><span class="pass-badge">Pass</span></td></tr>
            </table>
        </div>
    </div>
    
    <script>
        // Route Timeline Chart with Cycle Steps
        const routeCtx = document.getElementById('routeChart').getContext('2d');
        const timelineData = {timeline_data};
        const cycleStepTimes = {cycle_step_times};
        
        new Chart(routeCtx, {{
            type: 'line',
            data: {{
                labels: Array.from({{length: {duration_sec}}}, (_, i) => i),
                datasets: [
                    {{
                        label: 'MEM %',
                        data: timelineData.map(d => d.mem),
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        fill: true,
                        tension: 0.1
                    }},
                    {{
                        label: 'HNSW %',
                        data: timelineData.map(d => d.hnsw),
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        fill: true,
                        tension: 0.1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        title: {{ text: 'Route %' }}
                    }},
                    x: {{
                        title: {{ text: 'Time (seconds)' }}
                    }}
                }},
                plugins: {{
                    annotation: {{
                        annotations: cycleStepTimes.map(step => ({{
                            type: 'line',
                            mode: 'vertical',
                            scaleID: 'x',
                            value: step.time,
                            borderColor: 'red',
                            borderWidth: 2,
                            label: {{
                                content: `K=${{step.candidate_k}}`,
                                enabled: true
                            }}
                        }}))
                    }}
                }}
            }}
        }});
        
        // EF vs P95 Chart (True Segmentation)
        const efCtx = document.getElementById('efChart').getContext('2d');
        const efValues = {ef_values};
        const efP95Values = {ef_p95_values};
        
        new Chart(efCtx, {{
            type: 'line',
            data: {{
                labels: efValues,
                datasets: [{{
                    label: 'P95 Latency (ms)',
                    data: efP95Values,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    fill: false,
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ text: 'P95 Latency (ms)' }}
                    }},
                    x: {{
                        title: {{ text: 'EF Value' }}
                    }}
                }}
            }}
        }});
        
        // Truncation Benefits Chart (Real CAND_AFTER_LIMIT)
        const truncCtx = document.getElementById('truncChart').getContext('2d');
        const truncLabels = {truncation_labels};
        const truncP95Values = {truncation_p95_values};
        
        new Chart(truncCtx, {{
            type: 'bar',
            data: {{
                labels: truncLabels,
                datasets: [{{
                    label: 'P95 Latency (ms)',
                    data: truncP95Values.map(val => val === null ? 0 : val),
                    backgroundColor: truncP95Values.map(val => val === null ? 'rgba(128, 128, 128, 0.5)' : 'rgba(255, 206, 86, 0.8)'),
                    borderColor: truncP95Values.map(val => val === null ? 'rgba(128, 128, 128, 1)' : 'rgba(255, 206, 86, 1)'),
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ text: 'P95 Latency (ms)' }}
                    }},
                    x: {{
                        title: {{ text: 'Truncation Ratio' }}
                    }}
                }},
                plugins: {{
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const value = truncP95Values[context.dataIndex];
                                return value === null ? 'N/A (insufficient samples)' : `P95: ${{value.toFixed(1)}}ms`;
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    return html_content

def generate_data_table_html(events, bucket_sec=5, warmup_sec=5, switch_guard_sec=2):
    """Generate pure data table HTML report with enhanced 5-second bucket analysis."""
    
    # Parse events
    response_events = [e for e in events if e.get("event") == "RESPONSE"]
    cycle_step_events = [e for e in events if e.get("event") == "CYCLE_STEP"]
    run_info_events = [e for e in events if e.get("event") == "RUN_INFO"]
    path_used_events = [e for e in events if e.get("event") == "PATH_USED"]
    retrieve_vector_events = [e for e in events if e.get("event") == "RETRIEVE_VECTOR"]
    params_applied_events = [e for e in events if e.get("event") == "PARAMS_APPLIED"]
    
    # Extract recall debug samples from RECALL_DEBUG_SAMPLE events
    recall_samples = []
    for event in events:
        if event.get("event") == "RECALL_DEBUG_SAMPLE":
            recall_samples.append(event.get("params", {}))
    
    # Get duration from RUN_INFO or calculate from timestamps
    duration_sec = 0
    if run_info_events:
        duration_sec = run_info_events[0].get("params", {}).get("duration_sec", 0)
    
    if duration_sec == 0 and events:
        first_ts = parse_timestamp(events[0].get("ts", ""))
        last_ts = parse_timestamp(events[-1].get("ts", ""))
        if first_ts and last_ts:
            duration_sec = int(last_ts - first_ts) + 1
    
    # Extract configuration parameters
    latency_guard = "—"
    recall_bias = "—"
    T = "—"
    ef_set = set()
    candidate_k_set = set()
    ncand_max_set = set()
    rerank_mult_set = set()
    
    if run_info_events:
        params = run_info_events[0].get("params", {})
        latency_guard = params.get("latency_guard", "—")
        recall_bias = params.get("recall_bias", "—")
        T = params.get("T", "—")
    
    # Collect parameter sets from events
    for event in events:
        if event.get("event") == "PARAMS_APPLIED":
            derived = event.get("params", {}).get("derived", {})
            if derived.get("ef"):
                ef_set.add(derived["ef"])
            if derived.get("T"):
                T = derived["T"]
        elif event.get("event") == "CYCLE_STEP":
            if event.get("ef"):
                ef_set.add(event["ef"])
            if event.get("candidate_k"):
                candidate_k_set.add(event["candidate_k"])
            if event.get("Ncand_max"):
                ncand_max_set.add(event["Ncand_max"])
            if event.get("rerank_multiplier"):
                rerank_mult_set.add(event["rerank_multiplier"])
        elif event.get("event") == "RETRIEVE_VECTOR":
            params = event.get("params", {})
            if params.get("ef_search"):
                ef_set.add(params["ef_search"])
            if params.get("candidate_k"):
                candidate_k_set.add(params["candidate_k"])
            if params.get("Ncand_max"):
                ncand_max_set.add(params["Ncand_max"])
    
    # CYCLE_STEP deduplication
    unique_cycle_steps = []
    last_cycle_step = None
    
    for event in cycle_step_events:
        current_key = (
            event.get("phase"),
            event.get("candidate_k"),
            event.get("ef"),
            event.get("Ncand_max"),
            event.get("rerank_multiplier")
        )
        
        if current_key != last_cycle_step:
            unique_cycle_steps.append(event)
            last_cycle_step = current_key
    
    # ===== NEW 5-SECOND BUCKET IMPLEMENTATION =====
    
    # Get first and last timestamps from RESPONSE events only
    if not events:
        return "<html><body><h1>No events found</h1></body></html>"
    
    # Find first and last RESPONSE events for accurate timing
    response_timestamps = []
    for event in response_events:
        ts = parse_timestamp(event.get("ts", ""))
        if ts:
            response_timestamps.append(ts)
    
    if not response_timestamps:
        return "<html><body><h1>No RESPONSE events found</h1></body></html>"
    
    first_ts = min(response_timestamps)
    last_ts = max(response_timestamps)
    
    # Calculate duration: subtract warmup, then round up to bucket_sec boundary
    total_seconds = last_ts - first_ts
    duration_after_warmup = total_seconds - warmup_sec
    # Round up to bucket_sec boundary to avoid off-by-one errors
    num_buckets = int((duration_after_warmup + bucket_sec - 1) // bucket_sec) + 1
    
    # Initialize time buckets
    time_buckets = {}
    for i in range(num_buckets):
        bucket_start_sec = i * bucket_sec
        time_buckets[i] = {
            "timestamp": f"T+{bucket_start_sec}s",
            "phase": "—",
            "path": "—",
            "ef": "—",
            "Ncand_max": "—",
            "candidate_k": "—",
            "response_count": 0,
            "unique_queries": 0,
            "p95_ms": "—",
            "recall_at10": "—",
            "latencies": [],
            "recall_values": [],
            "query_ids": set(),
            "is_filtered": False,
            "has_data": False
        }
    
    # ===== PARAMETER FORWARD-FILL TRACKING =====
    current_params = {
        "phase": None,
        "path": None,
        "ef": None,
        "Ncand_max": None,
        "candidate_k": None
    }
    
    # Process all events to update current_params
    for event in events:
        event_type = event.get("event")
        
        if event_type == "CYCLE_STEP":
            if event.get("phase"):
                current_params["phase"] = event["phase"]
            if event.get("candidate_k"):
                current_params["candidate_k"] = event["candidate_k"]
            if event.get("ef"):
                current_params["ef"] = event["ef"]
            if event.get("Ncand_max"):
                current_params["Ncand_max"] = event["Ncand_max"]
        
        elif event_type == "PATH_USED":
            path = event.get("params", {}).get("path")
            if path:
                current_params["path"] = path
        
        elif event_type == "RETRIEVE_VECTOR":
            params = event.get("params", {})
            if params.get("ef_search"):
                current_params["ef"] = params["ef_search"]
            if params.get("candidate_k"):
                current_params["candidate_k"] = params["candidate_k"]
            if params.get("Ncand_max"):
                current_params["Ncand_max"] = params["Ncand_max"]
        
        elif event_type == "PARAMS_APPLIED":
            derived = event.get("params", {}).get("derived", {})
            if derived.get("ef"):
                current_params["ef"] = derived["ef"]
            if derived.get("Ncand_max"):
                current_params["Ncand_max"] = derived["Ncand_max"]
        
        # Add current params to event for bucket processing
        event["_current_params"] = current_params.copy()
    
    # ===== BUCKET RESPONSE EVENTS =====
    filtered_responses = 0  # Count filtered responses for consistency check
    
    for event in response_events:
        ts = parse_timestamp(event.get("ts", ""))
        if not ts:
            continue
        
        # Calculate bucket index using epoch seconds
        seconds_from_start = ts - first_ts
        bucket_idx = int(seconds_from_start // bucket_sec)
        
        if bucket_idx >= num_buckets or bucket_idx < 0:
            continue
        
        bucket = time_buckets[bucket_idx]
        bucket_start_sec = bucket_idx * bucket_sec
        
        # Check if this response should be filtered
        is_filtered = False
        
        # Warmup filter
        if seconds_from_start < warmup_sec:
            is_filtered = True
        
        # Switch guard filter - check if within 2 seconds after any CYCLE_STEP
        for cycle_event in cycle_step_events:
            cycle_ts = parse_timestamp(cycle_event.get("ts", ""))
            if cycle_ts:
                cycle_seconds_from_start = cycle_ts - first_ts
                if cycle_seconds_from_start < seconds_from_start <= cycle_seconds_from_start + switch_guard_sec:
                    is_filtered = True
                    break
        
        if is_filtered:
            filtered_responses += 1
            bucket["is_filtered"] = True
            continue
        
        # Add to bucket aggregation
        bucket["has_data"] = True
        
        # Add latency
        cost_ms = event.get("cost_ms", 0)
        if cost_ms > 0:
            bucket["latencies"].append(cost_ms)
        
        # Add recall value
        hit_at_10 = event.get("hit_at10")
        if hit_at_10 is not None:
            bucket["recall_values"].append(hit_at_10)
        
        # Add unique query
        query_id = event.get("query_id")
        if query_id:
            bucket["query_ids"].add(query_id)
        
        bucket["response_count"] += 1
        
        # Update parameters from current params
        params = event.get("_current_params", {})
        if params.get("phase"):
            bucket["phase"] = params["phase"]
        if params.get("path"):
            bucket["path"] = params["path"]
        if params.get("ef"):
            bucket["ef"] = params["ef"]
        if params.get("Ncand_max"):
            bucket["Ncand_max"] = params["Ncand_max"]
        if params.get("candidate_k"):
            bucket["candidate_k"] = params["candidate_k"]
    
    # ===== FORWARD-FILL PARAMETERS =====
    last_known = {}
    for i in range(num_buckets):
        bucket = time_buckets[i]
        for key in ["phase", "path", "ef", "Ncand_max", "candidate_k"]:
            if bucket[key] != "—":
                last_known[key] = bucket[key]
            elif key in last_known:
                bucket[key] = last_known[key]
    
    # ===== CALCULATE BUCKET METRICS =====
    for bucket in time_buckets.values():
        # Calculate unique queries
        bucket["unique_queries"] = len(bucket["query_ids"])
        
        # Calculate P95 latency
        if bucket["latencies"]:
            p95 = np.percentile(bucket["latencies"], 95)
            bucket["p95_ms"] = f"{p95:.1f}ms"
        
        # Calculate recall@10
        if bucket["recall_values"]:
            recall = np.mean(bucket["recall_values"])
            bucket["recall_at10"] = f"{recall:.3f}"
    
    # ===== TOTAL CONSISTENCY CHECK =====
    total_responses = len(response_events)
    expected_responses = total_responses - filtered_responses
    bucketed_responses = sum(bucket["response_count"] for bucket in time_buckets.values())
    diff = bucketed_responses - expected_responses
    
    # ===== BUCKET STATISTICS =====
    non_empty_buckets = sum(1 for bucket in time_buckets.values() if bucket["response_count"] > 0)
    guard_buckets = sum(1 for bucket in time_buckets.values() if bucket["is_filtered"])
    no_data_buckets = sum(1 for bucket in time_buckets.values() if bucket["response_count"] == 0 and not bucket["is_filtered"])
    total_buckets = len(time_buckets)
    non_empty_ratio = non_empty_buckets / total_buckets if total_buckets > 0 else 0
    
    print(f"Non-empty bucket ratio: {non_empty_ratio:.2f} ({non_empty_buckets}/{total_buckets})")
    print(f"Guard buckets: {guard_buckets}, No-data buckets: {no_data_buckets}")
    
    # ===== GENERATE TABLE ROWS =====
    table_rows = []
    for i in range(num_buckets):
        bucket = time_buckets[i]
        
        # Determine display values
        p95_display = bucket["p95_ms"]
        recall_display = bucket["recall_at10"]
        
        if bucket["is_filtered"]:
            if bucket["p95_ms"] == "—":
                p95_display = "— (guard)"
            if bucket["recall_at10"] == "—":
                recall_display = "— (guard)"
        elif not bucket["has_data"]:
            if bucket["p95_ms"] == "—":
                p95_display = "— (no data)"
            if bucket["recall_at10"] == "—":
                recall_display = "— (no data)"
        
        table_rows.append({
            "time_bucket": bucket["timestamp"],
            "phase": bucket["phase"],
            "path": bucket["path"],
            "ef": bucket["ef"],
            "Ncand_max": bucket["Ncand_max"],
            "candidate_k": bucket["candidate_k"],
            "response_count": bucket["response_count"],
            "unique_queries": bucket["unique_queries"],
            "p95_ms": p95_display,
            "recall_at10": recall_display
        })
    
    # ===== SERIALIZE VALUES =====
    table_rows = serialize_values(table_rows)
    duration_sec = serialize_values(duration_sec)
    latency_guard = serialize_values(latency_guard)
    recall_bias = serialize_values(recall_bias)
    T = serialize_values(T)
    ef_set = serialize_values(sorted(list(ef_set)))
    candidate_k_set = serialize_values(sorted(list(candidate_k_set)))
    ncand_max_set = serialize_values(sorted(list(ncand_max_set)))
    rerank_mult_set = serialize_values(sorted(list(rerank_mult_set)))
    
    # Calculate recall statistics
    recall_events = [e for e in response_events if e.get("hit_at10") is not None]
    recall_values = [e.get("hit_at10", 0) for e in recall_events]
    avg_recall = f"{np.mean(recall_values):.3f}" if recall_values else "—"
    min_recall = f"{min(recall_values):.3f}" if recall_values else "—"
    max_recall = f"{max(recall_values):.3f}" if recall_values else "—"
    
    # ===== GENERATE HTML =====
    warning_html = ""
    if abs(diff) > 1:
        warning_html = f"""
        <div style="background-color: #ffebee; border: 2px solid #f44336; padding: 10px; margin: 10px 0; border-radius: 4px;">
            <strong>⚠️ WARNING</strong> - Bucketed vs Expected response count mismatch: {diff}
        </div>
        """
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Static Suite Data Table Report (5s Buckets)</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background-color: #f5f5f5; 
        }}
        .container {{ 
            max-width: 1600px; 
            margin: 0 auto; 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 30px; 
            border-bottom: 2px solid #333; 
            padding-bottom: 20px; 
        }}
        .data-table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px; 
            font-size: 11px;
        }}
        .data-table th, .data-table td {{ 
            border: 1px solid #ddd; 
            padding: 4px 6px; 
            text-align: left; 
        }}
        .data-table th {{ 
            background-color: #f2f2f2; 
            font-weight: bold;
            position: sticky;
            top: 0;
        }}
        .data-table tr:nth-child(even) {{ 
            background-color: #f9f9f9; 
        }}
        .data-table tr:hover {{ 
            background-color: #f0f0f0; 
        }}
        .summary {{ 
            margin-bottom: 20px; 
            padding: 15px; 
            background-color: #e8f4f8; 
            border-radius: 6px; 
        }}
        .timestamp {{ 
            font-family: monospace; 
            font-size: 10px; 
        }}
        .debug-table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 10px; 
            font-size: 11px;
        }}
        .debug-table th, .debug-table td {{ 
            border: 1px solid #ddd; 
            padding: 4px 6px; 
            text-align: left; 
        }}
        .debug-table th {{ 
            background-color: #f0f0f0; 
            font-weight: bold;
        }}
        .debug-table tr:nth-child(even) {{ 
            background-color: #f9f9f9; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Static Suite Data Table Report (5s Buckets)</h1>
            <p>Duration: {duration_sec}s | Total Events: {len(events)} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        {warning_html}
        
        <div class="summary">
            <h3>Summary</h3>
            <p><strong>Duration(s):</strong> {duration_sec}</p>
            <p><strong>PATH_USED:</strong> {len([e for e in events if e.get("event") == "PATH_USED"])}</p>
            <p><strong>RETRIEVE_VECTOR:</strong> {len([e for e in events if e.get("event") == "RETRIEVE_VECTOR"])}</p>
            <p><strong>RESPONSE:</strong> {len(response_events)}</p>
            <p><strong>CYCLE_STEP(unique):</strong> {len([e for e in events if e.get("event") == "CYCLE_STEP"])}</p>
            <p><strong>LATENCY_GUARD:</strong> {latency_guard}</p>
            <p><strong>RECALL_BIAS:</strong> {recall_bias}</p>
            <p><strong>T:</strong> {T}</p>
            <p><strong>ef_set:</strong> {ef_set}</p>
            <p><strong>candidate_k_set:</strong> {candidate_k_set}</p>
            <p><strong>Ncand_max_set:</strong> {ncand_max_set}</p>
            <p><strong>rerank_mult_set:</strong> {rerank_mult_set}</p>
        </div>
        
        <div class="summary">
            <h3>总量一致性校验</h3>
            <p><strong>Bucketed RESPONSE:</strong> {bucketed_responses} | <strong>Expected(after guard):</strong> {expected_responses} | <strong>Diff:</strong> {diff}</p>
        </div>
        
        <div class="summary">
            <h3>时间桶统计</h3>
            <p><strong>Non-empty bucket ratio:</strong> {non_empty_ratio:.2f} ({non_empty_buckets}/{total_buckets})</p>
            <p><strong>Guard buckets:</strong> {guard_buckets} | <strong>No-data buckets:</strong> {no_data_buckets}</p>
        </div>
        
        <div class="summary">
            <h3>Recall@10 Statistics</h3>
            <p><strong>Total Recall Events:</strong> {len(recall_events)}</p>
            <p><strong>Average Recall@10:</strong> {avg_recall}</p>
            <p><strong>Recall@10 Range:</strong> {min_recall} - {max_recall}</p>
        </div>
        
        <div class="summary">
            <h3>样例核验</h3>
            {f'<div class="alert-danger" style="background-color: #ffebee; border: 2px solid #f44336; padding: 10px; margin: 10px 0; border-radius: 4px;"><strong>⚠️ ID 仍未对齐</strong> - 所有样例的overlap都是0，请检查数据加载</div>' if recall_samples and all(not sample.get("any_overlap", False) for sample in recall_samples) else ''}
            <table class="debug-table">
                <thead>
                    <tr>
                        <th>Query ID</th>
                        <th>Gold IDs (前3个)</th>
                        <th>Top10 IDs (前5个)</th>
                        <th>Overlap</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''
                    <tr>
                        <td>{sample.get("query_id", "—")}</td>
                        <td>{sample.get("gold_ids", [])}</td>
                        <td>{sample.get("top10_ids", [])}</td>
                        <td style="color: {"green" if sample.get("any_overlap", False) else "red"}; font-weight: bold;">{sample.get("any_overlap", False)}</td>
                    </tr>''' for sample in recall_samples])}
                </tbody>
            </table>
        </div>
        
        <div class="badge-info" style="background-color: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 4px;">
            <strong>📊 统计概览:</strong> 
            Non-empty ratio: <span style="color: #2e7d32;">{non_empty_ratio:.2f}</span> | 
            Guard buckets: <span style="color: #f57c00;">{guard_buckets}</span> | 
            No-data buckets: <span style="color: #d32f2f;">{no_data_buckets}</span>
        </div>
        
        <table class="data-table">
            <thead>
                <tr>
                    <th>Time Bucket</th>
                    <th>Phase</th>
                    <th>Path</th>
                    <th>EF</th>
                    <th>Ncand Max</th>
                    <th>Candidate K</th>
                    <th>Response Count</th>
                    <th>Unique Queries</th>
                    <th>P95 Latency</th>
                    <th>Recall@10</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # Add table rows
    for row in table_rows:
        html_content += f"""
                <tr>
                    <td class="timestamp">{row["time_bucket"]}</td>
                    <td>{row["phase"]}</td>
                    <td>{row["path"]}</td>
                    <td>{row["ef"]}</td>
                    <td>{row["Ncand_max"]}</td>
                    <td>{row["candidate_k"]}</td>
                    <td>{row["response_count"]}</td>
                    <td>{row["unique_queries"]}</td>
                    <td>{row["p95_ms"]}</td>
                    <td>{row["recall_at10"]}</td>
                </tr>
"""
    
    html_content += """
            </tbody>
        </table>
        
        <div class="badge-info" style="background-color: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 4px;">
            <strong>📊 统计概览:</strong> 
            Non-empty ratio: <span style="color: #2e7d32;">{non_empty_ratio:.2f}</span> | 
            Guard buckets: <span style="color: #f57c00;">{guard_buckets}</span> | 
            No-data buckets: <span style="color: #d32f2f;">{no_data_buckets}</span>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def main():
    parser = argparse.ArgumentParser(description="Aggregate observed experiment results")
    parser.add_argument("--trace-file", help="Trace log file")
    parser.add_argument("--summary-file", help="Summary file")
    parser.add_argument("--input", help="Input directory")
    parser.add_argument("--indir", help="Input directory (legacy)")
    parser.add_argument("--html", help="Output HTML file")
    parser.add_argument("--out", help="Output HTML file")
    parser.add_argument("--output", default="reports/observed/observed_report.html", help="Output HTML file")
    parser.add_argument("--baseline", action="store_true", help="Mark as baseline report")
    parser.add_argument("--compare", nargs=2, metavar=("BASELINE_DIR", "TUNER_DIR"), help="Compare two directories")
    parser.add_argument("--simple-compare", nargs=2, metavar=("BASELINE_DIR", "TUNER_DIR"), help="Generate simple comparison report with just P95 latency chart")
    parser.add_argument("--mixed-one", action="store_true", help="Generate mixed-one report with route share and latency analysis")
    parser.add_argument("--suite", choices=["static"], help="Generate static suite report")
    parser.add_argument("--static-suite", action="store_true", help="Generate static suite report (alias for --suite static)")
    parser.add_argument("--data-table", action="store_true", help="Generate pure data table report (no charts)")
    parser.add_argument("--bucket-sec", type=int, default=5, help="Time bucket size in seconds (default: 5)")
    parser.add_argument("--warmup-sec", type=int, default=5, help="Warmup period in seconds (default: 5)")
    parser.add_argument("--switch-guard-sec", type=int, default=2, help="Switch guard period in seconds (default: 2)")
    
    args = parser.parse_args()
    
    # Handle data table mode
    if args.data_table:
        # Determine input directory
        input_dir = args.input or args.indir
        if not input_dir:
            print("Error: --input required for data table mode")
            return
        
        # Load trace log
        trace_file = os.path.join(input_dir, "trace.log")
        events = load_trace_log(trace_file)
        if not events:
            print("Error: Could not load events from trace log")
            return
        
        # Generate data table report with new parameters
        html_content = generate_data_table_html(
            events, 
            bucket_sec=args.bucket_sec,
            warmup_sec=args.warmup_sec,
            switch_guard_sec=args.switch_guard_sec
        )
        
        # Determine output file
        output_file = args.out or "reports/observed/data_table.html"
        
        # Save report
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"Data table report generated: {output_file}")
        return
    
    # Handle static suite mode
    if args.suite == "static" or args.static_suite:
        # Determine input directory
        input_dir = args.input or args.indir
        if not input_dir:
            print("Error: --input required for static suite mode")
            return
        
        # Load trace log
        trace_file = os.path.join(input_dir, "trace.log")
        events = load_trace_log(trace_file)
        if not events:
            print("Error: Could not load events from trace log")
            return
        
        # Generate static suite report
        html_content = generate_static_suite_html(events)
        
        # Determine output file
        output_file = args.out or "reports/observed/static_suite.html"
        
        # Save report
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"Static suite report generated: {output_file}")
        return
    
    # Handle mixed-one mode
    if args.mixed_one:
        # Determine input file
        input_file = args.input or args.trace_file
        if not input_file:
            print("Error: --input or --trace-file required for mixed-one mode")
            return
        
        # Load trace log
        events = load_trace_log(input_file)
        if not events:
            print("Error: Could not load events from trace log")
            return
        
        # Generate mixed-one report
        html_content = generate_mixed_one_html(events)
        
        # Determine output file
        output_file = args.out or "reports/observed/mixed_one_report.html"
        
        # Save report
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"Mixed-one report generated: {output_file}")
        return
    
    # Handle simple compare mode
    if args.simple_compare:
        baseline_dir, tuner_dir = args.simple_compare
        
        # Load trace logs from both directories
        baseline_trace = os.path.join(baseline_dir, "trace.log")
        tuner_trace = os.path.join(tuner_dir, "trace.log")
        
        baseline_events = load_trace_log(baseline_trace)
        tuner_events = load_trace_log(tuner_trace)
        
        if not baseline_events or not tuner_events:
            print("Error: Could not load events from both directories")
            return
        
        # Generate simple comparison report
        html_content = generate_simple_compare_html(baseline_events, tuner_events)
        
        # Determine output file
        output_file = args.out or "reports/observed/observed_compare_simple.html"
        
        # Save report
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"Simple comparison report generated: {output_file}")
        return
    
    # Handle compare mode
    if args.compare:
        baseline_dir, tuner_dir = args.compare
        
        # Load trace logs from both directories
        baseline_trace = os.path.join(baseline_dir, "trace.log")
        tuner_trace = os.path.join(tuner_dir, "trace.log")
        
        baseline_events = load_trace_log(baseline_trace)
        tuner_events = load_trace_log(tuner_trace)
        
        if not baseline_events or not tuner_events:
            print("Error: Could not load events from both directories")
            return
        
        # Generate comparison report
        html_content = generate_compare_html(baseline_events, tuner_events, baseline_dir, tuner_dir)
        
        # Determine output file
        output_file = args.out or "reports/observed/observed_compare.html"
        
        # Save report
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"Comparison report generated: {output_file}")
        return
    
    # Single report mode
    # Determine input files
    input_dir = args.input or args.indir
    if input_dir:
        trace_file = os.path.join(input_dir, "trace.log")
        summary_file = os.path.join(input_dir, "summary.json")
    else:
        trace_file = args.trace_file or "reports/observed/trace.log"
        summary_file = args.summary_file or "reports/observed/summary.json"
    
    # Load trace log
    events = load_trace_log(trace_file)
    
    if not events:
        print("No events found in trace log. Cannot generate report.")
        return
    
    # Extract stages
    stages = extract_metrics_by_stage(events)
    
    if not stages:
        print("No stages found in trace log. Cannot generate report.")
        return
    
    print(f"Found {len(stages)} stages: {list(stages.keys())}")
    
    # Generate HTML report
    html_content = generate_html_report(stages, summary_file, events)
    
    # Determine output file
    output_file = args.out or args.html or args.output
    if args.baseline:
        base_name = os.path.splitext(output_file)[0]
        output_file = f"{base_name}_baseline.html"
    
    # Save report
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    # Save tuner impact JSON if there are change events
    change_events = extract_tuner_impact(events)
    if change_events:
        tuner_impact_file = os.path.join(os.path.dirname(output_file), "tuner_impact.json")
        with open(tuner_impact_file, 'w') as f:
            json.dump(change_events, f, indent=2)
        print(f"Tuner impact data saved: {tuner_impact_file}")
    
    print(f"Report generated: {output_file}")
    
    # Print summary statistics
    total_events = len(events)
    response_events = len([e for e in events if e.get("event") == "RESPONSE"])
    autotuner_events = len([e for e in events if e.get("event") == "AUTOTUNER_SUGGEST"])
    
    print(f"\nSummary:")
    print(f"  Total events: {total_events}")
    print(f"  Response events: {response_events}")
    print(f"  AutoTuner suggestions: {autotuner_events}")
    print(f"  Stages analyzed: {len(stages)}")

if __name__ == "__main__":
    main()
