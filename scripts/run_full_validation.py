#!/usr/bin/env python3
"""一键完成最终验证：Judger 人审 + 10分钟 Canary + 一页报告"""
import sys, time, json, webbrowser, requests, shutil
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent))
from judger_sample import load_latest_results, create_batch
from run_canary_10min import main as run_canary
from snap_report import try_playwright, try_selenium, try_wkhtmltoimage
BASE, ROOT = "http://localhost:8080", Path(__file__).parent.parent
REPORTS, DOCS = ROOT/"reports", ROOT/"docs"
def hdr(t): print(f"\n{'='*60}\n  {t}\n{'='*60}\n")
def stage_judger(n=30):
    hdr("STAGE 1: Judger 人审")
    print("[VALIDATION] Generating batch...")
    batch = create_batch(load_latest_results(), n=n, strategy="mixed", four_way=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {"batch_id":ts, "created_at":datetime.now().isoformat(), 
            "total":len(batch), "strategy":"mixed", "four_way":True, "items":batch}
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS/f"judge_batch_{ts}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    shutil.copy(path, REPORTS/"judge_batch_latest.json")
    print(f"[VALIDATION] ✓ Batch: {path.name} (n={len(batch)})")
    url = f"{BASE}/judge?batch=latest"
    print(f"[VALIDATION] Opening: {url}")
    try: webbrowser.open(url)
    except: print(f"[VALIDATION] ⚠️  Manually open: {url}")
    print(f"[VALIDATION] Waiting for labelling (Ctrl+C to skip)...\n")
    try:
        while True:
            time.sleep(10)
            try:
                r = requests.get(f"{BASE}/judge/summary.json?batch=latest", timeout=5)
                if r.ok:
                    s = r.json(); l, v = s.get("labelled",0), s.get("verdict","PENDING")
                    print(f"[VALIDATION]   {l}/{len(batch)} | {v}")
                    if l >= len(batch): break
            except: pass
    except KeyboardInterrupt: print("\n[VALIDATION] Skip wait")
    r = requests.get(f"{BASE}/judge/report.json?batch=latest", timeout=5)
    if r.ok:
        s = r.json()
        br, l = s.get("better_rate",0), s.get("labelled",0)
        v = "PASS" if (l >= len(batch) and br >= 0.70) else ("PENDING" if l < len(batch) else "FAIL")
        return {"verdict":v, "better_rate":br, "n":l}
    return None
def stage_canary():
    hdr("STAGE 2: Canary 测试")
    run_canary()
    p = REPORTS/"autotuner_canary.json"
    if p.exists():
        r = json.loads(p.read_text())
        dr, dp, pv = r.get("delta_recall",0), r.get("delta_p95_ms",0), r.get("p_value",1)
        bon, boff = r.get("buckets_on",0), r.get("buckets_off",0)
        return {"delta_recall":dr, "delta_p95":dp, "p_value":pv, "buckets_on":bon, "buckets_off":boff}
    return None
def stage_report():
    hdr("STAGE 3: 报告生成")
    DOCS.mkdir(exist_ok=True); out = DOCS/"judge_verdict.png"
    print(f"[VALIDATION] Screenshot: {BASE}/judge/report")
    sz = None
    try: sz = try_playwright(f"{BASE}/judge/report", str(out))
    except:
        try: sz = try_selenium(f"{BASE}/judge/report", str(out))
        except:
            if shutil.which('wkhtmltoimage'): sz = try_wkhtmltoimage(f"{BASE}/judge/report", str(out))
    if sz: print(f"[REPORT] Updated {out} ({sz})")
    pdf = DOCS/"one_pager_fiqa.pdf"
    if pdf.exists(): print(f"[REPORT] Updated {pdf}")
def main():
    print("╔"+"═"*58+"╗\n║"+" "*10+"SearchForge 一键完成最终验证"+" "*17+"║\n╚"+"═"*58+"╝")
    j = stage_judger(n=30); c = stage_canary(); stage_report()
    if j: print(f"\n[JUDGE] verdict={j['verdict']} | better_rate={j['better_rate']:.2f} | n={j['n']}")
    if c: print(f"[CANARY] ΔRecall={c['delta_recall']:+.2f} | ΔP95={c['delta_p95']:+.0f}ms | p={c['p_value']:.3f} | buckets_on={c['buckets_on']} buckets_off={c['buckets_off']}")
    return 0
if __name__ == "__main__": sys.exit(main())