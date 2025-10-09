#!/usr/bin/env python3
"""
Create a mixed-path comparison report from trace.log files
"""

import json
import os
import argparse
import re
from pathlib import Path
from collections import defaultdict

def parse_trace_events(trace_file):
    """Parse trace.log file and extract events"""
    events = {
        'ROUTE_CHOICE': [],
        'PATH_USED': [],
        'RETRIEVE_VECTOR': [],
        'RERANK_CE': []
    }
    
    if not os.path.exists(trace_file):
        print(f"Warning: {trace_file} not found")
        return events
    
    with open(trace_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                event = json.loads(line)
                event_type = event.get('event', '')
                if event_type in events:
                    events[event_type].append(event)
            except json.JSONDecodeError:
                continue
    
    return events

def create_mixed_report(stage1_trace, stage2_trace, output_file):
    """Create HTML report comparing two experiment stages"""
    
    # Parse trace events
    stage1_events = parse_trace_events(stage1_trace)
    stage2_events = parse_trace_events(stage2_trace)
    
    # Count route choices and path usage
    stage1_route_choices = len(stage1_events['ROUTE_CHOICE'])
    stage1_mem_used = len([e for e in stage1_events['PATH_USED'] if e.get('params', {}).get('path') == 'mem'])
    stage1_hnsw_used = len([e for e in stage1_events['PATH_USED'] if e.get('params', {}).get('path') == 'hnsw'])
    
    stage2_route_choices = len(stage2_events['ROUTE_CHOICE'])
    stage2_mem_used = len([e for e in stage2_events['PATH_USED'] if e.get('params', {}).get('path') == 'mem'])
    stage2_hnsw_used = len([e for e in stage2_events['PATH_USED'] if e.get('params', {}).get('path') == 'hnsw'])
    
    # Calculate ratios
    stage1_total_paths = stage1_mem_used + stage1_hnsw_used
    stage2_total_paths = stage2_mem_used + stage2_hnsw_used
    
    stage1_mem_ratio = (stage1_mem_used / stage1_total_paths * 100) if stage1_total_paths > 0 else 0
    stage1_hnsw_ratio = (stage1_hnsw_used / stage1_total_paths * 100) if stage1_total_paths > 0 else 0
    
    stage2_mem_ratio = (stage2_mem_used / stage2_total_paths * 100) if stage2_total_paths > 0 else 0
    stage2_hnsw_ratio = (stage2_hnsw_used / stage2_total_paths * 100) if stage2_total_paths > 0 else 0
    
    # Extract N and T values for histogram
    stage1_n_values = [e.get('params', {}).get('N', 0) for e in stage1_events['ROUTE_CHOICE']]
    stage1_t_values = [e.get('params', {}).get('T', 0) for e in stage1_events['ROUTE_CHOICE']]
    stage1_avg_t = sum(stage1_t_values) / len(stage1_t_values) if stage1_t_values else 0
    
    stage2_n_values = [e.get('params', {}).get('N', 0) for e in stage2_events['ROUTE_CHOICE']]
    stage2_t_values = [e.get('params', {}).get('T', 0) for e in stage2_events['ROUTE_CHOICE']]
    stage2_avg_t = sum(stage2_t_values) / len(stage2_t_values) if stage2_t_values else 0
    
    # Extract latency data
    stage1_latencies = []
    stage2_latencies = []
    
    for event in stage1_events['RETRIEVE_VECTOR']:
        if 'cost_ms' in event:
            stage1_latencies.append(event['cost_ms'])
    
    for event in stage2_events['RETRIEVE_VECTOR']:
        if 'cost_ms' in event:
            stage2_latencies.append(event['cost_ms'])
    
    # Calculate P95 latencies
    def p95(data):
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * 0.95)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    stage1_p95 = p95(stage1_latencies)
    stage2_p95 = p95(stage2_latencies)
    
    # Generate HTML report
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Mixed-path Probe Report (FiQA)</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metrics-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .chart-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .chart {{ height: 300px; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ color: #7f8c8d; margin-top: 5px; }}
        h1 {{ color: #2c3e50; margin: 0; }}
        h2 {{ color: #34495e; margin-top: 0; }}
        .stage-info {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Mixed-path Probe Report (FiQA)</h1>
            <p><strong>Duration:</strong> 90s each stage | <strong>QPS:</strong> 5 | <strong>Total Events:</strong> {stage1_route_choices + stage2_route_choices}</p>
        </div>
        
        <div class="stage-info">
            <h3>Stage 1: HNSW Majority (LATENCY_GUARD=0.0, T≈{stage1_avg_t:.0f}, candidate_k=400)</h3>
            <p>Route Choices: {stage1_route_choices} | MEM: {stage1_mem_used} ({stage1_mem_ratio:.1f}%) | HNSW: {stage1_hnsw_used} ({stage1_hnsw_ratio:.1f}%)</p>
        </div>
        
        <div class="stage-info">
            <h3>Stage 2: MEM Majority (LATENCY_GUARD=0.9, T≈{stage2_avg_t:.0f}, candidate_k=100)</h3>
            <p>Route Choices: {stage2_route_choices} | MEM: {stage2_mem_used} ({stage2_mem_ratio:.1f}%) | HNSW: {stage2_hnsw_used} ({stage2_hnsw_ratio:.1f}%)</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{stage1_hnsw_ratio:.1f}%</div>
                <div class="metric-label">Stage1 HNSW Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stage1_mem_ratio:.1f}%</div>
                <div class="metric-label">Stage1 MEM Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stage2_hnsw_ratio:.1f}%</div>
                <div class="metric-label">Stage2 HNSW Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stage2_mem_ratio:.1f}%</div>
                <div class="metric-label">Stage2 MEM Usage</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>📊 Route Selection Comparison</h2>
            <div class="chart">
                <canvas id="routeChart"></canvas>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>📈 P95 Latency Comparison</h2>
            <div class="chart">
                <canvas id="latencyChart"></canvas>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>📊 N Distribution with T Threshold</h2>
            <div class="chart">
                <canvas id="histogramChart"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        // Route Selection Chart
        const routeCtx = document.getElementById('routeChart').getContext('2d');
        new Chart(routeCtx, {{
            type: 'bar',
            data: {{
                labels: ['Stage1 (HNSW Majority)', 'Stage2 (MEM Majority)'],
                datasets: [{{
                    label: 'HNSW Path',
                    data: [{stage1_hnsw_ratio}, {stage2_hnsw_ratio}],
                    backgroundColor: '#e74c3c',
                    borderWidth: 1
                }}, {{
                    label: 'MEM Path', 
                    data: [{stage1_mem_ratio}, {stage2_mem_ratio}],
                    backgroundColor: '#3498db',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ stacked: true }},
                    y: {{ 
                        stacked: true,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'Percentage (%)'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'top'
                    }}
                }}
            }}
        }});
        
        // P95 Latency Chart
        const latencyCtx = document.getElementById('latencyChart').getContext('2d');
        new Chart(latencyCtx, {{
            type: 'bar',
            data: {{
                labels: ['Stage1 (HNSW Majority)', 'Stage2 (MEM Majority)'],
                datasets: [{{
                    label: 'P95 Latency (ms)',
                    data: [{stage1_p95:.1f}, {stage2_p95:.1f}],
                    backgroundColor: ['#e74c3c', '#3498db'],
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        title: {{
                            display: true,
                            text: 'P95 Latency (ms)'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
        
        // N Distribution Histogram
        const histCtx = document.getElementById('histogramChart').getContext('2d');
        
        // Create histogram data
        const stage1NData = {stage1_n_values};
        const stage2NData = {stage2_n_values};
        
        // Simple histogram bins
        const bins = [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500];
        const stage1Hist = new Array(bins.length-1).fill(0);
        const stage2Hist = new Array(bins.length-1).fill(0);
        
        stage1NData.forEach(n => {{
            for (let i = 0; i < bins.length-1; i++) {{
                if (n >= bins[i] && n < bins[i+1]) {{
                    stage1Hist[i]++;
                    break;
                }}
            }}
        }});
        
        stage2NData.forEach(n => {{
            for (let i = 0; i < bins.length-1; i++) {{
                if (n >= bins[i] && n < bins[i+1]) {{
                    stage2Hist[i]++;
                    break;
                }}
            }}
        }});
        
        const binLabels = bins.slice(0, -1).map((bin, i) => `${{bin}}-${{bins[i+1]}}`);
        
        new Chart(histCtx, {{
            type: 'bar',
            data: {{
                labels: binLabels,
                datasets: [{{
                    label: 'Stage1 (HNSW Majority)',
                    data: stage1Hist,
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    borderColor: '#e74c3c',
                    borderWidth: 1
                }}, {{
                    label: 'Stage2 (MEM Majority)',
                    data: stage2Hist,
                    backgroundColor: 'rgba(52, 152, 219, 0.7)',
                    borderColor: '#3498db',
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
                            text: 'N (candidate_k)'
                        }}
                    }},
                    y: {{
                        title: {{
                            display: true,
                            text: 'Count'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'top'
                    }}
                }},
                annotation: {{
                    annotations: {{
                        line1: {{
                            type: 'line',
                            xMin: {stage1_avg_t},
                            xMax: {stage1_avg_t},
                            borderColor: 'red',
                            borderWidth: 2,
                            label: {{
                                content: 'Stage1 T',
                                enabled: true
                            }}
                        }},
                        line2: {{
                            type: 'line',
                            xMin: {stage2_avg_t},
                            xMax: {stage2_avg_t},
                            borderColor: 'blue',
                            borderWidth: 2,
                            label: {{
                                content: 'Stage2 T',
                                enabled: true
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
    
    # Save report
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"Mixed-path comparison report generated: {output_file}")
    print(f"Stage1: {stage1_route_choices} route choices, {stage1_mem_used} MEM, {stage1_hnsw_used} HNSW")
    print(f"Stage2: {stage2_route_choices} route choices, {stage2_mem_used} MEM, {stage2_hnsw_used} HNSW")

def main():
    parser = argparse.ArgumentParser(description="Create mixed-path comparison report")
    parser.add_argument("--stage1", required=True, help="Stage1 trace.log file")
    parser.add_argument("--stage2", required=True, help="Stage2 trace.log file")
    parser.add_argument("--out", required=True, help="Output HTML file")
    
    args = parser.parse_args()
    create_mixed_report(args.stage1, args.stage2, args.out)

if __name__ == "__main__":
    main()
