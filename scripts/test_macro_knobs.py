#!/usr/bin/env python3
"""
Macro Knobs Test Script

This script runs a quick 3-minute sanity test for the macro knobs feature
with two test cases: latency-leaning and recall-leaning configurations.
"""

import os
import sys
import json
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from modules.search.search_pipeline import SearchPipeline
from modules.autotune.macros import get_macro_config, derive_params

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('macro_knobs_test.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def run_test_case(case_name: str, latency_guard: float, recall_bias: float, duration_sec: int = 180):
    """Run a test case with specific macro knob settings."""
    logger = logging.getLogger(__name__)
    
    # Set environment variables for this test case
    env = os.environ.copy()
    env.update({
        "DATASET": "fiqa",
        "COLLECTION": "beir_fiqa_full_ta",
        "LATENCY_GUARD": str(latency_guard),
        "RECALL_BIAS": str(recall_bias),
        "FORCE_HYBRID_ON": "1",
        "FORCE_CE_ON": "1",
        "CE_CACHE_SIZE": "0",
        "RERANK_K": "50",
        "CANDIDATE_K_STEP": "200",
        "CHAOS_LAT_MS": "200",
        "CHAOS_BURST_EVERY": "40",
        "DURATION_SEC": str(duration_sec),
        "QPS": "5"
    })
    
    logger.info(f"Starting {case_name} test case:")
    logger.info(f"  LATENCY_GUARD={latency_guard}")
    logger.info(f"  RECALL_BIAS={recall_bias}")
    
    # Get derived parameters
    macro_config = get_macro_config()
    derived_params = derive_params(macro_config["latency_guard"], macro_config["recall_bias"])
    
    logger.info(f"  Derived parameters: {derived_params}")
    
    # Create a simple config for the search pipeline
    config = {
        "retriever": {
            "type": "vector",
            "top_k": 200
        },
        "reranker": {
            "type": "simple_ce"
        }
    }
    
    # Initialize search pipeline
    pipeline = SearchPipeline(config)
    
    # Test queries
    test_queries = [
        "What are the best investment strategies for retirement?",
        "How to manage personal finances effectively?",
        "What are the risks of cryptocurrency investment?",
        "How to build a diversified investment portfolio?",
        "What is the difference between stocks and bonds?"
    ]
    
    results = []
    start_time = time.time()
    query_count = 0
    
    logger.info(f"Running queries for {duration_sec} seconds...")
    
    while time.time() - start_time < duration_sec:
        for query in test_queries:
            if time.time() - start_time >= duration_sec:
                break
                
            try:
                # Perform search
                search_start = time.time()
                search_results = pipeline.search(
                    query=query,
                    collection_name="beir_fiqa_full_ta",
                    trace_id=f"{case_name}_{query_count}"
                )
                search_time = (time.time() - search_start) * 1000  # Convert to ms
                
                results.append({
                    "case": case_name,
                    "query": query,
                    "query_id": query_count,
                    "search_time_ms": search_time,
                    "result_count": len(search_results),
                    "timestamp": time.time()
                })
                
                query_count += 1
                
                # Rate limiting: 5 QPS = 200ms between queries
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error in query {query_count}: {e}")
                continue
    
    logger.info(f"Completed {case_name}: {query_count} queries in {time.time() - start_time:.1f}s")
    return results

def analyze_results(results_a, results_b):
    """Analyze and compare results from both test cases."""
    logger = logging.getLogger(__name__)
    
    # Calculate P95 latency for each case
    def calc_p95_latency(results):
        latencies = [r["search_time_ms"] for r in results]
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        return latencies[p95_index] if latencies else 0
    
    p95_a = calc_p95_latency(results_a)
    p95_b = calc_p95_latency(results_b)
    
    logger.info(f"Case A (latency-leaning) P95 latency: {p95_a:.1f}ms")
    logger.info(f"Case B (recall-leaning) P95 latency: {p95_b:.1f}ms")
    
    return {
        "case_a_p95": p95_a,
        "case_b_p95": p95_b,
        "case_a_queries": len(results_a),
        "case_b_queries": len(results_b)
    }

def generate_chart(results_a, results_b, analysis):
    """Generate a simple HTML chart comparing the two test cases."""
    
    # Create time series data for the chart
    def create_time_series(results, case_name):
        time_series = []
        for result in results:
            time_series.append({
                "time": result["timestamp"],
                "latency": result["search_time_ms"]
            })
        return time_series
    
    series_a = create_time_series(results_a, "Case A")
    series_b = create_time_series(results_b, "Case B")
    
    # Generate HTML chart using Chart.js
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Macro Knobs Comparison</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .chart-container {{ width: 800px; height: 400px; margin: 20px 0; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>Macro Knobs Comparison Results</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Case A (Latency-leaning):</strong> P95 Latency = {analysis['case_a_p95']:.1f}ms, Queries = {analysis['case_a_queries']}</p>
        <p><strong>Case B (Recall-leaning):</strong> P95 Latency = {analysis['case_b_p95']:.1f}ms, Queries = {analysis['case_b_queries']}</p>
    </div>
    
    <div class="chart-container">
        <canvas id="latencyChart"></canvas>
    </div>
    
    <script>
        const ctx = document.getElementById('latencyChart').getContext('2d');
        
        // Convert timestamps to relative time in seconds
        const startTime = Math.min(...{json.dumps([r['timestamp'] for r in results_a + results_b])});
        
        const dataA = {json.dumps([{'x': (r['timestamp'] - startTime), 'y': r['search_time_ms']} for r in results_a])};
        const dataB = {json.dumps([{'x': (r['timestamp'] - startTime), 'y': r['search_time_ms']} for r in results_b])};
        
        new Chart(ctx, {{
            type: 'line',
            data: {{
                datasets: [
                    {{
                        label: 'Case A (Latency-leaning)',
                        data: dataA,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.1
                    }},
                    {{
                        label: 'Case B (Recall-leaning)',
                        data: dataB,
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        tension: 0.1
                    }}
                ]
            }},
            options: {{
                responsive: true,
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
                            text: 'Latency (ms)'
                        }}
                    }}
                }},
                plugins: {{
                    title: {{
                        display: true,
                        text: 'P95 Latency Over Time - Macro Knobs Comparison'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    return html_content

def main():
    """Main function to run the macro knobs test."""
    logger = setup_logging()
    
    logger.info("Starting Macro Knobs Test")
    logger.info("=" * 50)
    
    # Test Case A: Latency-leaning
    logger.info("Running Case A: Latency-leaning (LATENCY_GUARD=0.7, RECALL_BIAS=0.4)")
    results_a = run_test_case("Case A", 0.7, 0.4, 180)
    
    # Test Case B: Recall-leaning  
    logger.info("Running Case B: Recall-leaning (LATENCY_GUARD=0.3, RECALL_BIAS=0.7)")
    results_b = run_test_case("Case B", 0.3, 0.7, 180)
    
    # Analyze results
    analysis = analyze_results(results_a, results_b)
    
    # Generate chart
    chart_html = generate_chart(results_a, results_b, analysis)
    
    # Save chart to reports directory
    reports_dir = Path("reports/observed")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    chart_path = reports_dir / "macros_compare.html"
    with open(chart_path, 'w') as f:
        f.write(chart_html)
    
    logger.info(f"Chart saved to: {chart_path}")
    logger.info("Macro Knobs Test completed successfully!")

if __name__ == "__main__":
    main()
