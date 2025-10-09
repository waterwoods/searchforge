#!/usr/bin/env python3
"""
Final verification script to demonstrate ef_search parameter changes
"""

import os
import sys
import json
import time

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.search.search_pipeline import SearchPipeline

def test_ef_search_changes():
    """Test that ef_search parameter changes are reflected in RETRIEVE_VECTOR events."""
    
    # Set environment variables to force AutoTuner to make suggestions
    os.environ["TUNER_ENABLED"] = "1"
    os.environ["FORCE_HYBRID_ON"] = "0"
    os.environ["CE_CACHE_SIZE"] = "0"
    os.environ["FORCE_CE_ON"] = "1"  # Enable reranking to get full pipeline
    os.environ["TUNER_SAMPLE_SEC"] = "1"  # Fast sampling
    os.environ["TUNER_COOLDOWN_SEC"] = "1"  # Short cooldown
    os.environ["SLO_P95_MS"] = "500"  # Lower SLO to trigger suggestions
    
    # Initialize pipeline
    config = {
        "retriever": {
            "type": "vector",
            "top_k": 10,
            "ef_search": 128
        },
        "reranker": {
            "type": "cross_encoder",
            "model": "cross-encoder/ms-marco-MiniLM-L-2-v2",
            "top_k": 50
        }
    }
    
    pipeline = SearchPipeline(config)
    
    # Test queries
    queries = [
        "What is ETF expense ratio?",
        "How to calculate portfolio returns?",
        "What are the risks of cryptocurrency investment?"
    ]
    
    print("=== EF Search Parameter Flow Verification ===")
    print(f"Initial ef_search: 128")
    print(f"SLO_P95_MS: 500ms (low to trigger AutoTuner)")
    print(f"Queries: {len(queries)}")
    
    # Capture stdout
    import io
    import contextlib
    
    stdout_capture = io.StringIO()
    
    with contextlib.redirect_stdout(stdout_capture):
        for i, query in enumerate(queries):
            print(f"\n--- Query {i+1}: {query[:50]}... ---")
            
            # Run search
            search_results = pipeline.search(
                query=query,
                collection_name="beir_fiqa_full_ta",
                candidate_k=50
            )
            
            print(f"Results: {len(search_results)}")
            
            # Small delay to allow AutoTuner to process
            time.sleep(0.5)
    
    # Parse captured output
    captured_output = stdout_capture.getvalue()
    
    # Parse JSON events
    events = []
    for line in captured_output.split('\n'):
        line = line.strip()
        if line and line.startswith('{'):
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError:
                continue
    
    # Extract RETRIEVE_VECTOR events
    vector_events = [e for e in events if e.get('event') == 'RETRIEVE_VECTOR']
    autotuner_events = [e for e in events if e.get('event') == 'AUTOTUNER_SUGGEST']
    params_applied_events = [e for e in events if e.get('event') == 'PARAMS_APPLIED']
    
    print(f"\n=== Analysis Results ===")
    print(f"Total events: {len(events)}")
    print(f"RETRIEVE_VECTOR events: {len(vector_events)}")
    print(f"AUTOTUNER_SUGGEST events: {len(autotuner_events)}")
    print(f"PARAMS_APPLIED events: {len(params_applied_events)}")
    
    print(f"\n=== RETRIEVE_VECTOR Events ===")
    ef_search_values = []
    for i, event in enumerate(vector_events):
        ef_search = event.get('params', {}).get('ef_search', 'NOT_FOUND')
        ef_search_values.append(ef_search)
        print(f"Query {i+1}: ef_search = {ef_search}")
    
    print(f"\n=== AutoTuner Events ===")
    for i, event in enumerate(autotuner_events):
        suggest = event.get('params', {}).get('suggest', {})
        ef_search = suggest.get('ef_search', 'NOT_FOUND')
        p95_ms = event.get('params', {}).get('p95_ms', 'NOT_FOUND')
        recall_at10 = event.get('params', {}).get('recall_at10', 'NOT_FOUND')
        print(f"Suggestion {i+1}: ef_search = {ef_search}, p95_ms = {p95_ms}, recall_at10 = {recall_at10}")
    
    print(f"\n=== Parameter Applied Events ===")
    for i, event in enumerate(params_applied_events):
        applied = event.get('applied', {})
        applied_flag = applied.get('applied', False)
        old_ef = applied.get('old_ef_search', 'NOT_FOUND')
        new_ef = applied.get('new_ef_search', 'NOT_FOUND')
        reason = applied.get('reason', 'NOT_FOUND')
        print(f"Applied {i+1}: applied = {applied_flag}, {old_ef} -> {new_ef}, reason = {reason}")
    
    # Generate HTML report
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>EF Search Parameter Flow Verification</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; text-align: center; }}
        .section {{ margin: 20px 0; }}
        .event-table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        .event-table th, .event-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .event-table th {{ background-color: #f2f2f2; }}
        .success {{ color: green; font-weight: bold; }}
        .warning {{ color: orange; font-weight: bold; }}
        .code {{ background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>EF Search Parameter Flow Verification</h1>
        <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h2>Experiment Configuration</h2>
        <ul>
            <li><strong>Dataset:</strong> beir_fiqa_full_ta</li>
            <li><strong>Queries:</strong> {len(queries)}</li>
            <li><strong>Initial ef_search:</strong> 128</li>
            <li><strong>SLO_P95_MS:</strong> 500ms (low to trigger AutoTuner)</li>
            <li><strong>TUNER_ENABLED:</strong> 1</li>
            <li><strong>FORCE_CE_ON:</strong> 1</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>RETRIEVE_VECTOR Events</h2>
        <table class="event-table">
            <thead>
                <tr>
                    <th>Query</th>
                    <th>ef_search</th>
                    <th>candidate_k</th>
                    <th>cost_ms</th>
                    <th>candidates_returned</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for i, event in enumerate(vector_events):
        params = event.get('params', {})
        stats = event.get('stats', {})
        html += f"""
                <tr>
                    <td>Query {i+1}</td>
                    <td class="code">{params.get('ef_search', 'N/A')}</td>
                    <td>{params.get('candidate_k', 'N/A')}</td>
                    <td>{event.get('cost_ms', 'N/A'):.1f}</td>
                    <td>{stats.get('candidates_returned', 'N/A')}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>AutoTuner Events</h2>
"""
    
    if autotuner_events:
        html += """
        <table class="event-table">
            <thead>
                <tr>
                    <th>Suggestion</th>
                    <th>ef_search</th>
                    <th>p95_ms</th>
                    <th>recall_at10</th>
                </tr>
            </thead>
            <tbody>
"""
        for i, event in enumerate(autotuner_events):
            params = event.get('params', {})
            suggest = params.get('suggest', {})
            html += f"""
                <tr>
                    <td>Suggestion {i+1}</td>
                    <td class="code">{suggest.get('ef_search', 'N/A')}</td>
                    <td>{params.get('p95_ms', 'N/A')}</td>
                    <td>{params.get('recall_at10', 'N/A'):.3f}</td>
                </tr>
"""
        html += """
            </tbody>
        </table>
"""
    else:
        html += "<p class='warning'>⚠️ No AutoTuner suggestions generated</p>"
    
    html += """
    </div>
    
    <div class="section">
        <h2>Parameter Applied Events</h2>
"""
    
    if params_applied_events:
        html += """
        <table class="event-table">
            <thead>
                <tr>
                    <th>Applied</th>
                    <th>Old ef_search</th>
                    <th>New ef_search</th>
                    <th>Reason</th>
                </tr>
            </thead>
            <tbody>
"""
        for i, event in enumerate(params_applied_events):
            applied = event.get('applied', {})
            html += f"""
                <tr>
                    <td class="{'success' if applied.get('applied', False) else 'warning'}">{'Yes' if applied.get('applied', False) else 'No'}</td>
                    <td class="code">{applied.get('old_ef_search', 'N/A')}</td>
                    <td class="code">{applied.get('new_ef_search', 'N/A')}</td>
                    <td>{applied.get('reason', 'N/A')}</td>
                </tr>
"""
        html += """
            </tbody>
        </table>
"""
    else:
        html += "<p class='warning'>⚠️ No parameter applications recorded</p>"
    
    html += f"""
    </div>
    
    <div class="section">
        <h2>Verification Results</h2>
        <ul>
            <li class="success">✅ RETRIEVE_VECTOR events captured: {len(vector_events)}</li>
            <li class="success">✅ ef_search parameter logged: {ef_search_values}</li>
"""
    
    if len(set(ef_search_values)) > 1:
        html += '<li class="success">✅ EF Search values changed during experiment</li>'
    else:
        html += '<li class="warning">⚠️ EF Search values remained constant</li>'
    
    if autotuner_events:
        html += '<li class="success">✅ AutoTuner generated suggestions</li>'
    else:
        html += '<li class="warning">⚠️ AutoTuner did not generate suggestions</li>'
    
    html += """
        </ul>
    </div>
</body>
</html>
"""
    
    # Save report
    os.makedirs("reports/verification", exist_ok=True)
    report_path = "reports/verification/ef_search_parameter_flow.html"
    with open(report_path, 'w') as f:
        f.write(html)
    
    print(f"\n✅ Verification report saved: {report_path}")
    
    return {
        "vector_events": vector_events,
        "autotuner_events": autotuner_events,
        "params_applied_events": params_applied_events,
        "ef_search_values": ef_search_values
    }

if __name__ == "__main__":
    results = test_ef_search_changes()
