#!/usr/bin/env python3
"""
Macro Probe Experiment Script
Runs a 3-minute experiment to validate macro knob instrumentation
"""

import os
import sys
import time
import json
import logging
import asyncio
import numpy as np
from collections import defaultdict
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.search.search_pipeline import SearchPipeline
from modules.autotune.macros import get_macro_config, derive_params

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock queries for FiQA dataset
FIQA_QUERIES = [
    "What is the difference between stocks and bonds?",
    "What are the best investment strategies for retirement?",
    "How to manage personal finances effectively?",
    "What are the risks of cryptocurrency investment?",
    "How to build a diversified investment portfolio?",
    "What is compound interest and how does it work?",
    "How to choose the right mutual fund?",
    "What are the benefits of index funds?",
    "How to create a budget for monthly expenses?",
    "What is the 50-30-20 rule for budgeting?"
]

def setup_experiment_environment():
    """Setup environment variables for the experiment"""
    os.environ["DATASET"] = "fiqa"
    os.environ["COLLECTION"] = "beir_fiqa_full_ta"
    os.environ["FORCE_HYBRID_ON"] = "0"  # Use pure vector search to test macro knobs
    os.environ["FORCE_CE_ON"] = "0"  # Disable CE for cleaner traces
    os.environ["CE_CACHE_SIZE"] = "0"
    os.environ["RERANK_K"] = "50"
    os.environ["CANDIDATE_K_STEP"] = "200"
    os.environ["CHAOS_LAT_MS"] = "200"
    os.environ["CHAOS_BURST_EVERY"] = "40"
    os.environ["DURATION_SEC"] = "180"
    os.environ["QPS"] = "5"
    os.environ["LATENCY_GUARD"] = "0.5"
    os.environ["RECALL_BIAS"] = "0.5"

