import os
import sys
import time
import json
import logging
import asyncio
import numpy as np
from collections import defaultdict

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.search.search_pipeline import SearchPipeline
from modules.autotune.macros import get_macro_config, derive_params

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock queries for FiQA dataset
FIQA_QUERIES = [
    "What is the difference between stocks and bonds?",
    "What are the best investment strategies for retirement?",
    "How to manage personal finances effectively?",
    "What are the risks of cryptocurrency investment?",
    "How to build a diversified investment portfolio?"
]

def get_macro_config_from_env():
    """Reads macro knob configuration from environment variables."""
    latency_guard = float(os.environ.get("LATENCY_GUARD", 0.5))
    recall_bias = float(os.environ.get("RECALL_BIAS", 0.5))
    return {"latency_guard": latency_guard, "recall_bias": recall_bias}

async def run_test_case(case_name: str, latency_guard: float, recall_bias: float, duration_sec: int, qps: int):
    logger.info(f"Starting {case_name} with LATENCY_GUARD={latency_guard}, RECALL_BIAS={recall_bias}")

    # Set environment variables for the test case
    os.environ["DATASET"] = "fiqa"
    os.environ["COLLECTION"] = "beir_fiqa_full_ta"
    os.environ["FORCE_HYBRID_ON"] = "1"
    os.environ["FORCE_CE_ON"] = "0"  # Disable CE for this simplified test
    os.environ["CE_CACHE_SIZE"] = "0"
    os.environ["RERANK_K"] = "50"
    os.environ["CANDIDATE_K_STEP"] = "200"
    os.environ["CHAOS_LAT_MS"] = "200"
    os.environ["CHAOS_BURST_EVERY"] = "40"
    os.environ["DURATION_SEC"] = str(duration_sec)
    os.environ["QPS"] = str(qps)
    os.environ["LATENCY_GUARD"] = str(latency_guard)
    os.environ["RECALL_BIAS"] = str(recall_bias)

    # Re-initialize pipeline to pick up new ENV vars
    pipeline = SearchPipeline(config={"retriever": {"type": "hybrid", "top_k": 200}, "reranker": None})

    query_interval = 1.0 / qps
    start_time = time.time()
    query_count = 0
    results_for_chart = []

    while time.time() - start_time < duration_sec:
        query_start_time = time.time()
        query = FIQA_QUERIES[query_count % len(FIQA_QUERIES)]
        
        try:
            search_results = pipeline.search(query=query, collection_name="beir_fiqa_full_ta", trace_id=f"{case_name}_{query_count}")
            latency = (time.time() - query_start_time) * 1000
            results_for_chart.append({
                "timestamp": time.time(),
                "search_time_ms": latency
            })
            query_count += 1
            logger.info(f"Query {query_count}: {latency:.1f}ms, {len(search_results)} results")
        except Exception as e:
            logger.error(f"Error in query {query_count}: {e}")
        
        time_to_wait = query_interval - (time.time() - query_start_time)
        if time_to_wait > 0:
            await asyncio.sleep(time_to_wait)
    
    logger.info(f"Completed {case_name}: {query_count} queries in {round(time.time() - start_time)}s")
    return results_for_chart

def generate_chart(results_a, results_b, output_path):
    """Generates an HTML chart with Chart.js."""
    p95_a = np.percentile([r['search_time_ms'] for r in results_a], 95) if results_a else 0.0
    p95_b = np.percentile([r['search_time_ms'] for r in results_b], 95) if results_b else 0.0

    logger.info(f"Case A (latency-leaning) P95 latency: {p95_a:.1f}ms")
    logger.info(f"Case B (recall-leaning) P95 latency: {p95_b:.1f}ms")

    # Calculate relative timestamps
    all_timestamps = [r['timestamp'] for r in results_a + results_b]
    start_time = min(all_timestamps) if all_timestamps else 0
    
    # Sample data points to reduce density - take every 5th point
    data_a = [{'x': round((r['timestamp'] - start_time), 1), 'y': r['search_time_ms']} 
              for i, r in enumerate(results_a) if i % 5 == 0]
    data_b = [{'x': round((r['timestamp'] - start_time), 1), 'y': r['search_time_ms']} 
              for i, r in enumerate(results_b) if i % 5 == 0]

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Macro Knobs Comparison</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .chart-container {{ width: 800px; height: 400px; margin: 20px 0; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .params {{ background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>Macro Knobs Comparison Results</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Case A (Latency-leaning):</strong> P95 Latency = {p95_a:.1f}ms, Queries = {len(results_a)}</p>
        <p><strong>Case B (Recall-leaning):</strong> P95 Latency = {p95_b:.1f}ms, Queries = {len(results_b)}</p>
    </div>
    
    <div class="params">
        <h2>Macro Knob Parameters</h2>
        <p><strong>Case A:</strong> LATENCY_GUARD=0.7, RECALL_BIAS=0.4</p>
        <p><strong>Case B:</strong> LATENCY_GUARD=0.3, RECALL_BIAS=0.7</p>
    </div>
    
    <div class="chart-container">
        <canvas id="latencyChart"></canvas>
    </div>
    
    <script>
        const ctx = document.getElementById('latencyChart').getContext('2d');
        
        const dataA = {json.dumps(data_a)};
        const dataB = {json.dumps(data_b)};
        
        new Chart(ctx, {{
            type: 'line',
            data: {{
                datasets: [
                    {{
                        label: 'Case A (Latency-leaning)',
                        data: dataA,
                        borderColor: 'rgba(255, 99, 132, 0.8)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.1,
                        pointRadius: 0,
                        borderWidth: 2,
                        pointHoverRadius: 4,
                        fill: false
                    }},
                    {{
                        label: 'Case B (Recall-leaning)',
                        data: dataB,
                        borderColor: 'rgba(54, 162, 235, 0.8)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        tension: 0.1,
                        pointRadius: 0,
                        borderWidth: 2,
                        pointHoverRadius: 4,
                        fill: false
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        type: 'linear',
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
                    }},
                    tooltip: {{
                        callbacks: {{
                            title: function(context) {{
                                return 'Time: ' + context[0].parsed.x.toFixed(1) + 's';
                            }},
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + 'ms';
                            }}
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
    logger.info(f"Chart saved to: {output_path}")
    return html_content

async def main():
    duration_sec = 60  # Reduced duration for quicker testing
    qps = 5
    output_chart_path = "reports/observed/macros_compare.html"
    
    # Case A: Latency-leaning
    os.environ["LATENCY_GUARD"] = "0.7"
    os.environ["RECALL_BIAS"] = "0.4"
    results_a = await run_test_case("Case A (latency-leaning)", 0.7, 0.4, duration_sec, qps)

    # Case B: Recall-leaning
    os.environ["LATENCY_GUARD"] = "0.3"
    os.environ["RECALL_BIAS"] = "0.7"
    results_b = await run_test_case("Case B (recall-leaning)", 0.3, 0.7, duration_sec, qps)

    # Generate chart
    chart_html = generate_chart(results_a, results_b, output_chart_path)

    logger.info("Fixed Macro Knobs Test completed successfully!")

if __name__ == "__main__":
    # Clear any previous run info flag
    if hasattr(SearchPipeline, '_run_info_emitted'):
        del SearchPipeline._run_info_emitted
    asyncio.run(main())
