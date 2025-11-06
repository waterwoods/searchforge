#!/usr/bin/env python3
"""
Generate Lab Report from Current Experiment State
"""

import requests
import sys
from pathlib import Path

def generate_report_from_api():
    """Fetch experiment state from API and generate report."""
    
    # Get experiment status
    try:
        response = requests.get("http://localhost:8011/ops/lab/status")
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Failed to fetch experiment status: {e}")
        sys.exit(1)
    
    if not data.get("ok"):
        print("❌ No experiment data available")
        sys.exit(1)
    
    # Generate report
    lines = []
    lines.append("=" * 70)
    lines.append("LAB DASHBOARD EXPERIMENT REPORT")
    lines.append("=" * 70)
    lines.append("")
    
    # Experiment metadata
    lines.append("EXPERIMENT METADATA")
    lines.append("-" * 70)
    lines.append(f"Experiment ID: {data.get('experiment_id', 'N/A')}")
    lines.append(f"Type: {data.get('experiment_type', 'N/A')}")
    lines.append(f"Rounds: {data.get('total_rounds', 0)} (ABAB cycles)")
    lines.append(f"Status: {data.get('phase', 'N/A')}")
    lines.append("")
    
    # Window analysis
    windows = data.get("windows", [])
    a_windows = [w for w in windows if w.get("phase") == "A" and w.get("valid", False)]
    b_windows = [w for w in windows if w.get("phase") == "B" and w.get("valid", False)]
    
    lines.append("WINDOW ANALYSIS")
    lines.append("-" * 70)
    lines.append(f"Total Windows: {len(windows)}")
    lines.append(f"Valid A Windows: {len(a_windows)}")
    lines.append(f"Valid B Windows: {len(b_windows)}")
    lines.append(f"Noisy Windows: {len([w for w in windows if not w.get('valid', False)])}")
    lines.append("")
    
    # Compute deltas
    deltas = data.get("deltas", {})
    
    lines.append("DELTA METRICS (Valid Windows Only)")
    lines.append("-" * 70)
    
    delta_p95 = deltas.get("deltaP95")
    if delta_p95 is not None:
        lines.append(f"ΔP95: {delta_p95:+.1f}%")
    else:
        lines.append("ΔP95: [insufficient data]")
    
    delta_qps = deltas.get("deltaQPS")
    if delta_qps is not None:
        lines.append(f"ΔQPS: {delta_qps:+.1f}%")
    else:
        lines.append("ΔQPS: [insufficient data]")
    
    delta_recall = deltas.get("deltaRecall")
    if delta_recall is not None:
        lines.append(f"ΔRecall: {delta_recall:+.1f}%")
    else:
        lines.append("ΔRecall: [not available]")
    
    lines.append("")
    
    # Detailed window log
    lines.append("WINDOW LOG")
    lines.append("-" * 70)
    for i, w in enumerate(windows):
        status = "✓" if w.get("valid", False) else "✗ NOISY"
        p95 = w.get("p95_ms")
        p95_str = f"{p95:>6.1f}" if p95 is not None else "   N/A"
        qps = w.get("qps", 0.0)
        noise = w.get("noise_index", 0.0)
        phase = w.get("phase", "?")
        
        lines.append(
            f"{i+1:2d}. {phase} | p95={p95_str} qps={qps:>5.1f} "
            f"noise={noise:>5.1f} {status}"
        )
    
    lines.append("")
    
    # Summary
    lines.append("SUMMARY")
    lines.append("-" * 70)
    if delta_p95 is None and delta_qps == 0:
        lines.append("⚠️  No traffic detected during experiment")
        lines.append("    Consider running a load test to generate meaningful metrics")
    else:
        lines.append("✓ Experiment completed with valid metrics")
    
    lines.append("")
    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("=" * 70)
    
    report_text = "\n".join(lines)
    
    # Save report
    project_root = Path(__file__).parent.parent
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_path = reports_dir / "LAB_DASHBOARD_MINI.txt"
    report_path.write_text(report_text)
    
    print(f"✅ Report generated: {report_path}")
    print()
    print(report_text)
    
    return report_path


if __name__ == "__main__":
    generate_report_from_api()

