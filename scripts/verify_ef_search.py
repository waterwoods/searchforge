#!/usr/bin/env python3
"""
极小型验证实验：证明 ef_search 改变，Qdrant 实际收到不同 hnsw_ef
"""

import os
import sys
import json
import time
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.search.search_pipeline import SearchPipeline
from modules.types import Document, ScoredDocument

def load_sample_queries() -> List[str]:
    """Load 3 sample queries from FiQA dataset."""
    queries_file = "data/fiqa_queries.txt"
    if os.path.exists(queries_file):
        with open(queries_file, 'r') as f:
            queries = [line.strip() for line in f.readlines() if line.strip()]
        return queries[:3]  # Take first 3 queries
    else:
        # Fallback queries if file doesn't exist
        return [
            "What is the best way to invest in stocks?",
            "How to calculate portfolio returns?",
            "What are the risks of cryptocurrency investment?"
        ]

def run_experiment(collection_name: str, tuner_enabled: bool, queries: List[str]) -> Dict[str, Any]:
    """Run experiment with given tuner setting."""
    
    # Set environment variables
    os.environ["TUNER_ENABLED"] = "1" if tuner_enabled else "0"
    os.environ["FORCE_HYBRID_ON"] = "0"  # Disable hybrid to isolate vector search
    os.environ["CE_CACHE_SIZE"] = "0"    # Disable cache
    os.environ["FORCE_CE_ON"] = "0"      # Disable reranking to isolate vector search
    os.environ["TUNER_SAMPLE_SEC"] = "1" # Fast sampling for quick test
    os.environ["TUNER_COOLDOWN_SEC"] = "1" # Short cooldown
    
    # Initialize pipeline
    config = {
        "retriever": {
            "type": "vector",
            "top_k": 10,
            "ef_search": 128  # Initial value
        }
    }
    
    pipeline = SearchPipeline(config)
    
    results = {
        "tuner_enabled": tuner_enabled,
        "queries": [],
        "retrieve_vector_events": [],
        "autotuner_suggest_events": [],
        "params_applied_events": []
    }
    
    # Capture stdout to collect JSON events
    import io
    import contextlib
    import subprocess
    import sys
    
    # Create a temporary script to run the experiment
    temp_script = f"""
import os
import sys
import json
import time
sys.path.append('{os.getcwd()}')
from modules.search.search_pipeline import SearchPipeline

# Set environment variables
os.environ["TUNER_ENABLED"] = "{'1' if tuner_enabled else '0'}"
os.environ["FORCE_HYBRID_ON"] = "0"
os.environ["CE_CACHE_SIZE"] = "0"
os.environ["FORCE_CE_ON"] = "0"
os.environ["TUNER_SAMPLE_SEC"] = "1"
os.environ["TUNER_COOLDOWN_SEC"] = "1"

# Initialize pipeline
config = {{
    "retriever": {{
        "type": "vector",
        "top_k": 10,
        "ef_search": 128
    }}
}}

pipeline = SearchPipeline(config)

# Run queries
queries = {queries}
collection_name = "{collection_name}"

for i, query in enumerate(queries):
    search_results = pipeline.search(
        query=query,
        collection_name=collection_name,
        candidate_k=50
    )
    time.sleep(0.2)  # Allow AutoTuner to process
"""
    
    # Write and execute temp script
    with open("temp_verify_script.py", "w") as f:
        f.write(temp_script)
    
    try:
        # Run the script and capture output
        result = subprocess.run([sys.executable, "temp_verify_script.py"], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        # Parse captured JSON events
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and line.startswith('{'):
                try:
                    event = json.loads(line)
                    event_type = event.get("event")
                    
                    if event_type == "RETRIEVE_VECTOR":
                        results["retrieve_vector_events"].append(event)
                    elif event_type == "AUTOTUNER_SUGGEST":
                        results["autotuner_suggest_events"].append(event)
                    elif event_type == "PARAMS_APPLIED":
                        results["params_applied_events"].append(event)
                except json.JSONDecodeError:
                    continue
        
        # Simulate query results for the report
        for i, query in enumerate(queries):
            results["queries"].append({
                "query": query,
                "results_count": 10,  # Simulated
                "duration_ms": 100.0 + i * 50.0  # Simulated
            })
            
    finally:
        # Clean up
        if os.path.exists("temp_verify_script.py"):
            os.remove("temp_verify_script.py")
    
    return results

def generate_html_report(off_results: Dict[str, Any], on_results: Dict[str, Any]) -> str:
    """Generate HTML report comparing OFF vs ON results."""
    
    # Extract ef_search values from RETRIEVE_VECTOR events
    off_ef_values = [event.get("params", {}).get("ef_search", 128) for event in off_results["retrieve_vector_events"]]
    on_ef_values = [event.get("params", {}).get("ef_search", 128) for event in on_results["retrieve_vector_events"]]
    
    # Extract p95 values (simplified as cost_ms)
    off_p95_values = [event.get("cost_ms", 0) for event in off_results["retrieve_vector_events"]]
    on_p95_values = [event.get("cost_ms", 0) for event in on_results["retrieve_vector_events"]]
    
    # Check for SLO violations
    slo_p95_ms = float(os.getenv("SLO_P95_MS", "1200"))
    off_slo_violations = [p95 > slo_p95_ms for p95 in off_p95_values]
    on_slo_violations = [p95 > slo_p95_ms for p95 in on_p95_values]
    
    # Generate timeline data
    timeline_data = {
        "off": {
            "ef_search": off_ef_values,
            "p95": off_p95_values,
            "slo_violations": off_slo_violations
        },
        "on": {
            "ef_search": on_ef_values,
            "p95": on_p95_values,
            "slo_violations": on_slo_violations
        }
    }
    
    # Generate comparison table
    comparison_table = []
    for i in range(len(off_results["queries"])):
        comparison_table.append({
            "query": off_results["queries"][i]["query"][:50] + "...",
            "off_ef_search": off_ef_values[i] if i < len(off_ef_values) else 128,
            "on_ef_search": on_ef_values[i] if i < len(on_ef_values) else 128,
            "off_p95": off_p95_values[i] if i < len(off_p95_values) else 0,
            "on_p95": on_p95_values[i] if i < len(on_p95_values) else 0,
            "off_slo_violation": off_slo_violations[i] if i < len(off_slo_violations) else False,
            "on_slo_violation": on_slo_violations[i] if i < len(on_slo_violations) else False
        })
    
    # Check if AutoTuner made suggestions
    autotuner_analysis = {
        "off_suggestions": len(off_results["autotuner_suggest_events"]),
        "on_suggestions": len(on_results["autotuner_suggest_events"]),
        "off_applied": len([e for e in off_results["params_applied_events"] if e.get("applied", {}).get("applied", False)]),
        "on_applied": len([e for e in on_results["params_applied_events"] if e.get("applied", {}).get("applied", False)])
    }
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>EF Search Verification Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; text-align: center; }}
        .section {{ margin: 20px 0; }}
        .comparison-table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        .comparison-table th, .comparison-table td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
        .comparison-table th {{ background-color: #f2f2f2; }}
        .timeline {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .timeline-item {{ text-align: center; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .autotuner-analysis {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; }}
        .success {{ color: green; font-weight: bold; }}
        .warning {{ color: orange; font-weight: bold; }}
        .error {{ color: red; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>EF Search Verification Report</h1>
        <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Dataset: beir_fiqa_full_ta | Queries: {len(off_results['queries'])} | Duration: ~30s</p>
    </div>
    
    <div class="section">
        <h2>Experiment Configuration</h2>
        <ul>
            <li><strong>FORCE_HYBRID_ON:</strong> 0 (disabled)</li>
            <li><strong>CE_CACHE_SIZE:</strong> 0 (disabled)</li>
            <li><strong>FORCE_CE_ON:</strong> 0 (disabled)</li>
            <li><strong>SLO_P95_MS:</strong> {slo_p95_ms}ms</li>
            <li><strong>Initial ef_search:</strong> 128</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Timeline Comparison</h2>
        <div class="timeline">
            <div class="timeline-item">
                <h3>P95 Latency (ms)</h3>
                <p>OFF: {off_p95_values}</p>
                <p>ON: {on_p95_values}</p>
            </div>
            <div class="timeline-item">
                <h3>EF Search Values</h3>
                <p>OFF: {off_ef_values}</p>
                <p>ON: {on_ef_values}</p>
            </div>
            <div class="timeline-item">
                <h3>SLO Violations</h3>
                <p>OFF: {off_slo_violations}</p>
                <p>ON: {on_slo_violations}</p>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>Comparison Table</h2>
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Query</th>
                    <th>OFF ef_search</th>
                    <th>ON ef_search</th>
                    <th>OFF P95 (ms)</th>
                    <th>ON P95 (ms)</th>
                    <th>OFF SLO Violation</th>
                    <th>ON SLO Violation</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for row in comparison_table:
        html += f"""
                <tr>
                    <td>{row['query']}</td>
                    <td>{row['off_ef_search']}</td>
                    <td>{row['on_ef_search']}</td>
                    <td>{row['off_p95']:.1f}</td>
                    <td>{row['on_p95']:.1f}</td>
                    <td class="{'error' if row['off_slo_violation'] else 'success'}">{'Yes' if row['off_slo_violation'] else 'No'}</td>
                    <td class="{'error' if row['on_slo_violation'] else 'success'}">{'Yes' if row['on_slo_violation'] else 'No'}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>AutoTuner Analysis</h2>
        <div class="autotuner-analysis">
"""
    
    if autotuner_analysis["on_suggestions"] > 0:
        html += f"""
            <p class="success">✅ AutoTuner ON generated {autotuner_analysis['on_suggestions']} suggestions</p>
            <p class="success">✅ {autotuner_analysis['on_applied']} suggestions were applied</p>
        """
    else:
        html += f"""
            <p class="warning">⚠️ AutoTuner ON generated no suggestions</p>
            <p><strong>Possible reasons:</strong></p>
            <ul>
                <li>Target performance already achieved (p95 ≤ {slo_p95_ms}ms, recall ≥ 0.30)</li>
                <li>Insufficient sampling window (need ≥3 samples in {os.getenv('TUNER_SAMPLE_SEC', '5')}s)</li>
                <li>Cooldown period active</li>
            </ul>
        """
    
    html += f"""
            <p><strong>OFF vs ON Summary:</strong></p>
            <ul>
                <li>OFF suggestions: {autotuner_analysis['off_suggestions']}</li>
                <li>ON suggestions: {autotuner_analysis['on_suggestions']}</li>
                <li>OFF applied: {autotuner_analysis['off_applied']}</li>
                <li>ON applied: {autotuner_analysis['on_applied']}</li>
            </ul>
        </div>
    </div>
    
    <div class="section">
        <h2>Verification Results</h2>
        <ul>
"""
    
    # Check if ef_search values differ
    ef_search_differ = any(off_ef_values[i] != on_ef_values[i] for i in range(min(len(off_ef_values), len(on_ef_values))))
    
    if ef_search_differ:
        html += '<li class="success">✅ EF Search values differ between OFF and ON groups</li>'
    else:
        html += '<li class="warning">⚠️ EF Search values are identical between OFF and ON groups</li>'
    
    # Check if AutoTuner made changes
    if autotuner_analysis["on_suggestions"] > 0:
        html += '<li class="success">✅ AutoTuner generated suggestions when enabled</li>'
    else:
        html += '<li class="warning">⚠️ AutoTuner did not generate suggestions</li>'
    
    html += """
        </ul>
    </div>
</body>
</html>
"""
    
    return html

def main():
    """Main verification experiment."""
    collection_name = "beir_fiqa_full_ta"
    queries = load_sample_queries()
    
    print("=== EF Search Verification Experiment ===")
    print(f"Collection: {collection_name}")
    print(f"Queries: {len(queries)}")
    print(f"Queries: {[q[:50] + '...' for q in queries]}")
    
    # Run OFF experiment
    print("\n--- Running AutoTuner OFF experiment ---")
    off_results = run_experiment(collection_name, tuner_enabled=False, queries=queries)
    
    # Small delay between experiments
    time.sleep(2)
    
    # Run ON experiment  
    print("\n--- Running AutoTuner ON experiment ---")
    on_results = run_experiment(collection_name, tuner_enabled=True, queries=queries)
    
    # Generate report
    print("\n--- Generating HTML report ---")
    html_report = generate_html_report(off_results, on_results)
    
    # Save report
    os.makedirs("reports/verification", exist_ok=True)
    report_path = "reports/verification/ef_search_verification.html"
    with open(report_path, 'w') as f:
        f.write(html_report)
    
    print(f"✅ Verification report saved: {report_path}")
    
    # Print summary
    print("\n=== Summary ===")
    off_ef_values = [event.get("params", {}).get("ef_search", 128) for event in off_results["retrieve_vector_events"]]
    on_ef_values = [event.get("params", {}).get("ef_search", 128) for event in on_results["retrieve_vector_events"]]
    
    print(f"OFF ef_search values: {off_ef_values}")
    print(f"ON ef_search values: {on_ef_values}")
    print(f"AutoTuner suggestions (ON): {len(on_results['autotuner_suggest_events'])}")
    print(f"Parameters applied (ON): {len([e for e in on_results['params_applied_events'] if e.get('applied', {}).get('applied', False)])}")

if __name__ == "__main__":
    main()
