#!/usr/bin/env python3
"""
Multi-dataset bundle exporter.
Generates one-pager and bundles for individual datasets.
"""

import argparse
import csv
import base64
import json
import zipfile
import datetime
import pathlib
import subprocess
import sys
import yaml
from dataset_registry import get_dataset_registry

def _b64(path):
    """Convert image to base64 data URL."""
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

def _read_first(path):
    """Get the first file in a directory."""
    return next((p for p in sorted(pathlib.Path(path).glob("*")) if p.is_file()), None)

def get_golden_metrics(golden_config_path):
    """Extract metrics from golden config."""
    with open(golden_config_path) as f:
        config = yaml.safe_load(f)
    
    retriever = config.get("retriever", {})
    reranker = config.get("reranker", {})
    
    return {
        "candidate_k": retriever.get("top_k", 0),
        "rerank_k": reranker.get("top_k", 0),
        "collection": retriever.get("collection", "unknown")
    }

def get_sweep_best_metrics(sweep_csv_path):
    """Get best metrics from sweep CSV."""
    if not sweep_csv_path.exists():
        return {"recall_at10": 0.0, "p95_ms": 0.0}
    
    rows = []
    with open(sweep_csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            recall = float(row.get("recall_at10", 0))
            p95 = float(row.get("p95_ms", row.get("p95", 0)))
            candidate_k = int(row.get("candidate_k", 0))
            rerank_k = int(row.get("rerank_k", 0))
            rows.append((recall, p95, candidate_k, rerank_k))
    
    if not rows:
        return {"recall_at10": 0.0, "p95_ms": 0.0}
    
    # Sort by recall desc, then p95 asc, then candidate_k asc, then rerank_k asc
    rows.sort(key=lambda x: (-x[0], x[1], x[2], x[3]))
    best_recall, best_p95, _, _ = rows[0]
    
    return {"recall_at10": best_recall, "p95_ms": best_p95}

def generate_one_pager(dataset_name, bundle_dir, golden_metrics, sweep_metrics, sweep_png_path):
    """Generate one-pager HTML."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    
    # Embed sweep image if available
    img_b64 = ""
    if sweep_png_path and sweep_png_path.exists():
        img_b64 = _b64(sweep_png_path)
    
    onepager = bundle_dir / "one_pager.html"
    onepager.write_text(f"""<!doctype html>
<html lang="en"><meta charset="utf-8">
<title>Golden Config — {dataset_name.upper()} (Demo One-Pager)</title>
<style>
 body{{font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;max-width:900px;margin:40px auto;padding:0 16px;}}
 h1,h2{{margin: 12px 0;}}
 .kpi{{display:flex;gap:12px;flex-wrap:wrap}}
 .kpi>div{{flex:1;min-width:180px;background:#f6f7f9;border:1px solid #e6e8ec;border-radius:12px;padding:12px}}
 code,pre{{background:#f6f7f9;padding:2px 6px;border-radius:6px}}
 .img{{text-align:center;margin:16px 0}}
 .note{{font-size:12px;color:#666}}
</style>
<h1>Golden Config — {dataset_name.upper()}</h1>
<p>Selected by: max Recall@10 → min P95 → min candidate_k → min rerank_k</p>

<div class="kpi">
 <div><b>Recall@10</b><br>{sweep_metrics.get('recall_at10', 0):.3f}</div>
 <div><b>P95 (ms)</b><br>{sweep_metrics.get('p95_ms', 0):.0f}</div>
 <div><b>candidate_k</b><br>{golden_metrics.get('candidate_k', 0)}</div>
 <div><b>rerank_k</b><br>{golden_metrics.get('rerank_k', 0)}</div>
</div>

<h2>Why this is the "golden" point</h2>
<ul>
 <li>质量优先：在同等或更高 Recall@10 下，P95 也是更低/相当。</li>
 <li>性价比高：更小的 <code>candidate_k</code>/<code>rerank_k</code> 意味更低成本与更高吞吐。</li>
 <li>可复现：与窄域曲线一致，周边参数不显著更优。</li>
</ul>

<h2>Performance Sweep</h2>
{f'<div class="img"><img src="{img_b64}" style="max-width:100%;border:1px solid #eee;border-radius:8px"></div>' if img_b64 else '<p><em>No sweep data available</em></p>'}

<h2>Artifacts</h2>
<ul>
 <li>Full report (post-CE): <code>report_*.html</code></li>
 <li>Sweep CSV: <code>sweep_metrics.csv</code></li>
 <li>Sweep chart: <code>sweep_combined.png</code></li>
 <li>Golden config: <code>demo_{dataset_name}_golden.yaml</code></li>
</ul>

<p class="note">Generated: {ts}. You can print this page to PDF if needed.</p>
</html>
""", encoding="utf-8")
    
    return onepager

def main():
    parser = argparse.ArgumentParser(description="Export bundle for a single dataset")
    parser.add_argument("--dataset", required=True, help="Dataset name")
    parser.add_argument("--golden", required=True, help="Golden config YAML file")
    parser.add_argument("--sweep-dir", required=True, help="Sweep directory")
    
    args = parser.parse_args()
    
    # Validate inputs
    golden_config_path = pathlib.Path(args.golden)
    sweep_dir_path = pathlib.Path(args.sweep_dir)
    
    if not golden_config_path.exists():
        print(f"ERROR: Golden config not found: {golden_config_path}")
        sys.exit(1)
    
    if not sweep_dir_path.exists():
        print(f"ERROR: Sweep directory not found: {sweep_dir_path}")
        sys.exit(1)
    
    # Get dataset info
    registry = get_dataset_registry()
    if args.dataset not in registry:
        print(f"ERROR: Unknown dataset: {args.dataset}")
        sys.exit(1)
    
    dataset_info = registry[args.dataset]
    
    # Get golden metrics
    golden_metrics = get_golden_metrics(golden_config_path)
    
    # Get sweep metrics
    sweep_csv_path = sweep_dir_path / "sweep_metrics.csv"
    sweep_metrics = get_sweep_best_metrics(sweep_csv_path)
    
    # Create bundle directory
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    bundle_dir = pathlib.Path(f"reports/bundles/{args.dataset}_{ts}")
    bundle_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"=== Exporting bundle for dataset: {args.dataset} ===")
    print(f"Golden config: {golden_config_path}")
    print(f"Sweep dir: {sweep_dir_path}")
    print(f"Bundle dir: {bundle_dir}")
    
    # Copy artifacts
    out_golden = bundle_dir / f"demo_{args.dataset}_golden.yaml"
    out_csv = bundle_dir / "sweep_metrics.csv"
    out_png = bundle_dir / "sweep_combined.png"
    
    out_golden.write_bytes(golden_config_path.read_bytes())
    
    if sweep_csv_path.exists():
        out_csv.write_bytes(sweep_csv_path.read_bytes())
    
    sweep_png_path = sweep_dir_path / "sweep_combined.png"
    if sweep_png_path.exists():
        out_png.write_bytes(sweep_png_path.read_bytes())
    
    # Generate HTML report using existing script
    report_cmd = [
        "python", "scripts/rerank_report_html.py",
        "--config", str(golden_config_path),
        "--collection", golden_metrics.get("collection", dataset_info["collection"]),
        "--queries", dataset_info["queries_file"],
        "--candidate_k", str(golden_metrics.get("candidate_k", 100)),
        "--rerank_k", str(golden_metrics.get("rerank_k", 50)),
        "--normalize-ce",
        "--output", str(bundle_dir),
        "--sweep-dir", str(sweep_dir_path)
    ]
    
    try:
        subprocess.run(report_cmd, check=True)
        print("SUCCESS: Generated HTML report")
    except subprocess.CalledProcessError as e:
        print(f"WARNING: HTML report generation failed: {e}")
    
    # Generate one-pager
    one_pager_path = generate_one_pager(args.dataset, bundle_dir, golden_metrics, sweep_metrics, out_png if out_png.exists() else None)
    
    # Create ZIP bundle
    zip_path = pathlib.Path(f"{bundle_dir}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in bundle_dir.glob("*"):
            z.write(p, arcname=p.name)
    
    # Print summary
    print(f"\n=== BUNDLE SUMMARY ===")
    print(f"Dataset: {args.dataset}")
    print(f"Recall@10: {sweep_metrics.get('recall_at10', 0):.3f}")
    print(f"P95: {sweep_metrics.get('p95_ms', 0):.0f}ms")
    print(f"candidate_k: {golden_metrics.get('candidate_k', 0)}")
    print(f"rerank_k: {golden_metrics.get('rerank_k', 0)}")
    print(f"Bundle dir: {bundle_dir}")
    print(f"One-pager: {one_pager_path}")
    print(f"ZIP: {zip_path}")

if __name__ == "__main__":
    main()