async def run_experiment():
    """Run the 3-minute macro probe experiment"""
    logger.info("Starting Macro Probe Experiment")
    logger.info("Duration: 180 seconds, QPS: 5, LATENCY_GUARD=0.5, RECALL_BIAS=0.5")
    
    # Setup environment
    setup_experiment_environment()
    
    # Create output directory
    output_dir = Path("reports/observed/macro_probe_experiment")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Redirect stdout to trace.log
    import sys
    original_stdout = sys.stdout
    trace_file = output_dir / "trace.log"
    sys.stdout = open(trace_file, "w")
    
    # Initialize pipeline with pure vector search to test macro knobs
    pipeline = SearchPipeline(config={
        "retriever": {"type": "vector", "top_k": 200}, 
        "reranker": None
    })
    
    # Create output directory
    output_dir = Path("reports/observed/macro_probe_experiment")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Experiment parameters
    duration_sec = 180
    qps = 5
    query_interval = 1.0 / qps
    
    # Data collection
    start_time = time.time()
    query_count = 0
    latency_data = []
    
    # Clear any previous run info flag
    if hasattr(SearchPipeline, '_run_info_emitted'):
        del SearchPipeline._run_info_emitted
    
    logger.info(f"Experiment started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    while time.time() - start_time < duration_sec:
        query_start_time = time.time()
        query = FIQA_QUERIES[query_count % len(FIQA_QUERIES)]
        
        try:
            # Execute search
            search_results = pipeline.search(
                query=query, 
                collection_name="beir_fiqa_full_ta", 
                trace_id=f"macro_probe_{query_count}"
            )
            
            # Record latency
            latency = (time.time() - query_start_time) * 1000
            latency_data.append({
                "timestamp": time.time(),
                "query_id": query_count,
                "latency_ms": latency,
                "results_count": len(search_results)
            })
            
            query_count += 1
            if query_count % 10 == 0:
                logger.info(f"Completed {query_count} queries, avg latency: {np.mean([d['latency_ms'] for d in latency_data[-10:]]):.1f}ms")
                
        except Exception as e:
            logger.error(f"Error in query {query_count}: {e}")
        
        # Wait for next query
        time_to_wait = query_interval - (time.time() - query_start_time)
        if time_to_wait > 0:
            await asyncio.sleep(time_to_wait)
    
    logger.info(f"Experiment completed: {query_count} queries in {time.time() - start_time:.1f}s")
    
    # Restore stdout
    sys.stdout.close()
    sys.stdout = original_stdout
    
    # Save experiment data
    experiment_data = {
        "experiment_info": {
            "duration_sec": duration_sec,
            "qps": qps,
            "total_queries": query_count,
            "latency_guard": 0.5,
            "recall_bias": 0.5,
            "derived_params": derive_params(0.5, 0.5)
        },
        "latency_data": latency_data
    }
    
    # Save summary.json
    summary_path = output_dir / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(experiment_data, f, indent=2)
    
    logger.info(f"Experiment data saved to {summary_path}")
    
    return experiment_data

def parse_trace_log():
    """Parse trace.log to extract macro knob events"""
    # Try multiple possible trace.log locations
    trace_paths = [
        Path("reports/observed/macro_probe_experiment/trace.log"),
        Path("trace.log"),
        Path("reports/observed/trace.log")
    ]
    
    trace_path = None
    for path in trace_paths:
        if path.exists():
            trace_path = path
            break
    
    if not trace_path:
        logger.warning("trace.log not found in any expected location, creating empty trace data")
        return {
            "route_choices": [],
            "cand_after_limits": [],
            "exact_path_used": [],
            "responses": []
        }
    
    logger.info(f"Using trace.log from: {trace_path}")
    
    events = {
        "route_choices": [],
        "cand_after_limits": [],
        "exact_path_used": [],
        "responses": []
    }
    
    with open(trace_path, "r") as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                event_type = event.get("event")
                
                if event_type == "ROUTE_CHOICE":
                    events["route_choices"].append(event)
                elif event_type == "CAND_AFTER_LIMIT":
                    events["cand_after_limits"].append(event)
                elif event_type == "EXACT_PATH_USED":
                    events["exact_path_used"].append(event)
                elif event_type == "RESPONSE":
                    events["responses"].append(event)
            except json.JSONDecodeError:
                continue
    
    return events

def generate_html_report(experiment_data, trace_events):
    """Generate compact HTML report with 4 charts"""
    output_path = Path("reports/observed/macro_probe_report.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate metrics
    latency_data = experiment_data["latency_data"]
    latencies = [d["latency_ms"] for d in latency_data]
    p95_latency = np.percentile(latencies, 95) if latencies else 0
    
    # Route choice analysis
    route_choices = trace_events["route_choices"]
    mem_count = sum(1 for r in route_choices if r.get("params", {}).get("path") == "mem")
    hnsw_count = sum(1 for r in route_choices if r.get("params", {}).get("path") == "hnsw")
    total_routes = len(route_choices)
    mem_percentage = (mem_count / total_routes * 100) if total_routes > 0 else 0
    hnsw_percentage = (hnsw_count / total_routes * 100) if total_routes > 0 else 0
    
    # Truncation analysis
    cand_limits = trace_events["cand_after_limits"]
    truncation_ratios = []
    for c in cand_limits:
        params = c.get("params", {})
        before = params.get("before", 0)
        after = params.get("after", 0)
        if before > 0:
            truncation_ratios.append(after / before)
    avg_truncation_ratio = np.mean(truncation_ratios) if truncation_ratios else 1.0
    
    # Exact path usage
    exact_path_events = trace_events["exact_path_used"]
    exact_path_usage_rate = (len(exact_path_events) / total_routes * 100) if total_routes > 0 else 0
    
    # Time series data for P95 latency
    time_series_data = []
    if latency_data:
        # Group by 10-second windows
        start_time = min(d["timestamp"] for d in latency_data)
        window_size = 10  # seconds
        windows = defaultdict(list)
        
        for d in latency_data:
            window = int((d["timestamp"] - start_time) / window_size)
            windows[window].append(d["latency_ms"])
        
        for window, latencies in sorted(windows.items()):
            p95 = np.percentile(latencies, 95)
            time_series_data.append({
                "time": window * window_size,
                "p95_latency": p95
            })
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Macro Probe Experiment Report</title>
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Macro Probe Experiment Report</h1>
            <p><strong>Duration:</strong> 180s | <strong>QPS:</strong> 5 | <strong>Total Queries:</strong> {len(latency_data)}</p>
            <p><strong>Macro Knobs:</strong> LATENCY_GUARD=0.5, RECALL_BIAS=0.5</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{mem_percentage:.1f}%</div>
                <div class="metric-label">Memory Path Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{hnsw_percentage:.1f}%</div>
                <div class="metric-label">HNSW Path Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_truncation_ratio:.2f}</div>
                <div class="metric-label">Avg Truncation Ratio</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{exact_path_usage_rate:.1f}%</div>
                <div class="metric-label">Exact Path Usage Rate</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>📊 Route Selection Distribution</h2>
            <div class="chart">
                <canvas id="routeChart"></canvas>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>📈 P95 Latency Over Time</h2>
            <div class="chart">
                <canvas id="latencyChart"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        // Route Selection Chart
        const routeCtx = document.getElementById('routeChart').getContext('2d');
        new Chart(routeCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Memory Path', 'HNSW Path'],
                datasets: [{{
                    data: [{mem_count}, {hnsw_count}],
                    backgroundColor: ['#3498db', '#e74c3c'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // P95 Latency Chart
        const latencyCtx = document.getElementById('latencyChart').getContext('2d');
        const timeSeriesData = {json.dumps(time_series_data)};
        
        new Chart(latencyCtx, {{
            type: 'line',
            data: {{
                labels: timeSeriesData.map(d => d.time + 's'),
                datasets: [{{
                    label: 'P95 Latency (ms)',
                    data: timeSeriesData.map(d => d.p95_latency),
                    borderColor: '#27ae60',
                    backgroundColor: 'rgba(39, 174, 96, 0.1)',
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        title: {{
                            display: true,
                            text: 'Time (seconds)'
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
</html>"""
    
    with open(output_path, "w") as f:
        f.write(html_content)
    
    logger.info(f"HTML report generated: {output_path}")
    return output_path

async def main():
    """Main experiment function"""
    try:
        # Run experiment
        experiment_data = await run_experiment()
        
        # Parse trace events
        trace_events = parse_trace_log()
        
        # Generate HTML report
        report_path = generate_html_report(experiment_data, trace_events)
        
        logger.info("🎉 Macro Probe Experiment completed successfully!")
        logger.info(f"📊 Report available at: {report_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("📋 EXPERIMENT SUMMARY")
        print("="*60)
        print(f"Total Queries: {len(experiment_data['latency_data'])}")
        print(f"Route Choices: {len(trace_events['route_choices'])}")
        print(f"Truncation Events: {len(trace_events['cand_after_limits'])}")
        print(f"Exact Path Events: {len(trace_events['exact_path_used'])}")
        print(f"Report: {report_path}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
