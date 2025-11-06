#!/usr/bin/env python3
import os, sys, csv, base64, json, zipfile, datetime, pathlib, subprocess

def _read_first(path):
    return next((p for p in sorted(pathlib.Path(path).glob("*")) if p.is_file()), None)

def _b64(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

def main():
    # Default locations (adjust here if your paths differ)
    golden_report_dir = "reports/rerank_html/postce_scifact_ta_golden"
    sweep_dir = "reports/rerank_html/sweep_scifact_ta_narrow"
    golden_cfg = "configs/demo_beir_scifact_ta_golden.yaml"

    # Artifacts
    golden_report = _read_first(golden_report_dir)  # latest golden html
    sweep_csv = pathlib.Path(sweep_dir) / "sweep_metrics.csv"
    sweep_png = pathlib.Path(sweep_dir) / "sweep_combined.png"

    # Checks
    assert golden_report and golden_report.suffix == ".html", f"Golden report missing in {golden_report_dir}"
    assert sweep_csv.exists(), f"Missing {sweep_csv}"
    assert sweep_png.exists(), f"Missing {sweep_png}"
    assert pathlib.Path(golden_cfg).exists(), f"Missing {golden_cfg}"

    # Read sweep CSV (grab rows; find best by recall, then p95)
    rows = []
    with open(sweep_csv, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            # normalize fields
            row["recall_at10"] = float(row.get("recall_at10", 0))
            row["p95_ms"] = float(row.get("p95_ms", row.get("p95", 0)))
            row["candidate_k"] = int(row.get("candidate_k", 0))
            row["rerank_k"] = int(row.get("rerank_k", 0))
            rows.append(row)
    assert rows, "Empty sweep CSV"

    rows_sorted = sorted(rows, key=lambda x: (-x["recall_at10"], x["p95_ms"], x["candidate_k"], x["rerank_k"]))
    best = rows_sorted[0]

    # Prepare bundle dir
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    bundle_dir = pathlib.Path(f"reports/bundles/scifact_ta_golden_{ts}")
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # Copy artifacts
    out_report = bundle_dir / golden_report.name
    out_csv = bundle_dir / "sweep_metrics.csv"
    out_png = bundle_dir / "sweep_combined.png"
    out_cfg = bundle_dir / pathlib.Path(golden_cfg).name

    out_report.write_bytes(golden_report.read_bytes())
    out_csv.write_bytes(sweep_csv.read_bytes())
    out_png.write_bytes(sweep_png.read_bytes())
    out_cfg.write_bytes(pathlib.Path(golden_cfg).read_bytes())

    # One-pager HTML (embed sweep image; show best params & rationale)
    img_b64 = _b64(out_png)
    onepager = bundle_dir / "one_pager.html"
    onepager.write_text(f"""<!doctype html>

<html lang="en"><meta charset="utf-8">
<title>Golden Config — SciFact-TA (Demo One-Pager)</title>
<style>
 body{{font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;max-width:900px;margin:40px auto;padding:0 16px;}}
 h1,h2{{margin: 12px 0;}}
 .kpi{{display:flex;gap:12px;flex-wrap:wrap}}
 .kpi>div{{flex:1;min-width:180px;background:#f6f7f9;border:1px solid #e6e8ec;border-radius:12px;padding:12px}}
 code,pre{{background:#f6f7f9;padding:2px 6px;border-radius:6px}}
 .img{{text-align:center;margin:16px 0}}
 .note{{font-size:12px;color:#666}}
</style>
<h1>Golden Config — SciFact-TA</h1>
<p>Selected by: max Recall@10 → min P95 → min candidate_k → min rerank_k</p>


<div class="kpi">
 <div><b>Recall@10</b><br>{best["recall_at10"]:.3f}</div>
 <div><b>P95 (ms)</b><br>{best["p95_ms"]:.0f}</div>
 <div><b>candidate_k</b><br>{best["candidate_k"]}</div>
 <div><b>rerank_k</b><br>{best["rerank_k"]}</div>
</div>


<h2>Why this is the "golden" point</h2>
<ul>
 <li>质量优先：在同等或更高 Recall@10 下，P95 也是更低/相当。</li>
 <li>性价比高：更小的 <code>candidate_k</code>/<code>rerank_k</code> 意味更低成本与更高吞吐。</li>
 <li>可复现：与窄域曲线一致，周边参数不显著更优。</li>
</ul>


<h2>Performance Sweep (narrow range)</h2>
<div class="img"><img src="{img_b64}" style="max-width:100%;border:1px solid #eee;border-radius:8px"></div>


<h2>Artifacts</h2>
<ul>
 <li>Full report (post-CE): <code>{out_report.name}</code></li>
 <li>Sweep CSV: <code>{out_csv.name}</code></li>
 <li>Sweep chart: <code>{out_png.name}</code></li>
 <li>Golden config: <code>{out_cfg.name}</code></li>
</ul>


<p class="note">Generated: {ts}. You can print this page to PDF if needed.</p>
</html>
""", encoding="utf-8")


    # Try optional PDF (if weasyprint is available)
    pdf_path = bundle_dir / "one_pager.pdf"
    try:
        subprocess.run(["python", "-c", "import weasyprint,sys; weasyprint.HTML(sys.argv[1]).write_pdf(sys.argv[2])", str(onepager), str(pdf_path)], check=True)
        had_pdf = pdf_path.exists()
    except Exception:
        had_pdf = False

    # ZIP bundle
    zip_path = pathlib.Path(f"{bundle_dir}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in bundle_dir.glob("*"):
            z.write(p, arcname=p.name)

    # Console summary
    print("=== GOLDEN ONE-PAGER ===")
    print(f"Recall@10={best['recall_at10']:.3f}, P95={best['p95_ms']:.0f}ms, candidate_k={best['candidate_k']}, rerank_k={best['rerank_k']}")
    print(f"Bundle dir : {bundle_dir}")
    print(f"One-pager  : {onepager}")
    if had_pdf: print(f"PDF        : {pdf_path}")
    print(f"ZIP        : {zip_path}")

if __name__ == "__main__":
    sys.exit(main())
